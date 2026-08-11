#!/usr/bin/env python3
"""
Payment Alert Telegram Bot
Manages alert overrides, queries statistics, and provides interactive controls
"""

import os
import sys
import psycopg2
from psycopg2 import pool as psycopg2_pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import telebot
from telebot import types
import threading
import time
from contextlib import contextmanager

# Load environment variables
load_dotenv('/opt/payment-webhook/.env')

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
TELEGRAM_CHANNEL_IDS = [id.strip() for id in os.getenv('TELEGRAM_CHANNEL_ID', '').split(',') if id.strip()]

if not TELEGRAM_BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN not found in .env file")
    sys.exit(1)

# Initialize bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Connection pool: bot is low-traffic so 1–3 connections is plenty
_db_pool = psycopg2_pool.ThreadedConnectionPool(minconn=1, maxconn=3, **DB_CONFIG)

@contextmanager
def get_db_connection():
    """Borrow a connection from the pool, return it on exit."""
    conn = _db_pool.getconn()
    try:
        yield conn
    finally:
        _db_pool.putconn(conn)

def is_authorized(message):
    """Check if user is authorized to use the bot"""
    username = message.from_user.username
    user_id = message.from_user.id

    if not username:
        return False, "You need a Telegram username to use this bot"

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT role, is_active
                FROM telegram_authorized_users
                WHERE (telegram_username = %s OR telegram_user_id = %s)
                  AND is_active = true
            """, (username, user_id))
            result = cursor.fetchone()

        if result:
            return True, result['role']
        else:
            return False, f"User @{username} not authorized. Contact admin."

    except Exception as e:
        print(f"Authorization check error: {e}")
        return False, "Authorization check failed"

def log_interaction(username, user_id, command, action, details=None, success=True, error_message=None):
    """Log bot interaction for audit trail"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO telegram_bot_interactions
                (telegram_username, telegram_user_id, command, action, details, success, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (username, user_id, command, action, json.dumps(details) if details else None, success, error_message))
            conn.commit()
    except Exception as e:
        print(f"Failed to log interaction: {e}")

def require_auth(func):
    """Decorator to require authentication"""
    def wrapper(message):
        authorized, role_or_error = is_authorized(message)

        if not authorized:
            bot.reply_to(message, f"❌ {role_or_error}")
            log_interaction(
                message.from_user.username,
                message.from_user.id,
                message.text,
                'unauthorized_access',
                success=False,
                error_message=role_or_error
            )
            return

        # Add role to message object for use in handler
        message.user_role = role_or_error
        return func(message)

    return wrapper

# ============================================================================
# START & HELP COMMANDS
# ============================================================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Welcome message with main menu"""
    authorized, role_or_error = is_authorized(message)

    if not authorized:
        help_text = """
🤖 <b>Payment Alert Bot</b>

❌ You are not authorized to use this bot.

Contact your administrator to get access.
"""
        bot.reply_to(message, help_text, parse_mode='HTML')
        return

    # Create main menu buttons
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Today's Stats", callback_data="menu_stats_today"),
        types.InlineKeyboardButton("📈 Weekly Stats", callback_data="menu_stats_week"),
        types.InlineKeyboardButton("🔍 Find Alternatives", callback_data="menu_alternatives"),
        types.InlineKeyboardButton("✅ Recovered Routes", callback_data="menu_recovered"),
        types.InlineKeyboardButton("🔇 Suppress Route", callback_data="menu_suppress"),
        types.InlineKeyboardButton("📋 List Overrides", callback_data="menu_list_overrides"),
        types.InlineKeyboardButton("⚙️ Configuration", callback_data="menu_config"),
        types.InlineKeyboardButton("ℹ️ System Status", callback_data="menu_status"),
        types.InlineKeyboardButton("❓ Help", callback_data="menu_help")
    )

    welcome_text = f"""
🤖 <b>Welcome to Payment Alert Bot!</b>

👤 User: @{message.from_user.username}
🔑 Role: {role_or_error}

Choose an action below or use commands:
"""

    bot.reply_to(message, welcome_text, parse_mode='HTML', reply_markup=markup)

    log_interaction(
        message.from_user.username,
        message.from_user.id,
        message.text,
        'start'
    )

@bot.message_handler(commands=['menu'])
@require_auth
def show_menu(message):
    """Show main menu"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Today's Stats", callback_data="menu_stats_today"),
        types.InlineKeyboardButton("📈 Weekly Stats", callback_data="menu_stats_week"),
        types.InlineKeyboardButton("🔍 Find Alternatives", callback_data="menu_alternatives"),
        types.InlineKeyboardButton("✅ Recovered Routes", callback_data="menu_recovered"),
        types.InlineKeyboardButton("🔇 Suppress Route", callback_data="menu_suppress"),
        types.InlineKeyboardButton("📋 List Overrides", callback_data="menu_list_overrides"),
        types.InlineKeyboardButton("⚙️ Configuration", callback_data="menu_config"),
        types.InlineKeyboardButton("ℹ️ System Status", callback_data="menu_status")
    )

    bot.reply_to(message, "🎛️ <b>Main Menu</b>\n\nChoose an action:", parse_mode='HTML', reply_markup=markup)

@bot.message_handler(commands=['help'])
def send_help(message):
    """Help message"""
    authorized, role_or_error = is_authorized(message)

    if not authorized:
        help_text = """
🤖 <b>Payment Alert Bot</b>

You are not authorized to use this bot.
Contact your administrator to get access.
        """
        bot.reply_to(message, help_text, parse_mode='HTML')
        return

    help_text = f"""
🤖 <b>Payment Alert Bot</b>
Your role: <b>{role_or_error}</b>

<b>📋 Available Commands:</b>

<b>Override Management:</b>
/override list - List all active overrides
/override suppress MID BANK - Permanently suppress route
/override alert MID BANK - Force alert for route
/override remove MID BANK - Remove override

<b>Statistics & Queries:</b>
/stats today - Today's suppression stats
/stats week - Weekly summary
/alternatives BANK - Show alternative routes
/recovered - Show recovered routes

<b>Manual Checks:</b>
/check MID BANK - Check route health status
/test MID BANK - Simulate alert decision

<b>Configuration:</b> (Admin only)
/config show - Show current configuration
/config threshold VALUE - Set success rate threshold
/config enable - Enable smart filtering
/config disable - Disable smart filtering

<b>Other:</b>
/help - Show this help message
/status - Bot and system status

