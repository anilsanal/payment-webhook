#!/usr/bin/env python3
"""
Payment Gateway Performance Monitor
Monitors MID + Bank performance and sends Telegram alerts
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv('/opt/payment-webhook/.env')

# Configuration
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'payment_transactions'),
    'user': os.getenv('DB_USER', 'webhook_user'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_IDS = [id.strip() for id in os.getenv('TELEGRAM_CHANNEL_ID', '').split(',') if id.strip()]

# Alert thresholds
THRESHOLDS = {
    '5min': {
        'min_transactions': 8,
        'critical_decline_rate': 75,
        'warning_decline_rate': 60
    },
    '15min': {
        'min_transactions': 13,
        'critical_decline_rate': 75,
        'warning_decline_rate': 50
    },
    '30min': {
        'min_transactions': 25,
        'critical_decline_rate': 70,
        'warning_decline_rate': 50
    }
}

COOLDOWN_MINUTES = 1440  # 24 hours

# Smart filtering configuration
SMART_FILTER_CONFIG = {
    'enabled': True,  # Set to False to disable smart filtering
    'min_success_rate_threshold': 0.10,  # 10% - routes below this are considered "dead"
    'recent_period_hours': 24,  # Check last 24 hours for current performance
    'historical_period_days': 7,  # Check last 7 days to detect regressions
    'min_transactions_for_analysis': 10,  # Need at least 10 txns to make assessment
}

# Decline codes to EXCLUDE from alert calculations
EXCLUDED_DECLINE_CODES = [
    'F.0114',           # Insufficient funds. Failed to complete the transaction
    '39',               # Insufficient funds
    '005-39',           # Insufficient funds
    '4.01',             # Insufficient Funds
    'F.2008',           # Transaction didn't pass risk management system
]

# Decline descriptions to EXCLUDE (case-insensitive partial match)
EXCLUDED_DECLINE_DESCRIPTIONS = [
    'insufficient funds',
    'insufficient fund',
    "didn't pass risk management system",
    "did not pass risk management system",
    "risk management system",
]

# MIDs to EXCLUDE from alerts and monitoring (test/dummy MIDs)
EXCLUDED_MIDS = [
    '43110201461',  # Test MID - should not trigger alerts
]

# MID Names to EXCLUDE from alerts (case-insensitive partial match)
EXCLUDED_MID_NAMES = [
    'timesaver',    # Test MID name
    'test',         # Generic test MIDs
    'networxpay',   # Networxpay MIDs - silenced per request
]

def should_exclude_mid(mid_id, mid_name):
    """Check if a MID should be excluded from alerts"""
    # Check by MID ID
    if mid_id and mid_id in EXCLUDED_MIDS:
        return True

    # Check by MID name (case-insensitive partial match)
    if mid_name:
        mid_name_lower = mid_name.lower().strip()
        for excluded_name in EXCLUDED_MID_NAMES:
            if excluded_name in mid_name_lower:
                return True

    return False

def should_exclude_decline(reply_desc):
    """Check if a decline reason should be excluded from alerts"""
    if not reply_desc:
        return False

    reply_desc_lower = reply_desc.lower().strip()

    # Check if it matches any excluded descriptions
    for excluded in EXCLUDED_DECLINE_DESCRIPTIONS:
        if excluded in reply_desc_lower:
            return True

    return False

def check_route_health(cursor, mid_id, bank_name):
    """
    Check if a MID+Bank route is healthy enough to warrant alerts.
    Returns a dict with assessment and metrics.

    Logic:
    - If route has >10% success in last 24 hours → HEALTHY (alert on failures)
    - If route had >10% success in 7 days but <10% in 24h → REGRESSION (critical alert)
    - If route has <10% success historically → DEAD (suppress alerts)
    """

    if not SMART_FILTER_CONFIG['enabled']:
        return {'should_alert': True, 'reason': 'smart_filtering_disabled'}

    # Get transaction statistics
    cursor.execute("""
        SELECT
            COUNT(*) FILTER (WHERE status = 'success' AND last_updated_at >= NOW() - INTERVAL '%s hours') as success_24h,
            COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '%s hours') as total_24h,
            COUNT(*) FILTER (WHERE status = 'success' AND last_updated_at >= NOW() - INTERVAL '%s days') as success_7d,
            COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '%s days') as total_7d
        FROM transactions
        WHERE mid_id = %s
          AND bank_name = %s
    """, (
        SMART_FILTER_CONFIG['recent_period_hours'],
        SMART_FILTER_CONFIG['recent_period_hours'],
        SMART_FILTER_CONFIG['historical_period_days'],
        SMART_FILTER_CONFIG['historical_period_days'],
        mid_id,
        bank_name
    ))

    stats = cursor.fetchone()

    success_24h = stats['success_24h'] or 0
    total_24h = stats['total_24h'] or 0
    success_7d = stats['success_7d'] or 0
    total_7d = stats['total_7d'] or 0

    # Calculate success rates
    success_rate_24h = (success_24h / total_24h) if total_24h > 0 else 0
    success_rate_7d = (success_7d / total_7d) if total_7d > 0 else 0

    # Not enough data to assess (check 7-day history)
    if total_7d < SMART_FILTER_CONFIG['min_transactions_for_analysis']:
        return {
            'should_alert': True,
            'reason': 'insufficient_data',
            'success_rate_24h': success_rate_24h,
            'success_rate_7d': success_rate_7d,
            'success_24h': success_24h,
            'total_24h': total_24h,
            'success_7d': success_7d,
            'total_7d': total_7d
        }

    threshold = SMART_FILTER_CONFIG['min_success_rate_threshold']

    # Step 1: Route works recently (>10% success in 24 hours)
    if success_rate_24h > threshold:
        return {
            'should_alert': True,
            'reason': 'healthy_route',
            'assessment': f'Route has {success_rate_24h*100:.1f}% success (24h) - failure is unusual',
            'success_rate_24h': success_rate_24h,
            'success_rate_7d': success_rate_7d,
            'success_24h': success_24h,
            'total_24h': total_24h
        }

    # Step 2: Route worked historically (>10% in 7 days) but failing now (<10% in 24h)
    if success_rate_7d > threshold and success_rate_24h <= threshold:
        return {
            'should_alert': True,
            'reason': 'regression',
            'assessment': f'CRITICAL: Route had {success_rate_7d*100:.1f}% success (7d), now {success_rate_24h*100:.1f}% (24h)',
            'severity_upgrade': 'CRITICAL',  # Upgrade to critical
            'success_rate_24h': success_rate_24h,
            'success_rate_7d': success_rate_7d,
            'success_24h': success_24h,
            'total_24h': total_24h,
            'success_7d': success_7d,
            'total_7d': total_7d
        }

    # Step 3: Route never works (<10% success) - suppress
    return {
        'should_alert': False,
        'reason': 'dead_route',
        'assessment': f'Dead route: {success_rate_7d*100:.1f}% success (7d) - expected failure',
        'suppression_reason': 'low_success_rate' if success_7d > 0 else 'dead_route',
        'success_rate_24h': success_rate_24h,
        'success_rate_7d': success_rate_7d,
        'success_24h': success_24h,
        'total_24h': total_24h,
        'success_7d': success_7d,
        'total_7d': total_7d
    }

def check_manual_override(cursor, mid_id, bank_name):
    """
    Check if there's a manual override for this route.
    Returns dict with override decision and details.
    """
    cursor.execute("""
        SELECT
            override_action,
            reason,
            created_by,
            created_at
        FROM alert_overrides
        WHERE mid_id = %s
          AND bank_name = %s
          AND is_active = true
        ORDER BY created_at DESC
        LIMIT 1
    """, (mid_id, bank_name))

    override = cursor.fetchone()

    if not override:
        return {'has_override': False}

    return {
        'has_override': True,
        'action': override['override_action'],
        'reason': override['reason'],
        'created_by': override['created_by'],
        'created_at': override['created_at']
    }

def find_alternative_routes(cursor, bank_name, exclude_mid_id=None):
    """
    Find alternative MID+Bank routes for the same bank with better performance.
    Returns list of alternative routes sorted by success rate.
    Uses 24-hour performance window.
    """
    threshold = SMART_FILTER_CONFIG['min_success_rate_threshold']

    query = """
        WITH route_performance AS (
            SELECT
                mid_id,
                mid_name,
                COUNT(*) FILTER (WHERE status = 'success' AND last_updated_at >= NOW() - INTERVAL '24 hours') as success_24h,
                COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '24 hours') as total_24h,
                ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success' AND last_updated_at >= NOW() - INTERVAL '24 hours') /
                      NULLIF(COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '24 hours'), 0), 2) as success_rate_24h
            FROM transactions
            WHERE bank_name = %s
              AND last_updated_at >= NOW() - INTERVAL '24 hours'
              AND mid_id IS NOT NULL
    """

    if exclude_mid_id:
        query += " AND mid_id != %s"
        params = (bank_name, exclude_mid_id)
    else:
        params = (bank_name,)

    query += """
            GROUP BY mid_id, mid_name
            HAVING COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '24 hours') >= 10
        )
        SELECT
            mid_id,
            mid_name,
            success_rate_24h,
            total_24h
        FROM route_performance
        WHERE success_rate_24h > %s
        ORDER BY success_rate_24h DESC, total_24h DESC
        LIMIT 3
    """

    if exclude_mid_id:
        cursor.execute(query, params + (threshold * 100,))
    else:
        cursor.execute(query, params + (threshold * 100,))

    return cursor.fetchall()

def log_suppressed_alert(cursor, conn, mid_id, mid_name, bank_name, time_window,
                         health_check, current_decline_rate, alert_count_7d):
    """Log a suppressed alert to the suppression log table"""

    # Find alternative routes for this bank
    alternatives = find_alternative_routes(cursor, bank_name, exclude_mid_id=mid_id)

    # Build alternative routes metadata
    alternative_routes = []
    for alt in alternatives:
        alternative_routes.append({
            'mid_name': alt['mid_name'],
            'success_rate_24h': float(alt['success_rate_24h']),
            'total_24h': alt['total_24h']
        })

    try:
        # Map new field names (24h/7d) to database columns (7d/30d) for backward compatibility
        success_24h = health_check.get('success_24h', 0)
        total_24h = health_check.get('total_24h', 0)
        success_rate_24h = health_check.get('success_rate_24h', 0)
        success_rate_7d = health_check.get('success_rate_7d', 0)

        cursor.execute("""
            INSERT INTO alert_suppression_log (
                mid_id, mid_name, bank_name, suppression_reason,
                success_count_7d, declined_count_7d, total_transactions_7d,
                success_rate_7d, success_rate_30d, alert_count_7d,
                time_window, current_decline_rate, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            mid_id,
            mid_name,
            bank_name,
            health_check.get('suppression_reason', 'unknown'),
            success_24h,  # 24h stats mapped to _7d columns
            total_24h - success_24h,
            total_24h,
            round(success_rate_24h * 100, 2),  # 24h rate in _7d column
            round(success_rate_7d * 100, 2),   # 7d rate in _30d column
            alert_count_7d,
            time_window,
            current_decline_rate,
            Json({
                'assessment': health_check.get('assessment', ''),
                'reason': health_check.get('reason', ''),
                'alternative_routes': alternative_routes,
                'has_alternatives': len(alternative_routes) > 0
            })
        ))
        # Commit immediately so suppression count checks work
        conn.commit()
    except Exception as e:
        print(f"   ⚠️ Warning: Could not log suppression: {e}")

    return alternative_routes

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)

