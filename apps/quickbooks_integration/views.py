from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
import requests, os
from requests_oauthlib import OAuth2Session
from django.urls import reverse
from django.conf import settings
from quickbooks import QuickBooks
from apps.quickbooks_integration.models import *
from intuitlib.client import AuthClient
from quickbooks.objects.customer import Customer as CustomerModel
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
import json
import base64
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from apps.processor.models import Processor, ProcessorUser
from apps.processor2.models import Processor2, ProcessorUser2, ProcessorType
from apps.warehouseManagement.models import Customer , CustomerUser, ProcessorWarehouseShipment, WarehouseCustomerShipment, Invoice, PaymentForShipment, Purchase, PurchaseItem
from apps.contracts.models import ShipmentItem
from apps.accounts.models import User, Role
import traceback
from django.http import JsonResponse
from main.settings import BASE_DIR
from datetime import datetime
from oauthlib.oauth2 import TokenExpiredError
import logging
import time
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.db.models import Q
logger = logging.getLogger(__name__)

QUICKBOOKS_AUTHORIZATION_URL = "https://appcenter.intuit.com/connect/oauth2"
QUICKBOOKS_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

STATE_FILE_PATH = os.path.join(BASE_DIR, 'session.txt') 


def refresh_quickbooks_token(refresh_token):   
    client_id = settings.QUICKBOOKS_CLIENT_ID
    client_secret = settings.QUICKBOOKS_CLIENT_SECRET
    
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    url = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encoded_credentials}',
    }    
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    try:
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            token_data = response.json()
            new_access_token = token_data.get('access_token')
            new_refresh_token = token_data.get('refresh_token')
            
            token_instance = QuickBooksToken.objects.first()
            token_instance.access_token = new_access_token
            token_instance.refresh_token = new_refresh_token            
            expires_in = token_data.get('expires_in', 3600) 
            token_instance.update_expiry(expires_in)
            token_instance.save()
            return new_access_token
        else:
            logger.error(f"Failed to refresh token: {response.status_code} {response.text}")
        
            return initiate_quickbooks_login()
    except Exception as e:
        logger.error(f"Exception occurred while refreshing token: {e}")
        return None


def initiate_quickbooks_login():
    """
    Initiates the OAuth2 login flow by generating the authorization URL.
    If token refresh fails, this function will be called to log the user in again.
    """  
    qb = OAuth2Session(
        client_id=settings.QUICKBOOKS_CLIENT_ID,
        redirect_uri=settings.QUICKBOOKS_REDIRECT_URI,
        scope=settings.QUICKBOOKS_SCOPES
    )
    authorization_url, state = qb.authorization_url("https://appcenter.intuit.com/connect/oauth2")
    logger.info(f"Generated state: {state}")

    state_data = {"state": state, "next": "quickbooks_dashboard"}
    with open(STATE_FILE_PATH, 'w') as f:
        json.dump(state_data, f)

    logger.info(f"QuickBooks login required. Visit this URL to authorize: {authorization_url}")
    
    return authorization_url


def quickbooks_login(request):
    print("login function is called")
    
    qb = OAuth2Session(
        client_id=settings.QUICKBOOKS_CLIENT_ID,
        redirect_uri=settings.QUICKBOOKS_REDIRECT_URI,
        scope=settings.QUICKBOOKS_SCOPES
    )

    authorization_url, state = qb.authorization_url("https://appcenter.intuit.com/connect/oauth2")
    print("Generated state:", state)

    state_data = {"state": state, "next": "quickbooks_dashboard"}
    with open(STATE_FILE_PATH, 'w') as f:
        json.dump(state_data, f)

    return redirect(authorization_url)


def quickbooks_callback(request):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    try:
        with open(STATE_FILE_PATH, 'r') as f:
            state_data = json.load(f)
            state = state_data.get("state")            
            print("Read state from file:", state)
            print("Read next_url from file:", "quickbooks_dashboard")
    except FileNotFoundError:
        return HttpResponse("Error: 'oauth_state' file not found.")
    except json.JSONDecodeError:
        return HttpResponse("Error: Failed to decode JSON state file.")

    received_state = request.GET.get('state')
    if received_state != state:
        return HttpResponse("Error: State mismatch. CSRF Warning!")

    realm_id = request.GET.get('realmId')
    if not realm_id:
        return HttpResponse("Error: 'realmId' not found in the callback request.")

    qb = OAuth2Session(
        client_id=settings.QUICKBOOKS_CLIENT_ID,
        redirect_uri=settings.QUICKBOOKS_REDIRECT_URI,
        state=state
    )

    try:
        token = qb.fetch_token(
            "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
            authorization_response=request.build_absolute_uri(),
            client_secret=settings.QUICKBOOKS_CLIENT_SECRET
        )
        
        print("Token retrieved successfully:", token)

        quickbooks_token, created = QuickBooksToken.objects.update_or_create(
            realm_id=realm_id,
            defaults={
                'access_token': token['access_token'],
                'refresh_token': token['refresh_token'],
                'state': state,
                'created_at': timezone.now(),
                'expires_at': timezone.now() + timedelta(seconds=token.get('expires_in', 3600))
            }
        )

        if created:
            print("Created new QuickBooksToken instance.")
        else:
            print("Updated existing QuickBooksToken instance.")

        request.session["realmId"] = realm_id

        return redirect("quickbooks_dashboard")
    except Exception as e:
        print(f"Error retrieving token: {e}")
        return HttpResponse("Error during token exchange.")


def quickbooks_dashboard(request):
    realm_id = request.session.get('realmId')

    if not realm_id:
        return HttpResponse("Error: 'realmId' not found in request.")
    try:
        token_instance = QuickBooksToken.objects.get(realm_id=realm_id)
        access_token = token_instance.access_token 
    except QuickBooksToken.DoesNotExist:
        return redirect(reverse('quickbooks_login'))  
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }
    url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/companyinfo/{realm_id}'
    response = requests.get(url, headers=headers)
    company_info = response.json()  

    return render(request, 'quickbooks/dashboard.html', {'company_info': company_info})


def create_customer(realm_id, access_token, customer_data):
    url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/customer'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    
    response = requests.post(url, headers=headers, json=customer_data)
    
    if response.status_code in (200, 201):
        created_customer = response.json()
                   
        return created_customer 
    else:
        print(f"Error creating customer: {response.status_code} - {response.text}")
        return None


def get_customer_data(customer_id):
    try:
        token_instance = QuickBooksToken.objects.first()
        print(token_instance, "token", token_instance.expires_at)

        if not token_instance:
            print("No token found, redirecting to login...")
            return redirect(reverse('quickbooks_login'))

        if token_instance.is_token_expired():
            print("Token expired, refreshing...")            
            new_token_data = refresh_quickbooks_token(token_instance.refresh_token)          
            
            if not new_token_data:
                print("Token refresh failed, redirecting to login...")
                return redirect(reverse('quickbooks_login'))   
            time.sleep(2)        

    except QuickBooksToken.DoesNotExist:
        print("QuickBooksToken instance does not exist, redirecting to login...")
        return redirect(reverse('quickbooks_login'))

    try:        
        url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{token_instance.realm_id}/customer/{customer_id}"
        headers = {
            'Authorization': f'Bearer {token_instance.access_token}',
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            customer_data = response.json()
            return customer_data 
        else:
            print(f"Error fetching customer data: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"Exception occurred while fetching customer data: {e}")
        return None
 

def update_customer(realm_id, access_token, customer_id, sync_token, customer_data):
    print('update function called')
    """
    Update an existing customer's details in QuickBooks Online.
    """
    url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/customer'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    customer_data.update({
        "Id": str(customer_id),
        "SyncToken": str(sync_token)
    })

    response = requests.post(url, headers=headers, json=customer_data)

    if response.status_code in (200, 201):
        updated_customer = response.json()
        print("Customer updated successfully:", updated_customer)
        return updated_customer
    else:
        print(f"Error updating customer: {response.status_code} - {response.text}")
        return None


def create_vendor(realm_id, access_token, vendor_data):
    url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/vendor'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    
    response = requests.post(url, headers=headers, json=vendor_data)
    
    if response.status_code in (200, 201):
        created_vendor = response.json()                   
        return created_vendor 
    else:
        print(f"Error creating vendor: {response.status_code} - {response.text}")
        return None


def get_vendor_data(vendor_id):
    try:
        token_instance = QuickBooksToken.objects.first()
        print(token_instance, "token")

        if not token_instance:
            print("No token found, redirecting to login...")
            return redirect(reverse('quickbooks_login'))

        if token_instance.is_token_expired():
            print("Token expired, refreshing...")            
            new_token_data = refresh_quickbooks_token(token_instance.refresh_token)
            
            if not new_token_data:
                print("Token refresh failed, redirecting to login...")
                return redirect(reverse('quickbooks_login'))           

    except QuickBooksToken.DoesNotExist:
        print("QuickBooksToken instance does not exist, redirecting to login...")
        return redirect(reverse('quickbooks_login'))
    
    try:        
        url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{token_instance.realm_id}/vendor/{vendor_id}?minorversion=65"
        headers = {
            'Authorization': f'Bearer {token_instance.access_token}',
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            vendor_data = response.json()
            return vendor_data
        else:
            print(f"Error fetching vendor data: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"Exception occurred while fetching vendor data: {e}")
        return None
    
    
def update_vendor(realm_id, access_token, vendor_id, sync_token, vendor_data):
    url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/vendor?minorversion=73'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    vendor_data.update({
        "Id": str(vendor_id),
        "SyncToken": str(sync_token)
    })
    response = requests.post(url, headers=headers, json=vendor_data)

    if response.status_code == 200:
        updated_vendor = response.json()
        print("Vendor updated successfully:", updated_vendor)
        return updated_vendor
    else:
        print(f"Error updating vendor: {response.status_code} - {response.text}")
        return None


def create_invoice(realm_id, access_token, invoice_data):
    url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/invoice'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }    
    print(json.dumps(invoice_data, indent=4))
    response = requests.post(url, headers=headers, json=invoice_data)
    
    if response.status_code in (200, 201):
        created_invoice = response.json() 
        print("Invoice created successfully:")                        
        return created_invoice 
    else:
        print(f"Error creating invoice: {response.status_code} - {response.text}")      
        
        return None


def get_invoice_data(invoice_id):
    try:
        token_instance = QuickBooksToken.objects.first()
        print(token_instance, "token")

        if not token_instance:
            print("No token found, redirecting to login...")
            return redirect(reverse('quickbooks_login'))

        if token_instance.is_token_expired():
            print("Token expired, refreshing...")            
            new_token_data = refresh_quickbooks_token(token_instance.refresh_token)
            
            if not new_token_data:
                print("Token refresh failed, redirecting to login...")
                return redirect(reverse('quickbooks_login'))        

    except QuickBooksToken.DoesNotExist:
        print("QuickBooksToken instance does not exist, redirecting to login...")
        return redirect(reverse('quickbooks_login'))
    
    try:        
        url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{token_instance.realm_id}/invoice/{invoice_id}?minorversion=65'
        headers = {
            'Authorization': f'Bearer {token_instance.access_token}',
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            invoice_data = response.json()
            return invoice_data
        else:
            print(f"Error fetching invoice data: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"Exception occurred while fetching invoice data: {e}")
        return None


def update_invoice(realm_id, access_token, invoice_id, sync_token, invoice_data):
    url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/invoice?minorversion=73'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    invoice_data.update({
        "Id": str(invoice_id),
        "SyncToken": str(sync_token)
    })
    response = requests.post(url, headers=headers, json=invoice_data)

    if response.status_code == 200:
        updated_invoice = response.json()
        print("Invoice updated successfully:", updated_invoice)
        return updated_invoice
    else:
        print(f"Error updating invoice: {response.status_code} - {response.text}")
        return None


def create_item(realm_id, access_token, item_data):  
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/item?minorversion=73"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=json.dumps(item_data))

    if response.status_code in (200, 201):
        created_item = response.json()
        return created_item
    else:
        print(f"Error creating item: {response.status_code} - {response.text}")
        return None  


