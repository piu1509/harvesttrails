import string, random, json, time
from io import BytesIO
import qrcode
import stripe
from django.urls import reverse
from django.utils.http import urlencode
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from apps.warehouseManagement.models import *
from apps.warehouseManagement.forms import *
from apps.processor.models import Processor, ProcessorUser, Location
from apps.processor2.models import Processor2, ProcessorUser2, Processor2Location
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from apps.accounts.models import User, Role, ShowNotification, LogTable
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from apps.processor.views import calculate_milled_volume, get_sku_list
from rest_framework.response import Response
from django.conf import settings
protocol = 'http'
import datetime
from apps.contracts.models import *
from io import StringIO
from django.utils.dateparse import parse_date
from datetime import timedelta, date
import csv
from django.contrib.auth.decorators import login_required
from collections import defaultdict
from apps.quickbooks_integration.views import create_customer, get_tax_agencies, create_custom_tax_rate, refresh_quickbooks_token, get_customer_data, update_customer, create_invoice, get_tax_rates, create_payment
stripe.api_key = settings.STRIPE_SECRET_KEY
from django.views.decorators.http import require_GET
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Prefetch
from django.core.mail import send_mail
from django.core.files.base import ContentFile
import requests
from apps.processor.models import GrowerShipment
import pdfkit
from django.core.mail import EmailMessage
import csv


characters = list(string.ascii_letters + string.digits + "@#$%")
def generate_random_password():
	length = 8
	random.shuffle(characters)
	password = []
	for i in range(length):
		password.append(random.choice(characters))
	return "".join(password)


def get_lat_lng(address, api_key):    
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"

    response = requests.get(url)
    data = response.json()

    if data['status'] == 'OK':        
        lat = data['results'][0]['geometry']['location']['lat']
        lng = data['results'][0]['geometry']['location']['lng']
        return lat, lng
    else:      
        return None
 

@login_required()
def add_distributor(request):
    context = {}
    try:
        if request.user.is_authenticated:
            # superuser.................
            if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
                form = DistributorForm()
                context["form"] = form
                if request.method == 'POST':
                    form = DistributorForm(request.POST)                   
                    entity_name = request.POST.get('entity_name')
                    warehouse_ids  = request.POST.getlist('warehouse')
                    location = request.POST.get('location')
                    latitude  = request.POST.get('latitude ')
                    longitude = request.POST.get('longitude')                    
                
                    distributor = Distributor.objects.create(entity_name=entity_name,location=location,latitude =latitude ,longitude=longitude)
                    for warehouse_id in warehouse_ids:
                        try:
                            warehouse = Warehouse.objects.get(id=warehouse_id)
                            distributor.warehouse.add(warehouse)
                        except Warehouse.DoesNotExist:
                            pass  # Handle error or continue as per your need
                                
                    log_type, log_status, log_device = "Distributor", "Added", "Web"
                    log_idd, log_name = distributor.id, entity_name
                    log_email = None
                    log_details = (f"entity_name = {entity_name} | location = {location} | "
                           f"latitude = {latitude} | longitude = {longitude}")
                    action_by_userid = request.user.id
                    userr = User.objects.get(pk=action_by_userid)
                    user_role = userr.role.all()
                    action_by_username = f'{userr.first_name} {userr.last_name}'
                    action_by_email = userr.username
                    if request.user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                        log_details=log_details,log_device=log_device)
                    logtable.save()
                    
                    dis = Distributor.objects.get(entity_name=entity_name,location=location,latitude =latitude ,longitude=longitude)
                    counter = request.POST.get('counter')
                    for i in range(1,int(counter)+1):
                        contact_name = request.POST.get('contact_name{}'.format(i))

                        contact_email = request.POST.get('contact_email{}'.format(i))
                        country_code = request.POST.get('country_code{}'.format(i))
                        phone_number = request.POST.get('phone_number{}'.format(i))
                        contact_phone = country_code + phone_number
                        print(contact_phone)
                        contact_fax = request.POST.get('contact_fax{}'.format(i))
                        if User.objects.filter(email=contact_email).exists():
                            messages.error(request,'email already exists')
                        else:
                            password = generate_random_password()
                            
                            distributor_user = DistributorUser.objects.create(distributor_id = dis.id,contact_name=contact_name,contact_email=contact_email,contact_phone=contact_phone,contact_fax=contact_fax,p_password_raw=password)
                            
                            user = User.objects.create(email=contact_email, username=contact_email,first_name=contact_name)
                            user.role.add(Role.objects.get(role='Distributor'))
                            user.is_distributor=True
                            user.is_active=True
                            user.set_password(password)
                            user.password_raw = password
                            user.save()
                            
                            log_type, log_status, log_device = "DistributorUser", "Added", "Web"
                            log_idd, log_name = distributor_user.id, contact_name
                            log_email = contact_email
                            log_details = f"distributor_id = {dis.id} | distributor = {dis.entity_name} | contact_name= {contact_name} | contact_email = {contact_email} | contact_phone = {contact_phone} | contact_fax = {contact_fax} | p_password_raw = {password}"
                            action_by_userid = request.user.id
                            userr = User.objects.get(pk=action_by_userid)
                            user_role = userr.role.all()
                            action_by_username = f'{userr.first_name} {userr.last_name}'
                            action_by_email = userr.username
                            if request.user.id == 1 :
                                action_by_role = "superuser"
                            else:
                                action_by_role = str(','.join([str(i.role) for i in user_role]))
                            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                                action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                                log_details=log_details,log_device=log_device)
                            logtable.save()
                    return redirect('list-distributor')                    
                return render(request, 'distributor/add_distributor.html',context)
            else:
                messages.error(request, "Not a valid request.")
                return redirect("dashboard")
        else:
            return redirect('login')
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/add_distributor.html',context)


@login_required()
def add_distributor_user(request,pk):
    context = {}
    try:
        if request.user.is_authenticated:        
            # superuser..............
            if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
                distributor_user = DistributorUser.objects.get(id=pk)
                distributor_id = distributor_user.distributor.id
                distributor = Distributor.objects.get(id=distributor_id)
                context['distributor'] = distributor
                distributor_user = DistributorUser.objects.filter(distributor_id = distributor.id)
                context['distributor_user'] = distributor_user
                if request.method == 'POST':
                    counter = request.POST.get('counter')
                    for i in range(1,int(counter)+1):
                        contact_name = request.POST.get('contact_name{}'.format(i))

                        contact_email = request.POST.get('contact_email{}'.format(i))
                        country_code = request.POST.get('country_code{}'.format(i))
                        phone_number = request.POST.get('phone_number{}'.format(i))
                        contact_phone = country_code + phone_number
                        print(contact_phone)
                        contact_fax = request.POST.get('contact_fax{}'.format(i))

                        # print('contact_name',contact_name,'contact_email',contact_email,'contact_phone',contact_phone,'contact_fax',contact_fax)

                        if User.objects.filter(email=contact_email).exists():
                            messages.error(request,'email already exists')
                        else:
                            password = generate_random_password()
                            
                            dis_user = DistributorUser(distributor_id = distributor_id,contact_name=contact_name,contact_email=contact_email,contact_phone=contact_phone,contact_fax=contact_fax,p_password_raw=password)
                            dis_user.save()
                            user = User.objects.create(email=contact_email, username=contact_email,first_name=contact_name)
                            user.role.add(Role.objects.get(role='Distributor'))
                            user.is_distributor=True
                            user.is_active=True
                            user.set_password(password)
                            user.password_raw = password
                            user.save()

                            # 07-04-23 Log Table
                            log_type, log_status, log_device = "DistributorUser", "Added", "Web"
                            log_idd, log_name = dis_user.id, contact_name
                            log_email = contact_email
                            log_details = f"distributor_id = {distributor_id} | distributor = {distributor.entity_name}  | contact_name= {contact_name} | contact_email = {contact_email} | contact_phone = {contact_phone} | contact_fax = {contact_fax}"
                            
                            action_by_userid = request.user.id
                            userr = User.objects.get(pk=action_by_userid)
                            user_role = userr.role.all()
                            action_by_username = f'{userr.first_name} {userr.last_name}'
                            action_by_email = userr.username
                            if request.user.id == 1 :
                                action_by_role = "superuser"
                            else:
                                action_by_role = str(','.join([str(i.role) for i in user_role]))
                            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                                action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                                log_details=log_details,log_device=log_device)
                            logtable.save()

                    return redirect('list-distributor')
                return render(request, 'distributor/add_distributor_user.html',context)
            # processor ..............
            elif request.user.is_distributor:
                distributor_user = DistributorUser.objects.get(id=pk)
                distributor_id = distributor_user.distributor.id
                distributor = Distributor.objects.get(id=distributor_id)
                context['distributor'] = distributor
                distributor_user = DistributorUser.objects.filter(distributor_id = distributor.id)
                context['distributor_user'] = distributor_user
                if request.method == 'POST':
                    counter = request.POST.get('counter')
                    for i in range(1,int(counter)+1):
                        contact_name = request.POST.get('contact_name{}'.format(i))

                        contact_email = request.POST.get('contact_email{}'.format(i))
                        country_code = request.POST.get('country_code{}'.format(i))
                        phone_number = request.POST.get('phone_number{}'.format(i))
                        contact_phone = country_code + phone_number
                        print(contact_phone)
                        contact_fax = request.POST.get('contact_fax{}'.format(i))

                        # print('contact_name',contact_name,'contact_email',contact_email,'contact_phone',contact_phone,'contact_fax',contact_fax)

                        if User.objects.filter(email=contact_email).exists():
                            messages.error(request,'email already exists')
                        else:
                            password = generate_random_password()
                            
                            dis_user = DistributorUser(distributor_id = distributor_id,contact_name=contact_name,contact_email=contact_email,contact_phone=contact_phone,contact_fax=contact_fax,p_password_raw=password)
                            dis_user.save()
                            user = User.objects.create(email=contact_email, username=contact_email,first_name=contact_name)
                            user.role.add(Role.objects.get(role='Distributor'))
                            user.is_distributor=True
                            user.is_active=True
                            user.set_password(password)
                            user.password_raw = password
                            user.save()

                            # 07-04-23 Log Table
                            log_type, log_status, log_device = "DistributorUser", "Added", "Web"
                            log_idd, log_name = dis_user.id, contact_name
                            log_email = contact_email
                            log_details = f"distributor_id = {distributor_id} | distributor = {distributor.entity_name}  | contact_name= {contact_name} | contact_email = {contact_email} | contact_phone = {contact_phone} | contact_fax = {contact_fax}"
                            
                            action_by_userid = request.user.id
                            userr = User.objects.get(pk=action_by_userid)
                            user_role = userr.role.all()
                            action_by_username = f'{userr.first_name} {userr.last_name}'
                            action_by_email = userr.username
                            if request.user.id == 1 :
                                action_by_role = "superuser"
                            else:
                                action_by_role = str(','.join([str(i.role) for i in user_role]))
                            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                                action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                                log_details=log_details,log_device=log_device)
                            logtable.save()

                    return redirect('list-distributor')
                return render(request, 'distributor/add_distributor_user.html',context)
            
            else:
                messages.error(request, "Not a valid request")
                return redirect("dashboard")
        else:
            return redirect('login')
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/add_distributor_user.html',context)


@login_required()
def distributor_list(request):
    context = {}
    try:
        if request.user.is_authenticated:
            distributor = []
            search_name = request.GET.get('search_name', '')
            if 'Grower' in request.user.get_role() and not request.user.is_superuser:
                pass
            elif request.user.is_consultant:
                pass
            elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
                distributor = DistributorUser.objects.all()
                if search_name:
                    distributor = distributor.filter(Q(contact_name__icontains=search_name) | Q(distributor__entity_name__icontains=search_name)| Q(contact_email__icontains=search_name))
                    context['search_name'] = search_name
            elif request.user.is_distributor:
                dis = DistributorUser.objects.filter(contact_email=request.user.email).first()
                entity_name = dis.distributor
                distributor = DistributorUser.objects.filter(distributor=entity_name)
                if search_name:
                    distributor = distributor.filter(Q(contact_name__icontains=search_name) | Q(distributor__entity_name__icontains=search_name)| Q(contact_email__icontains=search_name))
                    context['search_name'] = search_name
            else:
                messages.error(request, "Not a valid request")
                return redirect("dashboard")

            # Pagination
            distributor = distributor.order_by("-id")
            paginator = Paginator(distributor, 20) 
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            context['page_obj'] = page_obj            

            return render(request, 'distributor/list_distributor.html', context)
        else:
            return redirect('login')
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/list_distributor.html', context)


@login_required()
def distributor_update(request,pk):
    context = {}
    try:
        if request.user.is_authenticated:        
            if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
                obj_id = DistributorUser.objects.get(id=pk)
                print(obj_id)
                context['p_user'] = obj_id
                distributor = Distributor.objects.get(id=obj_id.distributor.id)

                context['form'] = DistributorForm(instance=distributor)
                distributor_email = obj_id.contact_email
                user = User.objects.get(email=distributor_email)
                if request.method == 'POST':                   
                    form = DistributorForm( request.POST,instance=distributor)                    
                    if form.is_valid():                       
                        email_update = request.POST.get('contact_email1')
                        name_update = request.POST.get('contact_name1')
                        # country_code = request.POST.get('country_code1')
                        phone_number = request.POST.get('phone_number1')
                        phone_update = phone_number
                        fax_update = request.POST.get('contact_fax1')
                        
                        obj_id.contact_name = name_update
                        obj_id.contact_email = email_update
                        obj_id.contact_phone = phone_update
                        obj_id.contact_fax = fax_update
                        obj_id.save()
                        log_email = ''
                        if email_update != distributor_email:
                            f_name = name_update
                            user.email = email_update
                            user.username = email_update
                            user.first_name = f_name
                            user.save()
                            form.save()
                            log_email = email_update
                        else :
                            f_name = name_update
                            user.first_name = f_name
                            user.save()
                            form.save()
                            log_email = obj_id.contact_email
                        form.save()
                        # 07-04-23 Log Table
                        log_type, log_status, log_device = "DistributorUser", "Edited", "Web"
                        log_idd, log_name = obj_id.id, name_update
                        log_details = f"distributor_id = {distributor.id} | distributor = {distributor.entity_name}  | contact_name= {name_update} | contact_email = {email_update} | contact_phone = {phone_update} | contact_fax = {fax_update}"
                        action_by_userid = request.user.id
                        userr = User.objects.get(pk=action_by_userid)
                        user_role = userr.role.all()
                        action_by_username = f'{userr.first_name} {userr.last_name}'
                        action_by_email = userr.username
                        if request.user.id == 1 :
                            action_by_role = "superuser"
                        else:
                            action_by_role = str(','.join([str(i.role) for i in user_role]))
                        logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                            action_by_userid=action_by_userid,action_by_username=action_by_username,
                                            action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                            log_details=log_details,log_device=log_device)
                        logtable.save()
                        return redirect('list-distributor')
                return render(request, 'distributor/update_distributor.html',context)
            # distributor..........
            elif request.user.is_distributor:
                obj_id = DistributorUser.objects.get(id=pk)
                context['p_user'] = obj_id
                distributor = Distributor.objects.get(id=obj_id.distributor.id)

                context['form'] = DistributorForm(instance=distributor)
                distributor_email = obj_id.contact_email
                user = User.objects.get(email=distributor_email)
                if request.method == 'POST':
                    form = DistributorForm( request.POST,instance=distributor)
                    if form.is_valid():
                        email_update = request.POST.get('contact_email1')
                        name_update = request.POST.get('contact_name1')
                        # country_code = request.POST.get('country_code1')
                        phone_number = request.POST.get('phone_number1')
                        phone_update = phone_number
                        fax_update = request.POST.get('contact_fax1')
                        obj_id.contact_name = name_update
                        obj_id.contact_email = email_update
                        obj_id.contact_phone = phone_update
                        obj_id.contact_fax = fax_update
                        obj_id.save()
                        log_email = ''
                        if email_update != distributor_email:
                            f_name = name_update
                            user.email = email_update
                            user.username = email_update
                            user.first_name = f_name
                            user.save()
                            form.save()
                            log_email = email_update
                        else :
                            f_name = name_update
                            user.first_name = f_name
                            user.save()
                            form.save()
                            log_email = obj_id.contact_email
                        # 07-04-23 Log Table
                        log_type, log_status, log_device = "DistributorUser", "Edited", "Web"
                        log_idd, log_name = obj_id.id, name_update
                        log_details = f"distributor_id = {distributor.id} | distributor = {distributor.entity_name}  | contact_name= {name_update} | contact_email = {email_update} | contact_phone = {phone_update} | contact_fax = {fax_update}"
                        action_by_userid = request.user.id
                        userr = User.objects.get(pk=action_by_userid)
                        user_role = userr.role.all()
                        action_by_username = f'{userr.first_name} {userr.last_name}'
                        action_by_email = userr.username
                        if request.user.id == 1 :
                            action_by_role = "superuser"
                        else:
                            action_by_role = str(','.join([str(i.role) for i in user_role]))
                        logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                            action_by_userid=action_by_userid,action_by_username=action_by_username,
                                            action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                            log_details=log_details,log_device=log_device)
                        logtable.save()
                        return redirect('list-distributor')
                return render(request, 'distributor/update_distributor.html',context)
            else:
                messages.error(request, "Not a valid request")
                return redirect("dashboard")
        else:
            return redirect('login')
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/update_distributor.html',context)


@login_required()
def distributor_change_password(request,pk):
    context={}
    try:
        # Superuser..............
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            dist = DistributorUser.objects.get(id=pk)
            user = User.objects.get(email=dist.contact_email)
            context["userr"] = user
            if request.method == "POST":
                password1 = request.POST.get("password1")
                password2 = request.POST.get("password2")
                if len(password1) != 0 and len(password2) != 0 and password1 != None and password2 != None and password1 == password2:
                    # update_pass_user = User.objects.get(id=pk)
                    password = make_password(password1)
                    user.password = password
                    user.password_raw = password1
                    user.save()
                    dist.p_password_raw = password1
                    dist.save()
                    # 10-04-23 Log Table
                    log_type, log_status, log_device = "DistributorUser", "Password changed", "Web"
                    log_idd, log_name = dist.id, dist.contact_name
                    log_email = dist.contact_email
                    log_details = f"distributor_id = {dist.distributor.id} | distributor = {dist.distributor.entity_name} | contact_name= {dist.contact_name} | contact_email = {dist.contact_email} | contact_phone = {dist.contact_phone} | contact_fax = {dist.contact_fax}"
                    action_by_userid = request.user.id
                    user = User.objects.get(pk=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if request.user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                        log_details=log_details, log_device=log_device)
                    logtable.save()
                    messages.success(request,"Password changed successfully!")
            return render (request, 'distributor/distributor_change_password.html', context)
        # Distributor...............
        elif request.user.is_distributor:
            dist = DistributorUser.objects.get(id=pk)
            user = User.objects.get(email=dist.contact_email)
            context["userr"] = user
            if request.method == "POST":
                password1 = request.POST.get("password1")
                password2 = request.POST.get("password2")
                if len(password1) != 0 and len(password2) != 0 and password1 != None and password2 != None and password1 == password2:
                    # update_pass_user = User.objects.get(id=pk)
                    password = make_password(password1)
                    user.password = password
                    user.password_raw = password1
                    user.save()
                    dist.p_password_raw = password1
                    dist.save()
                    # 10-04-23 Log Table
                    log_type, log_status, log_device = "DistributorUser", "Password changed", "Web"
                    log_idd, log_name = dist.id, dist.contact_name
                    log_email = dist.contact_email
                    log_details = f"distributor_id = {dist.distributor.id} | distributor = {dist.distributor.entity_name} | contact_name= {dist.contact_name} | contact_email = {dist.contact_email} | contact_phone = {dist.contact_phone} | contact_fax = {dist.contact_fax}"
                    action_by_userid = request.user.id
                    user = User.objects.get(pk=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if request.user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                        log_details=log_details, log_device=log_device)
                    logtable.save()
                    messages.success(request,"Password changed successfully!")
        
        else:
            return redirect('dashboard')
        return render (request, 'distributor/distributor_change_password.html', context)
    except Exception as e:
        context["error_messages"] = str(e)
        return render (request, 'distributor/distributor_change_password.html', context)


@login_required()
def add_warehouse(request):
    context = {}
    try:
        if request.user.is_authenticated:
            if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_distributor:
                form = WarehouseForm()
                context["form"] = form
                if request.method == 'POST':
                    form = WarehouseForm(request.POST)

                    if form.is_valid():
                        name = form.cleaned_data['name']
                        location = form.cleaned_data['location']
                        latitude = form.cleaned_data['latitude']
                        longitude = form.cleaned_data['longitude']
                        status = form.cleaned_data['status']
                        distributors = form.cleaned_data['distributor']  
                        customers = form.cleaned_data['customers'] 

                        if Warehouse.objects.filter(name=name).exists():
                            messages.error(request, "A warehouse with this name already exists.")
                            return render(request, 'distributor/add_warehouse.html', context)

                        warehouse = Warehouse.objects.create(
                            name=name,
                            location=location,
                            latitude=latitude,
                            longitude=longitude,
                            status=status
                        )
                        for customer in customers:
                            customer.warehouse = warehouse  
                            customer.save()

                        for distributor in distributors:
                            distributor.warehouse.add(warehouse)

                        # Log the action
                        log_type, log_status, log_device = "Warehouse", "Added", "Web"
                        log_idd, log_name = warehouse.id, name
                        log_email = None
                        log_details = (f"name = {name} | location = {location} | "
                                        f"latitude = {latitude} | longitude = {longitude} | status = {status}")
                        action_by_userid = request.user.id
                        userr = User.objects.get(pk=action_by_userid)
                        user_role = userr.role.all()
                        action_by_username = f'{userr.first_name} {userr.last_name}'
                        action_by_email = userr.username
                        action_by_role = "superuser" if request.user.id == 1 else str(','.join([str(i.role) for i in user_role]))
                        logtable = LogTable(
                            log_type=log_type, log_status=log_status, log_idd=log_idd, log_name=log_name,
                            action_by_userid=action_by_userid, action_by_username=action_by_username,
                            action_by_email=action_by_email, action_by_role=action_by_role, log_email=log_email,
                            log_details=log_details, log_device=log_device
                        )
                        logtable.save()

                        # Add the single warehouse user
                        user_name = request.POST.get('user_name')
                        user_email = request.POST.get('user_email')
                        country_code = request.POST.get('country_code')
                        phone_number = request.POST.get('phone_number')
                        user_phone = country_code + phone_number
                        user_fax = request.POST.get('user_fax')
                        print(user_name, user_email, user_phone, user_fax)

                        if WarehouseUser.objects.filter(warehouse=warehouse).exists():                       
                            messages.error(request, "A user is already associated with this warehouse.")
                            return render(request, 'distributor/add_warehouse.html', context)

                        if User.objects.filter(email=user_email).exists():                        
                            messages.error(request, f'Email {user_email} already exists.')
                        else:
                            password = generate_random_password()                        
                            warehouse_user = WarehouseUser.objects.create(
                                warehouse=warehouse,
                                contact_name=user_name,
                                contact_email=user_email,
                                contact_phone=user_phone,
                                contact_fax=user_fax,
                                p_password_raw=password
                            )                    
                            user = User.objects.create(email=user_email, username=user_email,first_name=user_name)
                            user.role.add(Role.objects.get(role='WarehouseManager'))
                            user.is_warehouse_manager=True
                            user.is_active=True
                            user.set_password(password)
                            user.password_raw = password
                            user.save()

                            # Log the action for user creation
                            log_type, log_status, log_device = "WarehouseManager", "Added", "Web"
                            log_idd, log_name = warehouse_user.id, user_name
                            log_email = user_email
                            log_details = (f"warehouse_id = {warehouse.id} | warehouse = {warehouse.name} | "
                                            f"user_name= {user_name} | user_email = {user_email} | "
                                            f"user_phone = {user_phone} | user_fax = {user_fax} | password_raw = {password}")
                            logtable = LogTable(
                                log_type=log_type, log_status=log_status, log_idd=log_idd, log_name=log_name,
                                action_by_userid=action_by_userid, action_by_username=action_by_username,
                                action_by_email=action_by_email, action_by_role=action_by_role, log_email=log_email,
                                log_details=log_details, log_device=log_device
                            )
                            logtable.save()

                        return redirect('list-warehouse')                

                return render(request, 'distributor/add_warehouse.html', context)
            else:
                messages.error(request, "Not a valid request.")
                return redirect("dashboard")
        else:
            return redirect('login')
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/add_warehouse.html', context)


@login_required()
def list_warehouse(request):
    context = {}
    try:
        if request.user.is_authenticated:
            warehouse = []
            search_name = request.GET.get('search_name', '')
            if 'Grower' in request.user.get_role() and not request.user.is_superuser:
                pass
            elif request.user.is_consultant:
                pass
            elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
                warehouse = WarehouseUser.objects.all().select_related('warehouse').prefetch_related('warehouse__distributor_set')
                if search_name:
                    warehouse = warehouse.filter(Q(contact_name__icontains=search_name) | Q(warehouse__name__icontains=search_name)| Q(contact_email__icontains=search_name))
                    context['search_name'] = search_name
            elif request.user.is_warehouse_manager:
                warehouse_user= WarehouseUser.objects.filter(contact_email=request.user.email).select_related('warehouse').prefetch_related('warehouse__distributor_set').first()
                entity_name = warehouse_user.warehouse
                warehouse = WarehouseUser.objects.filter(warehouse=entity_name).select_related('warehouse').prefetch_related('warehouse__distributor_set')
                if search_name:
                    warehouse = warehouse.filter(Q(contact_name__icontains=search_name) | Q(warehouse__name__icontains=search_name)| Q(contact_email__icontains=search_name))
                    context['search_name'] = search_name

            elif request.user.is_distributor:
                distributor_user = DistributorUser.objects.filter(contact_email=request.user.email).select_related('distributor').first()
                warehouse_queryset = distributor_user.distributor.warehouse.all()  # Get the warehouses
                warehouse = WarehouseUser.objects.filter(warehouse__in=warehouse_queryset).select_related('warehouse').prefetch_related('warehouse__distributor_set')
                print(warehouse)

                # Optionally, filter based on the search criteria
                if search_name:
                    warehouse = warehouse.filter(
                        Q(name__icontains=search_name) |
                        Q(location__icontains=search_name) |
                        Q(warehouse_user__contact_name__icontains=search_name) |
                        Q(warehouse_user__contact_email__icontains=search_name)
            )
                    context['search_name'] = search_name
            else:
                messages.error(request, "Not a valid request")
                return redirect("dashboard")

            # Pagination
            warehouse = warehouse.order_by("-id")
            paginator = Paginator(warehouse, 20) 
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            context['page_obj'] = page_obj          

            return render(request, 'distributor/list_warehouse.html', context)
        else:
            return redirect('login')
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/list_warehouse.html', context)


@login_required()
def warehouse_update(request,pk):
    context = {}
    try:
        if request.user.is_authenticated:        
            if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
                obj_id = WarehouseUser.objects.get(id=pk)
                print(obj_id)
                context['p_user'] = obj_id
                warehouse = Warehouse.objects.get(id=obj_id.warehouse.id)

                context['form'] = WarehouseForm(instance=warehouse)
                warehouse_email = obj_id.contact_email
                user = User.objects.get(email=warehouse_email)
                if request.method == 'POST':                   
                    form = WarehouseForm( request.POST,instance=warehouse)                    
                    if form.is_valid(): 
                        distributors = form.cleaned_data['distributor']  
                        customers = form.cleaned_data['customers']                       
                                            
                        email_update = request.POST.get('contact_email1')
                        name_update = request.POST.get('contact_name1')
                        # country_code = request.POST.get('country_code1')
                        phone_number = request.POST.get('phone_number1')
                        phone_update = phone_number
                        fax_update = request.POST.get('contact_fax1')
                        
                        obj_id.contact_name = name_update
                        obj_id.contact_email = email_update
                        obj_id.contact_phone = phone_update
                        obj_id.contact_fax = fax_update
                        obj_id.save()

                        Customer.objects.filter(warehouse=warehouse).exclude(id__in=[customer.id for customer in customers]).update(warehouse=None)
            
                        # Then, set the current warehouse for each selected customer
                        for customer in customers:
                            customer.warehouse = warehouse
                            customer.save()                     
                        
                        current_distributors = warehouse.distributor_set.all()

                        for distributor in current_distributors:
                            if distributor not in distributors:
                                distributor.warehouse.remove(warehouse)

                        for distributor in distributors:
                            distributor.warehouse.add(warehouse)
                            
                        log_email = ''
                        if email_update != warehouse_email:
                            f_name = name_update
                            user.email = email_update
                            user.username = email_update
                            user.first_name = f_name
                            user.save()
                            form.save()
                            log_email = email_update
                        else :
                            f_name = name_update
                            user.first_name = f_name
                            user.save()
                            form.save()
                            log_email = obj_id.contact_email
                        form.save()
                        # 07-04-23 Log Table
                        log_type, log_status, log_device = "WarehouseUser", "Edited", "Web"
                        log_idd, log_name = obj_id.id, name_update
                        log_details = f"warehouse_id = {warehouse.id} | warehouse = {warehouse.name}  | contact_name= {name_update} | contact_email = {email_update} | contact_phone = {phone_update} | contact_fax = {fax_update}"
                        action_by_userid = request.user.id
                        userr = User.objects.get(pk=action_by_userid)
                        user_role = userr.role.all()
                        action_by_username = f'{userr.first_name} {userr.last_name}'
                        action_by_email = userr.username
                        if request.user.id == 1 :
                            action_by_role = "superuser"
                        else:
                            action_by_role = str(','.join([str(i.role) for i in user_role]))
                        logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                            action_by_userid=action_by_userid,action_by_username=action_by_username,
                                            action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                            log_details=log_details,log_device=log_device)
                        logtable.save()
                        return redirect('list-warehouse')
                return render(request, 'distributor/update_warehouse.html',context)
            # warehouse manager..........
            elif request.user.is_warehouse_manager:
                obj_id = WarehouseUser.objects.get(id=pk)
                print(obj_id)
                context['p_user'] = obj_id
                warehouse = Warehouse.objects.get(id=obj_id.warehouse.id)

                context['form'] = WarehouseForm(instance=warehouse)
                warehouse_email = obj_id.contact_email
                user = User.objects.get(email=warehouse_email)
                if request.method == 'POST':                   
                    form = WarehouseForm( request.POST,instance=warehouse)                    
                    if form.is_valid(): 
                        distributors = form.cleaned_data['distributor']  
                        customers = form.cleaned_data['customers']                       
                                            
                        email_update = request.POST.get('contact_email1')
                        name_update = request.POST.get('contact_name1')
                        # country_code = request.POST.get('country_code1')
                        phone_number = request.POST.get('phone_number1')
                        phone_update = phone_number
                        fax_update = request.POST.get('contact_fax1')
                        
                        obj_id.contact_name = name_update
                        obj_id.contact_email = email_update
                        obj_id.contact_phone = phone_update
                        obj_id.contact_fax = fax_update
                        obj_id.save()

                        Customer.objects.filter(warehouse=warehouse).exclude(id__in=[customer.id for customer in customers]).update(warehouse=None)
            
                        # Then, set the current warehouse for each selected customer
                        for customer in customers:
                            customer.warehouse = warehouse
                            customer.save()                     
                        
                        current_distributors = warehouse.distributor_set.all()

                        for distributor in current_distributors:
                            if distributor not in distributors:
                                distributor.warehouse.remove(warehouse)

                        for distributor in distributors:
                            distributor.warehouse.add(warehouse)
                            
                        log_email = ''
                        if email_update != warehouse_email:
                            f_name = name_update
                            user.email = email_update
                            user.username = email_update
                            user.first_name = f_name
                            user.save()
                            form.save()
                            log_email = email_update
                        else :
                            f_name = name_update
                            user.first_name = f_name
                            user.save()
                            form.save()
                            log_email = obj_id.contact_email
                        # 07-04-23 Log Table
                        log_type, log_status, log_device = "WarehouseUser", "Edited", "Web"
                        log_idd, log_name = obj_id.id, name_update
                        log_details = f"warehouse_id = {warehouse.id} | warehouse = {warehouse.name}  | contact_name= {name_update} | contact_email = {email_update} | contact_phone = {phone_update} | contact_fax = {fax_update}"
                        action_by_userid = request.user.id
                        userr = User.objects.get(pk=action_by_userid)
                        user_role = userr.role.all()
                        action_by_username = f'{userr.first_name} {userr.last_name}'
                        action_by_email = userr.username
                        if request.user.id == 1 :
                            action_by_role = "superuser"
                        else:
                            action_by_role = str(','.join([str(i.role) for i in user_role]))
                        logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                            action_by_userid=action_by_userid,action_by_username=action_by_username,
                                            action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                            log_details=log_details,log_device=log_device)
                        logtable.save()
                        return redirect('list-warehouse')
                return render(request, 'distributor/update_warehouse.html',context)
            else:
                messages.error(request, "Not a valid request")
                return redirect("dashboard")
        else:
            return redirect('login')
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/update_warehouse.html',context)


@login_required()
def warehouse_change_password(request,pk):
    context={}
    try:
        # Superuser..............
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            warehouse = WarehouseUser.objects.get(id=pk)
            user = User.objects.get(email=warehouse.contact_email)
            context["userr"] = user
            if request.method == "POST":
                password1 = request.POST.get("password1")
                password2 = request.POST.get("password2")
                if len(password1) != 0 and len(password2) != 0 and password1 != None and password2 != None and password1 == password2:
                    # update_pass_user = User.objects.get(id=pk)
                    password = make_password(password1)
                    user.password = password
                    user.password_raw = password1
                    user.save()
                    warehouse.p_password_raw = password1
                    warehouse.save()
                    # 10-04-23 Log Table
                    log_type, log_status, log_device = "WarehouseUser", "Password changed", "Web"
                    log_idd, log_name = warehouse.id, warehouse.contact_name
                    log_email = warehouse.contact_email
                    log_details = f"warehouse_id = {warehouse.warehouse.id} | warehouse = {warehouse.warehouse.name} | contact_name= {warehouse.contact_name} | contact_email = {warehouse.contact_email} | contact_phone = {warehouse.contact_phone} | contact_fax = {warehouse.contact_fax}"
                    action_by_userid = request.user.id
                    user = User.objects.get(pk=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if request.user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                        log_details=log_details, log_device=log_device)
                    logtable.save()
                    messages.success(request,"Password changed successfully!")
            return render (request, 'distributor/warehouse_change_password.html', context)
        # Distributor...............
        elif request.user.is_warehouse_manager:
            warehouse = WarehouseUser.objects.get(id=pk)
            user = User.objects.get(email=warehouse.contact_email)
            context["userr"] = user
            if request.method == "POST":
                password1 = request.POST.get("password1")
                password2 = request.POST.get("password2")
                if len(password1) != 0 and len(password2) != 0 and password1 != None and password2 != None and password1 == password2:
                    # update_pass_user = User.objects.get(id=pk)
                    password = make_password(password1)
                    user.password = password
                    user.password_raw = password1
                    user.save()
                    warehouse.p_password_raw = password1
                    warehouse.save()
                    # 10-04-23 Log Table
                    log_type, log_status, log_device = "WarehouseUser", "Password changed", "Web"
                    log_idd, log_name = warehouse.id, warehouse.contact_name
                    log_email = warehouse.contact_email
                    log_details = f"warehouse_id = {warehouse.warehouse.id} | warehouse = {warehouse.warehouse.name} | contact_name= {warehouse.contact_name} | contact_email = {warehouse.contact_email} | contact_phone = {warehouse.contact_phone} | contact_fax = {warehouse.contact_fax}"
                    action_by_userid = request.user.id
                    user = User.objects.get(pk=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if request.user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                        log_details=log_details, log_device=log_device)
                    logtable.save()
                    messages.success(request,"Password changed successfully!")
        
        else:
            return redirect('dashboard')
        return render (request, 'distributor/warehouse_change_password.html', context)
    except Exception as e:
        context["error_messages"] = str(e)
        return render (request, 'distributor/warehouse_change_password.html', context)


# from apps.quickbooks_integration.models import QuickBooksToken
# @login_required()
# def add_customer(request):
#     context = {}
#     try:
#         if request.user.is_authenticated:
#             if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_distributor or request.user.is_warehouse_manager:
#                 try:
#                     token_instance = QuickBooksToken.objects.first()                                    
#                     refresh_token = token_instance.refresh_token
#                     if token_instance.is_token_expired():
#                         print("Token expired, refreshing...")
#                         new_access_token = refresh_quickbooks_token(refresh_token)
#                         if not new_access_token:
#                             return redirect(f"{reverse('quickbooks_login')}?next=add-customer")
#                         token_instance.access_token = new_access_token
#                         token_instance.expires_at = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
#                         token_instance.save()
#                 except QuickBooksToken.DoesNotExist:
#                     return redirect(f"{reverse('quickbooks_login')}?next=add-customer")
#                 if request.method == 'POST':
#                     form = CustomerForm(request.POST)
#                     if form.is_valid():
#                         name = form.cleaned_data.get('name')
#                         location = form.cleaned_data.get('location')
#                         latitude = form.cleaned_data.get('latitude')
#                         longitude = form.cleaned_data.get('longitude')
#                         billing_address = form.cleaned_data.get('billing_address')
#                         shipping_address = form.cleaned_data.get('shipping_address')
#                         credit_terms = form.cleaned_data.get('credit_terms')
#                         is_tax_payable = form.cleaned_data.get('is_tax_payable')
#                         tax_percentage = form.cleaned_data.get('tax_percentage')
#                         warehouse = form.cleaned_data.get('warehouse')
                        
#                         if not is_tax_payable:
#                             tax_percentage = None

#                         if Customer.objects.filter(name=name).exists():
#                             messages.error(request, "A customer with this name already exists.")
#                             return render(request, 'distributor/add_customer.html', {'form': form})

#                         customer = Customer(
#                             name=name,
#                             location=location,
#                             latitude=latitude,
#                             longitude=longitude,
#                             billing_address=billing_address,
#                             shipping_address=shipping_address,
#                             credit_terms=credit_terms,
#                             is_tax_payable=is_tax_payable,
#                             tax_percentage=tax_percentage,
#                             warehouse=warehouse
#                         )                        
#                         customer.save()
#                         document_names = request.POST.getlist('document_name[]')                   
                    
#                         for name in document_names:
#                             document = CustomerDocuments(
#                                 customer=customer,
#                                 document_name=name                          
#                             )
#                             document.save()

#                         # Log the action
#                         log_type, log_status, log_device = "Customer", "Added", "Web"
#                         log_idd, log_name = customer.id, name
#                         log_email = None
#                         log_details = (f"name = {name} | location = {location} | "
#                                        f"latitude = {latitude} | longitude = {longitude}")
#                         action_by_userid = request.user.id
#                         userr = User.objects.get(pk=action_by_userid)
#                         user_role = userr.role.all()
#                         action_by_username = f'{userr.first_name} {userr.last_name}'
#                         action_by_email = userr.username
#                         action_by_role = "superuser" if request.user.id == 1 else ','.join([str(i.role) for i in user_role])
                        
#                         logtable = LogTable(
#                             log_type=log_type, log_status=log_status, log_idd=log_idd, log_name=log_name,
#                             action_by_userid=action_by_userid, action_by_username=action_by_username,
#                             action_by_email=action_by_email, action_by_role=action_by_role, log_email=log_email,
#                             log_details=log_details, log_device=log_device
#                         )
#                         logtable.save()
#                         user_email = request.POST.get('user_email')                       
#                         country_code = request.POST.get('country_code')
#                         phone_number = request.POST.get('phone_number')
#                         user_phone = country_code + phone_number
                       
#                         user_fax = request.POST.get('user_fax')

#                         if CustomerUser.objects.filter(customer=customer).exists():                       
#                             messages.error(request, "A user is already associated with this customer.")
#                             return render(request, 'distributor/add_customer.html', context)

#                         if User.objects.filter(email=user_email).exists():                        
#                             messages.error(request, f'Email {user_email} already exists.')
#                         else:
#                             password = generate_random_password()                        
#                             customer_user = CustomerUser.objects.create(
#                                 customer=customer,
#                                 contact_name=user_email,
#                                 contact_email=user_email,
#                                 contact_phone=user_phone,
#                                 contact_fax=user_fax,
#                                 p_password_raw=password
#                             )                    
#                             user = User.objects.create(email=user_email, username=user_email, first_name=customer.name)
#                             user.role.add(Role.objects.get(role='Customer'))
#                             user.is_customer = True
#                             user.is_active = True
#                             user.set_password(password)
#                             user.password_raw = password
#                             user.save()
#                             try:                              
#                                 customer_data = {
#                                     "GivenName": customer.name.split()[0] if " " in customer.name else customer.name,
#                                     "FamilyName": customer.name.split()[-1] if " " in customer.name else "",
#                                     "DisplayName": customer.name,
#                                     "CompanyName": customer.name,
#                                     "PrimaryEmailAddr": {
#                                         "Address": customer_user.contact_email 
#                                     },
#                                     "PrimaryPhone": {
#                                         "FreeFormNumber": user_phone
#                                     },
#                                     "Fax": {
#                                         "FreeFormNumber":user_fax
#                                     },
#                                     "Taxable":is_tax_payable,
#                                     "BillAddr": {
#                                         "Line1": billing_address,
#                                         "City": "",  
#                                         "CountrySubDivisionCode": "", 
#                                         "PostalCode": ""  
#                                     },
#                                     "ShipAddr": {
#                                         "Line1": shipping_address,
#                                         "City": "",  
#                                         "CountrySubDivisionCode": "", 
#                                         "PostalCode": "" 
#                                     }
#                                 }
#                                 if customer.is_tax_payable:                                    
#                                     tax_agencies = get_tax_agencies(token_instance.realm_id, token_instance.access_token)                                    
#                                     tax_agency_id = tax_agencies[0]['Id'] if tax_agencies else None                                    
#                                     tax_rate_name = f"Custom Tax Rate for {customer.name}" 
#                                     tax_rate_percentage = tax_percentage 
#                                     request_body = {        
#                                         "TaxRateDetails": [
#                                             {
#                                             "RateValue": str(tax_rate_percentage), 
#                                             "TaxApplicableOn": "Sales", 
#                                             "TaxAgencyId": str(tax_agency_id), 
#                                             "TaxRateName": str(tax_rate_name)
#                                             }
#                                         ], 
#                                         "TaxCode": str(tax_rate_name)
#                                         }
#                                     custom_tax_rate = create_custom_tax_rate(token_instance.realm_id, token_instance.access_token, request_body)
#                                     if custom_tax_rate:
#                                         print(custom_tax_rate)
#                                         print("Custom tax rate added successfully")
#                                         custom_tax_rate_id = custom_tax_rate['TaxCodeId']
#                                         customer_data.update({"DefaultTaxCodeRef": {"value": str(custom_tax_rate_id) }})
#                                     else:
#                                         print("Failed to add custom tax rate.")                                   
                               
#                                 created_customer = create_customer(token_instance.realm_id, token_instance.access_token, customer_data)                                
#                                 if created_customer:                                
#                                     messages.success(request, "Customer added successfully and synced with QuickBooks.")
#                                 else:
#                                     messages.error(request, "Failed to sync with QuickBooks.")
#                             except Exception as qb_error:
#                                 messages.error(request, f"Error creating customer in QuickBooks: {str(qb_error)}")
#                                 return render(request, 'distributor/add_customer.html', {'form': form})
#                             # Log the action for user creation
#                             log_type, log_status, log_device = "CustomerUser", "Added", "Web"
#                             log_idd, log_name = customer_user.id, customer.name
#                             log_email = user_email
#                             log_details = (f"customer_id = {customer.id} | customer = {customer.name} | "
#                                            f"user_name= {customer.name} | user_email = {user_email} | "
#                                            f"user_phone = {user_phone} | user_fax = {user_fax} | password_raw = {password}")
#                             logtable = LogTable(
#                                 log_type=log_type, log_status=log_status, log_idd=log_idd, log_name=log_name,
#                                 action_by_userid=action_by_userid, action_by_username=action_by_username,
#                                 action_by_email=action_by_email, action_by_role=action_by_role, log_email=log_email,
#                                 log_details=log_details, log_device=log_device
#                             )
#                             logtable.save()

#                         return redirect('list-customer')
#                     else:
#                         messages.error(request, "Please correct the errors below.")
                
#                 else:
#                     form = CustomerForm()

#                 context["form"] = form
#                 return render(request, 'distributor/add_customer.html', context)
#             else:
#                 messages.error(request, "Not a valid request.")
#                 return redirect("dashboard")
#         else:
#             return redirect('login')
#     except Exception as e:
#         context["error_messages"] = str(e)
#         return render(request, 'distributor/add_customer.html', context)


@login_required()
def add_customer(request):
    context = {}
    try:
        if request.user.is_authenticated:
            if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_distributor or request.user.is_warehouse_manager:
                
                if request.method == 'POST':
                    form = CustomerForm(request.POST)
                    if form.is_valid():
                        name = form.cleaned_data.get('name')
                        location = form.cleaned_data.get('location')
                        latitude = form.cleaned_data.get('latitude')
                        longitude = form.cleaned_data.get('longitude')
                        billing_address = form.cleaned_data.get('billing_address')
                        shipping_address = form.cleaned_data.get('shipping_address')
                        credit_terms = form.cleaned_data.get('credit_terms')
                        is_tax_payable = form.cleaned_data.get('is_tax_payable')
                        tax_percentage = form.cleaned_data.get('tax_percentage')
                        warehouse = form.cleaned_data.get('warehouse')
                        
                        if not is_tax_payable:
                            tax_percentage = None

                        if Customer.objects.filter(name=name).exists():
                            messages.error(request, "A customer with this name already exists.")
                            return render(request, 'distributor/add_customer.html', {'form': form})

                        customer = Customer(
                            name=name,
                            location=location,
                            latitude=latitude,
                            longitude=longitude,
                            billing_address=billing_address,
                            shipping_address=shipping_address,
                            credit_terms=credit_terms,
                            is_tax_payable=is_tax_payable,
                            tax_percentage=tax_percentage,
                            warehouse=warehouse
                        )                        
                        customer.save()
                        document_names = request.POST.getlist('document_name[]')                   
                    
                        for name in document_names:
                            document = CustomerDocuments(
                                customer=customer,
                                document_name=name                          
                            )
                            document.save()

                        # Log the action
                        log_type, log_status, log_device = "Customer", "Added", "Web"
                        log_idd, log_name = customer.id, name
                        log_email = None
                        log_details = (f"name = {name} | location = {location} | "
                                       f"latitude = {latitude} | longitude = {longitude}")
                        action_by_userid = request.user.id
                        userr = User.objects.get(pk=action_by_userid)
                        user_role = userr.role.all()
                        action_by_username = f'{userr.first_name} {userr.last_name}'
                        action_by_email = userr.username
                        action_by_role = "superuser" if request.user.id == 1 else ','.join([str(i.role) for i in user_role])
                        
                        logtable = LogTable(
                            log_type=log_type, log_status=log_status, log_idd=log_idd, log_name=log_name,
                            action_by_userid=action_by_userid, action_by_username=action_by_username,
                            action_by_email=action_by_email, action_by_role=action_by_role, log_email=log_email,
                            log_details=log_details, log_device=log_device
                        )
                        logtable.save()
                        user_email = request.POST.get('user_email')                       
                        country_code = request.POST.get('country_code')
                        phone_number = request.POST.get('phone_number')
                        user_phone = country_code + phone_number
                       
                        user_fax = request.POST.get('user_fax')

                        if CustomerUser.objects.filter(customer=customer).exists():                       
                            messages.error(request, "A user is already associated with this customer.")
                            return render(request, 'distributor/add_customer.html', context)

                        if User.objects.filter(email=user_email).exists():                        
                            messages.error(request, f'Email {user_email} already exists.')
                        else:
                            password = generate_random_password()                        
                            customer_user = CustomerUser.objects.create(
                                customer=customer,
                                contact_name=user_email,
                                contact_email=user_email,
                                contact_phone=user_phone,
                                contact_fax=user_fax,
                                p_password_raw=password
                            )                    
                            user = User.objects.create(email=user_email, username=user_email, first_name=customer.name)
                            user.role.add(Role.objects.get(role='Customer'))
                            user.is_customer = True
                            user.is_active = True
                            user.set_password(password)
                            user.password_raw = password
                            user.save()
                         
                            # Log the action for user creation
                            log_type, log_status, log_device = "CustomerUser", "Added", "Web"
                            log_idd, log_name = customer_user.id, customer.name
                            log_email = user_email
                            log_details = (f"customer_id = {customer.id} | customer = {customer.name} | "
                                           f"user_name= {customer.name} | user_email = {user_email} | "
                                           f"user_phone = {user_phone} | user_fax = {user_fax} | password_raw = {password}")
                            logtable = LogTable(
                                log_type=log_type, log_status=log_status, log_idd=log_idd, log_name=log_name,
                                action_by_userid=action_by_userid, action_by_username=action_by_username,
                                action_by_email=action_by_email, action_by_role=action_by_role, log_email=log_email,
                                log_details=log_details, log_device=log_device
                            )
                            logtable.save()

                        return redirect('list-customer')
                    else:
                        messages.error(request, "Please correct the errors below.")
                
                else:
                    form = CustomerForm()

                context["form"] = form
                return render(request, 'distributor/add_customer.html', context)
            else:
                messages.error(request, "Not a valid request.")
                return redirect("dashboard")
        else:
            return redirect('login')
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/add_customer.html', context)


@login_required()
def list_customer(request):
    context = {}
    try:
        if request.user.is_authenticated:
            customer = []
            search_name = request.GET.get('search_name', '')
            if 'Grower' in request.user.get_role() and not request.user.is_superuser:
                pass
            elif request.user.is_consultant:
                pass
            elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
                customer = CustomerUser.objects.all()
                if search_name:
                    customer = customer.filter(Q(contact_name__icontains=search_name) | Q(customer__name__icontains=search_name)| Q(contact_email__icontains=search_name))
                    context['search_name'] = search_name
            elif request.user.is_customer:
                customer_user= CustomerUser.objects.filter(contact_email=request.user.email).first()
                entity_name = customer_user.customer
                customer = CustomerUser.objects.filter(customer=entity_name)
                if search_name:
                    customer = customer.filter(Q(contact_name__icontains=search_name) | Q(customer__name__icontains=search_name)| Q(contact_email__icontains=search_name))
                    context['search_name'] = search_name
            else:
                messages.error(request, "Not a valid request")
                return redirect("dashboard")
            
            customers_with_unpaid_shipments = {}
            for cust in customer:                
                unpaid_shipments = WarehouseCustomerShipment.objects.filter(
                    customer_id=cust.customer.id,
                    is_paid=False
                ).exists()
                
                customers_with_unpaid_shipments[cust.id] = unpaid_shipments
            context['customers_with_unpaid_shipments'] = customers_with_unpaid_shipments           

            # Pagination
            customer = customer.order_by("-id")
            paginator = Paginator(customer, 20) 
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            context['page_obj'] = page_obj            

            return render(request, 'distributor/list_customer.html', context)
        else:
            return redirect('login')
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/list_customer.html', context)


# @login_required()
# def customer_update(request,pk):
#     context = {}
#     try:
#         if request.user.is_authenticated:
#             success_url = reverse('update-customer', kwargs={'pk': pk})
#             next_url = f"{success_url}"
#             redirect_url = f"{reverse('quickbooks_login')}?{urlencode({'next': next_url})}"
#             try:
#                 token_instance = QuickBooksToken.objects.first()                                    
#                 refresh_token = token_instance.refresh_token
#                 if token_instance.is_token_expired():
#                     print("Token expired, refreshing...")
#                     new_access_token = refresh_quickbooks_token(refresh_token)
#                     if not new_access_token:
#                         return redirect(redirect_url)
#                     token_instance.access_token = new_access_token
#                     token_instance.expires_at = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
#                     token_instance.save()
#             except QuickBooksToken.DoesNotExist:
#                 return redirect(redirect_url)        
#             if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() :
                
#                 obj_id = CustomerUser.objects.get(id=pk)
#                 print(obj_id)
#                 context['p_user'] = obj_id
#                 customer = Customer.objects.get(id=obj_id.customer.id)

#                 context['form'] = CustomerForm(instance=customer)
#                 customer_email = obj_id.contact_email
#                 user = User.objects.get(email=customer_email)
#                 if request.method == 'POST':                   
#                     form = CustomerForm( request.POST,instance=customer)   
                                   
#                     if form.is_valid(): 
#                         name = form.cleaned_data.get('name')
#                         location = form.cleaned_data.get('location')
#                         latitude = form.cleaned_data.get('latitude')
#                         longitude = form.cleaned_data.get('longitude')
#                         billing_address = form.cleaned_data.get('billing_address')
#                         shipping_address = form.cleaned_data.get('shipping_address')
#                         credit_terms = form.cleaned_data.get('credit_terms')
#                         is_tax_payable = form.cleaned_data.get('is_tax_payable')
#                         tax_percentage = form.cleaned_data.get('tax_percentage') 
#                         warehouse = form.cleaned_data.get('warehouse')

#                         customer.name=name
#                         customer.location = location
#                         customer.latitude=latitude
#                         customer.longitude=longitude
#                         customer.billing_address=billing_address
#                         customer.shipping_address=shipping_address
#                         customer.credit_terms=credit_terms
#                         customer.is_tax_payable=is_tax_payable
#                         customer.tax_percentage=tax_percentage
#                         customer.warehouse = warehouse
#                         customer.save()                       
                                           
#                         email_update = request.POST.get('contact_email1')                                               
#                         phone_number = request.POST.get('phone_number1')
#                         phone_update = phone_number
#                         fax_update = request.POST.get('contact_fax1')
                        
#                         obj_id.contact_name = email_update
#                         obj_id.contact_email = email_update
#                         obj_id.contact_phone = phone_update
#                         obj_id.contact_fax = fax_update
#                         obj_id.save()
#                         print(obj_id)
#                         log_email = ''
#                         if email_update != customer_email:
#                             f_name = customer.name
#                             user.email = email_update
#                             user.username = email_update
#                             user.first_name = customer.name
#                             user.save()
#                             form.save()
#                             log_email = email_update
#                         else :
#                             f_name = customer.name
#                             user.first_name = f_name
#                             user.save()
#                             form.save()
#                             log_email = obj_id.contact_email
#                         form.save()                       

#                         # Fetch the latest sync token for the customer
#                         customerId = customer.quickbooks_id
#                         print(customerId, "customer_id")
#                         customer_data = get_customer_data(customerId)
#                         sync_token = customer_data.get("Customer", {}).get("SyncToken")
#                         custom_tax_rate = customer_data.get('Customer', {}).get('DefaultTaxCodeRef', {}).get('value', '')
                        
#                         if sync_token:
#                             # Prepare data for updating the customer in QuickBooks
#                             quickbooks_customer_data = {
#                                 "Id": customer_data["Customer"]["Id"],
#                                 "SyncToken": sync_token,
#                                 "DisplayName": name,
#                                 "CompanyName": name,
#                                 "PrimaryEmailAddr": {
#                                     "Address": email_update
#                                 },
#                                 "PrimaryPhone": {
#                                     "FreeFormNumber": phone_number
#                                 },                                                               
#                                 "Fax": {
#                                     "FreeFormNumber": fax_update
#                                 },
#                                 "Taxable":is_tax_payable,
#                                 "BillAddr": {
#                                     "Line1": billing_address,
#                                     "City": "",  
#                                     "CountrySubDivisionCode": "", 
#                                     "PostalCode": ""  
#                                 },
#                                 "ShipAddr": {
#                                     "Line1": shipping_address,
#                                     "City": "",  
#                                     "CountrySubDivisionCode": "", 
#                                     "PostalCode": "" 
#                                 }
#                             }
#                             if customer.is_tax_payable :
#                                 if custom_tax_rate:
#                                     quickbooks_customer_data.update({ "DefaultTaxCodeRef":{
#                                         "value":str(custom_tax_rate)
#                                     }})
#                                 else:
#                                     tax_agencies = get_tax_agencies(token_instance.realm_id, token_instance.access_token)                                    
#                                     tax_agency_id = tax_agencies[0]['Id'] if tax_agencies else None                                    
#                                     tax_rate_name = f"Custom Tax Rate for {customer.name}" 
#                                     tax_rate_percentage = tax_percentage 
#                                     request_body = {        
#                                         "TaxRateDetails": [
#                                             {
#                                             "RateValue": str(tax_rate_percentage), 
#                                             "TaxApplicableOn": "Sales", 
#                                             "TaxAgencyId": str(tax_agency_id), 
#                                             "TaxRateName": str(tax_rate_name)
#                                             }
#                                         ], 
#                                         "TaxCode": str(tax_rate_name)
#                                         }
#                                     custom_tax_rate = create_custom_tax_rate(token_instance.realm_id, token_instance.access_token, request_body)
#                                     if custom_tax_rate:
#                                         print(custom_tax_rate)
#                                         print("Custom tax rate added successfully")
#                                         custom_tax_rate_id = custom_tax_rate['TaxCodeId']
#                                         customer_data.update({"DefaultTaxCodeRef": {"value": str(custom_tax_rate_id) }})
#                                     else:
#                                         print("Failed to add custom tax rate.")
                            
#                             # Update the customer in QuickBooks
#                             update_response = update_customer(
#                                 token_instance.realm_id, token_instance.access_token, customerId, sync_token, quickbooks_customer_data
#                             )

#                             if update_response:
#                                 print("Customer updated successfully in QuickBooks.")
#                                 messages.success(request, "Customer updated successfully in QuickBooks.")
#                             else:
#                                 print("Failed to update customer in QuickBooks.")
#                                 messages.error(request, "Falied to update customer in QuickBooks.")
#                         else:
#                             print("Failed to retrieve SyncToken for updating QuickBooks customer.")
                        
#                         # 07-04-23 Log Table
#                         log_type, log_status, log_device = "CustomerUser", "Edited", "Web"
#                         log_idd, log_name = obj_id.id, customer.name
#                         log_details = f"customer_id = {customer.id} | customer = {customer.name}  | contact_name= {customer.name} | contact_email = {email_update} | contact_phone = {phone_update} | contact_fax = {fax_update}"
#                         action_by_userid = request.user.id
#                         userr = User.objects.get(pk=action_by_userid)
#                         user_role = userr.role.all()
#                         action_by_username = f'{userr.first_name} {userr.last_name}'
#                         action_by_email = userr.username
#                         if request.user.id == 1 :
#                             action_by_role = "superuser"
#                         else:
#                             action_by_role = str(','.join([str(i.role) for i in user_role]))
#                         logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
#                                             action_by_userid=action_by_userid,action_by_username=action_by_username,
#                                             action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
#                                             log_details=log_details,log_device=log_device)
#                         logtable.save()
#                         return redirect('list-customer')
#                 return render(request, 'distributor/update_customer.html',context)
#             # customer..........
#             elif request.user.is_customer:
#                 obj_id = CustomerUser.objects.get(id=pk)
#                 context['p_user'] = obj_id
#                 customer = Customer.objects.get(id=obj_id.customer.id)

#                 context['form'] = CustomerForm(instance=customer)
#                 customer_email = obj_id.contact_email
#                 user = User.objects.get(email=customer_email)
#                 if request.method == 'POST':
#                     form = CustomerForm( request.POST,instance=customer)
#                     if form.is_valid():
#                         name = form.cleaned_data.get('name')
#                         location = form.cleaned_data.get('location')
#                         latitude = form.cleaned_data.get('latitude')
#                         longitude = form.cleaned_data.get('longitude')
#                         billing_address = form.cleaned_data.get('billing_address')
#                         shipping_address = form.cleaned_data.get('shipping_address')
#                         credit_terms = form.cleaned_data.get('credit_terms')
#                         is_tax_payable = form.cleaned_data.get('is_tax_payable')
#                         tax_percentage = form.cleaned_data.get('tax_percentage')

#                         email_update = request.POST.get('contact_email1')
                        
#                         # country_code = request.POST.get('country_code1')
#                         phone_number = request.POST.get('phone_number1')
#                         phone_update = phone_number
#                         fax_update = request.POST.get('contact_fax1')
#                         obj_id.contact_name = email_update
#                         obj_id.contact_email = email_update
#                         obj_id.contact_phone = phone_update
#                         obj_id.contact_fax = fax_update
#                         obj_id.save()
#                         log_email = ''
#                         if email_update != customer_email:
#                             f_name = customer.name
#                             user.email = email_update
#                             user.username = email_update
#                             user.first_name = f_name
#                             user.save()
#                             form.save()
#                             log_email = email_update
#                         else :
#                             f_name = customer.name
#                             user.first_name = f_name
#                             user.save()
#                             form.save()
#                             log_email = obj_id.contact_email
#                         form.save()

#                         # Fetch the latest sync token for the customer
#                         customerId = customer.quickbooks_id
#                         customer_data = get_customer_data(customerId)
#                         sync_token = customer_data.get("Customer", {}).get("SyncToken")
#                         custom_tax_rate = customer_data.get('Customer', {}).get('DefaultTaxCodeRef', {}).get('value', '')
#                         if sync_token:
#                             # Prepare data for updating the customer in QuickBooks
#                             quickbooks_customer_data = {
#                                 "Id": customer_data["Customer"]["Id"],
#                                 "SyncToken": sync_token,
#                                 "DisplayName": name,
#                                 "CompanyName": name,
#                                 "PrimaryEmailAddr": {
#                                     "Address": email_update
#                                 },
#                                 "PrimaryPhone": {
#                                     "FreeFormNumber": phone_number
#                                 },
                                
#                                 "Fax": {
#                                     "FreeFormNumber": fax_update
#                                 },
#                                 "BillAddr": {
#                                     "Line1": billing_address,
#                                     "City": "",  
#                                     "CountrySubDivisionCode": "", 
#                                     "PostalCode": ""  
#                                 },
#                                 "ShipAddr": {
#                                     "Line1": shipping_address,
#                                     "City": "",  
#                                     "CountrySubDivisionCode": "", 
#                                     "PostalCode": "" 
#                                 }
#                             }                                                       
#                             if customer.is_tax_payable :
#                                 if custom_tax_rate:
#                                     quickbooks_customer_data.update({ "DefaultTaxCodeRef":{
#                                         "value":str(custom_tax_rate)
#                                     }})
#                                 else:
#                                     tax_agencies = get_tax_agencies(token_instance.realm_id, token_instance.access_token)                                    
#                                     tax_agency_id = tax_agencies[0]['Id'] if tax_agencies else None                                    
#                                     tax_rate_name = f"Custom Tax Rate for {customer.name}" 
#                                     tax_rate_percentage = tax_percentage 
#                                     request_body = {        
#                                         "TaxRateDetails": [
#                                             {
#                                             "RateValue": str(tax_rate_percentage), 
#                                             "TaxApplicableOn": "Sales", 
#                                             "TaxAgencyId": str(tax_agency_id), 
#                                             "TaxRateName": str(tax_rate_name)
#                                             }
#                                         ], 
#                                         "TaxCode": str(tax_rate_name)
#                                         }
#                                     custom_tax_rate = create_custom_tax_rate(token_instance.realm_id, token_instance.access_token, request_body)
#                                     if custom_tax_rate:
#                                         print(custom_tax_rate)
#                                         print("Custom tax rate added successfully")
#                                         custom_tax_rate_id = custom_tax_rate['TaxCodeId']
#                                         customer_data.update({"DefaultTaxCodeRef": {"value": str(custom_tax_rate_id) }})
#                                     else:
#                                         print("Failed to add custom tax rate.")
                            
#                             # Update the customer in QuickBooks
#                             update_response = update_customer(
#                                 token_instance.realm_id, token_instance.access_token, customer.id, quickbooks_customer_data
#                             )

#                             if update_response:
#                                 print("Customer updated successfully in QuickBooks.")
#                                 messages.success(request, "Customer updated successfully in QuickBooks.")
#                             else:
#                                 print("Failed to update customer in QuickBooks.")
#                                 messages.error(request, "Failed to update Customer in QuickBooks.")
#                         else:
#                             print("Failed to retrieve SyncToken for updating QuickBooks customer.")
#                         # 07-04-23 Log Table
#                         log_type, log_status, log_device = "CustomerUser", "Edited", "Web"
#                         log_idd, log_name = obj_id.id, customer.name
#                         log_details = f"customer_id = {customer.id} | customer = {customer.name}  | contact_name= {customer.name} | contact_email = {email_update} | contact_phone = {phone_update} | contact_fax = {fax_update}"
#                         action_by_userid = request.user.id
#                         userr = User.objects.get(pk=action_by_userid)
#                         user_role = userr.role.all()
#                         action_by_username = f'{userr.first_name} {userr.last_name}'
#                         action_by_email = userr.username
#                         if request.user.id == 1 :
#                             action_by_role = "superuser"
#                         else:
#                             action_by_role = str(','.join([str(i.role) for i in user_role]))
#                         logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
#                                             action_by_userid=action_by_userid,action_by_username=action_by_username,
#                                             action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
#                                             log_details=log_details,log_device=log_device)
#                         logtable.save()
#                         return redirect('list-customer')
#                 return render(request, 'distributor/update_customer.html',context)
#             else:
#                 messages.error(request, "Not a valid request")
#                 return redirect("dashboard")
#         else:
#             return redirect('login')
#     except Exception as e:
#         context["error_messages"] = str(e)
#         return render(request, 'distributor/update_customer.html',context)


@login_required()
def customer_update(request,pk):
    context = {}
    try:
        if request.user.is_authenticated:
                   
            if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() :
                
                obj_id = CustomerUser.objects.get(id=pk)
                print(obj_id)
                context['p_user'] = obj_id
                customer = Customer.objects.get(id=obj_id.customer.id)

                context['form'] = CustomerForm(instance=customer)
                customer_email = obj_id.contact_email
                user = User.objects.get(email=customer_email)
                if request.method == 'POST':                   
                    form = CustomerForm( request.POST,instance=customer)   
                                   
                    if form.is_valid(): 
                        name = form.cleaned_data.get('name')
                        location = form.cleaned_data.get('location')
                        latitude = form.cleaned_data.get('latitude')
                        longitude = form.cleaned_data.get('longitude')
                        billing_address = form.cleaned_data.get('billing_address')
                        shipping_address = form.cleaned_data.get('shipping_address')
                        credit_terms = form.cleaned_data.get('credit_terms')
                        is_tax_payable = form.cleaned_data.get('is_tax_payable')
                        tax_percentage = form.cleaned_data.get('tax_percentage') 
                        warehouse = form.cleaned_data.get('warehouse')

                        customer.name=name
                        customer.location = location
                        customer.latitude=latitude
                        customer.longitude=longitude
                        customer.billing_address=billing_address
                        customer.shipping_address=shipping_address
                        customer.credit_terms=credit_terms
                        customer.is_tax_payable=is_tax_payable
                        customer.tax_percentage=tax_percentage
                        customer.warehouse = warehouse
                        customer.save()                       
                                           
                        email_update = request.POST.get('contact_email1')                                               
                        phone_number = request.POST.get('phone_number1')
                        phone_update = phone_number
                        fax_update = request.POST.get('contact_fax1')
                        
                        obj_id.contact_name = email_update
                        obj_id.contact_email = email_update
                        obj_id.contact_phone = phone_update
                        obj_id.contact_fax = fax_update
                        obj_id.save()
                        print(obj_id)
                        log_email = ''
                        if email_update != customer_email:
                            f_name = customer.name
                            user.email = email_update
                            user.username = email_update
                            user.first_name = customer.name
                            user.save()
                            form.save()
                            log_email = email_update
                        else :
                            f_name = customer.name
                            user.first_name = f_name
                            user.save()
                            form.save()
                            log_email = obj_id.contact_email
                        form.save()                  
                        # 07-04-23 Log Table
                        log_type, log_status, log_device = "CustomerUser", "Edited", "Web"
                        log_idd, log_name = obj_id.id, customer.name
                        log_details = f"customer_id = {customer.id} | customer = {customer.name}  | contact_name= {customer.name} | contact_email = {email_update} | contact_phone = {phone_update} | contact_fax = {fax_update}"
                        action_by_userid = request.user.id
                        userr = User.objects.get(pk=action_by_userid)
                        user_role = userr.role.all()
                        action_by_username = f'{userr.first_name} {userr.last_name}'
                        action_by_email = userr.username
                        if request.user.id == 1 :
                            action_by_role = "superuser"
                        else:
                            action_by_role = str(','.join([str(i.role) for i in user_role]))
                        logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                            action_by_userid=action_by_userid,action_by_username=action_by_username,
                                            action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                            log_details=log_details,log_device=log_device)
                        logtable.save()
                        return redirect('list-customer')
                return render(request, 'distributor/update_customer.html',context)
            # customer..........
            elif request.user.is_customer:
                obj_id = CustomerUser.objects.get(id=pk)
                context['p_user'] = obj_id
                customer = Customer.objects.get(id=obj_id.customer.id)

                context['form'] = CustomerForm(instance=customer)
                customer_email = obj_id.contact_email
                user = User.objects.get(email=customer_email)
                if request.method == 'POST':
                    form = CustomerForm( request.POST,instance=customer)
                    if form.is_valid():
                        name = form.cleaned_data.get('name')
                        location = form.cleaned_data.get('location')
                        latitude = form.cleaned_data.get('latitude')
                        longitude = form.cleaned_data.get('longitude')
                        billing_address = form.cleaned_data.get('billing_address')
                        shipping_address = form.cleaned_data.get('shipping_address')
                        credit_terms = form.cleaned_data.get('credit_terms')
                        is_tax_payable = form.cleaned_data.get('is_tax_payable')
                        tax_percentage = form.cleaned_data.get('tax_percentage')

                        email_update = request.POST.get('contact_email1')
                        
                        # country_code = request.POST.get('country_code1')
                        phone_number = request.POST.get('phone_number1')
                        phone_update = phone_number
                        fax_update = request.POST.get('contact_fax1')
                        obj_id.contact_name = email_update
                        obj_id.contact_email = email_update
                        obj_id.contact_phone = phone_update
                        obj_id.contact_fax = fax_update
                        obj_id.save()
                        log_email = ''
                        if email_update != customer_email:
                            f_name = customer.name
                            user.email = email_update
                            user.username = email_update
                            user.first_name = f_name
                            user.save()
                            form.save()
                            log_email = email_update
                        else :
                            f_name = customer.name
                            user.first_name = f_name
                            user.save()
                            form.save()
                            log_email = obj_id.contact_email
                        form.save()

                        # 07-04-23 Log Table
                        log_type, log_status, log_device = "CustomerUser", "Edited", "Web"
                        log_idd, log_name = obj_id.id, customer.name
                        log_details = f"customer_id = {customer.id} | customer = {customer.name}  | contact_name= {customer.name} | contact_email = {email_update} | contact_phone = {phone_update} | contact_fax = {fax_update}"
                        action_by_userid = request.user.id
                        userr = User.objects.get(pk=action_by_userid)
                        user_role = userr.role.all()
                        action_by_username = f'{userr.first_name} {userr.last_name}'
                        action_by_email = userr.username
                        if request.user.id == 1 :
                            action_by_role = "superuser"
                        else:
                            action_by_role = str(','.join([str(i.role) for i in user_role]))
                        logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                            action_by_userid=action_by_userid,action_by_username=action_by_username,
                                            action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                            log_details=log_details,log_device=log_device)
                        logtable.save()
                        return redirect('list-customer')
                return render(request, 'distributor/update_customer.html',context)
            else:
                messages.error(request, "Not a valid request")
                return redirect("dashboard")
        else:
            return redirect('login')
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/update_customer.html',context)


@login_required()
def customer_change_password(request,pk):
    context={}
    try:
        # Superuser..............
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_customer:
            customer = CustomerUser.objects.get(id=pk)
            user = User.objects.get(email=customer.contact_email)
            context["userr"] = user
            if request.method == "POST":
                password1 = request.POST.get("password1")
                password2 = request.POST.get("password2")
                if len(password1) != 0 and len(password2) != 0 and password1 != None and password2 != None and password1 == password2:
                    # update_pass_user = User.objects.get(id=pk)
                    password = make_password(password1)
                    user.password = password
                    user.password_raw = password1
                    user.save()
                    customer.p_password_raw = password1
                    customer.save()
                    # 10-04-23 Log Table
                    log_type, log_status, log_device = "CustomerUser", "Password changed", "Web"
                    log_idd, log_name = customer.id, customer.contact_name
                    log_email = customer.contact_email
                    log_details = f"customer_id = {customer.customer.id} | customer = {customer.customer.name} | contact_name= {customer.contact_name} | contact_email = {customer.contact_email} | contact_phone = {customer.contact_phone} | contact_fax = {customer.contact_fax}"
                    action_by_userid = request.user.id
                    user = User.objects.get(pk=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if request.user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                        log_details=log_details, log_device=log_device)
                    logtable.save()
                    messages.success(request,"Password changed successfully!")
            return render (request, 'distributor/customer_change_password.html', context)
        # Distributor...............
        elif request.user.is_customer:
            customer = CustomerUser.objects.get(id=pk)
            user = User.objects.get(email=customer.contact_email)
            context["userr"] = user
            if request.method == "POST":
                password1 = request.POST.get("password1")
                password2 = request.POST.get("password2")
                if len(password1) != 0 and len(password2) != 0 and password1 != None and password2 != None and password1 == password2:
                    # update_pass_user = User.objects.get(id=pk)
                    password = make_password(password1)
                    user.password = password
                    user.password_raw = password1
                    user.save()
                    customer.p_password_raw = password1
                    customer.save()
                    # 10-04-23 Log Table
                    log_type, log_status, log_device = "CustomerUser", "Password changed", "Web"
                    log_idd, log_name = customer.id, customer.contact_name
                    log_email = customer.contact_email
                    log_details = f"customer_id = {customer.customer.id} | customer = {customer.customer.name} | contact_name= {customer.contact_name} | contact_email = {customer.contact_email} | contact_phone = {customer.contact_phone} | contact_fax = {customer.contact_fax}"
                    action_by_userid = request.user.id
                    user = User.objects.get(pk=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if request.user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                        log_details=log_details, log_device=log_device)
                    logtable.save()
                    messages.success(request,"Password changed successfully!")
        
        else:
            return redirect('dashboard')
        return render (request, 'distributor/customer_change_password.html', context)
    except Exception as e:
        context["error_messages"] = str(e)
        return render (request, 'distributor/customer_change_password.html', context)


@login_required()
def customer_upload_documents(request, pk):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() :            
            customer = Customer.objects.filter(id=pk).first()
            documents = CustomerDocuments.objects.filter(customer=customer)
            context["documents"] = documents
            print(customer)
            if request.method == "POST":    
                delete_document_ids = request.POST.getlist('delete_document_ids[]')
                print(delete_document_ids)
                for document_id in delete_document_ids:
                    try:
                        document = CustomerDocuments.objects.get(id=document_id)
                        document.delete()  # Delete the document from the database
                    except CustomerDocuments.DoesNotExist:
                        pass

                document_ids =  request.POST.getlist('document_ids')
                for document_id in document_ids:
                    document_status = f'document_status_{document_id}'
                    if document_status in request.POST:                            
                        document_stat = request.POST.get(document_status)                         
                        
                        document = CustomerDocuments.objects.filter(id=document_id).first()
                        document.document_status = document_stat  # Assign the file to the FileField
                        document.save()                                
                         
                document_names = request.POST.getlist('document_name[]')  
                if document_names:                     
                    for i, name in enumerate(document_names):
                        # Check if there's a corresponding document ID
                        if i < len(document_ids):
                            document_id = document_ids[i]
                            # Update existing document
                            document = CustomerDocuments.objects.filter(id=document_id).first()
                            if document:
                                document.document_name = name  # Update the name
                                document.save()
                        else:
                            # Create new document if the document ID does not exist
                            CustomerDocuments.objects.create(customer=customer, document_name=name)

                return redirect('list-customer')
            return render(request, 'distributor/customer_document_upload.html', context)
        elif request.user.is_customer :  
            customer = Customer.objects.filter(id=pk).first()
            documents = CustomerDocuments.objects.filter(customer=customer)
            context["documents"] = documents
            print(customer)
            if request.method == "POST": 
                document_ids = request.POST.getlist('document_ids')        
                for document_id in document_ids:
                    file_field_name = f'document_file_{document_id}'
                    
                    if file_field_name in request.FILES:
                        uploaded_file = request.FILES[file_field_name]  
                        try:
                            document = CustomerDocuments.objects.get(id=document_id)
                            document.file = uploaded_file  
                            document.save()
                            
                        except CustomerDocuments.DoesNotExist:
                            
                            pass
                return redirect('list-customer')
            return render(request, 'distributor/customer_document_upload.html', context)
        else:
            return redirect('dashboard')
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/customer_document_upload.html', context)  


##########################QuickBooks Included##########################
# @login_required()
# def create_processor_shipment(request):
#     context = {}
#     try:
#         if request.user.is_authenticated:
#             try:
#                 from apps.quickbooks_integration.models import QuickBooksToken
#                 from apps.quickbooks_integration.views import refresh_quickbooks_token, create_purchase_order, update_purchase_order, get_purchase_order_data, get_chart_of_accounts
#                 token_instance = QuickBooksToken.objects.first()                                    
#                 refresh_token = token_instance.refresh_token
#                 if token_instance.is_token_expired():
#                     print("Token expired, refreshing...")
#                     new_access_token = refresh_quickbooks_token(refresh_token)
#                     if not new_access_token:
#                         return redirect(f"{reverse('quickbooks_login')}?next=add-processor-shipment")
#                     token_instance.access_token = new_access_token
#                     token_instance.expires_at = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
#                     token_instance.save()
#             except QuickBooksToken.DoesNotExist:
#                 return redirect(f"{reverse('quickbooks_login')}?next=add-processor-shipment")
            
#             if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
#                 current_time = timezone.now()
#                 contracts = AdminProcessorContract.objects.filter(contract_start_date__lte=current_time, end_date__gte=current_time).values('id','secret_key','processor_id','processor_type','processor_entity_name').order_by('-id')
                
#                 context["contracts"] = contracts
#                 context.update({
#                     "selected_contract": None,
#                     "crops": [],
#                     "milled_value": "None",
#                     "selected_processor_sku_id_list":[],
#                     "selected_destination": None,
#                     "warehouse_name" : None,
#                     "customer_name": None,
#                     "selected_customer_contract" : None              
#                 })
                
#                 if request.method == "POST":
#                     data = request.POST
#                     selected_contract = request.POST.get('selected_contract') 
#                     print(selected_contract)
#                     contract = AdminProcessorContract.objects.get(id=int(selected_contract))                   
#                     processor_id = contract.processor_id
#                     processor_type = contract.processor_type
#                     selected_sku_id = data.get('sender_sku_id')
#                     destination_type = data.get('selected_destination')
#                     destination_id = data.get('destination_id') 
#                     selected_crop = data.get('crop_id')   
#                     print(selected_crop, type(selected_crop))                
#                     context.update({
#                         "selected_contract":contract.id,
#                         "contract":contract,                        
#                         "selected_processor_id": processor_id,
#                         "carrier_type": data.get('carrier_type'),                    
#                         "outbound_type": data.get('outbound_type'),
#                         "purchase_order_name":data.get('purchase_order_name'),
#                         "purchase_order_number": data.get('purchase_order_number'),
#                         "lot_number": data.get('lot_number'),
#                         "sender_sku_id": selected_sku_id,
#                         "selected_destination": destination_type,
#                         "weight":data.get('weight'),
#                         "gross_weight":data.get('gross_weight'),
#                         "ship_weight":data.get('ship_weight'),
#                         "ship_quantity":data.get('ship_quantity'),
#                         "status":data.get('status'),
#                         "amount_unit":data.get('amount_unit') ,                         
#                         "final_payment_date":data.get('final_payment_date')              
                        
#                     })
#                     if selected_crop:
#                         selected_crop = int(selected_crop)
#                         context["selected_crop"] =selected_crop
#                     if destination_id:
#                         context["destination_id"] = int(destination_id)
#                     if selected_contract:
#                         context['crops'] = CropDetails.objects.filter(contract=contract).values('id', 'crop', 'crop_type')

#                     if destination_type == "customer" and destination_id and selected_crop:
                        
#                         crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first().crop
#                         crop_type = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first().crop_type                                              
#                         customer_contracts = AdminCustomerContract.objects.filter(customer_id=int(destination_id), customerContractCrop__crop=crop, customerContractCrop__crop_type=crop_type, contract_start_date__lte=current_time, end_date__gte=current_time)
                        
#                         context["customer_contracts"] = customer_contracts
#                     if processor_id and not data.get("save"):                                                                                       
                    
#                         if selected_sku_id and selected_crop:                            
#                             crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                             context["milled_value"] =  calculate_milled_volume(crop.crop, int(processor_id), processor_type, selected_sku_id)
#                             context["selected_sku"] = selected_sku_id
                        
#                         context["sender_sku_id_list"] = get_sku_list(int(processor_id),processor_type)["data"]
#                         if destination_type == 'warehouse':
#                             context['destination_list'] = Warehouse.objects.all().values('id','name')
#                         if destination_type == 'customer':
#                             context['destination_list'] = Customer.objects.filter(is_active=True).values('id','name')
#                         return render(request, 'distributor/create_outbound.html', context)
                    
                    
#                     else:                        
#                         if destination_type == 'warehouse':
#                             warehouse_id = Warehouse.objects.get(id=int(context.get('destination_id'))).id
#                             warehouse_name = Warehouse.objects.get(id=int(context.get('destination_id'))).name
#                             customer_id = None
#                             customer_name = None
#                             customer_contract = None
#                         else:
#                             warehouse_id = None
#                             warehouse_name = None
#                             customer_id = Customer.objects.get(id=int(context.get('destination_id'))).id
#                             customer_name = Customer.objects.get(id=int(context.get('destination_id'))).name
#                             selected_customer_contract = data.get('customer_contract')
#                             customer_contract = AdminCustomerContract.objects.filter(id=int(selected_customer_contract)).first()

#                         if data.get('carrier_type') == 'Truck/Trailer':
#                             if data.get('gross_weight') not in [None, 'null', ' ', ''] and data.get('ship_weight') not in [None, 'null', ' ', ''] and data.get('ship_quantity') not in [None, 'null', ' ', '']:
#                                 ship_quantity = int(data.get('ship_quantity'))
#                                 gross_weight = float(data.get('gross_weight'))
#                                 ship_weight = float(data.get('ship_weight'))                                    
#                                 net_weight = gross_weight - (ship_weight * ship_quantity)
#                             else:
#                                 context["error_messages"] = "Please provide Gross weight, Ship weight and Ship quantity."
#                                 return render(request, 'distributor/create_outbound.html', context)
                            
#                         elif data.get('carrier_type') == 'Rail Car':
                            
#                             gross_weight = 0
#                             ship_quantity = 1
#                             ship_weight = 0
#                             if data.get('weight') not in [None, 'null', ' ', '']:
#                                 net_weight = float(data.get('weight'))
#                             else:
#                                 context["error_messages"] = "Please provide Weight."
#                                 return render(request, 'distributor/create_outbound.html', context)
                            
#                         crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                         crop_name = crop.crop                        
#                         if crop.amount_unit == data.get('amount_unit'):                           
#                             contract_weight_left = float(crop.left_amount) - float(net_weight)
#                         else:                            
#                             if crop.amount_unit == "LBS" and data.get('amount_unit') == "MT":
#                                 net_weight_lbs = float(net_weight) * 2204.62
#                                 contract_weight_left = float(crop.left_amount) - net_weight_lbs 
#                             else:
#                                 net_weight_mt = float(net_weight) * 0.000453592
#                                 contract_weight_left = float(crop.left_amount) - net_weight_mt    

#                         outbound = ProcessorWarehouseShipment(
#                             contract=contract,
#                             processor_id=processor_id,
#                             processor_type=processor_type,
#                             processor_entity_name=contract.processor_entity_name,
#                             processor_sku_list=[selected_sku_id],
#                             crop_id = crop.id,
#                             crop = crop_name,
#                             carrier_type=data.get('carrier_type'),
#                             outbound_type=data.get('outbound_type'),
#                             purchase_order_name=data.get('purchase_order_name'),
#                             purchase_order_number=data.get('purchase_order_number'),
#                             lot_number=data.get('lot_number'),
#                             gross_weight=gross_weight,
#                             net_weight=net_weight,
#                             weight_unit=data.get('amount_unit'),
#                             ship_weight = ship_weight,
#                             ship_quantity=ship_quantity,
#                             contract_weight_left=contract_weight_left,
#                             status=data.get('status'),
#                             customer_id=customer_id,
#                             warehouse_id=warehouse_id,
#                             customer_name=customer_name,
#                             warehouse_name=warehouse_name,
#                             customer_contract=customer_contract
#                         )
#                         outbound.save()  
#                         if data.get('final_payment_date') not in [None, '', ' ', 'null']:
#                             final_payment_date = data.get('final_payment_date')
#                             outbound.final_payment_date=final_payment_date  
#                         outbound.save()                        
                        
#                         carrier_id = data.get('carrier_id')
#                         if carrier_id:
#                             CarrierDetails.objects.create(shipment=outbound, carrier_id=carrier_id)
                        
#                         files = request.FILES.getlist('files')
#                         for file in files:
#                             ProcessorWarehouseShipmentDocuments.objects.create(shipment=outbound, document_file=file)

#                         ## Send notification to the Destination.
#                         if outbound.warehouse_id not in [None, 'null', ' ', '']:                            
#                             all_user = WarehouseUser.objects.filter(warehouse_id=outbound.warehouse_id)                           
                            
#                             distributors = Distributor.objects.filter(warehouse__id=outbound.warehouse_id)                           
                            
#                             distributor_users = DistributorUser.objects.filter(distributor__in=distributors)
#                         else:                            
#                             all_user = CustomerUser.objects.filter(customer_id=outbound.customer_id)
#                             distributor_users = []                          
#                         all_users = list(all_user) + list(distributor_users)
#                         for user in all_users :
#                             msg = f'A shipment has been sent of {outbound.net_weight}{outbound.weight_unit} under Contract ID - {outbound.contract.secret_key}'
#                             get_user = User.objects.get(username=user.contact_email)
#                             notification_reason = 'New Shipment'
#                             redirect_url = "/warehouse/list-processor-shipment/"
#                             save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
#                                 notification_reason=notification_reason)
#                             save_notification.save()                    
                      
#                         if processor_type == "T1":
#                             processor = Processor.objects.filter(id=int(processor_id)).first()  
#                         else:
#                             processor = Processor2.objects.filter(id=int(processor_id)).first() 
#                         purchase = Purchase(
#                             shipment=outbound,
#                             processor_id=processor_id,
#                             processor_type=processor_type,
#                             processor_entity_name=contract.processor_entity_name,
#                             quantity=outbound.net_weight,
#                             per_unit_rate=crop.per_unit_rate,
#                             amount=outbound.total_payment,
#                             currency='USD'
#                         )  
#                         purchase.save()
#                         item = ShipmentItem.objects.filter(
#                             item_name=crop.crop, item_type=crop.crop_type, 
#                             per_unit_price=crop.per_unit_rate
#                         ).first()  
#                         accounts = get_chart_of_accounts(token_instance.realm_id, token_instance.access_token)                       
                        
#                         ap_account_id = None
#                         for account in accounts:
#                             if account['AccountType'] == 'Accounts Payable' and account['AccountSubType'] == 'AccountsPayable':
#                                 ap_account_id = account['Id'] 
#                                 break                       

#                         if not ap_account_id:
#                             messages.error(request, "Accounts Payable account not found in QuickBooks.")
#                             return render(request, 'distributor/create_outbound.html', context)

#                         purchase_order_data = {
#                             "TotalAmt": float(purchase.amount),  
#                             "TxnDate": datetime.now().strftime('%Y-%m-%d'),  
#                             "Line": [
#                                 {
#                                     "DetailType": "ItemBasedExpenseLineDetail",
#                                     "Amount": float(purchase.amount),  
#                                     "ItemBasedExpenseLineDetail": {
#                                         "ItemRef": {
#                                             "value": str(item.quickbooks_id),  
#                                             "name": str(item.item_name) 
#                                         },
#                                         "Qty": float(outbound.net_weight),  
#                                         "UnitPrice": float(purchase.per_unit_rate), 
#                                         "TaxCodeRef": {
#                                             "value": "NON" 
#                                         },
#                                         "BillableStatus": "NotBillable"  
#                                     }
#                                 }
#                             ],
#                             "APAccountRef": {
#                                 "name": "Accounts Payable (A/P)", 
#                                 "value": str(ap_account_id) 
#                             },
#                             "VendorRef": {
#                                 "name": str(contract.processor_entity_name), 
#                                 "value": str(processor.quickbooks_id) 
#                             },                                                 
#                             'CurrencyRef': {
#                                 'value': 'USD', 
#                                 'name': 'United States Dollar'
#                             },
#                             "CustomField": [
#                                 {
#                                     "DefinitionId": '1',  
#                                     "Type": "StringType",  
#                                     "Name": "ShipmentId",
#                                     "StringValue": str(purchase.shipment.shipment_id)  
#                                 }
#                             ]
#                         }

#                         try:
#                             created_purchase_order = create_purchase_order(token_instance.realm_id, token_instance.access_token, purchase_order_data)                        
#                             if created_purchase_order:                                
#                                 messages.success(request, "Purchase order added successfully and synced with QuickBooks.")
#                             else:
#                                 messages.error(request, "Failed to create Purchase in QuickBooks.")
#                         except Exception as qb_error:
#                             print(qb_error)
#                             messages.error(request, f"Error creating purchase order in QuickBooks: {str(qb_error)}")
#                             return render(request, 'distributor/create_outbound.html', context)        
#                         return redirect('list-processor-shipment')   

#                 return render(request, 'distributor/create_outbound.html', context)    
#             elif request.user.is_processor:
#                 current_time = timezone.now()
#                 user = request.user
#                 processor_user = ProcessorUser.objects.filter(contact_email=user.email).first()
#                 processor =  Processor.objects.filter(id=processor_user.processor.id).first()
#                 processor_id =processor.id
#                 processor_type = 'T1'                
#                 contracts = AdminProcessorContract.objects.filter(processor_id=processor_id, processor_type=processor_type,contract_start_date__lte=current_time, end_date__gte=current_time).values('id','secret_key','processor_id','processor_type','processor_entity_name').order_by('-id')
                
#                 context["contracts"] = contracts
#                 context.update({
#                     "selected_contract": None,
#                     "crops": [],
#                     "milled_value": "None",
#                     "selected_processor_sku_id_list":[],
#                     "selected_destination": None,
#                     "warehouse_name" : None,
#                     "customer_name": None               
#                 })
                
#                 if request.method == "POST":
#                     data = request.POST
#                     selected_contract = request.POST.get('selected_contract') 
#                     print(selected_contract)
#                     contract = AdminProcessorContract.objects.get(id=int(selected_contract))                   
#                     processor_id = contract.processor_id
#                     processor_type = contract.processor_type
#                     selected_sku_id = data.get('sender_sku_id')
#                     destination_type = data.get('selected_destination')
#                     destination_id = data.get('destination_id') 
#                     selected_crop = data.get('crop_id')                   
#                     context.update({
#                         "selected_contract":contract.id,
#                         "contract":contract,                        
#                         "selected_processor_id": processor_id,
#                         "carrier_type": data.get('carrier_type'),                    
#                         "outbound_type": data.get('outbound_type'),
#                         "purchase_order_name":data.get('purchase_order_name'),
#                         "purchase_order_number": data.get('purchase_order_number'),
#                         "lot_number": data.get('lot_number'),
#                         "sender_sku_id": selected_sku_id,
#                         "selected_destination": destination_type,
#                         "weight":data.get('weight'),
#                         "gross_weight":data.get('gross_weight'),
#                         "ship_weight":data.get('ship_weight'),
#                         "ship_quantity":data.get('ship_quantity'),
#                         "status":data.get('status'),
#                         "amount_unit":data.get('amount_unit') ,                         
#                         "final_payment_date":data.get('final_payment_date')                
                        
#                     })
#                     if selected_crop:
#                         selected_crop = int(selected_crop)
#                         context["selected_crop"] =selected_crop
#                     if destination_id:
#                         context["destination_id"] = int(destination_id)

#                     if selected_contract:
#                         context['crops'] = CropDetails.objects.filter(contract=contract).values('id', 'crop', 'crop_type')

#                     if destination_type == "customer" and destination_id and selected_crop:
#                         crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first().crop
#                         crop_type = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first().crop_type                        
#                         customer_contracts = AdminCustomerContract.objects.filter(customer_id=int(destination_id), customerContractCrop__crop=crop, customerContractCrop__crop_type=crop_type, contract_start_date__lte=current_time, end_date__gte=current_time)
                     
#                         context["customer_contracts"] = customer_contracts

#                     if processor_id and not data.get("save"):                        
                        
#                         if selected_sku_id and selected_crop:
#                             crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                             context["milled_value"] =  calculate_milled_volume(crop.crop, int(processor_id), processor_type, selected_sku_id)
#                             context["selected_sku"] = selected_sku_id
                       
#                         context["sender_sku_id_list"] = get_sku_list(int(processor_id),processor_type)["data"]
#                         if destination_type == 'warehouse':
#                             context['destination_list'] = Warehouse.objects.all().values('id','name')
#                         if destination_type == 'customer':
#                             context['destination_list'] = Customer.objects.filter(is_active=True).values('id','name')
#                         return render(request, 'distributor/create_outbound.html', context)
#                     else:
#                         if destination_type == 'warehouse':
#                             warehouse_id = Warehouse.objects.get(id=int(context.get('destination_id'))).id
#                             warehouse_name = Warehouse.objects.get(id=int(context.get('destination_id'))).name
#                             customer_id = None
#                             customer_name = None
#                             customer_contract = None
#                         else:
#                             warehouse_id = None
#                             warehouse_name = None
#                             customer_id = Customer.objects.get(id=int(context.get('destination_id'))).id
#                             customer_name = Customer.objects.get(id=int(context.get('destination_id'))).name
#                             selected_customer_contract = data.get('customer_contract')
#                             customer_contract = AdminCustomerContract.objects.filter(id=int(selected_customer_contract)).first()

#                         if data.get('carrier_type') == 'Truck/Trailer':
#                             if data.get('gross_weight') not in [None, 'null', ' ', ''] and data.get('ship_weight') not in [None, 'null', ' ', ''] and data.get('ship_quantity') not in [None, 'null', ' ', '']:
#                                 ship_quantity = int(data.get('ship_quantity'))
#                                 gross_weight = float(data.get('gross_weight'))
#                                 ship_weight = float(data.get('ship_weight'))                                    
#                                 net_weight = gross_weight - (ship_weight * ship_quantity)
#                             else:
#                                 context["error_messages"] = "Please provide Gross weight, Ship weight and Ship quantity."
#                                 return render(request, 'distributor/create_outbound.html', context)
                            
#                         elif data.get('carrier_type') == 'Rail Car':
                            
#                             gross_weight = 0
#                             ship_quantity = 1
#                             ship_weight = 0
#                             if data.get('weight') not in [None, 'null', ' ', '']:
#                                 net_weight = float(data.get('weight'))
#                             else:
#                                 context["error_messages"] = "Please provide Weight."
#                                 return render(request, 'distributor/create_outbound.html', context)
                            
#                         crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                         crop_name = crop.crop
                        
#                         if crop.amount_unit == data.get('amount_unit'):
#                             contract_weight_left = float(crop.left_amount) - float(net_weight)
#                         else:
#                             if crop.amount_unit == "LBS" and data.get('amount_unit') == "MT":
#                                 net_weight_lbs = float(net_weight) * 2204.62
#                                 contract_weight_left = float(crop.left_amount) - net_weight_lbs 
#                             else:
#                                 net_weight_mt = float(net_weight) * 0.000453592
#                                 contract_weight_left = float(crop.left_amount) - net_weight_mt                         
                        
#                         outbound = ProcessorWarehouseShipment(
#                             contract=contract,
#                             processor_id=processor_id,
#                             processor_type=processor_type,
#                             processor_entity_name=contract.processor_entity_name,
#                             processor_sku_list=[selected_sku_id],
#                             crop_id = crop.id,
#                             crop = crop_name,
#                             carrier_type=data.get('carrier_type'),
#                             outbound_type=data.get('outbound_type'),
#                             purchase_order_name=data.get('purchase_order_name'),
#                             purchase_order_number=data.get('purchase_order_number'),
#                             lot_number=data.get('lot_number'),
#                             gross_weight=gross_weight,
#                             net_weight=net_weight,
#                             weight_unit=data.get('amount_unit'),
#                             ship_weight = ship_weight,
#                             ship_quantity=ship_quantity,
#                             contract_weight_left=contract_weight_left,
#                             status=data.get('status'),
#                             customer_id=customer_id,
#                             warehouse_id=warehouse_id,
#                             customer_name=customer_name,
#                             warehouse_name=warehouse_name,
#                             customer_contract=customer_contract
#                         )
#                         outbound.save() 
#                         if data.get('final_payment_date') not in [None, '', ' ', 'null']:
#                             final_payment_date = data.get('final_payment_date')
#                             outbound.final_payment_date=final_payment_date  
#                         outbound.save()                           
                        
#                         carrier_id = data.get('carrier_id')
#                         if carrier_id:
#                             CarrierDetails.objects.create(shipment=outbound, carrier_id=carrier_id)
                        
#                         files = request.FILES.getlist('files')
#                         for file in files:
#                             ProcessorWarehouseShipmentDocuments.objects.create(shipment=outbound, document_file=file)

#                         ## Send notification to the Destination.
#                         if outbound.warehouse_id not in [None, 'null', ' ', '']:                            
#                             all_user = WarehouseUser.objects.filter(warehouse_id=outbound.warehouse_id)                           
                            
#                             distributors = Distributor.objects.filter(warehouse__id=outbound.warehouse_id)                           
                            
#                             distributor_users = DistributorUser.objects.filter(distributor__in=distributors)
#                         else:                            
#                             all_user = CustomerUser.objects.filter(customer_id=outbound.customer_id)
#                             distributor_users = []                          
#                         all_users = list(all_user) + list(distributor_users)
                        
#                         for user in all_users :
#                             msg = f'A shipment has been sent of {outbound.net_weight}{outbound.weight_unit} under Contract ID - {outbound.contract.secret_key}'
#                             get_user = User.objects.get(username=user.contact_email)
#                             notification_reason = 'New Shipment'
#                             redirect_url = "/warehouse/list-processor-shipment/"
#                             save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
#                                 notification_reason=notification_reason)
#                             save_notification.save()                                             
                        
#                         processor = Processor.objects.filter(id=int(processor_id)).first() 
                        
#                         purchase = Purchase(
#                             shipment=outbound,
#                             processor_id=processor_id,
#                             processor_type=processor_type,
#                             processor_entity_name=contract.processor_entity_name,
#                             quantity=outbound.net_weight,
#                             per_unit_rate=crop.per_unit_rate,
#                             amount=outbound.total_payment,
#                             currency='USD'
#                         )  
#                         purchase.save()
#                         item = ShipmentItem.objects.filter(
#                             item_name=crop.crop, item_type=crop.crop_type, 
#                             per_unit_price=crop.per_unit_rate
#                         ).first()  
#                         accounts = get_chart_of_accounts(token_instance.realm_id, token_instance.access_token)                       
                        
#                         ap_account_id = None
#                         for account in accounts:
#                             if account['AccountType'] == 'Accounts Payable' and account['AccountSubType'] == 'AccountsPayable':
#                                 ap_account_id = account['Id'] 
#                                 break                       

#                         if not ap_account_id:
#                             messages.error(request, "Accounts Payable account not found in QuickBooks.")
#                             return render(request, 'distributor/create_outbound.html', context)

#                         purchase_order_data = {
#                             "TotalAmt": float(purchase.amount),  
#                             "TxnDate": datetime.now().strftime('%Y-%m-%d'),  
#                             "Line": [
#                                 {
#                                     "DetailType": "ItemBasedExpenseLineDetail",
#                                     "Amount": float(purchase.amount),  
#                                     "ItemBasedExpenseLineDetail": {
#                                         "ItemRef": {
#                                             "value": str(item.quickbooks_id),  
#                                             "name": str(item.item_name) 
#                                         },
#                                         "Qty": float(outbound.net_weight),  
#                                         "UnitPrice": float(purchase.per_unit_rate), 
#                                         "TaxCodeRef": {
#                                             "value": "NON" 
#                                         },
#                                         "BillableStatus": "NotBillable"  
#                                     }
#                                 }
#                             ],
#                             "APAccountRef": {
#                                 "name": "Accounts Payable (A/P)", 
#                                 "value": str(ap_account_id) 
#                             },
#                             "VendorRef": {
#                                 "name": str(contract.processor_entity_name), 
#                                 "value": str(processor.quickbooks_id) 
#                             },                        
#                             'CurrencyRef': {
#                                 'value': 'USD', 
#                                 'name': 'United States Dollar'
#                             },                            
#                             "CustomField": [
#                                 {
#                                     "DefinitionId": '1',  
#                                     "Type": "StringType",  
#                                     "Name": "ShipmentId",
#                                     "StringValue": str(purchase.shipment.shipment_id)  
#                                 }
#                             ]
#                         }

#                         try:
#                             created_purchase_order = create_purchase_order(token_instance.realm_id, token_instance.access_token, purchase_order_data)                        
#                             if created_purchase_order:                                
#                                 messages.success(request, "Purchase order added successfully and synced with QuickBooks.")
#                             else:
#                                 messages.error(request, "Failed to create Purchase in QuickBooks.")
#                         except Exception as qb_error:
#                             print(qb_error)
#                             messages.error(request, f"Error creating purchase order in QuickBooks: {str(qb_error)}")
#                             return render(request, 'distributor/create_outbound.html', context)
#                         return redirect('list-processor-shipment') 
#                 return render(request, 'distributor/create_outbound.html', context) 
#             elif request.user.is_processor2:
#                 current_time = timezone.now()
#                 user = request.user
#                 processor_user = ProcessorUser2.objects.filter(contact_email=user.email).first()
#                 processor =  Processor2.objects.filter(id=processor_user.processor2.id).first()
#                 processor_id = processor.id
#                 processor_type = processor.processor_type.first().type_name                
#                 contracts = AdminProcessorContract.objects.filter(processor_type=processor_type, processor_id=processor_id, contract_start_date__lte=current_time, end_date__gte=current_time).values('id','secret_key','processor_id','processor_type','processor_entity_name').order_by('-id')
                
#                 context["contracts"] = contracts
#                 context.update({
#                     "selected_contract": None,
#                     "crops": [],
#                     "milled_value": "None",
#                     "selected_processor_sku_id_list":[],
#                     "selected_destination": None,
#                     "warehouse_name" : None,
#                     "customer_name": None               
#                 })
                
#                 if request.method == "POST":
#                     data = request.POST
#                     selected_contract = request.POST.get('selected_contract') 
#                     print(selected_contract)
#                     contract = AdminProcessorContract.objects.get(id=int(selected_contract))                   
#                     processor_id = contract.processor_id
#                     processor_type = contract.processor_type
#                     selected_sku_id = data.get('sender_sku_id')
#                     destination_type = data.get('selected_destination')
#                     destination_id = data.get('destination_id') 
#                     selected_crop = data.get('crop_id')                   
#                     context.update({
#                         "selected_contract":contract.id,
#                         "contract":contract,                        
#                         "selected_processor_id": processor_id,
#                         "carrier_type": data.get('carrier_type'),                    
#                         "outbound_type": data.get('outbound_type'),
#                         "purchase_order_name":data.get('purchase_order_name'),
#                         "purchase_order_number": data.get('purchase_order_number'),
#                         "lot_number": data.get('lot_number'),
#                         "sender_sku_id": selected_sku_id,
#                         "selected_destination": destination_type,
#                         "weight":data.get('weight'),
#                         "gross_weight":data.get('gross_weight'),
#                         "ship_weight":data.get('ship_weight'),
#                         "ship_quantity":data.get('ship_quantity'),
#                         "status":data.get('status'),
#                         "amount_unit":data.get('amount_unit') ,                        
#                         "final_payment_date":data.get('final_payment_date')                
                        
#                     })
#                     if selected_crop:
#                         selected_crop = int(selected_crop)
#                         context["selected_crop"] =selected_crop
#                     if destination_id:
#                         context["destination_id"] = int(destination_id)

#                     if selected_contract:
#                         context['crops'] = CropDetails.objects.filter(contract=contract).values('id', 'crop', 'crop_type')

#                     if destination_type == "customer" and destination_id and selected_crop:
#                         crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first().crop
#                         crop_type = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first().crop_type                        
#                         customer_contracts = AdminCustomerContract.objects.filter(customer_id=int(destination_id), customerContractCrop__crop=crop, customerContractCrop__crop_type=crop_type, contract_start_date__lte=current_time, end_date__gte=current_time)
                       
#                         context["customer_contracts"] = customer_contracts

#                     if processor_id and not data.get("save"): 
                        
#                         if selected_sku_id and selected_crop:
#                             crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                             context["milled_value"] =  calculate_milled_volume(crop.crop, int(processor_id), processor_type, selected_sku_id)
#                             context["selected_sku"] = selected_sku_id
                       
#                         context["sender_sku_id_list"] = get_sku_list(int(processor_id),processor_type)["data"]
#                         if destination_type == 'warehouse':
#                             context['destination_list'] = Warehouse.objects.all().values('id','name')
#                         if destination_type == 'customer':
#                             context['destination_list'] = Customer.objects.filter(is_active=True).values('id','name')
#                         return render(request, 'distributor/create_outbound.html', context)
#                     else:
#                         if destination_type == 'warehouse':
#                             warehouse_id = Warehouse.objects.get(id=int(context.get('destination_id'))).id
#                             warehouse_name = Warehouse.objects.get(id=int(context.get('destination_id'))).name
#                             customer_id = None
#                             customer_name = None
#                             customer_contract = None
#                         else:
#                             warehouse_id = None
#                             warehouse_name = None
#                             customer_id = Customer.objects.get(id=int(context.get('destination_id'))).id
#                             customer_name = Customer.objects.get(id=int(context.get('destination_id'))).name
#                             selected_customer_contract = data.get('customer_contract')
#                             customer_contract = AdminCustomerContract.objects.filter(id=int(selected_customer_contract)).first()

#                         if data.get('carrier_type') == 'Truck/Trailer':
#                             if data.get('gross_weight') not in [None, 'null', ' ', ''] and data.get('ship_weight') not in [None, 'null', ' ', ''] and data.get('ship_quantity') not in [None, 'null', ' ', '']:
#                                 ship_quantity = int(data.get('ship_quantity'))
#                                 gross_weight = float(data.get('gross_weight'))
#                                 ship_weight = float(data.get('ship_weight'))                                    
#                                 net_weight = gross_weight - (ship_weight * ship_quantity)
#                             else:
#                                 context["error_messages"] = "Please provide Gross weight, Ship weight and Ship quantity."
#                                 return render(request, 'distributor/create_outbound.html', context)
                            
#                         elif data.get('carrier_type') == 'Rail Car':
                            
#                             gross_weight = 0
#                             ship_quantity = 1
#                             ship_weight = 0
#                             if data.get('weight') not in [None, 'null', ' ', '']:
#                                 net_weight = float(data.get('weight'))
#                             else:
#                                 context["error_messages"] = "Please provide Weight."
#                                 return render(request, 'distributor/create_outbound.html', context)
                            
#                         crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                         crop_name = crop.crop
                        
#                         if crop.amount_unit == data.get('amount_unit'):
#                             contract_weight_left = float(crop.left_amount) - float(net_weight)
#                         else:
#                             if crop.amount_unit == "LBS" and data.get('amount_unit') == "MT":
#                                 net_weight_lbs = float(net_weight) * 2204.62
#                                 contract_weight_left = float(crop.left_amount) - net_weight_lbs 
#                             else:
#                                 net_weight_mt = float(net_weight) * 0.000453592
#                                 contract_weight_left = float(crop.left_amount) - net_weight_mt                         
                        
#                         outbound = ProcessorWarehouseShipment(
#                             contract=contract,
#                             processor_id=processor_id,
#                             processor_type=processor_type,
#                             processor_entity_name=contract.processor_entity_name,
#                             processor_sku_list=[selected_sku_id],
#                             crop_id = crop.id,
#                             crop = crop_name,
#                             carrier_type=data.get('carrier_type'),
#                             outbound_type=data.get('outbound_type'),
#                             purchase_order_name=data.get('purchase_order_name'),
#                             purchase_order_number=data.get('purchase_order_number'),
#                             lot_number=data.get('lot_number'),
#                             gross_weight=gross_weight,
#                             net_weight=net_weight,
#                             weight_unit=data.get('amount_unit'),
#                             ship_weight = ship_weight,
#                             ship_quantity=ship_quantity,
#                             contract_weight_left=contract_weight_left,
#                             status=data.get('status'),
#                             customer_id=customer_id,
#                             warehouse_id=warehouse_id,
#                             customer_name=customer_name,
#                             warehouse_name=warehouse_name,
#                             customer_contract=customer_contract
#                         )
#                         outbound.save() 

#                         if data.get('final_payment_date') not in [None, '', ' ', 'null']:
#                             final_payment_date = data.get('final_payment_date')
#                             outbound.final_payment_date=final_payment_date  
#                         outbound.save()                         
                        
#                         carrier_id = data.get('carrier_id')
#                         if carrier_id:
#                             CarrierDetails.objects.create(shipment=outbound, carrier_id=carrier_id)
                        
#                         files = request.FILES.getlist('files')
#                         for file in files:
#                             ProcessorWarehouseShipmentDocuments.objects.create(shipment=outbound, document_file=file)

#                         ## Send notification to the Destination.
#                         if outbound.warehouse_id not in [None, 'null', ' ', '']:                            
#                             all_user = WarehouseUser.objects.filter(warehouse_id=outbound.warehouse_id)                           
                            
#                             distributors = Distributor.objects.filter(warehouse__id=outbound.warehouse_id)                           
                            
#                             distributor_users = DistributorUser.objects.filter(distributor__in=distributors)
#                         else:                            
#                             all_user = CustomerUser.objects.filter(customer_id=outbound.customer_id)
#                             distributor_users = []                          
#                         all_users = list(all_user) + list(distributor_users)

#                         for user in all_users :
#                             msg = f'A shipment has been sent of {outbound.net_weight}{outbound.weight_unit} under Contract ID - {outbound.contract.secret_key}'
#                             get_user = User.objects.get(username=user.contact_email)
#                             notification_reason = 'New Shipment'
#                             redirect_url = "/warehouse/list-processor-shipment/"
#                             save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
#                                 notification_reason=notification_reason)
#                             save_notification.save()                    
                        
#                         processor = Processor2.objects.filter(id=int(processor_id)).first() 
                        
#                         purchase = Purchase(
#                             shipment=outbound,
#                             processor_id=processor_id,
#                             processor_type=processor_type,
#                             processor_entity_name=contract.processor_entity_name,
#                             quantity=outbound.net_weight,
#                             per_unit_rate=crop.per_unit_rate,
#                             amount=outbound.total_payment,
#                             currency='USD'
#                         )  
#                         purchase.save()
#                         item = ShipmentItem.objects.filter(
#                             item_name=crop.crop, item_type=crop.crop_type, 
#                             per_unit_price=crop.per_unit_rate
#                         ).first()  
#                         accounts = get_chart_of_accounts(token_instance.realm_id, token_instance.access_token)                       
                        
#                         ap_account_id = None
#                         for account in accounts:
#                             if account['AccountType'] == 'Accounts Payable' and account['AccountSubType'] == 'AccountsPayable':
#                                 ap_account_id = account['Id'] 
#                                 break                       

#                         if not ap_account_id:
#                             messages.error(request, "Accounts Payable account not found in QuickBooks.")
#                             return render(request, 'distributor/create_outbound.html', context)

#                         purchase_order_data = {
#                             "TotalAmt": float(purchase.amount),  
#                             "TxnDate": datetime.now().strftime('%Y-%m-%d'),  
#                             "Line": [
#                                 {
#                                     "DetailType": "ItemBasedExpenseLineDetail",
#                                     "Amount": float(purchase.amount),  
#                                     "ItemBasedExpenseLineDetail": {
#                                         "ItemRef": {
#                                             "value": str(item.quickbooks_id),  
#                                             "name": str(item.item_name) 
#                                         },
#                                         "Qty": float(outbound.net_weight),  
#                                         "UnitPrice": float(purchase.per_unit_rate), 
#                                         "TaxCodeRef": {
#                                             "value": "NON" 
#                                         },
#                                         "BillableStatus": "NotBillable"  
#                                     }
#                                 }
#                             ],
#                             "APAccountRef": {
#                                 "name": "Accounts Payable (A/P)", 
#                                 "value": str(ap_account_id) 
#                             },
#                             "VendorRef": {
#                                 "name": str(contract.processor_entity_name), 
#                                 "value": str(processor.quickbooks_id) 
#                             },                        
#                             'CurrencyRef': {
#                                 'value': 'USD', 
#                                 'name': 'United States Dollar'
#                             },                            
#                             "CustomField": [
#                                 {
#                                     "DefinitionId": '1',  
#                                     "Type": "StringType",  
#                                     "Name": "ShipmentId",
#                                     "StringValue": str(purchase.shipment.shipment_id)  
#                                 }
#                             ]
#                         }

#                         try:
#                             created_purchase_order = create_purchase_order(token_instance.realm_id, token_instance.access_token, purchase_order_data)                        
#                             if created_purchase_order:                                
#                                 messages.success(request, "Purchase order added successfully and synced with QuickBooks.")
#                             else:
#                                 messages.error(request, "Failed to create Purchase in QuickBooks.")
#                         except Exception as qb_error:
#                             print(qb_error)
#                             messages.error(request, f"Error creating purchase order in QuickBooks: {str(qb_error)}")
#                             return render(request, 'distributor/create_outbound.html', context)
#                         return redirect('list-processor-shipment') 
#                 return render(request, 'distributor/create_outbound.html', context) 
#         else:
#             return redirect('login')        
#     except Exception as e:
#         context["error_messages"] = str(e)
#         return render(request, 'distributor/create_outbound.html', context) 


###########################QuickBooks Excluded And Single Crop###################################
# @login_required()
# def create_processor_shipment(request):
#     context = {}
#     try:
#         if request.user.is_authenticated:            
            
#             if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
#                 current_time = timezone.now()
#                 contracts = AdminProcessorContract.objects.filter(contract_start_date__lte=current_time, end_date__gte=current_time).values('id','secret_key','processor_id','processor_type','processor_entity_name').order_by('-id')
                
#                 context["contracts"] = contracts
#                 context.update({
#                     "selected_contract": None,
#                     "crops": [],
#                     "milled_value": "None",
#                     "selected_processor_sku_id_list":[],
#                     "selected_destination": None,
#                     "warehouse_name" : None,
#                     "customer_name": None,
#                     "selected_customer_contract" : None              
#                 })
                
#                 if request.method == "POST":
#                     data = request.POST
#                     selected_contract = request.POST.get('selected_contract') 
#                     print(selected_contract)
#                     contract = AdminProcessorContract.objects.get(id=int(selected_contract))                   
#                     processor_id = contract.processor_id
#                     processor_type = contract.processor_type
#                     selected_sku_id = data.get('sender_sku_id')
#                     destination_type = data.get('selected_destination')
#                     destination_id = data.get('destination_id') 
#                     selected_crop = data.get('crop_id')   
#                     print(selected_crop, type(selected_crop))                
#                     context.update({
#                         "selected_contract":contract.id,
#                         "contract":contract,                        
#                         "selected_processor_id": processor_id,
#                         "carrier_type": data.get('carrier_type'),                    
#                         "outbound_type": data.get('outbound_type'),
#                         "purchase_order_name":data.get('purchase_order_name'),
#                         "purchase_order_number": data.get('purchase_order_number'),
#                         "lot_number": data.get('lot_number'),
#                         "sender_sku_id": selected_sku_id,
#                         "selected_destination": destination_type,
#                         "weight":data.get('weight'),
#                         "gross_weight":data.get('gross_weight'),
#                         "ship_weight":data.get('ship_weight'),
#                         "ship_quantity":data.get('ship_quantity'),
#                         "status":data.get('status'),
#                         "amount_unit":data.get('amount_unit') ,                         
#                         "final_payment_date":data.get('final_payment_date')              
                        
#                     })
#                     if selected_crop:
#                         selected_crop = int(selected_crop)
#                         context["selected_crop"] =selected_crop
#                     if destination_id:
#                         context["destination_id"] = int(destination_id)
#                     if selected_contract:
#                         context['crops'] = CropDetails.objects.filter(contract=contract).values('id', 'crop', 'crop_type')

#                     if destination_type == "customer" and destination_id and selected_crop:
                        
#                         crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first().crop
#                         crop_type = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first().crop_type                                              
#                         customer_contracts = AdminCustomerContract.objects.filter(customer_id=int(destination_id), customerContractCrop__crop=crop, customerContractCrop__crop_type=crop_type, contract_start_date__lte=current_time, end_date__gte=current_time)
                        
#                         context["customer_contracts"] = customer_contracts
#                     if processor_id and not data.get("save"):                                                                                       
                    
#                         if selected_sku_id and selected_crop:                            
#                             crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                             context["milled_value"] =  calculate_milled_volume(crop.crop, int(processor_id), processor_type, selected_sku_id)
#                             context["selected_sku"] = selected_sku_id
                        
#                         context["sender_sku_id_list"] = get_sku_list(int(processor_id),processor_type)["data"]
#                         if destination_type == 'warehouse':
#                             context['destination_list'] = Warehouse.objects.all().values('id','name')
#                         if destination_type == 'customer':
#                             context['destination_list'] = Customer.objects.filter(is_active=True).values('id','name')
#                         return render(request, 'distributor/create_outbound.html', context)
                    
                    
#                     else:                        
#                         if destination_type == 'warehouse':
#                             warehouse_id = Warehouse.objects.get(id=int(context.get('destination_id'))).id
#                             warehouse_name = Warehouse.objects.get(id=int(context.get('destination_id'))).name
#                             customer_id = None
#                             customer_name = None
#                             customer_contract = None
#                         else:
#                             warehouse_id = None
#                             warehouse_name = None
#                             customer_id = Customer.objects.get(id=int(context.get('destination_id'))).id
#                             customer_name = Customer.objects.get(id=int(context.get('destination_id'))).name
#                             selected_customer_contract = data.get('customer_contract')
#                             customer_contract = AdminCustomerContract.objects.filter(id=int(selected_customer_contract)).first()

#                         if data.get('carrier_type') == 'Truck/Trailer':
#                             if data.get('gross_weight') not in [None, 'null', ' ', ''] and data.get('ship_weight') not in [None, 'null', ' ', ''] and data.get('ship_quantity') not in [None, 'null', ' ', '']:
#                                 ship_quantity = int(data.get('ship_quantity'))
#                                 gross_weight = float(data.get('gross_weight'))
#                                 ship_weight = float(data.get('ship_weight'))                                    
#                                 net_weight = gross_weight - (ship_weight * ship_quantity)
#                             else:
#                                 context["error_messages"] = "Please provide Gross weight, Ship weight and Ship quantity."
#                                 return render(request, 'distributor/create_outbound.html', context)
                            
#                         elif data.get('carrier_type') == 'Rail Car':
                            
#                             gross_weight = 0
#                             ship_quantity = 1
#                             ship_weight = 0
#                             if data.get('weight') not in [None, 'null', ' ', '']:
#                                 net_weight = float(data.get('weight'))
#                             else:
#                                 context["error_messages"] = "Please provide Weight."
#                                 return render(request, 'distributor/create_outbound.html', context)
                            
#                         crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                         crop_name = crop.crop                        
#                         if crop.amount_unit == data.get('amount_unit'):                           
#                             contract_weight_left = float(crop.left_amount) - float(net_weight)
#                         else:                            
#                             if crop.amount_unit == "LBS" and data.get('amount_unit') == "MT":
#                                 net_weight_lbs = float(net_weight) * 2204.62
#                                 contract_weight_left = float(crop.left_amount) - net_weight_lbs 
#                             else:
#                                 net_weight_mt = float(net_weight) * 0.000453592
#                                 contract_weight_left = float(crop.left_amount) - net_weight_mt    

#                         outbound = ProcessorWarehouseShipment(
#                             contract=contract,
#                             processor_id=processor_id,
#                             processor_type=processor_type,
#                             processor_entity_name=contract.processor_entity_name,
#                             processor_sku_list=[selected_sku_id],
#                             crop_id = crop.id,
#                             crop = crop_name,
#                             carrier_type=data.get('carrier_type'),
#                             outbound_type=data.get('outbound_type'),
#                             purchase_order_name=data.get('purchase_order_name'),
#                             purchase_order_number=data.get('purchase_order_number'),
#                             lot_number=data.get('lot_number'),
#                             gross_weight=gross_weight,
#                             net_weight=net_weight,
#                             weight_unit=data.get('amount_unit'),
#                             ship_weight = ship_weight,
#                             ship_quantity=ship_quantity,
#                             contract_weight_left=contract_weight_left,
#                             status=data.get('status'),
#                             customer_id=customer_id,
#                             warehouse_id=warehouse_id,
#                             customer_name=customer_name,
#                             warehouse_name=warehouse_name,
#                             customer_contract=customer_contract
#                         )
#                         outbound.save()  
#                         if data.get('final_payment_date') not in [None, '', ' ', 'null']:
#                             final_payment_date = data.get('final_payment_date')
#                             outbound.final_payment_date=final_payment_date  
#                         outbound.save()                        
                        
#                         carrier_id = data.get('carrier_id')
#                         if carrier_id:
#                             CarrierDetails.objects.create(shipment=outbound, carrier_id=carrier_id)
                        
#                         files = request.FILES.getlist('files')
#                         for file in files:
#                             ProcessorWarehouseShipmentDocuments.objects.create(shipment=outbound, document_file=file)

#                         ## Send notification to the Destination.
#                         if outbound.warehouse_id not in [None, 'null', ' ', '']:                            
#                             all_user = WarehouseUser.objects.filter(warehouse_id=outbound.warehouse_id)                           
                            
#                             distributors = Distributor.objects.filter(warehouse__id=outbound.warehouse_id)                           
                            
#                             distributor_users = DistributorUser.objects.filter(distributor__in=distributors)
#                         else:                            
#                             all_user = CustomerUser.objects.filter(customer_id=outbound.customer_id)
#                             distributor_users = []                          
#                         all_users = list(all_user) + list(distributor_users)
#                         for user in all_users :
#                             msg = f'A shipment has been sent of {outbound.net_weight}{outbound.weight_unit} under Contract ID - {outbound.contract.secret_key}'
#                             get_user = User.objects.get(username=user.contact_email)
#                             notification_reason = 'New Shipment'
#                             redirect_url = "/warehouse/list-processor-shipment/"
#                             save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
#                                 notification_reason=notification_reason)
#                             save_notification.save()                                            
#                         return redirect('list-processor-shipment')   

#                 return render(request, 'distributor/create_outbound.html', context)    
#             elif request.user.is_processor:
#                 current_time = timezone.now()
#                 user = request.user
#                 processor_user = ProcessorUser.objects.filter(contact_email=user.email).first()
#                 processor =  Processor.objects.filter(id=processor_user.processor.id).first()
#                 processor_id =processor.id
#                 processor_type = 'T1'                
#                 contracts = AdminProcessorContract.objects.filter(processor_id=processor_id, processor_type=processor_type,contract_start_date__lte=current_time, end_date__gte=current_time).values('id','secret_key','processor_id','processor_type','processor_entity_name').order_by('-id')
                
#                 context["contracts"] = contracts
#                 context.update({
#                     "selected_contract": None,
#                     "crops": [],
#                     "milled_value": "None",
#                     "selected_processor_sku_id_list":[],
#                     "selected_destination": None,
#                     "warehouse_name" : None,
#                     "customer_name": None               
#                 })
                
#                 if request.method == "POST":
#                     data = request.POST
#                     selected_contract = request.POST.get('selected_contract') 
#                     print(selected_contract)
#                     contract = AdminProcessorContract.objects.get(id=int(selected_contract))                   
#                     processor_id = contract.processor_id
#                     processor_type = contract.processor_type
#                     selected_sku_id = data.get('sender_sku_id')
#                     destination_type = data.get('selected_destination')
#                     destination_id = data.get('destination_id') 
#                     selected_crop = data.get('crop_id')                   
#                     context.update({
#                         "selected_contract":contract.id,
#                         "contract":contract,                        
#                         "selected_processor_id": processor_id,
#                         "carrier_type": data.get('carrier_type'),                    
#                         "outbound_type": data.get('outbound_type'),
#                         "purchase_order_name":data.get('purchase_order_name'),
#                         "purchase_order_number": data.get('purchase_order_number'),
#                         "lot_number": data.get('lot_number'),
#                         "sender_sku_id": selected_sku_id,
#                         "selected_destination": destination_type,
#                         "weight":data.get('weight'),
#                         "gross_weight":data.get('gross_weight'),
#                         "ship_weight":data.get('ship_weight'),
#                         "ship_quantity":data.get('ship_quantity'),
#                         "status":data.get('status'),
#                         "amount_unit":data.get('amount_unit') ,                         
#                         "final_payment_date":data.get('final_payment_date')                
                        
#                     })
#                     if selected_crop:
#                         selected_crop = int(selected_crop)
#                         context["selected_crop"] =selected_crop
#                     if destination_id:
#                         context["destination_id"] = int(destination_id)

#                     if selected_contract:
#                         context['crops'] = CropDetails.objects.filter(contract=contract).values('id', 'crop', 'crop_type')

#                     if destination_type == "customer" and destination_id and selected_crop:
#                         crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first().crop
#                         crop_type = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first().crop_type                        
#                         customer_contracts = AdminCustomerContract.objects.filter(customer_id=int(destination_id), customerContractCrop__crop=crop, customerContractCrop__crop_type=crop_type, contract_start_date__lte=current_time, end_date__gte=current_time)
                     
#                         context["customer_contracts"] = customer_contracts

#                     if processor_id and not data.get("save"):                        
                        
#                         if selected_sku_id and selected_crop:
#                             crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                             context["milled_value"] =  calculate_milled_volume(crop.crop, int(processor_id), processor_type, selected_sku_id)
#                             context["selected_sku"] = selected_sku_id
                       
#                         context["sender_sku_id_list"] = get_sku_list(int(processor_id),processor_type)["data"]
#                         if destination_type == 'warehouse':
#                             context['destination_list'] = Warehouse.objects.all().values('id','name')
#                         if destination_type == 'customer':
#                             context['destination_list'] = Customer.objects.filter(is_active=True).values('id','name')
#                         return render(request, 'distributor/create_outbound.html', context)
#                     else:
#                         if destination_type == 'warehouse':
#                             warehouse_id = Warehouse.objects.get(id=int(context.get('destination_id'))).id
#                             warehouse_name = Warehouse.objects.get(id=int(context.get('destination_id'))).name
#                             customer_id = None
#                             customer_name = None
#                             customer_contract = None
#                         else:
#                             warehouse_id = None
#                             warehouse_name = None
#                             customer_id = Customer.objects.get(id=int(context.get('destination_id'))).id
#                             customer_name = Customer.objects.get(id=int(context.get('destination_id'))).name
#                             selected_customer_contract = data.get('customer_contract')
#                             customer_contract = AdminCustomerContract.objects.filter(id=int(selected_customer_contract)).first()

#                         if data.get('carrier_type') == 'Truck/Trailer':
#                             if data.get('gross_weight') not in [None, 'null', ' ', ''] and data.get('ship_weight') not in [None, 'null', ' ', ''] and data.get('ship_quantity') not in [None, 'null', ' ', '']:
#                                 ship_quantity = int(data.get('ship_quantity'))
#                                 gross_weight = float(data.get('gross_weight'))
#                                 ship_weight = float(data.get('ship_weight'))                                    
#                                 net_weight = gross_weight - (ship_weight * ship_quantity)
#                             else:
#                                 context["error_messages"] = "Please provide Gross weight, Ship weight and Ship quantity."
#                                 return render(request, 'distributor/create_outbound.html', context)
                            
#                         elif data.get('carrier_type') == 'Rail Car':
                            
#                             gross_weight = 0
#                             ship_quantity = 1
#                             ship_weight = 0
#                             if data.get('weight') not in [None, 'null', ' ', '']:
#                                 net_weight = float(data.get('weight'))
#                             else:
#                                 context["error_messages"] = "Please provide Weight."
#                                 return render(request, 'distributor/create_outbound.html', context)
                            
#                         crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                         crop_name = crop.crop
                        
#                         if crop.amount_unit == data.get('amount_unit'):
#                             contract_weight_left = float(crop.left_amount) - float(net_weight)
#                         else:
#                             if crop.amount_unit == "LBS" and data.get('amount_unit') == "MT":
#                                 net_weight_lbs = float(net_weight) * 2204.62
#                                 contract_weight_left = float(crop.left_amount) - net_weight_lbs 
#                             else:
#                                 net_weight_mt = float(net_weight) * 0.000453592
#                                 contract_weight_left = float(crop.left_amount) - net_weight_mt                         
                        
#                         outbound = ProcessorWarehouseShipment(
#                             contract=contract,
#                             processor_id=processor_id,
#                             processor_type=processor_type,
#                             processor_entity_name=contract.processor_entity_name,
#                             processor_sku_list=[selected_sku_id],
#                             crop_id = crop.id,
#                             crop = crop_name,
#                             carrier_type=data.get('carrier_type'),
#                             outbound_type=data.get('outbound_type'),
#                             purchase_order_name=data.get('purchase_order_name'),
#                             purchase_order_number=data.get('purchase_order_number'),
#                             lot_number=data.get('lot_number'),
#                             gross_weight=gross_weight,
#                             net_weight=net_weight,
#                             weight_unit=data.get('amount_unit'),
#                             ship_weight = ship_weight,
#                             ship_quantity=ship_quantity,
#                             contract_weight_left=contract_weight_left,
#                             status=data.get('status'),
#                             customer_id=customer_id,
#                             warehouse_id=warehouse_id,
#                             customer_name=customer_name,
#                             warehouse_name=warehouse_name,
#                             customer_contract=customer_contract
#                         )
#                         outbound.save() 
#                         if data.get('final_payment_date') not in [None, '', ' ', 'null']:
#                             final_payment_date = data.get('final_payment_date')
#                             outbound.final_payment_date=final_payment_date  
#                         outbound.save()                           
                        
#                         carrier_id = data.get('carrier_id')
#                         if carrier_id:
#                             CarrierDetails.objects.create(shipment=outbound, carrier_id=carrier_id)
                        
#                         files = request.FILES.getlist('files')
#                         for file in files:
#                             ProcessorWarehouseShipmentDocuments.objects.create(shipment=outbound, document_file=file)

#                         ## Send notification to the Destination.
#                         if outbound.warehouse_id not in [None, 'null', ' ', '']:                            
#                             all_user = WarehouseUser.objects.filter(warehouse_id=outbound.warehouse_id)                           
                            
#                             distributors = Distributor.objects.filter(warehouse__id=outbound.warehouse_id)                           
                            
#                             distributor_users = DistributorUser.objects.filter(distributor__in=distributors)
#                         else:                            
#                             all_user = CustomerUser.objects.filter(customer_id=outbound.customer_id)
#                             distributor_users = []                          
#                         all_users = list(all_user) + list(distributor_users)
                        
#                         for user in all_users :
#                             msg = f'A shipment has been sent of {outbound.net_weight}{outbound.weight_unit} under Contract ID - {outbound.contract.secret_key}'
#                             get_user = User.objects.get(username=user.contact_email)
#                             notification_reason = 'New Shipment'
#                             redirect_url = "/warehouse/list-processor-shipment/"
#                             save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
#                                 notification_reason=notification_reason)
#                             save_notification.save()                                             
                        
#                         return redirect('list-processor-shipment') 
#                 return render(request, 'distributor/create_outbound.html', context) 
#             elif request.user.is_processor2:
#                 current_time = timezone.now()
#                 user = request.user
#                 processor_user = ProcessorUser2.objects.filter(contact_email=user.email).first()
#                 processor =  Processor2.objects.filter(id=processor_user.processor2.id).first()
#                 processor_id = processor.id
#                 processor_type = processor.processor_type.first().type_name                
#                 contracts = AdminProcessorContract.objects.filter(processor_type=processor_type, processor_id=processor_id, contract_start_date__lte=current_time, end_date__gte=current_time).values('id','secret_key','processor_id','processor_type','processor_entity_name').order_by('-id')
                
#                 context["contracts"] = contracts
#                 context.update({
#                     "selected_contract": None,
#                     "crops": [],
#                     "milled_value": "None",
#                     "selected_processor_sku_id_list":[],
#                     "selected_destination": None,
#                     "warehouse_name" : None,
#                     "customer_name": None               
#                 })
                
#                 if request.method == "POST":
#                     data = request.POST
#                     selected_contract = request.POST.get('selected_contract') 
#                     print(selected_contract)
#                     contract = AdminProcessorContract.objects.get(id=int(selected_contract))                   
#                     processor_id = contract.processor_id
#                     processor_type = contract.processor_type
#                     selected_sku_id = data.get('sender_sku_id')
#                     destination_type = data.get('selected_destination')
#                     destination_id = data.get('destination_id') 
#                     selected_crop = data.get('crop_id')                   
#                     context.update({
#                         "selected_contract":contract.id,
#                         "contract":contract,                        
#                         "selected_processor_id": processor_id,
#                         "carrier_type": data.get('carrier_type'),                    
#                         "outbound_type": data.get('outbound_type'),
#                         "purchase_order_name":data.get('purchase_order_name'),
#                         "purchase_order_number": data.get('purchase_order_number'),
#                         "lot_number": data.get('lot_number'),
#                         "sender_sku_id": selected_sku_id,
#                         "selected_destination": destination_type,
#                         "weight":data.get('weight'),
#                         "gross_weight":data.get('gross_weight'),
#                         "ship_weight":data.get('ship_weight'),
#                         "ship_quantity":data.get('ship_quantity'),
#                         "status":data.get('status'),
#                         "amount_unit":data.get('amount_unit') ,                        
#                         "final_payment_date":data.get('final_payment_date')                
                        
#                     })
#                     if selected_crop:
#                         selected_crop = int(selected_crop)
#                         context["selected_crop"] =selected_crop
#                     if destination_id:
#                         context["destination_id"] = int(destination_id)

#                     if selected_contract:
#                         context['crops'] = CropDetails.objects.filter(contract=contract).values('id', 'crop', 'crop_type')

#                     if destination_type == "customer" and destination_id and selected_crop:
#                         crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first().crop
#                         crop_type = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first().crop_type                        
#                         customer_contracts = AdminCustomerContract.objects.filter(customer_id=int(destination_id), customerContractCrop__crop=crop, customerContractCrop__crop_type=crop_type, contract_start_date__lte=current_time, end_date__gte=current_time)
                       
#                         context["customer_contracts"] = customer_contracts

#                     if processor_id and not data.get("save"): 
                        
#                         if selected_sku_id and selected_crop:
#                             crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                             context["milled_value"] =  calculate_milled_volume(crop.crop, int(processor_id), processor_type, selected_sku_id)
#                             context["selected_sku"] = selected_sku_id
                       
#                         context["sender_sku_id_list"] = get_sku_list(int(processor_id),processor_type)["data"]
#                         if destination_type == 'warehouse':
#                             context['destination_list'] = Warehouse.objects.all().values('id','name')
#                         if destination_type == 'customer':
#                             context['destination_list'] = Customer.objects.filter(is_active=True).values('id','name')
#                         return render(request, 'distributor/create_outbound.html', context)
#                     else:
#                         if destination_type == 'warehouse':
#                             warehouse_id = Warehouse.objects.get(id=int(context.get('destination_id'))).id
#                             warehouse_name = Warehouse.objects.get(id=int(context.get('destination_id'))).name
#                             customer_id = None
#                             customer_name = None
#                             customer_contract = None
#                         else:
#                             warehouse_id = None
#                             warehouse_name = None
#                             customer_id = Customer.objects.get(id=int(context.get('destination_id'))).id
#                             customer_name = Customer.objects.get(id=int(context.get('destination_id'))).name
#                             selected_customer_contract = data.get('customer_contract')
#                             customer_contract = AdminCustomerContract.objects.filter(id=int(selected_customer_contract)).first()

#                         if data.get('carrier_type') == 'Truck/Trailer':
#                             if data.get('gross_weight') not in [None, 'null', ' ', ''] and data.get('ship_weight') not in [None, 'null', ' ', ''] and data.get('ship_quantity') not in [None, 'null', ' ', '']:
#                                 ship_quantity = int(data.get('ship_quantity'))
#                                 gross_weight = float(data.get('gross_weight'))
#                                 ship_weight = float(data.get('ship_weight'))                                    
#                                 net_weight = gross_weight - (ship_weight * ship_quantity)
#                             else:
#                                 context["error_messages"] = "Please provide Gross weight, Ship weight and Ship quantity."
#                                 return render(request, 'distributor/create_outbound.html', context)
                            
#                         elif data.get('carrier_type') == 'Rail Car':
                            
#                             gross_weight = 0
#                             ship_quantity = 1
#                             ship_weight = 0
#                             if data.get('weight') not in [None, 'null', ' ', '']:
#                                 net_weight = float(data.get('weight'))
#                             else:
#                                 context["error_messages"] = "Please provide Weight."
#                                 return render(request, 'distributor/create_outbound.html', context)
                            
#                         crop = CropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                         crop_name = crop.crop
                        
#                         if crop.amount_unit == data.get('amount_unit'):
#                             contract_weight_left = float(crop.left_amount) - float(net_weight)
#                         else:
#                             if crop.amount_unit == "LBS" and data.get('amount_unit') == "MT":
#                                 net_weight_lbs = float(net_weight) * 2204.62
#                                 contract_weight_left = float(crop.left_amount) - net_weight_lbs 
#                             else:
#                                 net_weight_mt = float(net_weight) * 0.000453592
#                                 contract_weight_left = float(crop.left_amount) - net_weight_mt                         
                        
#                         outbound = ProcessorWarehouseShipment(
#                             contract=contract,
#                             processor_id=processor_id,
#                             processor_type=processor_type,
#                             processor_entity_name=contract.processor_entity_name,
#                             processor_sku_list=[selected_sku_id],
#                             crop_id = crop.id,
#                             crop = crop_name,
#                             carrier_type=data.get('carrier_type'),
#                             outbound_type=data.get('outbound_type'),
#                             purchase_order_name=data.get('purchase_order_name'),
#                             purchase_order_number=data.get('purchase_order_number'),
#                             lot_number=data.get('lot_number'),
#                             gross_weight=gross_weight,
#                             net_weight=net_weight,
#                             weight_unit=data.get('amount_unit'),
#                             ship_weight = ship_weight,
#                             ship_quantity=ship_quantity,
#                             contract_weight_left=contract_weight_left,
#                             status=data.get('status'),
#                             customer_id=customer_id,
#                             warehouse_id=warehouse_id,
#                             customer_name=customer_name,
#                             warehouse_name=warehouse_name,
#                             customer_contract=customer_contract
#                         )
#                         outbound.save() 

#                         if data.get('final_payment_date') not in [None, '', ' ', 'null']:
#                             final_payment_date = data.get('final_payment_date')
#                             outbound.final_payment_date=final_payment_date  
#                         outbound.save()                         
                        
#                         carrier_id = data.get('carrier_id')
#                         if carrier_id:
#                             CarrierDetails.objects.create(shipment=outbound, carrier_id=carrier_id)
                        
#                         files = request.FILES.getlist('files')
#                         for file in files:
#                             ProcessorWarehouseShipmentDocuments.objects.create(shipment=outbound, document_file=file)

#                         ## Send notification to the Destination.
#                         if outbound.warehouse_id not in [None, 'null', ' ', '']:                            
#                             all_user = WarehouseUser.objects.filter(warehouse_id=outbound.warehouse_id)                           
                            
#                             distributors = Distributor.objects.filter(warehouse__id=outbound.warehouse_id)                           
                            
#                             distributor_users = DistributorUser.objects.filter(distributor__in=distributors)
#                         else:                            
#                             all_user = CustomerUser.objects.filter(customer_id=outbound.customer_id)
#                             distributor_users = []                          
#                         all_users = list(all_user) + list(distributor_users)

#                         for user in all_users :
#                             msg = f'A shipment has been sent of {outbound.net_weight}{outbound.weight_unit} under Contract ID - {outbound.contract.secret_key}'
#                             get_user = User.objects.get(username=user.contact_email)
#                             notification_reason = 'New Shipment'
#                             redirect_url = "/warehouse/list-processor-shipment/"
#                             save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
#                                 notification_reason=notification_reason)
#                             save_notification.save()                  
#                         return redirect('list-processor-shipment') 
#                 return render(request, 'distributor/create_outbound.html', context) 
#         else:
#             return redirect('login')        
#     except Exception as e:
#         context["error_messages"] = str(e)
#         return render(request, 'distributor/create_outbound.html', context) 


###########################QuickBooks Excluded And Multiple Crop###################################
@login_required
def create_processor_shipment(request):
    context = {}
    try:
        if request.user.is_authenticated:
            if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
                current_time = timezone.now()
                context["contracts"] = AdminProcessorContract.objects.filter(contract_start_date__lte=current_time, end_date__gte=current_time).values('id','secret_key','processor_id','processor_type','processor_entity_name').order_by('-id')
                
                if request.method == "POST":
                    data = request.POST
                    selected_contract_id = data.get("selected_contract")
                    outbound_type = data.get('outbound_type')
                    carrier_type = data.get('carrier_type')
                    carrier_id = data.get('carrier_id')
                    purchase_order_name = data.get('purchase_order_name')
                    purchase_order_number = data.get('purchase_order_number')
                    
                    shipment_type = data.get('shipment_type')
                    destination_type = data.get('selected_destination')
                    destination_id = data.get('destination_id') 
                    customer_contract = data.get('customer_contract')
                    crop_ids = data.getlist('crop_id[]')
                    lot_numbers = data.getlist('lot_number[]')
                    gross_weights = data.getlist('gross_weight[]')
                    weights = data.getlist('weight[]')
                    amount_unit = data.get('amount_unit')
                    ship_weights = data.getlist('ship_weight[]')
                    ship_quantities = data.getlist('ship_quantity[]')
                    status = data.get('status')
                    files = request.FILES.getlist('files')
                    final_payment_date = data.get('final_payment_date')

                    contract = AdminProcessorContract.objects.filter(id=int(selected_contract_id)).first()  
                    
                    if destination_type == 'warehouse':
                        warehouse_id = Warehouse.objects.get(id=int(destination_id)).id
                        warehouse_name = Warehouse.objects.get(id=int(destination_id)).name
                        customer_id = None
                        customer_name = None
                        customer_contract = None
                    else:
                        warehouse_id = None
                        warehouse_name = None
                        customer_id = Customer.objects.get(id=int(destination_id)).id
                        customer_name = Customer.objects.get(id=int(destination_id)).name            
                        customer_contract = AdminCustomerContract.objects.filter(id=int(customer_contract)).first()

                    outbound = ProcessorWarehouseShipment(
                        contract=contract,
                        processor_id=contract.processor_id,
                        processor_type=contract.processor_type,
                        processor_entity_name=contract.processor_entity_name,
                        
                        carrier_type=carrier_type,
                        outbound_type=outbound_type,
                        purchase_order_name=purchase_order_name,
                        purchase_order_number=purchase_order_number,                        
                        shipment_type=shipment_type,          
                        
                        status=status,
                        customer_id=customer_id,
                        warehouse_id=warehouse_id,
                        customer_name=customer_name,
                        warehouse_name=warehouse_name,
                        customer_contract=customer_contract
                    )
                    outbound.save()         

                    for i, crop_id in enumerate(crop_ids):
                        crop = CropDetails.objects.filter(id=int(crop_id)).first()
                        gross_weight = float(gross_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                        ship_weight = float(ship_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                        ship_quantity = int(ship_quantities[i]) if carrier_type == 'Truck/Trailer' else 1
                        weight = float(weights[i]) if carrier_type == 'Rail Car' else 0
                        lot_number = lot_numbers[i]
                        print(i, lot_number)
                        
                        if carrier_type == 'Truck/Trailer':
                            net_weight = gross_weight - (ship_weight * ship_quantity)
                        elif carrier_type == 'Rail Car':
                            net_weight = weight

                        shipment_amount_unit = amount_unit  
                        if crop.amount_unit == shipment_amount_unit:
                            contract_weight_left = float(crop.left_amount) - float(net_weight)
                        else:
                            if crop.amount_unit == "LBS" and shipment_amount_unit == "MT":
                                net_weight_lbs = float(net_weight) * 2204.62
                                contract_weight_left = float(crop.left_amount) - net_weight_lbs
                            elif crop.amount_unit == "MT" and shipment_amount_unit == "LBS":
                                net_weight_mt = float(net_weight) * 0.000453592
                                contract_weight_left = float(crop.left_amount) - net_weight_mt
                            else:
                                raise ValueError(f"Unsupported conversion from {crop.amount_unit} to {shipment_amount_unit}")

                        ProcessorShipmentCrops.objects.create(
                            shipment=outbound,
                            crop_id=crop_id,
                            crop=crop.crop,
                            crop_type=crop.crop_type,
                            net_weight=net_weight,
                            gross_weight=gross_weight,
                            ship_weight=ship_weight,
                            ship_quantity=ship_quantity,
                            weight_unit=shipment_amount_unit,
                            contract_weight_left=contract_weight_left,
                            lot_number=lot_number
                        )

                    if final_payment_date not in [None, '', ' ', 'null']:            
                        outbound.final_payment_date=final_payment_date  
                    outbound.save()

                    if carrier_id:
                        CarrierDetails.objects.create(shipment=outbound, carrier_id=carrier_id)      
                    
                    for file in files:
                        ProcessorWarehouseShipmentDocuments.objects.create(shipment=outbound, document_file=file)   

                    if outbound.warehouse_id not in [None, 'null', ' ', '']:                            
                        all_user = WarehouseUser.objects.filter(warehouse_id=outbound.warehouse_id)                           
                        
                        distributors = Distributor.objects.filter(warehouse__id=outbound.warehouse_id)                           
                        
                        distributor_users = DistributorUser.objects.filter(distributor__in=distributors)
                    else:                            
                        all_user = CustomerUser.objects.filter(customer_id=outbound.customer_id)
                        distributor_users = []                          
                    all_users = list(all_user) + list(distributor_users)
                    for user in all_users :
                        msg = f'A shipment has been sent  under Contract ID - {outbound.contract.secret_key}'
                        get_user = User.objects.get(username=user.contact_email)
                        notification_reason = 'New Shipment'
                        redirect_url = "/warehouse/list-processor-shipment/"
                        save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
                            notification_reason=notification_reason)
                        save_notification.save()                 
                            
                    return redirect('list-processor-shipment')      

                return render(request, "distributor/create_processor_shipment.html", context)
            
            elif request.user.is_processor:
                current_time = timezone.now()
                user = request.user
                processor_user = ProcessorUser.objects.filter(contact_email=user.email).first()
                processor =  Processor.objects.filter(id=processor_user.processor.id).first()
                processor_id = processor.id
                            
                contracts = AdminProcessorContract.objects.filter(processor_type="T1", processor_id=processor_id, contract_start_date__lte=current_time, end_date__gte=current_time).values('id','secret_key','processor_id','processor_type','processor_entity_name').order_by('-id')
                context["contracts"] = contracts
                
                if request.method == "POST":
                    data = request.POST
                    selected_contract_id = data.get("selected_contract")
                    outbound_type = data.get('outbound_type')
                    carrier_type = data.get('carrier_type')
                    carrier_id = data.get('carrier_id')
                    purchase_order_name = data.get('purchase_order_name')
                    purchase_order_number = data.get('purchase_order_number')
                    
                    shipment_type = data.get('shipment_type')
                    destination_type = data.get('selected_destination')
                    destination_id = data.get('destination_id') 
                    customer_contract = data.get('customer_contract')
                    crop_ids = data.getlist('crop_id[]')
                    lot_numbers = data.getlist('lot_number[]')
                    gross_weights = data.getlist('gross_weight[]')
                    weights = data.getlist('weight[]')
                    amount_unit = data.get('amount_unit')
                    ship_weights = data.getlist('ship_weight[]')
                    ship_quantities = data.getlist('ship_quantity[]')
                    status = data.get('status')
                    files = request.FILES.getlist('files')
                    final_payment_date = data.get('final_payment_date')

                    contract = AdminProcessorContract.objects.filter(id=int(selected_contract_id)).first()  
                    
                    if destination_type == 'warehouse':
                        warehouse_id = Warehouse.objects.get(id=int(destination_id)).id
                        warehouse_name = Warehouse.objects.get(id=int(destination_id)).name
                        customer_id = None
                        customer_name = None
                        customer_contract = None
                    else:
                        warehouse_id = None
                        warehouse_name = None
                        customer_id = Customer.objects.get(id=int(destination_id)).id
                        customer_name = Customer.objects.get(id=int(destination_id)).name            
                        customer_contract = AdminCustomerContract.objects.filter(id=int(customer_contract)).first()

                    outbound = ProcessorWarehouseShipment(
                        contract=contract,
                        processor_id=contract.processor_id,
                        processor_type=contract.processor_type,
                        processor_entity_name=contract.processor_entity_name,
                        
                        carrier_type=carrier_type,
                        outbound_type=outbound_type,
                        purchase_order_name=purchase_order_name,
                        purchase_order_number=purchase_order_number,                         
                        shipment_type=shipment_type,         
                        
                        status=status,
                        customer_id=customer_id,
                        warehouse_id=warehouse_id,
                        customer_name=customer_name,
                        warehouse_name=warehouse_name,
                        customer_contract=customer_contract
                    )
                    outbound.save()         

                    for i, crop_id in enumerate(crop_ids):
                        crop = CropDetails.objects.filter(id=int(crop_id)).first()
                        gross_weight = float(gross_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                        ship_weight = float(ship_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                        ship_quantity = int(ship_quantities[i]) if carrier_type == 'Truck/Trailer' else 1
                        weight = float(weights[i]) if carrier_type == 'Rail Car' else 0
                        lot_number = lot_numbers[i]
                        
                        if carrier_type == 'Truck/Trailer':
                            net_weight = gross_weight - (ship_weight * ship_quantity)
                        elif carrier_type == 'Rail Car':
                            net_weight = weight

                        shipment_amount_unit = amount_unit 
                        if crop.amount_unit == shipment_amount_unit:
                            contract_weight_left = float(crop.left_amount) - float(net_weight)
                        else:
                            if crop.amount_unit == "LBS" and shipment_amount_unit == "MT":
                                net_weight_lbs = float(net_weight) * 2204.62
                                contract_weight_left = float(crop.left_amount) - net_weight_lbs
                            elif crop.amount_unit == "MT" and shipment_amount_unit == "LBS":
                                net_weight_mt = float(net_weight) * 0.000453592
                                contract_weight_left = float(crop.left_amount) - net_weight_mt
                            else:
                                raise ValueError(f"Unsupported conversion from {crop.amount_unit} to {shipment_amount_unit}")

                        ProcessorShipmentCrops.objects.create(
                            shipment=outbound,
                            crop_id=crop_id,
                            crop=crop.crop,
                            crop_type=crop.crop_type,
                            net_weight=net_weight,
                            gross_weight=gross_weight,
                            ship_weight=ship_weight,
                            ship_quantity=ship_quantity,
                            weight_unit=shipment_amount_unit,
                            contract_weight_left=contract_weight_left,
                            lot_number=lot_number
                        )

                    if final_payment_date not in [None, '', ' ', 'null']:            
                        outbound.final_payment_date=final_payment_date  
                    outbound.save()

                    if carrier_id:
                        CarrierDetails.objects.create(shipment=outbound, carrier_id=carrier_id)      
                    
                    for file in files:
                        ProcessorWarehouseShipmentDocuments.objects.create(shipment=outbound, document_file=file)   

                    if outbound.warehouse_id not in [None, 'null', ' ', '']:                            
                        all_user = WarehouseUser.objects.filter(warehouse_id=outbound.warehouse_id)                         
                        distributors = Distributor.objects.filter(warehouse__id=outbound.warehouse_id)                         
                        distributor_users = DistributorUser.objects.filter(distributor__in=distributors)
                    else:                            
                        all_user = CustomerUser.objects.filter(customer_id=outbound.customer_id)
                        distributor_users = []                          
                    all_users = list(all_user) + list(distributor_users)
                    for user in all_users :
                        msg = f'A shipment has been sent  under Contract ID - {outbound.contract.secret_key}'
                        get_user = User.objects.get(username=user.contact_email)
                        notification_reason = 'New Shipment'
                        redirect_url = "/warehouse/list-processor-shipment/"
                        save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
                            notification_reason=notification_reason)
                        save_notification.save()                 
                            
                    return redirect('list-processor-shipment')      

                return render(request, "distributor/create_processor_shipment.html", context)
        
            elif request.user.is_processor2:
                current_time = timezone.now()
                user = request.user
                processor_user = ProcessorUser2.objects.filter(contact_email=user.email).first()
                processor =  Processor2.objects.filter(id=processor_user.processor2.id).first()
                processor_id = processor.id
                processor_type = processor.processor_type.first().type_name                
                contracts = AdminProcessorContract.objects.filter(processor_type=processor_type, processor_id=processor_id, contract_start_date__lte=current_time, end_date__gte=current_time).values('id','secret_key','processor_id','processor_type','processor_entity_name').order_by('-id')
                context["contracts"] = contracts
                
                if request.method == "POST":
                    data = request.POST
                    selected_contract_id = data.get("selected_contract")
                    outbound_type = data.get('outbound_type')
                    carrier_type = data.get('carrier_type')
                    carrier_id = data.get('carrier_id')
                    purchase_order_name = data.get('purchase_order_name')
                    purchase_order_number = data.get('purchase_order_number')                    
                    shipment_type = data.get('shipment_type')
                    destination_type = data.get('selected_destination')
                    destination_id = data.get('destination_id') 
                    customer_contract = data.get('customer_contract')
                    crop_ids = data.getlist('crop_id[]')
                    lot_numbers = data.getlist('lot_number[]')
                    gross_weights = data.getlist('gross_weight[]')
                    weights = data.getlist('weight[]')
                    amount_unit = data.get('amount_unit')
                    ship_weights = data.getlist('ship_weight[]')
                    ship_quantities = data.getlist('ship_quantity[]')
                    status = data.get('status')
                    files = request.FILES.getlist('files')
                    final_payment_date = data.get('final_payment_date')

                    contract = AdminProcessorContract.objects.filter(id=int(selected_contract_id)).first()  
                    
                    if destination_type == 'warehouse':
                        warehouse_id = Warehouse.objects.get(id=int(destination_id)).id
                        warehouse_name = Warehouse.objects.get(id=int(destination_id)).name
                        customer_id = None
                        customer_name = None
                        customer_contract = None
                    else:
                        warehouse_id = None
                        warehouse_name = None
                        customer_id = Customer.objects.get(id=int(destination_id)).id
                        customer_name = Customer.objects.get(id=int(destination_id)).name            
                        customer_contract = AdminCustomerContract.objects.filter(id=int(customer_contract)).first()

                    outbound = ProcessorWarehouseShipment(
                        contract=contract,
                        processor_id=contract.processor_id,
                        processor_type=contract.processor_type,
                        processor_entity_name=contract.processor_entity_name,
                        
                        carrier_type=carrier_type,
                        outbound_type=outbound_type,
                        purchase_order_name=purchase_order_name,
                        purchase_order_number=purchase_order_number,                         
                        shipment_type=shipment_type,         
                        
                        status=status,
                        customer_id=customer_id,
                        warehouse_id=warehouse_id,
                        customer_name=customer_name,
                        warehouse_name=warehouse_name,
                        customer_contract=customer_contract
                    )
                    outbound.save()         

                    for i, crop_id in enumerate(crop_ids):
                        crop = CropDetails.objects.filter(id=int(crop_id)).first()
                        gross_weight = float(gross_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                        ship_weight = float(ship_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                        ship_quantity = int(ship_quantities[i]) if carrier_type == 'Truck/Trailer' else 1
                        weight = float(weights[i]) if carrier_type == 'Rail Car' else 0
                        lot_number = lot_numbers[i]
                        
                        if carrier_type == 'Truck/Trailer':
                            net_weight = gross_weight - (ship_weight * ship_quantity)
                        elif carrier_type == 'Rail Car':
                            net_weight = weight

                        shipment_amount_unit = amount_unit  
                        if crop.amount_unit == shipment_amount_unit:
                            contract_weight_left = float(crop.left_amount) - float(net_weight)
                        else:
                            if crop.amount_unit == "LBS" and shipment_amount_unit == "MT":
                                net_weight_lbs = float(net_weight) * 2204.62
                                contract_weight_left = float(crop.left_amount) - net_weight_lbs
                            elif crop.amount_unit == "MT" and shipment_amount_unit == "LBS":
                                net_weight_mt = float(net_weight) * 0.000453592
                                contract_weight_left = float(crop.left_amount) - net_weight_mt
                            else:
                                raise ValueError(f"Unsupported conversion from {crop.amount_unit} to {shipment_amount_unit}")

                        ProcessorShipmentCrops.objects.create(
                            shipment=outbound,
                            crop_id=crop_id,
                            crop=crop.crop,
                            crop_type=crop.crop_type,
                            net_weight=net_weight,
                            gross_weight=gross_weight,
                            ship_weight=ship_weight,
                            ship_quantity=ship_quantity,
                            weight_unit=shipment_amount_unit,
                            contract_weight_left=contract_weight_left,
                            lot_number=lot_number
                        )

                    if final_payment_date not in [None, '', ' ', 'null']:            
                        outbound.final_payment_date=final_payment_date  
                    outbound.save()

                    if carrier_id:
                        CarrierDetails.objects.create(shipment=outbound, carrier_id=carrier_id)      
                    
                    for file in files:
                        ProcessorWarehouseShipmentDocuments.objects.create(shipment=outbound, document_file=file)   

                    if outbound.warehouse_id not in [None, 'null', ' ', '']:                            
                        all_user = WarehouseUser.objects.filter(warehouse_id=outbound.warehouse_id)                         
                        distributors = Distributor.objects.filter(warehouse__id=outbound.warehouse_id)                         
                        distributor_users = DistributorUser.objects.filter(distributor__in=distributors)
                    else:                            
                        all_user = CustomerUser.objects.filter(customer_id=outbound.customer_id)
                        distributor_users = []                          
                    all_users = list(all_user) + list(distributor_users)
                    for user in all_users :
                        msg = f'A shipment has been sent  under Contract ID - {outbound.contract.secret_key}'
                        get_user = User.objects.get(username=user.contact_email)
                        notification_reason = 'New Shipment'
                        redirect_url = "/warehouse/list-processor-shipment/"
                        save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
                            notification_reason=notification_reason)
                        save_notification.save()                 
                            
                    return redirect('list-processor-shipment')      

                return render(request, "distributor/create_processor_shipment.html", context)       
            
        else:
            return redirect('login')        
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/create_processor_shipment.html', context)
        

@login_required()
def list_processor_shipment(request):
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
            shipments = ProcessorWarehouseShipment.objects.prefetch_related(
                    Prefetch('processor_shipment_crop', queryset=ProcessorShipmentCrops.objects.all())
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
                shipments = shipments.filter(processor_id=int(processor_id))

            search_name = request.GET.get('search_name', '')

            if search_name and search_name is not None:
                shipments = shipments.filter(Q(warehouse_name__icontains=search_name) |
                                             Q(customer_name__icontains=search_name) |
                                             Q(processor_shipment_crop__crop__icontains=search_name)|                                              
                                             Q(contract__secret_key__icontains=search_name) |
                                             Q(outbound_type__icontains=search_name) |
                                             Q(carrier_type__icontains=search_name) |
                                             Q(status__icontains=search_name) |
                                             Q(purchase_order_name__icontains=search_name) |
                                             Q(lot_number__icontains=search_name) |
                                             Q(purchase_order_number__icontains=search_name))
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
                    shipments = shipments.filter(date_pulled__range=[start_date, end_date])
                elif start_date:
                    shipments = shipments.filter(date_pulled__gte=start_date)
                elif end_date:
                    shipments = shipments.filter(date_pulled__lte=end_date)

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None            
            
            shipments = shipments.order_by('-id')
            paginator = Paginator(shipments, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'distributor/list_outbound.html', context)
        
        elif request.user.is_processor:
            user_email = request.user.email
            p = ProcessorUser.objects.get(contact_email=user_email)
            processor_id = Processor.objects.get(id=p.processor.id).id
            processor_type = "T1"

            shipments = ProcessorWarehouseShipment.objects.prefetch_related(
                    Prefetch('processor_shipment_crop', queryset=ProcessorShipmentCrops.objects.all())
                ).filter(processor_id=processor_id, processor_type=processor_type)
            search_name = request.GET.get('search_name', '')

            if search_name and search_name is not None:
                shipments = shipments.filter(Q(warehouse_name__icontains=search_name) |
                                             Q(customer_name__icontains=search_name) |
                                             Q(processor_shipment_crop__crop__icontains=search_name)| 
                                             Q(contract__secret_key__icontains=search_name) |
                                             Q(outbound_type__icontains=search_name) |
                                             Q(carrier_type__icontains=search_name) |
                                             Q(status__icontains=search_name) |
                                             Q(purchase_order_name__icontains=search_name) |
                                             Q(lot_number__icontains=search_name) |
                                             Q(purchase_order_number__icontains=search_name))
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
                    shipments = shipments.filter(date_pulled__range=[start_date, end_date])
                elif start_date:
                    shipments = shipments.filter(date_pulled__gte=start_date)
                elif end_date:
                    shipments = shipments.filter(date_pulled__lte=end_date)

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None
            shipments = shipments.order_by('-id')
            paginator = Paginator(shipments, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'distributor/list_outbound.html', context)
        
        elif request.user.is_processor2:
            user_email = request.user.email
            p = ProcessorUser2.objects.get(contact_email=user_email)
            processor_id = Processor2.objects.get(id=p.processor2.id).id
            processor_type = Processor2.objects.get(id=p.processor2.id).processor_type.all().first().type_name

            shipments = ProcessorWarehouseShipment.objects.prefetch_related(
                    Prefetch('processor_shipment_crop', queryset=ProcessorShipmentCrops.objects.all())
                ).filter(processor_id=processor_id, processor_type=processor_type)

            search_name = request.GET.get('search_name', '')

            if search_name and search_name is not None:
                shipments = shipments.filter(Q(warehouse_name__icontains=search_name) |
                                             Q(customer_name__icontains=search_name) |
                                             Q(processor_shipment_crop__crop__icontains=search_name)| 
                                             Q(contract__secret_key__icontains=search_name) |
                                             Q(outbound_type__icontains=search_name) |
                                             Q(carrier_type__icontains=search_name) |
                                             Q(status__icontains=search_name) |
                                             Q(purchase_order_name__icontains=search_name) |
                                             Q(lot_number__icontains=search_name) |
                                             Q(purchase_order_number__icontains=search_name))
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
                    shipments = shipments.filter(date_pulled__range=[start_date, end_date])
                elif start_date:
                    shipments = shipments.filter(date_pulled__gte=start_date)
                elif end_date:
                    shipments = shipments.filter(date_pulled__lte=end_date)

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None

            shipments = shipments.order_by('-id')
            paginator = Paginator(shipments, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'distributor/list_outbound.html', context)
        
        elif request.user.is_distributor: 
            user_email = request.user.email
            d = DistributorUser.objects.get(contact_email=user_email)
            distributor = Distributor.objects.get(id=d.distributor.id)
            warehouses = distributor.warehouse.all().values_list('id', flat=True)
            shipments = []
            for warehouse_id in warehouses:
                check_shipment = ProcessorWarehouseShipment.objects.prefetch_related(
                    Prefetch('processor_shipment_crop', queryset=ProcessorShipmentCrops.objects.all())
                ).filter(warehouse_id=warehouse_id).order_by('-id')
                if check_shipment:
                    shipments = shipments+list(check_shipment)
            search_name = request.GET.get('search_name', '')

            if search_name and search_name is not None:
                shipments = shipments.filter(Q(warehouse_name__icontains=search_name) |
                                             Q(customer_name__icontains=search_name) | 
                                             Q(processor_shipment_crop__crop__icontains=search_name)|                                            
                                             Q(contract__secret_key__icontains=search_name) |
                                             Q(outbound_type__icontains=search_name) |
                                             Q(carrier_type__icontains=search_name) |
                                             Q(status__icontains=search_name) |
                                             Q(purchase_order_name__icontains=search_name) |
                                             Q(lot_number__icontains=search_name) |
                                             Q(purchase_order_number__icontains=search_name))
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
                    shipments = shipments.filter(date_pulled__range=[start_date, end_date])
                elif start_date:
                    shipments = shipments.filter(date_pulled__gte=start_date)
                elif end_date:
                    shipments = shipments.filter(date_pulled__lte=end_date)

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None

            paginator = Paginator(shipments, 100)
            print(paginator)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            print(context)
            return render(request, 'distributor/list_outbound.html', context)
        
        elif request.user.is_warehouse_manager:
            user_email = request.user.email
            w = WarehouseUser.objects.get(contact_email=user_email)
            warehouse_id = Warehouse.objects.get(id=w.warehouse.id).id
            shipments = ProcessorWarehouseShipment.objects.prefetch_related(
                    Prefetch('processor_shipment_crop', queryset=ProcessorShipmentCrops.objects.all())
                ).filter(warehouse_id=warehouse_id)

            search_name = request.GET.get('search_name', '')

            if search_name and search_name is not None:
                shipments = shipments.filter(Q(warehouse_name__icontains=search_name) |
                                             Q(customer_name__icontains=search_name) |
                                             Q(processor_shipment_crop__crop__icontains=search_name)|                                             
                                             Q(contract__secret_key__icontains=search_name) |
                                             Q(outbound_type__icontains=search_name) |
                                             Q(carrier_type__icontains=search_name) |
                                             Q(status__icontains=search_name) |
                                             Q(purchase_order_name__icontains=search_name) |
                                             Q(lot_number__icontains=search_name) |
                                             Q(purchase_order_number__icontains=search_name))
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
                    shipments = shipments.filter(date_pulled__range=[start_date, end_date])
                elif start_date:
                    shipments = shipments.filter(date_pulled__gte=start_date)
                elif end_date:
                    shipments = shipments.filter(date_pulled__lte=end_date)

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None

            shipments = shipments.order_by('-id')
            paginator = Paginator(shipments, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'distributor/list_outbound.html', context)
        
        elif request.user.is_customer:
            user_email = request.user.email
            c = CustomerUser.objects.get(contact_email=user_email)
            customer_id = Customer.objects.get(id=c.customer.id).id
            shipments = ProcessorWarehouseShipment.objects.prefetch_related(
                    Prefetch('processor_shipment_crop', queryset=ProcessorShipmentCrops.objects.all())
                ).filter(customer_id=customer_id)

            search_name = request.GET.get('search_name', '')

            if search_name and search_name is not None:
                shipments = shipments.filter(Q(warehouse_name__icontains=search_name) |
                                             Q(customer_name__icontains=search_name) | 
                                             Q(processor_shipment_crop__crop__icontains=search_name)|                                         
                                             Q(contract__secret_key__icontains=search_name) |
                                             Q(outbound_type__icontains=search_name) |
                                             Q(carrier_type__icontains=search_name) |
                                             Q(status__icontains=search_name) |
                                             Q(purchase_order_name__icontains=search_name) |
                                             Q(lot_number__icontains=search_name) |
                                             Q(purchase_order_number__icontains=search_name))
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
                    shipments = shipments.filter(date_pulled__range=[start_date, end_date])
                elif start_date:
                    shipments = shipments.filter(date_pulled__gte=start_date)
                elif end_date:
                    shipments = shipments.filter(date_pulled__lte=end_date)

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None
                
            shipments = shipments.order_by('-id')
            paginator = Paginator(shipments, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'distributor/list_outbound.html', context)
        else:
            messages.error(request, "Not a valid request.")
            return redirect("dashboard")   
    except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/list_outbound.html', context)


@login_required()
def processor_shipment_view(request, pk):
    context = {}
    try:
        shipment = ProcessorWarehouseShipment.objects.prefetch_related(
                    Prefetch('processor_shipment_crop', queryset=ProcessorShipmentCrops.objects.all())
                ).filter(id=pk).first()        
        carrier_details = CarrierDetails.objects.filter(shipment=shipment)
        shipment_date_str = shipment.date_pulled.strftime('%d %b, %Y') if shipment.date_pulled else None
        first_shipment = GrowerShipment.objects.order_by('date_time').first()
        if first_shipment:
            from_date = first_shipment.date_time.date() 
        else:
            from_date = None  
        to_date = date.today()
        datapy = {
            "shipment_id": shipment.shipment_id,
            "sender": shipment.processor_entity_name,            
            "shipment_date": shipment_date_str,
            "receiver": shipment.warehouse_name if shipment.warehouse_id not in ['null', '', None, ' '] else shipment.customer_name,
            "receive_date": shipment.distributor_receive_date,
            "traceability_url":  f"{request.scheme}://{request.get_host()}/tracemodule/trace_shipment/{shipment.shipment_id}/{from_date}/{to_date}/"
        }
        data = json.dumps(datapy)           
        img = qrcode.make(data)
        img_name = 'qr1_' + str(int(time.time())) + '.png'         
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)            
        file = ContentFile(buffer.read(), name=img_name)

        shipment.qr_code.save(img_name, file, save=True)
        img_name = shipment.qr_code
        context["img_name"] = img_name
        context["shipment"] = shipment
        context["documents"] = [
            {
                "id": file.id,
                "file": file.document_file,
                "name": file.document_file.name.split("/")[-1]  # Extract only the file name
            }
            for file in ProcessorWarehouseShipmentDocuments.objects.filter(shipment=shipment)
        ]
        context["carriers"] = carrier_details
        logs = ProcessorShipmentLog.objects.filter(shipment=shipment).order_by('id')
        context['logs'] = logs
        lot_entries = ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment)
        context["lot_entries"] = lot_entries
        return render (request, 'distributor/view_outbound.html', context)
    except (ValueError, AttributeError, ProcessorWarehouseShipment.DoesNotExist) as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/view_outbound.html', context)


def find_changes(data, shipment):
    changes = []    
    
    carrier_id = data.get("carrier_id")
    if carrier_id:
        carrier = CarrierDetails.objects.filter(shipment=shipment).first()
        if carrier and carrier.carrier_id != carrier_id:
            changes.append({"field": "Carrier ID", "old": carrier.carrier_id, "new": carrier_id})
   
    purchase_order_name = data.get("purchase_order_name")
    if purchase_order_name and shipment.purchase_order_name != purchase_order_name:
        changes.append({"field": "Purchase Order Name", "old": shipment.purchase_order_name, "new": purchase_order_name})
    
    purchase_order_number = data.get("purchase_order_number")
    if purchase_order_number and shipment.purchase_order_number != purchase_order_number:
        changes.append({"field": "Purchase Order Number", "old": shipment.purchase_order_number, "new": purchase_order_number})

    crop_ids = data.getlist('crop_id[]')
    lot_numbers = data.getlist('lot_number[]')
    gross_weights = data.getlist('gross_weight[]')
    weights = data.getlist('weight[]')
    ship_weights = data.getlist('ship_weight[]')
    ship_quantities = data.getlist('ship_quantity[]')
    id_crops = data.getlist("id_crop[]")
    print(id_crops, crop_ids, gross_weights, weights, ship_quantities, ship_weights)

    for index, crop_id in enumerate(id_crops):
        print(index)
        print(crop_ids[index])
        try:
            crop_instance = ProcessorShipmentCrops.objects.get(pk=crop_id)

            crop = int(crop_ids[index]) if crop_ids[index] else None
            if crop is not None and int(crop_instance.crop_id) != crop:
                crop_ = CropDetails.objects.filter(id=int(crop)).first().crop
                changes.append({
                    "field": f"Crop (Crop ID: {crop_id})",
                    "old": crop_instance.crop,
                    "new": crop_
                })
            
            lot_number = lot_numbers[index] if lot_numbers[index] else None
            if lot_number is not None and crop_instance.lot_number != lot_number:
                changes.append({
                    "field": f"Lot Number (Crop ID: {crop_id})",
                    "old": crop_instance.lot_number,
                    "new": lot_number
                })

            gross_weight = float(gross_weights[index]) if gross_weights[index] else None
            if gross_weight is not None and crop_instance.gross_weight != gross_weight:
                changes.append({
                    "field": f"Gross Weight (Crop ID: {crop_id})",
                    "old": crop_instance.gross_weight,
                    "new": gross_weight
                })

            net_weight = float(weights[index]) if weights[index] else None
            if net_weight is not None and crop_instance.net_weight != net_weight:
                changes.append({
                    "field": f"Net Weight (Crop ID: {crop_id})",
                    "old": crop_instance.net_weight,
                    "new": net_weight
                })

            ship_weight = float(ship_weights[index]) if ship_weights[index] else None
            if ship_weight is not None and crop_instance.ship_weight != ship_weight:
                changes.append({
                    "field": f"Ship Weight (Crop ID: {crop_id})",
                    "old": crop_instance.ship_weight,
                    "new": ship_weight
                })

            ship_quantity = int(ship_quantities[index]) if ship_quantities[index] else None
            if ship_quantity is not None and crop_instance.ship_quantity != ship_quantity:
                changes.append({
                    "field": f"Ship Quantity (Crop ID: {crop_id})",
                    "old": crop_instance.ship_quantity,
                    "new": ship_quantity
                })

        except ProcessorShipmentCrops.DoesNotExist:
            changes.append({"field": f"Crop ID {crop_id}", "old": "Not Found", "new": "New Crop Added"})
   
    status = data.get("status")
    if status and shipment.status != status:
        changes.append({"field": "Status", "old": shipment.status, "new": status})
   
    border_receive_date = data.get("border_receive_date")
    if border_receive_date:
        border_receive_date_parsed = datetime.strptime(border_receive_date, '%Y-%m-%d').date()
        stored_border_receive_date = shipment.border_receive_date.date() if shipment.border_receive_date else None
        if stored_border_receive_date != border_receive_date_parsed:
            changes.append({"field": "Border Receive Date", "old": str(stored_border_receive_date), "new": str(border_receive_date_parsed)})
    
    border_leaving_date = data.get("border_leaving_date")
    if border_leaving_date:
        border_leaving_date_parsed = datetime.strptime(border_leaving_date, '%Y-%m-%d').date()
        stored_border_leaving_date = shipment.border_leaving_date.date() if shipment.border_leaving_date else None
        if stored_border_leaving_date != border_leaving_date_parsed:
            changes.append({"field": "Border Leaving Date", "old": str(stored_border_leaving_date), "new": str(border_leaving_date_parsed)})
    
    final_receive_date = data.get("final_receive_date")
    if final_receive_date:
        final_receive_date_parsed = datetime.strptime(final_receive_date, '%Y-%m-%d').date()
        stored_receive_date = shipment.distributor_receive_date.date() if shipment.distributor_receive_date else None
        if stored_receive_date != final_receive_date_parsed:
            changes.append({"field": "Warehouse/Customer Receive Date", "old": str(stored_receive_date), "new": str(final_receive_date_parsed)})
   
    final_leaving_date = data.get("final_leaving_date")
    if final_leaving_date:
        final_leaving_date_parsed = datetime.strptime(final_leaving_date, '%Y-%m-%d').date()
        stored_leaving_date = shipment.distributor_leaving_date.date() if shipment.distributor_leaving_date else None
        if stored_leaving_date != final_leaving_date_parsed:
            changes.append({"field": "Warehouse/Customer Leaving Date", "old": str(stored_leaving_date), "new": str(final_leaving_date_parsed)})
    
    border_receive_date2 = data.get("border_receive_date2")
    if border_receive_date2:
        border_receive_date2_parsed = datetime.strptime(border_receive_date2, '%Y-%m-%d').date()
        stored_border_receive_date2 = shipment.border_back_receive_date.date() if shipment.border_back_receive_date else None
        if stored_border_receive_date2 != border_receive_date2_parsed:
            changes.append({"field": "Border Receive Date Back", "old": str(stored_border_receive_date2), "new": str(border_receive_date2_parsed)})
  
    border_leaving_date2 = data.get("border_leaving_date2")
    if border_leaving_date2:
        border_leaving_date2_parsed = datetime.strptime(border_leaving_date2, '%Y-%m-%d').date()
        stored_border_leaving_date2 = shipment.border_back_leaving_date.date() if shipment.border_back_leaving_date else None
        if stored_border_leaving_date2 != border_leaving_date2_parsed:
            changes.append({"field": "Border Leaving Date Back", "old": str(stored_border_leaving_date2), "new": str(border_leaving_date2_parsed)})
   
    processor_receive_date = data.get("processor_receive_date")
    if processor_receive_date:
        processor_receive_date_parsed = datetime.strptime(processor_receive_date, '%Y-%m-%d').date()
        stored_processor_receive_date = shipment.processor_receive_date.date() if shipment.processor_receive_date else None
        if stored_processor_receive_date != processor_receive_date_parsed:
            changes.append({"field": "Processor Receive Date", "old": str(stored_processor_receive_date), "new": str(processor_receive_date_parsed)})
    
    final_payment_date = data.get("final_payment_date")
    if final_payment_date:
        final_payment_date_parsed = datetime.strptime(final_payment_date, '%Y-%m-%d').date()
        stored_final_payment_date = shipment.final_payment_date.date() if shipment.final_payment_date else None
        if stored_final_payment_date != final_payment_date_parsed:
            changes.append({"field": "Final Payment Date", "old": str(stored_final_payment_date), "new": str(final_payment_date_parsed)})

    if data.get("files"):
        existing_files = [
            file.document_file.name.split("/")[-1]
            for file in ProcessorWarehouseShipmentDocuments.objects.filter(shipment=shipment)
        ]
        uploaded_files = [file["name"] for file in data.get("files")]
        if set(existing_files) != set(uploaded_files):
            changes.append({"field": "Upload File", "old": existing_files, "new": uploaded_files})

    return changes


###########################################QuickBooks Included#############################
# @login_required()
# def edit_processor_shipment(request, pk):
#     context = {}
#     try:
#         if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_processor or request.user.is_processor2:
#             try:
#                 from apps.quickbooks_integration.models import QuickBooksToken
#                 from apps.quickbooks_integration.views import refresh_quickbooks_token, update_purchase_order, get_purchase_order_data, get_chart_of_accounts
#                 token_instance = QuickBooksToken.objects.first()                                    
#                 refresh_token = token_instance.refresh_token
#                 success_url = reverse('edit-processor-shipment', kwargs={'pk': pk})
#                 next_url = f"{success_url}"
#                 redirect_url = f"{reverse('quickbooks_login')}?{urlencode({'next': next_url})}"
#                 if token_instance.is_token_expired():
#                     print("Token expired, refreshing...")
#                     new_access_token = refresh_quickbooks_token(refresh_token)
#                     if not new_access_token:
#                         return redirect(redirect_url)
#                     token_instance.access_token = new_access_token
#                     token_instance.expires_at = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
#                     token_instance.save()
#             except QuickBooksToken.DoesNotExist:
#                 return redirect(redirect_url)
#             check_shipment = ProcessorWarehouseShipment.objects.filter(id=pk)
            
#             shipment = check_shipment.first()        
#             carrier = CarrierDetails.objects.filter(shipment=shipment).first()
#             if carrier:
#                 context['carrier_id'] = carrier.carrier_id
#             context["files"] = [
#                 {
#                     "id": file.id,
#                     "name": file.document_file.name.split("/")[-1]  # Extract only the file name
#                 }
#                 for file in ProcessorWarehouseShipmentDocuments.objects.filter(shipment=shipment)
#             ]
#             context["shipment"] = shipment
#             context['crops'] = CropDetails.objects.filter(contract=shipment.contract)
#             selected_contract = shipment.contract               
                                    
#             processor_id = shipment.contract.processor_id
#             processor_type = shipment.contract.processor_type
#             destination_type = 'customer' if shipment.customer_id not in [None,'',' ', 'null'] else 'warehouse'
#             if destination_type == 'customer':
#                 destination_list = Customer.objects.filter(is_active=True).values('id','name')
#             else:
#                 destination_list = Warehouse.objects.all().values('id','name')
#             destination_id = shipment.warehouse_id if shipment.warehouse_id not in [None,'',' ', 'null'] else shipment.customer_id
#             destination_id = int(destination_id) if destination_id else None
            

#             crops = CropDetails.objects.filter(contract=shipment.contract).values('id', 'crop', 'crop_type')
#             crop = CropDetails.objects.filter(id=int(shipment.crop_id), contract=shipment.contract).first()
#             current_time = timezone.now()
#             customer_contracts = AdminCustomerContract.objects.filter(customer_id=int(destination_id), customerContractCrop__crop=crop.crop, customerContractCrop__crop_type=crop.crop_type,contract_start_date__lte=current_time, end_date__gte=current_time)
          
#             additional_lots = ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment)
#             context.update({           
#                 "milled_value": "None",
#                 "selected_processor_sku_id_list":shipment.processor_sku_list,
#                 "selected_destination": destination_type,
#                 "warehouse_name" : shipment.warehouse_name,
#                 "customer_name": shipment.customer_name ,             
#                 "contract":selected_contract,                        
#                 "selected_processor_id": processor_id,
#                 'destination_list':destination_list,
#                 "destination_id" : destination_id ,
#                 "customer_contract":shipment.customer_contract,
#                 "customer_contracts": customer_contracts,
#                 "crops":crops,
#                 "additional_lots":additional_lots
#             })
            
#             if request.method == "POST":
#                 data = request.POST
                
#                 button_value = request.POST.getlist('remove_files')                
#                 if button_value:
#                     for file_id in button_value:
#                         try:
#                             file_obj = ProcessorWarehouseShipmentDocuments.objects.get(id=file_id)
#                             file_obj.delete()
#                         except ProcessorWarehouseShipmentDocuments.DoesNotExist:
#                             pass          
#                 selected_sku_id = data.get('sender_sku_id')
#                 destination_type = data.get('selected_destination')
                
#                 context.update({                    
#                     "carrier_type": data.get('carrier_type'),                    
#                     "outbound_type": data.get('outbound_type'),
#                     "purchase_order_name":data.get('purchase_order_name'),
#                     "purchase_order_number": data.get('purchase_order_number'),
#                     "lot_number": data.get('lot_number'),
#                     "selected_processor_sku_id_list": [selected_sku_id],
#                     "selected_destination": destination_type,
#                     "weight":data.get('weight'),
#                     "gross_weight":data.get('gross_weight'),
#                     "ship_weight":data.get('ship_weight'),
#                     "ship_quantity":data.get('ship_quantity'),
#                     "status":data.get('status'),
#                     "amount_unit":data.get('amount_unit') , 
#                     "selected_crop": data.get('crop_id'), 
#                     "final_receive_date": data.get('final_receive_date'),
#                     "border_receive_date" : data.get('border_receive_date'),
#                     "border_leaving_date": data.get('border_leaving_date'),
#                     "final_leaving_date" : data.get('final_leaving_date'),
#                     "border_receive_date2": data.get('border_receive_date2'),
#                     "border_leaving_date2" : data.get('border_leaving_date2'),
#                     "processor_receive_date": data.get('processor_receive_date'),
#                     "selected_customer_contract" :data.get('customer_contract'),
#                     "final_payment_date":data.get("final_payment_date")            
                    
#                 })            

#                 if destination_type == "customer" and destination_id and data.get('crop_id'):
#                     crop = CropDetails.objects.filter(id=int(data.get('crop_id')), contract=shipment.contract).first()
                   
#                     customer_contracts = AdminCustomerContract.objects.filter(customer_id=int(destination_id), customerContractCrop__crop=crop.crop, customerContractCrop__crop_type=crop.crop_type, contract_start_date__lte=current_time,end_date__gte=current_time)
                    
#                     context["customer_contracts"] = customer_contracts
                
#                 if processor_id and not data.get("save"):                     
#                     if selected_sku_id :                        
#                         context["milled_value"] =  calculate_milled_volume(crop.crop, int(processor_id), processor_type, selected_sku_id)
#                         context["selected_sku"] = selected_sku_id
                    
#                     context["sender_sku_id_list"] = get_sku_list(int(processor_id),processor_type)["data"]
#                     if destination_type == 'warehouse':
#                         context['destination_list'] = Warehouse.objects.all().values('id','name')
#                     if destination_type == 'customer':
#                         context['destination_list'] = Customer.objects.filter(is_active=True).values('id','name')
#                     return render(request, 'distributor/edit_outbound.html', context)
#                 else:
#                     if destination_type == 'warehouse':
#                         warehouse_id = Warehouse.objects.get(id=int(data.get('destination_id'))).id
#                         warehouse_name = Warehouse.objects.get(id=int(data.get('destination_id'))).name
#                         customer_id = None
#                         customer_name = None
#                         customer_contract = None
#                     else:
#                         warehouse_id = None
#                         warehouse_name = None
#                         customer_id = Customer.objects.get(id=int(context.get('destination_id'))).id
#                         customer_name = Customer.objects.get(id=int(context.get('destination_id'))).name
#                         selected_customer_contract = data.get('customer_contract')
#                         customer_contract = AdminCustomerContract.objects.filter(id=int(selected_customer_contract)).first()                   

#                     if data.get('carrier_type') == 'Truck/Trailer':
#                         if data.get('gross_weight') not in [None, 'null', ' ', ''] and data.get('ship_weight') not in [None, 'null', ' ', ''] and data.get('ship_quantity') not in [None, 'null', ' ', '']:
#                             ship_quantity = int(data.get('ship_quantity'))
#                             gross_weight = float(data.get('gross_weight'))
#                             ship_weight = float(data.get('ship_weight'))                                    
#                             net_weight = gross_weight - (ship_weight * ship_quantity)
#                         else:
#                             context["error_messages"] = "Please provide Gross weight, Ship weight and Ship quantity."
#                             return render(request, 'distributor/edit_outbound.html', context)
                                
#                     elif data.get('carrier_type') == 'Rail Car':
                        
#                         gross_weight = 0
#                         ship_quantity = 1
#                         ship_weight = 0
#                         if data.get('weight') not in [None, 'null', ' ', '']:
#                             net_weight = float(data.get('weight'))
#                         else:
#                             context["error_messages"] = "Please provide Weight."
#                             return render(request, 'distributor/edit_outbound.html', context)
#                     crop = CropDetails.objects.filter(id=int(data.get('crop_id')), contract=shipment.contract).first()
#                     crop_name = crop.crop
#                     if crop.amount_unit == data.get('amount_unit'):
#                         contract_weight_left = float(crop.left_amount) - float(net_weight)
#                     else:
#                         if crop.amount_unit == "LBS" and data.get('amount_unit') == "MT":
#                             net_weight_lbs = float(net_weight) * 2204.62
#                             contract_weight_left = float(crop.left_amount) - net_weight_lbs 
#                         else:
#                             net_weight_mt = float(net_weight) * 0.000453592
#                             contract_weight_left = float(crop.left_amount) - net_weight_mt 
#                     changes = find_changes(context, shipment)
#                     shipment.contract=shipment.contract
#                     shipment.processor_id=processor_id
#                     shipment.processor_type=processor_type
#                     shipment.processor_entity_name=shipment.contract.processor_entity_name
#                     shipment.processor_sku_list=[selected_sku_id]
#                     shipment.carrier_type=data.get('carrier_type')
#                     shipment.outbound_type=data.get('outbound_type')
#                     shipment.purchase_order_name=data.get('purchase_order_name')
#                     shipment.purchase_order_number=data.get('purchase_order_number')
#                     shipment.lot_number=data.get('lot_number')
#                     shipment.crop = crop.id
#                     shipment.crop = crop_name
#                     shipment.gross_weight=gross_weight
#                     shipment.net_weight=net_weight
#                     shipment.ship_weight=ship_weight
#                     shipment.weight_unit=data.get('amount_unit')
#                     shipment.ship_quantity=ship_quantity
#                     shipment.contract_weight_left=contract_weight_left
#                     shipment.status= data.get('status')
#                     shipment.customer_id=customer_id
#                     shipment.warehouse_id=warehouse_id
#                     shipment.customer_name=customer_name
#                     shipment.warehouse_name=warehouse_name
#                     shipment.customer_contract=customer_contract
                                                                            
#                     shipment.save()
#                     if data.get('border_receive_date') not in [None, '', ' ', 'null']:
#                         border_receive_date = data.get('border_receive_date')
#                         shipment.border_receive_date= border_receive_date
#                     if data.get('border_leaving_date') not in [None, '', ' ', 'null']:
#                         border_leaving_date = data.get('border_leaving_date')
#                         shipment.border_leaving_date=border_leaving_date
#                     if data.get('final_receive_date') not in [None, '', ' ', 'null']:
#                         final_receive_date = data.get('final_receive_date')
#                         shipment.distributor_receive_date=final_receive_date
#                     if data.get('final_leaving_date') not in [None, '', ' ', 'null']:
#                         final_leaving_date = data.get('final_leaving_date')
#                         shipment.distributor_leaving_date=final_leaving_date
#                     if data.get('border_receive_date2') not in [None, '', ' ', 'null']:
#                         border_receive_date2 = data.get('border_receive_date2')
#                         shipment.border_back_receive_date=border_receive_date2
#                     if data.get('border_leaving_date2') not in [None, '', ' ', 'null']:
#                         border_leaving_date2 = data.get('border_leaving_date2')                    
#                         shipment.border_back_leaving_date= border_leaving_date2
#                     if data.get('processor_receive_date') not in [None, '', ' ', 'null']:
#                         processor_receive_date = data.get('processor_receive_date')
#                         shipment.processor_receive_date=processor_receive_date

#                     if data.get('final_payment_date') not in [None, '', ' ', 'null']:
#                         final_payment_date = data.get('final_payment_date')
#                         shipment.final_payment_date=final_payment_date
                    
#                     shipment.save()                   

#                     carrier_id = data.get('carrier_id')
#                     if carrier_id:
#                         # Get or create carrier details
#                         carrier_details, created = CarrierDetails.objects.update_or_create(
#                             shipment=shipment,
#                             defaults={'carrier_id': carrier_id}
#                         )
#                     else:
#                         # Ensure that carrier details are not deleted if no carrier_id is provided
#                         CarrierDetails.objects.filter(shipment=shipment).delete()
                    
#                     files = request.FILES.getlist('files')
#                     for file in files:
#                         ProcessorWarehouseShipmentDocuments.objects.create(shipment=shipment, document_file=file)

#                     lot_numbers = request.POST.getlist('lot_number[]')
#                     addresses = request.POST.getlist('address[]')
#                     descriptions = request.POST.getlist('description[]')
                    
#                     existing_lot_entries = list(
#                         ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment)
#                         .values('additional_lot_number', 'address', 'description')
#                     )
#                     if existing_lot_entries:                       
#                         old_value = existing_lot_entries[-1]['additional_lot_number']
#                     else:                        
#                         old_value = shipment.lot_number
                  
#                     ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment).delete()                   

#                     for lot_number, address, description in zip(lot_numbers, addresses, descriptions):
#                         additional_lot = ProcessorShipmentLotNumberTracking(
#                             shipment=shipment,
#                             additional_lot_number=lot_number,
#                             address=address,
#                             description=description
#                         )
#                         additional_lot.save()

#                         if {'additional_lot_number': lot_number, 'address': address, 'description': description} not in existing_lot_entries:
#                             changes.append({
#                                 "field": "Lot Number",
#                                 "old": old_value,
#                                 "new":lot_number
                                    
#                             })
#                         print(changes)
                    
#                     descriptions = request.POST.getlist('description')

#                     for  description in  descriptions:
#                         if  description:
                            
#                             ProcessorShipmentLog.objects.create(
#                                 shipment=shipment,                           
#                                 description=description,
#                                 changes = {"changes":changes},
#                                 updated_by = request.user
#                             )
#                         else:
#                             context["error_messages"] = f'PLease give description'
#                             return render(request, 'distributor/edit_outbound.html', context)
                    
#                     purchase = Purchase.objects.filter(shipment=shipment).first()  
                        
#                     item = ShipmentItem.objects.filter(
#                         item_name=crop.crop, item_type=crop.crop_type, 
#                         per_unit_price=crop.per_unit_rate
#                     ).first() 

#                     if shipment.processor_type == "T1":
#                         processor = Processor.objects.filter(id= int(shipment.processor_id)).first()
#                     else:
#                         processor = Processor2.objects.filter(id= int(shipment.processor_id)).first()

#                     accounts = get_chart_of_accounts(token_instance.realm_id, token_instance.access_token)                       
                        
#                     ap_account_id = None
#                     for account in accounts:
#                         if account['AccountType'] == 'Accounts Payable' and account['AccountSubType'] == 'AccountsPayable':
#                             ap_account_id = account['Id'] 
#                             break                       

#                     if not ap_account_id:
#                         messages.error(request, "Accounts Payable account not found in QuickBooks.")
#                         return render(request, 'distributor/create_outbound.html', context)
#                     purchase_order_id = purchase.quickbooks_id
                      
#                     data = get_purchase_order_data(purchase_order_id)
#                     sync_token = data.get("PurchaseOrder", {}).get("SyncToken")
                    
#                     doc_number = data.get("PurchaseOrder", {}).get("DocNumber")
#                     purchase_order_data = {
#                         "Id": str(purchase_order_id),
#                         "SyncToken": str(sync_token),
#                         "DocNumber": str(doc_number),
#                         "TotalAmt": float(purchase.amount),  
#                         "TxnDate": datetime.now().strftime('%Y-%m-%d'),  
#                         "Line": [
#                             {
#                                 "DetailType": "ItemBasedExpenseLineDetail",
#                                 "Amount": float(purchase.amount),  
#                                 "ItemBasedExpenseLineDetail": {
#                                     "ItemRef": {
#                                         "value": str(item.quickbooks_id),  
#                                         "name": str(item.item_name) 
#                                     },
#                                     "Qty": float(shipment.net_weight),  
#                                     "UnitPrice": float(purchase.per_unit_rate), 
#                                     "TaxCodeRef": {
#                                         "value": "NON" 
#                                     },
#                                     "BillableStatus": "NotBillable"  
#                                 }
#                             }
#                         ],
#                         "APAccountRef": {
#                             "name": "Accounts Payable (A/P)", 
#                             "value": str(ap_account_id) 
#                         },
#                         "VendorRef": {
#                             "name": str(shipment.processor_entity_name), 
#                             "value": str(processor.quickbooks_id) 
#                         },                                              
#                         'CurrencyRef': {
#                             'value': 'USD', 
#                             'name': 'United States Dollar'
#                         },
#                         "CustomField": [
#                             {
#                                 "DefinitionId": '1',  
#                                 "Type": "StringType",  
#                                 "Name": "ShipmentId",
#                                 "StringValue": str(purchase.shipment.shipment_id)  
#                             }
#                         ]
#                     }

#                     try:                        
#                         updated_purchase_order = update_purchase_order(token_instance.realm_id, token_instance.access_token, purchase_order_id, purchase_order_data)                        
#                         if updated_purchase_order:                                
#                             messages.success(request, "Purchase order updated successfully and synced with QuickBooks.")
#                         else:
#                             messages.success(request, "Failed to update Purchase in QuickBooks.")
#                     except Exception as qb_error:
                       
#                         messages.error(request, f"Error updating purchase order in QuickBooks: {str(qb_error)}")
#                         return render(request, 'distributor/edit_outbound.html', context)    
#                 return redirect('view-processor-shipment', pk=pk)
            
#             return render(request, 'distributor/edit_outbound.html', context)
                        
#     except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
#         context["error_messages"] = str(e)
#         return render(request, 'distributor/edit_outbound.html', context)


###################################Single Crop###############################
# @login_required()
# def edit_processor_shipment(request, pk):
#     context = {}
#     try:
#         if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_processor or request.user.is_processor2:
            
#             check_shipment = ProcessorWarehouseShipment.objects.filter(id=pk)            
#             shipment = check_shipment.first()        
#             carrier = CarrierDetails.objects.filter(shipment=shipment).first()
#             if carrier:
#                 context['carrier_id'] = carrier.carrier_id
#             context["files"] = [
#                 {
#                     "id": file.id,
#                     "name": file.document_file.name.split("/")[-1] 
#                 }
#                 for file in ProcessorWarehouseShipmentDocuments.objects.filter(shipment=shipment)
#             ]
#             context["shipment"] = shipment
#             context['crops'] = CropDetails.objects.filter(contract=shipment.contract)
#             selected_contract = shipment.contract               
                                    
#             processor_id = shipment.contract.processor_id
#             processor_type = shipment.contract.processor_type
#             destination_type = 'customer' if shipment.customer_id not in [None,'',' ', 'null'] else 'warehouse'
#             if destination_type == 'customer':
#                 destination_list = Customer.objects.filter(is_active=True).values('id','name')
#             else:
#                 destination_list = Warehouse.objects.all().values('id','name')
#             destination_id = shipment.warehouse_id if shipment.warehouse_id not in [None,'',' ', 'null'] else shipment.customer_id
#             destination_id = int(destination_id) if destination_id else None
            

#             crops = CropDetails.objects.filter(contract=shipment.contract).values('id', 'crop', 'crop_type')
#             crop = CropDetails.objects.filter(id=int(shipment.crop_id), contract=shipment.contract).first()
#             current_time = timezone.now()
#             customer_contracts = AdminCustomerContract.objects.filter(customer_id=int(destination_id), customerContractCrop__crop=crop.crop, customerContractCrop__crop_type=crop.crop_type,contract_start_date__lte=current_time, end_date__gte=current_time)
          
#             additional_lots = ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment)
#             context.update({           
#                 "milled_value": "None",
#                 "selected_processor_sku_id_list":shipment.processor_sku_list,
#                 "selected_destination": destination_type,
#                 "warehouse_name" : shipment.warehouse_name,
#                 "customer_name": shipment.customer_name ,             
#                 "contract":selected_contract,                        
#                 "selected_processor_id": processor_id,
#                 'destination_list':destination_list,
#                 "destination_id" : destination_id ,
#                 "customer_contract":shipment.customer_contract,
#                 "customer_contracts": customer_contracts,
#                 "crops":crops,
#                 "additional_lots":additional_lots
#             })
            
#             if request.method == "POST":
#                 data = request.POST
                
#                 button_value = request.POST.getlist('remove_files')                
#                 if button_value:
#                     for file_id in button_value:
#                         try:
#                             file_obj = ProcessorWarehouseShipmentDocuments.objects.get(id=file_id)
#                             file_obj.delete()
#                         except ProcessorWarehouseShipmentDocuments.DoesNotExist:
#                             pass          
#                 selected_sku_id = data.get('sender_sku_id')
#                 destination_type = data.get('selected_destination')
                
#                 context.update({                    
#                     "carrier_type": data.get('carrier_type'),                    
#                     "outbound_type": data.get('outbound_type'),
#                     "purchase_order_name":data.get('purchase_order_name'),
#                     "purchase_order_number": data.get('purchase_order_number'),
#                     "lot_number": data.get('lot_number'),
#                     "selected_processor_sku_id_list": [selected_sku_id],
#                     "selected_destination": destination_type,
#                     "weight":data.get('weight'),
#                     "gross_weight":data.get('gross_weight'),
#                     "ship_weight":data.get('ship_weight'),
#                     "ship_quantity":data.get('ship_quantity'),
#                     "status":data.get('status'),
#                     "amount_unit":data.get('amount_unit') , 
#                     "selected_crop": data.get('crop_id'), 
#                     "final_receive_date": data.get('final_receive_date'),
#                     "border_receive_date" : data.get('border_receive_date'),
#                     "border_leaving_date": data.get('border_leaving_date'),
#                     "final_leaving_date" : data.get('final_leaving_date'),
#                     "border_receive_date2": data.get('border_receive_date2'),
#                     "border_leaving_date2" : data.get('border_leaving_date2'),
#                     "processor_receive_date": data.get('processor_receive_date'),
#                     "selected_customer_contract" :data.get('customer_contract'),
#                     "final_payment_date":data.get("final_payment_date")            
                    
#                 })            

#                 if destination_type == "customer" and destination_id and data.get('crop_id'):
#                     crop = CropDetails.objects.filter(id=int(data.get('crop_id')), contract=shipment.contract).first()
                   
#                     customer_contracts = AdminCustomerContract.objects.filter(customer_id=int(destination_id), customerContractCrop__crop=crop.crop, customerContractCrop__crop_type=crop.crop_type, contract_start_date__lte=current_time,end_date__gte=current_time)
                    
#                     context["customer_contracts"] = customer_contracts
                
#                 if processor_id and not data.get("save"):                     
#                     if selected_sku_id :                        
#                         context["milled_value"] =  calculate_milled_volume(crop.crop, int(processor_id), processor_type, selected_sku_id)
#                         context["selected_sku"] = selected_sku_id
                    
#                     context["sender_sku_id_list"] = get_sku_list(int(processor_id),processor_type)["data"]
#                     if destination_type == 'warehouse':
#                         context['destination_list'] = Warehouse.objects.all().values('id','name')
#                     if destination_type == 'customer':
#                         context['destination_list'] = Customer.objects.filter(is_active=True).values('id','name')
#                     return render(request, 'distributor/edit_outbound.html', context)
#                 else:
#                     if destination_type == 'warehouse':
#                         warehouse_id = Warehouse.objects.get(id=int(data.get('destination_id'))).id
#                         warehouse_name = Warehouse.objects.get(id=int(data.get('destination_id'))).name
#                         customer_id = None
#                         customer_name = None
#                         customer_contract = None
#                     else:
#                         warehouse_id = None
#                         warehouse_name = None
#                         customer_id = Customer.objects.get(id=int(context.get('destination_id'))).id
#                         customer_name = Customer.objects.get(id=int(context.get('destination_id'))).name
#                         selected_customer_contract = data.get('customer_contract')
#                         customer_contract = AdminCustomerContract.objects.filter(id=int(selected_customer_contract)).first()                   

#                     if data.get('carrier_type') == 'Truck/Trailer':
#                         if data.get('gross_weight') not in [None, 'null', ' ', ''] and data.get('ship_weight') not in [None, 'null', ' ', ''] and data.get('ship_quantity') not in [None, 'null', ' ', '']:
#                             ship_quantity = int(data.get('ship_quantity'))
#                             gross_weight = float(data.get('gross_weight'))
#                             ship_weight = float(data.get('ship_weight'))                                    
#                             net_weight = gross_weight - (ship_weight * ship_quantity)
#                         else:
#                             context["error_messages"] = "Please provide Gross weight, Ship weight and Ship quantity."
#                             return render(request, 'distributor/edit_outbound.html', context)
                                
#                     elif data.get('carrier_type') == 'Rail Car':
                        
#                         gross_weight = 0
#                         ship_quantity = 1
#                         ship_weight = 0
#                         if data.get('weight') not in [None, 'null', ' ', '']:
#                             net_weight = float(data.get('weight'))
#                         else:
#                             context["error_messages"] = "Please provide Weight."
#                             return render(request, 'distributor/edit_outbound.html', context)
#                     crop = CropDetails.objects.filter(id=int(data.get('crop_id')), contract=shipment.contract).first()
#                     crop_name = crop.crop
#                     if crop.amount_unit == data.get('amount_unit'):
#                         contract_weight_left = float(crop.left_amount) - float(net_weight)
#                     else:
#                         if crop.amount_unit == "LBS" and data.get('amount_unit') == "MT":
#                             net_weight_lbs = float(net_weight) * 2204.62
#                             contract_weight_left = float(crop.left_amount) - net_weight_lbs 
#                         else:
#                             net_weight_mt = float(net_weight) * 0.000453592
#                             contract_weight_left = float(crop.left_amount) - net_weight_mt 
#                     changes = find_changes(context, shipment)
#                     shipment.contract=shipment.contract
#                     shipment.processor_id=processor_id
#                     shipment.processor_type=processor_type
#                     shipment.processor_entity_name=shipment.contract.processor_entity_name
#                     shipment.processor_sku_list=[selected_sku_id]
#                     shipment.carrier_type=data.get('carrier_type')
#                     shipment.outbound_type=data.get('outbound_type')
#                     shipment.purchase_order_name=data.get('purchase_order_name')
#                     shipment.purchase_order_number=data.get('purchase_order_number')
#                     shipment.lot_number=data.get('lot_number')
#                     shipment.crop = crop.id
#                     shipment.crop = crop_name
#                     shipment.gross_weight=gross_weight
#                     shipment.net_weight=net_weight
#                     shipment.ship_weight=ship_weight
#                     shipment.weight_unit=data.get('amount_unit')
#                     shipment.ship_quantity=ship_quantity
#                     shipment.contract_weight_left=contract_weight_left
#                     shipment.status= data.get('status')
#                     shipment.customer_id=customer_id
#                     shipment.warehouse_id=warehouse_id
#                     shipment.customer_name=customer_name
#                     shipment.warehouse_name=warehouse_name
#                     shipment.customer_contract=customer_contract
                                                                            
#                     shipment.save()
#                     if data.get('border_receive_date') not in [None, '', ' ', 'null']:
#                         border_receive_date = data.get('border_receive_date')
#                         shipment.border_receive_date= border_receive_date
#                     if data.get('border_leaving_date') not in [None, '', ' ', 'null']:
#                         border_leaving_date = data.get('border_leaving_date')
#                         shipment.border_leaving_date=border_leaving_date
#                     if data.get('final_receive_date') not in [None, '', ' ', 'null']:
#                         final_receive_date = data.get('final_receive_date')
#                         shipment.distributor_receive_date=final_receive_date
#                     if data.get('final_leaving_date') not in [None, '', ' ', 'null']:
#                         final_leaving_date = data.get('final_leaving_date')
#                         shipment.distributor_leaving_date=final_leaving_date
#                     if data.get('border_receive_date2') not in [None, '', ' ', 'null']:
#                         border_receive_date2 = data.get('border_receive_date2')
#                         shipment.border_back_receive_date=border_receive_date2
#                     if data.get('border_leaving_date2') not in [None, '', ' ', 'null']:
#                         border_leaving_date2 = data.get('border_leaving_date2')                    
#                         shipment.border_back_leaving_date= border_leaving_date2
#                     if data.get('processor_receive_date') not in [None, '', ' ', 'null']:
#                         processor_receive_date = data.get('processor_receive_date')
#                         shipment.processor_receive_date=processor_receive_date

#                     if data.get('final_payment_date') not in [None, '', ' ', 'null']:
#                         final_payment_date = data.get('final_payment_date')
#                         shipment.final_payment_date=final_payment_date
                    
#                     shipment.save()                   

#                     carrier_id = data.get('carrier_id')
#                     if carrier_id:
#                         # Get or create carrier details
#                         carrier_details, created = CarrierDetails.objects.update_or_create(
#                             shipment=shipment,
#                             defaults={'carrier_id': carrier_id}
#                         )
#                     else:
#                         # Ensure that carrier details are not deleted if no carrier_id is provided
#                         CarrierDetails.objects.filter(shipment=shipment).delete()
                    
#                     files = request.FILES.getlist('files')
#                     for file in files:
#                         ProcessorWarehouseShipmentDocuments.objects.create(shipment=shipment, document_file=file)

#                     lot_numbers = request.POST.getlist('lot_number[]')
#                     addresses = request.POST.getlist('address[]')
#                     descriptions = request.POST.getlist('description[]')
                    
#                     existing_lot_entries = list(
#                         ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment)
#                         .values('additional_lot_number', 'address', 'description')
#                     )
#                     if existing_lot_entries:                       
#                         old_value = existing_lot_entries[-1]['additional_lot_number']
#                     else:                        
#                         old_value = shipment.lot_number
                  
#                     ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment).delete()                   

#                     for lot_number, address, description in zip(lot_numbers, addresses, descriptions):
#                         additional_lot = ProcessorShipmentLotNumberTracking(
#                             shipment=shipment,
#                             additional_lot_number=lot_number,
#                             address=address,
#                             description=description
#                         )
#                         additional_lot.save()

#                         if {'additional_lot_number': lot_number, 'address': address, 'description': description} not in existing_lot_entries:
#                             changes.append({
#                                 "field": "Lot Number",
#                                 "old": old_value,
#                                 "new":lot_number
                                    
#                             })
#                         print(changes)
                    
#                     descriptions = request.POST.getlist('description')

#                     for  description in  descriptions:
#                         if  description:
                            
#                             ProcessorShipmentLog.objects.create(
#                                 shipment=shipment,                           
#                                 description=description,
#                                 changes = {"changes":changes},
#                                 updated_by = request.user
#                             )
#                         else:
#                             context["error_messages"] = f'PLease give description'
#                             return render(request, 'distributor/edit_outbound.html', context)                   
                       
#                 return redirect('view-processor-shipment', pk=pk)
            
#             return render(request, 'distributor/edit_outbound.html', context)
                        
#     except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
#         context["error_messages"] = str(e)
#         return render(request, 'distributor/edit_outbound.html', context)


@login_required()
def edit_processor_shipment(request, pk):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_processor or request.user.is_processor2:
            
            check_shipment = ProcessorWarehouseShipment.objects.filter(id=pk)            
            shipment = check_shipment.first()        
            carrier = CarrierDetails.objects.filter(shipment=shipment).first()
            if carrier:
                context['carrier_id'] = carrier.carrier_id
            context["files"] = [
                {
                    "id": file.id,
                    "name": file.document_file.name.split("/")[-1] 
                }
                for file in ProcessorWarehouseShipmentDocuments.objects.filter(shipment=shipment)
            ]
            context["shipment"] = shipment  
            if shipment.processor_type == "T1":
                processor = Processor.objects.filter(id=int(shipment.processor_id)).first()
                processor_location = Location.objects.filter(processor=processor).first().name 
                if processor_location:
                    location = processor_location.name
                else:
                    location = "Origin location"
            else:
                processor = Processor2.objects.filter(id=int(shipment.processor_id)).first()
                processor_location = Processor2Location.objects.filter(processor=processor).first()
                if processor_location:
                    location = processor_location.name
                else:
                    location = "Origin location"
            
            destination_type = 'customer' if shipment.customer_id not in [None,'',' ', 'null'] else 'warehouse'
            if destination_type == 'customer':
                destination_list = Customer.objects.filter(is_active=True).values('id','name')
                context["selected_customer_contract"] = shipment.customer_contract.id
            else:
                destination_list = Warehouse.objects.all().values('id','name')
            destination_id = shipment.warehouse_id if shipment.warehouse_id not in [None,'',' ', 'null'] else shipment.customer_id
            destination_id = int(destination_id) if destination_id else None            

            crops = ProcessorShipmentCrops.objects.filter(shipment=shipment)
            current_time = timezone.now()
            customer_contracts = AdminCustomerContract.objects.filter(contract_start_date__lte=current_time, end_date__gte=current_time)
          
            additional_lots = ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment)
            context.update({        
                "selected_destination": destination_type,             
                "contract":shipment.contract,                      
                'destination_list':destination_list,
                "destination_id" : destination_id ,                           
                "crops":crops,
                "additional_lots":additional_lots,
                "customer_contracts":customer_contracts
            })
            
            if request.method == "POST":
                data = request.POST                  
                outbound_type = data.get('outbound_type')
                carrier_type = data.get('carrier_type')
                carrier_id = data.get('carrier_id')
                purchase_order_name = data.get('purchase_order_name')
                purchase_order_number = data.get('purchase_order_number')                
                amount_unit = data.get('amount_unit')

                shipment_type = data.get('shipment_type') 
                destination_type = data.get('selected_destination')
                destination_id = data.get('destination_id') 
                customer_contract = data.get('customer_contract')                   
                crop_ids = data.getlist('crop_id[]')
                lot_numbers = data.getlist('lot_number[]')
                print(crop_ids)
                gross_weights = data.getlist('gross_weight[]')
                weights = data.getlist('weight[]')            
                ship_weights = data.getlist('ship_weight[]')
                ship_quantities = data.getlist('ship_quantity[]') 
                delete_flags = data.getlist("delete_flag[]") 
                id_crops = data.getlist("id_crop[]")
                files = request.FILES.getlist('files')
                button_value = data.getlist('remove_files') 
                final_payment_date = data.get('final_payment_date')       
                status = data.get('status')
                border_receive_date = data.get('border_receive_date')
                border_leaving_date = data.get('border_leaving_date') 
                final_receive_date = data.get('final_receive_date')
                final_leaving_date = data.get('final_leaving_date')
                border_receive_date2 = data.get('border_receive_date2')  
                border_leaving_date2 = data.get('border_leaving_date2') 
                processor_receive_date = data.get('processor_receive_date')           
                button_value = request.POST.getlist('remove_files') 

                if button_value:
                    for file_id in button_value:
                        try:
                            file_obj = ProcessorWarehouseShipmentDocuments.objects.get(id=file_id)
                            file_obj.delete()
                        except ProcessorWarehouseShipmentDocuments.DoesNotExist:
                            pass          
               
                if destination_type == 'warehouse':
                    warehouse_id = Warehouse.objects.get(id=int(destination_id)).id
                    warehouse_name = Warehouse.objects.get(id=int(destination_id)).name
                    customer_id = None
                    customer_name = None
                    customer_contract = None
                else:
                    warehouse_id = None
                    warehouse_name = None
                    customer_id = Customer.objects.get(id=int(destination_id)).id
                    customer_name = Customer.objects.get(id=int(destination_id)).name            
                    customer_contract = AdminCustomerContract.objects.filter(id=int(customer_contract)).first()                   

                changes = find_changes(data, shipment)                   
                shipment.carrier_type=carrier_type
                shipment.outbound_type=outbound_type
                shipment.purchase_order_name=purchase_order_name
                shipment.purchase_order_number=purchase_order_number
               
                shipment.shipment_type=shipment_type
                shipment.status=status
                shipment.customer_id=customer_id
                shipment.warehouse_id=warehouse_id
                shipment.customer_name=customer_name
                shipment.warehouse_name=warehouse_name
                shipment.customer_contract=customer_contract
                                                                        
                shipment.save()

                with transaction.atomic():
                    for i, id_crop in enumerate(id_crops):
                        if id_crop.isdigit() and delete_flags[i] == "1":
                            try:
                                ProcessorShipmentCrops.objects.get(id=int(id_crop)).delete()
                                print(f"Deleted crop with id {id_crop}")
                            except ProcessorShipmentCrops.DoesNotExist:
                                print(f"Crop with id {id_crop} not found.")
                        else:
                            print(f"Skipping crop with id {id_crop}, not marked for deletion.")

                    for i, crop_id in enumerate(crop_ids):
                        crop = CropDetails.objects.filter(id=int(crop_id)).first()
                        gross_weight = float(gross_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                        ship_weight = float(ship_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                        ship_quantity = int(ship_quantities[i]) if carrier_type == 'Truck/Trailer' else 1
                        weight = float(weights[i]) if carrier_type == 'Rail Car' else 0
                        lot_number = lot_numbers[i]
                        
                        if carrier_type == 'Truck/Trailer':
                            net_weight = gross_weight - (ship_weight * ship_quantity)
                        elif carrier_type == 'Rail Car':
                            net_weight = weight
                        
                        if crop.amount_unit == amount_unit:
                            contract_weight_left = float(crop.left_amount) - float(net_weight)
                        else:
                            if crop.amount_unit == "LBS" and amount_unit == "MT":
                                net_weight_lbs = float(net_weight) * 2204.62
                                contract_weight_left = float(crop.left_amount) - net_weight_lbs
                            elif crop.amount_unit == "MT" and amount_unit == "LBS":
                                net_weight_mt = float(net_weight) * 0.000453592
                                contract_weight_left = float(crop.left_amount) - net_weight_mt
                            else:
                                raise ValueError(f"Unsupported conversion from {crop.amount_unit} to {amount_unit}")
                            
                        id_crop = id_crops[i] if i < len(id_crops) else None
                        if id_crop and id_crop.isdigit():
                            try:
                                crop_detail = ProcessorShipmentCrops.objects.get(id=int(id_crop))                                    
                                crop_detail.crop_id = crop_id
                                crop.crop = crop.crop
                                crop.crop_type = crop.crop_type
                                crop_detail.net_weight = net_weight
                                crop_detail.weight_unit = amount_unit
                                crop_detail.gross_weight = gross_weight
                                crop_detail.ship_quantity = ship_quantity
                                crop_detail.ship_weight = ship_weight
                                crop_detail.contract_weight_left = contract_weight_left
                                crop_detail.lot_number = lot_number
                                crop_detail.save()                              
                                
                            except ProcessorShipmentCrops.DoesNotExist:
                                print(f"Crop with id {id_crop} not found.")
                        else:
                            ProcessorShipmentCrops.objects.create(
                                shipment=shipment,
                                crop_id=crop_id,
                                crop=crop.crop,
                                crop_type=crop.crop_type,
                                net_weight=net_weight,
                                gross_weight=gross_weight,
                                ship_weight=ship_weight,
                                ship_quantity=ship_quantity,
                                weight_unit=amount_unit,
                                contract_weight_left=contract_weight_left,
                                lot_number=lot_number
                            )                      

                if border_receive_date not in [None, '', ' ', 'null']:                      
                    shipment.border_receive_date= border_receive_date

                if border_leaving_date not in [None, '', ' ', 'null']:                        
                    shipment.border_leaving_date=border_leaving_date

                if final_receive_date not in [None, '', ' ', 'null']:                        
                    shipment.distributor_receive_date=final_receive_date

                if final_leaving_date not in [None, '', ' ', 'null']:                        
                    shipment.distributor_leaving_date=final_leaving_date

                if border_receive_date2 not in [None, '', ' ', 'null']:                        
                    shipment.border_back_receive_date=border_receive_date2

                if border_leaving_date2 not in [None, '', ' ', 'null']:                                          
                    shipment.border_back_leaving_date= border_leaving_date2
                    
                if processor_receive_date not in [None, '', ' ', 'null']:                       
                    shipment.processor_receive_date=processor_receive_date

                if final_payment_date not in [None, '', ' ', 'null']:                        
                    shipment.final_payment_date=final_payment_date
                
                shipment.save()                   

                carrier_id = data.get('carrier_id')
                if carrier_id:                     
                    carrier_details, created = CarrierDetails.objects.update_or_create(
                        shipment=shipment,
                        defaults={'carrier_id': carrier_id}
                    )
                else:                      
                    CarrierDetails.objects.filter(shipment=shipment).delete()
                
                for file in files:
                    ProcessorWarehouseShipmentDocuments.objects.create(shipment=shipment, document_file=file)

                crops = request.POST.getlist('crop[]')
                additional_lot_numbers = request.POST.getlist('additional_lot_number[]')
                addresses = request.POST.getlist('address[]')
                descriptions = request.POST.getlist('description[]')
                
                existing_lot_entries = ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment).select_related('crop')

                existing_lot_mapping = {
                    entry.crop.id: {
                        "additional_lot_number": entry.additional_lot_number,
                        "address": entry.address
                    } 
                    for entry in existing_lot_entries if entry.crop
                }

                ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment).delete()

                for crop_id, lot_number, address, description in zip(crops, additional_lot_numbers, addresses, descriptions):
                    
                    crop = ProcessorShipmentCrops.objects.filter(id=int(crop_id)).first()
                    if not crop:
                        continue  

                    old_lot_number = existing_lot_mapping.get(crop.id, {}).get("additional_lot_number", crop.lot_number)
                    old_address = existing_lot_mapping.get(crop.id, {}).get("address", location)

                    new_tracking_entry = ProcessorShipmentLotNumberTracking(
                        shipment=shipment,
                        crop=crop,
                        additional_lot_number=lot_number,
                        address=address,
                        description=description
                    )
                    new_tracking_entry.save()

                    if lot_number != old_lot_number:
                        changes.append({
                            "field": f"Lot Number of {crop}",
                            "old": old_lot_number,
                            "new": lot_number
                        })

                    if address != old_address:
                        changes.append({
                            "field": "Address",
                            "old": old_address,
                            "new": address
                        })

                descriptions = request.POST.getlist('description')

                for  description in  descriptions:
                    if  description:
                        
                        ProcessorShipmentLog.objects.create(
                            shipment=shipment,                           
                            description=description,
                            changes = {"changes":changes},
                            updated_by = request.user
                        )
                    else:
                        context["error_messages"] = f'PLease give description'
                        return render(request, 'distributor/edit_processor_shipment.html', context)                   
                       
                return redirect('view-processor-shipment', pk=pk)
            
            return render(request, 'distributor/edit_processor_shipment.html', context)
                        
    except (ValueError, AttributeError, ProcessorWarehouseShipment.DoesNotExist) as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/edit_processor_shipment.html', context)


@login_required
def processor_shipment_current_location_track(request, pk):
    context = {}
    try:
        check_shipment = ProcessorWarehouseShipment.objects.filter(id=pk)
        shipment = check_shipment.first()
        first_shipment = GrowerShipment.objects.order_by('date_time').first()
        if first_shipment:
            from_date = first_shipment.date_time.date() 
        else:
            from_date = None  
        to_date = date.today()
        if shipment.processor_type == "T1":
            processor = Processor.objects.filter(id=int(shipment.processor_id)).first()
            processor_location = Location.objects.filter(processor=processor).first()
            origin_lat =processor_location.latitude
            origin_long = processor_location.longitude
        else:
            processor = Processor2.objects.filter(id=int(shipment.processor_id)).first()
            processor_location = Processor2Location.objects.filter(processor=processor).first()
            origin_lat =processor_location.latitude
            origin_long = processor_location.longitude

        if shipment.customer_id not in [None, " ", "null", ""]:
            destination = Customer.objects.filter(id=int(shipment.customer_id)).first() 
        else:
            destination = Warehouse.objects.filter(id=int(shipment.warehouse_id)).first()

        origin_lat = float(origin_lat)  
        origin_long = float(origin_long)  
        destination_lat = float(destination.latitude)  
        destination_long = float(destination.longitude)  
        shipment_status = shipment.status
        additional_lat_long = []
        current_location = None
        check_lot_entries = list(ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment).values_list("address", flat=True))
        if check_lot_entries:
            for entry in check_lot_entries:
                print(entry)
                additional_lat, additional_long = get_lat_lng(entry, settings.MAP_API_KEY)
                if additional_lat and additional_long:                    
                    additional_lat_long.append({"lat":additional_lat, "lng":additional_long})
                         
        if check_lot_entries and shipment_status != "Received":
            current_location = additional_lat_long[-1]
        elif check_lot_entries and shipment_status == "Received":
            current_location = {"lat": destination_lat, "lng": destination_long}
        elif not check_lot_entries and shipment_status == "Received":
            current_location = {"lat": destination_lat, "lng": destination_long}
        elif not check_lot_entries and shipment_status != "Received":
            current_location = {"lat": origin_lat, "lng": origin_long}

        context = {
            "origin": {"lat": origin_lat, "lng": origin_long},
            "destination": {"lat": destination_lat, "lng": destination_long},
            "waypoints": additional_lat_long,
            "shipment_status": shipment_status,
            "current_location": current_location,
            "source":processor.entity_name,
            "destination_name": destination.name,
            "shipment_id":shipment.shipment_id,
            "contract_id":shipment.contract.secret_key,
            "from_date": from_date,
            "to_date": to_date
        }
        print(context)
        return render(request, "distributor/processor_shipment_location_tracker.html", context)        
    except (ValueError, AttributeError, ProcessorWarehouseShipment.DoesNotExist) as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/list_outbound.html', context)


###########################################QuickBooks Included#############################
# @login_required()
# def delete_processor_shipment(request, pk):
#     context = {}
#     try:
#         if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
#             try:
#                 from apps.quickbooks_integration.models import QuickBooksToken
#                 from apps.quickbooks_integration.views import refresh_quickbooks_token, delete_purchase_order, get_purchase_order_data, get_invoice_data, delete_invoice
#                 token_instance = QuickBooksToken.objects.first()                                    
#                 refresh_token = token_instance.refresh_token
#                 success_url = reverse('delete-processor-shipment', kwargs={'pk': pk})
#                 next_url = f"{success_url}"
#                 redirect_url = f"{reverse('quickbooks_login')}?{urlencode({'next': next_url})}"
#                 if token_instance.is_token_expired():
#                     print("Token expired, refreshing...")
#                     new_access_token = refresh_quickbooks_token(refresh_token)
#                     if not new_access_token:
#                         return redirect(redirect_url)
#                     token_instance.access_token = new_access_token
#                     token_instance.expires_at = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
#                     token_instance.save()
#             except QuickBooksToken.DoesNotExist:
#                 return redirect(redirect_url)
#             check_shipment = ProcessorWarehouseShipment.objects.filter(id=pk)            
#             shipment = check_shipment.first()        
#             purchase = Purchase.objects.filter(shipment=shipment).first()
#             invoice = Invoice.objects.filter(processor_shipment=shipment).first()
#             if request.method == "POST":
#                 if purchase:
#                     purchase_order_id = purchase.quickbooks_id
#                     purchase_details = get_purchase_order_data(purchase_order_id)
#                     sync_token = purchase_details.get('PurchaseOrder', {}).get('SyncToken', '')
#                     purchase_data = {
#                         "SyncToken": str(sync_token), 
#                         "Id": str(purchase_order_id)
#                     }
#                     deleted_purchase = delete_purchase_order(token_instance.realm_id, token_instance.access_token, purchase_data)

#                     if deleted_purchase:
#                         print("Purchase order deleted successfully and synced with quickbooks")
#                     else:
#                         print("Failed to delete purchase order from quickbooks.")
#                     purchase.delete()
#                 if invoice:
#                     invoice_id = invoice.quickbooks_id
#                     invoice_details = get_invoice_data(invoice_id)
#                     sync_token = invoice_details.get('Invoice', {}).get('SyncToken', '')
#                     invoice_data = {
#                         "SyncToken": str(sync_token), 
#                         "Id": str(invoice_id)
#                     }
#                     deleted_invoice = delete_invoice(token_instance.realm_id, token_instance.access_token, invoice_data)
#                     if deleted_invoice:
#                         print("Invoice deleted successfully and synced with quickbooks")
#                     else:
#                         print("Failed to delete invoice from quickbooks.")
#                     invoice.delete()
#                 shipment.delete()
#                 return redirect('list-processor-shipment')
#             return render(request, 'distributor/list_outbound.html', context)
                
#     except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
#         context["error_messages"] = str(e)
#         return render(request, 'distributor/list_outbound.html', context)


@login_required()
def delete_processor_shipment(request, pk):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
           
            check_shipment = ProcessorWarehouseShipment.objects.filter(id=pk)            
            shipment = check_shipment.first()        
            purchase = Purchase.objects.filter(shipment=shipment).first()
            invoice = Invoice.objects.filter(processor_shipment=shipment).first()
            if request.method == "POST":
                if purchase:                    
                    purchase.delete()
                if invoice:                    
                    invoice.delete()
                shipment.delete()
                return redirect('list-processor-shipment')
            return render(request, 'distributor/list_outbound.html', context)
                
    except (ValueError, AttributeError, ProcessorWarehouseShipment.DoesNotExist) as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/list_outbound.html', context)


###############################Single Crop##############################
# @login_required()
# def create_warehouse_shipment(request):
#     context = {}
#     try:
#         if request.user.is_authenticated:
#             if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
#                 current_time = timezone.now()
#                 contracts = AdminCustomerContract.objects.filter(contract_start_date__lte=current_time,end_date__gte=current_time).values('id','secret_key','customer_id','customer_name').order_by('-id')  
#                 warehouses = Warehouse.objects.all().values('id', 'name')              
#                 context["contracts"] = contracts
#                 context["warehouses"] = warehouses
#                 context.update({
#                     "selected_contract": None,                    
#                     "customer_id": None,
#                     "customer_name": None,
#                     "crops": [],            
#                 })
              
#                 if request.method == "POST":
#                     data = request.POST
#                     selected_contract = data.get('selected_contract') 
#                     selected_warehouse = data.get('selected_warehouse') 
#                     selected_crop = data.get('crop_id') 
#                     contract = AdminCustomerContract.objects.get(id=int(selected_contract))                   
#                     customer_id = contract.customer_id
#                     if not data.get('save'):
#                         context.update({
#                             "selected_contract":contract.id,
#                             "contract":contract,                        
#                             "selected_customer_id": int(customer_id),                            
#                             "carrier_type": data.get('carrier_type'),                    
#                             "outbound_type": data.get('outbound_type'),
#                             "purchase_order_name":data.get('purchase_order_name'),
#                             "purchase_order_number": data.get('purchase_order_number'),
#                             "lot_number": data.get('lot_number'),                        
#                             "weight":data.get('weight'),
#                             "gross_weight":data.get('gross_weight'),
#                             "ship_weight":data.get('ship_weight'),
#                             "ship_quantity":data.get('ship_quantity'),
#                             "status":data.get('status'),
#                             "amount_unit":data.get('amount_unit') ,                             
#                             "final_payment_date":data.get('final_payment_date')                   
                            
#                         }) 
#                         if selected_contract:
#                             context['selected_contract'] = int(selected_contract)
#                             context["crops"] = CustomerContractCropDetails.objects.filter(contract=contract).values('id', 'crop', 'crop_type')
#                             customer_id = AdminCustomerContract.objects.filter(id=int(selected_contract)).first().customer_id
#                             customer = Customer.objects.filter(id=int(customer_id)).first()
#                             context["warehouses"] = Warehouse.objects.filter(id=customer.warehouse.id).values('id', 'name')
#                         if selected_crop:
#                             selected_crop = int(selected_crop)
#                             context["selected_crop"] =selected_crop
#                         if selected_warehouse:
#                             context['selected_warehouse'] = int(selected_warehouse)
                        
#                     else:             
                         
#                         if data.get('carrier_type') == 'Truck/Trailer':
#                             if data.get('gross_weight') not in [None, 'null', ' ', ''] and data.get('ship_weight') not in [None, 'null', ' ', ''] and data.get('ship_quantity') not in [None, 'null', ' ', '']:
#                                 ship_quantity = int(data.get('ship_quantity'))
#                                 gross_weight = float(data.get('gross_weight'))
#                                 ship_weight = float(data.get('ship_weight'))                                    
#                                 net_weight = gross_weight - (ship_weight * ship_quantity)
#                             else:
#                                 context["error_messages"] = "Please provide Gross weight, Ship weight and Ship quantity."
#                                 return render(request, 'distributor/create_warehouse_outbound.html', context)
                            
#                         elif data.get('carrier_type') == 'Rail Car':
                            
#                             gross_weight = 0
#                             ship_quantity = 1
#                             ship_weight = 0
#                             if data.get('weight') not in [None, 'null', ' ', '']:
#                                 net_weight = float(data.get('weight'))
#                             else:
#                                 context["error_messages"] = "Please provide Weight."
#                                 return render(request, 'distributor/create_warehouse_outbound.html', context)
                        
#                         crop = CustomerContractCropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                         crop_name = crop.crop
                       
#                         if crop.amount_unit == data.get('amount_unit'):
#                             print('0000000000')
#                             contract_weight_left = float(crop.left_amount) - float(net_weight)
#                         else:
#                             if crop.amount_unit == "LBS" and data.get('amount_unit') == "MT":
#                                 net_weight_lbs = float(net_weight) * 2204.62
#                                 contract_weight_left = float(crop.left_amount) - net_weight_lbs 
#                             else:
#                                 net_weight_mt = float(net_weight) * 0.000453592
#                                 contract_weight_left = float(crop.left_amount) - net_weight_mt 
                           
#                         warehouse_name = Warehouse.objects.get(id=int(data.get('selected_warehouse'))).name                        
                        
#                         outbound = WarehouseCustomerShipment(
#                             contract=contract,
#                             warehouse_id=selected_warehouse, 
#                             warehouse_name = warehouse_name, 
#                             crop_id = crop.id,
#                             crop= crop_name,                      
#                             carrier_type=data.get('carrier_type'),
#                             outbound_type=data.get('outbound_type'),
#                             purchase_order_name=data.get('purchase_order_name'),
#                             purchase_order_number=data.get('purchase_order_number'),
#                             lot_number=data.get('lot_number'),
#                             gross_weight=gross_weight,
#                             net_weight=net_weight,
#                             ship_weight=ship_weight,
#                             weight_unit=data.get('amount_unit'),
#                             ship_quantity=ship_quantity,
#                             contract_weight_left=contract_weight_left,
#                             status=data.get('status'),
#                             customer_id=customer_id,                        
#                             customer_name=contract.customer_name,
                            
#                         )
#                         outbound.save()   
#                         if data.get('final_payment_date') not in [None, '', ' ', 'null']:
#                             final_payment_date = data.get('final_payment_date')
#                             outbound.final_payment_date=final_payment_date  
#                         outbound.save()                      
                        
#                         carrier_id = data.get('carrier_id')
#                         if carrier_id:
#                             CarrierDetails2.objects.create(shipment=outbound, carrier_id=carrier_id)
                        
#                         files = request.FILES.getlist('files')
#                         for file in files:
#                             WarehouseCustomerShipmentDocuments.objects.create(shipment=outbound, document_file=file)
                                             
#                         all_users = CustomerUser.objects.filter(customer_id=outbound.customer_id)
                        
#                         for user in all_users :
#                             msg = f'A shipment has been sent of {outbound.net_weight}{outbound.weight_unit} under Contract ID - {outbound.contract.secret_key}'
#                             get_user = User.objects.get(username=user.contact_email)
#                             notification_reason = 'New Shipment'
#                             redirect_url = "/warehouse/list-warehouse-shipment/"
#                             save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
#                                 notification_reason=notification_reason)
#                             save_notification.save()
                            
#                         return redirect('list-warehouse-shipment')  
#                 return render(request, 'distributor/create_warehouse_outbound.html', context) 
#             elif request.user.is_distributor: 
#                 current_time = timezone.now()               
#                 distributor_user = DistributorUser.objects.get(contact_email=request.user.email) 
#                 distributor = Distributor.objects.get(id=distributor_user.distributor.id)
#                 warehouses = distributor.warehouse.all().values('id', 'name') 
#                 warehouse_ids = [warehouse['id'] for warehouse in warehouses]
#                 customers = Customer.objects.filter(warehouse__id__in=warehouse_ids)  
#                 contracts = AdminCustomerContract.objects.filter(customer_id__in=customers.values_list('id', flat=True),contract_start_date__lte=current_time, end_date__gte=current_time).values('id', 'secret_key', 'customer_id', 'customer_name').order_by('-id')                    
#                 context["contracts"] = contracts
#                 context["warehouses"] = warehouses
#                 context.update({
#                     "selected_contract": None,                    
#                     "customer_id": None,
#                     "customer_name": None,
#                     "crops": [],            
#                 })
              
#                 if request.method == "POST":
#                     data = request.POST
#                     selected_contract = data.get('selected_contract') 
#                     selected_warehouse = data.get('selected_warehouse') 
#                     selected_crop = data.get('crop_id') 
#                     contract = AdminCustomerContract.objects.get(id=int(selected_contract))                   
#                     customer_id = contract.customer_id
#                     if not data.get('save'):
#                         context.update({
#                             "selected_contract":contract.id,
#                             "contract":contract,                        
#                             "selected_customer_id": int(customer_id),                            
#                             "carrier_type": data.get('carrier_type'),                    
#                             "outbound_type": data.get('outbound_type'),
#                             "purchase_order_name":data.get('purchase_order_name'),
#                             "purchase_order_number": data.get('purchase_order_number'),
#                             "lot_number": data.get('lot_number'),                        
#                             "weight":data.get('weight'),
#                             "gross_weight":data.get('gross_weight'),
#                             "ship_weight":data.get('ship_weight'),
#                             "ship_quantity":data.get('ship_quantity'),
#                             "status":data.get('status'),
#                             "amount_unit":data.get('amount_unit'),                            
#                             "final_payment_date":data.get('final_payment_date')                   
                            
#                         })
#                         if selected_crop:
#                             selected_crop = int(selected_crop)
#                             context["selected_crop"] =selected_crop 
#                         if selected_warehouse:
#                             context['selected_warehouse'] = int(selected_warehouse)
#                         if selected_contract:
#                             context['selected_contract'] = int(selected_contract)
#                             context["crops"] = CustomerContractCropDetails.objects.filter(contract=contract).values('id', 'crop','crop_type')
#                     else:             
                         
#                         if data.get('carrier_type') == 'Truck/Trailer':
#                             if data.get('gross_weight') not in [None, 'null', ' ', ''] and data.get('ship_weight') not in [None, 'null', ' ', ''] and data.get('ship_quantity') not in [None, 'null', ' ', '']:
#                                 ship_quantity = int(data.get('ship_quantity'))
#                                 gross_weight = float(data.get('gross_weight'))
#                                 ship_weight = float(data.get('ship_weight'))                                    
#                                 net_weight = gross_weight - (ship_weight * ship_quantity)
#                             else:
#                                 context["error_messages"] = "Please provide Gross weight, Ship weight and Ship quantity."
#                                 return render(request, 'distributor/create_outbound.html', context)
                            
#                         elif data.get('carrier_type') == 'Rail Car':
                            
#                             gross_weight = 0
#                             ship_quantity = 1
#                             ship_weight = 0
#                             if data.get('weight') not in [None, 'null', ' ', '']:
#                                 net_weight = float(data.get('weight'))
#                             else:
#                                 context["error_messages"] = "Please provide Weight."
#                                 return render(request, 'distributor/create_outbound.html', context)
                        
#                         crop = CustomerContractCropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                         crop_name = crop.crop
                       
#                         if crop.amount_unit == data.get('amount_unit'):
#                             contract_weight_left = float(crop.left_amount) - float(net_weight)
#                         else:
#                             if crop.amount_unit == "LBS" and data.get('amount_unit') == "MT":
#                                 net_weight_lbs = float(net_weight) * 2204.62
#                                 contract_weight_left = float(crop.left_amount) - net_weight_lbs 
#                             else:
#                                 net_weight_mt = float(net_weight) * 0.000453592
#                                 contract_weight_left = float(crop.left_amount) - net_weight_mt 

#                         warehouse_name = Warehouse.objects.get(id=int(data.get('selected_warehouse'))).name                        
#                         print(context.get('carrier_type'), context.get('outbound_type'), context.get('purchase_order_name'), context.get('purchase_order_number'), context.get('lot_number'), context.get('status'))
#                         outbound = WarehouseCustomerShipment(
#                             contract=contract,
#                             warehouse_id=selected_warehouse, 
#                             warehouse_name = warehouse_name, 
#                             crop_id = crop.id,
#                             crop= crop_name,                      
#                             carrier_type=data.get('carrier_type'),
#                             outbound_type=data.get('outbound_type'),
#                             purchase_order_name=data.get('purchase_order_name'),
#                             purchase_order_number=data.get('purchase_order_number'),
#                             lot_number=data.get('lot_number'),
#                             gross_weight=gross_weight,
#                             net_weight=net_weight,
#                             ship_weight=ship_weight,
#                             weight_unit=data.get('amount_unit'),
#                             ship_quantity=ship_quantity,
#                             contract_weight_left=contract_weight_left,
#                             status=data.get('status'),
#                             customer_id=customer_id,                        
#                             customer_name=contract.customer_name,
                            
#                         )
#                         outbound.save() 
#                         if data.get('final_payment_date') not in [None, '', ' ', 'null']:
#                             final_payment_date = data.get('final_payment_date')
#                             outbound.final_payment_date=final_payment_date  
#                         outbound.save()                          
                        
#                         carrier_id = data.get('carrier_id')
#                         if carrier_id:
#                             CarrierDetails2.objects.create(shipment=outbound, carrier_id=carrier_id)
                        
#                         files = request.FILES.getlist('files')
#                         for file in files:
#                             WarehouseCustomerShipmentDocuments.objects.create(shipment=outbound, document_file=file)

#                         ## Send notification to the Destination.                                                
#                         all_users = CustomerUser.objects.filter(customer_id=outbound.customer_id)
                        
#                         for user in all_users :
#                             msg = f'A shipment has been sent of {outbound.net_weight}{outbound.weight_unit} under Contract ID - {outbound.contract.secret_key}'
#                             get_user = User.objects.get(username=user.contact_email)
#                             notification_reason = 'New Shipment'
#                             redirect_url = "/warehouse/list-warehouse-shipment/"
#                             save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
#                                 notification_reason=notification_reason)
#                             save_notification.save()
                            
#                         return redirect('list-warehouse-shipment')  
#                 return render(request, 'distributor/create_warehouse_outbound.html', context)
#             elif request.user.is_warehouse_manager:              
#                 current_time = timezone.now()
#                 warehouse_user = WarehouseUser.objects.get(contact_email=request.user.email) 
#                 warehouse = warehouse_user.warehouse
#                 customers = Customer.objects.filter(warehouse=warehouse)  
#                 contracts = AdminCustomerContract.objects.filter(customer_id__in=customers.values_list('id', flat=True),contract_start_date__lte=current_time, end_date__gte=current_time).values('id', 'secret_key', 'customer_id', 'customer_name').order_by('-id')            
#                 context["contracts"] = contracts
#                 context["warehouses"] = warehouse
#                 context.update({
#                     "selected_contract": None,                    
#                     "customer_id": None,
#                     "customer_name": None,
#                     "crops": [],            
#                 })
              
#                 if request.method == "POST":
#                     data = request.POST
#                     selected_contract = data.get('selected_contract') 
#                     selected_warehouse = data.get('selected_warehouse') 
#                     selected_crop = data.get('crop_id') 
#                     contract = AdminCustomerContract.objects.get(id=int(selected_contract))                   
#                     customer_id = contract.customer_id
#                     if not data.get('save'):
#                         context.update({
#                             "selected_contract":contract.id,
#                             "contract":contract,                        
#                             "selected_customer_id": int(customer_id),                            
#                             "carrier_type": data.get('carrier_type'),                    
#                             "outbound_type": data.get('outbound_type'),
#                             "purchase_order_name":data.get('purchase_order_name'),
#                             "purchase_order_number": data.get('purchase_order_number'),
#                             "lot_number": data.get('lot_number'),                        
#                             "weight":data.get('weight'),
#                             "gross_weight":data.get('gross_weight'),
#                             "ship_weight":data.get('ship_weight'),
#                             "ship_quantity":data.get('ship_quantity'),
#                             "status":data.get('status'),
#                             "amount_unit":data.get('amount_unit'),                            
#                             "final_payment_date":data.get("final_payment_date")                    
                            
#                         }) 
#                         if selected_crop:
#                             selected_crop = int(selected_crop)
#                             context["selected_crop"] =selected_crop
#                         if selected_warehouse:
#                             context['selected_warehouse'] = int(selected_warehouse)
#                         if selected_contract:
#                             context['selected_contract'] = int(selected_contract)
#                             context["crops"] = CustomerContractCropDetails.objects.filter(contract=contract).values('id', 'crop','crop_type')
#                     else:             
                         
#                         if data.get('carrier_type') == 'Truck/Trailer':
#                             if data.get('gross_weight') not in [None, 'null', ' ', ''] and data.get('ship_weight') not in [None, 'null', ' ', ''] and data.get('ship_quantity') not in [None, 'null', ' ', '']:
#                                 ship_quantity = int(data.get('ship_quantity'))
#                                 gross_weight = float(data.get('gross_weight'))
#                                 ship_weight = float(data.get('ship_weight'))                                    
#                                 net_weight = gross_weight - (ship_weight * ship_quantity)
#                             else:
#                                 context["error_messages"] = "Please provide Gross weight, Ship weight and Ship quantity."
#                                 return render(request, 'distributor/create_outbound.html', context)
                            
#                         elif data.get('carrier_type') == 'Rail Car':
                            
#                             gross_weight = 0
#                             ship_quantity = 1
#                             ship_weight = 0
#                             if data.get('weight') not in [None, 'null', ' ', '']:
#                                 net_weight = float(data.get('weight'))
#                             else:
#                                 context["error_messages"] = "Please provide Weight."
#                                 return render(request, 'distributor/create_outbound.html', context)
                        
#                         crop = CustomerContractCropDetails.objects.filter(id=int(selected_crop), contract=contract).first()
#                         crop_name = crop.crop
                       
#                         if crop.amount_unit == data.get('amount_unit'):
#                             contract_weight_left = float(crop.left_amount) - float(net_weight)
#                         else:
#                             if crop.amount_unit == "LBS" and data.get('amount_unit') == "MT":
#                                 net_weight_lbs = float(net_weight) * 2204.62
#                                 contract_weight_left = float(crop.left_amount) - net_weight_lbs 
#                             else:
#                                 net_weight_mt = float(net_weight) * 0.000453592
#                                 contract_weight_left = float(crop.left_amount) - net_weight_mt 

#                         warehouse_name = Warehouse.objects.get(id=int(data.get('selected_warehouse'))).name                        
#                         print(context.get('carrier_type'), context.get('outbound_type'), context.get('purchase_order_name'), context.get('purchase_order_number'), context.get('lot_number'), context.get('status'))
#                         outbound = WarehouseCustomerShipment(
#                             contract=contract,
#                             warehouse_id=selected_warehouse, 
#                             warehouse_name = warehouse_name, 
#                             crop_id = crop.id,
#                             crop= crop_name,                      
#                             carrier_type=data.get('carrier_type'),
#                             outbound_type=data.get('outbound_type'),
#                             purchase_order_name=data.get('purchase_order_name'),
#                             purchase_order_number=data.get('purchase_order_number'),
#                             lot_number=data.get('lot_number'),
#                             gross_weight=gross_weight,
#                             net_weight=net_weight,
#                             ship_weight=ship_weight,
#                             weight_unit=data.get('amount_unit'),
#                             ship_quantity=ship_quantity,
#                             contract_weight_left=contract_weight_left,
#                             status=data.get('status'),
#                             customer_id=customer_id,                        
#                             customer_name=contract.customer_name,
                            
#                         )
#                         outbound.save()
#                         if data.get('final_payment_date') not in [None, '', ' ', 'null']:
#                             final_payment_date = data.get('final_payment_date')
#                             outbound.final_payment_date=final_payment_date  
#                         outbound.save()                           
                        
#                         carrier_id = data.get('carrier_id')
#                         if carrier_id:
#                             CarrierDetails2.objects.create(shipment=outbound, carrier_id=carrier_id)
                        
#                         files = request.FILES.getlist('files')
#                         for file in files:
#                             WarehouseCustomerShipmentDocuments.objects.create(shipment=outbound, document_file=file)

#                         all_users = CustomerUser.objects.filter(customer_id=outbound.customer_id)
                        
#                         for user in all_users :
#                             msg = f'A shipment has been sent of {outbound.net_weight}{outbound.weight_unit} under Contract ID - {outbound.contract.secret_key}'
#                             get_user = User.objects.get(username=user.contact_email)
#                             notification_reason = 'New Shipment'
#                             redirect_url = "/warehouse/list-warehouse-shipment/"
#                             save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
#                                 notification_reason=notification_reason)
#                             save_notification.save()
                            
#                         return redirect('list-warehouse-shipment')  
#                 return render(request, 'distributor/create_warehouse_outbound.html', context)
#         else:
#             return redirect('login')        
#     except Exception as e:
#         context["error_messages"] = str(e)
#         return render(request, 'distributor/create_warehouse_outbound.html', context)  


@login_required()
def create_warehouse_shipment(request):
    context = {}
    try:
        if request.user.is_authenticated:
            if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
                current_time = timezone.now()
                contracts = AdminCustomerContract.objects.filter(contract_start_date__lte=current_time,end_date__gte=current_time).values('id','secret_key','customer_id','customer_name').order_by('-id')  
                warehouses = Warehouse.objects.all().values('id', 'name')              
                context["contracts"] = contracts
                context["warehouses"] = warehouses                
              
                if request.method == "POST":
                    data = request.POST
                    selected_contract = data.get('selected_contract') 
                    selected_warehouse = data.get('selected_warehouse') 
                    outbound_type = data.get('outbound_type')
                    carrier_type = data.get('carrier_type')
                    carrier_id = data.get('carrier_id')
                    purchase_order_name = data.get('purchase_order_name')
                    purchase_order_number = data.get('purchase_order_number')
                    
                    shipment_type = data.get('shipment_type')                    
                    crop_ids = data.getlist('crop_id[]')
                    lot_numbers = data.getlist('lot_number[]')
                    gross_weights = data.getlist('gross_weight[]')
                    weights = data.getlist('weight[]')
                    amount_unit = data.get('amount_unit')
                    ship_weights = data.getlist('ship_weight[]')
                    ship_quantities = data.getlist('ship_quantity[]')
                    print(ship_quantities)
                    status = data.get('status')
                    files = request.FILES.getlist('files')
                    final_payment_date = data.get('final_payment_date')                   

                    contract = AdminCustomerContract.objects.filter(id=int(selected_contract)).first()
                    warehouse = Warehouse.objects.filter(id=int(selected_warehouse)).first()
                    
                    outbound = WarehouseCustomerShipment(
                        contract=contract,
                        warehouse_id=selected_warehouse, 
                        warehouse_name = warehouse.name,                                             
                        carrier_type=carrier_type,
                        outbound_type=outbound_type,
                        shipment_type=shipment_type,
                        purchase_order_name=purchase_order_name,
                        purchase_order_number=purchase_order_number,                                                
                        status=status,
                        customer_id=contract.customer_id,                        
                        customer_name=contract.customer_name,                        
                    )
                    outbound.save()

                    for i, crop_id in enumerate(crop_ids):
                        crop = CustomerContractCropDetails.objects.filter(id=int(crop_id)).first()
                        gross_weight = float(gross_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                        ship_weight = float(ship_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                        ship_quantity = int(ship_quantities[i]) if carrier_type == 'Truck/Trailer' else 1
                        weight = float(weights[i]) if carrier_type == 'Rail Car' else 0
                        lot_number = lot_numbers[i]
                        
                        if carrier_type == 'Truck/Trailer':
                            net_weight = gross_weight - (ship_weight * ship_quantity)
                        elif carrier_type == 'Rail Car':
                            net_weight = weight
                        
                        if crop.amount_unit == amount_unit:
                            contract_weight_left = float(crop.left_amount) - float(net_weight)
                        else:
                            if crop.amount_unit == "LBS" and amount_unit == "MT":
                                net_weight_lbs = float(net_weight) * 2204.62
                                contract_weight_left = float(crop.left_amount) - net_weight_lbs
                            elif crop.amount_unit == "MT" and amount_unit == "LBS":
                                net_weight_mt = float(net_weight) * 0.000453592
                                contract_weight_left = float(crop.left_amount) - net_weight_mt
                            else:
                                raise ValueError(f"Unsupported conversion from {crop.amount_unit} to {amount_unit}")

                        WarehouseShipmentCrops.objects.create(
                            shipment=outbound,
                            crop_id=crop_id,
                            crop=crop.crop,
                            crop_type=crop.crop_type,
                            net_weight=net_weight,
                            gross_weight=gross_weight,
                            ship_weight=ship_weight,
                            ship_quantity=ship_quantity,
                            weight_unit=amount_unit,
                            contract_weight_left=contract_weight_left,
                            lot_number=lot_number
                        )                       
                      
                    if final_payment_date not in [None, '', ' ', 'null']:                       
                        outbound.final_payment_date=final_payment_date  
                    outbound.save()                      
                    
                    carrier_id = data.get('carrier_id')
                    if carrier_id:
                        CarrierDetails2.objects.create(shipment=outbound, carrier_id=carrier_id)
                    
                    files = request.FILES.getlist('files')
                    for file in files:
                        WarehouseCustomerShipmentDocuments.objects.create(shipment=outbound, document_file=file)
                                            
                    all_users = CustomerUser.objects.filter(customer_id=outbound.customer_id)
                    
                    for user in all_users :
                        msg = f'A shipment has been sent under Contract ID - {outbound.contract.secret_key}'
                        get_user = User.objects.get(username=user.contact_email)
                        notification_reason = 'New Shipment'
                        redirect_url = "/warehouse/list-warehouse-shipment/"
                        save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
                            notification_reason=notification_reason)
                        save_notification.save()
                        
                    return redirect('list-warehouse-shipment')  
                return render(request, 'distributor/create_warehouse_shipment.html', context) 
            
            elif request.user.is_distributor: 
                current_time = timezone.now()               
                distributor_user = DistributorUser.objects.get(contact_email=request.user.email) 
                distributor = Distributor.objects.get(id=distributor_user.distributor.id)
                warehouses = distributor.warehouse.all().values('id', 'name') 
                warehouse_ids = [warehouse['id'] for warehouse in warehouses]
                customers = Customer.objects.filter(warehouse__id__in=warehouse_ids)  
                contracts = AdminCustomerContract.objects.filter(customer_id__in=list(customers.values_list('id', flat=True)),contract_start_date__lte=current_time, end_date__gte=current_time).values('id', 'secret_key', 'customer_id', 'customer_name').order_by('-id')                    
                context["contracts"] = contracts
                context["warehouses"] = warehouses

                if request.method == "POST":
                    data = request.POST
                    selected_contract = data.get('selected_contract') 
                    selected_warehouse = data.get('selected_warehouse') 
                    outbound_type = data.get('outbound_type')
                    carrier_type = data.get('carrier_type')
                    carrier_id = data.get('carrier_id')
                    purchase_order_name = data.get('purchase_order_name')
                    purchase_order_number = data.get('purchase_order_number')
                    
                    shipment_type = data.get('shipment_type')                    
                    crop_ids = data.getlist('crop_id[]')
                    lot_numbers= data.getlist('lot_number[]')
                    gross_weights = data.getlist('gross_weight[]')
                    weights = data.getlist('weight[]')
                    amount_unit = data.get('amount_unit')
                    ship_weights = data.getlist('ship_weight[]')
                    ship_quantities = data.getlist('ship_quantity[]')
                    status = data.get('status')
                    files = request.FILES.getlist('files')
                    final_payment_date = data.get('final_payment_date')

                    contract = AdminCustomerContract.objects.filter(id=int(selected_contract)).first()
                    warehouse = Warehouse.objects.filter(id=int(selected_warehouse)).first()
                    
                    outbound = WarehouseCustomerShipment(
                        contract=contract,
                        warehouse_id=selected_warehouse, 
                        warehouse_name = warehouse.name,                                             
                        carrier_type=carrier_type,
                        outbound_type=outbound_type,
                        shipment_type=shipment_type,
                        purchase_order_name=purchase_order_name,
                        purchase_order_number=purchase_order_number,                                                
                        status=status,
                        customer_id=contract.customer_id,                        
                        customer_name=contract.customer_name,
                        
                    )
                    outbound.save()

                    for i, crop_id in enumerate(crop_ids):
                        crop = CustomerContractCropDetails.objects.filter(id=int(crop_id)).first()
                        gross_weight = float(gross_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                        ship_weight = float(ship_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                        ship_quantity = int(ship_quantities[i]) if carrier_type == 'Truck/Trailer' else 1
                        weight = float(weights[i]) if carrier_type == 'Rail Car' else 0
                        lot_number= lot_numbers[i]
                        
                        if carrier_type == 'Truck/Trailer':
                            net_weight = gross_weight - (ship_weight * ship_quantity)
                        elif carrier_type == 'Rail Car':
                            net_weight = weight

                        shipment_amount_unit = amount_unit  
                        if crop.amount_unit == shipment_amount_unit:
                            contract_weight_left = float(crop.left_amount) - float(net_weight)
                        else:
                            if crop.amount_unit == "LBS" and shipment_amount_unit == "MT":
                                net_weight_lbs = float(net_weight) * 2204.62
                                contract_weight_left = float(crop.left_amount) - net_weight_lbs
                            elif crop.amount_unit == "MT" and shipment_amount_unit == "LBS":
                                net_weight_mt = float(net_weight) * 0.000453592
                                contract_weight_left = float(crop.left_amount) - net_weight_mt
                            else:
                                raise ValueError(f"Unsupported conversion from {crop.amount_unit} to {shipment_amount_unit}")

                        WarehouseShipmentCrops.objects.create(
                            shipment=outbound,
                            crop_id=crop_id,
                            crop=crop.crop,
                            crop_type=crop.crop_type,
                            net_weight=net_weight,
                            gross_weight=gross_weight,
                            ship_weight=ship_weight,
                            ship_quantity=ship_quantity,
                            weight_unit=shipment_amount_unit,
                            contract_weight_left=contract_weight_left,
                            lot_number=lot_number
                        )                       
                    
                       
                    if final_payment_date not in [None, '', ' ', 'null']:                     
                        outbound.final_payment_date=final_payment_date  
                    outbound.save()                      
                    
                    carrier_id = data.get('carrier_id')
                    if carrier_id:
                        CarrierDetails2.objects.create(shipment=outbound, carrier_id=carrier_id)
                    
                    files = request.FILES.getlist('files')
                    for file in files:
                        WarehouseCustomerShipmentDocuments.objects.create(shipment=outbound, document_file=file)
                                            
                    all_users = CustomerUser.objects.filter(customer_id=outbound.customer_id)
                    
                    for user in all_users :
                        msg = f'A shipment has been sent of under Contract ID - {outbound.contract.secret_key}'
                        get_user = User.objects.get(username=user.contact_email)
                        notification_reason = 'New Shipment'
                        redirect_url = "/warehouse/list-warehouse-shipment/"
                        save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
                            notification_reason=notification_reason)
                        save_notification.save()
                        
                    return redirect('list-warehouse-shipment')  
                return render(request, 'distributor/create_warehouse_shipment.html', context)
            
            elif request.user.is_warehouse_manager:              
                current_time = timezone.now()
                warehouse_user = WarehouseUser.objects.get(contact_email=request.user.email) 
                warehouse = warehouse_user.warehouse
                customers = Customer.objects.filter(warehouse=warehouse)  
                contracts = AdminCustomerContract.objects.filter(customer_id__in=list(customers.values_list('id', flat=True)),contract_start_date__lte=current_time, end_date__gte=current_time).values('id', 'secret_key', 'customer_id', 'customer_name').order_by('-id')            
                context["contracts"] = contracts
                context["warehouses"] = warehouse                
              
                if request.method == "POST":
                    data = request.POST
                    selected_contract = data.get('selected_contract') 
                    selected_warehouse = data.get('selected_warehouse') 
                    outbound_type = data.get('outbound_type')
                    carrier_type = data.get('carrier_type')
                    carrier_id = data.get('carrier_id')
                    purchase_order_name = data.get('purchase_order_name')
                    purchase_order_number = data.get('purchase_order_number')
                    
                    shipment_type = data.get('shipment_type')                    
                    crop_ids = data.getlist('crop_id[]')
                    lot_numbers = data.getlist('lot_number[]')
                    gross_weights = data.getlist('gross_weight[]')
                    weights = data.getlist('weight[]')
                    amount_unit = data.get('amount_unit')
                    ship_weights = data.getlist('ship_weight[]')
                    ship_quantities = data.getlist('ship_quantity[]')
                    status = data.get('status')
                    files = request.FILES.getlist('files')
                    final_payment_date = data.get('final_payment_date')

                    contract = AdminCustomerContract.objects.filter(id=int(selected_contract)).first()
                    warehouse = Warehouse.objects.filter(id=int(selected_warehouse)).first()
                    
                    outbound = WarehouseCustomerShipment(
                        contract=contract,
                        warehouse_id=selected_warehouse, 
                        warehouse_name = warehouse.name,                                             
                        carrier_type=carrier_type,
                        outbound_type=outbound_type,
                        shipment_type=shipment_type,
                        purchase_order_name=purchase_order_name,
                        purchase_order_number=purchase_order_number,                                                
                        status=status,
                        customer_id=contract.customer_id,                        
                        customer_name=contract.customer_name,
                        
                    )
                    outbound.save()

                    for i, crop_id in enumerate(crop_ids):
                        crop = CustomerContractCropDetails.objects.filter(id=int(crop_id)).first()
                        gross_weight = float(gross_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                        ship_weight = float(ship_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                        ship_quantity = int(ship_quantities[i]) if carrier_type == 'Truck/Trailer' else 1
                        weight = float(weights[i]) if carrier_type == 'Rail Car' else 0   
                        lot_number = lot_numbers[i]                     
                        
                        if carrier_type == 'Truck/Trailer':
                            net_weight = gross_weight - (ship_weight * ship_quantity)
                        elif carrier_type == 'Rail Car':
                            net_weight = weight

                        shipment_amount_unit = amount_unit                        
                        if crop.amount_unit == shipment_amount_unit:
                            contract_weight_left = float(crop.left_amount) - float(net_weight)
                        else:
                            if crop.amount_unit == "LBS" and shipment_amount_unit == "MT":
                                net_weight_lbs = float(net_weight) * 2204.62
                                contract_weight_left = float(crop.left_amount) - net_weight_lbs
                            elif crop.amount_unit == "MT" and shipment_amount_unit == "LBS":
                                net_weight_mt = float(net_weight) * 0.000453592
                                contract_weight_left = float(crop.left_amount) - net_weight_mt
                            else:
                                raise ValueError(f"Unsupported conversion from {crop.amount_unit} to {shipment_amount_unit}")

                        WarehouseShipmentCrops.objects.create(
                            shipment=outbound,
                            crop_id=crop_id,
                            crop=crop.crop,
                            crop_type=crop.crop_type,
                            net_weight=net_weight,
                            gross_weight=gross_weight,
                            ship_weight=ship_weight,
                            ship_quantity=ship_quantity,
                            weight_unit=shipment_amount_unit,
                            contract_weight_left=contract_weight_left,
                            lot_number=lot_number
                        )                       
                    
                       
                    if final_payment_date not in [None, '', ' ', 'null']:                     
                        outbound.final_payment_date=final_payment_date  
                    outbound.save()                      
                    
                    carrier_id = data.get('carrier_id')
                    if carrier_id:
                        CarrierDetails2.objects.create(shipment=outbound, carrier_id=carrier_id)
                    
                    files = request.FILES.getlist('files')
                    for file in files:
                        WarehouseCustomerShipmentDocuments.objects.create(shipment=outbound, document_file=file)
                                            
                    all_users = CustomerUser.objects.filter(customer_id=outbound.customer_id)
                    
                    for user in all_users :
                        msg = f'A shipment has been sent of under Contract ID - {outbound.contract.secret_key}'
                        get_user = User.objects.get(username=user.contact_email)
                        notification_reason = 'New Shipment'
                        redirect_url = "/warehouse/list-warehouse-shipment/"
                        save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
                            notification_reason=notification_reason)
                        save_notification.save()
                        
                    return redirect('list-warehouse-shipment')
                return render(request, 'distributor/create_warehouse_shipment.html', context)
        else:
            return redirect('login')        
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/create_warehouse_shipment.html', context)  


@login_required()
def warehouse_shipment_list(request):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            customers = Customer.objects.filter(is_active=True)
            
            context["customers"] = customers
            shipments = WarehouseCustomerShipment.objects.prefetch_related(
                    Prefetch('warehouse_shipment_crop', queryset=WarehouseShipmentCrops.objects.all())
                ).all()
            selected_customer = request.GET.get('selected_customer','All')
            
            if selected_customer != 'All':
                customer_id = int(selected_customer)
                context['selected_customer_id'] = customer_id
                
            else:  
                customer_id = None              
                context['selected_customer_id'] = None            

            if selected_customer and selected_customer != 'All':                
                shipments = shipments.filter(customer_id=int(customer_id))

            search_name = request.GET.get('search_name', '')

            if search_name and search_name is not None:
                shipments = shipments.filter(Q(warehouse_name__icontains=search_name) |
                                             Q(customer_name__icontains=search_name) |
                                             Q(warehouse_shipment_crop__crop__icontains=search_name) |
                                             Q(contract__secret_key__icontains=search_name) |
                                             Q(outbound_type__icontains=search_name) |
                                             Q(carrier_type__icontains=search_name) |
                                             Q(status__icontains=search_name) |
                                             Q(purchase_order_name__icontains=search_name) |
                                             Q(lot_number__icontains=search_name) |
                                             Q(purchase_order_number__icontains=search_name))
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
                    shipments = shipments.filter(date_pulled__range=[start_date, end_date])
                elif start_date:
                    shipments = shipments.filter(date_pulled__gte=start_date)
                elif end_date:
                    shipments = shipments.filter(date_pulled__lte=end_date)

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None          
            
            shipments = shipments.order_by('-id')
            paginator = Paginator(shipments, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'distributor/list_warehouse_outbound.html', context)
      
        elif request.user.is_distributor:
        
            user_email = request.user.email
            d = DistributorUser.objects.get(contact_email=user_email)
            distributor = Distributor.objects.get(id=d.distributor.id)
            warehouses = distributor.warehouse.all().values_list('id', flat=True)
            shipments = WarehouseCustomerShipment.objects.prefetch_related(
                Prefetch(
                    'warehouse_shipment_crop', 
                    queryset=WarehouseShipmentCrops.objects.all()
                )
            ).filter(warehouse_id__in=warehouses).order_by('-id')
            search_name = request.GET.get('search_name', '')

            if search_name and search_name is not None:
                shipments = shipments.filter(Q(warehouse_name__icontains=search_name) |
                                             Q(customer_name__icontains=search_name) |
                                             Q(warehouse_shipment_crop__crop__icontains=search_name) |
                                             Q(contract__secret_key__icontains=search_name) |
                                             Q(outbound_type__icontains=search_name) |
                                             Q(carrier_type__icontains=search_name) |
                                             Q(status__icontains=search_name) |
                                             Q(purchase_order_name__icontains=search_name) |
                                             Q(lot_number__icontains=search_name) |
                                             Q(purchase_order_number__icontains=search_name))
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
                    shipments = shipments.filter(date_pulled__range=[start_date, end_date])
                elif start_date:
                    shipments = shipments.filter(date_pulled__gte=start_date)
                elif end_date:
                    shipments = shipments.filter(date_pulled__lte=end_date)

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None    

            paginator = Paginator(shipments, 100)
            print(paginator)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            print(context)
            return render(request, 'distributor/list_warehouse_outbound.html', context)
        
        elif request.user.is_warehouse_manager:
            user_email = request.user.email
            w = WarehouseUser.objects.get(contact_email=user_email)
            warehouse_id = Warehouse.objects.get(id=w.warehouse.id).id
            shipments = WarehouseCustomerShipment.objects.prefetch_related(
                    Prefetch('warehouse_shipment_crop', queryset=WarehouseShipmentCrops.objects.all())
                ).filter(warehouse_id=warehouse_id)
            search_name = request.GET.get('search_name', '')

            if search_name and search_name is not None:
                shipments = shipments.filter(Q(warehouse_name__icontains=search_name) |
                                             Q(customer_name__icontains=search_name) |
                                             Q(warehouse_shipment_crop__crop__icontains=search_name) |
                                             Q(contract__secret_key__icontains=search_name) |
                                             Q(outbound_type__icontains=search_name) |
                                             Q(carrier_type__icontains=search_name) |
                                             Q(status__icontains=search_name) |
                                             Q(purchase_order_name__icontains=search_name) |
                                             Q(lot_number__icontains=search_name) |
                                             Q(purchase_order_number__icontains=search_name))
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
                    shipments = shipments.filter(date_pulled__range=[start_date, end_date])
                elif start_date:
                    shipments = shipments.filter(date_pulled__gte=start_date)
                elif end_date:
                    shipments = shipments.filter(date_pulled__lte=end_date)

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None    

            shipments = shipments.order_by('-id')
            paginator = Paginator(shipments, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'distributor/list_warehouse_outbound.html', context)
        
        elif request.user.is_customer:
            user_email = request.user.email
            c = CustomerUser.objects.get(contact_email=user_email)
            customer_id = Customer.objects.get(id=c.customer.id).id
            shipments = WarehouseCustomerShipment.objects.prefetch_related(
                    Prefetch('warehouse_shipment_crop', queryset=WarehouseShipmentCrops.objects.all())
                ).filter(customer_id=customer_id)
            search_name = request.GET.get('search_name', '')

            if search_name and search_name is not None:
                shipments = shipments.filter(Q(warehouse_name__icontains=search_name) |
                                             Q(customer_name__icontains=search_name) |
                                             Q(warehouse_shipment_crop__crop=search_name) |
                                             Q(contract__secret_key__icontains=search_name) |
                                             Q(outbound_type__icontains=search_name) |
                                             Q(carrier_type__icontains=search_name) |
                                             Q(status__icontains=search_name) |
                                             Q(purchase_order_name__icontains=search_name) |
                                             Q(lot_number__icontains=search_name) |
                                             Q(purchase_order_number__icontains=search_name))
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
                    shipments = shipments.filter(date_pulled__range=[start_date, end_date])
                elif start_date:
                    shipments = shipments.filter(date_pulled__gte=start_date)
                elif end_date:
                    shipments = shipments.filter(date_pulled__lte=end_date)

                context['start_date'] = start_date
                context['end_date'] = end_date
            else:
                context['start_date'] = None
                context['end_date'] = None    

            shipments = shipments.order_by('-id')
            paginator = Paginator(shipments, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)             
            context['contracts'] = report
            return render(request, 'distributor/list_warehouse_outbound.html', context)
        else:
            messages.error(request, "Not a valid request.")
            return redirect("dashboard")   
    except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/list_warehouse_outbound.html', context)
    

@login_required()
def warehouse_shipment_view(request, pk):
    context = {}
    try:
        shipment = WarehouseCustomerShipment.objects.prefetch_related(
                    Prefetch('warehouse_shipment_crop', queryset=WarehouseShipmentCrops.objects.all())
                ).filter(id=pk).first()        
        carrier_details = CarrierDetails2.objects.filter(shipment=shipment)
        shipment_date_str = shipment.date_pulled.strftime('%d %b, %Y') if shipment.date_pulled else None
        first_shipment = GrowerShipment.objects.order_by('date_time').first()
        if first_shipment:
            from_date = first_shipment.date_time.date() 
        else:
            from_date = None  
        to_date = date.today()
        datapy = {
            "shipment_id": shipment.shipment_id,
            "sender": shipment.warehouse_name,            
            "shipment_date": shipment_date_str,
            "receiver": shipment.customer_name,
            "receive_date": shipment.customer_receive_date,
            "traceability_url":  f"{request.scheme}://{request.get_host()}/tracemodule/trace_shipment/{shipment.shipment_id}/{from_date}/{to_date}/"
        }
        data = json.dumps(datapy)           
        img = qrcode.make(data)
        img_name = 'qr1_' + str(int(time.time())) + '.png'         
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)            
        file = ContentFile(buffer.read(), name=img_name)

        shipment.qr_code.save(img_name, file, save=True)
        img_name = shipment.qr_code
        context["img_name"] = img_name
        context["shipment"] = shipment
        context["documents"] = [
            {
                "id": file.id,
                "file": file.document_file,
                "name": file.document_file.name.split("/")[-1]  # Extract only the file name
            }
            for file in WarehouseCustomerShipmentDocuments.objects.filter(shipment=shipment)
        ]
        context["carriers"] = carrier_details
        logs = WarehouseShipmentLog.objects.filter(shipment=shipment).order_by('id')
        context['logs'] = logs
        lot_entries = WarehouseShipmentLotNumberTracking.objects.filter(shipment=shipment)
        context["lot_entries"] = lot_entries
        return render (request, 'distributor/view_warehouse_outbound.html', context)
    except (ValueError, AttributeError, WarehouseCustomerShipment.DoesNotExist) as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/view_warehouse_outbound.html', context)


def find_changes_for_customer_shipment(data, shipment):
    changes = []   
   
    carrier_id = data.get("carrier_id")
    if carrier_id:
        carrier = CarrierDetails2.objects.filter(shipment=shipment).first()
        if carrier and carrier.carrier_id != carrier_id:
            changes.append({"field": "Carrier ID", "old": carrier.carrier_id, "new": carrier_id})

    purchase_order_name = data.get("purchase_order_name")
    if purchase_order_name and shipment.purchase_order_name != purchase_order_name:
        changes.append({"field": "Purchase Order Name", "old": shipment.purchase_order_name, "new": purchase_order_name})

    purchase_order_number = data.get("purchase_order_number")
    if purchase_order_number and shipment.purchase_order_number != purchase_order_number:
        changes.append({"field": "Purchase Order Number", "old": shipment.purchase_order_number, "new": purchase_order_number})


    crop_ids = data.getlist('crop_id[]')
    lot_numbers = data.getlist('lot_number[]')
    gross_weights = data.getlist('gross_weight[]')
    weights = data.getlist('weight[]')
    ship_weights = data.getlist('ship_weight[]')
    ship_quantities = data.getlist('ship_quantity[]')
    id_crops = data.getlist("id_crop[]")    

    for index, crop_id in enumerate(id_crops):
        print(index)
        print(crop_ids[index])
        try:
            crop_instance = WarehouseShipmentCrops.objects.get(pk=crop_id)

            crop = int(crop_ids[index]) if crop_ids[index] else None
            if crop is not None and int(crop_instance.crop_id) != crop:
                crop_ = CustomerContractCropDetails.objects.filter(id=int(crop)).first().crop
                changes.append({
                    "field": f"Crop (Crop ID: {crop_id})",
                    "old": crop_instance.crop,
                    "new": crop_
                })
            
            lot_number = lot_numbers[index] if lot_numbers[index] else None
            if lot_number is not None and crop_instance.lot_number != lot_number:
                changes.append({
                    "field": f"Lot Number (Crop ID: {crop_id})",
                    "old": crop_instance.lot_number,
                    "new": lot_number
                })

            gross_weight = float(gross_weights[index]) if gross_weights[index] else None
            if gross_weight is not None and crop_instance.gross_weight != gross_weight:
                changes.append({
                    "field": f"Gross Weight (Crop ID: {crop_id})",
                    "old": crop_instance.gross_weight,
                    "new": gross_weight
                })

            net_weight = float(weights[index]) if weights[index] else None
            if net_weight is not None and crop_instance.net_weight != net_weight:
                changes.append({
                    "field": f"Net Weight (Crop ID: {crop_id})",
                    "old": crop_instance.net_weight,
                    "new": net_weight
                })

            ship_weight = float(ship_weights[index]) if ship_weights[index] else None
            if ship_weight is not None and crop_instance.ship_weight != ship_weight:
                changes.append({
                    "field": f"Ship Weight (Crop ID: {crop_id})",
                    "old": crop_instance.ship_weight,
                    "new": ship_weight
                })

            ship_quantity = int(ship_quantities[index]) if ship_quantities[index] else None
            if ship_quantity is not None and crop_instance.ship_quantity != ship_quantity:
                changes.append({
                    "field": f"Ship Quantity (Crop ID: {crop_id})",
                    "old": crop_instance.ship_quantity,
                    "new": ship_quantity
                })

        except WarehouseShipmentCrops.DoesNotExist:
            changes.append({"field": f"Crop ID {crop_id}", "old": "Not Found", "new": "New Crop Added"})
    
    status = data.get("status")
    if status and shipment.status != status:
        changes.append({"field": "Status", "old": shipment.status, "new": status})
    
    border_receive_date = data.get("border_receive_date")
    if border_receive_date:
        border_receive_date_parsed = datetime.strptime(border_receive_date, '%Y-%m-%d').date()
        stored_border_receive_date = shipment.border_receive_date.date() if shipment.border_receive_date else None
        if stored_border_receive_date != border_receive_date_parsed:
            changes.append({"field": "Border Receive Date", "old": str(stored_border_receive_date), "new": str(border_receive_date_parsed)})
   
    border_leaving_date = data.get("border_leaving_date")
    if border_leaving_date:
        border_leaving_date_parsed = datetime.strptime(border_leaving_date, '%Y-%m-%d').date()
        stored_border_leaving_date = shipment.border_leaving_date.date() if shipment.border_leaving_date else None
        if stored_border_leaving_date != border_leaving_date_parsed:
            changes.append({"field": "Border Leaving Date", "old": str(stored_border_leaving_date), "new": str(border_leaving_date_parsed)})
    
    final_receive_date = data.get("final_receive_date")
    if final_receive_date:
        final_receive_date_parsed = datetime.strptime(final_receive_date, '%Y-%m-%d').date()
        stored_receive_date = shipment.customer_receive_date.date() if shipment.customer_receive_date else None
        if stored_receive_date != final_receive_date_parsed:
            changes.append({"field": "Customer Receive Date", "old": str(stored_receive_date), "new": str(final_receive_date_parsed)})
   
    final_leaving_date = data.get("final_leaving_date")
    if final_leaving_date:
        final_leaving_date_parsed = datetime.strptime(final_leaving_date, '%Y-%m-%d').date()
        stored_leaving_date = shipment.customer_leaving_date.date() if shipment.customer_leaving_date else None
        if stored_leaving_date != final_leaving_date_parsed:
            changes.append({"field": "Customer Leaving Date", "old": str(stored_leaving_date), "new": str(final_leaving_date_parsed)})
    
    border_receive_date2 = data.get("border_receive_date2")
    if border_receive_date2:
        border_receive_date2_parsed = datetime.strptime(border_receive_date2, '%Y-%m-%d').date()
        stored_border_receive_date2 = shipment.border_back_receive_date.date() if shipment.border_back_receive_date else None
        if stored_border_receive_date2 != border_receive_date2_parsed:
            changes.append({"field": "Border Receive Date Back", "old": str(stored_border_receive_date2), "new": str(border_receive_date2_parsed)})
    
    border_leaving_date2 = data.get("border_leaving_date2")
    if border_leaving_date2:
        border_leaving_date2_parsed = datetime.strptime(border_leaving_date2, '%Y-%m-%d').date()
        stored_border_leaving_date2 = shipment.border_back_leaving_date.date() if shipment.border_back_leaving_date else None
        if stored_border_leaving_date2 != border_leaving_date2_parsed:
            changes.append({"field": "Border Leaving Date Back", "old": str(stored_border_leaving_date2), "new": str(border_leaving_date2_parsed)})
   
    processor_receive_date = data.get("processor_receive_date")
    if processor_receive_date:
        processor_receive_date_parsed = datetime.strptime(processor_receive_date, '%Y-%m-%d').date()
        stored_processor_receive_date = shipment.warehouse_receive_date.date() if shipment.warehouse_receive_date else None
        if stored_processor_receive_date != processor_receive_date_parsed:
            changes.append({"field": "Warehouse Receive Date", "old": str(stored_processor_receive_date), "new": str(processor_receive_date_parsed)})

    final_payment_date = data.get("final_payment_date")
    if final_payment_date:
        final_payment_date_parsed = datetime.strptime(final_payment_date, '%Y-%m-%d').date()
        stored_final_payment_date = shipment.final_payment_date.date() if shipment.final_payment_date else None
        if stored_final_payment_date != final_payment_date_parsed:
            changes.append({"field": "Final Payment Date", "old": str(stored_final_payment_date), "new": str(final_payment_date_parsed)})
    
    if data.get("files"):
        existing_files = [
            file.document_file.name.split("/")[-1]
            for file in WarehouseCustomerShipmentDocuments.objects.filter(shipment=shipment)
        ]
        uploaded_files = [file["name"] for file in data.get("files")]
        if set(existing_files) != set(uploaded_files):
            changes.append({"field": "Upload File", "old": existing_files, "new": uploaded_files})

    return changes


###############################Single Crop##############################
# @login_required()
# def edit_warehouse_shipment(request, pk):
#     context = {}
#     # try:
#     if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_distributor or request.user.is_warehouse_manager:
#         check_shipment = WarehouseCustomerShipment.objects.filter(id=pk)
#         if not check_shipment.exists():
#             # Handle the case where the shipment does not exist
#             context["error_messages"] = "Shipment not found."
#             return render(request, 'distributor/edit_warehouse_outbound.html', context)
#         print(check_shipment)
#         shipment = check_shipment.first()
        
#         carrier = CarrierDetails2.objects.filter(shipment=shipment).first()
#         if carrier:
#             context['carrier_id'] = carrier.carrier_id
#         context["files"] = [
#             {
#                 "id": file.id,
#                 "name": file.document_file.name.split("/")[-1]  # Extract only the file name
#             }
#             for file in WarehouseCustomerShipmentDocuments.objects.filter(shipment=shipment)
#         ]
#         context["shipment"] = shipment
        
#         selected_contract = shipment.contract               
#         warehouse_id = int(shipment.warehouse_id)                
#         sender_list = Warehouse.objects.all().values('id','name')
#         selected_crop = int(shipment.crop_id) if shipment.crop_id else None
#         crops = CustomerContractCropDetails.objects.filter(contract=shipment.contract)
#         additional_lots = WarehouseShipmentLotNumberTracking.objects.filter(shipment=shipment)

#         context.update({           
#             "contract":selected_contract,                        
#             "selected_warehouse_id": warehouse_id,
#             'destination_list':sender_list,
#             'selected_crop':selected_crop,
#             'crops':crops,
#             "additional_lots":additional_lots
                   
#         })
        
#         if request.method == "POST":
#             data = request.POST            
#             button_value = request.POST.getlist('remove_files')                
#             if button_value:
#                 for file_id in button_value:
#                     try:
#                         file_obj = WarehouseCustomerShipmentDocuments.objects.get(id=file_id)
#                         file_obj.delete()
#                     except WarehouseCustomerShipmentDocuments.DoesNotExist:
#                         pass          
            
#             context.update({                    
#                 "carrier_type": data.get('carrier_type'),                    
#                 "outbound_type": data.get('outbound_type'),
#                 "purchase_order_name":data.get('purchase_order_name'),
#                 "purchase_order_number": data.get('purchase_order_number'),
#                 "lot_number": data.get('lot_number'),                
#                 "weight":data.get('weight'),
#                 "gross_weight":data.get('gross_weight'),
#                 "ship_weight":data.get('ship_weight'),
#                 "ship_quantity":data.get('ship_quantity'),
#                 "status":data.get('status'),
#                 "amount_unit":data.get('amount_unit') ,   
#                 "final_receive_date": data.get('final_receive_date'),
#                 "border_receive_date" : data.get('border_receive_date'),
#                 "border_leaving_date": data.get('border_leaving_date'),
#                 "final_leaving_date" : data.get('final_leaving_date'),
#                 "border_receive_date2": data.get('border_receive_date2'),
#                 "border_leaving_date2" : data.get('border_leaving_date2'),
#                 "processor_receive_date": data.get('processor_receive_date'),
#                 'selected_crop':data.get('crop_id'), 
#                 "final_payment_date":data.get("final_payment_date")           
                
#             })                 
#             selected_crop = data.get('crop_id')
#             if data.get('carrier_type') == 'Truck/Trailer':
#                 if data.get('gross_weight') not in [None, 'null', ' ', ''] and data.get('ship_weight') not in [None, 'null', ' ', ''] and data.get('ship_quantity') not in [None, 'null', ' ', '']:
#                     ship_quantity = int(data.get('ship_quantity'))
#                     gross_weight = float(data.get('gross_weight'))
#                     ship_weight = float(data.get('ship_weight'))                                    
#                     net_weight = gross_weight - (ship_weight * ship_quantity)
#                 else:
#                     context["error_messages"] = "Please provide Gross weight, Ship weight and Ship quantity."
#                     return render(request, 'distributor/edit_warehouse_outbound.html', context)
                
#             elif data.get('carrier_type') == 'Rail Car':                
#                 gross_weight = 0
#                 ship_quantity = 1
#                 ship_weight = 0
#                 if data.get('weight') not in [None, 'null', ' ', '']:
#                     net_weight = float(data.get('weight'))
#                 else:
#                     context["error_messages"] = "Please provide Weight."
#                     return render(request, 'distributor/edit_warehouse_outbound.html', context)
            
#             crop = CustomerContractCropDetails.objects.filter(id=int(selected_crop), contract=shipment.contract).first()
#             crop_name = crop.crop
            
#             if crop.amount_unit == data.get('amount_unit'):
#                 contract_weight_left = float(crop.left_amount) - float(net_weight)
#             else:
#                 if crop.amount_unit == "LBS" and data.get('amount_unit') == "MT":
#                     net_weight_lbs = float(net_weight) * 2204.62
#                     contract_weight_left = float(crop.left_amount) - net_weight_lbs 
#                 else:
#                     net_weight_mt = float(net_weight) * 0.000453592
#                     contract_weight_left = float(crop.left_amount) - net_weight_mt
#             changes = find_changes_for_customer_shipment(context, shipment)
#             shipment.contract=shipment.contract                
#             shipment.carrier_type=data.get('carrier_type')
#             shipment.outbound_type=data.get('outbound_type')
#             shipment.crop_id= crop.id
#             shipment.crop = crop_name
#             shipment.purchase_order_name=data.get('purchase_order_name')
#             shipment.purchase_order_number=data.get('purchase_order_number')
#             shipment.lot_number=data.get('lot_number')
#             shipment.gross_weight=gross_weight
#             shipment.net_weight=net_weight
#             shipment.weight_unit=data.get('amount_unit')
#             shipment.ship_quantity=ship_quantity
#             shipment.ship_weight=ship_weight
#             shipment.contract_weight_left=contract_weight_left
#             shipment.status= data.get('status')
#             shipment.customer_id=shipment.contract.customer_id
#             shipment.warehouse_id=warehouse_id
#             shipment.customer_name=shipment.customer_name
#             shipment.warehouse_name=shipment.warehouse_name
                                                                    
#             shipment.save()
#             if data.get('border_receive_date') not in [None, '', ' ', 'null']:
#                 border_receive_date = data.get('border_receive_date')
#                 shipment.border_receive_date= border_receive_date
#             if data.get('border_leaving_date') not in [None, '', ' ', 'null']:
#                 border_leaving_date = data.get('border_leaving_date')
#                 shipment.border_leaving_date=border_leaving_date
#             if data.get('final_receive_date') not in [None, '', ' ', 'null']:
#                 final_receive_date = data.get('final_receive_date')
#                 shipment.customer_receive_date=final_receive_date
#             if data.get('final_leaving_date') not in [None, '', ' ', 'null']:
#                 final_leaving_date = data.get('final_leaving_date')
#                 shipment.customer_leaving_date=final_leaving_date
#             if data.get('border_receive_date2') not in [None, '', ' ', 'null']:
#                 border_receive_date2 = data.get('border_receive_date2')
#                 shipment.border_back_receive_date=border_receive_date2
#             if data.get('border_leaving_date2') not in [None, '', ' ', 'null']:
#                 border_leaving_date2 = data.get('border_leaving_date2')                    
#                 shipment.border_back_leaving_date= border_leaving_date2
#             if data.get('processor_receive_date') not in [None, '', ' ', 'null']:
#                 processor_receive_date = data.get('processor_receive_date')
#                 shipment.warehouse_receive_date=processor_receive_date

#             if data.get('final_payment_date') not in [None, '', ' ', 'null']:
#                 final_payment_date = data.get('final_payment_date')
#                 shipment.final_payment_date=final_payment_date              
            
#             shipment.save()           

#             carrier_id = data.get('carrier_id')
#             if carrier_id:
#                 # Get or create carrier details
#                 carrier_details, created = CarrierDetails2.objects.update_or_create(
#                     shipment=shipment,
#                     defaults={'carrier_id': carrier_id}
#                 )
#             else:
#                 # Ensure that carrier details are not deleted if no carrier_id is provided
#                 CarrierDetails2.objects.filter(shipment=shipment).delete()
            
#             files = request.FILES.getlist('files')
#             for file in files:
#                 WarehouseCustomerShipmentDocuments.objects.create(shipment=shipment, document_file=file)  

#             lot_numbers = request.POST.getlist('lot_number[]')
#             addresses = request.POST.getlist('address[]')
#             descriptions = request.POST.getlist('description[]')
            
#             existing_lot_entries = list(
#                 WarehouseShipmentLotNumberTracking.objects.filter(shipment=shipment)
#                 .values('additional_lot_number', 'address', 'description')
#             )
#             if existing_lot_entries:                
#                 old_value = existing_lot_entries[-1]['additional_lot_number']
#             else:
#                 old_value = shipment.lot_number

#             WarehouseShipmentLotNumberTracking.objects.filter(shipment=shipment).delete()                   

#             for lot_number, address, description in zip(lot_numbers, addresses, descriptions):
#                 additional_lot = WarehouseShipmentLotNumberTracking(
#                     shipment=shipment,
#                     additional_lot_number=lot_number,
#                     address=address,
#                     description=description
#                 )
#                 additional_lot.save()

#                 if {'additional_lot_number': lot_number, 'address': address, 'description': description} not in existing_lot_entries:
#                     changes.append({
#                         "field": "Lot Number",
#                         "old": old_value,
#                         "new":lot_number
                            
#                     })                             
#             descriptions = request.POST.getlist('description')
            
#             for  description in  descriptions:
#                 if  description:
                    
#                     WarehouseShipmentLog.objects.create(
#                         shipment=shipment,                           
#                         description=description,
#                         changes = {'changes':changes},
#                         updated_by = request.user
#                     )
#                 else:
#                     context["error_messages"] = f'PLease give description'
#                     return render(request, 'distributor/edit_warehouse_outbound.html', context)
#             return redirect('warehouse-shipment-view', pk=pk)
            
#         return render(request, 'distributor/edit_warehouse_outbound.html', context)


@login_required()
def edit_warehouse_shipment(request, pk):
    context = {}
    # try:
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or request.user.is_distributor or request.user.is_warehouse_manager:
        check_shipment = WarehouseCustomerShipment.objects.filter(id=pk)        
        shipment = check_shipment.first()        
        carrier = CarrierDetails2.objects.filter(shipment=shipment).first()        
        context['carrier_id'] = carrier.carrier_id
        context["files"] = [
            {
                "id": file.id,
                "name": file.document_file.name.split("/")[-1]
            }
            for file in WarehouseCustomerShipmentDocuments.objects.filter(shipment=shipment)
        ]
        context["shipment"] = shipment                   
                       
        sender_list = Warehouse.objects.all().values('id','name')
        
        crops = WarehouseShipmentCrops.objects.filter(shipment=shipment)
        additional_lots = WarehouseShipmentLotNumberTracking.objects.filter(shipment=shipment)
        warehouse = Warehouse.objects.filter(id=int(shipment.warehouse_id)).first()

        context.update({           
            "contract":shipment.contract,                        
            "selected_warehouse_id": int(shipment.warehouse_id),
            'destination_list':sender_list,            
            'crops':crops,
            "additional_lots":additional_lots                   
        })
        
        if request.method == "POST":
            data = request.POST  
            outbound_type = data.get('outbound_type')
            carrier_type = data.get('carrier_type')
            carrier_id = data.get('carrier_id')
            purchase_order_name = data.get('purchase_order_name')
            purchase_order_number = data.get('purchase_order_number')
            
            amount_unit = data.get('amount_unit')

            shipment_type = data.get('shipment_type')                    
            crop_ids = data.getlist('crop_id[]')
            lot_numbers = data.getlist('lot_number[]')
           
            gross_weights = data.getlist('gross_weight[]')
            weights = data.getlist('weight[]')            
            ship_weights = data.getlist('ship_weight[]')
            ship_quantities = data.getlist('ship_quantity[]') 
            delete_flags = data.getlist("delete_flag[]") 
            id_crops = data.getlist("id_crop[]")

            files = request.FILES.getlist('files')
            button_value = data.getlist('remove_files') 
            final_payment_date = data.get('final_payment_date')       
            status = data.get('status')
            border_receive_date = data.get('border_receive_date')
            border_leaving_date = data.get('border_leaving_date') 
            final_receive_date = data.get('final_receive_date')
            final_leaving_date = data.get('final_leaving_date')
            border_receive_date2 = data.get('border_receive_date2')  
            border_leaving_date2 = data.get('border_leaving_date2') 
            processor_receive_date = data.get('processor_receive_date')            

            if button_value:
                for file_id in button_value:
                    try:
                        file_obj = WarehouseCustomerShipmentDocuments.objects.get(id=file_id)
                        file_obj.delete()
                    except WarehouseCustomerShipmentDocuments.DoesNotExist:
                        pass                
            
            changes = find_changes_for_customer_shipment(data, shipment)               
            shipment.carrier_type=carrier_type
            shipment.outbound_type=outbound_type            
            shipment.purchase_order_name=purchase_order_name
            shipment.purchase_order_number=purchase_order_number                       
            shipment.status=status   
            shipment.shipment_type=shipment_type                                                                
            shipment.save()

            with transaction.atomic():
                for i, id_crop in enumerate(id_crops):
                    if id_crop.isdigit() and delete_flags[i] == "1":
                        try:
                            WarehouseShipmentCrops.objects.get(id=int(id_crop)).delete()
                            print(f"Deleted crop with id {id_crop}")
                        except WarehouseShipmentCrops.DoesNotExist:
                            print(f"Crop with id {id_crop} not found.")
                    else:
                        print(f"Skipping crop with id {id_crop}, not marked for deletion.")

                for i, crop_id in enumerate(crop_ids):
                    crop = CustomerContractCropDetails.objects.filter(id=int(crop_id)).first()
                    gross_weight = float(gross_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                    ship_weight = float(ship_weights[i]) if carrier_type == 'Truck/Trailer' else 0
                    ship_quantity = int(ship_quantities[i]) if carrier_type == 'Truck/Trailer' else 1
                    weight = float(weights[i]) if carrier_type == 'Rail Car' else 0
                    lot_number = lot_numbers[i]
                    
                    if carrier_type == 'Truck/Trailer':
                        net_weight = gross_weight - (ship_weight * ship_quantity)
                    elif carrier_type == 'Rail Car':
                        net_weight = weight
                    
                    if crop.amount_unit == amount_unit:
                        contract_weight_left = float(crop.left_amount) - float(net_weight)
                    else:
                        if crop.amount_unit == "LBS" and amount_unit == "MT":
                            net_weight_lbs = float(net_weight) * 2204.62
                            contract_weight_left = float(crop.left_amount) - net_weight_lbs
                        elif crop.amount_unit == "MT" and amount_unit == "LBS":
                            net_weight_mt = float(net_weight) * 0.000453592
                            contract_weight_left = float(crop.left_amount) - net_weight_mt
                        else:
                            raise ValueError(f"Unsupported conversion from {crop.amount_unit} to {amount_unit}")
                        
                    id_crop = id_crops[i] if i < len(id_crops) else None
                    if id_crop and id_crop.isdigit():
                        try:
                            crop_detail = WarehouseShipmentCrops.objects.get(id=int(id_crop))                                    
                            crop_detail.crop_id = crop_id
                            crop.crop = crop.crop
                            crop.crop_type = crop.crop_type
                            crop_detail.net_weight = net_weight
                            crop_detail.weight_unit = amount_unit
                            crop_detail.gross_weight = gross_weight
                            crop_detail.ship_quantity = ship_quantity
                            crop_detail.ship_weight = ship_weight
                            crop_detail.contract_weight_left = contract_weight_left
                            crop_detail.lot_number=lot_number
                            crop_detail.save()                              
                            
                        except WarehouseShipmentCrops.DoesNotExist:
                            print(f"Crop with id {id_crop} not found.")
                    else:
                        WarehouseShipmentCrops.objects.create(
                            shipment=shipment,
                            crop_id=crop_id,
                            crop=crop.crop,
                            crop_type=crop.crop_type,
                            net_weight=net_weight,
                            gross_weight=gross_weight,
                            ship_weight=ship_weight,
                            ship_quantity=ship_quantity,
                            weight_unit=amount_unit,
                            contract_weight_left=contract_weight_left,
                            lot_number=lot_number
                        )                      

            if border_receive_date not in [None, '', ' ', 'null']:                
                shipment.border_receive_date= border_receive_date

            if border_leaving_date not in [None, '', ' ', 'null']:               
                shipment.border_leaving_date=border_leaving_date

            if final_receive_date not in [None, '', ' ', 'null']:                
                shipment.customer_receive_date=final_receive_date

            if final_leaving_date not in [None, '', ' ', 'null']:               
                shipment.customer_leaving_date=final_leaving_date

            if border_receive_date2 not in [None, '', ' ', 'null']:               
                shipment.border_back_receive_date=border_receive_date2

            if border_leaving_date2 not in [None, '', ' ', 'null']:                                    
                shipment.border_back_leaving_date= border_leaving_date2

            if processor_receive_date not in [None, '', ' ', 'null']:                
                shipment.warehouse_receive_date=processor_receive_date

            if final_payment_date not in [None, '', ' ', 'null']:                
                shipment.final_payment_date=final_payment_date              
            
            shipment.save()           

            carrier_id = data.get('carrier_id')
            if carrier_id:      
                carrier_details, created = CarrierDetails2.objects.update_or_create(
                    shipment=shipment,
                    defaults={'carrier_id': carrier_id}
                )
            else:
                CarrierDetails2.objects.filter(shipment=shipment).delete()
            
            files = request.FILES.getlist('files')
            for file in files:
                WarehouseCustomerShipmentDocuments.objects.create(shipment=shipment, document_file=file)  

            crops = request.POST.getlist('crop[]')
            additional_lot_numbers = request.POST.getlist('additional_lot_number[]')
            addresses = request.POST.getlist('address[]')
            descriptions = request.POST.getlist('description[]')
            
            existing_lot_entries = WarehouseShipmentLotNumberTracking.objects.filter(shipment=shipment).select_related('crop')

            existing_lot_mapping = {
                entry.crop.id: {
                    "additional_lot_number": entry.additional_lot_number,
                    "address": entry.address
                } 
                for entry in existing_lot_entries if entry.crop
            }

            WarehouseShipmentLotNumberTracking.objects.filter(shipment=shipment).delete()

            for crop_id, lot_number, address, description in zip(crops, additional_lot_numbers, addresses, descriptions):
                
                crop = WarehouseShipmentCrops.objects.filter(id=int(crop_id)).first()
                if not crop:
                    continue  

                old_lot_number = existing_lot_mapping.get(crop.id, {}).get("additional_lot_number", crop.lot_number)
                old_address = existing_lot_mapping.get(crop.id, {}).get("address", warehouse.location)

                new_tracking_entry = WarehouseShipmentLotNumberTracking(
                    shipment=shipment,
                    crop=crop,
                    additional_lot_number=lot_number,
                    address=address,
                    description=description
                )
                new_tracking_entry.save()

                if lot_number != old_lot_number:
                    changes.append({
                        "field": f"Lot Number of {crop}",
                        "old": old_lot_number,
                        "new": lot_number
                    })

                if address != old_address:
                    changes.append({
                        "field": "Address",
                        "old": old_address,
                        "new": address
                    })
                                                   
            descriptions = request.POST.getlist('description')
            
            for  description in  descriptions:
                if  description:
                    
                    WarehouseShipmentLog.objects.create(
                        shipment=shipment,                           
                        description=description,
                        changes = {'changes':changes},
                        updated_by = request.user
                    )
                else:
                    context["error_messages"] = f'PLease give description'
                    return render(request, 'distributor/edit_warehouse_shipment.html', context)
            return redirect('warehouse-shipment-view', pk=pk)
            
        return render(request, 'distributor/edit_warehouse_shipment.html', context)


###########################################QuickBooks Included#############################
# @login_required()
# def delete_warehouse_shipment(request, pk):
#     context = {}
#     try:
#         if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
#             try:
#                 from apps.quickbooks_integration.models import QuickBooksToken
#                 from apps.quickbooks_integration.views import refresh_quickbooks_token, get_invoice_data, delete_invoice
#                 token_instance = QuickBooksToken.objects.first()                                    
#                 refresh_token = token_instance.refresh_token
#                 success_url = reverse('delete-warehouse-shipment', kwargs={'pk': pk})
#                 next_url = f"{success_url}"
#                 redirect_url = f"{reverse('quickbooks_login')}?{urlencode({'next': next_url})}"
#                 if token_instance.is_token_expired():
#                     print("Token expired, refreshing...")
#                     new_access_token = refresh_quickbooks_token(refresh_token)
#                     if not new_access_token:
#                         return redirect(redirect_url)
#                     token_instance.access_token = new_access_token
#                     token_instance.expires_at = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
#                     token_instance.save()
#             except QuickBooksToken.DoesNotExist:
#                 return redirect(redirect_url)
#             check_shipment = WarehouseCustomerShipment.objects.filter(id=pk)            
#             shipment = check_shipment.first()  
#             print(shipment)    
            
#             invoice = Invoice.objects.filter(warehouse_shipment=shipment).first()
#             if request.method == "POST":
#                 if invoice:
#                     invoice_id = invoice.quickbooks_id
#                     invoice_details = get_invoice_data(invoice_id)
#                     sync_token = invoice_details.get('Invoice', {}).get('SyncToken', '')
#                     invoice_data = {
#                         "SyncToken": str(sync_token), 
#                         "Id": str(invoice_id)
#                     }
#                     deleted_invoice = delete_invoice(token_instance.realm_id, token_instance.access_token, invoice_data)
#                     if deleted_invoice:
#                         print("Invoice deleted successfully and synced with quickbooks")
#                     else:
#                         print("Failed to delete invoice from quickbooks.")
#                     invoice.delete()
#                 shipment.delete()
#                 return redirect('list-warehouse-shipment')
#             return render(request, 'distributor/list_warehouse_outbound.html', context)
                
#     except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
#         context["error_messages"] = str(e)
#         return render(request, 'distributor/list_warehouse_outbound.html', context)


@login_required()
def delete_warehouse_shipment(request, pk):
    context = {}
    try:
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():           
            check_shipment = WarehouseCustomerShipment.objects.filter(id=pk)            
            shipment = check_shipment.first()  
            print(shipment)    
            
            invoice = Invoice.objects.filter(warehouse_shipment=shipment).first()
            if request.method == "POST":
                if invoice:                   
                    invoice.delete()
                shipment.delete()
                return redirect('list-warehouse-shipment')
            return render(request, 'distributor/list_warehouse_outbound.html', context)
                
    except (ValueError, AttributeError, WarehouseCustomerShipment.DoesNotExist) as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/list_warehouse_outbound.html', context)


@login_required
def warehouse_shipment_current_location_track(request, pk):
    context = {}
    try:
        check_shipment = WarehouseCustomerShipment.objects.filter(id=pk)
        shipment = check_shipment.first()
        first_shipment = GrowerShipment.objects.order_by('date_time').first()
        if first_shipment:
            from_date = first_shipment.date_time.date() 
        else:
            from_date = None  
        to_date = date.today()
        warehouse = Warehouse.objects.filter(id=int(shipment.warehouse_id)).first()
        customer = Customer.objects.filter(id=int(shipment.customer_id)).first()        
        origin_lat = float(warehouse.latitude)  
        origin_long = float(warehouse.longitude)  
        destination_lat = float(customer.latitude)  
        destination_long = float(customer.longitude)  
        shipment_status = shipment.status
        additional_lat_long = []
        current_location = None
        check_lot_entries = list(WarehouseShipmentLotNumberTracking.objects.filter(shipment=shipment).values_list("address", flat=True))
        if check_lot_entries:
            for entry in check_lot_entries:
                print(entry)
                additional_lat, additional_long = get_lat_lng(entry, settings.MAP_API_KEY)
                if additional_lat and additional_long:                    
                    additional_lat_long.append({"lat":additional_lat, "lng":additional_long})
                         
        if check_lot_entries and shipment_status != "Received":
            current_location = additional_lat_long[-1]
        elif check_lot_entries and shipment_status == "Received":
            current_location = {"lat": destination_lat, "lng": destination_long}
        elif not check_lot_entries and shipment_status == "Received":
            current_location = {"lat": destination_lat, "lng": destination_long}
        elif not check_lot_entries and shipment_status != "Received":
            current_location = {"lat": origin_lat, "lng": origin_long}

        context = {
            "origin": {"lat": origin_lat, "lng": origin_long},
            "destination": {"lat": destination_lat, "lng": destination_long},
            "waypoints": additional_lat_long,
            "shipment_status": shipment_status,
            "current_location": current_location,
            "source":warehouse.name,
            "destination_name": customer.name,
            "shipment_id":shipment.shipment_id,
            "contract_id":shipment.contract.secret_key,
            "from_date": from_date,
            "to_date": to_date

        }

        print(context)

        return render(request, "distributor/warehouse_shipment_location_tracker.html", context)        
    except (ValueError, AttributeError, WarehouseCustomerShipment.DoesNotExist) as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/list_warehouse_outbound.html', context)


###########################################QuickBooks Included#############################
# @login_required
# def generate_invoice(request, pk, type):
#     if not (
#         request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 
#         'SuperUser' in request.user.get_role() or request.user.is_distributor or 
#         request.user.is_warehouse_manager
#     ):
#         return redirect('dashboard')
    
#     invoice_url = reverse('generate_invoice', kwargs={'pk': pk, 'type': type})
#     next_url = f"{invoice_url}"
#     redirect_url = f"{reverse('quickbooks_login')}?{urlencode({'next': next_url})}"
    
#     token_instance = QuickBooksToken.objects.first()
#     if token_instance.is_token_expired():
#         new_access_token = refresh_quickbooks_token(token_instance.refresh_token)
#         if not new_access_token:
#             return redirect(redirect_url)
#         token_instance.access_token = new_access_token
#         token_instance.expires_at = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
#         token_instance.save()    
   
#     if type == 'warehouse':
#         shipment = WarehouseCustomerShipment.objects.filter(id=pk).first()
#         crop = CustomerContractCropDetails.objects.filter(id=shipment.crop_id).first()
#     else:
#         shipment = ProcessorWarehouseShipment.objects.filter(id=pk).first()
#         crop = CropDetails.objects.filter(id=shipment.crop_id).first()
    
#     try:       
#         shipment.invoice_approval = True
#         shipment.approval_time = timezone.now()
#         shipment.save()

#         customer = Customer.objects.filter(id=shipment.customer_id).first()
#         customer_user = CustomerUser.objects.filter(customer=customer).first()
#         due_date = shipment.final_payment_date if shipment.final_payment_date else (shipment.approval_time + timedelta(days=int(customer.credit_terms)))
        
#         # Create Invoice
#         item_amount = Decimal(shipment.net_weight) * crop.per_unit_rate
#         invoice = Invoice(
#             warehouse_shipment=shipment if type == 'warehouse' else None,
#             processor_shipment=shipment if type != 'warehouse' else None,
#             shipment_invoice_id=shipment.invoice_id,
#             due_date=due_date,
#             customer=customer,
#             currency='USD',
#             item_amount=item_amount
#         )
        
#         # Tax handling
#         if customer.is_tax_payable:
#             tax_percentage = Decimal(customer.tax_percentage)
#             tax_amount = (tax_percentage / 100) * invoice.item_amount
#             invoice.total_amount = invoice.item_amount + tax_amount
#             invoice.tax_amount = tax_amount
#         else:
#             invoice.total_amount = invoice.item_amount
        
#         invoice.save()       

#         # Prepare QuickBooks Invoice Data
#         item = ShipmentItem.objects.filter(
#             item_name=crop.crop, item_type=crop.crop_type, 
#             per_unit_price=crop.per_unit_rate
#         ).first()        
#         total_tax = float(invoice.tax_amount if customer.is_tax_payable else 0)
#         customer_details = get_customer_data(customer.quickbooks_id)
#         tax_code_value = "TAX" if customer.is_tax_payable else "NON"
#         tax_code_id = customer_details.get('Customer', {}).get('DefaultTaxCodeRef', {}).get('value', '')

#         invoice_data = {
#             "CustomerRef": {"value": str(customer.quickbooks_id)},
#             "CurrencyRef": {"value": "USD"},
#             "Line": [{
#                 "DetailType": "SalesItemLineDetail",
#                 "Amount": float(invoice.item_amount),
#                 "SalesItemLineDetail": {
#                     "ItemRef": {"value": str(item.quickbooks_id)},
#                     "Qty": float(shipment.net_weight),
#                     "UnitPrice": float(item.per_unit_price),
#                     "TaxCodeRef": {"value": tax_code_value}
#                 },
#                 "Description": item.description or ""
#             }],
#             "TxnTaxDetail": {
#                 "TotalTax": float(total_tax)
#                 },
#             "TotalAmt": float(invoice.total_amount),
#             "DocNumber": invoice.shipment_invoice_id,
#             "BillEmail": {"Address": customer_user.contact_email},
#             "ShipAddr": {
#                 "Lat": customer.latitude, "Long": customer.longitude,
#                 "CountrySubDivisionCode": customer.location
#             },
#             "TxnDate": datetime.now().strftime('%Y-%m-%d')
#         }
#         if customer.is_tax_payable:
#             tax_rates = get_tax_rates(token_instance.realm_id,token_instance.access_token)
#             rate_id = None
#             for rate in tax_rates:
#                 custom_tax_name = f'Custom Tax Rate for {customer.name}'
#                 if rate["Name"] == custom_tax_name and rate["Active"] == True:
#                     rate_id = rate["Id"] 
#                     rate_percentage = rate["RateValue"]               
#                     break

#             invoice_data.update({"TxnTaxDetail": {
#                 "TxnTaxCodeRef": {
#                     "value": str(tax_code_id)
#                 }, 
#                 "TotalTax": float(total_tax), 
#                 "TaxLine": [
#                     {
#                     "DetailType": "TaxLineDetail", 
#                     "Amount": float(total_tax), 
#                     "TaxLineDetail": {
#                         "NetAmountTaxable": float(invoice.item_amount), 
#                         "TaxPercent": float(customer.tax_percentage), 
#                         "TaxRateRef": {
#                             "value": str(rate_id)
#                         }, 
#                         "PercentBased": True
#                     }
#                     }
#                 ]
#                 }, 
#                 })

#         # Create invoice in QuickBooks
#         created_invoice = create_invoice(token_instance.realm_id, token_instance.access_token, invoice_data)
#         if created_invoice:
#             messages.success(request, "Invoice created successfully and synced with QuickBooks.")
#         else:
#             messages.error(request, "Failed to sync with QuickBooks.")
    
#     except Exception as e:
#         print(f"Error: {str(e)}")
#         messages.error(request, f"Failed to create invoice: {str(e)}")
    
#     return redirect('list-warehouse-shipment' if type == 'warehouse' else 'list-processor-shipment') 


@login_required
def generate_invoice(request, pk, type):
    if not (
        request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 
        'SuperUser' in request.user.get_role() or request.user.is_distributor or 
        request.user.is_warehouse_manager
    ):
        return redirect('dashboard') 
   
    if type == 'warehouse':
        shipment = WarehouseCustomerShipment.objects.filter(id=pk).first()        
    else:
        shipment = ProcessorWarehouseShipment.objects.filter(id=pk).first()  
    
    try:       
        shipment.invoice_approval = True
        shipment.approval_time = timezone.now()
        shipment.save()

    except Exception as e:
        print(f"Error: {str(e)}")
        messages.error(request, f"Failed to create invoice: {str(e)}")
    
    return redirect('list-warehouse-shipment' if type == 'warehouse' else 'list-processor-shipment') 


@login_required()
def warehouse_shipment_invoice(request, pk, type):
    context = {}
    try:
        if type == 'warehouse':
            shipment = WarehouseCustomerShipment.objects.filter(id=pk).first()      
            customer = Customer.objects.filter(id=shipment.customer_id).first()
            customer_user = CustomerUser.objects.filter(customer=customer).first()
            payment_details = PaymentForShipment.objects.filter(shipment_type='warehouse', warehouse_shipment=shipment, status=True).first()
            invoice = Invoice.objects.filter(warehouse_shipment=shipment, shipment_invoice_id=shipment.invoice_id, customer=customer).first()
            carrier_id = CarrierDetails2.objects.filter(shipment=shipment).first().carrier_id
            context["invoice"] = invoice
            context["shipment"] = shipment
            context["payment"] = payment_details       
            context['customer'] = customer
            context['total_amount'] = float(shipment.total_payment) 
            context['customer_user'] = customer_user
            context["carrier_id"] = carrier_id
            shipment_crops = WarehouseShipmentCrops.objects.filter(shipment=shipment).values()
            for crop in shipment_crops:
                crop_ =CustomerContractCropDetails.objects.filter(id=int(crop["crop_id"])).first()
                item = ShipmentItem.objects.filter(item_name=crop_.crop, item_type=crop_.crop_type).first()
                crop["per_unit_rate"] = crop_.per_unit_rate
                crop["description"] = item.description
            context["shipment_crops"] = shipment_crops
            
            due_date = shipment.final_payment_date if shipment.final_payment_date else (shipment.approval_time + timedelta(days=int(customer.credit_terms)))
            context['due_date'] = due_date
            context['type'] = 'warehouse'
            return render (request, 'distributor/invoice.html', context)
        else:
            shipment = ProcessorWarehouseShipment.objects.filter(id=pk).first()      
            customer = Customer.objects.filter(id=shipment.customer_id).first()
            customer_user = CustomerUser.objects.filter(customer=customer).first()
            payment_details = PaymentForShipment.objects.filter(shipment_type='processor', processor_shipment=shipment, status=True).first()
            invoice = Invoice.objects.filter(processor_shipment=shipment, shipment_invoice_id=shipment.invoice_id, customer=customer).first()
            carrier_id = CarrierDetails.objects.filter(shipment=shipment).first().carrier_id
            context["invoice"] = invoice
            context["shipment"] = shipment
            context["payment"] = payment_details       
            context['customer'] = customer
            context['total_amount'] = float(shipment.total_payment)
            context['customer_user'] = customer_user
            context["carrier_id"] = carrier_id
            shipment_crops = ProcessorShipmentCrops.objects.filter(shipment=shipment).values()           
            
            for crop in shipment_crops:
                crop_ =CropDetails.objects.filter(id=int(crop["crop_id"])).first()
                item = ShipmentItem.objects.filter(item_name=crop_.crop, item_type=crop_.crop_type).first()
                crop["per_unit_rate"] = crop_.per_unit_rate
                crop["description"] = item.description
            context["shipment_crops"] = shipment_crops
            
            due_date = shipment.final_payment_date if shipment.final_payment_date else (shipment.approval_time + timedelta(days=int(customer.credit_terms)))
            context['due_date'] = due_date
            context['type'] = 'processor'
            return render (request, 'distributor/invoice.html', context)
    except (ValueError, AttributeError, AdminProcessorContract.DoesNotExist) as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/invoice.html', context)


@login_required()
def create_payment_for_shipment(request, pk, type):
    if type == 'warehouse':
        warehouse_shipment = WarehouseCustomerShipment.objects.get(id=pk)   
        customer = Customer.objects.get(id=int(warehouse_shipment.customer_id))     
        amount = float(warehouse_shipment.total_payment)
        currency = 'USD'          
    else:
        processor_shipment = ProcessorWarehouseShipment.objects.get(id=pk)  
        customer = Customer.objects.get(id=int(processor_shipment.customer_id))     
        amount = float(processor_shipment.total_payment) 
        currency = 'USD'        

    # Create a Stripe Checkout session
    host = request.get_host()
    current_site = f"{protocol}://{host}"
    main_url = f'{current_site}/warehouse/checkout-success/{pk}/{type}/'
    user_email = request.user.email
    customer_user = CustomerUser.objects.filter(contact_email=user_email).first()
    if customer_user.stripe_id :
            stripe_customer_id = customer_user.stripe_id
    else:
        customer = stripe.Customer.create(email=user_email).to_dict()
        stripe_customer_id = customer["id"]
        customer_user.stripe_id = stripe_customer_id
        customer_user.save()
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        customer=stripe_customer_id,
        line_items=[
            {
                'price_data': {
                    'currency': currency.lower(),
                    'product_data': {
                        'name': f"Shipment Payment for {type.capitalize()}",
                    },
                    'unit_amount': int(amount * 100),  # Stripe expects amount in cents
                },
                'quantity': 1,
            },
        ],
        mode='payment',
       
        success_url=main_url + "{CHECKOUT_SESSION_ID}" + "/",
        cancel_url=f"{request.build_absolute_uri('/payment-cancelled/')}",
    )
    return HttpResponseRedirect(session.url)


###########################################QuickBooks Included#############################
# @login_required()
# def checkout_success(request,pk,type,checkout_session_id):
#     """
#     This view handles the creation of a PaymentForShipment instance once the payment has been completed.
#     """
#     stripe.api_key = settings.STRIPE_SECRET_KEY
#     pay = stripe.checkout.Session.retrieve(checkout_session_id).to_dict()
    
#     payment_intent = stripe.PaymentIntent.retrieve(pay['payment_intent'])
#     success_url = reverse('checkout-success', kwargs={'pk': pk, 'type': type, 'checkout_session_id':checkout_session_id})
#     next_url = f"{success_url}"
#     redirect_url = f"{reverse('quickbooks_login')}?{urlencode({'next': next_url})}"
#     try:
#         token_instance = QuickBooksToken.objects.first()                                    
#         refresh_token = token_instance.refresh_token
#         if token_instance.is_token_expired():
#             print("Token expired, refreshing...")
#             new_access_token = refresh_quickbooks_token(refresh_token)
#             if not new_access_token:
#                 return redirect(redirect_url)
#             token_instance.access_token = new_access_token
#             token_instance.expires_at = timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE)
#             token_instance.save()
#     except QuickBooksToken.DoesNotExist:
#         return redirect(redirect_url)  
    
#     if type == 'warehouse':
#         shipment = WarehouseCustomerShipment.objects.get(id=pk)
#         amount = shipment.total_payment
#         currency = 'USD'
#         payment_recived_by = User.objects.filter(is_superuser=True, is_staff=True).first()
#         payment_recived_user_type = 'Admin'
#     else:
#         shipment = ProcessorWarehouseShipment.objects.get(id=pk)
#         amount = shipment.total_payment
#         currency = 'USD'
#         payment_recived_by = User.objects.filter(is_superuser=True, is_staff=True).first()
#         payment_recived_user_type = 'Admin'   

#     customer = Customer.objects.filter(id=shipment.customer_id).first()
#     invoice = Invoice.objects.filter(shipment_invoice_id=shipment.invoice_id, customer=customer).first()

#     payment = PaymentForShipment.objects.create(
#         warehouse_shipment=shipment if type == 'warehouse' else None,
#         processor_shipment=shipment if type == 'processor' else None,
#         shipment_type=type,
#         amount=invoice.total_amount,
#         currency=currency,
#         payment_id=checkout_session_id,
#         payment_by=request.user,
#         user_type='Customer',
#         payment_recived_by=payment_recived_by,
#         payment_recived_user_type=payment_recived_user_type,
#         invoice_id = invoice.shipment_invoice_id
#     )
  
#     payment.payment_responce = pay 
#     payment.save()

#     payment_status = payment_intent.status         
    
#     payment_data = {
#         "CustomerRef": {
#             "value": customer.quickbooks_id, 
#         },
#         "TotalAmt": float(payment.amount),
#         "Line": [{
#             "Amount": float(payment.amount),
#             "LinkedTxn": [{
#                 "TxnId": invoice.quickbooks_id,  
#                 "TxnType": "Invoice"
#             }]
#         }],
#     }
#     try:
#         created_payment = create_payment(token_instance.realm_id, token_instance.access_token, payment_data)

#         if created_payment:
#             print("Payment created successfully and synced with QuickBooks.")
#             messages.success(request, "Payment created successfully and synced with QuickBooks.")
#         else:
#             print("Failed to sync payment with QuickBooks.")
#             messages.error(request, "Failed to create payment in QuickBooks.")

#     except ImproperlyConfigured as e:
#         print(str(e))

#     if payment_status == 'succeeded':
#         payment.status = True
#         shipment.is_paid = True
#         payment.save()  
#         shipment.save()            
#         return render(request, "distributor/success_payment.html")
#     else:
#         payment.status = False
#         payment.save()  
#         message = f"Payment failed: {payment_intent.last_payment_error.message}" if payment_intent.last_payment_error else "Payment failed"
#         return render(request, "distributor/failed_payment.html", {'error_message': message})


# @login_required()
# def checkout_success(request,pk,type,checkout_session_id):
#     """
#     This view handles the creation of a PaymentForShipment instance once the payment has been completed.
#     """
#     stripe.api_key = settings.STRIPE_SECRET_KEY
#     pay = stripe.checkout.Session.retrieve(checkout_session_id).to_dict()
    
#     payment_intent = stripe.PaymentIntent.retrieve(pay['payment_intent']) 
    
#     if type == 'warehouse':
#         shipment = WarehouseCustomerShipment.objects.get(id=pk)
#         amount = shipment.total_payment
#         currency = 'USD'
#         payment_recived_by = User.objects.filter(is_superuser=True, is_staff=True).first()
#         payment_recived_user_type = 'Admin'
#     else:
#         shipment = ProcessorWarehouseShipment.objects.get(id=pk)
#         amount = shipment.total_payment
#         currency = 'USD'
#         payment_recived_by = User.objects.filter(is_superuser=True, is_staff=True).first()
#         payment_recived_user_type = 'Admin'   

#     customer = Customer.objects.filter(id=shipment.customer_id).first()
#     invoice = Invoice.objects.filter(shipment_invoice_id=shipment.invoice_id, customer=customer).first()

#     payment = PaymentForShipment.objects.create(
#         warehouse_shipment=shipment if type == 'warehouse' else None,
#         processor_shipment=shipment if type == 'processor' else None,
#         shipment_type=type,
#         amount=amount,
#         currency=currency,
#         payment_id=checkout_session_id,
#         payment_by=request.user,
#         user_type='Customer',
#         payment_recived_by=payment_recived_by,
#         payment_recived_user_type=payment_recived_user_type,
#         invoice_id = shipment.invoice_id
#     )  
#     payment.payment_responce = pay 
#     payment.save()

#     payment_status = payment_intent.status         

#     if payment_status == 'succeeded':
#         payment.status = True
#         shipment.is_paid = True
#         payment.save()  
#         shipment.save()  
#         msg = "Payment received.."
#         customer_user = CustomerUser.objects.filter(contact_email=request.user.email).first()
#         customer_name = Customer.objects.filter(id=customer_user.customer.id).first()
#         msg_subject = 'New Payment received.'
#         msg_body = f'Dear Admin,\n\nA new payment has been received from customer {customer_name}.\n\nThe details of the same are as below: \n\nInvoice ID: {shipment.invoice_id} \nShipment ID: {shipment.shipment_id} \nContract ID: {shipment.contract.secret_key}  \nPayment Amount: ${shipment.total_payment} \nReceived date: {payment.paid_at} \n\nRegards\nCustomer Service\nAgreeta'
#         from_email = 'techsupportUS@agreeta.com'
#         to_email = ['Agreeta@agreetaus.com']
#         send_mail(
#         msg_subject,
#         msg_body,
#         from_email,
#         to_email,
#         fail_silently=False,
#         )          
#         return render(request, "distributor/success_payment.html")
#     else:
#         payment.status = False
#         payment.save()  
#         message = f"Payment failed: {payment_intent.last_payment_error.message}" if payment_intent.last_payment_error else "Payment failed"
#         return render(request, "distributor/failed_payment.html", {'error_message': message})


@login_required
def checkout_success(request, pk, type, checkout_session_id):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    pay = stripe.checkout.Session.retrieve(checkout_session_id).to_dict()
    payment_intent = stripe.PaymentIntent.retrieve(pay['payment_intent'])
    charge = stripe.Charge.retrieve(payment_intent['latest_charge'])
    
    if type == 'warehouse':
        shipment = WarehouseCustomerShipment.objects.get(id=pk)
        customer = Customer.objects.filter(id=int(shipment.customer_id)).first()
        amount = shipment.total_payment
        currency = 'USD'
        payment_recived_by = User.objects.filter(is_superuser=True, is_staff=True).first()
        payment_recived_user_type = 'Admin'
    else:
        shipment = ProcessorWarehouseShipment.objects.get(id=pk)
        customer = Customer.objects.filter(id=int(shipment.customer_id)).first()
        amount = shipment.total_payment
        currency = 'USD'
        payment_recived_by = User.objects.filter(is_superuser=True, is_staff=True).first()
        payment_recived_user_type = 'Admin'

    customer = Customer.objects.filter(id=shipment.customer_id).first()
    invoice = Invoice.objects.filter(shipment_invoice_id=shipment.invoice_id, customer=customer).first()
    
    payment = PaymentForShipment.objects.create(
        warehouse_shipment=shipment if type == 'warehouse' else None,
        processor_shipment=shipment if type == 'processor' else None,
        shipment_type=type,
        amount=amount,
        currency=currency,
        payment_id=checkout_session_id,
        payment_by=request.user,
        user_type='Customer',
        payment_recived_by=payment_recived_by,
        payment_recived_user_type=payment_recived_user_type,
        invoice_id = shipment.invoice_id
    )
    receipt_url = charge.get('receipt_url')
    print(receipt_url)

    if receipt_url:
        wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"  # Update with the actual path

        # Configuration for pdfkit
        pdfkit_config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        try:
            response = requests.get(receipt_url) 
            print(response.text)          
            if response.status_code == 200:
                html_content = response.text              
                pdf = pdfkit.from_string(html_content, False, configuration=pdfkit_config)
                file_name = f"payment_proof_{payment.id}.pdf"
                payment.payment_proof.save(file_name, ContentFile(pdf))
                if invoice:
                    invoice.payment_proof.save(file_name, ContentFile(pdf))
                    invoice.save()
            else:
                print(f"Failed to fetch receipt content, status: {response.status_code}")
        
        except Exception as e:
            print(f"Error generating PDF from receipt URL: {e}")      

    if payment_intent.status == 'succeeded':
        payment.status = True
        shipment.is_paid = True
        payment.save()
        shipment.save()
        customer_user = CustomerUser.objects.filter(contact_email=request.user.email).first()
        customer_name = Customer.objects.filter(id=customer_user.customer.id).first()
        msg_subject = 'New Payment received.'
        msg_body = f'Dear Admin,\n\nA new payment has been received from customer {customer_name}.\n\nThe details of the same are as below: \n\nInvoice ID: {shipment.invoice_id} \nShipment ID: {shipment.shipment_id} \nContract ID: {shipment.contract.secret_key}  \nPayment Amount: ${payment.amount} \nReceived date: {payment.paid_at} \n\nRegards\nCustomer Service\nAgreeta'
        from_email = 'rijughosh.claymindsolution@gmail.com'
        to_email = ['piu.de1996@gmail.com']

        email = EmailMessage(
            subject=msg_subject,
            body=msg_body,
            from_email=from_email,
            to=to_email,
        )
     
        if payment.payment_proof:
            email.attach(f"payment_proof_{payment.id}.pdf", payment.payment_proof.read(), 'application/pdf')

    
        try:
            email.send(fail_silently=False)
            print("Payment receipt email sent successfully.")
        except Exception as e:
            print(f"Error sending email: {e}")
        return render(request, "distributor/success_payment.html")
    else:
        payment.status = False
        payment.save()
        message = f"Payment failed: {payment_intent.last_payment_error.message}" if payment_intent.last_payment_error else "Payment failed"
        return render(request, "distributor/failed_payment.html", {'error_message': message})


@login_required() 
def customer_view(request, pk):
    context = {}
    try:
        customer_user = CustomerUser.objects.filter(id=pk).first()
        context['customer_user'] = customer_user
        context['customer'] = customer_user.customer
        context['documents'] = CustomerDocuments.objects.filter(customer=customer_user.customer)
        return render(request, 'distributor/customer_view.html', context)
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request, 'distributor/customer_view.html', context) 


@login_required()
def processor_shipment_generate_report(request):
    context = {}
    shipment_logs = ProcessorShipmentLog.objects.all()
    
    if request.method == "POST":
        date_choice = request.POST.get('date_choice')
        single_date = request.POST.get('single_date')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        start_date = request.POST.get('start_date')
        if date_choice == 'single_date' and single_date:        
            single_date_obj = parse_date(single_date)
            shipment_logs = shipment_logs.filter(updated_at__date=single_date_obj)
        elif date_choice == 'date_range' and start_date and end_date:        
            start_date_obj = parse_date(start_date)
            end_date_obj = parse_date(end_date)
            shipment_logs = shipment_logs.filter(updated_at__date__range=[start_date_obj, end_date_obj])
        changes_dict = {}

        for log in shipment_logs:
            if log.changes:
                shipment_id = log.shipment.shipment_id
                description = log.description
                if shipment_id not in changes_dict:
                    changes_dict[shipment_id] = {}
                if description not in changes_dict[shipment_id]:
                    changes_dict[shipment_id][description] = []
                
                for change in log.changes.get('changes', []):
                    changes_dict[shipment_id][description].append({
                        'field': change.get('field'),
                        'old': change.get('old'),
                        'new': change.get('new'),
                        'updated_at': log.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_by': log.updated_by.username if log.updated_by else 'Unknown'
                    })
        
        context["date_choice"] = date_choice
        context["single_date"] = single_date
        context["start_date"] = start_date
        context["end_date"] = end_date
        context['changes_dict'] = dict(changes_dict)
        print(context['changes_dict'])

    return render(request, 'report/processor_shipment_report_list.html', context)


@login_required
def processor_shipment_export_csv(request):
    date_choice = request.GET.get('date_choice')
    single_date = request.GET.get('single_date')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    shipment_logs = ProcessorShipmentLog.objects.all()

    if date_choice == 'single_date' and single_date:
        single_date_obj = parse_date(single_date)
        shipment_logs = shipment_logs.filter(updated_at__date=single_date_obj)
    elif date_choice == 'date_range' and start_date and end_date:
        start_date_obj = parse_date(start_date)
        end_date_obj = parse_date(end_date)
        shipment_logs = shipment_logs.filter(updated_at__date__range=[start_date_obj, end_date_obj])

    changes_dict = defaultdict(lambda: defaultdict(list))

    for log in shipment_logs:
        if log.changes:
            shipment_id = log.shipment.shipment_id
            description = log.description
            for change in log.changes.get('changes', []):
                changes_dict[shipment_id][description].append({
                    'field': change.get('field'),
                    'old': change.get('old'),
                    'new': change.get('new'),
                    'updated_at': log.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_by': log.updated_by.username if log.updated_by else 'Unknown'
                })

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="shipment_changes_report.csv"'
    writer = csv.writer(response)

    writer.writerow(['Shipment ID', 'Description', 'Field', 'Old Value', 'New Value', 'Updated At', 'Updated By'])

    for shipment_id, descriptions in changes_dict.items():
        for description, changes in descriptions.items():
            for change in changes:
                writer.writerow([
                    shipment_id,
                    description,
                    change['field'],
                    change['old'],
                    change['new'],
                    change['updated_at'],
                    change['updated_by']
                ])
    
    return response


@login_required
def processor_shipment_csv_single_shipment(request,shipment_id):  
    date_choice = request.GET.get('date_choice')
    single_date = request.GET.get('single_date')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    shipment_logs = ProcessorShipmentLog.objects.all()

    if shipment_id:

        shipment_logs = shipment_logs.filter(shipment__shipment_id=shipment_id)

    if date_choice == 'single_date' and single_date:
        single_date_obj = parse_date(single_date)
        shipment_logs = shipment_logs.filter(updated_at__date=single_date_obj)
    elif date_choice == 'date_range' and start_date and end_date:
        start_date_obj = parse_date(start_date)
        end_date_obj = parse_date(end_date)
        shipment_logs = shipment_logs.filter(updated_at__date__range=[start_date_obj, end_date_obj])

    changes_dict = defaultdict(lambda: defaultdict(list))

    for log in shipment_logs:
        if log.changes:
            description = log.description
            for change in log.changes.get('changes', []):
                changes_dict[log.shipment.shipment_id][description].append({
                    'field': change.get('field'),
                    'old': change.get('old'),
                    'new': change.get('new'),
                    'updated_at': log.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_by': log.updated_by.username if log.updated_by else 'Unknown'
                })

    response = HttpResponse(content_type='text/csv')
    filename = f"shipment_{shipment_id}_changes_report.csv" if shipment_id else "shipment_changes_report.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)

    writer.writerow(['Shipment ID', 'Description', 'Field', 'Old Value', 'New Value', 'Updated At', 'Updated By'])

    for shipment_id, descriptions in changes_dict.items():
        for description, changes in descriptions.items():
            for change in changes:
                writer.writerow([
                    shipment_id,
                    description,
                    change['field'],
                    change['old'],
                    change['new'],
                    change['updated_at'],
                    change['updated_by']
                ])
    
    return response


@login_required()
def warehouse_shipment_generate_report(request):
    context = {}
    shipment_logs = WarehouseShipmentLog.objects.all()
    
    if request.method == "POST":
        date_choice = request.POST.get('date_choice')
        single_date = request.POST.get('single_date')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        start_date = request.POST.get('start_date')
        if date_choice == 'single_date' and single_date:        
            single_date_obj = parse_date(single_date)
            shipment_logs = shipment_logs.filter(updated_at__date=single_date_obj)
        elif date_choice == 'date_range' and start_date and end_date:        
            start_date_obj = parse_date(start_date)
            end_date_obj = parse_date(end_date)
            shipment_logs = shipment_logs.filter(updated_at__date__range=[start_date_obj, end_date_obj])
        changes_dict = {}

        for log in shipment_logs:
            if log.changes:
                shipment_id = log.shipment.shipment_id
                description = log.description
                if shipment_id not in changes_dict:
                    changes_dict[shipment_id] = {}
                if description not in changes_dict[shipment_id]:
                    changes_dict[shipment_id][description] = []
                
                for change in log.changes.get('changes', []):
                    changes_dict[shipment_id][description].append({
                        'field': change.get('field'),
                        'old': change.get('old'),
                        'new': change.get('new'),
                        'updated_at': log.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'updated_by': log.updated_by.username if log.updated_by else 'Unknown'
                    })
        
        context["date_choice"] = date_choice
        context["single_date"] = single_date
        context["start_date"] = start_date
        context["end_date"] = end_date
        context['changes_dict'] = dict(changes_dict)
        print(context['changes_dict'])

    return render(request, 'report/warehouse_shipment_report_list.html', context)


@login_required
def warehouse_shipment_export_csv(request):
    date_choice = request.GET.get('date_choice')
    single_date = request.GET.get('single_date')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    shipment_logs = WarehouseShipmentLog.objects.all()

    if date_choice == 'single_date' and single_date:
        single_date_obj = parse_date(single_date)
        shipment_logs = shipment_logs.filter(updated_at__date=single_date_obj)
    elif date_choice == 'date_range' and start_date and end_date:
        start_date_obj = parse_date(start_date)
        end_date_obj = parse_date(end_date)
        shipment_logs = shipment_logs.filter(updated_at__date__range=[start_date_obj, end_date_obj])

    changes_dict = defaultdict(lambda: defaultdict(list))

    for log in shipment_logs:
        if log.changes:
            shipment_id = log.shipment.shipment_id
            description = log.description
            for change in log.changes.get('changes', []):
                changes_dict[shipment_id][description].append({
                    'field': change.get('field'),
                    'old': change.get('old'),
                    'new': change.get('new'),
                    'updated_at': log.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_by': log.updated_by.username if log.updated_by else 'Unknown'
                })

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="shipment_changes_report.csv"'
    writer = csv.writer(response)

    writer.writerow(['Shipment ID', 'Description', 'Field', 'Old Value', 'New Value', 'Updated At', 'Updated By'])

    for shipment_id, descriptions in changes_dict.items():
        for description, changes in descriptions.items():
            for change in changes:
                writer.writerow([
                    shipment_id,
                    description,
                    change['field'],
                    change['old'],
                    change['new'],
                    change['updated_at'],
                    change['updated_by']
                ])
    
    return response


@login_required
def warehouse_shipment_csv_single_shipment(request,shipment_id):  
    date_choice = request.GET.get('date_choice')
    single_date = request.GET.get('single_date')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    shipment_logs = WarehouseShipmentLog.objects.all()

    if shipment_id:
        shipment_logs = shipment_logs.filter(shipment__shipment_id=shipment_id)

    if date_choice == 'single_date' and single_date:
        single_date_obj = parse_date(single_date)
        shipment_logs = shipment_logs.filter(updated_at__date=single_date_obj)
    elif date_choice == 'date_range' and start_date and end_date:
        start_date_obj = parse_date(start_date)
        end_date_obj = parse_date(end_date)
        shipment_logs = shipment_logs.filter(updated_at__date__range=[start_date_obj, end_date_obj])

    changes_dict = defaultdict(lambda: defaultdict(list))

    for log in shipment_logs:
        if log.changes:
            description = log.description
            for change in log.changes.get('changes', []):
                changes_dict[log.shipment.shipment_id][description].append({
                    'field': change.get('field'),
                    'old': change.get('old'),
                    'new': change.get('new'),
                    'updated_at': log.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_by': log.updated_by.username if log.updated_by else 'Unknown'
                })

    response = HttpResponse(content_type='text/csv')
    filename = f"shipment_{shipment_id}_changes_report.csv" if shipment_id else "shipment_changes_report.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)

    writer.writerow(['Shipment ID', 'Description', 'Field', 'Old Value', 'New Value', 'Updated At', 'Updated By'])

    for shipment_id, descriptions in changes_dict.items():
        for description, changes in descriptions.items():
            for change in changes:
                writer.writerow([
                    shipment_id,
                    description,
                    change['field'],
                    change['old'],
                    change['new'],
                    change['updated_at'],
                    change['updated_by']
                ])
    
    return response

  
@require_GET
def get_selected_processor(request):
    selected_contract = request.GET.get('selected_contract')
    if not selected_contract:
        return JsonResponse({'error': 'No contract selected'}, status=400)
    
    contract = AdminProcessorContract.objects.filter(id=selected_contract).first()
    if contract:
        return JsonResponse({'selected_processor': contract.processor_entity_name})
    else:
        return JsonResponse({'error': 'Contract not found'}, status=404)


@require_GET
def get_destination_list(request):
    destination_type = request.GET.get('selected_destination')
    if not destination_type:
        return JsonResponse({'error': 'No destination type selected'}, status=400)
    if destination_type == 'warehouse':
        destination_list = Warehouse.objects.all().values('id','name')
    if destination_type == 'customer':
        destination_list = Customer.objects.filter(is_active=True).values('id','name')
    if destination_list:
        return JsonResponse({'destination_list': list(destination_list)})
    else:
        return JsonResponse({'error': 'Destination not found'}, status=404)


@require_GET
def get_crops(request):
    selected_contract_id = request.GET.get('selected_contract')
    if not selected_contract_id:
        return JsonResponse({'error': 'No contract selected'}, status=400)
    contract = AdminProcessorContract.objects.filter(id=int(selected_contract_id)).first()
    crops = CropDetails.objects.filter(contract=contract).values('id', 'crop', 'crop_type')
    if crops:
        return JsonResponse({'crops': list(crops)})
    else:
        return JsonResponse({'error': 'Crops not found'}, status=404)


@require_GET
def get_customer_contracts(request):
    print("function called")
    destination_id = request.GET.get('destination_id')
    crop_ids = request.GET.get('crop_ids')
    if not destination_id or not crop_ids:
        return JsonResponse({'error': 'Destination ID and crops are required'}, status=400)

    try:        
        crop_ids_list = [int(crop_id) for crop_id in crop_ids.split(',')]
        crops = CropDetails.objects.filter(id__in=crop_ids_list)

        if not crops.exists():
            return JsonResponse({'error': 'Invalid crops selected'}, status=404)
        customer_contracts = AdminCustomerContract.objects.filter(
            customer_id=int(destination_id),
            contract_start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )      
        for crop in crops:
            customer_contracts = customer_contracts.filter(
                customerContractCrop__crop=crop.crop,
                customerContractCrop__crop_type=crop.crop_type
            )
        if customer_contracts.exists():
            contract_data = list(customer_contracts.values('id', 'secret_key', 'customer_name'))
            return JsonResponse({'customer_contracts': contract_data})
        else:
            return JsonResponse({'error': 'No matching contracts found'}, status=404)

    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@require_GET
def get_selected_customer(request):
    selected_contract = request.GET.get('selected_contract')
    if not selected_contract:
        return JsonResponse({'error': 'No contract selected'}, status=400)
    
    contract = AdminCustomerContract.objects.filter(id=selected_contract).first()
    if contract:
        return JsonResponse({'selected_customer': contract.customer_name})
    else:
        return JsonResponse({'error': 'Contract not found'}, status=404)


@require_GET
def get_warehouse(request):
    selected_contract = request.GET.get('selected_contract')
    if not selected_contract:
        return JsonResponse({'error': 'No contract selected'}, status=400)
    
    contract = AdminCustomerContract.objects.filter(id=selected_contract).first()
    print(contract)
    if contract:
        customer = Customer.objects.filter(id=int(contract.customer_id)).first()
        if not customer:
            return JsonResponse({'error': 'Customer not found'}, status=404)

        if customer.warehouse: 
            warehouse = customer.warehouse
            warehouse_data = {
                'id': warehouse.id,
                'name': warehouse.name
            }
            return JsonResponse({'warehouses': [warehouse_data]})
    else:
        return JsonResponse({'error': 'Contract not found'}, status=404)
    

@require_GET
def get_customer_contract_crops(request):
    selected_contract_id = request.GET.get('selected_contract')
    if not selected_contract_id:
        return JsonResponse({'error': 'No contract selected'}, status=400)
    contract = AdminCustomerContract.objects.filter(id=int(selected_contract_id)).first()
    crops = CustomerContractCropDetails.objects.filter(contract=contract).values('id', 'crop', 'crop_type')
    if crops:
        return JsonResponse({'crops': list(crops)})
    else:
        return JsonResponse({'error': 'Crops not found'}, status=404)


@login_required() 
def processor_shipment_csv_download(request):  
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'PROCESSOR SHIPMENT.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)        
        writer.writerow(['SHIPMENT ID', 'INVOICE NUMBER', 'CONTRACT ID', 'ORIGIN', 'DESTINATION', 'CROP || WEIGHT || LOT NUMBER', 'OUTBOUND TYPE', 'CARRIER', 'CARRIER ID', 'PURCHASE ORDER NAME', 'PURCHASE ORDER NUMBER', 'DATE SHIPPED', 'DATE RECEIVED', 'STATUS', 'DUE DATE'])
        output = ProcessorWarehouseShipment.objects.prefetch_related(
                    Prefetch('processor_shipment_crop', queryset=ProcessorShipmentCrops.objects.all())
                ).all()
        for i in output:            
            carrier_id = CarrierDetails.objects.filter(shipment=i).first().carrier_id

            crop_details = "\n".join([
                f"{crop.crop} || {crop.net_weight or 0} {crop.weight_unit} || {crop.lot_number or 'N/A'}"
                for crop in i.processor_shipment_crop.all()
            ])
            writer.writerow([i.shipment_id, i.invoice_id, i.contract.secret_key, i.processor_entity_name, i.warehouse_name if i.warehouse_name else i.customer_name, crop_details, i.outbound_type, i.carrier_type, carrier_id, i.purchase_order_name, i.purchase_order_number, 
            i.date_pulled, i.distributor_receive_date, i.status, i.final_payment_date])
        return response 
       
    elif request.user.is_processor :
        user_email = request.user.email
        p = ProcessorUser.objects.get(contact_email=user_email)
        processor_id = Processor.objects.get(id=p.processor.id).id
        entity_name = Processor.objects.get(id=processor_id).entity_name
        output = ProcessorWarehouseShipment.objects.prefetch_related(
                    Prefetch('processor_shipment_crop', queryset=ProcessorShipmentCrops.objects.all())
                ).filter(processor_id=processor_id, processor_type="T1", processor_entity_name=entity_name)
        filename = f'PROCESSOR SHIPMENT_{entity_name}.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        
        writer.writerow(['SHIPMENT ID', 'INVOICE NUMBER', 'CONTRACT ID', 'ORIGIN', 'DESTINATION', 'CROP || WEIGHT || LOT NUMBER', 'OUTBOUND TYPE', 'CARRIER', 'CARRIER ID', 'PURCHASE ORDER NAME', 'PURCHASE ORDER NUMBER', 'DATE SHIPPED', 'DATE RECEIVED', 'STATUS', 'DUE DATE'])
        for i in output:            
            carrier_id = CarrierDetails.objects.filter(shipment=i).first().carrier_id

            crop_details ="\n".join([
                f"{crop.crop} || {crop.net_weight or 0} {crop.weight_unit} || {crop.lot_number or 'N/A'}"
                for crop in i.processor_shipment_crop.all()
            ])
            writer.writerow([i.shipment_id, i.invoice_id, i.contract.secret_key, i.processor_entity_name, i.warehouse_name if i.warehouse_name else i.customer_name, crop_details, i.outbound_type, i.carrier_type, carrier_id, i.purchase_order_name, i.purchase_order_number, 
            i.date_pulled, i.distributor_receive_date, i.status, i.final_payment_date])
        return response
    
    elif request.user.is_processor2 :
        user_email = request.user.email
        p = ProcessorUser2.objects.get(contact_email=user_email)
        processor_id = Processor2.objects.get(id=p.processor2.id).id
        entity_name = Processor2.objects.get(id=processor_id).entity_name
        processor_type = p.processor2.processor_type.all().first().type_name
        output = ProcessorWarehouseShipment.objects.prefetch_related(
                    Prefetch('processor_shipment_crop', queryset=ProcessorShipmentCrops.objects.all())
                ).filter(processor_id=processor_id, processor_type=processor_type, processor_entity_name=entity_name)
        filename = f'PROCESSOR SHIPMENT_{entity_name}.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        
        writer.writerow(['SHIPMENT ID', 'INVOICE NUMBER', 'CONTRACT ID', 'ORIGIN', 'DESTINATION', 'CROP || WEIGHT || LOT NUMBER', 'OUTBOUND TYPE', 'CARRIER', 'CARRIER ID', 'PURCHASE ORDER NAME', 'PURCHASE ORDER NUMBER', 'DATE SHIPPED', 'DATE RECEIVED', 'STATUS', 'DUE DATE'])
        for i in output:            
            carrier_id = CarrierDetails.objects.filter(shipment=i).first().carrier_id

            crop_details = "\n".join([
                f"{crop.crop} || {crop.net_weight or 0} {crop.weight_unit} || {crop.lot_number or 'N/A'}"
                for crop in i.processor_shipment_crop.all()
            ])
            writer.writerow([i.shipment_id, i.invoice_id, i.contract.secret_key, i.processor_entity_name, i.warehouse_name if i.warehouse_name else i.customer_name, crop_details, i.outbound_type, i.carrier_type, carrier_id, i.purchase_order_name, i.purchase_order_number, 
            i.date_pulled, i.distributor_receive_date, i.status, i.final_payment_date])
        return response
    else:
        return redirect("dashboard")


@login_required() 
def warehouse_shipment_csv_download(request):  
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'WAREHOUSE SHIPMENT.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)        
        writer.writerow(['SHIPMENT ID', 'INVOICE NUMBER', 'CONTRACT ID', 'ORIGIN', 'DESTINATION', 'CROP || WEIGHT || LOT NUMBER', 'OUTBOUND TYPE', 'CARRIER', 'CARRIER ID', 'PURCHASE ORDER NAME', 'PURCHASE ORDER NUMBER', 'DATE SHIPPED', 'DATE RECEIVED', 'STATUS', 'DUE DATE'])
        shipments = WarehouseCustomerShipment.objects.prefetch_related(
                    Prefetch('warehouse_shipment_crop', queryset=WarehouseShipmentCrops.objects.all())
                ).all()
        for i in shipments:            
            carrier_id = CarrierDetails2.objects.filter(shipment=i).first().carrier_id

            crop_details = "\n".join([
                f"{crop.crop} || {crop.net_weight or 0} {crop.weight_unit} || {crop.lot_number or 'N/A'}"
                for crop in i.warehouse_shipment_crop.all()
            ])
            writer.writerow([i.shipment_id, i.invoice_id, i.contract.secret_key, i.warehouse_name, i.customer_name, crop_details, i.outbound_type, i.carrier_type, carrier_id, i.purchase_order_name, i.purchase_order_number, 
            i.date_pulled, i.customer_receive_date, i.status, i.final_payment_date])
        return response 
       
    elif request.user.is_warehouse_manager:
        user_email = request.user.email
        w = WarehouseUser.objects.get(contact_email=user_email)
        warehouse = Warehouse.objects.get(id=w.warehouse.id)
        warehouse_id = warehouse.id
        shipments = WarehouseCustomerShipment.objects.prefetch_related(
                Prefetch('warehouse_shipment_crop', queryset=WarehouseShipmentCrops.objects.all())
            ).filter(warehouse_id=warehouse_id)
        filename = f'WAREHOUSE SHIPMENT_{warehouse.name}.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        
        writer.writerow(['SHIPMENT ID', 'INVOICE NUMBER', 'CONTRACT ID', 'ORIGIN', 'DESTINATION', 'CROP || WEIGHT || LOT NUMBER', 'OUTBOUND TYPE', 'CARRIER', 'CARRIER ID', 'PURCHASE ORDER NAME', 'PURCHASE ORDER NUMBER', 'DATE SHIPPED', 'DATE RECEIVED', 'STATUS', 'DUE DATE'])
        for i in shipments:            
            carrier_id = CarrierDetails2.objects.filter(shipment=i).first().carrier_id

            crop_details = "\n".join([
                f"{crop.crop} || {crop.net_weight or 0} {crop.weight_unit} || {crop.lot_number or 'N/A'}"
                for crop in i.warehouse_shipment_crop.all()
            ])
            writer.writerow([i.shipment_id, i.invoice_id, i.contract.secret_key, i.warehouse_name, i.customer_name, crop_details, i.outbound_type, i.carrier_type, carrier_id, i.purchase_order_name, i.purchase_order_number, 
            i.date_pulled, i.customer_receive_date, i.status, i.final_payment_date])
        return response
    
    elif request.user.is_distributor :
        user_email = request.user.email
        d = DistributorUser.objects.get(contact_email=user_email)
        distributor = Distributor.objects.get(id=d.distributor.id)
        warehouses = distributor.warehouse.all().values_list('id', flat=True)
        shipments = WarehouseCustomerShipment.objects.prefetch_related(
            Prefetch(
                'warehouse_shipment_crop', 
                queryset=WarehouseShipmentCrops.objects.all()
            )
        ).filter(warehouse_id__in=warehouses).order_by('-id')

        filename = f'WAREHOUSE SHIPMENT_{distributor.entity_name}.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        
        writer.writerow(['SHIPMENT ID', 'INVOICE NUMBER', 'CONTRACT ID', 'ORIGIN', 'DESTINATION', 'CROP || WEIGHT || LOT NUMBER', 'OUTBOUND TYPE', 'CARRIER', 'CARRIER ID', 'PURCHASE ORDER NAME', 'PURCHASE ORDER NUMBER', 'DATE SHIPPED', 'DATE RECEIVED', 'STATUS', 'DUE DATE'])
        for i in shipments:            
            carrier_id = CarrierDetails2.objects.filter(shipment=i).first().carrier_id

            crop_details = "\n".join([
                f"{crop.crop} || {crop.net_weight or 0} {crop.weight_unit} || {crop.lot_number or 'N/A'}"
                for crop in i.warehouse_shipment_crop.all()
            ])
            writer.writerow([i.shipment_id, i.invoice_id, i.contract.secret_key, i.warehouse_name, i.customer_name, crop_details, i.outbound_type, i.carrier_type, carrier_id, i.purchase_order_name, i.purchase_order_number, 
            i.date_pulled, i.customer_receive_date, i.status, i.final_payment_date])
        return response
    else:
        return redirect("dashboard")


def customer_credit_memo_issue(request, type, pk):
    if type == "warehouse": 
        shipment = WarehouseCustomerShipment.objects.filter(id=pk).first()        
        shipment_crops = WarehouseShipmentCrops.objects.filter(shipment=shipment)
        for crop in shipment_crops:
            contract_crop = CustomerContractCropDetails.objects.filter(contract=shipment.contract, id=crop.crop_id, crop=crop.crop, crop_type=crop.crop_type).first()
            if contract_crop:
                contract_unit = contract_crop.amount_unit
                shipment_unit = crop.weight_unit

                if contract_unit == "LBS" and shipment_unit == "MT":
                    weight_to_add_back = float(crop.net_weight) * 2204.62
                elif contract_unit == "MT" and shipment_unit == "LBS":
                    weight_to_add_back = float(crop.net_weight) / 2204.62
                else:
                    weight_to_add_back = float(crop.net_weight)

                contract_crop.left_amount += weight_to_add_back
                contract_crop.save()

        customer = Customer.objects.filter(id=int(shipment.customer_id)).first()
        if shipment.is_paid:            
            customer_available_credit = Decimal(customer.available_credit)
            shipment_total_payment = Decimal(shipment.total_payment)

            customer.available_credit = customer_available_credit + shipment_total_payment
            customer.save()
    else:
        shipment = ProcessorWarehouseShipment.objects.filter(id=pk).first()
        if shipment.customer_contract not in [None, "None", "", " ", "null"]:

            shipment_crops = WarehouseShipmentCrops.objects.filter(shipment=shipment)
            for crop in shipment_crops:
                contract_crop = CustomerContractCropDetails.objects.filter(contract=shipment.contract, id=crop.crop_id, crop=crop.crop, crop_type=crop.crop_type).first()
                if contract_crop:
                    contract_unit = contract_crop.amount_unit
                    shipment_unit = crop.weight_unit

                    if contract_unit == "LBS" and shipment_unit == "MT":
                        weight_to_add_back = float(crop.net_weight) * 2204.62
                    elif contract_unit == "MT" and shipment_unit == "LBS":
                        weight_to_add_back = float(crop.net_weight) / 2204.62
                    else:
                        weight_to_add_back = float(crop.net_weight)

                    contract_crop.left_amount += weight_to_add_back
                    contract_crop.save()

            customer = Customer.objects.filter(id=int(shipment.customer_id)).first()
            if shipment.is_paid:               
                customer_available_credit = Decimal(customer.available_credit)
                shipment_total_payment = Decimal(shipment.total_payment)

                customer.available_credit = customer_available_credit + shipment_total_payment
                customer.save()            
        else:
            pass
    return redirect('list-customer')

