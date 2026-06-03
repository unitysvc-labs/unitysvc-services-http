## HTTP Relay — Bring Your Own Endpoint

Route HTTP requests through the UnitySVC gateway using your own upstream HTTP endpoint and optional API key.

### Request Flow

```mermaid
sequenceDiagram
    autonumber
    participant U as User / Client
    participant G as UnitySVC Gateway
    participant E as Your Upstream<br/>(HTTP_RELAY_BASE_URL)

    U->>G: HTTP request<br/>Authorization: svcpass-xxx
    Note over G: Authenticate svcpass key<br/>Resolve enrollment secrets
    G->>E: Forwarded request<br/>Authorization: HTTP_RELAY_API_KEY
    E-->>G: Response
    G-->>U: Response
```

### Setup

1. **Enroll** in this service on the UnitySVC platform
2. **Provide your endpoint credentials** as customer secrets during enrollment:
   - `HTTP_RELAY_BASE_URL` — your upstream HTTP base URL (e.g., `https://api.example.com`)
   - `HTTP_RELAY_API_KEY` — your upstream API key (optional, leave empty if not needed)

3. **Send requests** through the UnitySVC HTTP gateway using your svcpass API key

### svcpass handling

Your svcpass key authenticates you to the gateway and is **never forwarded to your upstream**. What the gateway sends upstream depends on whether you set `HTTP_RELAY_API_KEY`:

- **No `HTTP_RELAY_API_KEY`** (unset/empty) — the gateway **strips** svcpass and forwards no auth. Use this for public or unauthenticated upstreams.
- **`HTTP_RELAY_API_KEY` set** — the gateway **overrides** svcpass with your key on the same header your client used (`Authorization` → `Bearer <key>`, otherwise the raw header value).

A non-svcpass token you send on a *different* accepted header (`Authorization`, `x-api-key`, or `x-goog-api-key`) passes through to your upstream untouched, so your own provider credential and svcpass can co-exist.

### Usage

Configure your HTTP client with:
- **Gateway URL**: `SERVICE_BASE_URL` (provided on enrollment)
- **Auth**: HTTP Basic Auth — username is the routing key, password is your svcpass API key

The gateway authenticates you, resolves your upstream endpoint from your enrollment secrets, and proxies the request.

### Supported Upstream Providers

Any HTTP/HTTPS endpoint works. Common use cases:
- **REST APIs**: any JSON or REST API behind your own auth
- **Internal services**: expose internal services through the gateway
- **Third-party APIs**: proxy requests to OpenAI, Stripe, etc. with your own keys
