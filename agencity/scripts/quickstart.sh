#!/bin/bash
# Quick start script for LinkedIn automation testing

set -e

echo "=================================================="
echo "LinkedIn Automation - Quick Start"
echo "=================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed"
    exit 1
fi

echo "✅ pip3 found"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install playwright playwright-stealth

# Install Playwright browsers
echo ""
echo "🌐 Installing Chromium..."
playwright install chromium

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p browser_profiles logs

echo ""
echo "✅ Setup complete!"
echo ""
echo "=================================================="
echo "Next Steps:"
echo "=================================================="
echo ""
echo "1. Set up test LinkedIn account (IMPORTANT: Use test account!)"
echo "   - Create account with temp email"
echo "   - Enable 2FA"
echo "   - Wait 48 hours (recommended)"
echo ""
echo "2. Set environment variables:"
echo "   export LINKEDIN_TEST_EMAIL='your-test@email.com'"
echo "   export LINKEDIN_TEST_PASSWORD='your-password'"
echo ""
echo "3. Run test:"
echo "   python scripts/test_linkedin_flow.py"
echo ""
echo "4. Check results:"
echo "   ls -la browser_profiles/"
echo "   cat logs/linkedin_automation.log"
echo ""
echo "5. Read full testing guide:"
echo "   cat TESTING_GUIDE.md"
echo ""
echo "=================================================="
