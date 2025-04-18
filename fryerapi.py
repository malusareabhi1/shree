from fyers_apiv3 import accessToken
import webbrowser

client_id = "YOUR_APP_ID"
secret_key = "YOUR_APP_SECRET"
redirect_uri = "https://127.0.0.1/"  # Must match the one you set in your app
response_type = "code"
state = "sample"

session = accessToken.SessionModel(
    client_id=client_id,
    secret_key=secret_key,
    redirect_uri=redirect_uri,
    response_type=response_type,
    state=state
)

# Step 1: Open this URL to get the authorization code
auth_url = session.generate_authcode()
webbrowser.open(auth_url)
print("Go to this URL, login, and paste the 'code' from the URL here.")


auth_code = input("Enter the auth code from URL: ")

session.set_token(auth_code)
access_token = session.generate_token()["access_token"]

# Save this token securely — it expires every 24 hours
print("Access Token:", access_token)