def check_recent_alert(cursor, mid_id, bank_name, minutes=30):
    """Check if we recently sent an alert for this MID+Bank combination"""
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM alert_history
        WHERE mid_id = %s
          AND bank_name = %s
          AND alert_time >= NOW() - INTERVAL '%s minutes'
    """, (mid_id, bank_name, minutes))

    result = cursor.fetchone()
    return result['count'] > 0

def log_alert(cursor, severity, time_window, mid_id, mid_name, bank_name,
              total, successful, declined, pending, success_rate, decline_rate,
              message, telegram_msg_id=None):
    """Log alert to database"""
    cursor.execute("""
        INSERT INTO alert_history (
            severity, time_window, mid_id, mid_name, bank_name,
            total_transactions, successful, declined, pending,
            success_rate, decline_rate, message, telegram_message_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (severity, time_window, mid_id, mid_name, bank_name,
          total, successful, declined, pending,
          success_rate, decline_rate, message, telegram_msg_id))

def get_decline_reasons(cursor, mid_id, bank_name, time_window):
    """Get breakdown of decline reasons for a specific MID+Bank combination"""

    # Map time window to minutes
    minutes_map = {'5min': 5, '15min': 15, '30min': 30}
    minutes = minutes_map.get(time_window, 30)

    cursor.execute("""
        SELECT
            reply_code,
            reply_desc,
            COUNT(*) as count
        FROM transactions
        WHERE mid_id = %s
          AND bank_name = %s
          AND status = 'declined'
          AND last_updated_at >= NOW() - INTERVAL '%s minutes'
        GROUP BY reply_code, reply_desc
        ORDER BY count DESC
    """, (mid_id, bank_name, minutes))

    results = cursor.fetchall()

    # Filter out excluded decline reasons (insufficient funds)
    filtered_results = [row for row in results if not should_exclude_decline(row['reply_desc'])]

    # Format as bullet points with reply code
    if not filtered_results:
        return "   • No decline reasons (all were insufficient funds or risk management)"

    reasons = [f"   • [{row['reply_code']}] {row['reply_desc']}: {row['count']}" for row in filtered_results]
    return "\n".join(reasons)