<b>💡 Tip:</b> You can also use interactive buttons on suppression alerts!
    """

    bot.reply_to(message, help_text, parse_mode='HTML')

# ============================================================================
# OVERRIDE MANAGEMENT COMMANDS
# ============================================================================

@bot.message_handler(commands=['override'])
@require_auth
def handle_override(message):
    """Handle override commands"""
    username = message.from_user.username
    user_id = message.from_user.id

    # Parse command
    parts = message.text.split(maxsplit=3)

    if len(parts) < 2:
        bot.reply_to(message, "Usage: /override <list|suppress|alert|remove> [MID] [BANK]")
        return

    action = parts[1].lower()

    if action == 'list':
        list_overrides(message)
    elif action in ['suppress', 'alert', 'remove']:
        if len(parts) < 4:
            bot.reply_to(message, f"Usage: /override {action} <MID_NAME> <BANK_NAME>")
            return

        mid_name = parts[2]
        bank_name = ' '.join(parts[3:])  # Bank name might have spaces

        if action == 'suppress':
            add_override_interactive(message, mid_name, bank_name, 'suppress')
        elif action == 'alert':
            add_override_interactive(message, mid_name, bank_name, 'force_alert')
        elif action == 'remove':
            remove_override(message, mid_name, bank_name)
    else:
        bot.reply_to(message, "❌ Unknown action. Use: list, suppress, alert, or remove")

def list_overrides(message):
    """List all active overrides"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT
                    id,
                    mid_name,
                    bank_name,
                    override_action,
                    reason,
                    created_by,
                    created_at
                FROM alert_overrides
                WHERE is_active = true
                ORDER BY created_at DESC
            """)
            overrides = cursor.fetchall()

        if not overrides:
            bot.reply_to(message, "ℹ️ No active overrides")
            return

        response = f"<b>📋 Active Overrides ({len(overrides)}):</b>\n\n"

        for i, override in enumerate(overrides, 1):
            action_emoji = "🔒" if override['override_action'] == 'suppress' else "🔓"
            action_text = "SUPPRESS" if override['override_action'] == 'suppress' else "FORCE ALERT"

            mid_display = override['mid_name'][:30] + "..." if len(override['mid_name']) > 30 else override['mid_name']
            bank_display = override['bank_name'][:30] + "..." if len(override['bank_name']) > 30 else override['bank_name']

            response += f"<b>{i}. {action_emoji} {mid_display}</b>\n"
            response += f"   + {bank_display}\n"
            response += f"   Action: <b>{action_text}</b>\n"
            response += f"   Reason: {override['reason']}\n"
            response += f"   By: @{override['created_by']} on {override['created_at'].strftime('%Y-%m-%d')}\n"
            response += f"   /remove_{override['id']}\n\n"

        bot.reply_to(message, response, parse_mode='HTML')

        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            'list_overrides',
            {'count': len(overrides)}
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error listing overrides: {e}")
        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            'list_overrides',
            success=False,
            error_message=str(e)
        )

def add_override_interactive(message, mid_name, bank_name, override_action):
    """Ask for reason before adding override"""
    msg = bot.reply_to(
        message,
        f"Please provide a reason for this override:\n\nMID: {mid_name}\nBank: {bank_name}\nAction: {override_action}"
    )

    bot.register_next_step_handler(
        msg,
        save_override,
        mid_name,
        bank_name,
        override_action
    )

def save_override(message, mid_name, bank_name, override_action):
    """Save override to database"""
    reason = message.text
    username = message.from_user.username

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT DISTINCT mid_id
                FROM transactions
                WHERE mid_name = %s AND bank_name = %s
                LIMIT 1
            """, (mid_name, bank_name))

            mid_result = cursor.fetchone()

            if not mid_result:
                bot.reply_to(message, f"❌ Route not found: {mid_name} + {bank_name}")
                return

            mid_id = mid_result['mid_id']

            cursor.execute("""
                INSERT INTO alert_overrides (mid_id, mid_name, bank_name, override_action, reason, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (mid_id, bank_name, override_action)
                DO UPDATE SET
                    reason = EXCLUDED.reason,
                    is_active = true,
                    last_modified_at = NOW(),
                    last_modified_by = EXCLUDED.created_by
                RETURNING id
            """, (mid_id, mid_name, bank_name, override_action, reason, username))

            override_id = cursor.fetchone()['id']
            conn.commit()

        action_text = "🔒 permanently suppressed" if override_action == 'suppress' else "🔓 forced to alert"

        bot.reply_to(
            message,
            f"✅ Override added (ID: {override_id})\n\n<b>{mid_name}</b> + {bank_name}\n\nWill be {action_text}\nReason: {reason}",
            parse_mode='HTML'
        )

        log_interaction(
            username,
            message.from_user.id,
            '/override',
            'add_override',
            {'mid_name': mid_name, 'bank_name': bank_name, 'action': override_action, 'reason': reason}
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error adding override: {e}")
        log_interaction(
            message.from_user.username,
            message.from_user.id,
            '/override',
            'add_override',
            success=False,
            error_message=str(e)
        )

def remove_override(message, mid_name, bank_name):
    """Remove an override"""
    username = message.from_user.username

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE alert_overrides
                SET is_active = false,
                    last_modified_at = NOW(),
                    last_modified_by = %s
                WHERE mid_name = %s
                  AND bank_name = %s
                  AND is_active = true
                RETURNING id
            """, (username, mid_name, bank_name))

            result = cursor.fetchone()

            if result:
                conn.commit()
                bot.reply_to(
                    message,
                    f"✅ Override removed\n\n<b>{mid_name}</b> + {bank_name}\n\nWill now follow normal smart filtering",
                    parse_mode='HTML'
                )
                log_interaction(
                    username,
                    message.from_user.id,
                    message.text,
                    'remove_override',
                    {'mid_name': mid_name, 'bank_name': bank_name}
                )
            else:
                bot.reply_to(message, f"❌ No active override found for: {mid_name} + {bank_name}")

    except Exception as e:
        bot.reply_to(message, f"❌ Error removing override: {e}")
        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            'remove_override',
            success=False,
            error_message=str(e)
        )

# Handle /remove_<id> shortcuts from list
@bot.message_handler(regexp=r'^/remove_\d+$')
@require_auth
def remove_override_by_id(message):
    """Remove override by ID"""
    override_id = int(message.text.split('_')[1])
    username = message.from_user.username

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                UPDATE alert_overrides
                SET is_active = false,
                    last_modified_at = NOW(),
                    last_modified_by = %s
                WHERE id = %s
                RETURNING mid_name, bank_name
            """, (username, override_id))

            result = cursor.fetchone()

            if result:
                conn.commit()
                bot.reply_to(
                    message,
                    f"✅ Override removed\n\n<b>{result['mid_name']}</b> + {result['bank_name']}",
                    parse_mode='HTML'
                )
            else:
                bot.reply_to(message, f"❌ Override {override_id} not found")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# ============================================================================
# STATISTICS & QUERY COMMANDS
# ============================================================================

@bot.message_handler(commands=['stats'])
@require_auth
def handle_stats(message):
    """Show statistics"""
    parts = message.text.split()

    if len(parts) < 2:
        period = 'today'
    else:
        period = parts[1].lower()

    if period == 'today':
        show_stats_today(message)
    elif period == 'week':
        show_stats_week(message)
    else:
        bot.reply_to(message, "Usage: /stats <today|week>")

def show_stats_today(message):
    """Show today's suppression statistics"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT
                    COUNT(*) as total_suppressions,
                    COUNT(DISTINCT mid_name || '|' || bank_name) as unique_routes,
                    suppression_reason,
                    COUNT(*) as count_by_reason
                FROM alert_suppression_log
                WHERE suppression_time >= CURRENT_DATE
                GROUP BY suppression_reason
            """)
            suppressions = cursor.fetchall()

            cursor.execute("""
                SELECT COUNT(*) as total_alerts
                FROM alert_history
                WHERE alert_time >= CURRENT_DATE
            """)
            alerts = cursor.fetchone()

        total_suppressions = sum(row['count_by_reason'] for row in suppressions)
        total_alerts = alerts['total_alerts'] if alerts else 0
        total_potential = total_suppressions + total_alerts

        if total_potential > 0:
            suppression_rate = (total_suppressions / total_potential) * 100
        else:
            suppression_rate = 0

        response = f"""<b>📊 Today's Statistics</b>
━━━━━━━━━━━━━━━━━━━━━

<b>Alerts:</b>
• Sent: {total_alerts}
• Suppressed: {total_suppressions}
• Noise Reduction: {suppression_rate:.1f}%

<b>Suppression Breakdown:</b>
"""

        for supp in suppressions:
            reason_display = {
                'dead_route': '🔴 Dead Routes (never work)',
                'low_success_rate': '🟡 Low Success (<10%)'
            }.get(supp['suppression_reason'], supp['suppression_reason'])

            response += f"• {reason_display}: {supp['count_by_reason']}\n"

        bot.reply_to(message, response, parse_mode='HTML')

        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            'stats_today'
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

