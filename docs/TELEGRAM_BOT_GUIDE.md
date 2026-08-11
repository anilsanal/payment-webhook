# Payment Alert Management Bot - Setup & Usage Guide

## Overview

The Telegram Bot provides an interactive interface for managing payment alert overrides, viewing statistics, and monitoring route health.

## Features

### ✅ Complete Features
- **Authentication System** - Role-based access control (admin, user, readonly)
- **Override Management** - Suppress or force alerts for specific routes
- **Statistics Dashboard** - View alert and suppression metrics
- **Alternative Routes** - Find better performing routes for a bank
- **Recovery Detection** - Monitor when suppressed routes recover
- **Route Health Check** - Detailed performance analysis
- **Alert Simulation** - Test what would happen if route triggers alert
- **Configuration Management** - Adjust thresholds and settings (admin only)
- **Interactive Buttons** - Quick actions on suppression messages
- **Audit Logging** - Track all bot interactions

---

## Setup Instructions

### Step 1: Get Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow prompts to create your bot:
   - Bot name: "Payment Alert Manager" (or your choice)
   - Bot username: Must end in "bot" (e.g., `your_company_alert_bot`)
4. Copy the bot token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Configure Bot Token

Edit the environment file:
```bash
nano /opt/payment-webhook/.env
```

Add your bot token:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here  # Optional: for direct messages
```

### Step 3: Add Authorized User

Add your Telegram username to the authorized users list:

```bash
/opt/payment-webhook/add_telegram_user.sh YOUR_TELEGRAM_USERNAME admin
```

Example:
```bash
/opt/payment-webhook/add_telegram_user.sh john_doe admin
```

**Note:** Your Telegram username is what appears in your profile (e.g., @john_doe). Do NOT include the @ symbol.

### Step 4: Start the Bot

Enable and start the bot service:

```bash
# Enable bot to start on system boot
sudo systemctl enable payment-alert-bot

# Start the bot now
sudo systemctl start payment-alert-bot

# Check status
sudo systemctl status payment-alert-bot

# View logs
sudo journalctl -u payment-alert-bot -f
```

### Step 5: Connect to Bot in Telegram

1. Open Telegram
2. Search for your bot username (e.g., @your_company_alert_bot)
3. Click "Start" or send `/start`
4. You should see a welcome message!

---

## Available Commands

### Basic Commands

#### `/start`
Show welcome message and bot information.

#### `/help`
Display all available commands with examples.

### Override Management

#### `/override list`
List all active overrides.

Example output:
```
🔇 Active Overrides (3)

