#!/usr/bin/env python3
"""
Payment Alert Daily Summary Report
Generates and sends daily summary of payment alerts via Telegram
"""

import os
import sys
import psycopg2
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'payment_transactions'),
    'user': os.getenv('DB_USER', 'webhook_user'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

def get_db_connection():
    """Create and return database connection"""
    return psycopg2.connect(**DB_CONFIG)

def send_telegram_message(message, parse_mode='HTML'):
    """Send message to Telegram channel"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Split message if it's too long (Telegram limit is 4096 chars)
    max_length = 4000  # Leave some buffer
    messages = []

    if len(message) <= max_length:
        messages = [message]
    else:
        # Split by sections (separated by lines of ━)
        sections = message.split('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')
        current_msg = ""

        for section in sections:
            if len(current_msg) + len(section) + 50 < max_length:
                current_msg += section + '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
            else:
                if current_msg:
                    messages.append(current_msg)
                current_msg = section + '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'

        if current_msg:
            messages.append(current_msg)

    # Send each message part
    for i, msg in enumerate(messages):
        if i > 0:
            msg = f"<b>📊 Daily Report (Part {i+1}/{len(messages)})</b>\n\n" + msg

        payload = {
            'chat_id': TELEGRAM_CHANNEL_ID,
            'text': msg,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"Error sending Telegram message (part {i+1}): {e}")
            return False

    return True

def generate_bar_chart(value, max_value, width=20):
    """Generate a simple text-based bar chart"""
    if max_value == 0:
        return '░' * width

    filled = int((value / max_value) * width)
    return '▓' * filled + '░' * (width - filled)

def get_alert_summary(cursor, start_date, end_date):
    """Get summary statistics for alerts in date range"""
    query = """
        SELECT
            COUNT(*) as total_alerts,
            COUNT(*) FILTER (WHERE severity = 'CRITICAL') as critical_count,
            COUNT(*) FILTER (WHERE severity = 'WARNING') as warning_count,
            COUNT(DISTINCT mid_name || ' + ' || bank_name) as unique_routes,
            COUNT(DISTINCT mid_name) as unique_mids,
            COUNT(DISTINCT bank_name) as unique_banks
        FROM alert_history
        WHERE alert_time >= %s AND alert_time < %s
    """
    cursor.execute(query, (start_date, end_date))
    return cursor.fetchone()

def get_top_problematic_routes(cursor, start_date, end_date, limit=10):
    """Get top problematic MID+Bank routes"""
    query = """
        SELECT
            mid_name,
            bank_name,
            COUNT(*) as alert_count,
            COUNT(*) FILTER (WHERE severity = 'CRITICAL') as critical,
            COUNT(*) FILTER (WHERE severity = 'WARNING') as warning,
            ROUND(AVG(decline_rate), 2) as avg_decline_rate,
            SUM(total_transactions) as total_txns,
            SUM(declined) as total_declined,
            SUM(successful) as total_successful
        FROM alert_history
        WHERE alert_time >= %s AND alert_time < %s
        GROUP BY mid_name, bank_name
        ORDER BY alert_count DESC, avg_decline_rate DESC
        LIMIT %s
    """
    cursor.execute(query, (start_date, end_date, limit))
    return cursor.fetchall()

def get_time_window_breakdown(cursor, start_date, end_date):
    """Get alert breakdown by time window"""
    query = """
        SELECT
            time_window,
            COUNT(*) as count
        FROM alert_history
        WHERE alert_time >= %s AND alert_time < %s
        GROUP BY time_window
        ORDER BY
            CASE time_window
                WHEN '5min' THEN 1
                WHEN '15min' THEN 2
                WHEN '30min' THEN 3
            END
    """
    cursor.execute(query, (start_date, end_date))
    return cursor.fetchall()

def get_top_banks(cursor, start_date, end_date, limit=5):
    """Get top affected banks"""
    query = """
        SELECT
            bank_name,
            COUNT(*) as alert_count,
            COUNT(DISTINCT mid_name) as affected_mids
        FROM alert_history
        WHERE alert_time >= %s AND alert_time < %s
        GROUP BY bank_name
        ORDER BY alert_count DESC
        LIMIT %s
    """
    cursor.execute(query, (start_date, end_date, limit))
    return cursor.fetchall()

def get_top_mids(cursor, start_date, end_date, limit=5):
    """Get top affected MIDs"""
    query = """
        SELECT
            mid_name,
            COUNT(*) as alert_count,
            COUNT(DISTINCT bank_name) as affected_banks
        FROM alert_history
        WHERE alert_time >= %s AND alert_time < %s
        GROUP BY mid_name
        ORDER BY alert_count DESC
        LIMIT %s
    """
    cursor.execute(query, (start_date, end_date, limit))
    return cursor.fetchall()

def get_trend_data(cursor, days=7):
    """Get trend data for the last N days"""
    query = """
        SELECT
            DATE(alert_time) as date,
            COUNT(*) as alerts
        FROM alert_history
        WHERE alert_time >= CURRENT_DATE - INTERVAL '%s days'
        GROUP BY DATE(alert_time)
        ORDER BY date DESC
    """
    cursor.execute(query, (days,))
    return cursor.fetchall()

def format_number(num):
    """Format number with commas"""
    if num is None:
        return "0"
    return f"{int(num):,}"

def generate_daily_report():
    """Generate and send daily alert report"""

    # Calculate date range (yesterday full day)
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=1)

    # For display
    report_date = start_date.strftime('%B %d, %Y')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Gather all data
        summary = get_alert_summary(cursor, start_date, end_date)
        top_routes = get_top_problematic_routes(cursor, start_date, end_date)
        time_windows = get_time_window_breakdown(cursor, start_date, end_date)
        top_banks = get_top_banks(cursor, start_date, end_date)
        top_mids = get_top_mids(cursor, start_date, end_date)
        trend_data = get_trend_data(cursor, days=7)

        # Unpack summary
        total_alerts, critical_count, warning_count, unique_routes, unique_mids, unique_banks = summary

        # Calculate percentages
        critical_pct = (critical_count / total_alerts * 100) if total_alerts > 0 else 0
        warning_pct = (warning_count / total_alerts * 100) if total_alerts > 0 else 0

        # Calculate trend comparison
        yesterday_alerts = trend_data[1][1] if len(trend_data) > 1 else 0
        trend_diff = total_alerts - yesterday_alerts
        trend_pct = (trend_diff / yesterday_alerts * 100) if yesterday_alerts > 0 else 0
        trend_emoji = "📉" if trend_diff < 0 else "📈" if trend_diff > 0 else "➡️"
        trend_text = "Improvement" if trend_diff < 0 else "Increase" if trend_diff > 0 else "Unchanged"

        # Calculate 7-day average
        total_7day = sum([row[1] for row in trend_data])
        avg_7day = total_7day / len(trend_data) if trend_data else 0
        avg_position_pct = ((total_alerts - avg_7day) / avg_7day * 100) if avg_7day > 0 else 0
        avg_emoji = "✅" if avg_position_pct < 0 else "⚠️"

        # Build report
        report = f"""🤖 <b>PolpayMonitor Daily Summary Report</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 <b>Report Period:</b> {report_date}
🕐 <b>Time Range:</b> 00:00 - 23:59 UTC

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>EXECUTIVE SUMMARY</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• <b>Total Alerts:</b> {total_alerts}
• 🔴 <b>Critical:</b> {critical_count} ({critical_pct:.1f}%)
• 🟡 <b>Warning:</b> {warning_count} ({warning_pct:.1f}%)
• <b>Unique MID+Bank Routes Affected:</b> {unique_routes}
• <b>Unique MIDs:</b> {unique_mids}
• <b>Unique Banks:</b> {unique_banks}

📈 <b>Trend:</b> {trend_emoji} {trend_diff:+d} vs yesterday ({trend_pct:+.1f}%) - {trend_text}
📊 <b>7-Day Average:</b> {avg_7day:.1f} alerts/day
📊 <b>Position:</b> {avg_position_pct:+.1f}% vs average {avg_emoji}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 <b>TOP 10 PROBLEMATIC ROUTES</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        # Add top routes
        for i, route in enumerate(top_routes, 1):
            mid_name, bank_name, alert_count, critical, warning, avg_decline, total_txns, declined, successful = route

            # Truncate long names
            bank_display = bank_name[:40] + "..." if len(bank_name) > 40 else bank_name
            mid_display = mid_name[:35] + "..." if len(mid_name) > 35 else mid_name

            all_declined = "❌ All Declined" if declined == total_txns else ""

            report += f"""<b>{i}. {mid_display}</b>
   ➜ {bank_display}
   • Alerts: {alert_count} (🔴 {critical}, 🟡 {warning})
   • Avg Decline Rate: {avg_decline:.1f}%
   • Total Transactions: {format_number(total_txns)}
"""
            if all_declined:
                report += f"   • {all_declined}\n"
            report += "\n"

        # Time window breakdown
        report += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>ALERT BREAKDOWN BY TIME WINDOW</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        window_totals = {row[0]: row[1] for row in time_windows}
        for window in ['5min', '15min', '30min']:
            count = window_totals.get(window, 0)
            pct = (count / total_alerts * 100) if total_alerts > 0 else 0
            report += f"• {window} window: {count} alerts ({pct:.1f}%)\n"

        # Top banks
        report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏦 <b>TOP 5 AFFECTED BANKS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        for i, bank in enumerate(top_banks, 1):
            bank_name, alert_count, affected_mids = bank
            bank_display = bank_name[:45] + "..." if len(bank_name) > 45 else bank_name
            report += f"""<b>{i}. {bank_display}</b>
   • Alerts: {alert_count}
   • Affected MIDs: {affected_mids}

"""

        # Top MIDs
        report += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 <b>TOP 5 AFFECTED MIDs</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        for i, mid in enumerate(top_mids, 1):
            mid_name, alert_count, affected_banks = mid
            mid_display = mid_name[:45] + "..." if len(mid_name) > 45 else mid_name
            multi_bank_warning = "⚠️ Multiple bank routing issues" if affected_banks > 3 else ""

            report += f"""<b>{i}. {mid_display}</b>
   • Alerts: {alert_count}
   • Affected Banks: {affected_banks}
"""
            if multi_bank_warning:
                report += f"   • {multi_bank_warning}\n"
            report += "\n"

        # Trend analysis with bar chart
        report += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 <b>TREND ANALYSIS (Last 7 Days)</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        max_alerts = max([row[1] for row in trend_data]) if trend_data else 1
        for i, trend_row in enumerate(trend_data):
            date, alerts = trend_row
            bar = generate_bar_chart(alerts, max_alerts, 20)
            date_str = date.strftime('%b %d')
            today_marker = " (Today)" if i == 0 else ""
            peak_marker = " (Peak)" if alerts == max_alerts else ""

            report += f"{date_str:10} {alerts:3} alerts  {bar}{today_marker}{peak_marker}\n"

        report += f"""
• <b>vs Yesterday:</b> {trend_diff:+d} alerts ({trend_pct:+.1f}%) {trend_emoji} {trend_text}
• <b>7-Day Average:</b> {avg_7day:.1f} alerts/day
• <b>7-Day Total:</b> {total_7day} alerts
• <b>Today's Position:</b> {avg_position_pct:+.1f}% vs average {avg_emoji}

"""

        # Key insights
        report += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>KEY INSIGHTS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        # Generate insights based on data
        if total_alerts > 0:
            # Check for problematic MID
            if top_mids and top_mids[0][1] > total_alerts * 0.3:
                top_mid_name = top_mids[0][0]
                top_mid_alerts = top_mids[0][1]
                top_mid_pct = (top_mid_alerts / total_alerts * 100)
                top_mid_banks = top_mids[0][2]

                report += f"""⚠️ <b>CRITICAL FINDING:</b>

<b>{top_mid_name}</b> experiencing widespread issues
→ Affected {top_mid_banks} different bank(s)
→ {top_mid_alerts} alerts ({top_mid_pct:.1f}% of all alerts)
→ <b>Immediate routing investigation required</b>

"""

            # Check for problematic bank
            if top_banks and top_banks[0][1] > total_alerts * 0.25:
                top_bank_name = top_banks[0][0]
                top_bank_alerts = top_banks[0][1]
                top_bank_mids = top_banks[0][2]

                report += f"""⚠️ <b>{top_bank_name[:40]}</b> showing highest bank-side issues
→ {top_bank_alerts} alerts across {top_bank_mids} different MID(s)
→ May indicate bank-level connectivity problems

"""

            # Positive trends
            if trend_diff < 0:
                report += f"""✅ <b>POSITIVE TREND:</b>
• Alert volume decreased {abs(trend_pct):.1f}% vs yesterday
"""

            if avg_position_pct < -10:
                report += "• Trending significantly below 7-day average\n"
        else:
            report += "✅ <b>No alerts in this period</b> - All systems performing normally\n"

        # Recommendations
        if total_alerts > 0:
            report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 <b>RECOMMENDED ACTIONS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

            priority_items = []

            # Add top 3 routes as priority items
            for i, route in enumerate(top_routes[:3], 1):
                mid_name = route[0]
                bank_name = route[1]
                priority_items.append(f"✓ Investigate {mid_name} routing to {bank_name[:30]}")

            if priority_items:
                report += "<b>Priority 1 - URGENT:</b>\n"
                for item in priority_items[:3]:
                    report += f"  {item}\n"
                report += "\n"

        # Footer
        report += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🕒 <b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
🤖 <b>Generated by:</b> PolpayMonitor
📊 <b>Data Source:</b> alert_history table
🔍 <b>Monitoring:</b> Real-time alerts with 24h cooldown
"""

        # Close database connection
        cursor.close()
        conn.close()

        # Send report
        print(f"Sending daily report for {report_date}...")
        success = send_telegram_message(report)

        if success:
            print(f"✅ Daily report sent successfully for {report_date}")
            return True
        else:
            print(f"❌ Failed to send daily report")
            return False

    except Exception as e:
        print(f"Error generating daily report: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = generate_daily_report()
    sys.exit(0 if success else 1)
