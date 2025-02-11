'''View Functions for Field app'''
import asyncio
import os
import pathlib
from asyncio import Semaphore, ensure_future
from dataclasses import field
import warnings
from django import forms
import pandas as pd
from apps.field.field_column import FieldColoumChoices
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.db.utils import IntegrityError
from django.db.models import Q, Count
import re, csv
from apps.field.models import CsvToField, ShapeFileDataCo, Crop, CropType, CropVariety
# from apps.grower.models import Grower
from apps.farms.models import Farm
from apps.contracts.models import Contracts, SignedContracts, ContractsVerifiers, VerifiedSignedContracts, \
    GrowerContracts
from apps.grower.models import Consultant, Grower
from . import forms
import shapefile
from django.http import JsonResponse
import json
import requests
import datetime
import time
from datetime import date, timedelta, datetime
from django.utils.dateformat import DateFormat
from django.utils.formats import get_format
from urllib.parse import urlparse
from django.utils.http import urlencode
import geojson
import numpy as np
import geopandas as gpd
from apps.grower.signals import send_contract_verification_email
from apps.growersurvey.views import render_to_pdf
from docusign_esign import EnvelopesApi
from django.views.generic.base import RedirectView
from django.conf import settings as conf_settings
from django.urls import reverse
from django.contrib.staticfiles.storage import staticfiles_storage
import base64
from docusign_esign.client.api_client import ApiException
from docusign_esign import EnvelopesApi, RecipientViewRequest, Document, Signer, EnvelopeDefinition, SignHere, Tabs, \
    Recipients
from apps.docusign.utils import create_api_client
from apps.docusign.consts import authentication_method, demo_docs_path, pattern, signer_client_id
from apps.accounts.models import User, Role, SubSuperUser, ShowNotification
from apps.contracts.DocusignEmbedded import DocusignEmbeddedSigningController
import requests
import threading
from asgiref.sync import sync_to_async, async_to_sync
from apps.contracts.tasks import create_envelope_and_store
from django.contrib.auth.decorators import login_required
from apps.processor.models import Processor, ProcessorUser
from apps.processor2.models import Processor2, ProcessorUser2
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from apps.contracts.models import *
from django.db.models import Prefetch
from apps.warehouseManagement.models import Customer, CustomerUser, Distributor, DistributorUser, Warehouse, WarehouseUser
from django.db import transaction
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET


warnings.simplefilter(action='ignore', category=FutureWarning)


# pylint: disable=no-member,expression-not-assigned, too-many-locals, too-many-ancestors, too-many-ancestors, bare-except


# class Eg001EmbeddedSigningController:
#     base_path = 'https://demo.docusign.net/restapi/'
#     account_id = 'ff270191-6865-46c0-b877-612897b757f8'
#     access_token = os.getenv('DOCUSIGN_ACCESS_TOKEN',
#                              'eyJ0eXAiOiJNVCIsImFsZyI6IlJTMjU2Iiwia2lkIjoiNjgxODVmZjEtNGU1MS00Y2U5LWFmMWMtNjg5ODEyMjAzMzE3In0.AQsAAAABAAUABwCA2cMeDGHaSAgAgBnnLE9h2kgCAP-kGvOW52dIntbCAV0jZ5wVAAEAAAAYAAEAAAAFAAAADQAkAAAANzQ4YzUyNzktOTc5NS00YjM5LWJkMTktNGRmNmI5OWU3ODRiIgAkAAAANzQ4YzUyNzktOTc5NS00YjM5LWJkMTktNGRmNmI5OWU3ODRiEgABAAAACwAAAGludGVyYWN0aXZlMAAAV8r8C2HaSDcA-1dAj9iZOE-7cToSPBcQGQ.pKBWrpfW8c7FqyEN4_kOpUvsE5N3Ew0FB-oP0L06KlEXDNqYWH_OlEmOhO_knU1GXZyKrpD1FsbJAnwhFCLmdEDBjwmQMp1qr3cgQb-5-7XaJ_rT2YFzuPeqWux0Pw4DN8x7zxSHuIgeo7a-JZmyPnW-KWm1pnt0qpZWhe1wHnGXnGzyu_KBgh5TNmC-J8WPNJNKaDzsoEqxCYdCNfwTI8AkzqdfGRGXn_DweKNNZ7bfgxiRMAIuJ2pdKM9s5-chFKO3_D8uDYoaoFk9vR93efbyZYb4Hl8qhDMt5aCqvbX2rN3uDPDknSv7wTJKx2E6VRCiAKH8fKNxyDZOQz04ug')
#     refresh_token = os.getenv('DOCUSIGN_REFRESH_TOKEN',
#                               'eyJ0eXAiOiJNVCIsImFsZyI6IlJTMjU2Iiwia2lkIjoiNjgxODVmZjEtNGU1MS00Y2U5LWFmMWMtNjg5ODEyMjAzMzE3In0.AQoAAAABAAgABwCA2cMeDGHaSAgAgFkoF5942kgCAP-kGvOW52dIntbCAV0jZ5wVAAEAAAAYAAEAAAAFAAAADQAkAAAANzQ4YzUyNzktOTc5NS00YjM5LWJkMTktNGRmNmI5OWU3ODRiIgAkAAAANzQ4YzUyNzktOTc5NS00YjM5LWJkMTktNGRmNmI5OWU3ODRiMAAAV8r8C2HaSDcA-1dAj9iZOE-7cToSPBcQGQ.G0iVE6LQiig_mpUHqkFiy1IDVV7FdJs2qPIPn0vWZSqN-Et8_64H4z5tFRW4PPpvYAdVX7FqToNrkcsYU3VI19v8XRPhRRakQImxqBVVsNtDriBDmVk07Y8N_ukzFXYYRxu0_dC6k9bzOK6J1jEq9ga-rKRMFCSpCjKkPPlF89MWE4L6EVI00D6NUbMioSJ_EpcjQ7Fao1O1uCFI548qVMuj0PfV1gxmeIZMvXDPdXZzdbF_vrSNDAm_zuADxtsWKuKbu-TGB4WmmOQeQbpbY1cIiduBrM4CwismPccD7mYep0VAVkHh9R5KqPnm-7RGqj28HPipT8bRr0KTNQZnow')
#     client_id = '748c5279-9795-4b39-bd19-4df6b99e784b'
#     redirect_uri = 'https://www.example.com/callback'
#
#     def __init__(self):
#         self.account_id = 'ff270191-6865-46c0-b877-612897b757f8'
#         self.base_path = 'https://demo.docusign.net/restapi/'
#
#     @classmethod
#     def get_args(cls, signer_email, signer_name, signer_client_id, session, contract, grower, request):
#         """Get request and session arguments"""
#         # More data validation would be a good idea here
#         # Strip anything other than characters listed
#         # 1. Parse request arguments
#         # signer_email = signer_email
#         # signer_name = signer_name
#         envelope_args = {
#             "signer_email": signer_email,
#             "signer_name": signer_name,
#             "signer_client_id": signer_client_id,
#             "ds_return_url": request.build_absolute_uri(
#                 reverse('docusign-contract-submit', kwargs={'contract_id': contract.id, 'grower_id': grower.id})),
#         }
#         args = {
#             "account_id": cls.account_id,
#             "base_path": cls.base_path,
#             "access_token": cls.access_token,
#             "envelope_args": envelope_args
#         }
#         return args
#
#     @classmethod
#     def create_envelope(cls, envelope_api, envelope_definition):
#         """
#         """
#         results = envelope_api.create_envelope(account_id=cls.account_id, envelope_definition=envelope_definition)
#         print(results)
#         return results
#
#     @classmethod
#     def create_recipient_view_request(cls, envelope_args):
#         """
#         """
#         recipient_view_request = RecipientViewRequest(
#             authentication_method=authentication_method,
#             client_user_id=envelope_args["signer_client_id"],
#             recipient_id="1",
#             return_url=envelope_args["ds_return_url"],
#             user_name=envelope_args["signer_name"],
#             email=envelope_args["signer_email"]
#         )
#         print(recipient_view_request)
#         return recipient_view_request
#
#     @classmethod
#     def create_recipient_view(cls, envelope_api, envelope_id, recipient_view_request):
#         """
#         """
#         results = envelope_api.create_recipient_view(
#             account_id=cls.account_id,
#             envelope_id=envelope_id,
#             recipient_view_request=recipient_view_request
#         )
#         print(results)
#         return results
#
#     @classmethod
#     def create_sender_view(cls, envelope_id, return_url):
#         """
#         """
#         api_client = create_api_client(base_path=cls.base_path, access_token=cls.access_token)
#         envelope_api = EnvelopesApi(api_client)
#         results = envelope_api.create_sender_view(
#             account_id=cls.account_id,
#             envelope_id=envelope_id,
#             return_url_request=return_url
#         )
#         print(results)
#         return results
#
#     @classmethod
#     def get_envelope(cls, envelope_id):
#         """
#         """
#         api_client = create_api_client(base_path=cls.base_path, access_token=cls.access_token)
#
#         envelope_api = EnvelopesApi(api_client)
#         results = envelope_api.get_envelope(
#             account_id=cls.account_id,
#             envelope_id=envelope_id
#         )
#         print(results)
#         return results
#
#     @classmethod
#     def get_document_file(cls, envelope_id, document_id):
#         """
#         """
#         api_client = create_api_client(base_path=cls.base_path, access_token=cls.access_token)
#
#         envelope_api = EnvelopesApi(api_client)
#         results = envelope_api.get_document(
#             account_id=cls.account_id,
#             envelope_id=envelope_id,
#             document_id=document_id
#         )
#         print(results)
#         return results
#
#     @staticmethod
#     def get_error_response_body(res):
#         error_body_json = res and hasattr(res, "body") and res.body
#         # we can pull the DocuSign error code and message from the response body
#         try:
#             error_body = json.loads(error_body_json)
#         except json.decoder.JSONDecodeError:
#             error_body = {}
#         return error_body
#
#     def get_auth_token(self, code):
#         url = "https://account-d.docusign.com/oauth/token"
#
#         # payload = f'code={code}&grant_type=authorization_code'
#         payload = f'grant_type=refresh_token&refresh_token={os.getenv("DOCUSIGN_REFRESH_TOKEN")}'
#         iKeyiSec = "748c5279-9795-4b39-bd19-4df6b99e784b:ec4e772b-6334-404d-b931-39cca6cd5be3"
#         b64Val = base64.b64encode(iKeyiSec.encode())
#         headers = {
#             'Authorization': f'Basic {b64Val}',
#             'Content-Type': 'application/x-www-form-urlencoded'
#         }
#         response = requests.request("POST", url, headers=headers, data=payload)
#         data = response.json()
#         print(data)
#         access_token = data['access_token']
#         token_type = data['token_type']
#         refresh_token = data['refresh_token']
#         os.environ['DOCUSIGN_ACCESS_TOKEN'] = access_token
#         os.environ['DOCUSIGN_REFRESH_TOKEN'] = refresh_token
#
#     @classmethod
#     def get_code_from_url(cls, request):
#         print(request.build_absolute_uri(reverse('contract-list')))
#         url = f"https://account-d.docusign.com/oauth/auth?response_type=code&scope=signature&client_id={cls.client_id}&redirect_uri={request.build_absolute_uri(reverse('contract-list'))}"
#         response = requests.request("GET", url)
#         print(f'inside code from url {response}')
#         for i in response.history:
#             print(i.url)
#
#     @classmethod
#     def get_list_of_documents(cls, envelope_id, request):
#         """
#         """
#         try:
#             api_client = create_api_client(base_path=cls.base_path, access_token=cls.access_token)
#
#             envelope_api = EnvelopesApi(api_client)
#             results = envelope_api.list_documents(
#                 account_id=cls.account_id,
#                 envelope_id=envelope_id
#             )
#             print(results)
#             return results
#         except Exception as err:
#             print("inside get list documents")
#             if err.body and cls.get_error_response_body(err)['errorCode'] == 'USER_AUTHENTICATION_FAILED':
#                 print("inside exception USER_AUTHENTICATION_FAILED")
#             print(type(err))
#             print(err)
#
#     @classmethod
#     def get_document_tabs(cls, envelope_id, document_id):
#         """
#         """
#         api_client = create_api_client(base_path=cls.base_path, access_token=cls.access_token)
#
#         envelope_api = EnvelopesApi(api_client)
#         results = envelope_api.get_document_tabs(
#             account_id=cls.account_id,
#             envelope_id=envelope_id,
#             document_id=document_id
#         )
#         print(results)
#         return results
#
#     @classmethod
#     def recreate_recepient_view(cls, envelope_id, args):
#         """
#         1. Create the envelope request object
#         2. Send the envelope
#         3. Create the Recipient View request object
#         4. Obtain the recipient_view_url for the embedded signing
#         """
#         envelope_args = args["envelope_args"]
#         # 1. Create the envelope request object
#
#         # 2. call Envelopes::create API method
#         # Exceptions will be caught by the calling function
#         api_client = create_api_client(base_path=args["base_path"], access_token=args["access_token"])
#
#         envelope_api = EnvelopesApi(api_client)
#
#         # 3. Create the Recipient View request object
#         recipient_view_request = cls.create_recipient_view_request(envelope_args)
#         # 4. Obtain the recipient_view_url for the embedded signing
#         # Exceptions will be caught by the calling function
#         results = cls.create_recipient_view(envelope_api, envelope_id, recipient_view_request)
#         return {"envelope_id": envelope_id, "redirect_url": results.url}
#
#     @classmethod
#     def worker(cls, args):
#         """
#         1. Create the envelope request object
#         2. Send the envelope
#         3. Create the Recipient View request object
#         4. Obtain the recipient_view_url for the embedded signing
#         """
#         envelope_args = args["envelope_args"]
#         # 1. Create the envelope request object
#         envelope_definition = cls.make_envelope(envelope_args)
#
#         # 2. call Envelopes::create API method
#         # Exceptions will be caught by the calling function
#         api_client = create_api_client(base_path=args["base_path"], access_token=args["access_token"])
#
#         envelope_api = EnvelopesApi(api_client)
#         results = cls.create_envelope(envelope_api, envelope_definition)
#
#         envelope_id = results.envelope_id
#         envelope_uri = results.uri
#
#         # 3. Create the Recipient View request object
#         recipient_view_request = cls.create_recipient_view_request(envelope_args)
#         # 4. Obtain the recipient_view_url for the embedded signing
#         # Exceptions will be caught by the calling function
#         results = cls.create_recipient_view(envelope_api, envelope_id, recipient_view_request)
#         return {"envelope_id": envelope_id, "redirect_url": results.url, 'envelope_uri': envelope_uri}
#
#     @classmethod
#     def worker_envelope_id(cls, envelope_id, request, args):
#         """
#         1. Get envelop id
#         2. Send the envelope
#         3. Create the Recipient View request object
#         4. Obtain the recipient_view_url for the embedded signing
#         """
#         try:
#             envelope_args = args["envelope_args"]
#             # 1. Create the envelope request object
#             envelope_definition = cls.make_envelope_from_envelope_id(envelope_id, envelope_args, request)
#
#             # 2. call Envelopes::create API method
#             # Exceptions will be caught by the calling function
#             api_client = create_api_client(base_path=args["base_path"], access_token=args["access_token"])
#
#             envelope_api = EnvelopesApi(api_client)
#             results = cls.create_envelope(envelope_api, envelope_definition)
#
#             envelope_id = results.envelope_id
#             envelope_uri = results.uri
#
#             # 3. Create the Recipient View request object
#             recipient_view_request = cls.create_recipient_view_request(envelope_args)
#             # 4. Obtain the recipient_view_url for the embedded signing
#             # Exceptions will be caught by the calling function
#             results = cls.create_recipient_view(envelope_api, envelope_id, recipient_view_request)
#             return {"envelope_id": envelope_id, "redirect_url": results.url, 'envelope_uri': envelope_uri}
#         except Exception as ex:
#             print("inside worker using id")
#             print(ex)
#
#     @classmethod
#     def make_envelope_from_envelope_id(cls, envelope_id, args, request):
#         """
#         Creates envelope
#         args -- parameters for the envelope:
#         signer_email, signer_name, signer_client_id
#         returns an envelope definition
#         """
#
#         # document 1 (pdf) has tag /sn1/
#         #
#         # The envelope has one recipient.
#         # recipient 1 - signer
#         # Create the signer recipient model
#         try:
#
#             signer = Signer(
#                 # The signer
#                 email=args["signer_email"],
#                 name=args["signer_name"],
#                 recipient_id="1",
#                 routing_order="1",
#                 # Setting the client_user_id marks the signer as embedded
#                 client_user_id=args["signer_client_id"]
#             )
#
#             # document_list = cls.get_list_of_documents(envelope_id)
#             document_list = []
#             envelope_documents_list = cls.get_list_of_documents(envelope_id, request)
#             for envelope_document in envelope_documents_list.envelope_documents:
#                 if envelope_document.type == 'content':
#                     response = cls.get_document_file(envelope_id, envelope_document.document_id)
#                     with open(response, "rb") as file:
#                         content_bytes = file.read()
#                     base64_file_content = base64.b64encode(content_bytes).decode("ascii")
#                     document = Document(  # create the DocuSign document object
#                         document_base64=base64_file_content,
#                         name=envelope_document.name,  # can be different from actual file name
#                         file_extension=pathlib.Path(response).suffix,  # many different document types are accepted
#                         document_id=envelope_document.document_id  # a label used to reference the doc
#                     )
#                     document_list.append(document)
#                     signer.tabs = cls.get_document_tabs(envelope_id, envelope_document.document_id)
#
#             # Add the tabs model (including the sign_here tab) to the signer
#             # The Tabs object wants arrays of the different field/tab types
#             # signer.tabs = Tabs(sign_here_tabs=[sign_here])
#
#             # Next, create the top level envelope definition and populate it.
#             envelope_definition = EnvelopeDefinition(
#                 email_subject="Please sign this document sent from the Python SDK from envelope id",
#                 documents=document_list,
#                 # The Recipients object wants arrays for each recipient type
#                 recipients=Recipients(signers=[signer]),
#                 status="sent"  # requests that the envelope be created and sent.
#             )
#             return envelope_definition
#         except Exception as ex:
#             print("inside make envelope using id")
#             print(ex)
#
#     @classmethod
#     def make_envelope(cls, args):
#         """
#         Creates envelope
#         args -- parameters for the envelope:
#         signer_email, signer_name, signer_client_id
#         returns an envelope definition
#         """
#
#         # document 1 (pdf) has tag /sn1/
#         #
#         # The envelope has one recipient.
#         # recipient 1 - signer
#         filepath = staticfiles_storage.path('demo_documents/' + conf_settings.DS_CONFIG["doc_pdf"])
#         with open(filepath, "rb") as file:
#             content_bytes = file.read()
#         base64_file_content = base64.b64encode(content_bytes).decode("ascii")
#
#         # Create the document model
#         document = Document(  # create the DocuSign document object
#             document_base64=base64_file_content,
#             name="Example document",  # can be different from actual file name
#             file_extension="pdf",  # many different document types are accepted
#             document_id=1  # a label used to reference the doc
#         )
#
#         # Create the signer recipient model
#         signer = Signer(
#             # The signer
#             email=args["signer_email"],
#             name=args["signer_name"],
#             recipient_id="1",
#             routing_order="1",
#             # Setting the client_user_id marks the signer as embedded
#             client_user_id=args["signer_client_id"]
#         )
#
#         # Create a sign_here tab (field on the document)
#         sign_here = SignHere(
#             # DocuSign SignHere field/tab
#             anchor_string="/sn1/",
#             anchor_units="pixels",
#             anchor_y_offset="10",
#             anchor_x_offset="20"
#         )
#
#         # Add the tabs model (including the sign_here tab) to the signer
#         # The Tabs object wants arrays of the different field/tab types
#         signer.tabs = Tabs(sign_here_tabs=[sign_here])
#
#         # Next, create the top level envelope definition and populate it.
#         envelope_definition = EnvelopeDefinition(
#             email_subject="Please sign this document sent from the Python SDK",
#             documents=[document],
#             # The Recipients object wants arrays for each recipient type
#             recipients=Recipients(signers=[signer]),
#             status="sent"  # requests that the envelope be created and sent.
#         )
#
#         return envelope_definition