def show_stats_week(message):
    """Show weekly statistics"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT
                    COUNT(*) as total_suppressions,
                    COUNT(DISTINCT mid_name || '|' || bank_name) as unique_routes
                FROM alert_suppression_log
                WHERE suppression_time >= CURRENT_DATE - INTERVAL '7 days'
            """)
            supp_stats = cursor.fetchone()

            cursor.execute("""
                SELECT COUNT(*) as total_alerts
                FROM alert_history
                WHERE alert_time >= CURRENT_DATE - INTERVAL '7 days'
            """)
            alert_stats = cursor.fetchone()

        total_supp = supp_stats['total_suppressions']
        total_alerts = alert_stats['total_alerts']
        total_potential = total_supp + total_alerts
        suppression_rate = (total_supp / total_potential * 100) if total_potential > 0 else 0

        response = f"""<b>📊 Last 7 Days Statistics</b>
━━━━━━━━━━━━━━━━━━━━━

<b>Summary:</b>
• Alerts Sent: {total_alerts}
• Alerts Suppressed: {total_supp}
• Unique Routes Suppressed: {supp_stats['unique_routes']}
• Noise Reduction: {suppression_rate:.1f}%

<b>Daily Average:</b>
• Alerts: {total_alerts/7:.1f}/day
• Suppressions: {total_supp/7:.1f}/day
"""

        bot.reply_to(message, response, parse_mode='HTML')

        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            'stats_week'
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# ============================================================================
# QUERY COMMANDS - Alternatives & Recovery
# ============================================================================

