#!/usr/bin/env python3
"""
Payment Gateway Performance Monitor
Monitors MID + Bank performance and sends Telegram alerts
"""

import psycopg2
from psycopg2.extras import RealDictCursor
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

def send_telegram_alert(severity, time_window, mid_name, bank_name,
                       total, successful, declined, pending,
                       success_rate, decline_rate, decline_reasons, merchant_breakdown):
    """Send alert to Telegram channels"""

    # Escape HTML special characters
    mid_name = escape_html(mid_name)
    bank_name = escape_html(bank_name)
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

<b>MID:</b> {mid_name}
<b>Bank:</b> {bank_name}
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

    # Send to all configured channels
    for channel_id in TELEGRAM_CHANNEL_IDS:
        payload = {
            'chat_id': channel_id,
            'text': message,
            'parse_mode': 'HTML'
        }

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

def check_performance_window(cursor, time_window):
    """Check performance for a specific time window"""

    thresholds = THRESHOLDS[time_window]

    # Map time window to minutes
    minutes_map = {'5min': 5, '15min': 15, '30min': 30}
    minutes = minutes_map.get(time_window, 30)

    # Get raw transaction data to recalculate excluding insufficient funds
    cursor.execute(f"""
        SELECT
            mid_id,
            mid_name,
            bank_name,
            COUNT(*) as total_transactions,
            COUNT(*) FILTER (WHERE status = 'success') as successful,
            COUNT(*) FILTER (WHERE status = 'declined') as total_declined,
            COUNT(*) FILTER (WHERE status = 'pending') as pending,
            -- Get declined transactions with their descriptions
            ARRAY_AGG(reply_desc) FILTER (WHERE status = 'declined') as decline_descriptions
        FROM transactions
        WHERE last_updated_at >= NOW() - INTERVAL '{minutes} minutes'
          AND mid_id IS NOT NULL
          AND bank_name IS NOT NULL
        GROUP BY mid_id, mid_name, bank_name
        HAVING COUNT(*) >= %s
    """, (thresholds['min_transactions'],))

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

        # Check if we recently alerted for this combination
        if check_recent_alert(cursor, mid_id, bank_name, COOLDOWN_MINUTES):
            print(f"⏭️  Skipping alert for {mid_name} + {bank_name} (cooldown active)")
            continue

        # Determine severity
        if decline_rate >= thresholds['critical_decline_rate']:
            severity = 'CRITICAL'
        else:
            severity = 'WARNING'

        excluded_note = f" (excluded {excluded_declines} insufficient funds)" if excluded_declines > 0 else ""
        print(f"{severity}: {mid_name} + {bank_name} - {decline_rate:.1f}% decline rate in {time_window}{excluded_note}")

        # Get decline reasons breakdown
        decline_reasons = get_decline_reasons(cursor, mid_id, bank_name, time_window)

        # Get merchant breakdown
        merchant_breakdown = get_merchant_breakdown(cursor, mid_id, bank_name, time_window)

        # Send Telegram alert
        telegram_msg_id = send_telegram_alert(
            severity, time_window, mid_name, bank_name,
            total, successful, declined, pending,
            success_rate, decline_rate, decline_reasons, merchant_breakdown
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
            alerts_sent += 1
            print(f"   ✅ Alert sent (Message ID: {telegram_msg_id})")
        else:
            print(f"   ❌ Failed to send alert")

    return alerts_sent

def check_low_volume_failures(cursor, time_window):
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

        # Escape HTML special characters
        mid_name_escaped = escape_html(mid_name)
        bank_name_escaped = escape_html(bank_name)

        # Check cooldown (reuse existing alert_history table)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM alert_history
            WHERE mid_id = %s
              AND bank_name = %s
              AND message LIKE %s
              AND alert_time >= NOW() - INTERVAL '30 minutes'
        """, (mid_id, bank_name, f"%Low Volume Complete Failure%"))

        cooldown_check = cursor.fetchone()
        if cooldown_check['count'] > 0:
            print(f"⏭️  Skipping low-volume alert for MID {mid_name} + {bank_name} (cooldown active)")
            continue

        print(f"🔴 CRITICAL: MID {mid_name} + {bank_name} - All last 10 transactions DECLINED (low volume)!")

        # Get decline reasons for last 10 transactions (excluding customer errors)
        cursor.execute("""
            SELECT
                reply_code,
                reply_desc,
                COUNT(*) as count
            FROM transactions
            WHERE mid_id = %s
              AND bank_name = %s
              AND status = 'declined'
              AND reply_code NOT IN ('111', 'F.0114', '39', '4', '005-4', 'F.0111', '510', '005', '005-39', '4.01', '005-42')
              AND reply_desc NOT ILIKE '%%insufficient fund%%'
              AND reply_desc NOT ILIKE '%%didn''t pass risk management%%'
              AND reply_desc NOT ILIKE '%%did not pass risk management%%'
              AND reply_desc NOT ILIKE '%%risk management system%%'
            GROUP BY reply_code, reply_desc
            ORDER BY count DESC
            LIMIT 10
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

        message_ids = []
        for channel_id in TELEGRAM_CHANNEL_IDS:
            payload = {
                'chat_id': channel_id,
                'text': message,
                'parse_mode': 'HTML'
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
            alerts = check_performance_window(cursor, time_window)
            total_alerts += alerts
            print(f"   Alerts sent: {alerts}")

            # For 5min window, also check low-volume complete failures
            if time_window == '5min':
                print(f"\n🔍 Checking low-volume complete failures...")
                low_vol_alerts = check_low_volume_failures(cursor, time_window)
                total_alerts += low_vol_alerts
                print(f"   Low-volume alerts sent: {low_vol_alerts}")

        # Commit alert logs
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
