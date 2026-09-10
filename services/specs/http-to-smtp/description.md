# HTTP-to-SMTP

Post a message to the UnitySVC API Gateway; it leaves as a real email through an
SMTP server **you** control.

This is the inverse of `smtp-to-http`. Where that service turns an inbound email
into an HTTP call, this one turns an inbound HTTP call into an outbound email —
the missing HTTP-in / email-out leg.

## What it accepts

Two body shapes, detected automatically:

| You post | Shape | Used when |
|---|---|---|
| `subject`, `text_body`, `html_body`, `attachments`, `headers` | **`email`** — the faithful payload | You are relaying a message: threading headers, both body parts and attachments survive |
| `title`, `body`, `type`, `format` | **`msg`** — the compact envelope | You are sending a notification and only have a title and a body |

The faithful shape is exactly what the `smtp-to-http` converter emits, so an
inbound email can be fanned out to this service without reshaping.

```jsonc
// the email shape
{
  "from": "alerts@example.com",
  "to": ["oncall@example.com"],
  "subject": "Disk alert",
  "text_body": "clickhouse disk 92%",
  "html_body": "<p>clickhouse disk <b>92%</b></p>",
  "headers": { "In-Reply-To": "<incident-4711@example.com>" },
  "attachments": [
    { "filename": "disk.csv", "content_type": "text/csv", "content_b64": "…" }
  ]
}
```

`from` and `to` fall back to the channel's configured sender and recipient when
the payload omits them. A message with no recipient anywhere, or no sender
anywhere, is rejected with a 400.

## What you get back

A 2xx means **accepted for delivery**, not delivered — the message is queued and
submitted to your SMTP server by a worker, exactly as the SMTP gateway's own
`250` works. Rejections that can be detected up front (no recipient, no sender,
an unrecognised body, an oversized payload) come back as 4xx immediately.

## The two channels

### `byok` — one SMTP server, free

Store your server in customer secrets and every call uses it:

| Secret | Meaning | Default |
|---|---|---|
| `HTTP_TO_SMTP_HOST` | SMTP hostname | *required* |
| `HTTP_TO_SMTP_PORT` | SMTP port | `587` |
| `HTTP_TO_SMTP_TLS` | `starttls`, `ssl`, or `none` | `starttls` |
| `HTTP_TO_SMTP_USERNAME` | SMTP username | empty |
| `HTTP_TO_SMTP_PASSWORD` | SMTP password | empty |
| `HTTP_TO_SMTP_FROM` | fallback envelope sender | empty |
| `HTTP_TO_SMTP_TO` | fallback recipient | empty |

Reach it at the canonical service URL:

```bash
curl -X POST "$API_GATEWAY_BASE_URL/http-to-smtp" \
  -H "Authorization: Bearer $UNITYSVC_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Disk alert","body":"clickhouse disk 92%","type":"warning","format":"text"}'
```

### `plus` — many SMTP servers, $1 per 1,000 messages

Enroll once per destination. Each enrollment binds its own host, port, TLS mode,
sender and recipient, and names the secrets holding its credentials:

| Parameter | Meaning | Default |
|---|---|---|
| `host` | SMTP hostname | `mailpit.unitysvc.dev` |
| `port` | SMTP port | `1025` |
| `tls` | `starttls`, `ssl`, or `none` | `none` |
| `from` | fallback envelope sender | the mailpit test sender |
| `to` | fallback recipient | the mailpit test recipient |
| `username_secret` | **name** of the secret holding the username | `HTTP_TO_SMTP_USERNAME` |
| `password_secret` | **name** of the secret holding the password | `HTTP_TO_SMTP_PASSWORD` |

Credentials are named, never inlined — the value stays in your secret store. Each
enrollment is reached at its own `/e/<code>` URL:

```bash
curl -X POST "$API_GATEWAY_BASE_URL/e/<code>" \
  -H "Authorization: Bearer $UNITYSVC_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"subject":"Disk alert","text_body":"clickhouse disk 92%"}'
```

## Sending through the UnitySVC SMTP gateway instead

This service always talks to a server **you** name, and refuses a host that
resolves back to the platform's own SMTP gateway. To deliver through the UnitySVC
SMTP gateway — and reach everything behind it (BYOK relays, aliases, broadcast
groups, enrollment codes) with your own svcpass replayed as the credential — use
the `http-to-smtp-gateway` service instead.

## Limits

- Recipients are capped at 10 per message.
- The payload is capped at 8 MiB; larger bodies get a 413.
- `tls: none` is accepted for testing sinks and trusted internal relays. Anything
  crossing a public network should use `starttls` or `ssl`.
- Delivery is queued: per-recipient bounces and DSNs are not surfaced on the HTTP
  response.
