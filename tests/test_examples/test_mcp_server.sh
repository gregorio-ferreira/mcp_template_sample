#!/bin/bash
# MCP Server Test Script using curl
# Tests the MCP server HTTP endpoints with raw JSON-RPC calls

set -e

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
        echo "   ❌ Error: $(echo "$response" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)"
        return 1
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

# Test 2: Timezone conversion
echo "2. Testing timezone conversion..."
make_mcp_call "tools/call" '{
    "name": "convert_timezone",
    "arguments": {
        "dt": "2025-08-10T15:30:00",
        "from_tz": "Europe/Madrid",
        "to_tz": "America/New_York"
    }
}' "Convert Madrid time to New York time"
echo

# Test 3: Unix time conversion
echo "3. Testing Unix time conversion..."
make_mcp_call "tools/call" '{
    "name": "to_unix_time",
    "arguments": {
        "dt": "2025-08-10T15:30:00+02:00",
        "unit": "milliseconds"
    }
}' "Convert ISO time to Unix milliseconds"
echo

# Test 4: Server ping
echo "4. Testing server connectivity..."
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
