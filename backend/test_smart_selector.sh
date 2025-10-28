#!/bin/bash

# Test Smart Agent Selector on EC2
# Usage: ./test_smart_selector.sh [API_URL]

API_URL="${1:-http://52.53.159.105:8000}"

echo "========================================"
echo "Testing Smart Agent Selector"
echo "========================================"
echo "API: $API_URL"
echo ""

# Test 1: Health Check
echo "🏥 [1/3] Health Check..."
curl -s "$API_URL/health/smart-selector" | jq '.'
echo ""

# Test 2: Basic Smart Selection (minimal test)
echo "🧠 [2/3] Testing smart selection with basic params..."
curl -s -X POST "$API_URL/api/analyze-ad-smart" \
  -H "Content-Type: application/json" \
  -d '{
    "ad_id": "test-123",
    "feature_vector": {
      "moondream": {
        "summary": "Gym membership advertisement",
        "caption": "Join now for $9.99/month",
        "cta": "Sign up today",
        "keywords": ["fitness", "gym", "workout"],
        "target_audience": "18-24"
      },
      "features": {
        "color": {
          "palette_hex": ["#ff0000", "#00ff00"],
          "colorfulness": 45.5
        },
        "layout": {
          "aspect_ratio": 0.5,
          "whitespace_ratio": 0.3
        }
      }
    },
    "target_age_range": "18-24",
    "industry_keywords": ["fitness", "health", "gym"],
    "num_personas": 5
  }' | jq '{
    ad_id: .ad_id,
    total_personas: .summary.total_personas,
    attention: .summary.attention,
    first_persona: .selected_personas[0].name
  }'
echo ""

# Test 3: Just persona selection endpoint (if exists)
echo "👥 [3/3] Testing personas endpoint..."
curl -s "$API_URL/agents/personas" | jq '[.[:3][] | {id, name, summary}]'
echo ""

echo "========================================"
echo "✅ Tests complete!"
echo "========================================"
