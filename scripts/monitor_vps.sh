#!/bin/bash
# ============================================================================
# VPS MONITORING SCRIPT - Jessica Reflexology Agent
# ============================================================================
# This script monitors the health and performance of the chatbot on VPS
# Run this on your VPS: bash scripts/monitor_vps.sh
# ============================================================================

echo "=========================================="
echo "🔍 JESSICA CHATBOT - VPS MONITORING"
echo "=========================================="
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# 1. SYSTEM RESOURCES
# ============================================================================
echo "=========================================="
echo "📊 SYSTEM RESOURCES"
echo "=========================================="

echo -e "${YELLOW}CPU Usage:${NC}"
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print "CPU Usage: " 100 - $1"%"}'

echo ""
echo -e "${YELLOW}Memory Usage:${NC}"
free -h | grep -v "^Swap"

echo ""
echo -e "${YELLOW}Disk Usage:${NC}"
df -h | grep -E "^/dev/"

echo ""
echo -e "${YELLOW}Uptime:${NC}"
uptime

# ============================================================================
# 2. APPLICATION STATUS
# ============================================================================
echo ""
echo "=========================================="
echo "🤖 APPLICATION STATUS"
echo "=========================================="

# Check if systemd service exists
if systemctl list-unit-files | grep -q chatbot.service; then
    echo -e "${YELLOW}Systemd Service Status:${NC}"
    systemctl status chatbot --no-pager -l | head -15

    if systemctl is-active --quiet chatbot; then
        echo -e "${GREEN}✅ Service is running${NC}"
    else
        echo -e "${RED}❌ Service is NOT running${NC}"
    fi
else
    echo -e "${YELLOW}No systemd service found. Checking manual processes...${NC}"
fi

echo ""
echo -e "${YELLOW}Running Processes:${NC}"
ps aux | grep -E "gunicorn|python.*app.py" | grep -v grep || echo "No processes found"

echo ""
echo -e "${YELLOW}Port 5001 Status:${NC}"
if command -v netstat &> /dev/null; then
    netstat -tulpn | grep 5001 || echo "Port 5001 not in use"
elif command -v ss &> /dev/null; then
    ss -tulpn | grep 5001 || echo "Port 5001 not in use"
else
    echo "Neither netstat nor ss available"
fi

# ============================================================================
# 3. APPLICATION HEALTH CHECK
# ============================================================================
echo ""
echo "=========================================="
echo "💚 HEALTH CHECK"
echo "=========================================="

HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:5001/health 2>/dev/null)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Health endpoint: OK (200)${NC}"
    echo "$HEALTH_BODY" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_BODY"
else
    echo -e "${RED}❌ Health endpoint: FAILED (HTTP $HTTP_CODE)${NC}"
    echo "Response: $HEALTH_BODY"
fi

# ============================================================================
# 4. CONFIGURATION CHECK
# ============================================================================
echo ""
echo "=========================================="
echo "⚙️  CONFIGURATION CHECK"
echo "=========================================="

if [ -f ".env" ]; then
    echo -e "${YELLOW}Debug Mode:${NC}"
    DEBUG_STATUS=$(grep "^FLASK_DEBUG=" .env | cut -d= -f2)
    if [ "$DEBUG_STATUS" = "True" ]; then
        echo -e "${RED}❌ FLASK_DEBUG=True (SECURITY RISK!)${NC}"
    else
        echo -e "${GREEN}✅ FLASK_DEBUG=$DEBUG_STATUS${NC}"
    fi

    echo -e "${YELLOW}Flask Environment:${NC}"
    FLASK_ENV=$(grep "^FLASK_ENV=" .env | cut -d= -f2)
    echo "FLASK_ENV=$FLASK_ENV"
else
    echo -e "${RED}❌ .env file not found${NC}"
fi

if [ -f "config/config.json" ]; then
    echo ""
    echo -e "${YELLOW}Logging Level:${NC}"
    grep '"level"' config/config.json | head -1
else
    echo -e "${RED}❌ config/config.json not found${NC}"
fi

# ============================================================================
# 5. RECENT LOGS ANALYSIS
# ============================================================================
echo ""
echo "=========================================="
echo "📝 RECENT LOGS (Last 10 lines)"
echo "=========================================="

LATEST_LOG=$(ls -t logs/ChatAgent_*.log 2>/dev/null | head -1)
if [ -f "$LATEST_LOG" ]; then
    echo "File: $LATEST_LOG"
    echo ""
    tail -10 "$LATEST_LOG"
else
    echo -e "${RED}❌ No log files found${NC}"
fi

# ============================================================================
# 6. ERROR LOGS
# ============================================================================
echo ""
echo "=========================================="
echo "🚨 RECENT ERRORS (Last 5)"
echo "=========================================="

LATEST_ERROR_LOG=$(ls -t logs/ChatAgent_errors_*.log 2>/dev/null | head -1)
if [ -f "$LATEST_ERROR_LOG" ]; then
    echo "File: $LATEST_ERROR_LOG"
    echo ""
    if [ -s "$LATEST_ERROR_LOG" ]; then
        tail -5 "$LATEST_ERROR_LOG"
    else
        echo -e "${GREEN}✅ No errors logged${NC}"
    fi