def get_merchant_breakdown(cursor, mid_id, bank_name, time_window):
    """Get breakdown of merchants affected by declines for a specific MID+Bank combination"""

    # Map time window to minutes
    minutes_map = {'5min': 5, '15min': 15, '30min': 30}
    minutes = minutes_map.get(time_window, 30)

    cursor.execute("""
        SELECT
            COALESCE(merchant_name, 'Unknown') as merchant_name,
            COUNT(*) FILTER (WHERE status = 'success') as success_count,
            COUNT(*) FILTER (WHERE status = 'declined') as declined_count,
            COUNT(*) as total_count
        FROM transactions
        WHERE mid_id = %s
          AND bank_name = %s
          AND last_updated_at >= NOW() - INTERVAL '%s minutes'
        GROUP BY merchant_name
        HAVING COUNT(*) FILTER (WHERE status = 'declined') > 0
        ORDER BY declined_count DESC, total_count DESC
        LIMIT 10
    """, (mid_id, bank_name, minutes))

    results = cursor.fetchall()

    if not results:
        return "   • No merchant data available"

    # Format as bullet points with merchant name and counts
    merchants = []
    for row in results:
        merchant = row['merchant_name']
        success = row['success_count']
        declined = row['declined_count']
        total = row['total_count']
        decline_pct = (declined / total * 100) if total > 0 else 0
        merchants.append(f"   • {merchant}: {declined}/{total} declined ({decline_pct:.1f}%)")

    return "\n".join(merchants)

def escape_html(text):
    """Escape HTML special characters for Telegram HTML mode"""
    if not text:
        return text

    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')

    return text

def send_telegram_message(message):
    """Send a plain HTML message to all configured Telegram channels"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for channel_id in TELEGRAM_CHANNEL_IDS:
        try:
            response = requests.post(url, json={
                'chat_id': channel_id,
                'text': message,
                'parse_mode': 'HTML'
            }, timeout=10)
            if not response.json().get('ok'):
                print(f"   ❌ Failed to send notification to {channel_id}: {response.json().get('description')}")
        except Exception as e:
            print(f"   ❌ Error sending notification to {channel_id}: {e}")

def send_telegram_alert(severity, time_window, mid_name, bank_name,
                       total, successful, declined, pending,
                       success_rate, decline_rate, decline_reasons, merchant_breakdown,
                       mid_id=None):
    """Send alert to Telegram channels with interactive buttons"""

    # Escape HTML special characters
    mid_name_display = escape_html(mid_name)
    bank_name_display = escape_html(bank_name)
    decline_reasons = escape_html(decline_reasons)
    merchant_breakdown = escape_html(merchant_breakdown)

    # Choose emoji based on severity
    if severity == 'CRITICAL':
        icon = '🔴'
        severity_text = '<b>CRITICAL ALERT</b>'
    elif severity == 'WARNING':
        icon = '🟡'
        severity_text = '<b>WARNING</b>'
    else:
        icon = '🔵'
        severity_text = '<b>INFO</b>'

    # Determine header text based on decline rate
    if decline_rate >= 100.0:
        header_text = '<b>⚠️ All Transactions Failing</b>'
    else:
        header_text = '<b>High Decline Rate Detected</b>'

    # Format the message in HTML
    message = f"""
{icon} {severity_text}
━━━━━━━━━━━━━━━━━━━━━
{header_text}

