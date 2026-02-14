#!/bin/bash

# Quick test script for backend

echo "Testing Kunjal Agents Backend..."
echo ""

# Test health endpoint
echo "1. Testing health endpoint..."
HEALTH=$(curl -s http://localhost:8000/health)
if [[ $HEALTH == *"ok"* ]]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed: $HEALTH"
fi
echo ""

# Test root endpoint
echo "2. Testing root endpoint..."
curl -s http://localhost:8000/ | python3 -m json.tool
echo ""

# Test chat endpoint
echo "3. Testing chat endpoint..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, this is a test"}')

echo "Response: $RESPONSE | python3 -m json.tool"
echo ""

echo "Backend test complete!"
