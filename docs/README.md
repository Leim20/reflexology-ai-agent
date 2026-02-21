# reflexology-agent(token-optimized) — Feature Documentation

This folder contains detailed technical documentation for each major feature of the reflexology AI agent.

## Documents

| # | File | Feature |
|---|------|---------|
| 1 | 01_conversation_history.md | Conversation History — in-memory sessions, auto-summarization, Google Sheets persistence |
| 2 | 02_customer_records_google_sheet.md | Customer Records — 6 Google Sheet tabs |
| 3 | 03_follow_up_feature.md | Follow-up Feature — campaign-based auto follow-up, 4-job pipeline |
| 4 | 04_reminder_feature.md | Booking Reminder — auto WhatsApp reminder before appointment |
| 5 | 05_broadcast_feature.md | Broadcast Feature — staff-scheduled bulk WhatsApp messages |

## Tech Stack

- AI Model: GPT-4o-mini (OpenAI)
- Web Framework: Flask
- Background Jobs: APScheduler
- WhatsApp API: WHAPI
- Google Sheets: gspread + Google Service Account
- Caching: In-memory CacheManager (TTL: 300s)
- Database: MySQL (booking sessions) + Google Sheets (records)