@bot.message_handler(commands=['alternatives'])
@require_auth
def handle_alternatives(message):
    """Show alternative routes for a specific bank"""
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        bot.reply_to(
            message,
            "Usage: /alternatives <BANK_NAME>\nExample: /alternatives SIPAY"
        )
        return

    bank_search = parts[1].strip()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT DISTINCT bank_name
                FROM transactions
                WHERE bank_name ILIKE %s
                ORDER BY bank_name
                LIMIT 5
            """, (f'%{bank_search}%',))
            banks = cursor.fetchall()

            if not banks:
                bot.reply_to(message, f"❌ No banks found matching '{bank_search}'")
                return

            if len(banks) > 1:
                bank_list = "\n".join([f"• {b['bank_name']}" for b in banks])
                bot.reply_to(
                    message,
                    f"Multiple banks found. Please be more specific:\n{bank_list}"
                )
                return

            bank_name = banks[0]['bank_name']

            cursor.execute("""
                WITH route_performance AS (
                    SELECT
                        mid_id,
                        mid_name,
                        COUNT(*) FILTER (WHERE status = 'success' AND last_updated_at >= NOW() - INTERVAL '7 days') as success_7d,
                        COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '7 days') as total_7d,
                        ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success' AND last_updated_at >= NOW() - INTERVAL '7 days') /
                              NULLIF(COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '7 days'), 0), 2) as success_rate_7d
                    FROM transactions
                    WHERE bank_name = %s
                      AND last_updated_at >= NOW() - INTERVAL '7 days'
                      AND mid_id IS NOT NULL
                    GROUP BY mid_id, mid_name
                    HAVING COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '7 days') >= 10
                )
                SELECT
                    mid_id,
                    mid_name,
                    success_rate_7d,
                    total_7d,
                    CASE
                        WHEN success_rate_7d >= 30 THEN '🟢'
                        WHEN success_rate_7d >= 10 THEN '🟡'
                        ELSE '🔴'
                    END as status_emoji
                FROM route_performance
                ORDER BY success_rate_7d DESC, total_7d DESC
            """, (bank_name,))
            routes = cursor.fetchall()

        if not routes:
            bot.reply_to(
                message,
                f"<b>No routes found for:</b>\n{bank_name[:50]}\n\n"
                f"ℹ️ Bank may have no recent traffic (last 7 days)",
                parse_mode='HTML'
            )
            return

        # Categorize routes
        healthy = [r for r in routes if r['success_rate_7d'] >= 10]
        dead = [r for r in routes if r['success_rate_7d'] < 10]

        response = f"<b>💡 Routes for {bank_name[:40]}</b>\n"
        response += "━" * 30 + "\n\n"

        if healthy:
            response += f"<b>✅ Working Routes ({len(healthy)}):</b>\n"
            for i, route in enumerate(healthy[:5], 1):
                response += (
                    f"{i}. {route['status_emoji']} <b>{route['mid_name']}</b>\n"
                    f"   Success: {route['success_rate_7d']:.1f}% "
                    f"({route['total_7d']} txns)\n"
                )
            response += "\n"

        if dead:
            response += f"<b>🔴 Dead Routes ({len(dead)}):</b>\n"
            for route in dead[:3]:
                response += (
                    f"• {route['mid_name']}: "
                    f"{route['success_rate_7d']:.1f}%\n"
                )

        bot.reply_to(message, response, parse_mode='HTML')

        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            'alternatives',
            details={'bank_name': bank_name}
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['recovered'])
@require_auth
def handle_recovered(message):
    """Show routes that have recovered from suppression"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                WITH recently_suppressed AS (
                    SELECT DISTINCT
                        s.mid_id,
                        s.mid_name,
                        s.bank_name,
                        AVG(s.success_rate_7d) as avg_suppressed_success_rate,
                        MAX(s.suppression_time) as last_suppressed
                    FROM alert_suppression_log s
                    WHERE s.suppression_time >= NOW() - INTERVAL '7 days'
                    GROUP BY s.mid_id, s.mid_name, s.bank_name
                    HAVING AVG(s.success_rate_7d) < 10
                ),
                current_performance AS (
                    SELECT
                        t.mid_id,
                        COUNT(*) FILTER (WHERE t.status = 'success' AND t.last_updated_at >= NOW() - INTERVAL '7 days') as success_7d,
                        COUNT(*) FILTER (WHERE t.last_updated_at >= NOW() - INTERVAL '7 days') as total_7d,
                        ROUND(100.0 * COUNT(*) FILTER (WHERE t.status = 'success' AND t.last_updated_at >= NOW() - INTERVAL '7 days') /
                              NULLIF(COUNT(*) FILTER (WHERE t.last_updated_at >= NOW() - INTERVAL '7 days'), 0), 2) as current_success_rate_7d
                    FROM transactions t
                    WHERE t.last_updated_at >= NOW() - INTERVAL '7 days'
                    GROUP BY t.mid_id
                )
                SELECT
                    rs.mid_name,
                    rs.bank_name,
                    rs.avg_suppressed_success_rate as old_success_rate,
                    cp.current_success_rate_7d as new_success_rate,
                    cp.total_7d as recent_transactions,
                    rs.last_suppressed
                FROM recently_suppressed rs
                JOIN current_performance cp ON rs.mid_id = cp.mid_id
                WHERE cp.current_success_rate_7d >= 10
                  AND cp.total_7d >= 10
                ORDER BY cp.current_success_rate_7d DESC
            """)
            recovered = cursor.fetchall()

        if not recovered:
            bot.reply_to(
                message,
                "<b>✅ No Recovered Routes</b>\n\n"
                "ℹ️ All previously suppressed routes are still underperforming.\n"
                "This is normal - dead routes usually stay dead.",
                parse_mode='HTML'
            )
            return

        response = f"<b>✅ RECOVERED ROUTES ({len(recovered)})</b>\n"
        response += "━" * 30 + "\n\n"
        response += "Routes that were suppressed but have recovered:\n\n"

        for i, route in enumerate(recovered, 1):
            improvement = route['new_success_rate'] - route['old_success_rate']
            response += (
                f"{i}. <b>{route['mid_name']}</b>\n"
                f"   Bank: {route['bank_name'][:40]}\n"
                f"   📊 Was: {route['old_success_rate']:.1f}% "
                f"→ Now: {route['new_success_rate']:.1f}% "
                f"<b>(+{improvement:.1f}%)</b>\n"
                f"   🔔 Alerts will resume for this route\n\n"
            )

        response += "💡 These routes now pass the 10% threshold"

        bot.reply_to(message, response, parse_mode='HTML')

        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            'recovered'
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['check'])
@require_auth
def handle_check(message):
    """Manually check route health status"""
    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(
            message,
            "Usage: /check <MID_NAME> <BANK_NAME>\n"
            "Example: /check Networxpay - LIVE - 3 SIPAY"
        )
        return

    mid_search = parts[1].strip()
    bank_search = parts[2].strip()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT DISTINCT mid_id, mid_name, bank_name
                FROM transactions
                WHERE mid_name ILIKE %s
                  AND bank_name ILIKE %s
                LIMIT 1
            """, (f'%{mid_search}%', f'%{bank_search}%'))
            route = cursor.fetchone()

            if not route:
                bot.reply_to(message, f"❌ No route found matching '{mid_search}' + '{bank_search}'")
                return

            mid_id = route['mid_id']
            mid_name = route['mid_name']
            bank_name = route['bank_name']

            cursor.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'success' AND last_updated_at >= NOW() - INTERVAL '7 days') as success_7d,
                    COUNT(*) FILTER (WHERE status = 'declined' AND last_updated_at >= NOW() - INTERVAL '7 days') as declined_7d,
                    COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '7 days') as total_7d,
                    COUNT(*) FILTER (WHERE status = 'success' AND last_updated_at >= NOW() - INTERVAL '30 days') as success_30d,
                    COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '30 days') as total_30d,
                    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success' AND last_updated_at >= NOW() - INTERVAL '7 days') /
                          NULLIF(COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '7 days'), 0), 2) as success_rate_7d,
                    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success' AND last_updated_at >= NOW() - INTERVAL '30 days') /
                          NULLIF(COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '30 days'), 0), 2) as success_rate_30d
                FROM transactions
                WHERE mid_id = %s AND bank_name = %s
            """, (mid_id, bank_name))
            stats = cursor.fetchone()

            cursor.execute("""
                SELECT override_action, reason, created_by, created_at
                FROM alert_overrides
                WHERE mid_id = %s AND bank_name = %s AND is_active = true
            """, (mid_id, bank_name))
            override = cursor.fetchone()

        # Determine health status
        sr_7d = stats['success_rate_7d'] or 0
        sr_30d = stats['success_rate_30d'] or 0

        if sr_7d >= 10:
            status = "✅ HEALTHY"
            status_desc = "Route is performing well"
        elif sr_30d >= 10 and sr_7d < 10:
            status = "⚠️ REGRESSION"
            status_desc = "Route was working but recently degraded"
        else:
            status = "🔴 DEAD"
            status_desc = "Route has consistently low success rate"

        response = f"<b>🔍 Route Health Check</b>\n"
        response += "━" * 30 + "\n\n"
        response += f"<b>Route:</b> {mid_name}\n"
        response += f"<b>Bank:</b> {bank_name[:40]}\n\n"
        response += f"<b>Status:</b> {status}\n"
        response += f"{status_desc}\n\n"
        response += f"<b>📊 Performance (Last 7 days):</b>\n"
        response += f"• Success: {stats['success_7d']}/{stats['total_7d']} ({sr_7d:.1f}%)\n"
        response += f"• Declined: {stats['declined_7d']}\n\n"
        response += f"<b>📊 Performance (Last 30 days):</b>\n"
        response += f"• Success: {stats['success_30d']}/{stats['total_30d']} ({sr_30d:.1f}%)\n\n"

        if override:
            action_display = "🔇 Forced Suppression" if override['override_action'] == 'suppress' else "🔔 Forced Alert"
            response += f"<b>Override Active:</b> {action_display}\n"
            response += f"• Reason: {override['reason']}\n"
            response += f"• By: {override['created_by']}\n"
        else:
            response += "<b>Override:</b> None\n"

        response += f"\n<b>Alert Decision:</b> "
        if override and override['override_action'] == 'suppress':
            response += "🔇 Suppressed (manual override)"
        elif override and override['override_action'] == 'force_alert':
            response += "🔔 Alerting (manual override)"
        elif sr_7d >= 10:
            response += "🔔 Alerting (healthy route)"
        else:
            response += "🔇 Suppressed (dead/unhealthy route)"

        bot.reply_to(message, response, parse_mode='HTML')

        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            'check',
            details={'mid_name': mid_name, 'bank_name': bank_name}
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['test'])
@require_auth
def handle_test(message):
    """Simulate alert decision for a route"""
    parts = message.text.split(maxsplit=2)

    if len(parts) < 3:
        bot.reply_to(
            message,
            "Usage: /test <MID_NAME> <BANK_NAME>\n"
            "Example: /test Networxpay - LIVE - 3 SIPAY\n\n"
            "This shows what would happen if this route triggered an alert right now."
        )
        return

    # Reuse check logic but with different messaging
    mid_search = parts[1].strip()
    bank_search = parts[2].strip()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT DISTINCT mid_id, mid_name, bank_name
                FROM transactions
                WHERE mid_name ILIKE %s
                  AND bank_name ILIKE %s
                LIMIT 1
            """, (f'%{mid_search}%', f'%{bank_search}%'))
            route = cursor.fetchone()

            if not route:
                bot.reply_to(message, f"❌ No route found")
                return

            mid_id = route['mid_id']
            mid_name = route['mid_name']
            bank_name = route['bank_name']

            cursor.execute("""
                SELECT
                    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success' AND last_updated_at >= NOW() - INTERVAL '7 days') /
                          NULLIF(COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '7 days'), 0), 2) as success_rate_7d
                FROM transactions
                WHERE mid_id = %s AND bank_name = %s
            """, (mid_id, bank_name))
            stats = cursor.fetchone()

            cursor.execute("""
                SELECT override_action FROM alert_overrides
                WHERE mid_id = %s AND bank_name = %s AND is_active = true
            """, (mid_id, bank_name))
            override = cursor.fetchone()

        sr_7d = stats['success_rate_7d'] or 0

        response = f"<b>🧪 Alert Simulation</b>\n"
        response += "━" * 30 + "\n\n"
        response += f"<b>Route:</b> {mid_name}\n"
        response += f"<b>Bank:</b> {bank_name[:40]}\n"
        response += f"<b>Success Rate (7d):</b> {sr_7d:.1f}%\n\n"

        if override:
            if override['override_action'] == 'suppress':
                response += "✅ <b>Result: Alert SUPPRESSED</b>\n"
                response += "📌 Reason: Manual override (forced suppression)\n"
            else:
                response += "✅ <b>Result: Alert SENT</b>\n"
                response += "📌 Reason: Manual override (forced alert)\n"
        elif sr_7d >= 10:
            response += "✅ <b>Result: Alert SENT</b>\n"
            response += "📌 Reason: Healthy route (success ≥ 10%)\n"
        else:
            response += "🔇 <b>Result: Alert SUPPRESSED</b>\n"
            response += "📌 Reason: Dead route (success < 10%)\n"

        bot.reply_to(message, response, parse_mode='HTML')

        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            'test'
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# ============================================================================
# CONFIGURATION COMMANDS (Admin Only)
# ============================================================================

