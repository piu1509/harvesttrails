from intuitlib.client import AuthClient
from django.conf import settings

def get_auth_client():
    client_id = settings.QUICKBOOKS_CLIENT_ID
    client_secret = settings.QUICKBOOKS_CLIENT_SECRET
    redirect_uri = settings.QUICKBOOKS_REDIRECT_URI
    environment = 'sandbox'  # or 'production'

    auth_client = AuthClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        environment=environment
    )
    return auth_client