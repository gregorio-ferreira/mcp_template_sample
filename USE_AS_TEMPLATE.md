# Using This Project as an MCP Server Template

This repository is designed to be used as a **template** for creating your own Model Context Protocol (MCP) servers. The existing time and timezone tools are **reference examples only** and should be replaced with your own tools that expose APIs, databases, or other services.

## 🎯 Template Purpose

This template helps you quickly create production-ready MCP servers that can:
- **Expose existing APIs** as MCP tools for AI agents
- **Wrap database operations** in a standardized interface
- **Integrate third-party services** (AWS, Google Cloud, etc.)
- **Provide custom business logic** to AI agents
- **Create conversational interfaces** with LangChain/LangGraph

## 🚀 Quick Start: Using as Template

### 1. Clone and Setup
```bash
# Clone this template
git clone <your-template-repo-url> my-mcp-server
cd my-mcp-server

# Install dependencies
make setup

# Test the template works
make run
make check-server  # In another terminal
```

### 2. Clean Demo Tools (Optional)
If you want to start fresh without the demo tools:

```bash
# Remove demo tools
rm src/mcp_server/tools/time_tools.py
rm tests/test_tools/test_time_tools.py

# Clean tool exports
echo "# Add your tool imports here" > src/mcp_server/tools/__init__.py

# Clean server registration (keep the structure)
# Edit src/mcp_server/server.py and remove time tool registrations
```

### 3. Add Your Tools
Follow the patterns in the existing code to add your own tools.

## 📚 Reference Examples (Remove These)

The template includes these **reference tools** that you should replace:

### Current Demo Tools
- **`time_tools.py`** - Timezone conversion and Unix timestamps
  - `convert_timezone()` - Convert between time zones
  - `to_unix_time()` - Convert to Unix timestamps
- **`file_tools.py`** - Template for file operations (placeholder)
- **`data_tools.py`** - Template for data processing (placeholder)

### Test Infrastructure
- **`test_mcp_server.sh`** - Keep this for testing your tools
- **`test_mcp_client.py`** - Keep this for integration testing
- **`mcp_chat_agent.py`** - Keep this for conversational testing

## 🛠️ Adding Your Own Tools

### Step 1: Create Your Tool Module

Create a new file `src/mcp_server/tools/my_api_tools.py`:

```python
"""Tools for integrating with My API service."""
from typing import Annotated, Optional
import httpx
from pydantic import BaseModel


class ApiResponse(BaseModel):
    """Response from My API."""
    data: dict
    status: str


async def get_user_data(
    user_id: Annotated[str, "User ID to fetch"],
    include_details: Annotated[bool, "Include detailed information"] = False,
) -> ApiResponse:
    """Fetch user data from My API.
    
    This tool connects to your API service and retrieves user information.
    Perfect for AI agents that need access to user data.
    """
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://my-api.com/users/{user_id}"
            params = {"details": include_details}
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            return ApiResponse(
                data=response.json(),
                status="success"
            )
    except httpx.HTTPStatusError as e:
        raise ValueError(f"API request failed: {e.response.status_code}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch user data: {e}")


def create_user(
    name: Annotated[str, "User's full name"],
    email: Annotated[str, "User's email address"],
    role: Annotated[str, "User role"] = "user",
) -> dict:
    """Create a new user in the system.
    
    This tool allows AI agents to create users in your system.
    """
    # Your implementation here
    return {
        "user_id": "12345",
        "name": name,
        "email": email,
        "role": role,
        "created": True
    }
```

### Step 2: Register Your Tools

Edit `src/mcp_server/server.py`:

```python
from mcp_server.tools.my_api_tools import get_user_data, create_user

def register_tools() -> None:
    """Register all available tools with the MCP server."""
    
    # Remove these demo tool registrations:
    # mcp.tool()(convert_timezone)
    # mcp.tool()(to_unix_time)
    
    # Add your tools:
    mcp.tool()(get_user_data)
    mcp.tool()(create_user)
```

### Step 3: Export Your Tools (Optional)

Add to `src/mcp_server/tools/__init__.py`:

```python
from .my_api_tools import get_user_data, create_user

__all__ = ["get_user_data", "create_user"]
```

### Step 4: Add Tests

Create `tests/test_tools/test_my_api_tools.py`:

```python
"""Tests for My API tools."""
import pytest
from mcp_server.tools.my_api_tools import create_user


def test_create_user():
    """Test user creation."""
    result = create_user(
        name="John Doe",
        email="john@example.com",
        role="admin"
    )
    
    assert result["name"] == "John Doe"
    assert result["email"] == "john@example.com"
    assert result["role"] == "admin"
    assert result["created"] is True


@pytest.mark.asyncio
async def test_get_user_data():
    """Test user data fetching."""
    # Mock your API calls here
    pass
```

### Step 5: Test Your Tools

```bash
# Start server
make run

# Test with curl (in another terminal)
make test-server

# Test with Python client
make test-client

# Test with AI agent
make chat
```

## 🏗️ Common Use Cases & Examples

### 1. Database Integration
```python
async def query_database(
    table: Annotated[str, "Table name"],
    filters: Annotated[dict, "Query filters"],
) -> list[dict]:
    """Query your database and return results."""
    # Implementation with your DB client
    pass
```

