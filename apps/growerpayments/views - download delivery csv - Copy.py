from django.shortcuts import render
from django.http.response import HttpResponse
import datetime
from django.contrib.auth.decorators import login_required
from apps.processor.models import *
from apps.accounts.models import *
from apps.grower.models import *
from apps.farms.models import *
from apps.field.models import *
from apps.storage.models import *
from apps.growersurvey.models import *
from apps.growerpayments.models import *
from datetime import datetime, timedelta, date
from django.shortcuts import render, redirect
# import investpy as inv
# import nasdaqdatalink
import yfinance as yf
import requests
from django.contrib import messages
import pandas as pd
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import csv
from django.http import JsonResponse
import os
from io import StringIO
from zipfile import ZipFile
from django.db.models import Q
from django.db.models import Subquery, OuterRef
# import investpy

# Create your views here.

@login_required()
def entry_feeds_add(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        # ef = EntryFeeds.objects.all()
        # grower_id_ef = [i.grower.id for i in ef]
        # growers = Grower.objects.all().exclude(id__in = grower_id_ef) .order_by("name")
        growers = Grower.objects.all().order_by("name")
        context["growers"] = growers
        if request.method == "POST":
            grower_id = request.POST.get("grower_id")
            if grower_id != "all":
                field = Field.objects.filter(grower_id = grower_id)
                crop_list = [i.crop for i in field]
                crop = []
                if "COTTON" in crop_list:
                    crop.append("COTTON")
                if "RICE" in crop_list:
                    crop.append("RICE")
                if "WHEAT" in crop_list:
                    crop.append("WHEAT")
                context["crop"] = crop
                context["selectedGrower"] = Grower.objects.get(id=grower_id)
                show_entry = EntryFeeds.objects.filter(grower_id=grower_id).order_by('-id')
                context["show_entry"] = show_entry
                grower_crop = request.POST.get("grower_crop")
                contracted_payment_option = request.POST.get("contracted_payment_option")
                contract_base_price = request.POST.get("contract_base_price")
                sustainability_premium = request.POST.get("sustainability_premium")
                from_date = request.POST.get("from_date")
                to_date = request.POST.get("to_date")
                context['from_date'] = str(from_date)
                context['to_date'] = str(to_date)
                if from_date and to_date :
                    check_from_date = datetime.strptime(from_date, '%Y-%m-%d')
                    check_to_date = datetime.strptime(to_date, '%Y-%m-%d')
                    if check_to_date > check_from_date :
                        from_date = from_date
                        to_date = to_date
                        # check_grower = EntryFeeds.objects.filter(grower_id=grower_id,from_date__lte=from_date,to_date__lte=to_date)
                        check_grower1 = EntryFeeds.objects.filter(grower_id=grower_id,from_date__range=[from_date, to_date])
                        check_grower2= EntryFeeds.objects.filter(grower_id=grower_id,to_date__range=[from_date, to_date])
                        
                        # check_grower = EntryFeeds.objects.filter(grower_id=grower_id,from_date__range=[from_date, to_date],to_date__range=[from_date, to_date])
                        # if check_grower.exists() :
                        if check_grower1.exists() or check_grower2.exists() :
                            messages.error(request,"Date Range Exists For This Grower")
                            return render(request, "growerpayments/entry_feeds_add.html",context)
                        else:
                            pass
                    else:
                        messages.error(request,"Not a Vaild Date Range")
                        return render(request, "growerpayments/entry_feeds_add.html",context)
                else:
                    from_date = None
                    to_date = None
                    check_grower3= EntryFeeds.objects.filter(grower_id=grower_id,from_date=from_date,to_date=to_date)
                    if check_grower3.exists() and grower_crop != None and grower_crop != 'all' :
                        messages.error(request,"Select Date Range For This Grower")
                        return render(request, "growerpayments/entry_feeds_add.html",context)

                # if crop Cotton / Rice 
                if grower_crop != None and grower_crop != 'all' and contracted_payment_option == "Fixed Price" and contract_base_price and sustainability_premium :
                    entryfeeds = EntryFeeds(grower_id=grower_id,crop=grower_crop,contracted_payment_option=contracted_payment_option,
                    contract_base_price=contract_base_price,sustainability_premium=sustainability_premium,from_date=from_date,to_date=to_date)
                    entryfeeds.save()
                    # Log Table 13-04-23
                    grower_name = Grower.objects.get(id=grower_id).name
                    log_type, log_status, log_device = "EntryFeeds", "Added", "Web"
                    log_idd, log_name = entryfeeds.id, f'{grower_name} - Fixed Price'
                    log_details = f"Grower = {grower_name}  | contracted_payment_option = Fixed Price | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date}"
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
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                                        
                    logtable.save()
                    return redirect('entry_feeds_list')
                elif grower_crop != None and grower_crop != 'all' and contracted_payment_option == "Delivered Market Price" :
                    entryfeeds = EntryFeeds(grower_id=grower_id,crop=grower_crop,contracted_payment_option=contracted_payment_option,from_date=from_date,to_date=to_date)
                    entryfeeds.save()
                    # Log Table 13-04-23
                    grower_name = Grower.objects.get(id=grower_id).name
                    log_type, log_status, log_device = "EntryFeeds", "Added", "Web"
                    log_idd, log_name = entryfeeds.id, f'{grower_name} - Delivered Market Price'
                    log_details = f"Grower = {grower_name}  | contracted_payment_option = Delivered Market Price | contract_base_price = None | sustainability_premium = 0.04 | from_date = {from_date} | to_date = {to_date}"
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
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                                        
                    logtable.save()
                    return redirect('entry_feeds_list')
                elif grower_crop != None and grower_crop != 'all' and contracted_payment_option == "Acreage Release"  and contract_base_price and sustainability_premium :
                    entryfeeds = EntryFeeds(grower_id=grower_id,crop=grower_crop,contracted_payment_option=contracted_payment_option,
                                            contract_base_price=contract_base_price,sustainability_premium=sustainability_premium,from_date=from_date,to_date=to_date)
                    entryfeeds.save()
                    # Log Table 13-04-23
                    grower_name = Grower.objects.get(id=grower_id).name
                    log_type, log_status, log_device = "EntryFeeds", "Added", "Web"
                    log_idd, log_name = entryfeeds.id, f'{grower_name} - Acreage Release'
                    log_details = f"Grower = {grower_name}  | contracted_payment_option = Acreage Release | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date}"
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
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                                        
                    logtable.save()
                    return redirect('entry_feeds_list')
        return render(request, "growerpayments/entry_feeds_add.html",context)
    elif 'Grower' in request.user.get_role() and not request.user.is_superuser:
        pass
    elif request.user.is_consultant:
        pass
    elif request.user.is_processor :
        pass

@login_required()
def entry_feeds_list(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        entery = EntryFeeds.objects.all()
        context["entery"] = entery
        return render(request, "growerpayments/entry_feeds_list.html",context)

@login_required()
def entry_feeds_edit(request,pk):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        en = EntryFeeds.objects.get(id=pk)
        context["en"]= en
        context["show_entry"]= EntryFeeds.objects.filter(grower_id = en.grower.id).order_by('-id')
        context["from_date"]= str(en.from_date) if en.from_date else ''
        context["to_date"]= str(en.to_date) if en.to_date else ''
        if request.method == "POST":
            contracted_payment_option = request.POST.get("contracted_payment_option")
            contract_base_price = request.POST.get("contract_base_price")
            sustainability_premium = request.POST.get("sustainability_premium")

            from_date = request.POST.get("from_date")
            to_date = request.POST.get("to_date")
            if from_date and to_date :
                check_from_date = datetime.strptime(from_date, '%Y-%m-%d')
                check_to_date = datetime.strptime(to_date, '%Y-%m-%d')
                if check_to_date > check_from_date :
                    from_date = from_date
                    to_date = to_date
                    # check_grower = EntryFeeds.objects.filter(grower_id=grower_id,from_date__lte=from_date,to_date__lte=to_date)
                    check_grower1 = EntryFeeds.objects.filter(grower_id=en.grower.id,from_date__range=[from_date, to_date]).exclude(id=en.id)
                    check_grower2= EntryFeeds.objects.filter(grower_id=en.grower.id,to_date__range=[from_date, to_date]).exclude(id=en.id)
                    # check_grower = EntryFeeds.objects.filter(grower_id=grower_id,from_date__range=[from_date, to_date],to_date__range=[from_date, to_date])
                    # if check_grower.exists() :
                    if check_grower1.exists() or check_grower2.exists() :
                        messages.error(request,"Date Range Exists For This Grower")
                        return render(request, "growerpayments/entry_feeds_edit.html",context)
                    else:
                        pass
                else:
                    messages.error(request,"Not a Vaild Date Range")
                    return render(request, "growerpayments/entry_feeds_edit.html",context)
            else:
                from_date = None
                to_date = None
            # quality_premium = request.POST.get("quality_premium")
            if contracted_payment_option != None and contracted_payment_option == "Fixed Price" :
                if contract_base_price != "" and sustainability_premium != "" :
                    en.contracted_payment_option = contracted_payment_option
                    en.contract_base_price = contract_base_price
                    en.sustainability_premium = sustainability_premium
                    en.from_date = from_date
                    en.to_date = to_date
                    en.save()

                    # Log Table 13-04-23
                    grower_name = en.grower.name
                    payment_option = en.contracted_payment_option
                    contract_base_price = en.contract_base_price
                    sustainability_premium = en.sustainability_premium
            
                    from_date = en.from_date
                    to_date = en.to_date
                    log_type, log_status, log_device = "EntryFeeds", "Edited", "Web"
                    log_idd, log_name = en.id, f'{grower_name} - {payment_option}'
                    log_details = f"Grower = {grower_name}  | contracted_payment_option = {payment_option} | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date}"
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
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                                        
                    logtable.save()
                    return redirect ("entry_feeds_list")
            elif contracted_payment_option != None and contracted_payment_option == "Delivered Market Price":
                en.contracted_payment_option = contracted_payment_option
                en.contract_base_price = None
                en.sustainability_premium = None
                en.from_date = from_date
                en.to_date = to_date
                en.save()
                # Log Table 13-04-23
                grower_name = en.grower.name
                payment_option = en.contracted_payment_option
                contract_base_price = en.contract_base_price
                sustainability_premium = 0.04

                from_date = en.from_date
                to_date = en.to_date
                log_type, log_status, log_device = "EntryFeeds", "Edited", "Web"
                log_idd, log_name = en.id, f'{grower_name} - {payment_option}'
                log_details = f"Grower = {grower_name}  | contracted_payment_option = {payment_option} | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date}"
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
                                    action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                    log_device=log_device)
                                    
                logtable.save()
                return redirect ("entry_feeds_list")

            elif contracted_payment_option != None and contracted_payment_option == "Acreage Release" and contract_base_price != None and sustainability_premium != None :
                en.contracted_payment_option = contracted_payment_option
                en.contract_base_price = contract_base_price
                en.sustainability_premium = sustainability_premium
                # en.quality_premium = quality_premium
                en.from_date = from_date
                en.to_date = to_date
                en.save()
                # Log Table 13-04-23
                grower_name = en.grower.name
                payment_option = en.contracted_payment_option
                contract_base_price = en.contract_base_price
                sustainability_premium = en.sustainability_premium

                from_date = en.from_date
                to_date = en.to_date
                log_type, log_status, log_device = "EntryFeeds", "Edited", "Web"
                log_idd, log_name = en.id, f'{grower_name} - {payment_option}'
                log_details = f"Grower = {grower_name}  | contracted_payment_option = {payment_option} | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date}"
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
                                    action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                    log_device=log_device)
                                    
                logtable.save()
                return redirect ("entry_feeds_list")
        return render(request, "growerpayments/entry_feeds_edit.html",context)


@login_required()
def entry_feeds_delete(request,pk):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        en = EntryFeeds.objects.get(id=pk)
        # Log Table 13-04-23
        grower_name = en.grower.name
        payment_option = en.contracted_payment_option
        contract_base_price = en.contract_base_price
        sustainability_premium = en.sustainability_premium
        if payment_option == "Delivered Market Price" :
            sustainability_premium = 0.04
        from_date = en.from_date
        to_date = en.to_date
        log_type, log_status, log_device = "EntryFeeds", "Deleted", "Web"
        log_idd, log_name = en.id, f'{grower_name} - {payment_option}'
        log_details = f"Grower = {grower_name}  | contracted_payment_option = {payment_option} | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date}"
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
                            action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                            log_device=log_device)
                            
        logtable.save()
        en.delete()
        return HttpResponse(1)


# grower delivery details List

@login_required()
def grower_payments_table(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        entry = EntryFeeds.objects.all()
        grower_payment = []
        fixed_price_id = []
        fixed_price_grower_id = []
        delivery_price_id = []
        acreage_Release_price_id = []
        delivery_grower_id = []
        acreage_Release_grower_id = []
        crop_cotton_grower_id = []
        crop_rice_grower_id = []
        flag = ''
        selectedCrop = ''
        selectedGrower = ''
        temp_grower_payment_start_index = 0
        temp_grower_payment_end_index = ''
        var_pagni_crop = ''
        # sorting grower_id and enteryfeed_id
        for i in entry :
            if i.contracted_payment_option == 'Fixed Price':
                fixed_price_id.append(i.id)
                fixed_price_grower_id.append(i.grower.id)
            if i.contracted_payment_option == 'Delivered Market Price':
                delivery_price_id.append(i.id)
                delivery_grower_id.append(i.grower.id)
            if i.contracted_payment_option == 'Acreage Release':
                acreage_Release_price_id.append(i.id)
                acreage_Release_grower_id.append(i.grower.id)
            if i.crop == 'COTTON' :
                crop_cotton_grower_id.append(i.grower.id)
            if i.crop == 'RICE' :
                crop_rice_grower_id.append(i.grower.id)
        total_grower_id = fixed_price_grower_id + delivery_grower_id + acreage_Release_grower_id
        growers = Grower.objects.filter(id__in = total_grower_id).order_by('name')
        context['growers'] = growers
        # if request.method == 'POST':
        grower_idd = request.GET.get('grower_id')
        crop_idd = request.GET.get('crop_id')
        get_page_no_temp = request.GET.get('get_page_no_temp')
        
        if get_page_no_temp :
            var_get_page_no_temp = get_page_no_temp
        else :
            var_get_page_no_temp = 1
        context['var_get_page_no_temp'] =int(var_get_page_no_temp)

        # seacrh with grower 
        if grower_idd and grower_idd != 'All' :
            selectedGrower = Grower.objects.get(id=grower_idd)
            if int(grower_idd) in fixed_price_grower_id :
                fixed_price_grower_id = [int(grower_idd)]
                delivery_grower_id = []
                total_grower_id = fixed_price_grower_id + delivery_grower_id
                selectedCrop = ''
            elif int(grower_idd) in delivery_grower_id :
                delivery_grower_id = [int(grower_idd)]
                fixed_price_grower_id = []
                total_grower_id = fixed_price_grower_id + delivery_grower_id
                selectedCrop = ''
            elif int(grower_idd) in acreage_Release_grower_id :
                delivery_grower_id = [int(grower_idd)]
                fixed_price_grower_id = []
                total_grower_id = fixed_price_grower_id + delivery_grower_id
                selectedCrop = ''
            elif grower_idd == 'All' :
                get_page_no_temp = 1
        # seacrh with crop 
        elif crop_idd :
            selectedCrop = crop_idd
            if crop_idd == "COTTON":
                # crop_cotton_grower_id
                fixed_price_grower_id = crop_cotton_grower_id
                delivery_grower_id = []
                total_grower_id = fixed_price_grower_id + delivery_grower_id
                selectedGrower = ''
                
            elif crop_idd == "RICE":
                # crop_rice_grower_id
                delivery_grower_id = crop_rice_grower_id
                fixed_price_grower_id = []
                total_grower_id = fixed_price_grower_id + delivery_grower_id
                
                selectedGrower = ''
            if get_page_no_temp :
                get_page_no_temp = get_page_no_temp
            else:
                get_page_no_temp = 1
        # seacrh with grower and crop .........
        elif crop_idd and grower_idd :
            selectedGrower = Grower.objects.get(id=grower_idd)
            selectedCrop = crop_idd
            total_grower_id = []
            var = EntryFeeds.objects.get(grower_id = grower_idd)
            selectedGrowerCrop = var.crop
            if selectedGrowerCrop == 'COTTON' :
                if int(grower_idd) in fixed_price_grower_id and selectedCrop == 'COTTON' :
                    fixed_price_grower_id = [int(grower_idd)]
                    delivery_grower_id = []
                    total_grower_id = fixed_price_grower_id + delivery_grower_id
                else:
                    fixed_price_grower_id = []
                    delivery_grower_id = []
                    total_grower_id = fixed_price_grower_id + delivery_grower_id
            elif selectedGrowerCrop == 'RICE' :
                if int(grower_idd) in fixed_price_grower_id and selectedCrop == 'RICE' :
                    fixed_price_grower_id = [int(grower_idd)]
                    delivery_grower_id = []
                    total_grower_id = fixed_price_grower_id + delivery_grower_id
                elif int(grower_idd) in delivery_grower_id and selectedCrop == 'RICE' :
                    delivery_grower_id = [int(grower_idd)]
                    fixed_price_grower_id = []
                    total_grower_id = fixed_price_grower_id + delivery_grower_id
            else :
                fixed_price_grower_id = []
                delivery_grower_id = []
                total_grower_id = fixed_price_grower_id + delivery_grower_id
            
        else:
            entry = entry
            grower_payment = grower_payment
            fixed_price_id = fixed_price_id
            fixed_price_grower_id = fixed_price_grower_id
            delivery_price_id = delivery_price_id
            delivery_grower_id = delivery_grower_id
        
        # custom pagination code 
        pagi_bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id)
        pagi_grower_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED')
        total_obj_qury = len(pagi_bale) + len(pagi_grower_shipment)
        tem_total_no_page = total_obj_qury // 100 

        if get_page_no_temp :
            if int(get_page_no_temp) == 1 :
                page_lower_limit, page_upper_limit = 0, 100
                temp_grower_payment_start_index, temp_grower_payment_end_index = page_lower_limit, page_upper_limit
            elif int(get_page_no_temp) == int(tem_total_no_page) :
                page_lower_limit, page_upper_limit = int(get_page_no_temp) * 100 , (int(get_page_no_temp) + 1) * 100
                temp_grower_payment_start_index, temp_grower_payment_end_index = page_lower_limit, total_obj_qury
            else :
                page_lower_limit, page_upper_limit = int(get_page_no_temp) * 100 , (int(get_page_no_temp) + 1) * 100
                temp_grower_payment_start_index, temp_grower_payment_end_index = page_lower_limit, page_upper_limit

        if crop_idd and crop_idd != 'All' :
            if int(get_page_no_temp) == 1 :
                page_lower_limit, page_upper_limit = 0, 100
                temp_grower_payment_start_index, temp_grower_payment_end_index = page_lower_limit, page_upper_limit
            elif int(get_page_no_temp) == int(tem_total_no_page) :
                page_lower_limit, page_upper_limit = int(get_page_no_temp) * 100 , (int(get_page_no_temp) + 1) * 100
                temp_grower_payment_start_index, temp_grower_payment_end_index = page_lower_limit, total_obj_qury
            else :
                page_lower_limit, page_upper_limit = int(get_page_no_temp) * 100 , (int(get_page_no_temp) + 1) * 100
                temp_grower_payment_start_index, temp_grower_payment_end_index = page_lower_limit, page_upper_limit
        context['temp_grower_payment_start_index'] = int(temp_grower_payment_start_index) + 1
        context['temp_grower_payment_end_index'] = temp_grower_payment_end_index
        # Fixed Market Price ..................
        if get_page_no_temp :
            bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id)[int(page_lower_limit):int(page_upper_limit)]
        elif crop_idd and crop_idd != 'All' :
            bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id)[int(page_lower_limit):int(page_upper_limit)]
        else :
            bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id)


        # bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id)
        qp_lbs = 0.00
        for i in bale :
            delivery_date = i.dt_class
            delivery_id = i.bale_id
            grower_name = i.ob3
            crop = "COTTON"
            field = i.field_name
            delivery_lbs = i.net_wt
            processor = i.classing.processor.entity_name
            classs = i.level
            # colorcode="#ffffff"
            # 27-03-23
            if delivery_date :
                str_date = str(delivery_date)
                if '-' in str_date :
                    try :
                        str_date = str_date.split('-')
                        mm = str_date[0]
                        dd = str_date[1]
                        yy = str_date[2]
                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                        finale_date = date(int(yyyy), int(mm), int(dd))
                    except :
                        continue
                elif '/' in str_date :
                    try :
                        str_date = str_date.split('/')
                        mm = str_date[0]
                        dd = str_date[1]
                        yy = str_date[2]
                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                        finale_date = date(int(yyyy), int(mm), int(dd))
                    except :
                        continue
                else:
                    finale_date = ''
            else:
                continue
            # 27-03-23
            check_entry = EntryFeeds.objects.filter(grower_id = i.ob2,crop='COTTON')
            if len(check_entry) == 0 :
                continue
            if len(check_entry) == 1 :
                var = EntryFeeds.objects.get(grower_id = i.ob2)
            if len(check_entry) > 1 :
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = i.ob2,from_date__lte=finale_date,to_date__gte=finale_date)
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = i.ob2,from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)
                elif check_entry_with_no_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)

            cpb_lbs = var.contract_base_price
            sp_lbs = var.sustainability_premium
            if classs == 'Bronze' :
                qp_lbs = 0.00
            elif classs == "Silver":
                qp_lbs = 0.02
            elif classs == "Gold":
                qp_lbs = 0.04
            elif classs == "None":
                qp_lbs = 0.00
                                    
            if classs != "None":
                total_price = float(cpb_lbs) + float(sp_lbs) + float(qp_lbs)
                delivered_value = float(delivery_lbs) * float(total_price)
                if delivery_date :
                    date_str = str(delivery_date).split("/")
                    dd = int(date_str[1])
                    mm = int(date_str[0])
                    yy = int(date_str[2])
                    if len(str(yy)) == 2 : 
                        yyyy = int("20{}".format(yy))
                    else:
                        yyyy = yy
                    specific_date = datetime(yyyy, mm, dd)
                    new_date = specific_date + timedelta(60)
                    payment_due_date = new_date.strftime("%m/%d/%y")
                else:
                    payment_due_date ="N/A"
            else:
                total_price = 0.00
                delivered_value = 0.00
                payment_due_date ="N/A"

            data = {
                    'delivery_date':delivery_date,
                    'delivery_id':delivery_id,
                    'grower_name':grower_name,
                    'crop':crop,
                    'variety':"-",
                    'field':field,
                    'delivery_lbs':delivery_lbs,
                    'processor':processor,
                    'class':classs,
                    'cpb_lbs':cpb_lbs,
                    'sp_lbs':sp_lbs,
                    'qp_lbs':qp_lbs,
                    'total_price':"{0:.5f}".format(total_price),
                    'delivered_value':"{0:.4f}".format(delivered_value),
                    'payment_due_date':payment_due_date,
                }
            grower_payment.append(data)

        # For Delivery Market ...........
        if get_page_no_temp :
            grower_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED')[int(page_lower_limit):int(page_upper_limit)]
        elif crop_idd and crop_idd != 'All' :
            grower_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED')[int(page_lower_limit):int(page_upper_limit)]
        else :
            grower_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED')

        # grower_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED') 
        for i in grower_shipment :
            grower_id = i.grower.id
            delivery_id = i.shipment_id
            grower_name = i.grower.name
            crop = i.crop
            variety = i.variety
            field = i.field.name
            if i.approval_date == None:
                process_date_int = i.process_date.strftime("%m/%d/%y")
                delivery_date = process_date_int
                new_date = i.process_date + timedelta(60)
                payment_due_date = new_date.strftime("%m/%d/%y")
                # 25-03-23
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i.process_date,to_date__gte=i.process_date)
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exist() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id=check_entry_id)
                elif check_entry_with_no_date.exist() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)
            else:
                process_date_int = i.approval_date.strftime("%m/%d/%y")
                delivery_date = process_date_int
                new_date = i.approval_date + timedelta(60)
                payment_due_date = new_date.strftime("%m/%d/%y")
                # 25-03-23
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i.approval_date,to_date__gte=i.approval_date)
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id=check_entry_id)
                elif check_entry_with_no_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)
                

            # if var.contracted_payment_option == 'Fixed Price' or var.contracted_payment_option == 'Acreage Release' :
            #     cpb_lbs = var.contract_base_price
            #     sp_lbs = var.sustainability_premium
            #     total_price_init = float(cpb_lbs) + float(sp_lbs)
            #     total_price = total_price_init
            if var.contracted_payment_option == 'Fixed Price' :
                cpb_lbs = var.contract_base_price
                sp_lbs = var.sustainability_premium
                total_price_init = float(cpb_lbs) + float(sp_lbs)
                total_price = total_price_init
            elif var.contracted_payment_option == 'Acreage Release' :
                cpb_lbs = var.contract_base_price
                sp_lbs = var.sustainability_premium
                total_price_init = float(cpb_lbs) + float(sp_lbs)
                total_price = total_price_init
            else:
                calculation_date = i.approval_date
                cpb_lbs = '-'
                sp_lbs = '-'
                if NasdaqApiData.objects.filter(date_api=calculation_date).count() !=0 :
                    total_price_init = NasdaqApiData.objects.get(date_api=calculation_date).close_value_api
                else:
                    for l in range(1,10):
                        next_date = calculation_date - timedelta(l)
                        if NasdaqApiData.objects.filter(date_api=next_date).count() !=0 :
                            total_price_init = NasdaqApiData.objects.get(date_api=next_date).close_value_api
                            break
                total_price2 = float(total_price_init) / 100
                total_price = total_price2 + 0.04
            if i.received_amount != None :
                delivery_lbs = int(float(i.received_amount)) 
                delivered_value = float(delivery_lbs) * total_price
            else:
                delivery_lbs = int(float(i.total_amount))
                delivered_value = float(delivery_lbs) * total_price
            
            processor = i.processor.entity_name
            total_price = "{0:.5f}".format(total_price)
            delivered_value = "{0:.4f}".format(delivered_value)
            # colorcode ="#ffffff"
            # new_date = i.date_time + timedelta(60)
            # payment_due_date = new_date.strftime("%m/%d/%y")
            
            # new code added for Entry feed variation
            # newcalc = GrowerPayments.objects.filter(delivery_id=delivery_id)
            # if newcalc.exists() :
            #     calcu_lbs = GrowerPayments.objects.get(delivery_id=delivery_id)
            #     total_price = "{0:.5f}".format(float(calcu_lbs.total_price))
            #     delivered_value = "{0:.4f}".format(float(calcu_lbs.delivered_value))
            #     cpb_lbs = calcu_lbs.contract_base_price
            #     sp_lbs = calcu_lbs.sustainability_premium
            #     colorcode ="#00FF00"

            data = {
                'delivery_date':delivery_date,
                'delivery_id':delivery_id,
                'grower_name':grower_name,
                'crop':crop,
                'variety':variety,
                'field':field,
                'delivery_lbs':delivery_lbs,
                'processor':processor,
                'class':'-',
                'cpb_lbs':cpb_lbs,
                'sp_lbs':sp_lbs,
                'qp_lbs':'-',
                'total_price':total_price,
                'delivered_value':delivered_value,
                'payment_due_date':payment_due_date,
            }
            grower_payment.append(data)
        
        # grower_idd
        context['selectedGrower'] = selectedGrower
        context['selectedCrop'] = selectedCrop

        if grower_idd :
            report = grower_payment
        else :
            paginator = Paginator(grower_payment, 100)
            page = request.GET.get('page')
            try:
                report = paginator.page(page)
            except PageNotAnInteger:
                report = paginator.page(1)
            except EmptyPage:
                report = paginator.page(paginator.num_pages)

        context['grower_payment'] = report
        context['temp_grower_payment_count'] = total_obj_qury
        context['range'] = range(tem_total_no_page)
        return render(request, "growerpayments/grower_payments_table.html",context)

