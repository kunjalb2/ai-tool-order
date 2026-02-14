"""
Test script for MCP implementation
Tests MCP endpoints and verifies existing functionality is preserved
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health_endpoints():
    """Test that all health endpoints work"""
    print("\n=== Testing Health Endpoints ===")

    # Test main health
    response = requests.get(f"{BASE_URL}/health")
    print(f"GET /health: {response.status_code} - {response.json()}")

    # Test MCP health
    response = requests.get(f"{BASE_URL}/api/mcp/health")
    print(f"GET /api/mcp/health: {response.status_code} - {response.json()}")

def test_mcp_endpoints():
    """Test MCP endpoints without auth first (should fail with 401)"""
    print("\n=== Testing MCP Endpoints (No Auth - Should Fail) ===")

    # List tools (should fail without auth)
    response = requests.get(f"{BASE_URL}/api/mcp/tools")
    print(f"GET /api/mcp/tools: {response.status_code}")
    if response.status_code == 401:
        print("  ✓ Correctly requires authentication")
    else:
        print(f"  ✗ Expected 401, got {response.status_code}")

    # List resources (should fail without auth)
    response = requests.get(f"{BASE_URL}/api/mcp/resources")
    print(f"GET /api/mcp/resources: {response.status_code}")
    if response.status_code == 401:
        print("  ✓ Correctly requires authentication")
    else:
        print(f"  ✗ Expected 401, got {response.status_code}")

    # List prompts (should fail without auth)
    response = requests.get(f"{BASE_URL}/api/mcp/prompts")
    print(f"GET /api/mcp/prompts: {response.status_code}")
    if response.status_code == 401:
        print("  ✓ Correctly requires authentication")
    else:
        print(f"  ✗ Expected 401, got {response.status_code}")

def test_with_auth():
    """Test MCP endpoints with authentication"""
    print("\n=== Testing MCP Endpoints (With Auth) ===")

    # Login to get token
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )

    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        print("\nCreating test user first...")
        # Try to register
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "password": "password123"
            }
        )
        print(f"Register: {register_response.status_code}")
        if register_response.status_code == 200:
            # Try login again
            login_response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": "test@example.com", "password": "password123"}
            )

    if login_response.status_code != 200:
        print(f"Still cannot login: {login_response.status_code}")
        return

    token_data = login_response.json()
    token = token_data.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    print(f"Logged in successfully")

    # Test: List tools
    response = requests.get(f"{BASE_URL}/api/mcp/tools", headers=headers)
    print(f"\nGET /api/mcp/tools: {response.status_code}")
    if response.status_code == 200:
        tools = response.json()
        print(f"  ✓ Found {len(tools.get('tools', []))} tools:")
        for tool in tools.get('tools', []):
            print(f"    - {tool['name']}: {tool['description']}")

    # Test: List resources
    response = requests.get(f"{BASE_URL}/api/mcp/resources", headers=headers)
    print(f"\nGET /api/mcp/resources: {response.status_code}")
    if response.status_code == 200:
        resources = response.json()
        print(f"  ✓ Found {len(resources.get('resources', []))} resources:")
        for resource in resources.get('resources', []):
            print(f"    - {resource['uri']}: {resource['name']}")

    # Test: List prompts
    response = requests.get(f"{BASE_URL}/api/mcp/prompts", headers=headers)
    print(f"\nGET /api/mcp/prompts: {response.status_code}")
    if response.status_code == 200:
        prompts = response.json()
        print(f"  ✓ Found {len(prompts.get('prompts', []))} prompts:")
        for prompt in prompts.get('prompts', []):
            print(f"    - {prompt['name']}: {prompt['description']}")

    # Test: Execute tool - list_user_orders
    response = requests.post(
        f"{BASE_URL}/api/mcp/tools/execute",
        headers=headers,
        json={
            "tool_name": "list_user_orders",
            "params": {"limit": 5}
        }
    )
    print(f"\nPOST /api/mcp/tools/execute (list_user_orders): {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            orders = result.get('result', {}).get('orders', [])
            print(f"  ✓ Found {len(orders)} orders")
        else:
            print(f"  Response: {result}")

    # Test: Execute tool - get_order_details (should fail if no orders)
    response = requests.post(
        f"{BASE_URL}/api/mcp/tools/execute",
        headers=headers,
        json={
            "tool_name": "get_order_details",
            "params": {"order_id": "ORD-001"}
        }
    )
    print(f"\nPOST /api/mcp/tools/execute (get_order_details): {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            order = result.get('result', {}).get('order')
            if order:
                print(f"  ✓ Order found: {order.get('order_id')} - {order.get('status')}")
            else:
                print(f"  ✓ API working (no order found, which is expected)")
        else:
            print(f"  Result: {result}")

    # Test: Generate prompt
    response = requests.post(
        f"{BASE_URL}/api/mcp/prompts/check_status_prompt",
        headers=headers,
        json={"order_id": "ORD-001"}
    )
    print(f"\nPOST /api/mcp/prompts/check_status_prompt: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            prompt = result.get('prompt', '')
            print(f"  ✓ Generated prompt ({len(prompt)} chars)")
        else:
            print(f"  Result: {result}")

def test_existing_endpoints():
    """Test that existing endpoints still work"""
    print("\n=== Testing Existing Endpoints (Preserved) ===")

    # Login first
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )

    if login_response.status_code != 200:
        print("Cannot test existing endpoints - login failed")
        return

    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # Test: Existing chat endpoint
    response = requests.post(
        f"{BASE_URL}/api/chat",
        headers=headers,
        json={
            "message": "Hello, what orders do I have?",
            "session_id": ""
        }
    )
    print(f"POST /api/chat: {response.status_code}")
    if response.status_code == 200:
        print("  ✓ Existing chat endpoint works")

    # Test: SSE events endpoint (just check if it's accessible)
    response = requests.get(f"{BASE_URL}/api/events?session_id=test123", stream=True, timeout=1)
    print(f"GET /api/events: {response.status_code}")
    if response.status_code == 200:
        print("  ✓ Existing SSE endpoint works")

if __name__ == "__main__":
    print("=" * 60)
    print("MCP Implementation Test Suite")
    print("=" * 60)

    try:
        test_health_endpoints()
        test_mcp_endpoints()
        test_with_auth()
        test_existing_endpoints()

        print("\n" + "=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to server.")
        print("  Please start the server first:")
        print("  cd server && python api.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
