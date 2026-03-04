import os
import logging
from datetime import datetime
from typing import Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#general")
RE_ALERT_THRESHOLD: float = float(os.getenv("RE_ALERT_THRESHOLD", "75.0"))

# ── Client ────────────────────────────────────────────────────────────────────
_client: Optional[WebClient] = None


def get_slack_client() -> WebClient:
    global _client
    if _client is None:
        if not SLACK_BOT_TOKEN:
            raise ValueError("SLACK_BOT_TOKEN is not set. Add it to your .env file.")
        _client = WebClient(token=SLACK_BOT_TOKEN)
    return _client


def _build_re_alert_blocks(re_score, entity_name, entity_id, extra_context=None):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    severity = "🔴 CRITICAL" if re_score >= 90 else "🟠 HIGH" if re_score >= 75 else "🟡 MEDIUM"

    fields = [
        {"type": "mrkdwn", "text": f"*Entity:*\n{entity_name}"},
        {"type": "mrkdwn", "text": f"*Entity ID:*\n`{entity_id}`"},
        {"type": "mrkdwn", "text": f"*RE Score:*\n`{re_score:.2f}` / 100"},
        {"type": "mrkdwn", "text": f"*Threshold:*\n`{RE_ALERT_THRESHOLD}`"},
        {"type": "mrkdwn", "text": f"*Severity:*\n{severity}"},
        {"type": "mrkdwn", "text": f"*Triggered At:*\n{timestamp}"},
    ]

    if extra_context:
        for key, value in extra_context.items():
            fields.append({"type": "mrkdwn", "text": f"*{key}:*\n{value}"})

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "⚠️  AREE — High Risk Exposure Alert",
                "emoji": True,
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"{severity}  |  RE score of *{re_score:.2f}* "
                    f"exceeded threshold of *{RE_ALERT_THRESHOLD}* "
                    f"for *{entity_name}*."
                ),
            },
        },
        {
            "type": "section",
            "fields": fields[:6],
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "🤖 Sent by *AREE Monitoring System* · Phase 12",
                }
            ],
        },
    ]
    return blocks


def send_re_alert(re_score, entity_name, entity_id, channel=None, extra_context=None):
    if re_score <= RE_ALERT_THRESHOLD:
        return False

    target_channel = channel or SLACK_CHANNEL

    try:
        client = get_slack_client()
        blocks = _build_re_alert_blocks(re_score, entity_name, entity_id, extra_context)

        response = client.chat_postMessage(
            channel=target_channel,
            text=f"⚠️ AREE Alert: RE score {re_score:.2f} for {entity_name} exceeded threshold {RE_ALERT_THRESHOLD}",
            blocks=blocks,
        )
        logger.info("Slack alert sent. ts=%s", response["ts"])
        return True

    except SlackApiError as e:
        logger.error("Slack API error: %s", e.response["error"])
        return False
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return False


def send_custom_message(text: str, channel=None) -> bool:
    target_channel = channel or SLACK_CHANNEL
    try:
        client = get_slack_client()
        client.chat_postMessage(channel=target_channel, text=text)
        logger.info("Slack message sent to %s.", target_channel)
        return True
    except SlackApiError as e:
        logger.error("Slack API error: %s", e.response["error"])
        return False
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        return False


def test_slack_connection() -> bool:
    return send_custom_message(
        f"✅ AREE Slack integration is live! Alerts will fire when RE > {RE_ALERT_THRESHOLD}."
    )