@login_required()
def grower_payments_table_csv_download(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'Grower Delivery Details.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        
        writer.writerow(['DELIVERY DATE','DELIVERY ID','GROWER NAME', 'CROP', 'VARIETY','FARM', 'FIELD', 'DELIVERY LBS','PROCESSOR',
        'CLASS', 'Contract Base Price / LBS','Sustainability Premium / LBS','Quality Premium / LBS', 'TOTAL PRICE / LBS ($)', 'DELIVERED VALUE ($)',
        'PAYMENT DUE DATE'])
        grower_payment = []

        entry = EntryFeeds.objects.all()
        total_grower_id = [i.grower.id for i in entry]
        # Fixed Market Price ..................
        bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id)
        for i in bale :
            delivery_date = i.dt_class
            delivery_id = i.bale_id
            grower_name = i.ob3
            crop = "COTTON"
            field = i.field_name
            delivery_lbs = i.net_wt
            processor = i.classing.processor.entity_name
            classs = i.level

            # 27-03-23
            if delivery_date :
                str_date = str(delivery_date)
                if '-' in str_date :
                    try :
                        str_date = str_date.split('-')
                        mm = str_date[0]
                        dd = str_date[1]
                        yy = str_date[2]
                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                        finale_date = date(int(yyyy), int(mm), int(dd))
                    except :
                        continue
                elif '/' in str_date :
                    try :
                        str_date = str_date.split('/')
                        mm = str_date[0]
                        dd = str_date[1]
                        yy = str_date[2]
                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                        finale_date = date(int(yyyy), int(mm), int(dd))
                    except :
                        continue
                else:
                    finale_date = ''
            else:
                continue
            
            # 27-03-23
            check_entry = EntryFeeds.objects.filter(grower_id = i.ob2)
            if len(check_entry) == 0 :
                continue
            if len(check_entry) == 1 :
                var = EntryFeeds.objects.get(grower_id = i.ob2)
            if len(check_entry) > 1 :
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = i.ob2,from_date__lte=finale_date,to_date__gte=finale_date)
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = i.ob2,from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)
                elif check_entry_with_no_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)

            # var = EntryFeeds.objects.get(grower_id = i.ob2)
            cpb_lbs = var.contract_base_price
            sp_lbs = var.sustainability_premium
            if classs == 'Bronze' :
                qp_lbs = 0.00
            elif classs == "Silver":
                qp_lbs = 0.02
            elif classs == "Gold":
                qp_lbs = 0.04
            elif classs == "None":
                qp_lbs = 0.00
                                    
            if classs != "None":
                total_price = float(cpb_lbs) + float(sp_lbs) + float(qp_lbs)
                delivered_value = float(delivery_lbs) * float(total_price)
                if delivery_date :
                    date_str = str(delivery_date).split("/")
                    dd = int(date_str[1])
                    mm = int(date_str[0])
                    yy = int(date_str[2])
                    if len(str(yy)) == 2 : 
                        yyyy = int("20{}".format(yy))
                    else:
                        yyyy = yy
                    specific_date = datetime(yyyy, mm, dd)
                    new_date = specific_date + timedelta(60)
                    payment_due_date = new_date.strftime("%m/%d/%y")
                else:
                    payment_due_date ="N/A"
            else:
                total_price = 0.00
                delivered_value = 0.00
                payment_due_date ="N/A"

            data = {
                    'delivery_date':delivery_date,
                    'delivery_id':delivery_id,
                    'grower_name':grower_name,
                    'crop':crop,
                    'variety':"-",
                    'field':field,
                    'delivery_lbs':delivery_lbs,
                    'processor':processor,
                    'classs':classs,
                    'cpb_lbs':cpb_lbs,
                    'sp_lbs':sp_lbs,
                    'qp_lbs':qp_lbs,
                    'total_price':"{0:.5f}".format(total_price),
                    'delivered_value':"{0:.4f}".format(delivered_value),
                    'payment_due_date':payment_due_date,
                }
            grower_payment.append(data)
        # For Delivery Market ...........
        grower_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED') 
        for i in grower_shipment :
            delivery_id = i.shipment_id
            grower_name = i.grower.name
            grower_id = i.grower.id
            crop = i.crop
            variety = i.variety
            field = i.field.name
            if i.approval_date == None:
                process_date_int = i.process_date.strftime("%m/%d/%y")
                delivery_date = process_date_int
                new_date = i.process_date + timedelta(60)
                payment_due_date = new_date.strftime("%m/%d/%y")
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i.process_date,to_date__gte=i.process_date)
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id=check_entry_id)
                elif check_entry_with_no_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)
            else:
                process_date_int = i.approval_date.strftime("%m/%d/%y")
                delivery_date = process_date_int
                new_date = i.approval_date + timedelta(60)
                payment_due_date = new_date.strftime("%m/%d/%y")
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i.approval_date,to_date__gte=i.approval_date)
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id=check_entry_id)
                elif check_entry_with_no_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)

            # var = EntryFeeds.objects.get(grower_id=grower_id)
            if var.contracted_payment_option == 'Fixed Price' or  var.contracted_payment_option == 'Acreage Release' :
                cpb_lbs = var.contract_base_price
                sp_lbs = var.sustainability_premium
                total_price_init = float(cpb_lbs) + float(sp_lbs)
                total_price = total_price_init
            else:
                calculation_date = i.approval_date
                if NasdaqApiData.objects.filter(date_api=calculation_date).count() !=0 :
                    total_price_init = NasdaqApiData.objects.get(date_api=calculation_date).close_value_api
                else:
                    for l in range(1,10):
                        next_date = calculation_date - timedelta(l)
                        if NasdaqApiData.objects.filter(date_api=next_date).count() !=0 :
                            total_price_init = NasdaqApiData.objects.get(date_api=next_date).close_value_api
                            break
                total_price2 = float(total_price_init) / 100
                total_price = total_price2 + 0.04
                cpb_lbs = '-'
                sp_lbs = '-'
            if i.received_amount != None :
                delivery_lbs = int(float(i.received_amount)) 
                delivered_value = float(delivery_lbs) * total_price
            else:
                delivery_lbs = int(float(i.total_amount))
                delivered_value = float(delivery_lbs) * total_price
            
            processor = i.processor.entity_name
            total_price = "{0:.5f}".format(total_price)
            delivered_value = "{0:.4f}".format(delivered_value)
            # new_date = i.date_time + timedelta(60)
            # payment_due_date = new_date.strftime("%m/%d/%y")
            # new code added for Entry feed variation
            # newcalc = GrowerPayments.objects.filter(delivery_id=delivery_id)
            # if newcalc.exists() :
            #     calcu_lbs = GrowerPayments.objects.get(delivery_id=delivery_id)
            #     total_price = "{0:.5f}".format(float(calcu_lbs.total_price))
            #     delivered_value = "{0:.4f}".format(float(calcu_lbs.delivered_value))
            #     cpb_lbs = "-"
            #     sp_lbs = "-"
                
            data = {
                'delivery_date':delivery_date,
                'delivery_id':delivery_id,
                'grower_name':grower_name,
                'crop':crop,
                'variety':variety,
                'field':field,
                'delivery_lbs':delivery_lbs,
                'processor':processor,
                'classs':'-',
                'cpb_lbs':cpb_lbs,
                'sp_lbs':sp_lbs,
                'qp_lbs':'-',
                'total_price':total_price,
                'delivered_value':delivered_value,
                'payment_due_date':payment_due_date,
            }
            grower_payment.append(data)

        # Making .csv file 
        for i in grower_payment :
            writer.writerow([i["delivery_date"],i["delivery_id"],i["grower_name"], i["crop"], i["variety"],'-', i["field"], i["delivery_lbs"],i["processor"],
            i["classs"], i["cpb_lbs"], i["sp_lbs"],i["qp_lbs"], i["total_price"], i["delivered_value"],i["payment_due_date"]])
           
        return response
@login_required()
def grower_payments_list_not_paid_csv_download(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'Not Paid Grower Payment Details.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        writer.writerow(['DELIVERY DATE','DELIVERY ID','GROWER NAME', 'CROP', 'VARIETY','FARM', 'FIELD', 'DELIVERY LBS',
        'CLASS', 'TOTAL PRICE / LBS ($)', 'DELIVERED VALUE ($)','PAYMENT DUE DATE','PAYMENT AMOUNT ($)' ,'PAYMENT DATE', 'PAYMENT TYPE', 'PAYMENT CONFIRMATION'])

        bale = BaleReportFarmField.objects.filter(
                    ~Q(bale_id__in=Subquery(
                        GrowerPayments.objects.values('delivery_id')
                    ))
                ).exclude(level='None').values('dt_class','bale_id','ob3','farm_name','field_name','net_wt','level','ob2')
        
        grower_shipment = GrowerShipment.objects.filter(~Q(shipment_id__in=Subquery(
                        GrowerPayments.objects.values('delivery_id')
                    ))).filter(crop='RICE').filter(status='APPROVED').values('id','shipment_id',
                        'grower__name','grower__id','crop','variety','field__name','approval_date',
                        'process_date','total_amount','received_amount')
        for i in bale :
            delivery_date = i['dt_class']
            delivery_id = i['bale_id']
            grower_name = i['ob3']
            crop = "COTTON"
            # field = i.field_name
            field = i['field_name']
            delivery_lbs = i['net_wt']
            farm = i['farm_name']
            # processor = i.classing.processor.entity_name
            classs = i['level']
            if delivery_date :
                str_date = str(delivery_date)
                if '-' in str_date :
                    try :
                        str_date = str_date.split('-')
                        mm = str_date[0]
                        dd = str_date[1]
                        yy = str_date[2]
                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                        finale_date = date(int(yyyy), int(mm), int(dd))
                    except :
                        continue
                elif '/' in str_date :
                    try :
                        str_date = str_date.split('/')
                        mm = str_date[0]
                        dd = str_date[1]
                        yy = str_date[2]
                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                        finale_date = date(int(yyyy), int(mm), int(dd))
                    except :
                        continue
                else:
                    finale_date = ''
            else:
                continue
            # 27-03-23
            check_entry = EntryFeeds.objects.filter(grower_id = i['ob2'])
            if len(check_entry) == 0 :
                continue
            if len(check_entry) == 1 :
                var = EntryFeeds.objects.get(grower_id = i['ob2'])
            if len(check_entry) > 1 :
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = i['ob2'],from_date__lte=finale_date,to_date__gte=finale_date)
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = i['ob2'],from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)
                elif check_entry_with_no_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)
            # var = EntryFeeds.objects.get(grower_id = i['ob2'])
            # contract_base_price sustainability_premium 
            cpb_lbs = var.contract_base_price
            sp_lbs = var.sustainability_premium
            if cpb_lbs :
                cpb_lbs = var.contract_base_price
            else:
                cpb_lbs = 0.0
            if sp_lbs :
                sp_lbs = var.sustainability_premium
            else:
                sp_lbs = 0.0
            if classs == 'Bronze' :
                qp_lbs = 0.00
            elif classs == "Silver":
                qp_lbs = 0.02
            elif classs == "Gold":
                qp_lbs = 0.04
            elif classs == "None":
                qp_lbs = 0.00
                                    
            if classs != "None":
                total_price = float(cpb_lbs) + float(sp_lbs) + float(qp_lbs)
                delivered_value = float(delivery_lbs) * float(total_price)
                if delivery_date :
                    date_str = str(delivery_date).split("/")
                    dd = int(date_str[1])
                    mm = int(date_str[0])
                    yy = int(date_str[2])
                    if len(str(yy)) == 2 : 
                        yyyy = int("20{}".format(yy))
                    else:
                        yyyy = yy
                    specific_date = datetime(yyyy, mm, dd)
                    new_date = specific_date + timedelta(60)
                    payment_due_date = new_date.strftime("%m/%d/%y")
                else:
                    payment_due_date ="N/A"
            else:
                total_price = 0.00
                delivered_value = 0.00
                payment_due_date ="N/A"
            writer.writerow([delivery_date,delivery_id,grower_name, crop, '-', farm, field, delivery_lbs,
                classs, total_price, delivered_value,payment_due_date,'-','-','-','-'])  
                

        # For Rice
        # grower_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED').values('id','shipment_id',
        #                 'grower__name','grower__id','crop','variety','field__name','approval_date','process_date','total_amount','received_amount')
        # approval_date process_date shipment_id grower__id grower__name crop variety field__name
        for i in grower_shipment : 
            delivery_id = i['shipment_id']
            grower_name = i['grower__name']
            grower_id = i['grower__id']
            crop = i['crop']
            variety = i['variety']
            field = i["field__name"]

            if i['approval_date'] == None:
                delivery_date = i['process_date'].strftime("%m/%d/%y")
                new_date = i['process_date'] + timedelta(60)
                payment_due_date = new_date.strftime("%m/%d/%y")
                # 27-03-23
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i['process_date'],to_date__gte=i['process_date'])
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id=check_entry_id)
                elif check_entry_with_no_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)
            else:
                delivery_date = i['approval_date'].strftime("%m/%d/%y")
                new_date = i['approval_date'] + timedelta(60)
                payment_due_date = new_date.strftime("%m/%d/%y")
                # 27-03-23
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i['approval_date'],to_date__gte=i['approval_date'])
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id=check_entry_id)
                elif check_entry_with_no_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)

            # var = EntryFeeds.objects.get(grower_id=grower_id)
            if var.contracted_payment_option == 'Fixed Price' or  var.contracted_payment_option == 'Acreage Release' :
                cpb_lbs = var.contract_base_price
                sp_lbs = var.sustainability_premium
                total_price_init = float(cpb_lbs) + float(sp_lbs)
                total_price = total_price_init
            else:
                calculation_date = i['approval_date']
                if NasdaqApiData.objects.filter(date_api=calculation_date).count() !=0 :
                    total_price_init = NasdaqApiData.objects.get(date_api=calculation_date).close_value_api
                else:
                    for l in range(1,10):
                        next_date = calculation_date - timedelta(l)
                        if NasdaqApiData.objects.filter(date_api=next_date).count() !=0 :
                            total_price_init = NasdaqApiData.objects.get(date_api=next_date).close_value_api
                            break
                total_price2 = float(total_price_init) / 100
                total_price = total_price2 + 0.04
            if i['received_amount'] != None :
                delivery_lbs = int(float(i['received_amount'])) 
                delivered_value = float(delivery_lbs) * total_price
            else:
                delivery_lbs = int(float(i['total_amount']))
                delivered_value = float(delivery_lbs) * total_price

            total_price = "{0:.5f}".format(total_price)
            delivered_value = "{0:.4f}".format(delivered_value)
            
            writer.writerow([delivery_date,delivery_id,grower_name, crop, variety, '',field, delivery_lbs,
                '-', total_price, delivered_value,payment_due_date,'-','-','-','-']) 
                 
        return response


@login_required()
def grower_payments_list_paid_csv_download(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'Paid Grower Payment Details.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        writer.writerow(['DELIVERY DATE','DELIVERY ID','GROWER NAME', 'CROP', 'VARIETY','FARM', 'FIELD', 'DELIVERY LBS',
        'CLASS', 'TOTAL PRICE / LBS ($)', 'DELIVERED VALUE ($)','PAYMENT DUE DATE','PAYMENT AMOUNT ($)' ,'PAYMENT DATE', 'PAYMENT TYPE', 'PAYMENT CONFIRMATION'])

        bale = GrowerPayments.objects.all().order_by("id").values('delivery_date','delivery_id','grower__name','crop',
                                                   'variety','farm_name','field_name','delivery_lbs','total_price','delivered_value',
                                                   'payment_due_date','payment_amount','payment_date','payment_type',
                                                   'payment_confirmation','level')       
        
        for i in bale :
            writer.writerow([i['delivery_date'],i['delivery_id'],i['grower__name'], i['crop'], i['variety'], i['farm_name'], i['field_name'], i['delivery_lbs'],
                i['level'], i['total_price'], i['delivered_value'],i['payment_due_date'],i['payment_amount'],i['payment_date'],i['payment_type'],
                i['payment_confirmation']])
        return response

@login_required()
def update_paid_payments_list(request) :
    update_payment = GrowerPayments.objects.all().order_by("id").values("id")[50000:]

    for i in update_payment :
        get_payment = GrowerPayments.objects.get(id=i["id"])
        if get_payment.crop == "COTTON":
            check_bale = BaleReportFarmField.objects.filter(bale_id=get_payment.delivery_id).values("ob3","field_name","ob4","farm_name","farm_id","level","crop_variety")
            if len(check_bale) == 1 :
             
                if not get_payment.field :
                    get_payment.field = [i["ob4"] for i in check_bale][0] if len([i["ob4"] for i in check_bale])!=0 else None
                
                if not get_payment.farm :
                    get_payment.farm = [i["farm_id"] for i in check_bale][0] if len([i["farm_id"] for i in check_bale])!=0 else None
                
                get_payment.grower_name = [i["ob3"] for i in check_bale][0] if len([i["ob3"] for i in check_bale])!=0 else None
                get_payment.field_name = [i["field_name"] for i in check_bale][0] if len([i["field_name"] for i in check_bale])!=0 else None
                get_payment.farm_name = [i["farm_name"] for i in check_bale][0] if len([i["farm_name"] for i in check_bale])!=0 else None
                get_payment.variety = [i["crop_variety"] for i in check_bale][0] if len([i["crop_variety"] for i in check_bale])!=0 else None
                get_payment.level = [i["level"] for i in check_bale][0] if len([i["level"] for i in check_bale])!=0 else None
                get_payment.save()
        elif get_payment.crop == "RICE":
            check_shipment = GrowerShipment.objects.filter(shipment_id=get_payment.delivery_id).values("grower__name","field_id","field__name","field__farm__id","field__farm__name","variety")
            if len(check_shipment) == 1 :

                if not get_payment.field :
                    get_payment.field = [i["field_id"] for i in check_shipment][0] if len([i["field_id"] for i in check_shipment][0])!=0 else None
                
                if not get_payment.farm :
                    get_payment.farm = [i["field__farm__id"] for i in check_shipment][0] if len([i["field__farm__id"] for i in check_shipment])!=0 else None

                get_payment.grower_name = [i["grower__name"] for i in check_shipment][0] if len([i["grower__name"] for i in check_shipment])!=0 else None
                get_payment.field_name = [i["field__name"] for i in check_shipment][0] if len([i["field__name"] for i in check_shipment][0])!=0 else None
                get_payment.farm_name = [i["field__farm__name"] for i in check_shipment][0] if len([i["field__farm__name"] for i in check_shipment])!=0 else None
                get_payment.variety = [i["variety"] for i in check_shipment][0] if len([i["variety"] for i in check_shipment])!=0 else None
                get_payment.level = ""
                get_payment.save()
    return HttpResponse("update done")

