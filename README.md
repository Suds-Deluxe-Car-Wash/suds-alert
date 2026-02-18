# 🚨 Suds Alert

**Incident Escalation System for Suds Deluxe Car Wash**

Lightweight Slack-to-SMS escalation that routes critical operational incidents (`/down`, `/quality`) to the right leadership team via SMS — based on which location channel the command is sent from.

---

## How It Works

```
Site staff runs /down or /quality in #kyle-management
        ↓
System extracts location from channel name
        ↓
Looks up routing group (Central TX → Tom, Rick, Shahan)
        ↓
Sends SMS to all recipients via Twilio
        ↓
Confirms delivery in Slack + logs to database
```

## Quick Start

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd suds-alert
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your real credentials
```

### 3. Run Locally

```bash
python app.py
```

The server starts on `http://localhost:3000`. Use ngrok for Slack testing:

```bash
ngrok http 3000
```

### 4. Run Tests

```bash
python -m pytest tests.py -v
```

---

## Slack App Setup

### Create the Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App**
2. Choose **From scratch**, name it **Suds Alert**
3. Select your Suds Deluxe workspace

### Add Slash Commands

Go to **Slash Commands** → Create two commands:

| Command     | Request URL                          | Description                          |
|-------------|--------------------------------------|--------------------------------------|
| `/down`     | `https://your-domain.com/slack/commands` | Report a wash outage or critical failure |
| `/quality`  | `https://your-domain.com/slack/commands` | Report wash quality or CX issues     |

### Get Signing Secret

Go to **Basic Information** → Copy **Signing Secret** → Add to `.env` as `SLACK_SIGNING_SECRET`

### Install to Workspace

Go to **Install App** → Install to your workspace

---

## Twilio Setup

1. Sign up at [twilio.com](https://www.twilio.com)
2. Get a phone number with SMS capability
3. Copy your Account SID, Auth Token, and phone number to `.env`

---

## Deployment Options

### Option A: Railway / Render / Fly.io (Recommended)

Most PaaS platforms auto-detect the `Dockerfile`. Just push and set env vars in the dashboard.

**Railway:**
```bash
railway init
railway up
```

**Render:**
- Connect your repo → New Web Service → it detects the Dockerfile automatically.

### Option B: Docker

```bash
docker build -t suds-alert .
docker run -p 3000:3000 --env-file .env suds-alert
```

### Option C: Direct (VPS/EC2)

```bash
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:3000 --workers 2 app:app
```

---

## Routing Configuration

Routing is defined in `config.py`. To add a new location:

1. Add the `#<location>-management` channel to the appropriate group
2. That's it — the channel-to-group mapping is auto-generated

### Current Routing

| Group | Region | Recipients | Channels |
|-------|--------|-----------|----------|
| A | Central TX / Austin | Tom, Rick, Shahan | austin, commerce, culebra, georgetown, kyle, round-rock, san-marcos-ww, sm35 |
| B | Houston | Andy, Roman, Shahan | bissonnet, hwy-6, pasadena, stafford, sugar-land, tomball |

---

## Project Structure

```
suds-alert/
├── app.py           # Flask app — slash command handler
├── config.py        # Routing groups, contacts, settings
├── sms.py           # Twilio SMS delivery
├── db.py            # SQLite incident logging
├── tests.py         # Test suite
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

## SMS Format

```
🚨 SUDS ALERT — DOWN
Location: KYLE
"Tunnel stopped, conveyor not moving"
Reported by: @jose
Ref: INC-10421
```

## Slack Response Format

**Success:**
```
✅ Alert sent
Type: DOWN
Location: KYLE
Notified: Tom, Rick, Shahan
Ref: INC-10421
```

**Failure (unrecognized channel):**
```
⚠️ This channel is not configured for alerts.
Please use a #<location>-management channel.
```
