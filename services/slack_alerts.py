import os
from slack_sdk import WebClient
from dotenv import load_dotenv

load_dotenv()

client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

def send_slack(message: str, channel="U0AJJT1UZ0A"):
    client.chat_postMessage(channel=channel, text=message)
    print(f"✅ Slack sent: {message}")