def get_item_data(item_id):
    try:
        token_instance = QuickBooksToken.objects.first()
        print(token_instance, "token")

        if not token_instance:
            print("No token found, redirecting to login...")
            return redirect(reverse('quickbooks_login'))

        if token_instance.is_token_expired():
            print("Token expired, refreshing...")            
            new_token_data = refresh_quickbooks_token(token_instance.refresh_token)
            
            if not new_token_data:
                print("Token refresh failed, redirecting to login...")
                return redirect(reverse('quickbooks_login'))

    except QuickBooksToken.DoesNotExist:
        print("QuickBooksToken instance does not exist, redirecting to login...")
        return redirect(reverse('quickbooks_login'))
    
    try:        
        url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{token_instance.realm_id}/item/{item_id}?minorversion=73'
        headers = {
            'Authorization': f'Bearer {token_instance.access_token}',
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            item_data = response.json()
            return item_data
        else:
            print(f"Error fetching item data: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"Exception occurred while fetching item data: {e}")
        return None


def update_item(realm_id, access_token, item_id, sync_token, item_data):
    url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/item?minorversion=73'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    item_data.update({
        "Id": str(item_id),
        "SyncToken": str(sync_token)
    })
    response = requests.post(url, headers=headers, json=item_data)

    if response.status_code == 200:
        updated_item = response.json()
        print("Item updated successfully:", updated_item)
        return updated_item
    else:
        print(f"Error updating item: {response.status_code} - {response.text}")
        return None


def create_purchase_order(realm_id, access_token, purchase_order_data):    
    url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/purchaseorder?minorversion=73'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        "Accept": "application/json",
        'Content-Type': 'application/json'
    } 
    print(json.dumps(purchase_order_data, indent=4))
    
    json_data = json.dumps(purchase_order_data)
    try:
        response = requests.post(url, headers=headers, data=json_data)

        if response.status_code in (200, 201):  
            created_purchase_order = response.json()  
            print(response.json())
            return created_purchase_order
        else:
            
            print(f"Error creating purchase order: {response.status_code} - {response.text}")
            return None
    except Exception as qb_error:
                        print(qb_error)