### 2. AWS Services Integration
```python
async def upload_to_s3(
    bucket: Annotated[str, "S3 bucket name"],
    key: Annotated[str, "Object key"],
    content: Annotated[str, "File content"],
) -> dict:
    """Upload content to AWS S3."""
    # Implementation with boto3
    pass
```

### 3. External API Wrapper
```python
async def send_notification(
    recipient: Annotated[str, "Notification recipient"],
    message: Annotated[str, "Message content"],
    priority: Annotated[str, "Priority level"] = "normal",
) -> bool:
    """Send notification via external service."""
    # Implementation with requests/httpx
    pass
```

### 4. Business Logic Tools
```python
def calculate_pricing(
    product_id: Annotated[str, "Product identifier"],
    quantity: Annotated[int, "Quantity to price"],
    discount_code: Annotated[str, "Discount code"] = None,
) -> dict:
    """Calculate pricing for products with discounts."""
    # Your business logic here
    pass
```

## 🔧 Configuration for Your Use Case

### Environment Variables
Add your specific configuration to `.env`:

```bash
# Your API Configuration
MY_API_KEY=your-api-key
MY_API_BASE_URL=https://api.example.com
DATABASE_URL=postgresql://user:pass@localhost/db

# Existing MCP Configuration
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_PATH=/mcp
OPENAI_API_KEY=your-openai-key  # For AI agents
```

### Dependencies
Add your dependencies to `pyproject.toml`:

```toml
dependencies = [
    "fastmcp>=2.0",
    "pydantic>=2.5",
    # Add your dependencies:
    "httpx>=0.27",        # For HTTP clients
    "asyncpg>=0.29",      # For PostgreSQL
    "boto3>=1.34",        # For AWS services
    "redis>=5.0",         # For caching
    # ... your other dependencies
]
```

## 🧪 Testing Your Implementation

### Complete Testing Workflow
```bash
# 1. Install your dependencies
make setup

# 2. Run your code quality checks
make format
make lint
make mypy

# 3. Run unit tests
make test

# 4. Start server and test integration
make run              # Terminal 1
make check-server     # Terminal 2
make test-server      # Test with curl
make test-client      # Test with Python

# 5. Test with AI agent
make chat
```

### Test Your Tools Work
1. **Unit tests** - Test individual tool logic
2. **Integration tests** - Test via MCP protocol
3. **Agent tests** - Test with conversational AI
4. **Manual testing** - Use the provided test scripts

## 📝 Best Practices

### Tool Design
- **One responsibility per tool** - Keep tools focused
- **Clear descriptions** - AI agents read these
- **Proper error handling** - Return meaningful errors
- **Type hints everywhere** - Use `Annotated` for parameters
- **Async when needed** - For I/O operations

### Security Considerations
- **Validate inputs** - Use Pydantic models for complex data
- **Sanitize outputs** - Don't expose sensitive information
- **Environment secrets** - Use `.env` for API keys
- **Rate limiting** - Consider rate limits for external APIs
- **Authentication** - Implement proper auth for your tools

### Performance Tips
- **Connection pooling** - Reuse database/HTTP connections
- **Caching** - Cache expensive operations
- **Async operations** - Use async/await for I/O
- **Batch operations** - Group related API calls

## 🚀 Deployment

### Production Checklist
- [ ] Remove demo tools (`time_tools.py`, tests)
- [ ] Add your actual tools
- [ ] Configure production environment variables
- [ ] Set up proper logging and monitoring
- [ ] Test all tools work correctly
- [ ] Document your tools in README.md
- [ ] Set up CI/CD for testing

### Deployment Options
- **Docker** - Use the provided structure
- **Cloud platforms** - AWS Lambda, Google Cloud Run
- **Traditional servers** - systemd service
- **Kubernetes** - Container orchestration

## 📖 Documentation

### Update Documentation
After customizing the template:

1. **Update README.md** - Describe your specific tools
2. **Update AGENTS.md** - Add agent-specific guidance
3. **Document your APIs** - Include examples in docstrings
4. **Create usage examples** - Update `examples/` directory

### Example README Section
```markdown
## Available Tools

### User Management
- `get_user_data(user_id)` - Fetch user information
- `create_user(name, email, role)` - Create new users
- `update_user_status(user_id, status)` - Update user status

### Data Processing  
- `process_dataset(data_url)` - Process external datasets
- `generate_report(filters)` - Generate custom reports
```

## 🆘 Support & Troubleshooting

### Common Issues
1. **Tools not appearing** - Check tool registration in `server.py`
2. **Import errors** - Verify tool exports in `__init__.py`
3. **Type errors** - Use proper type hints and `Annotated`
4. **Agent integration** - Ensure OpenAI API key is set

### Getting Help
- Review the existing `time_tools.py` for patterns
- Check test examples in `tests/test_examples/`
- Use the provided testing infrastructure
- Follow the patterns in `AGENTS.md`

---

**Remember:** This template is designed to be customized! The demo tools are just examples to show you the patterns. Replace them with tools that expose your specific APIs, databases, or services to AI agents.

Start building your MCP server by adding tools that solve your specific use case! 🚀
