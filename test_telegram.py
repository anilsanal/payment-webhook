#!/usr/bin/env python3
"""
Quick test script to verify Telegram bot can send messages
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/opt/payment-webhook/.env')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_IDS = [id.strip() for id in os.getenv('TELEGRAM_CHANNEL_ID', '').split(',') if id.strip()]

def send_test_message():
    """Send a test message to all configured channels"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    success_count = 0

    for channel_id in TELEGRAM_CHANNEL_IDS:
        message = """
🤖 **Polpay Monitor Bot - Active**

✅ Bot successfully configured!

━━━━━━━━━━━━━━━━━━━━━
**Configuration:**
• Channel ID: `{channel_id}`
• Bot: @PolpayMonitorBot
• Status: ✅ Online

━━━━━━━━━━━━━━━━━━━━━
**What's Next:**
The monitoring system will track:
• MID + Bank performance
• Decline rates (5min, 15min, 30min)
• Success rate drops
• Real-time alerts

━━━━━━━━━━━━━━━━━━━━━
🚀 System will be active in a few minutes!
""".format(channel_id=channel_id)

        payload = {
            'chat_id': channel_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        try:
            response = requests.post(url, json=payload)
            data = response.json()

            if data.get('ok'):
                print(f"✅ Test message sent successfully to channel {channel_id}")
                print(f"   Message ID: {data['result']['message_id']}")
                success_count += 1
            else:
                print(f"❌ Failed to send to channel {channel_id}: {data.get('description')}")
        except Exception as e:
            print(f"❌ Error sending to channel {channel_id}: {e}")

    print(f"\n📊 Results: {success_count}/{len(TELEGRAM_CHANNEL_IDS)} channels successful")
    return success_count == len(TELEGRAM_CHANNEL_IDS)

if __name__ == "__main__":
    print("Testing Telegram bot...")
    send_test_message()