else
    echo -e "${YELLOW}No error log file found${NC}"
fi

# ============================================================================
# 7. ESCALATION LOGS
# ============================================================================
echo ""
echo "=========================================="
echo "📞 RECENT ESCALATIONS"
echo "=========================================="

if [ -f "logs/escalations.log" ]; then
    ESCALATION_COUNT=$(wc -l < logs/escalations.log)
    echo "Total escalations: $ESCALATION_COUNT"
    echo ""
    echo "Last 3 escalations:"
    tail -3 logs/escalations.log || echo -e "${GREEN}✅ No escalations yet${NC}"
else
    echo -e "${YELLOW}No escalation log file found${NC}"
fi

# ============================================================================
# 8. WHATSAPP CONNECTIVITY
# ============================================================================
echo ""
echo "=========================================="
echo "💬 WHATSAPP CONNECTIVITY"
echo "=========================================="

if [ -f ".env" ]; then
    WHAPI_TOKEN=$(grep "^WHAPI_API_TOKEN=" .env | cut -d= -f2)
    if [ -n "$WHAPI_TOKEN" ]; then
        echo "Testing Whapi connection..."
        WHAPI_RESPONSE=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $WHAPI_TOKEN" https://gate.whapi.cloud/settings 2>/dev/null)
        WHAPI_CODE=$(echo "$WHAPI_RESPONSE" | tail -n1)

        if [ "$WHAPI_CODE" = "200" ]; then
            echo -e "${GREEN}✅ Whapi API: Connected${NC}"
        else
            echo -e "${RED}❌ Whapi API: Connection failed (HTTP $WHAPI_CODE)${NC}"
        fi
    else
        echo -e "${YELLOW}WHAPI_API_TOKEN not found in .env${NC}"
    fi
else
    echo -e "${RED}❌ .env file not found${NC}"
fi

# ============================================================================
# 9. GOOGLE SHEETS INTEGRATION
# ============================================================================
echo ""
echo "=========================================="
echo "📊 GOOGLE SHEETS CRM"
echo "=========================================="

if [ -f "config/<PUT_YOUR_GOOGLE_PROJECT_ID_HERE>-c123857bd130.json" ]; then
    echo -e "${GREEN}✅ Google credentials file exists${NC}"
else
    echo -e "${RED}❌ Google credentials file not found${NC}"
fi

# Check recent Google Sheets activity in logs
if [ -f "$LATEST_LOG" ]; then
    SHEETS_ACTIVITY=$(grep -c "Google Sheets" "$LATEST_LOG" 2>/dev/null || echo "0")
    echo "Recent Google Sheets API calls: $SHEETS_ACTIVITY"
fi

# ============================================================================
# 10. NETWORK & FIREWALL
# ============================================================================
echo ""
echo "=========================================="
echo "🌐 NETWORK & FIREWALL"
echo "=========================================="

echo -e "${YELLOW}Firewall Status:${NC}"
if command -v ufw &> /dev/null; then
    ufw status | head -10
else
    echo "UFW not installed"
fi

echo ""
echo -e "${YELLOW}Open Ports:${NC}"
if command -v netstat &> /dev/null; then
    netstat -tuln | grep LISTEN | head -10
elif command -v ss &> /dev/null; then
    ss -tuln | grep LISTEN | head -10
fi

# ============================================================================
# 11. SCHEDULED JOBS (Follow-up System)
# ============================================================================
echo ""
echo "=========================================="
echo "⏰ SCHEDULED JOBS"
echo "=========================================="

if [ -f "$LATEST_LOG" ]; then
    echo "Recent scheduler activity:"
    grep -i "apscheduler\|follow.*up\|scheduler" "$LATEST_LOG" 2>/dev/null | tail -5 || echo "No scheduler activity found"
fi

# ============================================================================
# 12. SUMMARY & RECOMMENDATIONS
# ============================================================================
echo ""
echo "=========================================="
echo "📋 SUMMARY"
echo "=========================================="

# Count issues
ISSUES=0

if [ "$HTTP_CODE" != "200" ]; then
    ISSUES=$((ISSUES + 1))
    echo -e "${RED}❌ Health check failed${NC}"
fi

if [ "$DEBUG_STATUS" = "True" ]; then
    ISSUES=$((ISSUES + 1))
    echo -e "${RED}❌ Debug mode is enabled (security risk)${NC}"
fi

if ! systemctl is-active --quiet chatbot 2>/dev/null && ! ps aux | grep -q "[g]unicorn.*app:app"; then
    ISSUES=$((ISSUES + 1))
    echo -e "${RED}❌ Application not running${NC}"
fi

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! System is healthy.${NC}"
else
    echo -e "${YELLOW}⚠️  Found $ISSUES issue(s) that need attention${NC}"
fi

echo ""
echo "=========================================="
echo "Monitor completed at $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
