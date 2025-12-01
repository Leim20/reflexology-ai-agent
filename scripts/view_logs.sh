#!/bin/bash
# ============================================================================
# LOG VIEWER - Interactive log viewing
# ============================================================================
# Run: bash scripts/view_logs.sh [option]
# Options: live, errors, escalations, today, all
# ============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

OPTION=${1:-live}

case $OPTION in
    live)
        echo -e "${BLUE}📡 Watching live logs... (Press Ctrl+C to stop)${NC}"
        LATEST_LOG=$(ls -t logs/ChatAgent_*.log 2>/dev/null | head -1)
        if [ -f "$LATEST_LOG" ]; then
            tail -f "$LATEST_LOG"
        else
            echo -e "${RED}❌ No log files found${NC}"
        fi
        ;;

    errors)
        echo -e "${RED}🚨 Error Logs${NC}"
        echo "=========================================="
        LATEST_ERROR_LOG=$(ls -t logs/ChatAgent_errors_*.log 2>/dev/null | head -1)
        if [ -f "$LATEST_ERROR_LOG" ]; then
            if [ -s "$LATEST_ERROR_LOG" ]; then
                echo "File: $LATEST_ERROR_LOG"
                echo ""
                cat "$LATEST_ERROR_LOG"
            else
                echo -e "${GREEN}✅ No errors logged${NC}"
            fi
        else
            echo -e "${YELLOW}No error log file found${NC}"
        fi
        ;;

    escalations)
        echo -e "${YELLOW}📞 Escalation Logs${NC}"
        echo "=========================================="
        if [ -f "logs/escalations.log" ]; then
            cat logs/escalations.log
        else
            echo -e "${GREEN}✅ No escalations yet${NC}"
        fi
        ;;

    today)
        echo -e "${BLUE}📅 Today's Activity${NC}"
        echo "=========================================="
        TODAY=$(date +%Y%m%d)
        TODAY_LOG="logs/ChatAgent_${TODAY}.log"
        if [ -f "$TODAY_LOG" ]; then
            echo "File: $TODAY_LOG"
            echo "Lines: $(wc -l < $TODAY_LOG)"
            echo ""
            tail -50 "$TODAY_LOG"
        else
            echo -e "${YELLOW}No log file for today${NC}"
        fi
        ;;

    all)
        echo -e "${BLUE}📚 All Log Files${NC}"
        echo "=========================================="
        ls -lh logs/*.log 2>/dev/null || echo "No log files found"
        ;;

    whatsapp)
        echo -e "${GREEN}💬 WhatsApp Activity (Last 20 messages)${NC}"
        echo "=========================================="
        LATEST_LOG=$(ls -t logs/ChatAgent_*.log 2>/dev/null | head -1)
        if [ -f "$LATEST_LOG" ]; then
            grep -i "whatsapp\|webhook\|whapi" "$LATEST_LOG" | tail -20
        else
            echo -e "${RED}❌ No log files found${NC}"
        fi
        ;;

    google)
        echo -e "${BLUE}📊 Google Sheets Activity${NC}"
        echo "=========================================="
        LATEST_LOG=$(ls -t logs/ChatAgent_*.log 2>/dev/null | head -1)
        if [ -f "$LATEST_LOG" ]; then
            grep -i "google\|sheets\|gspread" "$LATEST_LOG" | tail -20
        else
            echo -e "${RED}❌ No log files found${NC}"
        fi
        ;;

    *)
        echo "Usage: bash scripts/view_logs.sh [option]"
        echo ""
        echo "Options:"
        echo "  live        - Watch logs in real-time (default)"
        echo "  errors      - Show all error logs"
        echo "  escalations - Show escalation logs"
        echo "  today       - Show today's activity"
        echo "  all         - List all log files"
        echo "  whatsapp    - Show WhatsApp activity only"
        echo "  google      - Show Google Sheets activity"
        echo ""
        echo "Examples:"
        echo "  bash scripts/view_logs.sh live"
        echo "  bash scripts/view_logs.sh errors"
        ;;
esac