@login_required()
def grower_payments_list_csv_download(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'Grower Payment Details.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        
        writer.writerow(['DELIVERY DATE','DELIVERY ID','GROWER NAME', 'CROP', 'VARIETY','FARM', 'FIELD', 'DELIVERY LBS',
        'CLASS', 'TOTAL PRICE / LBS ($)', 'DELIVERED VALUE ($)','PAYMENT DUE DATE','PAYMENT AMOUNT ($)' ,'PAYMENT DATE', 'PAYMENT TYPE', 'PAYMENT CONFIRMATION'])
        
        grower_payment = []
        entry = EntryFeeds.objects.all()
        total_grower_id = [i.grower.id for i in entry]
        # Fixed Market Price ..................
        # bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id).exclude(level='None').values('dt_class','bale_id',
        # 'ob3','field_name','net_wt','level','ob2')
        bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id).exclude(level='None').values('dt_class','bale_id',
        'ob3','field_name','net_wt','level','ob2')
        # dt_class bale_id grower_name=ob3 field_name net_wt level grower_id=ob2
        for i in bale :
            delivery_id = i['bale_id']
            delivery_date = i['dt_class']
            delivery_id = i['bale_id']
            grower_name = i['ob3']
            crop = "COTTON"
            # field = i.field_name
            field = i['field_name']
            delivery_lbs = i['net_wt']
            # processor = i.classing.processor.entity_name
            classs = i['level']
            try:
                check_p = GrowerPayments.objects.get(delivery_id=delivery_id)
                
                data = {
                        'delivery_date':delivery_date,
                        'delivery_id':delivery_id,
                        'grower_name':grower_name,
                        'crop':crop,
                        'variety':"-",
                        'field':field,
                        'delivery_lbs':delivery_lbs,
                        'classs':classs,
                        'total_price':"{0:.5f}".format(float(check_p.total_price)),
                        'delivered_value':"{0:.4f}".format(float(check_p.delivered_value)),
                        'payment_due_date':check_p.payment_due_date,
                        'payment_amount':check_p.payment_amount,
                        'payment_date':check_p.payment_date,
                        'payment_type':check_p.payment_type,
                        'payment_confirmation':check_p.payment_confirmation,
                    }
                grower_payment.append(data)
            except:
                # 27-03-23
                if delivery_date :
                    str_date = str(delivery_date)
                    if '-' in str_date :
                        try :
                            str_date = str_date.split('-')
                            mm = str_date[0]
                            dd = str_date[1]
                            yy = str_date[2]
                            yyyy = f'20{yy}' if len(yy) == 2 else yy
                            finale_date = date(int(yyyy), int(mm), int(dd))
                        except :
                            continue
                    elif '/' in str_date :
                        try :
                            str_date = str_date.split('/')
                            mm = str_date[0]
                            dd = str_date[1]
                            yy = str_date[2]
                            yyyy = f'20{yy}' if len(yy) == 2 else yy
                            finale_date = date(int(yyyy), int(mm), int(dd))
                        except :
                            continue
                    else:
                        finale_date = ''
                else:
                    continue
                # 27-03-23
                check_entry = EntryFeeds.objects.filter(grower_id = i['ob2'])
                if len(check_entry) == 0 :
                    continue
                if len(check_entry) == 1 :
                    var = EntryFeeds.objects.get(grower_id = i['ob2'])
                if len(check_entry) > 1 :
                    check_entry_with_date = EntryFeeds.objects.filter(grower_id = i['ob2'],from_date__lte=finale_date,to_date__gte=finale_date)
                    check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = i['ob2'],from_date__isnull=True,to_date__isnull=True)
                    if check_entry_with_date.exists() :
                        check_entry_id = [i.id for i in check_entry_with_date][0]
                        var = EntryFeeds.objects.get(id = check_entry_id)
                    elif check_entry_with_no_date.exists() :
                        check_entry_id = [i.id for i in check_entry_with_no_date][0]
                        var = EntryFeeds.objects.get(id = check_entry_id)
                # var = EntryFeeds.objects.get(grower_id = i['ob2'])
                # contract_base_price sustainability_premium 
                cpb_lbs = var.contract_base_price
                sp_lbs = var.sustainability_premium
                if cpb_lbs :
                    cpb_lbs = var.contract_base_price
                else:
                    cpb_lbs = 0.0
                if sp_lbs :
                    sp_lbs = var.sustainability_premium
                else:
                    sp_lbs = 0.0
                if classs == 'Bronze' :
                    qp_lbs = 0.00
                elif classs == "Silver":
                    qp_lbs = 0.02
                elif classs == "Gold":
                    qp_lbs = 0.04
                elif classs == "None":
                    qp_lbs = 0.00
                                        
                if classs != "None":
                    total_price = float(cpb_lbs) + float(sp_lbs) + float(qp_lbs)
                    delivered_value = float(delivery_lbs) * float(total_price)
                    if delivery_date :
                        date_str = str(delivery_date).split("/")
                        dd = int(date_str[1])
                        mm = int(date_str[0])
                        yy = int(date_str[2])
                        if len(str(yy)) == 2 : 
                            yyyy = int("20{}".format(yy))
                        else:
                            yyyy = yy
                        specific_date = datetime(yyyy, mm, dd)
                        new_date = specific_date + timedelta(60)
                        payment_due_date = new_date.strftime("%m/%d/%y")
                    else:
                        payment_due_date ="N/A"
                else:
                    total_price = 0.00
                    delivered_value = 0.00
                    payment_due_date ="N/A"
                # gpay = GrowerPayments.objects.filter(delivery_id=delivery_id).values('id')
                # delivery_id payment_amount payment_date payment_type payment_confirmation
                # if gpay.exists() :
                #     get_gpay = GrowerPayments.objects.get(delivery_id=delivery_id)
                #     payment_amount = get_gpay.payment_amount
                #     payment_date = get_gpay.payment_date
                #     payment_type = get_gpay.payment_type
                #     payment_confirmation = get_gpay.payment_confirmation
                # else:
                #     payment_amount = ''
                #     payment_date = ''
                #     payment_type = ''
                # total_deliverd_lbs.append(int(float(delivery_lbs)))
                # total_deliverd_values.append(float(delivered_value))
                data = {
                        'delivery_date':delivery_date,
                        'delivery_id':delivery_id,
                        'grower_name':grower_name,
                        'crop':crop,
                        'variety':"-",
                        'field':field,
                        'delivery_lbs':delivery_lbs,
                        'classs':classs,
                        'total_price':"{0:.5f}".format(total_price),
                        'delivered_value':"{0:.4f}".format(delivered_value),
                        'payment_due_date':payment_due_date,
                        'payment_amount':'',
                        'payment_date':'',
                        'payment_type':'',
                        'payment_confirmation':'',
                    }
                grower_payment.append(data)

        # For Delivery Market ...........
        grower_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED').values('id','shipment_id',
                        'grower__name','grower__id','crop','variety','field__name','approval_date','process_date','total_amount','received_amount')
        # approval_date process_date shipment_id grower__id grower__name crop variety field__name
        for i in grower_shipment : 
            delivery_id = i['shipment_id']
            grower_name = i['grower__name']
            grower_id = i['grower__id']
            crop = i['crop']
            variety = i['variety']
            field = i["field__name"]
            try:
                check_p = GrowerPayments.objects.get(delivery_id=delivery_id)
                if i['approval_date'] == None:
                    delivery_date = i['process_date'].strftime("%m/%d/%y")
                else:
                    delivery_date = i['approval_date'].strftime("%m/%d/%y")
                data = {
                        'delivery_date':delivery_date,
                        'delivery_id':delivery_id,
                        'grower_name':check_p.grower.name,
                        'crop':crop,
                        'variety':"-",
                        'field':field,
                        'delivery_lbs':check_p.delivery_lbs,
                        'classs':"classs",
                        'total_price':"{0:.5f}".format(float(check_p.total_price)),
                        'delivered_value':"{0:.4f}".format(float(check_p.delivered_value)),
                        'payment_due_date':check_p.payment_due_date,
                        'payment_amount':check_p.payment_amount,
                        'payment_date':check_p.payment_date,
                        'payment_type':check_p.payment_type,
                        'payment_confirmation':check_p.payment_confirmation,
                    }
                grower_payment.append(data)
            except :
                if i['approval_date'] == None:
                    delivery_date = i['process_date'].strftime("%m/%d/%y")
                    new_date = i['process_date'] + timedelta(60)
                    payment_due_date = new_date.strftime("%m/%d/%y")
                    # 27-03-23
                    check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i['process_date'],to_date__gte=i['process_date'])
                    check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
                    if check_entry_with_date.exists() :
                        check_entry_id = [i.id for i in check_entry_with_date][0]
                        var = EntryFeeds.objects.get(id=check_entry_id)
                    elif check_entry_with_no_date.exists() :
                        check_entry_id = [i.id for i in check_entry_with_no_date][0]
                        var = EntryFeeds.objects.get(id = check_entry_id)
                else:
                    delivery_date = i['approval_date'].strftime("%m/%d/%y")
                    new_date = i['approval_date'] + timedelta(60)
                    payment_due_date = new_date.strftime("%m/%d/%y")
                    # 27-03-23
                    check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i['approval_date'],to_date__gte=i['approval_date'])
                    check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
                    if check_entry_with_date.exists() :
                        check_entry_id = [i.id for i in check_entry_with_date][0]
                        var = EntryFeeds.objects.get(id=check_entry_id)
                    elif check_entry_with_no_date.exists() :
                        check_entry_id = [i.id for i in check_entry_with_no_date][0]
                        var = EntryFeeds.objects.get(id = check_entry_id)

                # var = EntryFeeds.objects.get(grower_id=grower_id)
                if var.contracted_payment_option == 'Fixed Price' or  var.contracted_payment_option == 'Acreage Release' :
                    cpb_lbs = var.contract_base_price
                    sp_lbs = var.sustainability_premium
                    total_price_init = float(cpb_lbs) + float(sp_lbs)
                    total_price = total_price_init
                else:
                    calculation_date = i['approval_date']
                    if NasdaqApiData.objects.filter(date_api=calculation_date).count() !=0 :
                        total_price_init = NasdaqApiData.objects.get(date_api=calculation_date).close_value_api
                    else:
                        for l in range(1,10):
                            next_date = calculation_date - timedelta(l)
                            if NasdaqApiData.objects.filter(date_api=next_date).count() !=0 :
                                total_price_init = NasdaqApiData.objects.get(date_api=next_date).close_value_api
                                break
                    total_price2 = float(total_price_init) / 100
                    total_price = total_price2 + 0.04
                if i['received_amount'] != None :
                    delivery_lbs = int(float(i['received_amount'])) 
                    delivered_value = float(delivery_lbs) * total_price
                else:
                    delivery_lbs = int(float(i['total_amount']))
                    delivered_value = float(delivery_lbs) * total_price

                total_price = "{0:.5f}".format(total_price)
                delivered_value = "{0:.4f}".format(delivered_value)
                data = {
                    'delivery_date':delivery_date,
                    'delivery_id':delivery_id,
                    'grower_name':grower_name,
                    'crop':crop,
                    'variety':variety,
                    'field':field,
                    'delivery_lbs':delivery_lbs,
                    'classs':'-',
                    'total_price':total_price,
                    'delivered_value':delivered_value,
                    'payment_due_date':payment_due_date,
                    'payment_amount':'',
                    'payment_date':'',
                    'payment_type':'',
                    'payment_confirmation':'',
                }
                grower_payment.append(data)

        for i in  grower_payment:
          writer.writerow([i["delivery_date"],i["delivery_id"],i["grower_name"], i["crop"], i["variety"],'-', i["field"], i["delivery_lbs"],
            i["classs"], i["total_price"], i["delivered_value"],i["payment_due_date"],i["payment_amount"],i["payment_date"],i["payment_type"],
            i["payment_confirmation"]])  

        return response


@login_required()
def grower_payments_list(request):
    context = {}
    
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        entry = EntryFeeds.objects.all()
        grower_payment = []
        total_cal_grower_payment = []
        fixed_price_id = []
        fixed_price_grower_id = []
        delivery_price_id = []
        acreage_Release_price_id = []
        delivery_grower_id = []
        acreage_Release_grower_id = []
        crop_cotton_grower_id = []
        crop_rice_grower_id = []
        flag = ''
        selectedCrop = ''
        selectedGrower = ''
        total_deliverd_lbs = []
        total_cal_total_deliverd_lbs = []
        total_deliverd_values = []
        total_cal_total_deliverd_values = []
        total_cal_payment_am = []
        payment_am = []
        temp_grower_payment_start_index = 0
        temp_grower_payment_end_index = ''
        var_pagni_crop = ''
        # sorting grower_id and enteryfeed_id
        for i in entry :
            if i.contracted_payment_option == 'Fixed Price':
                fixed_price_id.append(i.id)
                fixed_price_grower_id.append(i.grower.id)
            if i.contracted_payment_option == 'Delivered Market Price':
                delivery_price_id.append(i.id)
                delivery_grower_id.append(i.grower.id)
            if i.contracted_payment_option == 'Acreage Release':
                acreage_Release_price_id.append(i.id)
                acreage_Release_grower_id.append(i.grower.id)
            if i.crop == 'COTTON' :
                crop_cotton_grower_id.append(i.grower.id)
            if i.crop == 'RICE' :
                crop_rice_grower_id.append(i.grower.id)
        total_grower_id = fixed_price_grower_id + delivery_grower_id + acreage_Release_grower_id
        growers = Grower.objects.filter(id__in = total_grower_id).order_by('name')
        context['growers'] = growers
        grower_idd = request.GET.get('grower_id')
        crop_idd = request.GET.get('crop_id')
        get_page_no_temp = request.GET.get('get_page_no_temp')
        if get_page_no_temp :
            var_get_page_no_temp = get_page_no_temp
        else :
            var_get_page_no_temp = 1
        context['var_get_page_no_temp'] =int(var_get_page_no_temp)
        # seacrh with grower 
        if grower_idd and grower_idd != 'All' :
            selectedGrower = Grower.objects.get(id=grower_idd)
            
            if int(grower_idd) in fixed_price_grower_id or int(grower_idd) in acreage_Release_grower_id :
                fixed_price_grower_id = [int(grower_idd)]
                delivery_grower_id = []
                total_grower_id = fixed_price_grower_id + delivery_grower_id
                selectedCrop = ''
            elif int(grower_idd) in delivery_grower_id :
                delivery_grower_id = [int(grower_idd)]
                fixed_price_grower_id = []
                total_grower_id = fixed_price_grower_id + delivery_grower_id
                selectedCrop = ''

        elif grower_idd == 'All' :
            get_page_no_temp = 1
        # seacrh with crop 
        elif crop_idd and crop_idd != 'All' :
            if crop_idd == "COTTON":
                # crop_cotton_grower_id
                fixed_price_grower_id = crop_cotton_grower_id
                delivery_grower_id = []
                total_grower_id = fixed_price_grower_id + delivery_grower_id
                selectedGrower = ''
                selectedCrop = "COTTON"
        
            elif crop_idd == "RICE":
                # crop_rice_grower_id
                delivery_grower_id = crop_rice_grower_id
                fixed_price_grower_id = []
                total_grower_id = fixed_price_grower_id + delivery_grower_id
                selectedCrop = "RICE"
                selectedGrower = ''
            context['var_pagni_crop'] = crop_idd
            if get_page_no_temp :
                get_page_no_temp = get_page_no_temp
            else:
                get_page_no_temp = 1
        elif crop_idd and crop_idd == 'All' :
            get_page_no_temp = 1
        # seacrh with grower and crop .........
        elif crop_idd and crop_idd != 'All' and grower_idd and grower_idd != 'All' :
            selectedGrower = Grower.objects.get(id=grower_idd)
            selectedCrop = crop_idd
            total_grower_id = []
            var = EntryFeeds.objects.get(grower_id = grower_idd)
            selectedGrowerCrop = var.crop
            if selectedGrowerCrop == 'COTTON' :
                if int(grower_idd) in fixed_price_grower_id and selectedCrop == 'COTTON' :
                    fixed_price_grower_id = [int(grower_idd)]
                    delivery_grower_id = []
                    total_grower_id = fixed_price_grower_id + delivery_grower_id
                else:
                    fixed_price_grower_id = []
                    delivery_grower_id = []
                    total_grower_id = fixed_price_grower_id + delivery_grower_id
            elif selectedGrowerCrop == 'RICE' :
                if int(grower_idd) in fixed_price_grower_id and selectedCrop == 'RICE' :
                    fixed_price_grower_id = [int(grower_idd)]
                    delivery_grower_id = []
                    total_grower_id = fixed_price_grower_id + delivery_grower_id
                elif int(grower_idd) in delivery_grower_id and selectedCrop == 'RICE' :
                    delivery_grower_id = [int(grower_idd)]
                    fixed_price_grower_id = []
                    total_grower_id = fixed_price_grower_id + delivery_grower_id
            else :
                fixed_price_grower_id = []
                delivery_grower_id = []
                total_grower_id = fixed_price_grower_id + delivery_grower_id
        else:
            entry = entry
            grower_payment = grower_payment
            fixed_price_id = fixed_price_id
            fixed_price_grower_id = fixed_price_grower_id
            delivery_price_id = delivery_price_id
            delivery_grower_id = delivery_grower_id
        # custom pagination code 
        pagi_bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id).exclude(level='None')
        pagi_grower_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED')
        total_obj_qury = len(pagi_bale) + len(pagi_grower_shipment)
        tem_total_no_page = total_obj_qury // 100 

        if get_page_no_temp :
            if int(get_page_no_temp) == 1 :
                page_lower_limit, page_upper_limit = 0, 100
                temp_grower_payment_start_index, temp_grower_payment_end_index = page_lower_limit, page_upper_limit
            elif int(get_page_no_temp) == int(tem_total_no_page) :
                page_lower_limit, page_upper_limit = int(get_page_no_temp) * 100 , (int(get_page_no_temp) + 1) * 100
                temp_grower_payment_start_index, temp_grower_payment_end_index = page_lower_limit, total_obj_qury
            else :
                page_lower_limit, page_upper_limit = int(get_page_no_temp) * 100 , (int(get_page_no_temp) + 1) * 100
                temp_grower_payment_start_index, temp_grower_payment_end_index = page_lower_limit, page_upper_limit

        if crop_idd and crop_idd != 'All' :
            
            if int(get_page_no_temp) == 1 :
                page_lower_limit, page_upper_limit = 0, 100
                temp_grower_payment_start_index, temp_grower_payment_end_index = page_lower_limit, page_upper_limit
            elif int(get_page_no_temp) == int(tem_total_no_page) :
                page_lower_limit, page_upper_limit = int(get_page_no_temp) * 100 , (int(get_page_no_temp) + 1) * 100
                temp_grower_payment_start_index, temp_grower_payment_end_index = page_lower_limit, total_obj_qury
            else :
                page_lower_limit, page_upper_limit = int(get_page_no_temp) * 100 , (int(get_page_no_temp) + 1) * 100
                temp_grower_payment_start_index, temp_grower_payment_end_index = page_lower_limit, page_upper_limit

        context['temp_grower_payment_start_index'] = int(temp_grower_payment_start_index) + 1
        context['temp_grower_payment_end_index'] = temp_grower_payment_end_index

        # Fixed Market Price ..................
        if get_page_no_temp :
            bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id).exclude(level='None')[int(page_lower_limit):int(page_upper_limit)]
        elif crop_idd and crop_idd != 'All' :
            bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id).exclude(level='None')[int(page_lower_limit):int(page_upper_limit)]
        else :
            bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id).exclude(level='None')

        if bale.exists() :
            context['crop_check'] = 'COTTON'
        qp_lbs = 0.00
        for i in bale :
            delivery_date = i.dt_class
            delivery_id = i.bale_id
            grower_name = i.ob3
            crop = "COTTON"
            # field = i.field_name
            field = i.field_name
            delivery_lbs = i.net_wt
            # processor = i.classing.processor.entity_name
            classs = i.level
            payment_amount = ''
            payment_date = ''
            payment_type = ''
            payment_confirmation = ''
            payment_add = 'add'
            # 27-03-23
            if delivery_date :
                str_date = str(delivery_date)
                if '-' in str_date :
                    try :
                        str_date = str_date.split('-')
                        mm = str_date[0]
                        dd = str_date[1]
                        yy = str_date[2]
                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                        finale_date = date(int(yyyy), int(mm), int(dd))
                    except :
                        continue
                elif '/' in str_date :
                    try :
                        str_date = str_date.split('/')
                        mm = str_date[0]
                        dd = str_date[1]
                        yy = str_date[2]
                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                        finale_date = date(int(yyyy), int(mm), int(dd))
                    except :
                        continue
                else:
                    finale_date = ''
            else:
                continue
            # 27-03-23
            check_entry = EntryFeeds.objects.filter(grower_id = i.ob2)
            if len(check_entry) == 0 :
                continue
            if len(check_entry) == 1 :
                var = EntryFeeds.objects.get(grower_id = i.ob2)
            if len(check_entry) > 1 :
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = i.ob2,from_date__lte=finale_date,to_date__gte=finale_date)
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = i.ob2,from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)
                elif check_entry_with_no_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)

            # var = EntryFeeds.objects.get(grower_id = i.ob2)
            cpb_lbs = var.contract_base_price
            if cpb_lbs :
                cpb_lbs = var.contract_base_price
            else:
                cpb_lbs = 0.0
            sp_lbs = var.sustainability_premium
            if sp_lbs :
                sp_lbs = var.sustainability_premium
            else:
                sp_lbs = 0.0
            
            if classs == 'Bronze' :
                qp_lbs = 0.00
            elif classs == "Silver":
                qp_lbs = 0.02
            elif classs == "Gold":
                qp_lbs = 0.04
            elif classs == "None":
                qp_lbs = 0.00
                                    
            if classs != "None":
                total_price = float(cpb_lbs) + float(sp_lbs) + float(qp_lbs)
                delivered_value = float(delivery_lbs) * float(total_price)
                if delivery_date :
                    date_str = str(delivery_date).split("/")
                    dd = int(date_str[1])
                    mm = int(date_str[0])
                    yy = int(date_str[2])
                    if len(str(yy)) == 2 : 
                        yyyy = int("20{}".format(yy))
                    else:
                        yyyy = yy
                    specific_date = datetime(yyyy, mm, dd)
                    new_date = specific_date + timedelta(60)
                    payment_due_date = new_date.strftime("%m/%d/%y")
                else:
                    payment_due_date ="N/A"
            else:
                total_price = 0.00
                delivered_value = 0.00
                payment_due_date ="N/A"

            gpay = GrowerPayments.objects.filter(delivery_id=delivery_id)
            if gpay.exists() :
                get_gpay = GrowerPayments.objects.get(delivery_id=delivery_id)
                payment_amount = get_gpay.payment_amount
                payment_date = get_gpay.payment_date
                payment_type = get_gpay.payment_type
                payment_confirmation = get_gpay.payment_confirmation
                payment_add = ''
                try:
                    total_price = float(get_gpay.total_price)
                    delivered_value = float(get_gpay.delivered_value)
                except:
                    pass
                payment_am.append(int(float(payment_amount)))
            else:
                payment_amount = ''
                payment_date = ''
                payment_type = ''
                payment_confirmation = ''
                payment_add = 'add'
            total_deliverd_lbs.append(int(float(delivery_lbs)))
            total_deliverd_values.append(float(delivered_value))

            data = {
                    'delivery_date':delivery_date,
                    'delivery_id':delivery_id,
                    'grower_name':grower_name,
                    'crop':crop,
                    'variety':"-",
                    'field':field,
                    'delivery_lbs':delivery_lbs,
                    # 'processor':processor,
                    'class':classs,
                    # 'cpb_lbs':cpb_lbs,
                    # 'sp_lbs':sp_lbs,
                    # 'qp_lbs':qp_lbs,
                    'total_price':"{0:.5f}".format(total_price),
                    'delivered_value':"{0:.4f}".format(delivered_value),
                    'payment_due_date':payment_due_date,
                    'payment_amount':payment_amount,
                    'payment_date':payment_date,
                    'payment_type':payment_type,
                    'payment_confirmation':payment_confirmation,
                    'id':i.id,
                    'var':"BaleReportFarmField",
                    'payment_add':payment_add,
                }
            grower_payment.append(data)

        # For Delivery Market ...........
        if get_page_no_temp :
            grower_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED')[int(page_lower_limit):int(page_upper_limit)]
        elif crop_idd and crop_idd != 'All' :
            grower_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED')[int(page_lower_limit):int(page_upper_limit)]
        else :
            grower_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED')
        
        for i in grower_shipment :
            delivery_id = i.shipment_id
            grower_name = i.grower.name
            grower_id = i.grower.id
            crop = i.crop
            variety = i.variety
            field = i.field.name
            
            if i.approval_date == None:
                process_date_int = i.process_date.strftime("%m/%d/%y")
                delivery_date = process_date_int
                new_date = i.process_date + timedelta(60)
                payment_due_date = new_date.strftime("%m/%d/%y")
                # 27-03-23
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i.process_date,to_date__gte=i.process_date)
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id=check_entry_id)
                elif check_entry_with_no_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)
            else:
                process_date_int = i.approval_date.strftime("%m/%d/%y")
                delivery_date = process_date_int
                new_date = i.approval_date + timedelta(60)
                payment_due_date = new_date.strftime("%m/%d/%y")
                # 27-03-23
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i.approval_date,to_date__gte=i.approval_date)
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id=check_entry_id)
                elif check_entry_with_no_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)

            # var = EntryFeeds.objects.get(grower_id=grower_id)
            if var.contracted_payment_option == 'Fixed Price' :
                cpb_lbs = var.contract_base_price
                sp_lbs = var.sustainability_premium
                total_price_init = float(cpb_lbs) + float(sp_lbs)
                total_price = total_price_init
            elif var.contracted_payment_option == 'Acreage Release' :
                cpb_lbs = var.contract_base_price
                sp_lbs = var.sustainability_premium
                total_price_init = float(cpb_lbs) + float(sp_lbs)
                total_price = total_price_init
            else:
                calculation_date = i.approval_date
                if NasdaqApiData.objects.filter(date_api=calculation_date).count() !=0 :
                    total_price_init = NasdaqApiData.objects.get(date_api=calculation_date).close_value_api
                else:
                    for l in range(1,10):
                        next_date = calculation_date - timedelta(l)
                        if NasdaqApiData.objects.filter(date_api=next_date).count() !=0 :
                            total_price_init = NasdaqApiData.objects.get(date_api=next_date).close_value_api
                            break
                total_price2 = float(total_price_init) / 100
                total_price = total_price2 + 0.04
            if i.received_amount != None :
                delivery_lbs = int(float(i.received_amount)) 
                delivered_value = float(delivery_lbs) * total_price
            else:
                delivery_lbs = int(float(i.total_amount))
                delivered_value = float(delivery_lbs) * total_price

            
            gpay = GrowerPayments.objects.filter(delivery_id=delivery_id)
            if gpay.exists() :
                get_gpay = GrowerPayments.objects.get(delivery_id=delivery_id)
                payment_amount = get_gpay.payment_amount
                payment_date = get_gpay.payment_date
                payment_type = get_gpay.payment_type
                payment_confirmation = get_gpay.payment_confirmation
                payment_add = ''
                # try:
                #     total_price = float(get_gpay.total_price)
                #     delivered_value = float(get_gpay.delivered_value)
                # except:
                #     pass
                payment_am.append(int(float(payment_amount)))
            else:
                payment_amount = ''
                payment_date = ''
                payment_type = ''
                payment_confirmation = ''
                payment_add = 'add'
            total_deliverd_lbs.append(int(float(delivery_lbs)))
            total_deliverd_values.append(float(delivered_value))
            total_price = "{0:.5f}".format(total_price)
            delivered_value = "{0:.4f}".format(delivered_value)
            # new_date = i.date_time + timedelta(60)
            # payment_due_date = new_date.strftime("%m/%d/%y")
            data = {
                'delivery_date':delivery_date,
                'delivery_id':delivery_id,
                'grower_name':grower_name,
                'crop':crop,
                'variety':variety,
                'field':field,
                'delivery_lbs':delivery_lbs,
                # 'processor':processor,
                'class':'-',
                # 'cpb_lbs':'-',
                # 'sp_lbs':'-',
                # 'qp_lbs':'-',
                'total_price':total_price,
                'delivered_value':delivered_value,
                'payment_due_date':payment_due_date,
                'payment_amount':payment_amount,
                'payment_date':payment_date,
                'payment_type':payment_type,
                'payment_confirmation':payment_confirmation,
                'id':i.id,
                'var':"GrowerShipment",
                "payment_add":payment_add,
            }
            grower_payment.append(data)

        total_deliverd_lbs = sum(total_deliverd_lbs)
        count = len(grower_payment)
        total_deliverd_values = sum(total_deliverd_values)
        paid_amount = sum(payment_am)
        amount_open_for_payments = total_deliverd_values - paid_amount

        context['selectedGrower'] = selectedGrower
        context['selectedCrop'] = selectedCrop
        

        context['range'] = range(tem_total_no_page)
        context['temp_grower_payment_count'] = total_obj_qury
      
        context['grower_payment'] = grower_payment
        # context['total_deliverd_lbs'] = total_deliverd_lbs
        # context['count'] = count
        # context['total_deliverd_values'] = "${0:.2f} USD".format(total_deliverd_values)
        # context['paid_amount'] = "${0:.2f} USD".format(paid_amount)
        # context['amount_open_for_payments'] = "${0:.2f} USD".format(amount_open_for_payments) 
        # context['netamount_open_for_payments'] = int(amount_open_for_payments)
            

        return render(request, "growerpayments/grower_payments_list.html",context)
    # For Grower Payment View ......
    if 'Grower' in request.user.get_role() and not request.user.is_superuser:
        grower_id= request.user.grower.id 
        total_grower_id = [grower_id]
        if EntryFeeds.objects.filter(grower_id=grower_id).count() > 0:
            # Fixed Market Price ..................
            total_deliverd_lbs = []
            total_deliverd_values = []
            grower_payment = []
            payment_am = []
            bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id).exclude(level='None')
            for i in bale :
                delivery_date = i.dt_class
                delivery_id = i.bale_id
                grower_name = i.ob3
                crop = "COTTON"
                # field = i.field_name
                field = i.field_name
                delivery_lbs = i.net_wt
                # processor = i.classing.processor.entity_name
                classs = i.level
                # 04-04-23
                payment_amount = ''
                payment_date = ''
                payment_type = ''
                payment_confirmation = ''
                payment_add = 'add'
                if delivery_date :
                    str_date = str(delivery_date)
                    if '-' in str_date :
                        try :
                            str_date = str_date.split('-')
                            mm = str_date[0]
                            dd = str_date[1]
                            yy = str_date[2]
                            yyyy = f'20{yy}' if len(yy) == 2 else yy
                            finale_date = date(int(yyyy), int(mm), int(dd))
                        except :
                            continue
                    elif '/' in str_date :
                        try :
                            str_date = str_date.split('/')
                            mm = str_date[0]
                            dd = str_date[1]
                            yy = str_date[2]
                            yyyy = f'20{yy}' if len(yy) == 2 else yy
                            finale_date = date(int(yyyy), int(mm), int(dd))
                        except :
                            continue
                    else:
                        finale_date = ''
                else:
                    continue
                # 27-03-23
                check_entry = EntryFeeds.objects.filter(grower_id = i.ob2)
                if len(check_entry) == 0 :
                    continue
                if len(check_entry) == 1 :
                    var = EntryFeeds.objects.get(grower_id = i.ob2)
                if len(check_entry) > 1 :
                    check_entry_with_date = EntryFeeds.objects.filter(grower_id = i.ob2,from_date__lte=finale_date,to_date__gte=finale_date)
                    check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = i.ob2,from_date__isnull=True,to_date__isnull=True)
                    if check_entry_with_date.exists() :
                        check_entry_id = [i.id for i in check_entry_with_date][0]
                        var = EntryFeeds.objects.get(id = check_entry_id)
                    elif check_entry_with_no_date.exists() :
                        check_entry_id = [i.id for i in check_entry_with_no_date][0]
                        var = EntryFeeds.objects.get(id = check_entry_id)
                # var = EntryFeeds.objects.get(grower_id = i.ob2)
                cpb_lbs = var.contract_base_price
                if cpb_lbs :
                    cpb_lbs = var.contract_base_price
                else:
                    cpb_lbs = 0.0
                sp_lbs = var.sustainability_premium
                if sp_lbs :
                    sp_lbs = var.sustainability_premium
                else:
                    sp_lbs = 0.0
                if classs == 'Bronze' :
                    qp_lbs = 0.00
                elif classs == "Silver":
                    qp_lbs = 0.02
                elif classs == "Gold":
                    qp_lbs = 0.04
                elif classs == "None":
                    qp_lbs = 0.00
                                        
                if classs != "None":
                    total_price = float(cpb_lbs) + float(sp_lbs) + float(qp_lbs)
                    delivered_value = float(delivery_lbs) * float(total_price)
                    if delivery_date :
                        date_str = str(delivery_date).split("/")
                        dd = int(date_str[1])
                        mm = int(date_str[0])
                        yy = int(date_str[2])
                        if len(str(yy)) == 2 : 
                            yyyy = int("20{}".format(yy))
                        else:
                            yyyy = yy
                        specific_date = datetime(yyyy, mm, dd)
                        new_date = specific_date + timedelta(60)
                        payment_due_date = new_date.strftime("%m/%d/%y")
                    else:
                        payment_due_date ="N/A"
                else:
                    total_price = 0.00
                    delivered_value = 0.00
                    payment_due_date ="N/A"
                gpay = GrowerPayments.objects.filter(delivery_id=delivery_id)
                if gpay.exists() :
                    get_gpay = GrowerPayments.objects.get(delivery_id=delivery_id)
                    payment_amount = get_gpay.payment_amount
                    payment_date = get_gpay.payment_date
                    payment_type = get_gpay.payment_type
                    payment_confirmation = get_gpay.payment_confirmation
                    payment_add = ''
                    try:
                        total_price = float(get_gpay.total_price)
                        delivered_value = float(get_gpay.delivered_value)
                    except:
                        pass
                    payment_am.append(int(float(payment_amount)))
                else:
                    payment_amount = ''
                    payment_date = ''
                    payment_type = ''
                    payment_confirmation = ''
                    payment_add = 'add'
                total_deliverd_lbs.append(int(float(delivery_lbs)))
                total_deliverd_values.append(float(delivered_value))
                data = {
                        'delivery_date':delivery_date,
                        'delivery_id':delivery_id,
                        'grower_name':grower_name,
                        'crop':crop,
                        'variety':"-",
                        'field':field,
                        'delivery_lbs':delivery_lbs,
                        # 'processor':processor,
                        'class':classs,
                        # 'cpb_lbs':cpb_lbs,
                        # 'sp_lbs':sp_lbs,
                        # 'qp_lbs':qp_lbs,
                        'total_price':"{0:.5f}".format(total_price),
                        'delivered_value':"{0:.4f}".format(delivered_value),
                        'payment_due_date':payment_due_date,
                        'payment_amount':payment_amount,
                        'payment_date':payment_date,
                        'payment_type':payment_type,
                        'payment_confirmation':payment_confirmation,
                        'id':i.id,
                        'var':"BaleReportFarmField",
                        'payment_add':payment_add,
                    }
                grower_payment.append(data)

            # For Delivery Market ...........
            grower_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED') 
            for i in grower_shipment :
                delivery_id = i.shipment_id
                grower_name = i.grower.name
                grower_id = i.grower.id
                crop = i.crop
                variety = i.variety
                field = i.field.name
                if i.approval_date == None:
                    process_date_int = i.process_date.strftime("%m/%d/%y")
                    delivery_date = process_date_int
                    new_date = i.process_date + timedelta(60)
                    payment_due_date = new_date.strftime("%m/%d/%y")
                    # 27-03-23
                    check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i.process_date,to_date__gte=i.process_date)
                    check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
                    if check_entry_with_date.exists() :
                        check_entry_id = [i.id for i in check_entry_with_date][0]
                        var = EntryFeeds.objects.get(id=check_entry_id)
                    elif check_entry_with_no_date.exists() :
                        check_entry_id = [i.id for i in check_entry_with_no_date][0]
                        var = EntryFeeds.objects.get(id = check_entry_id)
                else:
                    process_date_int = i.approval_date.strftime("%m/%d/%y")
                    delivery_date = process_date_int
                    new_date = i.approval_date + timedelta(60)
                    payment_due_date = new_date.strftime("%m/%d/%y")
                    # 27-03-23
                    check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i.approval_date,to_date__gte=i.approval_date)
                    check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
                    if check_entry_with_date.exists() :
                        check_entry_id = [i.id for i in check_entry_with_date][0]
                        var = EntryFeeds.objects.get(id=check_entry_id)
                    elif check_entry_with_no_date.exists() :
                        check_entry_id = [i.id for i in check_entry_with_no_date][0]
                        var = EntryFeeds.objects.get(id = check_entry_id)
                
                # var = EntryFeeds.objects.get(grower_id=grower_id)
                if var.contracted_payment_option == 'Fixed Price' :
                    cpb_lbs = var.contract_base_price
                    sp_lbs = var.sustainability_premium
                    total_price_init = float(cpb_lbs) + float(sp_lbs)
                    total_price = total_price_init
                elif var.contracted_payment_option == 'Acreage Release' :
                    cpb_lbs = var.contract_base_price
                    sp_lbs = var.sustainability_premium
                    total_price_init = float(cpb_lbs) + float(sp_lbs)
                    total_price = total_price_init
                else:
                    calculation_date = i.approval_date
                    if NasdaqApiData.objects.filter(date_api=calculation_date).count() !=0 :
                        total_price_init = NasdaqApiData.objects.get(date_api=calculation_date).close_value_api
                    else:
                        for l in range(1,10):
                            next_date = calculation_date - timedelta(l)
                            if NasdaqApiData.objects.filter(date_api=next_date).count() !=0 :
                                total_price_init = NasdaqApiData.objects.get(date_api=next_date).close_value_api
                                break
                    total_price2 = float(total_price_init) / 100
                    total_price = total_price2 + 0.04
                if i.received_amount != None :
                    delivery_lbs = int(float(i.received_amount)) 
                    delivered_value = float(delivery_lbs) * total_price
                else:
                    delivery_lbs = int(float(i.total_amount))
                    delivered_value = float(delivery_lbs) * total_price
                # total_deliverd_lbs.append(int(float(delivery_lbs)))
                # total_deliverd_values.append(float(delivered_value))
                # processor = i.processor.entity_name
                # total_price = "{0:.5f}".format(total_price)
                # delivered_value = "{0:.4f}".format(delivered_value)
                # new_date = i.date_time + timedelta(60)
                # payment_due_date = new_date.strftime("%m/%d/%y")
                gpay = GrowerPayments.objects.filter(delivery_id=delivery_id)
                if gpay.exists() :
                    get_gpay = GrowerPayments.objects.get(delivery_id=delivery_id)
                    payment_amount = get_gpay.payment_amount
                    payment_date = get_gpay.payment_date
                    payment_type = get_gpay.payment_type
                    payment_confirmation = get_gpay.payment_confirmation
                    payment_add = ''
                    # try:
                    #     total_price = float(get_gpay.total_price)
                    #     delivered_value = float(get_gpay.delivered_value)
                    # except:
                    #     pass
                    payment_am.append(int(float(payment_amount)))
                else:
                    payment_amount = ''
                    payment_date = ''
                    payment_type = ''
                    payment_confirmation = ''
                    payment_add = 'add'
                total_deliverd_lbs.append(int(float(delivery_lbs)))
                total_deliverd_values.append(float(delivered_value))
                total_price = "{0:.5f}".format(total_price)
                delivered_value = "{0:.4f}".format(delivered_value)
                # new_date = i.date_time + timedelta(60)
                # payment_due_date = new_date.strftime("%m/%d/%y")
                data = {
                    'delivery_date':delivery_date,
                    'delivery_id':delivery_id,
                    'grower_name':grower_name,
                    'crop':crop,
                    'variety':variety,
                    'field':field,
                    'delivery_lbs':delivery_lbs,
                    # 'processor':processor,
                    'class':'-',
                    # 'cpb_lbs':'-',
                    # 'sp_lbs':'-',
                    # 'qp_lbs':'-',
                    'total_price':total_price,
                    'delivered_value':delivered_value,
                    'payment_due_date':payment_due_date,
                    'payment_amount':payment_amount,
                    'payment_date':payment_date,
                    'payment_type':payment_type,
                    'payment_confirmation':payment_confirmation,
                    'id':i.id,
                    'var':"GrowerShipment",
                    "payment_add":payment_add,
                }
                grower_payment.append(data)

            total_deliverd_lbs = sum(total_deliverd_lbs)
            count = len(grower_payment)
            total_deliverd_values = sum(total_deliverd_values)
            paid_amount = sum(payment_am)
            amount_open_for_payments = total_deliverd_values - paid_amount
            context['grower_payment'] = grower_payment
            context['total_deliverd_lbs'] = total_deliverd_lbs
            context['count'] = count
            context['total_deliverd_values'] = "$ {0:.2f} USD".format(total_deliverd_values)
            context['paid_amount'] = paid_amount 
            context['amount_open_for_payments'] = "$ {0:.2f} USD".format(amount_open_for_payments)
            context['netamount_open_for_payments'] = int(amount_open_for_payments)

            context['temp_grower_payment_count'] = count
            context['temp_grower_payment_start_index'] = 1
            context['temp_grower_payment_end_index'] = count

            return render(request, "growerpayments/grower_payments_list.html",context)
        else:
            return redirect('/')
        
    else:
        return redirect('/')    

