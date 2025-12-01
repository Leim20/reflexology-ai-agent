#!/bin/bash
# ============================================================================
# ALERT CHECKER - Check for critical issues
# ============================================================================
# Run this periodically (can be added to cron)
# Example cron: */5 * * * * /path/to/scripts/check_alerts.sh
# ============================================================================

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

ALERT_COUNT=0

echo "=========================================="
echo "🚨 CRITICAL ALERTS CHECK"
echo "=========================================="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. Check if application is running
echo -n "Checking application status... "
if systemctl is-active --quiet chatbot 2>/dev/null || ps aux | grep -q "[g]unicorn.*app:app"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}ALERT!${NC}"
    echo "❌ CRITICAL: Application is NOT running!"
    ALERT_COUNT=$((ALERT_COUNT + 1))
fi

# 2. Check health endpoint
echo -n "Checking health endpoint... "
HEALTH_CODE=$(curl -s -w "%{http_code}" http://localhost:5001/health -o /dev/null 2>/dev/null)
if [ "$HEALTH_CODE" = "200" ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}ALERT!${NC}"
    echo "❌ CRITICAL: Health check failed (HTTP $HEALTH_CODE)"
    ALERT_COUNT=$((ALERT_COUNT + 1))
fi

# 3. Check debug mode
echo -n "Checking debug mode... "
if grep -q "^FLASK_DEBUG=True" .env 2>/dev/null; then
    echo -e "${RED}ALERT!${NC}"
    echo "❌ WARNING: Debug mode is enabled (SECURITY RISK)"
    ALERT_COUNT=$((ALERT_COUNT + 1))
else
    echo -e "${GREEN}OK${NC}"
fi

# 4. Check disk space
echo -n "Checking disk space... "
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo -e "${RED}ALERT!${NC}"
    echo "❌ WARNING: Disk usage is ${DISK_USAGE}%"
    ALERT_COUNT=$((ALERT_COUNT + 1))
elif [ "$DISK_USAGE" -gt 80 ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo "⚠️  Disk usage is ${DISK_USAGE}%"
else
    echo -e "${GREEN}OK${NC}"
fi

# 5. Check memory usage
echo -n "Checking memory usage... "
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ "$MEM_USAGE" -gt 90 ]; then
    echo -e "${RED}ALERT!${NC}"
    echo "❌ WARNING: Memory usage is ${MEM_USAGE}%"
    ALERT_COUNT=$((ALERT_COUNT + 1))
elif [ "$MEM_USAGE" -gt 80 ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo "⚠️  Memory usage is ${MEM_USAGE}%"
else
    echo -e "${GREEN}OK${NC}"
fi

# 6. Check for recent errors
echo -n "Checking for recent errors... "
LATEST_ERROR_LOG=$(ls -t logs/ChatAgent_errors_*.log 2>/dev/null | head -1)
if [ -f "$LATEST_ERROR_LOG" ]; then
    RECENT_ERRORS=$(find "$LATEST_ERROR_LOG" -mmin -30 -exec wc -l {} \; 2>/dev/null | head -1)
    if [ -n "$RECENT_ERRORS" ] && [ "$RECENT_ERRORS" -gt 10 ]; then
        echo -e "${RED}ALERT!${NC}"
        echo "❌ WARNING: $RECENT_ERRORS errors in last 30 minutes"
        echo "Recent errors:"
        tail -5 "$LATEST_ERROR_LOG" | sed 's/^/  /'
        ALERT_COUNT=$((ALERT_COUNT + 1))
    elif [ -n "$RECENT_ERRORS" ] && [ "$RECENT_ERRORS" -gt 0 ]; then
        echo -e "${YELLOW}WARNING${NC}"
        echo "⚠️  $RECENT_ERRORS errors in last 30 minutes"
    else
        echo -e "${GREEN}OK${NC}"
    fi
else
    echo -e "${GREEN}OK${NC}"
fi

# 7. Check port 5001
echo -n "Checking port 5001... "
if ss -tuln 2>/dev/null | grep -q ":5001" || netstat -tuln 2>/dev/null | grep -q ":5001"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}ALERT!${NC}"
    echo "❌ CRITICAL: Port 5001 is not listening"
    ALERT_COUNT=$((ALERT_COUNT + 1))
fi

# 8. Check log file size
echo -n "Checking log file sizes... "
LARGE_LOGS=$(find logs/ -type f -size +100M 2>/dev/null)
if [ -n "$LARGE_LOGS" ]; then
    echo -e "${YELLOW}WARNING${NC}"
    echo "⚠️  Large log files found:"
    echo "$LARGE_LOGS" | sed 's/^/  /'
else
    echo -e "${GREEN}OK${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="

if [ $ALERT_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ All systems operational - No alerts${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Found $ALERT_COUNT critical alert(s)${NC}"
    echo ""
    echo "Recommended actions:"
    echo "1. Check logs: bash scripts/view_logs.sh errors"
    echo "2. Check status: bash scripts/monitor_vps.sh"
    echo "3. Restart if needed: sudo systemctl restart chatbot"
    exit 1
fi
