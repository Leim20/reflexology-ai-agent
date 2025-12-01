#!/bin/bash
# ============================================================================
# QUICK STATUS CHECK - Fast overview
# ============================================================================
# Run: bash scripts/quick_status.sh
# ============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Quick Status Check - $(date '+%H:%M:%S')"
echo "=========================================="

# Service running?
if systemctl is-active --quiet chatbot 2>/dev/null || ps aux | grep -q "[g]unicorn.*app:app"; then
    echo -e "${GREEN}✅ Application: RUNNING${NC}"
else
    echo -e "${RED}❌ Application: NOT RUNNING${NC}"
fi

# Health check
HEALTH=$(curl -s -w "%{http_code}" http://localhost:5001/health -o /dev/null 2>/dev/null)
if [ "$HEALTH" = "200" ]; then
    echo -e "${GREEN}✅ Health Check: OK${NC}"
else
    echo -e "${RED}❌ Health Check: FAILED (HTTP $HEALTH)${NC}"
fi

# Debug mode
if grep -q "^FLASK_DEBUG=True" .env 2>/dev/null; then
    echo -e "${RED}❌ Debug Mode: ENABLED (SECURITY RISK!)${NC}"
else
    echo -e "${GREEN}✅ Debug Mode: Disabled${NC}"
fi

# Resource usage
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print 100 - $8"%"}')
MEM=$(free | grep Mem | awk '{printf "%.0f%%", $3/$2 * 100.0}')
echo -e "${YELLOW}📊 CPU: $CPU | RAM: $MEM${NC}"

# Recent errors
LATEST_ERROR_LOG=$(ls -t logs/ChatAgent_errors_*.log 2>/dev/null | head -1)
if [ -f "$LATEST_ERROR_LOG" ] && [ -s "$LATEST_ERROR_LOG" ]; then
    ERROR_COUNT=$(wc -l < "$LATEST_ERROR_LOG")
    echo -e "${YELLOW}⚠️  Total Errors: $ERROR_COUNT${NC}"
else
    echo -e "${GREEN}✅ No Errors${NC}"
fi

echo "=========================================="