def ajax_grower_payments_list(request,grower_id,crop_id):

    entry = EntryFeeds.objects.all()
    fixed_price_grower_id =[]
    delivery_grower_id =[]
    fixed_price_id = []
    fixed_price_grower_id = []
    delivery_price_id = []
    delivery_grower_id = []
    crop_cotton_grower_id = []
    crop_rice_grower_id = []
    total_cal_payment_am = []
    total_cal_total_deliverd_lbs = []
    total_cal_total_deliverd_values = []
    for i in entry :
        if i.contracted_payment_option == 'Fixed Price':
            fixed_price_id.append(i.id)
            fixed_price_grower_id.append(i.grower.id)
        if i.contracted_payment_option == 'Delivered Market Price':
            delivery_price_id.append(i.id)
            delivery_grower_id.append(i.grower.id)
        if i.crop == 'COTTON' :
            crop_cotton_grower_id.append(i.grower.id)
        if i.crop == 'RICE' :
            crop_rice_grower_id.append(i.grower.id)

    if grower_id == 'grower' :
        total_grower_id = [crop_id]

    elif grower_id == 'crop' :
        if crop_id == "COTTON":
            # crop_cotton_grower_id
            fixed_price_grower_id = crop_cotton_grower_id
            delivery_grower_id = []
            total_grower_id = fixed_price_grower_id + delivery_grower_id
            # selectedGrower = ''
            # selectedCrop = "COTTON"
    
        elif crop_id == "RICE":
            # crop_rice_grower_id
            delivery_grower_id = crop_rice_grower_id
            fixed_price_grower_id = []
            total_grower_id = fixed_price_grower_id + delivery_grower_id
            # selectedCrop = "RICE"
            # selectedGrower = ''
    elif grower_id == 'All' and crop_id == 'All' :

        # entry = EntryFeeds.objects.all()
        # fixed_price_grower_id =[]
        # delivery_grower_id =[]
        # total_cal_payment_am =[]
        # total_cal_total_deliverd_lbs =[]
        # total_cal_total_deliverd_values =[]
        # for i in entry :
        #     if i.contracted_payment_option == 'Fixed Price':
        #         fixed_price_grower_id.append(i.grower.id)
        #     if i.contracted_payment_option == 'Delivered Market Price':
        #         delivery_grower_id.append(i.grower.id)
        total_grower_id = fixed_price_grower_id + delivery_grower_id
    cal_bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id).exclude(level='None').values('bale_id','net_wt','dt_class','level','ob2')
    count_cal_bale = cal_bale.count()
    qp_lbs = 0.00
    for i in cal_bale :
        delivery_date = i['dt_class']
        delivery_lbs = i['net_wt']
        delivery_id = i['bale_id']
        classs = i['level']
        # 27-03-23
        if delivery_date :
            str_date = str(delivery_date)
            if '-' in str_date :
                try :
                    str_date = str_date.split('-')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = date(int(yyyy), int(mm), int(dd))
                except :
                    continue
            elif '/' in str_date :
                try :
                    str_date = str_date.split('/')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = date(int(yyyy), int(mm), int(dd))
                except :
                    continue
            else:
                finale_date = ''
        else:
            continue
        # 27-03-23
        check_entry = EntryFeeds.objects.filter(grower_id = i["ob2"])
        if len(check_entry) == 0 :
            continue
        if len(check_entry) == 1 :
            var = EntryFeeds.objects.get(grower_id = i["ob2"])
        if len(check_entry) > 1 :
            check_entry_with_date = EntryFeeds.objects.filter(grower_id = i["ob2"],from_date__lte=finale_date,to_date__gte=finale_date)
            check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = i["ob2"],from_date__isnull=True,to_date__isnull=True)
            if check_entry_with_date.exists() :
                check_entry_id = [i.id for i in check_entry_with_date][0]
                var = EntryFeeds.objects.get(id = check_entry_id)
            elif check_entry_with_no_date.exists() :
                check_entry_id = [i.id for i in check_entry_with_no_date][0]
                var = EntryFeeds.objects.get(id = check_entry_id)

        # var = EntryFeeds.objects.get(grower_id = i['ob2'])
        cpb_lbs = var.contract_base_price
        if cpb_lbs :
            cpb_lbs = var.contract_base_price
        else:
            cpb_lbs = 0.00
        
        sp_lbs = var.sustainability_premium
        if sp_lbs :
            sp_lbs = var.sustainability_premium
        else:
            sp_lbs = 0.00

        if classs == 'Bronze' :
            qp_lbs = 0.00
        elif classs == "Silver":
            qp_lbs = 0.02
        elif classs == "Gold":
            qp_lbs = 0.04
        elif classs == "None":
            qp_lbs = 0.00
                                
        if classs != "None":
            total_price = float(cpb_lbs) + float(sp_lbs) + float(qp_lbs)
            delivered_value = float(delivery_lbs) * float(total_price)
        else:
            total_price = 0.00
            delivered_value = 0.00
            payment_due_date ="N/A"
        gpay = GrowerPayments.objects.filter(delivery_id=delivery_id)
        if gpay.exists() :
            get_gpay = GrowerPayments.objects.get(delivery_id=delivery_id)
            payment_amount = get_gpay.payment_amount
            total_cal_payment_am.append(int(float(payment_amount)))
        else:
            pass
            
        total_cal_total_deliverd_lbs.append(int(float(delivery_lbs)))
        total_cal_total_deliverd_values.append(float(delivered_value))
        
    cal_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED').values('shipment_id','grower_id','received_amount','process_date','approval_date')
    count_cal_shipment = cal_shipment.count()
    
    for i in cal_shipment :
        if i['approval_date'] == None:
            process_date_int = i['process_date'].strftime("%m/%d/%y")
            delivery_date = process_date_int
            new_date = i['process_date'].process_date + timedelta(60)
            payment_due_date = new_date.strftime("%m/%d/%y")
            # 27-03-23
            check_entry_with_date = EntryFeeds.objects.filter(grower_id = i['grower_id'],from_date__lte=i['process_date'],to_date__gte=i['process_date'])
            check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = i['grower_id'],from_date__isnull=True,to_date__isnull=True)
            if check_entry_with_date.exists() :
                check_entry_id = [i.id for i in check_entry_with_date][0]
                var = EntryFeeds.objects.get(id=check_entry_id)
            elif check_entry_with_no_date.exists() :
                check_entry_id = [i.id for i in check_entry_with_no_date][0]
                var = EntryFeeds.objects.get(id = check_entry_id)

        else:
            process_date_int = i['approval_date'].strftime("%m/%d/%y")
            delivery_date = process_date_int
            new_date = i['approval_date'] + timedelta(60)
            payment_due_date = new_date.strftime("%m/%d/%y")
            # 27-03-23
            check_entry_with_date = EntryFeeds.objects.filter(grower_id = i['grower_id'],from_date__lte=i['approval_date'],to_date__gte=i['approval_date'])
            check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = i['grower_id'],from_date__isnull=True,to_date__isnull=True)
            if check_entry_with_date.exists() :
                check_entry_id = [i.id for i in check_entry_with_date][0]
                var = EntryFeeds.objects.get(id=check_entry_id)
            elif check_entry_with_no_date.exists() :
                check_entry_id = [i.id for i in check_entry_with_no_date][0]
                var = EntryFeeds.objects.get(id = check_entry_id)

        delivery_id = i['shipment_id']
        grower_id = i['grower_id']
        # var = EntryFeeds.objects.get(grower_id=grower_id)
        if var.contracted_payment_option == 'Fixed Price' :
            cpb_lbs = var.contract_base_price
            sp_lbs = var.sustainability_premium
            total_price_init = float(cpb_lbs) + float(sp_lbs)
            total_price = total_price_init
        elif var.contracted_payment_option == 'Acreage Release' :
            cpb_lbs = var.contract_base_price
            sp_lbs = var.sustainability_premium
            total_price_init = float(cpb_lbs) + float(sp_lbs)
            total_price = total_price_init
        else:
            calculation_date = i['approval_date']
            if NasdaqApiData.objects.filter(date_api=calculation_date).count() !=0 :
                total_price_init = NasdaqApiData.objects.get(date_api=calculation_date).close_value_api
            else:
                for l in range(1,10):
                    next_date = calculation_date - timedelta(l)
                    if NasdaqApiData.objects.filter(date_api=next_date).count() !=0 :
                        total_price_init = NasdaqApiData.objects.get(date_api=next_date).close_value_api
                        break
            total_price2 = float(total_price_init) / 100
            total_price = total_price2 + 0.04
        if i['received_amount'] != None :
            delivery_lbs = int(float(i['received_amount'])) 
            delivered_value = float(delivery_lbs) * total_price
        else:
            delivery_lbs = int(float(i['total_amount']))
            delivered_value = float(delivery_lbs) * total_price
        total_cal_total_deliverd_lbs.append(int(float(delivery_lbs)))
        total_cal_total_deliverd_values.append(float(delivered_value))
        
        gpay = GrowerPayments.objects.filter(delivery_id=delivery_id)
        if gpay.exists() :
            get_gpay = GrowerPayments.objects.get(delivery_id=delivery_id)
            payment_amount = get_gpay.payment_amount
            total_cal_payment_am.append(int(float(payment_amount)))
        else:
            pass
    
    total_cal_total_deliverd_lbs = sum(total_cal_total_deliverd_lbs)
    total_cal_count = count_cal_bale + count_cal_shipment
    total_cal_total_deliverd_values = sum(total_cal_total_deliverd_values)
    total_cal_paid_amount = sum(total_cal_payment_am)
    total_cal_amount_open_for_payments = total_cal_total_deliverd_values - total_cal_paid_amount
    data = {
        "total_cal_total_deliverd_lbs" : total_cal_total_deliverd_lbs,
        "total_cal_count" : total_cal_count,
        "total_cal_total_deliverd_values" : "{0:.4f}".format(total_cal_total_deliverd_values),
        "total_cal_paid_amount" : "{0:.4f}".format(total_cal_paid_amount),
        "total_cal_amount_open_for_payments" : "{0:.4f}".format(total_cal_amount_open_for_payments),
        "netamount_open_for_payments" : int(total_cal_amount_open_for_payments),
    }
    
    # context['total_cal_total_deliverd_lbs'] = total_cal_total_deliverd_lbs
    # context['total_cal_count'] = total_cal_count
    # context['total_cal_total_deliverd_values'] = "${0:.2f} USD".format(total_cal_total_deliverd_values)
    # context['total_cal_paid_amount'] = "${0:.2f} USD".format(total_cal_paid_amount)
    # context['total_cal_amount_open_for_payments'] = "${0:.2f} USD".format(total_cal_amount_open_for_payments) 
    # context['total_cal_netamount_open_for_payments'] = int(total_cal_amount_open_for_payments)
    # context['static_total'] = "static_total"
    
    return JsonResponse(data)