class UpdateDocumentSignedView(LoginRequiredMixin, RedirectView):
    '''Generic Class Based view to list all the field objects in database'''
    permanent = False
    query_string = True
    url = None

    def get_redirect_url(self, *args, **kwargs):
        url_parameters = re.findall(r'\d+', self.request.get_full_path())
        grower_contract = GrowerContracts.objects.get(contract_id=url_parameters[0], grower_id=url_parameters[1])

        if "ttl_expired" == self.request.GET.get("event"):
            embedded = DocusignEmbeddedSigningController()
            args = embedded.get_args(grower_contract.grower.email, grower_contract.grower.name,
                                     grower_contract.grower.id,
                                     self.request.session, grower_contract.contract, grower_contract.grower,
                                     self.request)
            self.request.META["QUERY_STRING"] = None
            self.url = embedded.recreate_recepient_view(grower_contract.envelope_id, args)["redirect_url"]
            parsed_uri = urlparse(self.url)
            self.request.META["PATH_INFO"] = parsed_uri.path
            self.request.META["HTTP_HOST"] = parsed_uri.netloc
        if "signing_complete" == self.request.GET.get("event"):
            grower_contract.is_signed = True
            grower_contract.save()
            self.request.META["QUERY_STRING"] = None
            self.url = reverse('contract-list')
        return super().get_redirect_url(*args, **kwargs)