<b>MID:</b> {mid_name_display}
<b>Bank:</b> {bank_name_display}
<b>Window:</b> Last {time_window}
━━━━━━━━━━━━━━━━━━━━━
📊 <b>Performance:</b>
   ✅ Success: {successful} ({success_rate:.1f}%)
   ❌ Declined: {declined} ({decline_rate:.1f}%)
   ⏳ Pending: {pending}
   📈 Total: {total}
━━━━━━━━━━━━━━━━━━━━━
🔍 <b>Decline Reasons:</b>
{decline_reasons}
━━━━━━━━━━━━━━━━━━━━━
🏢 <b>Affected Merchants:</b>
{merchant_breakdown}
━━━━━━━━━━━━━━━━━━━━━
📏 <b>Alert Criteria:</b>
   ⚠️ Threshold: {THRESHOLDS[time_window]['warning_decline_rate']}% decline rate
   📉 Current: {decline_rate:.1f}% decline rate
   📊 Min Transactions: {THRESHOLDS[time_window]['min_transactions']}
   ⏱️ Window: {time_window}

ℹ️ <b>Note:</b> Insufficient funds & risk management declines are excluded from calculations

🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    message_ids = []
    success_count = 0

    # Create inline keyboard buttons if mid_id is provided
    reply_markup = None
    if mid_id:
        import json
        # Create callback data - use first 30 chars of bank name to fit in 64 byte limit
        bank_short = bank_name[:30]
        inline_keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "💡 Show Alternatives",
                        "callback_data": f"alertalt_{mid_id}_{bank_short}"
                    },
                    {
                        "text": "🔇 Suppress This Route",
                        "callback_data": f"alertsup_{mid_id}_{bank_short}"
                    }
                ]
            ]
        }
        reply_markup = json.dumps(inline_keyboard)

    # Send to all configured channels
    for channel_id in TELEGRAM_CHANNEL_IDS:
        payload = {
            'chat_id': channel_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        # Add reply_markup if we have buttons
        if reply_markup:
            payload['reply_markup'] = reply_markup

        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()

            if data.get('ok'):
                msg_id = data['result']['message_id']
                message_ids.append(msg_id)
                success_count += 1
                print(f"   ✅ Sent to channel {channel_id} (Message ID: {msg_id})")
            else:
                print(f"   ❌ Failed to send to channel {channel_id}: {data.get('description')}")
        except Exception as e:
            print(f"   ❌ Error sending to channel {channel_id}: {e}")

    # Return first message ID if any succeeded (for backward compatibility with logging)
    return message_ids[0] if message_ids else None

def check_performance_window(cursor, conn, time_window):
    """Check performance for a specific time window"""

    thresholds = THRESHOLDS[time_window]

    # Map time window to minutes
    minutes_map = {'5min': 5, '15min': 15, '30min': 30}
    minutes = minutes_map.get(time_window, 30)

    # Get raw transaction data to recalculate excluding insufficient funds
    cursor.execute("""
        SELECT
            mid_id,
            mid_name,
            bank_name,
            COUNT(*) as total_transactions,
            COUNT(*) FILTER (WHERE status = 'success') as successful,
            COUNT(*) FILTER (WHERE status = 'declined') as total_declined,
            COUNT(*) FILTER (WHERE status = 'pending') as pending,
            ARRAY_AGG(reply_desc) FILTER (WHERE status = 'declined') as decline_descriptions
        FROM transactions
        WHERE last_updated_at >= NOW() - INTERVAL %s
          AND mid_id IS NOT NULL
          AND bank_name IS NOT NULL
        GROUP BY mid_id, mid_name, bank_name
        HAVING COUNT(*) >= %s
    """, (f'{minutes} minutes', thresholds['min_transactions'],))

    results = cursor.fetchall()
    alerts_sent = 0

    for row in results:
        mid_id = row['mid_id']
        mid_name = row['mid_name']
        bank_name = row['bank_name']
        total = row['total_transactions']
        successful = row['successful']
        total_declined = row['total_declined']
        pending = row['pending']
        decline_descriptions = row['decline_descriptions'] or []

        # Skip excluded MIDs (test/dummy MIDs)
        if should_exclude_mid(mid_id, mid_name):
            print(f"⏭️  Skipping excluded MID: {mid_name} ({mid_id})")
            continue

        # Count how many declines should be excluded (insufficient funds)
        excluded_declines = sum(1 for desc in decline_descriptions if should_exclude_decline(desc))

        # Recalculate declined count excluding insufficient funds
        declined = total_declined - excluded_declines

        # Recalculate rates excluding insufficient funds declines
        completed_transactions = successful + declined  # Exclude pending and excluded declines

        if completed_transactions == 0:
            continue  # Skip if no completed non-excluded transactions

        success_rate = (successful / completed_transactions) * 100
        decline_rate = (declined / completed_transactions) * 100

        # Only alert if decline rate (excluding insufficient funds) meets threshold
        if decline_rate < thresholds['warning_decline_rate']:
            continue

        # MANUAL OVERRIDE CHECK: Check if user manually overrode this route (check BEFORE cooldown)
        manual_override = check_manual_override(cursor, mid_id, bank_name)

        if manual_override['has_override'] and manual_override['action'] == 'suppress':
            # User manually suppressed this route - but check if it has recovered
            health_check = check_route_health(cursor, mid_id, bank_name)

            if health_check.get('should_alert') and health_check.get('reason') == 'healthy_route':
                # Route has recovered! Auto-remove the manual suppression
                print(f"✅ AUTO-RECOVERY: {mid_name} + {bank_name}")
                print(f"   Route recovered: {health_check.get('success_rate_24h', 0)*100:.1f}% success (24h)")
                print(f"   Removing manual suppression (was set by: {manual_override['created_by']})")

                # Deactivate the manual override
                cursor.execute("""
                    UPDATE alert_overrides
                    SET is_active = false,
                        updated_at = NOW()
                    WHERE mid_id = %s
                      AND bank_name = %s
                      AND override_action = 'suppress'
                      AND is_active = true
                """, (mid_id, bank_name))
                conn.commit()

                # Continue with normal alert flow (will go through smart filter below)
            else:
                # Route still unhealthy, keep suppression active
                print(f"🔇 MANUAL SUPPRESS: {mid_name} + {bank_name}")
                print(f"   Reason: {manual_override['reason']}")
                print(f"   By: {manual_override['created_by']}")
                continue  # Skip alert due to manual suppression

        # Check if we recently alerted for this combination
        if check_recent_alert(cursor, mid_id, bank_name, COOLDOWN_MINUTES):
            print(f"⏭️  Skipping alert for {mid_name} + {bank_name} (cooldown active)")
            continue

        # Check if manual override has force_alert action
        if manual_override['has_override'] and manual_override['action'] == 'force_alert':
            # User wants alerts even if route is unhealthy
            print(f"🔔 MANUAL FORCE ALERT: {mid_name} + {bank_name}")
            print(f"   Reason: {manual_override['reason']}")
            print(f"   By: {manual_override['created_by']}")
            # Continue to send alert (skip smart filter check)
            severity = 'CRITICAL'  # Force as critical
            health_check = {'should_alert': True, 'reason': 'manual_force'}
        else:
            # No manual override (or already handled suppress above), check smart filter
            # SMART FILTERING: Check if this route is healthy enough to alert
            health_check = check_route_health(cursor, mid_id, bank_name)

        if not health_check['should_alert']:
            # Route is dead/unhealthy - suppress alert
            print(f"🔇 SUPPRESSED: {mid_name} + {bank_name} - {health_check['assessment']}")

            # Get recent alert count for logging
            cursor.execute("""
                SELECT COUNT(*) as count FROM alert_history
                WHERE mid_id = %s AND bank_name = %s
                  AND alert_time >= NOW() - INTERVAL '7 days'
            """, (mid_id, bank_name))
            alert_count_7d = cursor.fetchone()['count']

            # Log the suppression and find alternatives
            alternatives = log_suppressed_alert(
                cursor, conn, mid_id, mid_name, bank_name, time_window,
                health_check, decline_rate, alert_count_7d
            )

            # Display alternative routes if available
            if alternatives:
                print(f"   💡 Alternative routes for {bank_name[:40]}:")
                for alt in alternatives:
                    print(f"      → {alt['mid_name']}: {alt['success_rate_24h']:.1f}% success ({alt['total_24h']} txns in 24h)")
            else:
                print(f"   ⚠️  No alternative routes available for this bank")

            # Send Telegram notification for auto-suppression (once per day per route)
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM alert_suppression_log
                WHERE mid_id = %s
                  AND bank_name = %s
                  AND suppression_time >= NOW() - INTERVAL '24 hours'
            """, (mid_id, bank_name))

            recent_suppression_count = cursor.fetchone()['count']

            # Only notify once per day per route
            if recent_suppression_count == 1:  # First suppression in 24h
                success_24h = health_check.get('success_rate_24h', 0) * 100
                success_7d = health_check.get('success_rate_7d', 0) * 100

                # Build notification message
                notification = f"🔇 <b>AUTO-SUPPRESSED ALERT</b>\n\n"
                notification += f"<b>Route:</b> {mid_name}\n"
                notification += f"<b>Bank:</b> {bank_name[:60]}\n\n"
                notification += f"<b>Reason:</b> {health_check.get('assessment', 'Dead route')}\n\n"
                notification += f"📊 <b>Performance:</b>\n"
                notification += f"  • Last 24h: {success_24h:.1f}% success\n"
                notification += f"  • Last 7d: {success_7d:.1f}% success\n"
                notification += f"  • Decline rate: {decline_rate:.1f}%\n\n"

                if alternatives:
                    notification += f"💡 <b>Alternative Routes:</b>\n"
                    for alt in alternatives[:3]:
                        notification += f"  • {alt['mid_name']}: {alt['success_rate_24h']:.1f}% success\n"
                else:
                    notification += f"⚠️ No alternative routes available\n\n"

                notification += f"\n<i>This route will not trigger alerts until performance improves.</i>"

                # Send to Telegram
                send_telegram_message(notification)
                print(f"   📤 Auto-suppression notification sent to Telegram")

            continue

        # Determine severity
        if decline_rate >= thresholds['critical_decline_rate']:
            severity = 'CRITICAL'
        else:
            severity = 'WARNING'

        # Upgrade severity if this is a regression (route used to work)
        if health_check.get('severity_upgrade') == 'CRITICAL':
            severity = 'CRITICAL'
            regression_note = f" [REGRESSION: was {health_check['success_rate_7d']*100:.1f}% success (7d)]"
        else:
            regression_note = ""

        excluded_note = f" (excluded {excluded_declines} insufficient funds)" if excluded_declines > 0 else ""
        print(f"{severity}: {mid_name} + {bank_name} - {decline_rate:.1f}% decline rate in {time_window}{excluded_note}{regression_note}")

        # Get decline reasons breakdown
        decline_reasons = get_decline_reasons(cursor, mid_id, bank_name, time_window)

        # Get merchant breakdown
        merchant_breakdown = get_merchant_breakdown(cursor, mid_id, bank_name, time_window)

        # Send Telegram alert
        telegram_msg_id = send_telegram_alert(
            severity, time_window, mid_name, bank_name,
            total, successful, declined, pending,
            success_rate, decline_rate, decline_reasons, merchant_breakdown,
            mid_id=mid_id
        )

        if telegram_msg_id:
            # Log alert to database
            log_alert(
                cursor, severity, time_window, mid_id, mid_name, bank_name,
                total, successful, declined, pending,
                success_rate, decline_rate,
                f"Decline rate {decline_rate:.1f}% exceeded threshold",
                telegram_msg_id
            )
            # Commit immediately so cooldown checks can see this alert
            conn.commit()
            alerts_sent += 1
            print(f"   ✅ Alert sent (Message ID: {telegram_msg_id})")
        else:
            print(f"   ❌ Failed to send alert")

    return alerts_sent

def check_low_volume_failures(cursor, conn, time_window):
    """
    Check for MID + Bank combinations with complete failures (5min window only)
    Alert if:
    - More than 0 but less than 8 transactions in last 5 minutes
    - AND all of the last 10 transactions overall are declined
    """

    # Only check this for 5min window
    if time_window != '5min':
        return 0

    query = """
    -- Find MID + Bank combinations with > 0 and < 8 transactions in 5-min window
    WITH recent_low_volume AS (
        SELECT
            mid_id,
            bank_name,
            COUNT(*) as recent_count
        FROM transactions
        WHERE last_updated_at >= NOW() - INTERVAL '5 minutes'
            AND mid_id IS NOT NULL
            AND bank_name IS NOT NULL
        GROUP BY mid_id, bank_name
        HAVING COUNT(*) > 0 AND COUNT(*) < 8
    ),
    -- For those combinations, get last 10 transactions (exclude customer-related errors)
    last_10_per_combination AS (
        SELECT
            t.mid_id,
            t.mid_name,
            t.bank_name,
            t.status,
            t.reply_code,
            t.reply_desc,
            t.last_updated_at,
            ROW_NUMBER() OVER (PARTITION BY t.mid_id, t.bank_name ORDER BY t.last_updated_at DESC) as rn
        FROM transactions t
        INNER JOIN recent_low_volume rlv ON t.mid_id = rlv.mid_id AND t.bank_name = rlv.bank_name
        WHERE t.mid_id IS NOT NULL
            AND t.bank_name IS NOT NULL
            -- Exclude customer-related errors
            AND (t.status != 'declined' OR (
                t.reply_code NOT IN ('111', 'F.0114', '39', '4', '005-4', 'F.0111', '510', '005', '005-39', '4.01', '005-42')
                AND t.reply_desc NOT ILIKE '%insufficient fund%'
                AND t.reply_desc NOT ILIKE '%didn''t pass risk management%'
                AND t.reply_desc NOT ILIKE '%did not pass risk management%'
                AND t.reply_desc NOT ILIKE '%risk management system%'
            ))
    ),
    -- Check if all 10 are declined
    all_declined_check AS (
        SELECT
            mid_id,
            mid_name,
            bank_name,
            COUNT(*) as last_10_count,
            COUNT(*) FILTER (WHERE status = 'declined') as declined_count,
            COUNT(*) FILTER (WHERE status = 'success') as success_count
        FROM last_10_per_combination
        WHERE rn <= 10
        GROUP BY mid_id, mid_name, bank_name
    )
    -- Alert if all 10 are declined (excluding customer errors)
    SELECT
        adc.mid_id,
        adc.mid_name,
        adc.bank_name,
        rlv.recent_count as transactions_in_5min,
        adc.last_10_count,
        adc.declined_count,
        adc.success_count
    FROM all_declined_check adc
    INNER JOIN recent_low_volume rlv ON adc.mid_id = rlv.mid_id AND adc.bank_name = rlv.bank_name
    WHERE adc.last_10_count = 10
        AND adc.declined_count = 10
        AND adc.success_count = 0
    ORDER BY rlv.recent_count DESC
    """

    cursor.execute(query)
    results = cursor.fetchall()
    alerts_sent = 0

    for row in results:
        mid_id = row['mid_id']
        mid_name = row['mid_name']
        bank_name = row['bank_name']
        txns_in_5min = row['transactions_in_5min']
        last_10_count = row['last_10_count']
        declined_count = row['declined_count']

        # Skip excluded MIDs (test/dummy MIDs)
        if should_exclude_mid(mid_id, mid_name):
            print(f"⏭️  Skipping excluded MID in low-volume check: {mid_name} ({mid_id})")
            continue

        # Escape HTML special characters
        mid_name_escaped = escape_html(mid_name)
        bank_name_escaped = escape_html(bank_name)

        # MANUAL OVERRIDE CHECK: Check if user manually overrode this route (check BEFORE cooldown)
        manual_override = check_manual_override(cursor, mid_id, bank_name)

        if manual_override['has_override'] and manual_override['action'] == 'suppress':
            # User manually suppressed this route - but check if it has recovered
            health_check = check_route_health(cursor, mid_id, bank_name)

            if health_check.get('should_alert') and health_check.get('reason') == 'healthy_route':
                # Route has recovered! Auto-remove the manual suppression
                print(f"✅ AUTO-RECOVERY (low-volume): {mid_name} + {bank_name}")
                print(f"   Route recovered: {health_check.get('success_rate_24h', 0)*100:.1f}% success (24h)")
                print(f"   Removing manual suppression (was set by: {manual_override['created_by']})")

                # Deactivate the manual override
                cursor.execute("""
                    UPDATE alert_overrides
                    SET is_active = false,
                        updated_at = NOW()
                    WHERE mid_id = %s
                      AND bank_name = %s
                      AND override_action = 'suppress'
                      AND is_active = true
                """, (mid_id, bank_name))
                conn.commit()

                # Continue with normal alert flow (will go through smart filter below)
            else:
                # Route still unhealthy, keep suppression active
                print(f"🔇 MANUAL SUPPRESS (low-volume): {mid_name} + {bank_name}")
                print(f"   Reason: {manual_override['reason']}")
                print(f"   By: {manual_override['created_by']}")
                continue  # Skip alert due to manual suppression

        # Check cooldown (reuse existing alert_history table)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM alert_history
            WHERE mid_id = %s
              AND bank_name = %s
              AND message LIKE %s
              AND alert_time >= NOW() - INTERVAL '1440 minutes'
        """, (mid_id, bank_name, f"%Low Volume Complete Failure%"))

        cooldown_check = cursor.fetchone()
        if cooldown_check['count'] > 0:
            print(f"⏭️  Skipping low-volume alert for MID {mid_name} + {bank_name} (cooldown active)")
            continue

        # Check if manual override has force_alert action
        if manual_override['has_override'] and manual_override['action'] == 'force_alert':
            print(f"🔔 MANUAL FORCE ALERT (low-volume): {mid_name} + {bank_name}")
            # Continue to send alert
            health_check = {'should_alert': True, 'reason': 'manual_force'}
        else:
            # No manual override (or already handled suppress above), check smart filter
            # SMART FILTERING: Check if this route is healthy enough to alert
            health_check = check_route_health(cursor, mid_id, bank_name)

        if not health_check['should_alert']:
            # Route is dead/unhealthy - suppress alert
            print(f"🔇 SUPPRESSED (low-volume): {mid_name} + {bank_name} - {health_check['assessment']}")

            # Get recent alert count for logging
            cursor.execute("""
                SELECT COUNT(*) as count FROM alert_history
                WHERE mid_id = %s AND bank_name = %s
                  AND alert_time >= NOW() - INTERVAL '7 days'
            """, (mid_id, bank_name))
            alert_count_7d = cursor.fetchone()['count']

            # Log the suppression and find alternatives
            alternatives = log_suppressed_alert(
                cursor, conn, mid_id, mid_name, bank_name, '5min',
                health_check, 100.0, alert_count_7d  # 100% decline rate for low-volume
            )

            # Display alternative routes if available
            if alternatives:
                print(f"   💡 Alternative routes for {bank_name[:40]}:")
                for alt in alternatives:
                    print(f"      → {alt['mid_name']}: {alt['success_rate_24h']:.1f}% success ({alt['total_24h']} txns in 24h)")
            else:
                print(f"   ⚠️  No alternative routes available for this bank")

            # Send Telegram notification for auto-suppression (once per day per route)
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM alert_suppression_log
                WHERE mid_id = %s
                  AND bank_name = %s
                  AND suppression_time >= NOW() - INTERVAL '24 hours'
            """, (mid_id, bank_name))

            recent_suppression_count = cursor.fetchone()['count']

            # Only notify once per day per route
            if recent_suppression_count == 1:  # First suppression in 24h
                success_24h = health_check.get('success_rate_24h', 0) * 100
                success_7d = health_check.get('success_rate_7d', 0) * 100

                # Build notification message
                notification = f"🔇 <b>AUTO-SUPPRESSED ALERT (Low Volume)</b>\n\n"
                notification += f"<b>Route:</b> {mid_name}\n"
                notification += f"<b>Bank:</b> {bank_name[:60]}\n\n"
                notification += f"<b>Reason:</b> {health_check.get('assessment', 'Dead route')}\n\n"
                notification += f"📊 <b>Performance:</b>\n"
                notification += f"  • Last 24h: {success_24h:.1f}% success\n"
                notification += f"  • Last 7d: {success_7d:.1f}% success\n"
                notification += f"  • All last 10 transactions declined\n\n"

                if alternatives:
                    notification += f"💡 <b>Alternative Routes:</b>\n"
                    for alt in alternatives[:3]:
                        notification += f"  • {alt['mid_name']}: {alt['success_rate_24h']:.1f}% success\n"
                else:
                    notification += f"⚠️ No alternative routes available\n\n"

                notification += f"\n<i>This route will not trigger alerts until performance improves.</i>"

                # Send to Telegram
                send_telegram_message(notification)
                print(f"   📤 Auto-suppression notification sent to Telegram")

            continue

        print(f"🔴 CRITICAL: MID {mid_name} + {bank_name} - All last 10 transactions DECLINED (low volume)!")

        # Get decline reasons for last 10 transactions (excluding customer errors)
        cursor.execute("""
            WITH last_10_declined AS (
                SELECT
                    reply_code,
                    reply_desc
                FROM transactions
                WHERE mid_id = %s
                  AND bank_name = %s
                  AND status = 'declined'
                  AND reply_code NOT IN ('111', 'F.0114', '39', '4', '005-4', 'F.0111', '510', '005', '005-39', '4.01', '005-42')
                  AND reply_desc NOT ILIKE '%%insufficient fund%%'
                  AND reply_desc NOT ILIKE '%%didn''t pass risk management%%'
                  AND reply_desc NOT ILIKE '%%did not pass risk management%%'
                  AND reply_desc NOT ILIKE '%%risk management system%%'
                ORDER BY last_updated_at DESC
                LIMIT 10
            )
            SELECT
                reply_code,
                reply_desc,
                COUNT(*) as count
            FROM last_10_declined
            GROUP BY reply_code, reply_desc
            ORDER BY count DESC
        """, (mid_id, bank_name))

        decline_reasons_rows = cursor.fetchall()
        if decline_reasons_rows:
            decline_reasons_text = "\n".join([
                f"   • [{escape_html(row['reply_code'])}] {escape_html(row['reply_desc'])}: {row['count']}"
                for row in decline_reasons_rows
            ])
        else:
            decline_reasons_text = "   • No decline reasons available"

        # Get merchant breakdown for this alert (using last 10 overall transactions)
        cursor.execute("""
            SELECT
                COALESCE(merchant_name, 'Unknown') as merchant_name,
                COUNT(*) FILTER (WHERE status = 'success') as success_count,
                COUNT(*) FILTER (WHERE status = 'declined') as declined_count,
                COUNT(*) as total_count
            FROM (
                SELECT merchant_name, status
                FROM transactions
                WHERE mid_id = %s
                  AND bank_name = %s
                ORDER BY last_updated_at DESC
                LIMIT 10
            ) recent_txns
            GROUP BY merchant_name
            ORDER BY declined_count DESC, total_count DESC
        """, (mid_id, bank_name))

        merchant_rows = cursor.fetchall()
        if merchant_rows:
            merchant_text = "\n".join([
                f"   • {escape_html(row['merchant_name'])}: {row['declined_count']}/{row['total_count']} declined"
                for row in merchant_rows
                if row['declined_count'] > 0
            ])
            if not merchant_text:
                merchant_text = "   • No merchant data available"
        else:
            merchant_text = "   • No merchant data available"

        # Send Telegram alert in HTML format
        message = f"""
