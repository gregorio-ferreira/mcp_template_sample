# JSON-RPC examples

### What it is (in one line)

JSON-RPC 2.0 is a lightweight, transport-agnostic RPC protocol that uses JSON to call methods and return results or errors. The spec defines the message shapes (request, response, error, batch, notification). ([jsonrpc.org](https://www.jsonrpc.org/specification "JSON-RPC 2.0 Specification"))

### Minimal request/response

Client calls a method and supplies an `id`; server returns a matching `id` with either `result` or `error`.

```json
// request
{ "jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1 }

// response
{ "jsonrpc": "2.0", "result": 19, "id": 1 }
```

This mirrors the spec’s example. ([jsonrpc.org](https://www.jsonrpc.org/specification "JSON-RPC 2.0 Specification"))

### Notification (no response)

If you omit `id`, it’s a notification and the server MUST NOT reply.

```json
{ "jsonrpc": "2.0", "method": "update", "params": [1,2,3,4,5] }
```

Per spec §4.1, notifications get no response. ([jsonrpc.org](https://www.jsonrpc.org/specification "JSON-RPC 2.0 Specification"))

### Error response

On failure, the server returns an `error` object with a code and message (e.g., method not found = `-32601`).

```json
// request for a missing method
{ "jsonrpc": "2.0", "method": "foobar", "id": "1" }

// error response
{
  "jsonrpc": "2.0",
  "error": { "code": -32601, "message": "Method not found" },
  "id": "1"
}
```

Error object and codes are defined in §5/§5.1. ([jsonrpc.org](https://www.jsonrpc.org/specification "JSON-RPC 2.0 Specification"))

### Batch requests

Send an array of request objects; you’ll get an array of responses (order may differ). Notifications inside a batch still get no response.

```json
[
  { "jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1" },
  { "jsonrpc": "2.0", "method": "notify_hello", "params": [7] },
  { "jsonrpc": "2.0", "method": "subtract", "params": [42,23], "id": "2" }
]
```

The spec’s §6/§7 shows request and response shapes for batches. ([jsonrpc.org](https://www.jsonrpc.org/specification "JSON-RPC 2.0 Specification"))

### Typical HTTP POST (one common transport)

JSON-RPC is transport-independent, but many APIs carry it over HTTP with `Content-Type: application/json`.

```bash
curl -X POST https://api.example.com/rpc \
  -H "Content-Type: application/json" \
  -d '{ "jsonrpc":"2.0", "method":"subtract", "params":[42,23], "id":1 }'
```

The protocol itself is transport-agnostic (stdio, sockets, HTTP, etc.); HTTP usage like this is a common convention documented by third-party guides. ([jsonrpc.org](https://www.jsonrpc.org/specification "JSON-RPC 2.0 Specification"), [simple-is-better.org](https://www.simple-is-better.org/json-rpc/transport_http.html?utm_source=chatgpt.com "JSON-RPC 2.0 Transport: HTTP - simple is better"))

If you want, I can turn one of these into a tiny server/client snippet in Python or TypeScript.
