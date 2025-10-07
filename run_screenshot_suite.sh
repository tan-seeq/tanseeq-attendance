#!/bin/bash

# TANSEEQ HR System - Screenshot Suite Runner
# ==========================================

echo "🎯 TANSEEQ HR System - Automated Screenshot Suite"
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r tests/requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Create evidence directory if it doesn't exist
mkdir -p evidence

# Run the screenshot suite
echo "🚀 Starting screenshot suite..."
echo "   - Testing with admin@tanseeq.com/ADMIN"
echo "   - Testing with jihad@tanseeq.com/jihad123"
echo "   - Capturing 20+ routes with screenshots, modals, and downloads"
echo "   - Viewport: 1920x800, Quality: 20"
echo ""

python3 tests/playwright_screenshot_suite.py

# Check if the test completed successfully
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Screenshot suite completed successfully!"
    echo "📁 Evidence saved to: ./evidence/"
    echo "📊 Check ./evidence/test_report.json for detailed results"
    echo "📋 Check ./evidence/summary_report.md for summary"
    echo ""
    echo "📂 Evidence Structure:"
    echo "   evidence/"
    echo "   ├── Dashboard/"
    echo "   │   ├── admin/ (screenshots, modals, downloads, interactions)"
    echo "   │   └── user/"
    echo "   ├── Attendance/"
    echo "   ├── Leaves/"
    echo "   ├── ... (20+ routes)"
    echo "   ├── test_report.json"
    echo "   └── summary_report.md"
    echo ""
    echo "🎉 Ready for review and handoff!"
else
    echo ""
    echo "❌ Screenshot suite failed. Check the logs above for details."
    exit 1
fi