🔴 <b>CRITICAL ALERT - Low Volume Complete Failure</b>
━━━━━━━━━━━━━━━━━━━━━
<b>⚠️ All Transactions Failing</b>

<b>MID:</b> {mid_name_escaped}
<b>Bank:</b> {bank_name_escaped}
<b>Window:</b> Last 5 minutes
━━━━━━━━━━━━━━━━━━━━━
📊 <b>Status:</b>
   🔴 Last 10 Transactions: <b>ALL DECLINED</b>
   📉 Recent Volume: {txns_in_5min} transactions in 5min
   ⚠️ Success Rate: <b>0%</b>
━━━━━━━━━━━━━━━━━━━━━
🔍 <b>Decline Reasons:</b>
{decline_reasons_text}
━━━━━━━━━━━━━━━━━━━━━
🏢 <b>Affected Merchants:</b>
{merchant_text}
━━━━━━━━━━━━━━━━━━━━━
⚡ <b>Action Required:</b>
   This MID + Bank combination has low volume but
   all recent transactions are failing.
   Immediate investigation needed!

ℹ️ <b>Note:</b> Insufficient funds & risk management declines are excluded from calculations

🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

        # Create inline keyboard buttons
        import json
        bank_short = bank_name[:30]
        inline_keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "💡 Show Alternatives",
                        "callback_data": f"alertalt_{mid_id}_{bank_short}"
                    },
                    {
                        "text": "🔇 Suppress This Route",
                        "callback_data": f"alertsup_{mid_id}_{bank_short}"
                    }
                ]
            ]
        }
        reply_markup = json.dumps(inline_keyboard)

        message_ids = []
        for channel_id in TELEGRAM_CHANNEL_IDS:
            payload = {
                'chat_id': channel_id,
                'text': message,
                'parse_mode': 'HTML',
                'reply_markup': reply_markup
            }

            try:
                response = requests.post(url, json=payload, timeout=10)
                data = response.json()

                if data.get('ok'):
                    msg_id = data['result']['message_id']
                    message_ids.append(msg_id)
                    print(f"   ✅ Sent to channel {channel_id} (Message ID: {msg_id})")
                else:
                    print(f"   ❌ Failed to send to channel {channel_id}: {data.get('description')}")
            except Exception as e:
                print(f"   ❌ Error sending to channel {channel_id}: {e}")

        if message_ids:
            # Log to database
            cursor.execute("""
                INSERT INTO alert_history (
                    severity, time_window, mid_id, mid_name, bank_name,
                    total_transactions, successful, declined, pending,
                    success_rate, decline_rate, message, telegram_message_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ('CRITICAL', '5min', mid_id, mid_name, bank_name,
                  last_10_count, 0, declined_count, 0, 0.0, 100.0,
                  f"Low Volume Complete Failure: {mid_name} + {bank_name}: All last 10 transactions declined",
                  message_ids[0]))
            # Commit immediately so next cooldown check can see this alert
            conn.commit()
            alerts_sent += 1
            print(f"   ✅ Low-volume MID+Bank alert sent and logged")

    return alerts_sent

def main():
    """Main monitoring function"""
    print("=" * 60)
    print("Payment Gateway Performance Monitor")
    print(f"Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Alert channels: {len(TELEGRAM_CHANNEL_IDS)} configured")
    print("=" * 60)

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_IDS:
        print("❌ Error: Telegram credentials not configured in .env file")
        sys.exit(1)

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        total_alerts = 0

        # Check each time window
        for time_window in ['5min', '15min', '30min']:
            print(f"\n🔍 Checking {time_window} window...")
            alerts = check_performance_window(cursor, conn, time_window)
            total_alerts += alerts
            print(f"   Alerts sent: {alerts}")

            # For 5min window, also check low-volume complete failures
            if time_window == '5min':
                print(f"\n🔍 Checking low-volume complete failures...")
                low_vol_alerts = check_low_volume_failures(cursor, conn, time_window)
                total_alerts += low_vol_alerts
                print(f"   Low-volume alerts sent: {low_vol_alerts}")

        # All alerts already committed individually
        # Final commit for any remaining changes (suppression logs, etc.)
        conn.commit()

        print("\n" + "=" * 60)
        print(f"✅ Monitoring complete: {total_alerts} alerts sent")
        print("=" * 60)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ Error during monitoring: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
