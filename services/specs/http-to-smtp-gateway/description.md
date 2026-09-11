# HTTP-to-SMTP Gateway

Post a message to the UnitySVC API Gateway; it is delivered as email to any route
on the UnitySVC **SMTP Gateway** — as your own identity.

This is the HTTP door into the SMTP side of the platform. Everything already
reachable over SMTP — BYOK relays, aliases, tee broadcasts, enrollment codes —
becomes reachable from an HTTP caller, without re-entering SMTP credentials
anywhere.

## How the credential works

The platform submits the message to its own SMTP Gateway using:

- **SMTP username** — the route you chose (`target`)
- **SMTP password** — *your* UnitySVC API key, replayed

So the SMTP leg is metered against the same key that made the HTTP call, and any
restriction on that key carries over. The host is fixed to the platform's own
gateway, so the forwarded credential never leaves UnitySVC; you choose only the
route.

Whatever the target route bills, it bills under its own listing. This hop is free
on the `default` channel.

## What it accepts

Two body shapes, detected automatically:

| You post | Shape | Used when |
|---|---|---|
| `subject`, `text_body`, `html_body`, `attachments`, `headers` | **`email`** — the faithful payload | You are relaying a message: threading headers, both body parts and attachments survive |
| `title`, `body`, `type`, `format` | **`msg`** — the compact envelope | You are sending a notification and only have a title and a body |

The faithful shape is exactly what the `smtp-to-http` converter emits, so an
inbound email can be fanned out to this service without reshaping — which is what
makes cross-transport fan-out work:

```
email ──► smtp-to-api-gateway ──► /b/<group> ──┬─► http-to-smtp-gateway  (email → an SMTP route)
                                               ├─► http-to-smtp          (email → your own server)
                                               └─► any other leg that accepts the same shape
```

## What you get back

A 2xx means **accepted for delivery**, not delivered — the message is queued and
submitted to the SMTP Gateway by a worker, exactly as that gateway's own `250`
works. Rejections detectable up front (no recipient, no sender, an unrecognised
body, an oversized payload) come back as 4xx immediately.

## The two channels

### `default` — one route, free

| Secret | Meaning | Default |
|---|---|---|
| `HTTP_TO_SMTP_GATEWAY_TARGET` | SMTP Gateway route to deliver to | `smtp-byok` |
| `HTTP_TO_SMTP_GATEWAY_FROM` | fallback envelope sender | empty |
| `HTTP_TO_SMTP_GATEWAY_TO` | fallback recipient | empty |

```bash
curl -X POST "$API_GATEWAY_BASE_URL/http-to-smtp-gateway" \
  -H "Authorization: Bearer $UNITYSVC_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Disk alert","body":"clickhouse disk 92%","type":"warning","format":"text"}'
```

### `plus` — many routes, $1 per 1,000 messages

Enroll once per bridge. Each enrollment binds its own `target`, `from` and `to`,
and is reached at its own `/e/<code>` URL:

```bash
curl -X POST "$API_GATEWAY_BASE_URL/e/<code>" \
  -H "Authorization: Bearer $UNITYSVC_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"subject":"Disk alert","text_body":"clickhouse disk 92%"}'
```

## What `target` can name

Any route the SMTP Gateway resolves on the AUTH username:

| Form | Example | Reaches |
|---|---|---|
| a service route | `smtp-byok` | the SMTP relay bound to your own stored server |
| an alias | `a/alerts` | whatever the alias currently points at |
| a broadcast group | `b/relay` | every member of the group |
| an enrollment code | `XXXXXX` | one specific enrollment |

No scheme, no leading slash. A target the SMTP Gateway cannot resolve surfaces as
that gateway's own auth/route failure on the queued send.

## Delivering through your own server instead

This service always goes through the platform's SMTP Gateway. To deliver directly
to an SMTP server you operate, use the `http-to-smtp` service — same payload
shapes, same queued-delivery contract, your own host and credentials.

## Limits

- Recipients are capped at 10 per message.
- The payload is capped at 8 MiB; larger bodies get a 413.
- A message that has already passed through this service once is refused on
  re-entry, so an SMTP route that loops back cannot cycle.
- Delivery is queued: per-recipient bounces and DSNs are not surfaced on the HTTP
  response.
