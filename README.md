# WhatsApp AI Booking Assistant

A WhatsApp-native, production-ready AI booking agent designed for local service businesses (salons, clinics, tutors, dentists). This bot operates automatically 24/7 utilizing a free-tier stack of modern AI technologies.

## Tech Stack
* **Backend:** Python + FastAPI
* **AI Engine:** Groq API (Llama 3 70b & 8b)
* **Database:** Supabase (PostgreSQL)
* **Messaging:** Meta WhatsApp Cloud API
* **Logging:** Loguru

## Core Capabilities
1. **Conversational Support:** Answers FAQs (pricing, hours, location) using local RAG memory context via Groq LLMs.
2. **Intent Engine:** Rapidly intercepts "booking", "canceling", or "questions" intents using Llama-3-8b constrained JSON parsing.
3. **Availability Engine:** Computes free 30-minute intervals by subtracting active bookings from business operating hours.
4. **Double Booking Prevention:** Handled flawlessly via PostgreSQL exclusion constraints `no_overlapping_appointments`.
5. **State Machine Orchestrator:** Maps WhatsApp users through a 5-stage funnel: `INIT -> ASK_SERVICE -> ASK_TIME -> CONFIRM_BOOKING -> BOOKED`.

## Local Development
1. Clone the repo and activate a VENV.
2. Run `pip install -r requirements.txt`.
3. Create a `.env` file (see `backend/config.py` for exact variables).
4. Spin up the server: `uvicorn backend.main:app --reload`.
5. Expose locally with ngrok: `ngrok http 8000`.
6. Plug the Ngrok URL into the Meta Developer Portal's Webhook configuration.

## Deployment to Render (Free Tier)
1. Push branch to GitHub.
2. Create standard Render Web Service. Build command: `pip install -r requirements.txt`. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
3. Include environment variables.

## Database (Supabase)
Execute the `database_schema.sql` artifact in your Supabase SQL Editor. This will generate the Multi-tenant Business tables, Customer tables, Appointment trackers, and Context stores for the LLMs.
