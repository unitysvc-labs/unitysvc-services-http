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