@bot.message_handler(commands=['config'])
@require_auth
def handle_config(message):
    """Handle configuration commands"""
    if message.user_role not in ['admin']:
        bot.reply_to(message, "❌ This command requires admin privileges")
        return

    parts = message.text.split()

    if len(parts) < 2:
        bot.reply_to(
            message,
            "Usage: /config <show|threshold|enable|disable>\n\n"
            "Examples:\n"
            "• /config show - Show current configuration\n"
            "• /config threshold 15 - Set success rate threshold to 15%\n"
            "• /config enable - Enable smart filtering\n"
            "• /config disable - Disable smart filtering"
        )
        return

    action = parts[1].lower()

    if action == 'show':
        show_config(message)
    elif action == 'threshold':
        if len(parts) < 3:
            bot.reply_to(message, "❌ Usage: /config threshold <VALUE>")
            return
        try:
            threshold = float(parts[2])
            if threshold < 0 or threshold > 100:
                bot.reply_to(message, "❌ Threshold must be between 0 and 100")
                return
            update_config_threshold(message, threshold)
        except ValueError:
            bot.reply_to(message, "❌ Threshold must be a number")
    elif action == 'enable':
        update_config_enabled(message, True)
    elif action == 'disable':
        update_config_enabled(message, False)
    else:
        bot.reply_to(message, f"❌ Unknown config action: {action}")

def show_config(message):
    """Show current smart filtering configuration"""
    # Read from payment_monitor.py
    try:
        with open('/opt/payment-webhook/services/payment_monitor.py', 'r') as f:
            content = f.read()

        # Extract SMART_FILTER_CONFIG
        import re
        enabled_match = re.search(r"'enabled':\s*(True|False)", content)
        threshold_match = re.search(r"'min_success_rate_threshold':\s*(\d+\.?\d*)", content)
        recent_days_match = re.search(r"'recent_period_days':\s*(\d+)", content)
        historical_days_match = re.search(r"'historical_period_days':\s*(\d+)", content)

        enabled = enabled_match.group(1) if enabled_match else "Unknown"
        threshold = float(threshold_match.group(1)) * 100 if threshold_match else "Unknown"
        recent = recent_days_match.group(1) if recent_days_match else "Unknown"
        historical = historical_days_match.group(1) if historical_days_match else "Unknown"

        status_icon = "✅" if enabled == "True" else "🔴"

        response = f"""<b>⚙️ Smart Filtering Configuration</b>
━━━━━━━━━━━━━━━━━━━━━

<b>Status:</b> {status_icon} {enabled}
<b>Success Rate Threshold:</b> {threshold}%
<b>Recent Period:</b> {recent} days
<b>Historical Period:</b> {historical} days

<b>What this means:</b>
• Routes with &lt;{threshold}% success rate will be suppressed
• Recent = last {recent} days performance
• Historical = last {historical} days for regression detection

<b>Admin only:</b> Use /config threshold or /config enable/disable to modify
"""

        bot.reply_to(message, response, parse_mode='HTML')

        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            'config_show'
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error reading config: {e}")

def update_config_threshold(message, threshold):
    """Update success rate threshold"""
    try:
        # Read current file
        with open('/opt/payment-webhook/services/payment_monitor.py', 'r') as f:
            content = f.read()

        # Update threshold
        import re
        threshold_decimal = threshold / 100
        content = re.sub(
            r"'min_success_rate_threshold':\s*\d+\.?\d*",
            f"'min_success_rate_threshold': {threshold_decimal}",
            content
        )

        # Write back
        with open('/opt/payment-webhook/services/payment_monitor.py', 'w') as f:
            f.write(content)

        bot.reply_to(
            message,
            f"✅ <b>Configuration Updated</b>\n\n"
            f"Success rate threshold set to <b>{threshold}%</b>\n\n"
            f"⚠️ Note: Changes will take effect on next monitoring run (within 5 minutes)",
            parse_mode='HTML'
        )

        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            'config_update_threshold',
            details={'new_threshold': threshold},
            success=True
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error updating config: {e}")
        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            'config_update_threshold',
            success=False,
            error_message=str(e)
        )

def update_config_enabled(message, enabled):
    """Enable or disable smart filtering"""
    try:
        with open('/opt/payment-webhook/services/payment_monitor.py', 'r') as f:
            content = f.read()

        import re
        content = re.sub(
            r"'enabled':\s*(True|False)",
            f"'enabled': {enabled}",
            content
        )

        with open('/opt/payment-webhook/services/payment_monitor.py', 'w') as f:
            f.write(content)

        status = "enabled" if enabled else "disabled"
        icon = "✅" if enabled else "🔴"

        bot.reply_to(
            message,
            f"{icon} <b>Smart Filtering {status.title()}</b>\n\n"
            f"⚠️ Changes will take effect on next monitoring run (within 5 minutes)",
            parse_mode='HTML'
        )

        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            f'config_{status}',
            success=True
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")
        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            'config_update',
            success=False,
            error_message=str(e)
        )

@bot.message_handler(commands=['status'])
@require_auth
def handle_status(message):
    """Show bot and system status"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("SELECT NOW() as current_time")
            db_status = cursor.fetchone()

            cursor.execute("SELECT alert_time FROM alert_history ORDER BY alert_time DESC LIMIT 1")
            last_alert = cursor.fetchone()

            cursor.execute("SELECT suppression_time FROM alert_suppression_log ORDER BY suppression_time DESC LIMIT 1")
            last_suppression = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) as count FROM alert_overrides WHERE is_active = true")
            override_count = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) as count FROM telegram_authorized_users WHERE is_active = true")
            user_count = cursor.fetchone()

        # Format timestamps
        from datetime import datetime
        now = datetime.now()

        if last_alert and last_alert['alert_time']:
            alert_ago = now - last_alert['alert_time']
            alert_str = f"{alert_ago.seconds // 3600}h {(alert_ago.seconds % 3600) // 60}m ago"
        else:
            alert_str = "Never"

        if last_suppression and last_suppression['suppression_time']:
            supp_ago = now - last_suppression['suppression_time']
            supp_str = f"{supp_ago.seconds // 3600}h {(supp_ago.seconds % 3600) // 60}m ago"
        else:
            supp_str = "Never"

        response = f"""<b>🤖 Bot Status</b>
━━━━━━━━━━━━━━━━━━━━━

<b>🔌 System Health:</b>
• Bot: ✅ Running
• Database: ✅ Connected
• Server Time: {db_status['current_time'].strftime('%Y-%m-%d %H:%M:%S UTC')}

<b>📊 Activity:</b>
• Last Alert: {alert_str}
• Last Suppression: {supp_str}
• Active Overrides: {override_count['count']}
• Authorized Users: {user_count['count']}

