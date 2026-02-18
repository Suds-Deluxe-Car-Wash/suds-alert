"""
Suds Alert — SMS Delivery via Twilio
======================================
Sends SMS alerts to recipients and tracks delivery status.
"""

import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER

logger = logging.getLogger("suds_alert")


def _get_twilio_client() -> Client | None:
    """Initialize Twilio client. Returns None if not configured."""
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER]):
        logger.warning("Twilio credentials not configured — SMS will be simulated")
        return None
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_sms_alerts(recipients: list[dict], body: str) -> list[dict]:
    """
    Send SMS to all recipients.

    Args:
        recipients: List of {"name": str, "phone": str}
        body: SMS message body

    Returns:
        List of delivery results: {"name", "phone", "status", "sid"|"error"}
    """
    client = _get_twilio_client()
    results = []

    for recipient in recipients:
        name = recipient["name"]
        phone = recipient["phone"]

        if not phone or phone == "+1XXXXXXXXXX":
            logger.warning(f"Skipping {name} — no phone number configured")
            results.append({
                "name": name,
                "phone": phone,
                "status": "skipped",
                "error": "Phone number not configured",
            })
            continue

        if client is None:
            # Dev/test mode — simulate sending
            logger.info(f"[SIMULATED SMS] → {name} ({phone}): {body[:60]}...")
            results.append({
                "name": name,
                "phone": phone,
                "status": "sent",
                "sid": "SIMULATED",
            })
            continue

        try:
            message = client.messages.create(
                body=body,
                from_=TWILIO_FROM_NUMBER,
                to=phone,
            )
            logger.info(f"SMS sent to {name} ({phone}) — SID: {message.sid}")
            results.append({
                "name": name,
                "phone": phone,
                "status": "sent",
                "sid": message.sid,
            })
        except TwilioRestException as e:
            logger.error(f"SMS failed for {name} ({phone}): {e}")
            results.append({
                "name": name,
                "phone": phone,
                "status": "failed",
                "error": str(e),
            })

    return results
