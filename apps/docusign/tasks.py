from __future__ import absolute_import, unicode_literals

import json

from celery import shared_task
from django.conf import settings

from apps.docusign.tokens import docusign_token
import requests

DS_CONFIG = getattr(settings, "DS_CONFIG", None)
DS_JWT = getattr(settings, "DS_JWT", None)


@shared_task(name='get_docusign_token')
def get_and_update_session_token():
    try:
        token = docusign_token()
        post_data = {'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer', 'assertion': token }
        base_url = f"https://{DS_JWT['authorization_server']}/oauth/token"
        response = requests.post(base_url, data=post_data)
        token = response.json()
        f = open(DS_JWT['session_store_file'], "w")
        json.dump(token, f)
        f.close()
        print('task get token ran successfully')
    except Exception as err:
        print(err)