@login_required()
def grower_payments_add(request,var,pk):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        if var == 'GrowerShipment':
            lst = []
            bale = GrowerShipment.objects.get(id=pk)
            field_name = bale.field.name
            grower_name = bale.grower.name
            farm_name = bale.field.farm.name
            farm = bale.field.farm.id
            variety = bale.variety
            if bale.approval_date == None:
                process_date_int = bale.process_date.strftime("%m/%d/%y")
                delivery_date = process_date_int
                process_date_raw= bale.process_date
                # 28-03-23
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = bale.grower.id,from_date__lte=bale.process_date,to_date__gte=bale.process_date,crop='RICE')
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = bale.grower.id,from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id=check_entry_id)
                    contracted_payment_option = var.contracted_payment_option
                elif check_entry_with_no_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)
                    contracted_payment_option = var.contracted_payment_option
            else:
                process_date_int = bale.approval_date.strftime("%m/%d/%y")
                delivery_date = process_date_int
                process_date_raw= bale.approval_date
                # 28-03-23
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = bale.grower.id,from_date__lte=bale.approval_date,to_date__gte=bale.approval_date,crop='RICE')
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = bale.grower.id,from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id=check_entry_id)
                    contracted_payment_option = var.contracted_payment_option
                elif check_entry_with_no_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)
                    contracted_payment_option = var.contracted_payment_option
            if contracted_payment_option == 'Acreage Release' or  contracted_payment_option == 'Fixed Price' :
                # total_price = float([i.contract_base_price for i in entry][0]) + float([i.sustainability_premium for i in entry][0])
                entry_id = var.id
                contract_base_price = var.contract_base_price if var.contract_base_price else 0.0
                sustainability_premium =  var.sustainability_premium if var.sustainability_premium else 0.0

                # total_price = float(var.contract_base_price) + float(var.sustainability_premium)
                total_price = float(contract_base_price) + float(sustainability_premium)
                if bale.received_amount != None :
                    received_amount_data = int(bale.received_amount) 
                    delivered_value = float(received_amount_data) * total_price
                else:
                    received_amount_data = int(bale.total_amount)
                    delivered_value = float(received_amount_data) * total_price 
            else:
                entry_id = var.id
                calculation_date = bale.approval_date
                if NasdaqApiData.objects.filter(date_api=calculation_date).count() !=0 :
                    total_price_init = NasdaqApiData.objects.get(date_api=calculation_date).close_value_api
                else:
                    for l in range(1,10):
                        next_date = calculation_date - timedelta(l)
                        if NasdaqApiData.objects.filter(date_api=next_date).count() !=0 :
                            total_price_init = NasdaqApiData.objects.get(date_api=next_date).close_value_api
                            break
                total_price2 = float(total_price_init) / 100
                total_price = total_price2 + 0.04

                if bale.received_amount != None :
                    received_amount_data = int(bale.received_amount) 
                    delivered_value = float(received_amount_data) * total_price
                else:
                    received_amount_data = int(bale.total_amount)
                    delivered_value = float(received_amount_data) * total_price 

            new_date = process_date_raw + timedelta(60)
            payment_due_date = new_date.strftime("%m/%d/%y")
            lst.append(process_date_int)
            lst.append(bale.shipment_id)
            lst.append(bale.grower.name)
            lst.append(bale.crop)
            lst.append(bale.variety)
            lst.append(bale.field.farm.name)
            lst.append(bale.field.name)
            lst.append(received_amount_data)
            lst.append("{0:.5f} USD".format(total_price))
            lst.append("{0:.4f} USD".format(delivered_value))
            lst.append(payment_due_date)

            context["lst"] = lst
            if request.method == "POST":
                payment_amount = request.POST.get("payment_amount")
                # formate (yyyy-mm-dd)
                payment_amount = payment_amount.replace(",", "")
                payment_date = request.POST.get("payment_date")
                payment_type = request.POST.get("payment_type")
                payment_confirmation = request.POST.get("payment_confirmation")

                # Save Grower Payment 
                grower_payment = GrowerPayments(enteyfeeds_id=entry_id, grower_id=bale.grower.id, processor=bale.processor.id,
                delivery_id=bale.shipment_id, delivery_date=bale.date_time, delivery_lbs=received_amount_data,
                total_price=total_price, delivered_value=delivered_value,crop=bale.crop,field=bale.field.id,
                payment_due_date=payment_due_date, payment_amount=payment_amount, payment_date=payment_date, 
                payment_type=payment_type, payment_confirmation=payment_confirmation,grower_name=grower_name,
                field_name=field_name,farm_name=farm_name,level=None,farm=farm,variety=variety)
                grower_payment.save()
                # Notification For GrowerShipment
                gower_user_email = Grower.objects.get(id=bale.grower.id).email
                msg1 = 'You have received a new payment '
                g_user_id = User.objects.get(username=gower_user_email)
                notification_reason1 = 'Payment received'
                redirect_url1 = "/growerpayments/grower_payments_list/"
                save_notification = ShowNotification(user_id_to_show=g_user_id.id,msg=msg1,status="UNREAD",redirect_url=redirect_url1,
                notification_reason=notification_reason1)
                save_notification.save()
                # Log Table 13-04-23
                grower_name = grower_name
                payment_option = grower_payment.enteyfeeds.contracted_payment_option
                contract_base_price = grower_payment.enteyfeeds.contract_base_price
                sustainability_premium = grower_payment.enteyfeeds.sustainability_premium
                if payment_option == "Delivered Market Price" :
                    sustainability_premium = 0.04
                from_date = grower_payment.enteyfeeds.from_date
                to_date = grower_payment.enteyfeeds.to_date
                log_type, log_status, log_device = "GrowerPayments", "Added", "Web"
                log_idd, log_name = grower_payment.id, f'{grower_name} - {bale.shipment_id}'
                log_details = f"Grower = {grower_name}  | contracted_payment_option = {payment_option} | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date} | crop = {grower_payment.crop} | variety = {grower_payment.variety} | field_name = {grower_payment.field_name} | farm_name = {grower_payment.farm_name} | delivery_id = {grower_payment.delivery_id} | delivery_date = {grower_payment.delivery_date} | delivery_lbs = {grower_payment.delivery_lbs} | total_price = {grower_payment.total_price} | delivered_value = {grower_payment.delivered_value} | payment_due_date = {grower_payment.payment_due_date} | payment_amount = {grower_payment.payment_amount} | payment_date = {grower_payment.payment_date} | payment_type = {grower_payment.payment_type} | payment_confirmation = {grower_payment.payment_confirmation}"
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
                                    action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                    log_device=log_device)
                                    
                logtable.save()
                context['payment_amount'] = payment_amount                
                context['payment_date'] = str(payment_date)
                if payment_type == "Check" :
                   context['selectedCheck'] = "selectedCheck "
                elif payment_type == "ACH" :
                   context['selectedACH'] = "ACH"
                context['payment_type'] = payment_type
                context['payment_confirmation'] = payment_confirmation
                messages.success(request,"Payment added successfully")
                return render(request, "growerpayments/grower_payments_add.html",context)
        elif var == 'BaleReportFarmField':
            bale = BaleReportFarmField.objects.get(id = pk)
            field_id = bale.ob4
            classs = bale.level
            classing = ClassingReport.objects.get(id=bale.classing.id)
            grower_id = bale.classing.grower.id
            grower_name = bale.classing.grower.name
            processor_id = classing.processor.id
            delivery_date = bale.dt_class
            field_name = bale.field_name
            farm_name = bale.farm_name
            farm = bale.farm_id
            variety = bale.crop_variety
            # entry = EntryFeeds.objects.filter(grower_id=grower_id)
            if delivery_date :
                str_date = str(delivery_date)
                if '-' in str_date :
                    try :
                        str_date = str_date.split('-')
                        mm = str_date[0]
                        dd = str_date[1]
                        yy = str_date[2]
                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                        finale_date = date(int(yyyy), int(mm), int(dd))
                    except :
                        pass
                elif '/' in str_date :
                    try :
                        str_date = str_date.split('/')
                        mm = str_date[0]
                        dd = str_date[1]
                        yy = str_date[2]
                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                        finale_date = date(int(yyyy), int(mm), int(dd))
                    except :
                        pass
                else:
                    finale_date = ''
            else:
                pass

            # 27-03-23
            check_entry = EntryFeeds.objects.filter(grower_id = bale.ob2)
            if len(check_entry) == 0 :
                pass
            if len(check_entry) == 1 :
                var = EntryFeeds.objects.get(grower_id = bale.ob2)
            if len(check_entry) > 1 :
                check_entry_with_date = EntryFeeds.objects.filter(grower_id = bale.ob2,from_date__lte=finale_date,to_date__gte=finale_date)
                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = bale.ob2,from_date__isnull=True,to_date__isnull=True)
                if check_entry_with_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)
                elif check_entry_with_no_date.exists() :
                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                    var = EntryFeeds.objects.get(id = check_entry_id)

            entry_id = var.id
            crop = var.crop
            contract_base_price = var.contract_base_price 
            sustainability_premium = var.sustainability_premium 
            quality_premium = var.quality_premium 
            if classs == 'Bronze' :
                qp_lbs = 0.00
            elif classs == "Silver":
                qp_lbs = 0.02
            elif classs == "Gold":
                qp_lbs = 0.04
            elif classs == "None":
                qp_lbs = 0.00
            total_price_lbs = float(contract_base_price) + float(sustainability_premium) + float(qp_lbs)
            delivered_value = float(bale.net_wt) * float(total_price_lbs)
            date_str = bale.dt_class.split("/")
            dd = int(date_str[1])
            mm = int(date_str[0])
            yy = int(date_str[2])
            if len(str(yy)) == 2: 
                yyyy = int("20{}".format(yy))
            else:
                yyyy = yy
            specific_date = datetime(yyyy, mm, dd)
            new_date = specific_date + timedelta(60)
            payment_due_date = new_date.strftime("%m/%d/%y")
            lst = []
            lst.append(bale.dt_class)
            lst.append(bale.bale_id)
            lst.append(grower_name)
            lst.append(crop)

            lst.append('')
            lst.append(bale.farm_name)
            lst.append(bale.field_name)
            lst.append(bale.net_wt)
            lst.append("{0:.5f} USD".format(total_price_lbs))
            lst.append("{0:.4f} USD".format(delivered_value))
            lst.append(payment_due_date)
            context["lst"] = lst
            if request.method == "POST":
                payment_amount = request.POST.get("payment_amount")
                # formate (yyyy-mm-dd)
                payment_amount = payment_amount.replace(",", "")
                payment_date = request.POST.get("payment_date")
                payment_type = request.POST.get("payment_type")
                payment_confirmation = request.POST.get("payment_confirmation")
                # print(payment_amount,payment_date,payment_type,payment_confirmation)
                # Save Grower Payment 
                grower_payment = GrowerPayments(enteyfeeds_id=entry_id, grower_id=grower_id, processor=processor_id,crop=crop,field=field_id,
                delivery_id=bale.bale_id, delivery_date=bale.dt_class, delivery_lbs=bale.net_wt, contract_base_price=contract_base_price,
                sustainability_premium=sustainability_premium, quality_premium=quality_premium, total_price=total_price_lbs, delivered_value=delivered_value,
                payment_due_date=payment_due_date, payment_amount=payment_amount, payment_date=payment_date, payment_type=payment_type, 
                payment_confirmation=payment_confirmation,grower_name=grower_name,field_name=field_name,farm_name=farm_name,level=classs,farm=farm,variety=variety)
                
                grower_payment.save()

                # Notification For BaleReportFarmField
                gower_user_email = Grower.objects.get(id=grower_id).email
                msg1 = 'You have received a new payment '
                g_user_id = User.objects.get(username=gower_user_email)
                notification_reason1 = 'Payment received'
                redirect_url1 = "/growerpayments/grower_payments_list/"
                save_notification = ShowNotification(user_id_to_show=g_user_id.id,msg=msg1,status="UNREAD",redirect_url=redirect_url1,
                notification_reason=notification_reason1)
                save_notification.save()

                # Log Table 13-04-23
                grower_name = grower_name
                payment_option = grower_payment.enteyfeeds.contracted_payment_option
                contract_base_price = grower_payment.enteyfeeds.contract_base_price
                sustainability_premium = grower_payment.enteyfeeds.sustainability_premium
                if payment_option == "Delivered Market Price" :
                    sustainability_premium = 0.04
                from_date = grower_payment.enteyfeeds.from_date
                to_date = grower_payment.enteyfeeds.to_date
                log_type, log_status, log_device = "GrowerPayments", "Added", "Web"
                log_idd, log_name = grower_payment.id, f'{grower_name} - {bale.bale_id}'
                log_details = f"Grower = {grower_name}  | contracted_payment_option = {payment_option} | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date} | crop = {grower_payment.crop} | variety = {grower_payment.variety} | field_name = {grower_payment.field_name} | farm_name = {grower_payment.farm_name} | level = {classs} | delivery_id = {grower_payment.delivery_id} | delivery_date = {grower_payment.delivery_date} | delivery_lbs = {grower_payment.delivery_lbs} | total_price = {grower_payment.total_price} | delivered_value = {grower_payment.delivered_value} | payment_due_date = {grower_payment.payment_due_date} | payment_amount = {grower_payment.payment_amount} | payment_date = {grower_payment.payment_date} | payment_type = {grower_payment.payment_type} | payment_confirmation = {grower_payment.payment_confirmation}"
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
                                    action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                    log_device=log_device)
                                    
                logtable.save()

                context['payment_amount'] = payment_amount
                context['payment_date'] = payment_date
                if payment_type == "Check" :
                   context['selectedCheck'] = "selectedCheck "
                elif payment_type == "ACH" :
                   context['selectedACH'] = "ACH"
                context['payment_confirmation'] = payment_confirmation
                messages.success(request,"Payment added successfully")
                return render(request, "growerpayments/grower_payments_add.html",context)
        return render(request, "growerpayments/grower_payments_add.html",context)