<b>ℹ️ Monitoring:</b>
• Runs every 5 minutes
• Daily reports at 09:00 UTC
• Smart filtering: Active
"""

        bot.reply_to(message, response, parse_mode='HTML')

        log_interaction(
            message.from_user.username,
            message.from_user.id,
            message.text,
            'status'
        )

    except Exception as e:
        bot.reply_to(
            message,
            f"⚠️ <b>Bot Status: Degraded</b>\n\n"
            f"Database connection error:\n{e}",
            parse_mode='HTML'
        )

# ============================================================================
# CALLBACK HANDLERS - Interactive Buttons
# ============================================================================

# Menu button callbacks
@bot.callback_query_handler(func=lambda call: call.data.startswith('menu_'))
def handle_menu_callback(call):
    """Handle main menu button clicks"""
    try:
        action = call.data.replace('menu_', '')

        if action == 'stats_today':
            bot.answer_callback_query(call.id, "Loading today's stats...")
            # Create a fake message object to reuse existing function
            fake_msg = type('obj', (object,), {
                'from_user': call.from_user,
                'chat': call.message.chat,
                'message_id': call.message.message_id,
                'text': '/stats today',
                'user_role': call.message.chat.type  # Will be set by auth check
            })()
            show_stats_today(fake_msg)

        elif action == 'stats_week':
            bot.answer_callback_query(call.id, "Loading weekly stats...")
            fake_msg = type('obj', (object,), {
                'from_user': call.from_user,
                'chat': call.message.chat,
                'message_id': call.message.message_id,
                'text': '/stats week',
                'user_role': call.message.chat.type
            })()
            show_stats_week(fake_msg)

        elif action == 'alternatives':
            bot.answer_callback_query(call.id)
            # Ask for bank name
            msg = bot.send_message(
                call.message.chat.id,
                "🔍 <b>Find Alternative Routes</b>\n\n"
                "Please enter the bank name (or part of it):\n\n"
                "Examples:\n"
                "• SIPAY\n"
                "• ZIRAAT\n"
                "• QNB",
                parse_mode='HTML'
            )
            bot.register_next_step_handler(msg, process_alternatives_search)

        elif action == 'recovered':
            bot.answer_callback_query(call.id, "Checking recovered routes...")
            fake_msg = type('obj', (object,), {
                'from_user': call.from_user,
                'chat': call.message.chat,
                'message_id': call.message.message_id,
                'text': '/recovered',
                'user_role': call.message.chat.type
            })()
            handle_recovered(fake_msg)

        elif action == 'suppress':
            bot.answer_callback_query(call.id)
            # Ask for MID name
            msg = bot.send_message(
                call.message.chat.id,
                "🔇 <b>Suppress Route</b>\n\n"
                "Step 1 of 2: Enter the MID name:\n\n"
                "Example: Networxpay - LIVE - 3",
                parse_mode='HTML'
            )
            bot.register_next_step_handler(msg, process_suppress_step1)

        elif action == 'list_overrides':
            bot.answer_callback_query(call.id, "Loading overrides...")
            fake_msg = type('obj', (object,), {
                'from_user': call.from_user,
                'chat': call.message.chat,
                'message_id': call.message.message_id,
                'text': '/override list',
                'user_role': call.message.chat.type
            })()
            handle_override(fake_msg)

        elif action == 'config':
            bot.answer_callback_query(call.id, "Loading configuration...")
            fake_msg = type('obj', (object,), {
                'from_user': call.from_user,
                'chat': call.message.chat,
                'message_id': call.message.message_id,
                'text': '/config show',
                'user_role': call.message.chat.type
            })()
            show_config(fake_msg)

        elif action == 'status':
            bot.answer_callback_query(call.id, "Checking system status...")
            fake_msg = type('obj', (object,), {
                'from_user': call.from_user,
                'chat': call.message.chat,
                'message_id': call.message.message_id,
                'text': '/status',
                'user_role': call.message.chat.type
            })()
            handle_status(fake_msg)

        elif action == 'help':
            bot.answer_callback_query(call.id)
            fake_msg = type('obj', (object,), {
                'from_user': call.from_user,
                'chat': call.message.chat,
                'message_id': call.message.message_id,
                'text': '/help',
                'user_role': call.message.chat.type
            })()
            send_help(fake_msg)

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)[:100]}")
        print(f"Menu callback error: {e}")

def process_alternatives_search(message):
    """Process bank search for alternatives"""
    bank_search = message.text.strip()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT DISTINCT bank_name
                FROM transactions
                WHERE bank_name ILIKE %s
                ORDER BY bank_name
                LIMIT 10
            """, (f'%{bank_search}%',))
            banks = cursor.fetchall()

            if not banks:
                bot.reply_to(message, f"❌ No banks found matching '{bank_search}'")
                return

            if len(banks) > 1:
                markup = types.InlineKeyboardMarkup(row_width=1)
                for bank in banks:
                    bank_name = bank['bank_name']
                    display_name = bank_name if len(bank_name) <= 50 else bank_name[:47] + "..."
                    callback_data = f"alt_{bank_name[:50]}"
                    markup.add(types.InlineKeyboardButton(display_name, callback_data=callback_data))
                bot.reply_to(message, f"Found {len(banks)} banks. Select one:", reply_markup=markup)
                return

            bank_name = banks[0]['bank_name']
            show_alternatives_for_bank(message.chat.id, bank_name, cursor, username=message.from_user.username, user_id=message.from_user.id)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

def show_alternatives_for_bank(chat_id, bank_name, cursor=None, username=None, user_id=None):
    """Show alternative routes for a bank"""
    own_conn = cursor is None

    try:
        if own_conn:
            _conn = _db_pool.getconn()
            cursor = _conn.cursor(cursor_factory=RealDictCursor)
        else:
            _conn = None
        # Get alternative routes for this bank
        cursor.execute("""
            WITH route_performance AS (
                SELECT
                    mid_id,
                    mid_name,
                    COUNT(*) FILTER (WHERE status = 'success' AND last_updated_at >= NOW() - INTERVAL '7 days') as success_7d,
                    COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '7 days') as total_7d,
                    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'success' AND last_updated_at >= NOW() - INTERVAL '7 days') /
                          NULLIF(COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '7 days'), 0), 2) as success_rate_7d
                FROM transactions
                WHERE bank_name = %s
                  AND last_updated_at >= NOW() - INTERVAL '7 days'
                  AND mid_id IS NOT NULL
                GROUP BY mid_id, mid_name
                HAVING COUNT(*) FILTER (WHERE last_updated_at >= NOW() - INTERVAL '7 days') >= 10
            )
            SELECT
                mid_id,
                mid_name,
                success_rate_7d,
                total_7d,
                CASE
                    WHEN success_rate_7d >= 30 THEN '🟢'
                    WHEN success_rate_7d >= 10 THEN '🟡'
                    ELSE '🔴'
                END as status_emoji
            FROM route_performance
            ORDER BY success_rate_7d DESC, total_7d DESC
            LIMIT 10
        """, (bank_name,))

        routes = cursor.fetchall()

        if not routes:
            bot.send_message(
                chat_id,
                f"<b>No routes found for:</b>\n{bank_name[:50]}\n\n"
                f"ℹ️ Bank may have no recent traffic (last 7 days)",
                parse_mode='HTML'
            )
            return

        # Categorize routes
        healthy = [r for r in routes if r['success_rate_7d'] >= 10]
        dead = [r for r in routes if r['success_rate_7d'] < 10]

        response = f"<b>💡 Routes for {bank_name[:40]}</b>\n"
        response += "━" * 30 + "\n\n"

        # Add buttons for each route
        markup = types.InlineKeyboardMarkup(row_width=1)

        if healthy:
            response += f"<b>✅ Working Routes ({len(healthy)}):</b>\n"
            for i, route in enumerate(healthy[:5], 1):
                response += (
                    f"{i}. {route['status_emoji']} <b>{route['mid_name']}</b>\n"
                    f"   Success: {route['success_rate_7d']:.1f}% "
                    f"({route['total_7d']} txns)\n"
                )
                # Add button to check this route
                markup.add(types.InlineKeyboardButton(
                    f"🔍 Check {route['mid_name'][:30]}",
                    callback_data=f"checkroute_{route['mid_id']}"
                ))
            response += "\n"

        if dead:
            response += f"<b>🔴 Dead Routes ({len(dead)}):</b>\n"
            for route in dead[:3]:
                response += (
                    f"• {route['mid_name']}: "
                    f"{route['success_rate_7d']:.1f}%\n"
                )

        bot.send_message(chat_id, response, parse_mode='HTML', reply_markup=markup if healthy else None)

        if username:
            log_interaction(username, user_id, f'/alternatives {bank_name}', 'alternatives', details={'bank_name': bank_name})

    finally:
        if own_conn and _conn:
            _db_pool.putconn(_conn)

