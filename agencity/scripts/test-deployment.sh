#!/bin/bash

# Agencity Deployment Test Suite
# Tests all endpoints and services to ensure deployment is operational

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get server URL
if [ -f "deployment-info.txt" ]; then
    PUBLIC_IP=$(grep PUBLIC_IP deployment-info.txt | cut -d= -f2)
    SERVER_URL="http://${PUBLIC_IP}"
else
    read -p "Enter server URL or IP: " input
    if [[ $input == http* ]]; then
        SERVER_URL=$input
    else
        SERVER_URL="http://${input}"
    fi
fi

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Agencity Deployment Test Suite                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Testing server: ${SERVER_URL}${NC}"
echo ""

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Test function
test_endpoint() {
    local test_name="$1"
    local endpoint="$2"
    local expected_status="${3:-200}"
    local expected_content="$4"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    echo -n "[$TESTS_TOTAL] Testing $test_name... "

    # Make request
    response=$(curl -s -w "\n%{http_code}" "$SERVER_URL$endpoint" 2>&1)
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    # Check status code
    if [ "$http_code" != "$expected_status" ]; then
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Expected status: $expected_status, Got: $http_code"
        echo "  Response: $body"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    # Check content if specified
    if [ -n "$expected_content" ]; then
        if echo "$body" | grep -q "$expected_content"; then
            echo -e "${GREEN}✓ PASSED${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            echo -e "${RED}✗ FAILED${NC}"
            echo "  Expected content not found: $expected_content"
            echo "  Response: $body"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    fi

    echo -e "${GREEN}✓ PASSED${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
}

# Test JSON response
test_json_endpoint() {
    local test_name="$1"
    local endpoint="$2"
    local json_field="$3"
    local expected_value="$4"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    echo -n "[$TESTS_TOTAL] Testing $test_name... "

    # Make request
    response=$(curl -s "$SERVER_URL$endpoint" 2>&1)

    # Check if response is valid JSON
    if ! echo "$response" | jq . > /dev/null 2>&1; then
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Invalid JSON response"
        echo "  Response: $response"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    # Check field value if specified
    if [ -n "$json_field" ] && [ -n "$expected_value" ]; then
        actual_value=$(echo "$response" | jq -r ".$json_field")
        if [ "$actual_value" = "$expected_value" ]; then
            echo -e "${GREEN}✓ PASSED${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            echo -e "${RED}✗ FAILED${NC}"
            echo "  Expected $json_field: $expected_value"
            echo "  Got: $actual_value"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    fi

    echo -e "${GREEN}✓ PASSED${NC}"
    echo "  Response: $response"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    return 0
}

# Test with timeout
test_with_timeout() {
    local test_name="$1"
    local endpoint="$2"
    local timeout="${3:-10}"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    echo -n "[$TESTS_TOTAL] Testing $test_name (timeout: ${timeout}s)... "

    # Make request with timeout
    response=$(timeout $timeout curl -s -w "\n%{http_code}" "$SERVER_URL$endpoint" 2>&1)
    exit_code=$?

    if [ $exit_code -eq 124 ]; then
        echo -e "${RED}✗ FAILED (TIMEOUT)${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    http_code=$(echo "$response" | tail -n 1)

    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED (HTTP $http_code)${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Core Endpoints${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test root endpoint
test_json_endpoint "Root endpoint" "/" "name" "Agencity"

# Test health endpoint
test_json_endpoint "Health check" "/health" "status" "healthy"

# Test health details
test_endpoint "Health environment" "/health" "200" "production"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  API Endpoints${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test Slack endpoints
test_endpoint "Slack events endpoint (POST)" "/api/slack/events" "405" ""
test_endpoint "Slack install endpoint" "/api/slack/install" "200" ""

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Performance Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test response times
echo -n "[$((TESTS_TOTAL + 1))] Testing response time (health endpoint)... "
TESTS_TOTAL=$((TESTS_TOTAL + 1))

start_time=$(date +%s%N)
curl -s "$SERVER_URL/health" > /dev/null
end_time=$(date +%s%N)

response_time=$(( (end_time - start_time) / 1000000 ))

if [ $response_time -lt 1000 ]; then
    echo -e "${GREEN}✓ PASSED${NC} (${response_time}ms)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
elif [ $response_time -lt 3000 ]; then
    echo -e "${YELLOW}✓ PASSED (SLOW)${NC} (${response_time}ms)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAILED (TOO SLOW)${NC} (${response_time}ms)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test concurrent requests
echo -n "[$((TESTS_TOTAL + 1))] Testing concurrent requests (5 parallel)... "
TESTS_TOTAL=$((TESTS_TOTAL + 1))

for i in {1..5}; do
    curl -s "$SERVER_URL/health" > /dev/null &
done
wait

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASSED${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAILED${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test server uptime
if [ -f "deployment-info.txt" ]; then
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Server Information${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    PUBLIC_IP=$(grep PUBLIC_IP deployment-info.txt | cut -d= -f2)
    INSTANCE_ID=$(grep INSTANCE_ID deployment-info.txt | cut -d= -f2)

    echo -e "${YELLOW}Server URL:${NC} $SERVER_URL"
    echo -e "${YELLOW}Public IP:${NC} $PUBLIC_IP"
    echo -e "${YELLOW}Instance ID:${NC} $INSTANCE_ID"
fi

# Summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "Total Tests:  $TESTS_TOTAL"
echo -e "${GREEN}Passed:       $TESTS_PASSED${NC}"
echo -e "${RED}Failed:       $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ ALL TESTS PASSED - DEPLOYMENT SUCCESSFUL!        ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Update Slack Event Subscription URL:"
    echo "   ${SERVER_URL}/api/slack/events"
    echo ""
    echo "2. Test Slack integration by messaging the bot"
    echo ""
    echo "3. Monitor logs:"
    echo "   ssh -i ~/.ssh/agencity-key.pem ubuntu@${PUBLIC_IP} 'sudo journalctl -u agencity -f'"
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ✗ SOME TESTS FAILED - CHECK DEPLOYMENT             ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "1. Check if service is running:"
    echo "   ssh -i ~/.ssh/agencity-key.pem ubuntu@${PUBLIC_IP} 'sudo systemctl status agencity'"
    echo ""
    echo "2. Check logs:"
    echo "   ssh -i ~/.ssh/agencity-key.pem ubuntu@${PUBLIC_IP} 'sudo journalctl -u agencity -n 50'"
    echo ""
    echo "3. Check Nginx:"
    echo "   ssh -i ~/.ssh/agencity-key.pem ubuntu@${PUBLIC_IP} 'sudo systemctl status nginx'"
    exit 1
fi