class DocusignCallbackUrlForAuth(LoginRequiredMixin, ListView):
    """Generic Class Based view to list all the field objects in database"""

    def get_redirect_field_name(self):
        if self.request.GET.get("code"):
            print(self.request.GET.get("code"))
            url = "https://account-d.docusign.com/oauth/token"

            payload = f'code={self.request.GET.get("code")}&grant_type=authorization_code'
            iKeyiSec = "748c5279-9795-4b39-bd19-4df6b99e784b:ec4e772b-6334-404d-b931-39cca6cd5be3"
            b64Val = base64.b64encode(iKeyiSec.encode())
            headers = {
                'Authorization': f'Basic {b64Val}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            data = response.json()
            access_token = data['access_token']
            token_type = data['token_type']
            refresh_token = data['refresh_token']
            os.environ['DOCUSIGN_ACCESS_TOKEN'] = access_token


class ContractsListView(LoginRequiredMixin, ListView):
    """Generic Class Based view to list all the field objects in database"""
    model = Contracts
    context_object_name = 'Contracts'
    template_name = 'contracts/contracts_list.html'

    def get_queryset(self):
        if self.request.user.grower:
            grower_contracts = GrowerContracts.objects.filter(grower_id=self.request.user.grower.id).order_by(
                '-modified_date')
            data = [
                {'name': grower_contract.contract.name, 'signed_contract_count': 0, 'url': grower_contract.contract_url,
                 'is_signed': grower_contract.is_signed} for grower_contract in grower_contracts]
        else:
            contracts = Contracts.objects.all().order_by('-modified_date')
            data = [{'name': contract.name,
                     'signed_contract_count': GrowerContracts.objects.filter(contract=contract, is_signed=True).count(),
                     'envelope_id': contract.envelope_id} for contract in contracts]
        return data


def create_grower_save(contract, grower, results, created_by):
    grower_contract = GrowerContracts.objects.create(contract=contract,
                                                     contract_url=results['url'],
                                                     grower=grower,
                                                     created_by=created_by,
                                                     envelope_id=results['envelope_id']
                                                     )
    print(grower_contract)
    grower_contract.save()


async def get_envelope_results(grower, contract, request):
    try:
        args = DocusignEmbeddedSigningController.get_args(grower.email, grower.name,
                                                          grower.id, request.session, contract,
                                                          grower, request)
        results = DocusignEmbeddedSigningController.worker_envelope_id(contract.envelope_id, request, args)
        # await create_grower_save(contract, grower, results, request.user)
        grower_contract = GrowerContracts.objects.create(contract=contract,
                                                         contract_url=results['url'],
                                                         grower=grower,
                                                         created_by=request.user,
                                                         envelope_id=results['envelope_id']
                                                         )
        print(grower_contract)
        sync_to_async(grower_contract.save, thread_sensitive=True)
    except Exception as err:
        return print(err)


async def create_grower_contracts(growers, contract, request):
    for grower in growers:
        asyncio.ensure_future(get_envelope_results(grower, contract, request))  # fire and forget async_foo()


def loop_in_thread(loop, growers, contract, request):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(create_grower_contracts(growers, contract, request))


def get_envelope_id_and_save_in_db(grower, contract, request, document_list, tabs):
    try:
        args = DocusignEmbeddedSigningController.get_args(grower.email, grower.name,
                                                          grower.id, request.session, contract,
                                                          grower, request)
        results = DocusignEmbeddedSigningController.worker_envelope_id(document_list, tabs, args)
        grower_contract = GrowerContracts.objects.create(contract=contract,
                                                         contract_url=results['redirect_url'],
                                                         grower=grower,
                                                         created_by=request.user,
                                                         envelope_id=results['envelope_id']
                                                         )
        grower_contract.save()
    except Exception as err:
        return print(err)


class ContractsCreateView(LoginRequiredMixin, CreateView):
    """Generic Class Based view to create a new field"""
    model = Contracts
    # fields = "__all__"
    form_class = forms.ContractCreateForm
    template_name = 'contracts/contract_create.html'
    success_url = reverse_lazy('contract-list')

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new Field"""
        form.instance.created_by = self.request.user
        contract = form.save()


        # try:
        #     loop = asyncio.get_running_loop()
        #
        # except RuntimeError:  # 'RuntimeError: There is no current event loop...'
        #     loop = asyncio.new_event_loop()
        #
        # t = threading.Thread(target=loop_in_thread, args=(loop, growers[:10], contract, self.request))
        # t.start()
        # try:
        #     embedded = DocusignEmbeddedSigningController()
        #     document_list, tabs = embedded.get_document_list_from_envelope_id_with_tabs(contract.envelope_id)
        # except Exception as err:
        #     return print(err)
        return_url = self.request.build_absolute_uri(
            reverse('docusign-contract-submit', kwargs={'contract_id': contract.id, 'grower_id': contract.id}))

        create_envelope_and_store.delay(contract.id, self.request.user.username, return_url)
        # for grower in growers: sync_to_async(get_envelope_id_and_save_in_db, thread_sensitive=True)(grower,
        # contract, self.request, document_list, tabs)
        messages.success(self.request, f'Contract Created Successfully!')
        return super(ContractsCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ContractsCreateView, self).get_context_data(**kwargs)
        context["is_create"] = True
        return context


class ContractsUpdateView(LoginRequiredMixin, UpdateView):
    model = Contracts
    # fields = "__all__"
    form_class = forms.ContractCreateForm
    template_name = 'contracts/contract_create.html'
    success_url = reverse_lazy('contract-list')

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new Field"""
        form.instance.created_by = self.request.user
        form.save()
        messages.success(self.request, f'Contract Updated Successfully!')
        return super(ContractsUpdateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ContractsUpdateView, self).get_context_data(**kwargs)
        context["is_create"] = False
        return context


class SignedContractsListView(LoginRequiredMixin, ListView):
    '''Generic Class Based view to list all the field objects in database'''
    model = SignedContracts
    template_name = 'contracts/signed_contracts_list.html'

    def get_queryset(self):
        """overriding the queryset to return all the fields in the database when a superuser is logged in,
        and to get only the fields mapped to the logged in user's grower"""
        if 'Grower' in self.request.user.get_role() and not self.request.user.is_superuser:
            # do something grower
            # SustainabilitySurvey_data = SustainabilitySurvey.objects.filter(grower_id=request.user.grower.id)
            return self.model.objects.filter(grower_id=self.request.user.grower.id).order_by('-created_date')
            # return self.model.objects.all().order_by('-created_date')
        else:
            if self.request.user.is_consultant:
                # do something consultant
                consultant_id = Consultant.objects.get(email=self.request.user.email).id
                get_growers = Grower.objects.filter(consultant=consultant_id)
                grower_ids = [data.id for data in get_growers]
                grower_data = Grower.objects.filter(id__in=grower_ids)
                return self.model.objects.filter(grower__in=grower_data).order_by('-created_date')
            else:
                # do something allpower
                return self.model.objects.all().order_by('-created_date')


class ContractDetailView(LoginRequiredMixin, DetailView):
    """Generic Class Based View for user detail page"""
    model = Contracts
    template_name = 'contracts/contracts_detail.html'

    def get_context_data(self, **kwargs):
        context = super(ContractDetailView, self).get_context_data(**kwargs)
        is_signed = False
        signature = ""
        signatures = []
        if self.request.user.grower:
            singed_data = SignedContracts.objects.filter(
                contract_id=self.kwargs.get('pk'),
                grower_id=self.request.user.grower.id
            ).last()
            if singed_data:
                is_signed = True
                signature = singed_data.signature
        else:
            signatures = SignedContracts.objects.filter(
                contract_id=self.kwargs.get('pk'),
            ).values("signature", "grower__name")
            if signatures:
                is_signed = True
        context["is_signed"] = is_signed
        context["signature"] = signature
        context["signatures"] = signatures
        return context


class ContractsSignSaveView(LoginRequiredMixin, CreateView):
    @classmethod
    def post(cls, request):
        '''Default function for get request'''
        signature = request.POST.get('signature')
        grower_id = request.POST.get('grower_id')
        contract_id = request.POST.get('contract_id')

        # Adding signature to contracts
        signed_contract = SignedContracts.objects.create(
            signature=signature,
            contract_id=contract_id,
            grower_id=grower_id,
            created_by=request.user
        )

        # Updating Contracts is_signed Status
        Contracts.objects.filter(
            id=contract_id
        ).update(
            is_signed=True
        )

        # Sending Email to Verifiers
        verifiers = ContractsVerifiers.objects.filter(
            contract_id=contract_id
        )
        for verifier in verifiers:
            verified_signer = VerifiedSignedContracts.objects.create(
                name=verifier.name,
                email=verifier.email,
                signature="",
                signed_contracts=signed_contract,
                is_verified=False,
            )
            contract_verification_link = "http://traceableoutcomes.tech/contracts/signed/" + str(
                verified_signer.id) + "/details/"
            # Send Email Invite
            send_contract_verification_email(
                verifier,
                [verifier.email],
                request.user.grower.name,
                contract_verification_link
            )

        messages.success(request, f'Signed Contract Successfully!')
        return HttpResponseRedirect('/contracts/list/')


class SignedContractDetailView(DetailView):
    """Generic Class Based View for user detail page"""
    model = VerifiedSignedContracts
    template_name = 'contracts/signed_contract_details.html'

    def get_context_data(self, **kwargs):
        context = super(SignedContractDetailView, self).get_context_data(**kwargs)
        return context


class ContractsSignVerificationSaveView(CreateView):
    @classmethod
    def post(cls, request):
        '''Default function for get request'''
        signature = request.POST.get('signature')
        pk = request.POST.get('pk')

        # Adding signature to contracts
        VerifiedSignedContracts.objects.filter(
            id=pk
        ).update(
            signature=signature,
            is_verified=True
        )
        messages.success(request, f'Verification Successful!')
        return HttpResponseRedirect('/contracts/signed/' + str(pk) + '/details/')


class ContractPdfView(LoginRequiredMixin, ListView):
    @classmethod
    def get(cls, request, pk, **kwargs):
        contract_signers = []
        signed_contracts = SignedContracts.objects.get(id=pk)
        contract_title = signed_contracts.contract.name
        contract_details = signed_contracts.contract.contract
        grower_data = {
            "name": signed_contracts.grower.name,
            "signature": signed_contracts.signature,
        }
        contract_signers.append(grower_data)

        verified_contracts = VerifiedSignedContracts.objects.filter(
            signed_contracts=signed_contracts
        ).all()
        for i in verified_contracts:
            data = {
                "name": i.name,
                "signature": i.signature,
            }
            contract_signers.append(data)

        return render_to_pdf(
            'contracts/contract_pdf.html',
            {
                "contract_title": contract_title,
                "contract_details": contract_details,
                "contract_signers": contract_signers,
            }
        )


@require_GET
def get_crop_types(request):
    crop_code = request.GET.get('crop_code')
    if crop_code:        
        crop_types = ShipmentItem.objects.filter(item=crop_code).values("item_type", "per_unit_price")
        return JsonResponse({'crop_types': list(crop_types)})
    return JsonResponse({'crop_types': []})


# @login_required()
# def admin_processor_contract_create(request):
#     context = {}
#     try:
#         if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
#             processor1 = list(Processor.objects.all().values("id", "entity_name"))
#             processor2 = list(Processor2.objects.filter(processor_type__type_name="T2").values("id", "entity_name"))
#             processor3 = list(Processor2.objects.filter(processor_type__type_name="T3").values("id", "entity_name"))
#             processor4 = list(Processor2.objects.filter(processor_type__type_name="T4").values("id", "entity_name"))
#             processor = []
#             crops = ShipmentItem.objects.all()
#             context["crops"] = crops
#             for i in processor1:
#                 my_dict = {"id":None, "entity_name":None, "type":None}
#                 my_dict["id"] = i["id"]
#                 my_dict["entity_name"] = i["entity_name"]
#                 my_dict["type"] = "T1"
#                 processor.append(my_dict)

#             for i in processor2:
#                 my_dict = {"id":None, "entity_name":None, "type":None}
#                 my_dict["id"] = i["id"]
#                 my_dict["entity_name"] = i["entity_name"]
#                 my_dict["type"] = "T2"
#                 processor.append(my_dict)

#             for i in processor3:
#                 my_dict = {"id":None, "entity_name":None, "type":None}
#                 my_dict["id"] = i["id"]
#                 my_dict["entity_name"] = i["entity_name"]
#                 my_dict["type"] = "T3"
#                 processor.append(my_dict)

#             for i in processor4:
#                 my_dict = {"id":None, "entity_name":None, "type":None}
#                 my_dict["id"] = i["id"]
#                 my_dict["entity_name"] = i["entity_name"]
#                 my_dict["type"] = "T4"
#                 processor.append(my_dict)

#             context["processor"] = processor

#             try:
#                 from apps.quickbooks_integration.views import create_item, refresh_quickbooks_token, get_quickbooks_accounts
#                 from apps.quickbooks_integration.models import QuickBooksToken                
#                 token_instance = QuickBooksToken.objects.first()
#                 if not token_instance:
#                     return redirect(f"{reverse('quickbooks_login')}?next=add-contract")
                                                
#                 if token_instance.is_token_expired():
#                     print("Token expired, refreshing...")
#                     new_access_token = refresh_quickbooks_token(token_instance.refresh_token)
#                     if not new_access_token:
#                         return redirect(f"{reverse('quickbooks_login')}?next=add-contract")
                    
#                     token_instance.access_token = new_access_token
#                     token_instance.expires_at = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
#                     token_instance.save()
#             except QuickBooksToken.DoesNotExist:
#                 return redirect(f"{reverse('quickbooks_login')}?next=add-contract")
#             # Get processors and add to context
            
#             if request.method == "POST":
#                 print("post method is hit")               
#                 selected_processor = request.POST.get('selected_processor') 
#                 contract_type = request.POST.get('contract_type')               
#                 contract_start_date = request.POST.get('contract_start_date')
#                 contract_period = request.POST.get('contract_period')
#                 status = request.POST.get('status')                
               
#                 if selected_processor:
#                     try:
#                         processor_id, processor_type = selected_processor.split("_")
#                     except ValueError:
#                         context["error_messages"] = "Invalid processor selection."
#                         return render(request, 'contracts/create_admin_processor_contract.html', context)
                    
#                     # Retrieve the processor object
#                     if processor_type == "T1":
#                         processor = Processor.objects.filter(id=processor_id).first()
#                     else:
#                         processor = Processor2.objects.filter(id=processor_id).first()
                    
#                     # Check if the processor exists
#                     if not processor:
#                         context["error_messages"] = "Selected processor does not exist."
#                         return render(request, 'contracts/create_admin_processor_contract.html', context)

#                     contract = AdminProcessorContract.objects.create(                        
#                         processor_id=processor_id, 
#                         processor_type=processor_type,
#                         processor_entity_name=processor.entity_name, 
#                         contract_type=contract_type,                        
#                         contract_start_date=contract_start_date, 
#                         contract_period=contract_period,
#                         status=status, 
#                         created_by_id=request.user.id
#                     )

#                     crop_names = request.POST.getlist('crop[]')
#                     crop_types = request.POST.getlist('crop_type[]')
#                     contract_amounts = request.POST.getlist('contract_amount[]')
#                     amount_units = request.POST.getlist('amount_unit[]')
#                     per_unit_rates = request.POST.getlist('per_unit_rate[]')

#                     for crop_name, crop_type, contract_amount, amount_unit, per_unit_rate in zip(
#                             crop_names, crop_types, contract_amounts, amount_units, per_unit_rates):
                        
#                         # Create crop details for each crop entry
#                         item_name = ShipmentItem.objects.filter(item=crop_name).first().item_name
#                         crop = CropDetails.objects.create(
#                             contract=contract,
#                             crop=item_name,
#                             crop_type=crop_type,
#                             contract_amount=contract_amount,
#                             amount_unit=amount_unit,
#                             per_unit_rate=per_unit_rate
#                         )
#                         item_name = f"{crop.crop}"
#                         item_type = f"{crop.crop_type}"
#                         description = f"Crop: {crop.crop}, Type: {crop.crop_type}, Rate: {crop.per_unit_rate} per unit"
                        
#                         item, created = ShipmentItem.objects.update_or_create(
#                             item_name=item_name,
#                             item_type=item_type,
#                             per_unit_price=crop.per_unit_rate,
#                             defaults={
#                                 "description": description,
#                                 "type": "Inventory",
#                                 "is_active": True,
#                             }
#                         )
#                         if created:
#                             try:                                
#                                 accounts = get_quickbooks_accounts(token_instance.realm_id, token_instance.access_token)
                                
#                                 income_account_id = None
#                                 expense_account_id = None
#                                 asset_account_id = None

#                                 for account in accounts:
#                                     if account.get("AccountType") == "Income" and account.get("AccountSubType") == "SalesOfProductIncome" and income_account_id is None:
#                                         income_account_id = account.get("Id")
#                                     elif (account.get("AccountType") == "Cost of Goods Sold" and account.get("AccountSubType") == "SuppliesMaterialsCogs" and expense_account_id is None):
#                                         expense_account_id = account.get("Id")
#                                     elif account.get("AccountType") in ["Other Current Asset", "Inventory Asset"] and account.get("AccountSubType") == "Inventory" and asset_account_id is None:
#                                         asset_account_id = account.get("Id")

#                                     if income_account_id and expense_account_id and asset_account_id:
#                                         break

#                                 item_data = {
#                                     "Name": f"{item.item_name}-{item.item_type}-{item.per_unit_price}",
#                                     "Type": item.type,
#                                     "UnitPrice": str(item.per_unit_price),
#                                     "IncomeAccountRef": {
#                                         "value": income_account_id,
#                                     },
#                                     "ExpenseAccountRef": {
#                                         "value": expense_account_id,
#                                     },
#                                     "AssetAccountRef": {
#                                         "value": asset_account_id,
#                                     },
#                                     "Description": item.description or "",
#                                     "Active": item.is_active,
#                                     "QtyOnHand":float(crop.contract_amount),
#                                     "TrackQtyOnHand":True,
#                                     "InvStartDate": datetime.now().strftime('%Y-%m-%d')
#                                 }                               
                               
#                                 created_item = create_item(token_instance.realm_id, token_instance.access_token, item_data)                               
#                                 if created_item:
#                                     print("Item added successfully and synced with QuickBooks.")
#                                     messages.success(request, "Item added successfully and synced with QuickBooks.")
#                                 else:
#                                     print("Failed to sync with QuickBooks.")
#                                     messages.error(request, "Failed to add Item in QuickBooks.")

#                             except ImproperlyConfigured as e:
#                                 print(str(e))

#                     ## Send notification to the processor.
#                     if processor_type == "T1":
#                         all_processor_user = ProcessorUser.objects.filter(processor_id=processor_id)
#                     else:
#                         all_processor_user = ProcessorUser2.objects.filter(processor2_id=processor_id)
#                     for user in all_processor_user :
#                         msg = 'A new Contract has been initiated between Admin and you.'
#                         get_user = User.objects.get(username=user.contact_email)
#                         notification_reason = 'New Contract Assigned.'
#                         redirect_url = "/contracts/admin-processor-contract-list/"
#                         save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
#                             notification_reason=notification_reason)
#                         save_notification.save()

#                     document_names = request.POST.getlist('document_name[]')                   
                    
#                     for name in document_names:
#                         AdminProcessorContractDocuments.objects.create(
#                             contract=contract,
#                             name=name                            
#                         )                    
#                     return redirect('list-contract')
#                 else:
#                     context["error_messages"] = "Processor must be selected."
            
#             return render(request, 'contracts/create_admin_processor_contract.html', context)
#         else:
#             messages.error(request, "Not a valid request.")
#             return redirect("dashboard")                                  
#     except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
#         context["error_messages"] = str(e)
#     return render(request, 'contracts/create_admin_processor_contract.html', context)


@login_required()
def admin_processor_contract_create(request):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            processor1 = list(Processor.objects.all().values("id", "entity_name"))
            processor2 = list(Processor2.objects.filter(processor_type__type_name="T2").values("id", "entity_name"))
            processor3 = list(Processor2.objects.filter(processor_type__type_name="T3").values("id", "entity_name"))
            processor4 = list(Processor2.objects.filter(processor_type__type_name="T4").values("id", "entity_name"))
            processor = []
            crops = ShipmentItem.objects.all()
            context["crops"] = crops
            for i in processor1:
                my_dict = {"id":None, "entity_name":None, "type":None}
                my_dict["id"] = i["id"]
                my_dict["entity_name"] = i["entity_name"]
                my_dict["type"] = "T1"
                processor.append(my_dict)

            for i in processor2:
                my_dict = {"id":None, "entity_name":None, "type":None}
                my_dict["id"] = i["id"]
                my_dict["entity_name"] = i["entity_name"]
                my_dict["type"] = "T2"
                processor.append(my_dict)

            for i in processor3:
                my_dict = {"id":None, "entity_name":None, "type":None}
                my_dict["id"] = i["id"]
                my_dict["entity_name"] = i["entity_name"]
                my_dict["type"] = "T3"
                processor.append(my_dict)

            for i in processor4:
                my_dict = {"id":None, "entity_name":None, "type":None}
                my_dict["id"] = i["id"]
                my_dict["entity_name"] = i["entity_name"]
                my_dict["type"] = "T4"
                processor.append(my_dict)

            context["processor"] = processor
            
            # Get processors and add to context
            
            if request.method == "POST":
                print("post method is hit")               
                selected_processor = request.POST.get('selected_processor') 
                contract_type = request.POST.get('contract_type')               
                contract_start_date = request.POST.get('contract_start_date')
                contract_period = request.POST.get('contract_period')
                status = request.POST.get('status')                
               
                if selected_processor:
                    try:
                        processor_id, processor_type = selected_processor.split("_")
                    except ValueError:
                        context["error_messages"] = "Invalid processor selection."
                        return render(request, 'contracts/create_admin_processor_contract.html', context)
                    
                    # Retrieve the processor object
                    if processor_type == "T1":
                        processor = Processor.objects.filter(id=processor_id).first()
                    else:
                        processor = Processor2.objects.filter(id=processor_id).first()
                    
                    # Check if the processor exists
                    if not processor:
                        context["error_messages"] = "Selected processor does not exist."
                        return render(request, 'contracts/create_admin_processor_contract.html', context)

                    contract = AdminProcessorContract.objects.create(                        
                        processor_id=processor_id, 
                        processor_type=processor_type,
                        processor_entity_name=processor.entity_name, 
                        contract_type=contract_type,                        
                        contract_start_date=contract_start_date, 
                        contract_period=contract_period,
                        status=status, 
                        created_by_id=request.user.id
                    )

                    crop_names = request.POST.getlist('crop[]')
                    crop_types = request.POST.getlist('crop_type[]')
                    contract_amounts = request.POST.getlist('contract_amount[]')
                    amount_units = request.POST.getlist('amount_unit[]')
                    per_unit_rates = request.POST.getlist('per_unit_rate[]')

                    for crop_name, crop_type, contract_amount, amount_unit, per_unit_rate in zip(
                            crop_names, crop_types, contract_amounts, amount_units, per_unit_rates):
                        
                        # Create crop details for each crop entry
                        item_name = ShipmentItem.objects.filter(item=crop_name).first().item_name
                        crop = CropDetails.objects.create(
                            contract=contract,
                            crop=item_name,
                            crop_type=crop_type,
                            contract_amount=contract_amount,
                            amount_unit=amount_unit,
                            per_unit_rate=per_unit_rate
                        )                       

                    ## Send notification to the processor.
                    if processor_type == "T1":
                        all_processor_user = ProcessorUser.objects.filter(processor_id=processor_id)
                    else:
                        all_processor_user = ProcessorUser2.objects.filter(processor2_id=processor_id)
                    for user in all_processor_user :
                        msg = 'A new Contract has been initiated between Admin and you.'
                        get_user = User.objects.get(username=user.contact_email)
                        notification_reason = 'New Contract Assigned.'
                        redirect_url = "/contracts/admin-processor-contract-list/"
                        save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
                            notification_reason=notification_reason)
                        save_notification.save()

                    document_names = request.POST.getlist('document_name[]')                   
                    
                    for name in document_names:
                        AdminProcessorContractDocuments.objects.create(
                            contract=contract,
                            name=name                            
                        )                    
                    return redirect('list-contract')
                else:
                    context["error_messages"] = "Processor must be selected."
            
            return render(request, 'contracts/create_admin_processor_contract.html', context)
        else:
            messages.error(request, "Not a valid request.")
            return redirect("dashboard")                                  
    except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
        context["error_messages"] = str(e)
    return render(request, 'contracts/create_admin_processor_contract.html', context)


