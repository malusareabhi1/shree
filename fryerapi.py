from fyers_apiv2 import accessToken
from fyers_apiv2 import fyersModel

# STEP 1: App details
client_id = "YOUR_CLIENT_ID"
secret_key = "YOUR_SECRET_KEY"
redirect_uri = "https://127.0.0.1"  # Must match portal
grant_type = "authorization_code"
response_type = "code"
state = "sample"

# STEP 2: Generate auth code URL
session = accessToken.SessionModel(
    client_id=client_id,
    secret_key=secret_key,
    redirect_uri=redirect_uri,
    response_type=response_type,
    state=state
)

auth_url = session.generate_authcode()
print("Login URL:", auth_url)