@login_required()
def grower_payments_bulk_add(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        if request.method == 'POST' :

            action_by_userid = request.user.id
            user = User.objects.get(pk=action_by_userid)
            user_role = user.role.all()
            action_by_username = f'{user.first_name} {user.last_name}'
            action_by_email = user.username
            if request.user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))

            csv = request.FILES.get("csv_file")
            df = pd.read_csv(csv)
            not_found_bale_id = []
            not_found_entry_feeds = []
            for i in range(len(df)):
                line = df.iloc[i]
                delivery_id = line[0]
                crop = str(line[1]).upper()
                payment_amount = line[2]
                payment_amount = str(payment_amount).replace(",", "").replace("$","")
                payment_date = line[3]
                payment_type = line[4]
                payment_confirmation = line[5]
                saved_grower_id = []
                wrong_spelling = []
                if crop == 'RICE':
                    bale = GrowerShipment.objects.filter(shipment_id=delivery_id)
                    
                    exist_payment = GrowerPayments.objects.filter(delivery_id=delivery_id)
                    if bale.exists() :
                        grower_id = [GrowerShipment.objects.get(shipment_id=delivery_id).grower.id]
                    else:
                        grower_id = []
                    exist_entry_feeds = EntryFeeds.objects.filter(grower_id__in=grower_id)

                    if bale.exists() and len(exist_payment) == 0 and exist_entry_feeds.exists() :
                        bale = GrowerShipment.objects.get(shipment_id=delivery_id)
                        field_name = bale.field.name
                        grower_name = bale.grower.name
                        farm_name = bale.field.farm.name
                        farm = bale.field.farm.id
                        variety = bale.variety
                        entry = EntryFeeds.objects.filter(grower_id=bale.grower.id).filter(crop='RICE')
                        contracted_payment_option = [i.contracted_payment_option for i in entry][0]
                        contract_base_price = [i.contract_base_price for i in entry][0]

                        if bale.approval_date == None:
                            process_date_int = bale.process_date.strftime("%m/%d/%y")
                            delivery_date = process_date_int
                            process_date_raw= bale.process_date
                        else:
                            process_date_int = bale.approval_date.strftime("%m/%d/%y")
                            delivery_date = process_date_int
                            process_date_raw= bale.approval_date

                        entry_id = [i.id for i in entry][0]
                        field_id = bale.field.id

                        if contracted_payment_option == "Acreage Release" :
                            total_price = float([i.contract_base_price for i in entry][0]) + float([i.sustainability_premium for i in entry][0])
                            if bale.received_amount != None :
                                received_amount_data = int(bale.received_amount) 
                                delivered_value = float(received_amount_data) * total_price
                            else:
                                received_amount_data = int(bale.total_amount)
                                delivered_value = float(received_amount_data) * total_price 
                        else:
                            calculation_date = bale.approval_date
                            if NasdaqApiData.objects.filter(date_api=calculation_date).count() !=0 :
                                total_price_init = NasdaqApiData.objects.get(date_api=calculation_date).close_value_api
                            else:
                                for l in range(1,10):
                                    next_date = calculation_date - timedelta(l)
                                    if NasdaqApiData.objects.filter(date_api=next_date).count() !=0 :
                                        total_price_init = NasdaqApiData.objects.get(date_api=next_date).close_value_api
                                        break
                            total_price2 = float(total_price_init) / 100
                            total_price = total_price2 + 0.04

                            if bale.received_amount != None :
                                received_amount_data = int(bale.received_amount) 
                                delivered_value = float(received_amount_data) * total_price
                            else:
                                received_amount_data = int(bale.total_amount)
                                delivered_value = float(received_amount_data) * total_price

                        new_date = process_date_raw + timedelta(60)
                        payment_due_date = new_date.strftime("%m/%d/%y")
                        # data saved part
                        grower_payment = GrowerPayments(enteyfeeds_id=entry_id, grower_id=bale.grower.id, processor=bale.processor.id,
                        delivery_id=bale.shipment_id, delivery_date=bale.date_time, delivery_lbs=received_amount_data,
                        total_price=total_price, delivered_value=delivered_value,crop=crop,field=field_id,
                        payment_due_date=payment_due_date, payment_amount=payment_amount, payment_date=payment_date, payment_type=payment_type, 
                        payment_confirmation=payment_confirmation,grower_name=grower_name,field_name=field_name,farm_name=farm_name,level=None,
                        farm=farm,variety=variety)
                        grower_payment.save()
                        # For Notification
                        saved_grower_id.append(bale.grower.id)

                        # Log Table 13-04-23
                        grower_name = grower_name
                        payment_option = grower_payment.enteyfeeds.contracted_payment_option
                        contract_base_price = grower_payment.enteyfeeds.contract_base_price
                        sustainability_premium = grower_payment.enteyfeeds.sustainability_premium
                        if payment_option == "Delivered Market Price" :
                            sustainability_premium = 0.04
                        from_date = grower_payment.enteyfeeds.from_date
                        to_date = grower_payment.enteyfeeds.to_date
                        log_type, log_status, log_device = "GrowerPayments", "Added", "Web"
                        log_idd, log_name = grower_payment.id, f'{grower_name} - {grower_payment.delivery_id}'
                        log_details = f"Grower = {grower_name}  | contracted_payment_option = {payment_option} | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date} | crop = {grower_payment.crop} | variety = {grower_payment.variety} | field_name = {grower_payment.field_name} | farm_name = {grower_payment.farm_name} | delivery_id = {grower_payment.delivery_id} | delivery_date = {grower_payment.delivery_date} | delivery_lbs = {grower_payment.delivery_lbs} | total_price = {grower_payment.total_price} | delivered_value = {grower_payment.delivered_value} | payment_due_date = {grower_payment.payment_due_date} | payment_amount = {grower_payment.payment_amount} | payment_date = {grower_payment.payment_date} | payment_type = {grower_payment.payment_type} | payment_confirmation = {grower_payment.payment_confirmation}"
                        
                        logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                            action_by_userid=action_by_userid,action_by_username=action_by_username,
                                            action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                            log_device=log_device)
                                            
                        logtable.save()

                    elif bale.exists() and exist_payment.exists() :
                        update_grower_payment = GrowerPayments.objects.get(delivery_id=delivery_id)
                        update_grower_payment.crop = crop
                        update_grower_payment.payment_amount = payment_amount
                        update_grower_payment.payment_date = payment_date
                        update_grower_payment.payment_type = payment_type
                        update_grower_payment.payment_confirmation = payment_confirmation
                        update_grower_payment.save()
                        # For Notification
                        saved_grower_id.append(update_grower_payment.grower.id)
                        # Log Table 13-04-23
                        grower_name = update_grower_payment.grower.name
                        payment_option = update_grower_payment.enteyfeeds.contracted_payment_option
                        contract_base_price = update_grower_payment.enteyfeeds.contract_base_price
                        sustainability_premium = update_grower_payment.enteyfeeds.sustainability_premium
                        if payment_option == "Delivered Market Price" :
                            sustainability_premium = 0.04
                        from_date = update_grower_payment.enteyfeeds.from_date
                        to_date = update_grower_payment.enteyfeeds.to_date
                        log_type, log_status, log_device = "GrowerPayments", "Edited", "Web"
                        log_idd, log_name = update_grower_payment.id, f'{grower_name} - {update_grower_payment.delivery_id}'
                        log_details = f"Grower = {grower_name}  | contracted_payment_option = {payment_option} | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date} | crop = {update_grower_payment.crop} | variety = {update_grower_payment.variety} | field_name = {update_grower_payment.field_name} | farm_name = {update_grower_payment.farm_name} | delivery_id = {update_grower_payment.delivery_id} | delivery_date = {update_grower_payment.delivery_date} | delivery_lbs = {update_grower_payment.delivery_lbs} | total_price = {update_grower_payment.total_price} | delivered_value = {update_grower_payment.delivered_value} | payment_due_date = {update_grower_payment.payment_due_date} | payment_amount = {update_grower_payment.payment_amount} | payment_date = {update_grower_payment.payment_date} | payment_type = {update_grower_payment.payment_type} | payment_confirmation = {update_grower_payment.payment_confirmation}"
                        
                        logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                            action_by_userid=action_by_userid,action_by_username=action_by_username,
                                            action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                            log_device=log_device)
                                            
                        logtable.save()
                        
                    elif len(bale) == 0 and exist_entry_feeds.exists() :
                        not_found_bale_id.append(delivery_id)
                    elif bale.exists() and len(exist_entry_feeds) == 0 :
                        not_found_entry_feeds.append(delivery_id)
                    elif len(bale) == 0 and len(exist_entry_feeds) == 0 :
                        not_found_bale_id.append(delivery_id)
                elif crop == 'COTTON':
                    bale = BaleReportFarmField.objects.filter(bale_id = delivery_id)
                    exist_payment = GrowerPayments.objects.filter(delivery_id=delivery_id)
                    bale0 = BaleReportFarmField.objects.filter(bale_id = f"0{delivery_id}")
                    exist_payment0 = GrowerPayments.objects.filter(delivery_id=f"0{delivery_id}")
                    
                    if bale.exists() :
                        grower_id = [BaleReportFarmField.objects.get(bale_id = delivery_id).ob2]
                        exist_entry_feeds = EntryFeeds.objects.filter(grower_id__in=grower_id)
                        if bale.exists() and len(exist_payment) == 0 and exist_entry_feeds.exists() :
                            bale = BaleReportFarmField.objects.get(bale_id = delivery_id)
                            classing = ClassingReport.objects.get(id=bale.classing.id)
                            grower_id = bale.classing.grower.id
                            field_id = bale.ob4
                            processor_id = classing.processor.id
                            grower_name = bale.classing.grower.name
                            processor_id = classing.processor.id
                            delivery_date = bale.dt_class
                            field_name = bale.field_name
                            farm_name = bale.farm_name
                            farm = bale.farm_id
                            variety = bale.crop_variety
                            classs = bale.level
                            entry = EntryFeeds.objects.filter(grower_id=grower_id)
                            entry_id = [i.id for i in entry][0]
                            crop = [i.crop for i in entry][0]
                            contract_base_price = [i.contract_base_price for i in entry][0]
                            sustainability_premium = [i.sustainability_premium for i in entry][0]
                            quality_premium = [i.quality_premium for i in entry][0]
                            total_price_lbs = float(contract_base_price) + float(sustainability_premium)
                            delivered_value = float(bale.net_wt) * float(total_price_lbs)
                            if bale.dt_class :
                                delivery_date = bale.dt_class
                                date_str = bale.dt_class.split("/")
                                dd = int(date_str[1])
                                mm = int(date_str[0])
                                yy = int(date_str[2])
                                if len(str(yy)) == 2: 
                                    yyyy = int("20{}".format(yy))
                                else:
                                    yyyy = yy
                                specific_date = datetime(yyyy, mm, dd)
                                new_date = specific_date + timedelta(60)
                                payment_due_date = new_date.strftime("%m/%d/%y")
                            else:
                                delivery_date = None
                                payment_due_date = None
                            grower_payment = GrowerPayments(enteyfeeds_id=entry_id, grower_id=grower_id, processor=processor_id,crop=crop,field=field_id,
                            delivery_id=bale.bale_id, delivery_date=delivery_date, delivery_lbs=bale.net_wt, contract_base_price=contract_base_price,
                            sustainability_premium=sustainability_premium, quality_premium=quality_premium, total_price=total_price_lbs, delivered_value=delivered_value,
                            payment_due_date=payment_due_date, payment_amount=payment_amount, payment_date=payment_date, payment_type=payment_type, payment_confirmation=payment_confirmation,
                            grower_name=grower_name,field_name=field_name,farm_name=farm_name,level=classs,farm=farm,variety=variety)
                            grower_payment.save()
                            # For Notification
                            saved_grower_id.append(grower_id)
                            # Log Table 13-04-23
                            grower_name = grower_name
                            payment_option = grower_payment.enteyfeeds.contracted_payment_option
                            contract_base_price = grower_payment.enteyfeeds.contract_base_price
                            sustainability_premium = grower_payment.enteyfeeds.sustainability_premium
                            if payment_option == "Delivered Market Price" :
                                sustainability_premium = 0.04
                            from_date = grower_payment.enteyfeeds.from_date
                            to_date = grower_payment.enteyfeeds.to_date
                            log_type, log_status, log_device = "GrowerPayments", "Added", "Web"
                            log_idd, log_name = grower_payment.id, f'{grower_name} - {grower_payment.delivery_id}'
                            log_details = f"Grower = {grower_name}  | contracted_payment_option = {payment_option} | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date} | crop = COTTON | variety = {grower_payment.variety} | field_name = {grower_payment.field_name} | farm_name = {grower_payment.farm_name} | delivery_id = {grower_payment.delivery_id} | delivery_date = {grower_payment.delivery_date} | delivery_lbs = {grower_payment.delivery_id} | total_price = {grower_payment.total_price} | delivered_value = {grower_payment.delivered_value} | payment_due_date = {grower_payment.payment_due_date} | payment_amount = {grower_payment.payment_amount} | payment_date = {grower_payment.payment_date} | payment_type = {grower_payment.payment_type} | payment_confirmation = {grower_payment.payment_confirmation}"
                            
                            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                                action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                                log_device=log_device)
                                                
                            logtable.save()
                        elif bale.exists() and exist_payment.exists() :
                            update_grower_payment = GrowerPayments.objects.get(delivery_id=delivery_id)
                            update_grower_payment.crop = crop
                            update_grower_payment.payment_amount = payment_amount
                            update_grower_payment.payment_date = payment_date
                            update_grower_payment.payment_type = payment_type
                            update_grower_payment.payment_confirmation = payment_confirmation
                            update_grower_payment.save()
                            # For Notification
                            saved_grower_id.append(update_grower_payment.grower.id)
                            # Log Table 13-04-23
                            grower_name = update_grower_payment.grower.name
                            payment_option = update_grower_payment.enteyfeeds.contracted_payment_option
                            contract_base_price = update_grower_payment.enteyfeeds.contract_base_price
                            sustainability_premium = update_grower_payment.enteyfeeds.sustainability_premium
                            if payment_option == "Delivered Market Price" :
                                sustainability_premium = 0.04
                            from_date = update_grower_payment.enteyfeeds.from_date
                            to_date = update_grower_payment.enteyfeeds.to_date
                            log_type, log_status, log_device = "GrowerPayments", "Edited", "Web"
                            # grower_payment
                            log_idd, log_name = update_grower_payment.id, f'{grower_name} - {update_grower_payment.delivery_id}'
                            log_details = f"Grower = {grower_name}  | contracted_payment_option = {payment_option} | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date} | crop = {update_grower_payment.crop} | variety = {update_grower_payment.variety} | field_name = {update_grower_payment.field_name} | farm_name = {update_grower_payment.farm_name} | delivery_id = {update_grower_payment.delivery_id} | delivery_date = {update_grower_payment.delivery_date} | delivery_lbs = {update_grower_payment.delivery_id} | total_price = {update_grower_payment.total_price} | delivered_value = {update_grower_payment.delivered_value} | payment_due_date = {update_grower_payment.payment_due_date} | payment_amount = {update_grower_payment.payment_amount} | payment_date = {update_grower_payment.payment_date} | payment_type = {update_grower_payment.payment_type} | payment_confirmation = {update_grower_payment.payment_confirmation}"
                            
                            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                                action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                                log_device=log_device)
                                                
                            logtable.save()
                        elif len(bale) == 0 and exist_entry_feeds.exists() :
                            not_found_bale_id.append(delivery_id)
                        elif bale.exists() and len(exist_entry_feeds) == 0 :
                            not_found_entry_feeds.append(delivery_id)
                        elif len(bale) == 0 and len(exist_entry_feeds) == 0 :
                            not_found_bale_id.append(delivery_id)
                    
                    elif bale0.exists() :
                        grower_id = [BaleReportFarmField.objects.get(bale_id = f"0{delivery_id}").ob2]
                        exist_entry_feeds0 = EntryFeeds.objects.filter(grower_id__in=grower_id)
                        if bale0.exists() and len(exist_payment0) == 0 and exist_entry_feeds0.exists() :
                            bale = BaleReportFarmField.objects.get(bale_id = f"0{delivery_id}")
                            classing = ClassingReport.objects.get(id=bale.classing.id)
                            grower_id = bale.classing.grower.id
                            field_id = bale.ob4
                            processor_id = classing.processor.id
                            grower_name = bale.classing.grower.name
                            delivery_date = bale.dt_class
                            field_name = bale.field_name
                            farm_name = bale.farm_name
                            farm = bale.farm_id
                            variety = bale.crop_variety
                            classs = bale.level

                            entry = EntryFeeds.objects.filter(grower_id=grower_id)
                            entry_id = [i.id for i in entry][0]
                            crop = [i.crop for i in entry][0]
                            contract_base_price = [i.contract_base_price for i in entry][0]
                            sustainability_premium = [i.sustainability_premium for i in entry][0]
                            quality_premium = [i.quality_premium for i in entry][0]
                            total_price_lbs = float(contract_base_price) + float(sustainability_premium)
                            delivered_value = float(bale.net_wt) * float(total_price_lbs)
                            if bale.dt_class :
                                delivery_date = bale.dt_class
                                date_str = bale.dt_class.split("/")
                                dd = int(date_str[1])
                                mm = int(date_str[0])
                                yy = int(date_str[2])
                                if len(str(yy)) == 2: 
                                    yyyy = int("20{}".format(yy))
                                else:
                                    yyyy = yy
                                specific_date = datetime(yyyy, mm, dd)
                                new_date = specific_date + timedelta(60)
                                payment_due_date = new_date.strftime("%m/%d/%y")
                            else:
                                delivery_date = None
                                payment_due_date = None
                            grower_payment = GrowerPayments(enteyfeeds_id=entry_id, grower_id=grower_id, processor=processor_id,crop=crop,field=field_id,
                            delivery_id=bale.bale_id, delivery_date=delivery_date, delivery_lbs=bale.net_wt, contract_base_price=contract_base_price,
                            sustainability_premium=sustainability_premium, quality_premium=quality_premium, total_price=total_price_lbs, delivered_value=delivered_value,
                            payment_due_date=payment_due_date, payment_amount=payment_amount, payment_date=payment_date, payment_type=payment_type, payment_confirmation=payment_confirmation,
                            grower_name=grower_name,field_name=field_name,farm_name=farm_name,level=classs,farm=farm,variety=variety)
                            grower_payment.save()
                            # For Notification
                            saved_grower_id.append(grower_id)
                            # Log Table 13-04-23
                            grower_name = grower_name
                            payment_option = grower_payment.enteyfeeds.contracted_payment_option
                            contract_base_price = grower_payment.enteyfeeds.contract_base_price
                            sustainability_premium = grower_payment.enteyfeeds.sustainability_premium
                            if payment_option == "Delivered Market Price" :
                                sustainability_premium = 0.04
                            from_date = grower_payment.enteyfeeds.from_date
                            to_date = grower_payment.enteyfeeds.to_date
                            log_type, log_status, log_device = "GrowerPayments", "Added", "Web"
                            log_idd, log_name = grower_payment.id, f'{grower_name} - {grower_payment.delivery_id}'
                            log_details = f"Grower = {grower_name}  | contracted_payment_option = {payment_option} | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date} | crop = {grower_payment.crop} | variety = {grower_payment.variety} | field_name = {grower_payment.field_name} | farm_name = {grower_payment.farm_name} | delivery_id = {grower_payment.delivery_id} | delivery_date = {grower_payment.delivery_date} | delivery_lbs = {grower_payment.delivery_id} | total_price = {grower_payment.total_price} | delivered_value = {grower_payment.delivered_value} | payment_due_date = {grower_payment.payment_due_date} | payment_amount = {grower_payment.payment_amount} | payment_date = {grower_payment.payment_date} | payment_type = {grower_payment.payment_type} | payment_confirmation = {grower_payment.payment_confirmation}"
                            
                            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                                action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                                log_device=log_device)
                                                
                            logtable.save()
                        elif bale0.exists() and exist_payment0.exists() :
                            update_grower_payment = GrowerPayments.objects.get(delivery_id=f"0{delivery_id}")
                            update_grower_payment.crop = crop
                            update_grower_payment.payment_amount = payment_amount
                            update_grower_payment.payment_date = payment_date
                            update_grower_payment.payment_type = payment_type
                            update_grower_payment.payment_confirmation = payment_confirmation
                            update_grower_payment.save()
                            # For Notification
                            saved_grower_id.append(update_grower_payment.grower.id)
                            # Log Table 13-04-23 Log Table
                            grower_name = update_grower_payment.grower.name
                            payment_option = update_grower_payment.enteyfeeds.contracted_payment_option
                            contract_base_price = update_grower_payment.enteyfeeds.contract_base_price
                            sustainability_premium = update_grower_payment.enteyfeeds.sustainability_premium
                            if payment_option == "Delivered Market Price" :
                                sustainability_premium = 0.04
                            from_date = update_grower_payment.enteyfeeds.from_date
                            to_date = update_grower_payment.enteyfeeds.to_date
                            log_type, log_status, log_device = "GrowerPayments", "Edited", "Web"
                            log_idd, log_name = update_grower_payment.id, f'{grower_name} - {update_grower_payment.delivery_id}'
                            log_details = f"Grower = {grower_name}  | contracted_payment_option = {payment_option} | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date} | crop = {update_grower_payment.crop} | variety = {update_grower_payment.variety} | field_name = {update_grower_payment.field_name} | farm_name = {update_grower_payment.farm_name} | delivery_id = {update_grower_payment.delivery_id} | delivery_date = {update_grower_payment.delivery_date} | delivery_lbs = {update_grower_payment.delivery_id} | total_price = {update_grower_payment.total_price} | delivered_value = {update_grower_payment.delivered_value} | payment_due_date = {update_grower_payment.payment_due_date} | payment_amount = {update_grower_payment.payment_amount} | payment_date = {update_grower_payment.payment_date} | payment_type = {update_grower_payment.payment_type} | payment_confirmation = {update_grower_payment.payment_confirmation}"
                            
                            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                                action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                                log_device=log_device)
                                                
                            logtable.save()
                        elif len(bale0) == 0 and exist_entry_feeds0.exists() :
                            not_found_bale_id.append(delivery_id)
                        elif bale0.exists() and len(exist_entry_feeds0) == 0 :
                            not_found_entry_feeds.append(delivery_id)
                        elif len(bale0) == 0 and len(exist_entry_feeds0) == 0 :
                            not_found_bale_id.append(delivery_id)
                    else:
                        not_found_bale_id.append(delivery_id)
                else:
                    wrong_spelling.append(delivery_id)
            # For Notification
            unique_saved_grower_id = list(set(saved_grower_id))
            for i in unique_saved_grower_id :
                gower_user_email = Grower.objects.get(id=i).email
                msg1 = 'You have received a new payment '
                g_user_id = User.objects.get(username=gower_user_email)
                notification_reason1 = 'Payment received'
                redirect_url1 = "/growerpayments/grower_payments_list/"
                save_notification = ShowNotification(user_id_to_show=g_user_id.id,msg=msg1,status="UNREAD",redirect_url=redirect_url1,
                notification_reason=notification_reason1)
                save_notification.save()


            if len(not_found_bale_id) == 0 and len(not_found_entry_feeds) == 0  :
                messages.success(request,"CSV Uploaded Successfully")
            if len(not_found_bale_id) != 0 and len(not_found_entry_feeds) == 0 :
                messages.success(request,"CSV Uploaded Successfully")
                messages.error(request,f"Bale Id(s) not inserted as its not in Classing list : {set(not_found_bale_id)}")
            if len(not_found_bale_id) == 0 and len(not_found_entry_feeds) != 0 :
                messages.success(request,"CSV Uploaded Successfully")
                messages.error(request,f"Bale Id(s) not inserted as it misses Entry Feeds : {set(not_found_entry_feeds)}")
            if len(not_found_bale_id) != 0 and len(not_found_entry_feeds) != 0 :
                messages.success(request,"CSV Uploaded Successfully")
                messages.error(request,f"Bale Id(s) not inserted as it misses Entry Feeds : {set(not_found_entry_feeds)}")
                messages.error(request,f"Bale Id(s) not inserted as its not in Classing list : {set(not_found_bale_id)}")
            if len(wrong_spelling) != 0 :
                messages.error(request,f"The Delivery Id {set(wrong_spelling)} doesn’t have a proper crop type. Please fix and reupload.")
        return render(request, "growerpayments/grower_payments_bulk_add.html",context)


@login_required()
def grower_payments_edit(request,var,pk):
    context = {}
    
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        if var == 'GrowerShipment':
            bale = GrowerShipment.objects.get(id=pk)
            gp = GrowerPayments.objects.get(delivery_id=bale.shipment_id)
            context["gp"] = gp
            try:            
                var_date = gp.payment_date.split('/')
                var_date_mm = var_date[0]
                var_date_dd= var_date[1]
                var_date_yyyy = var_date[2]
                if len(var_date_yyyy) == 2 :
                    var_date_yyyy = f'20{var_date_yyyy}'
                else:
                    var_date_yyyy = var_date_yyyy
                gp_date = f"{var_date_yyyy}-{var_date_mm}-{var_date_dd}"
                context["gp_date"] = gp_date
            except:
                context["gp_date"] = str(gp.payment_date)
            # entry = EntryFeeds.objects.filter(grower_id=bale.grower.id).filter(crop='RICE')
            # contract_base_price = [i.contract_base_price for i in entry][0]
            # contracted_payment_option = [i.contracted_payment_option for i in entry][0]
            # if contracted_payment_option == "Acreage Release" or contracted_payment_option == "Fixed Price" :
            #     total_price = float([i.contract_base_price for i in entry][0]) + float([i.sustainability_premium for i in entry][0])
            #     if bale.received_amount != None :
            #         received_amount_data = int(bale.received_amount) 
            #         delivered_value = float(received_amount_data) * total_price
            #     else:
            #         received_amount_data = int(bale.total_amount)
            #         delivered_value = float(received_amount_data) * total_price 
            # else:
            #     total_price_init = [i.contract_base_price for i in entry][0]
            #     total_price = float(total_price_init) / 100
            #     if bale.received_amount != None :
            #         received_amount_data = int(bale.received_amount) 
            #         delivered_value = float(received_amount_data) * total_price
            #     else:
            #         received_amount_data = int(bale.total_amount)
            #         delivered_value = float(received_amount_data) * total_price 
            
            new_date = bale.date_time + timedelta(60)
            payment_due_date = new_date.strftime("%m/%d/%y")
            lst = []
            if bale.approval_date == None:
                process_date_int = bale.process_date.strftime("%m/%d/%y")
                process_date_raw = bale.process_date
            else:
                process_date_int = bale.approval_date.strftime("%m/%d/%y")
                process_date_raw = bale.approval_date
            
            new_date = process_date_raw + timedelta(60)
            payment_due_date = new_date.strftime("%m/%d/%y")

            # 31-03-23
            total_price = float(gp.total_price)
            delivered_value = float(gp.delivered_value)
            received_amount_data = gp.delivery_lbs

            lst.append(process_date_int)
            lst.append(bale.shipment_id)
            lst.append(bale.grower.name)
            lst.append(bale.crop)
            lst.append(bale.variety)
            lst.append(bale.field.farm.name)
            lst.append(bale.field.name)
            lst.append(received_amount_data)
            lst.append("{0:.5f} USD".format(total_price))
            lst.append("{0:.4f} USD".format(delivered_value))
            lst.append(payment_due_date)

            context["lst"] = lst
            if request.method == "POST":
                payment_amount = request.POST.get("payment_amount")
                # formate (yyyy-mm-dd)
                payment_amount = payment_amount.replace(",", "")
                payment_date = request.POST.get("payment_date")
                payment_type = request.POST.get("payment_type")
                payment_confirmation = request.POST.get("payment_confirmation")
                if payment_amount !=None and payment_date !=None and payment_type !=None and payment_confirmation !=None:
                    gp.payment_amount =payment_amount
                    gp.payment_date =payment_date
                    gp.payment_type =payment_type
                    gp.payment_confirmation =payment_confirmation
                    gp.save()
                    # Notification 
                    gower_user_email = Grower.objects.get(id=gp.grower.id).email
                    msg1 = 'You have received a new payment '
                    g_user_id = User.objects.get(username=gower_user_email)
                    notification_reason1 = 'Payment received'
                    redirect_url1 = "/growerpayments/grower_payments_list/"
                    save_notification = ShowNotification(user_id_to_show=g_user_id.id,msg=msg1,status="UNREAD",redirect_url=redirect_url1,
                    notification_reason=notification_reason1)
                    save_notification.save()
                    context["gp_date"] = str(payment_date)
                    # Log Table 13-04-23
                    grower_name = gp.grower.name
                    payment_option = gp.enteyfeeds.contracted_payment_option
                    contract_base_price = gp.enteyfeeds.contract_base_price
                    sustainability_premium = gp.enteyfeeds.sustainability_premium
                    if payment_option == "Delivered Market Price" :
                        sustainability_premium = 0.04
                    from_date = gp.enteyfeeds.from_date
                    to_date = gp.enteyfeeds.to_date
                    log_type, log_status, log_device = "GrowerPayments", "Edited", "Web"
                    log_idd, log_name = gp.id, f'{grower_name} - {gp.delivery_id}'
                    log_details = f"Grower = {grower_name}  | contracted_payment_option = {payment_option} | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date} | crop = {bale.crop} | variety = {gp.variety} | field_name = {gp.field_name} | farm_name = {gp.farm_name} | delivery_id = {gp.delivery_id} | delivery_date = {gp.delivery_date} | delivery_lbs = {gp.delivered_value} | total_price = {gp.total_price} | delivered_value = {gp.delivered_value} | payment_due_date = {gp.payment_due_date} | payment_amount = {payment_amount} | payment_date = {payment_date} | payment_type = {payment_type} | payment_confirmation = {payment_confirmation}"
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
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                                        
                    logtable.save()
                    messages.success(request,"Payment edited successfully")
                    return render(request, "growerpayments/grower_payments_edit.html",context)
        elif var == 'BaleReportFarmField':
            
            bale = BaleReportFarmField.objects.get(id = pk)
            gp = GrowerPayments.objects.get(delivery_id=bale.bale_id)
            context["gp"] = gp
            try:            
                # 11/09/22
                var_date = gp.payment_date.split('/')
                var_date_mm = var_date[0]
                var_date_dd= var_date[1] 
                var_date_yyyy = var_date[2]
                if len(var_date_yyyy) == 2 :
                    var_date_yyyy = f'20{var_date_yyyy}'
                else:
                    var_date_yyyy = var_date_yyyy
                gp_date = f"{var_date_yyyy}-{var_date_mm}-{var_date_dd}"
                context["gp_date"] = gp_date

            except:
                pass
                context["gp_date"] = str(gp.payment_date)
            classing = ClassingReport.objects.get(id=bale.classing.id)
            grower_id = bale.classing.grower.id
            grower_name = bale.classing.grower.name
            # processor_id = classing.processor.id
            entry = EntryFeeds.objects.filter(grower_id=grower_id)
            # entry_id = [i.id for i in entry][0]
            crop = [i.crop for i in entry][0]
            # contract_base_price = [i.contract_base_price for i in entry][0]
            # sustainability_premium = [i.sustainability_premium for i in entry][0]
            # quality_premium = [i.quality_premium for i in entry][0]
            # total_price_lbs = float(contract_base_price) + float(sustainability_premium)
            # delivered_value = float(bale.net_wt) * float(contract_base_price)
            
            # 31-03-23
            total_price_lbs = float(gp.total_price)
            delivered_value = float(gp.delivered_value)
            
            date_str = bale.dt_class.split("/")
            dd = int(date_str[1])
            mm = int(date_str[0])
            yy = int(date_str[2])
            if len(str(yy)) == 2: 
                yyyy = int("20{}".format(yy))
            else:
                yyyy = yy
            specific_date = datetime(yyyy, mm, dd)
            new_date = specific_date + timedelta(60)
            payment_due_date = new_date.strftime("%m/%d/%y")
            lst = []
            lst.append(bale.dt_class)
            lst.append(bale.bale_id)
            lst.append(grower_name)
            lst.append(crop)

            lst.append('')
            lst.append(bale.farm_name)
            lst.append(bale.field_name)
            lst.append(bale.net_wt)
            lst.append("{0:.5f} USD".format(total_price_lbs))
            lst.append("{0:.4f} USD".format(delivered_value))
            lst.append(payment_due_date)
            context["lst"] = lst
            if request.method == "POST":
                payment_amount = request.POST.get("payment_amount")
                # formate (yyyy-mm-dd)
                payment_amount = payment_amount.replace(",", "")
                payment_date = request.POST.get("payment_date")
                payment_type = request.POST.get("payment_type")
                payment_confirmation = request.POST.get("payment_confirmation")
                if payment_amount !=None and payment_date !=None and payment_type !=None and payment_confirmation !=None:
                    gp.crop =crop
                    gp.payment_amount =payment_amount
                    gp.payment_date =payment_date
                    gp.payment_type =payment_type
                    gp.payment_confirmation =payment_confirmation
                    gp.save()
                    # Notification 
                    gower_user_email = Grower.objects.get(id=gp.grower.id).email
                    msg1 = 'You have received a new payment '
                    g_user_id = User.objects.get(username=gower_user_email)
                    notification_reason1 = 'Payment received'
                    redirect_url1 = "/growerpayments/grower_payments_list/"
                    save_notification = ShowNotification(user_id_to_show=g_user_id.id,msg=msg1,status="UNREAD",redirect_url=redirect_url1,
                    notification_reason=notification_reason1)
                    save_notification.save()
                    context["gp_date"] = str(payment_date)
                    # Log Table 13-04-23
                    grower_name = grower_name
                    payment_option = gp.enteyfeeds.contracted_payment_option
                    contract_base_price = gp.enteyfeeds.contract_base_price
                    sustainability_premium = gp.enteyfeeds.sustainability_premium
                    if payment_option == "Delivered Market Price" :
                        sustainability_premium = 0.04
                    from_date = gp.enteyfeeds.from_date
                    to_date = gp.enteyfeeds.to_date
                    log_type, log_status, log_device = "GrowerPayments", "Edited", "Web"
                    log_idd, log_name = gp.id, f'{grower_name} - {gp.delivery_id}'
                    log_details = f"Grower = {grower_name}  | contracted_payment_option = {payment_option} | contract_base_price = {contract_base_price} | sustainability_premium = {sustainability_premium} | from_date = {from_date} | to_date = {to_date} | crop = {gp.crop} | variety = {gp.variety} | field_name = {gp.field_name} | farm_name = {gp.farm_name} | delivery_id = {gp.delivery_id} | delivery_date = {gp.delivery_date} | delivery_lbs = {gp.delivered_value} | total_price = {gp.total_price} | delivered_value = {gp.delivered_value} | payment_due_date = {gp.payment_due_date} | payment_amount = {payment_amount} | payment_date = {payment_date} | payment_type = {payment_type} | payment_confirmation = {payment_confirmation}"
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
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                                        
                    logtable.save()
                    messages.success(request,"Payment edited successfully")
                    return render(request, "growerpayments/grower_payments_edit.html",context)
        return render(request, "growerpayments/grower_payments_edit.html",context)



