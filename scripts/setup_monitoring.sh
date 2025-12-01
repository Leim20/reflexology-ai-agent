#!/bin/bash
# ============================================================================
# MONITORING SETUP SCRIPT
# ============================================================================
# Run this once after uploading files to VPS
# ============================================================================

echo "=========================================="
echo "🔧 Setting up monitoring scripts..."
echo "=========================================="
echo ""

# Make all monitoring scripts executable
echo "Making scripts executable..."
chmod +x scripts/monitor_vps.sh
chmod +x scripts/monitor_live.sh
chmod +x scripts/quick_status.sh
chmod +x scripts/view_logs.sh
chmod +x scripts/check_alerts.sh
chmod +x scripts/setup_monitoring.sh

echo "✅ Scripts are now executable"
echo ""

# Test if required commands are available
echo "Checking required commands..."

command -v curl >/dev/null 2>&1 || { echo "⚠️  curl not found. Install: sudo apt install curl"; }
command -v python3 >/dev/null 2>&1 || { echo "⚠️  python3 not found."; }
command -v systemctl >/dev/null 2>&1 || { echo "⚠️  systemctl not found."; }

if command -v ss >/dev/null 2>&1; then
    echo "✅ ss available"
elif command -v netstat >/dev/null 2>&1; then
    echo "✅ netstat available"
else
    echo "⚠️  Neither ss nor netstat found. Install: sudo apt install net-tools"
fi

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "Available commands:"
echo "  bash scripts/quick_status.sh    - Quick health check"
echo "  bash scripts/monitor_vps.sh     - Full system analysis"
echo "  bash scripts/monitor_live.sh    - Live monitoring"
echo "  bash scripts/view_logs.sh       - View logs"
echo "  bash scripts/check_alerts.sh    - Check for alerts"
echo ""
echo "Run your first check:"
echo "  bash scripts/quick_status.sh"
echo ""