def get_purchase_order_data(purchase_order_id):
    try:
        token_instance = QuickBooksToken.objects.first()
        print(token_instance, "token")

        if not token_instance:
            print("No token found, redirecting to login...")
            return redirect(reverse('quickbooks_login'))

        if token_instance.is_token_expired():
            print("Token expired, refreshing...")            
            new_token_data = refresh_quickbooks_token(token_instance.refresh_token)
            
            if not new_token_data:
                print("Token refresh failed, redirecting to login...")
                return redirect(reverse('quickbooks_login'))

    except QuickBooksToken.DoesNotExist:
        print("QuickBooksToken instance does not exist, redirecting to login...")
        return redirect(reverse('quickbooks_login'))
    
    try:        
        url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{token_instance.realm_id}/purchaseorder/{purchase_order_id}?minorversion=73'
        headers = {
            'Authorization': f'Bearer {token_instance.access_token}',
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            purchase_data = response.json()
            return purchase_data
        else:
            print(f"Error fetching purchase order data: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"Exception occurred while fetching purchase order data: {e}")
        return None
# p = get_purchase_order_data(201)
# print(p)
def update_purchase_order(realm_id, access_token, purchase_order_id, purchase_order_data):
    url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/purchaseorder?minorversion=73'

    headers = {
        'Authorization': f'Bearer {access_token}',
        "Accept": "application/json",        
        'Content-Type': 'application/json'
    }    
    print(json.dumps(purchase_order_data, indent=4))
    
    json_data = json.dumps(purchase_order_data)
    response = requests.post(url, headers=headers, data=json_data)

    if response.status_code == 200:
        updated_purchase_order = response.json()
        print("Purchase order updated successfully:", updated_purchase_order)
        return updated_purchase_order
    else:
        print(f"Error updating purchase order: {response.status_code} - {response.text}")
        return None


def delete_purchase_order(realm_id, access_token, purchase_data):
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/purchaseorder?operation=delete&minorversion=73"

    headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
    try:
        response = requests.post(url, headers=headers, json=purchase_data)
        
        if response.status_code == 200:
            print('Successfully deleted purchase order')
            return response.json()
        else:
            print(f"Error deleting purchase order data: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None


def delete_invoice(realm_id, access_token, invoice_data):
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/invoice?operation=delete&minorversion=73"

    headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
    try:
        response = requests.post(url, headers=headers, json=invoice_data)
        
        if response.status_code == 200:
            print('Successfully deleted invoice')
            return response.json()
        else:
            print(f"Error deleting invoice: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None


def create_credit_memo(realm_id, access_token, credit_memo_data):
    url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/creditmemo?minorversion=65'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=credit_memo_data)

    if response.status_code in (200, 201):
        credit_memo = response.json()
        print("Credit memo created successfully:", credit_memo)
        return credit_memo
    else:
        print(f"Error creating credit memo: {response.status_code} - {response.text}")
        return None


def get_credit_memo_data(credit_memo_id):
    try:
        token_instance = QuickBooksToken.objects.first()
        print(token_instance, "token")

        if not token_instance:
            print("No token found, redirecting to login...")
            return redirect(reverse('quickbooks_login'))

        if token_instance.is_token_expired():
            print("Token expired, refreshing...")            
            new_token_data = refresh_quickbooks_token(token_instance.refresh_token)
            
            if not new_token_data:
                print("Token refresh failed, redirecting to login...")
                return redirect(reverse('quickbooks_login'))

    except QuickBooksToken.DoesNotExist:
        print("QuickBooksToken instance does not exist, redirecting to login...")
        return redirect(reverse('quickbooks_login'))
    
    try:        
        url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{token_instance.realm_id}/creditmemo/{credit_memo_id}?minorversion=65'
        headers = {
            'Authorization': f'Bearer {token_instance.access_token}',
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            credit_memo_data = response.json()
            return credit_memo_data
        else:
            print(f"Error fetching credit memo data: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception occurred while fetching credit memo data: {e}")
        return None


def update_credit_memo(realm_id, access_token, credit_memo_id, sync_token, credit_memo_data):
    url = f'https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/creditmemo?minorversion=65'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    credit_memo_data.update({
        "Id": str(credit_memo_id),
        "SyncToken": str(sync_token)
    })
    response = requests.post(url, headers=headers, data=credit_memo_data)

    if response.status_code == 200:
        updated_credit_memo = response.json()
        print("Credit memo updated successfully:", updated_credit_memo)
        return updated_credit_memo
    else:
        print(f"Error updating credit memo: {response.status_code} - {response.text}")
        return None


def get_quickbooks_accounts(realm_id, access_token):
    select_statement = "SELECT * FROM Account where Metadata.CreateTime > '2021-12-31'"
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/query?query={select_statement}&minorversion=73"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        print("Successfully fetched accounts.")
        return response.json().get("QueryResponse", {}).get("Account", [])
    else:        
        print(f"Error fetching accounts: {response.status_code} - {response.text}")
        return []


def get_tax_rates(realm_id, access_token):
    select_statement = "SELECT * FROM TaxRate"
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/query?query={select_statement}&minorversion=73"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/text'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('QueryResponse', {}).get('TaxRate', [])
    else:
        print(f"Error fetching tax rates: {response.status_code}")
        return None


def get_tax_codes(realm_id, access_token):
    select_statement = "SELECT * FROM TaxCode"
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/query?query={select_statement}&minorversion=73"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/text'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('QueryResponse', {}).get('TaxCode', [])
    else:
        print(f"Error fetching tax rates: {response.status_code}")
        return None
    

def create_payment(realm_id, access_token, payment_data):
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/payment"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }   
    
    response = requests.post(url, json=payment_data, headers=headers)

    if response.status_code in (200, 201):
        created_payment = response.json()
        print("Payment created successfully:", created_payment)
        return created_payment
    else:
        print(f"Error creating payment: {response.status_code} - {response.text}")
        return None


def get_payment_data(payment_id):
    try:
        token_instance = QuickBooksToken.objects.first()
        if not token_instance:
            return redirect(reverse('quickbooks_login'))

        if token_instance.is_token_expired():
            print("Token expired, refreshing...")
            new_access_token = refresh_quickbooks_token(token_instance.refresh_token)
            if not new_access_token:
                return redirect(reverse('quickbooks_login'))
            token_instance.access_token = new_access_token
            token_instance.expires_at = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
            token_instance.save()
    except QuickBooksToken.DoesNotExist:
        return redirect(reverse('quickbooks_login'))
    try:
        url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{token_instance.realm_id}/payment/{payment_id}"
        headers = {
            "Authorization": f"Bearer {token_instance.access_token}",
            "Accept": "application/json",
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            payment_data = response.json()
            return payment_data
        else:
            print(f"Error fetching payment data: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception occurred while fetching payment data: {e}")
        return None


def get_chart_of_accounts(realm_id, access_token):
    
    select_statement = "SELECT * FROM Account WHERE AccountType='Accounts Payable' AND AccountSubType='AccountsPayable'"
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/query?query={select_statement}&minorversion=73"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
   
    if response.status_code == 200:
        print("Successfully fetched accounts.")
        
        return response.json().get("QueryResponse", {}).get("Account", [])
    else:        
        print(f"Error fetching accounts: {response.status_code} - {response.text}")
        return []


def get_tax_agencies(realm_id, access_token):
    select_statement = "SELECT * FROM TaxAgency"
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/query?query={select_statement}&minorversion=73"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:       
        print("Successfully fetched tax agencies.")
        
        return response.json().get("QueryResponse", {}).get("TaxAgency", [])
    else:        
        print(f"Error fetching tax agencies: {response.status_code} - {response.text}")
        return []


def create_custom_tax_rate(realm_id, access_token, tax_rate_data):
    print('function called')
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/taxservice/taxcode?minorversion=73"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept":"application/json",
        "Content-Type": "application/json"
    }   
    response = requests.post(url, headers=headers, json=tax_rate_data)
    
    if response.status_code == 200:
        print("Successfully created custom tax rate.")
        return response.json()
    else:
        print(f"Error creating tax rate: {response.status_code} - {response.text}")
        return None  


@csrf_exempt
def quickbooks_webhook_request(request):
    print('Received webhook request...')  
    try:
        token_instance = QuickBooksToken.objects.first()
        print(token_instance, "token", token_instance.expires_at)

        if not token_instance:
            print("No token found, redirecting to login...")
            return redirect(reverse('quickbooks_login'))

        if token_instance.is_token_expired():
            print("Token expired, refreshing...")            
            new_token_data = refresh_quickbooks_token(token_instance.refresh_token)          
            
            if not new_token_data:
                print("Token refresh failed, redirecting to login...")
                return redirect(reverse('quickbooks_login'))          

    except QuickBooksToken.DoesNotExist:
        print("QuickBooksToken instance does not exist, redirecting to login...")
        return redirect(reverse('quickbooks_login')) 
    
    if request.method == 'POST':
        try:           
            data = json.loads(request.body)
            print("Parsed JSON data: ", data)
            event_notifications = data.get('eventNotifications', [])

            for event in event_notifications:
                for entity in event.get('dataChangeEvent', {}).get('entities', []):
                    if entity.get('name') == 'Customer' and entity.get('operation') == 'Create':

                        customer_id = entity.get('id')
                        print(f"Customer ID received: {customer_id}")

                        full_customer_data = get_customer_data(customer_id)
                        if not full_customer_data:
                            print("Unable to fetch customer data from QuickBooks")
                            return JsonResponse({'error': 'Unable to fetch customer data from QuickBooks'}, status=400)

                        customer_email = full_customer_data.get('Customer', {}).get('PrimaryEmailAddr', {}).get('Address', '')
                        customer_name = full_customer_data.get('Customer', {}).get('DisplayName', '')
                        bill_address = full_customer_data.get('Customer', {}).get('BillAddr', {})
                        bill_addr = ', '.join(filter(None, [
                            bill_address.get('Line1', ''),
                            bill_address.get('Line2', ''),
                            bill_address.get('City', ''),
                            bill_address.get('CountrySubDivisionCode', ''),
                            bill_address.get('PostalCode', '')
                        ]))

                        ship_address = full_customer_data.get('Customer', {}).get('ShipAddr', {})
                        ship_addr = ', '.join(filter(None, [
                            ship_address.get('Line1', ''),
                            ship_address.get('Line2', ''),
                            ship_address.get('City', ''),
                            ship_address.get('CountrySubDivisionCode', ''),
                            ship_address.get('PostalCode', '')
                        ]))
                        taxable = full_customer_data.get('Customer', {}).get('Taxable', False)
                        sales_term = full_customer_data.get('Customer', {}).get('SalesTermRef', {}).get('value', 30)
                        tax_rate = full_customer_data.get('Customer', {}).get('DefaultTaxCodeRef', {}).get('value', 0)

                        if Customer.objects.filter(name=customer_name).exists():
                            print(f"Customer with {customer_name} already exists. Skipping creation.")
                            customer = Customer.objects.filter(name=customer_name).first()
                            customer.quickbooks_id = customer_id
                            customer.save()

                        else:                       
                            customer = Customer.objects.create(
                                quickbooks_id=customer_id,
                                name=customer_name,
                                billing_address=bill_addr,
                                shipping_address=ship_addr,
                                credit_terms=sales_term,
                                is_tax_payable=taxable,
                                tax_percentage=tax_rate,
                                location=bill_addr
                            )
                            print("Customer successfully created in Django database.")
                            from apps.warehouseManagement.views import generate_random_password
                            password = generate_random_password()

                            user_name = full_customer_data.get('Customer', {}).get('GivenName', customer_name)
                            user_phone = full_customer_data.get('Customer', {}).get('PrimaryPhone', {}).get('FreeFormNumber', '')
                            user_fax = full_customer_data.get('Customer', {}).get('Fax', {}).get('FreeFormNumber', '')

                            customer_user = CustomerUser.objects.create(
                                customer=customer,
                                contact_name=user_name,
                                contact_email=customer_email,
                                contact_phone=user_phone,
                                contact_fax=user_fax,
                                p_password_raw=password
                            )
                            user = User.objects.create(
                                email=customer_email,
                                username=customer_email,
                                first_name=user_name,
                            )
                            customer_role = Role.objects.get(role='Customer')
                            user.role.add(customer_role)

                            user.is_customer = True
                            user.is_active = True
                            user.set_password(password)
                            user.password_raw = password  
                            user.save()

                            print("Customer user and role successfully created.")

                    elif entity.get('name') == 'Customer' and entity.get('operation') == 'Update':
                        customer_id = entity.get('id')
                        print(f"Customer ID received: {customer_id}")
                        full_customer_data = get_customer_data(customer_id)
                     
                        if not full_customer_data:
                            print("Unable to fetch customer data from QuickBooks")
                            return JsonResponse({'error': 'Unable to fetch customer data from QuickBooks'}, status=400)
                        
                        customer_email = full_customer_data.get('Customer', {}).get('PrimaryEmailAddr', {}).get('Address', '')
                        customer_name = full_customer_data.get('Customer', {}).get('DisplayName', '')
                        bill_address = full_customer_data.get('Customer', {}).get('BillAddr', {})
                        bill_addr = ', '.join(filter(None, [
                            bill_address.get('Line1', ''),
                            bill_address.get('Line2', ''),
                            bill_address.get('City', ''),
                            bill_address.get('CountrySubDivisionCode', ''),
                            bill_address.get('PostalCode', '')
                        ]))
                        
                        ship_address = full_customer_data.get('Customer', {}).get('ShipAddr', {})
                        ship_addr = ', '.join(filter(None, [
                            ship_address.get('Line1', ''),
                            ship_address.get('Line2', ''),
                            ship_address.get('City', ''),
                            ship_address.get('CountrySubDivisionCode', ''),
                            ship_address.get('PostalCode', '')
                        ]))
                        taxable = full_customer_data.get('Customer', {}).get('Taxable', False)
                        sales_term = full_customer_data.get('Customer', {}).get('SalesTermRef', {}).get('value', 30)
                        tax_rate = full_customer_data.get('Customer', {}).get('DefaultTaxCodeRef', {}).get('value', 0)
                        is_active = full_customer_data.get('Customer', {}).get('Active', True)
                        user_name = full_customer_data.get('Customer', {}).get('GivenName', customer_name)
                        user_phone = full_customer_data.get('Customer', {}).get('PrimaryPhone', {}).get('FreeFormNumber', '')
                        user_fax = full_customer_data.get('Customer', {}).get('Fax', {}).get('FreeFormNumber', '')

                        if Customer.objects.filter(Q(quickbooks_id=customer_id) | Q(name=customer_name)).exists():
                            customer = Customer.objects.filter(Q(quickbooks_id=customer_id) | Q(name=customer_name)).first()
                            customer_user = CustomerUser.objects.filter(customer=customer).first()                            
                            user = User.objects.filter(email=customer_user.contact_email).first()

                            customer.name = customer_name
                            customer.billing_address = bill_addr
                            customer.shipping_address = ship_addr
                            customer.is_active = is_active
                            customer.is_tax_payable = taxable
                            customer.tax_percentage = tax_rate
                            customer.quickbooks_id = customer_id
                            customer.location = bill_addr
                            customer.save()
                            
                            customer_user.contact_name = user_name
                            customer_user.contact_email = customer_email
                            customer_user.contact_phone = user_phone
                            customer_user.contact_fax = user_fax
                            customer_user.save()

                            user.email = customer_email
                            user.username = customer_email
                            user.first_name = user_name
                            user.save()

                            print("Customer and Customer user successfully updated.") 
                        else:
                            customer = Customer.objects.create(
                            quickbooks_id=customer_id,
                            name=customer_name,
                            billing_address=bill_addr,
                            shipping_address=ship_addr,
                            credit_terms=sales_term,
                            is_tax_payable=taxable,
                            tax_percentage=tax_rate,
                            location=bill_addr
                            )
                            print("Customer successfully created in Django database.")
                            from apps.warehouseManagement.views import generate_random_password
                            password = generate_random_password()

                            customer_user = CustomerUser.objects.create(
                                customer=customer,
                                contact_name=user_name,
                                contact_email=customer_email,
                                contact_phone=user_phone,
                                contact_fax=user_fax,
                                p_password_raw=password
                            )
                            user = User.objects.create(
                                email=customer_email,
                                username=customer_email,
                                first_name=user_name,
                            )
                            customer_role = Role.objects.get(role='Customer')
                            user.role.add(customer_role)

                            user.is_customer = True
                            user.is_active = True
                            user.set_password(password)
                            user.password_raw = password  
                            user.save()

                            print("Customer user and role successfully created.")

                    elif entity.get('name') == 'Vendor' and entity.get('operation') == 'Create':
                        vendor_id = entity.get('id')
                        print(f"Vendor ID received: {vendor_id}")

                        full_vendor_data = get_vendor_data(vendor_id)
                        if not full_vendor_data:
                            print("Unable to fetch vendor data from QuickBooks")
                            return JsonResponse({'error': 'Unable to fetch vendor data from QuickBooks'}, status=400)
                        
                        processor_email = full_vendor_data.get('Vendor', {}).get('PrimaryEmailAddr', {}).get('Address', '')
                        entity_name = full_vendor_data.get('Vendor', {}).get('DisplayName', '')
                        website = full_vendor_data.get('Vendor', {}).get('WebAddr', {}).get('URI', '')
                        phone_number = full_vendor_data.get('Vendor', {}).get('PrimaryPhone', {}).get('FreeFormNumber', '')
                        
                        vendor_type = full_vendor_data.get('Vendor', {}).get('Suffix', '')
                        bill_address = full_vendor_data.get('Vendor', {}).get('BillAddr', {})
                        bill_addr = ', '.join(filter(None, [
                            bill_address.get('Line1', ''),
                            bill_address.get('Line2', ''),
                            bill_address.get('City', ''),
                            bill_address.get('CountrySubDivisionCode', ''),
                            bill_address.get('PostalCode', '')
                        ]))
                        account_no = full_vendor_data.get('Vendor', {}).get('AcctNum', '')

                        if vendor_type == "T1":
                            if Processor.objects.filter(Q(quickbooks_id=vendor_id) | Q(entity_name=entity_name)).exists():
                                processor = Processor.objects.filter(Q(quickbooks_id=vendor_id) | Q(entity_name=entity_name)).first()
                                processor_user = ProcessorUser.objects.filter(processor=processor).first()
                                user = User.objects.filter(email=processor_user.contact_email).first()

                                processor.quickbooks_id = vendor_id                    
                                processor.entity_name=entity_name
                                processor.main_email=processor_email
                                processor.main_number=phone_number
                                processor.billing_address=bill_addr
                                processor.shipping_address=bill_addr
                                processor.website=website
                                processor.account_number=account_no
                                processor.save()

                                processor_user.contact_name=entity_name
                                processor_user.contact_email=processor_email
                                processor_user.contact_phone=phone_number
                                processor_user.save()
                                
                                user.email = processor_email
                                user.username = processor_email
                                user.first_name = entity_name
                                user.save()
                            
                            else:
                                processor = Processor(
                                    quickbooks_id=vendor_id,
                                    entity_name=entity_name,
                                    main_email=processor_email,
                                    main_number=phone_number,
                                    billing_address=bill_addr,
                                    shipping_address=bill_addr,
                                    website=website,
                                    account_number=account_no
                                )
                                processor.save()

                                from apps.processor.views import generate_random_password
                                password = generate_random_password()
                                processor_user = ProcessorUser(
                                    processor=processor,
                                    contact_name=entity_name,
                                    contact_email=processor_email,
                                    contact_phone=phone_number,
                                    p_password_raw=password
                                )
                                processor_user.save()

                                user = User.objects.create(email=processor_email, username=processor_email,first_name=entity_name)
                                user.role.add(Role.objects.get(role='Processor'))
                                user.is_processor=True
                                user.is_active=True
                                user.set_password(password)
                                user.password_raw = password
                                user.save()
                                print("Vendor successfully created in Django database.")
                        else: 
                            if Processor2.objects.filter(Q(quickbooks_id=vendor_id) | Q(entity_name=entity_name)).exists():
                                processor = Processor2.objects.filter(Q(quickbooks_id=vendor_id) | Q(entity_name=entity_name)).first()
                                processor_user = ProcessorUser2.objects.filter(processor2=processor).first()
                                user = User.objects.filter(email=processor_user.contact_email).first()

                                processor.quickbooks_id = vendor_id                    
                                processor.entity_name=entity_name
                                processor.main_email=processor_email
                                processor.main_number=phone_number
                                processor.billing_address=bill_addr
                                processor.shipping_address=bill_addr
                                processor.website=website
                                processor.account_number=account_no
                                processor.save()

                                processor_user.contact_name=entity_name
                                processor_user.contact_email=processor_email
                                processor_user.contact_phone=phone_number
                                processor_user.save()
                                
                                user.email = processor_email
                                user.username = processor_email
                                user.first_name = entity_name
                                user.save()                        
                                
                            else:
                                processor = Processor2(
                                    quickbooks_id=vendor_id,
                                    entity_name=entity_name,
                                    main_email=processor_email,
                                    main_number=phone_number,
                                    billing_address=bill_addr,
                                    shipping_address=bill_addr,
                                    website=website,
                                    account_number=account_no
                                )
                                processor.save()

                                from apps.processor.views import generate_random_password
                                password = generate_random_password()
                                processor_user = ProcessorUser2(
                                    processor2=processor,
                                    contact_name=entity_name,
                                    contact_email=processor_email,
                                    contact_phone=phone_number,
                                    p_password_raw=password
                                )
                                processor_user.save()
                                user = User.objects.create(email=processor_email, username=processor_email,first_name=entity_name)
                                user.role.add(Role.objects.get(role='Processor'))
                                user.is_processor2=True
                                user.is_active=True
                                user.set_password(password)
                                user.password_raw = password
                                user.save()
                                check_type = ProcessorType.objects.filter(id=vendor_type).first()
                                processor.processor_type.add(check_type)
                                print("Vendor successfully created in Django database.")
                        
                    elif entity.get('name') == 'Vendor' and entity.get('operation') == 'Update':
                        vendor_id = entity.get('id')
                        print(f"Vendor ID received: {vendor_id}")

                        full_vendor_data = get_vendor_data(vendor_id)
                        if not full_vendor_data:
                            print("Unable to fetch vendor data from QuickBooks")
                            return JsonResponse({'error': 'Unable to fetch vendor data from QuickBooks'}, status=400)
                        
                        processor_email = full_vendor_data.get('Vendor', {}).get('PrimaryEmailAddr', {}).get('Address', '')
                        entity_name = full_vendor_data.get('Vendor', {}).get('DisplayName', '')
                        website = full_vendor_data.get('Vendor', {}).get('WebAddr', {}).get('URI', '')
                        phone_number = full_vendor_data.get('Vendor', {}).get('PrimaryPhone', {}).get('FreeFormNumber', '')
                        
                        vendor_type = full_vendor_data.get('Vendor', {}).get('Suffix', '')
                        bill_address = full_vendor_data.get('Vendor', {}).get('BillAddr', {})
                        bill_addr = ', '.join(filter(None, [
                            bill_address.get('Line1', ''),
                            bill_address.get('Line2', ''),
                            bill_address.get('City', ''),
                            bill_address.get('CountrySubDivisionCode', ''),
                            bill_address.get('PostalCode', '')
                        ]))
                        is_active = full_vendor_data.get('Vendor', {}).get('Active', True)
                        account_no = full_vendor_data.get('Vendor', {}).get('AcctNum', '')

                        if vendor_type == "T1":
                            if Processor.objects.filter(Q(quickbooks_id=vendor_id) | Q(entity_name=entity_name)).exists():
                                processor = Processor.objects.filter(Q(quickbooks_id=vendor_id) | Q(entity_name=entity_name)).first()  
                                processor_user = ProcessorUser.objects.filter(processor=processor).first()
                                user = User.objects.filter(email=processor_user.contact_email).first()

                                processor.entity_name = entity_name
                                processor.main_email = processor_email
                                processor.main_number = phone_number
                                processor.website = website
                                processor.billing_address = bill_addr  
                                processor.is_active = is_active 
                                processor.account_number = account_no  
                                processor.quickbooks_id = vendor_id                          
                                processor.save()
                                print('Vendor updated successfully.')

                                processor_user.contact_name=entity_name
                                processor_user.contact_email=processor_email
                                processor_user.contact_phone=phone_number
                                processor_user.save()
                                
                                user.email = processor_email
                                user.username = processor_email
                                user.first_name = entity_name
                                user.save()  
                            
                            else:
                                processor = Processor(
                                    quickbooks_id=vendor_id,
                                    entity_name=entity_name,
                                    main_email=processor_email,
                                    main_number=phone_number,
                                    billing_address=bill_addr,
                                    shipping_address=bill_addr,
                                    website=website,
                                    account_number=account_no
                                )
                                processor.save()  

                                from apps.processor.views import generate_random_password
                                password = generate_random_password()
                                processor_user = ProcessorUser(
                                    processor=processor,
                                    contact_name=entity_name,
                                    contact_email=processor_email,
                                    contact_phone=phone_number,
                                    p_password_raw=password
                                )
                                processor_user.save()
                                user = User.objects.create(email=processor_email, username=processor_email,first_name=entity_name)
                                user.role.add(Role.objects.get(role='Processor'))
                                user.is_processor=True
                                user.is_active=True
                                user.set_password(password)
                                user.password_raw = password
                                user.save()                              
                                print("Vendor successfully created in Django database.")

                        else:
                            if Processor2.objects.filter(Q(quickbooks_id=vendor_id) | Q(entity_name=entity_name)).exists():
                                processor = Processor2.objects.filter(Q(quickbooks_id=vendor_id) | Q(entity_name=entity_name)).first()
                                processor_user = ProcessorUser2.objects.filter(processor2=processor).first()
                                user = User.objects.filter(email=processor_user.contact_email).first()
                            
                                processor.entity_name = entity_name
                                processor.main_email = processor_email
                                processor.main_number = phone_number
                                processor.website = website
                                processor.billing_address = bill_addr
                                processor.is_active = is_active
                                processor.account_number = account_no
                                processor.quickbooks_id = vendor_id
                                processor.save()
                                print('Vendor updated successfully.')

                                processor_user.contact_name=entity_name
                                processor_user.contact_email=processor_email
                                processor_user.contact_phone=phone_number
                                processor_user.save()
                                
                                user.email = processor_email
                                user.username = processor_email
                                user.first_name = entity_name
                                user.save()  
                            else:
                                processor = Processor2(
                                    quickbooks_id=vendor_id,
                                    entity_name=entity_name,
                                    main_email=processor_email,
                                    main_number=phone_number,
                                    billing_address=bill_addr,
                                    shipping_address=bill_addr,
                                    website=website,
                                    account_number=account_no
                                )
                                processor.save()

                                from apps.processor.views import generate_random_password
                                password = generate_random_password()
                                processor_user = ProcessorUser2(
                                    processor2=processor,
                                    contact_name=entity_name,
                                    contact_email=processor_email,
                                    contact_phone=phone_number,
                                    p_password_raw=password
                                )
                                processor_user.save()

                                user = User.objects.create(email=processor_email, username=processor_email,first_name=entity_name)
                                user.role.add(Role.objects.get(role='Processor'))
                                user.is_processor2=True
                                user.is_active=True
                                user.set_password(password)
                                user.password_raw = password
                                user.save()
                                check_type = ProcessorType.objects.filter(id=vendor_type).first()
                                processor.processor_type.add(check_type)
                                print("Vendor successfully created in Django database.")

                    elif entity.get('name') == 'Invoice' and entity.get('operation') == 'Create':
                        invoice_id = entity.get('id')
                        print(f"Invoice ID received: {invoice_id}")

                        full_invoice_data = get_invoice_data(invoice_id)
                        if not full_invoice_data:
                            print("Unable to fetch invoice data from QuickBooks")
                            return JsonResponse({'error': 'Unable to fetch invoice data from QuickBooks'}, status=400)
                        
                        customer_id = full_invoice_data.get('Invoice', {}).get('CustomerRef', {}).get('value', '')
                        customer = Customer.objects.filter(quickbooks_id=customer_id).first()
                        # custom_fields = full_invoice_data.get('Invoice', {}).get('CustomField', [])
                        # for field in custom_fields:
                        #     if field.get('Name') == "InvoiceRef":
                        #         shipment_invoice_id = field.get('StringValue')
                        #         break
                        invoice_number = full_invoice_data.get('Invoice', {}).get('DocNumber','')
                        shipment_invoice_id = full_invoice_data.get('Invoice', {}).get('ShipTrackingNumber','')
                        total_amount = full_invoice_data.get('Invoice', {}).get('TotalAmt', '')
                        tax_amount = full_invoice_data.get('Invoice', {}).get('TxnTaxDetail', {}).get('TotalTax', '')
                        due_date = full_invoice_data.get('Invoice', {}).get('DueDate', '')
                        item_amount = float(total_amount) - float(tax_amount)

                        if ProcessorWarehouseShipment.objects.filter(invoice_id=shipment_invoice_id).exists():
                            shipment = ProcessorWarehouseShipment.objects.filter(invoice_id=shipment_invoice_id, customer_id=customer.id).first()
                            if Invoice.objects.filter(customer=customer, processor_shipment=shipment, shipment_invoice_id=shipment.invoice_id).exists():
                                invoice = Invoice.objects.filter(customer=customer, processor_shipment=shipment, shipment_invoice_id=shipment.invoice_id).first()
                                invoice.quickbooks_id = invoice_id
                                invoice.invoice_number = invoice_number
                                invoice.save()
                            else:
                                invoice = Invoice(
                                    processor_shipment=shipment,
                                    customer=customer,
                                    quickbooks_id=invoice_id,
                                    shipment_invoice_id=shipment_invoice_id,
                                    invoice_number = invoice_number,
                                    total_amount=total_amount,
                                    item_amount=item_amount,
                                    due_date=due_date,
                                    tax_amount=tax_amount
                                )                                
                                invoice.save() 

                            shipment.invoice_approval = True
                            shipment.approval_time = timezone.now()
                            shipment.tax_amount = tax_amount
                            shipment.product_payment_amount = item_amount
                            shipment.total_payment = total_amount
                            shipment.save()                         

                        if WarehouseCustomerShipment.objects.filter(invoice_id=shipment_invoice_id).exists():
                            shipment = WarehouseCustomerShipment.objects.filter(invoice_id=shipment_invoice_id, customer_id=customer.id).first()
                            if Invoice.objects.filter(customer=customer, warehouse_shipment=shipment, shipment_invoice_id=shipment.invoice_id).exists():
                                invoice = Invoice.objects.filter(customer=customer, warehouse_shipment=shipment, shipment_invoice_id=shipment.invoice_id).first()
                                invoice.quickbooks_id = invoice_id
                                invoice.invoice_number = invoice_number
                                invoice.save()
                            else:
                                invoice = Invoice(
                                    warehouse_shipment=shipment,
                                    customer=customer,
                                    quickbooks_id=invoice_id,
                                    shipment_invoice_id=shipment_invoice_id,
                                    invoice_number = invoice_number,
                                    total_amount=total_amount,
                                    item_amount=item_amount,
                                    due_date=due_date,
                                    tax_amount = tax_amount
                                )
                                invoice.save()
                                
                            shipment.invoice_approval = True
                            shipment.approval_time = timezone.now()
                            shipment.tax_amount = tax_amount
                            shipment.product_payment_amount = item_amount
                            shipment.total_payment = total_amount
                            shipment.save()

                    elif entity.get('name') == 'Invoice' and entity.get('operation') == 'Update':
                        invoice_id = entity.get('id')
                        print(f"Invoice ID received: {invoice_id}")

                        full_invoice_data = get_invoice_data(invoice_id)
                        if not full_invoice_data:
                            print("Unable to fetch invoice data from QuickBooks")
                            return JsonResponse({'error': 'Unable to fetch invoice data from QuickBooks'}, status=400)
                        
                        customer_id = full_invoice_data.get('Invoice', {}).get('CustomerRef', {}).get('value', '')
                        customer = Customer.objects.filter(quickbooks_id=customer_id).first()

                        # custom_fields = full_invoice_data.get('Invoice', {}).get('CustomField', [])
                        # for field in custom_fields:
                        #     if field.get('Name') == "InvoiceRef":
                        #         shipment_invoice_id = field.get('StringValue')
                        #         break

                        shipment_invoice_id = full_invoice_data.get('Invoice', {}).get('ShipTrackingNumber','')
                        total_amount = full_invoice_data.get('Invoice', {}).get('TotalAmt', '')
                        tax_amount = full_invoice_data.get('Invoice', {}).get('TxnTaxDetail', {}).get('TotalTax', '')
                        due_date = full_invoice_data.get('Invoice', {}).get('DueDate', '')
                        item_amount = float(total_amount) - float(tax_amount)

                        if Invoice.objects.filter(Q(quickbooks_id=invoice_id) | Q(shipment_invoice_id=shipment_invoice_id)).exists():
                            invoice = Invoice.objects.filter(Q(quickbooks_id=invoice_id) | Q(shipment_invoice_id=shipment_invoice_id)).first()
                            invoice.total_amount = total_amount
                            invoice.item_amount = item_amount
                            invoice.tax_amount = tax_amount
                            invoice.due_date = due_date
                            invoice.shipment_invoice_id = shipment_invoice_id
                            invoice.invoice_number = invoice_number
                            invoice.quickbooks_id = invoice_id
                            invoice.save()
                        else:
                            if WarehouseCustomerShipment.objects.filter(invoice_id=shipment_invoice_id).exists():
                                shipment = WarehouseCustomerShipment.objects.filter(invoice_id=shipment_invoice_id, customer_id=customer.id).first()
                                invoice = Invoice(
                                    warehouse_shipment=shipment,
                                    customer=customer,
                                    quickbooks_id=invoice_id,
                                    shipment_invoice_id=shipment_invoice_id,
                                    invoice_number = invoice_number,
                                    total_amount=total_amount,
                                    item_amount=item_amount,
                                    due_date=due_date,
                                    tax_amount = tax_amount
                                )
                                invoice.save()

                                shipment.invoice_approval = True
                                shipment.approval_time = timezone.now()
                                shipment.tax_amount = tax_amount
                                shipment.product_payment_amount = item_amount
                                shipment.total_payment = total_amount
                                shipment.save()
                                
                            else:
                                shipment = ProcessorWarehouseShipment.objects.filter(invoice_id=shipment_invoice_id, customer_id=customer.id).first()
                                invoice = Invoice(
                                    processor_shipment=shipment,
                                    customer=customer,
                                    quickbooks_id=invoice_id,
                                    shipment_invoice_id=shipment_invoice_id,
                                    invoice_number = invoice_number,
                                    total_amount=total_amount,
                                    item_amount=item_amount,
                                    due_date=due_date,
                                    tax_amount = tax_amount
                                )
                                invoice.save()

                                shipment.invoice_approval = True
                                shipment.approval_time = timezone.now()
                                shipment.tax_amount = tax_amount
                                shipment.product_payment_amount = item_amount
                                shipment.total_payment = total_amount
                                shipment.save()
                    
                    elif entity.get('name') == 'Invoice' and entity.get('operation') == 'Delete':
                        invoice_id = entity.get('id')
                        print(f"Delete operation detected for Invoice ID: {invoice_id}")

                        invoice = Invoice.objects.filter(quickbooks_id=invoice_id).first()
                        if invoice:
                            shipment_invoice_id = invoice.shipment_invoice_id
                            customer_id = invoice.customer_id

                            invoice.delete()
                            print(f"Invoice with ID {invoice_id} and number {shipment_invoice_id} deleted from the system.")
                            
                            processor_shipment_exists = ProcessorWarehouseShipment.objects.filter(invoice_id=shipment_invoice_id).exists()
                            customer_shipment_exists = WarehouseCustomerShipment.objects.filter(invoice_id=shipment_invoice_id).exists()

                            if processor_shipment_exists:
                                shipment = ProcessorWarehouseShipment.objects.filter(invoice_id=shipment_invoice_id, customer_id=customer_id).first()
                                shipment.invoice_approval = False
                                shipment.save()

                            if customer_shipment_exists:
                                shipment = WarehouseCustomerShipment.objects.filter(invoice_id=shipment_invoice_id, customer_id=customer_id).first()
                                shipment.invoice_approval = False
                                shipment.save()

                            return JsonResponse({'message': 'Invoice and related records deleted successfully'}, status=200)
                        else:
                            print("Invoice not found for deletion.")
                            return JsonResponse({'error': 'Invoice not found'}, status=404)
                    
                    elif entity.get('name') == 'PurchaseOrder' and entity.get('operation') == 'Create':
                        purchase_order_id = entity.get('id')
                        print(f"PurchaseOrder ID received: {purchase_order_id}")

                        full_purchase_order_data = get_purchase_order_data(purchase_order_id)
                        if not full_purchase_order_data:
                            print("Unable to fetch purchase order data from QuickBooks")
                            return JsonResponse({'error': 'Unable to fetch purchase order data from QuickBooks'}, status=400)
                       
                        processor_name = full_purchase_order_data.get('PurchaseOrder', {}).get('VendorRef', {}).get('name', '')
                        custom_fields = full_purchase_order_data.get('PurchaseOrder', {}).get('CustomField', [])
                        total_amount = full_purchase_order_data.get('PurchaseOrder', {}).get('TotalAmt', '')
                        all_line_items_details = []

                        line_items = full_purchase_order_data.get('PurchaseOrder', {}).get('Line', [])
                        if line_items:
                            for line_item in line_items:                                
                                quantity = line_item.get('ItemBasedExpenseLineDetail', {}).get('Qty', '')
                                per_unit_rate = line_item.get('ItemBasedExpenseLineDetail', {}).get('UnitPrice', '')
                                item_name = line_item.get('ItemBasedExpenseLineDetail', {}).get('ItemRef', {}).get('name', '')
                                item_id = line_item.get('ItemBasedExpenseLineDetail', {}).get('ItemRef', {}).get('value', '')
                                description = line_item.get('Description', '')
                                amount = line_item.get('Amount', '')

                                all_line_items_details.append({
                                    'item_name': item_name,
                                    'item_id': item_id,
                                    'quantity': quantity,
                                    'per_unit_rate': per_unit_rate,
                                    'description': description,
                                    'amount': amount,
                                    'line_item': line_item
                                })
                        currency = full_purchase_order_data.get('PurchaseOrder', {}).get('CurrencyRef', {}).get('value', '')

                        for field in custom_fields:
                            if field.get('Name') == "ShipmentId":
                                shipment_id = field.get('StringValue')
                                break

                        if Purchase.objects.filter(processor_entity_name=processor_name, shipment__shipment_id=shipment_id).exists():
                            purchase = Purchase.objects.filter(processor_entity_name=processor_name, shipment__shipment_id=shipment_id).first()
                            print('Purchase order already exists. Skipping creation.')
                            purchase.quickbooks_id = purchase_order_id                            
                            purchase.currency = currency
                            purchase.save() 
                            purchase_items = PurchaseItem.objects.filter(purchase=purchase)
                            if purchase_items:
                                for item in purchase_items:
                                    for i in all:
                                        item.item_name=all_line_items_details[i]["item_name"]
                                        item.item_id=all_line_items_details[i]["item_id"]
                                        item.quantity=all_line_items_details[i]["quantity"]
                                        item.per_unit_rate=all_line_items_details[i]["per_unit_rate"]
                                        item.amount=all_line_items_details[i]["amount"]
                                        item.description=all_line_items_details[i]["description"]
                            else:
                                for item in all_line_items_details:
                                    PurchaseItem.objects.create(
                                        purchase=purchase,
                                        item_name=item["item_name"],
                                        item_id=item["item_id"],
                                        quantity=item["quantity"],
                                        amount=item["amount"],
                                        per_unit_price=item["per_unit_price"],
                                        description=item["description"]
                                        )                            
                        else:                            
                            shipment = ProcessorWarehouseShipment.objects.filter(shipment_id=shipment_id).first()
                            if shipment:
                                purchase= Purchase(
                                    shipment=shipment,
                                    processor_entity_name=shipment.processor_entity_name,
                                    processor_id=shipment.processor_id,
                                    processor_type=shipment.processor_type,
                                    quickbooks_id=purchase_order_id,
                                    currency=currency                                    
                                )
                                purchase.save()
                                for item in all_line_items_details:
                                    PurchaseItem.objects.create(
                                        purchase=purchase,
                                        item_name=item["item_name"],
                                        item_id=item["item_id"],
                                        quantity=item["quantity"],
                                        amount=item["amount"],
                                        per_unit_price=item["per_unit_price"],
                                        description=item["description"]
                                        )
                           
                    elif entity.get('name') == 'PurchaseOrder' and entity.get('operation') == 'Update':
                        purchase_order_id = entity.get('id')
                        print(f"PurchaseOrder ID received: {purchase_order_id}")

                        full_purchase_order_data = get_purchase_order_data(purchase_order_id)
                        if not full_purchase_order_data:
                            print("Unable to fetch purchase order data from QuickBooks")
                            return JsonResponse({'error': 'Unable to fetch purchase order data from QuickBooks'}, status=400)
                        
                        processor_name = full_purchase_order_data.get('PurchaseOrder', {}).get('VendorRef', {}).get('name', '')
                        custom_fields = full_purchase_order_data.get('PurchaseOrder', {}).get('CustomField', [])
                        total_amount = full_purchase_order_data.get('PurchaseOrder', {}).get('TotalAmt', '')
                        
                        all_line_items_details = []

                        line_items = full_purchase_order_data.get('PurchaseOrder', {}).get('Line', [])
                        if line_items:
                            for line_item in line_items:                                
                                quantity = line_item.get('ItemBasedExpenseLineDetail', {}).get('Qty', '')
                                per_unit_rate = line_item.get('ItemBasedExpenseLineDetail', {}).get('UnitPrice', '')
                                item_name = line_item.get('ItemBasedExpenseLineDetail', {}).get('ItemRef', {}).get('name', '')
                                item_id = line_item.get('ItemBasedExpenseLineDetail', {}).get('ItemRef', {}).get('value', '')
                                description = line_item.get('Description', '')
                                amount = line_item.get('Amount', '')

                                all_line_items_details.append({
                                    'item_name': item_name,
                                    'item_id': item_id,
                                    'quantity': quantity,
                                    'per_unit_rate': per_unit_rate,
                                    'description': description,
                                    'amount': amount,
                                    'line_item': line_item
                                })

                        currency = full_purchase_order_data.get('PurchaseOrder', {}).get('CurrencyRef', {}).get('value', '')

                        for field in custom_fields:
                            if field.get('Name') == "ShipmentId":
                                shipment_id = field.get('StringValue')
                                break
                        
                        if Purchase.objects.filter(processor_entity_name=processor_name, shipment__shipment_id=shipment_id, quickbooks_id=purchase_order_id).exists():
                            purchase = Purchase.objects.filter(processor_entity_name=processor_name, shipment__shipment_id=shipment_id, quickbooks_id=purchase_order_id).first()
                            print('Purchase order already exists. Skipping creation.')
                            purchase.quickbooks_id = purchase_order_id                            
                            purchase.currency = currency
                            purchase.save() 
                            purchase_items = PurchaseItem.objects.filter(purchase=purchase)
                            if purchase_items:
                                for item in purchase_items:
                                    for i in all:
                                        item.item_name=all_line_items_details[i]["item_name"]
                                        item.item_id=all_line_items_details[i]["item_id"]
                                        item.quantity=all_line_items_details[i]["quantity"]
                                        item.per_unit_rate=all_line_items_details[i]["per_unit_rate"]
                                        item.amount=all_line_items_details[i]["amount"]
                                        item.description=all_line_items_details[i]["description"]
                            else:
                                for item in all_line_items_details:
                                    PurchaseItem.objects.create(
                                        purchase=purchase,
                                        item_name=item["item_name"],
                                        item_id=item["item_id"],
                                        quantity=item["quantity"],
                                        amount=item["amount"],
                                        per_unit_price=item["per_unit_price"],
                                        description=item["description"]
                                        )
                            
                        else:                            
                            shipment = ProcessorWarehouseShipment.objects.filter(shipment_id=shipment_id).first()
                            if shipment:
                                purchase= Purchase(
                                    shipment=shipment,
                                    processor_entity_name=shipment.processor_entity_name,
                                    processor_id=shipment.processor_id,
                                    processor_type=shipment.processor_type,
                                    quickbooks_id=purchase_order_id,
                                    currency=currency                                    
                                )
                                purchase.save()
                                for item in all_line_items_details:
                                    PurchaseItem.objects.create(
                                        purchase=purchase,
                                        item_name=item["item_name"],
                                        item_id=item["item_id"],
                                        quantity=item["quantity"],
                                        amount=item["amount"],
                                        per_unit_price=item["per_unit_price"],
                                        description=item["description"]
                                        )              
                       
                    elif entity.get('name') == 'PurchaseOrder' and entity.get('operation') == 'Delete':
                        purchase_order_id = entity.get('id')
                        print(f"PurchaseOrder ID received: {purchase_order_id}")

                        full_purchase_order_data = get_purchase_order_data(purchase_order_id)
                        if not full_purchase_order_data:
                            print("Unable to fetch purchase order data from QuickBooks")
                            return JsonResponse({'error': 'Unable to fetch purchase order data from QuickBooks'}, status=400)
                        
                        processor_name = full_purchase_order_data.get('PurchaseOrder', {}).get('VendorRef', {}).get('name', '')
                        custom_fields = full_purchase_order_data.get('PurchaseOrder', {}).get('CustomField', [])
                        for field in custom_fields:
                            if field.get('Name') == "ShipmentId":
                                shipment_id = field.get('StringValue')
                                break
                        
                        purchase = Purchase.objects.filter(processor_entity_name=processor_name, shipment__shipment_id=shipment_id, quickbooks_id=purchase_order_id).first()
                        if purchase:
                            purchase.delete()
                        
                    elif entity.get('name') == 'Item' and entity.get('operation') == 'Create':
                        item_id = entity.get('id')
                        print(f"Item ID received: {item_id}")

                        full_item_data = get_item_data(item_id)
                        if not full_item_data:
                            print("Unable to fetch item data from QuickBooks")
                            return JsonResponse({'error': 'Unable to fetch item data from QuickBooks'}, status=400)
                        
                        item_name_ = full_item_data.get('Item', {}).get('Name', '')
                        type = full_item_data.get('Item', {}).get('Type', '')
                        per_unit_price = full_item_data.get('Item', {}).get('UnitPrice', '')
                        description = full_item_data.get('Item', {}).get('Description', '')
                        is_active = full_item_data.get('Item', {}).get('Active', True) 

                        class_ref = full_item_data.get('Item', {}).get('ClassRef', {})
                        class_name = class_ref.get('name', 'No Class')
                        class_id = class_ref.get('value', 'No Class ID')                       

                        name = class_name.upper()                       
                        item = f'{name}-{item_name_}'
                        if ShipmentItem.objects.filter(item=item).exists():
                            
                            print(f"ShipmentItem already exists. Skipping creation.")
                            shipment_item = ShipmentItem.objects.filter(item=item_name_).first()
                            shipment_item.item = item
                            shipment_item.quickbooks_id = item_id
                            shipment_item.item_name= name
                            shipment_item.item_type = item_name_
                            shipment_item.type=type
                            shipment_item.per_unit_price=per_unit_price
                            shipment_item.description=description
                            shipment_item.is_active=is_active
                            shipment_item.save()
                             
                        else:
                            shipment_item = ShipmentItem(
                                quickbooks_id=item_id,
                                item=item,    
                                item_name= name,
                                item_type = item_name_,                          
                                per_unit_price=per_unit_price,
                                type= type,
                                description=description,
                                is_active=is_active
                            )
                            shipment_item.save()
                                                
                    elif entity.get('name') == 'Item' and entity.get('operation') == 'Update':
                        item_id = entity.get('id')
                        print(f"Item ID received: {item_id}")

                        full_item_data = get_item_data(item_id)
                        if not full_item_data:
                            print("Unable to fetch item data from QuickBooks")
                            return JsonResponse({'error': 'Unable to fetch item data from QuickBooks'}, status=400)
                        
                        item_name_ = full_item_data.get('Item', {}).get('Name', '')
                        type = full_item_data.get('Item', {}).get('Type', '')
                        per_unit_price = full_item_data.get('Item', {}).get('UnitPrice', '')
                        description = full_item_data.get('Item', {}).get('Description', '')
                        is_active = full_item_data.get('Item', {}).get('Active', True)

                        class_ref = full_item_data.get('Item', {}).get('ClassRef', {})
                        class_name = class_ref.get('name', 'No Class')
                        class_id = class_ref.get('value', 'No Class ID')                       

                        name = class_name.upper()
                        item = f'{name}-{item_name_}'
                        shipment_item = ShipmentItem.objects.filter(Q(quickbooks_id=item_id) | Q(item=item)).first()
                        if shipment_item: 
                            shipment_item.item = item
                            shipment_item.quickbooks_id = item_id
                            shipment_item.item_name= name
                            shipment_item.item_type = item_name_
                            shipment_item.type=type
                            shipment_item.per_unit_price=per_unit_price
                            shipment_item.description=description
                            shipment_item.is_active=is_active
                            shipment_item.save()
                        else:
                            shipment_item = ShipmentItem(
                                quickbooks_id=item_id,
                                item=item,    
                                item_name= name,
                                item_type = item_name_,                          
                                per_unit_price=per_unit_price,
                                type= type,
                                description=description,
                                is_active=is_active
                            )
                            shipment_item.save()

                    elif entity.get('name') == 'CreditMemo' and entity.get('operation') == 'Create':
                        credit_memo_id = entity.get('id')
                        print(f"Credit memo ID received: {credit_memo_id}")

                        full_credit_memo_data = get_credit_memo_data(credit_memo_id)
                        if not full_credit_memo_data:
                            print("Unable to fetch credit memo data from QuickBooks")
                            return JsonResponse({'error': 'Unable to fetch credit memo data from QuickBooks'}, status=400)
                        
                    elif entity.get('name') == 'CreditMemo' and entity.get('operation') == 'Update':
                        credit_memo_id = entity.get('id')
                        print(f"Credit memo ID received: {credit_memo_id}")

                        full_credit_memo_data = get_credit_memo_data(credit_memo_id)
                        if not full_credit_memo_data:
                            print("Unable to fetch credit memo data from QuickBooks")
                            return JsonResponse({'error': 'Unable to fetch credit memo data from QuickBooks'}, status=400)

                    # elif entity.get('name') == 'Payment' and entity.get('operation') == 'Create':
                    #     payment_id = entity.get('id')
                    #     print(f"Payment ID received: {payment_id}")

                    #     full_payment_data = get_payment_data(payment_id)
                    #     if not full_payment_data:
                    #         print("Unable to fetch payment data from QuickBooks")
                    #         return JsonResponse({'error': 'Unable to fetch payment data from QuickBooks'}, status=400)
                        
                    #     line_items = full_payment_data.get('Payment', {}).get('Line', [])
                    #     invoice_id = None

                    #     for line_item in line_items:
                    #         linked_txns = line_item.get('LinkedTxn', [])
                    #         for txn in linked_txns:
                    #             if txn.get('TxnType') == 'Invoice':
                    #                 invoice_id = txn.get('TxnId')
                    #                 break
                    #     unapplied_amount = full_payment_data.get('Payment', {}).get('UnappliedAmt', 0)
                    #     total_amount = full_payment_data.get('Payment', {}).get('TotalAmt', 0)
                    #     linked_txns = full_payment_data.get('Payment', {}).get('Line', [])[0].get('LinkedTxn', [])

                    #     is_payment_successful = False

                    #     if unapplied_amount == 0 and total_amount > 0:
                    #         is_payment_successful = True

                    #     if linked_txns:
                    #         is_payment_successful = True
                        
                    #     if invoice_id:
                    #         invoice = Invoice.objects.filter(quickbooks_id=invoice_id).first()
                    #         invoice.payment_status = 'paid' if is_payment_successful == True else 'unpaid'
                    #         payment = PaymentForShipment.objects.filter(invoice_id=invoice.shipment_invoice_id).first()
                    #         payment.status = is_payment_successful
                    #         payment.quickbooks_id = payment_id
                    #         payment.save()
                    #     else:
                    #         print("No associated invoice found for this payment.")

            return JsonResponse({'status': 'success'}, status=200)
        except Exception as e:
            print(f"Error processing webhook: {e}")
            print(traceback.format_exc()) 
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=400)


def get_all_vendor_data(realm_id, access_token):    
    select_statement = "SELECT * FROM Vendor"
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/query?query={select_statement}&minorversion=73"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return

    vendor_data = response.json()
    vendors = vendor_data.get("QueryResponse", {}).get("Vendor", [])
    
    return vendors


def get_all_customer_data(realm_id, access_token):
    select_statement = "SELECT * FROM Customer"
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/query?query={select_statement}&minorversion=73"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return

    customer_data = response.json()
    customers = customer_data.get("QueryResponse", {}).get("Customer", [])

    return customers


def get_all_item_data(realm_id, access_token):
    select_statement = "SELECT * FROM Item"
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/query?query={select_statement}&minorversion=73"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return

    item_data = response.json()
    items = item_data.get("QueryResponse", {}).get("Item", [])

    return items


def get_all_invoice_data(realm_id, access_token):
    select_statement = "SELECT * FROM Invoice"
    url = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{realm_id}/query?query={select_statement}&minorversion=73"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return

    invoice_data = response.json()
    invoices = invoice_data.get("QueryResponse", {}).get("Invoice", [])

    for full_invoice_data in invoices:
        invoice_id = full_invoice_data.get('Id', '')
        customer_id = full_invoice_data.get('CustomerRef', {}).get('value', '')
        customer = Customer.objects.filter(quickbooks_id=customer_id).first()
        # custom_fields = full_invoice_data.get('Invoice', {}).get('CustomField', [])
        # for field in custom_fields:
        #     if field.get('Name') == "InvoiceRef":
        #         shipment_invoice_id = field.get('StringValue')
        #         break

        shipment_invoice_id = full_invoice_data.get('ShipTrackingNumber','')
        total_amount = full_invoice_data.get('TotalAmt', '')
        tax_amount = full_invoice_data.get('TxnTaxDetail', {}).get('TotalTax', '')
        due_date = full_invoice_data.get('DueDate', '')
        item_amount = float(total_amount) - float(tax_amount)

        if ProcessorWarehouseShipment.objects.filter(invoice_id=shipment_invoice_id).exists():
            shipment = ProcessorWarehouseShipment.objects.filter(invoice_id=shipment_invoice_id, customer_id=customer.id).first()
            if Invoice.objects.filter(customer=customer, processor_shipment=shipment, shipment_invoice_id=shipment.invoice_id).exists():
                invoice = Invoice.objects.filter(customer=customer, processor_shipment=shipment, shipment_invoice_id=shipment.invoice_id).first()
                invoice.quickbooks_id = invoice_id
                invoice.save()
            else:
                invoice = Invoice(
                    processor_shipment=shipment,
                    customer=customer,
                    quickbooks_id=invoice_id,
                    shipment_invoice_id=shipment_invoice_id,
                    total_amount=total_amount,
                    item_amount=item_amount,
                    due_date=due_date,
                    tax_amount=tax_amount
                )                                
                invoice.save()                           

        if WarehouseCustomerShipment.objects.filter(invoice_id=shipment_invoice_id).exists():
            shipment = WarehouseCustomerShipment.objects.filter(invoice_id=shipment_invoice_id, customer_id=customer.id).first()
            if Invoice.objects.filter(customer=customer, warehouse_shipment=shipment, shipment_invoice_id=shipment.invoice_id).exists():
                invoice = Invoice.objects.filter(customer=customer, warehouse_shipment=shipment, shipment_invoice_id=shipment.invoice_id).first()
                invoice.quickbooks_id = invoice_id
                invoice.save()
            else:
                invoice = Invoice(
                    warehouse_shipment=shipment,
                    customer=customer,
                    quickbooks_id=invoice_id,
                    shipment_invoice_id=shipment_invoice_id,
                    total_amount=total_amount,
                    item_amount=item_amount,
                    due_date=due_date,
                    tax_amount = tax_amount
                )
                invoice.save()
                
        shipment.invoice_approval = True
        shipment.approval_time = timezone.now()
        shipment.tax_amount = tax_amount
        shipment.product_payment_amount = item_amount
        shipment.total_payment = total_amount
        shipment.save()
        print(full_invoice_data)
    return invoices


def get_all_purchase_order_data(realm_id, access_token):
    select_statement = "SELECT * FROM PurchaseOrder"
    url = f"https://quickbooks.api.intuit.com/v3/company/{realm_id}/query?query={select_statement}&minorversion=73"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)    
    if response.status_code != 200:
        print(f"Error: {response.status_code}, {response.text}")
        return

    purchase_order_data = response.json()
    purchase_orders = purchase_order_data.get("QueryResponse", {}).get("PurchaseOrder", [])
    for full_purchase_order_data in purchase_orders:
        print(full_purchase_order_data)
    return purchase_orders


def vendor_list(request):
    context = {}
    try:
        token_instance = QuickBooksToken.objects.first()
        print(token_instance, "token", token_instance.expires_at)

        if not token_instance:
            print("No token found, redirecting to login...")
            return redirect(reverse('quickbooks_login'))

        if token_instance.is_token_expired():
            print("Token expired, refreshing...")            
            new_token_data = refresh_quickbooks_token(token_instance.refresh_token)          
            
            if not new_token_data:
                print("Token refresh failed, redirecting to login...")
                return redirect(reverse('quickbooks_login'))          

    except QuickBooksToken.DoesNotExist:
        print("QuickBooksToken instance does not exist, redirecting to login...")
        return redirect(reverse('quickbooks_login'))
    
    realm_id = QuickBooksToken.objects.first().realm_id
    access_token = QuickBooksToken.objects.first().access_token
    raw_vendor_list = get_all_vendor_data(realm_id, access_token)
    vendor_list = []
    for full_vendor_data in raw_vendor_list:        
        suffix = full_vendor_data.get("Suffix", "")
        if suffix:  
            vendor = {
                "id": full_vendor_data.get("Id", ""),
                "email": full_vendor_data.get("PrimaryEmailAddr", {}).get("Address", ""),
                "name": full_vendor_data.get("DisplayName", ""),
                "website": full_vendor_data.get("WebAddr", {}).get("URI", ""),
                "phone": full_vendor_data.get("PrimaryPhone", {}).get("FreeFormNumber", ""),
                "type": suffix,
                
                "bill_address": ', '.join(filter(None, [
                    full_vendor_data.get("BillAddr", {}).get("Line1", ""),
                    full_vendor_data.get("BillAddr", {}).get("Line2", ""),
                    full_vendor_data.get("BillAddr", {}).get("City", ""),
                    full_vendor_data.get("BillAddr", {}).get("CountrySubDivisionCode", ""),
                    full_vendor_data.get("BillAddr", {}).get("PostalCode", "")
                ])),
                "ship_address": ', '.join(filter(None, [
                    full_vendor_data.get("ShipAddr", {}).get("Line1", ""),
                    full_vendor_data.get("ShipAddr", {}).get("Line2", ""),
                    full_vendor_data.get("ShipAddr", {}).get("City", ""),
                    full_vendor_data.get("ShipAddr", {}).get("CountrySubDivisionCode", ""),
                    full_vendor_data.get("ShipAddr", {}).get("PostalCode", "")
                ])),
                "account_no":  full_vendor_data.get("AcctNum", ""),
            }
            vendor_list.append(vendor)

    paginator = Paginator(vendor_list, 20) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)      
    context["vendors"] = page_obj
    return render(request, "quickbooks/vendor_list.html", context)


def import_vendor(request):
    try:
        token_instance = QuickBooksToken.objects.first()
        print(token_instance, "token", token_instance.expires_at)

        if not token_instance:
            print("No token found, redirecting to login...")
            return redirect(reverse('quickbooks_login'))

        if token_instance.is_token_expired():
            print("Token expired, refreshing...")            
            new_token_data = refresh_quickbooks_token(token_instance.refresh_token)          
            
            if not new_token_data:
                print("Token refresh failed, redirecting to login...")
                return redirect(reverse('quickbooks_login'))          

    except QuickBooksToken.DoesNotExist:
        print("QuickBooksToken instance does not exist, redirecting to login...")
        return redirect(reverse('quickbooks_login'))
    
    if request.method == "POST":
        vendor_ids = request.POST.getlist("vendor_ids")        
        existing_vendors = []
        new_vendors = []
        for vendor_id in vendor_ids:
            full_vendor_data = get_vendor_data(vendor_id)           
            vendor_name = full_vendor_data.get('Vendor', {}).get('DisplayName', '') 
           
            if Processor.objects.filter(Q(quickbooks_id=vendor_id) | Q(entity_name=vendor_name)).exists():
                processor = Processor.objects.filter(Q(quickbooks_id=vendor_id) | Q(entity_name=vendor_name)).first()
                existing_vendors.append({
                    "id": vendor_id,
                    "name": vendor_name
                })
            elif Processor2.objects.filter(Q(quickbooks_id=vendor_id) | Q(entity_name=vendor_name)).exists():
                processor = Processor2.objects.filter(Q(quickbooks_id=vendor_id) | Q(entity_name=vendor_name)).first()
                existing_vendors.append({
                    "id": vendor_id,
                    "name": vendor_name
                })
                
            else:
                new_vendors.append({
                    "id": vendor_id,
                    "data": full_vendor_data
                })
        
        if existing_vendors:
            return render(request, 'quickbooks/confirm_import_vendor.html', {
                'existing_vendors': existing_vendors,
                'new_vendors': new_vendors,
            })
        
        return render(request, 'quickbooks/confirm_import_vendor.html', {
            'new_vendors': new_vendors,
            'existing_vendors': []
        })
    if request.method == "GET" and request.GET.get('confirm') == "true":
        vendor_ids = request.GET.getlist('vendor_ids')
        for vendor_id in vendor_ids:
            full_vendor_data = get_vendor_data(vendor_id)
            processor_email = full_vendor_data.get('Vendor', {}).get('PrimaryEmailAddr', {}).get('Address', '')
            entity_name = full_vendor_data.get('Vendor', {}).get('DisplayName', '')
            website = full_vendor_data.get('Vendor', {}).get('WebAddr', {}).get('URI', '')
            phone_number = full_vendor_data.get('Vendor', {}).get('PrimaryPhone', {}).get('FreeFormNumber', '')
            
            vendor_type = full_vendor_data.get('Vendor', {}).get('Suffix', '')
            bill_address = full_vendor_data.get('Vendor', {}).get('BillAddr', {})
            bill_addr = ', '.join(filter(None, [
                bill_address.get('Line1', ''),
                bill_address.get('Line2', ''),
                bill_address.get('City', ''),
                bill_address.get('CountrySubDivisionCode', ''),
                bill_address.get('PostalCode', '')
            ]))
            account_no = full_vendor_data.get('Vendor', {}).get('AcctNum', '')

            if vendor_type == "T1":
                if Processor.objects.filter(Q(quickbooks_id=vendor_id) | Q(entity_name=entity_name)).exists():
                    print(f"Vendor with {entity_name} already exists. Skipping creation.")
                    processor = Processor.objects.filter(Q(quickbooks_id=vendor_id) | Q(entity_name=entity_name)).first()
                    processor_user = ProcessorUser.objects.filter(processor=processor).first()
                    user = User.objects.filter(email=processor_user.contact_email).first()

                    processor.quickbooks_id = vendor_id                    
                    processor.entity_name=entity_name
                    processor.main_email=processor_email
                    processor.main_number=phone_number
                    processor.billing_address=bill_addr
                    processor.shipping_address=bill_addr
                    processor.website=website
                    processor.account_number=account_no
                    processor.save()

                    processor_user.contact_name=entity_name
                    processor_user.contact_email=processor_email
                    processor_user.contact_phone=phone_number
                    processor_user.save()
                    
                    user.email = processor_email
                    user.username = processor_email
                    user.first_name = entity_name
                    user.save()
                
                else:
                    processor = Processor(
                        quickbooks_id=vendor_id,
                        entity_name=entity_name,
                        main_email=processor_email,
                        main_number=phone_number,
                        billing_address=bill_addr,
                        shipping_address=bill_addr,
                        website=website,
                        account_number=account_no
                    )
                    processor.save()

                    from apps.processor.views import generate_random_password
                    password = generate_random_password()
                    processor_user = ProcessorUser(
                        processor=processor,
                        contact_name=entity_name,
                        contact_email=processor_email,
                        contact_phone=phone_number,
                        p_password_raw=password
                    )
                    processor_user.save()

                    user = User.objects.create(email=processor_email, username=processor_email,first_name=entity_name)
                    user.role.add(Role.objects.get(role='Processor'))
                    user.is_processor=True
                    user.is_active=True
                    user.set_password(password)
                    user.password_raw = password
                    user.save()
                    subject = "Welcome to HarvestTrails"                   
                   
                    msg_body = f"""
                        <p>Dear {entity_name},</p>

                        <p>Welcome to <strong>HarvestTrails</strong>.</p>

                        <p>Below are the login credentials for you to access HarvestTrails:</p>
                        <ul>
                            <li><strong>Name:</strong> {entity_name}</li>
                            <li><strong>Username:</strong> {processor_email}</li>
                            <li><strong>Password:</strong> {password}</li>
                        </ul>

                        <p>You can log in to HarvestTrails by clicking the link below:</p>
                        <p><a href="https://harvesttrails.app" target="_blank">Login to HarvestTrails</a></p>

                        <p>You may change your password for security purposes after logging in.</p>

                        <p>Regards,<br>Customer Service<br>Agreeta</p>
                    """
                    # from_email = 'techsupportUS@agreeta.com'
                    # to_email = [processor_email]
                    
                    email = EmailMessage(
                        subject=subject,
                        body=msg_body,
                        from_email='rijughosh.claymindsolution@gmail.com',
                        to=[processor_email]
                    )
                    email.content_subtype = "html" 
                    email.send()
                    print("Vendor successfully created in Django database.")
            else: 
                if Processor2.objects.filter(entity_name=entity_name).exists():
                    print(f"Vendor with {entity_name} already exists. Skipping creation.")
                    processor = Processor2.objects.filter(entity_name=entity_name).first()
                    processor_user = ProcessorUser2.objects.filter(processor2=processor).first()
                    user = User.objects.filter(email=processor_user.contact_email).first()

                    processor.quickbooks_id = vendor_id                    
                    processor.entity_name=entity_name
                    processor.main_email=processor_email
                    processor.main_number=phone_number
                    processor.billing_address=bill_addr
                    processor.shipping_address=bill_addr
                    processor.website=website
                    processor.account_number=account_no
                    processor.save()

                    processor_user.contact_name=entity_name
                    processor_user.contact_email=processor_email
                    processor_user.contact_phone=phone_number
                    processor_user.save()
                    
                    user.email = processor_email
                    user.username = processor_email
                    user.first_name = entity_name
                    user.save()                         
                    
                else:
                    processor = Processor2(
                        quickbooks_id=vendor_id,
                        entity_name=entity_name,
                        main_email=processor_email,
                        main_number=phone_number,
                        billing_address=bill_addr,
                        shipping_address=bill_addr,
                        website=website,
                        account_number=account_no
                    )
                    processor.save()

                    from apps.processor.views import generate_random_password
                    password = generate_random_password()
                    processor_user = ProcessorUser2(
                        processor2=processor,
                        contact_name=entity_name,
                        contact_email=processor_email,
                        contact_phone=phone_number,
                        p_password_raw=password
                    )
                    processor_user.save()
                    user = User.objects.create(email=processor_email, username=processor_email,first_name=entity_name)
                    user.role.add(Role.objects.get(role='Processor'))
                    user.is_processor2=True
                    user.is_active=True
                    user.set_password(password)
                    user.password_raw = password
                    user.save()
                    check_type = ProcessorType.objects.filter(id=vendor_type).first()
                    processor.processor_type.add(check_type)
                    subject = "Welcome to HarvestTrails"                   
                   
                    msg_body = f"""
                        <p>Dear {entity_name},</p>

                        <p>Welcome to <strong>HarvestTrails</strong>.</p>

                        <p>Below are the login credentials for you to access HarvestTrails:</p>
                        <ul>
                            <li><strong>Name:</strong> {entity_name}</li>
                            <li><strong>Username:</strong> {processor_email}</li>
                            <li><strong>Password:</strong> {password}</li>
                        </ul>

                        <p>You can log in to HarvestTrails by clicking the link below:</p>
                        <p><a href="https://harvesttrails.app" target="_blank">Login to HarvestTrails</a></p>

                        <p>You may change your password for security purposes after logging in.</p>

                        <p>Regards,<br>Customer Service<br>Agreeta</p>
                    """
                    # from_email = 'techsupportUS@agreeta.com'
                    # to_email = [processor_email]
                    email = EmailMessage(
                        subject=subject,
                        body=msg_body,
                        from_email='rijughosh.claymindsolution@gmail.com',
                        to=[processor_email]
                    )
                    email.content_subtype = "html" 
                    email.send()
                    print("Vendor successfully created in Django database.")

        return redirect('vendors')
    return redirect('vendors')

    
def customer_list(request):
    context = {}
    try:
        token_instance = QuickBooksToken.objects.first()
        print(token_instance, "token", token_instance.expires_at)

        if not token_instance:
            print("No token found, redirecting to login...")
            return redirect(reverse('quickbooks_login'))

        if token_instance.is_token_expired():
            print("Token expired, refreshing...")            
            new_token_data = refresh_quickbooks_token(token_instance.refresh_token)          
            
            if not new_token_data:
                print("Token refresh failed, redirecting to login...")
                return redirect(reverse('quickbooks_login'))          

    except QuickBooksToken.DoesNotExist:
        print("QuickBooksToken instance does not exist, redirecting to login...")
        return redirect(reverse('quickbooks_login'))
    
    realm_id = QuickBooksToken.objects.first().realm_id
    access_token = QuickBooksToken.objects.first().access_token
    raw_customer_list = get_all_customer_data(realm_id, access_token)

    customer_list = []
    for full_customer_data in raw_customer_list:
        customer = {
            "id": full_customer_data.get("Id", ""),
            "email": full_customer_data.get("PrimaryEmailAddr", {}).get("Address", ""),
            "name": full_customer_data.get("DisplayName", ""),
            "phone": full_customer_data.get('PrimaryPhone', {}).get('FreeFormNumber', ''),
            "fax": full_customer_data.get('Fax', {}).get('FreeFormNumber', ''),
            "bill_address": ', '.join(filter(None, [
                full_customer_data.get("BillAddr", {}).get("Line1", ""),
                full_customer_data.get("BillAddr", {}).get("Line2", ""),
                full_customer_data.get("BillAddr", {}).get("City", ""),
                full_customer_data.get("BillAddr", {}).get("CountrySubDivisionCode", ""),
                full_customer_data.get("BillAddr", {}).get("PostalCode", "")
            ])),
            "ship_address": ', '.join(filter(None, [
                full_customer_data.get("ShipAddr", {}).get("Line1", ""),
                full_customer_data.get("ShipAddr", {}).get("Line2", ""),
                full_customer_data.get("ShipAddr", {}).get("City", ""),
                full_customer_data.get("ShipAddr", {}).get("CountrySubDivisionCode", ""),
                full_customer_data.get("ShipAddr", {}).get("PostalCode", "")
            ])),
            "taxable": full_customer_data.get("Taxable", False),
            "sales_term": full_customer_data.get("SalesTermRef", {}).get("value", 30),
            "tax_rate": full_customer_data.get("DefaultTaxCodeRef", {}).get("value", 0),
            "is_active": full_customer_data.get('Active', True)
        }
        customer_list.append(customer)
    paginator = Paginator(customer_list, 20) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context["customers"] = page_obj
    return render(request, "quickbooks/customer_list.html", context)


def import_customer(request):
    try:
        token_instance = QuickBooksToken.objects.first()
        print(token_instance, "token", token_instance.expires_at)

        if not token_instance:
            print("No token found, redirecting to login...")
            return redirect(reverse('quickbooks_login'))

        if token_instance.is_token_expired():
            print("Token expired, refreshing...")            
            new_token_data = refresh_quickbooks_token(token_instance.refresh_token)          
            
            if not new_token_data:
                print("Token refresh failed, redirecting to login...")
                return redirect(reverse('quickbooks_login'))          

    except QuickBooksToken.DoesNotExist:
        print("QuickBooksToken instance does not exist, redirecting to login...")
        return redirect(reverse('quickbooks_login'))
    
    if request.method == "POST":
        customer_ids = request.POST.getlist("customer_ids")
        print(customer_ids)
        existing_customers = []
        new_customers = []
        for customer_id in customer_ids:
            full_customer_data = get_customer_data(customer_id)           
            customer_name = full_customer_data.get('Customer', {}).get('DisplayName', '')  
            print(customer_name)
            if Customer.objects.filter(Q(quickbooks_id=customer_id) | Q(name=customer_name)).exists():
                customer = Customer.objects.filter(Q(quickbooks_id=customer_id) | Q(name=customer_name)).first()
                existing_customers.append({
                    "id": customer_id,
                    "name": customer_name
                })
                
            else:
                new_customers.append({
                    "id": customer_id,
                    "data": full_customer_data
                })
       
        if existing_customers:
            return render(request, 'quickbooks/confirm_import_customer.html', {
                'existing_customers': existing_customers,
                'new_customers': new_customers,
            })
        
        return render(request, 'quickbooks/confirm_import_customer.html', {
            'new_customers': new_customers,
            'existing_customers': []
        })
    if request.method == "GET" and request.GET.get('confirm') == "true":
        customer_ids = request.GET.getlist('customer_ids')

        for customer_id in customer_ids:
            full_customer_data = get_customer_data(customer_id)
            customer_email = full_customer_data.get('Customer', {}).get('PrimaryEmailAddr', {}).get('Address', '')
            customer_name = full_customer_data.get('Customer', {}).get('DisplayName', '')
            bill_address = full_customer_data.get('Customer', {}).get('BillAddr', {})
            bill_addr = ', '.join(filter(None, [
                bill_address.get('Line1', ''),
                bill_address.get('Line2', ''),
                bill_address.get('City', ''),
                bill_address.get('CountrySubDivisionCode', ''),
                bill_address.get('PostalCode', '')
            ]))
            
            ship_address = full_customer_data.get('Customer', {}).get('ShipAddr', {})
            ship_addr = ', '.join(filter(None, [
                ship_address.get('Line1', ''),
                ship_address.get('Line2', ''),
                ship_address.get('City', ''),
                ship_address.get('CountrySubDivisionCode', ''),
                ship_address.get('PostalCode', '')
            ]))

            taxable = full_customer_data.get('Customer', {}).get('Taxable', False)
            sales_term = full_customer_data.get('Customer', {}).get('SalesTermRef', {}).get('value', 30)
            tax_rate = full_customer_data.get('Customer', {}).get('DefaultTaxCodeRef', {}).get('value', 0)
            is_active = full_customer_data.get('Customer', {}).get('Active', True)
            user_name = full_customer_data.get('Customer', {}).get('GivenName', customer_name)
            user_phone = full_customer_data.get('Customer', {}).get('PrimaryPhone', {}).get('FreeFormNumber', '')
            user_fax = full_customer_data.get('Customer', {}).get('Fax', {}).get('FreeFormNumber', '')

            if Customer.objects.filter(Q(quickbooks_id=customer_id) | Q(name=customer_name)).exists():
                customer = Customer.objects.filter(Q(quickbooks_id=customer_id) | Q(name=customer_name)).first()
                customer_user = CustomerUser.objects.filter(customer=customer).first()                            
                user = User.objects.filter(email=customer_user.contact_email).first()

                customer.name = customer_name
                customer.billing_address = bill_addr
                customer.shipping_address = ship_addr
                customer.is_active = is_active
                customer.is_tax_payable = taxable
                customer.tax_percentage = tax_rate
                customer.quickbooks_id = customer_id
                customer.location = bill_addr
                customer.save()
                
                customer_user.contact_name = user_name
                customer_user.contact_email = customer_email
                customer_user.contact_phone = user_phone
                customer_user.contact_fax = user_fax
                customer_user.save()

                user.email = customer_email
                user.username = customer_email
                user.first_name = user_name
                user.save()

                print("Customer and Customer user successfully updated.") 
            else:
                customer = Customer.objects.create(
                quickbooks_id=customer_id,
                name=customer_name,
                billing_address=bill_addr,
                shipping_address=ship_addr,
                credit_terms=sales_term,
                is_tax_payable=taxable,
                tax_percentage=tax_rate,
                location=bill_addr
                )
                print("Customer successfully created in Django database.")
                from apps.warehouseManagement.views import generate_random_password
                password = generate_random_password()

                customer_user = CustomerUser.objects.create(
                    customer=customer,
                    contact_name=user_name,
                    contact_email=customer_email,
                    contact_phone=user_phone,
                    contact_fax=user_fax,
                    p_password_raw=password
                )
                user = User.objects.create(
                    email=customer_email,
                    username=customer_email,
                    first_name=user_name,
                )
                customer_role = Role.objects.get(role='Customer')
                user.role.add(customer_role)

                user.is_customer = True
                user.is_active = True
                user.set_password(password)
                user.password_raw = password  
                user.save()

                subject = "Welcome to HarvestTrails"                   
                   
                msg_body = f"""
                        <p>Dear {customer_name},</p>

                        <p>Welcome to <strong>HarvestTrails</strong>.</p>

                        <p>Below are the login credentials for you to access HarvestTrails:</p>
                        <ul>
                            <li><strong>Name:</strong> {customer_name}</li>
                            <li><strong>Username:</strong> {customer_email}</li>
                            <li><strong>Password:</strong> {password}</li>
                        </ul>

                        <p>You can log in to HarvestTrails by clicking the link below:</p>
                        <p><a href="https://harvesttrails.app" target="_blank">Login to HarvestTrails</a></p>

                        <p>You may change your password for security purposes after logging in.</p>

                        <p>Regards,<br>Customer Service<br>Agreeta</p>
                    """
                # from_email = 'techsupportUS@agreeta.com'
                # to_email = [customer_email]
                email = EmailMessage(
                        subject=subject,
                        body=msg_body,
                        from_email='rijughosh.claymindsolution@gmail.com',
                        to=['piu.de1996@gmail.com']
                    )
                email.content_subtype = "html" 
                email.send()
        return redirect('list-customer')

    return redirect('list-customer')

                
def item_list(request):
    context = {}
    try:
        token_instance = QuickBooksToken.objects.first()
        print(token_instance, "token", token_instance.expires_at)

        if not token_instance:
            print("No token found, redirecting to login...")
            return redirect(reverse('quickbooks_login'))

        if token_instance.is_token_expired():
            print("Token expired, refreshing...")            
            new_token_data = refresh_quickbooks_token(token_instance.refresh_token)          
            
            if not new_token_data:
                print("Token refresh failed, redirecting to login...")
                return redirect(reverse('quickbooks_login'))          

    except QuickBooksToken.DoesNotExist:
        print("QuickBooksToken instance does not exist, redirecting to login...")
        return redirect(reverse('quickbooks_login'))
    
    realm_id = QuickBooksToken.objects.first().realm_id
    access_token = QuickBooksToken.objects.first().access_token
    raw_item_list = get_all_item_data(realm_id, access_token)
    item_list = []
    for full_item_data in raw_item_list:
        item_type = full_item_data.get('Type', '')
        if item_type == 'Inventory': 
            class_ref = full_item_data.get('ClassRef', {})
            item = {
                "id": full_item_data.get('Id', ''),
                "item_name": full_item_data.get('Name', ''),
                "type": item_type,
                "per_unit_price": full_item_data.get('UnitPrice', ''),
                "description": full_item_data.get('Description', ''),
                "is_active": full_item_data.get('Active', True),            
                "class_name": class_ref.get('name', 'No Class'),
                "class_id": class_ref.get('value', 'No Class ID'),
            }
            item_list.append(item)
                              
    paginator = Paginator(item_list, 20) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context["items"] = page_obj
    return render(request, "quickbooks/item_list.html", context)


def import_item(request):
    try:
        token_instance = QuickBooksToken.objects.first()
        print(token_instance, "token", token_instance.expires_at)

        if not token_instance:
            print("No token found, redirecting to login...")
            return redirect(reverse('quickbooks_login'))

        if token_instance.is_token_expired():
            print("Token expired, refreshing...")            
            new_token_data = refresh_quickbooks_token(token_instance.refresh_token)          
            
            if not new_token_data:
                print("Token refresh failed, redirecting to login...")
                return redirect(reverse('quickbooks_login'))          

    except QuickBooksToken.DoesNotExist:
        print("QuickBooksToken instance does not exist, redirecting to login...")
        return redirect(reverse('quickbooks_login'))
    
    if request.method == "POST":
        item_ids = request.POST.getlist("item_ids")
        print(item_ids)
        existing_items = []
        new_items = []
        for item_id in item_ids:
            full_item_data = get_item_data(item_id)         
      
            item_name = full_item_data.get('Item', {}).get('Name', '')
            class_ref = full_item_data.get('Item', {}).get('ClassRef', {})
            class_name = class_ref.get('name', 'No Class')                     

            name = class_name.upper()
            item = f'{name}-{item_name}'
            if ShipmentItem.objects.filter(Q(quickbooks_id=item_id) | Q(item=item)).exists():
                item = ShipmentItem.objects.filter(Q(quickbooks_id=item_id) | Q(item=item)).first() 
                existing_items.append({
                    "id": item_id,
                    "name": item_name
                })                
            else:
                new_items.append({
                    "id": item_id,
                    "data": full_item_data
                })
      
        if existing_items:
            return render(request, 'quickbooks/confirm_import_item.html', {
                'existing_items': existing_items,
                'new_items': new_items,
            })
        
        return render(request, 'quickbooks/confirm_import_item.html', {
            'new_items': new_items,
            'existing_items': []
        })
    if request.method == "GET" and request.GET.get('confirm') == "true":
        item_ids = request.GET.getlist('item_ids')

        for item_id in item_ids:

            full_item_data = get_item_data(item_id)
            item_name_ = full_item_data.get('Item', {}).get('Name', '')
            type = full_item_data.get('Item', {}).get('Type', '')
            per_unit_price = full_item_data.get('Item', {}).get('UnitPrice', '')
            description = full_item_data.get('Item', {}).get('Description', '')
            is_active = full_item_data.get('Item', {}).get('Active', True) 

            class_ref = full_item_data.get('Item', {}).get('ClassRef', {})
            class_name = class_ref.get('name', 'No Class')
            class_id = class_ref.get('value', 'No Class ID')                       

            name = class_name.upper()
            item = f'{name}-{item_name_}'
            if ShipmentItem.objects.filter(item=item).exists():
                
                print(f"ShipmentItem already exists. Skipping creation.")
                shipment_item = ShipmentItem.objects.filter(item=item).first()
                shipment_item.item = item
                shipment_item.quickbooks_id = item_id
                shipment_item.item_name= name
                shipment_item.item_type = item_name_
                shipment_item.type=type
                shipment_item.per_unit_price=per_unit_price
                shipment_item.description=description
                shipment_item.is_active=is_active
                shipment_item.save()
                    
            else:
                shipment_item = ShipmentItem(
                    quickbooks_id=item_id,
                    item=item,    
                    item_name= name,
                    item_type = item_name_,                          
                    per_unit_price=per_unit_price,
                    type= type,
                    description=description,
                    is_active=is_active
                )
                shipment_item.save()
        return redirect('shipment_item_list')

    return redirect('shipment_item_list')