@login_required()
def admin_processor_contract_list(request):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            processor1 = list(Processor.objects.all().values("id", "entity_name"))
            processor2 = list(Processor2.objects.filter(processor_type__type_name="T2").values("id", "entity_name"))
            processor3 = list(Processor2.objects.filter(processor_type__type_name="T3").values("id", "entity_name"))
            processor4 = list(Processor2.objects.filter(processor_type__type_name="T4").values("id", "entity_name"))
            processor = []
            
            for i in processor1:
                my_dict = {"id":None, "entity_name":None, "type":None}
                my_dict["id"] = i["id"]
                my_dict["entity_name"] = i["entity_name"]
                my_dict["type"] = "T1"
                processor.append(my_dict)

            for i in processor2:
                my_dict = {"id":None, "entity_name":None, "type":None}
                my_dict["id"] = i["id"]
                my_dict["entity_name"] = i["entity_name"]
                my_dict["type"] = "T2"
                processor.append(my_dict)

            for i in processor3:
                my_dict = {"id":None, "entity_name":None, "type":None}
                my_dict["id"] = i["id"]
                my_dict["entity_name"] = i["entity_name"]
                my_dict["type"] = "T3"
                processor.append(my_dict)

            for i in processor4:
                my_dict = {"id":None, "entity_name":None, "type":None}
                my_dict["id"] = i["id"]
                my_dict["entity_name"] = i["entity_name"]
                my_dict["type"] = "T4"
                processor.append(my_dict)

            context["processor"] = processor
            
            contracts = AdminProcessorContract.objects.prefetch_related(
                    Prefetch('contractCrop', queryset=CropDetails.objects.all())
                ).all()
            
            selected_processor = request.GET.get('selected_processor','All')
            
            if selected_processor != 'All':
                processor_id, processor_type = selected_processor.split('_')
                context['selected_processor_id'] = int(processor_id)
                context['selected_processor_type'] = processor_type
            else:
                processor_id, processor_type = None, None
                context['selected_processor_id'] = None
                context['selected_processor_type'] = None
            if selected_processor and selected_processor != 'All':                
                contracts = contracts.filter(processor_id=int(processor_id))

            search_name = request.GET.get('search_name', '')   
            if search_name and search_name is not None:
                contracts = contracts.filter(Q(secret_key__icontains=search_name)| Q(contractCrop__crop__icontains=search_name) | Q(contractCrop__crop_type__icontains=search_name))
                context['search_name'] = search_name
            else:
                context['search_name'] = None 
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            
            if start_date or end_date:
                if start_date:
                    start_date = parse_date(start_date)
                if end_date:
                    end_date = parse_date(end_date)

                if start_date and end_date:
                    contracts = contracts.filter(
                        Q(contract_start_date__lte=end_date) & 
                        (
                            Q(contract_start_date__lte=start_date) |  
                            Q(contract_start_date__range=(start_date, end_date))
                        ) &
                        (
                            Q(end_date__range=(start_date, end_date)) |
                            Q(end_date__gte=end_date)  
                        )
                    )               

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None           
            
            contracts = contracts.order_by('-id')
            paginator = Paginator(contracts, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'contracts/admin_processor_contract_list.html', context)
        
        elif request.user.is_processor:
            user_email = request.user.email
            p = ProcessorUser.objects.get(contact_email=user_email)
            processor_id = Processor.objects.get(id=p.processor.id).id
            processor_type = "T1"
            
            contracts = AdminProcessorContract.objects.prefetch_related(
                    Prefetch('contractCrop', queryset=CropDetails.objects.all())
                ).filter(processor_id=processor_id, processor_type=processor_type)
            
            search_name = request.GET.get('search_name', '')   
            if search_name and search_name is not None:
                contracts = contracts.filter(Q(secret_key__icontains=search_name)| Q(contractCrop__crop__icontains=search_name) | Q(contractCrop__crop_type__icontains=search_name))
                context['search_name'] = search_name
            else:
                context['search_name'] = None 
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            
            if start_date or end_date:
                if start_date:
                    start_date = parse_date(start_date)
                if end_date:
                    end_date = parse_date(end_date)

                if start_date and end_date:
                    contracts = contracts.filter(
                        Q(contract_start_date__lte=end_date) & 
                        (
                            Q(contract_start_date__lte=start_date) |  
                            Q(contract_start_date__range=(start_date, end_date))
                        ) &
                        (
                            Q(end_date__range=(start_date, end_date)) |
                            Q(end_date__gte=end_date)  
                        )
                    )               

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None
            
            contracts = contracts.order_by('-id')
            paginator = Paginator(contracts, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'contracts/admin_processor_contract_list.html', context)
        
        elif request.user.is_processor2:
            user_email = request.user.email
            p = ProcessorUser2.objects.get(contact_email=user_email)
            processor_id = Processor2.objects.get(id=p.processor2.id).id
            processor_type = Processor2.objects.get(id=p.processor2.id).processor_type.all().first().type_name

            contracts = AdminProcessorContract.objects.prefetch_related(
                    Prefetch('contractCrop', queryset=CropDetails.objects.all())
                ).filter(processor_id=processor_id, processor_type=processor_type)
            
            search_name = request.GET.get('search_name', '')   
            if search_name and search_name is not None:
                contracts = contracts.filter(Q(secret_key__icontains=search_name)| Q(contractCrop__crop__icontains=search_name) | Q(contractCrop__crop_type__icontains=search_name))
                context['search_name'] = search_name
            else:
                context['search_name'] = None 
            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            
            if start_date or end_date:
                if start_date:
                    start_date = parse_date(start_date)
                if end_date:
                    end_date = parse_date(end_date)

                if start_date and end_date:
                    contracts = contracts.filter(
                        Q(contract_start_date__lte=end_date) & 
                        (
                            Q(contract_start_date__lte=start_date) |  
                            Q(contract_start_date__range=(start_date, end_date))
                        ) &
                        (
                            Q(end_date__range=(start_date, end_date)) |
                            Q(end_date__gte=end_date)  
                        )
                    )               

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None
            
            contracts = contracts.order_by('-id')
            paginator = Paginator(contracts, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'contracts/admin_processor_contract_list.html', context)
    
        else:
            messages.error(request, "Not a valid request.")
            return redirect("dashboard")   
    except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
        context["error_messages"] = str(e)
    return render(request, 'contracts/admin_processor_contract_list.html', context)


@login_required()
def admin_processor_contract_view(request, pk):
    context ={}
    try:
        # Superuser................
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_processor or request.user.is_processor2:
            contract = AdminProcessorContract.objects.prefetch_related(
                    Prefetch('contractCrop', queryset=CropDetails.objects.all())
                ).filter(id=pk).first()
            documents = AdminProcessorContractDocuments.objects.filter(contract=contract)
            context["contract"] = contract
            
            context["documents"] = documents
            return render (request, 'contracts/admin_processor_contract_view.html', context)
        else:
            return redirect('login') 
    except Exception as e:
        context["error_messages"] = str(e)
        return render (request, 'contracts/admin_processor_contract_view.html', context)


# @login_required()
# def edit_admin_processor_contract(request, pk):
#     context = {}
#     try:
#         from apps.quickbooks_integration.views import create_item, get_item_data, update_item,refresh_quickbooks_token, get_quickbooks_accounts
#         from apps.quickbooks_integration.models import QuickBooksToken

#         success_url = reverse('edit-admin-processor-contract', kwargs={'pk': pk})
#         next_url = f"{success_url}"
#         redirect_url = f"{reverse('quickbooks_login')}?{urlencode({'next': next_url})}"
        
#         token_instance = QuickBooksToken.objects.first()
#         if not token_instance:
#             return redirect(redirect_url)
                                        
#         if token_instance.is_token_expired():
#             print("Token expired, refreshing...")
#             new_access_token = refresh_quickbooks_token(token_instance.refresh_token)
#             if not new_access_token:
#                 return redirect(redirect_url)
            
#             token_instance.access_token = new_access_token
#             token_instance.expires_at = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
#             token_instance.save()
#     except QuickBooksToken.DoesNotExist:
#         return redirect(redirect_url)
#     try:
#         contract = get_object_or_404(AdminProcessorContract, id=pk)       

#         processor1 = list(Processor.objects.all().values("id", "entity_name"))
#         processor2 = list(Processor2.objects.filter(processor_type__type_name="T2").values("id", "entity_name"))
#         processor3 = list(Processor2.objects.filter(processor_type__type_name="T3").values("id", "entity_name"))
#         processor4 = list(Processor2.objects.filter(processor_type__type_name="T4").values("id", "entity_name"))
#         processor = []
        
#         for i in processor1:
#             my_dict = {"id":None, "entity_name":None, "type":None}
#             my_dict["id"] = i["id"]
#             my_dict["entity_name"] = i["entity_name"]
#             my_dict["type"] = "T1"
#             processor.append(my_dict)

#         for i in processor2:
#             my_dict = {"id":None, "entity_name":None, "type":None}
#             my_dict["id"] = i["id"]
#             my_dict["entity_name"] = i["entity_name"]
#             my_dict["type"] = "T2"
#             processor.append(my_dict)

#         for i in processor3:
#             my_dict = {"id":None, "entity_name":None, "type":None}
#             my_dict["id"] = i["id"]
#             my_dict["entity_name"] = i["entity_name"]
#             my_dict["type"] = "T3"
#             processor.append(my_dict)

#         for i in processor4:
#             my_dict = {"id":None, "entity_name":None, "type":None}
#             my_dict["id"] = i["id"]
#             my_dict["entity_name"] = i["entity_name"]
#             my_dict["type"] = "T4"
#             processor.append(my_dict)       

#         documents = AdminProcessorContractDocuments.objects.filter(contract=contract)     
#         crop_names = Crop.objects.all()   
        
#         crops = CropDetails.objects.filter(contract=contract)
#         context = {
#             "contract": contract,
#             "processor": processor,
#             'selected_processor_id': contract.processor_id,
#             'selected_processor_type': contract.processor_type,
#             'selected_contract_type':contract.contract_type,
#             'crops': crops,
#             "crop_names":crop_names,
#             "contract_start_date": contract.contract_start_date,
#             "contract_period": contract.contract_period,
#             "status": contract.status,
#             "documents": documents,
#         }

#         if request.method == "POST":
#             if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():

#                 selected_processor = request.POST.get('selected_processor')
#                 selected_contract_type = request.POST.get('contract_type')
#                 contract_start_date = request.POST.get('contract_start_date')
#                 contract_period = request.POST.get('contract_period')
#                 status = request.POST.get('status')
                
#                 if selected_processor:
#                     try:
#                         processor_id, processor_type = selected_processor.split("_")
#                     except ValueError:
#                         context["error_messages"] = "Invalid processor selection."
#                         return render(request, 'contracts/edit_admin_processor_contract.html', context)

#                     if processor_type == "T1":
#                         processor = Processor.objects.filter(id=processor_id).first()
#                     else:
#                         processor = Processor2.objects.filter(id=processor_id).first()

#                     if not processor:
#                         context["error_messages"] = "Selected processor does not exist."
#                         return render(request, 'contracts/edit_admin_processor_contract.html', context)

#                     contract.processor_id = processor_id
#                     contract.processor_type = processor_type
#                     contract.processor_entity_name = processor.entity_name
#                     contract.contract_type = selected_contract_type                    
#                     contract.contract_start_date = contract_start_date
#                     contract.contract_period = contract_period
#                     contract.status = status
#                     contract.save()

#                     crop_ids = request.POST.getlist("crop_id[]")
#                     crops = request.POST.getlist("crop[]")
#                     crop_types = request.POST.getlist("crop_type[]")
#                     contract_amounts = request.POST.getlist("contract_amount[]")
#                     amount_units = request.POST.getlist("amount_unit[]")
#                     per_unit_rates = request.POST.getlist("per_unit_rate[]")
#                     delete_flags = request.POST.getlist("delete_flag[]") 

#                     with transaction.atomic():
#                         for idx, crop_id in enumerate(crop_ids):

#                             if crop_id.isdigit() and delete_flags[idx] == "1":
#                                 try:
#                                     CropDetails.objects.get(id=int(crop_id)).delete()
#                                     print(f"Deleted crop with id {crop_id}")
#                                 except CropDetails.DoesNotExist:
#                                     print(f"Crop with id {crop_id} not found.")
#                             else:
#                                 print(f"Skipping crop with id {crop_id}, not marked for deletion.")

#                         for idx in range(len(crops)):
#                             crop_id = crop_ids[idx] if idx < len(crop_ids) else None

#                             if crop_id and crop_id.isdigit():
#                                 try:
#                                     crop_detail = CropDetails.objects.get(id=int(crop_id))
#                                     item = ShipmentItem.objects.filter(item_name=crop_detail.crop,item_type=crop_detail.crop_type,per_unit_price=crop_detail.per_unit_rate,type="Inventory").first()
#                                     crop_detail.crop = crops[idx]
#                                     crop_detail.crop_type = crop_types[idx]
#                                     crop_detail.contract_amount = contract_amounts[idx]
#                                     crop_detail.amount_unit = amount_units[idx]
#                                     crop_detail.per_unit_rate = per_unit_rates[idx]
#                                     crop_detail.save()

#                                     if crop_detail.crop_type != item.item_type or float(crop_detail.per_unit_rate) != float(item.per_unit_price):
#                                         item_name = f"{crop_detail.crop}"
#                                         item_type = f"{crop_detail.crop_type}"
#                                         description = f"Crop: {crop_detail.crop}, Type: {crop_detail.crop_type}, Rate: {crop_detail.per_unit_rate} per unit"
#                                         item.item_name = item_name
#                                         item.item_type = item_type
#                                         item.per_unit_price = crop_detail.per_unit_rate
#                                         item.description = description
#                                         item.save()
#                                         try:                                      
#                                             accounts = get_quickbooks_accounts(token_instance.realm_id, token_instance.access_token)                                        
#                                             income_account_id = None
#                                             expense_account_id = None
#                                             asset_account_id = None

#                                             for account in accounts:
#                                                 if account.get("AccountType") == "Income" and account.get("AccountSubType") == "SalesOfProductIncome" and income_account_id is None:
#                                                     income_account_id = account.get("Id")
#                                                 elif (account.get("AccountType") == "Cost of Goods Sold" and account.get("AccountSubType") == "SuppliesMaterialsCogs" and expense_account_id is None):
#                                                     expense_account_id = account.get("Id")
#                                                 elif account.get("AccountType") in ["Other Current Asset", "Inventory Asset"] and account.get("AccountSubType") == "Inventory" and asset_account_id is None:
#                                                     asset_account_id = account.get("Id")

#                                                 if income_account_id and expense_account_id and asset_account_id:
#                                                     break

#                                             item_data = {
#                                                 "Name": f"{item.item_name}-{item.item_type}-{item.per_unit_price}",
#                                                 "Type": item.type,
#                                                 "UnitPrice": str(item.per_unit_price),
#                                                 "IncomeAccountRef": {
#                                                     "value": income_account_id,
#                                                 },
#                                                 "ExpenseAccountRef": {
#                                                     "value": expense_account_id,
#                                                 },
#                                                 "AssetAccountRef": {
#                                                     "value": asset_account_id,
#                                                 },
#                                                 "Description": item.description or "",
#                                                 "Active": item.is_active,
#                                                 "QtyOnHand":float(crop_detail.contract_amount),
#                                                 "TrackQtyOnHand":True,
#                                                 "InvStartDate": datetime.now().strftime('%Y-%m-%d')
#                                             }
                                            
