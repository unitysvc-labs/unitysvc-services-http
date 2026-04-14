#!/bin/bash
# Test HTTP relay connectivity

# Local testing: BASE_URL from upstream_access_config
BASE_URL=${HTTP_RELAY_BASE_URL:-http://localhost:8080}

curl -sf --max-time 5 "${BASE_URL}" -o /dev/null && echo "connectivity ok"