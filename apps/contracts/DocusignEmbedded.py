import base64
import json
import os
import pathlib

import requests
from django.urls import reverse
from docusign_esign.client.api_client import ApiException, ApiClient
# from apps.docusign.utils import create_api_client
from docusign_esign import EnvelopesApi, RecipientViewRequest, Document, Signer, EnvelopeDefinition, SignHere, Tabs, \
    Recipients
from django.contrib.staticfiles.storage import staticfiles_storage
from django.conf import settings as conf_settings

from apps.docusign.consts import authentication_method

from apps.docusign.tokens import get_docusign_token
from apps.docusign.ds_client import DSClient


DS_CONFIG = getattr(conf_settings, "DS_CONFIG", None)
DS_JWT = getattr(conf_settings, "DS_JWT", None)


class DocusignEmbeddedSigningController:
    # base_path = 'https://app.docusign.com/restapi'
    # base_path = 'https://demo.docusign.net/restapi/'
    base_path = f"{DS_JWT['ds_base_url']}/restapi"
    account_id = DS_JWT['ds_account_id']
    access_token = os.getenv('DOCUSIGN_ACCESS_TOKEN',
                             'eyJ0eXAiOiJNVCIsImFsZyI6IlJTMjU2Iiwia2lkIjoiNjgxODVmZjEtNGU1MS00Y2U5LWFmMWMtNjg5ODEyMjAzMzE3In0.AQoAAAABAAUABwCAZG1bJ2baSAgAgKSQaWpm2kgCAICDdkC95i5GpGp5TompepMVAAEAAAAYAAEAAAAFAAAADQAkAAAAYWE0NDc4YWEtNWY1NC00NzE2LWJmNmUtYjkyYmJhZTE3MzEwIgAkAAAAYWE0NDc4YWEtNWY1NC00NzE2LWJmNmUtYjkyYmJhZTE3MzEwMACApT07J2baSDcATV88Of4t7Uu2E43N4saApQ.nseDCJJPxWNvb881dCqvPc376fVtFKx-SfcJ1v8cTyeIRBHcvQw1EVGhUJiF_mH7p4vLmbxFweCxS5gdbgzI8_cyXXonBGYXfutRcXczIiVjI07jYCDRvPKMhwvFo-2yOjX3HK6WIZbDFQspCkZQvwJwW90cYjTk8vCicvLJly70Zah3BQbxtAANSJdekQy31-bLjFZfFb9zPsYzVLKLjAl_iZM7anWUjhDXQx2ZcfjoFqFJ4aJwHHezmn_iIuNiPHmGEWBcvQ291pOWRly8ogB8NDZpnzhVXjMnfu83RleWgFDxOeckYYdr-xzH2vRAe9egu_Bk-wt8qjc89rFA5A')
    refresh_token = os.getenv('DOCUSIGN_REFRESH_TOKEN',
                              'eyJ0eXAiOiJNVCIsImFsZyI6IlJTMjU2Iiwia2lkIjoiNjgxODVmZjEtNGU1MS00Y2U5LWFmMWMtNjg5ODEyMjAzMzE3In0.AQoAAAABAAgABwAA8hwiXmXaSAgAAHKBGvF82kgCAICDdkC95i5GpGp5TompepMVAAEAAAAYAAEAAAAFAAAADQAkAAAAYWE0NDc4YWEtNWY1NC00NzE2LWJmNmUtYjkyYmJhZTE3MzEwIgAkAAAAYWE0NDc4YWEtNWY1NC00NzE2LWJmNmUtYjkyYmJhZTE3MzEwMACA9rYDXmXaSDcATV88Of4t7Uu2E43N4saApQ.Mi0tyuq_U2zx01VrfYW7gAQ05QwIzVmbpna5jLQ7Kj2yLo_ZvNrsyfKr-gaXskeStjrd48wBKxXyt0j_NTOL-IOhzxYkt_pWbNPIRiVum0EmRYeHz7zBaiOfBG8okU4fu8rHEBUKNKnIQmiutYH7XhY099fNkCi62pSdDTEYWB5OYbW2c7znP3XcdyA0mxMtxj9sI0mmvwwuyolYyvSanZMbceKYpxBXqDN9lp1ipEAxeVX0_6u2wrgtDM8tGIg2pTlExi5N2xTsww-f-X5cG1MeneUAxA6LDxfdrKTAgVVQiVLIrH6JtE4ipDTTvV_82xyOqDvTXLmuEPD3wp23Fg')
    # client_id = 'aa4478aa-5f54-4716-bf6e-b92bbae17310'  # integration key
    client_id = DS_JWT['ds_client_id']
    redirect_uri = 'https://dev.traceableoutcomes.tech/docusign/callback'

    def get_access_token(self):
        self.access_token = get_docusign_token()

    # api_client = ApiClient()
    # api_client.host = 'https://demo.docusign.net/restapi/'
    # SCOPES = ["signature"]
    # in_file = open(conf_settings['private_key'])
    # private_key = in_file.read()
    # in_file.close()

    # def get_client(self):
    #     try:
    #         access_token = self.api_client.request_jwt_application_token(
    #             client_id=conf_settings['client_id'],
    #             oauth_host_name="account-d.docusign.com",
    #             private_key_bytes=self.private_key,
    #             expires_in=3600,
    #             scopes=self.SCOPES
    #         )
    #         self.api_client.set_default_header(header_name="Authorization",
    #                                            header_value=f"Bearer {access_token.access_token}")
    #     except ApiException as err:
    #         print(err)

    @classmethod
    def get_args(cls, signer_email, signer_name, signer_client_id, contract, grower, request):
        """Get request and session arguments"""
        # More data validation would be a good idea here
        # Strip anything other than characters listed
        # 1. Parse request arguments
        # signer_email = signer_email
        # signer_name = signer_name
        envelope_args = {
            "signer_email": signer_email,
            "signer_name": signer_name,
            "signer_client_id": signer_client_id,
            "ds_return_url": request.build_absolute_uri(
                reverse('docusign-contract-submit', kwargs={'contract_id': contract.id, 'grower_id': grower.id})),
        }
        args = {
            "account_id": cls.account_id,
            "base_path": cls.base_path,
            "access_token": cls.access_token,
            "envelope_args": envelope_args
        }
        return args

    @classmethod
    def create_envelope(cls, envelope_api, envelope_definition):
        """
        """
        results = envelope_api.create_envelope(account_id=cls.account_id, envelope_definition=envelope_definition)
        print(f' in line 57 {results}')
        return results

    @classmethod
    def create_recipient_view_request(cls, envelope_args):
        """
        """
        recipient_view_request = RecipientViewRequest(
            authentication_method=authentication_method,
            client_user_id=envelope_args["signer_client_id"],
            recipient_id="1",
            return_url=envelope_args["ds_return_url"],
            user_name=envelope_args["signer_name"],
            email=envelope_args["signer_email"]
        )
        print(recipient_view_request)
        return recipient_view_request

    @classmethod
    def create_recipient_view(cls, envelope_api, envelope_id, recipient_view_request):
        """
        """
        results = envelope_api.create_recipient_view(
            account_id=cls.account_id,
            envelope_id=envelope_id,
            recipient_view_request=recipient_view_request
        )
        print(results)
        return results

    @classmethod
    def create_sender_view(cls, envelope_id, return_url):
        """
        """
        api_client = DSClient.get_api_client()
        envelope_api = EnvelopesApi(api_client)
        results = envelope_api.create_sender_view(
            account_id=cls.account_id,
            envelope_id=envelope_id,
            return_url_request=return_url
        )
        print(results)
        return results

    @classmethod
    def get_envelope(cls, envelope_id):
        """
        """
        api_client = DSClient.get_api_client()

        envelope_api = EnvelopesApi(api_client)
        results = envelope_api.get_envelope(
            account_id=cls.account_id,
            envelope_id=envelope_id
        )
        print(results)
        return results

    @classmethod
    def get_document_file(cls, envelope_id, document_id):
        """
        """
        api_client = DSClient.get_api_client()

        envelope_api = EnvelopesApi(api_client)
        results = envelope_api.get_document(
            account_id=cls.account_id,
            envelope_id=envelope_id,
            document_id=document_id
        )
        print(results)
        return results

    @staticmethod
    def get_error_response_body(res):
        error_body_json = res and hasattr(res, "body") and res.body
        # we can pull the DocuSign error code and message from the response body
        try:
            error_body = json.loads(error_body_json)
        except json.decoder.JSONDecodeError:
            error_body = {}
        return error_body

    def get_auth_token(self, code):
        url = "https://account-d.docusign.com/oauth/token"

        # payload = f'code={code}&grant_type=authorization_code'
        payload = f'grant_type=refresh_token&refresh_token={os.getenv("DOCUSIGN_REFRESH_TOKEN")}'
        iKeyiSec = "748c5279-9795-4b39-bd19-4df6b99e784b:ec4e772b-6334-404d-b931-39cca6cd5be3"
        b64Val = base64.b64encode(iKeyiSec.encode())
        headers = {
            'Authorization': f'Basic {b64Val}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        print(data)
        access_token = data['access_token']
        token_type = data['token_type']
        refresh_token = data['refresh_token']
        os.environ['DOCUSIGN_ACCESS_TOKEN'] = access_token
        os.environ['DOCUSIGN_REFRESH_TOKEN'] = refresh_token

    @classmethod
    def get_code_from_url(cls, request):
        print(request.build_absolute_uri(reverse('contract-list')))
        url = f"https://account-d.docusign.com/oauth/auth?response_type=code&scope=signature&client_id={cls.client_id}&redirect_uri={request.build_absolute_uri(reverse('contract-list'))}"
        response = requests.request("GET", url)
        print(f'inside code from url {response}')
        for i in response.history:
            print(i.url)

    @classmethod
    def get_list_of_documents(cls, envelope_id):
        """
        """
        try:
            api_client = DSClient.get_api_client()

            envelope_api = EnvelopesApi(api_client)
            results = envelope_api.list_documents(
                account_id=cls.account_id,
                envelope_id=envelope_id
            )
            print(results)
            return results
        except Exception as err:
            print("inside get list documents")
            # if err.get('body') and cls.get_error_response_body(err)['errorCode'] == 'USER_AUTHENTICATION_FAILED':
            #     print("inside exception USER_AUTHENTICATION_FAILED")
            print(type(err))
            print(err)

    @classmethod
    def get_document_tabs(cls, envelope_id, document_id):
        """
        """
        api_client = DSClient.get_api_client()

        envelope_api = EnvelopesApi(api_client)
        results = envelope_api.get_document_tabs(
            account_id=cls.account_id,
            envelope_id=envelope_id,
            document_id=document_id
        )
        print(results)
        return results

    @classmethod
    def recreate_recepient_view(cls, envelope_id, args):
        """
        1. Create the envelope request object
        2. Send the envelope
        3. Create the Recipient View request object
        4. Obtain the recipient_view_url for the embedded signing
        """
        envelope_args = args["envelope_args"]
        # 1. Create the envelope request object

        # 2. call Envelopes::create API method
        # Exceptions will be caught by the calling function
        api_client = DSClient.get_api_client()

        envelope_api = EnvelopesApi(api_client)

        # 3. Create the Recipient View request object
        recipient_view_request = cls.create_recipient_view_request(envelope_args)
        # 4. Obtain the recipient_view_url for the embedded signing
        # Exceptions will be caught by the calling function
        results = cls.create_recipient_view(envelope_api, envelope_id, recipient_view_request)
        return {"envelope_id": envelope_id, "redirect_url": results.url}

    @classmethod
    def worker(cls, args):
        """
        1. Create the envelope request object
        2. Send the envelope
        3. Create the Recipient View request object
        4. Obtain the recipient_view_url for the embedded signing
        """
        envelope_args = args["envelope_args"]
        # 1. Create the envelope request object
        envelope_definition = cls.make_envelope(envelope_args)

        # 2. call Envelopes::create API method
        # Exceptions will be caught by the calling function
        api_client = DSClient.get_api_client()

        envelope_api = EnvelopesApi(api_client)
        results = cls.create_envelope(envelope_api, envelope_definition)

        envelope_id = results.envelope_id
        envelope_uri = results.uri

        # 3. Create the Recipient View request object
        recipient_view_request = cls.create_recipient_view_request(envelope_args)
        # 4. Obtain the recipient_view_url for the embedded signing
        # Exceptions will be caught by the calling function
        results = cls.create_recipient_view(envelope_api, envelope_id, recipient_view_request)
        return {"envelope_id": envelope_id, "redirect_url": results.url, 'envelope_uri': envelope_uri}

    @classmethod
    def worker_envelope_id(cls, document_list, tabs, args):
        """
        1. Get envelop id
        2. Send the envelope
        3. Create the Recipient View request object
        4. Obtain the recipient_view_url for the embedded signing
        """
        try:
            envelope_args = args["envelope_args"]
            # 1. Create the envelope request object
            envelope_definition = cls.make_envelope_from_envelope_id(document_list, tabs, envelope_args)

            # 2. call Envelopes::create API method
            # Exceptions will be caught by the calling function
            # api_client = create_api_client(base_path=args["base_path"], access_token=args["access_token"])
            api_client = DSClient.get_api_client()
            envelope_api = EnvelopesApi(api_client)
            results = cls.create_envelope(envelope_api, envelope_definition)
            print(f' in line 277 {results}')
            envelope_id = results.envelope_id
            envelope_uri = results.uri

            # 3. Create the Recipient View request object
            recipient_view_request = cls.create_recipient_view_request(envelope_args)
            # 4. Obtain the recipient_view_url for the embedded signing
            # Exceptions will be caught by the calling function
            results = cls.create_recipient_view(envelope_api, envelope_id, recipient_view_request)
            return {"envelope_id": envelope_id, "redirect_url": results.url, 'envelope_uri': envelope_uri}
        except Exception as ex:
            print("inside worker using id")
            print(ex)

    @classmethod
    def get_document_list_from_envelope_id_with_tabs(cls, envelope_id):
        document_list = []
        tabs = []
        envelope_documents_list = cls.get_list_of_documents(envelope_id)
        for envelope_document in envelope_documents_list.envelope_documents:
            if envelope_document.type == 'content':
                response = cls.get_document_file(envelope_id, envelope_document.document_id)
                with open(response, "rb") as file:
                    content_bytes = file.read()
                base64_file_content = base64.b64encode(content_bytes).decode("ascii")
                document = Document(  # create the DocuSign document object
                    document_base64=base64_file_content,
                    name=envelope_document.name,  # can be different from actual file name
                    file_extension=pathlib.Path(response).suffix,  # many different document types are accepted
                    document_id=envelope_document.document_id  # a label used to reference the doc
                )
                document_list.append(document)
                tabs = cls.get_document_tabs(envelope_id, envelope_document.document_id)
        return document_list, tabs

    @classmethod
    def make_envelope_from_envelope_id(cls, document_list, tabs, args):
        """
        Creates envelope
        args -- parameters for the envelope:
        signer_email, signer_name, signer_client_id
        returns an envelope definition
        """

        # document 1 (pdf) has tag /sn1/
        #
        # The envelope has one recipient.
        # recipient 1 - signer
        # Create the signer recipient model
        try:

            signer = Signer(
                # The signer
                email=args["signer_email"],
                name=args["signer_name"],
                recipient_id="1",
                routing_order="1",
                # Setting the client_user_id marks the signer as embedded
                client_user_id=args["signer_client_id"]
            )

            # document_list = cls.get_list_of_documents(envelope_id)
            signer.tabs = tabs

            # Add the tabs model (including the sign_here tab) to the signer
            # The Tabs object wants arrays of the different field/tab types
            # signer.tabs = Tabs(sign_here_tabs=[sign_here])

            # Next, create the top level envelope definition and populate it.
            envelope_definition = EnvelopeDefinition(
                email_subject="Please sign this document sent from the Python SDK from envelope id",
                documents=document_list,
                # The Recipients object wants arrays for each recipient type
                recipients=Recipients(signers=[signer]),
                status="sent"  # requests that the envelope be created and sent.
            )
            return envelope_definition
        except Exception as ex:
            print("inside make envelope using id")
            print(ex)

    @classmethod
    def make_envelope(cls, args):
        """
        Creates envelope
        args -- parameters for the envelope:
        signer_email, signer_name, signer_client_id
        returns an envelope definition
        """

        # document 1 (pdf) has tag /sn1/
        #
        # The envelope has one recipient.
        # recipient 1 - signer
        filepath = staticfiles_storage.path('demo_documents/' + conf_settings.DS_CONFIG["doc_pdf"])
        with open(filepath, "rb") as file:
            content_bytes = file.read()
        base64_file_content = base64.b64encode(content_bytes).decode("ascii")

        # Create the document model
        document = Document(  # create the DocuSign document object
            document_base64=base64_file_content,
            name="Example document",  # can be different from actual file name
            file_extension="pdf",  # many different document types are accepted
            document_id=1  # a label used to reference the doc
        )

        # Create the signer recipient model
        signer = Signer(
            # The signer
            email=args["signer_email"],
            name=args["signer_name"],
            recipient_id="1",
            routing_order="1",
            # Setting the client_user_id marks the signer as embedded
            client_user_id=args["signer_client_id"]
        )

        # Create a sign_here tab (field on the document)
        sign_here = SignHere(
            # DocuSign SignHere field/tab
            anchor_string="/sn1/",
            anchor_units="pixels",
            anchor_y_offset="10",
            anchor_x_offset="20"
        )

        # Add the tabs model (including the sign_here tab) to the signer
        # The Tabs object wants arrays of the different field/tab types
        signer.tabs = Tabs(sign_here_tabs=[sign_here])

        # Next, create the top level envelope definition and populate it.
        envelope_definition = EnvelopeDefinition(
            email_subject="Please sign this document sent from the Python SDK",
            documents=[document],
            # The Recipients object wants arrays for each recipient type
            recipients=Recipients(signers=[signer]),
            status="sent"  # requests that the envelope be created and sent.
        )

        return envelope_definition