@login_required()
def nasdaq_get_data(request):
    context = {}
    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        mycsv = pd.read_csv(csv_file)
        api_date = mycsv['Date']
        api_close_value = mycsv['Close/Last']
        for i in range(len(mycsv)):
            var = api_date[i].split('/')
            yyyy = var[2]
            mm = var[0]
            dd = var[1]
            date_api = f"{yyyy}-{mm}-{dd}"
            if len(NasdaqApiData.objects.filter(date_api=date_api)) > 0 :
                pass
            else:
                nsd = NasdaqApiData(date_api=date_api,close_value_api=api_close_value[i])
                nsd.save()
        messages.success(request, "Uploaded Csv successfully")
    return render(request, "growerpayments/nasdaq_get_data.html",context)

@login_required()
def nasdaq_list_data(request):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        context = {}
        report = NasdaqApiData.objects.all().order_by("-date_api")
        if request.method == 'POST' :
            get_date = request.POST.get('get_date')

            if get_date :
                #  ['“05-19-2023” value has an invalid date format. It must be in YYYY-MM-DD format.']
                my_date = str(get_date).split('-')
                yyyy = my_date[2]
                mm = my_date[0]
                dd = my_date[1]
                check_date = f"{yyyy}-{mm}-{dd}"
                report = report.filter(date_api=check_date)
                context['show_date'] = str(get_date)
                
        context['all_report'] = report

        paginator = Paginator(report, 100)
        page = request.GET.get('page')
        try:
            report = paginator.page(page)
        except PageNotAnInteger:
            report = paginator.page(1)
        except EmptyPage:
            report = paginator.page(paginator.num_pages)
        
        context['report'] = report
        return render(request, "growerpayments/nasdaq_list_data.html",context)
    else:
        return redirect ('dashboard')
    

@login_required()
def grower_split_payee_add(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        growers = Grower.objects.all().order_by('name')
        context['growers'] = growers
        if request.method == 'POST':
            grower_id = request.POST.get('grower_id')
            field_id = request.POST.get('field_id')
            grower_crop = request.POST.get('grower_crop')
            if grower_id :
                selectedGrower = Grower.objects.get(id=grower_id)
                fields = Field.objects.filter(grower_id=grower_id)
                context['selectedGrower'] = selectedGrower
                context['fields'] = fields
                if field_id :
                    crops = Field.objects.get(id=field_id).crop
                    context['selectedField'] = Field.objects.get(id=field_id)
                    context['crops'] = crops
                if grower_id and field_id and grower_crop :
                    payee_entity_name = request.POST.get('payee_entity_name')
                    payee_tax_id = request.POST.get('payee_tax_id')
                    payee_physical_address = request.POST.get('payee_physical_address')
                    payee_mailing_address = request.POST.get('payee_mailing_address')
                    payee_phone = request.POST.get('payee_phone')
                    payee_email = request.POST.get('payee_email')

                    select_lien_holder = request.POST.get('lien_holder')
                    select_payment_splits = request.POST.get('payment_splits')
                    ccounter = request.POST.get('counter')

                    lien_name = request.POST.get('lien_name')
                    lien_tax_id = request.POST.get('lien_tax_id')
                    lien_physical_add = request.POST.get('lien_physical_add')
                    lien_mailing = request.POST.get('lien_mailing')
                    lien_contact_person = request.POST.get('lien_contact_person')
                    lien_phone = request.POST.get('lien_phone')
                    lien_email = request.POST.get('lien_email')
                    lien_split_payee_percentage = request.POST.get('lien_split_payee_percentage')
                    
                    split_name = request.POST.get('split_name')
                    split_tax_id = request.POST.get('split_tax_id')
                    split_physical_add = request.POST.get('split_physical_add')
                    split_mailing = request.POST.get('split_mailing')
                    split_contact_person = request.POST.get('split_contact_person')
                    split_phone = request.POST.get('split_phone')
                    split_email = request.POST.get('split_email')
                    split_split_payee_percentage = request.POST.get('split_split_payee_percentage')

                    grower_namee = Grower.objects.get(id=grower_id).name
                    field_namee = Field.objects.get(id=field_id).name
                    crop = Field.objects.get(id=field_id).crop
                  
                    grower_payee = GrowerPayee(grower_id=grower_id,field_id=field_id,grower_namee=grower_namee,grower_idd=grower_id,
                    field_namee=field_namee,field_idd=field_id,crop=crop,payee_entity_name=payee_entity_name,payee_tax_id=payee_tax_id,
                    payee_physical_address=payee_physical_address,payee_mailing_address=payee_mailing_address,payee_phone=payee_phone,
                    payee_email=payee_email,lien_holder_status=select_lien_holder,payment_split_status=select_payment_splits)
                    grower_payee.save()
                    # 20-04-23 LogTable
                    status_lien_holder_status = "YES" if select_lien_holder == 'YES' else "NO"
                    status_payment_split_status = "YES" if select_payment_splits == 'YES' else "NO"
                    log_type, log_status, log_device = "GrowerPayee", "Added", "Web"
                    log_idd, log_name = grower_payee.id, f"{grower_payee.grower_namee} - {grower_payee.field_namee}"
                    log_details = f"grower = {grower_payee.grower_namee} | grower_id = {grower_payee.grower_idd} | field = {grower_payee.field_namee} | field_id = {grower_payee.field_idd} | crop = {grower_payee.crop} | payee_entity_name = {grower_payee.payee_entity_name} | payee_tax_id = {grower_payee.payee_tax_id} | payee_physical_address = {grower_payee.payee_physical_address} | payee_mailing_address = {grower_payee.payee_mailing_address} | payee_phone = {grower_payee.payee_phone} | payee_email = {grower_payee.payee_email} | lien_holder_status ={status_lien_holder_status} | payment_split_status = {status_payment_split_status} | net_payee = {grower_payee.net_payee} |"
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
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()

                    if select_lien_holder == 'YES' :
                        payment_split = PaymentSplits(grower_payee_id=grower_payee.id,split_payee_name=lien_name,split_payee_tax_id=lien_tax_id,
                        split_payee_physical_address=lien_physical_add,split_payee_mailing_address=lien_mailing,split_payee_contact_person=lien_contact_person,
                        split_payee_phone=lien_phone,split_payee_email=lien_email,split_payee_percent=lien_split_payee_percentage,
                        split_payee_type='Lien')
                        payment_split.save()
                        
                    if select_payment_splits == 'YES' :
                        payment_split = PaymentSplits(grower_payee_id=grower_payee.id,split_payee_name=split_name,split_payee_tax_id=split_tax_id,
                        split_payee_physical_address=split_physical_add,split_payee_mailing_address=split_mailing,split_payee_contact_person=split_contact_person,
                        split_payee_phone=split_phone,split_payee_email=split_email,split_payee_percent=split_split_payee_percentage,
                        split_payee_type='Split')
                        payment_split.save()
                        
                    if int(ccounter) > 1 :
                        for i in range(2,int(ccounter)+1) :
                            split_name = request.POST.get('split_name{}'.format(i))
                            split_tax_id = request.POST.get('split_tax_id{}'.format(i))
                            split_physical_add = request.POST.get('split_physical_add{}'.format(i))
                            split_mailing = request.POST.get('split_mailing{}'.format(i))
                            split_contact_person = request.POST.get('split_contact_person{}'.format(i))
                            split_phone = request.POST.get('split_phone{}'.format(i))
                            split_email = request.POST.get('split_email{}'.format(i))
                            split_split_payee_percentage = request.POST.get('split_split_payee_percentage{}'.format(i))

                            payment_split = PaymentSplits(grower_payee_id=grower_payee.id,split_payee_name=split_name,split_payee_tax_id=split_tax_id,
                            split_payee_physical_address=split_physical_add,split_payee_mailing_address=split_mailing,split_payee_contact_person=split_contact_person,
                            split_payee_phone=split_phone,split_payee_email=split_email,split_payee_percent=split_split_payee_percentage,
                            split_payee_type='Split')
                            payment_split.save()
                            
                    return redirect ('grower_payment_split_list')           
        return render(request, "growerpayments/grower_split_payee_add.html",context)


@login_required()
def grower_split_payee_list(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        grower_payment = []
        total_deliverd_lbs = []
        total_deliverd_values = []
        crop_get_check = []
        entry_feeds_obj = []
        grower_payee = GrowerPayee.objects.all()
        gg_id = [i.grower_idd for i in grower_payee]
        growers = Grower.objects.filter(id__in=gg_id).order_by('name')
        context['growers'] = growers
        if request.method == 'POST':
            grower_id = request.POST.get('grower_id')
            field_id = request.POST.get('field_id')
            grower_crop = request.POST.get('grower_crop')  
            if grower_id :
                context['selectedGrower'] = Grower.objects.get(id=grower_id)
                fields = Field.objects.filter(grower_id=grower_id).order_by('name')
                context['fields'] = fields
            if field_id and grower_id :
                selectedField = Field.objects.get(id=field_id)
                context['selectedField'] = selectedField
                context['selectedGrower'] = Grower.objects.get(id=grower_id)
                context['selectedCrop'] = Field.objects.get(id=field_id).crop
                if GrowerPayee.objects.filter(field_idd=field_id).filter(grower_idd=grower_id).exists() :
                    grower_payee_id = [i.id for i in GrowerPayee.objects.filter(field_idd=field_id).filter(grower_idd=grower_id)][0]
                    grower_payee = GrowerPayee.objects.get(id=grower_payee_id)
                    grower_payee_iddd = grower_payee.id
                    context['grower_payee_iddd'] = grower_payee_iddd
                    grower_payee_len = GrowerPayee.objects.filter(id=grower_payee_id)
                    start_date = request.POST.get('start_date')
                    end_date = request.POST.get('end_date')
                    if EntryFeeds.objects.filter(grower_id = grower_payee.grower_idd).exists() :
                        # entry_feeds = EntryFeeds.objects.get(grower_id = grower_payee.grower_idd)
                        total_grower_id = [grower_payee.grower_idd]
                        bale = BaleReportFarmField.objects.filter(ob2__in = total_grower_id).exclude(level='None')
                        grower_shipment = GrowerShipment.objects.filter(grower_id__in=total_grower_id).filter(crop='RICE').filter(status='APPROVED')
                        
                        # if start_date and end_date :
                            # Loop for Bale
                        for i in bale :
                            # cpb_lbs = entry_feeds.contract_base_price
                            # sp_lbs = entry_feeds.sustainability_premium
                            delivery_date = i.dt_class
                            delivery_id = i.bale_id
                            grower_name = i.ob3
                            crop = "COTTON"
                            # field = i.field_name
                            field = i.field_name
                            delivery_lbs = i.net_wt
                            # processor = i.classing.processor.entity_name
                            classs = i.level

                            # 13-04-23 (27-03-23)
                            if delivery_date :
                                str_date = str(delivery_date)
                                if '-' in str_date :
                                    try :
                                        str_date = str_date.split('-')
                                        mm = str_date[0]
                                        dd = str_date[1]
                                        yy = str_date[2]
                                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                                        finale_date = date(int(yyyy), int(mm), int(dd))
                                    except :
                                        continue
                                elif '/' in str_date :
                                    try :
                                        str_date = str_date.split('/')
                                        mm = str_date[0]
                                        dd = str_date[1]
                                        yy = str_date[2]
                                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                                        finale_date = date(int(yyyy), int(mm), int(dd))
                                    except :
                                        continue
                                else:
                                    finale_date = ''
                            else:
                                continue
                            # 13-04-23 (27-03-23)
                            check_entry = EntryFeeds.objects.filter(grower_id = i.ob2)
                            if len(check_entry) == 0 :
                                continue
                            if len(check_entry) == 1 :
                                var = EntryFeeds.objects.get(grower_id = i.ob2)
                            if len(check_entry) > 1 :
                                check_entry_with_date = EntryFeeds.objects.filter(grower_id = i.ob2,from_date__lte=finale_date,to_date__gte=finale_date)
                                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = i.ob2,from_date__isnull=True,to_date__isnull=True)
                                if check_entry_with_date.exists() :
                                    check_entry_id = [i.id for i in check_entry_with_date][0]
                                    var = EntryFeeds.objects.get(id = check_entry_id)
                                elif check_entry_with_no_date.exists() :
                                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                                    var = EntryFeeds.objects.get(id = check_entry_id)

                            # var = EntryFeeds.objects.get(grower_id = i.ob2)
                            cpb_lbs = var.contract_base_price
                            if cpb_lbs :
                                cpb_lbs = var.contract_base_price
                            else:
                                cpb_lbs = 0.0
                            sp_lbs = var.sustainability_premium
                            if sp_lbs :
                                sp_lbs = var.sustainability_premium
                            else:
                                sp_lbs = 0.0

                            # var = EntryFeeds.objects.get(grower_id = i.ob2)
                            # cpb_lbs = var.contract_base_price
                            # sp_lbs = var.sustainability_premium
                            if classs == 'Bronze' :
                                qp_lbs = 0.00
                            elif classs == "Silver":
                                qp_lbs = 0.02
                            elif classs == "Gold":
                                qp_lbs = 0.04
                            elif classs == "None":
                                qp_lbs = 0.00
                                                    
                            if classs != "None":
                                total_price = float(cpb_lbs) + float(sp_lbs) + float(qp_lbs)
                                delivered_value = float(delivery_lbs) * float(total_price)
                                if delivery_date :
                                    date_str = str(delivery_date).split("/")
                                    dd = int(date_str[1])
                                    mm = int(date_str[0])
                                    yy = int(date_str[2])
                                    if len(str(yy)) == 2 : 
                                        yyyy = int("20{}".format(yy))
                                    else:
                                        yyyy = yy
                                    specific_date = datetime(yyyy, mm, dd)
                                    new_date = specific_date + timedelta(60)
                                    payment_due_date = new_date.strftime("%m/%d/%y")
                                else:
                                    payment_due_date ="N/A"
                            else:
                                total_price = 0.00
                                delivered_value = 0.00
                                payment_due_date ="N/A"
                            
                            # Search by date range for bale
                            if start_date and end_date and selectedField.name == field :
                                start_date_var = start_date.split('-')
                                end_date_var = end_date.split('-')
                                d0 = date(int(start_date_var[0]), int(start_date_var[1]), int(start_date_var[2]))
                                d1 = date(int(end_date_var[0]), int(end_date_var[1]), int(end_date_var[2]))
                                delta = (d1 - d0).days
                                context['selected_start_date'] = str(start_date)
                                context['selected_end_date'] = str(end_date)
                                context['selected_start_date_low'] = f"{start_date_var[1]}/{start_date_var[2]}/{start_date_var[0]}"
                                context['selected_end_date_low'] = f"{end_date_var[1]}/{end_date_var[2]}/{end_date_var[0]}"

                                for i in range(0,delta + 1 ) :
                                    d_check = str(d0 + timedelta(days=i))
                                    dd_check = new_date.strftime("%Y-%m-%d")
                                    if d_check == dd_check :
                                        total_deliverd_lbs.append(int(float(delivery_lbs)))
                                        total_deliverd_values.append(float(delivered_value))
                                        crop_get_check.append('COTTON')
                                        data = {
                                                'delivery_date':delivery_date,
                                                'delivery_id':delivery_id,
                                                'grower_name':grower_name,
                                                'crop':crop,
                                                'variety':"-",
                                                'field':field,
                                                'delivery_lbs':delivery_lbs,
                                                'classs':classs,
                                                'total_price':"{0:.5f}".format(total_price),
                                                'delivered_value':"{0:.2f}".format(delivered_value),
                                                'payment_due_date':payment_due_date,
                                                # 'payment_air_tax':"{0:.2f}".format(int(delivered_value) * 0.00135),
                                                'payment_air_tax':"0.00",
                                                # 'payment_net_pay': "{0:.2f}".format(int(float(delivered_value)) - (int(delivered_value) * 0.00135)),
                                                'payment_net_pay': "{0:.2f}".format(delivered_value),
                                            }
                                        grower_payment.append(data)
                                        
                                    else:
                                        pass
                            # Cotton 
                            elif selectedField.name == field and len(start_date) == 0 and len(end_date) == 0 :
                                total_deliverd_lbs.append(int(float(delivery_lbs)))
                                total_deliverd_values.append(float(delivered_value))
                                crop_get_check.append('COTTON')
                                data = {
                                        'delivery_date':delivery_date,
                                        'delivery_id':delivery_id,
                                        'grower_name':grower_name,
                                        'crop':crop,
                                        'variety':"-",
                                        'field':field,
                                        'delivery_lbs':delivery_lbs,
                                        'classs':classs,
                                        'total_price':"{0:.5f}".format(total_price),
                                        'delivered_value':"{0:.2f}".format(delivered_value),
                                        'payment_due_date':payment_due_date,
                                        # 'payment_air_tax':"{0:.2f}".format(int(delivered_value) * 0.00135),
                                        'payment_air_tax':"0.00",
                                        'payment_net_pay': "{0:.2f}".format(delivered_value),
                                    }
                                grower_payment.append(data)
                                
                            else:
                                pass
                        # Loop For Shipment
                        for i in grower_shipment :
                            if i.approval_date == None:
                                process_date_int = i.process_date.strftime("%m/%d/%y")
                                delivery_date = process_date_int
                                new_date = i.process_date + timedelta(60)
                                payment_due_date = new_date.strftime("%m/%d/%y")
                                # 13-04-23 27-03-23
                                check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i.process_date,to_date__gte=i.process_date)
                                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
                                if check_entry_with_date.exists() :
                                    check_entry_id = [i.id for i in check_entry_with_date][0]
                                    var = EntryFeeds.objects.get(id=check_entry_id)
                                    entry_feeds_obj.append(var.contracted_payment_option)
                                elif check_entry_with_no_date.exists() :
                                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                                    var = EntryFeeds.objects.get(id = check_entry_id)
                                    entry_feeds_obj.append(var.contracted_payment_option)
                            else:
                                process_date_int = i.approval_date.strftime("%m/%d/%y")
                                delivery_date = process_date_int
                                new_date = i.approval_date + timedelta(60)
                                payment_due_date = new_date.strftime("%m/%d/%y")
                                # 13-04-23 27-03-23
                                check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i.approval_date,to_date__gte=i.approval_date)
                                check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
                                if check_entry_with_date.exists() :
                                    check_entry_id = [i.id for i in check_entry_with_date][0]
                                    var = EntryFeeds.objects.get(id=check_entry_id)
                                    entry_feeds_obj.append(var.contracted_payment_option)
                                elif check_entry_with_no_date.exists() :
                                    check_entry_id = [i.id for i in check_entry_with_no_date][0]
                                    var = EntryFeeds.objects.get(id = check_entry_id)
                                    entry_feeds_obj.append(var.contracted_payment_option)

                            delivery_id = i.shipment_id
                            grower_name = i.grower.name
                            grower_id = i.grower.id
                            crop = i.crop
                            variety = i.variety
                            field = i.field.name
                            
                            if var.contracted_payment_option == 'Fixed Price' :
                                cpb_lbs = var.contract_base_price
                                sp_lbs = var.sustainability_premium
                                total_price_init = float(cpb_lbs) + float(sp_lbs)
                                total_price = total_price_init
                                delivery_lbs = int(float(i.received_amount)) if i.received_amount != None else int(float(i.total_amount))
                                payment_air_tax = "{0:.2f}".format((int(delivery_lbs) * 0.0135)/45)
                            elif var.contracted_payment_option == 'Acreage Release' :
                                cpb_lbs = var.contract_base_price
                                sp_lbs = var.sustainability_premium
                                total_price_init = float(cpb_lbs) + float(sp_lbs)
                                total_price = total_price_init
                                payment_air_tax = 0.00
                            else:
                                calculation_date = i.approval_date
                                if NasdaqApiData.objects.filter(date_api=calculation_date).count() !=0 :
                                    total_price_init = NasdaqApiData.objects.get(date_api=calculation_date).close_value_api
                                else:
                                    for l in range(1,10):
                                        next_date = calculation_date - timedelta(l)
                                        if NasdaqApiData.objects.filter(date_api=next_date).count() !=0 :
                                            total_price_init = NasdaqApiData.objects.get(date_api=next_date).close_value_api
                                            break
                                delivery_lbs = int(float(i.received_amount)) if i.received_amount != None else int(float(i.total_amount))
                                payment_air_tax = "{0:.2f}".format((int(delivery_lbs) * 0.0135)/45)
                                total_price2 = float(total_price_init) / 100
                                total_price = total_price2 + 0.04
                            if i.received_amount != None :
                                delivery_lbs = int(float(i.received_amount)) 
                                delivered_value = float(delivery_lbs) * total_price
                            else:
                                delivery_lbs = int(float(i.total_amount))
                                delivered_value = float(delivery_lbs) * total_price
                            total_price = "{0:.5f}".format(total_price)
                            # Search by date range for shipment
                            if start_date and end_date and selectedField.name == field :
                                start_date_var = start_date.split('-')
                                end_date_var = end_date.split('-')
                                d0 = date(int(start_date_var[0]), int(start_date_var[1]), int(start_date_var[2]))
                                d1 = date(int(end_date_var[0]), int(end_date_var[1]), int(end_date_var[2]))
                                delta = (d1 - d0).days
                                context['selected_start_date'] = str(start_date)
                                context['selected_end_date'] = str(end_date)
                                context['selected_start_date_low'] = f"{start_date_var[1]}/{start_date_var[2]}/{start_date_var[0]}"
                                context['selected_end_date_low'] = f"{end_date_var[1]}/{end_date_var[2]}/{end_date_var[0]}"
                                for i in range(0,delta + 1 ) :
                                    d_check = str(d0 + timedelta(days=i))
                                    dd_check = new_date.strftime("%Y-%m-%d")
                                    if d_check == dd_check :
                                        data = {
                                                'delivery_date':delivery_date,
                                                'delivery_id':delivery_id,
                                                'grower_name':grower_name,
                                                'crop':crop,
                                                'variety':variety,
                                                'field':field,
                                                'delivery_lbs':delivery_lbs,
                                                'class':'-',
                                                'total_price':total_price,
                                                'delivered_value':"{0:.2f}".format(delivered_value),
                                                'payment_due_date':payment_due_date,
                                                # 'payment_air_tax':"{0:.2f}".format((int(delivery_lbs) * 0.0135)/45),
                                                'payment_air_tax':payment_air_tax,
                                                'payment_net_pay': "{0:.2f}".format(float(delivered_value) - float(payment_air_tax)),
                                            }
                                        grower_payment.append(data)
                                        total_deliverd_lbs.append(int(float(delivery_lbs)))
                                        total_deliverd_values.append(float(delivered_value))
                                        crop_get_check.append('RICE')
                                    else:
                                        pass
                            # Rice
                            elif selectedField.name == field and len(start_date) == 0 and len(end_date) == 0 :
                                data = {
                                        'delivery_date':delivery_date,
                                        'delivery_id':delivery_id,
                                        'grower_name':grower_name,
                                        'crop':crop,
                                        'variety':variety,
                                        'field':field,
                                        'delivery_lbs':delivery_lbs,
                                        'class':'-',
                                        'total_price':total_price,
                                        'delivered_value':"{0:.2f}".format(delivered_value),
                                        'payment_due_date':payment_due_date,
                                        # 'payment_air_tax':"{0:.2f}".format(int(delivered_value) * 0.00135),
                                        # 'payment_air_tax':"{0:.2f}".format((int(delivery_lbs) * 0.0135)/45),
                                        'payment_air_tax':payment_air_tax,
                                        'payment_net_pay': "{0:.2f}".format(float(delivered_value) - float(payment_air_tax)),
                                    }
                                grower_payment.append(data)
                                total_deliverd_lbs.append(int(float(delivery_lbs)))
                                total_deliverd_values.append(float(delivered_value))
                                crop_get_check.append('RICE')
                            else:
                                pass

                        context['grower_payee'] = grower_payee_len
                        context['payment_splits_crop'] = grower_payee.crop
                        payment_splits = PaymentSplits.objects.filter(grower_payee_id = grower_payee.id)
                        
                        # Payment Settlement Statement
                        context['payment_splits_crop'] = grower_payee.crop
                        context['payment_splits_grower'] = grower_payee.grower_namee
                        context['payment_splits_address'] = grower_payee.payee_physical_address
                        context['payment_splits_mail_address'] = grower_payee.payee_mailing_address
                        context['payment_splits_phone'] = grower_payee.payee_phone
                        context['payment_splits_email'] = grower_payee.payee_email
                        context['lien_status'] = grower_payee.lien_holder_status
                        
                        # Payment Splits .......
                        net_pay = 0
                        split_data = []
                        for i in payment_splits :
                            
                            if i.split_payee_type == "Lien" :
                                context['lien_Holer_name'] = i.split_payee_name
                                context['lien_Holer_address'] = i.split_payee_physical_address
                                context['lien_Holer_mail_address'] = i.split_payee_mailing_address
                                context['lien_Holer_phone'] = i.split_payee_phone
                                context['lien_Holer_email'] = i.split_payee_email
                            
                            elif i.split_payee_type == "Split" :
                                # split_data_payment_amount = (sum(total_deliverd_values) * 0.99865) * (int(float(i.split_payee_percent)) / 100)
                                # split_data_payment_amount = net pay * split % 
                                if 'COTTON' in crop_get_check :
                                    net_pay = sum(total_deliverd_values)
                                elif 'RICE' in crop_get_check :
                                    if 'Acreage Release' in entry_feeds_obj :
                                        ar_tax = 0.00
                                    else:
                                        ar_tax = sum(total_deliverd_values) * 0.00135
                                    net_pay = sum(total_deliverd_values) - ar_tax

                                # split_data_payment_amount = (sum(total_deliverd_values)) * (float(i.split_payee_percent) / 100)
                                split_data_payment_amount = net_pay * (float(i.split_payee_percent) / 100)
                                data = {
                                    "split_data_field_name" : i.grower_payee.field_namee,
                                    "split_data_split_percent" : i.split_payee_percent,
                                    "split_data_payment_amount" : "{0:.2f}".format(split_data_payment_amount),
                                    "split_data_entity_name" : i.split_payee_name,
                                    "split_data_address" : i.split_payee_physical_address,
                                    "split_data_mail_address" : i.split_payee_mailing_address,
                                    "split_data_tax_id" : i.split_payee_tax_id,
                                    "split_data_phone" : i.split_payee_phone,
                                }
                                split_data.append(data)
                        context['split_data'] = split_data
                        context['grower_payment'] = grower_payment 
                        context['delivery_lbs'] = sum(total_deliverd_lbs)   
                        context['delivered_value'] =  "{0:.2f}".format(sum(total_deliverd_values))  
                        
                        if 'COTTON' in crop_get_check :
                            ar_tax = "0.00"
                            context['ar_tax'] = ar_tax
                            net_pay = sum(total_deliverd_values)
                          
                        elif 'RICE' in crop_get_check :
                            entry_feeds_obj = list(set(entry_feeds_obj))
                            if 'Acreage Release' in entry_feeds_obj :
                                ar_tax = 0.00
                                context['ar_tax'] = ar_tax
                            else:
                                ar_tax = sum(total_deliverd_values) * 0.00135
                                context['ar_tax'] = "{0:.2f}".format(ar_tax)
                            net_pay = sum(total_deliverd_values) - ar_tax

                        context['net_pay'] = "{0:.2f}".format(net_pay)
                        context['today_date'] = date.today()
                else:
                    grower_payee = ''
            # 

        return render(request, "growerpayments/grower_split_payee_list.html",context)



