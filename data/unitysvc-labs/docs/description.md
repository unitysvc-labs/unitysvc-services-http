## HTTP Relay

Route HTTP requests through the UnitySVC gateway to your own upstream HTTP endpoint.

### Usage

Configure your HTTP client with:

- **Gateway URL**: `SERVICE_BASE_URL` (provided on enrollment)
- **Auth**: HTTP Basic Auth
- **Username**: your service routing key
- **Password**: your svcpass API key

The gateway authenticates you, resolves your upstream endpoint from your enrollment, and proxies the request.
