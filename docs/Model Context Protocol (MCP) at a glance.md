# Model Context Protocol (MCP) at a glance

The Model Context Protocol is an open, transport-agnostic standard that lets AI applications (clients/hosts) securely discover and call external “servers” that expose tools, resources, and prompts, using JSON-RPC 2.0 with a defined handshake, capability negotiation, and lifecycle. Think of it as a USB-C–like connector for agents to talk to APIs, files, and services in a consistent way. The authoritative spec is maintained at modelcontextprotocol.io and uses RFC-style MUST/SHOULD requirements. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18 "Specification - Model Context Protocol"))

MCP originated at Anthropic in November 2024 and has continued to evolve through 2025 (for example, the current base spec revision is 2025-06-18; lifecycle examples reference 2025-03-26). ([Anthropic](https://www.anthropic.com/news/model-context-protocol "Introducing the Model Context Protocol \ Anthropic"), [Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18 "Specification - Model Context Protocol"))

## Summaries of the sources you provided

- **Anthropic docs portal (docs.anthropic.com/en/docs/mcp).** Landing page that defines MCP, reiterates the “USB-C for AI” analogy, and links to the official spec, SDKs, and product integrations (Claude Desktop, Claude Code, Messages API). Good jumping-off point rather than the spec itself. ([Anthropic](https://docs.anthropic.com/en/docs/mcp "Model Context Protocol (MCP) - Anthropic"))

- **IBM Think overview.** Explains the host-client-server model, where clients translate host requests into MCP calls and servers expose tools/resources/prompts. Describes JSON-RPC messaging and common transports, and clarifies that MCP complements orchestration frameworks like LangChain/LangGraph rather than replacing them. ([IBM](https://www.ibm.com/think/topics/model-context-protocol "What is Model Context Protocol (MCP)? | IBM"))

- **GitHub organization (github.com/modelcontextprotocol).** Organization hub with the spec repo, official SDKs (Python, TS, Java, Kotlin, C#, Go, Ruby, Rust), maintained servers, and **Inspector** (a visual testing tool). Notes that the project is run by Anthropic PBC but open to community contributions. ([GitHub](https://github.com/modelcontextprotocol "Model Context Protocol · GitHub"))

- **Getting started intro (modelcontextprotocol.io/docs/getting-started/intro).** Short “what is MCP” page plus entry points to concepts, SDKs, and quickstarts to build servers and clients. Emphasizes a growing catalog of integrations and that anyone can implement the protocol. ([Model Context Protocol](https://modelcontextprotocol.io/docs/getting-started/intro "Introduction - Model Context Protocol"))

- **Anthropic announcement (Nov 25, 2024).** Introduces MCP as an open standard for secure, two-way connections between data sources and AI tools, and highlights early components and product integrations. ([Anthropic](https://www.anthropic.com/news/model-context-protocol "Introducing the Model Context Protocol \ Anthropic"))

- **Wikipedia.** Community overview covering purpose, history, transport options (stdio and HTTP with optional SSE/streaming), and broad industry adoption summaries. Useful for background, but always defer to the spec for normative details. ([Wikipedia](https://en.wikipedia.org/wiki/Model_Context_Protocol "Model Context Protocol - Wikipedia"))

## What it means to be “MCP-compliant”

Below is the practical, spec-based checklist for **minimum compliance** (server and client). The MUST/SHOULD words mirror the spec.

### Base protocol and lifecycle

- Use **JSON-RPC 2.0** UTF-8 messages. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18 "Specification - Model Context Protocol"))

- Implement the **initialization handshake** as the very first interaction:
  
  - Client sends `initialize` with `protocolVersion`, declared **capabilities**, and `clientInfo`.
  
  - Server replies with its **capabilities** and `serverInfo`.
  
  - Client then sends `initialized`.  
    The `initialize` request MUST NOT be batched. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle "Lifecycle - Model Context Protocol"))

### Capabilities and features

- A server may expose any of: **resources**, **prompts**, **tools**. If you expose one, you **MUST** declare that capability during initialization and implement its list/get/read calls. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18 "Specification - Model Context Protocol"))
  
  - **Tools:** implement `tools/list` and `tools/call`. Each tool has a `name`, human-readable metadata, an **inputSchema** (JSON Schema), and may include an **outputSchema**. ([Model Context Protocol](https://modelcontextprotocol.io/docs/concepts/tools "Tools - Model Context Protocol"))
  
  - **Resources:** implement `resources/list` and `resources/read`; each resource is identified by a **URI**. Optional `subscribe` and `listChanged` behaviors are negotiated via capability flags. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18/server/resources "Resources - Model Context Protocol"))
  
  - **Prompts:** implement `prompts/list` and `prompts/get`; expose optional arguments and support pagination. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18/server/prompts "Prompts - Model Context Protocol"))

### Transports

- Support at least one **standard transport**:
  
  - **stdio** (client spawns server; strict rule: nothing but MCP on stdout).
  
  - **Streamable HTTP** (single MCP endpoint handling POST and optional GET for SSE-style streaming).  
    The spec includes precise requirements for headers, batching, SSE behavior, and session management. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports "Transports - Model Context Protocol"))

### Authorization (for HTTP transports)

- **Optional** but recommended. When present, follow the MCP auth profile based on OAuth 2.1.
  
  - Clients **MUST** support Authorization Server Metadata (RFC 8414).
  
  - Servers **SHOULD** support dynamic client registration and choose appropriate grant types (auth code, client credentials).
  
  - STDIO servers typically use environment-based credentials instead. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization "Authorization - Model Context Protocol"))

### Error handling and versioning

- Use standard JSON-RPC errors for protocol failures; feature chapters define common codes (for example, resource not found). ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18/server/resources "Resources - Model Context Protocol"))

