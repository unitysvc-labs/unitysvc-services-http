## HTTP Relay — Multi-Enrollment

Route HTTP requests through the UnitySVC gateway using your own upstream endpoints. Unlike the simple BYOE service, this allows **multiple enrollments** — each enrollment connects to a different upstream HTTP endpoint.

### Use Cases

- **Dev + Prod**: one enrollment for your staging API, another for production
- **Multi-tenant**: different upstream endpoints for different clients or projects
- **Multiple providers**: separate enrollments for different third-party APIs under one account

### Setup

1. **Create customer secrets** for each upstream endpoint you want to use. Use a naming convention to keep them organized:

   ```
   # First endpoint (e.g., staging API)
   STAGING_API_URL = https://api.staging.example.com
   STAGING_API_KEY = sk-staging-xxxxx

   # Second endpoint (e.g., production API)
   PROD_API_URL = https://api.example.com
   PROD_API_KEY = sk-prod-xxxxx
   ```

2. **Enroll** in this service, providing the secret names as parameters:

   For the staging enrollment:
   - `base_url_secret` = `STAGING_API_URL`
   - `api_key_secret` = `STAGING_API_KEY`

   For the production enrollment:
   - `base_url_secret` = `PROD_API_URL`
   - `api_key_secret` = `PROD_API_KEY`

3. **Send requests** through each enrollment's unique gateway endpoint using your svcpass API key

### How It Works

Each enrollment resolves `${ customer_secrets.{{ params.base_url_secret }} }` to look up the secret name from your enrollment parameters, then retrieves the actual credential from your customer secrets. This indirection allows the same service template to support unlimited HTTP endpoint configurations.

### svcpass handling — `api_key_secret` dispositions

Your svcpass key authenticates you to the gateway. What the gateway sends to your upstream is controlled by the **value** of the customer secret you named in `api_key_secret` — four dispositions are recognized (see [unitysvc#1198](https://github.com/unitysvc/unitysvc/issues/1198)). Disposition is per-enrollment because `api_key_secret` is, so a dev enrollment can strip while a prod enrollment overrides without changing the offering.

| Value of the secret named by `api_key_secret` | Behavior | When to use |
|---|---|---|
| **unset / empty** (or `api_key_secret` itself left blank) | **strip** — gateway removes the svcpass-bearing header and injects nothing | Public upstream, or you authenticate via a *different* header (see "Header co-existence" below) |
| `__strip__` | **strip** (explicit synonym of the unset default) | Same as unset, but makes the intent visible in your enrollment |
| `__forward__` | **forward** — gateway passes your svcpass token through to the upstream untouched on its original header | Only valid when the enrollment's `base_url_secret` resolves to a trusted (svcpass-aware) host. Rejected at validate-time for arbitrary external hosts — svcpass is a platform credential and the platform refuses to leak it to untrusted upstreams |
| _any other literal_ (e.g. `sk-prod-xxxxx`) | **override** — gateway removes svcpass and injects this value on the **same header** your client used | Default for normal upstreams that have their own API key. Header is `Authorization` (scheme `Bearer`) if you sent svcpass on `Authorization`, otherwise the raw value on `x-api-key` / `x-goog-api-key` |

The sentinels (`__strip__`, `__forward__`) are matched as authored literals after customer-secret resolution. If you set a secret to either reserved token, the gateway treats it as the disposition, not as a credential — don't use them as real upstream keys.

#### Header co-existence

A non-svcpass token you send on a *different* recognized header (`Authorization`, `x-api-key`, or `x-goog-api-key`) passes through to your upstream **untouched**. If your upstream takes its credential on a different header than where you placed svcpass, the two tokens co-exist — `__strip__` plus an inline upstream credential on a side-channel header is the canonical way to authenticate to your upstream without storing the key on UnitySVC at all.
