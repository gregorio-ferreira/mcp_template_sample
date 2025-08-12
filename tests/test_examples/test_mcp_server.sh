#!/bin/bash
# MCP Server Test Script using curl
# Tests the MCP server HTTP endpoints with raw JSON-RPC calls

set -e

# Test configuration
TARGET_QUERY_ID="LNQ_1140092_66fe2dcd3e9eb298096e8db3"
TARGET_QUERY_NAME="BAYER"

HOST="${MCP_HOST:-127.0.0.1}"
PORT="${MCP_PORT:-8000}"
PATH_PREFIX="${MCP_PATH:-/mcp}"
SERVER_URL="http://${HOST}:${PORT}${PATH_PREFIX}/"
HEADERS=(-H "Content-Type: application/json" -H "Accept: application/json, text/event-stream")

echo "🧪 MCP Server Test Suite (curl)"
echo "================================"
echo "📍 Server URL: $SERVER_URL"
echo

# Function to make MCP JSON-RPC calls
make_mcp_call() {
    local method="$1"
    local params="$2"
    local description="$3"
    
    echo "🔧 Testing: $description"
    
    local payload=$(cat <<EOF
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "$method",
    "params": $params
}
EOF
)
    
    echo "   Request: $method"
    local response=$(curl -s -X POST "$SERVER_URL" "${HEADERS[@]}" -d "$payload")
    
    if echo "$response" | grep -q '"error"'; then
        local error_msg=$(echo "$response" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
        
        # Check for expected authentication errors for Emplifi tools
        if [[ "$error_msg" == *"EMPLIFI_TOKEN"* ]] || [[ "$error_msg" == *"EMPLIFI_SECRET"* ]] || [[ "$error_msg" == *"credentials"* ]]; then
            echo "   ⚠️  Expected: $error_msg (set EMPLIFI_TOKEN and EMPLIFI_SECRET for full test)"
            return 0
        else
            echo "   ❌ Error: $error_msg"
            return 1
        fi
    elif echo "$response" | grep -q '"result"'; then
        if echo "$response" | grep -q 'event: message'; then
            # Parse SSE format
            local result=$(echo "$response" | grep 'data: {' | sed 's/data: //' | jq -r '.result.content[0].text // .result.structuredContent.result // .result')
        else
            # Parse JSON format
            local result=$(echo "$response" | jq -r '.result.content[0].text // .result.structuredContent.result // .result')
        fi
        echo "   ✅ Success: $result"
        return 0
    else
        echo "   ⚠️  Unexpected response format"
        echo "   Response: $response"
        return 1
    fi
}

# Test 1: List available tools
echo "1. Listing available tools..."
make_mcp_call "tools/list" "{}" "List MCP tools"
echo

# Test 2: List Emplifi listening queries (may fail if no credentials)
echo "2. Testing Emplifi listening queries..."
make_mcp_call "tools/call" '{
    "name": "list_listening_queries",
    "arguments": {}
}' "List available Emplifi listening queries"
echo

# Test 3: Get recent posts with real query ID
echo "3. Testing Emplifi recent posts with BAYER query..."
make_mcp_call "tools/call" '{
    "name": "get_recent_posts", 
    "arguments": {
        "query_id": "'"$TARGET_QUERY_ID"'",
        "days_back": 7,
        "limit": 10
    }
}' "Get recent posts for BAYER query (7 days, 10 posts)"
echo

# Test 4: Fetch listening posts with date range
echo "4. Testing Emplifi fetch posts with date range..."
make_mcp_call "tools/call" '{
    "name": "fetch_listening_posts",
    "arguments": {
        "query_ids": ["'"$TARGET_QUERY_ID"'"],
        "date_start": "2025-08-05",
        "date_end": "2025-08-12",
        "limit": 5,
        "sort_order": "desc"
    }
}' "Fetch BAYER posts from Aug 5-12, 2025"
echo

# Test 5: Server ping
echo "5. Testing server connectivity..."
make_mcp_call "ping" "{}" "Ping server"
echo

echo "🎉 All curl tests completed!"
echo
echo "💡 Usage:"
echo "   $0                    # Run all tests"
echo "   $0 --check-server     # Just check if server is running"

# Optional: Check if server is running
if [[ "${1:-}" == "--check-server" ]]; then
    echo "🔍 Checking server status..."
    # Use the same ping request we tested above
    if response=$(make_mcp_call "ping" "{}"); then
        echo "✅ Server is running at $SERVER_URL"
        exit 0
    else
        echo "❌ Server is not running or not accessible"
        echo "💡 Start the server with: uv run python scripts/run_server.py"
        exit 1
    fi
fi
