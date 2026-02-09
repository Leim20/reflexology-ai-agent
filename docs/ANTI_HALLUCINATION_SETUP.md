# Anti-Hallucination System Setup Guide

## Overview

This system prevents the AI from hallucinating booking data from conversation history. When a user provides partial booking information (e.g., just a date), the AI will no longer fill in missing fields (like time) from previous conversations.

## Architecture

### Two-Phase Validation

```
Phase 1: AI extracts fields with FULL conversation context (existing MCQ flow)
    ↓
Phase 2: Validator checks each field against ONLY the current message
    ↓
Only validated fields are saved to booking session
```

### Session Expiry Logic

| Time Since Last Update | Behavior |
|----------------------|----------|
| < 1 hour | Auto-continue booking |
| 1-24 hours | Auto-continue booking |
| > 24 hours | Ask user if they want to continue or start fresh |

## New Files Created

1. **`scripts/setup_mysql.sql`** - Database schema for booking sessions
2. **`core/booking_session_sql.py`** - SQL-backed session management
3. **`core/field_validator.py`** - Two-Phase LLM validation
4. **Modified `web/app.py`** - Integrated validation into booking flow
5. **Modified `config/config.json`** - Added MySQL configuration

## Deployment Steps

### 1. Install MySQL (if not already installed)

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server

# Start MySQL
sudo systemctl start mysql
sudo systemctl enable mysql
```

### 2. Install Python MySQL connector

```bash
pip install mysql-connector-python
```

### 3. Set up the database

```bash
# Login to MySQL as root
sudo mysql -u root

# Run the setup script
source /root/reflexology-agent(token-optimized26)/scripts/setup_mysql.sql

# Create the application user (update password!)
CREATE USER 'reflexology_app'@'localhost' IDENTIFIED BY 'YOUR_SECURE_PASSWORD';
GRANT SELECT, INSERT, UPDATE, DELETE ON reflexology_booking.* TO 'reflexology_app'@'localhost';
GRANT EXECUTE ON PROCEDURE reflexology_booking.cleanup_expired_sessions TO 'reflexology_app'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Configure the application

Option A: Environment variables (recommended)
```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=reflexology_app
export MYSQL_PASSWORD=YOUR_SECURE_PASSWORD
export MYSQL_DATABASE=reflexology_booking
```

Option B: Edit `config/config.json`
```json
"mysql": {
  "enabled": true,
  "host": "localhost",
  "port": 3306,
  "user": "reflexology_app",
  "password": "YOUR_SECURE_PASSWORD",
  "database": "reflexology_booking"
}
```

### 5. Restart the application

```bash
# If using systemd
sudo systemctl restart reflexology-agent

# If using PM2
pm2 restart reflexology-agent

# If running directly
cd /root/reflexology-agent(token-optimized26)
python -m web.app
```

## Testing the Anti-Hallucination System

### Test Case 1: Partial Booking Data

1. Start a booking conversation
2. Provide date only: "我要预约3月1日"
3. **Expected**: AI should ask for time, NOT fill in a time from previous conversations

### Test Case 2: All-at-Once Booking

1. Send all booking info in one message:
   "我要预约3月1日下午2点，脚底按摩，女技师"
2. **Expected**: All fields should be captured in one message

### Test Case 3: Session Expiry

1. Start a booking, provide some fields
2. Wait > 24 hours (or manually set updated_at in database)
3. Continue conversation
4. **Expected**: AI should ask if user wants to continue previous booking or start fresh

## Monitoring

### Check validation logs
```sql
SELECT * FROM field_validation_log
WHERE validation_result = 'hallucinated'
ORDER BY validated_at DESC
LIMIT 20;
```

### Check session history
```sql
SELECT * FROM booking_session_history
ORDER BY session_completed_at DESC
LIMIT 20;
```

### View active sessions
```sql
SELECT session_id, service, date, time, updated_at
FROM booking_sessions
WHERE status = 'active';
```

## Rollback

If issues occur, you can disable Phase 2 validation by removing the import and validation code block in `app.py`:

1. Remove the import: `from core.field_validator import validate_booking_extraction`
2. Remove the Phase 2 validation block in `handle_update_booking_fields_function_call`

The system will fall back to the original MCQ-only validation.

## Cost Impact

- Phase 2 validation uses gpt-4o-mini (same as Phase 1)
- Adds ~1 extra API call per booking message with extracted fields
- Estimated cost: ~$0.001-0.002 per validation (negligible)
- Quick validators (phone, date/time patterns) reduce LLM calls

## Troubleshooting

### "MySQL connection pool" errors
- Check MySQL is running: `sudo systemctl status mysql`
- Verify credentials in config
- Check database exists: `mysql -u reflexology_app -p -e "USE reflexology_booking;"`

### Fields still being hallucinated
- Check Phase 2 validation is running (look for "PHASE 2" in logs)
- Verify `current_user_message` is being passed correctly
- Check `field_validation_log` table for validation results

### Sessions not persisting
- Verify MySQL connection is working
- Check `booking_sessions` table has data
- Ensure `use_sql: true` in config
