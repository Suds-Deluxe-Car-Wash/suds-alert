"""
Suds Alert — Incident Escalation System for Suds Deluxe Car Wash
================================================================
Lightweight Slack-to-SMS escalation for critical operational incidents.
Routes /down and /quality slash commands to the right people via SMS.
"""

import os
import time
import hmac
import hashlib
import uuid
import logging
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from dotenv import load_dotenv

from config import ROUTING_GROUPS, CHANNEL_TO_GROUP, CONTACTS
from sms import send_sms_alerts
from db import init_db, log_incident, get_incident_count

load_dotenv()

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("suds_alert.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("suds_alert")

# ---------------------------------------------------------------------------
# Slack Request Verification
# ---------------------------------------------------------------------------
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")


def verify_slack_request(req) -> bool:
    """Verify that the incoming request is genuinely from Slack."""
    if not SLACK_SIGNING_SECRET:
        logger.warning("SLACK_SIGNING_SECRET not set — skipping verification (dev mode)")
        return True

    timestamp = req.headers.get("X-Slack-Request-Timestamp", "")
    signature = req.headers.get("X-Slack-Signature", "")

    # Reject requests older than 5 minutes (replay attack protection)
    if abs(time.time() - int(timestamp)) > 300:
        return False

    sig_basestring = f"v0:{timestamp}:{req.get_data(as_text=True)}"
    my_signature = (
        "v0="
        + hmac.new(
            SLACK_SIGNING_SECRET.encode(),
            sig_basestring.encode(),
            hashlib.sha256,
        ).hexdigest()
    )
    return hmac.compare_digest(my_signature, signature)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_location_from_channel(channel_name: str) -> str | None:
    """
    Extract the location identifier from a #<location>-management channel.
    Returns None if the channel doesn't match the expected format.
    """
    if not channel_name:
        return None
    # Strip leading # if present
    channel_name = channel_name.lstrip("#")
    if channel_name.endswith("-management"):
        return channel_name.replace("-management", "")
    return None


def resolve_routing(channel_name: str) -> dict | None:
    """
    Given a Slack channel name, determine which routing group applies
    and return the list of SMS recipients.
    """
    location = extract_location_from_channel(channel_name)
    if not location:
        return None

    group_key = CHANNEL_TO_GROUP.get(f"{location}-management")
    if not group_key:
        return None

    group = ROUTING_GROUPS[group_key]
    recipients = []
    for name in group["recipients"]:
        contact = CONTACTS.get(name)
        if contact:
            recipients.append({"name": name, "phone": contact})

    return {
        "location": location,
        "group": group_key,
        "region": group["region"],
        "recipients": recipients,
    }


def generate_incident_id() -> str:
    """Generate a short, human-friendly incident reference ID."""
    count = get_incident_count() + 10001
    return f"INC-{count}"


# ---------------------------------------------------------------------------
# Slack Slash Command Endpoint
# ---------------------------------------------------------------------------

@app.route("/slack/commands", methods=["POST"])
def handle_slash_command():
    """
    Unified handler for /down and /quality slash commands.
    Slack sends form-encoded POST data.
    """
    # 1. Verify Slack request authenticity
    if not verify_slack_request(request):
        logger.warning("Failed Slack signature verification")
        return jsonify({"response_type": "ephemeral", "text": "⚠️ Request verification failed."}), 401

    # 2. Parse the slash command payload
    command = request.form.get("command", "").strip()        # e.g. "/down" or "/quality"
    description = request.form.get("text", "").strip()       # free-text description
    channel_name = request.form.get("channel_name", "")      # e.g. "kyle-management"
    user_name = request.form.get("user_name", "")            # Slack username
    user_id = request.form.get("user_id", "")                # Slack user ID

    # 3. Determine incident type
    incident_type = "DOWN" if command in ("/down", "/suds-down") else "QUALITY"

    # 4. Validate description
    if not description:
        return jsonify({
            "response_type": "ephemeral",
            "text": f"⚠️ Please include a description.\nUsage: `{command} <description of the issue>`",
        })

    # 5. Resolve location and routing from channel name
    routing = resolve_routing(channel_name)

    if not routing:
        logger.warning(f"Routing failed for channel: #{channel_name}")
        return jsonify({
            "response_type": "ephemeral",
            "text": (
                "⚠️ This channel is not configured for alerts.\n"
                "Please use a `#<location>-management` channel."
            ),
        })

    # 6. Generate incident ID
    incident_id = generate_incident_id()
    location_display = routing["location"].upper().replace("-", " ")

    # 7. Send SMS notifications
    sms_body = (
        f"🚨 SUDS ALERT — {incident_type}\n"
        f"Location: {location_display}\n"
        f"\"{description}\"\n"
        f"Reported by: @{user_name}\n"
        f"Ref: {incident_id}"
    )

    sms_results = send_sms_alerts(routing["recipients"], sms_body)

    # 8. Log the incident
    log_incident(
        incident_id=incident_id,
        incident_type=incident_type,
        location=routing["location"],
        region=routing["region"],
        description=description,
        reporter=user_name,
        reporter_id=user_id,
        channel=channel_name,
        recipients=[r["name"] for r in routing["recipients"]],
        sms_results=sms_results,
    )

    # 9. Build Slack response
    notified_names = ", ".join(r["name"].title() for r in routing["recipients"])
    success_count = sum(1 for r in sms_results if r["status"] == "sent")
    total_count = len(sms_results)

    if success_count == total_count:
        slack_response = {
            "response_type": "in_channel",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"✅ *Alert sent*\n"
                            f"*Type:* {incident_type}\n"
                            f"*Location:* {location_display}\n"
                            f"*Notified:* {notified_names}\n"
                            f"*Ref:* `{incident_id}`"
                        ),
                    },
                },
            ],
        }
    else:
        slack_response = {
            "response_type": "in_channel",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"⚠️ *Alert partially sent* ({success_count}/{total_count} SMS delivered)\n"
                            f"*Type:* {incident_type}\n"
                            f"*Location:* {location_display}\n"
                            f"*Notified:* {notified_names}\n"
                            f"*Ref:* `{incident_id}`"
                        ),
                    },
                },
            ],
        }

    logger.info(f"[{incident_id}] {incident_type} at {location_display} — {success_count}/{total_count} SMS sent")
    return jsonify(slack_response)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "suds-alert", "timestamp": datetime.now(timezone.utc).isoformat()})


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 3000))
    debug = os.getenv("FLASK_ENV", "production") == "development"
    logger.info(f"🚀 Suds Alert starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
