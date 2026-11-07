# Jessica — AI Booking & Sales Agent for a Reflexology Spa

A production WhatsApp + web AI agent I built during my AI engineering internship (Oct 2025 – Feb 2026).
"Jessica" chats with real customers of a reflexology/massage centre in English, Chinese and Malay,
answers questions from a knowledge base, takes bookings, registers members, sends follow-ups and
broadcasts, and hands over to a human manager when needed. It ran on a Linux VPS and handled live traffic.

> The client is anonymised as **"Serenity Reflexology"**. All API keys, phone numbers, server
> addresses, spreadsheet IDs and staff names were removed or replaced with placeholders.
> The git history is a replay of my real version folders (one commit per version, with its original date).

## What it does

| Area | Details |
|---|---|
| Channels | WhatsApp (Whapi API webhooks), web chat (Flask), Chatwoot CRM inbox for human agents |
| LLM | OpenAI GPT-4o-mini with **function calling** (10 tools), Whisper for voice notes, vision for images |
| Booking | Multi-turn slot filling → Redis/MySQL booking session → validation → record to Google Sheets |
| Anti-hallucination | Two-phase field validator: extracted fields must be grounded in what the customer actually said |
| Multilingual dates | Parses "明天晚上8点", "礼拜六", "esok petang", "next Fri 3pm" into real datetimes |
| CRM / data | Google Sheets as lightweight CRM: leads, members, bookings, follow-ups, cancellations, insights |
| Automation | APScheduler jobs: booking reminders, campaign follow-ups, staff-scheduled broadcasts |
| Safety | Rate limiting, anti-spam/abuse blocking, escalation to manager by issue type |
| Cost | Prompt-caching-aware message ordering, tiered prompts, Sheets read caching (quota 429 fixes) |

## How the agent works (one message, end to end)

```
WhatsApp user ──► Whapi webhook ──► web/app.py
                                      │
                    anti_spam.py ◄────┤  rate limit / block / whitelist
                                      │
          voice.py / image.py ◄───────┤  voice → Whisper text, image → vision description
                                      │
        conversation_manager.py ◄─────┤  load session history (+ auto-summary when long)
                                      │
          token_optimizer.py ◄────────┤  build messages in cache-friendly order:
                                      │  [system prompt, knowledge base, memory, history, user msg]
                                      ▼
                         core/ai_engine.py  ──►  OpenAI chat.completions (tools=[...])
                                      │
                 tool_calls? ─── yes ─┤
                                      ▼
   update_booking_fields · validate_booking_datetime · record_booking · register_member
   check_my_membership · lookup_my_bookings · send_menu_image · track_conversation_info
   log_cancellation_reason · escalate_to_human
                                      │  results appended as tool messages → model called again
                                      ▼
            field_validator.py ──► reject values the user never said (anti-hallucination)
                                      ▼
            reply ──► WhatsApp / web  +  mirror to Chatwoot  +  lead_manager → Google Sheets
```

Key ideas I learned by building and debugging this:

- **Function calling is a loop, not a single call.** The model proposes tool calls, my code executes them,
  appends the results, and calls the model again until it produces a final answer.
- **Never trust extracted fields blindly.** The model sometimes "fills in" a date or pax the user never gave.
  `core/field_validator.py` re-checks every extracted field against the conversation (two-phase validation).
- **State belongs outside the prompt.** Booking progress lives in Redis, later MySQL (`core/booking_session_sql.py`),
  so the agent survives restarts and long conversations, and prompts stay short.
- **Token cost is an architecture problem.** Static content (system prompt + knowledge base) goes first so OpenAI
  prompt caching hits; history is summarised; prompts were restructured into tiers (see commits around 23–25 Dec).
- **External APIs have quotas.** Early versions read Google Sheets cell-by-cell and hit HTTP 429; fixed with batching,
  caching and a rate limiter (`utils/batch_manager.py`, `utils/cache_manager.py`, `utils/rate_limiter.py`).

Detailed write-ups for each subsystem are in [`docs/`](docs/) — e.g.
[AI engine](docs/06_ai_engine.md), [function calling](docs/14_function_calling_overview.md),
[booking workflow](docs/13_booking_workflow.md), [field validator](docs/21_field_validator.md),
[token optimizer](docs/23_token_optimizer.md), [bugs & lessons learned](docs/BUGS_API_QUOTA_TOKEN_WASTE_INCOMPLETE_FUNCTION.md).

## Project structure

```
core/       ai_engine, conversation_manager, booking_session(_sql), booking_extractor,
            date_extractor, field_validator, anti_spam, config_loader
handlers/   whatsapp_handler, web_handler, chatwoot_handler
handlers/tools/  lead_manager, follow_up_manager, broadcast_manager, escalation, voice, image, video, document
utils/      token_optimizer, cache_manager, rate_limiter, batch_manager, redis_client, logger
config/     config.json, system prompts (web / whatsapp), .env.template
data/       knowledge_base/catalog.txt (services, prices, policies)
scripts/    Google Sheets setup, MySQL schema, VPS monitoring, tests
web/        Flask app, webhook endpoints, web chat UI
docs/       technical documentation + docs/dev-notes (my working notes during development)
```

## Development timeline (from the commit history)

| Period | Milestone |
|---|---|
| Nov 2025 | Built from my own `chat-agent-template` repo; WhatsApp + web, function calling, escalation, anti-spam, broadcast, follow-ups |
| Early Dec | Deployed to VPS (gunicorn + systemd); fixed Google Sheets 429 quota errors |
| Mid–late Dec | Chatwoot CRM integration, video/voice tools, multilingual & sales-framework prompt rewrite, token optimisation |
| Jan 2026 | Voice notes, datetime parser, cancellation/retention flow, Redis booking sessions + LLM booking extractor |
| Feb 2026 | Booking sessions migrated to MySQL, two-phase anti-hallucination validator, broadcast split, multilingual date extractor, documentation |

## Running locally

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp config/.env.template .env                       # fill in OPENAI_API_KEY, WHAPI_API_TOKEN, ...
python web/app.py                                  # web chat on http://localhost:5001
```

Google Sheets features need a service-account JSON in `config/` and the sheet setup scripts in `scripts/`.

## Tech stack

Python · Flask · OpenAI API (GPT-4o-mini, Whisper, vision, function calling) · Whapi (WhatsApp) · Chatwoot ·
Redis · MySQL · Google Sheets (gspread) · APScheduler · gunicorn · Ubuntu VPS