#                                             item_id = item.quickbooks_id
#                                             item_details = get_item_data(item_id)
#                                             sync_token = item_details.get('Item', {}).get('SyncToken', '')
#                                             updated_item = update_item(token_instance.realm_id, token_instance.access_token, item_id, sync_token, item_data)                               
#                                             if updated_item:
#                                                 print("Item updated successfully and synced with QuickBooks.")
#                                                 messages.success(request, "Item updated successfully and synced with QuickBooks.")
#                                             else:
#                                                 print("Failed to update Item in QuickBooks.")
#                                                 messages.error(request, "Failed to update Item in QuickBooks.")

#                                         except ImproperlyConfigured as e:
#                                             print(str(e))
#                                     else:
#                                         pass
                                    
                                    
#                                 except CropDetails.DoesNotExist:
#                                     print(f"Crop with id {crop_id} not found.")
#                             else:
#                                 crop = CropDetails.objects.create(
#                                     contract=contract,
#                                     crop=crops[idx],
#                                     crop_type=crop_types[idx],
#                                     contract_amount=contract_amounts[idx],
#                                     amount_unit=amount_units[idx],
#                                     per_unit_rate=per_unit_rates[idx]
#                                 )
#                                 item_name = f"{crop.crop}"
#                                 item_type = f"{crop.crop_type}"
#                                 description = f"Crop: {crop.crop}, Type: {crop.crop_type}, Rate: {crop.per_unit_rate} per unit"
                                
#                                 item, created = ShipmentItem.objects.update_or_create(
#                                     item_name=item_name,
#                                     item_type=item_type,
#                                     per_unit_price=crop.per_unit_rate,
#                                     defaults={
#                                         "description": description,
#                                         "type": "Inventory",
#                                         "is_active": True,
#                                     }
#                                 )
#                                 if created:
#                                     try:                                      
#                                         accounts = get_quickbooks_accounts(token_instance.realm_id, token_instance.access_token)
                                        
#                                         income_account_id = None
#                                         expense_account_id = None
#                                         asset_account_id = None

#                                         for account in accounts:
#                                             if account.get("AccountType") == "Income" and account.get("AccountSubType") == "SalesOfProductIncome" and income_account_id is None:
#                                                 income_account_id = account.get("Id")
#                                             elif (account.get("AccountType") == "Cost of Goods Sold" and account.get("AccountSubType") == "SuppliesMaterialsCogs" and expense_account_id is None):
#                                                 expense_account_id = account.get("Id")
#                                             elif account.get("AccountType") in ["Other Current Asset", "Inventory Asset"] and account.get("AccountSubType") == "Inventory" and asset_account_id is None:
#                                                 asset_account_id = account.get("Id")

#                                             if income_account_id and expense_account_id and asset_account_id:
#                                                 break

#                                         item_data = {
#                                             "Name": f"{item.item_name}-{item.item_type}-{item.per_unit_price}",
#                                             "Type": item.type,
#                                             "UnitPrice": str(item.per_unit_price),
#                                             "IncomeAccountRef": {
#                                                 "value": income_account_id,
#                                             },
#                                             "ExpenseAccountRef": {
#                                                 "value": expense_account_id,
#                                             },
#                                             "AssetAccountRef": {
#                                                 "value": asset_account_id,
#                                             },
#                                             "Description": item.description or "",
#                                             "Active": item.is_active,
#                                             "QtyOnHand":float(crop.contract_amount),
#                                             "TrackQtyOnHand":True,
#                                             "InvStartDate": datetime.now().strftime('%Y-%m-%d')
#                                         }
                               
#                                         created_item = create_item(token_instance.realm_id, token_instance.access_token, item_data)                               
#                                         if created_item:
#                                             print("Item added successfully and synced with QuickBooks.")
#                                             messages.success(request, "Item added successfully and synced with QuickBooks.")
#                                         else:
#                                             print("Failed to sync with QuickBooks.")
#                                             messages.error(request, "Failed to add item in QuickBooks.")

#                                     except ImproperlyConfigured as e:
#                                         print(str(e))


#                     delete_document_ids = request.POST.getlist('delete_document_ids[]')                    
#                     for document_id in delete_document_ids:
#                         try:
#                             document = AdminProcessorContractDocuments.objects.get(id=document_id)
#                             document.delete()  
#                         except AdminProcessorContractDocuments.DoesNotExist:
#                             pass
#                     document_ids =  request.POST.getlist('document_ids')
#                     for document_id in document_ids:
#                         document_status = f'document_status_{document_id}'
#                         if document_status in request.POST:                            
#                             document_stat = request.POST.get(document_status)                         
                            
#                             document = AdminProcessorContractDocuments.objects.filter(id=document_id).first()
#                             document.document_status = document_stat 
#                             document.save()                                
                            
#                     document_names = request.POST.getlist('document_name[]')  
#                     if document_names:                      
                    
#                         for i, name in enumerate(document_names):
#                             if i < len(document_ids):
#                                 document_id = document_ids[i]

#                                 document = AdminProcessorContractDocuments.objects.filter(id=document_id).first()
#                                 if document:
#                                     document.name = name 
#                                     document.save()
#                             else:
#                                 AdminProcessorContractDocuments.objects.create(contract=contract, name=name)
#                 return redirect('list-contract')
            
#             elif request.user.is_processor or request.user.is_processor2:
#                 document_ids = request.POST.getlist('document_ids')        
#                 for document_id in document_ids:
#                     file_field_name = f'document_file_{document_id}'
                    
#                     if file_field_name in request.FILES:
#                         uploaded_file = request.FILES[file_field_name]                        

#                         try:
#                             document = AdminProcessorContractDocuments.objects.get(id=document_id)
#                             document.document = uploaded_file  
#                             document.save()
                            
#                         except AdminProcessorContractDocuments.DoesNotExist:

#                             pass
#                 contract.status = "Under Review"
#                 contract.save()
#                 return redirect('list-contract')
#         return render(request, 'contracts/edit_admin_processor_contract.html', context)
#     except Exception as e:
#         print(f"Exception occurred: {str(e)}")
#         context["error_messages"] = str(e)
#         return render(request, 'contracts/edit_admin_processor_contract.html', context)


@login_required()
def edit_admin_processor_contract(request, pk):
    context = {}    
    try:
        contract = get_object_or_404(AdminProcessorContract, id=pk)       

        processor1 = list(Processor.objects.all().values("id", "entity_name"))
        processor2 = list(Processor2.objects.filter(processor_type__type_name="T2").values("id", "entity_name"))
        processor3 = list(Processor2.objects.filter(processor_type__type_name="T3").values("id", "entity_name"))
        processor4 = list(Processor2.objects.filter(processor_type__type_name="T4").values("id", "entity_name"))
        processor = []
        
        for i in processor1:
            my_dict = {"id":None, "entity_name":None, "type":None}
            my_dict["id"] = i["id"]
            my_dict["entity_name"] = i["entity_name"]
            my_dict["type"] = "T1"
            processor.append(my_dict)

        for i in processor2:
            my_dict = {"id":None, "entity_name":None, "type":None}
            my_dict["id"] = i["id"]
            my_dict["entity_name"] = i["entity_name"]
            my_dict["type"] = "T2"
            processor.append(my_dict)

        for i in processor3:
            my_dict = {"id":None, "entity_name":None, "type":None}
            my_dict["id"] = i["id"]
            my_dict["entity_name"] = i["entity_name"]
            my_dict["type"] = "T3"
            processor.append(my_dict)

        for i in processor4:
            my_dict = {"id":None, "entity_name":None, "type":None}
            my_dict["id"] = i["id"]
            my_dict["entity_name"] = i["entity_name"]
            my_dict["type"] = "T4"
            processor.append(my_dict)       

        documents = AdminProcessorContractDocuments.objects.filter(contract=contract)     
        crop_names = ShipmentItem.objects.all()  
        
        crops = CropDetails.objects.filter(contract=contract)
        context = {
            "contract": contract,
            "processor": processor,
            'selected_processor_id': contract.processor_id,
            'selected_processor_type': contract.processor_type,
            'selected_contract_type':contract.contract_type,
            'crops': crops,
            "crop_names":crop_names,
            "contract_start_date": contract.contract_start_date,
            "contract_period": contract.contract_period,
            "status": contract.status,
            "documents": documents,
        }

        if request.method == "POST":
            if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():

                selected_processor = request.POST.get('selected_processor')
                selected_contract_type = request.POST.get('contract_type')
                contract_start_date = request.POST.get('contract_start_date')
                contract_period = request.POST.get('contract_period')
                status = request.POST.get('status')
                
                if selected_processor:
                    try:
                        processor_id, processor_type = selected_processor.split("_")
                    except ValueError:
                        context["error_messages"] = "Invalid processor selection."
                        return render(request, 'contracts/edit_admin_processor_contract.html', context)

                    if processor_type == "T1":
                        processor = Processor.objects.filter(id=processor_id).first()
                    else:
                        processor = Processor2.objects.filter(id=processor_id).first()

                    if not processor:
                        context["error_messages"] = "Selected processor does not exist."
                        return render(request, 'contracts/edit_admin_processor_contract.html', context)

                    contract.processor_id = processor_id
                    contract.processor_type = processor_type
                    contract.processor_entity_name = processor.entity_name
                    contract.contract_type = selected_contract_type                    
                    contract.contract_start_date = contract_start_date
                    contract.contract_period = contract_period
                    contract.status = status
                    contract.save()

                    crop_ids = request.POST.getlist("crop_id[]")
                    crops = request.POST.getlist("crop[]")
                    crop_types = request.POST.getlist("crop_type[]")
                    contract_amounts = request.POST.getlist("contract_amount[]")
                    amount_units = request.POST.getlist("amount_unit[]")
                    per_unit_rates = request.POST.getlist("per_unit_rate[]")
                    delete_flags = request.POST.getlist("delete_flag[]") 

                    with transaction.atomic():
                        for idx, crop_id in enumerate(crop_ids):
                            if crop_id.isdigit() and delete_flags[idx] == "1":
                                try:
                                    CropDetails.objects.get(id=int(crop_id)).delete()
                                    print(f"Deleted crop with id {crop_id}")
                                except CropDetails.DoesNotExist:
                                    print(f"Crop with id {crop_id} not found.")
                            else:
                                print(f"Skipping crop with id {crop_id}, not marked for deletion.")

                        for idx in range(len(crops)):
                            crop_id = crop_ids[idx] if idx < len(crop_ids) else None

                            if crop_id and crop_id.isdigit():
                                try:
                                    item_name = ShipmentItem.objects.filter(item=crops[idx]).first().item_name
                                    crop_detail = CropDetails.objects.get(id=int(crop_id))                                    
                                    crop_detail.crop = item_name
                                    crop_detail.crop_type = crop_types[idx]
                                    crop_detail.contract_amount = contract_amounts[idx]
                                    crop_detail.amount_unit = amount_units[idx]
                                    crop_detail.per_unit_rate = per_unit_rates[idx]
                                    crop_detail.save()                              
                                    
                                except CropDetails.DoesNotExist:
                                    print(f"Crop with id {crop_id} not found.")
                            else:
                                item_name = ShipmentItem.objects.filter(item=crops[idx]).first().item_name
                                crop = CropDetails.objects.create(
                                    contract=contract,
                                    crop=item_name,
                                    crop_type=crop_types[idx],
                                    contract_amount=contract_amounts[idx],
                                    amount_unit=amount_units[idx],
                                    per_unit_rate=per_unit_rates[idx]
                                )
                                
                    delete_document_ids = request.POST.getlist('delete_document_ids[]')                    
                    for document_id in delete_document_ids:
                        try:
                            document = AdminProcessorContractDocuments.objects.get(id=document_id)
                            document.delete()  
                        except AdminProcessorContractDocuments.DoesNotExist:
                            pass
                    document_ids =  request.POST.getlist('document_ids')
                    for document_id in document_ids:
                        document_status = f'document_status_{document_id}'
                        if document_status in request.POST:                            
                            document_stat = request.POST.get(document_status)                         
                            
                            document = AdminProcessorContractDocuments.objects.filter(id=document_id).first()
                            document.document_status = document_stat 
                            document.save()                                
                            
                    document_names = request.POST.getlist('document_name[]')  
                    if document_names:                      
                    
                        for i, name in enumerate(document_names):
                            if i < len(document_ids):
                                document_id = document_ids[i]

                                document = AdminProcessorContractDocuments.objects.filter(id=document_id).first()
                                if document:
                                    document.name = name 
                                    document.save()
                            else:
                                AdminProcessorContractDocuments.objects.create(contract=contract, name=name)
                return redirect('list-contract')
            
            elif request.user.is_processor or request.user.is_processor2:
                document_ids = request.POST.getlist('document_ids')        
                for document_id in document_ids:
                    file_field_name = f'document_file_{document_id}'
                    
                    if file_field_name in request.FILES:
                        uploaded_file = request.FILES[file_field_name]                        

                        try:
                            document = AdminProcessorContractDocuments.objects.get(id=document_id)
                            document.document = uploaded_file  
                            document.save()
                            
                        except AdminProcessorContractDocuments.DoesNotExist:

                            pass
                contract.status = "Under Review"
                contract.save()
                return redirect('list-contract')
        return render(request, 'contracts/edit_admin_processor_contract.html', context)
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        context["error_messages"] = str(e)
        return render(request, 'contracts/edit_admin_processor_contract.html', context)


# @login_required()
# def admin_customer_contract_create(request):
#     context = {}
#     try:
#         if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_distributor or request.user.warehouse_manager:
#             from apps.quickbooks_integration.views import create_item, refresh_quickbooks_token, get_quickbooks_accounts
#             from apps.quickbooks_integration.models import QuickBooksToken 
#             try:         
#                 token_instance = QuickBooksToken.objects.first()
#                 if not token_instance:
#                     return redirect(f"{reverse('quickbooks_login')}?next=add-admin-customer-contract")

#                 # Refresh the token if it is expired
#                 if token_instance.is_token_expired():
#                     print("Token expired, refreshing...")
#                     new_access_token = refresh_quickbooks_token(token_instance.refresh_token)
#                     if not new_access_token:
#                         return redirect(f"{reverse('quickbooks_login')}?next=add-admin-customer-contract")
                    
#                     token_instance.access_token = new_access_token
#                     token_instance.expires_at = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
#                     token_instance.save()
#             except QuickBooksToken.DoesNotExist:
#                 return redirect(f"{reverse('quickbooks_login')}?next=add-admin-customer-contract")
#             customers = Customer.objects.filter(is_active=True).values('id', 'name').order_by('name')          
#             context["customers"] = customers
#             crops = Crop.objects.all()
#             context["crops"] = crops
            
#             if request.method == "POST":

#                 selected_customer = request.POST.get('selected_customer') 
#                 contract_type = request.POST.get('contract_type')               
#                 contract_start_date = request.POST.get('contract_start_date')
#                 contract_period = request.POST.get('contract_period')
#                 status = request.POST.get('status')                

#                 if selected_customer:
#                     customer = Customer.objects.filter(id=selected_customer).first()  
#                     customer_name = customer.name                 
                    
#                     if not customer:
#                         context["error_messages"] = "Selected customer does not exist."
#                         return render(request, 'contracts/create_admin_customer_contract.html', context)
                    
#                     contract = AdminCustomerContract.objects.create(                        
#                         customer_id=customer.id,  
#                         customer_name= customer_name, 
#                         contract_type = contract_type,                                
#                         contract_start_date=contract_start_date, 
#                         contract_period=contract_period,
#                         status=status, 
#                         created_by_id=request.user.id
#                     )
#                     crop_names = request.POST.getlist('crop[]')
#                     crop_types = request.POST.getlist('crop_type[]')
#                     contract_amounts = request.POST.getlist('contract_amount[]')
#                     amount_units = request.POST.getlist('amount_unit[]')
#                     per_unit_rates = request.POST.getlist('per_unit_rate[]')
                    
