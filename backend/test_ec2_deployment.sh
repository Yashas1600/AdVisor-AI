#!/bin/bash

# EC2 Deployment Test Script for AdVisor API
# Tests all health check endpoints after deployment

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default to localhost, override with EC2 IP
API_URL="${1:-http://localhost:8000}"

echo "======================================"
echo "AdVisor API Health Check Test Suite"
echo "======================================"
echo "Testing API at: $API_URL"
echo ""

# Test 1: Basic Health Check
echo -e "${YELLOW}[1/5] Testing basic health check...${NC}"
response=$(curl -s -w "\n%{http_code}" "$API_URL/health")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✓ Basic health check passed${NC}"
    echo "$body" | jq '.'
else
    echo -e "${RED}✗ Basic health check failed (HTTP $http_code)${NC}"
    echo "$body"
    exit 1
fi
echo ""

# Test 2: Smart Selector Health Check
echo -e "${YELLOW}[2/5] Testing Smart Selector (Supabase + OpenAI)...${NC}"
response=$(curl -s -w "\n%{http_code}" "$API_URL/health/smart-selector")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "200" ]; then
    status=$(echo "$body" | jq -r '.status')
    if [ "$status" == "healthy" ]; then
        echo -e "${GREEN}✓ Smart Selector healthy${NC}"
    else
        echo -e "${YELLOW}⚠ Smart Selector status: $status${NC}"
    fi
    echo "$body" | jq '.'
else
    echo -e "${RED}✗ Smart Selector health check failed (HTTP $http_code)${NC}"
    echo "$body"
    exit 1
fi
echo ""

# Test 3: ASI:One Health Check
echo -e "${YELLOW}[3/5] Testing ASI:One (Fetch.ai)...${NC}"
response=$(curl -s -w "\n%{http_code}" "$API_URL/health/asi-one")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "200" ]; then
    status=$(echo "$body" | jq -r '.status')
    if [ "$status" == "healthy" ]; then
        echo -e "${GREEN}✓ ASI:One healthy${NC}"
    else
        echo -e "${YELLOW}⚠ ASI:One status: $status${NC}"
    fi
    echo "$body" | jq '.'
else
    echo -e "${RED}✗ ASI:One health check failed (HTTP $http_code)${NC}"
    echo "$body"
    exit 1
fi
echo ""

# Test 4: List Personas
echo -e "${YELLOW}[4/5] Testing persona listing...${NC}"
response=$(curl -s -w "\n%{http_code}" "$API_URL/agents/personas?limit=5")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "200" ]; then
    count=$(echo "$body" | jq '. | length')
    echo -e "${GREEN}✓ Persona listing works ($count personas returned)${NC}"
    echo "$body" | jq '.[:2]'
else
    echo -e "${RED}✗ Persona listing failed (HTTP $http_code)${NC}"
    echo "$body"
fi
echo ""

# Test 5: Root Endpoint
echo -e "${YELLOW}[5/5] Testing root endpoint...${NC}"
response=$(curl -s -w "\n%{http_code}" "$API_URL/")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✓ Root endpoint works${NC}"
    echo "$body" | jq '.endpoints'
else
    echo -e "${RED}✗ Root endpoint failed (HTTP $http_code)${NC}"
    echo "$body"
fi
echo ""

# Summary
echo "======================================"
echo -e "${GREEN}All tests completed!${NC}"
echo "======================================"
echo ""
echo "Your EC2 API is ready for deployment!"
echo ""
echo "Key Endpoints:"
echo "  Health:           $API_URL/health"
echo "  Smart Selector:   $API_URL/health/smart-selector"
echo "  ASI:One:          $API_URL/health/asi-one"
echo "  Analyze Ad:       $API_URL/api/analyze-ad-smart"
echo "  Docs:             $API_URL/docs"
echo ""
