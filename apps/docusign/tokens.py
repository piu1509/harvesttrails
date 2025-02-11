import json

from jose import jws
from cryptography.hazmat.primitives import serialization as crypto_serialization
import time
from django.conf import settings

DS_CONFIG = getattr(settings, "DS_CONFIG", None)
DS_JWT = getattr(settings, "DS_JWT", None)


def docusign_token():
    iat = time.time()
    exp = iat + (3600 * 24)
    payload = {
        "sub": DS_JWT['ds_impersonated_user_id'],
        "iss": DS_JWT['ds_client_id'],
        "iat": iat,  # session start_time
        "exp": exp,  # session end_time
        "aud": DS_JWT['authorization_server'],
        "scope": "signature"
    }
    with open(DS_JWT['private_key_file'], "rb") as key_file:
        private_key = crypto_serialization.load_pem_private_key(key_file.read(), password=None)
    key = private_key.private_bytes(crypto_serialization.Encoding.PEM, crypto_serialization.PrivateFormat.PKCS8,
                                    crypto_serialization.NoEncryption())
    jwt_token = jws.sign(payload, key, algorithm='RS256')
    return jwt_token


def get_docusign_token():
    print("its is in token file")
    f= open(DS_JWT['session_store_file'])
    token = json.load(f)
    print(f'token is {token}')
    return token