@bot.callback_query_handler(func=lambda call: call.data.startswith('alt_'))
def handle_bank_selection(call):
    """Handle bank selection for alternatives"""
    try:
        bank_name = call.data.replace('alt_', '')
        bot.answer_callback_query(call.id, f"Loading routes for {bank_name[:30]}...")
        show_alternatives_for_bank(
            call.message.chat.id,
            bank_name,
            username=call.from_user.username,
            user_id=call.from_user.id
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)[:50]}")

def process_suppress_step1(message):
    """Step 1: Get MID name"""
    mid_search = message.text.strip()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT DISTINCT mid_id, mid_name
                FROM transactions
                WHERE mid_name ILIKE %s
                ORDER BY mid_name
                LIMIT 10
            """, (f'%{mid_search}%',))
            mids = cursor.fetchall()

        if not mids:
            bot.reply_to(message, f"❌ No MIDs found matching '{mid_search}'")
            return

        if len(mids) > 1:
            # Show buttons to select MID
            markup = types.InlineKeyboardMarkup(row_width=1)
            for mid in mids:
                markup.add(types.InlineKeyboardButton(
                    mid['mid_name'],
                    callback_data=f"selmid_{mid['mid_id']}"
                ))

            bot.reply_to(message, f"Found {len(mids)} MIDs. Select one:", reply_markup=markup)
            return

        # Only one MID found, ask for bank
        mid_id = mids[0]['mid_id']
        mid_name = mids[0]['mid_name']

        msg = bot.reply_to(
            message,
            f"✅ MID: {mid_name}\n\n"
            f"Step 2 of 2: Enter the bank name:\n\n"
            f"Example: SIPAY"
        )
        bot.register_next_step_handler(msg, lambda m: process_suppress_step2(m, mid_id, mid_name))

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('selmid_'))
def handle_mid_selection(call):
    """Handle MID selection for suppress"""
    try:
        mid_id = call.data.replace('selmid_', '')

        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT DISTINCT mid_name FROM transactions WHERE mid_id = %s LIMIT 1", (mid_id,))
            result = cursor.fetchone()

        if not result:
            bot.answer_callback_query(call.id, "❌ MID not found")
            return

        mid_name = result['mid_name']
        bot.answer_callback_query(call.id)

        msg = bot.send_message(
            call.message.chat.id,
            f"✅ MID: {mid_name}\n\n"
            f"Step 2 of 2: Enter the bank name:\n\n"
            f"Example: SIPAY"
        )
        bot.register_next_step_handler(msg, lambda m: process_suppress_step2(m, mid_id, mid_name))

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)[:50]}")

def process_suppress_step2(message, mid_id, mid_name):
    """Step 2: Get bank name and add suppression"""
    bank_search = message.text.strip()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT DISTINCT bank_name
                FROM transactions
                WHERE mid_id = %s AND bank_name ILIKE %s
                ORDER BY bank_name
                LIMIT 10
            """, (mid_id, f'%{bank_search}%'))
            banks = cursor.fetchall()

        if not banks:
            bot.reply_to(message, f"❌ No banks found for this MID matching '{bank_search}'")
            return

        if len(banks) > 1:
            # Show buttons to select bank
            markup = types.InlineKeyboardMarkup(row_width=1)
            for bank in banks:
                bank_name = bank['bank_name']
                display_name = bank_name if len(bank_name) <= 50 else bank_name[:47] + "..."
                markup.add(types.InlineKeyboardButton(
                    display_name,
                    callback_data=f"supbank_{mid_id}_{bank_name[:30]}"
                ))

            bot.reply_to(message, f"Found {len(banks)} banks. Select one:", reply_markup=markup)
            return

        bank_name = banks[0]['bank_name']

        # Ask for reason
        msg = bot.reply_to(
            message,
            f"✅ Route: {mid_name} + {bank_name[:30]}\n\n"
            f"Final step: Enter the reason for suppression:\n\n"
            f"Example: Dead route, bank confirmed no fix planned"
        )
        bot.register_next_step_handler(msg, lambda m: save_suppression(m, mid_id, mid_name, bank_name))

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('supbank_'))
def handle_bank_for_suppress(call):
    """Handle bank selection for suppress"""
    try:
        parts = call.data.replace('supbank_', '').split('_', 1)
        if len(parts) < 2:
            bot.answer_callback_query(call.id, "❌ Invalid data")
            return

        mid_id = parts[0]
        bank_search = parts[1]

        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT DISTINCT mid_name, bank_name
                FROM transactions
                WHERE mid_id = %s AND bank_name ILIKE %s
                LIMIT 1
            """, (mid_id, f'%{bank_search}%'))
            result = cursor.fetchone()

        if not result:
            bot.answer_callback_query(call.id, "❌ Route not found")
            return

        mid_name = result['mid_name']
        bank_name = result['bank_name']

        bot.answer_callback_query(call.id)

        msg = bot.send_message(
            call.message.chat.id,
            f"✅ Route: {mid_name} + {bank_name[:30]}\n\n"
            f"Final step: Enter the reason for suppression:\n\n"
            f"Example: Dead route, bank confirmed no fix planned"
        )
        bot.register_next_step_handler(msg, lambda m: save_suppression(m, mid_id, mid_name, bank_name))

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)[:50]}")

def save_suppression(message, mid_id, mid_name, bank_name):
    """Save the suppression override"""
    reason = message.text.strip()

    if not reason or len(reason) < 3:
        bot.reply_to(message, "❌ Reason too short. Override not saved.")
        return

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alert_overrides (mid_id, mid_name, bank_name, override_action, reason, created_by, created_at)
                VALUES (%s, %s, %s, 'suppress', %s, %s, NOW())
                ON CONFLICT (mid_id, bank_name, override_action)
                DO UPDATE SET
                    reason = EXCLUDED.reason,
                    last_modified_at = NOW(),
                    last_modified_by = EXCLUDED.created_by,
                    is_active = true
            """, (mid_id, mid_name, bank_name, reason, message.from_user.username))
            conn.commit()

        bot.reply_to(
            message,
            f"✅ <b>Suppression Added</b>\n\n"
            f"Route: {mid_name}\n"
            f"Bank: {bank_name[:30]}\n"
            f"Reason: {reason}",
            parse_mode='HTML'
        )

        log_interaction(
            message.from_user.username,
            message.from_user.id,
            f"Suppress via menu: {mid_name} + {bank_name}",
            'suppress_via_menu',
            details={'mid_id': mid_id, 'bank_name': bank_name, 'reason': reason},
            success=True
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('alertalt_'))
def handle_alert_alternatives_callback(call):
    """Handle 'Show Alternatives' button click from alerts"""
    try:
        # Format: alertalt_{mid_id}_{bank_short}
        parts = call.data.replace('alertalt_', '').split('_', 1)
        if len(parts) < 2:
            bot.answer_callback_query(call.id, "❌ Invalid button data")
            return

        mid_id = parts[0]
        bank_search = parts[1]

        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT DISTINCT bank_name
                FROM transactions
                WHERE mid_id = %s AND bank_name ILIKE %s
                LIMIT 1
            """, (mid_id, f'%{bank_search}%'))
            result = cursor.fetchone()

        if not result:
            bot.answer_callback_query(call.id, "❌ Bank not found")
            return

        bank_name = result['bank_name']
        bot.answer_callback_query(call.id, f"Loading alternatives for {bank_name[:30]}...")

        show_alternatives_for_bank(
            call.message.chat.id,
            bank_name,
            username=call.from_user.username,
            user_id=call.from_user.id
        )

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)[:50]}")
        print(f"Alert alternatives error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('alertsup_'))
def handle_alert_suppress_callback(call):
    """Handle 'Suppress This Route' button click from alerts"""
    try:
        # Format: alertsup_{mid_id}_{bank_short}
        parts = call.data.replace('alertsup_', '').split('_', 1)
        if len(parts) < 2:
            bot.answer_callback_query(call.id, "❌ Invalid button data")
            return

        mid_id = parts[0]
        bank_search = parts[1]

        reason = "Suppressed via alert button"
        username = call.from_user.username or f"user_{call.from_user.id}"

        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT DISTINCT mid_name, bank_name
                FROM transactions
                WHERE mid_id = %s AND bank_name ILIKE %s
                LIMIT 1
            """, (mid_id, f'%{bank_search}%'))
            result = cursor.fetchone()

            if not result:
                bot.answer_callback_query(call.id, "❌ Route not found")
                return

            mid_name = result['mid_name']
            bank_name = result['bank_name']

            cursor.execute("""
                INSERT INTO alert_overrides (mid_id, mid_name, bank_name, override_action, reason, created_by, created_at)
                VALUES (%s, %s, %s, 'suppress', %s, %s, NOW())
                ON CONFLICT (mid_id, bank_name, override_action)
                DO UPDATE SET
                    reason = EXCLUDED.reason,
                    last_modified_at = NOW(),
                    last_modified_by = EXCLUDED.created_by,
                    is_active = true
            """, (mid_id, mid_name, bank_name, reason, username))
            conn.commit()

        bot.answer_callback_query(call.id, "✅ Route suppressed!")

        # Send confirmation message
        bot.send_message(
            call.message.chat.id,
            f"✅ <b>Route Suppressed</b>\n\n"
            f"<b>MID:</b> {mid_name}\n"
            f"<b>Bank:</b> {bank_name[:50]}\n\n"
            f"Future alerts for this route will be suppressed.\n"
            f"It will auto-resume if the route recovers.",
            parse_mode='HTML'
        )

        # Log interaction
        log_interaction(
            username,
            call.from_user.id,
            f"Suppress via alert: {mid_name} + {bank_name}",
            'suppress_via_alert',
            details={'mid_id': mid_id, 'bank_name': bank_name},
            success=True
        )

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {str(e)[:50]}")
        print(f"Alert suppress error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('suppress_'))
def handle_suppress_callback(call):
    """Handle suppress button clicks from alert messages"""
    try:
        # Extract MID and Bank from callback data
        # Format: suppress_<mid_id>_<bank_name_hash>
        parts = call.data.split('_', 2)
        if len(parts) < 3:
            bot.answer_callback_query(call.id, "❌ Invalid button data")
            return

        mid_id = parts[1]
        bank_hash = parts[2]

        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT DISTINCT mid_name, bank_name
                FROM transactions
                WHERE mid_id = %s
                LIMIT 1
            """, (mid_id,))
            route = cursor.fetchone()

        if not route:
            bot.answer_callback_query(call.id, "❌ Route not found")
            return

        msg = bot.send_message(
            call.message.chat.id,
            f"Adding permanent suppression for:\n{route['mid_name']} + {route['bank_name'][:30]}\n\n"
            f"Please reply with the reason:"
        )
        bot.register_next_step_handler(msg, lambda m: save_override_from_button(
            m, mid_id, route['mid_name'], route['bank_name'], 'suppress'
        ))

        bot.answer_callback_query(call.id, "✅ Please provide a reason")

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('alert_'))
def handle_alert_callback(call):
    """Handle force alert button clicks"""
    try:
        parts = call.data.split('_', 2)
        if len(parts) < 3:
            bot.answer_callback_query(call.id, "❌ Invalid button data")
            return

        mid_id = parts[1]
        bank_hash = parts[2]

        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT DISTINCT mid_name, bank_name
                FROM transactions
                WHERE mid_id = %s
                LIMIT 1
            """, (mid_id,))
            route = cursor.fetchone()

        if not route:
            bot.answer_callback_query(call.id, "❌ Route not found")
            return

        msg = bot.send_message(
            call.message.chat.id,
            f"Adding force alert for:\n{route['mid_name']} + {route['bank_name'][:30]}\n\n"
            f"Please reply with the reason:"
        )
        bot.register_next_step_handler(msg, lambda m: save_override_from_button(
            m, mid_id, route['mid_name'], route['bank_name'], 'force_alert'
        ))

        bot.answer_callback_query(call.id, "✅ Please provide a reason")

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'dismiss')
def handle_dismiss_callback(call):
    """Handle dismiss button - just acknowledge"""
    bot.answer_callback_query(call.id, "✅ Dismissed")
    # Optionally edit the message to show it was dismissed
    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
    except:
        pass

