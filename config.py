"""
Suds Alert — Configuration
===========================
Location-based routing rules, contacts, and channel mappings.

To add a new location:
  1. Add the channel to the appropriate group in ROUTING_GROUPS
  2. CHANNEL_TO_GROUP is auto-generated — no manual update needed

To add/change a contact's phone number:
  Update CONTACTS dict (or use env vars for production)
"""

import os

# ---------------------------------------------------------------------------
# SMS Contacts (phone numbers from environment variables)
# ---------------------------------------------------------------------------
# In production, set these as env vars: PHONE_SHAHAN=+15551234567, etc.
# Fallback values here are placeholders — REPLACE before deploying.

CONTACTS = {
    "shahan": os.getenv("PHONE_SHAHAN", "+1XXXXXXXXXX"),
    "tom":    os.getenv("PHONE_TOM",    "+1XXXXXXXXXX"),
    "rick":   os.getenv("PHONE_RICK",   "+1XXXXXXXXXX"),
    "andy":   os.getenv("PHONE_ANDY",    "+1XXXXXXXXXX"),
    "roman":  os.getenv("PHONE_ROMAN",  "+1XXXXXXXXXX"),
}


# ---------------------------------------------------------------------------
# Routing Groups
# ---------------------------------------------------------------------------
ROUTING_GROUPS = {
    "group_a": {
        "region": "Central Texas / Austin",
        "recipients": ["tom", "rick", "shahan"],
        "channels": [
            "austin-management",
            "commerce-management",
            "culebra-management",
            "georgetown-management",
            "kyle-management",
            "round-rock-management",
            "san-marcos-ww-management",
            "sm35-management",
        ],
    },
    "group_b": {
        "region": "Houston",
        "recipients": ["andy", "roman", "shahan"],
        "channels": [
            "bissonnet-management",
            "hwy-6-management",
            "pasadena-management",
            "stafford-management",
            "sugar-land-management",
            "tomball-management",
        ],
    },
}


# ---------------------------------------------------------------------------
# Auto-generated: Channel → Group lookup
# ---------------------------------------------------------------------------
CHANNEL_TO_GROUP: dict[str, str] = {}
for group_key, group_data in ROUTING_GROUPS.items():
    for channel in group_data["channels"]:
        CHANNEL_TO_GROUP[channel] = group_key


# ---------------------------------------------------------------------------
# Twilio Configuration
# ---------------------------------------------------------------------------
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")  # e.g. "+15559876543"
TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID", "")  # e.g. "MGxxxxxxxx"
