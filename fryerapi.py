from fyers_apiv3 import fyersModel
#from fyers_apiv3.fyers_api import accessToken
from fyers_apiv3 import accessToken, fyersModel


# --- Step 1: App details ---
client_id = "YOUR_CLIENT_ID"             # Format: ABC123-100
secret_key = "YOUR_SECRET_KEY"
redirect_uri = "https://127.0.0.1"       # Must match exactly in Fyers app
response_type = "code"
grant_type = "authorization_code"
state = "sample_state"

# --- Step 2: Create Session Model for generating auth URL ---
session = accessToken.SessionModel(
    client_id=client_id,
    secret_key=secret_key,
    redirect_uri=redirect_uri,
    response_type=response_type,
    state=state
)

# --- Step 3: Generate Login URL and Print ---
auth_url = session.generate_authcode()
print("🔐 Login URL:", auth_url)

# --- Step 4: After user login, you will get `auth_code` as a query param ---
# Replace 'AUTH_CODE_FROM_CALLBACK' with actual code
auth_code = input("Paste the received auth_code here: ")
session.set_token(auth_code)

# --- Step 5: Exchange auth_code for access token ---
response = session.generate_token()
print("✅ Access Token Response:")
print(response)

# You can now use: response['access_token']
