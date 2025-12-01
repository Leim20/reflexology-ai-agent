#!/bin/bash
# ============================================================================
# LIVE MONITORING SCRIPT - Continuous Monitoring
# ============================================================================
# Run this for real-time monitoring: bash scripts/monitor_live.sh
# Press Ctrl+C to stop
# ============================================================================

echo "=========================================="
echo "📡 LIVE MONITORING - Jessica Chatbot"
echo "=========================================="
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Press Ctrl+C to stop"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check status
check_status() {
    clear
    echo "=========================================="
    echo "📡 LIVE STATUS - $(date '+%H:%M:%S')"
    echo "=========================================="
    echo ""

    # 1. Service Status
    echo -e "${YELLOW}Service Status:${NC}"
    if systemctl is-active --quiet chatbot 2>/dev/null; then
        echo -e "${GREEN}✅ Running${NC}"
    elif ps aux | grep -q "[g]unicorn.*app:app"; then
        echo -e "${GREEN}✅ Running (manual)${NC}"
    else
        echo -e "${RED}❌ Not Running${NC}"
    fi

    # 2. Resource Usage
    echo ""
    echo -e "${YELLOW}CPU & Memory:${NC}"
    top -bn1 | grep "Cpu(s)" | awk '{print "CPU: " 100 - $8"%"}'
    free | grep Mem | awk '{printf "RAM: %.1f%% (%dMB / %dMB)\n", $3/$2 * 100.0, $3/1024, $2/1024}'

    # 3. Process Info
    echo ""
    echo -e "${YELLOW}Active Processes:${NC}"
    ps aux | grep -E "[g]unicorn|[p]ython.*app.py" | awk '{printf "PID: %s | CPU: %s%% | MEM: %s%% | %s\n", $2, $3, $4, $11}' | head -5

    # 4. Port Status
    echo ""
    echo -e "${YELLOW}Port 5001:${NC}"
    if ss -tuln 2>/dev/null | grep -q ":5001"; then
        echo -e "${GREEN}✅ Listening${NC}"
    else
        echo -e "${RED}❌ Not listening${NC}"
    fi

    # 5. Recent Activity (last 3 log lines)
    echo ""
    echo -e "${YELLOW}Recent Activity:${NC}"
    LATEST_LOG=$(ls -t logs/ChatAgent_*.log 2>/dev/null | head -1)
    if [ -f "$LATEST_LOG" ]; then
        tail -3 "$LATEST_LOG" | cut -c1-100
    else
        echo "No logs found"
    fi

    # 6. Error Count
    echo ""
    echo -e "${YELLOW}Errors (last 5 minutes):${NC}"
    LATEST_ERROR_LOG=$(ls -t logs/ChatAgent_errors_*.log 2>/dev/null | head -1)
    if [ -f "$LATEST_ERROR_LOG" ]; then
        ERROR_COUNT=$(find "$LATEST_ERROR_LOG" -mmin -5 -exec wc -l {} \; 2>/dev/null || echo "0")
        if [ "$ERROR_COUNT" -gt 0 ]; then
            echo -e "${RED}⚠️  $ERROR_COUNT new errors${NC}"
        else
            echo -e "${GREEN}✅ No recent errors${NC}"
        fi
    else
        echo "No error log"
    fi

    # 7. Active Conversations
    echo ""
    echo -e "${YELLOW}Active Conversations:${NC}"
    curl -s http://localhost:5001/health 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Web: {data.get('conversations', {}).get('web', {}).get('count', 0)} | WhatsApp: {data.get('conversations', {}).get('whatsapp', {}).get('count', 0)}\")" 2>/dev/null || echo "Unable to fetch"

    echo ""
    echo "=========================================="
    echo "Next update in 5 seconds... (Ctrl+C to stop)"
    echo "=========================================="
}

# Main loop
while true; do
    check_status
    sleep 5
done
