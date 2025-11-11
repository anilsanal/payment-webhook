#!/usr/bin/env python3
"""
Telegram Bot Setup and Testing Script
Helps you get your channel ID and test the bot
"""

import requests
import sys

TELEGRAM_BOT_TOKEN = "8237771288:AAFvEX6RDJzID5KoPITr62SsCcYm39HSmlw"

def test_bot_token():
    """Test if the bot token is valid"""
    print("=" * 60)
    print("Testing Bot Token...")
    print("=" * 60)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"

    try:
        response = requests.get(url)
        data = response.json()

        if data.get('ok'):
            bot_info = data['result']
            print(f"✅ Bot token is valid!")
            print(f"   Bot Name: {bot_info['first_name']}")
            print(f"   Username: @{bot_info['username']}")
            print(f"   Bot ID: {bot_info['id']}")
            return True
        else:
            print(f"❌ Bot token is invalid: {data.get('description')}")
            return False
    except Exception as e:
        print(f"❌ Error testing bot: {e}")
        return False

def get_updates():
    """Get recent updates to find channel ID"""
    print("\n" + "=" * 60)
    print("Getting Channel Updates...")
    print("=" * 60)
    print("\n📝 INSTRUCTIONS:")
    print("   1. Add your bot (@PolpayMonitorBot) to your channel as admin")
    print("   2. Post ANY message in your channel")
    print("   3. Wait 5 seconds, then press Enter here")
    print()
    input("Press Enter when ready...")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"

    try:
        response = requests.get(url)
        data = response.json()

        if not data.get('ok'):
            print(f"❌ Failed to get updates: {data.get('description')}")
            return

        updates = data.get('result', [])

        if not updates:
            print("\n⚠️  No updates found!")
            print("   Make sure you:")
            print("   1. Added the bot to your channel as administrator")
            print("   2. Posted a message in the channel")
            print("   3. Waited a few seconds")
            return

        print(f"\n✅ Found {len(updates)} updates!")
        print("\n" + "=" * 60)
        print("CHANNEL IDs FOUND:")
        print("=" * 60)

        channel_ids = set()

        for update in updates:
            # Check for channel posts
            if 'channel_post' in update:
                chat = update['channel_post']['chat']
                channel_id = chat['id']
                channel_title = chat.get('title', 'Unknown')
                channel_type = chat.get('type', 'Unknown')

                channel_ids.add((channel_id, channel_title, channel_type))

            # Check for messages in groups/channels
            if 'message' in update:
                chat = update['message']['chat']
                if chat['type'] in ['channel', 'supergroup']:
                    channel_id = chat['id']
                    channel_title = chat.get('title', 'Unknown')
                    channel_type = chat.get('type', 'Unknown')

                    channel_ids.add((channel_id, channel_title, channel_type))

        if channel_ids:
            for channel_id, title, chat_type in channel_ids:
                print(f"\n📢 Channel: {title}")
                print(f"   Type: {chat_type}")
                print(f"   ID: {channel_id}")
                print(f"   👉 USE THIS ID: {channel_id}")
        else:
            print("\n⚠️  No channel IDs found in updates")
            print("   The bot might not have admin rights in the channel")

    except Exception as e:
        print(f"❌ Error getting updates: {e}")

def test_send_message(channel_id):
    """Test sending a message to the channel"""
    print("\n" + "=" * 60)
    print("Testing Message Send...")
    print("=" * 60)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    message = """
🤖 **Bot Test Message**

✅ Your Polpay Monitor Bot is working!

This is a test message to verify the bot can post to this channel.

━━━━━━━━━━━━━━━━━━━━━
Next steps:
1. The monitoring system will be configured
2. You'll receive alerts when payment issues are detected
3. Alerts will show MID + Bank performance metrics
"""

    payload = {
        'chat_id': channel_id,
        'text': message,
        'parse_mode': 'Markdown'
    }

    try:
        response = requests.post(url, json=payload)
        data = response.json()

        if data.get('ok'):
            print(f"✅ Test message sent successfully!")
            print(f"   Message ID: {data['result']['message_id']}")
            print(f"   Check your channel to see the message!")
            return True
        else:
            print(f"❌ Failed to send message: {data.get('description')}")
            print(f"   Make sure the bot is an admin in the channel")
            return False
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def main():
    print("\n🤖 Polpay Monitor Bot - Setup Script\n")

    # Step 1: Test bot token
    if not test_bot_token():
        sys.exit(1)

    # Step 2: Get channel ID
    get_updates()

    # Step 3: Test sending message
    print("\n" + "=" * 60)
    channel_id = input("\nEnter your channel ID (from above): ").strip()

    if not channel_id:
        print("❌ No channel ID provided. Exiting.")
        sys.exit(1)

    # Validate channel ID format
    try:
        channel_id_int = int(channel_id)
        if channel_id_int > 0:
            print("⚠️  Warning: Channel IDs are usually negative numbers")
    except ValueError:
        print("❌ Invalid channel ID format")
        sys.exit(1)

    # Test sending message
    if test_send_message(channel_id):
        print("\n" + "=" * 60)
        print("✅ SETUP COMPLETE!")
        print("=" * 60)
        print(f"\nYour configuration:")
        print(f"  Bot Token: {TELEGRAM_BOT_TOKEN}")
        print(f"  Channel ID: {channel_id}")
        print("\nSave these values - they will be configured in the monitoring system.")
        print("=" * 60)
    else:
        print("\n❌ Setup incomplete. Please check the errors above.")

if __name__ == "__main__":
    main()
