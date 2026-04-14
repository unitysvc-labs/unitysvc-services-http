import requests
import os


# Local testing: connect directly to upstream HTTP endpoint
base_url = os.environ.get('HTTP_RELAY_BASE_URL', 'http://localhost:8080')
api_key = os.environ.get('HTTP_RELAY_API_KEY', '')
auth = None
headers = {'Authorization': f'Bearer {api_key}'} if api_key else {}


# Send a test HTTP GET request
response = requests.get(
    base_url,
    auth=auth,
    headers=headers,
    timeout=10,
)
print(f'Status: {response.status_code}')
print('connectivity ok')