@login_required()
def grower_split_payee_edit(request,grower_payee_iddd):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        grower_payee = GrowerPayee.objects.get(id=grower_payee_iddd)
        context['grower_payee'] = grower_payee
        lien = PaymentSplits.objects.filter(grower_payee_id = grower_payee_iddd).filter(split_payee_type = 'Lien')
        
        split = PaymentSplits.objects.filter(grower_payee_id = grower_payee_iddd).filter(split_payee_type = 'Split').order_by('id')
        if lien.exists() :
            lien_id = [i.id for i in lien][0]
            lien_get = PaymentSplits.objects.get(id=lien_id)
            context['lien'] = lien_get
        if split.exists() :
            split = split
            context['split'] = split
        if request.method == 'POST':
            payee_entity_name = request.POST.get('payee_entity_name')
            payee_tax_id = request.POST.get('payee_tax_id')
            payee_physical_address = request.POST.get('payee_physical_address')
            payee_mailing_address = request.POST.get('payee_mailing_address')
            payee_phone = request.POST.get('payee_phone')
            payee_email = request.POST.get('payee_email')
            lien_holder_satus = request.POST.get('lien_holder')
            payment_splits_satus = request.POST.get('payment_splits')

            lien_name = request.POST.get('lien_name')
            lien_tax_id = request.POST.get('lien_tax_id')
            lien_physical_add = request.POST.get('lien_physical_add')
            lien_mailing = request.POST.get('lien_mailing')
            lien_contact_person = request.POST.get('lien_contact_person')
            lien_phone = request.POST.get('lien_phone')
            lien_email = request.POST.get('lien_email')
            lien_split_payee_percentage = request.POST.get('lien_split_payee_percentage')

            ccounter = request.POST.get('counter')

            grower_payee.payee_entity_name =payee_entity_name
            grower_payee.payee_tax_id =payee_tax_id
            grower_payee.payee_physical_address =payee_physical_address
            grower_payee.payee_mailing_address =payee_mailing_address
            grower_payee.payee_phone =payee_phone

            grower_payee.payee_email =payee_email
            
            if lien_holder_satus == 'YES' :
                grower_payee.lien_holder_status = 'YES'
                if lien.exists() :
                    lien_get.split_payee_name = lien_name
                    lien_get.split_payee_tax_id = lien_tax_id
                    lien_get.split_payee_physical_address = lien_physical_add
                    lien_get.split_payee_mailing_address = lien_mailing
                    lien_get.split_payee_contact_person = lien_contact_person
                    lien_get.split_payee_phone = lien_phone
                    lien_get.split_payee_email = lien_email
                    lien_get.split_payee_percent = lien_split_payee_percentage
                    lien_get.save()
                                        
                else:
                    payment_split = PaymentSplits(grower_payee_id=grower_payee.id,split_payee_name=lien_name,split_payee_tax_id=lien_tax_id,
                    split_payee_physical_address=lien_physical_add,split_payee_mailing_address=lien_mailing,split_payee_contact_person=lien_contact_person,
                    split_payee_phone=lien_phone,split_payee_email=lien_email,split_payee_percent=lien_split_payee_percentage,
                    split_payee_type='Lien')
                    payment_split.save()
                    grower_payee.lien_holder_status = 'YES'
                    grower_payee.save()
                    
            else :
                lien.delete()
                grower_payee.lien_holder_status = 'NO'
                grower_payee.save()
            
            # 20-04-23 LogTable
            status_lien_holder_status = "YES" if lien_holder_satus == 'YES' else "NO"
            status_payment_split_status = "YES" if payment_splits_satus == 'YES' else "NO"
            log_type, log_status, log_device = "GrowerPayee", "Edited", "Web"
            log_idd, log_name = grower_payee.id, f"{grower_payee.grower_namee} - {grower_payee.field_namee}"
            log_details = f"grower = {grower_payee.grower_namee} | grower_id = {grower_payee.grower_idd} | field = {grower_payee.field_namee} | field_id = {grower_payee.field_idd} | crop = {grower_payee.crop} | payee_entity_name = {grower_payee.payee_entity_name} | payee_tax_id = {grower_payee.payee_tax_id} | payee_physical_address = {grower_payee.payee_physical_address} | payee_mailing_address = {grower_payee.payee_mailing_address} | payee_phone = {grower_payee.payee_phone} | payee_email = {grower_payee.payee_email} | lien_holder_status ={status_lien_holder_status} | payment_split_status = {status_payment_split_status} | net_payee = {grower_payee.net_payee} |"
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
                                action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                log_device=log_device)
            logtable.save()

            if payment_splits_satus == 'YES' :
                grower_payee.payment_split_status = 'YES'
                grower_payee.save()
                for i in range(1,len(split)+1) :
                    split_name = request.POST.get('split_name_{}'.format(i))
                    split_tax_id = request.POST.get('split_tax_id_{}'.format(i))
                    split_physical_add = request.POST.get('split_physical_add_{}'.format(i))
                    split_mailing = request.POST.get('split_mailing_{}'.format(i))
                    split_contact_person = request.POST.get('split_contact_person_{}'.format(i))
                    split_phone = request.POST.get('split_phone_{}'.format(i))
                    split_email = request.POST.get('split_email_{}'.format(i))
                    split_split_payee_percentage = request.POST.get('split_split_payee_percentage_{}'.format(i))
                    split_id = split[i-1].id
                    ss = PaymentSplits.objects.get(id=split_id)
                    ss.split_payee_name = split_name
                    ss.split_payee_tax_id = split_tax_id
                    ss.split_payee_physical_address = split_physical_add
                    ss.split_payee_mailing_address = split_mailing
                    ss.split_payee_contact_person = split_contact_person
                    ss.split_payee_phone = split_phone
                    ss.split_payee_email = split_email
                    ss.split_payee_percent = split_split_payee_percentage
                    ss.save()
                    
                    
                if int(ccounter) > 1 :
                        for i in range(2,int(ccounter)+1) :
                            split_name = request.POST.get('split_name{}'.format(i))
                            split_tax_id = request.POST.get('split_tax_id{}'.format(i))
                            split_physical_add = request.POST.get('split_physical_add{}'.format(i))
                            split_mailing = request.POST.get('split_mailing{}'.format(i))
                            split_contact_person = request.POST.get('split_contact_person{}'.format(i))
                            split_phone = request.POST.get('split_phone{}'.format(i))
                            split_email = request.POST.get('split_email{}'.format(i))
                            split_split_payee_percentage = request.POST.get('split_split_payee_percentage{}'.format(i))
                            payment_split = PaymentSplits(grower_payee_id=grower_payee.id,split_payee_name=split_name,split_payee_tax_id=split_tax_id,
                            split_payee_physical_address=split_physical_add,split_payee_mailing_address=split_mailing,split_payee_contact_person=split_contact_person,
                            split_payee_phone=split_phone,split_payee_email=split_email,split_payee_percent=split_split_payee_percentage,
                            split_payee_type='Split')
                            payment_split.save()
            else:
                for i in range(len(split)) :
                    split_id = split[i].id
                    PaymentSplits.objects.get(id=split_id).delete()
            return redirect ('grower_payment_split_list')
        return render(request, "growerpayments/grower_split_payee_edit.html",context)



@login_required()
def grower_payment_split_list(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        grower_payee = GrowerPayee.objects.all().order_by('-id')
        grower_payee_lst = []
        for i in grower_payee :
            lien = PaymentSplits.objects.filter(grower_payee_id = i.id).filter(split_payee_type = 'Lien')
            split = PaymentSplits.objects.filter(grower_payee_id = i.id).filter(split_payee_type = 'Split').order_by('id')
            if lien.exists() :
                lien_id = [i.id for i in lien][0]
                lien_name = PaymentSplits.objects.get(id=lien_id).split_payee_name
            else:
                lien_name = 'N/A'
            if split.exists() :
                split_conut = len(split)
            else:
                split_conut = 'N/A'
            data = {
                "grower_namee" : i.grower_namee,
                "field_namee" : i.field_namee,
                "lien_name" : lien_name,
                "split_conut" : split_conut,
                "id" : i.id,
            }
            grower_payee_lst.append(data)
        context['grower_payee_lst'] = grower_payee_lst
        return render(request, "growerpayments/grower_payment_split_list.html",context)


@login_required()
def grower_split_payee_delete(request,pk):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        gp = GrowerPayee.objects.get(id=pk)
        # 20-04-23 LogTable
        log_type, log_status, log_device = "GrowerPayee", "Deleted", "Web"
        log_idd, log_name = gp.id, f"{gp.grower_namee} - {gp.field_namee}"
        log_details = f"grower = {gp.grower_namee} | grower_id = {gp.grower_idd} | field = {gp.field_namee} | field_id = {gp.field_idd} | crop = {gp.crop} | payee_entity_name = {gp.payee_entity_name} | payee_tax_id = {gp.payee_tax_id} | payee_physical_address = {gp.payee_physical_address} | payee_mailing_address = {gp.payee_mailing_address} | payee_phone = {gp.payee_phone} | payee_email = {gp.payee_email} | lien_holder_status ={gp.lien_holder_status} | payment_split_status = {gp.payment_split_status} | net_payee = {gp.net_payee} |"
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
                            action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                            log_device=log_device)
        logtable.save()
        gp.delete()
        return HttpResponse (1)

@login_required()
def split_payee_block_delete(request,id):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        ps = PaymentSplits.objects.get(id=id)
        # 20-04-23 LogTable
        status_lien_holder_status = "YES" if ps.split_payee_type == 'Lien' else "NO"
        status_payment_split_status = "YES" if ps.split_payee_type == 'Split' else "NO"
        log_type, log_status, log_device = "GrowerPayee", "Edited", "Web"
        log_idd, log_name = ps.grower_payee.id, f"{ps.grower_payee.grower_namee} - {ps.grower_payee.field_namee}"
        log_details = f"grower = {ps.grower_payee.grower_namee} | grower_id = {ps.grower_payee.grower_idd} | field = {ps.grower_payee.field_namee} | field_id = {ps.grower_payee.field_idd} | crop = {ps.grower_payee.crop} | payee_entity_name = {ps.grower_payee.payee_entity_name} | payee_tax_id = {ps.grower_payee.payee_tax_id} | payee_physical_address = {ps.grower_payee.payee_physical_address} | payee_mailing_address = {ps.grower_payee.payee_mailing_address} | payee_phone = {ps.grower_payee.payee_phone} | payee_email = {ps.grower_payee.payee_email} | lien_holder_status ={status_lien_holder_status} | payment_split_status = {status_payment_split_status} | net_payee = {ps.grower_payee.net_payee} |"
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
                            action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                            log_device=log_device)
        logtable.save()
        ps.delete()
        return HttpResponse (1)

@login_required()
def classing_invoice_bundle_zip(request,pk):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        bale = BaleReportFarmField.objects.filter(ob2=pk).exclude(level='None')
        grower_name = Grower.objects.get(id=pk).name
        bronze_id = []
        silver_id = []
        gold_id = []
        llano_super_id = []

        bronze_bale_id = []
        silver_bale_id = []
        gold_bale_id = []
        llano_super_bale_id = []
        for i in bale :
            delivery_id = i.bale_id
            classs = i.level                                    
            gpay = GrowerPayments.objects.filter(delivery_id=delivery_id)
            if gpay.exists() :
                pass
            else:
                if classs == 'Bronze' :
                    bronze_id.append(i.id)
                elif classs == "Silver":
                    silver_id.append(i.id)
                elif classs == "Gold":
                    gold_id.append(i.id)
                elif classs == "Llano Super":
                    llano_super_id.append(i.id)

        scripts = []

        response = HttpResponse(content_type='application/zip')
        zf = ZipFile(response, 'w')
        ZIPFILE_NAME = "{}.zip".format(grower_name) 
        

        if len(bronze_id) > 0 :
            for i in bronze_id :
                bale = BaleReportFarmField.objects.get(id=i).bale_id
                bronze_bale_id.append("{}".format(bale))
            
            
        if len(silver_id) > 0 :
            for i in silver_id :
                bale = BaleReportFarmField.objects.get(id=i).bale_id
                silver_bale_id.append("{}".format(bale))
            

        if len(gold_id) > 0 :
            for i in gold_id :
                bale = BaleReportFarmField.objects.get(id=i).bale_id
                gold_bale_id.append("{}".format(bale))
        
        if len(llano_super_id) > 0 :
            for i in llano_super_id :
                bale = BaleReportFarmField.objects.get(id=i).bale_id
                llano_super_bale_id.append("{}".format(bale))
                

        if len(bronze_id) > 0 :
            result1 = '\n'.join(map(str, bronze_bale_id))
            zf.writestr("{}_bronze.txt".format(grower_name),result1)

        if len(silver_id) > 0 :
            result2 = '\n'.join(map(str, silver_bale_id))
            zf.writestr("{}_silver.txt".format(grower_name),result2)

        if len(gold_id) > 0 :
            result3 = '\n'.join(map(str, gold_bale_id))
            zf.writestr("{}_gold.txt".format(grower_name),result3)

        if len(llano_super_id) > 0 :
            result4 = '\n'.join(map(str, llano_super_bale_id))
            zf.writestr("{}_super.txt".format(grower_name),result4)

        response['Content-Disposition'] = f'attachment; filename={ZIPFILE_NAME}'
        return response


@login_required()
def processor_grower_certificate_level_status(request) :
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        selectedprocessor = 'All'
        context['selectedprocessor']  = selectedprocessor
        selectedgrower = 'All'
        context['selectedgrower']  = selectedgrower
        selectedLel = 'All'
        context['selectedLel']  = selectedLel
        selectedCre = 'All'
        context['selectedCre']  = selectedCre
        selectedpayment = 'All'
        context['selectedpayment']  = selectedpayment
        proSelction = request.GET.get('proSelction')
        cerSelction = request.GET.get('cerSelction')
        lelSelction = request.GET.get('lelSelction')
        paymentSelction = request.GET.get('paymentSelction')
        groSelction = request.GET.get('groSelction')

        context['processors']  = Processor.objects.all().order_by('entity_name')
        context['growers']  = Grower.objects.all().order_by('name')
        
        if proSelction == 'All' and groSelction == 'All' and cerSelction == 'All' and lelSelction == 'All' and paymentSelction == 'All' :
            # bale = BaleReportFarmField.objects.all()
            bale = BaleReportFarmField.objects.filter(id__isnull = False)

        elif proSelction == None and groSelction == None and cerSelction == None and lelSelction == None and paymentSelction == None :
            bale = BaleReportFarmField.objects.filter(id__isnull = False)
        # elif proSelction != 'All' or cerSelction != 'All' or lelSelction != 'All' or paymentSelction != 'All' :
        else:
            bale = BaleReportFarmField.objects.filter(id__isnull = False)
            if proSelction != 'All' :
                selectedprocessor = Processor.objects.filter(id=proSelction)
                if selectedprocessor.exists() :
                    selectedprocessor = Processor.objects.get(id=proSelction)
                    context['selectedprocessor']  = selectedprocessor
                    classing_obj = ClassingReport.objects.filter(processor_id = selectedprocessor.id)
                    classing_id = [i.id for i in classing_obj]
                    bale = bale.filter(classing_id__in = classing_id)
            
            if groSelction != 'All' :
                check_grower = Grower.objects.filter(id=groSelction)
                if check_grower.exists() :
                    selectedgrower= Grower.objects.get(id=groSelction)
                    bale = bale.filter(ob2=groSelction)
                    context['selectedgrower']  = selectedgrower

            if cerSelction != 'All' :
                if cerSelction == "None" :
                    context['selectedCre']  = cerSelction
                    cerSelction = [cerSelction]
                    bale = bale.filter(ob5=None)
                else:
                    context['selectedCre']  = cerSelction
                    cerSelction = [cerSelction]
                    bale = bale.filter(ob5__in = cerSelction)
                                
            if lelSelction != 'All' :
                context['selectedLel']  = lelSelction
                lelSelction = [lelSelction]
                bale = bale.filter(level__in = lelSelction)

            if paymentSelction != 'All' :
                if paymentSelction == 'Paid' :
                    context['selectedpayment']  = paymentSelction
                    g_pay_exsit = GrowerPayments.objects.all()
                    delivery_id = [i.delivery_id for i in g_pay_exsit]
                    bale = bale.filter(bale_id__in = delivery_id)

                elif paymentSelction == 'Unpaid' :
                    context['selectedpayment']  = paymentSelction
                    g_pay_exsit = GrowerPayments.objects.all()
                    delivery_id = [i.delivery_id for i in g_pay_exsit]
                    bale = bale.exclude(bale_id__in = delivery_id)
        if len(bale) == 0 :
            data_text = 'No Record Found'
            context['data_text']  = data_text
            
        paginator = Paginator(bale, 100)
        page = request.GET.get('page')
        try:
            report = paginator.page(page)
        except PageNotAnInteger:
            report = paginator.page(1)
        except EmptyPage:
            report = paginator.page(paginator.num_pages)  
        context['grower_payment']  = report
        
        return render(request, "growerpayments/processor_grower_certificate_level_status.html",context)


@login_required()
def processor_grower_certificate_level_status_csv_download(request,selectedprocessor,selectedgrower,selectedLel,selectedCre,selectedpayment) :
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        if selectedprocessor != 'All' and selectedgrower != 'All' :
            filename = f'{selectedprocessor}_{selectedgrower}.csv'
        elif selectedprocessor != 'All' :
            filename = f'{selectedprocessor}.csv'
        elif selectedgrower != 'All' :
            filename = f'{selectedgrower}.csv'
        else:
            filename = 'Bale info for Gin.csv'
        if selectedprocessor == 'All' and selectedgrower == 'All' and selectedCre == 'All' and selectedLel == 'All' and selectedpayment == 'All' :
            # bale = BaleReportFarmField.objects.all()
            bale = BaleReportFarmField.objects.filter(id__isnull = False)

        elif selectedprocessor == None and selectedgrower == None and selectedCre == None and selectedLel == None and selectedpayment == None :
            bale = BaleReportFarmField.objects.filter(id__isnull = False)
        # elif proSelction != 'All' or cerSelction != 'All' or lelSelction != 'All' or paymentSelction != 'All' :
        else:
            bale = BaleReportFarmField.objects.filter(id__isnull = False)
            if selectedprocessor != 'All' :
                # filename = f'{selectedprocessor}.csv'
                get_processor = Processor.objects.filter(entity_name=selectedprocessor)
                if get_processor.exists() :
                    selectedprocessor = Processor.objects.get(entity_name=selectedprocessor)
                    classing_obj = ClassingReport.objects.filter(processor_id = selectedprocessor.id)
                    classing_id = [i.id for i in classing_obj]
                    bale = bale.filter(classing_id__in = classing_id)

            if selectedgrower != 'All' :
                check_grower = Grower.objects.filter(name=selectedgrower)
                if check_grower.exists() :
                    selectedgrower_id= Grower.objects.get(name=selectedgrower).id
                    bale = bale.filter(ob2=selectedgrower_id)

            if selectedCre != 'All' :
                if selectedCre == "None" :
                    selectedCre = [selectedCre]
                    bale = bale.filter(ob5=None)
                else:
                    selectedCre = [selectedCre]
                    bale = bale.filter(ob5__in = selectedCre)
                                
            if selectedLel != 'All' :
                selectedLel = [selectedLel]
                bale = bale.filter(level__in = selectedLel)

            if selectedpayment != 'All' :
                if selectedpayment == 'Paid' :
                    g_pay_exsit = GrowerPayments.objects.all()
                    delivery_id = [i.delivery_id for i in g_pay_exsit]
                    bale = bale.filter(bale_id__in = delivery_id)

                elif selectedpayment == 'Unpaid' :
                    g_pay_exsit = GrowerPayments.objects.all()
                    delivery_id = [i.delivery_id for i in g_pay_exsit]
                    bale = bale.exclude(bale_id__in = delivery_id)

        # filename = 'Bale info for Gin.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        
        writer.writerow(['BALE ID','PROCESSOR','GROWER', 'LEVEL', 'CERTIFICATE','NET WT', 'FARM', 'FIELD','PAYMENT'])

        for i in bale :
            if i.ob5 :
                cer = i.ob5
            else:
                cer = 'None'
            g_pay_exsit = GrowerPayments.objects.filter(delivery_id = i.bale_id)
            if g_pay_exsit.exists() :
                p_status = 'Paid'
            else:
                p_status = 'Due'
            writer.writerow([i.bale_id,i.classing.processor.entity_name,i.ob3,i.level,cer,i.net_wt,i.farm_name,i.field_name,p_status])
            
           
        return response
        # return HttpResponse (1)



