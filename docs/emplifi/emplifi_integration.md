# Emplifi Listening API Integration

This MCP server provides tools for interacting with the Emplifi Listening API, allowing AI agents to:

- List listening queries
- Fetch social media posts and mentions
- Retrieve aggregated metrics
- Get recent posts and daily mention counts

## 🔧 Setup

### 1. Install Dependencies

The Emplifi tools require the `httpx` library, which is already included in the `pyproject.toml`:

```bash
# Install all dependencies
make setup
```

### 2. Configure Authentication

The Emplifi API supports two authentication methods:

#### Option A: OAuth 2.0 (Recommended)

Set these environment variables:

```bash
export EMPLIFI_CLIENT_ID="your_client_id"
export EMPLIFI_CLIENT_SECRET="your_client_secret"
export EMPLIFI_REDIRECT_URI="http://localhost:8765/callback"
export EMPLIFI_SCOPES="api.read offline_access"  # Optional, defaults shown
```

#### Option B: Basic Authentication

Set these environment variables:

```bash
export EMPLIFI_TOKEN="your_api_token"
export EMPLIFI_SECRET="your_api_secret"
```

### 3. Initial OAuth Setup (OAuth only)

For OAuth authentication, you'll need to perform an initial interactive login to obtain tokens:

```python
# Run this once to get your tokens
python -c "
import asyncio
from mcp_server.tools.emplifi_tools import EmplifiOAuthClient, _get_config

async def auth():
    config = _get_config()
    client = EmplifiOAuthClient(config)
    # This will open a browser for authorization
    code = client._interactive_login()
    await client._exchange_code_for_tokens(code)
    print('Authorization complete! Token saved to emplifi_token.json')

asyncio.run(auth())
"
```

## 🛠️ Available Tools

### Core Tools

#### `list_listening_queries()`
Lists all available listening queries from your Emplifi account.

**Returns:** List of `ListeningQuery` objects with id, name, description, and status.

#### `fetch_listening_posts(query_ids, date_start, date_end, ...)`
Fetches social media posts and mentions for specified queries and date range.

**Parameters:**
- `query_ids`: List of listening query IDs
- `date_start`: Start date (YYYY-MM-DD format)
- `date_end`: End date (YYYY-MM-DD format)
- `fields`: Optional list of fields to include
- `limit`: Posts per page (max 100, default 100)
- `filters`: Optional list of filters
- `sort`: Optional sort configuration
- `max_pages`: Maximum pages to fetch (default 1)

**Returns:** List of `ListeningPost` objects.

#### `fetch_listening_metrics(query_ids, date_start, date_end, metrics, ...)`
Fetches aggregated metrics for specified queries and date range.

**Parameters:**
- `query_ids`: List of listening query IDs
- `date_start`: Start date (YYYY-MM-DD format)  
- `date_end`: End date (YYYY-MM-DD format)
- `metrics`: List of `MetricConfig` objects (e.g., `[{"type": "mentions"}]`)
- `dimensions`: Optional list of `DimensionConfig` objects
- `filters`: Optional list of filters

**Returns:** `ListeningMetrics` object with data and metadata.

### Convenience Tools

#### `get_recent_posts(query_id, days_back=7, limit_per_page=50, max_pages=2)`
Gets recent posts for a specific listening query with sensible defaults.

#### `get_daily_mention_metrics(query_id, days_back=30)`
Gets daily mention count metrics for a listening query.

## 📝 Usage Examples

### AI Agent Usage

Once the server is running, AI agents can use these tools like this:

**List queries:**
```
Please list all my listening queries.
```

**Get recent posts:**
```
Show me recent posts for query LNQ_12345 from the last 3 days.
```

**Fetch metrics:**
```
Get daily mention counts for query LNQ_12345 over the last month.
```

**Advanced post search:**
```
Fetch posts for queries LNQ_12345 and LNQ_67890 from January 1-7, 2024, 
filtered by platform=facebook, sorted by created_time desc, max 200 posts.
```

### Direct API Usage

```python
from mcp_server.tools.emplifi_tools import (
    list_listening_queries,
    fetch_listening_posts,
    get_recent_posts
)

# List all queries
queries = await list_listening_queries()
print(f"Found {len(queries)} queries")

# Get recent posts
posts = await get_recent_posts("LNQ_12345", days_back=7)
print(f"Found {len(posts)} recent posts")

# Fetch specific posts with filters
from mcp_server.tools.emplifi_tools import PostsFilter, PostsSort

posts = await fetch_listening_posts(
    query_ids=["LNQ_12345"],
    date_start="2024-01-01",
    date_end="2024-01-07",
    filters=[PostsFilter(field="platform", value="facebook")],
    sort=[PostsSort(field="created_time", order="desc")],
    max_pages=3
)
```

## 🧪 Testing

Run the tests:

```bash
# Run all tests
make test

# Run only Emplifi tests
python -m pytest tests/test_tools/test_emplifi_tools.py -v
```

## 🚀 Development

### Adding New Endpoints

To add support for new Emplifi API endpoints:

1. **Add new functions** to `src/mcp_server/tools/emplifi_tools.py`
2. **Register the functions** in `src/mcp_server/server.py`
3. **Export them** from `src/mcp_server/tools/__init__.py`
4. **Add tests** in `tests/test_tools/test_emplifi_tools.py`

### Model Extensions

To extend the data models (add new fields, etc.):

1. **Update Pydantic models** in `emplifi_tools.py`
2. **Update tests** to reflect the changes
3. **Update documentation**

## 🔐 Security Notes

- **Tokens are cached** in `emplifi_token.json` for OAuth flows
- **Add `emplifi_token.json` to `.gitignore`** to avoid committing tokens
- **Use environment variables** for all credentials
- **Rotate tokens regularly** in production
- **Consider token expiration** - OAuth tokens auto-refresh, Basic auth tokens don't expire

## 📚 References

- [Emplifi Listening API Documentation](https://developers.emplifi.io/reference/listening-api)
- [Emplifi OAuth 2.0 Guide](https://developers.emplifi.io/reference/oauth-2-0)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)

## 🐛 Troubleshooting

### Common Issues

**"No authentication configured"**
- Check that environment variables are set correctly
- Ensure either OAuth or Basic auth credentials are provided

**"No valid access token available"**
- For OAuth: Run the initial authentication script
- For Basic auth: Check that token/secret are correct

**"Token refresh failed"**
- OAuth tokens may have expired or been revoked
- Re-run the initial authentication script

**API rate limits**
- The Emplifi API has rate limits
- Consider adding delays between requests for large operations
- Use pagination wisely (`max_pages` parameter)

### Debug Mode

Enable debug logging to see detailed API requests:

```python
import structlog
structlog.configure(level="DEBUG")
```