#                     for crop_name, crop_type, contract_amount, amount_unit, per_unit_rate in zip(
#                             crop_names, crop_types, contract_amounts, amount_units, per_unit_rates):
                        
#                         crop = CustomerContractCropDetails.objects.create(
#                             contract=contract,
#                             crop=crop_name,
#                             crop_type=crop_type,
#                             contract_amount=contract_amount,
#                             amount_unit=amount_unit,
#                             per_unit_rate=per_unit_rate
#                         )
#                         item_name = f"{crop.crop}"
#                         item_type = f"{crop.crop_type}"
#                         description = f"Crop: {crop.crop}, Type: {crop.crop_type}, Rate: {crop.per_unit_rate} per unit"
                        
#                         item, created = ShipmentItem.objects.update_or_create(
#                             item_name=item_name,
#                             item_type=item_type,
#                             per_unit_price=crop.per_unit_rate,
#                             defaults={
#                                 "description": description,
#                                 "type": "Inventory",
#                                 "is_active": True,
#                             }
#                         )
#                         if created:
#                             try:                               
#                                 accounts = get_quickbooks_accounts(token_instance.realm_id, token_instance.access_token)  
                                                            
#                                 income_account_id = None
#                                 expense_account_id = None
#                                 asset_account_id = None

#                                 for account in accounts:
#                                     if account.get("AccountType") == "Income" and account.get("AccountSubType") == "SalesOfProductIncome" and income_account_id is None:
#                                         income_account_id = account.get("Id")
#                                     elif (account.get("AccountType") == "Cost of Goods Sold" and account.get("AccountSubType") == "SuppliesMaterialsCogs" and expense_account_id is None):
#                                         expense_account_id = account.get("Id")
#                                     elif account.get("AccountType") in ["Other Current Asset", "Inventory Asset"] and account.get("AccountSubType") == "Inventory" and asset_account_id is None:
#                                         asset_account_id = account.get("Id")

#                                     if income_account_id and expense_account_id and asset_account_id:
#                                         break

#                                 item_data = {
#                                     "Name": f"{item.item_name}-{item.item_type}-{item.per_unit_price}",
#                                     "Type": item.type,
#                                     "UnitPrice": str(item.per_unit_price),
#                                     "IncomeAccountRef": {
#                                         "value": income_account_id,
#                                     },
#                                     "ExpenseAccountRef": {
#                                         "value": expense_account_id,
#                                     },
#                                     "AssetAccountRef": {
#                                         "value": asset_account_id,
#                                     },
#                                     "Description": item.description or "",
#                                     "Active": item.is_active,
#                                     "QtyOnHand":float(crop.contract_amount),
#                                     "TrackQtyOnHand":True,
#                                     "InvStartDate": datetime.now().strftime('%Y-%m-%d')
#                                 }
                               
#                                 created_item = create_item(token_instance.realm_id, token_instance.access_token, item_data)                               
#                                 if created_item:
#                                     print("Item added successfully and synced with QuickBooks.")
#                                     messages.success(request, "Item added successfully and synced with QuickBooks.")
#                                 else:
#                                     print("Failed to sync with QuickBooks.")
#                                     messages.error(request, "Failed to add item in QuickBooks.")

#                             except ImproperlyConfigured as e:
#                                 print(str(e))
                  
#                     all_customer_user = CustomerUser.objects.filter(customer_id=customer.id)                    
#                     for user in all_customer_user :
#                         msg = 'A new Contract has been initiated between Admin and you.'
#                         get_user = User.objects.get(username=user.contact_email)
#                         notification_reason = 'New Contract Assigned.'
#                         redirect_url = "/contracts/admin-customer-contract-list/"
#                         save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
#                             notification_reason=notification_reason)
#                         save_notification.save()

#                     document_names = request.POST.getlist('document_name[]')                   
                    
#                     for name in document_names:
#                         AdminCustomerContractDocuments.objects.create(
#                             contract=contract,
#                             name=name                            
#                         )
                    
#                     return redirect('admin-customer-contract-list')
#                 else:
#                     context["error_messages"] = "Customer must be selected."
            
#             return render(request, 'contracts/create_admin_customer_contract.html', context)
#         else:
#             messages.error(request, "Not a valid request.")
#             return redirect("dashboard")                                  
#     except (ValueError, AttributeError, AdminCustomerContract.DoesNotExist) as e:
#         context["error_messages"] = str(e)
#     return render(request, 'contracts/create_admin_customer_contract.html', context)


@login_required()
def admin_customer_contract_create(request):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_distributor or request.user.warehouse_manager:
            
            customers = Customer.objects.filter(is_active=True).values('id', 'name').order_by('name')          
            context["customers"] = customers
            crops = ShipmentItem.objects.all()
            context["crops"] = crops
            
            if request.method == "POST":

                selected_customer = request.POST.get('selected_customer') 
                contract_type = request.POST.get('contract_type')               
                contract_start_date = request.POST.get('contract_start_date')
                contract_period = request.POST.get('contract_period')
                status = request.POST.get('status')                

                if selected_customer:
                    customer = Customer.objects.filter(id=selected_customer).first()  
                    customer_name = customer.name                 
                    
                    if not customer:
                        context["error_messages"] = "Selected customer does not exist."
                        return render(request, 'contracts/create_admin_customer_contract.html', context)
                    
                    contract = AdminCustomerContract.objects.create(                        
                        customer_id=customer.id,  
                        customer_name= customer_name, 
                        contract_type = contract_type,                                
                        contract_start_date=contract_start_date, 
                        contract_period=contract_period,
                        status=status, 
                        created_by_id=request.user.id
                    )
                    crop_names = request.POST.getlist('crop[]')
                    crop_types = request.POST.getlist('crop_type[]')
                    contract_amounts = request.POST.getlist('contract_amount[]')
                    amount_units = request.POST.getlist('amount_unit[]')
                    per_unit_rates = request.POST.getlist('per_unit_rate[]')
                    
                    for crop_name, crop_type, contract_amount, amount_unit, per_unit_rate in zip(
                            crop_names, crop_types, contract_amounts, amount_units, per_unit_rates):
                        
                        item_name = ShipmentItem.objects.filter(item=crop_name).first().item_name                        
                        crop = CustomerContractCropDetails.objects.create(
                            contract=contract,
                            crop=item_name,
                            crop_type=crop_type,
                            contract_amount=contract_amount,
                            amount_unit=amount_unit,
                            per_unit_rate=per_unit_rate
                        )
                        
                    all_customer_user = CustomerUser.objects.filter(customer_id=customer.id)                    
                    for user in all_customer_user :
                        msg = 'A new Contract has been initiated between Admin and you.'
                        get_user = User.objects.get(username=user.contact_email)
                        notification_reason = 'New Contract Assigned.'
                        redirect_url = "/contracts/admin-customer-contract-list/"
                        save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
                            notification_reason=notification_reason)
                        save_notification.save()

                    document_names = request.POST.getlist('document_name[]')                   
                    
                    for name in document_names:
                        AdminCustomerContractDocuments.objects.create(
                            contract=contract,
                            name=name                            
                        )                    
                    return redirect('admin-customer-contract-list')
                else:
                    context["error_messages"] = "Customer must be selected."
            
            return render(request, 'contracts/create_admin_customer_contract.html', context)
        else:
            messages.error(request, "Not a valid request.")
            return redirect("dashboard")                                  
    except (ValueError, AttributeError, AdminCustomerContract.DoesNotExist) as e:
        context["error_messages"] = str(e)
    return render(request, 'contracts/create_admin_customer_contract.html', context)


@login_required()
def admin_customer_contract_list(request):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            customers = Customer.objects.filter(is_active=True).values('id', 'name').order_by('name')           
                    
            context["customers"] = customers          
            
            contracts = AdminCustomerContract.objects.prefetch_related(
                    Prefetch('customerContractCrop', queryset=CustomerContractCropDetails.objects.all())
                ).all()
            selected_customer = request.GET.get('selected_customer','All')
            
            if selected_customer != 'All':
                customer_id = int(selected_customer)
                context['selected_customer_id'] = int(customer_id)
                
            else:   
                customer_id = None             
                context['selected_customer_id'] = None
                
            if selected_customer and selected_customer != 'All':                
                contracts = contracts.filter(customer_id=int(customer_id))

            search_name = request.GET.get('search_name', '')   
            if search_name and search_name is not None:
                contracts = contracts.filter(Q(secret_key__icontains=search_name) | Q(customerContractCrop__crop__icontains=search_name) | Q(customerContractCrop__crop_type__icontains=search_name))
                context['search_name'] = search_name
            else:
                context['search_name'] = None  

            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            
            if start_date or end_date:
                if start_date:
                    start_date = parse_date(start_date)
                if end_date:
                    end_date = parse_date(end_date)

                if start_date and end_date:
                    contracts = contracts.filter(
                        Q(contract_start_date__lte=end_date) & 
                        (
                            Q(contract_start_date__lte=start_date) |  
                            Q(contract_start_date__range=(start_date, end_date))
                        ) &
                        (
                            Q(end_date__range=(start_date, end_date)) |
                            Q(end_date__gte=end_date)  
                        )
                    )               

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None           
            
            contracts = contracts.order_by('-id')
            paginator = Paginator(contracts, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'contracts/admin_customer_contract_list.html', context)
        
        elif request.user.is_customer:
            user_email = request.user.email
            c = CustomerUser.objects.get(contact_email=user_email)
            customer_id = Customer.objects.get(id=c.customer.id).id

            contracts = AdminCustomerContract.objects.prefetch_related(
                    Prefetch('customerContractCrop', queryset=CustomerContractCropDetails.objects.all())
                ).filter(customer_id=customer_id)
            
            search_name = request.GET.get('search_name', '')   
            if search_name and search_name is not None:
                contracts = contracts.filter(Q(secret_key__icontains=search_name) | Q(customerContractCrop__crop__icontains=search_name) | Q(customerContractCrop__crop_type__icontains=search_name))
                context['search_name'] = search_name
            else:
                context['search_name'] = None  

            start_date = request.GET.get('start_date', '')
            end_date = request.GET.get('end_date', '')
            
            if start_date or end_date:
                if start_date:
                    start_date = parse_date(start_date)
                if end_date:
                    end_date = parse_date(end_date)

                if start_date and end_date:
                    contracts = contracts.filter(
                        Q(contract_start_date__lte=end_date) & 
                        (
                            Q(contract_start_date__lte=start_date) |  
                            Q(contract_start_date__range=(start_date, end_date))
                        ) &
                        (
                            Q(end_date__range=(start_date, end_date)) |
                            Q(end_date__gte=end_date)  
                        )
                    )               

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None 
                
            contracts = contracts.order_by('-id')
            paginator = Paginator(contracts, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'contracts/admin_customer_contract_list.html', context) 
             
        elif request.user.is_distributor:
            user_email = request.user.email
            d = DistributorUser.objects.get(contact_email=user_email)
            distributor_id = Distributor.objects.get(id=d.distributor.id).id
            contracts = contracts = AdminCustomerContract.objects.prefetch_related(
                    Prefetch('customerContractCrop', queryset=CustomerContractCropDetails.objects.all())
                ).all()
            contracts = contracts.order_by('-id')
            paginator = Paginator(contracts, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'contracts/admin_customer_contract_list.html', context)
        
        elif request.user.is_warehouse_manager:
            user_email = request.user.email
            # d = DistributorUser.objects.get(contact_email=user_email)
            # distributor_id = Distributor.objects.get(id=d.distributor.id).id
            contracts = contracts = AdminCustomerContract.objects.prefetch_related(
                    Prefetch('customerContractCrop', queryset=CustomerContractCropDetails.objects.all())
                ).all()
            contracts = contracts.order_by('-id')
            paginator = Paginator(contracts, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'contracts/admin_customer_contract_list.html', context)
        else:
            messages.error(request, "Not a valid request.")
            return redirect("dashboard")   
    except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
        context["error_messages"] = str(e)
    return render(request, 'contracts/admin_customer_contract_list.html', context)


@login_required()
def admin_customer_contract_view(request, pk):
    context ={}
    try:
        # Superuser................
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_customer or request.user.is_distributor or request.user.is_warehouse_manager:
            contract = AdminCustomerContract.objects.prefetch_related(
                    Prefetch('customerContractCrop', queryset=CustomerContractCropDetails.objects.all())
                ).filter(id=pk).first()
            documents = AdminCustomerContractDocuments.objects.filter(contract=contract)
            context["contract"] = contract
            context['customer'] = Customer.objects.filter(id=contract.customer_id).first().name
            
            context["documents"] = documents
            return render (request, 'contracts/admin_customer_contract_view.html', context)
        else:
            return redirect('login') 
    except Exception as e:
        context["error_messages"] = str(e)
        return render (request, 'contracts/admin_customer_contract_view.html', context)


# @login_required()
# def edit_admin_customer_contract(request, pk):
#     context = {}
#     try:
#         from apps.quickbooks_integration.views import create_item, update_item, get_item_data, refresh_quickbooks_token, get_quickbooks_accounts
#         from apps.quickbooks_integration.models import QuickBooksToken
#         success_url = reverse('edit-admin-customer-contract', kwargs={'pk': pk})
#         next_url = f"{success_url}"
#         redirect_url = f"{reverse('quickbooks_login')}?{urlencode({'next': next_url})}"

#         token_instance = QuickBooksToken.objects.first()
#         if not token_instance:
#             return redirect(redirect_url)
                                        
#         if token_instance.is_token_expired():
#             print("Token expired, refreshing...")
#             new_access_token = refresh_quickbooks_token(token_instance.refresh_token)
#             if not new_access_token:
#                 return redirect(redirect_url)
            
#             token_instance.access_token = new_access_token
#             token_instance.expires_at = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
#             token_instance.save()
#     except QuickBooksToken.DoesNotExist:
#         return redirect(redirect_url)
#     try:
#         contract = get_object_or_404(AdminCustomerContract, id=pk)     

#         customers = Customer.objects.filter(is_active=True).values('id', 'name').order_by('name')       

#         documents = AdminCustomerContractDocuments.objects.filter(contract=contract)        
#         crops = CustomerContractCropDetails.objects.filter(contract=contract)
#         crop_names = Crop.objects.all()
#         context = {
#             "contract": contract,
#             "customers": customers,
#             'selected_customer_id': contract.customer_id,  
#             'selected_contract_type': contract.contract_type,          
#             'crops': crops,    
#             "crop_names":crop_names,        
#             "contract_start_date": contract.contract_start_date,
#             "contract_period": contract.contract_period,
#             "status": contract.status,
#             "documents": documents,
#         }

#         if request.method == "POST":
#             if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_distributor or request.user.is_warehouse_manager:

#                 selected_customer = request.POST.get('selected_customer') 
#                 selected_contract_type = request.POST.get('contract_type')               
#                 contract_start_date = request.POST.get('contract_start_date')
#                 contract_period = request.POST.get('contract_period')
#                 status = request.POST.get('status')
                
#                 if selected_customer:                    
#                     customer = Customer.objects.filter(id=int(selected_customer)).first()  
#                     customer_name = customer.name                 

#                     if not customer:
#                         context["error_messages"] = "Selected customer does not exist."
#                         return render(request, 'contracts/edit_admin_customer_contract.html', context)

