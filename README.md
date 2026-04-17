# Vunoh Global — AI Task Assistant

An AI-powered web application that helps Kenyans in the diaspora initiate and track services back home. Customers describe what they need in plain English. The system extracts intent, scores risk, generates fulfilment steps, assigns to the right team, and sends structured confirmations across three channels.

---

## Stack

| Layer    | Choice              |
|----------|---------------------|
| Backend  | Python + Flask (Blueprints) |
| Frontend | HTML, CSS, Vanilla JS |
| Database | Supabase (PostgreSQL) |
| AI       | Groq (Llama 3.1 8B Instant)  |

---

## Project Structure

```
vunoh/
├── app/
│   ├── __init__.py               # App factory
│   ├── blueprints/
│   │   ├── tasks/                # Task submission + status update routes
│   │   ├── dashboard/            # Dashboard page + tasks API
│   │   └── messages/             # Message retrieval
│   ├── services/
│   │   ├── ai_service.py         # Groq prompts: intent, steps, messages
│   │   ├── risk_service.py       # Risk scoring logic
│   │   └── supabase_service.py   # All database operations
│   ├── static/
│   │   ├── css/main.css
│   │   └── js/main.js
│   └── templates/
│       └── dashboard/index.html
├── migrations/
│   └── schema.sql                # Full schema + 5 sample tasks
├── config.py
├── run.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

### 1. Clone and create environment

```bash
git clone <your-repo-url>
cd vunoh
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in:

```
GROQ_API_KEY=your_groq_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
FLASK_SECRET_KEY=some-random-string
FLASK_ENV=development
```

**Get a Groq API key:** https://console.groq.com/keys (free, no billing required)

**Get Supabase credentials:** Create a project at https://supabase.com, then go to Project Settings → API.

### 3. Set up the database

In your Supabase project, go to the **SQL Editor** and run the contents of `migrations/schema.sql`. This creates both tables and inserts five sample tasks with full data.

### 4. Run

```bash
python run.py
```

Visit http://localhost:5000

---

## Features

- **Intent extraction** — Groq identifies the service type and pulls out key details (amount, recipient, location, urgency, etc.)
- **Risk scoring** — A rule-based engine scores each request 0–100 based on factors specific to the Kenyan diaspora context
- **Task creation** — Every request becomes a tracked record with a unique code (e.g. `VNH-A1B2C3`)
- **Fulfilment steps** — AI generates a logical sequence of steps tailored to the intent
- **Three-format messages** — WhatsApp, Email, and SMS confirmations generated and stored
- **Employee assignment** — Each intent routes to Finance, Legal, Operations, Logistics, or Support
- **Live dashboard** — All tasks visible with status updates that save immediately to the database

---

## Risk Scoring Logic

Scores are additive and capped at 100. Each rule reflects a real consideration for diaspora-managed tasks in Kenya.

| Signal | Points | Why |
|--------|--------|-----|
| Land title verification | +20 base +25 document | Title fraud is one of the most common property crimes in Kenya |
| Send money intent | +15 base | Financial transfers have inherent fraud and reversal risk |
| Amount ≥ KES 100k | +30 | CBK and M-Pesa impose enhanced due diligence at this threshold |
| Amount ≥ KES 50k | +20 | Recipient verification required by policy |
| Amount ≥ KES 10k | +10 | Standard monitoring threshold |
| Urgency flag | +15 | Rushed transfers are the most common social engineering vector |
| No recipient identified | +10 | Cannot verify who receives funds or service |
| No location specified | +5 | Increases operational uncertainty for field teams |
| Returning customer, 3+ completed tasks, no high-risk history | -15 | Demonstrated trustworthy history reduces friction |
| Returning customer, 1+ completed tasks, no high-risk history | -7 | Some positive signal, modest reduction |
| Prior high-risk task on account | +8 | History of elevated-risk requests warrants continued caution |

**Labels:** 0–29 = Low, 30–59 = Medium, 60–100 = High

---

## Decisions I Made and Why

### Which AI tools I used and for which parts

I used Claude (claude.ai) as a pair programmer throughout the build. It helped me think through the blueprint structure, draft the Groq system prompts, and write the SQL schema. I used it like a senior developer I could talk to — I'd describe what I was trying to do, review what it gave me, and either use it, modify it, or push back on it.

For the actual AI brain inside the application, I chose **Groq (Llama 3.1 8B Instant) ** because it is free, has a generous rate limit on the free tier, and is fast enough for a synchronous request flow. I initially tried `gemini-1.5-flash & gemini-2.0-flash` which threw a 404 — that model was deprecated. Switching to `Groq (Llama 3.1 8B Instant)` resolved it immediately.

### How I designed the system prompts

Each of the three Groq calls (intent extraction, step generation, message generation) has its own focused system prompt. I made a deliberate decision to keep them separate rather than doing everything in one call. One call doing three things produces inconsistent structure — separating concerns makes each output more reliable and easier to validate.

For intent extraction, the most important constraint I added was: *"Return ONLY a valid JSON object with no markdown, no explanation, no code fences."* Without this, Groq wraps output in triple backticks and the `json.loads` call fails. I also listed the exact fields allowed in `entities` so the model doesn't invent its own keys.

For message generation, I wrote detailed rules per channel rather than just saying "make a WhatsApp message." Specifying that the SMS must be under 160 characters and include the task code forced the model to actually think about the constraint rather than just producing a slightly shorter version of the email.

### One decision where I changed what the AI suggested

When scaffolding the risk scoring module, the initial suggestion was to call Groq again to score the risk — essentially asking the AI to rate its own output. I changed this to a deterministic rule-based system for two reasons. First, an AI-scored risk is a black box that cannot be explained to a customer or auditor. Second, the brief explicitly says "you will be asked to explain your scoring logic" — a model producing a number does not count as an explanation. The rule table in this README is the explanation. Every point added to a score can be traced to a line of code and a real-world reason.

### On customer identity

The brief mentions that "a returning customer with a clean history should carry lower risk" but does not ask for a full login system. I implemented a lightweight identifier field — phone number or email — that a customer types when submitting a request. No password, no session, no auth overhead. The risk scorer looks up prior tasks under that identifier and adjusts the score: -15 for three or more completed tasks with no high-risk incidents, -7 for one or more, and +8 if there is a prior high-risk task on the account. This directly addresses the brief's language without adding a feature that would take a full day to build and test properly.

### One thing that did not work the way I expected

Supabase's Python client raises an exception when you call `.single()` on a query that returns no rows, rather than returning `None`. This broke the `get_task_by_code` and `get_messages_for_task` functions during testing — a missing task caused a 500 error instead of a clean 404. I added `try/except` blocks around all `.single()` calls and have the routes return a proper 404 response when the exception is caught. It is a small thing but it matters: a missing task code entered by a customer should say "not found", not crash the server.

---

## Deployment (Optional)

The app is ready to deploy on **Railway** or **Render**. Both support Python + Flask with zero configuration beyond setting the environment variables.

For Railway:
1. Push your repo to GitHub
2. Create a new Railway project from the repo
3. Add environment variables in the Railway dashboard
4. Railway detects the `requirements.txt` and deploys automatically

Set the start command to: `python run.py`
