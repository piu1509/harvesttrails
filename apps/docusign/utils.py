from datetime import timedelta, datetime
from functools import wraps

from docusign_esign import ApiClient

from apps.docusign.ds_client import DSClient
from apps.docusign.consts import minimum_buffer_min
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def ds_logout_internal(request):
    # remove the keys and their values from the session
    request.session("ds_access_token")
    request.session("ds_refresh_token")
    request.session("ds_user_email")
    request.session("ds_user_name")
    request.session("ds_expiration")
    request.session("ds_account_id")
    request.session("ds_account_name")
    request.session("ds_base_path")
    request.session("envelope_id")
    request.session("eg")
    request.session("envelope_documents")
    request.session("template_id")
    request.session("auth_type")
    DSClient.destroy()


def create_api_client(base_path, access_token):
    """Create api client and construct API headers"""
    api_client = ApiClient()
    api_client.host = base_path
    api_client.set_default_header(header_name="Authorization", header_value=f"Bearer {access_token}")
    return api_client


def ds_token_ok(request, buffer_min=60):
    """
    :param request: the django request object
    :param buffer_min: buffer time needed in minutes
    :return: true iff the user has an access token that will be good for another buffer min
    """

    ok = "ds_access_token" in request.session and "ds_expiration" in request.session
    ok = ok and (request.session["ds_expiration"] - timedelta(minutes=buffer_min)) > datetime.utcnow()

    return ok


def authenticate(eg):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f'the args are {args}')
            print(f'the kwargs are {kwargs}')
            if ds_token_ok(args[1], minimum_buffer_min):
                return func(*args, **kwargs)
            else:
                # We could store the parameters of the requested operation
                # so it could be restarted automatically.
                # But since it should be rare to have a token issue here,
                # we"ll make the user re-enter the form data after
                # authentication.
                # args[1].session["eg"] = reverse(eg + ".get_view")
                if args[1].session.get("auth_type"):
                    messages.add_message(args[1], messages.INFO, "Token has been updated")
                    return redirect(reverse("ds_login"))
                else:
                    return redirect(reverse("ds_must_authenticate"))

        return wrapper

    return decorator