def save_override_from_button(message, mid_id, mid_name, bank_name, override_action):
    """Save override from button interaction"""
    reason = message.text.strip()

    if not reason or len(reason) < 3:
        bot.reply_to(message, "❌ Reason too short. Override not saved.")
        return

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alert_overrides (mid_id, mid_name, bank_name, override_action, reason, created_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (mid_id, bank_name, override_action)
                DO UPDATE SET
                    reason = EXCLUDED.reason,
                    last_modified_at = NOW(),
                    last_modified_by = EXCLUDED.created_by,
                    is_active = true
            """, (mid_id, mid_name, bank_name, override_action, reason, message.from_user.username))
            conn.commit()

        action_display = "🔇 Suppression" if override_action == 'suppress' else "🔔 Force Alert"

        bot.reply_to(
            message,
            f"✅ <b>{action_display} Added</b>\n\n"
            f"Route: {mid_name}\n"
            f"Bank: {bank_name[:30]}\n"
            f"Reason: {reason}",
            parse_mode='HTML'
        )

        log_interaction(
            message.from_user.username,
            message.from_user.id,
            f"Button override: {override_action}",
            'override_from_button',
            details={'mid_id': mid_id, 'action': override_action},
            success=True
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")
        log_interaction(
            message.from_user.username,
            message.from_user.id,
            "Button override failed",
            'override_from_button',
            success=False,
            error_message=str(e)
        )

# ============================================================================
# MAIN BOT LOOP
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 Payment Alert Management Bot")
    print("=" * 60)
    print()
    print("Bot is starting...")
    print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"Database: {DB_CONFIG['dbname']} @ {DB_CONFIG['host']}")
    print()
    print("Commands available:")
    print("  /start - Show welcome message")
    print("  /help - Show all commands")
    print("  /override - Manage alert overrides")
    print("  /stats - View statistics")
    print("  /alternatives - Find alternative routes")
    print("  /recovered - Check recovered routes")
    print("  /check - Health check for route")
    print("  /test - Simulate alert decision")
    print("  /config - Configuration (admin only)")
    print("  /status - System status")
    print()
    print("✅ Bot is ready! Press Ctrl+C to stop.")
    print("=" * 60)
    print()

    try:
        bot.polling(none_stop=True, timeout=60)
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n\n❌ Bot crashed: {e}")
        import traceback
        traceback.print_exc()
