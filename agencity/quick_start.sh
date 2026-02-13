#!/bin/bash

# Quick Start Script for Unified Search + Slack Integration
# Run this to verify everything is set up correctly

echo "=========================================="
echo "Unified Search + Slack Quick Start"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Environment variables
echo "1. Checking environment variables..."
if [ -f .env ]; then
    echo -e "${GREEN}✓${NC} .env file found"

    # Check required variables
    source .env

    if [ -z "$SUPABASE_URL" ]; then
        echo -e "${RED}✗${NC} SUPABASE_URL not set"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} SUPABASE_URL set"

    if [ -z "$SUPABASE_KEY" ]; then
        echo -e "${RED}✗${NC} SUPABASE_KEY not set"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} SUPABASE_KEY set"

    if [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${RED}✗${NC} OPENAI_API_KEY not set"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} OPENAI_API_KEY set"

    if [ -z "$SLACK_BOT_TOKEN" ]; then
        echo -e "${YELLOW}⚠${NC}  SLACK_BOT_TOKEN not set (needed for Slack)"
    else
        echo -e "${GREEN}✓${NC} SLACK_BOT_TOKEN set"
    fi

    if [ -z "$SLACK_SIGNING_SECRET" ]; then
        echo -e "${YELLOW}⚠${NC}  SLACK_SIGNING_SECRET not set (needed for Slack)"
    else
        echo -e "${GREEN}✓${NC} SLACK_SIGNING_SECRET set"
    fi
else
    echo -e "${RED}✗${NC} .env file not found"
    echo ""
    echo "Create a .env file with:"
    echo "  SUPABASE_URL=..."
    echo "  SUPABASE_KEY=..."
    echo "  OPENAI_API_KEY=..."
    echo "  SLACK_BOT_TOKEN=..."
    echo "  SLACK_SIGNING_SECRET=..."
    exit 1
fi

echo ""

# Check 2: Python dependencies
echo "2. Checking Python dependencies..."
if python -c "import fastapi" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} fastapi installed"
else
    echo -e "${RED}✗${NC} fastapi not installed"
    echo "Run: pip install fastapi"
    exit 1
fi

if python -c "import uvicorn" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} uvicorn installed"
else
    echo -e "${RED}✗${NC} uvicorn not installed"
    echo "Run: pip install uvicorn"
    exit 1
fi

if python -c "import openai" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} openai installed"
else
    echo -e "${RED}✗${NC} openai not installed"
    echo "Run: pip install openai"
    exit 1
fi

if python -c "import httpx" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} httpx installed"
else
    echo -e "${RED}✗${NC} httpx not installed"
    echo "Run: pip install httpx"
    exit 1
fi

if python -c "from supabase import create_client" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} supabase installed"
else
    echo -e "${RED}✗${NC} supabase not installed"
    echo "Run: pip install supabase"
    exit 1
fi

echo ""

# Check 3: Test unified search (optional - user can skip)
echo "3. Test unified search (local, no Slack)?"
echo "   This will search ~9,000 candidates and display results"
read -p "   Run test? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Running test_unified_search.py..."
    python test_unified_search.py
    echo ""
    echo -e "${GREEN}✓${NC} Test complete!"
fi

echo ""

# Check 4: Instructions for starting server
echo "4. Start the backend server"
echo ""
echo "   Run in this terminal:"
echo -e "   ${YELLOW}uvicorn app.main:app --reload --port 8001${NC}"
echo ""
echo "   You should see:"
echo "   INFO:     Uvicorn running on http://127.0.0.1:8001"
echo ""
read -p "Press Enter when server is running..."

echo ""

# Check 5: ngrok setup
echo "5. Expose localhost with ngrok (for Slack webhooks)"
echo ""
echo "   In a NEW terminal, run:"
echo -e "   ${YELLOW}ngrok http 8001${NC}"
echo ""
echo "   Copy the ngrok URL (e.g., https://abc123.ngrok.io)"
echo "   You'll need this for Slack Event Subscriptions"
echo ""
read -p "Press Enter when ngrok is running..."

echo ""

# Check 6: Slack setup
echo "6. Configure Slack App"
echo ""
echo "   Go to: https://api.slack.com/apps"
echo ""
echo "   Configure Event Subscriptions:"
echo "   • Request URL: https://YOUR-NGROK-URL.ngrok.io/api/slack/events"
echo "   • Subscribe to: app_mention, message.im"
echo ""
echo "   Get credentials:"
echo "   • Bot Token (OAuth & Permissions): Copy to .env as SLACK_BOT_TOKEN"
echo "   • Signing Secret (Basic Information): Copy to .env as SLACK_SIGNING_SECRET"
echo ""
read -p "Press Enter when Slack is configured..."

echo ""

# Check 7: Workspace mapping
echo "7. Link Slack workspace to company"
echo ""
echo "   Run this SQL in Supabase:"
echo ""
echo "   INSERT INTO org_profiles ("
echo "       slack_workspace_id,"
echo "       company_id,"
echo "       company_name"
echo "   ) VALUES ("
echo "       'T01234ABCD',                              -- Your Slack team ID"
echo "       '100b5ac1-1912-4970-a378-04d0169fd597',    -- Your company_id"
echo "       'Your Company Name'"
echo "   );"
echo ""
echo "   Get company_id:"
echo "   SELECT id, name FROM companies;"
echo ""
read -p "Press Enter when workspace is linked..."

echo ""

# Done!
echo "=========================================="
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Test in Slack:"
echo "  1. Invite bot to channel: /invite @Hermes"
echo "  2. Mention bot: @Hermes I need a prompt engineer"
echo "  3. Watch for:"
echo "     • 🤔 reaction (processing)"
echo "     • Searching message"
echo "     • Shortlist with 12 candidates"
echo "     • ✅ reaction (done)"
echo ""
echo "Troubleshooting:"
echo "  • Check backend logs (uvicorn terminal)"
echo "  • Check ngrok is forwarding (visit ngrok URL/docs)"
echo "  • See SLACK_STARTUP_GUIDE.md for detailed troubleshooting"
echo ""
echo "Happy searching! 🚀"
echo ""