#                     contract.customer_id = customer.id  
#                     contract.customer_name = customer_name  
#                     contract.contract_type = selected_contract_type                
#                     contract.contract_start_date = contract_start_date
#                     contract.contract_period = contract_period
#                     contract.status = status
#                     contract.save()

#                     print(contract)
#                     crop_ids = request.POST.getlist("crop_id[]")
#                     crops = request.POST.getlist("crop[]")
#                     crop_types = request.POST.getlist("crop_type[]")
#                     contract_amounts = request.POST.getlist("contract_amount[]")
#                     amount_units = request.POST.getlist("amount_unit[]")
#                     per_unit_rates = request.POST.getlist("per_unit_rate[]")
#                     delete_flags = request.POST.getlist("delete_flag[]") 

#                     print(crop_ids, crops, crop_types, contract_amounts, amount_units, per_unit_rates)
#                     print("Length of crop_ids:", len(crop_ids))
#                     print("Length of crops:", len(crops))

#                     with transaction.atomic():
#                         for idx, crop_id in enumerate(crop_ids):
#                             if crop_id.isdigit() and delete_flags[idx] == "1":
#                                 try:
#                                     CustomerContractCropDetails.objects.get(id=int(crop_id)).delete()
#                                     print(f"Deleted crop with id {crop_id}")
#                                 except CustomerContractCropDetails.DoesNotExist:
#                                     print(f"Crop with id {crop_id} not found.")
#                             else:
#                                 print(f"Skipping crop with id {crop_id}, not marked for deletion.")

#                         for idx in range(len(crops)):
#                             crop_id = crop_ids[idx] if idx < len(crop_ids) else None

#                             if crop_id and crop_id.isdigit():
#                                 try:
#                                     crop_detail = CustomerContractCropDetails.objects.get(id=int(crop_id))
#                                     item = ShipmentItem.objects.filter(item_name=crop_detail.crop,item_type=crop_detail.crop_type,per_unit_price=crop_detail.per_unit_rate,type="Inventory").first()
#                                     crop_detail.crop = crops[idx]
#                                     crop_detail.crop_type = crop_types[idx]
#                                     crop_detail.contract_amount = contract_amounts[idx]
#                                     crop_detail.amount_unit = amount_units[idx]
#                                     crop_detail.per_unit_rate = per_unit_rates[idx]
#                                     crop_detail.save()

#                                     if crop_detail.crop_type != item.item_type  or float(crop_detail.per_unit_rate) != float(item.per_unit_price):
#                                         item_name = f"{crop_detail.crop}"
#                                         item_type = f"{crop_detail.crop_type}"
#                                         description = f"Crop: {crop_detail.crop}, Type: {crop_detail.crop_type}, Rate: {crop_detail.per_unit_rate} per unit"
#                                         item.item_name = item_name
#                                         item.item_type = item_type
#                                         item.per_unit_price = crop_detail.per_unit_rate
#                                         item.description = description
#                                         item.save()
#                                         try:                                      
#                                             accounts = get_quickbooks_accounts(token_instance.realm_id, token_instance.access_token)                                        
#                                             income_account_id = None
#                                             expense_account_id = None
#                                             asset_account_id = None

#                                             for account in accounts:
#                                                 if account.get("AccountType") == "Income" and account.get("AccountSubType") == "SalesOfProductIncome" and income_account_id is None:
#                                                     income_account_id = account.get("Id")
#                                                 elif (account.get("AccountType") == "Cost of Goods Sold" and account.get("AccountSubType") == "SuppliesMaterialsCogs" and expense_account_id is None):
#                                                     expense_account_id = account.get("Id")
#                                                 elif account.get("AccountType") in ["Other Current Asset", "Inventory Asset"] and account.get("AccountSubType") == "Inventory" and asset_account_id is None:
#                                                     asset_account_id = account.get("Id")

#                                                 if income_account_id and expense_account_id and asset_account_id:
#                                                     break

#                                             item_data = {
#                                                 "Name": f"{item.item_name}-{item.item_type}-{item.per_unit_price}",
#                                                 "Type": item.type,
#                                                 "UnitPrice": str(item.per_unit_price),
#                                                 "IncomeAccountRef": {
#                                                     "value": income_account_id,
#                                                 },
#                                                 "ExpenseAccountRef": {
#                                                     "value": expense_account_id,
#                                                 },
#                                                 "AssetAccountRef": {
#                                                     "value": asset_account_id,
#                                                 },
#                                                 "Description": item.description or "",
#                                                 "Active": item.is_active,
#                                                 "QtyOnHand":float(crop_detail.contract_amount),
#                                                 "TrackQtyOnHand":True,
#                                                 "InvStartDate": datetime.now().strftime('%Y-%m-%d')
#                                             }
                                            
#                                             item_id = item.quickbooks_id
#                                             item_details = get_item_data(item_id)
#                                             sync_token = item_details.get('Item', {}).get('SyncToken', '')
#                                             updated_item = update_item(token_instance.realm_id, token_instance.access_token, item_id, sync_token, item_data)                               
#                                             if updated_item:
#                                                 print("Item updated successfully and synced with QuickBooks.")
#                                                 messages.success(request, "Item updated successfully and synced with QuickBooks.")
#                                             else:
#                                                 print("Failed to update Item in QuickBooks.")
#                                                 messages.error(request, "Failed to update Item in QuickBooks.")

#                                         except ImproperlyConfigured as e:
#                                             print(str(e))
#                                     else:
#                                         pass
                                    
#                                 except CustomerContractCropDetails.DoesNotExist:
#                                     print(f"Crop with id {crop_id} not found.")
#                             else:
                               
#                                 crop = CustomerContractCropDetails.objects.create(
#                                     contract=contract,
#                                     crop=crops[idx],
#                                     crop_type=crop_types[idx],
#                                     contract_amount=contract_amounts[idx],
#                                     amount_unit=amount_units[idx],
#                                     per_unit_rate=per_unit_rates[idx]
#                                 )
#                                 item_name = f"{crop.crop}"
#                                 item_type = f"{crop.crop_type}"
#                                 description = f"Crop: {crop.crop}, Type: {crop.crop_type}, Rate: {crop.per_unit_rate} per unit"
                                
#                                 item, created = ShipmentItem.objects.update_or_create(
#                                     item_name=item_name,
#                                     item_type=item_type,
#                                     per_unit_price=crop.per_unit_rate,
#                                     defaults={
#                                         "description": description,
#                                         "type": "Inventory",
#                                         "is_active": True,
#                                     }
#                                 )
#                                 if created:
#                                     try:
#                                         accounts = get_quickbooks_accounts(token_instance.realm_id, token_instance.access_token)                                        
#                                         income_account_id = None
#                                         expense_account_id = None
#                                         asset_account_id = None

#                                         for account in accounts:
#                                             if account.get("AccountType") == "Income" and account.get("AccountSubType") == "SalesOfProductIncome" and income_account_id is None:
#                                                 income_account_id = account.get("Id")
#                                             elif (account.get("AccountType") == "Cost of Goods Sold" and account.get("AccountSubType") == "SuppliesMaterialsCogs" and expense_account_id is None):
#                                                 expense_account_id = account.get("Id")
#                                             elif account.get("AccountType") in ["Other Current Asset", "Inventory Asset"] and account.get("AccountSubType") == "Inventory" and asset_account_id is None:
#                                                 asset_account_id = account.get("Id")

#                                             if income_account_id and expense_account_id and asset_account_id:
#                                                 break

#                                         item_data = {
#                                             "Name": f"{item.item_name}-{item.item_type}-{item.per_unit_price}",
#                                             "Type": item.type,
#                                             "UnitPrice": str(item.per_unit_price),
#                                             "IncomeAccountRef": {
#                                                 "value": income_account_id,
#                                             },
#                                             "ExpenseAccountRef": {
#                                                 "value": expense_account_id,
#                                             },
#                                             "AssetAccountRef": {
#                                                 "value": asset_account_id,
#                                             },
#                                             "Description": item.description or "",
#                                             "Active": item.is_active,
#                                             "QtyOnHand":float(crop.contract_amount),
#                                             "TrackQtyOnHand":True,
#                                             "InvStartDate": datetime.now().strftime('%Y-%m-%d')
#                                         }                               
                                    
#                                         created_item = create_item(token_instance.realm_id, token_instance.access_token, item_data)                               
#                                         if created_item:
#                                             print("Item added successfully and synced with QuickBooks.")
#                                             messages.success(request, "Item added successfully and synced with QuickBooks.")
#                                         else:
#                                             print("Failed to sync with QuickBooks.")
#                                             messages.error(request, "Failed to add item in QuickBooks.")

#                                     except ImproperlyConfigured as e:
#                                         print(str(e))


#                     delete_document_ids = request.POST.getlist('delete_document_ids[]')
#                     print(delete_document_ids)
#                     for document_id in delete_document_ids:
#                         try:
#                             document = AdminCustomerContractDocuments.objects.get(id=document_id)
#                             document.delete() 
#                         except AdminCustomerContractDocuments.DoesNotExist:
#                             pass

#                     document_ids =  request.POST.getlist('document_ids')
#                     for document_id in document_ids:
#                         document_status = f'document_status_{document_id}'
#                         if document_status in request.POST:                            
#                             document_stat = request.POST.get(document_status)                         
                            
#                             document = AdminCustomerContractDocuments.objects.filter(id=document_id).first()
#                             document.document_status = document_stat  
#                             document.save()                                
                            
#                     document_names = request.POST.getlist('document_name[]')  
#                     if document_names:                     
#                         for i, name in enumerate(document_names):
                           
#                             if i < len(document_ids):
#                                 document_id = document_ids[i]
                                
#                                 document = AdminCustomerContractDocuments.objects.filter(id=document_id).first()
#                                 if document:
#                                     document.name = name 
#                                     document.save()
#                             else:
                               
#                                 AdminCustomerContractDocuments.objects.create(contract=contract, name=name)
                    
#                 return redirect('admin-customer-contract-list')
                        
#             elif request.user.is_customer:
#                 document_ids = request.POST.getlist('document_ids')        
#                 for document_id in document_ids:
#                     file_field_name = f'document_file_{document_id}'
                    
#                     if file_field_name in request.FILES:
#                         uploaded_file = request.FILES[file_field_name]                       
                        
#                         try:
#                             document = AdminCustomerContractDocuments.objects.get(id=document_id)
#                             document.document = uploaded_file  
#                             document.save()
                            
#                         except AdminCustomerContractDocuments.DoesNotExist:
                            
#                             pass
#                 contract.status = "Under Review"
#                 contract.save()
#                 return redirect('admin-customer-contract-list')
#         return render(request, 'contracts/edit_admin_customer_contract.html', context)
#     except Exception as e:
#         print(f"Exception occurred: {str(e)}")
#         context["error_messages"] = str(e)
#         return render(request, 'contracts/edit_admin_customer_contract.html', context)


@login_required()
def edit_admin_customer_contract(request, pk):
    context = {}
    try:
        contract = get_object_or_404(AdminCustomerContract, id=pk)    

        customers = Customer.objects.filter(is_active=True).values('id', 'name').order_by('name')       

        documents = AdminCustomerContractDocuments.objects.filter(contract=contract)        
        crops = CustomerContractCropDetails.objects.filter(contract=contract)
        crop_names = ShipmentItem.objects.all()
        context = {
            "contract": contract,
            "customers": customers,
            'selected_customer_id': contract.customer_id,  
            'selected_contract_type': contract.contract_type,          
            'crops': crops,    
            "crop_names":crop_names,        
            "contract_start_date": contract.contract_start_date,
            "contract_period": contract.contract_period,
            "status": contract.status,
            "documents": documents,
        }

        if request.method == "POST":
            if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_distributor or request.user.is_warehouse_manager:

                selected_customer = request.POST.get('selected_customer') 
                selected_contract_type = request.POST.get('contract_type')               
                contract_start_date = request.POST.get('contract_start_date')
                contract_period = request.POST.get('contract_period')
                status = request.POST.get('status')
                
                if selected_customer:                    
                    customer = Customer.objects.filter(id=int(selected_customer)).first()  
                    customer_name = customer.name                 

                    if not customer:
                        context["error_messages"] = "Selected customer does not exist."
                        return render(request, 'contracts/edit_admin_customer_contract.html', context)

                    contract.customer_id = customer.id  
                    contract.customer_name = customer_name  
                    contract.contract_type = selected_contract_type                
                    contract.contract_start_date = contract_start_date
                    contract.contract_period = contract_period
                    contract.status = status
                    contract.save()

                    print(contract)
                    crop_ids = request.POST.getlist("crop_id[]")
                    crops = request.POST.getlist("crop[]")
                    crop_types = request.POST.getlist("crop_type[]")
                    contract_amounts = request.POST.getlist("contract_amount[]")
                    amount_units = request.POST.getlist("amount_unit[]")
                    per_unit_rates = request.POST.getlist("per_unit_rate[]")
                    delete_flags = request.POST.getlist("delete_flag[]") 

                    with transaction.atomic():
                        for idx, crop_id in enumerate(crop_ids):
                            if crop_id.isdigit() and delete_flags[idx] == "1":
                                try:
                                    CustomerContractCropDetails.objects.get(id=int(crop_id)).delete()
                                    print(f"Deleted crop with id {crop_id}")
                                except CustomerContractCropDetails.DoesNotExist:
                                    print(f"Crop with id {crop_id} not found.")
                            else:
                                print(f"Skipping crop with id {crop_id}, not marked for deletion.")

                        for idx in range(len(crops)):
                            crop_id = crop_ids[idx] if idx < len(crop_ids) else None

                            if crop_id and crop_id.isdigit():
                                try:
                                    item_name = ShipmentItem.objects.filter(item=crops[idx]).first().item_name
                                    crop_detail = CustomerContractCropDetails.objects.get(id=int(crop_id))                                    
                                    crop_detail.crop = item_name
                                    crop_detail.crop_type = crop_types[idx]
                                    crop_detail.contract_amount = contract_amounts[idx]
                                    crop_detail.amount_unit = amount_units[idx]
                                    crop_detail.per_unit_rate = per_unit_rates[idx]
                                    crop_detail.save()                                    
                                    
                                except CustomerContractCropDetails.DoesNotExist:
                                    print(f"Crop with id {crop_id} not found.")
                            else:
                                item_name = ShipmentItem.objects.filter(item=crops[idx]).first().item_name
                                crop = CustomerContractCropDetails.objects.create(
                                    contract=contract,
                                    crop=item_name,
                                    crop_type=crop_types[idx],
                                    contract_amount=contract_amounts[idx],
                                    amount_unit=amount_units[idx],
                                    per_unit_rate=per_unit_rates[idx]
                                )

                    delete_document_ids = request.POST.getlist('delete_document_ids[]')
                    print(delete_document_ids)
                    for document_id in delete_document_ids:
                        try:
                            document = AdminCustomerContractDocuments.objects.get(id=document_id)
                            document.delete() 
                        except AdminCustomerContractDocuments.DoesNotExist:
                            pass

                    document_ids =  request.POST.getlist('document_ids')
                    for document_id in document_ids:
                        document_status = f'document_status_{document_id}'
                        if document_status in request.POST:                            
                            document_stat = request.POST.get(document_status)                         
                            
                            document = AdminCustomerContractDocuments.objects.filter(id=document_id).first()
                            document.document_status = document_stat  
                            document.save()                                
                            
                    document_names = request.POST.getlist('document_name[]')  
                    if document_names:                     
                        for i, name in enumerate(document_names):                           
                            if i < len(document_ids):
                                document_id = document_ids[i]
                                
                                document = AdminCustomerContractDocuments.objects.filter(id=document_id).first()
                                if document:
                                    document.name = name 
                                    document.save()
                            else:                               
                                AdminCustomerContractDocuments.objects.create(contract=contract, name=name)
                    
                return redirect('admin-customer-contract-list')
                        
            elif request.user.is_customer:
                document_ids = request.POST.getlist('document_ids')        
                for document_id in document_ids:
                    file_field_name = f'document_file_{document_id}'
                    
                    if file_field_name in request.FILES:
                        uploaded_file = request.FILES[file_field_name]                       
                        
                        try:
                            document = AdminCustomerContractDocuments.objects.get(id=document_id)
                            document.document = uploaded_file  
                            document.save()
                            
                        except AdminCustomerContractDocuments.DoesNotExist:
                            
                            pass
                contract.status = "Under Review"
                contract.save()
                return redirect('admin-customer-contract-list')
        return render(request, 'contracts/edit_admin_customer_contract.html', context)
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        context["error_messages"] = str(e)
        return render(request, 'contracts/edit_admin_customer_contract.html', context)