1. Networxpay - LIVE - 3 + SIPAY
   Action: Suppress
   Reason: Dead route, no recovery expected
   By: john_doe | 2 days ago
   [Remove #123]

2. Networxpay - LIVE - 8 + Ziraat
   Action: Force Alert
   Reason: Critical route for high-value transactions
   By: jane_doe | 5 hours ago
   [Remove #124]
```

#### `/override suppress <MID> <BANK>`
Add a route to permanent suppression (won't send alerts).

Example:
```
/override suppress Networxpay - LIVE - 3 SIPAY
```

The bot will ask for a reason. Reply with your reason:
```
Dead route, bank confirmed issue won't be fixed
```

#### `/override alert <MID> <BANK>`
Force alerts for a route even if it's normally suppressed.

Example:
```
/override alert Networxpay - LIVE - 5 ZIRAAT
```

#### `/override remove <MID> <BANK>`
Remove an override.

Example:
```
/override remove Networxpay - LIVE - 3 SIPAY
```

Or click `[Remove #123]` button in `/override list` output.

### Statistics

#### `/stats today`
Show today's alert and suppression statistics.

Example output:
```
📊 Today's Statistics

Alerts:
• Sent: 12
• Suppressed: 8
• Noise Reduction: 40.0%

Suppression Breakdown:
• 🔴 Dead Routes: 6
• 🟡 Low Success: 2
```

#### `/stats week`
Show last 7 days statistics with daily averages.

### Query Commands

#### `/alternatives <BANK>`
Find alternative routes for a specific bank.

Example:
```
/alternatives SIPAY
```

Output:
```
💡 Routes for SIPAY ELEKTRONIK...

✅ Working Routes (2):
1. 🟢 Networxpay - LIVE - 5
   Success: 29.5% (78 txns)
2. 🟡 Networxpay - LIVE - 9
   Success: 11.1% (81 txns)

🔴 Dead Routes (1):
• Networxpay - LIVE - 3: 0.6%
```

#### `/recovered`
Check if any suppressed routes have recovered.

Example output:
```
✅ RECOVERED ROUTES (2)

Routes that were suppressed but have recovered:

1. Networxpay - LIVE - 7
   Bank: TURKIYE VAKIFLAR BANKASI
   📊 Was: 3.2% → Now: 45.1% (+41.9%)
   🔔 Alerts will resume for this route

💡 These routes now pass the 10% threshold
```

#### `/check <MID> <BANK>`
Detailed health check for a specific route.

Example:
```
/check Networxpay - LIVE - 3 SIPAY
```

Output:
```
🔍 Route Health Check

Route: Networxpay - LIVE - 3
Bank: SIPAY ELEKTRONIK...

Status: 🔴 DEAD
Route has consistently low success rate

📊 Performance (Last 7 days):
• Success: 1/156 (0.6%)
• Declined: 155

📊 Performance (Last 30 days):
• Success: 5/623 (0.8%)

Override: 🔇 Forced Suppression
• Reason: Dead route
• By: john_doe

Alert Decision: 🔇 Suppressed (manual override)
```

#### `/test <MID> <BANK>`
Simulate what would happen if this route triggered an alert right now.

Example:
```
/test Networxpay - LIVE - 5 SIPAY
```

Output:
```
🧪 Alert Simulation

Route: Networxpay - LIVE - 5
Bank: SIPAY ELEKTRONIK...
Success Rate (7d): 29.5%

✅ Result: Alert SENT
📌 Reason: Healthy route (success ≥ 10%)
```

### Configuration (Admin Only)

#### `/config show`
Show current smart filtering configuration.

#### `/config threshold <VALUE>`
Set success rate threshold (0-100).

Example:
```
/config threshold 15
```

This changes the threshold to 15% (routes below 15% will be suppressed).

#### `/config enable`
Enable smart filtering.

#### `/config disable`
Disable smart filtering (all alerts will be sent).

### System Status

#### `/status`
Show bot and system health status.

Example output:
```
🤖 Bot Status

🔌 System Health:
• Bot: ✅ Running
• Database: ✅ Connected
• Server Time: 2024-01-15 14:32:10 UTC

📊 Activity:
• Last Alert: 5m ago
• Last Suppression: 12m ago
• Active Overrides: 3
• Authorized Users: 5

ℹ️ Monitoring:
• Runs every 5 minutes
• Daily reports at 09:00 UTC
• Smart filtering: Active
```

---

## Interactive Buttons

When a route is suppressed by smart filtering, the system can send a message with interactive buttons:

```
🔇 Route Suppressed

Networxpay - LIVE - 3 + SIPAY
Success Rate: 0.6% (1/156)
Reason: Dead route

💡 Alternatives available:
→ Networxpay - LIVE - 5: 29.5%

[Permanent Suppress] [Force Alert] [Dismiss]
```

Click a button to:
- **Permanent Suppress** - Add to override table (won't alert again)
- **Force Alert** - Override suppression (always alert for this route)
- **Dismiss** - Just acknowledge, no action taken

---

## User Roles

### Admin
- Can use all commands
- Can modify configuration (`/config threshold`, `/config enable/disable`)
- Can add/remove overrides
- Can view all statistics

### User
- Can use most commands
- Can add/remove overrides
- Can view statistics
- Cannot modify configuration

### Readonly
- Can view statistics (`/stats`)
- Can check route health (`/check`, `/test`)
- Can view alternatives (`/alternatives`)
- Cannot add/remove overrides
- Cannot modify configuration

---

## Usage Examples

### Example 1: Suppress a Noisy Route

You keep getting alerts for a route that you know is broken and won't be fixed:

```
You: /override suppress Networxpay - LIVE - 3 SIPAY
Bot: Please reply with the reason:
You: Bank confirmed issue on their end, no fix planned
Bot: ✅ Suppression Added
     Route: Networxpay - LIVE - 3
     Bank: SIPAY ELEKTRONIK...
     Reason: Bank confirmed issue on their end, no fix planned
```

Now you won't get alerts for this route.

### Example 2: Find Better Route for a Bank

A route is broken, you need to find an alternative:

```
You: /alternatives SIPAY
Bot: 💡 Routes for SIPAY ELEKTRONIK...

     ✅ Working Routes (2):
     1. 🟢 Networxpay - LIVE - 5
        Success: 29.5% (78 txns)
     2. 🟡 Networxpay - LIVE - 9
        Success: 11.1% (81 txns)
```

Switch your routing to use Networxpay - LIVE - 5 instead.

### Example 3: Check If Suppressed Route Recovered

```
You: /recovered
Bot: ✅ RECOVERED ROUTES (1)

     1. Networxpay - LIVE - 7
        Bank: TURKIYE VAKIFLAR BANKASI
        📊 Was: 3.2% → Now: 45.1% (+41.9%)
        🔔 Alerts will resume for this route
```

The route recovered! You might want to remove the override:

```
You: /override remove Networxpay - LIVE - 7 ZIRAAT
```

### Example 4: Test Alert Decision

Before adding an override, test what would happen:

```
You: /test Networxpay - LIVE - 3 SIPAY
Bot: 🧪 Alert Simulation

     Route: Networxpay - LIVE - 3
     Bank: SIPAY ELEKTRONIK...
     Success Rate (7d): 0.6%

     🔇 Result: Alert SUPPRESSED
     📌 Reason: Dead route (success < 10%)
```

The route is already being suppressed automatically. No need to add override unless you want permanent suppression.

---

## Troubleshooting

### Bot Not Responding

1. Check bot is running:
   ```bash
   sudo systemctl status payment-alert-bot
   ```

2. Check logs for errors:
   ```bash
   sudo journalctl -u payment-alert-bot -n 50
   ```

3. Restart bot:
   ```bash
   sudo systemctl restart payment-alert-bot
   ```

### "Not Authorized" Error

Your Telegram username is not in the authorized users list.

Add yourself:
```bash
/opt/payment-webhook/add_telegram_user.sh YOUR_USERNAME admin
```

Then try `/start` again.

### Commands Not Working

1. Make sure you're typing commands correctly (case-sensitive)
2. Check you have the right role for the command
3. Check bot logs for error messages

### Database Connection Errors

Check PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

Check .env file has correct database credentials:
```bash
cat /opt/payment-webhook/.env | grep DB_
```

---

## Management Commands

### Add User
```bash
/opt/payment-webhook/add_telegram_user.sh USERNAME ROLE
```

### Remove User
```bash
sudo -u postgres psql -d payment_transactions -c \
  "UPDATE telegram_authorized_users SET is_active = false WHERE telegram_username = 'USERNAME';"
```

### List All Users
```bash
sudo -u postgres psql -d payment_transactions -c \
  "SELECT telegram_username, role, is_active, added_at FROM telegram_authorized_users;"
```

### View Bot Interactions (Audit Log)
```bash
sudo -u postgres psql -d payment_transactions -c \
  "SELECT telegram_username, command, action, success, created_at
   FROM telegram_bot_interactions
   ORDER BY created_at DESC
   LIMIT 20;"
```

### Check Active Overrides
```bash
sudo -u postgres psql -d payment_transactions -c \
  "SELECT mid_name, bank_name, override_action, reason, created_by
   FROM alert_overrides
   WHERE is_active = true;"
```

---

## Maintenance

### Update Bot Code

1. Edit the bot file:
   ```bash
   nano /opt/payment-webhook/telegram_bot.py
   ```

2. Restart the bot:
   ```bash
   sudo systemctl restart payment-alert-bot
   ```

### View Live Logs

```bash
sudo journalctl -u payment-alert-bot -f
```

Press Ctrl+C to stop viewing.

### Stop Bot

```bash
sudo systemctl stop payment-alert-bot
```

### Disable Bot (Prevent Auto-Start)

```bash
sudo systemctl disable payment-alert-bot
```

---

## Security Notes

- **Bot Token**: Keep your bot token secure. Anyone with the token can control your bot.
- **User Authorization**: Only add trusted users to the authorized users list.
- **Role Assignment**: Use 'readonly' role for users who should only view data.
- **Admin Role**: Limit admin role to trusted administrators only.
- **Audit Trail**: All bot interactions are logged in `telegram_bot_interactions` table.

---

## Database Tables

### alert_overrides
Stores manual overrides for routes.

Columns:
- `mid_id`, `mid_name`, `bank_name` - Route identifier
- `override_action` - 'suppress' or 'force_alert'
- `reason` - Why this override exists
- `created_by` - Telegram username who created it
- `is_active` - Boolean flag
- `expires_at` - Optional expiration timestamp

### telegram_authorized_users
Stores authorized bot users.

Columns:
- `telegram_username` - Telegram username
- `telegram_user_id` - Telegram numeric ID
- `role` - 'admin', 'user', or 'readonly'
- `is_active` - Boolean flag
- `added_at` - When user was added

### telegram_bot_interactions
Audit log of all bot interactions.

Columns:
- `telegram_username` - Who performed action
- `command` - What command was used
- `action` - What action was taken
- `details` - JSONB with additional details
- `success` - Boolean flag
- `error_message` - If failed, why
- `created_at` - When it happened

---

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u payment-alert-bot -f`
2. Review this guide
3. Check database tables for data issues
4. Contact system administrator

---

## Quick Reference Card

```
OVERRIDE COMMANDS
/override list                    - List all overrides
/override suppress MID BANK      - Suppress route
/override alert MID BANK         - Force alert route
/override remove MID BANK        - Remove override

STATISTICS
/stats today                     - Today's stats
/stats week                      - Weekly stats

QUERIES
/alternatives BANK               - Find alternatives
/recovered                       - Check recovered routes
/check MID BANK                  - Health check
/test MID BANK                   - Simulate alert

CONFIG (Admin)
/config show                     - Show config
/config threshold VALUE          - Set threshold
/config enable                   - Enable filtering
/config disable                  - Disable filtering

SYSTEM
/status                          - System status
/help                            - Show all commands
```

---

## Next Steps

After setup:
1. Add all team members: `/opt/payment-webhook/add_telegram_user.sh <username> <role>`
2. Test the bot: Send `/start` in Telegram
3. Try `/stats today` to see if data is loading
4. Use `/alternatives SIPAY` to test queries
5. Add an override to test: `/override suppress ...`
6. Check `/status` to confirm everything is working

Enjoy your new bot! 🤖
