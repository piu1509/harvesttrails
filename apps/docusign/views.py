from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from apps.docusign.ds_client import DSClient, DS_CONFIG, DS_JWT
from apps.docusign.consts import base_uri_suffix
from django.views.generic import View
from django.urls import reverse
from django.contrib import messages
from docusign_esign.apis import EnvelopesApi
from django.http import JsonResponse

from apps.docusign.utils import authenticate


class DsLoginView(View):
    def get(self, request):
        if not request.session.get('auth_type') is None:
            request.session["auth_type"] = "jwt"
        return DSClient.login("jwt", request)


class DsCallback(View):
    def get(self, request):
        redirect_url = request.session.pop("eg", None)
        resp = DSClient.get_token("code_grant")

        request.session["ds_access_token"] = resp["access_token"]
        request.session["ds_refresh_token"] = resp["refresh_token"]
        request.session["ds_expiration"] = datetime.utcnow() + timedelta(seconds=int(resp["expires_in"]))

        if not request.session.get("ds_account_id"):
            messages.add_message(request, messages.INFO, "You have authenticated with DocuSign.")
            # Request to API to get the user information
            response = DSClient.get_user(request.session["ds_access_token"])
            request.session["ds_user_name"] = response["name"]
            request.session["ds_user_email"] = response["email"]
            accounts = response["accounts"]
            # Find the account...
            target_account_id = DS_CONFIG["target_account_id"]
            if target_account_id:
                account = next((a for a in accounts if a["account_id"] == target_account_id), None)
                if not account:
                    # The user does not have the targeted account. They should not log in!
                    raise Exception(f"No access to target account with ID: {target_account_id}")
            else:  # get the default account
                account = next((a for a in accounts if a["is_default"]), None)
                if not account:
                    # Every user should always have a default account
                    raise Exception("No default account. Every user should always have a default account")

            # Save the account information
            request.session["ds_account_id"] = account["account_id"]
            request.session["ds_account_name"] = account["account_name"]
            request.session["ds_base_path"] = account["base_uri"] + base_uri_suffix

        if not redirect_url:
            redirect_url = reverse('core_index')
        return redirect(redirect_url)


class DsMustAuthenticate(View):
    def get(self, request):
        request.session["auth_type"] = "jwt"
        return redirect(reverse("ds_login"))


def get(request):
    return redirect(reverse('core_index'))


class DsReturn(View):
    pass


class CoreIndex(View):
    def get(self, request):
        return redirect(reverse("eg001.get_view"))


class CoreRIndex(View):
    def get(self, request):
        return redirect(reverse("core_r_index"))


class DocusignEnvelopeApi(View):
    def get(self, request):
        try:
            account_id = DS_JWT['ds_account_id']
            ds_client = DSClient()
            print("it is here")
            envelope_api = EnvelopesApi(ds_client.get_api_client())
            print("it is here.....")
            from_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
            results = envelope_api.list_status_changes(account_id=account_id, from_date=from_date)
            print(results)
            return JsonResponse(results.to_dict())
        except Exception as err:
            print(err)