@login_required()
def export_admin_processor_contract(request):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            
            filename = 'AllProcessorContract.csv'
            response = HttpResponse(
                content_type='text/csv',
                headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
            )
            writer = csv.writer(response)
            
            writer.writerow(['CONTRACT ID','PROCESSOR NAME', 'PROCESSOR TYPE', 'CROP', 'AMOUNT',
                            'PER UNIT RATE', 'CONTRACT START DATE', 'CONTRACT PERIOD', 'CONTRACT END DATE','Status'])
            
            contracts = CropDetails.objects.all()
            for i in contracts:
                processor_type = i.contract.processor_type
                processor = None
                if processor_type == 'T1':
                    processor = Processor.objects.get(id=int(i.contract.processor_id))
                elif processor_type == 'T2' or processor_type == 'T3' or processor_type == 'T4':
                    processor = Processor2.objects.get(id=int(i.contract.processor_id))
                else:
                    pass
                if processor:
                    processor_name = processor.entity_name
                else:
                    processor_name = None
                writer.writerow([i.contract.secret_key, processor_name, processor_type, i.crop, i.contract_amount,
                                 i.per_unit_rate, i.contract.contract_start_date.date(), i.contract.contract_period , i.contract.end_date.date(), i.contract.status])
            return response
        else:
            messages.error(request, "Not a valid request.")
            return redirect("dashboard")   
    except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
        context["error_messages"] = str(e)
    return render(request, 'contracts/admin_processor_contract_list.html', context)


@login_required()
def export_admin_customer_contract(request):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            
            filename = 'AllCustomerContract.csv'
            response = HttpResponse(
                content_type='text/csv',
                headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
            )
            writer = csv.writer(response)
            
            writer.writerow(['CONTRACT ID','CUSTOMER NAME', 'CROP', 'AMOUNT',
                            'PER UNIT RATE', 'CONTRACT START DATE', 'CONTRACT PERIOD', 'CONTRACT END DATE','Status'])
            
            contracts = CustomerContractCropDetails.objects.all()
            for i in contracts:
                writer.writerow([i.contract.secret_key, i.contract.customer_name, i.crop, i.contract_amount,
                                 i.per_unit_rate, i.contract.contract_start_date.date(), i.contract.contract_period , i.contract.end_date.date(), i.contract.status])
            return response
        else:
            messages.error(request, "Not a valid request.")
            return redirect("dashboard")   
    except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
        context["error_messages"] = str(e)
    return render(request, 'contracts/admin_processor_contract_list.html', context)


@login_required()
def export_open_admin_processor_contracts(request):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            filename = 'OpenPurchaseContracts.csv'
            response = HttpResponse(
                content_type='text/csv',
                headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
            )
            writer = csv.writer(response)
            writer.writerow(['COMMODITY','CONTRACT ID', 'PROCESSOR NAME', 'INVENTORY',
                            'MONTH', 'RELEASED QUANTITY', 'UNIT', 'UNRELEASED QUANTITY', 'UNIT'])
            
            today_date = date.today()
            active_contracts = AdminProcessorContract.objects.filter(end_date__date__gte=today_date).exclude(
                status__in=['Completed', 'Terminated']
            )
            active_crops = CropDetails.objects.filter(contract__in=active_contracts)

            for crop in active_crops:
                active_months = crop.contract.get_active_months()

                net_sent_weight = 0
                is_first_row = False 
                from apps.warehouseManagement.models import ProcessorWarehouseShipment
                total_shipments = ProcessorWarehouseShipment.objects.filter(
                        contract=crop.contract                        
                    )
                if total_shipments.exists():
                    for shipment in total_shipments:                           
                        matching_crops = shipment.processor_shipment_crop.filter(crop=crop.crop, crop_type=crop.crop_type)
                        if matching_crops.exists(): 
                                                      
                            net_sent_weight += sum(matching_crop.net_weight for matching_crop in matching_crops)
                            
                for month in active_months:                    
                    date_obj = datetime.strptime(month, '%B %Y')
                    year, month_num = date_obj.year, date_obj.month
                    
                    shipments = ProcessorWarehouseShipment.objects.filter(
                        contract=crop.contract, 
                        date_pulled__year=year,
                        date_pulled__month=month_num
                    )
                    total_net_weight = 0  
                    
                    if shipments.exists():
                        is_first_row = True 
                        for shipment in shipments:                           
                            matching_crops = shipment.processor_shipment_crop.filter(crop=crop.crop, crop_type=crop.crop_type)
                            if matching_crops.exists(): 
                                                           
                                total_net_weight += sum(matching_crop.net_weight for matching_crop in matching_crops)
                                

                    remaining_amount = float(crop.contract_amount) - float(net_sent_weight)
                    writer.writerow([
                        crop.crop, 
                        crop.contract.secret_key, 
                        crop.contract.processor_entity_name, 
                        crop.crop_type,
                        month, 
                        total_net_weight, 
                        crop.amount_unit, 
                        remaining_amount if is_first_row else "", 
                        crop.amount_unit
                    ])
                    is_first_row = False
            return response

        else:
            messages.error(request, "Not a valid request.")
            return redirect("dashboard")   

    except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
        context["error_messages"] = str(e)
        return render(request, 'contracts/admin_processor_contract_list.html', context)


@login_required()
def export_completed_admin_processor_contracts(request):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            filename = 'CompletedPurchaseContracts.csv'
            response = HttpResponse(
                content_type='text/csv',
                headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
            )
            writer = csv.writer(response)
            writer.writerow(['COMMODITY','CONTRACT ID', 'PROCESSOR NAME', 'INVENTORY',
                            'MONTH', 'RELEASED QUANTITY', 'UNIT', 'UNRELEASED QUANTITY', 'UNIT'])
            
            today_date = date.today()
            completed_contracts = AdminProcessorContract.objects.filter(Q(end_date__date__lte=today_date)| Q(status__in=['Completed', 'Terminated']))
            
            completed_contracts_crops = CropDetails.objects.filter(contract__in=completed_contracts)

            for crop in completed_contracts_crops:
                active_months = crop.contract.get_active_months()

                net_sent_weight = 0
                is_first_row = False 
                from apps.warehouseManagement.models import ProcessorWarehouseShipment
                total_shipments = ProcessorWarehouseShipment.objects.filter(
                        contract=crop.contract                        
                    )
                if total_shipments.exists():
                    for shipment in total_shipments:                           
                        matching_crops = shipment.processor_shipment_crop.filter(crop=crop.crop, crop_type=crop.crop_type)
                        if matching_crops.exists(): 
                                                      
                            net_sent_weight += sum(matching_crop.net_weight for matching_crop in matching_crops)

                for month in active_months:
                    print(month)
                    date_obj = datetime.strptime(month, '%B %Y')
                    year, month_num = date_obj.year, date_obj.month
                    
                    shipments = ProcessorWarehouseShipment.objects.filter(
                        contract=crop.contract, 
                        date_pulled__year=year,
                        date_pulled__month=month_num
                    )
                    total_net_weight = 0  
                    
                    if shipments.exists():
                        is_first_row = True 
                        for shipment in shipments:                           
                            matching_crops = shipment.processor_shipment_crop.filter(crop=crop.crop, crop_type=crop.crop_type)
                            if matching_crops.exists():                             
                                total_net_weight += sum(matching_crop.net_weight for matching_crop in matching_crops)

                    remaining_amount = float(crop.contract_amount) - float(net_sent_weight)
                    writer.writerow([
                        crop.crop, 
                        crop.contract.secret_key, 
                        crop.contract.processor_entity_name, 
                        crop.crop_type,
                        month, 
                        total_net_weight, 
                        crop.amount_unit, 
                        remaining_amount if is_first_row else "", 
                        crop.amount_unit
                    ])
            return response

        else:
            messages.error(request, "Not a valid request.")
            return redirect("dashboard")   

    except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
        context["error_messages"] = str(e)
        return render(request, 'contracts/admin_processor_contract_list.html', context) 


@login_required()
def export_open_admin_customer_contracts(request):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            filename = 'OpenSalesContracts.csv'
            response = HttpResponse(
                content_type='text/csv',
                headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
            )
            writer = csv.writer(response)
            writer.writerow(['COMMODITY','CONTRACT ID', 'CUSTOMER NAME', 'INVENTORY',
                            'MONTH', 'RELEASED QUANTITY', 'UNIT', 'UNRELEASED QUANTITY', 'UNIT'])
            
            today_date = date.today()
            active_contracts = AdminCustomerContract.objects.filter(end_date__date__gte=today_date).exclude(
                status__in=['Completed', 'Terminated']
            )
            active_crops = CustomerContractCropDetails.objects.filter(contract__in=active_contracts)

            for crop in active_crops:
                active_months = crop.contract.get_active_months()

                net_sent_weight = 0
                is_first_row = False 
                from apps.warehouseManagement.models import WarehouseCustomerShipment
                total_shipments = WarehouseCustomerShipment.objects.filter(
                        contract=crop.contract                        
                    )
                if total_shipments.exists():
                    for shipment in total_shipments:                           
                        matching_crops = shipment.warehouse_shipment_crop.filter(crop=crop.crop, crop_type=crop.crop_type)
                        if matching_crops.exists(): 
                                                      
                            net_sent_weight += sum(matching_crop.net_weight for matching_crop in matching_crops)

                for month in active_months:
                    print(month)
                    date_obj = datetime.strptime(month, '%B %Y')
                    year, month_num = date_obj.year, date_obj.month

                    shipments = WarehouseCustomerShipment.objects.filter(
                        contract=crop.contract, 
                        date_pulled__year=year,
                        date_pulled__month=month_num
                    )
                    total_net_weight = 0  
                    
                    if shipments.exists():
                        for shipment in shipments: 
                            is_first_row = True                          
                            matching_crops = shipment.warehouse_shipment_crop.filter(crop=crop.crop, crop_type=crop.crop_type)
                            if matching_crops.exists():                             
                                total_net_weight += sum(matching_crop.net_weight for matching_crop in matching_crops)

                    remaining_amount = float(crop.contract_amount) - float(net_sent_weight)
                    writer.writerow([
                        crop.crop, 
                        crop.contract.secret_key, 
                        crop.contract.customer_name, 
                        crop.crop_type,
                        month, 
                        total_net_weight, 
                        crop.amount_unit, 
                        remaining_amount if is_first_row else "", 
                        crop.amount_unit
                    ])
            return response

        else:
            messages.error(request, "Not a valid request.")
            return redirect("dashboard")   

    except (ValueError, AttributeError, AdminCustomerContract.DoesNotExist) as e:
        context["error_messages"] = str(e)
        return render(request, 'contracts/admin_customer_contract_list.html', context)
  

@login_required()
def export_completed_admin_customer_contracts(request):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            filename = 'CompletedSalesContracts.csv'
            response = HttpResponse(
                content_type='text/csv',
                headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
            )
            writer = csv.writer(response)
            writer.writerow(['COMMODITY','CONTRACT ID', 'CUSTOMER NAME', 'INVENTORY',
                            'MONTH', 'RELEASED QUANTITY', 'UNIT', 'UNRELEASED QUANTITY', 'UNIT'])
            
            today_date = date.today()
            completed_contracts = AdminCustomerContract.objects.filter(Q(end_date__date__lte=today_date)| Q(status__in=['Completed', 'Terminated']))
            
            completed_contracts_crops = CustomerContractCropDetails.objects.filter(contract__in=completed_contracts)

            for crop in completed_contracts_crops:
                active_months = crop.contract.get_active_months()

                net_sent_weight = 0
                is_first_row = False 
                from apps.warehouseManagement.models import WarehouseCustomerShipment
                total_shipments = WarehouseCustomerShipment.objects.filter(
                        contract=crop.contract                        
                    )
                if total_shipments.exists():
                    for shipment in total_shipments:                           
                        matching_crops = shipment.warehouse_shipment_crop.filter(crop=crop.crop, crop_type=crop.crop_type)
                        if matching_crops.exists(): 
                                                      
                            net_sent_weight += sum(matching_crop.net_weight for matching_crop in matching_crops)

                for month in active_months:
                    print(month)
                    date_obj = datetime.strptime(month, '%B %Y')
                    year, month_num = date_obj.year, date_obj.month

                    shipments = WarehouseCustomerShipment.objects.filter(
                        contract=crop.contract, 
                        date_pulled__year=year,
                        date_pulled__month=month_num
                    )
                    total_net_weight = 0  
                    
                    if shipments.exists():
                        for shipment in shipments:   
                            is_first_row = True                        
                            matching_crops = shipment.warehouse_shipment_crop.filter(crop=crop.crop, crop_type=crop.crop_type)
                            if matching_crops.exists():                             
                                total_net_weight += sum(matching_crop.net_weight for matching_crop in matching_crops)

                    remaining_amount = float(crop.contract_amount) - float(net_sent_weight)
                    writer.writerow([
                        crop.crop, 
                        crop.contract.secret_key, 
                        crop.contract.customer_name, 
                        crop.crop_type,
                        month, 
                        total_net_weight, 
                        crop.amount_unit, 
                        remaining_amount if is_first_row else "", 
                        crop.amount_unit
                    ])
            return response

        else:
            messages.error(request, "Not a valid request.")
            return redirect("dashboard")   

    except (ValueError, AttributeError, AdminCustomerContract.DoesNotExist) as e:
        context["error_messages"] = str(e)
        return render(request, 'contracts/admin_customer_contract_list.html', context) 


def create_items(request):
    crops = CropDetails.objects.all()
    for crop in crops:
        item_name = f"{crop.crop}"
        item_type = f"{crop.crop_type}"
        description = f"Crop: {crop.crop}, Type: {crop.crop_type}, Rate: {crop.per_unit_rate} per unit"
        
        ShipmentItem.objects.update_or_create(
            item_name=item_name,
            item_type=item_type,
            per_unit_price=crop.per_unit_rate,
            defaults={
                "description": description,
                "type": "Inventory",
                "is_active": True,
            }
        )
    return HttpResponse(1)


def shipment_item_list(request):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        context = {}
        item_list = ShipmentItem.objects.all()        
        item_list = item_list.order_by('-id')
        paginator = Paginator(item_list, 100)
        page = request.GET.get('page')
        try:
            report = paginator.page(page)
        except PageNotAnInteger:
            report = paginator.page(1)
        except EmptyPage:
            report = paginator.page(paginator.num_pages)             
        context['items'] = report
        return render(request, 'contracts/shipment_item_list.html', context)