- Include a concrete **protocol version** string in `initialize` and follow the revision’s semantics (for example, 2025-06-18). Backwards-compat notes cover HTTP transport changes from earlier revisions. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle "Lifecycle - Model Context Protocol"))

### Security and safety considerations

- **Tools:** validate inputs, enforce access control, rate-limit, sanitize outputs; put a human in the loop for sensitive actions (UI confirmation, visible indicators). ([Model Context Protocol](https://modelcontextprotocol.io/docs/concepts/tools "Tools - Model Context Protocol"))

- **Resources:** validate URIs, check permissions, encode binary data properly. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18/server/resources "Resources - Model Context Protocol"))

- **HTTP transport:** validate the **Origin** header, bind to localhost in dev, and require auth; otherwise DNS-rebinding can expose local servers. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports "Transports - Model Context Protocol"))

### Operational hygiene

- For **stdio servers**, never write logs to stdout; log to **stderr** (or files) to avoid corrupting the JSON-RPC stream. ([Model Context Protocol](https://modelcontextprotocol.io/quickstart/server "Build an MCP Server - Model Context Protocol"))

## Practical recommendations

- **Use an official SDK** (Python, TypeScript, Java, Kotlin, C#, Go, etc.) to abstract the wire protocol and reduce foot-guns. ([GitHub](https://github.com/modelcontextprotocol "Model Context Protocol · GitHub"))

- **Ship JSON Schemas** for all tool inputs (and outputs when structured) so clients and LLMs can validate and parse reliably. ([Model Context Protocol](https://modelcontextprotocol.io/docs/concepts/tools "Tools - Model Context Protocol"))

- **Implement capability flags** (`listChanged`, `subscribe`) only if you truly support them; clients rely on these at runtime. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18/server/resources "Resources - Model Context Protocol"))

- **Prefer Streamable HTTP** for remote servers and stdio for local integrations. If you support HTTP, follow the spec’s Accept/Content-Type rules and SSE behavior. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports "Transports - Model Context Protocol"))

- **Test with Inspector** to exercise listing, calling, streaming, and error paths in a UI. ([GitHub](https://github.com/modelcontextprotocol "Model Context Protocol · GitHub"))

- **Document security expectations** (auth scopes, rate limits, data residency) in your server README even though MCP doesn’t mandate a specific policy. The transport and feature chapters include concrete security considerations. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization "Authorization - Model Context Protocol"))

## Bottom line

- **What is the standard?** MCP is an open, JSON-RPC–based protocol that standardizes how AI apps discover capabilities and exchange context with external systems, with a strict lifecycle, capability negotiation, and defined feature surfaces for tools, resources, and prompts. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18 "Specification - Model Context Protocol"))

- **How to comply?** Implement the handshake and lifecycle, declare and implement the features you expose, conform to a supported transport (stdio or Streamable HTTP), follow the error and security guidance, and, if using HTTP, follow the OAuth-based authorization profile. Use SDKs and Inspector to validate behavior. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle "Lifecycle - Model Context Protocol"))

- [The Verge](https://www.theverge.com/news/669298/microsoft-windows-ai-foundry-mcp-support?utm_source=chatgpt.com)
- [Axios](https://www.axios.com/2025/04/17/model-context-protocol-anthropic-open-source?utm_source=chatgpt.com)
