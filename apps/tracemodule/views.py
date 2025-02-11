from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from apps.field.models import *
from apps.farms.models import *
from apps.grower.models import *
from apps.processor.models import *
from apps.processor2.models import *
import csv
from django.db.models import Q, Case, When, Value, F, OuterRef, Subquery, CharField, BigIntegerField
from itertools import chain
from operator import itemgetter
from django.db.models.functions import Cast
import datetime
import requests
from datetime import date
from apps.warehouseManagement.models import *
from django.conf import settings

from django.utils.timezone import make_aware, is_naive
from datetime import datetime

def format_date(date_input):
    if not date_input:
        return ""
    try:
        # Handle naive datetime
        if isinstance(date_input, datetime) and is_naive(date_input):
            date_input = make_aware(date_input)
        
        # Format date to "25th August, 2024"
        day = date_input.day
        suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return f"{day}{suffix} {date_input.strftime('%B, %Y')}"
    except Exception as e:
        return str(date_input)
    

def get_Origin_deliveryid(crop,field_id,field_name,bale_id,warehouse_wh_id) :
    if type(field_id) != None and field_id !=  None :
        get_field = Field.objects.get(id=field_id)
    elif type(field_name) != None and field_name !=  None :
        get_field = Field.objects.get(id=field_id)
    else:
        get_field = ''
    variety = get_field.variety if get_field.variety else ''
    field_name = get_field.name if get_field.name else ''
    field_id = get_field.id if get_field.id else ''
    projected_yeild = float(get_field.total_yield) if get_field.total_yield else ''
    reported_yeild = ''
    yield_delta = ''
    harvest_date = get_field.harvest_date if get_field.harvest_date else ''
    water_savings = get_field.gal_water_saved if get_field.gal_water_saved else ''
    water_per_pound_savings = get_field.water_lbs_saved if get_field.water_lbs_saved else ''
    land_use = get_field.land_use_efficiency if get_field.land_use_efficiency else ''
    less_GHG = get_field.ghg_reduction if get_field.ghg_reduction else ''
    co2_eQ_footprint = get_field.co2_eq_reduced if get_field.co2_eq_reduced else ''
    premiums_to_growers = get_field.grower_premium_percentage if get_field.grower_premium_percentage else ''
    surveyscore1 = get_field.get_survey1()
    surveyscore2 = get_field.get_survey2()
    surveyscore3 = get_field.get_survey3()
    if surveyscore1 != '' and surveyscore1 != None :
        surveyscore1 = float(surveyscore1)
    else:
        surveyscore1 = 0
    if surveyscore2 != '' and surveyscore2 != None :
        surveyscore2 = float(surveyscore2)
    else:
        surveyscore2 = 0
    if surveyscore3 != '' and surveyscore3 != None :
        surveyscore3 = float(surveyscore3)
    else:
        surveyscore3 = 0
    composite_score = round((surveyscore1*0.25)+(surveyscore2*0.50)+(surveyscore3*0.25),2)
    
    if crop == "COTTON":
        if composite_score >= 75:
            pf_sus = "Pass"
        elif composite_score < 75:
            pf_sus = "Fail"
    else:        
        if composite_score >= 70:
            pf_sus = "Pass"
        elif composite_score < 70:
            pf_sus = "Fail"

    if crop == 'COTTON' :
        get_bale = BaleReportFarmField.objects.filter(bale_id=bale_id,warehouse_wh_id=warehouse_wh_id)
        if len(get_bale) == 1 :
            get_bale_id = [i.id for i in get_bale][0]
            get_bale = BaleReportFarmField.objects.get(id=get_bale_id)
            reported_yeild = float(get_bale.net_wt.strip())
            pf_sus = get_bale.ob5
            level = get_bale.level
            grade = get_bale.gr
            leaf = get_bale.lf
            staple = get_bale.st
            length = get_bale.len_num
            strength = get_bale.str_no
            mic = get_bale.mic
            storage_quanitty = get_bale.net_wt
            if get_field.total_yield :
                projected_yeild = float(get_field.total_yield)
                reported_yeild = reported_yeild
                yield_delta = reported_yeild - projected_yeild
            else :
                projected_yeild = ''
                reported_yeild = reported_yeild
                yield_delta = ''
        #  search by Field 
        else:
            if get_field.total_yield :
                projected_yeild = float(get_field.total_yield)
            else:
                projected_yeild = ''
            reported_yeild = ''
            yield_delta = ''
            level = ''
            grade = ''
            leaf = ''
            staple = ''
            length = ''
            strength = ''
            mic = ''
            storage_quanitty = ''
    else :
        shipment = GrowerShipment.objects.filter(shipment_id=bale_id, crop=crop)
        if shipment.exists() :
            shipment = GrowerShipment.objects.get(shipment_id=bale_id, crop=crop)
            variety = shipment.variety
            field_name = shipment.field.name
            field_id = shipment.field.id
            reported_yeild = shipment.total_amount
            storage_quanitty = shipment.total_amount

            if get_field.total_yield :
                projected_yeild = float(get_field.total_yield)
                reported_yeild = float(reported_yeild)
                yield_delta = reported_yeild - projected_yeild
            else :
                projected_yeild = ''
                reported_yeild = reported_yeild
                yield_delta = ''
        else:
            pass
        level = ''
        grade = ''
        leaf = ''
        staple = ''
        length = ''
        strength = ''
        mic = ''
        storage_quanitty = ''
    return [{"get_select_crop":crop,"variety":variety,"field_name":field_name,"field_id":field_id,"grower_name":get_field.grower.name,
        "grower_id":get_field.grower.id,"farm_name":get_field.farm.name,"farm_id":get_field.farm.id,
        "harvest_date":harvest_date,"projected_yeild":projected_yeild,"reported_yeild":reported_yeild,"yield_delta":yield_delta,
        "pf_sus":pf_sus,"water_savings":water_savings,"water_per_pound_savings":water_per_pound_savings,"land_use":land_use,
        "less_GHG":less_GHG,"co2_eQ_footprint":co2_eQ_footprint,"premiums_to_growers":premiums_to_growers,"level":level,
        "grade":grade,"leaf":leaf,"staple":staple,"length":length,"strength":strength,"mic":mic,"storage_quanitty":storage_quanitty}]


def Origin_searchby_Grower(crop,search_text,*grower_field_ids):
    return_lst = []
    if crop == 'COTTON' :
        for i in grower_field_ids :
            get_field = Field.objects.get(id=i)
            grower_name = get_field.grower.name
            grower_id = get_field.grower.id
            variety = get_field.variety
            field_name = get_field.name
            field_id = get_field.id
            farm_name = get_field.farm.name
            farm_id = get_field.farm.id
            harvest_date = get_field.harvest_date
            projected_yeild = get_field.total_yield
            storage_quanitty = get_field.total_yield
            water_savings = get_field.gal_water_saved
            land_use = get_field.land_use_efficiency
            less_GHG = get_field.ghg_reduction
            premiums_to_growers = get_field.grower_premium_percentage

            water_per_pound_savings = get_field.water_lbs_saved
            co2_eQ_footprint = get_field.co2_eq_reduced
            surveyscore1 = get_field.get_survey1()
            surveyscore2 = get_field.get_survey2()
            surveyscore3 = get_field.get_survey3()
            if surveyscore1 != '' and surveyscore1 != None :
                surveyscore1 = float(surveyscore1)
            else:
                surveyscore1 = 0
            if surveyscore2 != '' and surveyscore2 != None :
                surveyscore2 = float(surveyscore2)
            else:
                surveyscore2 = 0
            if surveyscore3 != '' and surveyscore3 != None :
                surveyscore3 = float(surveyscore3)
            else:
                surveyscore3 = 0
            composite_score = round((surveyscore1*0.25)+(surveyscore2*0.50)+(surveyscore3*0.25),2)
            
            if crop == "COTTON":
                if composite_score >= 75:
                    pf_sus = "Pass"
                elif composite_score < 75:
                    pf_sus = "Fail"
            else:
                if composite_score >= 70:
                    pf_sus = "Pass"
                elif composite_score < 70:
                    pf_sus = "Fail"

            if projected_yeild :
                projected_yeild = float(get_field.total_yield)
                bale = BaleReportFarmField.objects.filter(ob4=get_field.id)
                
                if bale.exists() :
                    reported_yeild_lst = []
                    for j in bale :
                        var_wt = j.net_wt.strip()
                        
                        try:
                            cotton_net_wt = float(var_wt)
                        except:
                            cotton_net_wt = 0
                        reported_yeild_lst.append(cotton_net_wt)
                    reported_yeild = float(sum(reported_yeild_lst))
                    yield_delta = projected_yeild - reported_yeild
                else:
                    reported_yeild = 'None'
                    yield_delta = 'None'
            else:
                projected_yeild = 'None'
                reported_yeild = 'None'
                yield_delta = 'None'
            return_lst.extend([{"get_select_crop":'COTTON', "variety":variety, "field_name":field_name, "field_id":field_id, 
                                "grower_name":grower_name, "grower_id":grower_id, "farm_name":farm_name, "farm_id":farm_id,
                                "harvest_date":harvest_date if harvest_date else '', "projected_yeild":projected_yeild, "reported_yeild":reported_yeild,
                                "yield_delta":yield_delta, "storage_quanitty":storage_quanitty,"pf_sus":pf_sus,"water_savings":water_savings,"water_per_pound_savings":water_per_pound_savings,"land_use":land_use,
                                "less_GHG":less_GHG,"co2_eQ_footprint":co2_eQ_footprint,"premiums_to_growers":premiums_to_growers}])
    else:
        
        for i in grower_field_ids :
            get_field = Field.objects.get(id=i)
            grower_name = get_field.grower.name
            grower_id = get_field.grower.id
            variety = get_field.variety
            field_name = get_field.name
            field_id = get_field.id
            farm_name = get_field.farm.name
            farm_id = get_field.farm.id
            harvest_date = get_field.harvest_date
            projected_yeild = get_field.total_yield
            storage_quanitty = get_field.total_yield
            water_savings = get_field.gal_water_saved
            land_use = get_field.land_use_efficiency
            less_GHG = get_field.ghg_reduction
            premiums_to_growers = get_field.grower_premium_percentage

            water_per_pound_savings = get_field.water_lbs_saved
            co2_eQ_footprint = get_field.co2_eq_reduced

            surveyscore1 = get_field.get_survey1()
            surveyscore2 = get_field.get_survey2()
            surveyscore3 = get_field.get_survey3()
            if surveyscore1 != '' and surveyscore1 != None :
                surveyscore1 = float(surveyscore1)
            else:
                surveyscore1 = 0
            if surveyscore2 != '' and surveyscore2 != None :
                surveyscore2 = float(surveyscore2)
            else:
                surveyscore2 = 0
            if surveyscore3 != '' and surveyscore3 != None :
                surveyscore3 = float(surveyscore3)
            else:
                surveyscore3 = 0
            composite_score = round((surveyscore1*0.25)+(surveyscore2*0.50)+(surveyscore3*0.25),2)
            
            if crop == "COTTON":
                if composite_score >= 75:
                    pf_sus = "Pass"
                elif composite_score < 75:
                    pf_sus = "Fail"
            else:
                if composite_score >= 70:
                    pf_sus = "Pass"
                elif composite_score < 70:
                    pf_sus = "Fail"

            if projected_yeild :
                projected_yeild = float(get_field.total_yield)
                bale = GrowerShipment.objects.filter(field_id=get_field,status="APPROVED", crop=crop)
                if bale.exists() :
                    reported_yeild_lst = []
                    for j in bale :
                        var_wt = j.received_amount.strip()
                        try:
                            rice_net_wt = float(var_wt)
                        except:
                            rice_net_wt = 0
                        reported_yeild_lst.append(rice_net_wt)
                    reported_yeild = float(sum(reported_yeild_lst))
                    yield_delta = projected_yeild - reported_yeild
                else:
                    reported_yeild = 'None'
                    yield_delta = 'None'
            else:
                projected_yeild = 'None'
                reported_yeild = 'None'
                yield_delta = 'None'
            return_lst.extend([{"get_select_crop":crop, "variety":variety, "field_name":field_name, "field_id":field_id, 
                                "grower_name":grower_name, "grower_id":grower_id, "farm_name":farm_name, "farm_id":farm_id,
                                "harvest_date":harvest_date if harvest_date else '', "projected_yeild":projected_yeild, "reported_yeild":reported_yeild,
                                "yield_delta":yield_delta, "storage_quanitty":storage_quanitty if storage_quanitty else '',"pf_sus":pf_sus,"water_savings":water_savings,"water_per_pound_savings":water_per_pound_savings,"land_use":land_use,
                                "less_GHG":less_GHG,"co2_eQ_footprint":co2_eQ_footprint,"premiums_to_growers":premiums_to_growers}])
    return return_lst


def Origin_searchby_Processor(crop,*bale_id):
    return_lst = []
    if crop == 'COTTON' :
        for i in bale_id :
            get_bale = BaleReportFarmField.objects.get(id=i)
            variety = get_bale.crop_variety
            field_name = get_bale.field_name
            field_id = get_bale.ob4
            grower_name = get_bale.ob3
            grower_id = get_bale.ob2
            farm_name = get_bale.farm_name
            reported_yeild = get_bale.net_wt
            storage_quanitty = reported_yeild
            farm_id = ''
            harvest_date = ''
            projected_yeild = ''
            yield_delta = ''
            water_savings = ''
            land_use = ''
            less_GHG = ''
            premiums_to_growers = ''
            water_per_pound_savings = ''
            co2_eQ_footprint = ''
            pf_sus = ''
            if field_id :
                try :
                    get_field = Field.objects.get(id=field_id)
                    water_savings = get_field.gal_water_saved
                    land_use = get_field.land_use_efficiency
                    less_GHG = get_field.ghg_reduction
                    premiums_to_growers = get_field.grower_premium_percentage
                    water_per_pound_savings = get_field.water_lbs_saved
                    co2_eQ_footprint = get_field.co2_eq_reduced
                    harvest_date = get_field.harvest_date
                    projected_yeild = get_field.total_yield
                    surveyscore1 = get_field.get_survey1()
                    surveyscore2 = get_field.get_survey2()
                    surveyscore3 = get_field.get_survey3()
                    if surveyscore1 != '' and surveyscore1 != None :
                        surveyscore1 = float(surveyscore1)
                    else:
                        surveyscore1 = 0
                    if surveyscore2 != '' and surveyscore2 != None :
                        surveyscore2 = float(surveyscore2)
                    else:
                        surveyscore2 = 0
                    if surveyscore3 != '' and surveyscore3 != None :
                        surveyscore3 = float(surveyscore3)
                    else:
                        surveyscore3 = 0
                    composite_score = round((surveyscore1*0.25)+(surveyscore2*0.50)+(surveyscore3*0.25),2)

                    if crop == "COTTON":
                        if composite_score >= 75:
                            pf_sus = "Pass"
                        elif composite_score < 75:
                            pf_sus = "Fail"

                    else:
                        if composite_score >= 70:
                            pf_sus = "Pass"
                        elif composite_score < 70:
                            pf_sus = "Fail"                    

                    if projected_yeild :
                        reported_yeild = float(reported_yeild)
                        projected_yeild = float(projected_yeild)
                        yield_delta = reported_yeild - projected_yeild
                except :
                    pass

            return_lst.extend([{"get_select_crop":'COTTON', "variety":variety, "field_name":field_name, "field_id":field_id, 
                                "grower_name":grower_name, "grower_id":grower_id, "farm_name":farm_name, "farm_id":farm_id,
                                "harvest_date":harvest_date, "projected_yeild":projected_yeild, "reported_yeild":reported_yeild,
                                "yield_delta":yield_delta, "storage_quanitty":storage_quanitty, "water_savings":water_savings,
                                "water_per_pound_savings":water_per_pound_savings, "land_use":land_use, "less_GHG":less_GHG,
                                "co2_eQ_footprint":co2_eQ_footprint, "premiums_to_growers":premiums_to_growers,"pf_sus":pf_sus}])
    else:
        for i in bale_id :
            get_bale = GrowerShipment.objects.get(id=i)
            field_id = get_bale.field.id
            get_field = Field.objects.get(id=field_id)
            variety = get_field.variety
            field_name = get_field.name
            grower_name = get_field.grower.name
            # grower_location = get_field.grower.physical_address1
            grower_id = get_field.grower.id
            farm_name = get_field.farm.name
            farm_id = get_field.farm.id
            projected_yeild = get_field.total_yield
            reported_yeild = get_bale.received_amount
            storage_quanitty = reported_yeild
            water_savings = get_field.gal_water_saved
            land_use = get_field.land_use_efficiency
            less_GHG = get_field.ghg_reduction
            premiums_to_growers = get_field.grower_premium_percentage
            water_per_pound_savings = get_field.water_lbs_saved
            co2_eQ_footprint = get_field.co2_eq_reduced
            harvest_date = get_field.harvest_date
            yield_delta =''
            surveyscore1 = get_field.get_survey1()
            surveyscore2 = get_field.get_survey2()
            surveyscore3 = get_field.get_survey3()
            if surveyscore1 != '' and surveyscore1 != None :
                surveyscore1 = float(surveyscore1)
            else:
                surveyscore1 = 0
            if surveyscore2 != '' and surveyscore2 != None :
                surveyscore2 = float(surveyscore2)
            else:
                surveyscore2 = 0
            if surveyscore3 != '' and surveyscore3 != None :
                surveyscore3 = float(surveyscore3)
            else:
                surveyscore3 = 0
            composite_score = round((surveyscore1*0.25)+(surveyscore2*0.50)+(surveyscore3*0.25),2)
            
            if crop == "COTTON":
                if composite_score >= 75:
                    pf_sus = "Pass"
                elif composite_score < 75:
                    pf_sus = "Fail"
            else:
                if composite_score >= 70:
                    pf_sus = "Pass"
                elif composite_score < 70:
                    pf_sus = "Fail"
            try :
                reported_yeild = float(reported_yeild)
                projected_yeild = float(projected_yeild)
                yield_delta = reported_yeild - projected_yeild
            except:
                pass          
            return_lst.extend([{"get_select_crop":crop, "variety":variety, "field_name":field_name, "field_id":field_id, 
                                "grower_name":grower_name, "grower_id":grower_id, "farm_name":farm_name, "farm_id":farm_id,
                                "harvest_date":harvest_date, "projected_yeild":projected_yeild, "reported_yeild":reported_yeild,
                                "yield_delta":yield_delta, "storage_quanitty":storage_quanitty, "water_savings":water_savings,
                                "water_per_pound_savings":water_per_pound_savings, "land_use":land_use, "less_GHG":less_GHG,
                                "co2_eQ_footprint":co2_eQ_footprint, "premiums_to_growers":premiums_to_growers,"pf_sus":pf_sus}])
            
    
    return return_lst


def outbound1_Wip_Grower(crop,search_text,from_date,to_date,*grower_field_ids) :
    grower_field_ids = list(grower_field_ids)
    return_lst = []
    if crop == 'COTTON' :
        pass
    else:
        # orders = GrowerShipment.objects.filter(Q(process_date__gte=from_date), Q(process_date__lte=to_date))
        get_shipment = GrowerShipment.objects.filter(field_id__in=grower_field_ids,status='', crop=crop).filter(Q(process_date__gte=from_date), Q(process_date__lte=to_date)).order_by('-id').values('id')
        if get_shipment.exists() :
            for i in get_shipment :
                get_shipment = GrowerShipment.objects.get(id=i['id'])
                deliveryid = get_shipment.shipment_id
                process_date = get_shipment.process_date
                quantity = get_shipment.total_amount
                skuid = get_shipment.sku   # add sku id
                transportation = ''
                destination = get_shipment.processor.entity_name
                grower_name = get_shipment.grower.name
                return_lst.extend([{"shipment_id":deliveryid,"source":grower_name,"skuid":skuid,"date":process_date,"quantity":quantity,"transportation":transportation,"destination":destination}])
        
    return return_lst


def outbound1_Wip_field(crop,search_text,from_date,to_date,field_id):
    return_lst = []
    if crop == 'COTTON' :
        pass
        
    else :
        get_shipment = GrowerShipment.objects.filter(field_id=field_id,status="", crop=crop).filter(Q(process_date__gte=from_date), Q(process_date__lte=to_date)).order_by('-id').values("id")
        if get_shipment.exists :
            for i in get_shipment :
                get_shipment_id = i["id"]
                get_shipment = GrowerShipment.objects.get(id=get_shipment_id)
                shipment_date = get_shipment.process_date
                quantity = get_shipment.total_amount
                deliveryid = get_shipment.shipment_id
                skuid = get_shipment.sku   # add sku id
                transportation = ''
                destination = get_shipment.processor.entity_name
                grower_name = get_shipment.grower.name
                return_lst.extend([{"shipment_id":deliveryid,"source":grower_name,"skuid":skuid,"date":shipment_date,"quantity":quantity,"transportation":transportation,"destination":destination}])
    return return_lst


def outbound1_Wip_Processor(crop,from_date,to_date,processorid):
    return_lst = []
    if crop == 'COTTON' :
        pass
    else :
        get_shipment = GrowerShipment.objects.filter(processor_id=processorid,status="", crop=crop).filter(Q(process_date__gte=from_date), Q(process_date__lte=to_date)).order_by('-id').values("id")
        for i in get_shipment :
            get_shipment = GrowerShipment.objects.get(id=i["id"])
            shipment_date = get_shipment.process_date
            quantity = get_shipment.total_amount
            deliveryid = get_shipment.shipment_id
            grower_name = get_shipment.grower.name
            
            # skuid = get_shipment.sku   # add sku id
            # module_tag = get_shipment.module_number   # add module tag
            transportation = ''
            destination = get_shipment.processor.entity_name
            return_lst.extend([{"shipment_id":deliveryid,"source":grower_name,"date":shipment_date,"quantity":quantity,"transportation":transportation,"destination":destination}])
    return return_lst


def outbound1_Wip_deliveryid(crop,search_text,warehouse_wh_id,from_date,to_date):
    return_lst = []
    if crop == 'COTTON' :
        get_bale = BaleReportFarmField.objects.filter(bale_id=search_text,warehouse_wh_id=warehouse_wh_id)
        if len(get_bale) == 1 :
            get_bale_id = [i.id for i in get_bale][0]
            get_bale = BaleReportFarmField.objects.get(id=get_bale_id)
            dt_class = get_bale.dt_class
            transportation = ''
            return_lst.extend([{"shipment_id":search_text,"date":dt_class,"transportation":transportation}])
    else :
        get_shipment = GrowerShipment.objects.filter(shipment_id=search_text,status="", crop=crop).filter(Q(process_date__gte=from_date), Q(process_date__lte=to_date))
        if len(get_shipment) == 1 :
            get_shipment_id = [i.id for i in get_shipment][0]
            get_shipment = GrowerShipment.objects.get(id=get_shipment_id)
            shipment_date = get_shipment.process_date
            transportation = ''
            skuid = get_shipment.sku   # add sku id
            quantity = get_shipment.total_amount
            destination = get_shipment.processor.entity_name
            grower_name = get_shipment.grower.name
            return_lst.extend([{"shipment_id":search_text,"source":grower_name,"skuid":skuid,"date":shipment_date,"quantity":quantity,"transportation":transportation,"destination":destination}])
    return return_lst


def t1_Processor_grower(crop,check_grower_id,from_date,to_date) :
    return_lst = []
    if crop == 'COTTON' :
        bale = BaleReportFarmField.objects.filter(ob2=check_grower_id).values("id")
        for i in bale :
            get_bale = BaleReportFarmField.objects.get(id=i["id"])
            # yyyy-mm-dd
            processor_name = get_bale.classing.processor.entity_name
            processor_id = get_bale.classing.processor.id
            deliveryid = get_bale.bale_id
            dt_class = get_bale.dt_class
            # dt_class mm-dd-yy
            if dt_class :
                str_date = str(dt_class)
                if '-' in str_date :
                    str_date = str_date.split('-')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                    from_date = str(from_date).replace('-','/')
                    to_date = str(to_date).replace('-','/')
                    format = '%Y/%m/%d'
                    # convert from string format to datetime format
                    from_date = datetime.datetime.strptime(from_date, format).date()
                    to_date = datetime.datetime.strptime(to_date, format).date()

                    if finale_date >= from_date and finale_date <= to_date:
                        res = True
                    else:
                        continue
                elif '/' in str_date :
                    str_date = str_date.split('/')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                    from_date = str(from_date).replace('-','/')
                    to_date = str(to_date).replace('-','/')
                    format = '%Y/%m/%d'
                    # convert from string format to datetime format
                    from_date = datetime.datetime.strptime(from_date, format).date()
                    to_date = datetime.datetime.strptime(to_date, format).date()

                    if finale_date >= from_date and finale_date <= to_date:
                        res = True
                    else:
                        continue
                else:
                    continue
            else:
                continue
            
            pounds_shipped = get_bale.net_wt
            pounds_received = get_bale.net_wt
            grower = get_bale.ob3
            field = get_bale.field_name
            field_id = get_bale.ob4
            farm = ''
            if field_id :
                try:
                    get_field = Field.objects.get(id=field_id)
                    farm = get_field.farm.name
                except:
                    farm = ''
            
            pounds_delta = ''
            try:
                pounds_delta = float(pounds_shipped) - float(pounds_received)
            except:
                pounds_delta = ''
            return_lst.extend([{"processor_name":processor_name,"grower":grower,"farm":farm,"field":field,"processor_id":processor_id,"shipment_id":deliveryid,
                                "date":dt_class,"pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta}])
    else :
        get_shipment = GrowerShipment.objects.filter(grower_id=check_grower_id,status="APPROVED", crop=crop).filter(Q(approval_date__gte=from_date), Q(approval_date__lte=to_date)).values("id")
        for i in get_shipment :
            get_shipment = GrowerShipment.objects.get(id=i["id"])
            processor_name = get_shipment.processor.entity_name
            processor_id = get_shipment.processor.id
            deliveryid = get_shipment.shipment_id
            dt_class = get_shipment.approval_date
            pounds_shipped = get_shipment.total_amount
            pounds_received = get_shipment.received_amount
            grower = get_shipment.grower.name
            field = get_shipment.field.name
            field_id = get_shipment.field.id
            get_field = Field.objects.get(id=field_id)
            farm = get_field.farm.name
            skuid = get_shipment.sku   # add sku_id
            pounds_delta = ''
            try:
                pounds_delta = float(pounds_shipped) - float(pounds_received)
            except:
                pounds_delta = ''
            return_lst.extend([{"processor_name":processor_name,"grower":grower,"farm":farm,"field":field,"processor_id":processor_id,"shipment_id":deliveryid,"skuid":skuid,
                                "date":dt_class,"pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta}])
                                
    return return_lst


def t1_Processor_field(crop,field_name,field_id,from_date,to_date) :
    return_lst = []
    if crop == 'COTTON' :
        get_bale = BaleReportFarmField.objects.filter(field_name=field_name,ob4=field_id).values("id")
        if get_bale.exists() :
            for i in get_bale :
                get_bale_id = i["id"]
                get_bale = BaleReportFarmField.objects.get(id=get_bale_id)
                processor_id = get_bale.classing.processor.id
                processor_name = get_bale.classing.processor.entity_name
                deliveryid = get_bale.bale_id
                shipment_date = get_bale.dt_class
                dt_class = get_bale.dt_class
                if dt_class :
                    str_date = str(dt_class)
                    if '-' in str_date :
                        str_date = str_date.split('-')
                        mm = str_date[0]
                        dd = str_date[1]
                        yy = str_date[2]
                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                        finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                        from_date = str(from_date).replace('-','/')
                        to_date = str(to_date).replace('-','/')
                        format = '%Y/%m/%d'
                        # convert from string format to datetime format
                        from_date = datetime.datetime.strptime(from_date, format).date()
                        to_date = datetime.datetime.strptime(to_date, format).date()

                        if finale_date >= from_date and finale_date <= to_date:
                            res = True
                        else:
                            continue
                    elif '/' in str_date :
                        str_date = str_date.split('/')
                        mm = str_date[0]
                        dd = str_date[1]
                        yy = str_date[2]
                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                        finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                        from_date = str(from_date).replace('-','/')
                        to_date = str(to_date).replace('-','/')
                        format = '%Y/%m/%d'
                        # convert from string format to datetime format
                        from_date = datetime.datetime.strptime(from_date, format).date()
                        to_date = datetime.datetime.strptime(to_date, format).date()

                        if finale_date >= from_date and finale_date <= to_date:
                            res = True
                        else:
                            continue
                    else:
                        continue
                else:
                    continue
                pounds_shipped = get_bale.net_wt
                pounds_received = get_bale.net_wt
                pounds_delta = ''
                grower = get_bale.ob3
                field = get_bale.field_name
                field_id = get_bale.ob4
                farm = ''
                if field_id :
                    try:
                        get_field = Field.objects.get(id=field_id)
                        farm = get_field.farm.name
                    except:
                        farm = ''
                try:
                    pounds_delta = float(pounds_shipped) - float(pounds_received)
                except:
                    pounds_delta = ''
                return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"shipment_id":deliveryid,"date":shipment_date,
                                    "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta,
                                    "grower":grower,"farm":farm,"field":field}])
    else :
        get_shipment = GrowerShipment.objects.filter(field_id=field_id,status="APPROVED", crop=crop).filter(Q(approval_date__gte=from_date), Q(approval_date__lte=to_date)).values("id")
        if get_shipment.exists :
            for i in get_shipment :
                get_shipment_id = i["id"]
                get_shipment = GrowerShipment.objects.get(id=get_shipment_id)
                processor_name = get_shipment.processor.entity_name
                processor_id = get_shipment.processor.id
                shipment_date = get_shipment.approval_date
                deliveryid = get_shipment.shipment_id
                pounds_shipped = get_shipment.total_amount
                pounds_received = get_shipment.received_amount
                grower = get_shipment.grower.name
                field = get_shipment.field.name
                field_id = get_shipment.field.id
                get_field = Field.objects.get(id=field_id)
                farm = get_field.farm.name
                skuid = get_shipment.sku   # add sku_id
                pounds_delta = ''
                try:
                    pounds_delta = float(pounds_shipped) - float(pounds_received)
                except:
                    pounds_delta = ''
                return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"shipment_id":deliveryid,"skuid":skuid,"date":shipment_date,
                                    "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta,
                                    "grower":grower,"farm":farm,"field":field,}])
    return return_lst


def t1_Processor_Processor(crop,processor_id,from_date,to_date,*bale_id) :
    return_lst = []
    if crop == 'COTTON' :
        bale_id = list(bale_id)
        check_bale = BaleReportFarmField.objects.filter(id__in=bale_id).values('id')
        for i in check_bale :
            get_bale = BaleReportFarmField.objects.get(id=i['id'])
            processor_id = get_bale.classing.processor.id
            processor_name = get_bale.classing.processor.entity_name
            deliveryid = get_bale.bale_id
            shipment_date = get_bale.dt_class
            dt_class = get_bale.dt_class
            unit = ''
            if dt_class :
                str_date = str(dt_class)
                if '-' in str_date :
                    str_date = str_date.split('-')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                    from_date = str(from_date).replace('-','/')
                    to_date = str(to_date).replace('-','/')
                    format = '%Y/%m/%d'
                    # convert from string format to datetime format
                    from_date = datetime.datetime.strptime(from_date, format).date()
                    to_date = datetime.datetime.strptime(to_date, format).date()

                    if finale_date >= from_date and finale_date <= to_date:
                        res = True
                    else:
                        continue
                elif '/' in str_date :
                    str_date = str_date.split('/')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                    from_date = str(from_date).replace('-','/')
                    to_date = str(to_date).replace('-','/')
                    format = '%Y/%m/%d'
                    # convert from string format to datetime format
                    from_date = datetime.datetime.strptime(from_date, format).date()
                    to_date = datetime.datetime.strptime(to_date, format).date()

                    if finale_date >= from_date and finale_date <= to_date:
                        res = True
                    else:
                        continue
                else:
                    continue
            else:
                continue
            pounds_shipped = get_bale.net_wt
            pounds_received = get_bale.net_wt
            grower = get_bale.ob3
            field = get_bale.field_name
            field_id = get_bale.ob4
            id = get_bale.id
            farm = ''
            if field_id :
                try:
                    get_field = Field.objects.get(id=field_id)
                    farm = get_field.farm.name
                except:
                    farm = ''
            pounds_delta = ''
            try:
                pounds_delta = float(pounds_shipped) - float(pounds_received)
            except:
                pounds_delta = ''
            return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"shipment_id":deliveryid,"date":shipment_date,
                                "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"unit":unit,"crop":"COTTON", "pounds_delta":pounds_delta,
                                "grower":grower,"farm":farm,"field":field, "id":id}])
    else :
        check_shipment = list(bale_id)
        get_shipment = GrowerShipment.objects.filter(id__in=check_shipment,status='APPROVED', crop=crop).filter(Q(approval_date__gte=from_date), Q(approval_date__lte=to_date)).values('id')
        for i in get_shipment :
            get_shipment = GrowerShipment.objects.get(id=i['id'])
            processor_name = get_shipment.processor.entity_name
            processor_id = get_shipment.processor.id
            shipment_date = get_shipment.approval_date
            deliveryid = get_shipment.shipment_id
            pounds_shipped = get_shipment.total_amount
            pounds_received = get_shipment.received_amount
            grower = get_shipment.grower.name
            field = get_shipment.field.name
            field_id = get_shipment.field.id
            get_field = Field.objects.get(id=field_id)
            farm = get_field.farm.name
            skuid = get_shipment.sku   # add sku_id
            pounds_delta = ''
            unit = get_shipment.unit_type
            crop = get_shipment.crop
            id = get_shipment.id
            try:
                pounds_delta = float(pounds_shipped) - float(pounds_received)
            except:
                pounds_delta = ''
            return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"shipment_id":deliveryid,"skuid":skuid,"date":shipment_date,
                                "pounds_shipped":pounds_shipped,"pounds_received":pounds_received, "unit":unit,"crop":crop, "pounds_delta":pounds_delta,
                                "grower":grower,"farm":farm,"field":field,"id":id}])      
    return return_lst


def t1_Processor_deliveryid(crop,search_text,warehouse_wh_id,from_date,to_date) :
    return_lst = []
    if crop == 'COTTON' :
        get_bale = BaleReportFarmField.objects.filter(bale_id=search_text,warehouse_wh_id=warehouse_wh_id)
        if len(get_bale) == 1 :
            get_bale_id = [i.id for i in get_bale][0]
            get_bale = BaleReportFarmField.objects.get(id=get_bale_id)
            processor_name = get_bale.classing.processor.entity_name
            processor_id = get_bale.classing.processor.id
            dt_class = get_bale.dt_class
            if dt_class :
                str_date = str(dt_class)
                if '-' in str_date :
                    str_date = str_date.split('-')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                    from_date = str(from_date).replace('-','/')
                    to_date = str(to_date).replace('-','/')
                    format = '%Y/%m/%d'
                    # convert from string format to datetime format
                    from_date = datetime.datetime.strptime(from_date, format).date()
                    to_date = datetime.datetime.strptime(to_date, format).date()

                    if finale_date >= from_date and finale_date <= to_date:
                        res = True                       
                    else:
                        return return_lst

                elif '/' in str_date :
                    str_date = str_date.split('/')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                    from_date = str(from_date).replace('-','/')
                    to_date = str(to_date).replace('-','/')
                    format = '%Y/%m/%d'
                    # convert from string format to datetime format
                    from_date = datetime.datetime.strptime(from_date, format).date()
                    to_date = datetime.datetime.strptime(to_date, format).date()

                    if finale_date >= from_date and finale_date <= to_date:
                        res = True
                        
                    else:
                        return return_lst
                else:
                    return return_lst
            else:
                return return_lst

            pounds_shipped = get_bale.net_wt
            pounds_received = get_bale.net_wt
            grower = get_bale.ob3
            field = get_bale.field_name
            field_id = get_bale.ob4
            farm = ''
            if field_id :
                try:
                    get_field = Field.objects.get(id=field_id)
                    farm = get_field.farm.name
                except:
                    farm = ''
            try:
                pounds_delta = float(pounds_shipped) - float(pounds_received)
            except:
                pounds_delta = ''
            return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"shipment_id":search_text,"date":dt_class,
                                "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta,
                                "grower":grower,"farm":farm,"field":field}])
    else :
        get_shipment = GrowerShipment.objects.filter(shipment_id=search_text,status="APPROVED", crop=crop).filter(Q(approval_date__gte=from_date), Q(approval_date__lte=to_date))
        if len(get_shipment) == 1 :
            get_shipment_id = [i.id for i in get_shipment][0]
            get_shipment = GrowerShipment.objects.get(id=get_shipment_id)
            processor_name = get_shipment.processor.entity_name
            processor_id = get_shipment.processor.id
            shipment_date = get_shipment.approval_date
            pounds_shipped = get_shipment.total_amount
            pounds_received = get_shipment.received_amount
            grower = get_shipment.grower.name
            field = get_shipment.field.name
            field_id = get_shipment.field.id
            get_field = Field.objects.get(id=field_id)
            farm = get_field.farm.name
            skuid = get_shipment.sku   # add sku_id
            pounds_delta = ''
            try:
                pounds_delta = float(pounds_shipped) - float(pounds_received)
            except:
                pounds_delta = ''
            return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"shipment_id":search_text,"skuid":skuid,"date":shipment_date,
                                    "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta,
                                    "grower":grower,"farm":farm,"field":field}])
    return return_lst


def outbound2_Wip_Grower(crop,check_grower_id,from_date,to_date,*grower_field_ids):
    grower_field_ids = list(grower_field_ids)
    return_lst = []
    if crop == 'COTTON' :
        pass
    else :
        get_processor = GrowerShipment.objects.filter(grower_id=check_grower_id, crop=crop).values('processor_id')
        if get_processor.exists():
            processor_id = [i['processor_id'] for i in get_processor][0]
        else:
            processor_id = ''
        get_shipment = ShipmentManagement.objects.filter(processor_idd=processor_id, crop=crop).filter(Q(date_pulled__date__gte=from_date), Q(date_pulled__date__lte=to_date)).values('id').order_by('-id')
        for i in get_shipment :
            get_shipment = ShipmentManagement.objects.get(id=i['id'])
            purchase_order_number = get_shipment.purchase_order_number
            date_pulled = get_shipment.date_pulled
            volume_shipped = get_shipment.volume_shipped
            equipment_type = get_shipment.equipment_type
            bin_location = get_shipment.bin_location
            storage_skuid = get_shipment.storage_bin_send
            receiver_skuid = get_shipment.storage_bin_recive
            destination = get_shipment.processor2_name
            return_lst.extend([{"shipment_id":purchase_order_number,"storage_skuid":storage_skuid,"date":date_pulled,"quantity":volume_shipped,"transportation":equipment_type,"destination":destination}])
    return return_lst


def outbound2_Wip_Field(crop,field_name,field_id,from_date,to_date):
    return_lst = []
    if crop == 'COTTON' :
        pass
    else :
        get_processor = GrowerShipment.objects.filter(field_id=field_id, crop=crop).values('processor_id')
        if get_processor.exists() :
            processor_id = [i['processor_id'] for i in get_processor][0]
        else:
            processor_id = ''
        get_shipment = ShipmentManagement.objects.filter(processor_idd=processor_id, crop=crop).filter(Q(date_pulled__date__gte=from_date), Q(date_pulled__date__lte=to_date)).values('id').order_by('-id')
        for i in get_shipment :
            get_shipment = ShipmentManagement.objects.get(id=i['id'])
            purchase_order_number = get_shipment.purchase_order_number
            date_pulled = get_shipment.date_pulled
            volume_shipped = get_shipment.volume_shipped
            equipment_type = get_shipment.equipment_type
            bin_location = get_shipment.bin_location
            storage_skuid = get_shipment.storage_bin_send  # add storage_bin
            return_lst.extend([{"shipment_id":purchase_order_number,"storage_skuid":storage_skuid,"date":date_pulled,"quantity":volume_shipped,"transportation":equipment_type,"destination":bin_location}])
    return return_lst


def outbound_Wip_Processor(crop,processor_id,processor_type,from_date,to_date) :
    return_lst = []
    if crop == 'COTTON' :
        pass
    else :
        if processor_type == "T1":
            get_shipment = ShipmentManagement.objects.filter(sender_processor_type="T1", processor_idd = processor_id, date_pulled__date__gte = from_date, date_pulled__date__lte = to_date, crop=crop).values()
           
        elif processor_type == "T2":            
            get_shipment = ShipmentManagement.objects.filter(sender_processor_type="T2", processor_idd = processor_id, date_pulled__date__gte = from_date, date_pulled__date__lte = to_date, crop=crop).values()
           
        elif processor_type == "T3":
            get_shipment = ShipmentManagement.objects.filter(sender_processor_type="T3", processor_idd = processor_id, date_pulled__date__gte = from_date, date_pulled__date__lte = to_date, crop=crop).values()
            
        elif processor_type == "T4":
            get_shipment = ShipmentManagement.objects.filter(sender_processor_type="T4", processor_idd = processor_id, date_pulled__date__gte = from_date, date_pulled__date__lte = to_date, status = None, crop=crop).values()
           
    return list(get_shipment)


def inbound_Wip_Processor(crop,processor_id,processor_type,from_date,to_date) :
    return_lst = []
    if crop == 'COTTON' :
        pass
    else :
        get_shipment = []
        if processor_type == "T2":
            get_shipment = ShipmentManagement.objects.filter(receiver_processor_type="T2", processor2_idd = processor_id, date_pulled__date__gte = from_date, date_pulled__date__lte = to_date, status="APPROVED", crop=crop).values()
           
        elif processor_type == "T3":
            get_shipment = ShipmentManagement.objects.filter(receiver_processor_type="T3", processor2_idd = processor_id, date_pulled__date__gte = from_date, date_pulled__date__lte = to_date, status="APPROVED", crop=crop).values()
           
        elif processor_type == "T4":
            get_shipment = ShipmentManagement.objects.filter(receiver_processor_type="T4", processor2_idd = processor_id, date_pulled__date__gte = from_date, date_pulled__date__lte = to_date, status="APPROVED", crop=crop).values()
          
    return list(get_shipment)


def outbound2_Wip_deliveryid(crop,search_text,rice_shipment_id,from_date,to_date) :
    return_lst = []
    if crop == 'COTTON' :
        pass
    else :
        get_processor = GrowerShipment.objects.filter(shipment_id=rice_shipment_id, crop=crop).values('processor_id')
        processor_id = [i['processor_id'] for i in get_processor][0]
        get_shipment = ShipmentManagement.objects.filter(processor_idd=processor_id, crop=crop).filter(Q(date_pulled__date__gte=from_date), Q(date_pulled__date__lte=to_date)).values('id').order_by('-id')
        for i in get_shipment :
            get_shipment = ShipmentManagement.objects.get(id=i['id'])
            purchase_order_number = get_shipment.purchase_order_number
            date_pulled = get_shipment.date_pulled
            volume_shipped = get_shipment.volume_shipped
            equipment_type = get_shipment.equipment_type
            bin_location = get_shipment.bin_location
            storage_skuid = get_shipment.storage_bin_send  # add storage_bin
            return_lst.extend([{"shipment_id":purchase_order_number,"storage_skuid":storage_skuid,"date":date_pulled,"quantity":volume_shipped,"transportation":equipment_type,"destination":bin_location}])
    return return_lst


def t2_Processor_grower(crop,check_grower_id,from_date,to_date) :
    return_lst = []
    if crop == 'COTTON' :
        bale = AssignedBaleProcessor2.objects.filter(grower_idd=check_grower_id).values("id")
        for i in bale :
            get_bale = AssignedBaleProcessor2.objects.get(id=i["id"])
            processor_name = get_bale.processor2.entity_name
            processor_id = get_bale.processor2.id
            deliveryid = get_bale.assigned_bale
            dt_class = get_bale.dt_class
            if dt_class :
                str_date = str(dt_class)
                if '-' in str_date :
                    str_date = str_date.split('-')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                    from_date = str(from_date).replace('-','/')
                    to_date = str(to_date).replace('-','/')
                    format = '%Y/%m/%d'
                    # convert from string format to datetime format
                    from_date = datetime.datetime.strptime(from_date, format).date()
                    to_date = datetime.datetime.strptime(to_date, format).date()

                    if finale_date >= from_date and finale_date <= to_date:
                        res = True                       
                    else:
                        continue
                elif '/' in str_date :
                    str_date = str_date.split('/')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                    from_date = str(from_date).replace('-','/')
                    to_date = str(to_date).replace('-','/')
                    format = '%Y/%m/%d'
                    # convert from string format to datetime format
                    from_date = datetime.datetime.strptime(from_date, format).date()
                    to_date = datetime.datetime.strptime(to_date, format).date()

                    if finale_date >= from_date and finale_date <= to_date:
                        res = True                      
                    else:
                        continue
                else:
                    continue
            else:
                continue
            pounds_shipped = get_bale.net_wt
            pounds_received = get_bale.net_wt
            grower = get_bale.grower_name
            field = get_bale.field_name
            field_id = get_bale.field_idd
            farm = ''
            if field_id :
                try:
                    get_field = Field.objects.get(id=field_id)
                    farm = get_field.farm.name
                except:
                    farm = ''
            pounds_delta = ''
            try:
                pounds_delta = float(pounds_shipped) - float(pounds_received)
            except:
                pounds_delta = ''
            return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"shipment_id":deliveryid,
                                "grower":grower,"farm":farm,"field":field,"date":dt_class,"pounds_shipped":pounds_shipped,
                                "pounds_received":pounds_received,"pounds_delta":pounds_delta}])
    else :
        # pass
    #     get_shipment = GrowerShipment.objects.filter(grower_id=check_grower_id,status="APPROVED").values("id")
    #     for i in get_shipment :
    #         get_shipment = GrowerShipment.objects.get(id=i["id"])
    #         processor_name = get_shipment.processor.entity_name
    #         processor_id = get_shipment.processor.id
    #         deliveryid = get_shipment.shipment_id
    #         dt_class = get_shipment.approval_date
    #         pounds_shipped = get_shipment.total_amount
    #         pounds_received = get_shipment.received_amount
   
    #         pounds_delta = ''
    #         try:
    #             pounds_delta = float(pounds_shipped) - float(pounds_received)
    #         except:
    #             pounds_delta = ''
    #         return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"deliveryid":deliveryid,"date":dt_class,
    #                             "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta,}])
    # return return_lst
        
        get_grower = GrowerShipment.objects.filter(grower_id=check_grower_id,status="APPROVED", crop=crop)
        if get_grower.exists():
            shipment = ShipmentManagement.objects.filter(crop=crop)
            for i in range(len(shipment)):
                var = shipment[i].storage_bin_send
                grower_shipment = GrowerShipment.objects.filter(sku = var, crop=crop).filter(grower_id=check_grower_id)
                for r in grower_shipment :
                    del_id = r.shipment_id
                    shipment_date = r.approval_date
                    get_shipment = ShipmentManagement.objects.get(storage_bin_send=var)
                    processor_id = get_shipment.processor2_idd
                    processor_name = get_shipment.processor2_name
                    sku_id = get_shipment.storage_bin_send
                    pounds_shipped = r.total_amount
                    pounds_received = r.received_amount
                    pounds_delta = ''
                    try:
                        pounds_delta = float(pounds_shipped) - float(pounds_received)
                    except:
                        pounds_delta = ''
                    return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"shipment_id":del_id,"date":shipment_date,
                                "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta,"skuid":sku_id}])

        return return_lst
    

def t2_Processor_field(crop,field_name,field_id,from_date,to_date) :
    return_lst = []
    if crop == 'COTTON' :
        get_bale = AssignedBaleProcessor2.objects.filter(field_name=field_name,field_idd=field_id).values("id")
        if get_bale.exists() :
            for i in get_bale :
                get_bale_id = i["id"]
                get_bale = AssignedBaleProcessor2.objects.get(id=get_bale_id)
                processor_id = get_bale.processor2.id
                processor_name = get_bale.processor2.entity_name
                deliveryid = get_bale.assigned_bale
                shipment_date = get_bale.dt_class
                dt_class = get_bale.dt_class
                if dt_class :
                    str_date = str(dt_class)
                    if '-' in str_date :
                        str_date = str_date.split('-')
                        mm = str_date[0]
                        dd = str_date[1]
                        yy = str_date[2]
                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                        finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                        from_date = str(from_date).replace('-','/')
                        to_date = str(to_date).replace('-','/')
                        format = '%Y/%m/%d'
                        # convert from string format to datetime format
                        from_date = datetime.datetime.strptime(from_date, format).date()
                        to_date = datetime.datetime.strptime(to_date, format).date()

                        if finale_date >= from_date and finale_date <= to_date:
                            res = True
                            
                        else:
                            continue
                    elif '/' in str_date :
                        str_date = str_date.split('/')
                        mm = str_date[0]
                        dd = str_date[1]
                        yy = str_date[2]
                        yyyy = f'20{yy}' if len(yy) == 2 else yy
                        finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                        from_date = str(from_date).replace('-','/')
                        to_date = str(to_date).replace('-','/')
                        format = '%Y/%m/%d'
                        # convert from string format to datetime format
                        from_date = datetime.datetime.strptime(from_date, format).date()
                        to_date = datetime.datetime.strptime(to_date, format).date()

                        if finale_date >= from_date and finale_date <= to_date:
                            res = True
                           
                        else:
                            continue
                    else:
                        continue
                else:
                    continue
                pounds_shipped = get_bale.net_wt
                pounds_received = get_bale.net_wt
                grower = get_bale.grower_name
                field = get_bale.field_name
                field_id = get_bale.field_idd
                farm = ''
                if field_id :
                    try:
                        get_field = Field.objects.get(id=field_id)
                        farm = get_field.farm.name
                    except:
                        farm = ''
                pounds_delta = ''
                try:
                    pounds_delta = float(pounds_shipped) - float(pounds_received)
                except:
                    pounds_delta = ''
                return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"shipment_id":deliveryid,"date":shipment_date,
                                    "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta,
                                    "grower":grower,"farm":farm,"field":field}])
    else :
        pass
    #     get_shipment = GrowerShipment.objects.filter(field_id=field_id,status="APPROVED").values("id")
    #     if get_shipment.exists :
    #         for i in get_shipment :
    #             get_shipment_id = i["id"]
    #             get_shipment = GrowerShipment.objects.get(id=get_shipment_id)
    #             processor_name = get_shipment.processor.entity_name
    #             processor_id = get_shipment.processor.id
    #             shipment_date = get_shipment.approval_date
    #             deliveryid = get_shipment.shipment_id
    #             pounds_shipped = get_shipment.total_amount
    #             pounds_received = get_shipment.received_amount
    #             pounds_delta = ''
    #             try:
    #                 pounds_delta = float(pounds_shipped) - float(pounds_received)
    #             except:
    #                 pounds_delta = ''
    #             return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"deliveryid":deliveryid,"date":shipment_date,
    #                                 "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta}])
    # return return_lst
    
        get_shipment_data = GrowerShipment.objects.filter(field_id=field_id,status="APPROVED", crop=crop)
        if get_shipment_data.exists():    
            shipment = ShipmentManagement.objects.filter(crop=crop)
            for i in range(len(shipment)):
                var = shipment[i].storage_bin_send
                grower_shipment = GrowerShipment.objects.filter(sku = var).filter(field_id=field_id)
                for r in grower_shipment :
                    del_id = r.shipment_id
                    shipment_date = r.approval_date
                    get_shipment = ShipmentManagement.objects.get(storage_bin_send=var)
                    processor_id = get_shipment.processor2_idd
                    processor_name = get_shipment.processor2_name
                    sku_id = get_shipment.storage_bin_send
                    pounds_shipped = r.total_amount
                    pounds_received = r.received_amount
                    pounds_delta = ''
                    try:
                        pounds_delta = float(pounds_shipped) - float(pounds_received)
                    except:
                        pounds_delta = ''
                    return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"shipment_id":del_id,"date":shipment_date,
                                "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta,"skuid":sku_id}])

        return return_lst


def t2_Processor_Processor(crop,processor_id,from_date,to_date,*bale_id) :
    return_lst = []
    if crop == 'COTTON' :
        bale_id = list(bale_id)
        check_bale = AssignedBaleProcessor2.objects.filter(bale_id__in=bale_id).values('id')
        for i in check_bale :
            get_bale = AssignedBaleProcessor2.objects.get(id=i['id'])
            processor_id = get_bale.processor2.id
            processor_name = get_bale.processor2.entity_name
            deliveryid = get_bale.assigned_bale
            shipment_date = get_bale.dt_class
            dt_class = get_bale.dt_class
            if dt_class :
                str_date = str(dt_class)
                if '-' in str_date :
                    str_date = str_date.split('-')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                    from_date = str(from_date).replace('-','/')
                    to_date = str(to_date).replace('-','/')
                    format = '%Y/%m/%d'
                    # convert from string format to datetime format
                    from_date = datetime.datetime.strptime(from_date, format).date()
                    to_date = datetime.datetime.strptime(to_date, format).date()

                    if finale_date >= from_date and finale_date <= to_date:
                        res = True
                       
                    else:
                        continue
                elif '/' in str_date :
                    str_date = str_date.split('/')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                    from_date = str(from_date).replace('-','/')
                    to_date = str(to_date).replace('-','/')
                    format = '%Y/%m/%d'
                    # convert from string format to datetime format
                    from_date = datetime.datetime.strptime(from_date, format).date()
                    to_date = datetime.datetime.strptime(to_date, format).date()

                    if finale_date >= from_date and finale_date <= to_date:
                        res = True
                      
                    else:
                        continue
                else:
                    continue
            else:
                continue
            pounds_shipped = get_bale.net_wt
            pounds_received = get_bale.net_wt
            grower = get_bale.grower_name
            field = get_bale.field_name
            field_id = get_bale.field_idd
            farm = ''
            if field_id :
                try:
                    get_field = Field.objects.get(id=field_id)
                    farm = get_field.farm.name
                except:
                    farm = ''
            pounds_delta = ''
            try:
                pounds_delta = float(pounds_shipped) - float(pounds_received)
            except:
                pounds_delta = ''
            return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"shipment_id":deliveryid,"date":shipment_date,
                                "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta,
                                "grower":grower,"farm":farm,"field":field}])
    else :      
        check_shipment = list(bale_id)
        get_shipment_data = GrowerShipment.objects.filter(id__in=check_shipment,status='APPROVED', crop=crop)
        if get_shipment_data.exists():
            
            shipment = ShipmentManagement.objects.filter(processor_idd = processor_id, crop=crop)
            
            for i in range(len(shipment)):
                var = shipment[i].storage_bin_send
                grower_shipment = GrowerShipment.objects.filter(sku = var)
                for r in grower_shipment :
                    del_id = r.shipment_id
                    shipment_date = r.approval_date
                    get_shipment = ShipmentManagement.objects.get(storage_bin_send=var)
                    processor_id = get_shipment.processor2_idd
                    processor_name = get_shipment.processor2_name
                    sku_id = get_shipment.storage_bin_send
                    pounds_shipped = r.total_amount
                    pounds_received = r.received_amount
                    pounds_delta = ''
                    try:
                        pounds_delta = float(pounds_shipped) - float(pounds_received)
                    except:
                        pounds_delta = ''
                    return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"shipment_id":del_id,"date":shipment_date,
                                "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta,"skuid":sku_id}])
        
        return return_lst


def t2_Processor_deliveryid(crop,search_text,warehouse_wh_id,from_date,to_date) :
    return_lst = []
    if crop == 'COTTON' :
        get_bale = AssignedBaleProcessor2.objects.filter(assigned_bale=search_text,warehouse_wh_id=warehouse_wh_id)
        if len(get_bale) == 1 :
            get_bale_id = [i.id for i in get_bale][0]
            get_bale = AssignedBaleProcessor2.objects.get(id=get_bale_id)
            processor_name = get_bale.processor2.entity_name
            processor_id = get_bale.processor2.id
            dt_class = get_bale.dt_class
            if dt_class :
                str_date = str(dt_class)
                if '-' in str_date :
                    str_date = str_date.split('-')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                    from_date = str(from_date).replace('-','/')
                    to_date = str(to_date).replace('-','/')
                    format = '%Y/%m/%d'
                    # convert from string format to datetime format
                    from_date = datetime.datetime.strptime(from_date, format).date()
                    to_date = datetime.datetime.strptime(to_date, format).date()

                    if finale_date >= from_date and finale_date <= to_date:
                        res = True
                       
                    else:
                        return return_lst
                elif '/' in str_date :
                    str_date = str_date.split('/')
                    mm = str_date[0]
                    dd = str_date[1]
                    yy = str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = datetime.date(int(yyyy), int(mm), int(dd))
                    from_date = str(from_date).replace('-','/')
                    to_date = str(to_date).replace('-','/')
                    format = '%Y/%m/%d'
                    # convert from string format to datetime format
                    from_date = datetime.datetime.strptime(from_date, format).date()
                    to_date = datetime.datetime.strptime(to_date, format).date()

                    if finale_date >= from_date and finale_date <= to_date:
                        res = True
                       
                    else:
                        return return_lst
                else:
                    return return_lst
            else:
                return return_lst
            pounds_shipped = get_bale.net_wt
            pounds_received = get_bale.net_wt
            grower = get_bale.grower_name
            field = get_bale.field_name
            field_id = get_bale.field_idd
            farm = ''
            if field_id :
                try:
                    get_field = Field.objects.get(id=field_id)
                    farm = get_field.farm.name
                except:
                    farm = ''
            try:
                pounds_delta = float(pounds_shipped) - float(pounds_received)
            except:
                pounds_delta = ''
            return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"shipment_id":search_text,"date":dt_class,
                                "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta,
                                "grower":grower,"farm":farm,"field":field}])
    else :
        # pass
    #     get_shipment = GrowerShipment.objects.filter(shipment_id=search_text,status="APPROVED")
    #     if len(get_shipment) == 1 :
    #         get_shipment_id = [i.id for i in get_shipment][0]
    #         get_shipment = GrowerShipment.objects.get(id=get_shipment_id)
    #         processor_name = get_shipment.processor.entity_name
    #         processor_id = get_shipment.processor.id
    #         shipment_date = get_shipment.approval_date
    #         pounds_shipped = get_shipment.total_amount
    #         pounds_received = get_shipment.received_amount
    #         pounds_delta = ''

    #         try:
    #             pounds_delta = float(pounds_shipped) - float(pounds_received)
    #         except:
    #             pounds_delta = ''
    #         return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"deliveryid":search_text,"date":shipment_date,
    #                                 "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta}])
    # return return_lst
    
        get_shipment_data = GrowerShipment.objects.filter(shipment_id=search_text,status="APPROVED", crop=crop)
        if get_shipment_data.exists():    
            shipment = ShipmentManagement.objects.filter(crop=crop)
            for i in range(len(shipment)):
                var = shipment[i].storage_bin_send
                grower_shipment = GrowerShipment.objects.filter(sku = var,crop=crop).filter(shipment_id=search_text)
                for r in grower_shipment :
                    del_id = r.shipment_id
                    shipment_date = r.approval_date
                    get_shipment = ShipmentManagement.objects.get(storage_bin_send=var)
                    processor_id = get_shipment.processor2_idd
                    processor_name = get_shipment.processor2_name
                    sku_id = get_shipment.storage_bin_send
                    pounds_shipped = r.total_amount
                    pounds_received = r.received_amount
                    pounds_delta = ''
                    try:
                        pounds_delta = float(pounds_shipped) - float(pounds_received)
                    except:
                        pounds_delta = ''
                    return_lst.extend([{"processor_name":processor_name,"processor_id":processor_id,"shipment_id":del_id,"date":shipment_date,
                                "pounds_shipped":pounds_shipped,"pounds_received":pounds_received,"pounds_delta":pounds_delta,"skuid":sku_id}])

        return return_lst


def get_processor_type(processor_name):
    check_processor = Processor.objects.filter(entity_name=processor_name)
    if check_processor:
        processor_details = {'id':check_processor.first().id,
                             'type':'T1'}        
    else:
        get_processor = Processor2.objects.filter(entity_name=processor_name)
        if get_processor:
            processor = get_processor.first()
            processor_type = processor.processor_type.all().first().type_name
           
            processor_details = {'id':processor.id,
                             'type':processor_type}
        else:
            processor_details = None
    return processor_details


def get_outbound5_wip(crop, outbound_wip, from_date, to_date):
    processor_ids = []  
    unique_processors = set()  

    for outbound in outbound_wip:        
        processor_tuple = (outbound["processor_idd"], outbound["sender_processor_type"])
        if processor_tuple not in unique_processors:
            unique_processors.add(processor_tuple)
            processor_ids.append({"id": outbound["processor_idd"], "type": outbound["sender_processor_type" ]})

        if outbound["status"] == "APPROVED":
            processor_tuple = (outbound["processor2_idd"], outbound["receiver_processor_type"])

            if processor_tuple not in unique_processors:                
                unique_processors.add(processor_tuple)
                processor_ids.append({"id": outbound["processor2_idd"], "type": outbound["receiver_processor_type"]})

            if ShipmentManagement.objects.filter(crop=crop, processor_idd=int(outbound["processor2_idd"]), status="APPROVED").exists():
                shipments = ShipmentManagement.objects.filter(crop=crop, processor_idd=int(outbound["processor2_idd"]), status="APPROVED")
                for ship in shipments:
                    processor_tuple = (ship.processor2_idd, ship.receiver_processor_type)

                    if processor_tuple not in unique_processors:
                        unique_processors.add(processor_tuple)
                        processor_ids.append({"id": ship.processor2_idd, "type": ship.receiver_processor_type})

                    if ship.receiver_processor_type == "T4":
                        break

                    elif ShipmentManagement.objects.filter(crop=crop, processor_idd=int(ship.processor2_idd), status="APPROVED").exists():
                        shipments_2 = ShipmentManagement.objects.filter(crop=crop, processor_idd=int(ship.processor2_idd), status="APPROVED")
                        for shipment in shipments_2:
                            processor_tuple = (shipment.processor2_idd, shipment.receiver_processor_type)

                            if processor_tuple not in unique_processors:
                                unique_processors.add(processor_tuple)
                                processor_ids.append({"id": shipment.processor2_idd, "type": shipment.receiver_processor_type})

    outbound5_wip = []    

    for processor in processor_ids:      

        shipments = ProcessorWarehouseShipment.objects.filter(
            processor_shipment_crop__crop=crop,
            processor_id=int(processor["id"]),
            processor_type=processor["type"],
            date_pulled__date__gte=from_date,
            date_pulled__date__lte=to_date
        ).values("id", "contract__secret_key","contract_id","processor_shipment_crop__crop", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled","status", "carrier_type", "distributor_receive_date")

        for shipment in shipments: 
            if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
             
            carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
            shipment["carrier_id"] = carrier.carrier_id  
            outbound5_wip.append(shipment)


    return outbound5_wip


def get_inbound5_wip(outbound_wip):
    inbound5_wip = []
    for shipment in outbound_wip:       
        if shipment["warehouse_id"] not in [None, "null", "", " "]:          
            
            inbound5_wip.append(shipment)   
    return inbound5_wip


def get_outbound6_wip(crop, outbound_wip, from_date, to_date):    
    outbound6_wip = []
    for shipment in outbound_wip:     
        
        if shipment["warehouse_id"] not in [None, "null", "", " "] and WarehouseCustomerShipment.objects.filter( warehouse_shipment_crop__crop=crop, warehouse_id=int(shipment["warehouse_id"]), date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).exists():
            shipments = WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=crop, warehouse_id=int(shipment["warehouse_id"]), date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id", "contract__secret_key","warehouse_shipment_crop__crop","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name",  "date_pulled", "status", "carrier_type", "customer_receive_date")
            
            for shipment in shipments :
                if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                    shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                  
                carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                shipment["carrier_id"] = carrier.carrier_id               
                outbound6_wip.append(shipment)   
    return outbound6_wip


def processor_traceability_report_response(crop, processor_id,processor_type, from_date, to_date, search_text):
    context = {}
    if processor_type in ["T1"]:        
        check_processor = Processor.objects.filter(entity_name__icontains=search_text)

        if check_processor.exists():            
            get_shipment = GrowerShipment.objects.filter(processor_id=processor_id,crop=crop).values("id")
            if get_shipment.exists() :
                bale_id = [i["id"] for i in get_shipment]  
                get_Origin_Processor = Origin_searchby_Processor(crop, *bale_id)        
                context["origin_context"] = get_Origin_Processor
                context["search_by"] = "processor"
                outbound1_wip = outbound1_Wip_Processor(crop, from_date,to_date,processor_id)
                context["outbound1_wip"] = outbound1_wip
                t1_processor = t1_Processor_Processor(crop, processor_id,from_date,to_date,*bale_id)
                context["t1_processor"] = t1_processor
               
                # T1 to T2
                outbound2_wip = outbound_Wip_Processor(crop, processor_id,processor_type,from_date,to_date)         
                context["outbound2_wip"] = outbound2_wip
                                                             
                # T2 to T3                
                processor_type = "T2"
                link_t2_processor_id_list = list(LinkProcessor1ToProcessor.objects.filter(processor1=processor_id, processor2__processor_type__type_name = "T2").values_list("processor2_id", flat=True))
                unique_link_t2_processor_id_list = list(set(link_t2_processor_id_list))
                outbound3_wip = []
                for t2_id in unique_link_t2_processor_id_list:
                    outbound_wip = outbound_Wip_Processor(crop, t2_id,processor_type,from_date,to_date)         
                    outbound3_wip = outbound3_wip + outbound_wip
                context["outbound3_wip"] = outbound3_wip

                # T3 to T4
                processor_type = "T3"
                link_t3_processor_id_list = list(LinkProcessorToProcessor.objects.filter(processor_id__in = link_t2_processor_id_list, linked_processor__processor_type__type_name = "T3").values_list("linked_processor_id", flat=True))
                unique_link_t3_processor_id_list = list(set(link_t3_processor_id_list))
                outbound4_wip = []
                for t3_id in unique_link_t3_processor_id_list:
                    outbound4_wip_ = outbound_Wip_Processor(crop, t3_id,processor_type,from_date,to_date)         
                    outbound4_wip = outbound4_wip + outbound4_wip_
                context["outbound4_wip"] = outbound4_wip                
                
                # T2 to T3
                processor_type = "T2"
                link_t2_processor_id_list = list(LinkProcessor1ToProcessor.objects.filter(processor1=processor_id, processor2__processor_type__type_name = "T2").values_list("processor2_id", flat=True))
                unique_link_t2_processor_id_list = list(set(link_t2_processor_id_list))
                inbound2_wip = []
                for t2_id in unique_link_t2_processor_id_list:
                    inbound_wip = inbound_Wip_Processor(crop, t2_id,processor_type,from_date,to_date)         
                    inbound2_wip = inbound2_wip + inbound_wip
                context["inbound2_wip"] = inbound2_wip               

                # T3 to T4
                processor_type = "T3"
                link_t3_processor_id_list = list(LinkProcessorToProcessor.objects.filter(processor_id__in = link_t2_processor_id_list, linked_processor__processor_type__type_name = "T3").values_list("linked_processor_id", flat=True))
                unique_link_t3_processor_id_list = list(set(link_t3_processor_id_list))
                inbound3_wip = []
                for t3_id in unique_link_t3_processor_id_list:
                    inbound_wip = inbound_Wip_Processor(crop, t3_id,processor_type,from_date,to_date)         
                    inbound3_wip = inbound3_wip + inbound_wip
                context["inbound3_wip"] = inbound3_wip                
                
                processor_type = "T4"
                link_t4_processor_id_list = list(LinkProcessorToProcessor.objects.filter(processor_id__in = link_t3_processor_id_list, linked_processor__processor_type__type_name = "T4").values_list("linked_processor_id", flat=True))
                unique_link_t4_processor_id_list = list(set(link_t4_processor_id_list))
                inbound4_wip = []
                for t4_id in unique_link_t4_processor_id_list:
                    inbound2_wip = inbound_Wip_Processor(crop, t4_id,processor_type,from_date,to_date)         
                    inbound4_wip = inbound4_wip + inbound2_wip
                context["inbound4_wip"] = inbound4_wip           

                outbound5_wip = get_outbound5_wip(crop, outbound2_wip, from_date, to_date)
                context["outbound5_wip"] = outbound5_wip 

                inbound5_wip = get_inbound5_wip(outbound5_wip)     
                context["inbound5_wip"] = inbound5_wip

                outbound6_wip = get_outbound6_wip(crop, outbound5_wip, from_date, to_date) 
                context["outbound6_wip"] = outbound6_wip 

                inbound6_wip = []  
                for shipment in outbound5_wip:                    
                    if shipment["customer_id"] not in [None, "null" ,"", " "]:                        
                        inbound6_wip.append(shipment)
                inbound6_wip.extend(outbound6_wip) 
                context["inbound6_wip"] = inbound6_wip                                
                
    elif processor_type in ["T2", "T3", "T4"]:        
        if processor_type == "T2":            
            linked_t1 = list(LinkProcessor1ToProcessor.objects.filter(processor2_id=processor_id).values_list("processor1_id", flat=True))
            grower_list = []
            outbound2_wip = []
            outbound1 = []
            inbound1 = []
            for t1_id in linked_t1:
                get_shipment = GrowerShipment.objects.filter(processor_id=t1_id,crop=crop).values("id")
                if get_shipment.exists():
                    bale_id = [i["id"] for i in get_shipment]  
                    get_Origin_Processor = Origin_searchby_Processor(crop,*bale_id) 
                    grower_list = grower_list + get_Origin_Processor
                    outbound1_wip = outbound1_Wip_Processor(crop,from_date,to_date,processor_id)
                    outbound1 = outbound1 + outbound1_wip
                    t1_processor = t1_Processor_Processor(crop,t1_id,from_date,to_date,*bale_id)
                    inbound1 = inbound1 + t1_processor

                    processor_type = "T1"
                    outbound2_wip_ = outbound_Wip_Processor(crop,t1_id,processor_type,from_date,to_date)         
                    outbound2_wip = outbound2_wip + outbound2_wip_
            context["outbound2_wip"] = outbound2_wip
                    
            context["origin_context"] = grower_list
            context["search_by"] = "processor"
            context["outbound1_wip"] = outbound1
            context["t1_processor"] = inbound1            

            processor_type = "T2"  
            outbound3_wip = outbound_Wip_Processor(crop,processor_id,processor_type,from_date,to_date)  
            context["outbound3_wip"] = outbound3_wip

            processor_type = "T3"
            link_t3_processor_id_list = list(LinkProcessorToProcessor.objects.filter(processor_id = processor_id, linked_processor__processor_type__type_name = "T3").values_list("linked_processor_id", flat=True))
            unique_link_t3_processor_id_list = list(set(link_t3_processor_id_list))
            outbound4_wip = []
            for t3_id in unique_link_t3_processor_id_list:
                outbound2_wip = outbound_Wip_Processor(crop,t3_id,processor_type,from_date,to_date)         
                outbound4_wip = outbound4_wip + outbound2_wip
            context["outbound4_wip"] = outbound4_wip

            processor_type = "T2"                                    
            inbound2_wip = inbound_Wip_Processor(crop,processor_id,processor_type,from_date,to_date)  
            context["inbound2_wip"] = inbound2_wip

            processor_type = "T3"
            link_t3_processor_id_list = list(LinkProcessorToProcessor.objects.filter(processor_id = processor_id, linked_processor__processor_type__type_name = "T3").values_list("linked_processor_id", flat=True))
            unique_link_t3_processor_id_list = list(set(link_t3_processor_id_list))
            inbound3_wip = []
            for t3_id in unique_link_t3_processor_id_list:
                inbound_wip = inbound_Wip_Processor(crop,t3_id,processor_type,from_date,to_date)         
                inbound3_wip = inbound3_wip + inbound_wip
            context["inbound3_wip"] = inbound3_wip           
            
            processor_type = "T4"
            link_t4_processor_id_list = list(LinkProcessorToProcessor.objects.filter(processor_id__in = link_t3_processor_id_list, linked_processor__processor_type__type_name = "T4").values_list("linked_processor_id", flat=True))
            unique_link_t4_processor_id_list = list(set(link_t4_processor_id_list))
            inbound4_wip = []
            for t4_id in unique_link_t4_processor_id_list:
                inbound2_wip = inbound_Wip_Processor(crop,t4_id,processor_type,from_date,to_date)         
                inbound4_wip = inbound4_wip + inbound2_wip
            context["inbound4_wip"] = inbound4_wip 

            outbound5_wip = get_outbound5_wip(crop, outbound2_wip, from_date, to_date)
            context["outbound5_wip"] = outbound5_wip 

            inbound5_wip = get_inbound5_wip(outbound5_wip)     
            context["inbound5_wip"] = inbound5_wip

            outbound6_wip = get_outbound6_wip(crop,outbound5_wip, from_date, to_date) 
            context["outbound6_wip"] = outbound6_wip 

            inbound6_wip = []  
            for shipment in outbound5_wip:                    
                if shipment["customer_id"] not in [None, "null" ,"", " "]:                    
                    inbound6_wip.append(shipment)
            inbound6_wip.extend(outbound6_wip) 
            context["inbound6_wip"] = inbound6_wip    

        elif processor_type == "T3":            
            linked_t2 = list(LinkProcessorToProcessor.objects.filter(linked_processor_id=processor_id, processor__processor_type__type_name="T2").values_list("processor_id", flat=True))
            grower_list = []
            outbound1 = []
            inbound1 = []
            outbound2 = []
            outbound3 = []
            inbound2 = []
            linked_t1 = []
            unique_linked_t2 = list(set(linked_t2))
            
            for t2_id in unique_linked_t2:
                linked_t1_ = list(LinkProcessor1ToProcessor.objects.filter(processor2_id=t2_id).values_list("processor1_id", flat=True))
                linked_t1 = linked_t1 + linked_t1_

                processor_type = "T2"  
                outbound3_wip = outbound_Wip_Processor(crop,t2_id,processor_type,from_date,to_date)  
                outbound3 =  outbound3 + outbound3_wip

                processor_type = "T2"                                    
                inbound2_wip = inbound_Wip_Processor(crop,t2_id,processor_type,from_date,to_date)  
                inbound2 = inbound2 + inbound2_wip

            unique_linked_t1 = list(set(linked_t1))
            for t1_id in unique_linked_t1:
                get_shipment = GrowerShipment.objects.filter(processor_id=t1_id,crop=crop).values("id")
                if get_shipment.exists():
                    bale_id = [i["id"] for i in get_shipment]  
                    get_Origin_Processor = Origin_searchby_Processor(crop,*bale_id) 
                    grower_list = grower_list + get_Origin_Processor

                    outbound1_wip = outbound1_Wip_Processor(crop,from_date,to_date,t1_id)
                    outbound1 = outbound1 + outbound1_wip

                    t1_processor = t1_Processor_Processor(crop,t1_id,from_date,to_date,*bale_id)
                    inbound1 = inbound1 + t1_processor
            
                    processor_type = "T1"
                    outbound2_wip = outbound_Wip_Processor(crop,t1_id,processor_type,from_date,to_date)         
                    outbound2 = outbound2 + outbound2_wip

            context["origin_context"] = grower_list            
            context["search_by"] = "processor"
            context["outbound1_wip"] = outbound1            
            context["t1_processor"] = inbound1           
            context["outbound2_wip"] = outbound2           
            context["outbound3_wip"] = outbound3            
            context["inbound2_wip"] = inbound2  

            processor_type = "T3"                                    
            outbound4_wip = outbound_Wip_Processor(crop,processor_id,processor_type,from_date,to_date)        
            context["outbound4_wip"] = outbound4_wip            
            processor_type = "T3"                                    
            inbound3_wip = inbound_Wip_Processor(crop,processor_id,processor_type,from_date,to_date)       
                
            context["inbound3_wip"] = inbound3_wip          
            processor_type = "T4"
            # link_t3_processor_id_list = 
            link_t4_processor_id_list = list(LinkProcessorToProcessor.objects.filter(processor_id = processor_id, linked_processor__processor_type__type_name = "T4").values_list("linked_processor_id", flat=True))
            unique_link_t4_processor_id_list = list(set(link_t4_processor_id_list))
            inbound4_wip = []
            for t4_id in unique_link_t4_processor_id_list:
                inbound2_wip = inbound_Wip_Processor(crop,t4_id,processor_type,from_date,to_date)         
                inbound4_wip = inbound4_wip +inbound2_wip
            context["inbound4_wip"] = inbound4_wip

            outbound5_wip = get_outbound5_wip(crop, outbound2, from_date, to_date)
            context["outbound5_wip"] = outbound5_wip 

            inbound5_wip = get_inbound5_wip(outbound5_wip)     
            context["inbound5_wip"] = inbound5_wip

            outbound6_wip = get_outbound6_wip(crop,outbound5_wip, from_date, to_date) 
            context["outbound6_wip"] = outbound6_wip 

            inbound6_wip = []  
            for shipment in outbound5_wip:                    
                if shipment["customer_id"] not in [None, "null" ,"", " "]:                    
                    inbound6_wip.append(shipment)
            inbound6_wip.extend(outbound6_wip) 
            context["inbound6_wip"] = inbound6_wip 
               
        elif processor_type == "T4":
            grower_list = []
            outbound1 = []
            inbound1 = []
            outbound2 = []
            outbound3 = []
            inbound2 = [] 
            outbound4_wip = []
            inbound3_wip = []
            linked_t2 = []
            linked_t1 = []
            linked_t3 = list(LinkProcessorToProcessor.objects.filter(linked_processor_id=processor_id, processor__processor_type__type_name="T3").values_list("processor_id", flat=True))
            unique_linked_t3 = list(set(linked_t3))
            
            for t3_id in unique_linked_t3:
                linked_t2_ = list(LinkProcessorToProcessor.objects.filter(linked_processor_id=t3_id, processor__processor_type__type_name="T2").values_list("processor_id", flat=True))
                linked_t2 = linked_t2 + linked_t2_

                processor_type = "T3"                                    
                outbound4_wip_ = outbound_Wip_Processor(crop,t3_id,processor_type,from_date,to_date)        
                outbound4_wip = outbound4_wip + outbound4_wip_  
                

                processor_type = "T3"                                    
                inbound3_wip_ = inbound_Wip_Processor(crop,t3_id,processor_type,from_date,to_date)         
                inbound3_wip = inbound3_wip + inbound3_wip_
            unique_linked_t2 = list(set(linked_t2))
            
            for t2_id in unique_linked_t2:
                linked_t1_ = list(LinkProcessor1ToProcessor.objects.filter(processor2_id=t2_id).values_list("processor1_id", flat=True))
                linked_t1 = linked_t1 + linked_t1_

                processor_type = "T2"  
                outbound3_wip = outbound_Wip_Processor(crop,t2_id,processor_type,from_date,to_date)  
                outbound3 =  outbound3 + outbound3_wip

                processor_type = "T2"                                    
                inbound2_wip = inbound_Wip_Processor(crop,t2_id,processor_type,from_date,to_date)  
                inbound2 = inbound2 + inbound2_wip

            unique_linked_t1 = list(set(linked_t1))            
            for t1_id in unique_linked_t1:
                get_shipment = GrowerShipment.objects.filter(processor_id=t1_id,crop=crop).values("id")
                if get_shipment.exists():
                    bale_id = [i["id"] for i in get_shipment]  
                    get_Origin_Processor = Origin_searchby_Processor(crop,*bale_id) 
                    grower_list = grower_list + get_Origin_Processor

                    outbound1_wip = outbound1_Wip_Processor(crop,from_date,to_date,t1_id)
                    outbound1 = outbound1 + outbound1_wip

                    t1_processor = t1_Processor_Processor(crop,t1_id,from_date,to_date,*bale_id)
                    inbound1 = inbound1 + t1_processor
            
                    processor_type = "T1"
                    outbound2_wip = outbound_Wip_Processor(crop,t1_id,processor_type,from_date,to_date)         
                    outbound2 = outbound2 + outbound2_wip           
            
            context["origin_context"] = grower_list
            context["search_by"] = "processor"
            context["outbound1_wip"] = outbound1
            
            context["t1_processor"] = inbound1
            context["outbound2_wip"] = outbound2
            context["outbound3_wip"] = outbound3
            context["inbound2_wip"] = inbound2
            context["inbound3_wip"] = inbound3_wip
            context["outbound4_wip"] = outbound4_wip
            processor_type = "T4"                                    
            inbound4_wip = inbound_Wip_Processor(crop,processor_id,processor_type,from_date,to_date)         
                
            context["inbound4_wip"] = inbound4_wip
            outbound5_wip = ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop = crop, processor_id=processor_id, processor_type=processor_type, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id", "processor_shipment_crop__crop","contract__secret_key","contract_id", "processor_entity_name", "processor_id","processor_type", "shipment_id","warehouse_id", "customer_id", "warehouse_name","customer_name",  "date_pulled", "carrier_type", "distributor_receive_date", "status")
            for shipment in outbound5_wip:
                if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                    shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                
                carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                shipment["carrier_id"] = carrier.carrier_id  
            context["outbound5_wip"] = outbound5_wip  

            inbound5_wip = get_inbound5_wip(outbound5_wip)     
            context["inbound5_wip"] = inbound5_wip

            outbound6_wip = get_outbound6_wip(crop,outbound5_wip, from_date, to_date) 
            context["outbound6_wip"] = outbound6_wip 

            inbound6_wip = []  
            for shipment in outbound5_wip:                    
                if shipment["customer_id"] not in [None, "null" ,"", " "]:
                    
                    inbound6_wip.append(shipment)
            inbound6_wip.extend(outbound6_wip) 
            context["inbound6_wip"] = inbound6_wip         
    else:
        context['no_rec_found_msg'] = "No Records Found"
    return context


def processor_traceability_report(crop, processor_id,processor_type, from_date, to_date, search_text):
    context = {}
    if processor_type == "T1": 
                 
        get_shipment = GrowerShipment.objects.filter(processor_id=processor_id,crop=crop).values("id")
        if get_shipment.exists() :
            bale_id = [i["id"] for i in get_shipment]  
            get_Origin_Processor = Origin_searchby_Processor(crop, *bale_id)        
            context["origin_context"] = get_Origin_Processor
            context["search_by"] = "processor"
            outbound1_wip = outbound1_Wip_Processor(crop, from_date,to_date,processor_id)
            context["outbound1_wip"] = outbound1_wip
            t1_processor = t1_Processor_Processor(crop, processor_id,from_date,to_date,*bale_id)
            context["t1_processor"] = t1_processor                                                           
                         
    elif processor_type == "T2":            
        shipments = ShipmentManagement.objects.filter(processor2_idd=processor_id, crop=crop)                 

        context["inbound2_wip"] = list(shipments.values())  
        context["outbound2_wip"] = list(shipments.values())

        processor_id_list = [i.processor_idd for i in shipments]
        unique_processor_id_list = list(set(processor_id_list))
        t1_processor_ = []
        outbound1_wip_ = []
        field_ids = []
        for i in unique_processor_id_list:
            # inbound
            t1_processor = list(GrowerShipment.objects.filter(processor_id=i, status="APPROVED", crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
            if len(t1_processor) != 0:
                for processor in t1_processor:
                    processor["processor_name"] = processor.get("processor__entity_name")
                    processor["shipment_id"] = processor.get("shipment_id")
                    processor["skuid"] = processor.get("sku")
                    processor["date"] = processor.get("approval_date")
                    processor["grower"] = processor.get("grower__name")
                    processor["farm"] = processor.get("field__farm__name")
                    processor["field"] = processor.get("field__name")
                    processor["pounds_received"] = processor.get("received_amount")
                    processor["pounds_shipped"] = processor.get("total_amount")
                    processor["unit"] = processor.get("unit_type")
                    processor["crop"] =  processor.get("crop")
                    processor["id"] =  processor.get("id")
                    try:
                        processor["pounds_delta"] = float(processor["pounds_shipped"]) - float(processor["pounds_received"])
                    except (TypeError, ValueError):
                        processor["pounds_delta"] = "Something is wrong"
            t1_processor_ = t1_processor_ + t1_processor

            #outbound
            outbound1_wip = list(GrowerShipment.objects.filter(processor_id=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("shipment_id", "processor__entity_name", "date_time","total_amount"))
            if len(outbound1_wip) != 0:
                for item in outbound1_wip:
                    item["shipment_id"] = item.get("shipment_id")
                    item["destination"] = item.get("processor__entity_name")
                    item["date"] = item.get("date_time")
                    item["quantity"] = item.get("total_amount")
                    item["transportation"] = "" 
            outbound1_wip_ = outbound1_wip_ + outbound1_wip

            field_ids_ = list(GrowerShipment.objects.filter(processor_id=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values_list("field_id", flat=True))
            field_ids = field_ids + field_ids_
        context["outbound1_wip"] = outbound1_wip_
        context["t1_processor"] = t1_processor_

        get_Origin_Grower = Origin_searchby_Grower(crop,search_text,*field_ids)                                              
        context["origin_context"] = get_Origin_Grower           

    elif processor_type == "T3":            
        shipments = ShipmentManagement.objects.filter(processor2_idd=processor_id, crop=crop).values() 
        
        context["inbound3_wip"] = list(shipments.filter(status="APPROVED"))
        outbound2_wip = []
        outbound3_wip = []
        for shipment in shipments:
            if shipment["sender_processor_type"] == "T1":
                outbound2_wip.append(shipment)
            elif shipment["sender_processor_type"] == "T2":
                outbound3_wip.append(shipment)

        if outbound3_wip:
            inbound2_wip = []
            outbound2_wip = []
            context["outbound3_wip"] = outbound3_wip
            sender_processor_id_list = [i["processor_idd"] for i in outbound3_wip]                
            for i in sender_processor_id_list:
                #inbound 2
                inbound2_wip_ = list(ShipmentManagement.objects.filter(processor2_idd=i, status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                inbound2_wip = inbound2_wip + inbound2_wip_
                #outbound 2
                outbound2_wip_ = list(ShipmentManagement.objects.filter(processor2_idd=i, status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                outbound2_wip = outbound2_wip + outbound2_wip_
            context["inbound2_wip"] = inbound2_wip
            context["outbound2_wip"] = outbound2_wip
        else:
            context["outbound3_wip"] = []
            context["outbound2_wip"] = outbound2_wip                    
            context["inbound2_wip"] = []

        processor_id_list = [i["processor_idd"] for i in outbound2_wip]
        unique_processor_id_list = list(set(processor_id_list))
        t1_processor_ = []
        outbound1_wip_ = []
        field_ids = []
        for i in unique_processor_id_list:
            # inbound
            t1_processor = list(GrowerShipment.objects.filter(processor_id=i, status="APPROVED", crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
            if len(t1_processor) != 0:
                for processor in t1_processor:
                    processor["processor_name"] = processor.get("processor__entity_name")
                    processor["shipment_id"] = processor.get("shipment_id")
                    processor["skuid"] = processor.get("sku")
                    processor["date"] = processor.get("approval_date")
                    processor["grower"] = processor.get("grower__name")
                    processor["farm"] = processor.get("field__farm__name")
                    processor["field"] = processor.get("field__name")
                    processor["pounds_received"] = processor.get("received_amount")
                    processor["pounds_shipped"] = processor.get("total_amount")
                    processor["unit"] = processor.get("unit_type")
                    processor["crop"] =  processor.get("crop")
                    processor["id"] =  processor.get("id")
                    try:
                        processor["pounds_delta"] = float(processor["pounds_shipped"]) - float(processor["pounds_received"])
                    except (TypeError, ValueError):
                        processor["pounds_delta"] = "Something is wrong"
            t1_processor_ = t1_processor_ + t1_processor

            #outbound
            outbound1_wip = list(GrowerShipment.objects.filter(processor_id=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("shipment_id", "processor__entity_name", "date_time","total_amount"))
            if len(outbound1_wip) != 0:
                for item in outbound1_wip:
                    item["shipment_id"] = item.get("shipment_id")
                    item["destination"] = item.get("processor__entity_name")
                    item["date"] = item.get("date_time")
                    item["quantity"] = item.get("total_amount")
                    item["transportation"] = "" 
            outbound1_wip_ = outbound1_wip_ + outbound1_wip

            field_ids_ = list(GrowerShipment.objects.filter(processor_id=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values_list("field_id", flat=True))
            field_ids = field_ids + field_ids_
        context["outbound1_wip"] = outbound1_wip_
        context["t1_processor"] = t1_processor_

        get_Origin_Grower = Origin_searchby_Grower(crop,search_text,*field_ids)                                              
        context["origin_context"] = get_Origin_Grower   
        
               
    elif processor_type == "T4":
        shipments = ShipmentManagement.objects.filter(processor2_idd=processor_id, crop=crop) 
        inbound4_wip = list(shipments.filter(status="APPROVED").values())
        context["inbound4_wip"] = inbound4_wip
        outbound2_wip = []
        outbound3_wip = []
        outbound4_wip = []
        for shipment in inbound4_wip:
            if shipment["sender_processor_type"] == "T1":
                outbound2_wip.append(shipment)
            elif shipment["sender_processor_type"] == "T2":
                outbound3_wip.append(shipment)
            elif shipment["sender_processor_type"] == "T3":
                outbound4_wip.append(shipment)
        
        if outbound4_wip:
            inbound3_wip = []
            outbound3_wip = []
            inbound2_wip = []
            outbound2_wip = []
            context["outbound4_wip"] = outbound4_wip
            sender_processor_id_list = [i["processor_idd"] for i in outbound4_wip]                
            for i in sender_processor_id_list:
                
                inbound3_wip_ = list(ShipmentManagement.objects.filter(processor2_idd=i, status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                inbound3_wip = inbound3_wip + inbound3_wip_
                
                outbound3_wip_ = list(ShipmentManagement.objects.filter(processor2_idd=i, status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                outbound3_wip = outbound3_wip + outbound3_wip_
            
            sender_processor_id_list2 = [i["processor_idd"] for i in outbound3_wip]                
            for i in sender_processor_id_list2:
                #inbound 2
                inbound2_wip_ = list(ShipmentManagement.objects.filter(processor2_idd=i, status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                inbound2_wip = inbound2_wip + inbound2_wip_
                #outbound 2
                outbound2_wip_ = list(ShipmentManagement.objects.filter(processor2_idd=i, status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                outbound2_wip = outbound2_wip + outbound2_wip_

            context["inbound2_wip"] = inbound2_wip
            context["outbound2_wip"] = outbound2_wip
            context["inbound3_wip"] = inbound3_wip
            context["outbound3_wip"] = outbound3_wip

        elif outbound3_wip:
            context["outbound4_wip"] = []
            context["outbound3_wip"] = outbound3_wip
            sender_processor_id_list = [i["processor_idd"] for i in outbound3_wip]                
            for i in sender_processor_id_list:
                #inbound 2
                inbound2_wip_ = list(ShipmentManagement.objects.filter(processor2_idd=i, status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                inbound2_wip = inbound2_wip + inbound2_wip_
                #outbound 2
                outbound2_wip_ = list(ShipmentManagement.objects.filter(processor2_idd=i, status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                outbound2_wip = outbound2_wip + outbound2_wip_
            context["inbound2_wip"] = inbound2_wip
            context["outbound2_wip"] = outbound2_wip
        else:
            context["outbound4_wip"] = []
            context["outbound3_wip"] = []
            context["outbound2_wip"] = outbound2_wip                    
            context["inbound2_wip"] = []

        processor_id_list = [i["processor_idd"] for i in outbound2_wip]
        unique_processor_id_list = list(set(processor_id_list))
        t1_processor_ = []
        outbound1_wip_ = []
        field_ids = []
        for i in unique_processor_id_list:
            # inbound
            t1_processor = list(GrowerShipment.objects.filter(processor_id=i, status="APPROVED", crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
            if len(t1_processor) != 0:
                for processor in t1_processor:
                    processor["processor_name"] = processor.get("processor__entity_name")
                    processor["shipment_id"] = processor.get("shipment_id")
                    processor["skuid"] = processor.get("sku")
                    processor["date"] = processor.get("approval_date")
                    processor["grower"] = processor.get("grower__name")
                    processor["farm"] = processor.get("field__farm__name")
                    processor["field"] = processor.get("field__name")
                    processor["pounds_received"] = processor.get("received_amount")
                    processor["pounds_shipped"] = processor.get("total_amount")
                    processor["unit"] = processor.get("unit_type")
                    processor["crop"] =  processor.get("crop")
                    processor["id"] =  processor.get("id")
                    try:
                        processor["pounds_delta"] = float(processor["pounds_shipped"]) - float(processor["pounds_received"])
                    except (TypeError, ValueError):
                        processor["pounds_delta"] = "Something is wrong"
            t1_processor_ = t1_processor_ + t1_processor

            #outbound
            outbound1_wip = list(GrowerShipment.objects.filter(processor_id=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("shipment_id", "processor__entity_name", "date_time","total_amount"))
            if len(outbound1_wip) != 0:
                for item in outbound1_wip:
                    item["shipment_id"] = item.get("shipment_id")
                    item["destination"] = item.get("processor__entity_name")
                    item["date"] = item.get("date_time")
                    item["quantity"] = item.get("total_amount")
                    item["transportation"] = "" 
            outbound1_wip_ = outbound1_wip_ + outbound1_wip

            field_ids_ = list(GrowerShipment.objects.filter(processor_id=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values_list("field_id", flat=True))
            field_ids = field_ids + field_ids_
        context["outbound1_wip"] = outbound1_wip_
        context["t1_processor"] = t1_processor_

        get_Origin_Grower = Origin_searchby_Grower(crop,search_text,*field_ids)                                              
        context["origin_context"] = get_Origin_Grower   
                       
    else:
        context['no_rec_found_msg'] = "No Records Found"
    return context


def skuid_traceability_response(crop, search_text, from_date, to_date):
    context = {}
    get_sku_id = GrowerShipment.objects.filter(sku=search_text, crop=crop, date_time__gte=from_date, date_time__lte=to_date)
    if get_sku_id.exists():                            
        field = list(get_sku_id.values_list('field_id', flat=True))
        sku_id = get_sku_id.first().sku                            
        get_Origin_Grower = Origin_searchby_Grower(crop,search_text,*field)                                              
        context["origin_context"] = get_Origin_Grower
        #
        if get_sku_id.first().status == "" or get_sku_id.first().status == None or get_sku_id.first().status == "DISAPPROVED":
            pass
        else:
            # outbound 1
            outbound1_wip = list(get_sku_id.values("shipment_id", "processor__entity_name", "date_time","total_amount"))
            if len(outbound1_wip) != 0:
                for item in outbound1_wip:
                    item["shipment_id"] = item.get("shipment_id")
                    item["destination"] = item.get("processor__entity_name")
                    item["date"] = item.get("date_time")
                    item["quantity"] = item.get("total_amount")
                    item["transportation"] = ""
            context["outbound1_wip"] = outbound1_wip
            
            # inbound 1
            t1_processor = list(get_sku_id.values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
            if len(t1_processor) != 0:
                for processor in t1_processor:
                    processor["processor_name"] = processor.get("processor__entity_name")
                    processor["shipment_id"] = processor.get("shipment_id")
                    processor["skuid"] = processor.get("sku")
                    processor["date"] = processor.get("approval_date")
                    processor["grower"] = processor.get("grower__name")
                    processor["farm"] = processor.get("field__farm__name")
                    processor["field"] = processor.get("field__name")
                    processor["pounds_received"] = processor.get("received_amount")
                    processor["pounds_shipped"] = processor.get("total_amount")
                    processor["unit"] = processor.get("unit_type")
                    processor["crop"] =  processor.get("crop")
                    processor["id"] =  processor.get("id")
                    try:
                        processor["pounds_delta"] = float(processor["pounds_shipped"]) - float(processor["pounds_received"])
                    except (TypeError, ValueError):
                        processor["pounds_delta"] = "Something is wrong"
            
            context["t1_processor"] = t1_processor

            # outbound 2
            t1_sku_id = sku_id
            outbound2_wip = list(ShipmentManagement.objects.filter(storage_bin_send=t1_sku_id, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
            context["outbound2_wip"] = outbound2_wip

            #inbound 2
            t1_sku_id = sku_id
            inbound2_wip = list(ShipmentManagement.objects.filter(storage_bin_send=t1_sku_id,crop=crop, receiver_processor_type="T2", status="APPROVED", date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
            context["inbound2_wip"] = inbound2_wip
            
            # outbound 3
            t2_sku_id = [i["storage_bin_recive"] for i in inbound2_wip]            
            unique_t2_sku_id = list(set(t2_sku_id))            
            outbound3_wip = []
            for l_sku in unique_t2_sku_id:
                outbound3_wip_ = list(ShipmentManagement.objects.filter(storage_bin_send=l_sku, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                outbound3_wip = outbound3_wip + outbound3_wip_
            context["outbound3_wip"] = outbound3_wip

            #inbound 3
            inbound3_wip = []
            
            unique_t2_sku_id.append(t1_sku_id)
            for l_sku3 in unique_t2_sku_id:
                inbound3_wip_ = list(ShipmentManagement.objects.filter(storage_bin_send=l_sku3, receiver_processor_type="T3", status="APPROVED", crop=crop,  date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                inbound3_wip = inbound3_wip + inbound3_wip_
            context["inbound3_wip"] = inbound3_wip

            # outbound 4
            t3_sku_id = [i["storage_bin_recive"] for i in inbound3_wip]
            unique_t3_sku_id = list(set(t3_sku_id))
            outbound4_wip = []
            for l_sku2 in unique_t3_sku_id:
                outbound4_wip_ = list(ShipmentManagement.objects.filter(storage_bin_send=l_sku2, crop=crop,  date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                outbound4_wip = outbound4_wip + outbound4_wip_                
            context["outbound4_wip"] = outbound4_wip

            #inbound 4
            inbound4_wip = []
            unique_t3_sku_id.extend(unique_t2_sku_id)
            t3_sku_id_list = list(set(unique_t3_sku_id))
            for l_sku4 in t3_sku_id_list:
                inbound4_wip_ = list(ShipmentManagement.objects.filter(storage_bin_send=l_sku4, receiver_processor_type="T4", status="APPROVED", crop=crop,  date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                inbound4_wip = inbound4_wip + inbound4_wip_            
            context["inbound4_wip"] = inbound4_wip

            outbound5_wip = get_outbound5_wip(crop, outbound2_wip, from_date, to_date)
            context["outbound5_wip"] = outbound5_wip 

            inbound5_wip = get_inbound5_wip(outbound5_wip)     
            context["inbound5_wip"] = inbound5_wip

            outbound6_wip = get_outbound6_wip(crop,outbound5_wip, from_date, to_date) 
            context["outbound6_wip"] = outbound6_wip 

            inbound6_wip = []  
            for shipment in outbound5_wip:                    
                if shipment["customer_id"] not in [None, "null" ,"", " "]:
                    inbound6_wip.append(shipment)
            inbound6_wip.extend(outbound6_wip) 
            context["inbound6_wip"] = inbound6_wip 
            
    elif not get_sku_id:        
        sku_id = ShipmentManagement.objects.filter(storage_bin_send=search_text, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date)
        
        if sku_id.exists():
            get_sku_id = sku_id.first().storage_bin_send            
            sender_processor_type = sku_id.first().sender_processor_type
            
            if sender_processor_type == "T1":
                field_ids = list(GrowerShipment.objects.filter(sku=get_sku_id, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values_list("field_id", flat=True))
                get_Origin_Grower = Origin_searchby_Grower(crop,search_text,*field_ids)                                              
                context["origin_context"] = get_Origin_Grower

                #outbound 1
                outbound1_wip = list(GrowerShipment.objects.filter(sku=get_sku_id, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("shipment_id", "processor__entity_name", "date_time","total_amount"))
                if len(outbound1_wip) != 0:
                    for item in outbound1_wip:
                        item["shipment_id"] = item.get("shipment_id")
                        item["destination"] = item.get("processor__entity_name")
                        item["date"] = item.get("date_time")
                        item["quantity"] = item.get("total_amount")
                        item["transportation"] = ""
                context["outbound1_wip"] = outbound1_wip

                #inbound 1
                t1_processor = list(GrowerShipment.objects.filter(sku=get_sku_id, status="APPROVED", crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
                if len(t1_processor) != 0:
                    for processor in t1_processor:
                        processor["processor_name"] = processor.get("processor__entity_name")
                        processor["shipment_id"] = processor.get("shipment_id")
                        processor["skuid"] = processor.get("sku")
                        processor["date"] = processor.get("approval_date")
                        processor["grower"] = processor.get("grower__name")
                        processor["farm"] = processor.get("field__farm__name")
                        processor["field"] = processor.get("field__name")
                        processor["pounds_received"] = processor.get("received_amount")
                        processor["pounds_shipped"] = processor.get("total_amount")
                        processor["unit"] = processor.get("unit_type")
                        processor["crop"] =  processor.get("crop")
                        processor["id"] =  processor.get("id")
                        try:
                            processor["pounds_delta"] = float(processor["pounds_shipped"]) - float(processor["pounds_received"])
                        except (TypeError, ValueError):
                            processor["pounds_delta"] = "Something is wrong"
                
                context["t1_processor"] = t1_processor

                #outbound 2
                outbound2_wip = ShipmentManagement.objects.filter(storage_bin_send=get_sku_id, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values()
                context["outbound2_wip"] = outbound2_wip

                #inbound 2
                inbound2_wip = ShipmentManagement.objects.filter(storage_bin_send=get_sku_id, receiver_processor_type="T2",status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values()
                context["inbound2_wip"] = inbound2_wip

                #outbound 3
                t2_sku_id = [i["storage_bin_recive"] for i in inbound2_wip]
                unique_t2_sku_id = list(set(t2_sku_id))
                outbound3_wip = []
                for l_sku in unique_t2_sku_id:
                    outbound3_wip_ = list(ShipmentManagement.objects.filter(storage_bin_send=l_sku, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    outbound3_wip = outbound3_wip + outbound3_wip_
                context["outbound3_wip"] = outbound3_wip

                #inbound 3
                inbound3_wip = []
                unique_t2_sku_id.append(get_sku_id)
                for l_sku3 in unique_t2_sku_id:
                    inbound3_wip_ = list(ShipmentManagement.objects.filter(storage_bin_send=l_sku3, receiver_processor_type="T3", status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    inbound3_wip = inbound3_wip + inbound3_wip_
                context["inbound3_wip"] = inbound3_wip

                # outbound 4
                t3_sku_id = [i["storage_bin_recive"] for i in inbound3_wip]
                unique_t3_sku_id =list(set(t3_sku_id))
                outbound4_wip = []
                for l_sku2 in unique_t3_sku_id:
                    outbound4_wip_ = list(ShipmentManagement.objects.filter(storage_bin_send=l_sku2, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    outbound4_wip = outbound4_wip + outbound4_wip_
                context["outbound4_wip"] = outbound4_wip

                #inbound 4
                inbound4_wip = []
                unique_t3_sku_id.extend(unique_t2_sku_id)
                t3_sku_id_list = list(set(unique_t3_sku_id))
                for l_sku4 in t3_sku_id_list:
                    inbound4_wip_ = list(ShipmentManagement.objects.filter(storage_bin_send=l_sku4, receiver_processor_type="T4", status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    inbound4_wip = inbound4_wip + inbound4_wip_
                context["inbound4_wip"] = inbound4_wip
                
                outbound5_wip = get_outbound5_wip(crop, outbound2_wip, from_date, to_date)
                context["outbound5_wip"] = outbound5_wip 

                inbound5_wip = get_inbound5_wip(outbound5_wip)     
                context["inbound5_wip"] = inbound5_wip

                outbound6_wip = get_outbound6_wip(crop,outbound5_wip, from_date, to_date) 
                context["outbound6_wip"] = outbound6_wip 

                inbound6_wip = []  
                for shipment in outbound5_wip:                    
                    if shipment["customer_id"] not in [None, "null" ,"", " "]:
                       
                        inbound6_wip.append(shipment)
                inbound6_wip.extend(outbound6_wip) 
                context["inbound6_wip"] = inbound6_wip 

            if sender_processor_type == "T2":
                #outbound 2
                outbound2_wip = list(ShipmentManagement.objects.filter(storage_bin_recive=get_sku_id, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                context["outbound2_wip"] = outbound2_wip

                #inbound 2
                inbound2_wip = list(ShipmentManagement.objects.filter(storage_bin_recive=get_sku_id, receiver_processor_type="T2", status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                context["inbound2_wip"] = inbound2_wip

                #outbound 3
                outbound3_wip = list(ShipmentManagement.objects.filter(storage_bin_send=get_sku_id, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())                                       
                context["outbound3_wip"] = outbound3_wip

                #inbound 3
                inbound3_wip = list(ShipmentManagement.objects.filter(storage_bin_send=get_sku_id, receiver_processor_type="T3", status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values()) 
                context["inbound3_wip"] = inbound3_wip

                #outbound 4
                t3_sku_id = [i["storage_bin_recive"] for i in inbound3_wip]
                unique_t3_sku_id = list(set(t3_sku_id))
                outbound4_wip = []
                for l_sku2 in unique_t3_sku_id:
                    outbound4_wip_ = list(ShipmentManagement.objects.filter(storage_bin_send=l_sku2, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    outbound4_wip = outbound4_wip + outbound4_wip_
                context["outbound4_wip"] = outbound4_wip

                #inbound 4
                inbound4_wip = []
                unique_t3_sku_id.append(get_sku_id)
                for l_sku4 in unique_t3_sku_id:
                    inbound4_wip_ = list(ShipmentManagement.objects.filter(storage_bin_send=l_sku4, receiver_processor_type="T4", status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    inbound4_wip = inbound4_wip + inbound4_wip_
                context["inbound4_wip"] = inbound4_wip

                #inbound 1
                sku_id_list = [i["storage_bin_send"] for i in inbound2_wip]
                t1_processor_ = []
                outbound1_wip_ = []
                field_ids = []
                for i in sku_id_list:
                    # inbound
                    t1_processor = list(GrowerShipment.objects.filter(sku=i, status="APPROVED", crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
                    if len(t1_processor) != 0:
                        for processor in t1_processor:
                            processor["processor_name"] = processor.get("processor__entity_name")
                            processor["shipment_id"] = processor.get("shipment_id")
                            processor["skuid"] = processor.get("sku")
                            processor["date"] = processor.get("approval_date")
                            processor["grower"] = processor.get("grower__name")
                            processor["farm"] = processor.get("field__farm__name")
                            processor["field"] = processor.get("field__name")
                            processor["pounds_received"] = processor.get("received_amount")
                            processor["pounds_shipped"] = processor.get("total_amount")
                            processor["unit"] = processor.get("unit_type")
                            processor["crop"] =  processor.get("crop")
                            processor["id"] =  processor.get("id")
                            try:
                                processor["pounds_delta"] = float(processor["pounds_shipped"]) - float(processor["pounds_received"])
                            except (TypeError, ValueError):
                                processor["pounds_delta"] = "Something is wrong"
                    t1_processor_ = t1_processor_ + t1_processor

                    #outbound
                    outbound1_wip = list(GrowerShipment.objects.filter(sku=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("shipment_id", "processor__entity_name", "date_time","total_amount"))
                    if len(outbound1_wip) != 0:
                        for item in outbound1_wip:
                            item["shipment_id"] = item.get("shipment_id")
                            item["destination"] = item.get("processor__entity_name")
                            item["date"] = item.get("date_time")
                            item["quantity"] = item.get("total_amount")
                            item["transportation"] = ""
                    outbound1_wip_ = outbound1_wip_ + outbound1_wip
                    field_ids_ = list(GrowerShipment.objects.filter(sku=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values_list("field_id", flat=True))
                    field_ids = field_ids + field_ids_
                context["outbound1_wip"] = outbound1_wip_
                context["t1_processor"] = t1_processor_
                get_Origin_Grower = Origin_searchby_Grower(crop,search_text,*field_ids)                                              
                context["origin_context"] = get_Origin_Grower

                outbound5_wip = get_outbound5_wip(crop, outbound2_wip, from_date, to_date)
                context["outbound5_wip"] = outbound5_wip 

                inbound5_wip = get_inbound5_wip(outbound5_wip)     
                context["inbound5_wip"] = inbound5_wip

                outbound6_wip = get_outbound6_wip(crop,outbound5_wip, from_date, to_date) 
                context["outbound6_wip"] = outbound6_wip 

                inbound6_wip = []  
                for shipment in outbound5_wip:                    
                    if shipment["customer_id"] not in [None, "null" ,"", " "]:
                        
                        inbound6_wip.append(shipment)
                inbound6_wip.extend(outbound6_wip) 
                context["inbound6_wip"] = inbound6_wip 

            if sender_processor_type == "T3":                
                #outbound 4
                outbound4_wip = list(ShipmentManagement.objects.filter(storage_bin_send=get_sku_id, receiver_processor_type="T4", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                context["outbound4_wip"] = outbound4_wip

                #inbound 4
                inbound4_wip = list(ShipmentManagement.objects.filter(storage_bin_send=get_sku_id, receiver_processor_type="T4", status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                context["inbound4_wip"] = inbound4_wip                

                #inbound 3
                inbound3_wip = list(ShipmentManagement.objects.filter(storage_bin_recive=get_sku_id, receiver_processor_type="T3", status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                context["inbound3_wip"] = inbound3_wip

                #outbound 3
                outbound3_wip = list(ShipmentManagement.objects.filter(storage_bin_recive=get_sku_id, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                context["outbound3_wip"] = outbound3_wip                                
                
                sku_id_list = [i["storage_bin_send"] for i in outbound3_wip]
                inbound2_wip = []
                outbound2_wip = []
                for i in sku_id_list:
                    #inbound 2
                    inbound2_wip_ = list(ShipmentManagement.objects.filter(storage_bin_recive=i, receiver_processor_type="T2", status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    inbound2_wip = inbound2_wip + inbound2_wip_
                    #outbound 2
                    outbound2_wip_ = list(ShipmentManagement.objects.filter(storage_bin_recive=i, status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    outbound2_wip = outbound2_wip + outbound2_wip_
                context["inbound2_wip"] = inbound2_wip
                context["outbound2_wip"] = outbound2_wip

                grower_sku_id_list = [i["storage_bin_send"] for i in outbound2_wip]
                unique_grower_sku_id_list = list(set(grower_sku_id_list))
                t1_processor_ = []
                outbound1_wip_ = []
                field_ids = []
                for i in unique_grower_sku_id_list:
                    # inbound
                    t1_processor = list(GrowerShipment.objects.filter(sku=i, status="APPROVED", crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
                    if len(t1_processor) != 0:
                        for processor in t1_processor:
                            processor["processor_name"] = processor.get("processor__entity_name")
                            processor["shipment_id"] = processor.get("shipment_id")
                            processor["skuid"] = processor.get("sku")
                            processor["date"] = processor.get("approval_date")
                            processor["grower"] = processor.get("grower__name")
                            processor["farm"] = processor.get("field__farm__name")
                            processor["field"] = processor.get("field__name")
                            processor["pounds_received"] = processor.get("received_amount")
                            processor["pounds_shipped"] = processor.get("total_amount")
                            processor["unit"] = processor.get("unit_type")
                            processor["crop"] =  processor.get("crop")
                            processor["id"] =  processor.get("id")
                            try:
                                processor["pounds_delta"] = float(processor["pounds_shipped"]) - float(processor["pounds_received"])
                            except (TypeError, ValueError):
                                processor["pounds_delta"] = "Something is wrong"
                    t1_processor_ = t1_processor_ + t1_processor

                    #outbound
                    outbound1_wip = list(GrowerShipment.objects.filter(sku=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("shipment_id", "processor__entity_name", "date_time","total_amount"))
                    if len(outbound1_wip) != 0:
                        for item in outbound1_wip:
                            item["shipment_id"] = item.get("shipment_id")
                            item["destination"] = item.get("processor__entity_name")
                            item["date"] = item.get("date_time")
                            item["quantity"] = item.get("total_amount")
                            item["transportation"] = "" 
                    outbound1_wip_ = outbound1_wip_ + outbound1_wip
                    field_ids_ = list(GrowerShipment.objects.filter(sku=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values_list("field_id", flat=True))
                    field_ids = field_ids + field_ids_
                context["outbound1_wip"] = outbound1_wip_
                context["t1_processor"] = t1_processor_

                get_Origin_Grower = Origin_searchby_Grower(crop,search_text,*field_ids)                                              
                context["origin_context"] = get_Origin_Grower

                outbound5_wip = get_outbound5_wip(crop, outbound4_wip, from_date, to_date)
                context["outbound5_wip"] = outbound5_wip
                                            
        elif not sku_id.exists():
            get_sku = ShipmentManagement.objects.filter(storage_bin_recive=search_text, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date)
            if get_sku:                
                sender_processor_type = get_sku.first().sender_processor_type
                sku_id = get_sku.first().storage_bin_recive

                if sender_processor_type == "T1":
                    inbound4_wip = list(ShipmentManagement.objects.filter(storage_bin_recive=sku_id, receiver_processor_type="T4", sender_processor_type="T1", status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    context["inbound4_wip"] = inbound4_wip

                    outbound2_wip = list(ShipmentManagement.objects.filter(crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date, sender_processor_type="T1", storage_bin_recive=sku_id).values())
                    context["outbound2_wip"] = outbound2_wip

                    context["inbound3_wip"] = []
                    context["outbound3_wip"] = []
                    context["inbound2_wip"] = []
                    t1_processor_ = []
                    outbound1_wip_ = []
                    field_ids = []

                    skuid_list = [i["storage_bin_send"] for i in outbound2_wip]
                    unique_skuid_list = list(set(skuid_list))
                    for i in unique_skuid_list:
                        # inbound
                        t1_processor = list(GrowerShipment.objects.filter(sku=i, status="APPROVED", crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
                        if len(t1_processor) != 0:
                           for processor in t1_processor:
                                processor["processor_name"] = processor.get("processor__entity_name")
                                processor["shipment_id"] = processor.get("shipment_id")
                                processor["skuid"] = processor.get("sku")
                                processor["date"] = processor.get("approval_date")
                                processor["grower"] = processor.get("grower__name")
                                processor["farm"] = processor.get("field__farm__name")
                                processor["field"] = processor.get("field__name")
                                processor["pounds_received"] = processor.get("received_amount")
                                processor["pounds_shipped"] = processor.get("total_amount")
                                processor["unit"] = processor.get("unit_type")
                                processor["crop"] =  processor.get("crop")
                                processor["id"] =  processor.get("id")
                                try:
                                    processor["pounds_delta"] = float(processor["pounds_shipped"]) - float(processor["pounds_received"])
                                except (TypeError, ValueError):
                                    processor["pounds_delta"] = "Something is wrong"
                        t1_processor_ = t1_processor_ + t1_processor

                        #outbound
                        outbound1_wip = list(GrowerShipment.objects.filter(sku=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("shipment_id", "processor__entity_name", "date_time","total_amount"))
                        if len(outbound1_wip) != 0:
                            for item in outbound1_wip:
                                item["shipment_id"] = item.get("shipment_id")
                                item["destination"] = item.get("processor__entity_name")
                                item["date"] = item.get("date_time")
                                item["quantity"] = item.get("total_amount")
                                item["transportation"] = ""
                        outbound1_wip_ = outbound1_wip_ + outbound1_wip
                        field_ids_ = list(GrowerShipment.objects.filter(sku=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values_list("field_id", flat=True))
                        field_ids = field_ids + field_ids_
                    context["outbound1_wip"] = outbound1_wip_
                    context["t1_processor"] = t1_processor_

                    get_Origin_Grower = Origin_searchby_Grower(crop,search_text,*field_ids)                                              
                    context["origin_context"] = get_Origin_Grower

                    outbound5_wip = ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=crop, processor_id=int(get_sku.first().processor2_idd), processor_type="T4", date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id", "processor_shipment_crop__crop","contract__secret_key","contract_id", "processor_entity_name", "processor_id","processor_type", "shipment_id", "warehouse_id", "customer_id", "warehouse_name","customer_name", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in outbound5_wip:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    context["outbound5_wip"] = outbound5_wip

                    inbound5_wip = get_inbound5_wip(outbound5_wip)     
                    context["inbound5_wip"] = inbound5_wip

                    outbound6_wip = get_outbound6_wip(crop,outbound5_wip, from_date, to_date) 
                    context["outbound6_wip"] = outbound6_wip 

                    inbound6_wip = []  
                    for shipment in outbound5_wip:                    
                        if shipment["customer_id"] not in [None, "null" ,"", " "]:
                           
                            inbound6_wip.append(shipment)
                    inbound6_wip.extend(outbound6_wip) 
                    context["inbound6_wip"] = inbound6_wip 

                if sender_processor_type == "T2":
                    inbound4_wip = list(ShipmentManagement.objects.filter(storage_bin_recive=sku_id, receiver_processor_type="T4", sender_processor_type="T2", status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    context["inbound4_wip"] = inbound4_wip

                    outbound3_wip = list(ShipmentManagement.objects.filter(storage_bin_recive=sku_id, sender_processor_type="T2", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    context["outbound3_wip"] = outbound3_wip

                    context["inbound3_wip"] = []
                    inbound2_wip = []
                    outbound2_wip = []

                    sku_id_list_ = [i["storage_bin_send"] for i in outbound3_wip]
                    unique_sku_id_list_ = list(set(sku_id_list_))
                    for i in unique_sku_id_list_:
                        inbound2_wip_ = list(ShipmentManagement.objects.filter(storage_bin_recive=i, receiver_processor_type="T2", status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                        inbound2_wip = inbound2_wip + inbound2_wip_
                        
                        outbound2_wip_ = list(ShipmentManagement.objects.filter(storage_bin_recive=i, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                        outbound2_wip = outbound2_wip + outbound2_wip_

                    context["inbound2_wip"] = inbound2_wip
                    context["outbound2_wip"] = outbound2_wip

                    t1_processor_ = []
                    outbound1_wip_ = []
                    field_ids = []
                    skuid_list = [i["storage_bin_send"] for i in outbound2_wip]
                    unique_skuid_list = list(set(skuid_list))
                    for i in unique_skuid_list:
                        # inbound
                        t1_processor = list(GrowerShipment.objects.filter(sku=i, status="APPROVED", crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
                        if len(t1_processor) != 0:
                           for processor in t1_processor:
                                processor["processor_name"] = processor.get("processor__entity_name")
                                processor["shipment_id"] = processor.get("shipment_id")
                                processor["skuid"] = processor.get("sku")
                                processor["date"] = processor.get("approval_date")
                                processor["grower"] = processor.get("grower__name")
                                processor["farm"] = processor.get("field__farm__name")
                                processor["field"] = processor.get("field__name")
                                processor["pounds_received"] = processor.get("received_amount")
                                processor["pounds_shipped"] = processor.get("total_amount")
                                processor["unit"] = processor.get("unit_type")
                                processor["crop"] =  processor.get("crop")
                                processor["id"] =  processor.get("id")
                                try:
                                    processor["pounds_delta"] = float(processor["pounds_shipped"]) - float(processor["pounds_received"])
                                except (TypeError, ValueError):
                                    processor["pounds_delta"] = "Something is wrong"
                        t1_processor_ = t1_processor_ + t1_processor

                        #outbound
                        outbound1_wip = list(GrowerShipment.objects.filter(sku=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("shipment_id", "processor__entity_name", "date_time","total_amount"))
                        if len(outbound1_wip) != 0:
                            for item in outbound1_wip:
                                item["shipment_id"] = item.get("shipment_id")
                                item["destination"] = item.get("processor__entity_name")
                                item["date"] = item.get("date_time")
                                item["quantity"] = item.get("total_amount")
                                item["transportation"] = ""
                        outbound1_wip_ = outbound1_wip_ + outbound1_wip
                        field_ids_ = list(GrowerShipment.objects.filter(sku=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values_list("field_id", flat=True))
                        field_ids = field_ids + field_ids_
                    context["outbound1_wip"] = outbound1_wip_
                    context["t1_processor"] = t1_processor_

                    get_Origin_Grower = Origin_searchby_Grower(crop,search_text,*field_ids)                                              
                    context["origin_context"] = get_Origin_Grower

                    outbound5_wip = ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=crop, processor_id=int(get_sku.first().processor2_idd), processor_type="T4", date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id", "processor_shipment_crop__crop","contract__secret_key","contract_id", "processor_entity_name", "processor_id", "processor_type","shipment_id", "warehouse_id", "customer_id", "warehouse_name","customer_name", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in outbound5_wip:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    context["outbound5_wip"] = outbound5_wip

                    inbound5_wip = get_inbound5_wip(outbound5_wip)     
                    context["inbound5_wip"] = inbound5_wip

                    outbound6_wip = get_outbound6_wip(crop,outbound5_wip, from_date, to_date) 
                    context["outbound6_wip"] = outbound6_wip 

                    inbound6_wip = []  
                    for shipment in outbound5_wip:                    
                        if shipment["customer_id"] not in [None, "null" ,"", " "]:
                            
                            inbound6_wip.append(shipment)
                    inbound6_wip.extend(outbound6_wip) 
                    context["inbound6_wip"] = inbound6_wip 

                if sender_processor_type == "T3":
                    inbound4_wip = list(ShipmentManagement.objects.filter(storage_bin_recive=sku_id, receiver_processor_type="T4", status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    context["inbound4_wip"] = inbound4_wip

                    outbound4_wip = list(ShipmentManagement.objects.filter(storage_bin_recive=sku_id, status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    context["outbound4_wip"] = outbound4_wip

                    inbound3_wip = []
                    outbound3_wip = []
                    sku_id_list = [i["storage_bin_send"] for i in outbound4_wip]
                    unique_sku_id_list = list(set(sku_id_list))
                    for i in unique_sku_id_list:
                        inbound3_wip_ = list(ShipmentManagement.objects.filter(storage_bin_recive=i, receiver_processor_type="T3", status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                        inbound3_wip = inbound3_wip + inbound3_wip_
                        
                        outbound3_wip_ = list(ShipmentManagement.objects.filter(storage_bin_recive=i, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                        outbound3_wip = outbound3_wip + outbound3_wip_

                    context["inbound3_wip"] = inbound3_wip
                    context["outbound3_wip"] = outbound3_wip

                    inbound2_wip = []
                    outbound2_wip = []
                    sku_id_list_ = [i["storage_bin_send"] for i in outbound3_wip]
                    unique_sku_id_list_ = list(set(sku_id_list_))
                    for i in unique_sku_id_list_:
                        inbound2_wip_ = list(ShipmentManagement.objects.filter(storage_bin_recive=i, receiver_processor_type="T2", status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                        inbound2_wip = inbound2_wip + inbound2_wip_
                        
                        outbound2_wip_ = list(ShipmentManagement.objects.filter(storage_bin_recive=i, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                        outbound2_wip = outbound2_wip + outbound2_wip_

                    context["inbound2_wip"] = inbound2_wip
                    context["outbound2_wip"] = outbound2_wip

                    t1_processor_ = []
                    outbound1_wip_ = []
                    field_ids = []
                    skuid_list = [i["storage_bin_send"] for i in outbound2_wip]
                    unique_skuid_list = list(set(skuid_list))
                    for i in unique_skuid_list:
                        # inbound
                        t1_processor = list(GrowerShipment.objects.filter(sku=i, status="APPROVED", crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
                        if len(t1_processor) != 0:
                           for processor in t1_processor:
                                processor["processor_name"] = processor.get("processor__entity_name")
                                processor["shipment_id"] = processor.get("shipment_id")
                                processor["skuid"] = processor.get("sku")
                                processor["date"] = processor.get("approval_date")
                                processor["grower"] = processor.get("grower__name")
                                processor["farm"] = processor.get("field__farm__name")
                                processor["field"] = processor.get("field__name")
                                processor["pounds_received"] = processor.get("received_amount")
                                processor["pounds_shipped"] = processor.get("total_amount")
                                processor["unit"] = processor.get("unit_type")
                                processor["crop"] =  processor.get("crop")
                                processor["id"] =  processor.get("id")
                                try:
                                    processor["pounds_delta"] = float(processor["pounds_shipped"]) - float(processor["pounds_received"])
                                except (TypeError, ValueError):
                                    processor["pounds_delta"] = "Something is wrong"
                        t1_processor_ = t1_processor_ + t1_processor

                        #outbound
                        outbound1_wip = list(GrowerShipment.objects.filter(sku=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("shipment_id", "processor__entity_name", "date_time","total_amount"))
                        if len(outbound1_wip) != 0:
                            for item in outbound1_wip:
                                item["shipment_id"] = item.get("shipment_id")
                                item["destination"] = item.get("processor__entity_name")
                                item["date"] = item.get("date_time")
                                item["quantity"] = item.get("total_amount")
                                item["transportation"] = ""
                        outbound1_wip_ = outbound1_wip_ + outbound1_wip
                        field_ids_ = list(GrowerShipment.objects.filter(sku=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values_list("field_id", flat=True))
                        field_ids = field_ids + field_ids_
                    context["outbound1_wip"] = outbound1_wip_
                    context["t1_processor"] = t1_processor_

                    get_Origin_Grower = Origin_searchby_Grower(crop,search_text,*field_ids)                                              
                    context["origin_context"] = get_Origin_Grower

                    outbound5_wip = ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=crop, processor_id=int(get_sku.first().processor2_idd), processor_type="T4", date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id", "processor_shipment_crop__crop","contract__secret_key","contract_id", "processor_entity_name", "processor_id","processor_type", "shipment_id", "warehouse_id", "customer_id", "warehouse_name","customer_name", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in outbound5_wip:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    context["outbound5_wip"] = outbound5_wip

                    inbound5_wip = get_inbound5_wip(outbound5_wip)     
                    context["inbound5_wip"] = inbound5_wip

                    outbound6_wip = get_outbound6_wip(crop,outbound5_wip, from_date, to_date) 
                    context["outbound6_wip"] = outbound6_wip 

                    inbound6_wip = []  
                    for shipment in outbound5_wip:                    
                        if shipment["customer_id"] not in [None, "null" ,"", " "]:
                            
                            inbound6_wip.append(shipment)
                    inbound6_wip.extend(outbound6_wip) 
                    context["inbound6_wip"] = inbound6_wip 
                else:
                    context['no_rec_found_msg'] = "No Records Found"
            else:
                context['no_rec_found_msg'] = "No Records Found"
        else:
            context['no_rec_found_msg'] = "No Records Found"  
    else:
        context['no_rec_found_msg'] = "No Records Found"           
    
    return context


def shipmentid_traceability_response(crop, search_text, from_date, to_date):
    context = {}
    get_sku_id = GrowerShipment.objects.filter(shipment_id=search_text, crop=crop, date_time__gte=from_date, date_time__lte=to_date)
    if get_sku_id.exists():                            
        field = list(get_sku_id.values_list('field_id', flat=True))                                   
        get_Origin_Grower = Origin_searchby_Grower(crop,search_text,*field)                                              
        context["origin_context"] = get_Origin_Grower
        #
        if get_sku_id.first().status == "" or get_sku_id.first().status == None or get_sku_id.first().status == "DISAPPROVED":
            pass
        else:
            # outbound 1
            outbound1_wip = list(get_sku_id.values("shipment_id", "processor__entity_name", "date_time","total_amount"))
            if len(outbound1_wip) != 0:
                for item in outbound1_wip:
                    item["shipment_id"] = item.get("shipment_id")
                    item["destination"] = item.get("processor__entity_name")
                    item["date"] = item.get("date_time")
                    item["quantity"] = item.get("total_amount")
                    item["transportation"] = ""
            context["outbound1_wip"] = outbound1_wip
            
            # inbound 1
            t1_processor = list(get_sku_id.values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
            if len(t1_processor) != 0:
                for processor in t1_processor:
                    processor["processor_name"] = processor.get("processor__entity_name")
                    processor["shipment_id"] = processor.get("shipment_id")
                    processor["skuid"] = processor.get("sku")
                    processor["date"] = processor.get("approval_date")
                    processor["grower"] = processor.get("grower__name")
                    processor["farm"] = processor.get("field__farm__name")
                    processor["field"] = processor.get("field__name")
                    processor["pounds_received"] = processor.get("received_amount")
                    processor["pounds_shipped"] = processor.get("total_amount")
                    processor["unit"] = processor.get("unit_type")
                    processor["crop"] =  processor.get("crop")
                    processor["id"] =  processor.get("id")
                    try:
                        processor["pounds_delta"] = float(processor["pounds_shipped"]) - float(processor["pounds_received"])
                    except (TypeError, ValueError):
                        processor["pounds_delta"] = "Something is wrong"
            
            context["t1_processor"] = t1_processor
            
            
    elif not get_sku_id and ShipmentManagement.objects.filter(shipment_id=search_text, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).exists():        
        sku_id = ShipmentManagement.objects.filter(shipment_id=search_text, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date)
                           
        sender_processor_type = sku_id.first().sender_processor_type
        sender_processor_id = sku_id.first().processor_idd
        receiver_processor_id = sku_id.first().processor2_idd
        receiver_processor_type = sku_id.first().receiver_processor_type
        
        if sender_processor_type == "T1":
            field_ids = list(GrowerShipment.objects.filter(processor_id=sender_processor_id, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values_list("field_id", flat=True))
            get_Origin_Grower = Origin_searchby_Grower(crop,search_text,*field_ids)                                              
            context["origin_context"] = get_Origin_Grower

            #outbound 1
            outbound1_wip = list(GrowerShipment.objects.filter(processor_id=sender_processor_id, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("shipment_id", "processor__entity_name", "date_time","total_amount"))
            if len(outbound1_wip) != 0:
                for item in outbound1_wip:
                    item["shipment_id"] = item.get("shipment_id")
                    item["destination"] = item.get("processor__entity_name")
                    item["date"] = item.get("date_time")
                    item["quantity"] = item.get("total_amount")
                    item["transportation"] = ""
            context["outbound1_wip"] = outbound1_wip

            #inbound 1
            t1_processor = list(GrowerShipment.objects.filter(processor_id=sender_processor_id, status="APPROVED", crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
            if len(t1_processor) != 0:
                for processor in t1_processor:
                    processor["processor_name"] = processor.get("processor__entity_name")
                    processor["shipment_id"] = processor.get("shipment_id")
                    processor["skuid"] = processor.get("sku")
                    processor["date"] = processor.get("approval_date")
                    processor["grower"] = processor.get("grower__name")
                    processor["farm"] = processor.get("field__farm__name")
                    processor["field"] = processor.get("field__name")
                    processor["pounds_received"] = processor.get("received_amount")
                    processor["pounds_shipped"] = processor.get("total_amount")
                    processor["unit"] = processor.get("unit_type")
                    processor["crop"] =  processor.get("crop")
                    processor["id"] =  processor.get("id")
                    try:
                        processor["pounds_delta"] = float(processor["pounds_shipped"]) - float(processor["pounds_received"])
                    except (TypeError, ValueError):
                        processor["pounds_delta"] = "Something is wrong"
            
            context["t1_processor"] = t1_processor

            #outbound 2
            outbound2_wip = ShipmentManagement.objects.filter(shipment_id=search_text, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values()
            context["outbound2_wip"] = outbound2_wip               
            
            if receiver_processor_type == "T2":
                context["inbound2_wip"] = outbound2_wip
            elif receiver_processor_type == "T3":
                context["inbound3_wip"] = outbound2_wip
            elif receiver_processor_type == "T4":
                context["inbound4_wip"] = outbound2_wip          
                            
        if sender_processor_type == "T2":
            #outbound 2
            outbound2_wip = list(ShipmentManagement.objects.filter(processor2_idd=sender_processor_id, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
            context["outbound2_wip"] = outbound2_wip

            #inbound 2
            inbound2_wip = list(ShipmentManagement.objects.filter(processor2_idd=sender_processor_id, status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
            context["inbound2_wip"] = inbound2_wip

            #outbound 3
            outbound3_wip = list(ShipmentManagement.objects.filter(shipment_id=search_text, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())                                       
            context["outbound3_wip"] = outbound3_wip

            if receiver_processor_type == "T3":
                context["inbound3_wip"] = outbound3_wip
            elif receiver_processor_type == "T4":
                context["inbound4_wip"] = outbound3_wip 

            #inbound 1
            t1_processor_id_list = [i["processor_idd"] for i in inbound2_wip]
            t1_processor_ = []
            outbound1_wip_ = []
            field_ids = []
            for i in t1_processor_id_list:
                # inbound
                t1_processor = list(GrowerShipment.objects.filter(processor_id=i, status="APPROVED", crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
                if len(t1_processor) != 0:
                    for processor in t1_processor:
                        processor["processor_name"] = processor.get("processor__entity_name")
                        processor["shipment_id"] = processor.get("shipment_id")
                        processor["skuid"] = processor.get("sku")
                        processor["date"] = processor.get("approval_date")
                        processor["grower"] = processor.get("grower__name")
                        processor["farm"] = processor.get("field__farm__name")
                        processor["field"] = processor.get("field__name")
                        processor["pounds_received"] = processor.get("received_amount")
                        processor["pounds_shipped"] = processor.get("total_amount")
                        processor["unit"] = processor.get("unit_type")
                        processor["crop"] =  processor.get("crop")
                        processor["id"] =  processor.get("id")
                        try:
                            processor["pounds_delta"] = float(processor["pounds_shipped"]) - float(processor["pounds_received"])
                        except (TypeError, ValueError):
                            processor["pounds_delta"] = "Something is wrong"
                t1_processor_ = t1_processor_ + t1_processor

                #outbound
                outbound1_wip = list(GrowerShipment.objects.filter(processor_id=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("shipment_id", "processor__entity_name", "date_time","total_amount"))
                if len(outbound1_wip) != 0:
                    for item in outbound1_wip:
                        item["shipment_id"] = item.get("shipment_id")
                        item["destination"] = item.get("processor__entity_name")
                        item["date"] = item.get("date_time")
                        item["quantity"] = item.get("total_amount")
                        item["transportation"] = ""
                outbound1_wip_ = outbound1_wip_ + outbound1_wip
                field_ids_ = list(GrowerShipment.objects.filter(processor_id=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values_list("field_id", flat=True))
                field_ids = field_ids + field_ids_

            context["outbound1_wip"] = outbound1_wip_
            context["t1_processor"] = t1_processor_
            get_Origin_Grower = Origin_searchby_Grower(crop,search_text,*field_ids)                                              
            context["origin_context"] = get_Origin_Grower                

        if sender_processor_type == "T3":                
            #outbound 4
            outbound4_wip = list(ShipmentManagement.objects.filter(shipment_id=search_text, crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
            context["outbound4_wip"] = outbound4_wip

            #inbound 4
            if receiver_processor_type == "T4":
                context["inbound4_wip"] = outbound4_wip                

            #inbound 3
            inbound3_wip = list(ShipmentManagement.objects.filter(processor2_idd=sender_processor_id, status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
            context["inbound3_wip"] = inbound3_wip
            inbound2_wip = []
            outbound2_wip = []
            outbound3_wip = []

            for shipment in inbound3_wip:
                if shipment["sender_processor_type"] == "T1":
                    outbound2_wip.append(shipment)
                elif shipment["sender_processor_type"] == "T2":
                    outbound3_wip.append(shipment)
            if outbound3_wip:
                inbound2_wip = []
                outbound2_wip = []
                context["outbound3_wip"] = outbound3_wip
                sender_processor_id_list = [i["processor_idd"] for i in outbound3_wip]                
                for i in sender_processor_id_list:
                    #inbound 2
                    inbound2_wip_ = list(ShipmentManagement.objects.filter(processor2_idd=i, status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    inbound2_wip = inbound2_wip + inbound2_wip_
                    #outbound 2
                    outbound2_wip_ = list(ShipmentManagement.objects.filter(processor2_idd=i, status="APPROVED", crop=crop, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values())
                    outbound2_wip = outbound2_wip + outbound2_wip_
                context["inbound2_wip"] = inbound2_wip
                context["outbound2_wip"] = outbound2_wip
            else:
                context["outbound3_wip"] = []
                context["outbound2_wip"] = outbound2_wip                    
                context["inbound2_wip"] = []


            processor_id_list = [i["processor_idd"] for i in outbound2_wip]
            unique_processor_id_list = list(set(processor_id_list))
            t1_processor_ = []
            outbound1_wip_ = []
            field_ids = []
            for i in unique_processor_id_list:
                # inbound
                t1_processor = list(GrowerShipment.objects.filter(processor_id=i, status="APPROVED", crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
                if len(t1_processor) != 0:
                    for processor in t1_processor:
                        processor["processor_name"] = processor.get("processor__entity_name")
                        processor["shipment_id"] = processor.get("shipment_id")
                        processor["skuid"] = processor.get("sku")
                        processor["date"] = processor.get("approval_date")
                        processor["grower"] = processor.get("grower__name")
                        processor["farm"] = processor.get("field__farm__name")
                        processor["field"] = processor.get("field__name")
                        processor["pounds_received"] = processor.get("received_amount")
                        processor["pounds_shipped"] = processor.get("total_amount")
                        processor["unit"] = processor.get("unit_type")
                        processor["crop"] =  processor.get("crop")
                        processor["id"] =  processor.get("id")
                        try:
                            processor["pounds_delta"] = float(processor["pounds_shipped"]) - float(processor["pounds_received"])
                        except (TypeError, ValueError):
                            processor["pounds_delta"] = "Something is wrong"
                t1_processor_ = t1_processor_ + t1_processor

                #outbound
                outbound1_wip = list(GrowerShipment.objects.filter(processor_id=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values("shipment_id", "processor__entity_name", "date_time","total_amount"))
                if len(outbound1_wip) != 0:
                    for item in outbound1_wip:
                        item["shipment_id"] = item.get("shipment_id")
                        item["destination"] = item.get("processor__entity_name")
                        item["date"] = item.get("date_time")
                        item["quantity"] = item.get("total_amount")
                        item["transportation"] = "" 
                outbound1_wip_ = outbound1_wip_ + outbound1_wip

                field_ids_ = list(GrowerShipment.objects.filter(processor_id=i, crop=crop, date_time__gte=from_date, date_time__lte=to_date).values_list("field_id", flat=True))
                field_ids = field_ids + field_ids_
            context["outbound1_wip"] = outbound1_wip_
            context["t1_processor"] = t1_processor_

            get_Origin_Grower = Origin_searchby_Grower(crop,search_text,*field_ids)                                              
            context["origin_context"] = get_Origin_Grower  
         
        context['no_rec_found_msg'] = "No Records Found"           
    
    return context


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
    

def generate_static_map_url(origin, destination, waypoints=None):
    base_url = "https://www.google.com/maps/embed/v1/directions"
    api_key = "AIzaSyAQ_OGAb4yuL8g55IMufP3Dwd4yjrWxrdI"
    
    # Prepare parameters
    params = {
        "origin": origin,
        "destination": destination,
        "key": api_key
    }
    
    # Add waypoints if provided
    if waypoints:
        waypoints_str = "|".join([f"{point['lat']},{point['long']}" for point in waypoints])
        params["waypoints"] = waypoints_str

    # Encode parameters and construct the complete URL
    encoded_params = "&".join([f"{k}={v}" for k, v in params.items()])
    embed_map_url = f"{base_url}?{encoded_params}"
    
    return embed_map_url


def grower_location(context):
    origin_context = context.get("origin_context", [])

    t1_processor = context.get("t1_processor",[])
    inbound2_wip = context.get("inbound2_wip", [])
    inbound3_wip = context.get("inbound3_wip", [])
    inbound4_wip = context.get("inbound4_wip", [])
    inbound5_wip = context.get("inbound5_wip", [])
    inbound6_wip = context.get("inbound6_wip", [])
    
    field_location_list = []
    if origin_context:
        for i in context["origin_context"]:
            j = {"grower":"","field":"", "lat": 0.0, "lng": 0.0}
            field_id = i["field_id"]
            field = Field.objects.filter(id=field_id)
            if field:
                field_lat = field.first().latitude
                field_long = field.first().longitude
                j["grower"] = field.first().grower.name
                j["field"] = field.first().name
                try:
                    j["lat"] = float(field_lat)
                    j["lng"] = float(field_long)
                except:
                    j["lat"] = 0.0
                    j["lng"] = 0.0
            else:
                j["grower"] = None
                j["field"] = None
                j["lat"] = 0.0
                j["lng"] = 0.0
            field_location_list.append(j)    
    
    t1_location_list = []
    if t1_processor:
        for i in context["t1_processor"]:
            j = {"processor":"", "lat":0.0, "lng":0.0}
            processor = i["processor_name"]
            processor_location = Location.objects.filter(processor__entity_name=processor)
            if processor_location:
                j["processor"] = processor
                try:
                    j["lat"] = float(processor_location.first().latitude)
                    j["lng"] = float(processor_location.first().longitude)
                except:
                    j["lat"] = 0.0
                    j["lng"] = 0.0
                t1_location_list.append(j)
            else:
                j["processor"] = None                
                j["lat"] = 0.0
                j["lng"] = 0.0
            
    
    t2_location_list = []
    if inbound2_wip:
        for i in context["inbound2_wip"]:
            j = {"processor":"", "lat":0.0, "lng":0.0}
            processor_id = i["processor2_idd"]
            processor = i["processor2_name"]
            processor_location = Processor2Location.objects.filter(processor_id=processor_id)
            if processor_location:
                j["processor"] = processor
                try:
                    j["lat"] = float(processor_location.first().latitude)
                    j["lng"] = float(processor_location.first().longitude)
                except:
                    j["lat"] = 0.0
                    j["lng"] = 0.0
                t2_location_list.append(j)
            else:
                j["processor"] = None                
                j["lat"] = 0.0
                j["lng"] = 0.0
            
    
    t3_location_list = []
    if inbound3_wip:
        for i in context["inbound3_wip"]:
            j = {"processor":"", "lat":0.0, "lng":0.0}
            processor_id = i["processor2_idd"]
            processor = i["processor2_name"]
            processor_location = Processor2Location.objects.filter(processor_id=processor_id)
            if processor_location:
                j["processor"] = processor
                try:
                    j["lat"] = float(processor_location.first().latitude)
                    j["lng"] = float(processor_location.first().longitude)
                except:
                    j["lat"] = 0.0
                    j["lng"] = 0.0
                t3_location_list.append(j)
            else:
                j["processor"] = None                
                j["lat"] = 0.0
                j["lng"] = 0.0
            
   
    t4_location_list = []
    if inbound4_wip:
        for i in context["inbound4_wip"]:
            j = {"processor":"", "lat":0.0, "lng":0.0}
            processor_id = i["processor2_idd"]
            processor = i["processor2_name"]
            processor_location = Processor2Location.objects.filter(processor_id=processor_id)
            if processor_location:
                j["processor"] = processor
                try:
                    j["lat"] = float(processor_location.first().latitude)
                    j["lng"] = float(processor_location.first().longitude)
                except:
                    j["lat"] = 0.0
                    j["lng"] = 0.0
                t4_location_list.append(j)
            else:
                j["processor"] = None                
                j["lat"] = 0.0
                j["lng"] = 0.0
            

    warehouse_location_list = []
    if inbound5_wip:
        
        for i in context["inbound5_wip"]:            
            j = {"warehouse":"", "lat":0.0, "lng":0.0}
            warehouse_id = i["warehouse_id"]
            warehouse_name = i["warehouse_name"]            
            warehouse = Warehouse.objects.filter(id=int(warehouse_id)).first()
            if warehouse:                
                j["warehouse"] = warehouse_name
                try:
                    j["lat"] = float(warehouse.latitude)
                    j["lng"] = float(warehouse.longitude)
                except:
                    j["lat"] = 0.0
                    j["lng"] = 0.0
                warehouse_location_list.append(j)
            else:
                j["warehouse"] = None                
                j["lat"] = 0.0
                j["lng"] = 0.0
            
            

    customer_location_list = []
    if inbound6_wip:
        for i in context["inbound6_wip"]:
            j = {"customer":"", "lat":0.0, "lng":0.0}
            customer_id = i["customer_id"]
            customer_name = i["customer_name"]
            customer = Customer.objects.filter(id=int(customer_id)).first()
            if customer:                
                j["customer"] = customer_name
                try:
                    j["lat"] = float(customer.latitude)
                    j["lng"] = float(customer.longitude)
                except:
                    j["lat"] = 0.0
                    j["lng"] = 0.0
                customer_location_list.append(j)
            else:
                j["customer"] = None                
                j["lat"] = 0.0
                j["lng"] = 0.0
            

    context.update({
        "field_location_list":field_location_list,
        "t1_location_list":t1_location_list,
        "t2_location_list":t2_location_list,
        "t3_location_list":t3_location_list, 
        "t4_location_list":t4_location_list,
        "warehouse_location_list":warehouse_location_list,
        "customer_location_list":customer_location_list
        }) 
        
    return context


def location_response(context): 
    if context.get("outbound2_wip"): 
        for i in context["outbound2_wip"]:
            processor1 = i["processor_idd"]
            processor2 = i["processor2_idd"]
            check_processor1_location = Location.objects.filter(processor_id=processor1)
            origin_name = Processor.objects.filter(id=int(processor1)).first().entity_name

            if check_processor1_location:
                out2_processor1_lat = check_processor1_location.first().latitude
                out2_processor1_long = check_processor1_location.first().longitude 

                org_lat = float(out2_processor1_lat)
                org_lng = float(out2_processor1_long)                
            else:
                org_lat = 0
                org_lng = 0
            
            check_processor2_location = Processor2Location.objects.filter(processor_id=processor2)
            destination_name = Processor2.objects.filter(id=int(processor2)).first().entity_name

            if check_processor2_location:
                out2_processor2_lat = check_processor2_location.first().latitude
                out2_processor2_long = check_processor2_location.first().longitude                
                
                des_lat = float(out2_processor2_lat)
                des_lng = float(out2_processor2_long)               
            else:
                des_lat = 0
                des_lng = 0
            
            i["origin_lat"] = org_lat
            i["origin_lng"] = org_lng
            i["destination_lat"] = des_lat
            i["destination_lng"] = des_lng
            i["origin_name"] = origin_name
            i["destination_name"] = destination_name

            origin = f"{org_lat},{org_lng}"
            destination = f"{des_lat},{des_lng}"
            
            i["map_url"] = generate_static_map_url(origin, destination, waypoints=None)       
    else:
        pass

    if context.get("outbound3_wip"):       
        for j in context["outbound3_wip"]:
            processor1 = j["processor_idd"]
            processor2 = j["processor2_idd"]
            check_processor1_location = Processor2Location.objects.filter(processor_id=processor1, processor__processor_type__type_name="T2")
            origin_name = Processor2.objects.filter(id=int(processor1)).first().entity_name

            if check_processor1_location:
                out3_processor1_lat = check_processor1_location.first().latitude
                out3_processor1_long = check_processor1_location.first().longitude               
                
                org_lat = float(out3_processor1_lat)
                org_lng = float(out3_processor1_long)              
            else:
                org_lat = 0
                org_lng = 0
            check_processor2_location = Processor2Location.objects.filter(processor_id=processor2)
            destination_name = Processor2.objects.filter(id=int(processor2)).first().entity_name

            if check_processor2_location:
                out3_processor2_lat = check_processor2_location.first().latitude
                out3_processor2_long = check_processor2_location.first().longitude               
                
                des_lat = float(out3_processor2_lat)
                des_lng = float(out3_processor2_long)                
            else:
                des_lat = 0
                des_lng = 0

            j["origin_lat"] = org_lat
            j["origin_lng"] = org_lng
            j["destination_lat"] = des_lat
            j["destination_lng"] = des_lng
            j["origin_name"] = origin_name
            j["destination_name"] = destination_name
            origin = f"{org_lat},{org_lng}"
            destination = f"{des_lat},{des_lng}"
            
            j["map_url"] = generate_static_map_url(origin, destination, waypoints=None)
    else:
        pass

    if context.get("outbound4_wip"):    
        for k in context["outbound4_wip"]:
            processor1 = k["processor_idd"]
            processor2 = k["processor2_idd"]
            check_processor1_location = Processor2Location.objects.filter(processor_id=processor1, processor__processor_type__type_name="T3")
            origin_name = Processor2.objects.filter(id=int(processor1)).first().entity_name

            if check_processor1_location:
                out4_processor1_lat = check_processor1_location.first().latitude
                out4_processor1_long = check_processor1_location.first().longitude
                
                org_lat = float(out4_processor1_lat)
                org_lng = float(out4_processor1_long)                
            else:
                org_lat = 0
                org_lng = 0
            check_processor2_location = Processor2Location.objects.filter(processor_id=processor2)
            destination_name = Processor2.objects.filter(id=int(processor2)).first().entity_name

            if check_processor2_location:
                out4_processor2_lat = check_processor2_location.first().latitude
                out4_processor2_long = check_processor2_location.first().longitude                
                
                des_lat = float(out4_processor2_lat)
                des_lng = float(out4_processor2_long)                
            else:
                des_lat = 0
                des_lng = 0

            k["origin_lat"] = org_lat
            k["origin_lng"] = org_lng
            k["destination_lat"] = des_lat
            k["destination_lng"] = des_lng
            k["origin_name"] = origin_name
            k["destination_name"] = destination_name

            origin = f"{org_lat},{org_lng}"
            destination = f"{des_lat},{des_lng}"
            k["map_url"] = generate_static_map_url(origin, destination, waypoints=None)
    else:
        pass

    if context.get("outbound5_wip"):

        for k in context["outbound5_wip"]:
           
            processor_id = k["processor_id"]
            processor_type = k["processor_type"]
            warehouse_id = k["warehouse_id"]
            customer_id = k["customer_id"]
            if processor_type == "T1":
                origin_name = Processor.objects.filter(id=int(processor_id)).first().entity_name
                processor_location = Location.objects.filter(processor_id=int(processor_id)).first()
            else:
                origin_name = Processor2.objects.filter(id=int(processor_id)).first().entity_name
                processor_location = Processor2Location.objects.filter(processor_id=int(processor_id)).first()

            if processor_location:
                out5_processor_lat = processor_location.latitude
                out5_processor_long = processor_location.longitude
                
                org_lat = float(out5_processor_lat)
                org_lng = float(out5_processor_long)
            else:   
                org_lat = 0
                org_lng = 0

            if warehouse_id not in [None, "null", "", " "]:
                warehouse = Warehouse.objects.filter(id=int(warehouse_id)).first()
                destination_lat = warehouse.latitude
                destination_long = warehouse.longitude
                destination_name = warehouse.name
            else:
                customer = Customer.objects.filter(id=int(customer_id)).first()
                destination_lat = customer.latitude
                destination_long = customer.longitude
                destination_name = customer.name

            if destination_long and destination_lat:               
                
                des_lat = float(destination_lat)
                des_lng = float(destination_long)                
            else:
                des_lat = 0
                des_lng = 0

            k["origin_lat"] = org_lat
            k["origin_lng"] = org_lng
            k["destination_lat"] = des_lat
            k["destination_lng"] = des_lng
            k["origin_name"] = origin_name
            k["destination_name"] = destination_name

            origin = f"{org_lat},{org_lng}"
            destination = f"{des_lat},{des_lng}"

            additional_lat_long = []
            check_lot_entries = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=k["id"])
            if check_lot_entries:
                for entry in check_lot_entries:
                    additional_lat, additional_long = get_lat_lng(entry.address, settings.MAP_API_KEY)
                    crop = ProcessorShipmentCrops.objects.filter(id=int(entry.crop.id)).first().crop
                    previous_lot_number = ProcessorShipmentCrops.objects.filter(id=int(entry.crop.id)).first().lot_number
                    if additional_lat and additional_long:
                        info = f"Lot number changed for {crop} from {previous_lot_number} to {entry.additional_lot_number}"
                        additional_lat_long.append({"lat":additional_lat, "long":additional_long,"info":info, "address": entry.address})

            k["additional_lat_long"] = additional_lat_long

            k["map_url"] = generate_static_map_url(origin, destination, additional_lat_long)
    else:
        pass

    if context.get("outbound6_wip"):    
        for k in context["outbound6_wip"]:            
            warehouse_id = k["warehouse_id"]
            customer_id = k["customer_id"]    
            
            warehouse = Warehouse.objects.filter(id=int(warehouse_id)).first()
            origin_lat = warehouse.latitude
            origin_long = warehouse.longitude

            if origin_lat and origin_long:               
                
                org_lat = float(origin_lat)
                org_lng = float(origin_long)                
            else:
                org_lat = 0
                org_lng = 0
            
            customer = Customer.objects.filter(id=int(customer_id)).first()
            destination_lat = customer.latitude
            destination_long = customer.longitude

            if destination_long and destination_lat:                
                
                des_lat = float(destination_lat)
                des_lng = float(destination_long)               
            else:
                des_lat = 0
                des_lng = 0

            k["origin_lat"] = org_lat
            k["origin_lng"] = org_lng
            k["destination_lat"] = des_lat
            k["destination_lng"] = des_lng
            k["origin_name"] = warehouse.name
            k["destination_name"] = customer.name

            origin = f"{org_lat},{org_lng}"
            destination = f"{des_lat},{des_lng}"
            additional_lat_long = []

            check_lot_entries = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=k["id"]) 
            if check_lot_entries:
                for entry in check_lot_entries:
                    additional_lat, additional_long = get_lat_lng(entry.address, settings.MAP_API_KEY)
                    crop = WarehouseShipmentCrops.objects.filter(id=int(entry.crop.id)).first().crop
                    previous_lot_number = WarehouseShipmentCrops.objects.filter(id=int(entry.crop.id)).first().lot_number
                    if additional_lat and additional_long:
                        info = f"Lot number changed for {crop} from {previous_lot_number} to {entry.additional_lot_number}"
                        additional_lat_long.append({"lat":additional_lat, "long":additional_long, "info":info, "address": entry.address})

            k["additional_lat_long"] = additional_lat_long

            k["map_url"] = generate_static_map_url(origin, destination, additional_lat_long)
    else:
        pass
    
    return context

   
@login_required()
def traceability_report_list(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        crops = Crop.objects.all()
        context["crops"] = crops
        if request.method == 'POST':
            select_crop= request.POST.get('select_crop')
            get_search_by= request.POST.get('get_search_by')
            search_text= request.POST.get('search_text')
            filter_type = request.POST.get('filter_type')            

            from_date = None
            to_date = None
            crop_year = None
            if filter_type == "date_range":
                from_date = request.POST.get('from_date')
                to_date = request.POST.get('to_date')
            elif filter_type == "year":
                crop_year = request.POST.get('crop_year')
                if crop_year:  
                    try:
                        year = int(crop_year)
                        from_date = date(year, 1, 1)  
                        to_date = date(year, 12, 31) 
                    except ValueError:                        
                        pass
            else:
                first_shipment = GrowerShipment.objects.order_by('date_time').first()
                if first_shipment:
                    from_date = first_shipment.date_time.date() 
                else:
                    from_date = None  
                to_date = date.today()            

            if select_crop and search_text and get_search_by:
                context['select_crop'] = select_crop
                context['search_text'] = search_text
                context['get_search_by'] = get_search_by
                context['filter_type'] = filter_type
                if crop_year or (from_date and to_date):
                    context['crop_year'] = crop_year
                    context['from_date'] = from_date
                    context['to_date'] = to_date                
                
                if select_crop == 'COTTON' :
                    # Origin ........                   
                    # search by Grower ....
                    if get_search_by and get_search_by == 'grower' :
                        check_grower = Grower.objects.filter(name__icontains=search_text)
                        if check_grower.exists() :
                            check_grower_id = [i.id for i in check_grower][0]
                            check_grower_field_crop = Field.objects.filter(crop='COTTON',grower_id=check_grower_id)
                            if check_grower_field_crop.exists() :
                                grower_field_ids = [i.id for i in check_grower_field_crop]
                                get_Origin_Grower = Origin_searchby_Grower('COTTON',search_text,*grower_field_ids)         
                                context["origin_context"] = get_Origin_Grower
                                context["search_by"] = "grower"
                                outbound1_wip = outbound1_Wip_Grower('COTTON',search_text,from_date,to_date,*grower_field_ids)         
                                context["outbound1_wip"] = outbound1_wip
                                t1_processor = t1_Processor_grower('COTTON',check_grower_id,from_date,to_date)
                                context["t1_processor"] = t1_processor
                                # 20-03-23
                                outbound2_wip = outbound2_Wip_Grower('COTTON',check_grower_id,from_date,to_date,*grower_field_ids)         
                                context["outbound2_wip"] = outbound2_wip
                                t2_processor = t2_Processor_grower('COTTON',check_grower_id,from_date,to_date)
                                context["t2_processor"] = t2_processor
                            else:
                                context['no_rec_found_msg'] = "No Records Found"
                        else:
                            context['no_rec_found_msg'] = "No Records Found"
                    # search by Field ....
                    elif get_search_by and get_search_by == 'field' :
                        check_field = Field.objects.filter(name__icontains=search_text,crop='COTTON')
                        if check_field.exists() :
                            field_id = [i.id for i in check_field][0]
                            field_name = [i.name for i in check_field][0]
                            warehouse_wh_id = ''
                            get_origin_details = get_Origin_deliveryid('COTTON',field_id,field_name,'',warehouse_wh_id)
                            context["origin_context"] = get_origin_details
                            context["search_by"] = "field"
                            outbound1_wip = outbound1_Wip_field('COTTON',search_text,from_date,to_date,field_id)
                            context["outbound1_wip"] = outbound1_wip
                            t1_processor = t1_Processor_field('COTTON',field_name,field_id,field_id,from_date,to_date)
                            context["t1_processor"] = t1_processor
                            # 20-03-23
                            outbound2_wip = outbound2_Wip_Field('COTTON',field_name,field_id,from_date,to_date)         
                            context["outbound2_wip"] = outbound2_wip
                            t2_processor = t2_Processor_field('COTTON',field_name,field_id,from_date,to_date)
                            context["t2_processor"] = t2_processor
                        else:
                            context['no_rec_found_msg'] = "No Records Found"
                    # search by Processor ....
                    elif get_search_by and get_search_by == 'processor' :
                        check_processor = Processor.objects.filter(entity_name__icontains=search_text)
                        if check_processor.exists() :
                            processor_id = [i.id for i in check_processor][0]
                            get_classing = ClassingReport.objects.filter(processor_id=processor_id).values("id")
                            classing_id = [i["id"] for i in get_classing]
                            bale= BaleReportFarmField.objects.filter(classing_id__in=classing_id).values("id")
                            if bale.exists() :
                                bale_id = [i["id"] for i in bale]
                                get_Origin_Processor = Origin_searchby_Processor('COTTON',search_text,*bale_id)         
                                context["origin_context"] = get_Origin_Processor
                                context["search_by"] = "processor"
                                t1_processor = t1_Processor_Processor('COTTON',processor_id,from_date,to_date,*bale_id)
                                context["t1_processor"] = t1_processor
                                # 20-03-23
                                outbound2_wip = outbound_Wip_Processor('COTTON',search_text,processor_id,from_date,to_date)         
                                context["outbound2_wip"] = outbound2_wip
                                t2_processor =  t2_Processor_Processor('COTTON',processor_id,from_date,to_date,*bale_id) 
                                context["t2_processor"] = t2_processor
                            else:
                                context['no_rec_found_msg'] = "No Records Found"
                        else:
                            context['no_rec_found_msg'] = "No Records Found"
                    # search by Delivery ID ....
                    elif get_search_by and get_search_by == 'deliveryid' :
                        get_delivery_id1 = BaleReportFarmField.objects.filter(bale_id__icontains=search_text)
                        get_delivery_id2 = BaleReportFarmField.objects.filter(bale_id__icontains=f"0{search_text}")
                        if get_delivery_id1.exists() :
                            field_id = [i.ob4 for i in get_delivery_id1][0]
                            field_name = [i.field_name for i in get_delivery_id1][0]
                            warehouse_wh_id = [i.warehouse_wh_id for i in get_delivery_id1][0]
                            get_origin_details = get_Origin_deliveryid('COTTON',field_id,field_name,search_text,warehouse_wh_id)
                            context["origin_context"] = get_origin_details
                            context["search_by"] = "bale_id"
                            
                            t1_processor = t1_Processor_deliveryid('COTTON',search_text,warehouse_wh_id,from_date,to_date)
                            context["t1_processor"] = t1_processor
                            t2_processor =  t2_Processor_deliveryid('COTTON',search_text,warehouse_wh_id,from_date,to_date)
                            context["t2_processor"] = t2_processor
                        elif get_delivery_id2.exists() :
                            field_id = [i.ob4 for i in get_delivery_id2][0]
                            field_name = [i.field_name for i in get_delivery_id2][0]
                            warehouse_wh_id = [i.warehouse_wh_id for i in get_delivery_id2][0]
                            get_origin_details = get_Origin_deliveryid('COTTON',field_id,field_name,f"0{search_text}",warehouse_wh_id)
                            context["origin_context"] = get_origin_details
                            context["search_by"] = "bale_id"
                            
                            t1_processor = t1_Processor_deliveryid('COTTON',f"0{search_text}",warehouse_wh_id,from_date,to_date)
                            context["t1_processor"] = t1_processor  
                            t2_processor =  t2_Processor_deliveryid('COTTON',f"0{search_text}",warehouse_wh_id,from_date,to_date)
                            context["t2_processor"] = t2_processor
                        else:
                            context['no_rec_found_msg'] = "No Records Found"                   
                    else:
                        context['no_rec_found_msg'] = "No Records Found"
                    
                else:                  
                    # search by Grower ....
                    if get_search_by and get_search_by == 'grower' :
                        check_grower = Grower.objects.filter(name__icontains=search_text)
                        if check_grower.exists() :
                            check_grower_id = check_grower.first().id
                            check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                            if check_grower_field_crop.exists() :
                                grower_field_ids = [i.id for i in check_grower_field_crop]
                                get_Origin_Grower = Origin_searchby_Grower(select_crop,search_text,*grower_field_ids)                                              
                                context["origin_context"] = get_Origin_Grower
                                context["search_by"] = "grower"

                                processor_id = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.id
                                entity_name = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.entity_name
                                t1_processor = list(GrowerShipment.objects.filter(processor_id=processor_id, grower_id=check_grower_id,crop=select_crop, status="APPROVED").values("id","processor__entity_name","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount", "unit_type", "crop"))
                                
                                if len(t1_processor) != 0:
                                    for entry in t1_processor:
                                        entry["processor_name"] = entry["processor__entity_name"]
                                        entry["shipment_id"] = entry["shipment_id"]
                                        entry["skuid"] = entry["sku"]
                                        entry["date"] = entry["approval_date"]
                                        entry["grower"] = entry["grower__name"]
                                        entry["farm"] = entry["field__farm__name"]
                                        entry["field"] = entry["field__name"]
                                        entry["pounds_received"] = entry["received_amount"]
                                        entry["pounds_shipped"] = entry["total_amount"]
                                        entry["unit"] = entry["unit_type"]
                                        entry["crop"] =  entry.get("crop")
                                        entry["id"] =  entry.get("id")
                                        try:
                                            entry["pounds_delta"] = float(entry["total_amount"]) - float(entry["received_amount"])
                                        except (ValueError, TypeError):
                                            entry["pounds_delta"] = "Something is wrong"
                                
                                context["t1_processor"] = t1_processor                                
                                processor_type = "T1"
                                return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)
                                new_context = location_response(return_context)                                
                                del return_context["origin_context"]
                                del return_context["t1_processor"]
                                context.update(return_context)                                                                
                                context.update(new_context)  
                                
                            else:
                                context['no_rec_found_msg'] = "No Records Found"
                        else:
                            context['no_rec_found_msg'] = "No Records Found"
                    
                    # search by Field ....
                    elif get_search_by and get_search_by == 'field' :
                        check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                        if check_field.exists() :
                            field_name = search_text
                            field_id = check_field.first().id
                            warehouse_wh_id = ''
                            get_origin_details = get_Origin_deliveryid(select_crop,field_id,field_name,'',warehouse_wh_id)
                            context["origin_context"] = get_origin_details
                            context["search_by"] = "field"
                            grower_id =  check_field.first().grower.id
                            

                            outbound1_wip = outbound1_Wip_field(select_crop,search_text,from_date,to_date,field_id)
                            context["outbound1_wip"] = outbound1_wip
                            t1_processor = t1_Processor_field(select_crop,search_text,field_id,from_date,to_date)
                            context["t1_processor"] = t1_processor
                            # 20-03-23
                            processor_id = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.id
                            entity_name = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.entity_name
                            processor_type = "T1"
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)
                            new_context = location_response(return_context)
                            del return_context["origin_context"]
                            del return_context["outbound1_wip"]
                            del return_context["t1_processor"]
                            
                            context.update(return_context)                            
                            context.update(new_context)                            
                            
                        else:
                            context['no_rec_found_msg'] = "No Records Found"
                   
                    # search by Processor ....
                    elif get_search_by and get_search_by == 'processor' :
                        check_processor = get_processor_type(search_text)
                        if check_processor:
                            processor_type = check_processor["type"]
                            processor_id = check_processor["id"]
                            context2 = processor_traceability_report_response(select_crop, processor_id,processor_type, from_date, to_date, search_text)
                            new_context = location_response(context2)                           
                            context.update(context2)
                            context.update(new_context)
                            
                        else:
                            context['no_rec_found_msg'] = "No Records Found"
   
                    # search by SKU Id ....
                    elif get_search_by and get_search_by == 'sku_id':
                        context_ = skuid_traceability_response(select_crop, search_text, from_date, to_date)                        
                        context["get_search_by"] = "sku_id" 
                        origin_context = context_.get("origin_context",[]) 
                        if origin_context:                                              
                            new_context = location_response(context_)                          
                            context.update(context_)
                            context.update(new_context)                                                     
                        else:
                            context["no_rec_found_msg"] = "Not Found Origin"
                    
                    # search by Delivery Id ....
                    elif get_search_by and get_search_by == 'deliveryid' :
                        context["get_search_by"] = "deliveryid"
                        check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)
                        
                        if check_shipment.exists() :
                            get_shipment = check_shipment.first()
                            sku_id = get_shipment.sku
                            context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                            

                            if len(context_["origin_context"]) == 0:
                                context["no_rec_found_msg"] = "Not Found Origin"
                            else:
                                context.update(context_)
                                new_context = location_response(context_)                                
                                context.update(new_context)                               

                        elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                            get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                            
                            if get_shipment and not get_shipment.receiver_processor_type == "T4":
                                sku_id = get_shipment.storage_bin_send 
                                context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                                
                                if len(context_["origin_context"]) == 0:
                                    context["no_rec_found_msg"] = "Not Found Origin"
                                else:                                    
                                    context.update(context_)                                    
                                    new_context = location_response(context_)
                                    context.update(new_context)

                            elif get_shipment and get_shipment.receiver_processor_type == "T4":
                                sku_id = get_shipment.storage_bin_recive 
                                context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                               
                                if len(context_["origin_context"]) == 0:
                                    context["no_rec_found_msg"] = "Not Found Origin"
                                else:                                    
                                    context.update(context_)                                    
                                    new_context = location_response(context_)
                                    context.update(new_context)

                            else:
                                context['no_rec_found_msg'] = "No Records Found"

                        elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                            
                            shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                            for shipment in shipments:
                                if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                
                                carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id  
                            get_shipment = shipments.first()
                            if get_shipment["warehouse_id"] not in [None, "null", "", " "]:
                                inbound5 = list(shipments)
                                context["inbound5_wip"] = inbound5
                                context["outbound5_wip"] = inbound5
                                crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                                outbound6 = []
                                for crop in crops:
                                    
                                    if WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).exists():
                                        shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                                        for shipment in shipments:
                                            if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                                shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                            
                                            carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                            shipment["carrier_id"] = carrier.carrier_id  
                                        outbound6.extend(list(shipments))
                                context["outbound6_wip"] = outbound6
                                context["inbound6_wip"] = outbound6
                                processor_entity_name = get_shipment["processor_entity_name"]
                                processor_id = get_shipment["processor_id"]
                                processor_type = get_shipment["processor_type"]
                                for crop in crops:
                                    select_crop = crop.crop
                                    return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                                    
                                    del return_context["inbound5_wip"]
                                    del return_context["inbound6_wip"]
                                    del return_context["outbound5_wip"]
                                    del return_context["outbound6_wip"]
                                    
                                    keys_to_extend = [
                                        "origin_context",
                                        "t1_processor",
                                        "inbound2_wip",
                                        "inbound3_wip",
                                        "inbound4_wip",
                                        "outbound2_wip",
                                        "outbound3_wip",
                                        "outbound4_wip",
                                    ]

                                    for key in keys_to_extend:
                                        if return_context.get(key):
                                            context[key] = context.get(key, [])
                                            context[key].extend(return_context[key])                                      
                                
                                    new_context_ = location_response(context)                           
                                    context.update(new_context_)
                                
                            else:
                                inbound6 = shipments
                                context["inbound6_wip"] = inbound6
                                context["outbound5_wip"] = inbound6
                                context["inbound5_wip"] = []
                                context["outbound6_wip"] = []

                                crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])

                                processor_entity_name = get_shipment["processor_entity_name"]
                                processor_id = get_shipment["processor_id"]
                                processor_type = get_shipment["processor_type"]
                                for crop in crops:
                                    select_crop = crop.crop
                                    return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                                    del return_context["inbound5_wip"]
                                    del return_context["inbound6_wip"]
                                    del return_context["outbound5_wip"]
                                    del return_context["outbound6_wip"]
                                    keys_to_extend = [
                                        "origin_context",
                                        "t1_processor",
                                        "inbound2_wip",
                                        "inbound3_wip",
                                        "inbound4_wip",
                                        "outbound2_wip",
                                        "outbound3_wip",
                                        "outbound4_wip",
                                    ]

                                    for key in keys_to_extend:
                                        if return_context.get(key):
                                            context[key] = context.get(key, [])
                                            context[key].extend(return_context[key])                                      
                                
                                    new_context_ = location_response(context)                           
                                    context.update(new_context_)
                        
                        elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                            shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id","customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                            for shipment in shipments:
                                if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                
                                carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id  

                            get_shipment = shipments.first()
                            context["inbound6_wip"] = list(shipments)
                            context["outbound6_wip"] = list(shipments)
                            crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                            outbound5_processor = []
                            for crop in crops:
                                select_crop = crop.crop
                                check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                                if check_processor_shipment:
                                        for shipment in check_processor_shipment:
                                            if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                                shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                           
                                            carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                            shipment["carrier_id"] = carrier.carrier_id                                 

                                        outbound5_processor.extend(check_processor_shipment) 
                                        processor_entity_name = shipment["processor_entity_name"]
                                        processor_id = shipment["processor_id"]
                                        processor_type = shipment["processor_type"]                             
                                        return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                                        del return_context["inbound5_wip"]
                                        del return_context["inbound6_wip"]
                                        del return_context["outbound5_wip"]
                                        del return_context["outbound6_wip"]
                                        keys_to_extend = [
                                            "origin_context",
                                            "t1_processor",
                                            "inbound2_wip",
                                            "inbound3_wip",
                                            "inbound4_wip",
                                            "outbound2_wip",
                                            "outbound3_wip",
                                            "outbound4_wip",
                                        ]

                                        for key in keys_to_extend:
                                            if return_context.get(key):
                                                context[key] = context.get(key, [])
                                                context[key].extend(return_context[key])                                      
                                    
                                        new_context_ = location_response(context)                           
                                        context.update(new_context_)

                            context["outbound5_wip"] = outbound5_processor
                            context["inbound5_wip"] = outbound5_processor                        
                        else:
                            context['no_rec_found_msg'] = "No Records Found"    
                    
                    # search by Warehouse....
                    elif get_search_by and get_search_by == 'warehouse':
                        context["get_search_by"] = "warehouse"
                        check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                        if check_warehouse.exists():                            
                            warehouse = check_warehouse.first()                            
                            inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                            for shipment in inbound5:
                                if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                
                                carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id  
                            context["inbound5_wip"] = inbound5

                            outbound6 = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                            for shipment in outbound6:
                                if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                
                                carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id  
                            context["outbound6_wip"] = outbound6
                            
                            context["inbound6_wip"] = outbound6
                            context["outbound5_wip"] = inbound5
                            for shipment in inbound5:
                                processor_id = shipment["processor_id"]
                                processor_type = shipment["processor_type"]
                                processor_entity_name = shipment["processor_entity_name"]
                                return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                                del return_context["inbound5_wip"]
                                del return_context["inbound6_wip"]
                                del return_context["outbound5_wip"]
                                del return_context["outbound6_wip"]
                                keys_to_extend = [
                                    "origin_context",
                                    "t1_processor",
                                    "inbound2_wip",
                                    "inbound3_wip",
                                    "inbound4_wip",
                                    "outbound2_wip",
                                    "outbound3_wip",
                                    "outbound4_wip",
                                ]

                                for key in keys_to_extend:
                                    if return_context.get(key):
                                        context[key] = context.get(key, [])
                                        context[key].extend(return_context[key])                                      
                            
                                new_context_ = location_response(context)                           
                                context.update(new_context_)
                        else:
                            context['no_rec_found_msg'] = "No Records Found"
                    
                    # search by Customer....
                    elif get_search_by and get_search_by == 'customer':
                        context["get_search_by"] = "customer"
                        check_customer = Customer.objects.filter(name__icontains=search_text)
                        if check_customer.exists():
                            customer = check_customer.first()
                            inbound6 = []
                            
                            processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                                processor_shipment_crop__crop=select_crop,
                                customer_id=customer.id, 
                                date_pulled__date__gte=from_date, 
                                date_pulled__date__lte=to_date
                            ).values(
                                "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                                "processor_type", "processor_id", "shipment_id", "warehouse_id",
                                "warehouse_name", "customer_name", "customer_id", 
                                "date_pulled", "carrier_type", "distributor_receive_date", "status"
                            ))
                            for shipment in processor_shipments:
                                if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                               
                                carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id  
                                inbound6.append(shipment)

                            warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                                warehouse_shipment_crop__crop=select_crop, 
                                customer_id=customer.id, 
                                date_pulled__date__gte=from_date, 
                                date_pulled__date__lte=to_date
                            ).values(
                                "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                                "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                            ))
                            for shipment in warehouse_shipments:
                                if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                               
                                carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id  
                                inbound6.append(shipment)

                            context["inbound6_wip"] = inbound6
                            context["outbound6_wip"] = warehouse_shipments

                            warehouse_ids = [shipment["warehouse_id"] for shipment in warehouse_shipments]
                            
                            inbound5 = list(ProcessorWarehouseShipment.objects.filter(
                                processor_shipment_crop__crop=select_crop,
                                warehouse_id__in=warehouse_ids,
                                date_pulled__date__gte=from_date,
                                date_pulled__date__lte=to_date
                            ).values(
                                "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                                "processor_type", "processor_id", "shipment_id", "warehouse_id",
                                "warehouse_name", "customer_name", "customer_id", 
                                "date_pulled", "carrier_type", "distributor_receive_date", "status"
                            ))
                            for shipment in inbound5:
                                if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                
                                carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id  
                            context["inbound5_wip"] = inbound5
                            outbound5 = inbound5 + processor_shipments
                            context["outbound5_wip"] = outbound5

                            for shipment in outbound5:
                                processor_id = shipment.get("processor_id")
                                processor_type = shipment.get("processor_type")
                                processor_entity_name = shipment.get("processor_entity_name")
                                
                                return_context = processor_traceability_report_response(
                                    select_crop, processor_id, processor_type, 
                                    from_date, to_date, processor_entity_name
                                )
                                del return_context["inbound5_wip"]
                                del return_context["inbound6_wip"]
                                del return_context["outbound5_wip"]
                                del return_context["outbound6_wip"]
                                keys_to_extend = [
                                    "origin_context",
                                    "t1_processor",
                                    "inbound2_wip",
                                    "inbound3_wip",
                                    "inbound4_wip",
                                    "outbound2_wip",
                                    "outbound3_wip",
                                    "outbound4_wip",
                                ]

                                for key in keys_to_extend:
                                    if return_context.get(key):
                                        context[key] = context.get(key, [])
                                        context[key].extend(return_context[key])                                      
                            
                                new_context_ = location_response(context)                           
                                context.update(new_context_)                            
                                
                        else:
                            context['no_rec_found_msg'] = "No Records Found" 
                    
                    else:
                        context['no_rec_found_msg'] = "No Records Found"
                
                map_show = request.POST.get("map_view")
                table_show = request.POST.get("table_view")
                context = grower_location(context)
                if map_show:
                    return render (request, 'tracemodule/traceability_map_show.html', context)
                if table_show:
                    return render (request, 'tracemodule/test_trace_module.html', context) 

        return render (request, 'tracemodule/test_trace_module.html', context)
    else:
        return redirect ('dashboard')


@login_required()
def autocomplete_suggestions(request, select_search):
    lst =[]
    if select_search == 'grower' :
        grower_name = Grower.objects.all().order_by('name').values('name')
        lst = [i['name'] for i in grower_name]
    elif select_search == 'field' : 
        field_name = Field.objects.all().order_by('name').values('name')
        lst = [i['name'] for i in field_name]
    elif select_search == 'processor' :    
        processor_name = list(Processor.objects.all().order_by('entity_name').values_list('entity_name', flat=True))
        processor2_name = list(Processor2.objects.all().order_by('entity_name').values_list('entity_name', flat=True))
        lst = processor_name + processor2_name    
    
    elif select_search == 'warehouse':
        lst = list(Warehouse.objects.all().order_by('name').values_list('name', flat=True))
        
    elif select_search == 'customer':
        lst = list(Customer.objects.all().order_by('name').values_list('name', flat=True))
    responce = {'select_search':lst}   
    return JsonResponse(responce)


@login_required()
def showsustainability_metrics(request,get_search_by,field_id):
    get_field = Field.objects.get(id=field_id)
    if get_search_by == 'bale_id' :
        pass
    elif get_search_by == 'shipment_id' :
        pass
    elif get_search_by == 'field' :
        pass
    elif get_search_by == 'grower' :
        pass
    harvest_date = get_field.harvest_date if get_field.harvest_date else ''
    water_savings = get_field.gal_water_saved if get_field.gal_water_saved else ''
    water_per_pound_savings = get_field.water_lbs_saved if get_field.water_lbs_saved else ''
    land_use = get_field.land_use_efficiency if get_field.land_use_efficiency else ''
    less_GHG = get_field.ghg_reduction if get_field.ghg_reduction else ''
    co2_eQ_footprint = get_field.co2_eq_reduced if get_field.co2_eq_reduced else ''
    premiums_to_growers = get_field.grower_premium_percentage if get_field.grower_premium_percentage else ''

    
    crop = get_field.crop
    surveyscore1 = get_field.get_survey1()
    surveyscore2 = get_field.get_survey2()
    surveyscore3 = get_field.get_survey3()
    if surveyscore1 != '' and surveyscore1 != None :
        surveyscore1 = float(surveyscore1)
    else:
        surveyscore1 = 0
    if surveyscore2 != '' and surveyscore2 != None :
        surveyscore2 = float(surveyscore2)
    else:
        surveyscore2 = 0
    if surveyscore3 != '' and surveyscore3 != None :
        surveyscore3 = float(surveyscore3)
    else:
        surveyscore3 = 0
    composite_score = round((surveyscore1*0.25)+(surveyscore2*0.50)+(surveyscore3*0.25),2)
    
    if crop == "COTTON":
        if composite_score >= 75:
            pf_sus = "Pass"
        elif composite_score < 75:
            pf_sus = "Fail"
    
    else:
        if composite_score >= 70:
            pf_sus = "Pass"
        elif composite_score < 70:
            pf_sus = "Fail"
 
    
    responce = {"pf_sus":pf_sus,"harvest_date":harvest_date,"water_savings":water_savings,"water_per_pound_savings":water_per_pound_savings,
                "land_use":land_use,"less_GHG":less_GHG,"co2_eQ_footprint":co2_eQ_footprint,"premiums_to_growers":premiums_to_growers}
    return JsonResponse(responce)


@login_required()
def showquality_metrics(request,get_search_by,delivery_idd):
    responce = {}
    level, grade, leaf, staple, length, strength, mic = '', '', '', '', '', '', ''
    bale1 = BaleReportFarmField.objects.filter(bale_id=delivery_idd)
    bale2 = BaleReportFarmField.objects.filter(bale_id=f'0{delivery_idd}')
    shipment = GrowerShipment.objects.filter(shipment_id=delivery_idd)
    if len(bale1) == 1 :
        bale1_id = [i.id for i in bale1][0]
        bale1 = BaleReportFarmField.objects.get(id=bale1_id)
        grade = bale1.gr
        leaf = bale1.lf
        staple = bale1.st
        length = bale1.len_num
        strength = bale1.str_no
        mic = bale1.mic
        level = bale1.level
    elif len(bale2) == 1 :
        bale2_id = [i.id for i in bale2][0]
        bale2 = BaleReportFarmField.objects.get(id=bale2_id)
        grade = bale2.gr
        leaf = bale2.lf
        staple = bale2.st
        length = bale2.len_num
        strength = bale2.str_no
        mic = bale2.mic
        level = bale2.level
    elif len(shipment) == 1 :
        pass
    
    
    responce = {"level":level,"grade":grade,"leaf":leaf,"staple":staple,"length":length,"strength":strength,"mic":mic}
    
    return JsonResponse(responce)


@login_required()
def traceability_report_Origin_csv_download(request,select_crop,get_search_by,search_text,from_date,to_date):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'Origin.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        if select_crop == 'COTTON' :
            writer.writerow(['CROP', 'VARIETY', 'FIELD', 'GROWER', 'FARM', 'HARVEST DATE', 
                            'PROJECTED YIELD', 'ACTUAL YIELD', 'YIELD  DELTA', 'Pass / Fail Sustainability','Water Savings %',
                            'Land Use Efficiency %', 'Less GHG % ', 'Premiums to Growers %', 'CO2 EQ Footprint #','Pounds of Water Per Pound Savings %'])
            
            
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = [i.id for i in check_grower][0]
                    check_grower_field_crop = Field.objects.filter(crop='COTTON',grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        grower_field_ids = [i.id for i in check_grower_field_crop]
                        output = Origin_searchby_Grower('COTTON',search_text,*grower_field_ids)         
                                        
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop='COTTON')
                if check_field.exists() :
                    field_id = [i.id for i in check_field][0]
                    field_name = [i.name for i in check_field][0]
                    warehouse_wh_id = ''
                    output = get_Origin_deliveryid('COTTON',field_id,field_name,'',warehouse_wh_id)
                                        
            elif get_search_by and get_search_by == 'processor' :
                check_processor = Processor.objects.filter(entity_name__icontains=search_text)
                if check_processor.exists() :
                    processor_id = [i.id for i in check_processor][0]
                    get_classing = ClassingReport.objects.filter(processor_id=processor_id).values("id")
                    classing_id = [i["id"] for i in get_classing]
                    bale= BaleReportFarmField.objects.filter(classing_id__in=classing_id).values("id")
                    if bale.exists() :
                        bale_id = [i["id"] for i in bale]
                        output = Origin_searchby_Processor('COTTON',search_text,*bale_id)         
                               
            elif get_search_by and get_search_by == 'deliveryid' :
                get_delivery_id1 = BaleReportFarmField.objects.filter(bale_id__icontains=search_text)
                get_delivery_id2 = BaleReportFarmField.objects.filter(bale_id__icontains=f"0{search_text}")
                if get_delivery_id1.exists() :
                    field_id = [i.ob4 for i in get_delivery_id1][0]
                    field_name = [i.field_name for i in get_delivery_id1][0]
                    warehouse_wh_id = [i.warehouse_wh_id for i in get_delivery_id1][0]
                    output = get_Origin_deliveryid('COTTON',field_id,field_name,search_text,warehouse_wh_id)
                    
                elif get_delivery_id2.exists() :
                    field_id = [i.ob4 for i in get_delivery_id2][0]
                    field_name = [i.field_name for i in get_delivery_id2][0]
                    warehouse_wh_id = [i.warehouse_wh_id for i in get_delivery_id2][0]
                    output = get_Origin_deliveryid('COTTON',field_id,field_name,f"0{search_text}",warehouse_wh_id)
            else:
                output = []
            for i in output:
                writer.writerow([i["get_select_crop"], i["variety"], i["field_name"], i["grower_name"], i["farm_name"], i["harvest_date"], 
                i["projected_yeild"], i["reported_yeild"], i["yield_delta"],i["pf_sus"],i["water_savings"],i["land_use"],i["premiums_to_growers"],
                i["co2_eQ_footprint"],i["water_per_pound_savings"]])
        # crop rice
        else:
            writer.writerow(['CROP', 'VARIETY', 'FIELD', 'GROWER', 'FARM', 'HARVEST DATE', 
                            'PROJECTED YIELD', 'ACTUAL YIELD', 'YIELD  DELTA', 'Pass / Fail Sustainability','Water Savings %',
                            'Land Use Efficiency %', 'Less GHG % ', 'Premiums to Growers %', 'CO2 EQ Footprint #','Pounds of Water Per Pound Savings %'])
            
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = check_grower.first().id
                    check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        grower_field_ids = [i.id for i in check_grower_field_crop]
                        output = Origin_searchby_Grower(select_crop,search_text,*grower_field_ids) 
                    else:
                        output = []
                else:
                    output = []

            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                if check_field.exists() :
                    field_name = search_text
                    field_id = check_field.first().id
                    warehouse_wh_id = ''
                    output = get_Origin_deliveryid(select_crop,field_id,field_name,'',warehouse_wh_id)
                else:
                    output = []    
                    
            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    context_ = processor_traceability_report_response(select_crop, processor_id,processor_type, from_date, to_date, search_text)
                    output = context_.get("origin_context")
                else:
                    output = []

            elif get_search_by and get_search_by == 'sku_id' :
                context_ = skuid_traceability_response(select_crop, search_text, from_date, to_date)
                output = context_.get("origin_context")
                              
            elif get_search_by and get_search_by == 'deliveryid' :                
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)
                        
                if check_shipment.exists() :
                    get_shipment = check_shipment.first()
                    sku_id = get_shipment.sku
                    context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                    output = context_.get("origin_context")      

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                    get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                    
                    if get_shipment and not get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_send 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("origin_context")                        

                    elif get_shipment and get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_recive 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)                        
                        output = context_.get("origin_context")

                    else:
                        output = []

                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id","warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    get_shipment = shipments.first()

                    if get_shipment["warehouse_id"] not in [None, "null", "", " "]:                                               
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        outbound6 = []
                        for crop in crops:                            
                            if WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).exists():
                                shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                                for shipment in shipments:
                                    if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id  
                                outbound6.extend(list(shipments))                        
                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        
                            if return_context.get("origin_context"):                                
                                output.extend(return_context["origin_context"])                                   
                        
                    else:  
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                            
                            if return_context.get("origin_context"):                                
                                output.extend(return_context["origin_context"])                                      
                               
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id","customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                    for shipment in shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    get_shipment = shipments.first()                    
                    crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                    outbound5_processor = []
                    for crop in crops:
                        select_crop = crop.crop
                        check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                        if check_processor_shipment:
                            for shipment in check_processor_shipment:
                                if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                
                                carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id                                 

                            outbound5_processor.extend(check_processor_shipment) 
                            processor_entity_name = shipment["processor_entity_name"]
                            processor_id = shipment["processor_id"]
                            processor_type = shipment["processor_type"]                             
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)

                            if return_context.get("origin_context"):                                
                                output.extend(return_context["origin_context"])                      
                else:
                    output = []
            
            elif get_search_by and get_search_by == 'warehouse': 
                output = []                       
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                    
                    warehouse = check_warehouse.first()                   
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id                     

                    outbound6 = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    for shipment in outbound6:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    
                    for shipment in inbound5:
                        processor_id = shipment["processor_id"]
                        processor_type = shipment["processor_type"]
                        processor_entity_name = shipment["processor_entity_name"]
                        return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        if return_context.get("origin_context"):                                
                            output.extend(return_context["origin_context"]) 
                else:
                    output = []
                     
            elif get_search_by and get_search_by == 'customer':
                
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()
                    inbound6 = []
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in processor_shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(processor_shipments)

                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop, 
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    for shipment in warehouse_shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(warehouse_shipments)

                    warehouse_ids = [shipment["warehouse_id"] for shipment in warehouse_shipments]
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        warehouse_id__in=warehouse_ids,
                        date_pulled__date__gte=from_date,
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    outbound5 = inbound5 + processor_shipments
                    for shipment in outbound5:
                        processor_id = shipment.get("processor_id")
                        processor_type = shipment.get("processor_type")
                        processor_entity_name = shipment.get("processor_entity_name")
                        
                        return_context = processor_traceability_report_response(
                            select_crop, processor_id, processor_type, 
                            from_date, to_date, processor_entity_name
                        )                        
                        if return_context.get("origin_context"):                                
                            output.extend(return_context["origin_context"]) 
                else:
                    output = [] 
                    
            else:
                output = []
            for i in output:
                writer.writerow([i["get_select_crop"], i["variety"], i["field_name"], i["grower_name"], i["farm_name"], i["harvest_date"], 
                i["projected_yeild"], i["reported_yeild"], i["yield_delta"],i["pf_sus"],i["water_savings"],i["land_use"],i["premiums_to_growers"],
                i["co2_eQ_footprint"],i["water_per_pound_savings"]])
        
        return response
    else:
        return redirect ('dashboard')


@login_required()
def traceability_report_WIP1_csv_download(request,select_crop,get_search_by,search_text,from_date,to_date):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'Outbound 1 WIP.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        if select_crop == 'COTTON' :
            pass
        else:
            writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS',  'DESTINATION'])
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = check_grower.first().id
                    check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        processor_id = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.id
                        entity_name = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.entity_name
                                                       
                        processor_type = "T1"
                        context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)      
                        output = context_.get("outbound1_wip")
                    else:
                        output = []
                else:
                    output = []

            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                if check_field.exists() :
                    field_name = search_text
                    field_id = check_field.first().id                 
                    output = outbound1_Wip_field(select_crop,search_text,from_date,to_date,field_id)
                else:
                    output = []
            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    context_ = processor_traceability_report_response(select_crop,processor_id,processor_type, from_date, to_date, search_text)
                    output = context_.get("outbound1_wip")
                else:
                    output = []
                    
            elif get_search_by and get_search_by == 'sku_id' :
                context_ = skuid_traceability_response(select_crop, search_text, from_date, to_date)  
                output = context_.get("outbound1_wip")

            elif get_search_by and get_search_by == 'deliveryid' :                
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)
                        
                if check_shipment.exists() :
                    get_shipment = check_shipment.first()
                    sku_id = get_shipment.sku
                    context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                    output = context_.get("outbound1_wip")      

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                    get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                    
                    if get_shipment and not get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_send 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("outbound1_wip")                        

                    elif get_shipment and get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_recive 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)                        
                        output = context_.get("outbound1_wip")

                    else:
                        output = []

                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    get_shipment = shipments.first()

                    if get_shipment["warehouse_id"] not in [None, "null", "", " "]:                                               
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        outbound6 = []
                        for crop in crops:                            
                            if WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).exists():
                                shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                                for shipment in shipments:
                                    if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id  
                                outbound6.extend(list(shipments))

                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        
                            if return_context.get("outbound1_wip"):                                
                                output.extend(return_context["outbound1_wip"])                                   
                        
                    else:  
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                            
                            if return_context.get("outbound1_wip"):                                
                                output.extend(return_context["outbound1_wip"])                                      
                               
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id" ,"customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                    for shipment in shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    get_shipment = shipments.first()                    
                    crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                    outbound5_processor = []
                    for crop in crops:
                        select_crop = crop.crop
                        check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                        if check_processor_shipment:
                            for shipment in check_processor_shipment:
                                if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                
                                carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id                                 

                            outbound5_processor.extend(check_processor_shipment) 
                            processor_entity_name = shipment["processor_entity_name"]
                            processor_id = shipment["processor_id"]
                            processor_type = shipment["processor_type"]                             
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)

                            if return_context.get("outbound1_wip"):                                
                                output.extend(return_context["outbound1_wip"])                      
                else:
                    output = []
            
            elif get_search_by and get_search_by == 'warehouse': 
                output = []                       
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                    
                    warehouse = check_warehouse.first()                   
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id                     

                    outbound6 = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id","shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    for shipment in outbound6:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    
                    for shipment in inbound5:
                        processor_id = shipment["processor_id"]
                        processor_type = shipment["processor_type"]
                        processor_entity_name = shipment["processor_entity_name"]
                        return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        if return_context.get("outbound1_wip"):                                
                            output.extend(return_context["outbound1_wip"]) 
                else:
                    output = []
                     
            elif get_search_by and get_search_by == 'customer':
                
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()
                    inbound6 = []
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in processor_shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(processor_shipments)

                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop, 
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    for shipment in warehouse_shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(warehouse_shipments)

                    warehouse_ids = [shipment["warehouse_id"] for shipment in warehouse_shipments]
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        warehouse_id__in=warehouse_ids,
                        date_pulled__date__gte=from_date,
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    outbound5 = inbound5 + processor_shipments
                    for shipment in outbound5:
                        processor_id = shipment.get("processor_id")
                        processor_type = shipment.get("processor_type")
                        processor_entity_name = shipment.get("processor_entity_name")
                        
                        return_context = processor_traceability_report_response(
                            select_crop, processor_id, processor_type, 
                            from_date, to_date, processor_entity_name
                        )                        
                        if return_context.get("outbound1_wip"):                                
                            output.extend(return_context["outbound1_wip"]) 
                else:
                    output = [] 
             
            else:
                output = []
            for i in output:
                writer.writerow([i["shipment_id"], i["date"], i["quantity"], i["destination"]])
        return response
    else:
        return redirect ('dashboard')


@login_required()
def traceability_report_T1_Processor_csv_download(request,select_crop,get_search_by,search_text,from_date,to_date):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'T1 Processor.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        if select_crop == 'COTTON' :
            writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                             'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = [i.id for i in check_grower][0]
                    check_grower_field_crop = Field.objects.filter(crop='COTTON',grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        
                        output = t1_Processor_grower('COTTON',check_grower_id,from_date,to_date)        
                                        
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop='COTTON')
                if check_field.exists() :
                    field_id = [i.id for i in check_field][0]
                    field_name = [i.name for i in check_field][0]
                    warehouse_wh_id = ''
                    output = t1_Processor_field('COTTON',field_name,field_id,from_date,to_date)
   

            elif get_search_by and get_search_by == 'processor' :
                check_processor = Processor.objects.filter(entity_name__icontains=search_text)
                if check_processor.exists() :
                    processor_id = [i.id for i in check_processor][0]
                    get_classing = ClassingReport.objects.filter(processor_id=processor_id).values("id")
                    classing_id = [i["id"] for i in get_classing]
                    bale= BaleReportFarmField.objects.filter(classing_id__in=classing_id).values("id")
                    if bale.exists() :
                        bale_id = [i["id"] for i in bale]
                        output = t1_Processor_Processor('COTTON',processor_id,from_date,to_date,*bale_id)   
               
            elif get_search_by and get_search_by == 'deliveryid' :
                get_delivery_id1 = BaleReportFarmField.objects.filter(bale_id__icontains=search_text)
                get_delivery_id2 = BaleReportFarmField.objects.filter(bale_id__icontains=f"0{search_text}")
                if get_delivery_id1.exists() :
                    field_id = [i.ob4 for i in get_delivery_id1][0]
                    field_name = [i.field_name for i in get_delivery_id1][0]
                    warehouse_wh_id = [i.warehouse_wh_id for i in get_delivery_id1][0]
                    output = t1_Processor_deliveryid('COTTON',search_text,warehouse_wh_id,from_date,to_date)

                elif get_delivery_id2.exists() :
                    field_id = [i.ob4 for i in get_delivery_id2][0]
                    field_name = [i.field_name for i in get_delivery_id2][0]
                    warehouse_wh_id = [i.warehouse_wh_id for i in get_delivery_id2][0]                    
                    output = t1_Processor_deliveryid('COTTON',f"0{search_text}",warehouse_wh_id,from_date,to_date)

            else:
                output = []
            for i in output:
                writer.writerow([i["processor_name"] , i["processor_id"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                                 i["pounds_received"], i["pounds_delta"]])
            
        else :
            writer.writerow(['PROCESSOR NAME', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                             'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = check_grower.first().id
                    check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        grower_field_ids = [i.id for i in check_grower_field_crop]                       

                        processor_id = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.id
                        entity_name = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.entity_name
                        t1_processor = list(GrowerShipment.objects.filter(processor_id=processor_id, grower_id=check_grower_id, status="APPROVED", crop=select_crop).values("processor__entity_name","shipment_id","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount"))

                        if len(t1_processor) != 0:
                            for entry in t1_processor:
                                entry["processor_name"] = entry["processor__entity_name"]
                                entry["shipment_id"] = entry["shipment_id"]
                                entry["date"] = entry["approval_date"]
                                entry["grower"] = entry["grower__name"]
                                entry["farm"] = entry["field__farm__name"]
                                entry["field"] = entry["field__name"]
                                entry["pounds_received"] = entry["received_amount"]
                                entry["pounds_shipped"] = entry["total_amount"]
                                try:
                                    entry["pounds_delta"] = float(entry["total_amount"]) - float(entry["received_amount"])
                                except (ValueError, TypeError):
                                    entry["pounds_delta"] = "Something is wrong"                        
                        output = t1_processor 
                    else:
                        output = []
                else:
                    output = []
            
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                if check_field.exists() :
                    field_name = search_text
                    field_id = check_field.first().id                    
                    output = t1_Processor_field(select_crop,search_text,field_id,from_date,to_date)
                else:
                    output = []   

            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    context_ = processor_traceability_report_response(select_crop, processor_id,processor_type, from_date, to_date, search_text)
                    output = context_.get("t1_processor")
                else:
                    output = []
            
            elif get_search_by and get_search_by == 'sku_id' :
                context_ = skuid_traceability_response(select_crop, search_text, from_date, to_date)  
                output = context_.get("t1_processor")  

            elif get_search_by and get_search_by == 'deliveryid' :                
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)
                        
                if check_shipment.exists() :
                    get_shipment = check_shipment.first()
                    sku_id = get_shipment.sku
                    context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                    output = context_.get("t1_processor")      

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                    get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                    
                    if get_shipment and not get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_send 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("t1_processor")                        

                    elif get_shipment and get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_recive 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)                        
                        output = context_.get("t1_processor")

                    else:
                        output = []

                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    get_shipment = shipments.first()

                    if get_shipment["warehouse_id"] not in [None, "null", "", " "]:                                               
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        outbound6 = []
                        for crop in crops:                            
                            if WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).exists():
                                shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id","customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                                for shipment in shipments:
                                    if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id  
                                outbound6.extend(list(shipments))

                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        
                            if return_context.get("t1_processor"):                                
                                output.extend(return_context["t1_processor"])                                   
                        
                    else:  
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                            
                            if return_context.get("t1_processor"):                                
                                output.extend(return_context["t1_processor"])                                      
                               
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id" ,"customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                    for shipment in shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    get_shipment = shipments.first()                    
                    crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                    outbound5_processor = []
                    for crop in crops:
                        select_crop = crop.crop
                        check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                        if check_processor_shipment:
                            for shipment in check_processor_shipment:
                                if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                
                                carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id                                 

                            outbound5_processor.extend(check_processor_shipment) 
                            processor_entity_name = shipment["processor_entity_name"]
                            processor_id = shipment["processor_id"]
                            processor_type = shipment["processor_type"]                             
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)

                            if return_context.get("t1_processor"):                                
                                output.extend(return_context["t1_processor"])                      
                else:
                    output = []
            
            elif get_search_by and get_search_by == 'warehouse': 
                output = []                       
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                    
                    warehouse = check_warehouse.first()                   
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id                     

                    outbound6 = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    for shipment in outbound6:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    
                    for shipment in inbound5:
                        processor_id = shipment["processor_id"]
                        processor_type = shipment["processor_type"]
                        processor_entity_name = shipment["processor_entity_name"]
                        return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        if return_context.get("t1_processor"):                                
                            output.extend(return_context["t1_processor"]) 
                else:
                    output = []
                     
            elif get_search_by and get_search_by == 'customer':
                
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()
                    inbound6 = []
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in processor_shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(processor_shipments)

                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop, 
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    for shipment in warehouse_shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(warehouse_shipments)

                    warehouse_ids = [shipment["warehouse_id"] for shipment in warehouse_shipments]
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        warehouse_id__in=warehouse_ids,
                        date_pulled__date__gte=from_date,
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    outbound5 = inbound5 + processor_shipments
                    for shipment in outbound5:
                        processor_id = shipment.get("processor_id")
                        processor_type = shipment.get("processor_type")
                        processor_entity_name = shipment.get("processor_entity_name")
                        
                        return_context = processor_traceability_report_response(
                            select_crop, processor_id, processor_type, 
                            from_date, to_date, processor_entity_name
                        )                        
                        if return_context.get("t1_processor"):                                
                            output.extend(return_context["t1_processor"]) 
                else:
                    output = [] 
             
            else:
                output = []
            for i in output:
                writer.writerow([i["processor_name"] , i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                                 i["pounds_received"], i["pounds_delta"]])
        return response
    else:
        return redirect ('dashboard')


@login_required()
def traceability_report_WIP2_csv_download(request,select_crop,get_search_by,search_text,from_date,to_date):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'Outbound 2 WIP.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
        output = []
        if select_crop == 'COTTON' :
            if get_search_by and get_search_by == 'grower' :
                pass      
                                        
            elif get_search_by and get_search_by == 'field' :
                pass
   
            elif get_search_by and get_search_by == 'processor' :
                pass
                  
            elif get_search_by and get_search_by == 'deliveryid' :
                pass

            else:
                output = []
            for i in output:
                writer.writerow([i["processor_name"] , i["processor_id"], i["shipment_id"], i["date"], i["pounds_shipped"], 
                                 i["pounds_received"], i["pounds_delta"]])
            
        else :
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = check_grower.first().id
                    check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        processor_id = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.id
                        entity_name = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.entity_name
                                                       
                        processor_type = "T1"
                        context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)      
                        output = context_.get("outbound2_wip")
                    else:
                        output = []
                else:
                    output = []               
            
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                if check_field.exists() :
                    field_name = search_text
                    field_id = check_field.first().id                    
                    grower_id =  check_field.first().grower.id                    
                    processor_id = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.id
                    entity_name = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.entity_name
                    processor_type = "T1"
                    context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)
                    output = context_.get("outbound2_wip")
                else:
                    output = []        
                            
            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    context_ = processor_traceability_report_response(select_crop, processor_id,processor_type, from_date, to_date, search_text)
                    output = context_.get("outbound2_wip")
                else:
                    output = []

            elif get_search_by and get_search_by == 'sku_id' :
                context_ = skuid_traceability_response(select_crop, search_text, from_date, to_date)  
                output = context_.get("outbound2_wip") 

            elif get_search_by and get_search_by == 'deliveryid' :                
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)
                        
                if check_shipment.exists() :
                    get_shipment = check_shipment.first()
                    sku_id = get_shipment.sku
                    context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                    output = context_.get("outbound2_wip")      

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                    get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                    
                    if get_shipment and not get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_send 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("outbound2_wip")                        

                    elif get_shipment and get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_recive 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)                        
                        output = context_.get("outbound2_wip")

                    else:
                        output = []

                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    get_shipment = shipments.first()

                    if get_shipment["warehouse_id"] not in [None, "null", "", " "]:                                               
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        outbound6 = []
                        for crop in crops:                            
                            if WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).exists():
                                shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id","customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                                for shipment in shipments:
                                    if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id  
                                outbound6.extend(list(shipments))

                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        
                            if return_context.get("outbound2_wip"):                                
                                output.extend(return_context["outbound2_wip"])                                   
                        
                    else:  
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                            
                            if return_context.get("outbound2_wip"):                                
                                output.extend(return_context["outbound2_wip"])                                      
                               
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id" ,"customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                    for shipment in shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    get_shipment = shipments.first()                    
                    crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                    outbound5_processor = []
                    for crop in crops:
                        select_crop = crop.crop
                        check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                        if check_processor_shipment:
                            for shipment in check_processor_shipment:
                                if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                
                                carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id                                 

                            outbound5_processor.extend(check_processor_shipment) 
                            processor_entity_name = shipment["processor_entity_name"]
                            processor_id = shipment["processor_id"]
                            processor_type = shipment["processor_type"]                             
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)

                            if return_context.get("outbound2_wip"):                                
                                output.extend(return_context["outbound2_wip"])                      
                else:
                    output = []

            elif get_search_by and get_search_by == 'warehouse': 
                output = []                       
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                    
                    warehouse = check_warehouse.first()                   
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id                     

                    outbound6 = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    for shipment in outbound6:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    
                    for shipment in inbound5:
                        processor_id = shipment["processor_id"]
                        processor_type = shipment["processor_type"]
                        processor_entity_name = shipment["processor_entity_name"]
                        return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        if return_context.get("outbound2_wip"):                                
                            output.extend(return_context["outbound2_wip"]) 
                else:
                    output = []
                     
            elif get_search_by and get_search_by == 'customer':
                
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()
                    inbound6 = []
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in processor_shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(processor_shipments)

                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop, 
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    for shipment in warehouse_shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(warehouse_shipments)

                    warehouse_ids = [shipment["warehouse_id"] for shipment in warehouse_shipments]
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        warehouse_id__in=warehouse_ids,
                        date_pulled__date__gte=from_date,
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    outbound5 = inbound5 + processor_shipments
                    for shipment in outbound5:
                        processor_id = shipment.get("processor_id")
                        processor_type = shipment.get("processor_type")
                        processor_entity_name = shipment.get("processor_entity_name")
                        
                        return_context = processor_traceability_report_response(
                            select_crop, processor_id, processor_type, 
                            from_date, to_date, processor_entity_name
                        )                        
                        if return_context.get("outbound2_wip"):                                
                            output.extend(return_context["outbound2_wip"]) 
                else:
                    output = [] 
                                
            else:
                output = []
            for i in output:
                writer.writerow([i["shipment_id"] , i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
        return response
    else:
        return redirect ('dashboard')


@login_required()
def traceability_report_T2_Processor_csv_download(request,select_crop,get_search_by,search_text,from_date,to_date):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'T2 Processor.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        writer.writerow(['PROCESSOR NAME', 'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                             'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
        output = []
        if select_crop == 'COTTON' :
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = [i.id for i in check_grower][0]
                    check_grower_field_crop = Field.objects.filter(crop='COTTON',grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        output = t2_Processor_grower('COTTON',check_grower_id,from_date,to_date)        
                                        
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop='COTTON')
                if check_field.exists() :
                    field_id = [i.id for i in check_field][0]
                    field_name = [i.name for i in check_field][0]
                    warehouse_wh_id = ''
                    output = t2_Processor_field('COTTON',field_name,field_id,from_date,to_date)
   
            elif get_search_by and get_search_by == 'processor' :
                check_processor = Processor.objects.filter(entity_name__icontains=search_text)
                if check_processor.exists() :
                    processor_id = [i.id for i in check_processor][0]
                    get_classing = ClassingReport.objects.filter(processor_id=processor_id).values("id")
                    classing_id = [i["id"] for i in get_classing]
                    bale= BaleReportFarmField.objects.filter(classing_id__in=classing_id).values("id")
                    if bale.exists() :
                        bale_id = [i["id"] for i in bale]
                        output = t2_Processor_Processor('COTTON',processor_id,from_date,to_date,*bale_id)
                  
            elif get_search_by and get_search_by == 'deliveryid' :
                get_delivery_id1 = BaleReportFarmField.objects.filter(bale_id__icontains=search_text)
                get_delivery_id2 = BaleReportFarmField.objects.filter(bale_id__icontains=f"0{search_text}")
                if get_delivery_id1.exists() :
                    field_id = [i.ob4 for i in get_delivery_id1][0]
                    field_name = [i.field_name for i in get_delivery_id1][0]
                    warehouse_wh_id = [i.warehouse_wh_id for i in get_delivery_id1][0]
                    output = t2_Processor_deliveryid('COTTON',search_text,warehouse_wh_id,from_date,to_date)

                elif get_delivery_id2.exists() :
                    field_id = [i.ob4 for i in get_delivery_id2][0]
                    field_name = [i.field_name for i in get_delivery_id2][0]
                    warehouse_wh_id = [i.warehouse_wh_id for i in get_delivery_id2][0]                    
                    output = t2_Processor_deliveryid('COTTON',f"0{search_text}",warehouse_wh_id,from_date,to_date)

            else:
                output = []
            for i in output:
                writer.writerow([i["processor_name"] , i["processor_id"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                                 i["pounds_received"], i["pounds_delta"]])
            
        else :
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = check_grower.first().id
                    check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        processor_id = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.id
                        entity_name = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.entity_name
                                                       
                        processor_type = "T1"
                        context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)      
                        output = context_.get("inbound2_wip")
                    else:
                        output = []
                else:
                    output = []
       
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                if check_field.exists() :
                    field_name = search_text
                    field_id = check_field.first().id                    
                    grower_id =  check_field.first().grower.id                    
                    processor_id = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.id
                    entity_name = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.entity_name
                    processor_type = "T1"
                    context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)
                    output = context_.get("inbound2_wip")
                else:
                    output = []
            
            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    context_ = processor_traceability_report_response(select_crop, processor_id,processor_type, from_date, to_date, search_text)
                    output = context_.get("inbound2_wip")
                else:
                    output = []

            elif get_search_by and get_search_by == 'sku_id' :
                context_ = skuid_traceability_response(select_crop, search_text, from_date, to_date)  
                output = context_.get("inbound2_wip")

            elif get_search_by and get_search_by == 'deliveryid' :                
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)
                        
                if check_shipment.exists() :
                    get_shipment = check_shipment.first()
                    sku_id = get_shipment.sku
                    context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                    output = context_.get("inbound2_wip")      

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                    get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                    
                    if get_shipment and not get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_send 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("inbound2_wip")                        

                    elif get_shipment and get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_recive 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)                        
                        output = context_.get("inbound2_wip")

                    else:
                        output = []

                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    get_shipment = shipments.first()

                    if get_shipment["warehouse_id"] not in [None, "null", "", " "]:                                               
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        outbound6 = []
                        for crop in crops:                            
                            if WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).exists():
                                shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id","customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                                for shipment in shipments:
                                    if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id  
                                outbound6.extend(list(shipments))

                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        
                            if return_context.get("inbound2_wip"):                                
                                output.extend(return_context["inbound2_wip"])                                   
                        
                    else:  
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                            
                            if return_context.get("inbound2_wip"):                                
                                output.extend(return_context["inbound2_wip"])                                      
                               
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id" ,"customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                    for shipment in shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    get_shipment = shipments.first()                    
                    crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                    outbound5_processor = []
                    for crop in crops:
                        select_crop = crop.crop
                        check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id","processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                        if check_processor_shipment:
                            for shipment in check_processor_shipment:
                                if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                
                                carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id                                 

                            outbound5_processor.extend(check_processor_shipment) 
                            processor_entity_name = shipment["processor_entity_name"]
                            processor_id = shipment["processor_id"]
                            processor_type = shipment["processor_type"]                             
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)

                            if return_context.get("inbound2_wip"):                                
                                output.extend(return_context["inbound2_wip"])                      
                else:
                    output = []
            
            elif get_search_by and get_search_by == 'warehouse': 
                output = []                       
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                    
                    warehouse = check_warehouse.first()                   
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id                     

                    outbound6 = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id","shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    for shipment in outbound6:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    
                    for shipment in inbound5:
                        processor_id = shipment["processor_id"]
                        processor_type = shipment["processor_type"]
                        processor_entity_name = shipment["processor_entity_name"]
                        return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        if return_context.get("inbound2_wip"):                                
                            output.extend(return_context["inbound2_wip"]) 
                else:
                    output = []
                     
            elif get_search_by and get_search_by == 'customer':
                
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()
                    inbound6 = []
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in processor_shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(processor_shipments)

                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop, 
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    for shipment in warehouse_shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(warehouse_shipments)

                    warehouse_ids = [shipment["warehouse_id"] for shipment in warehouse_shipments]
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        warehouse_id__in=warehouse_ids,
                        date_pulled__date__gte=from_date,
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    outbound5 = inbound5 + processor_shipments
                    for shipment in outbound5:
                        processor_id = shipment.get("processor_id")
                        processor_type = shipment.get("processor_type")
                        processor_entity_name = shipment.get("processor_entity_name")
                        
                        return_context = processor_traceability_report_response(
                            select_crop, processor_id, processor_type, 
                            from_date, to_date, processor_entity_name
                        )                        
                        if return_context.get("inbound2_wip"):                                
                            output.extend(return_context["inbound2_wip"]) 
                else:
                    output = [] 
             
            else:
                output = []
            for i in output:
                writer.writerow([i["processor_e_name"] , i["shipment_id"], i["recive_delivery_date"], i["volume_shipped"], 
                                 i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
        return response
    else:
        return redirect ('dashboard')


@login_required()
def traceability_report_WIP3_csv_download(request,select_crop,get_search_by,search_text,from_date,to_date):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'Outbound 3 WIP.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
        output = []
        if select_crop == "COTTON":
            pass
        else :
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = check_grower.first().id
                    check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        processor_id = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.id
                        entity_name = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.entity_name
                                                       
                        processor_type = "T1"
                        context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)      
                        output = context_.get("outbound3_wip")
                    else:
                        output = []
                else:
                    output = []              
            
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                if check_field.exists() :
                    field_name = search_text
                    field_id = check_field.first().id                    
                    grower_id =  check_field.first().grower.id                    
                    processor_id = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.id
                    entity_name = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.entity_name
                    processor_type = "T1"
                    context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)
                    output = context_.get("outbound3_wip")
                else:
                    output = []         
                            
            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    context_ = processor_traceability_report_response(select_crop, processor_id,processor_type, from_date, to_date, search_text)
                    output = context_.get("outbound3_wip")
                else:
                    output = []

            elif get_search_by and get_search_by == 'sku_id' :
                context_ = skuid_traceability_response(select_crop, search_text, from_date, to_date)  
                output = context_.get("outbound3_wip") 

            elif get_search_by and get_search_by == 'deliveryid' :                
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)
                        
                if check_shipment.exists() :
                    get_shipment = check_shipment.first()
                    sku_id = get_shipment.sku
                    context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                    output = context_.get("outbound3_wip")      

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                    get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                    
                    if get_shipment and not get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_send 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("outbound3_wip")                        

                    elif get_shipment and get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_recive 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)                        
                        output = context_.get("outbound3_wip")

                    else:
                        output = []

                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    get_shipment = shipments.first()

                    if get_shipment["warehouse_id"] not in [None, "null", "", " "]:                                               
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        outbound6 = []
                        for crop in crops:                            
                            if WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).exists():
                                shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                                for shipment in shipments:
                                    if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id  
                                outbound6.extend(list(shipments))

                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        
                            if return_context.get("outbound3_wip"):                                
                                output.extend(return_context["outbound3_wip"])                                   
                        
                    else:  
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                            
                            if return_context.get("outbound3_wip"):                                
                                output.extend(return_context["outbound3_wip"])                                      
                               
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id" ,"customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                    for shipment in shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    get_shipment = shipments.first()                    
                    crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                    outbound5_processor = []
                    for crop in crops:
                        select_crop = crop.crop
                        check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                        if check_processor_shipment:
                            for shipment in check_processor_shipment:
                                if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                
                                carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id                                 

                            outbound5_processor.extend(check_processor_shipment) 
                            processor_entity_name = shipment["processor_entity_name"]
                            processor_id = shipment["processor_id"]
                            processor_type = shipment["processor_type"]                             
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)

                            if return_context.get("outbound3_wip"):                                
                                output.extend(return_context["outbound3_wip"])                      
                else:
                    output = []

            elif get_search_by and get_search_by == 'warehouse': 
                output = []                       
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                    
                    warehouse = check_warehouse.first()                   
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id                     

                    outbound6 = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    for shipment in outbound6:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    
                    for shipment in inbound5:
                        processor_id = shipment["processor_id"]
                        processor_type = shipment["processor_type"]
                        processor_entity_name = shipment["processor_entity_name"]
                        return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        if return_context.get("outbound3_wip"):                                
                            output.extend(return_context["outbound3_wip"]) 
                else:
                    output = []
                     
            elif get_search_by and get_search_by == 'customer':
                
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()
                    inbound6 = []
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in processor_shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(processor_shipments)

                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop, 
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    for shipment in warehouse_shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(warehouse_shipments)

                    warehouse_ids = [shipment["warehouse_id"] for shipment in warehouse_shipments]
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        warehouse_id__in=warehouse_ids,
                        date_pulled__date__gte=from_date,
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    outbound5 = inbound5 + processor_shipments
                    for shipment in outbound5:
                        processor_id = shipment.get("processor_id")
                        processor_type = shipment.get("processor_type")
                        processor_entity_name = shipment.get("processor_entity_name")
                        
                        return_context = processor_traceability_report_response(
                            select_crop, processor_id, processor_type, 
                            from_date, to_date, processor_entity_name
                        )                        
                        if return_context.get("outbound3_wip"):                                
                            output.extend(return_context["outbound3_wip"]) 
                else:
                    output = [] 
                                 
            else:
                output = []
            for i in output:
                writer.writerow([i["shipment_id"] , i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
        return response
    else:
        return redirect ('dashboard')


@login_required()
def traceability_report_T3_Processor_csv_download(request,select_crop,get_search_by,search_text,from_date,to_date):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'T3 Processor.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        writer.writerow(['PROCESSOR NAME', 'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                             'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
        output = []
        if select_crop == 'COTTON':
            pass
        else :
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = check_grower.first().id
                    check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        processor_id = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.id
                        entity_name = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.entity_name
                                                       
                        processor_type = "T1"
                        context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)      
                        output = context_.get("inbound3_wip")
                    else:
                        output = []
                else:
                    output = []
       
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                if check_field.exists() :
                    field_name = search_text
                    field_id = check_field.first().id                    
                    grower_id =  check_field.first().grower.id                    
                    processor_id = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.id
                    entity_name = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.entity_name
                    processor_type = "T1"
                    context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)
                    output = context_.get("inbound3_wip")
                else:
                    output = []
            
            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    context_ = processor_traceability_report_response(select_crop, processor_id,processor_type, from_date, to_date, search_text)
                    output = context_.get("inbound3_wip")
                else:
                    output = []

            elif get_search_by and get_search_by == 'sku_id' :
                context_ = skuid_traceability_response(select_crop, search_text, from_date, to_date)  
                output = context_.get("inbound3_wip")

            elif get_search_by and get_search_by == 'deliveryid' :                
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)
                        
                if check_shipment.exists() :
                    get_shipment = check_shipment.first()
                    sku_id = get_shipment.sku
                    context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                    output = context_.get("inbound3_wip")      

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                    get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                    
                    if get_shipment and not get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_send 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("inbound3_wip")                        

                    elif get_shipment and get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_recive 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)                        
                        output = context_.get("inbound3_wip")

                    else:
                        output = []

                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id","warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    get_shipment = shipments.first()

                    if get_shipment["warehouse_id"] not in [None, "null", "", " "]:                                               
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        outbound6 = []
                        for crop in crops:                            
                            if WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).exists():
                                shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                                for shipment in shipments:
                                    if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id  
                                outbound6.extend(list(shipments))

                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        
                            if return_context.get("inbound3_wip"):                                
                                output.extend(return_context["inbound3_wip"])                                   
                        
                    else:  
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                            
                            if return_context.get("inbound3_wip"):                                
                                output.extend(return_context["inbound3_wip"])                                      
                               
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id","customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                    for shipment in shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    get_shipment = shipments.first()                    
                    crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                    outbound5_processor = []
                    for crop in crops:
                        select_crop = crop.crop
                        check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id","processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                        if check_processor_shipment:
                            for shipment in check_processor_shipment:
                                if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                
                                carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id                                 

                            outbound5_processor.extend(check_processor_shipment) 
                            processor_entity_name = shipment["processor_entity_name"]
                            processor_id = shipment["processor_id"]
                            processor_type = shipment["processor_type"]                             
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)

                            if return_context.get("inbound3_wip"):                                
                                output.extend(return_context["inbound3_wip"])                      
                else:
                    output = []

            elif get_search_by and get_search_by == 'warehouse': 
                output = []                       
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                    
                    warehouse = check_warehouse.first()                   
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id                     

                    outbound6 = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id","shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    for shipment in outbound6:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    
                    for shipment in inbound5:
                        processor_id = shipment["processor_id"]
                        processor_type = shipment["processor_type"]
                        processor_entity_name = shipment["processor_entity_name"]
                        return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        if return_context.get("inbound3_wip"):                                
                            output.extend(return_context["inbound3_wip"]) 
                else:
                    output = []
                     
            elif get_search_by and get_search_by == 'customer':
                
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()
                    inbound6 = []
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in processor_shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(processor_shipments)

                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop, 
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    for shipment in warehouse_shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(warehouse_shipments)

                    warehouse_ids = [shipment["warehouse_id"] for shipment in warehouse_shipments]
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        warehouse_id__in=warehouse_ids,
                        date_pulled__date__gte=from_date,
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    outbound5 = inbound5 + processor_shipments
                    for shipment in outbound5:
                        processor_id = shipment.get("processor_id")
                        processor_type = shipment.get("processor_type")
                        processor_entity_name = shipment.get("processor_entity_name")
                        
                        return_context = processor_traceability_report_response(
                            select_crop, processor_id, processor_type, 
                            from_date, to_date, processor_entity_name
                        )                        
                        if return_context.get("inbound3_wip"):                                
                            output.extend(return_context["inbound3_wip"]) 
                else:
                    output = [] 
              
            else:
                output = []
            for i in output:
                writer.writerow([i["processor_e_name"] , i["shipment_id"], i["recive_delivery_date"], i["volume_shipped"], 
                                 i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
        return response
    else:
        return redirect ('dashboard')


@login_required()
def traceability_report_WIP4_csv_download(request,select_crop,get_search_by,search_text,from_date,to_date):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'Outbound 4 WIP.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
        output = []
        if select_crop == "COTTON":
            pass
        else:
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = check_grower.first().id
                    check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        processor_id = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.id
                        entity_name = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.entity_name
                                                       
                        processor_type = "T1"
                        context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)      
                        output = context_.get("outbound4_wip")
                    else:
                        output = []
                else:
                    output = []               
            
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                if check_field.exists() :
                    field_name = search_text
                    field_id = check_field.first().id                    
                    grower_id =  check_field.first().grower.id                    
                    processor_id = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.id
                    entity_name = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.entity_name
                    processor_type = "T1"
                    context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)
                    output = context_.get("outbound4_wip")
                else:
                    output = []         
                            
            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    context_ = processor_traceability_report_response(select_crop, processor_id,processor_type, from_date, to_date, search_text)
                    output = context_.get("outbound4_wip")
                else:
                    output = []

            elif get_search_by and get_search_by == 'sku_id' :
                context_ = skuid_traceability_response(select_crop, search_text, from_date, to_date)  
                output = context_.get("outbound4_wip") 

            elif get_search_by and get_search_by == 'deliveryid' :                
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)
                        
                if check_shipment.exists() :
                    get_shipment = check_shipment.first()
                    sku_id = get_shipment.sku
                    context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                    output = context_.get("outbound4_wip")      

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                    get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                    
                    if get_shipment and not get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_send 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("outbound4_wip")                        

                    elif get_shipment and get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_recive 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)                        
                        output = context_.get("outbound4_wip")

                    else:
                        output = []

                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    get_shipment = shipments.first()

                    if get_shipment["warehouse_id"] not in [None, "null", "", " "]:                                               
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        outbound6 = []
                        for crop in crops:                            
                            if WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).exists():
                                shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                                for shipment in shipments:
                                    if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id  
                                outbound6.extend(list(shipments))

                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        
                            if return_context.get("outbound4_wip"):                                
                                output.extend(return_context["outbound4_wip"])                                   
                        
                    else:  
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                            
                            if return_context.get("outbound4_wip"):                                
                                output.extend(return_context["outbound4_wip"])                                      
                               
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id" ,"customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                    for shipment in shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    get_shipment = shipments.first()                    
                    crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                    outbound5_processor = []
                    for crop in crops:
                        select_crop = crop.crop
                        check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id","processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                        if check_processor_shipment:
                            for shipment in check_processor_shipment:
                                if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                
                                carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id                                 

                            outbound5_processor.extend(check_processor_shipment) 
                            processor_entity_name = shipment["processor_entity_name"]
                            processor_id = shipment["processor_id"]
                            processor_type = shipment["processor_type"]                             
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)

                            if return_context.get("outbound4_wip"):                                
                                output.extend(return_context["outbound4_wip"])                      
                else:
                    output = []

            elif get_search_by and get_search_by == 'warehouse': 
                output = []                       
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                    
                    warehouse = check_warehouse.first()                   
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id                     

                    outbound6 = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id","shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    for shipment in outbound6:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    
                    for shipment in inbound5:
                        processor_id = shipment["processor_id"]
                        processor_type = shipment["processor_type"]
                        processor_entity_name = shipment["processor_entity_name"]
                        return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        if return_context.get("outbound4_wip"):                                
                            output.extend(return_context["outbound4_wip"]) 
                else:
                    output = []
                     
            elif get_search_by and get_search_by == 'customer':
                
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()
                    inbound6 = []
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in processor_shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(processor_shipments)

                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop, 
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    for shipment in warehouse_shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(warehouse_shipments)

                    warehouse_ids = [shipment["warehouse_id"] for shipment in warehouse_shipments]
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        warehouse_id__in=warehouse_ids,
                        date_pulled__date__gte=from_date,
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    outbound5 = inbound5 + processor_shipments
                    for shipment in outbound5:
                        processor_id = shipment.get("processor_id")
                        processor_type = shipment.get("processor_type")
                        processor_entity_name = shipment.get("processor_entity_name")
                        
                        return_context = processor_traceability_report_response(
                            select_crop, processor_id, processor_type, 
                            from_date, to_date, processor_entity_name
                        )                        
                        if return_context.get("outbound4_wip"):                                
                            output.extend(return_context["outbound4_wip"]) 
                else:
                    output = [] 
              
            else:
                output = []
            for i in output:
                writer.writerow([i["shipment_id"] , i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
        return response
    else:
        return redirect ('dashboard')


@login_required()
def traceability_report_T4_Processor_csv_download(request,select_crop,get_search_by,search_text,from_date,to_date):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'T4 Processor.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        writer.writerow(['PROCESSOR NAME', 'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                             'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
        output = []
        if select_crop == 'COTTON':
            pass
        else:
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = check_grower.first().id
                    check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        processor_id = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.id
                        entity_name = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.entity_name
                                                       
                        processor_type = "T1"
                        context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)      
                        output = context_.get("inbound4_wip")
                    else:
                        output = []
                else:
                    output = []
       
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                if check_field.exists() :
                    field_name = search_text
                    field_id = check_field.first().id                    
                    grower_id =  check_field.first().grower.id                    
                    processor_id = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.id
                    entity_name = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.entity_name
                    processor_type = "T1"
                    context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)
                    output = context_.get("inbound4_wip")
                else:
                    output = []
            
            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    context_ = processor_traceability_report_response(select_crop, processor_id,processor_type, from_date, to_date, search_text)
                    output = context_.get("inbound4_wip")
                else:
                    output = []

            elif get_search_by and get_search_by == 'sku_id' :
                context_ = skuid_traceability_response(select_crop, search_text, from_date, to_date)  
                output = context_.get("inbound4_wip")

            elif get_search_by and get_search_by == 'deliveryid' :                
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)
                        
                if check_shipment.exists() :
                    get_shipment = check_shipment.first()
                    sku_id = get_shipment.sku
                    context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                    output = context_.get("inbound4_wip")      

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                    get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                    
                    if get_shipment and not get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_send 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("inbound4_wip")                        

                    elif get_shipment and get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_recive 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)                        
                        output = context_.get("inbound4_wip")

                    else:
                        output = []

                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    get_shipment = shipments.first()

                    if get_shipment["warehouse_id"] not in [None, "null", "", " "]:                                               
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        outbound6 = []
                        for crop in crops:                            
                            if WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).exists():
                                shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                                for shipment in shipments:
                                    if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id  
                                outbound6.extend(list(shipments))

                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        
                            if return_context.get("inbound4_wip"):                                
                                output.extend(return_context["inbound4_wip"])                                   
                        
                    else:  
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                            
                            if return_context.get("inbound4_wip"):                                
                                output.extend(return_context["inbound4_wip"])                                      
                               
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                    output = []
                    shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id" ,"customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                    for shipment in shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    get_shipment = shipments.first()                    
                    crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                    outbound5_processor = []
                    for crop in crops:
                        select_crop = crop.crop
                        check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id","processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                        if check_processor_shipment:
                            for shipment in check_processor_shipment:
                                if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                    shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                
                                carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                shipment["carrier_id"] = carrier.carrier_id                                 

                            outbound5_processor.extend(check_processor_shipment) 
                            processor_entity_name = shipment["processor_entity_name"]
                            processor_id = shipment["processor_id"]
                            processor_type = shipment["processor_type"]                             
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)

                            if return_context.get("inbound4_wip"):                                
                                output.extend(return_context["inbound4_wip"])                      
                else:
                    output = []

            elif get_search_by and get_search_by == 'warehouse': 
                output = []                       
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                    
                    warehouse = check_warehouse.first()                   
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id                     

                    outbound6 = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id","shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    for shipment in outbound6:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    
                    for shipment in inbound5:
                        processor_id = shipment["processor_id"]
                        processor_type = shipment["processor_type"]
                        processor_entity_name = shipment["processor_entity_name"]
                        return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        if return_context.get("inbound4_wip"):                                
                            output.extend(return_context["inbound4_wip"]) 
                else:
                    output = []
                     
            elif get_search_by and get_search_by == 'customer':
                
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()
                    inbound6 = []
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in processor_shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(processor_shipments)

                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop, 
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    for shipment in warehouse_shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(warehouse_shipments)

                    warehouse_ids = [shipment["warehouse_id"] for shipment in warehouse_shipments]
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        warehouse_id__in=warehouse_ids,
                        date_pulled__date__gte=from_date,
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    outbound5 = inbound5 + processor_shipments
                    for shipment in outbound5:
                        processor_id = shipment.get("processor_id")
                        processor_type = shipment.get("processor_type")
                        processor_entity_name = shipment.get("processor_entity_name")
                        
                        return_context = processor_traceability_report_response(
                            select_crop, processor_id, processor_type, 
                            from_date, to_date, processor_entity_name
                        )                        
                        if return_context.get("inbound4_wip"):                                
                            output.extend(return_context["inbound4_wip"]) 
                else:
                    output = [] 
              
            else:
                output = []
            for i in output:
                writer.writerow([i["processor_e_name"] , i["shipment_id"], i["recive_delivery_date"], i["volume_shipped"], 
                                 i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
        return response
    else:
        return redirect ('dashboard')


@login_required()
def traceability_report_WIP5_csv_download(request,select_crop, get_search_by, search_text, from_date, to_date):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'Outbound 5 WIP.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        writer.writerow(['DELIVERY ID', 'PROCESSOR NAME', 'WAREHOUSE/CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
        output = []
        if select_crop == "COTTON":
            pass
        else:
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = check_grower.first().id
                    check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        processor_id = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.id
                        entity_name = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.entity_name
                                                       
                        processor_type = "T1"
                        context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)      
                        output = context_.get("outbound5_wip")
                    else:
                        output = []
                else:
                    output = []               
            
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                if check_field.exists() :
                    field_name = search_text
                    field_id = check_field.first().id                    
                    grower_id =  check_field.first().grower.id                    
                    processor_id = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.id
                    entity_name = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.entity_name
                    processor_type = "T1"
                    context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)
                    output = context_.get("outbound5_wip")
                else:
                    output = []         
                            
            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    context_ = processor_traceability_report_response(select_crop, processor_id,processor_type, from_date, to_date, search_text)
                    output = context_.get("outbound5_wip")
                else:
                    output = []

            elif get_search_by and get_search_by == 'sku_id' :
                context_ = skuid_traceability_response(select_crop, search_text, from_date, to_date)  
                output = context_.get("outbound5_wip") 

            elif get_search_by and get_search_by == 'deliveryid' :                        
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)
                
                if check_shipment.exists() :
                    get_shipment = check_shipment.first()
                    sku_id = get_shipment.sku
                    context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                    output = context_.get("outbound5_wip")                               

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                    get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                    
                    if get_shipment and not get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_send 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("outbound5_wip")

                    elif get_shipment and get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_recive 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("outbound5_wip")

                    else:
                        output = []

                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                    
                    shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    get_shipment = shipments.first()
                    if get_shipment["warehouse_id"] not in [None, "null", "", " "]:
                        inbound5 = list(shipments)                        
                        output = inbound5                        
                        
                    else:
                        output = shipments
                             
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                    shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id" ,"customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                    for shipment in shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    get_shipment = shipments.first()
                   
                    crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                    outbound5_processor = []
                    for crop in crops:
                        select_crop = crop.crop
                        check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id","processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                        if check_processor_shipment:
                                for shipment in check_processor_shipment:
                                    if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id                                 

                                outbound5_processor.extend(check_processor_shipment)                                

                    output = outbound5_processor
                                           
                else:
                    output = []   
              
            elif get_search_by and get_search_by == 'warehouse':               
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                  
                    warehouse = check_warehouse.first()                    
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    outbound6 = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id","shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    for shipment in outbound6:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    
                    output = inbound5
                    
                else:
                    output = []
            
            elif get_search_by and get_search_by == 'customer':                
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()
                    inbound6 = []
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in processor_shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(processor_shipments)

                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop, 
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    for shipment in warehouse_shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(warehouse_shipments)

                    warehouse_ids = [shipment["warehouse_id"] for shipment in warehouse_shipments]
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        warehouse_id__in=warehouse_ids,
                        date_pulled__date__gte=from_date,
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    
                    output = inbound5 + processor_shipments
                else:
                    output = []
            
            else:
                output = []
            for i in output:
                writer.writerow([i["shipment_id"] ,i["processor_entity_name"], i["warehouse_name"] if i["warehouse_name"] is not None else i["customer_name"], i["date_pulled"], i["carrier_type"]])
        return response
    else:
        return redirect ('dashboard')


@login_required()
def traceability_report_Warehouse_csv_download(request, select_crop, get_search_by, search_text, from_date, to_date):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'Warehouse.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        writer.writerow(['PROCESSOR NAME', 'WAREHOUSE NAME', 'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
        output = []
        if select_crop == 'COTTON':
            pass
        else:
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = check_grower.first().id
                    check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        processor_id = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.id
                        entity_name = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.entity_name
                                                       
                        processor_type = "T1"
                        context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)      
                        output = context_.get("inbound5_wip")
                    else:
                        output = []
                else:
                    output = []
       
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                if check_field.exists() :
                    field_name = search_text
                    field_id = check_field.first().id                    
                    grower_id =  check_field.first().grower.id                    
                    processor_id = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.id
                    entity_name = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.entity_name
                    processor_type = "T1"
                    context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)
                    output = context_.get("inbound5_wip")
                else:
                    output = []
            
            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    context_ = processor_traceability_report_response(select_crop, processor_id,processor_type, from_date, to_date, search_text)
                    output = context_.get("inbound5_wip")
                else:
                    output = []

            elif get_search_by and get_search_by == 'sku_id' :
                context_ = skuid_traceability_response(select_crop, search_text, from_date, to_date)  
                output = context_.get("inbound5_wip")

            elif get_search_by and get_search_by == 'deliveryid' :                        
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)
                
                if check_shipment.exists() :
                    get_shipment = check_shipment.first()
                    sku_id = get_shipment.sku
                    context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                    output = context_.get("inbound5_wip")                              

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                    get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                    
                    if get_shipment and not get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_send 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("inbound5_wip")

                    elif get_shipment and get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_recive 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("inbound5_wip")

                    else:
                        output = []

                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                    
                    shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    get_shipment = shipments.first()
                    if get_shipment["warehouse_id"] not in [None, "null", "", " "]:
                        inbound5 = list(shipments)
                        output = inbound5
                        
                    else:
                        output = []
                        
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                    shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id" ,"customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                    for shipment in shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    get_shipment = shipments.first()                    
                    crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                    outbound5_processor = []
                    for crop in crops:
                        select_crop = crop.crop
                        check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id","processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                        if check_processor_shipment:
                                for shipment in check_processor_shipment:
                                    if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id                                 

                                outbound5_processor.extend(check_processor_shipment)                               
                    output = outbound5_processor                        
                else:
                    output = []   

            elif get_search_by and get_search_by == 'warehouse':                
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                  
                    warehouse = check_warehouse.first()                    
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    output = inbound5
                    
                else:
                    output = []
            
            elif get_search_by and get_search_by == 'customer':                
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()
                    inbound6 = []
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in processor_shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(processor_shipments)

                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop, 
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    for shipment in warehouse_shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(warehouse_shipments)

                    warehouse_ids = [shipment["warehouse_id"] for shipment in warehouse_shipments]
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        warehouse_id__in=warehouse_ids,
                        date_pulled__date__gte=from_date,
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    output = inbound5
                    
                else:
                    output = [] 
            
            else:
                output = []
            for i in output:
                writer.writerow([i["processor_entity_name"] ,i["warehouse_name"], i["shipment_id"], i["distributor_receive_date"] 
                                 ])
        return response
    else:
        return redirect ('dashboard')


@login_required()
def traceability_report_WIP6_csv_download(request,select_crop, get_search_by, search_text, from_date, to_date):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'Outbound 6 WIP.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        writer.writerow(['DELIVERY ID', 'WAREHOUSE NAME', 'CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
        output = []
        if select_crop == "COTTON":
            pass
        else:
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = check_grower.first().id
                    check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        processor_id = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.id
                        entity_name = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.entity_name
                                                       
                        processor_type = "T1"
                        context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)      
                        output = context_.get("outbound6_wip")
                    else:
                        output = []
                else:
                    output = []               
            
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                if check_field.exists() :
                    field_name = search_text
                    field_id = check_field.first().id                    
                    grower_id =  check_field.first().grower.id                    
                    processor_id = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.id
                    entity_name = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.entity_name
                    processor_type = "T1"
                    context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)
                    output = context_.get("outbound6_wip")
                else:
                    output = []         
                            
            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    context_ = processor_traceability_report_response(select_crop, processor_id,processor_type, from_date, to_date, search_text)
                    output = context_.get("outbound6_wip")
                else:
                    output = []

            elif get_search_by and get_search_by == 'sku_id' :
                context_ = skuid_traceability_response(select_crop, search_text, from_date, to_date)  
                output = context_.get("outbound6_wip") 

            elif get_search_by and get_search_by == 'deliveryid' :
                        
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)
                
                if check_shipment.exists() :
                    get_shipment = check_shipment.first()
                    sku_id = get_shipment.sku
                    context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                    output = context_.get("outbound6_wip")                              

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                    get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                    
                    if get_shipment and not get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_send 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("outbound6_wip") 

                    elif get_shipment and get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_recive 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("outbound6_wip") 

                    else:
                        output = []

                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                    
                    shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id","warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    get_shipment = shipments.first()
                    if get_shipment["warehouse_id"] not in [None, "null", "", " "]:
                        inbound5 = list(shipments)                        
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        outbound6 = []
                        for crop in crops:
                            
                            if WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).exists():
                                shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                                for shipment in shipments:
                                    if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id  
                                outbound6.extend(list(shipments))
                        output = outbound6                        
                    else:
                          output = []
                        
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                    shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id" ,"customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                    for shipment in shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id                    
                    output = list(shipments)
                                           
                else:
                    output = []   

            elif get_search_by and get_search_by == 'warehouse':
                
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                   
                    warehouse = check_warehouse.first()                  
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id                      

                    outbound6 = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id","shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    for shipment in outbound6:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    output = outbound6
                    
                else:
                    output = []
              
            elif get_search_by and get_search_by == 'customer':
                
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()
                    inbound6 = []
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in processor_shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(processor_shipments)

                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop, 
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    for shipment in warehouse_shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(warehouse_shipments)                    
                    output = warehouse_shipments
                    
                else:
                    output = []
            
            else:
                output = []
            for i in output:
                writer.writerow([i["shipment_id"] ,i["warehouse_name"], i["customer_name"], i["date_pulled"],  i["carrier_type"]])
        return response
    else:
        return redirect ('dashboard')


@login_required()
def traceability_report_Customer_csv_download(request, select_crop, get_search_by, search_text, from_date, to_date):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'Customer.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        writer.writerow(['WAREHOUSE/PROCESSOR NAME', 'CUSTOMER NAME', 'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
        output = []
        if select_crop == 'COTTON':
            pass
        else:
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = check_grower.first().id
                    check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        processor_id = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.id
                        entity_name = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.entity_name
                                                       
                        processor_type = "T1"
                        context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)      
                        output = context_.get("inbound6_wip")
                    else:
                        output = []
                else:
                    output = []
       
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                if check_field.exists() :
                    field_name = search_text
                    field_id = check_field.first().id                    
                    grower_id =  check_field.first().grower.id                    
                    processor_id = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.id
                    entity_name = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.entity_name
                    processor_type = "T1"
                    context_ = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)
                    output = context_.get("inbound6_wip")
                else:
                    output = []
            
            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    context_ = processor_traceability_report_response(select_crop, processor_id,processor_type, from_date, to_date, search_text)
                    output = context_.get("inbound6_wip")
                else:
                    output = []

            elif get_search_by and get_search_by == 'sku_id' :
                context_ = skuid_traceability_response(select_crop, search_text, from_date, to_date)  
                output = context_.get("inbound6_wip")

            elif get_search_by and get_search_by == 'deliveryid' :                        
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)                        
                if check_shipment.exists() :
                    get_shipment = check_shipment.first()
                    sku_id = get_shipment.sku
                    context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                    output = context_.get("inbound6_wip")                              

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                    get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                    
                    if get_shipment and not get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_send 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("inbound6_wip")

                    elif get_shipment and get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_recive 
                        context_ = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                        output = context_.get("inbound6_wip")

                    else:
                        output = []

                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                    
                    shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    get_shipment = shipments.first()
                    if get_shipment["warehouse_id"] not in [None, "null", "", " "]:
                        inbound5 = list(shipments)                        
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        outbound6 = []
                        for crop in crops:
                          
                            if WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).exists():
                                shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                                for shipment in shipments:
                                    if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id  
                                outbound6.extend(list(shipments))                        
                        output = outbound6                        
                    else:
                        output = shipments
                        
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                    shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id" ,"customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                    for shipment in shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    get_shipment = shipments.first()
                    output = list(shipments)                                         
                
                else:
                    output = []    
        
            elif get_search_by and get_search_by == 'warehouse':                
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                    
                    warehouse = check_warehouse.first()                    
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id                     

                    outbound6 = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id","shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    for shipment in outbound6:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    output = outbound6                   
                    
                else:
                    output = []
            
            elif get_search_by and get_search_by == 'customer':                
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()
                    inbound6 = []
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in processor_shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(processor_shipments)

                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop, 
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    for shipment in warehouse_shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(warehouse_shipments)

                    output = inbound6
                    
                else:
                    output = [] 
            
            else:
                output = []
            
            for i in output:
                writer.writerow([i["warehouse_name"] if i["warehouse_name"] is not None else i["processor_entity_name"] ,i["customer_name"], i["shipment_id"], i["customer_receive_date"] if i["warehouse_name"] is not None else i["distributor_receive_date"]
                                 ])
        return response
    else:
        return redirect ('dashboard')
   

@login_required()
def traceability_report_all_csv_download(request,select_crop,get_search_by,search_text,from_date,to_date):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'TRACE MODULE.csv'
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        
        output_origin = []
        if select_crop == 'COTTON' :
            # search by Grower ....
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = [i.id for i in check_grower][0]
                    check_grower_field_crop = Field.objects.filter(crop='COTTON',grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        grower_field_ids = [i.id for i in check_grower_field_crop]
                        writer.writerow(["Origin"])
                        writer.writerow(['CROP', 'VARIETY', 'FIELD', 'GROWER', 'FARM', 'HARVEST DATE', 
                            'PROJECTED YIELD', 'ACTUAL YIELD', 'YIELD  DELTA', 'Pass / Fail Sustainability','Water Savings %',
                            'Land Use Efficiency %', 'Less GHG % ', 'Premiums to Growers %', 'CO2 EQ footprint #','Pounds of Water Per Pound Savings %'])
                        get_Origin_Grower = Origin_searchby_Grower('COTTON',search_text,*grower_field_ids)         
                        for i in get_Origin_Grower :
                            writer.writerow([i["get_select_crop"], i["variety"], i["field_name"], i["grower_name"], i["farm_name"], i["harvest_date"], 
                            i["projected_yeild"], i["reported_yeild"], i["yield_delta"],i["pf_sus"],i["water_savings"],i["land_use"],i["premiums_to_growers"],
                            i["co2_eQ_footprint"],i["water_per_pound_savings"]])
                        writer.writerow([""])
                        writer.writerow(["Outbound 1 WIP"])
                        writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                               
                        writer.writerow([""])
                        writer.writerow(["T1 Processor"])
                        writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                        'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                        t1_processor = t1_Processor_grower('COTTON',check_grower_id,from_date,to_date)
                        for i in t1_processor:
                            writer.writerow([i["processor_name"] , i["processor_id"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                            i["pounds_received"], i["pounds_delta"]])
                        # 20-03-23
                        writer.writerow([""])
                        writer.writerow(["Outbound 2 WIP"])
                        writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                       
                        writer.writerow([""])
                        writer.writerow(["T2 Processor"])
                        writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                        'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                        t2_processor = t2_Processor_grower('COTTON',check_grower_id,from_date,to_date)
                        for i in t2_processor:
                            writer.writerow([i["processor_name"] , i["processor_id"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                            i["pounds_received"], i["pounds_delta"]])
 
                    else:
                        pass
                else:
                    pass
            # search by Field ....
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop='COTTON')
                if check_field.exists() :
                    field_id = [i.id for i in check_field][0]
                    field_name = [i.name for i in check_field][0]
                    warehouse_wh_id = ''
                    writer.writerow(["Origin"])
                    writer.writerow(['CROP', 'VARIETY', 'FIELD', 'GROWER', 'FARM', 'HARVEST DATE', 
                        'PROJECTED YIELD', 'ACTUAL YIELD', 'YIELD  DELTA', 'Pass / Fail Sustainability','Water Savings %',
                        'Land Use Efficiency %', 'Less GHG % ', 'Premiums to Growers %', 'CO2 EQ footprint #','Pounds of Water Per Pound Savings %'])
                    get_origin_details = get_Origin_deliveryid('COTTON',field_id,field_name,'',warehouse_wh_id)
                    for i in get_origin_details :
                        writer.writerow([i["get_select_crop"], i["variety"], i["field_name"], i["grower_name"], i["farm_name"], i["harvest_date"], 
                        i["projected_yeild"], i["reported_yeild"], i["yield_delta"],i["pf_sus"],i["water_savings"],i["land_use"],i["premiums_to_growers"],
                        i["co2_eQ_footprint"],i["water_per_pound_savings"]])
                    writer.writerow([""])
                    writer.writerow(["Outbound 1 WIP"])
                    writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                    # outbound1_wip = outbound1_Wip_field('COTTON',search_text,from_date,to_date,field_id)
                    writer.writerow([""])
                    writer.writerow(["T1 Processor"])
                    writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                    'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                    t1_processor = t1_Processor_field('COTTON',field_name,field_id,field_id,from_date,to_date)
                    for i in t1_processor:
                        writer.writerow([i["processor_name"] , i["processor_id"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                        i["pounds_received"], i["pounds_delta"]])
                    # 20-03-23
                    writer.writerow([""])
                    writer.writerow(["Outbound 2 WIP"])
                    writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                           
                    writer.writerow([""])
                    writer.writerow(["T2 Processor"])
                    writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                    'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                    t2_processor = t2_Processor_field('COTTON',field_name,field_id,from_date,to_date)
                    for i in t2_processor:
                        writer.writerow([i["processor_name"] , i["processor_id"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                        i["pounds_received"], i["pounds_delta"]])
                else:
                    pass
            # search by Processor ....
            elif get_search_by and get_search_by == 'processor' :
                check_processor = Processor.objects.filter(entity_name__icontains=search_text)
                if check_processor.exists() :
                    processor_id = [i.id for i in check_processor][0]
                    get_classing = ClassingReport.objects.filter(processor_id=processor_id).values("id")
                    classing_id = [i["id"] for i in get_classing]
                    bale= BaleReportFarmField.objects.filter(classing_id__in=classing_id).values("id")
                    if bale.exists() :
                        bale_id = [i["id"] for i in bale]
                        writer.writerow(["Origin"])
                        writer.writerow(['CROP', 'VARIETY', 'FIELD', 'GROWER', 'FARM', 'HARVEST DATE', 
                            'PROJECTED YIELD', 'ACTUAL YIELD', 'YIELD  DELTA', 'Pass / Fail Sustainability','Water Savings %',
                            'Land Use Efficiency %', 'Less GHG % ', 'Premiums to Growers %', 'CO2 EQ footprint #','Pounds of Water Per Pound Savings %'])
                        get_Origin_Processor = Origin_searchby_Processor('COTTON',search_text,*bale_id)         
                        for i in get_Origin_Processor :
                            writer.writerow([i["get_select_crop"], i["variety"], i["field_name"], i["grower_name"], i["farm_name"], i["harvest_date"], 
                            i["projected_yeild"], i["reported_yeild"], i["yield_delta"],i["pf_sus"],i["water_savings"],i["land_use"],i["premiums_to_growers"],
                            i["co2_eQ_footprint"],i["water_per_pound_savings"]])
                        writer.writerow([""])
                        writer.writerow(["Outbound 1 WIP"])
                        writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                        writer.writerow([""])
                        writer.writerow(["T1 Processor"])
                        writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                        'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                        t1_processor = t1_Processor_Processor('COTTON',processor_id,from_date,to_date,*bale_id)
                        for i in t1_processor:
                            writer.writerow([i["processor_name"] , i["processor_id"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                            i["pounds_received"], i["pounds_delta"]])
                        # 20-03-23
                        writer.writerow([""])
                        writer.writerow(["Outbound 2 WIP"])
                        writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                        # outbound2_wip = outbound2_Wip_Processor('COTTON',search_text,processor_id,from_date,to_date)        
                        writer.writerow([""])
                        writer.writerow(["T2 Processor"])
                        writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                        'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])                        
                        t2_processor =  t2_Processor_Processor('COTTON',processor_id,from_date,to_date,*bale_id) 
                        for i in t2_processor:
                            writer.writerow([i["processor_name"] , i["processor_id"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                            i["pounds_received"], i["pounds_delta"]])
                    else:
                        pass
                else:
                    pass
            # search by Delivery ID ....
            elif get_search_by and get_search_by == 'deliveryid' :
                get_delivery_id1 = BaleReportFarmField.objects.filter(bale_id__icontains=search_text)
                get_delivery_id2 = BaleReportFarmField.objects.filter(bale_id__icontains=f"0{search_text}")
                if get_delivery_id1.exists() :
                    field_id = [i.ob4 for i in get_delivery_id1][0]
                    field_name = [i.field_name for i in get_delivery_id1][0]
                    warehouse_wh_id = [i.warehouse_wh_id for i in get_delivery_id1][0]
                    writer.writerow(["Origin"])
                    writer.writerow(['CROP', 'VARIETY', 'FIELD', 'GROWER', 'FARM', 'HARVEST DATE', 
                        'PROJECTED YIELD', 'ACTUAL YIELD', 'YIELD  DELTA', 'Pass / Fail Sustainability','Water Savings %',
                        'Land Use Efficiency %', 'Less GHG % ', 'Premiums to Growers %', 'CO2 EQ footprint #','Pounds of Water Per Pound Savings %'])
                    get_origin_details = get_Origin_deliveryid('COTTON',field_id,field_name,search_text,warehouse_wh_id)
                    for i in get_Origin_Processor :
                            writer.writerow([i["get_select_crop"], i["variety"], i["field_name"], i["grower_name"], i["farm_name"], i["harvest_date"], 
                            i["projected_yeild"], i["reported_yeild"], i["yield_delta"],i["pf_sus"],i["water_savings"],i["land_use"],i["premiums_to_growers"],
                            i["co2_eQ_footprint"],i["water_per_pound_savings"]])
                    
                    writer.writerow([""])
                    writer.writerow(["Outbound 1 WIP"])
                    writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                    writer.writerow([""])
                    writer.writerow(["T1 Processor"])
                    writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                    'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                    t1_processor = t1_Processor_deliveryid('COTTON',search_text,warehouse_wh_id,from_date,to_date)
                    for i in t1_processor:
                        writer.writerow([i["processor_name"] , i["processor_id"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                        i["pounds_received"], i["pounds_delta"]])
                    writer.writerow([""])
                    writer.writerow(["Outbound 2 WIP"])
                    writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                    writer.writerow([""])
                    writer.writerow(["T2 Processor"])
                    writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                    'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])   
                    t2_processor =  t2_Processor_deliveryid('COTTON',search_text,warehouse_wh_id,from_date,to_date)
                    for i in t2_processor:
                        writer.writerow([i["processor_name"] , i["processor_id"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                        i["pounds_received"], i["pounds_delta"]])
                elif get_delivery_id2.exists() :
                    field_id = [i.ob4 for i in get_delivery_id2][0]
                    field_name = [i.field_name for i in get_delivery_id2][0]
                    warehouse_wh_id = [i.warehouse_wh_id for i in get_delivery_id2][0]
                    writer.writerow(["Origin"])
                    writer.writerow(['CROP', 'VARIETY', 'FIELD', 'GROWER', 'FARM', 'HARVEST DATE', 
                        'PROJECTED YIELD', 'ACTUAL YIELD', 'YIELD  DELTA', 'Pass / Fail Sustainability','Water Savings %',
                        'Land Use Efficiency %', 'Less GHG % ', 'Premiums to Growers %', 'CO2 EQ footprint #','Pounds of Water Per Pound Savings %'])
                    get_origin_details = get_Origin_deliveryid('COTTON',field_id,field_name,f"0{search_text}",warehouse_wh_id)
                    for i in get_Origin_Processor :
                            writer.writerow([i["get_select_crop"], i["variety"], i["field_name"], i["grower_name"], i["farm_name"], i["harvest_date"], 
                            i["projected_yeild"], i["reported_yeild"], i["yield_delta"],i["pf_sus"],i["water_savings"],i["land_use"],i["premiums_to_growers"],
                            i["co2_eQ_footprint"],i["water_per_pound_savings"]])
                    
                    writer.writerow([""])
                    writer.writerow(["Outbound 1 WIP"])
                    writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                    writer.writerow([""])
                    writer.writerow(["T1 Processor"])
                    writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                    'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                    t1_processor = t1_Processor_deliveryid('COTTON',f"0{search_text}",warehouse_wh_id,from_date,to_date)
                    for i in t1_processor:
                        writer.writerow([i["processor_name"] , i["processor_id"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                        i["pounds_received"], i["pounds_delta"]])
                    writer.writerow([""])
                    writer.writerow(["Outbound 2 WIP"])
                    writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                    writer.writerow([""])
                    writer.writerow(["T2 Processor"])
                    writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                    'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])   
                    t2_processor =  t2_Processor_deliveryid('COTTON',f"0{search_text}",warehouse_wh_id,from_date,to_date)
                    for i in t2_processor:
                        writer.writerow([i["processor_name"] , i["processor_id"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                        i["pounds_received"], i["pounds_delta"]])
                else:
                    pass                  
            else:
                pass
        else:
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    check_grower_id = [i.id for i in check_grower][0]
                    check_grower_field_crop = Field.objects.filter(crop=select_crop,grower_id=check_grower_id)
                    if check_grower_field_crop.exists() :
                        grower_field_ids = [i.id for i in check_grower_field_crop]
                        writer.writerow(["Origin"])
                        writer.writerow(['CROP', 'VARIETY', 'FIELD', 'GROWER', 'FARM', 'HARVEST DATE', 
                        'PROJECTED YIELD', 'ACTUAL YIELD', 'YIELD  DELTA', 'Pass / Fail Sustainability','Water Savings %',
                        'Land Use Efficiency %', 'Less GHG % ', 'Premiums to Growers %', 'CO2 EQ footprint #','Pounds of Water Per Pound Savings %'])
                        get_Origin_Grower = Origin_searchby_Grower(select_crop,search_text,*grower_field_ids)                                              
                        for i in get_Origin_Grower:
                            writer.writerow([i["get_select_crop"], i["variety"], i["field_name"], i["grower_name"], i["farm_name"], i["harvest_date"], 
                            i["projected_yeild"], i["reported_yeild"], i["yield_delta"],i["pf_sus"],i["water_savings"],i["land_use"],i["premiums_to_growers"],
                            i["co2_eQ_footprint"],i["water_per_pound_savings"]])
                        processor_id = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.id
                        entity_name = LinkGrowerToProcessor.objects.filter(grower_id=check_grower_id).first().processor.entity_name
                        processor_type = "T1"
                        context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)
                       
                        writer.writerow([""])
                        writer.writerow(["Outbound 1 WIP"])
                        writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                        outbound1_wip = context.get("outbound1_wip")
                        if outbound1_wip:    
                            for i in outbound1_wip:
                                writer.writerow([i["shipment_id"], i["date"], i["quantity"], i["transportation"], i["destination"]])
                        
                        writer.writerow([""])
                        writer.writerow(["T1 Processor"])
                        writer.writerow(['PROCESSOR NAME', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                        'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                        t1_processor = t1_processor = list(GrowerShipment.objects.filter(processor_id=processor_id, grower_id=check_grower_id, status="APPROVED", crop=select_crop).values("processor__entity_name","processor_id","shipment_id","sku","approval_date","grower__name","field__farm__name","field__name","total_amount","received_amount"))
                        if t1_processor:
                            for i in t1_processor:
                                writer.writerow([i["processor__entity_name"], i["shipment_id"], i["grower__name"], i["field__farm__name"], i["field__name"], i["approval_date"], i["total_amount"], 
                                                i["received_amount"], float(i["total_amount"]) - float(i["received_amount"])])
                       
                        writer.writerow([""])
                        writer.writerow(["Outbound 2 WIP"])
                        writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                        outbound2_wip = context.get("outbound2_wip") 
                        if outbound1_wip:       
                            for i in outbound2_wip:
                                writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
                        
                        writer.writerow([""])
                        writer.writerow(["T2 Processor"])
                        writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                        'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                        t2_processor = context.get("inbound2_wip")
                        if t2_processor:
                            for i in t2_processor:
                                writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                        i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                        
                        writer.writerow([""])
                        writer.writerow(["Outbound 3 WIP"])
                        writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                        outbound3_wip = context.get("outbound3_wip")
                        if outbound3_wip:        
                            for i in outbound3_wip:
                                writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
                        
                        writer.writerow([""])
                        writer.writerow(["T3 Processor"])
                        writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                        'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                        t3_processor = context.get("inbound3_wip")
                        if t3_processor:
                            for i in t3_processor:
                                writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                        i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                        
                        writer.writerow([""])
                        writer.writerow(["Outbound 4 WIP"])
                        writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                        outbound4_wip = context.get("outbound4_wip") 
                        if outbound4_wip:       
                            for i in outbound4_wip:
                                writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])

                        writer.writerow([""])
                        writer.writerow(["T4 Processor"])
                        writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                        'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                        t4_processor = context.get("inbound4_wip")
                        if t4_processor:
                            for i in t4_processor:
                                writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                        i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                            
                        writer.writerow([""])
                        writer.writerow(["Outbound 5 WIP"])
                        writer.writerow(['DELIVERY ID', 'PROCESSOR NAME', 'WAREHOUSE/CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
                        outbound5_wip = context.get("outbound5_wip") 
                        if outbound5_wip:      
                            for i in outbound5_wip:
                                writer.writerow([i["shipment_id"] ,i["processor_entity_name"], i["warehouse_name"] if i["warehouse_name"] is not None else i["customer_name"], i["date_pulled"], i["carrier_type"]])

                        writer.writerow([""])
                        writer.writerow(["Warehouse"])
                        writer.writerow(['PROCESSOR NAME', 'WAREHOUSE NAME', 'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
                        warehouse = context.get("inbound5_wip")
                        if warehouse:
                            for i in warehouse:
                                writer.writerow([i["processor_entity_name"] ,i["warehouse_name"], i["shipment_id"], i["distributor_receive_date"] 
                                        ])
                            
                        writer.writerow([""])
                        writer.writerow(["Outbound 6 WIP"])
                        writer.writerow(['DELIVERY ID', 'WAREHOUSE NAME', 'CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
                        outbound6_wip = context.get("outbound6_wip") 
                        if outbound6_wip:       
                            for i in outbound6_wip:
                                writer.writerow([i["shipment_id"] ,i["warehouse_name"], i["customer_name"], i["date_pulled"],  i["carrier_type"]])
                            
                        writer.writerow([""])
                        writer.writerow(["Customer"])
                        writer.writerow(['WAREHOUSE/PROCESSOR NAME', 'CUSTOMER NAME',  'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
                        customer = context.get("inbound6_wip")
                        if customer:
                            for i in customer:
                                writer.writerow([i["warehouse_name"] if i["warehouse_name"] is not None else i["processor_entity_name"], i["customer_name"], i["shipment_id"], i["customer_receive_date"] if i["warehouse_name"] is not None else i["distributor_receive_date"] 
                                        ])
                    else:
                        pass
                else:
                    pass
                
            # search by Field ....
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text,crop=select_crop)
                if check_field.exists() :
                    field_name = search_text
                    field_id = [i.id for i in check_field][0]
                    warehouse_wh_id = ''
                    writer.writerow(["Origin"])
                    writer.writerow(['CROP', 'VARIETY', 'FIELD', 'GROWER', 'FARM', 'HARVEST DATE', 
                    'PROJECTED YIELD', 'ACTUAL YIELD', 'YIELD  DELTA', 'Pass / Fail Sustainability','Water Savings %',
                    'Land Use Efficiency %', 'Less GHG % ', 'Premiums to Growers %', 'CO2 EQ footprint #','Pounds of Water Per Pound Savings %'])
                    get_origin_details = get_Origin_deliveryid(select_crop,field_id,field_name,'',warehouse_wh_id)
                    for i in get_origin_details:
                        writer.writerow([i["get_select_crop"], i["variety"], i["field_name"], i["grower_name"], i["farm_name"], i["harvest_date"], 
                        i["projected_yeild"], i["reported_yeild"], i["yield_delta"],i["pf_sus"],i["water_savings"],i["land_use"],i["premiums_to_growers"],
                        i["co2_eQ_footprint"],i["water_per_pound_savings"]])
                    
                    writer.writerow([""])
                    writer.writerow(["Outbound 1 WIP"])
                    writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                    outbound1_wip = outbound1_Wip_field(select_crop,search_text,from_date,to_date,field_id)
                    for i in outbound1_wip:
                        writer.writerow([i["shipment_id"], i["date"], i["quantity"], i["transportation"], i["destination"]])
                    
                    writer.writerow([""])
                    writer.writerow(["T1 Processor"])
                    writer.writerow(['PROCESSOR NAME', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                    'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                    t1_processor = t1_Processor_field(select_crop,search_text,field_id,from_date,to_date)
                    for i in t1_processor:
                        writer.writerow([i["processor_name"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                                        i["pounds_received"], i["pounds_delta"]])

                    grower_id =  check_field.first().grower.id
                    processor_id = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.id
                    entity_name = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).first().processor.entity_name
                    processor_type = "T1"
                    context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, entity_name)
                   
                    writer.writerow([""])
                    writer.writerow(["Outbound 2 WIP"])
                    writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                    outbound2_wip = context.get("outbound2_wip") 
                    if outbound1_wip:       
                        for i in outbound2_wip:
                            writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
                    
                    writer.writerow([""])
                    writer.writerow(["T2 Processor"])
                    writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                    'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                    t2_processor = context.get("inbound2_wip")
                    if t2_processor:
                        for i in t2_processor:
                            writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                    i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                    
                    writer.writerow([""])
                    writer.writerow(["Outbound 3 WIP"])
                    writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                    outbound3_wip = context.get("outbound3_wip")
                    if outbound3_wip:        
                        for i in outbound3_wip:
                            writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
                    
                    writer.writerow([""])
                    writer.writerow(["T3 Processor"])
                    writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                    'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                    t3_processor = context.get("inbound3_wip")
                    if t3_processor:
                        for i in t3_processor:
                            writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                    i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                    
                    writer.writerow([""])
                    writer.writerow(["Outbound 4 WIP"])
                    writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                    outbound4_wip = context.get("outbound4_wip") 
                    if outbound4_wip:       
                        for i in outbound4_wip:
                            writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])

                    writer.writerow([""])
                    writer.writerow(["T4 Processor"])
                    writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                    'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                    t4_processor = context.get("inbound4_wip")
                    if t4_processor:
                        for i in t4_processor:
                            writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                    i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                        
                    writer.writerow([""])
                    writer.writerow(["Outbound 5 WIP"])
                    writer.writerow(['DELIVERY ID', 'PROCESSOR NAME', 'WAREHOUSE/CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
                    outbound5_wip = context.get("outbound5_wip") 
                    if outbound5_wip:      
                        for i in outbound5_wip:
                            writer.writerow([i["shipment_id"] ,i["processor_entity_name"], i["warehouse_name"] if i["warehouse_name"] is not None else i["customer_name"], i["date_pulled"], i["carrier_type"]])

                    writer.writerow([""])
                    writer.writerow(["Warehouse"])
                    writer.writerow(['PROCESSOR NAME', 'WAREHOUSE NAME', 'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
                    warehouse = context.get("inbound5_wip")
                    if warehouse:
                        for i in warehouse:
                            writer.writerow([i["processor_entity_name"] ,i["warehouse_name"], i["shipment_id"], i["distributor_receive_date"] 
                                    ])
                        
                    writer.writerow([""])
                    writer.writerow(["Outbound 6 WIP"])
                    writer.writerow(['DELIVERY ID', 'WAREHOUSE NAME', 'CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
                    outbound6_wip = context.get("outbound6_wip") 
                    if outbound6_wip:       
                        for i in outbound6_wip:
                            writer.writerow([i["shipment_id"] ,i["warehouse_name"], i["customer_name"], i["date_pulled"],  i["carrier_type"]])
                        
                    writer.writerow([""])
                    writer.writerow(["Customer"])
                    writer.writerow(['WAREHOUSE/PROCESSOR NAME', 'CUSTOMER NAME',  'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
                    customer = context.get("inbound6_wip")
                    if customer:
                        for i in customer:
                            writer.writerow([i["warehouse_name"] if i["warehouse_name"] is not None else i["processor_entity_name"], i["customer_name"], i["shipment_id"], i["customer_receive_date"] if i["warehouse_name"] is not None else i["distributor_receive_date"] 
                                    ])
                else:
                    pass

            # search by Processor ....
            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    context = processor_traceability_report_response(select_crop, processor_id,processor_type, from_date, to_date, search_text)
                    
                    writer.writerow(["Origin"])
                    writer.writerow(['CROP', 'VARIETY', 'FIELD', 'GROWER', 'FARM', 'HARVEST DATE', 
                    'PROJECTED YIELD', 'ACTUAL YIELD', 'YIELD  DELTA', 'Pass / Fail Sustainability','Water Savings %',
                    'Land Use Efficiency %', 'Less GHG % ', 'Premiums to Growers %', 'CO2 EQ footprint #','Pounds of Water Per Pound Savings %'])
                    get_origin_details = context.get("origin_context")
                    if get_origin_details:
                        for i in get_origin_details:
                            writer.writerow([i["get_select_crop"], i["variety"], i["field_name"], i["grower_name"], i["farm_name"], i["harvest_date"], 
                            i["projected_yeild"], i["reported_yeild"], i["yield_delta"],i["pf_sus"],i["water_savings"],i["land_use"],i["premiums_to_growers"],
                            i["co2_eQ_footprint"],i["water_per_pound_savings"]])

                    writer.writerow([""])
                    writer.writerow(["Outbound 1 WIP"])
                    writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                    outbound1_wip = context.get("outbound1_wip")
                    if outbound1_wip:
                        for i in outbound1_wip:
                            writer.writerow([i["shipment_id"], i["date"], i["quantity"], i["transportation"], i["destination"]])

                    writer.writerow([""])
                    writer.writerow(["T1 Processor"])
                    writer.writerow(['PROCESSOR NAME', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                    'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                    t1_processor = context.get("t1_processor")
                    if t1_processor:
                        for i in t1_processor:
                            writer.writerow([i["processor_name"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                                        i["pounds_received"], i["pounds_delta"]])
                    
                    writer.writerow([""])
                    writer.writerow(["Outbound 2 WIP"])
                    writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                    outbound2_wip = context.get("outbound2_wip") 
                    if outbound1_wip:       
                        for i in outbound2_wip:
                            writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
                    
                    writer.writerow([""])
                    writer.writerow(["T2 Processor"])
                    writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                    'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                    t2_processor = context.get("inbound2_wip")
                    if t2_processor:
                        for i in t2_processor:
                            writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                    i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                    
                    writer.writerow([""])
                    writer.writerow(["Outbound 3 WIP"])
                    writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                    outbound3_wip = context.get("outbound3_wip")
                    if outbound3_wip:        
                        for i in outbound3_wip:
                            writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
                    
                    writer.writerow([""])
                    writer.writerow(["T3 Processor"])
                    writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                    'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                    t3_processor = context.get("inbound3_wip")
                    if t3_processor:
                        for i in t3_processor:
                            writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                    i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                    
                    writer.writerow([""])
                    writer.writerow(["Outbound 4 WIP"])
                    writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                    outbound4_wip = context.get("outbound4_wip") 
                    if outbound4_wip:       
                        for i in outbound4_wip:
                            writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])

                    writer.writerow([""])
                    writer.writerow(["T4 Processor"])
                    writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                    'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                    t4_processor = context.get("inbound4_wip")
                    if t4_processor:
                        for i in t4_processor:
                            writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                    i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                        
                    writer.writerow([""])
                    writer.writerow(["Outbound 5 WIP"])
                    writer.writerow(['DELIVERY ID', 'PROCESSOR NAME', 'WAREHOUSE/CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
                    outbound5_wip = context.get("outbound5_wip") 
                    if outbound5_wip:      
                        for i in outbound5_wip:
                            writer.writerow([i["shipment_id"] ,i["processor_entity_name"], i["warehouse_name"] if i["warehouse_name"] is not None else i["customer_name"], i["date_pulled"], i["carrier_type"]])

                    writer.writerow([""])
                    writer.writerow(["Warehouse"])
                    writer.writerow(['PROCESSOR NAME', 'WAREHOUSE NAME', 'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
                    warehouse = context.get("inbound5_wip")
                    if warehouse:
                        for i in warehouse:
                            writer.writerow([i["processor_entity_name"] ,i["warehouse_name"], i["shipment_id"], i["distributor_receive_date"] 
                                    ])
                        
                    writer.writerow([""])
                    writer.writerow(["Outbound 6 WIP"])
                    writer.writerow(['DELIVERY ID', 'WAREHOUSE NAME', 'CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
                    outbound6_wip = context.get("outbound6_wip") 
                    if outbound6_wip:       
                        for i in outbound6_wip:
                            writer.writerow([i["shipment_id"] ,i["warehouse_name"], i["customer_name"], i["date_pulled"],  i["carrier_type"]])
                        
                    writer.writerow([""])
                    writer.writerow(["Customer"])
                    writer.writerow(['WAREHOUSE/PROCESSOR NAME', 'CUSTOMER NAME',  'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
                    customer = context.get("inbound6_wip")
                    if customer:
                        for i in customer:
                            writer.writerow([i["warehouse_name"] if i["warehouse_name"] is not None else i["processor_entity_name"], i["customer_name"], i["shipment_id"], i["customer_receive_date"] if i["warehouse_name"] is not None else i["distributor_receive_date"] 
                                    ])              
                else:
                    pass
            
            # search by SKU ID......
            elif get_search_by and get_search_by == 'sku_id':
                context = skuid_traceability_response(select_crop, search_text, from_date, to_date)

                writer.writerow(["Origin"])
                writer.writerow(['CROP', 'VARIETY', 'FIELD', 'GROWER', 'FARM', 'HARVEST DATE', 
                'PROJECTED YIELD', 'ACTUAL YIELD', 'YIELD  DELTA', 'Pass / Fail Sustainability','Water Savings %',
                'Land Use Efficiency %', 'Less GHG % ', 'Premiums to Growers %', 'CO2 EQ footprint #','Pounds of Water Per Pound Savings %'])
                get_origin_details = context.get("origin_context")
                if get_origin_details:
                    for i in get_origin_details:
                        writer.writerow([i["get_select_crop"], i["variety"], i["field_name"], i["grower_name"], i["farm_name"], i["harvest_date"], 
                        i["projected_yeild"], i["reported_yeild"], i["yield_delta"],i["pf_sus"],i["water_savings"],i["land_use"],i["premiums_to_growers"],
                        i["co2_eQ_footprint"],i["water_per_pound_savings"]])

                writer.writerow([""])
                writer.writerow(["Outbound 1 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound1_wip = context.get("outbound1_wip")
                if outbound1_wip:
                    for i in outbound1_wip:
                        writer.writerow([i["shipment_id"], i["date"], i["quantity"], i["transportation"], i["destination"]])

                writer.writerow([""])
                writer.writerow(["T1 Processor"])
                writer.writerow(['PROCESSOR NAME', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t1_processor = context.get("t1_processor")
                if t1_processor:
                    for i in t1_processor:
                        writer.writerow([i["processor_name"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                                    i["pounds_received"], i["pounds_delta"]])
                
                writer.writerow([""])
                writer.writerow(["Outbound 2 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound2_wip = context.get("outbound2_wip") 
                if outbound1_wip:       
                    for i in outbound2_wip:
                        writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
                
                writer.writerow([""])
                writer.writerow(["T2 Processor"])
                writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t2_processor = context.get("inbound2_wip")
                if t2_processor:
                    for i in t2_processor:
                        writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                
                writer.writerow([""])
                writer.writerow(["Outbound 3 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound3_wip = context.get("outbound3_wip")
                if outbound3_wip:        
                    for i in outbound3_wip:
                        writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
                
                writer.writerow([""])
                writer.writerow(["T3 Processor"])
                writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t3_processor = context.get("inbound3_wip")
                if t3_processor:
                    for i in t3_processor:
                        writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                
                writer.writerow([""])
                writer.writerow(["Outbound 4 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound4_wip = context.get("outbound4_wip") 
                if outbound4_wip:       
                    for i in outbound4_wip:
                        writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])

                writer.writerow([""])
                writer.writerow(["T4 Processor"])
                writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t4_processor = context.get("inbound4_wip")
                if t4_processor:
                    for i in t4_processor:
                        writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                    
                writer.writerow([""])
                writer.writerow(["Outbound 5 WIP"])
                writer.writerow(['DELIVERY ID', 'PROCESSOR NAME', 'WAREHOUSE/CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
                outbound5_wip = context.get("outbound5_wip") 
                if outbound5_wip:      
                    for i in outbound5_wip:
                        writer.writerow([i["shipment_id"] ,i["processor_entity_name"], i["warehouse_name"] if i["warehouse_name"] is not None else i["customer_name"], i["date_pulled"], i["carrier_type"]])

                writer.writerow([""])
                writer.writerow(["Warehouse"])
                writer.writerow(['PROCESSOR NAME', 'WAREHOUSE NAME', 'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
                warehouse = context.get("inbound5_wip")
                if warehouse:
                    for i in warehouse:
                        writer.writerow([i["processor_entity_name"] ,i["warehouse_name"], i["shipment_id"], i["distributor_receive_date"] 
                                ])
                    
                writer.writerow([""])
                writer.writerow(["Outbound 6 WIP"])
                writer.writerow(['DELIVERY ID', 'WAREHOUSE NAME', 'CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
                outbound6_wip = context.get("outbound6_wip") 
                if outbound6_wip:       
                    for i in outbound6_wip:
                        writer.writerow([i["shipment_id"] ,i["warehouse_name"], i["customer_name"], i["date_pulled"],  i["carrier_type"]])
                    
                writer.writerow([""])
                writer.writerow(["Customer"])
                writer.writerow(['WAREHOUSE/PROCESSOR NAME', 'CUSTOMER NAME',  'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
                customer = context.get("inbound6_wip")
                if customer:
                    for i in customer:
                        writer.writerow([i["warehouse_name"] if i["warehouse_name"] is not None else i["processor_entity_name"], i["customer_name"], i["shipment_id"], i["customer_receive_date"] if i["warehouse_name"] is not None else i["distributor_receive_date"] 
                                ])

            # search by Delivery ID ....
            elif get_search_by and get_search_by == 'deliveryid' :
                context = {}
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text, crop=select_crop)
                        
                if check_shipment.exists() :
                    get_shipment = check_shipment.first()
                    sku_id = get_shipment.sku
                    context = skuid_traceability_response(select_crop, sku_id, from_date, to_date)                    

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).exists():
                    get_shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).first()
                    
                    if get_shipment and not get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_send 
                        context = skuid_traceability_response(select_crop, sku_id, from_date, to_date)                                              

                    elif get_shipment and get_shipment.receiver_processor_type == "T4":
                        sku_id = get_shipment.storage_bin_recive 
                        context = skuid_traceability_response(select_crop, sku_id, from_date, to_date)
                                             
                    else:
                        context['no_rec_found_msg'] = "No Records Found"

                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).exists():
                    
                    shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                    for shipment in shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    get_shipment = shipments.first()
                    if get_shipment["warehouse_id"] not in [None, "null", "", " "]:
                        inbound5 = list(shipments)
                        context["inbound5_wip"] = inbound5
                        context["outbound5_wip"] = inbound5
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                        outbound6 = []
                        for crop in crops:                          
                            if WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).exists():
                                shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], warehouse_shipment_crop__crop=crop.crop, warehouse_shipment_crop__crop_type=crop.crop_type).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                                for shipment in shipments:
                                    if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id  
                                outbound6.extend(list(shipments))
                        context["outbound6_wip"] = outbound6
                        context["inbound6_wip"] = outbound6
                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                            
                            del return_context["inbound5_wip"]
                            del return_context["inbound6_wip"]
                            del return_context["outbound5_wip"]
                            del return_context["outbound6_wip"]
                            
                            keys_to_extend = [
                                "origin_context",
                                "t1_processor",
                                "inbound2_wip",
                                "inbound3_wip",
                                "inbound4_wip",
                                "outbound2_wip",
                                "outbound3_wip",
                                "outbound4_wip",
                            ]

                            for key in keys_to_extend:
                                if return_context.get(key):
                                    context[key] = context.get(key, [])
                                    context[key].extend(return_context[key])                                      
                        
                    else:
                        inbound6 = shipments
                        context["inbound6_wip"] = inbound6
                        context["outbound5_wip"] = inbound6
                        context["inbound5_wip"] = []
                        context["outbound6_wip"] = []
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])

                        processor_entity_name = get_shipment["processor_entity_name"]
                        processor_id = get_shipment["processor_id"]
                        processor_type = get_shipment["processor_type"]
                        for crop in crops:
                            select_crop = crop.crop
                            return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                            del return_context["inbound5_wip"]
                            del return_context["inbound6_wip"]
                            del return_context["outbound5_wip"]
                            del return_context["outbound6_wip"]
                            keys_to_extend = [
                                "origin_context",
                                "t1_processor",
                                "inbound2_wip",
                                "inbound3_wip",
                                "inbound4_wip",
                                "outbound2_wip",
                                "outbound3_wip",
                                "outbound4_wip",
                            ]

                            for key in keys_to_extend:
                                if return_context.get(key):
                                    context[key] = context.get(key, [])
                                    context[key].extend(return_context[key])                                      
                        
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).exists():
                    shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id" ,"customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
                    for shipment in shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                    get_shipment = shipments.first()
                    context["inbound6_wip"] = list(shipments)
                    context["outbound6_wip"] = list(shipments)
                    crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
                    outbound5_processor = []
                    for crop in crops:
                        select_crop = crop.crop
                        check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id","processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
                        if check_processor_shipment:
                                for shipment in check_processor_shipment:
                                    if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                                        shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                                    
                                    carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                                    shipment["carrier_id"] = carrier.carrier_id                                 

                                outbound5_processor.extend(check_processor_shipment) 
                                processor_entity_name = shipment["processor_entity_name"]
                                processor_id = shipment["processor_id"]
                                processor_type = shipment["processor_type"]                             
                                return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                                del return_context["inbound5_wip"]
                                del return_context["inbound6_wip"]
                                del return_context["outbound5_wip"]
                                del return_context["outbound6_wip"]
                                keys_to_extend = [
                                    "origin_context",
                                    "t1_processor",
                                    "inbound2_wip",
                                    "inbound3_wip",
                                    "inbound4_wip",
                                    "outbound2_wip",
                                    "outbound3_wip",
                                    "outbound4_wip",
                                ]

                                for key in keys_to_extend:
                                    if return_context.get(key):
                                        context[key] = context.get(key, [])
                                        context[key].extend(return_context[key])                                      

                    context["outbound5_wip"] = outbound5_processor
                    context["inbound5_wip"] = outbound5_processor                       
                
                writer.writerow(["Origin"])
                writer.writerow(['CROP', 'VARIETY', 'FIELD', 'GROWER', 'FARM', 'HARVEST DATE', 
                'PROJECTED YIELD', 'ACTUAL YIELD', 'YIELD  DELTA', 'Pass / Fail Sustainability','Water Savings %',
                'Land Use Efficiency %', 'Less GHG % ', 'Premiums to Growers %', 'CO2 EQ footprint #','Pounds of Water Per Pound Savings %'])
                get_origin_details = context.get("origin_context")
                if get_origin_details:
                    for i in get_origin_details:
                        writer.writerow([i["get_select_crop"], i["variety"], i["field_name"], i["grower_name"], i["farm_name"], i["harvest_date"], 
                        i["projected_yeild"], i["reported_yeild"], i["yield_delta"],i["pf_sus"],i["water_savings"],i["land_use"],i["premiums_to_growers"],
                        i["co2_eQ_footprint"],i["water_per_pound_savings"]])

                writer.writerow([""])
                writer.writerow(["Outbound 1 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound1_wip = context.get("outbound1_wip")
                if outbound1_wip:
                    for i in outbound1_wip:
                        writer.writerow([i["shipment_id"], i["date"], i["quantity"], i["transportation"], i["destination"]])

                writer.writerow([""])
                writer.writerow(["T1 Processor"])
                writer.writerow(['PROCESSOR NAME', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t1_processor = context.get("t1_processor")
                if t1_processor:
                    for i in t1_processor:
                        writer.writerow([i["processor_name"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                                    i["pounds_received"], i["pounds_delta"]])
                
                writer.writerow([""])
                writer.writerow(["Outbound 2 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound2_wip = context.get("outbound2_wip") 
                if outbound1_wip:       
                    for i in outbound2_wip:
                        writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
                
                writer.writerow([""])
                writer.writerow(["T2 Processor"])
                writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t2_processor = context.get("inbound2_wip")
                if t2_processor:
                    for i in t2_processor:
                        writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                
                writer.writerow([""])
                writer.writerow(["Outbound 3 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound3_wip = context.get("outbound3_wip")
                if outbound3_wip:        
                    for i in outbound3_wip:
                        writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
                
                writer.writerow([""])
                writer.writerow(["T3 Processor"])
                writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t3_processor = context.get("inbound3_wip")
                if t3_processor:
                    for i in t3_processor:
                        writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                
                writer.writerow([""])
                writer.writerow(["Outbound 4 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound4_wip = context.get("outbound4_wip") 
                if outbound4_wip:       
                    for i in outbound4_wip:
                        writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])

                writer.writerow([""])
                writer.writerow(["T4 Processor"])
                writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t4_processor = context.get("inbound4_wip")
                if t4_processor:
                    for i in t4_processor:
                        writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                    
                writer.writerow([""])
                writer.writerow(["Outbound 5 WIP"])
                writer.writerow(['DELIVERY ID', 'PROCESSOR NAME', 'WAREHOUSE/CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
                outbound5_wip = context.get("outbound5_wip") 
                if outbound5_wip:      
                    for i in outbound5_wip:
                        writer.writerow([i["shipment_id"] ,i["processor_entity_name"], i["warehouse_name"] if i["warehouse_name"] is not None else i["customer_name"], i["date_pulled"], i["carrier_type"]])

                writer.writerow([""])
                writer.writerow(["Warehouse"])
                writer.writerow(['PROCESSOR NAME', 'WAREHOUSE NAME', 'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
                warehouse = context.get("inbound5_wip")
                if warehouse:
                    for i in warehouse:
                        writer.writerow([i["processor_entity_name"] ,i["warehouse_name"], i["shipment_id"], i["distributor_receive_date"] 
                                ])
                    
                writer.writerow([""])
                writer.writerow(["Outbound 6 WIP"])
                writer.writerow(['DELIVERY ID', 'WAREHOUSE NAME', 'CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
                outbound6_wip = context.get("outbound6_wip") 
                if outbound6_wip:       
                    for i in outbound6_wip:
                        writer.writerow([i["shipment_id"] ,i["warehouse_name"], i["customer_name"], i["date_pulled"],  i["carrier_type"]])
                    
                writer.writerow([""])
                writer.writerow(["Customer"])
                writer.writerow(['WAREHOUSE/PROCESSOR NAME', 'CUSTOMER NAME',  'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
                customer = context.get("inbound6_wip")
                if customer:
                    for i in customer:
                        writer.writerow([i["warehouse_name"] if i["warehouse_name"] is not None else i["processor_entity_name"], i["customer_name"], i["shipment_id"], i["customer_receive_date"] if i["warehouse_name"] is not None else i["distributor_receive_date"] 
                                ])
           
            # search by Warehouse....
            elif get_search_by and get_search_by == 'warehouse':
                context = {}
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                   
                    warehouse = check_warehouse.first()                    
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(processor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status"))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    context["inbound5_wip"] = inbound5

                    outbound6 = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id","shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    for shipment in outbound6:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    context["outbound6_wip"] = outbound6
                    
                    context["inbound6_wip"] = outbound6
                    context["outbound5_wip"] = inbound5
                    for shipment in inbound5:
                        processor_id = shipment["processor_id"]
                        processor_type = shipment["processor_type"]
                        processor_entity_name = shipment["processor_entity_name"]
                        return_context = processor_traceability_report_response(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                        del return_context["inbound5_wip"]
                        del return_context["inbound6_wip"]
                        del return_context["outbound5_wip"]
                        del return_context["outbound6_wip"]
                        keys_to_extend = [
                            "origin_context",
                            "t1_processor",
                            "inbound2_wip",
                            "inbound3_wip",
                            "inbound4_wip",
                            "outbound2_wip",
                            "outbound3_wip",
                            "outbound4_wip",
                        ]

                        for key in keys_to_extend:
                            if return_context.get(key):
                                context[key] = context.get(key, [])
                                context[key].extend(return_context[key])                                            
                        
                else:
                    context['no_rec_found_msg'] = "No Records Found"

                writer.writerow(["Origin"])
                writer.writerow(['CROP', 'VARIETY', 'FIELD', 'GROWER', 'FARM', 'HARVEST DATE', 
                'PROJECTED YIELD', 'ACTUAL YIELD', 'YIELD  DELTA', 'Pass / Fail Sustainability','Water Savings %',
                'Land Use Efficiency %', 'Less GHG % ', 'Premiums to Growers %', 'CO2 EQ footprint #','Pounds of Water Per Pound Savings %'])
                get_origin_details = context.get("origin_context")
                if get_origin_details:
                    for i in get_origin_details:
                        writer.writerow([i["get_select_crop"], i["variety"], i["field_name"], i["grower_name"], i["farm_name"], i["harvest_date"], 
                        i["projected_yeild"], i["reported_yeild"], i["yield_delta"],i["pf_sus"],i["water_savings"],i["land_use"],i["premiums_to_growers"],
                        i["co2_eQ_footprint"],i["water_per_pound_savings"]])

                writer.writerow([""])
                writer.writerow(["Outbound 1 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound1_wip = context.get("outbound1_wip")
                if outbound1_wip:
                    for i in outbound1_wip:
                        writer.writerow([i["shipment_id"], i["date"], i["quantity"], i["transportation"], i["destination"]])

                writer.writerow([""])
                writer.writerow(["T1 Processor"])
                writer.writerow(['PROCESSOR NAME', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t1_processor = context.get("t1_processor")
                if t1_processor:
                    for i in t1_processor:
                        writer.writerow([i["processor_name"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                                    i["pounds_received"], i["pounds_delta"]])
                
                writer.writerow([""])
                writer.writerow(["Outbound 2 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound2_wip = context.get("outbound2_wip") 
                if outbound1_wip:       
                    for i in outbound2_wip:
                        writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
                
                writer.writerow([""])
                writer.writerow(["T2 Processor"])
                writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t2_processor = context.get("inbound2_wip")
                if t2_processor:
                    for i in t2_processor:
                        writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                
                writer.writerow([""])
                writer.writerow(["Outbound 3 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound3_wip = context.get("outbound3_wip")
                if outbound3_wip:        
                    for i in outbound3_wip:
                        writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
                
                writer.writerow([""])
                writer.writerow(["T3 Processor"])
                writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t3_processor = context.get("inbound3_wip")
                if t3_processor:
                    for i in t3_processor:
                        writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                
                writer.writerow([""])
                writer.writerow(["Outbound 4 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound4_wip = context.get("outbound4_wip") 
                if outbound4_wip:       
                    for i in outbound4_wip:
                        writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])

                writer.writerow([""])
                writer.writerow(["T4 Processor"])
                writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t4_processor = context.get("inbound4_wip")
                if t4_processor:
                    for i in t4_processor:
                        writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                    
                writer.writerow([""])
                writer.writerow(["Outbound 5 WIP"])
                writer.writerow(['DELIVERY ID', 'PROCESSOR NAME', 'WAREHOUSE/CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
                outbound5_wip = context.get("outbound5_wip") 
                if outbound5_wip:      
                    for i in outbound5_wip:
                        writer.writerow([i["shipment_id"] ,i["processor_entity_name"], i["warehouse_name"] if i["warehouse_name"] is not None else i["customer_name"], i["date_pulled"], i["carrier_type"]])

                writer.writerow([""])
                writer.writerow(["Warehouse"])
                writer.writerow(['PROCESSOR NAME', 'WAREHOUSE NAME', 'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
                warehouse = context.get("inbound5_wip")
                if warehouse:
                    for i in warehouse:
                        writer.writerow([i["processor_entity_name"] ,i["warehouse_name"], i["shipment_id"], i["distributor_receive_date"] 
                                ])
                    
                writer.writerow([""])
                writer.writerow(["Outbound 6 WIP"])
                writer.writerow(['DELIVERY ID', 'WAREHOUSE NAME', 'CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
                outbound6_wip = context.get("outbound6_wip") 
                if outbound6_wip:       
                    for i in outbound6_wip:
                        writer.writerow([i["shipment_id"] ,i["warehouse_name"], i["customer_name"], i["date_pulled"],  i["carrier_type"]])
                    
                writer.writerow([""])
                writer.writerow(["Customer"])
                writer.writerow(['WAREHOUSE/PROCESSOR NAME', 'CUSTOMER NAME',  'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
                customer = context.get("inbound6_wip")
                if customer:
                    for i in customer:
                        writer.writerow([i["warehouse_name"] if i["warehouse_name"] is not None else i["processor_entity_name"], i["customer_name"], i["shipment_id"], i["customer_receive_date"] if i["warehouse_name"] is not None else i["distributor_receive_date"] 
                                ])
            
            # search by Customer....
            elif get_search_by and get_search_by == 'customer':
                print('this function called')
                context = {}
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()
                    inbound6 = []
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in processor_shipments:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(processor_shipments)

                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop, 
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    for shipment in warehouse_shipments:
                        if WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = WarehouseShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    inbound6.extend(warehouse_shipments)

                    context["inbound6_wip"] = inbound6
                    context["outbound6_wip"] = warehouse_shipments

                    warehouse_ids = [shipment["warehouse_id"] for shipment in warehouse_shipments]
                    inbound5 = list(ProcessorWarehouseShipment.objects.filter(
                        processor_shipment_crop__crop=select_crop,
                        warehouse_id__in=warehouse_ids,
                        date_pulled__date__gte=from_date,
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in inbound5:
                        if ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).exists():
                            shipment["new_lot_number"] = ProcessorShipmentLotNumberTracking.objects.filter(shipment_id=shipment["id"]).last().additional_lot_number
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  
                    context["inbound5_wip"] = inbound5
                    outbound5 = inbound5 + processor_shipments
                    context["outbound5_wip"] = outbound5

                    for shipment in outbound5:
                        processor_id = shipment.get("processor_id")
                        processor_type = shipment.get("processor_type")
                        processor_entity_name = shipment.get("processor_entity_name")
                        
                        return_context = processor_traceability_report_response(
                            select_crop, processor_id, processor_type, 
                            from_date, to_date, processor_entity_name
                        )
                        del return_context["inbound5_wip"]
                        del return_context["inbound6_wip"]
                        del return_context["outbound5_wip"]
                        del return_context["outbound6_wip"]
                        keys_to_extend = [
                            "origin_context",
                            "t1_processor",
                            "inbound2_wip",
                            "inbound3_wip",
                            "inbound4_wip",
                            "outbound2_wip",
                            "outbound3_wip",
                            "outbound4_wip",
                        ]

                        for key in keys_to_extend:
                            if return_context.get(key):
                                context[key] = context.get(key, [])
                                context[key].extend(return_context[key])                                      
                    
                        new_context_ = location_response(context)                           
                        context.update(new_context_)                                    
                            
                else:
                    context['no_rec_found_msg'] = "No Records Found"
                
                
                writer.writerow(["Origin"])
                writer.writerow(['CROP', 'VARIETY', 'FIELD', 'GROWER', 'FARM', 'HARVEST DATE', 
                'PROJECTED YIELD', 'ACTUAL YIELD', 'YIELD  DELTA', 'Pass / Fail Sustainability','Water Savings %',
                'Land Use Efficiency %', 'Less GHG % ', 'Premiums to Growers %', 'CO2 EQ footprint #','Pounds of Water Per Pound Savings %'])
                get_origin_details = context.get("origin_context")
                if get_origin_details:
                    for i in get_origin_details:
                        writer.writerow([i["get_select_crop"], i["variety"], i["field_name"], i["grower_name"], i["farm_name"], i["harvest_date"], 
                        i["projected_yeild"], i["reported_yeild"], i["yield_delta"],i["pf_sus"],i["water_savings"],i["land_use"],i["premiums_to_growers"],
                        i["co2_eQ_footprint"],i["water_per_pound_savings"]])

                writer.writerow([""])
                writer.writerow(["Outbound 1 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound1_wip = context.get("outbound1_wip")
                if outbound1_wip:
                    for i in outbound1_wip:
                        writer.writerow([i["shipment_id"], i["date"], i["quantity"], i["transportation"], i["destination"]])

                writer.writerow([""])
                writer.writerow(["T1 Processor"])
                writer.writerow(['PROCESSOR NAME', 'DELIVERY ID', 'Grower', 'Farm', 'Field', 'DATE', 'QUANTITY POUNDS SHIPPED', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t1_processor = context.get("t1_processor")
                if t1_processor:
                    for i in t1_processor:
                        writer.writerow([i["processor_name"], i["shipment_id"], i["grower"], i["farm"], i["field"], i["date"], i["pounds_shipped"], 
                                    i["pounds_received"], i["pounds_delta"]])
                
                writer.writerow([""])
                writer.writerow(["Outbound 2 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound2_wip = context.get("outbound2_wip") 
                if outbound1_wip:       
                    for i in outbound2_wip:
                        writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
                
                writer.writerow([""])
                writer.writerow(["T2 Processor"])
                writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t2_processor = context.get("inbound2_wip")
                if t2_processor:
                    for i in t2_processor:
                        writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                
                writer.writerow([""])
                writer.writerow(["Outbound 3 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound3_wip = context.get("outbound3_wip")
                if outbound3_wip:        
                    for i in outbound3_wip:
                        writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])
                
                writer.writerow([""])
                writer.writerow(["T3 Processor"])
                writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t3_processor = context.get("inbound3_wip")
                if t3_processor:
                    for i in t3_processor:
                        writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                
                writer.writerow([""])
                writer.writerow(["Outbound 4 WIP"])
                writer.writerow(['DELIVERY ID OUTBOUND', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'DESTINATION'])
                outbound4_wip = context.get("outbound4_wip") 
                if outbound4_wip:       
                    for i in outbound4_wip:
                        writer.writerow([i["shipment_id"] , i["storage_bin_send"], i["date_pulled"], i["volume_shipped"], i["equipment_type"], i["processor2_name"]])

                writer.writerow([""])
                writer.writerow(["T4 Processor"])
                writer.writerow(['PROCESSOR NAME', 'PROCESSOR ID #', 'DELIVERY ID', 'SENDER SKU ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'RECEIVER PROCESSOR', 'RECEIVER SKU ID', 
                'QUANTITY POUNDS RECEIVED', 'QUANTITY DELTA'])
                t4_processor = context.get("inbound4_wip")
                if t4_processor:
                    for i in t4_processor:
                        writer.writerow([i["processor_e_name"] , i["processor_idd"], i["shipment_id"], i["storage_bin_send"],  i["recive_delivery_date"], i["volume_shipped"], i["processor2_name"], i["storage_bin_recive"],
                                i["received_weight"], float(i["volume_shipped"]) - float(i["received_weight"])])
                    
                writer.writerow([""])
                writer.writerow(["Outbound 5 WIP"])
                writer.writerow(['DELIVERY ID', 'PROCESSOR NAME', 'WAREHOUSE/CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
                outbound5_wip = context.get("outbound5_wip") 
                if outbound5_wip:      
                    for i in outbound5_wip:
                        writer.writerow([i["shipment_id"] ,i["processor_entity_name"], i["warehouse_name"] if i["warehouse_name"] is not None else i["customer_name"], i["date_pulled"], i["carrier_type"]])

                writer.writerow([""])
                writer.writerow(["Warehouse"])
                writer.writerow(['PROCESSOR NAME', 'WAREHOUSE NAME', 'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
                warehouse = context.get("inbound5_wip")
                if warehouse:
                    for i in warehouse:
                        writer.writerow([i["processor_entity_name"] ,i["warehouse_name"], i["shipment_id"], i["distributor_receive_date"] 
                                ])
                    
                writer.writerow([""])
                writer.writerow(["Outbound 6 WIP"])
                writer.writerow(['DELIVERY ID', 'WAREHOUSE NAME', 'CUSTOMER NAME', 'DATE', 'QUANTITY POUNDS', 'TRANSPORTATION MODE (RAIL OR TRUCK)', 'PER UNIT RATE'])
                outbound6_wip = context.get("outbound6_wip") 
                if outbound6_wip:       
                    for i in outbound6_wip:
                        writer.writerow([i["shipment_id"] ,i["warehouse_name"], i["customer_name"], i["date_pulled"],  i["carrier_type"]])
                    
                writer.writerow([""])
                writer.writerow(["Customer"])
                writer.writerow(['WAREHOUSE/PROCESSOR NAME', 'CUSTOMER NAME',  'DELIVERY ID', 'DATE', 'QUANTITY POUNDS SHIPPED', 'PER UNIT PRICE'])
                customer = context.get("inbound6_wip")
                if customer:
                    for i in customer:
                        writer.writerow([i["warehouse_name"] if i["warehouse_name"] is not None else i["processor_entity_name"], i["customer_name"], i["shipment_id"], i["customer_receive_date"] if i["warehouse_name"] is not None else i["distributor_receive_date"] 
                                ])
                 
            else:
                pass
        return response
    else:
        return redirect ('dashboard')
 

def transport_list(request):
    outbound2_wip = [
        {'shipment_id': 'ABC123', 'origin_lat': 40.7128, 'origin_lng': -74.0060, 'destination_lat': 34.0522, 'destination_lng': -80.2437},
        {'shipment_id': 'DEF456', 'origin_lat': 34.0522, 'origin_lng': -76.2437, 'destination_lat': 41.8781, 'destination_lng': -87.6298},
        # Add more demo data as needed
    ]

    # Demo data for outbound3_wip
    outbound3_wip = [
        {'shipment_id': 'GHI789', 'origin_lat': 37.7749, 'origin_lng': -122.4194, 'destination_lat': 40.7128, 'destination_lng': -74.0060},
        # Add more demo data as needed
    ]

    # Demo data for outbound4_wip
    outbound4_wip = [
        {'shipment_id': 'JKL101', 'origin_lat': 41.8781, 'origin_lng': -87.6298, 'destination_lat': 37.7749, 'destination_lng': -82.4194},
        # Add more demo data as needed
    ]

    # Pass the demo data to your template
    context = {
        'outbound2_wip': outbound2_wip,
        'outbound3_wip': outbound3_wip,
        'outbound4_wip': outbound4_wip,
    }
    return render(request, 'tracemodule/traceability_map_show.html', context)
    

def shipmentid_response(search_text, from_date, to_date):
    new_context = {}
    check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text)
                        
    if check_shipment.exists() :
        
        get_shipment = check_shipment.values().first()            
        select_crop = get_shipment["crop"]
        context = shipmentid_traceability_response(select_crop, get_shipment["shipment_id"], from_date, to_date)
        new_context.update(context)

    elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text).exists():
        
        shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text)
        get_shipment = shipment.values().first()       
        select_crop = get_shipment["crop"]        
        context = shipmentid_traceability_response(select_crop, get_shipment["shipment_id"], from_date, to_date)
          
        new_context.update(context)

    elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text).exists():
       
        shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id" ,"processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
        
        for shipment in shipments:
            crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

            # Add crops and their additional lot numbers to the shipment
            shipment["crops"] = []
            for crop in crops:
                
                additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
                    shipment_id=shipment["id"],
                    crop_id=crop["id"]
                ).order_by("-id").values("additional_lot_number").first()

                shipment["crops"].append({
                    "crop_name": crop["crop"],
                    "lot_number": crop["lot_number"],
                    "net_weight": crop["net_weight"],
                    "weight_unit": crop["weight_unit"],
                    "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                })
            carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
            shipment["carrier_id"] = carrier.carrier_id  
        get_shipment = shipments.first()
        if get_shipment["warehouse_id"] not in [None, "null", "", " "]:
            shipments = get_unique_shipments_by_id(shipments)
            inbound5 = list(shipments)
            new_context["inbound5_wip"] = inbound5
            new_context["outbound5_wip"] = inbound5
            crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])           
            
            processor_entity_name = get_shipment["processor_entity_name"]
            processor_id = get_shipment["processor_id"]
            processor_type = get_shipment["processor_type"]
            for crop in crops:
                select_crop = crop.crop
                return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                
                keys_to_extend = [
                    "origin_context",
                    "t1_processor",
                    "inbound2_wip",
                    "inbound3_wip",
                    "inbound4_wip",
                    "outbound2_wip",
                    "outbound3_wip",
                    "outbound4_wip",
                ]

                for key in keys_to_extend:
                    if return_context.get(key):
                        new_context[key] = new_context.get(key, [])
                        new_context[key].extend(return_context[key])                                    
            
               
        else:
            shipments = get_unique_shipments_by_id(shipments)
            inbound6 = shipments
            new_context["inbound6_wip"] = inbound6
            new_context["outbound5_wip"] = inbound6
            new_context["inbound5_wip"] = []
            new_context["outbound6_wip"] = []

            crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])

            processor_entity_name = get_shipment["processor_entity_name"]
            processor_id = get_shipment["processor_id"]
            processor_type = get_shipment["processor_type"]
            for crop in crops:
                select_crop = crop.crop
                return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                
                keys_to_extend = [
                    "origin_context",
                    "t1_processor",
                    "inbound2_wip",
                    "inbound3_wip",
                    "inbound4_wip",
                    "outbound2_wip",
                    "outbound3_wip",
                    "outbound4_wip",
                ]

                for key in keys_to_extend:
                    if return_context.get(key):
                        new_context[key] = new_context.get(key, [])
                        new_context[key].extend(return_context[key])                                      
    
    elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text).exists():
        
        shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
        
        for shipment in shipments:
            shipment_crops = WarehouseShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

            # Add crops and their additional lot numbers to the shipment
            shipment["crops"] = []
            for crop_ in shipment_crops:
                
                additional_lot = WarehouseShipmentLotNumberTracking.objects.filter(
                    shipment_id=shipment["id"],
                    crop_id=crop_["id"]
                ).order_by("-id").values("additional_lot_number").first()

                shipment["crops"].append({
                    "crop_name": crop_["crop"],
                    "lot_number": crop_["lot_number"],
                    "net_weight": crop_["net_weight"],
                    "weight_unit": crop_["weight_unit"],
                    "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                })
            carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
            shipment["carrier_id"] = carrier.carrier_id  

        get_shipment = shipments.first()
        shipments = get_unique_shipments_by_id(shipments)
        new_context["inbound6_wip"] = list(shipments)
        new_context["outbound6_wip"] = list(shipments)
        crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
        outbound5_processor = []
        for crop in crops:
            select_crop = crop.crop
            check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
            if check_processor_shipment:
                check_processor_shipment = get_unique_shipments_by_id(check_processor_shipment)
                for shipment in check_processor_shipment:                   
                    shipment_crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

                    # Add crops and their additional lot numbers to the shipment
                    shipment["crops"] = []
                    for crop_ in shipment_crops:
                        
                        additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
                            shipment_id=shipment["id"],
                            crop_id=crop_["id"]
                        ).order_by("-id").values("additional_lot_number").first()

                        shipment["crops"].append({
                            "crop_name": crop_["crop"],
                            "lot_number": crop_["lot_number"],
                            "net_weight": crop_["net_weight"],
                            "weight_unit": crop_["weight_unit"],
                            "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                        })
                    carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                    shipment["carrier_id"] = carrier.carrier_id  
                    outbound5_processor.extend(check_processor_shipment) 
                    processor_entity_name = shipment["processor_entity_name"]
                    processor_id = shipment["processor_id"]
                    processor_type = shipment["processor_type"]                             
                    return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                    
                    keys_to_extend = [
                        "origin_context",
                        "t1_processor",
                        "inbound2_wip",
                        "inbound3_wip",
                        "inbound4_wip",
                        "outbound2_wip",
                        "outbound3_wip",
                        "outbound4_wip",
                    ]

                    for key in keys_to_extend:
                        if return_context.get(key):
                            new_context[key] = new_context.get(key, [])
                            new_context[key].extend(return_context[key])                                   
                
        new_context["outbound5_wip"] = outbound5_processor
        new_context["inbound5_wip"] = outbound5_processor 

    return new_context


@login_required()
def traceability_report(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        crops = Crop.objects.all()
        context["crops"] = crops
        grower_shipments = GrowerShipment.objects.filter(status="APPROVED").values(
            'id', 'date_time', 'shipment_id', 'grower__name', 'grower_id',
            'processor__id', 'processor__entity_name', 'approval_date', 'status', 'crop', 'received_amount', 'unit_type'
        ).annotate(
            date_field=F('date_time'),
            shipment_type=Value('GrowerShipment', output_field=CharField()),
            location=Case(
                When(
                    status="APPROVED",
                    then=Subquery(
                        Location.objects.filter(
                            processor_id=Cast(OuterRef('processor__id'), output_field=BigIntegerField())
                        ).values('name')[:1]
                    )
                ),
                When(
                    status="DISAPPROVED",
                    then=Subquery(
                        Grower.objects.filter(
                            id=Cast(OuterRef('grower_id'), output_field=BigIntegerField())
                        ).values('physical_address1')[:1]
                    )
                ),
                default=Value("In Transit"), output_field=CharField(),
            )
        )

        # Optimized processor shipments
        processor_shipments = ShipmentManagement.objects.filter(status="APPROVED").values(
            'id', 'date_pulled', 'shipment_id', 'processor_idd', 'processor_e_name',
            'sender_processor_type', 'processor2_idd', 'processor2_name', 'recive_delivery_date', 'crop', 'status', 'lot_number', 'received_weight', 'weight_of_product_unit'
        ).annotate(
            date_field=F('date_pulled'),
            shipment_type=Value('ShipmentManagement', output_field=CharField()),
            location=Case(
                When(
                    status="APPROVED",
                    then=Subquery(
                        Processor2Location.objects.filter(
                            processor_id=Cast(OuterRef('processor2_idd'), output_field=BigIntegerField())
                        ).values('name')[:1]
                    )
                ),
                When(
                    status="DISAPPROVED",
                    then=Case(
                        When(
                            sender_processor_type="T1",
                            then=Subquery(
                                Location.objects.filter(
                                    processor_id=Cast(OuterRef('processor_idd'), output_field=BigIntegerField())
                                ).values('name')[:1]
                            )
                        ),
                        default=Subquery(
                            Processor2Location.objects.filter(
                                processor_id=Cast(OuterRef('processor2_idd'), output_field=BigIntegerField())
                            ).values('name')[:1]
                        )
                    )
                ),
                default=Value("In Transit"), output_field=CharField(),
            )
        )

        # Optimized contract processor shipments
        contract_processor_shipments = ProcessorWarehouseShipment.objects.values(
            'id', 'date_pulled', 'shipment_id', 'processor_id', 'processor_entity_name', 'warehouse_id', 'warehouse_name',
            'customer_id', 'customer_name', 'status', 'distributor_receive_date'
        ).annotate(
            date_field=F('date_pulled'),
            shipment_type=Value('ProcessorWarehouseShipment', output_field=CharField()),
            location=Case(
                When(
                    status="Received",
                    then=Subquery(
                        Warehouse.objects.filter(
                            id=Cast(OuterRef('warehouse_id'), output_field=BigIntegerField())
                        ).values('location')[:1]
                    )
                ),
                When(
                    status="Received",
                    then=Subquery(
                        Customer.objects.filter(
                            id=Cast(OuterRef('customer_id'), output_field=BigIntegerField())
                        ).values('location')[:1]
                    )
                ),
                default=Value("In Transit"), output_field=CharField(),
            )
        )
        for shipment in contract_processor_shipments:
            crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

            shipment["crops"] = []
            for crop in crops:
                
                additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
                    shipment_id=shipment["id"],
                    crop_id=crop["id"]
                ).order_by("-id").values("additional_lot_number").first()

                shipment["crops"].append({
                    "crop_name": crop["crop"],
                    "lot_number": crop["lot_number"],
                    "net_weight": crop["net_weight"],
                    "weight_unit": crop["weight_unit"],
                    "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                })
            carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
            shipment["carrier_id"] = carrier.carrier_id
            
        # Optimized contract warehouse shipments
        contract_warehouse_shipments = WarehouseCustomerShipment.objects.values(
            'id', 'date_pulled', 'shipment_id', 'warehouse_id', 'warehouse_name', 'customer_id',
            'customer_name', 'status', 'customer_receive_date'
        ).annotate(
            date_field=F('date_pulled'),
            shipment_type=Value('WarehouseCustomerShipment', output_field=CharField()),
            location=Case(
                When(
                    status="Received",
                    then=Subquery(
                        Warehouse.objects.filter(
                            id=Cast(OuterRef('warehouse_id'), output_field=BigIntegerField())
                        ).values('location')[:1]
                    )
                ),
                default=Value("In Transit"), output_field=CharField(),
            )
        )
        for shipment in contract_warehouse_shipments:
            crops = WarehouseShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

            shipment["crops"] = []
            for crop in crops:
                
                additional_lot = WarehouseShipmentLotNumberTracking.objects.filter(
                    shipment_id=shipment["id"],
                    crop_id=crop["id"]
                ).order_by("-id").values("additional_lot_number").first()

                shipment["crops"].append({
                    "crop_name": crop["crop"],
                    "lot_number": crop["lot_number"],
                    "net_weight": crop["net_weight"],
                    "weight_unit": crop["weight_unit"],
                    "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                })
            carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
            shipment["carrier_id"] = carrier.carrier_id
            
        # Combine all shipments and sort
        combined_shipments = chain(
            grower_shipments,
            processor_shipments,
            contract_processor_shipments,
            contract_warehouse_shipments
        )
        sorted_shipments = sorted(combined_shipments, key=itemgetter('date_field'), reverse=True)

        # Limit to recent shipments
        recent_shipments = sorted_shipments[:10]

        # Determine from and to dates
        first_shipment = GrowerShipment.objects.order_by('date_time').first()
        from_date = first_shipment.date_time.date() if first_shipment else None
        to_date = date.today()

        # Return results
        context['recent_shipments'] = recent_shipments
        context['from_date'] = from_date
        context['to_date'] = to_date        

        if request.method == 'POST':
            table_show = request.POST.get("table_view")
            select_crop= request.POST.get('select_crop')
            get_search_by= request.POST.get('get_search_by')
            search_text= request.POST.get('search_text')
            filter_type = request.POST.get('filter_type')            

            from_date = None
            to_date = None
            crop_year = None
            if filter_type == "date_range":
                from_date = request.POST.get('from_date')
                to_date = request.POST.get('to_date')
            elif filter_type == "year":
                crop_year = request.POST.get('crop_year')
                if crop_year:  
                    try:
                        year = int(crop_year)
                        from_date = date(year, 1, 1)  
                        to_date = date(year, 12, 31) 
                    except ValueError:                        
                        pass
            else:
                first_shipment = GrowerShipment.objects.order_by('date_time').first()
                if first_shipment:
                    from_date = first_shipment.date_time.date() 
                else:
                    from_date = None  
                to_date = date.today()            

            if search_text and get_search_by:
                
                context['search_text'] = search_text
                context['get_search_by'] = get_search_by
                context['filter_type'] = filter_type

                if select_crop:
                    context['select_crop'] = select_crop

                if crop_year or (from_date and to_date):
                    context['crop_year'] = crop_year
                    context['from_date'] = from_date
                    context['to_date'] = to_date  
            
            shipments = []
            search_by = None
            type = None
            
            # search by Grower ....
            if get_search_by and get_search_by == 'grower' :
                check_grower = Grower.objects.filter(name__icontains=search_text)
                if check_grower.exists() :
                    grower_id = check_grower.first().id
                    shipments = list(GrowerShipment.objects.filter(grower_id=grower_id).values("id","shipment_id","grower_id", "grower__name", "field_id", "field__name", "processor__id", "processor__entity_name", "crop", "variety", "total_amount", "received_amount", "unit_type", "date_time", "approval_date", "sku", "status"))
                    if select_crop:
                        shipments = list(GrowerShipment.objects.filter(grower_id=grower_id, crop=select_crop).values("id","shipment_id","grower_id", "grower__name", "field_id", "field__name", "processor__id", "processor__entity_name", "crop", "variety", "total_amount", "received_amount", "unit_type", "date_time", "approval_date", "sku", "status"))
                    type = "grower_shipments" 
                    search_by = "grower" 
                    for shipment in shipments:
                        if shipment["status"] == "APPROVED":
                            processor = Processor.objects.filter(id=int(shipment["processor__id"])).first()
                            processor_location = Location.objects.filter(processor=processor).first()
                            if processor_location:
                                location = processor_location.name
                            else:
                                location = "N/A"
                        elif shipment["status"] == "DISAPPROVED":
                            grower = Grower.objects.filter(id=int(shipment["grower_id"])).first()
                            location = grower.physical_address1
                        else:
                            location = "In Transit"
                        shipment["location"] = location  
                                    
                else:
                    context['no_rec_found_msg'] = "No Records Found"

            # search by Field ....
            elif get_search_by and get_search_by == 'field' :
                check_field = Field.objects.filter(name__icontains=search_text)
                if check_field.exists() :                    
                    field_id = check_field.first().id                  
                    grower_id =  check_field.first().grower.id
                    shipments = list(GrowerShipment.objects.filter(grower_id=grower_id, field_id=field_id).values("id","shipment_id","grower_id", "grower__name", "field_id", "field__name", "processor__id", "processor__entity_name", "crop", "variety", "total_amount", "received_amount", "unit_type", "date_time", "approval_date", "sku", "status", "received_amount", "unit_type"))
                    if select_crop:
                        shipments = list(GrowerShipment.objects.filter(grower_id=grower_id, field_id=field_id, crop=select_crop).values("id","shipment_id","grower_id", "grower__name", "field_id", "field__name", "processor__id", "processor__entity_name", "crop", "variety", "total_amount", "received_amount", "unit_type", "date_time", "approval_date", "sku"))
                    type = "grower_shipments" 
                    search_by = "field"                                                              
                    for shipment in shipments:
                        if shipment["status"] == "APPROVED":
                            processor = Processor.objects.filter(id=int(shipment["processor__id"])).first()
                            processor_location = Location.objects.filter(processor=processor).first()
                            if processor_location:
                                location = processor_location.name
                            else:
                                location = "N/A"
                        elif shipment["status"] == "DISAPPROVED":
                            grower = Grower.objects.filter(id=int(shipment["grower_id"])).first()
                            location = grower.physical_address1
                        else:
                            location = "In Transit"
                        shipment["location"] = location
                else:
                    context['no_rec_found_msg'] = "No Records Found"
            
            # search by Processor ....
            elif get_search_by and get_search_by == 'processor' :
                check_processor = get_processor_type(search_text)
                if check_processor:
                    processor_type = check_processor["type"]
                    processor_id = check_processor["id"]
                    if processor_type == "T1":
                        inbound_shipments = list(GrowerShipment.objects.filter(processor_id=processor_id).values("id","shipment_id","grower_id", "grower__name", "field_id", "field__name", "processor__id", "processor__entity_name", "crop", "variety", "total_amount", "received_amount", "unit_type", "date_time", "approval_date", "sku", "status", "received_amount", "unit_type"))
                        for shipment in inbound_shipments:
                            if shipment["status"] == "APPROVED":
                                processor = Processor.objects.filter(id=int(shipment["processor__id"])).first()
                                processor_location = Location.objects.filter(processor=processor).first()
                                if processor_location:
                                    location = processor_location.name
                                else:
                                    location = "N/A"
                            elif shipment["status"] == "DISAPPROVED":
                                grower = Grower.objects.filter(id=int(shipment["grower_id"])).first()
                                location = grower.physical_address1
                            else:
                                location = "In Transit"
                            shipment["location"] = location
                    else:
                        inbound_shipments = list(ShipmentManagement.objects.filter(processor2_idd=processor_id, receiver_processor_type=processor_type).values())
                        
                        for shipment in inbound_shipments:
                            if shipment["status"] == "APPROVED":
                                processor = Processor2.objects.filter(id=int(shipment["processor2_idd"])).first()
                                processor_location = Processor2Location.objects.filter(processor=processor).first()
                                if processor_location:
                                    location = processor_location.name
                                else:
                                    location = "N/A"
                            elif shipment["status"]== "DISAPPROVED":
                                if shipment["sender_processor_type"] == "T1":
                                    processor = Processor.objects.filter(id=int(shipment["processor_idd"])).first()
                                    processor_location = Location.objects.filter(processor=processor).first()
                                    if processor_location:
                                        location = processor_location.name
                                    else:
                                        location = "N/A"
                                else:            
                                    processor = Processor2.objects.filter(id=int(shipment["processor2_idd"])).first()
                                    processor_location = Processor2Location.objects.filter(processor=processor).first()
                                    if processor_location:
                                        location = processor_location.name
                                    else:
                                        location = "N/A"
                            else:
                                location = "In Transit"                            
                            shipment["location"] = location

                    outbound_shipments = list(ShipmentManagement.objects.filter(processor_idd=processor_id, sender_processor_type=processor_type).values())
                    
                    contract_shipments = list(ProcessorWarehouseShipment.objects.filter(processor_id=processor_id, processor_type=processor_type).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    if select_crop:
                        if processor_type == "T1":
                            inbound_shipments = list(GrowerShipment.objects.filter(processor_id=processor_id, crop=select_crop).values("id","shipment_id","grower_id", "grower__name", "field_id", "field__name", "processor__id", "processor__entity_name", "crop", "variety", "total_amount", "received_amount", "unit_type", "date_time", "approval_date", "sku", "status"))
                            for shipment in inbound_shipments:
                                if shipment["status"] == "APPROVED":
                                    processor = Processor.objects.filter(id=int(shipment["processor__id"])).first()
                                    processor_location = Location.objects.filter(processor=processor).first()
                                    if processor_location:
                                        location = processor_location.name
                                    else:
                                        location = "N/A"
                                elif shipment["status"] == "DISAPPROVED":
                                    grower = Grower.objects.filter(id=int(shipment["grower_id"])).first()
                                    location = grower.physical_address1
                                else:
                                    location = "In Transit"
                                shipment["location"] = location
                        else:
                            inbound_shipments = list(ShipmentManagement.objects.filter(processor2_idd=processor_id, sender_processor_type=processor_type, crop=select_crop).values())
                        
                        outbound_shipments = list(ShipmentManagement.objects.filter(processor_idd=processor_id, sender_processor_type=processor_type, crop=select_crop).values())
                        
                        contract_shipments = list(ProcessorWarehouseShipment.objects.filter(processor_id=processor_id, processor_type=processor_type, processor_shipment_crop__crop=select_crop).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                        
                    for shipment in outbound_shipments:
                        if shipment["status"] == "APPROVED":
                            processor = Processor2.objects.filter(id=int(shipment["processor2_idd"])).first()
                            location = Processor2Location.objects.filter(processor=processor).first().name
                        elif shipment["status"]== "DISAPPROVED":
                            if shipment["sender_processor_type"] == "T1":
                                processor = Processor.objects.filter(id=int(shipment["processor_idd"])).first()
                                processor_location = Location.objects.filter(processor=processor).first()
                                if processor_location:
                                    location = processor_location.name
                                else:
                                    location = "N/A"
                            else:            
                                processor = Processor2.objects.filter(id=int(shipment["processor2_idd"])).first()
                                processor_location = Processor2Location.objects.filter(processor=processor).first()
                                if processor_location:
                                    location = processor_location.name
                                else:
                                    location = "N/A"
                        else:
                            location = "In Transit"
                        shipment["location"] = location

                    for shipment in contract_shipments:
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

                        # Add crops and their additional lot numbers to the shipment
                        shipment["crops"] = []
                        for crop in crops:
                            
                            additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
                                shipment_id=shipment["id"],
                                crop_id=crop["id"]
                            ).order_by("-id").values("additional_lot_number").first()

                            shipment["crops"].append({
                                "crop_name": crop["crop"],
                                "lot_number": crop["lot_number"],
                                "net_weight": crop["net_weight"],
                                "weight_unit": crop["weight_unit"],
                                "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                            })
                        
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id 

                        check_lot_entries = list(ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment["id"]).values_list("address", flat=True))
                        if check_lot_entries and shipment["status"] != "Received":
                            location = check_lot_entries[-1]

                        elif check_lot_entries and shipment["status"] == "Received":
                            if shipment["warehouse_id"] not in [None, "null", "", " "]:
                                destination = Warehouse.objects.filter(id=int(shipment["warehouse_id"])).first()
                            else:
                                destination = Customer.objects.filter(id=int(shipment["customer_id"])).first()
                            location = destination.location
                        else:
                            location = "In Transit"
                        shipment["location"] = location
                    
                    shipments = outbound_shipments + contract_shipments + inbound_shipments
                    type = "processor_shipments" 
                    search_by = "processor"                    
                    
                else:
                    context['no_rec_found_msg'] = "No Records Found"
            
            # search by SKU Id ....
            elif get_search_by and get_search_by == 'sku_id':
                grower_shipments = list(GrowerShipment.objects.filter(sku__icontains=search_text).values("id","shipment_id","grower_id", "grower__name", "field_id", "field__name", "processor__id", "processor__entity_name", "crop", "variety", "total_amount", "received_amount", "unit_type", "date_time", "approval_date", "sku", "status"))
                if select_crop:
                    grower_shipments = list(GrowerShipment.objects.filter(sku__icontains=search_text, crop=select_crop).values("id","shipment_id","grower_id", "grower__name", "field_id", "field__name", "processor__id", "processor__entity_name", "crop", "variety", "total_amount", "received_amount", "unit_type", "date_time", "approval_date", "sku", "status"))

                for shipment in grower_shipments:
                    if shipment["status"] == "APPROVED":
                        processor = Processor.objects.filter(id=int(shipment["processor__id"])).first()
                        processor_location = Location.objects.filter(processor=processor).first()
                        if processor_location:
                            location = processor_location.name
                        else:
                            location = "N/A"
                    elif shipment["status"] == "DISAPPROVED":
                        grower = Grower.objects.filter(id=int(shipment["grower_id"])).first()
                        location = grower.physical_address1
                    else:
                        location = "In Transit"
                    shipment["location"] = location
                processor_shipments = list(ShipmentManagement.objects.filter(Q(storage_bin_send__icontains=search_text) | Q(storage_bin_recive__icontains=search_text)).values())                                      
                if select_crop:
                    processor_shipments = list(ShipmentManagement.objects.filter((Q(storage_bin_send__icontains=search_text) | Q(storage_bin_recive__icontains=search_text)), crop=select_crop).values())

                for shipment in processor_shipments:
                    if shipment["status"] == "APPROVED":
                        processor = Processor2.objects.filter(id=int(shipment["processor2_idd"])).first()
                        processor_location = Processor2Location.objects.filter(processor=processor).first()
                        if processor_location:
                            location = processor_location.name
                        else:
                            location = "N/A"
                    elif shipment["status"]== "DISAPPROVED":
                        if shipment["sender_processor_type"] == "T1":
                            processor = Processor.objects.filter(id=int(shipment["processor_idd"])).first()
                            processor_location = Location.objects.filter(processor=processor).first()
                            if processor_location:
                                location = processor_location.name
                            else:
                                location = "N/A"
                        else:            
                            processor = Processor2.objects.filter(id=int(shipment["processor2_idd"])).first()
                            processor_location = Processor2Location.objects.filter(processor=processor).first()
                            if processor_location:
                                location = processor_location.name
                            else:
                                location = "N/A"
                    else:
                        location = "In Transit"                            
                    shipment["location"] = location
                    
                shipments = grower_shipments + processor_shipments  
                type = "processor_shipments" 
                search_by = "sku_id"  
                 
            # search by Delivery Id ....
            elif get_search_by and get_search_by == 'deliveryid' : 
                search_by = "deliveryid"                              
                check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text)
                
                if check_shipment.exists() :
                   shipments = list(check_shipment.values("id","shipment_id","grower_id", "grower__name", "field_id", "field__name", "processor__id", "processor__entity_name", "crop", "variety", "total_amount", "received_amount", "unit_type", "date_time", "approval_date", "sku", "status", "received_amount", "unit_type")) 
                   if select_crop:
                       shipments = list(check_shipment.filter(crop=select_crop).values("id","shipment_id","grower_id", "grower__name", "field_id", "field__name", "processor__id", "processor__entity_name", "crop", "variety", "total_amount", "received_amount", "unit_type", "date_time", "approval_date", "sku", "status")) 
                   type = "grower_shipments"  

                   for shipment in shipments:
                        if shipment["status"] == "APPROVED":
                            processor = Processor.objects.filter(id=int(shipment["processor__id"])).first()
                            processor_location = Location.objects.filter(processor=processor).first()
                            if processor_location:
                                location = processor_location.name
                            else:
                                location = "N/A"
                        elif shipment["status"] == "DISAPPROVED":
                            grower = Grower.objects.filter(id=int(shipment["grower_id"])).first()
                            location = grower.physical_address1
                        else:
                            location = "In Transit"
                        shipment["location"] = location
                               

                elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text).exists():
                    shipments = ShipmentManagement.objects.filter(shipment_id__icontains=search_text).values()
                    if select_crop:
                        shipments = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop).values()

                    for shipment in shipments:
                        if shipment["status"] == "APPROVED":
                            processor = Processor2.objects.filter(id=int(shipment["processor2_idd"])).first()
                            processor_location = Processor2Location.objects.filter(processor=processor).first()
                            if processor_location:
                                location = processor_location.name
                            else:
                                location = "N/A"
                        elif shipment["status"]== "DISAPPROVED":
                            if shipment["sender_processor_type"] == "T1":
                                processor = Processor.objects.filter(id=int(shipment["processor_idd"])).first()
                                processor_location = Location.objects.filter(processor=processor).first()
                                if processor_location:
                                    location = processor_location.name
                                else:
                                    location = "N/A"
                            else:            
                                processor = Processor2.objects.filter(id=int(shipment["processor2_idd"])).first()
                                processor_location = Processor2Location.objects.filter(processor=processor).first()
                                if processor_location:
                                    location = processor_location.name
                                else:
                                    location = "N/A"
                        else:
                            location = "In Transit"                            
                        shipment["location"] = location 

                    type = "processor_shipments"                
                    
                elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text).exists():                    
                    shipments = list(ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    if select_crop:
                        shipments = list(ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in shipments:
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

                        shipment["crops"] = []
                        for crop in crops:
                            
                            additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
                                shipment_id=shipment["id"],
                                crop_id=crop["id"]
                            ).order_by("-id").values("additional_lot_number").first()

                            shipment["crops"].append({
                                "crop_name": crop["crop"],
                                "lot_number": crop["lot_number"],
                                "net_weight": crop["net_weight"],
                                "weight_unit": crop["weight_unit"],
                                "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                            })
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id 

                        check_lot_entries = list(ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment["id"]).values_list("address", flat=True))
                        if check_lot_entries and shipment["status"] != "Received":
                            location = check_lot_entries[-1]

                        elif check_lot_entries and shipment["status"] == "Received":
                            if shipment["warehouse_id"] not in [None, "null", "", " "]:
                                destination = Warehouse.objects.filter(id=int(shipment["warehouse_id"])).first()
                            else:
                                destination = Customer.objects.filter(id=int(shipment["customer_id"])).first()
                            location = destination.location
                        else:
                            location = "In Transit"
                        shipment["location"] = location

                    type = "contract_shipments"  
                           
                
                elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text).exists():
                    shipments = list(WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text).values(
                            "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                            "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                        ))
                    if select_crop:
                        shipments = list(WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop).values(
                            "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                            "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                        ))
                    for shipment in shipments:
                        crops = WarehouseShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

                        shipment["crops"] = []
                        for crop in crops:
                            
                            additional_lot = WarehouseShipmentLotNumberTracking.objects.filter(
                                shipment_id=shipment["id"],
                                crop_id=crop["id"]
                            ).order_by("-id").values("additional_lot_number").first()

                            shipment["crops"].append({
                                "crop_name": crop["crop"],
                                "lot_number": crop["lot_number"],
                                "net_weight": crop["net_weight"],
                                "weight_unit": crop["weight_unit"],
                                "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                            })
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id 

                        check_lot_entries = list(ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment["id"]).values_list("address", flat=True))
                        if check_lot_entries and shipment["status"] != "Received":
                            location = check_lot_entries[-1]

                        elif check_lot_entries and shipment["status"] == "Received":                            
                            destination = Warehouse.objects.filter(id=int(shipment["warehouse_id"])).first()                            
                            location = destination.location
                        else:
                            location = "In Transit"
                        shipment["location"] = location 

                    type = "contract_shipments"  
                                                               
                else:
                    context['no_rec_found_msg'] = "No Records Found"   

            # search by Warehouse....
            elif get_search_by and get_search_by == 'warehouse':
                search_by = "warehouse"
                type = "contract_shipments"
                check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
                if check_warehouse.exists():                            
                    warehouse = check_warehouse.first()                            
                    inbound_shipments = list(ProcessorWarehouseShipment.objects.filter( warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    if select_crop:
                        inbound_shipments = list(ProcessorWarehouseShipment.objects.filter(prcessor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    for shipment in inbound_shipments:
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

                        shipment["crops"] = []
                        for crop in crops:
                            
                            additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
                                shipment_id=shipment["id"],
                                crop_id=crop["id"]
                            ).order_by("-id").values("additional_lot_number").first()

                            shipment["crops"].append({
                                "crop_name": crop["crop"],
                                "lot_number": crop["lot_number"],
                                "net_weight": crop["net_weight"],
                                "weight_unit": crop["weight_unit"],
                                "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                            })
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                        check_lot_entries = list(ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment["id"]).values_list("address", flat=True))
                        if check_lot_entries and shipment["status"] != "Received":
                            location = check_lot_entries[-1]

                        elif check_lot_entries and shipment["status"] == "Received":                            
                            destination = Warehouse.objects.filter(id=int(shipment["warehouse_id"])).first()                            
                            location = destination.location
                        else:
                            location = "In Transit"
                        shipment["location"] = location
                
                    outbound_shipments = list(WarehouseCustomerShipment.objects.filter(warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id","shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    if select_crop:
                        outbound_shipments = list(WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop,warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id","shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"))
                    for shipment in outbound_shipments:
                        crops = WarehouseShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

                        # Add crops and their additional lot numbers to the shipment
                        shipment["crops"] = []
                        for crop in crops:
                            
                            additional_lot = WarehouseShipmentLotNumberTracking.objects.filter(
                                shipment_id=shipment["id"],
                                crop_id=crop["id"]
                            ).order_by("-id").values("additional_lot_number").first()

                            shipment["crops"].append({
                                "crop_name": crop["crop"],
                                "lot_number": crop["lot_number"],
                                "net_weight": crop["net_weight"],
                                "weight_unit": crop["weight_unit"],
                                "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                            })
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id  

                        check_lot_entries = list(WarehouseShipmentLotNumberTracking.objects.filter(shipment=shipment["id"]).values_list("address", flat=True))
                        if check_lot_entries and shipment["status"] != "Received":
                            location = check_lot_entries[-1]

                        elif check_lot_entries and shipment["status"] == "Received":                            
                            destination = Customer.objects.filter(id=int(shipment["customer_id"])).first()
                            location = destination.location
                        else:
                            location = "In Transit"
                        shipment["location"] = location

                    shipments = inbound_shipments + outbound_shipments        
                    
                else:
                    context['no_rec_found_msg'] = "No Records Found"
                     
            # search by Customer....
            elif get_search_by and get_search_by == 'customer':
                search_by = "customer"
                type = "contract_shipments"
                check_customer = Customer.objects.filter(name__icontains=search_text)
                if check_customer.exists():
                    customer = check_customer.first()                   
                    
                    processor_shipments = list(ProcessorWarehouseShipment.objects.filter(                        
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                        "processor_type", "processor_id", "shipment_id", "warehouse_id",
                        "warehouse_name", "customer_name", "customer_id", 
                        "date_pulled", "carrier_type", "distributor_receive_date", "status"
                    ))
                    if select_crop:
                        processor_shipments = list(ProcessorWarehouseShipment.objects.filter( 
                        processor_shipment_crop__crop=select_crop,                       
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                        ).values(
                            "id","processor_shipment_crop__crop", "contract__secret_key", "contract_id", "processor_entity_name",
                            "processor_type", "processor_id", "shipment_id", "warehouse_id",
                            "warehouse_name", "customer_name", "customer_id", 
                            "date_pulled", "carrier_type", "distributor_receive_date", "status"
                        ))

                    for shipment in processor_shipments:
                        crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

                        # Add crops and their additional lot numbers to the shipment
                        shipment["crops"] = []
                        for crop in crops:
                            
                            additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
                                shipment_id=shipment["id"],
                                crop_id=crop["id"]
                            ).order_by("-id").values("additional_lot_number").first()

                            shipment["crops"].append({
                                "crop_name": crop["crop"],
                                "lot_number": crop["lot_number"],
                                "net_weight": crop["net_weight"],
                                "weight_unit": crop["weight_unit"],
                                "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                            })
                        carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id 

                        check_lot_entries = list(ProcessorShipmentLotNumberTracking.objects.filter(shipment=shipment["id"]).values_list("address", flat=True))
                        if check_lot_entries and shipment["status"] != "Received":
                            location = check_lot_entries[-1]

                        elif check_lot_entries and shipment["status"] == "Received":
                            if shipment["warehouse_id"] not in [None, "null", "", " "]:
                                destination = Warehouse.objects.filter(id=int(shipment["warehouse_id"])).first()
                            else:
                                destination = Customer.objects.filter(id=int(shipment["customer_id"])).first()
                            location = destination.location
                        else:
                            location = "In Transit"
                        shipment["location"] = location
                        
                    warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(                         
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                    ).values(
                        "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                        "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                    ))
                    if select_crop:
                        warehouse_shipments = list(WarehouseCustomerShipment.objects.filter(
                        warehouse_shipment_crop__crop=select_crop,                         
                        customer_id=customer.id, 
                        date_pulled__date__gte=from_date, 
                        date_pulled__date__lte=to_date
                        ).values(
                            "id", "warehouse_shipment_crop__crop","contract__secret_key", "contract_id", "shipment_id",
                            "warehouse_id", "customer_id", "warehouse_name", "customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status"
                        ))

                    for shipment in warehouse_shipments:
                        crops = WarehouseShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

                        # Add crops and their additional lot numbers to the shipment
                        shipment["crops"] = []
                        for crop in crops:
                            
                            additional_lot = WarehouseShipmentLotNumberTracking.objects.filter(
                                shipment_id=shipment["id"],
                                crop_id=crop["id"]
                            ).order_by("-id").values("additional_lot_number").first()

                            shipment["crops"].append({
                                "crop_name": crop["crop"],
                                "lot_number": crop["lot_number"],
                                "net_weight": crop["net_weight"],
                                "weight_unit": crop["weight_unit"],
                                "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                            })
                        carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
                        shipment["carrier_id"] = carrier.carrier_id

                        check_lot_entries = list(WarehouseShipmentLotNumberTracking.objects.filter(shipment=shipment["id"]).values_list("address", flat=True))
                        if check_lot_entries and shipment["status"] != "Received":
                            location = check_lot_entries[-1]

                        elif check_lot_entries and shipment["status"] == "Received":                            
                            destination = Customer.objects.filter(id=int(shipment["customer_id"])).first()
                            location = destination.location
                        else:
                            location = "In Transit"
                        shipment["location"] = location
            
                    shipments=  processor_shipments + warehouse_shipments                    
                        
                else:
                    context['no_rec_found_msg'] = "No Records Found" 
            
            else:
                context['no_rec_found_msg'] = "No Records Found"

            context["shipments"] = shipments
            context["get_search_by"] = search_by
            context["type"] = type
            if table_show:
                    return render (request, 'tracemodule/test_trace_module.html', context)                                                          
        return render (request, 'tracemodule/test_trace_module.html', context)
    else:
        return redirect ('dashboard')       
                    
                   
@login_required()
def trace_shipment(request, search_text, from_date, to_date):  
    
    new_context = {}
    first_shipment = GrowerShipment.objects.order_by('date_time').first()
    if first_shipment:
        from_date = first_shipment.date_time.date() 
    else:
        from_date = None  
    to_date = date.today() 
    check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text)
                        
    if check_shipment.exists() :        
        type = "grower_shipment"
        get_shipment = check_shipment.first()  

        if get_shipment.status == "APPROVED":
            processor = Processor.objects.filter(id=int(get_shipment.processor.id)).first()
            processor_location = Location.objects.filter(processor=processor).first()
            if processor_location:
                location = processor_location.name
            else:
                location = "N/A"
        elif get_shipment.status== "DISAPPROVED":
            grower = Grower.objects.filter(id=int(get_shipment.grower.id)).first()
            location = grower.physical_address1
        else:
            location = "In Transit"
               
        select_crop = get_shipment.crop
        context = shipmentid_traceability_response(select_crop, get_shipment.shipment_id, from_date, to_date)
        new_context.update(context)    
        context_ = location_response(new_context)                                
        new_context.update(context_) 
    
    elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text).exists():
        type = "processor_shipment"
        shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text)
        get_shipment = shipment.first()  

        if get_shipment.status == "APPROVED":
            processor = Processor2.objects.filter(id=int(get_shipment.processor2_idd)).first()
            processor_location = Processor2Location.objects.filter(processor=processor).first()
            if processor_location:
                location = processor_location.name
            else:
                location = "N/A"
        elif get_shipment.status== "DISAPPROVED":
            if get_shipment.sender_processor_type == "T1":
                processor = Processor.objects.filter(id=int(get_shipment.processor_idd)).first()
                processor_location = Location.objects.filter(processor=processor).first()
                if processor_location:
                    location = processor_location.name
                else:
                    location = "N/A"
            else:            
                processor = Processor2.objects.filter(id=int(get_shipment.processor2_idd)).first()
                processor_location = Processor2Location.objects.filter(processor=processor).first()
                if processor_location:
                    location = processor_location.name
                else:
                    location = "N/A"
        else:
            location = "In Transit"    
        select_crop = get_shipment.crop        
        context = shipmentid_traceability_response(select_crop, get_shipment.shipment_id, from_date, to_date)
          
        new_context.update(context)    
        context_ = location_response(new_context)                                
        new_context.update(context_) 
        
    elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text).exists():
        type = "contract_shipment"
        shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id" ,"processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
        for shipment in shipments:
            crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

            shipment["crops"] = []
            for crop in crops:
                
                additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
                    shipment_id=shipment["id"],
                    crop_id=crop["id"]
                ).order_by("-id").values("additional_lot_number").first()

                shipment["crops"].append({
                    "crop_name": crop["crop"],
                    "lot_number": crop["lot_number"],
                    "net_weight": crop["net_weight"],
                    "weight_unit": crop["weight_unit"],
                    "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                })
            carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
            shipment["carrier_id"] = carrier.carrier_id  

        get_shipment = shipments.first()
        check_lot_entries = list(ProcessorShipmentLotNumberTracking.objects.filter(shipment=get_shipment["id"]).values_list("address", flat=True))
        if check_lot_entries and get_shipment["status"] != "Received":
            location = check_lot_entries[-1]
        elif check_lot_entries and get_shipment["status"] == "Received":
            if get_shipment["warehouse_id"] not in [None, "null", "", " "]:
                destination = Warehouse.objects.filter(id=int(get_shipment["warehouse_id"])).first()
            else:
                destination = Customer.objects.filter(id=int(get_shipment["customer_id"])).first()
            location = destination.location
        else:
            location = "In Transit"
        if get_shipment["warehouse_id"] not in [None, "null", "", " "]:
            
            inbound5 = list(shipments)
            new_context["inbound5_wip"] = inbound5
            new_context["outbound5_wip"] = inbound5
            crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
            processor_entity_name = get_shipment["processor_entity_name"]
            processor_id = get_shipment["processor_id"]
            processor_type = get_shipment["processor_type"]
            for crop in crops:
                select_crop = crop.crop
                return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                
                keys_to_extend = [
                    "origin_context",
                    "t1_processor",
                    "inbound2_wip",
                    "inbound3_wip",
                    "inbound4_wip",
                    "outbound2_wip",
                    "outbound3_wip",
                    "outbound4_wip",
                ]

                for key in keys_to_extend:
                    if return_context.get(key):
                        new_context[key] = new_context.get(key, [])
                        new_context[key].extend(return_context[key])                                      
            
            new_context_ = location_response(new_context)                           
            new_context.update(new_context_)
        else:
             
            inbound6 = list(shipments)
            new_context["inbound6_wip"] = inbound6
            new_context["outbound5_wip"] = inbound6
            new_context["inbound5_wip"] = []
            new_context["outbound6_wip"] = []

            crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])

            processor_entity_name = get_shipment["processor_entity_name"]
            processor_id = get_shipment["processor_id"]
            processor_type = get_shipment["processor_type"]
            for crop in crops:
                select_crop = crop.crop
                return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                
                keys_to_extend = [
                    "origin_context",
                    "t1_processor",
                    "inbound2_wip",
                    "inbound3_wip",
                    "inbound4_wip",
                    "outbound2_wip",
                    "outbound3_wip",
                    "outbound4_wip",
                ]

                for key in keys_to_extend:
                    if return_context.get(key):
                        new_context[key] = new_context.get(key, [])
                        new_context[key].extend(return_context[key])                                      
            
            new_context_ = location_response(new_context)                           
            new_context.update(new_context_)
    
    elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text).exists():
        type = "contract_shipment"
        shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id","shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
        for shipment in shipments:
            crops = WarehouseShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

            shipment["crops"] = []
            for crop in crops:
                
                additional_lot = WarehouseShipmentLotNumberTracking.objects.filter(
                    shipment_id=shipment["id"],
                    crop_id=crop["id"]
                ).order_by("-id").values("additional_lot_number").first()

                shipment["crops"].append({
                    "crop_name": crop["crop"],
                    "lot_number": crop["lot_number"],
                    "net_weight": crop["net_weight"],
                    "weight_unit": crop["weight_unit"],
                    "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                })
            carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
            shipment["carrier_id"] = carrier.carrier_id  

        get_shipment = shipments.first()
        check_lot_entries = list(WarehouseShipmentLotNumberTracking.objects.filter(shipment=get_shipment["id"]).values_list("address", flat=True))
        if check_lot_entries and get_shipment["status"] != "Received":
            location = check_lot_entries[-1]
        elif check_lot_entries and get_shipment["status"] == "Received":
            
            destination = Customer.objects.filter(id=int(get_shipment["customer_id"])).first()
            location = destination.location
        else:
            location = "In Transit"
        new_context["inbound6_wip"] = list(shipments)
        new_context["outbound6_wip"] = list(shipments)
        crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
        outbound5_processor = []
        for crop in crops:
            select_crop = crop.crop
            check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
            if check_processor_shipment:
                for shipment in check_processor_shipment:                   
                    shipment_crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

                    shipment["crops"] = []
                    for crop_ in shipment_crops:
                        
                        additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
                            shipment_id=shipment["id"],
                            crop_id=crop_["id"]
                        ).order_by("-id").values("additional_lot_number").first()

                        shipment["crops"].append({
                            "crop_name": crop_["crop"],
                            "lot_number": crop_["lot_number"],
                            "net_weight": crop_["net_weight"],
                            "weight_unit": crop_["weight_unit"],
                            "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                        })
                    carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                    shipment["carrier_id"] = carrier.carrier_id  
                    outbound5_processor.extend(check_processor_shipment) 
                    processor_entity_name = shipment["processor_entity_name"]
                    processor_id = shipment["processor_id"]
                    processor_type = shipment["processor_type"]                             
                    return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                    
                    keys_to_extend = [
                        "origin_context",
                        "t1_processor",
                        "inbound2_wip",
                        "inbound3_wip",
                        "inbound4_wip",
                        "outbound2_wip",
                        "outbound3_wip",
                        "outbound4_wip",
                    ]

                    for key in keys_to_extend:
                        if return_context.get(key):
                            new_context[key] = new_context.get(key, [])
                            new_context[key].extend(return_context[key])                                     
                
        new_context["outbound5_wip"] = outbound5_processor
        new_context["inbound5_wip"] = outbound5_processor   

        new_context_ = location_response(new_context)                           
        new_context.update(new_context_)                     
    
    else:
        new_context['no_rec_found_msg'] = "No Records Found"  
    
    context_ = grower_location(new_context)
    new_context.update(context_)
    new_context["shipment"] = get_shipment
    new_context["shipment_type"] = type
    new_context["from_date"] = from_date
    new_context["to_date"] = to_date
    new_context["location"] = location
    
    return render(request, 'tracemodule/view_traceability.html', new_context)


# @login_required()
# def trace_shipment(request, search_text, from_date, to_date):  
    
#     new_context = {}
#     first_shipment = GrowerShipment.objects.order_by('date_time').first()
#     if first_shipment:
#         from_date = first_shipment.date_time.date() 
#     else:
#         from_date = None  
#     to_date = date.today() 
#     check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text)
                        
#     if check_shipment.exists() :        
#         type = "grower_shipment"
#         get_shipment = check_shipment.first()  

#         if get_shipment.status == "APPROVED":
#             processor = Processor.objects.filter(id=int(get_shipment.processor.id)).first()
#             processor_location = Location.objects.filter(processor=processor).first()
#             if processor_location:
#                 location = processor_location.name
#             else:
#                 location = "N/A"
#         elif get_shipment.status== "DISAPPROVED":
#             grower = Grower.objects.filter(id=int(shipment["grower_id"])).first()
#             location = grower.physical_address1
#         else:
#             location = "In Transit"
               
#         select_crop = get_shipment.crop
#         crops_context = [] 
#         return_context = shipmentid_traceability_response(select_crop, get_shipment.shipment_id, from_date, to_date)
#         crop_context = {
#             "crop": select_crop,
#             "origin_context": return_context.get("origin_context", []),
#             "t1_processor": return_context.get("t1_processor", []),
#             "inbound2_wip": return_context.get("inbound2_wip", []),
#             "inbound3_wip": return_context.get("inbound3_wip", []),
#             "inbound4_wip": return_context.get("inbound4_wip", []),
#             "outbound2_wip": return_context.get("outbound2_wip", []),
#             "outbound3_wip": return_context.get("outbound3_wip", []),
#             "outbound4_wip": return_context.get("outbound4_wip", []),
#             "inbound6_wip": [],
#             "outbound6_wip": [],
#             "outbound5_wip": [],
#             "inbound5_wip": []
#         }
            
#         crop_context.update(location_response(crop_context))
#         crop_context.update(grower_location(crop_context))
#         crops_context.append(crop_context)
#         new_context["crops_context"] = crops_context
    
#     elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text).exists():
#         type = "processor_shipment"
#         shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text)
#         get_shipment = shipment.first()  

#         if get_shipment.status == "APPROVED":
#             processor = Processor2.objects.filter(id=int(get_shipment.processor2_idd)).first()
#             processor_location = Processor2Location.objects.filter(processor=processor).first()
#             if processor_location:
#                 location = processor_location.name
#             else:
#                 location = "N/A"
#         elif get_shipment.status== "DISAPPROVED":
#             if get_shipment.sender_processor_type == "T1":
#                 processor = Processor.objects.filter(id=int(get_shipment.processor_idd)).first()
#                 processor_location = Location.objects.filter(processor=processor).first()
#                 if processor_location:
#                     location = processor_location.name
#                 else:
#                     location = "N/A"
#             else:            
#                 processor = Processor2.objects.filter(id=int(get_shipment.processor2_idd)).first()
#                 processor_location = Processor2Location.objects.filter(processor=processor).first()
#                 if processor_location:
#                     location = processor_location.name
#                 else:
#                     location = "N/A"
#         else:
#             location = "In Transit"    
#         select_crop = get_shipment.crop  
#         crops_context = []      
#         return_context = shipmentid_traceability_response(select_crop, get_shipment.shipment_id, from_date, to_date)
#         crop_context = {
#             "crop": select_crop,
#             "origin_context": return_context.get("origin_context", []),
#             "t1_processor": return_context.get("t1_processor", []),
#             "inbound2_wip": return_context.get("inbound2_wip", []),
#             "inbound3_wip": return_context.get("inbound3_wip", []),
#             "inbound4_wip": return_context.get("inbound4_wip", []),
#             "outbound2_wip": return_context.get("outbound2_wip", []),
#             "outbound3_wip": return_context.get("outbound3_wip", []),
#             "outbound4_wip": return_context.get("outbound4_wip", []),
#             "inbound6_wip": [],
#             "outbound6_wip": [],
#             "outbound5_wip": [],
#             "inbound5_wip": []
#         }
            
#         crop_context.update(location_response(crop_context))
#         crop_context.update(grower_location(crop_context))
#         crops_context.append(crop_context)
#         new_context["crops_context"] = crops_context
        
#     elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text).exists():
#         type = "contract_shipment"
#         shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id" ,"processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
#         for shipment in shipments:
#             crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

#             shipment["crops"] = []
#             for crop in crops:
                
#                 additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
#                     shipment_id=shipment["id"],
#                     crop_id=crop["id"]
#                 ).order_by("-id").values("additional_lot_number").first()

#                 shipment["crops"].append({
#                     "crop_name": crop["crop"],
#                     "lot_number": crop["lot_number"],
#                     "net_weight": crop["net_weight"],
#                     "weight_unit": crop["weight_unit"],
#                     "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
#                 })
#             carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
#             shipment["carrier_id"] = carrier.carrier_id  

#         get_shipment = shipments.first()
#         check_lot_entries = list(ProcessorShipmentLotNumberTracking.objects.filter(shipment=get_shipment["id"]).values_list("address", flat=True))
#         if check_lot_entries and get_shipment["status"] != "Received":
#             location = check_lot_entries[-1]
#         elif check_lot_entries and get_shipment["status"] == "Received":
#             if get_shipment["warehouse_id"] not in [None, "null", "", " "]:
#                 destination = Warehouse.objects.filter(id=int(get_shipment["warehouse_id"])).first()
#             else:
#                 destination = Customer.objects.filter(id=int(get_shipment["customer_id"])).first()
#             location = destination.location
#         else:
#             location = "In Transit"
#         if get_shipment["warehouse_id"] not in [None, "null", "", " "]:
            
#             inbound5 = list(shipments)
#             new_context["inbound5_wip"] = inbound5
#             new_context["outbound5_wip"] = inbound5
#             crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
#             processor_entity_name = get_shipment["processor_entity_name"]
#             processor_id = get_shipment["processor_id"]
#             processor_type = get_shipment["processor_type"]
#             crops_context = []
#             for crop in crops:
#                 select_crop = crop.crop
#                 return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                
#                 crop_context = {
#                     "crop": select_crop,
#                     "origin_context": return_context.get("origin_context", []),
#                     "t1_processor": return_context.get("t1_processor", []),
#                     "inbound2_wip": return_context.get("inbound2_wip", []),
#                     "inbound3_wip": return_context.get("inbound3_wip", []),
#                     "inbound4_wip": return_context.get("inbound4_wip", []),
#                     "outbound2_wip": return_context.get("outbound2_wip", []),
#                     "outbound3_wip": return_context.get("outbound3_wip", []),
#                     "outbound4_wip": return_context.get("outbound4_wip", []),
#                     "inbound5_wip": inbound5,
#                     "outbound5_wip": inbound5,
#                     "outbound6_wip": [],
#                     "inbound6_wip": []
#                 }
                
#                 crop_context.update(location_response(crop_context))
#                 crop_context.update(grower_location(crop_context))
#                 crops_context.append(crop_context)
#             new_context["crops_context"] = crops_context
#         else:
             
#             inbound6 = list(shipments)
#             new_context["inbound6_wip"] = inbound6
#             new_context["outbound5_wip"] = inbound6
#             new_context["inbound5_wip"] = []
#             new_context["outbound6_wip"] = []

#             crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
#             crops_context = []
#             processor_entity_name = get_shipment["processor_entity_name"]
#             processor_id = get_shipment["processor_id"]
#             processor_type = get_shipment["processor_type"]
#             for crop in crops:
#                 select_crop = crop.crop
#                 return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                
#                 crop_context = {
#                     "crop": select_crop,
#                     "origin_context": return_context.get("origin_context", []),
#                     "t1_processor": return_context.get("t1_processor", []),
#                     "inbound2_wip": return_context.get("inbound2_wip", []),
#                     "inbound3_wip": return_context.get("inbound3_wip", []),
#                     "inbound4_wip": return_context.get("inbound4_wip", []),
#                     "outbound2_wip": return_context.get("outbound2_wip", []),
#                     "outbound3_wip": return_context.get("outbound3_wip", []),
#                     "outbound4_wip": return_context.get("outbound4_wip", []),
#                     "inbound5_wip": [],
#                     "outbound5_wip": inbound6,
#                     "inbound6_wip": inbound6,
#                     "outbound6_wip": [],
#                 }
                
#                 crop_context.update(location_response(crop_context))
#                 crop_context.update(grower_location(crop_context))
#                 crops_context.append(crop_context)
#             new_context["crops_context"] = crops_context
    
#     elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text).exists():
#         type = "contract_shipment"
#         shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id","shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
#         for shipment in shipments:
#             crops = WarehouseShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

#             shipment["crops"] = []
#             for crop in crops:
                
#                 additional_lot = WarehouseShipmentLotNumberTracking.objects.filter(
#                     shipment_id=shipment["id"],
#                     crop_id=crop["id"]
#                 ).order_by("-id").values("additional_lot_number").first()

#                 shipment["crops"].append({
#                     "crop_name": crop["crop"],
#                     "lot_number": crop["lot_number"],
#                     "net_weight": crop["net_weight"],
#                     "weight_unit": crop["weight_unit"],
#                     "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
#                 })
#             carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
#             shipment["carrier_id"] = carrier.carrier_id  

#         get_shipment = shipments.first()
#         check_lot_entries = list(WarehouseShipmentLotNumberTracking.objects.filter(shipment=get_shipment["id"]).values_list("address", flat=True))
#         if check_lot_entries and get_shipment["status"] != "Received":
#             location = check_lot_entries[-1]
#         elif check_lot_entries and get_shipment["status"] == "Received":
            
#             destination = Customer.objects.filter(id=int(get_shipment["customer_id"])).first()
#             location = destination.location
#         else:
#             location = "In Transit"
#         new_context["inbound6_wip"] = list(shipments)
#         new_context["outbound6_wip"] = list(shipments)
#         crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
#         outbound5_processor = []
#         crops_context = []
#         for crop in crops:
#             select_crop = crop.crop
#             check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
#             if check_processor_shipment:
#                 for shipment in check_processor_shipment:                   
#                     shipment_crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

#                     shipment["crops"] = []
#                     for crop_ in shipment_crops:
                        
#                         additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
#                             shipment_id=shipment["id"],
#                             crop_id=crop_["id"]
#                         ).order_by("-id").values("additional_lot_number").first()

#                         shipment["crops"].append({
#                             "crop_name": crop_["crop"],
#                             "lot_number": crop_["lot_number"],
#                             "net_weight": crop_["net_weight"],
#                             "weight_unit": crop_["weight_unit"],
#                             "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
#                         })
#                     carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
#                     shipment["carrier_id"] = carrier.carrier_id  
#                     outbound5_processor.extend(check_processor_shipment) 
#                     processor_entity_name = shipment["processor_entity_name"]
#                     processor_id = shipment["processor_id"]
#                     processor_type = shipment["processor_type"]                             
#                     return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                    
#                     crop_context = {
#                         "crop": select_crop,
#                         "origin_context": return_context.get("origin_context", []),
#                         "t1_processor": return_context.get("t1_processor", []),
#                         "inbound2_wip": return_context.get("inbound2_wip", []),
#                         "inbound3_wip": return_context.get("inbound3_wip", []),
#                         "inbound4_wip": return_context.get("inbound4_wip", []),
#                         "outbound2_wip": return_context.get("outbound2_wip", []),
#                         "outbound3_wip": return_context.get("outbound3_wip", []),
#                         "outbound4_wip": return_context.get("outbound4_wip", []),
#                         "inbound6_wip": list(shipments),
#                         "outbound6_wip": list(shipments),
#                         "outbound5_wip": list(check_processor_shipment),
#                         "inbound5_wip": list(check_processor_shipment)
#                     }
                    
#                     crop_context.update(location_response(crop_context))
#                     crop_context.update(grower_location(crop_context))
#                     crops_context.append(crop_context)
#                 new_context["crops_context"] = crops_context                                     
                
#         new_context["outbound5_wip"] = outbound5_processor
#         new_context["inbound5_wip"] = outbound5_processor   
                    
#     else:
#         new_context['no_rec_found_msg'] = "No Records Found"  

#     new_context["shipment"] = get_shipment
#     new_context["shipment_type"] = type
#     new_context["from_date"] = from_date
#     new_context["to_date"] = to_date
#     new_context["location"] = location
#     print(new_context)
#     return render(request, 'tracemodule/view_traceability2.html', new_context)


def view_traceability(request, search_text, from_date, to_date):  
    
    new_context = {}
    first_shipment = GrowerShipment.objects.order_by('date_time').first()
    if first_shipment:
        from_date = first_shipment.date_time.date() 
    else:
        from_date = None  
    to_date = date.today() 
    check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text)
                        
    if check_shipment.exists() :        
        type = "grower_shipment"
        get_shipment = check_shipment.first()  

        if get_shipment.status == "APPROVED":
            processor = Processor.objects.filter(id=int(get_shipment.processor.id)).first()
            processor_location = Location.objects.filter(processor=processor).first()
            if processor_location:
                location = processor_location.name
            else:
                location = "N/A"
        elif get_shipment.status== "DISAPPROVED":
            grower = Grower.objects.filter(id=int(get_shipment.grower.id)).first()
            location = grower.physical_address1
        else:
            location = "In Transit"
               
        select_crop = get_shipment.crop
        context = shipmentid_traceability_response(select_crop, get_shipment.shipment_id, from_date, to_date)
        new_context.update(context)    
        context_ = location_response(new_context)                                
        new_context.update(context_) 
    
    elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text).exists():
        type = "processor_shipment"
        shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text)
        get_shipment = shipment.first()  

        if get_shipment.status == "APPROVED":
            processor = Processor2.objects.filter(id=int(get_shipment.processor2_idd)).first()
            processor_location = Processor2Location.objects.filter(processor=processor).first()
            if processor_location:
                location = processor_location.name
            else:
                location = "N/A"
        elif get_shipment.status== "DISAPPROVED":
            if get_shipment.sender_processor_type == "T1":
                processor = Processor.objects.filter(id=int(get_shipment.processor_idd)).first()
                processor_location = Location.objects.filter(processor=processor).first()
                if processor_location:
                    location = processor_location.name
                else:
                    location = "N/A"
            else:            
                processor = Processor2.objects.filter(id=int(get_shipment.processor2_idd)).first()
                processor_location = Processor2Location.objects.filter(processor=processor).first()
                if processor_location:
                    location = processor_location.name
                else:
                    location = "N/A"
        else:
            location = "In Transit"    
        select_crop = get_shipment.crop        
        context = shipmentid_traceability_response(select_crop, get_shipment.shipment_id, from_date, to_date)
          
        new_context.update(context)    
        context_ = location_response(new_context)                                
        new_context.update(context_) 
        
    elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text).exists():
        type = "contract_shipment"
        shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id" ,"processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
        for shipment in shipments:
            crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

            shipment["crops"] = []
            for crop in crops:
                
                additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
                    shipment_id=shipment["id"],
                    crop_id=crop["id"]
                ).order_by("-id").values("additional_lot_number").first()

                shipment["crops"].append({
                    "crop_name": crop["crop"],
                    "lot_number": crop["lot_number"],
                    "net_weight": crop["net_weight"],
                    "weight_unit": crop["weight_unit"],
                    "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                })
            carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
            shipment["carrier_id"] = carrier.carrier_id  

        get_shipment = shipments.first()
        check_lot_entries = list(ProcessorShipmentLotNumberTracking.objects.filter(shipment=get_shipment["id"]).values_list("address", flat=True))
        if check_lot_entries and get_shipment["status"] != "Received":
            location = check_lot_entries[-1]
        elif check_lot_entries and get_shipment["status"] == "Received":
            if get_shipment["warehouse_id"] not in [None, "null", "", " "]:
                destination = Warehouse.objects.filter(id=int(get_shipment["warehouse_id"])).first()
            else:
                destination = Customer.objects.filter(id=int(get_shipment["customer_id"])).first()
            location = destination.location
        else:
            location = "In Transit"
        if get_shipment["warehouse_id"] not in [None, "null", "", " "]:
            
            inbound5 = list(shipments)
            new_context["inbound5_wip"] = inbound5
            new_context["outbound5_wip"] = inbound5
            crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
            processor_entity_name = get_shipment["processor_entity_name"]
            processor_id = get_shipment["processor_id"]
            processor_type = get_shipment["processor_type"]
            for crop in crops:
                select_crop = crop.crop
                return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                
                keys_to_extend = [
                    "origin_context",
                    "t1_processor",
                    "inbound2_wip",
                    "inbound3_wip",
                    "inbound4_wip",
                    "outbound2_wip",
                    "outbound3_wip",
                    "outbound4_wip",
                ]

                for key in keys_to_extend:
                    if return_context.get(key):
                        new_context[key] = new_context.get(key, [])
                        new_context[key].extend(return_context[key])                                      
            
            new_context_ = location_response(new_context)                           
            new_context.update(new_context_)
        else:
             
            inbound6 = list(shipments)
            new_context["inbound6_wip"] = inbound6
            new_context["outbound5_wip"] = inbound6
            new_context["inbound5_wip"] = []
            new_context["outbound6_wip"] = []

            crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])

            processor_entity_name = get_shipment["processor_entity_name"]
            processor_id = get_shipment["processor_id"]
            processor_type = get_shipment["processor_type"]
            for crop in crops:
                select_crop = crop.crop
                return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                
                keys_to_extend = [
                    "origin_context",
                    "t1_processor",
                    "inbound2_wip",
                    "inbound3_wip",
                    "inbound4_wip",
                    "outbound2_wip",
                    "outbound3_wip",
                    "outbound4_wip",
                ]

                for key in keys_to_extend:
                    if return_context.get(key):
                        new_context[key] = new_context.get(key, [])
                        new_context[key].extend(return_context[key])                                      
            
            new_context_ = location_response(new_context)                           
            new_context.update(new_context_)
    
    elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text).exists():
        type = "contract_shipment"
        shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id","shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
        for shipment in shipments:
            crops = WarehouseShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

            shipment["crops"] = []
            for crop in crops:
                
                additional_lot = WarehouseShipmentLotNumberTracking.objects.filter(
                    shipment_id=shipment["id"],
                    crop_id=crop["id"]
                ).order_by("-id").values("additional_lot_number").first()

                shipment["crops"].append({
                    "crop_name": crop["crop"],
                    "lot_number": crop["lot_number"],
                    "net_weight": crop["net_weight"],
                    "weight_unit": crop["weight_unit"],
                    "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                })
            carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
            shipment["carrier_id"] = carrier.carrier_id  

        get_shipment = shipments.first()
        check_lot_entries = list(WarehouseShipmentLotNumberTracking.objects.filter(shipment=get_shipment["id"]).values_list("address", flat=True))
        if check_lot_entries and get_shipment["status"] != "Received":
            location = check_lot_entries[-1]
        elif check_lot_entries and get_shipment["status"] == "Received":
            
            destination = Customer.objects.filter(id=int(get_shipment["customer_id"])).first()
            location = destination.location
        else:
            location = "In Transit"
        new_context["inbound6_wip"] = list(shipments)
        new_context["outbound6_wip"] = list(shipments)
        crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
        outbound5_processor = []
        for crop in crops:
            select_crop = crop.crop
            check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
            if check_processor_shipment:
                for shipment in check_processor_shipment:                   
                    shipment_crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

                    shipment["crops"] = []
                    for crop_ in shipment_crops:
                        
                        additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
                            shipment_id=shipment["id"],
                            crop_id=crop_["id"]
                        ).order_by("-id").values("additional_lot_number").first()

                        shipment["crops"].append({
                            "crop_name": crop_["crop"],
                            "lot_number": crop_["lot_number"],
                            "net_weight": crop_["net_weight"],
                            "weight_unit": crop_["weight_unit"],
                            "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                        })
                    carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                    shipment["carrier_id"] = carrier.carrier_id  
                    outbound5_processor.extend(check_processor_shipment) 
                    processor_entity_name = shipment["processor_entity_name"]
                    processor_id = shipment["processor_id"]
                    processor_type = shipment["processor_type"]                             
                    return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                    
                    keys_to_extend = [
                        "origin_context",
                        "t1_processor",
                        "inbound2_wip",
                        "inbound3_wip",
                        "inbound4_wip",
                        "outbound2_wip",
                        "outbound3_wip",
                        "outbound4_wip",
                    ]

                    for key in keys_to_extend:
                        if return_context.get(key):
                            new_context[key] = new_context.get(key, [])
                            new_context[key].extend(return_context[key])                                     
                
        new_context["outbound5_wip"] = outbound5_processor
        new_context["inbound5_wip"] = outbound5_processor   

        new_context_ = location_response(new_context)                           
        new_context.update(new_context_)                     
    
    else:
        new_context['no_rec_found_msg'] = "No Records Found"  
    
    context_ = grower_location(new_context)
    new_context.update(context_)
    new_context["shipment"] = get_shipment
    new_context["shipment_type"] = type
    new_context["from_date"] = from_date
    new_context["to_date"] = to_date
    new_context["location"] = location
    
    return render(request, 'tracemodule/view_traceability2.html', new_context)


def get_unique_shipments_by_id(shipments):
    """
    Ensures the list of shipments is unique by shipment_id.
    """
    unique_shipments = {}
    for shipment in shipments:
        shipment_id = shipment.get("shipment_id")
        if shipment_id not in unique_shipments:
            unique_shipments[shipment_id] = shipment
    return list(unique_shipments.values())


@login_required()
def export_all_csv_for_shipmentID(request, search_text, from_date, to_date):
    
    filename = 'TRACEABILITY REPORT.csv'
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
    )
    writer = csv.writer(response)
    new_context = {}
    
    check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text)
                        
    if check_shipment.exists() :
        
        get_shipment = check_shipment.values().first()            
        select_crop = get_shipment["crop"]
        context = shipmentid_traceability_response(select_crop, get_shipment["shipment_id"], from_date, to_date)
        new_context.update(context)

    elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text).exists():
        
        shipment = ShipmentManagement.objects.filter(shipment_id__icontains=search_text)
        get_shipment = shipment.values().first()       
        select_crop = get_shipment["crop"]        
        context = shipmentid_traceability_response(select_crop, get_shipment["shipment_id"], from_date, to_date)
          
        new_context.update(context)

    elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text).exists():
       
        shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id" ,"processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
        
        for shipment in shipments:
            crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

            # Add crops and their additional lot numbers to the shipment
            shipment["crops"] = []
            for crop in crops:
                
                additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
                    shipment_id=shipment["id"],
                    crop_id=crop["id"]
                ).order_by("-id").values("additional_lot_number").first()

                shipment["crops"].append({
                    "crop_name": crop["crop"],
                    "lot_number": crop["lot_number"],
                    "net_weight": crop["net_weight"],
                    "weight_unit": crop["weight_unit"],
                    "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                })
            carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
            shipment["carrier_id"] = carrier.carrier_id  
        get_shipment = shipments.first()
        if get_shipment["warehouse_id"] not in [None, "null", "", " "]:
            shipments = get_unique_shipments_by_id(shipments)
            inbound5 = list(shipments)
            new_context["inbound5_wip"] = inbound5
            new_context["outbound5_wip"] = inbound5
            crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])           
            
            processor_entity_name = get_shipment["processor_entity_name"]
            processor_id = get_shipment["processor_id"]
            processor_type = get_shipment["processor_type"]
            for crop in crops:
                select_crop = crop.crop
                return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                
                keys_to_extend = [
                    "origin_context",
                    "t1_processor",
                    "inbound2_wip",
                    "inbound3_wip",
                    "inbound4_wip",
                    "outbound2_wip",
                    "outbound3_wip",
                    "outbound4_wip",
                ]

                for key in keys_to_extend:
                    if return_context.get(key):
                        new_context[key] = new_context.get(key, [])
                        new_context[key].extend(return_context[key])                                    
            
               
        else:
            shipments = get_unique_shipments_by_id(shipments)
            inbound6 = shipments
            new_context["inbound6_wip"] = inbound6
            new_context["outbound5_wip"] = inbound6
            new_context["inbound5_wip"] = []
            new_context["outbound6_wip"] = []

            crops = ProcessorShipmentCrops.objects.filter(shipment_id=get_shipment["id"])

            processor_entity_name = get_shipment["processor_entity_name"]
            processor_id = get_shipment["processor_id"]
            processor_type = get_shipment["processor_type"]
            for crop in crops:
                select_crop = crop.crop
                return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                
                keys_to_extend = [
                    "origin_context",
                    "t1_processor",
                    "inbound2_wip",
                    "inbound3_wip",
                    "inbound4_wip",
                    "outbound2_wip",
                    "outbound3_wip",
                    "outbound4_wip",
                ]

                for key in keys_to_extend:
                    if return_context.get(key):
                        new_context[key] = new_context.get(key, [])
                        new_context[key].extend(return_context[key])                                      
    
    elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text).exists():
        
        shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text).values("id","warehouse_shipment_crop__crop","contract__secret_key","contract_id", "shipment_id", "warehouse_id", "customer_id","warehouse_name","customer_name", "date_pulled", "carrier_type", "customer_receive_date", "status")
        
        for shipment in shipments:
            shipment_crops = WarehouseShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

            # Add crops and their additional lot numbers to the shipment
            shipment["crops"] = []
            for crop_ in shipment_crops:
                
                additional_lot = WarehouseShipmentLotNumberTracking.objects.filter(
                    shipment_id=shipment["id"],
                    crop_id=crop_["id"]
                ).order_by("-id").values("additional_lot_number").first()

                shipment["crops"].append({
                    "crop_name": crop_["crop"],
                    "lot_number": crop_["lot_number"],
                    "net_weight": crop_["net_weight"],
                    "weight_unit": crop_["weight_unit"],
                    "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                })
            carrier = CarrierDetails2.objects.filter(shipment_id=shipment["id"]).first() 
            shipment["carrier_id"] = carrier.carrier_id  

        get_shipment = shipments.first()
        shipments = get_unique_shipments_by_id(shipments)
        new_context["inbound6_wip"] = list(shipments)
        new_context["outbound6_wip"] = list(shipments)
        crops = WarehouseShipmentCrops.objects.filter(shipment_id=get_shipment["id"])
        outbound5_processor = []
        for crop in crops:
            select_crop = crop.crop
            check_processor_shipment = ProcessorWarehouseShipment.objects.filter(warehouse_id=get_shipment["warehouse_id"], processor_shipment_crop__crop=crop.crop, processor_shipment_crop__crop_type=crop.crop_type).values("id","processor_shipment_crop__crop", "contract__secret_key","contract_id", "processor_entity_name","processor_type", "processor_id", "shipment_id", "warehouse_id", "warehouse_name","customer_name","customer_id", "date_pulled", "carrier_type", "distributor_receive_date", "status")
            if check_processor_shipment:
                check_processor_shipment = get_unique_shipments_by_id(check_processor_shipment)
                for shipment in check_processor_shipment:                   
                    shipment_crops = ProcessorShipmentCrops.objects.filter(shipment_id=shipment["id"]).values("id", "crop","lot_number", "net_weight", "weight_unit" )

                    # Add crops and their additional lot numbers to the shipment
                    shipment["crops"] = []
                    for crop_ in shipment_crops:
                        
                        additional_lot = ProcessorShipmentLotNumberTracking.objects.filter(
                            shipment_id=shipment["id"],
                            crop_id=crop_["id"]
                        ).order_by("-id").values("additional_lot_number").first()

                        shipment["crops"].append({
                            "crop_name": crop_["crop"],
                            "lot_number": crop_["lot_number"],
                            "net_weight": crop_["net_weight"],
                            "weight_unit": crop_["weight_unit"],
                            "additional_lot_number": additional_lot["additional_lot_number"] if additional_lot else None,
                        })
                    carrier = CarrierDetails.objects.filter(shipment_id=shipment["id"]).first() 
                    shipment["carrier_id"] = carrier.carrier_id  
                    outbound5_processor.extend(check_processor_shipment) 
                    processor_entity_name = shipment["processor_entity_name"]
                    processor_id = shipment["processor_id"]
                    processor_type = shipment["processor_type"]                             
                    return_context = processor_traceability_report(select_crop, processor_id, processor_type, from_date, to_date, processor_entity_name)
                    
                    keys_to_extend = [
                        "origin_context",
                        "t1_processor",
                        "inbound2_wip",
                        "inbound3_wip",
                        "inbound4_wip",
                        "outbound2_wip",
                        "outbound3_wip",
                        "outbound4_wip",
                    ]

                    for key in keys_to_extend:
                        if return_context.get(key):
                            new_context[key] = new_context.get(key, [])
                            new_context[key].extend(return_context[key])                                   
                
        new_context["outbound5_wip"] = outbound5_processor
        new_context["inbound5_wip"] = outbound5_processor  

    writer.writerow([f"Shipment ID = {get_shipment['shipment_id']}"])
    writer.writerow([""])
    
    excluded_key = "no_rec_found_msg" 
    filtered_context = {key: value for key, value in new_context.items() if key != excluded_key}
   
    headers = []

    if "origin_context" in filtered_context and len(filtered_context["origin_context"]) > 0:
            headers.extend(["Origin: Field", "Grower"])

    if "t1_processor" in filtered_context and len(filtered_context["t1_processor"]) > 0:
        headers.extend(["Inbound Mill: Shipment ID", "Crop", "Weight", "Date", "Grower"])
    
    if "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"]) > 0 and "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"])> 0:
        headers.extend(["In Mill: Mill", "Shipment ID", "Crop", "Weight", "Lot Number"])
    
    elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0 and "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"])> 0:
        headers.extend(["In Mill: Mill", "Shipment ID", "Crop", "Weight", "Lot Number"])

    elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0 and "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"])> 0:
        headers.extend(["In Mill: Mill", "Shipment ID", "Crop", "Weight","Lot Number"]) 

    elif "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"]) > 0:
        headers.extend(["In Mill: Mill", "Shipment ID","Crop", "Weight", "Lot Number"])

    elif "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"]) > 0:
        headers.extend(["In Mill: Mill", "Shipment ID","Crop", "Weight", "Lot Number"])

    elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0:
        headers.extend(["In Mill: Mill", "Shipment ID", "Crop", "Weight","Lot Number"])

    if "outbound5_wip" in filtered_context and len(filtered_context["outbound5_wip"]) > 0:
        headers.extend(["Assigned Lot Number: Mill", "Crop", "Weight","Lot Number", "Shipment ID"])
        headers.extend(["Shipped To Warehouse/Customer: Shipment ID", "Crop", "Weight", "Transit ID", "New Lot Number", "Date"])

    if "inbound5_wip" in filtered_context and len(filtered_context["inbound5_wip"]) > 0:
        headers.extend(["Received By Warehouse: Warehouse Name", "Warehouse ID", "Receive Date", "Crop", "Weight", "Shipment ID"])

    if "outbound6_wip" in filtered_context and len(filtered_context["outbound6_wip"]) > 0:
        headers.extend(["Shipped To Customer: Shipment ID", "Crop", "Weight", "Transit ID", "New Lot Number", "Date"])

    if "inbound6_wip" in filtered_context and len(filtered_context["inbound6_wip"]) > 0:
        headers.extend(["Received By Customer: Customer Name", "Customer ID", "Receive Date", "Crop", "Weight", "Shipment ID"])

    writer.writerow(headers)
    writer.writerow([""])
    
    origin_context = new_context.get("origin_context", [])
    t1_processor = new_context.get("t1_processor", [])
    outbound5 = new_context.get("outbound5_wip", [])
    inbound5 = new_context.get("inbound5_wip", [])
    outbound6 = new_context.get("outbound6_wip", [])
    inbound6 = new_context.get("inbound6_wip", [])
    in_mill_data = []

    if "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"]) > 0 and "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"])> 0 :
            in_mill_data = new_context.get("inbound4_wip")

    elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0 and "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"])> 0 :
        in_mill_data = new_context.get("inbound4_wip")

    elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0 and "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"])> 0:
        in_mill_data = new_context.get("inbound3_wip")   

    elif "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"]) > 0:
        in_mill_data = new_context.get("inbound4_wip")  

    elif "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"]) > 0 :
        in_mill_data = new_context.get("inbound3_wip")   
    
    elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0:
        in_mill_data = new_context.get("inbound2_wip")
    
    max_rows = max(len(origin_context), len(t1_processor),len(in_mill_data),len(outbound5), len(inbound5), len(outbound6), len(inbound6))
    
   # Populate rows dynamically
    for i in range(max_rows):
        row = []

        # Origin Data
        if "Origin: Field" in headers and "Grower" in headers:
            if i < len(origin_context):
                origin = origin_context[i]
                row.extend([
                    origin.get("field_name", ""), origin.get("grower_name", "")
                ])
            else:
                row.extend([""] * 2)

        # T1 Processor Data
        if "Inbound Mill: Shipment ID" in headers:
            if i < len(t1_processor):
                t1_processor_data = t1_processor[i]
                crop_data = f'{t1_processor_data.get("crop", "")}'
                print(format_date(t1_processor_data.get("date", "")))
                weight_data = f'{t1_processor_data.get("pounds_received") if t1_processor_data.get("pounds_received") not in ["None", None, "", "null"] else t1_processor_data.get("pounds_shipped")} {t1_processor_data.get("unit", "")}'
                row.extend([
                    t1_processor_data.get("shipment_id", ""), crop_data, weight_data, format_date(t1_processor_data.get("date", "")), t1_processor_data.get("grower", "")
                ])
            else:
                row.extend([""] * 5)

        # In Mill Data
        if "In Mill: Mill" in headers:
            if i < len(in_mill_data):
                mill_data = in_mill_data[i]
                crop_data = f'{mill_data.get("crop", "")}'
                weight_data = f'{mill_data.get("received_weight") if mill_data.get("received_weight") else mill_data.get("weight_or_product")} {mill_data.get("weight_of_product_unit", "")}'
                row.extend([
                    mill_data.get("processor2_name", ""), mill_data.get("shipment_id", ""), crop_data, weight_data, mill_data.get("lot_number", "")
                ])
            else:
                row.extend([""] * 5)
        
        # Outbound5 Data
        if "Assigned Lot Number: Mill" in headers:
            if i < len(outbound5):
                outbound5_data = outbound5[i]
                crop_data = "\n".join(
                    f"{crop['crop_name']}" 
                    for crop in outbound5_data.get("crops", [])
                )
                weight_data = "\n".join(
                    f"{crop['net_weight']} {crop['weight_unit']}"
                    for crop in outbound5_data.get("crops", [])
                )
                lot_number_data = "\n".join(
                    f"{crop['lot_number']}"
                    for crop in outbound5_data.get("crops", [])
                )
                row.extend([
                    outbound5_data.get("processor_entity_name", ""), crop_data, weight_data, lot_number_data, outbound5_data.get("shipment_id")
                ])
            else:
                row.extend([""] * 5)
                
        if "Shipped To Warehouse/Customer: Shipment ID" in headers:
            if i < len(outbound5):
                outbound5_data = outbound5[i]                
                crop_data = "\n".join(
                    f"{crop['crop_name']}" 
                    for crop in outbound5_data.get("crops", [])
                )
                weight_data = "\n".join(
                    f"{crop['net_weight']} {crop['weight_unit']}"
                    for crop in outbound5_data.get("crops", [])
                )
                new_lot_number_data = "\n".join(
                    f"{crop['additional_lot_number']}"
                    for crop in outbound5_data.get("crops", [])
                )
                row.extend([
                    outbound5_data.get("shipment_id", ""), crop_data, weight_data, outbound5_data.get("carrier_id", ""), 
                    new_lot_number_data, format_date(outbound5_data.get("date_pulled", ""))
                ])
            else:
                row.extend([""] * 6)

        # Inbound5 Data
        if "Received By Warehouse: Warehouse Name" in headers:
            if i < len(inbound5):
                inbound5_data = inbound5[i]
                crop_data = "\n".join(
                    f"{crop['crop_name']}" 
                    for crop in inbound5_data.get("crops", [])
                )
                weight_data = "\n".join(
                    f"{crop['net_weight']} {crop['weight_unit']}"
                    for crop in inbound5_data.get("crops", [])
                )
                row.extend([
                    inbound5_data.get("warehouse_name", ""), inbound5_data.get("warehouse_id", ""), 
                    format_date(inbound5_data.get("distributor_receive_date", "")), crop_data, weight_data, inbound5_data.get("shipment_id", "")
                ])
            else:
                row.extend([""] * 6)

        # Outbound6 Data
        if "Shipped To Customer: Shipment ID" in headers:
            if i < len(outbound6):
                outbound6_data = outbound6[i]
                crop_data = "\n".join(
                    f"{crop['crop_name']}" 
                    for crop in outbound6_data.get("crops", [])
                )
                weight_data = "\n".join(
                    f"{crop['net_weight']} {crop['weight_unit']}"
                    for crop in outbound6_data.get("crops", [])
                )
                new_lot_number_data = "\n".join(
                    f"{crop['additional_lot_number']}"
                    for crop in outbound6_data.get("crops", [])
                )
                row.extend([
                    outbound6_data.get("shipment_id", ""), crop_data, weight_data, outbound6_data.get("carrier_id", ""), 
                    new_lot_number_data, format_date(outbound6_data.get("date_pulled", ""))
                ])
            else:
                row.extend([""] * 6)

        # Inbound6 Data
        if "Received By Customer: Customer Name" in headers:
            if i < len(inbound6):
                inbound6_data = inbound6[i]
                crop_data = "\n".join(
                    f"{crop['crop_name']}" 
                    for crop in inbound6_data.get("crops", [])
                )
                weight_data = "\n".join(
                    f"{crop['net_weight']} {crop['weight_unit']}"
                    for crop in inbound6_data.get("crops", [])
                )
                row.extend([
                    inbound6_data.get("customer_name", ""), inbound6_data.get("customer_id", ""), 
                    format_date(inbound6_data.get("customer_receive_date", "")), crop_data, weight_data, inbound6_data.get("shipment_id", "")
                ])
            else:
                row.extend([""] * 6)

        # Write the row to the CSV
        writer.writerow(row)

    return response


@login_required()
def generate_csv_for_multiple_shipments(request, search_text, get_search_by, from_date, to_date, select_crop=None):
    new_context = {}
    filename = 'TRACE MODULE.csv'
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
    )
    writer = csv.writer(response)

    # search by Grower ....
    if get_search_by and get_search_by == 'grower' :
        check_grower = Grower.objects.filter(name__icontains=search_text)
        if check_grower.exists() :
            grower_id = check_grower.first().id
            shipments = GrowerShipment.objects.filter(grower_id=grower_id)
            if select_crop:
                shipments = GrowerShipment.objects.filter(grower_id=grower_id, crop=select_crop)                            
        else:
            context['no_rec_found_msg'] = "No Records Found"

    # search by Field ....
    elif get_search_by and get_search_by == 'field' :
        check_field = Field.objects.filter(name__icontains=search_text)
        if check_field.exists() :                    
            field_id = check_field.first().id                  
            grower_id =  check_field.first().grower.id
            shipments = GrowerShipment.objects.filter(grower_id=grower_id, field_id=field_id)
            if select_crop:
                shipments = GrowerShipment.objects.filter(grower_id=grower_id, field_id=field_id, crop=select_crop)
                                                                          
        else:
            context['no_rec_found_msg'] = "No Records Found"
    
    # search by Processor ....
    elif get_search_by and get_search_by == 'processor' :
        check_processor = get_processor_type(search_text)
        if check_processor:
            processor_type = check_processor["type"]
            processor_id = check_processor["id"]
            if processor_type == "T1":
                inbound_shipments = GrowerShipment.objects.filter(processor_id=processor_id)
            else:
                inbound_shipments = ShipmentManagement.objects.filter(processor2_idd=processor_id, sender_processor_type=processor_type)
            outbound_shipments = ShipmentManagement.objects.filter(processor_idd=processor_id, sender_processor_type=processor_type)
            
            contract_shipments = ProcessorWarehouseShipment.objects.filter(processor_id=processor_id, processor_type=processor_type)
            if select_crop:
                if processor_type == "T1":
                    inbound_shipments = GrowerShipment.objects.filter(processor_id=processor_id, crop=select_crop)
                else:
                    inbound_shipments = ShipmentManagement.objects.filter(processor2_idd=processor_id, sender_processor_type=processor_type, crop=select_crop)
                
                outbound_shipments = ShipmentManagement.objects.filter(processor_idd=processor_id, sender_processor_type=processor_type, crop=select_crop)
                
                contract_shipments = ProcessorWarehouseShipment.objects.filter(processor_id=processor_id, processor_type=processor_type, processor_shipment_crop__crop=select_crop)
            
            shipments = list(outbound_shipments) + list(contract_shipments) + list(inbound_shipments)                              
            
        else:
            context['no_rec_found_msg'] = "No Records Found"
    
    # search by SKU Id ....
    elif get_search_by and get_search_by == 'sku_id':
        grower_shipments = GrowerShipment.objects.filter(sku__icontains=search_text)
        processor_shipments = ShipmentManagement.objects.filter(Q(storage_bin_send__icontains=search_text) | Q(storage_bin_recive__icontains=search_text))                               
        shipments = list(grower_shipments) + list(processor_shipments)    

    # search by Delivery Id ....
    elif get_search_by and get_search_by == 'deliveryid' :                                  
        check_shipment = GrowerShipment.objects.filter(shipment_id__icontains=search_text)
        
        if check_shipment.exists() :
            shipments = check_shipment
            if select_crop:
                shipments = check_shipment.filter(crop=select_crop)           

        elif not check_shipment and ShipmentManagement.objects.filter(shipment_id__icontains=search_text).exists():
            shipments = ShipmentManagement.objects.filter(shipment_id__icontains=search_text)
            if select_crop:
                shipments = ShipmentManagement.objects.filter(shipment_id__icontains=search_text, crop=select_crop)                     
            
        elif not check_shipment and ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text).exists():                    
            shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text)
            if select_crop:
                shipments = ProcessorWarehouseShipment.objects.filter(shipment_id__icontains=search_text, processor_shipment_crop__crop=select_crop)
             
        elif not check_shipment and WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text).exists():
            shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text)
            if select_crop:
                shipments = WarehouseCustomerShipment.objects.filter(shipment_id__icontains=search_text, warehouse_shipment_crop__crop=select_crop)
                                                        
        else:
            context['no_rec_found_msg'] = "No Records Found"   

    # search by Warehouse....
    elif get_search_by and get_search_by == 'warehouse':
        
        check_warehouse = Warehouse.objects.filter(name__icontains=search_text)
        if check_warehouse.exists():                            
            warehouse = check_warehouse.first()                            
            inbound_shipments = ProcessorWarehouseShipment.objects.filter( warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date)
            if select_crop:
                inbound_shipments = ProcessorWarehouseShipment.objects.filter(prcessor_shipment_crop__crop=select_crop, warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date)
            
            outbound_shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date)
            if select_crop:
                outbound_shipments = WarehouseCustomerShipment.objects.filter(warehouse_shipment_crop__crop=select_crop,warehouse_id=warehouse.id, date_pulled__date__gte=from_date, date_pulled__date__lte=to_date)

            shipments = list(inbound_shipments) + list(outbound_shipments)       
            
        else:
            context['no_rec_found_msg'] = "No Records Found"
                
    # search by Customer....
    elif get_search_by and get_search_by == 'customer':
        
        check_customer = Customer.objects.filter(name__icontains=search_text)
        if check_customer.exists():
            customer = check_customer.first()                   
            
            processor_shipments = ProcessorWarehouseShipment.objects.filter(                        
                customer_id=customer.id, 
                date_pulled__date__gte=from_date, 
                date_pulled__date__lte=to_date
            )
            if select_crop:
                processor_shipments = ProcessorWarehouseShipment.objects.filter( 
                processor_shipment_crop__crop=select_crop,                       
                customer_id=customer.id, 
                date_pulled__date__gte=from_date, 
                date_pulled__date__lte=to_date
                )           
                
            warehouse_shipments = WarehouseCustomerShipment.objects.filter(                         
                customer_id=customer.id, 
                date_pulled__date__gte=from_date, 
                date_pulled__date__lte=to_date
            )
            if select_crop:
                warehouse_shipments = WarehouseCustomerShipment.objects.filter(
                warehouse_shipment_crop__crop=select_crop,                         
                customer_id=customer.id, 
                date_pulled__date__gte=from_date, 
                date_pulled__date__lte=to_date
                )

            shipments=  list(processor_shipments) + list(warehouse_shipments )                    
                
        else:
            context['no_rec_found_msg'] = "No Records Found" 
            
    shipment_ids = []
    for shipment in shipments:
        shipment_ids.append(shipment.shipment_id)
    for shipment_id in shipment_ids:
        
        context = shipmentid_response(shipment_id, from_date, to_date)
        new_context.update(context)
        writer.writerow([""])
        writer.writerow([f"Shipment ID = {shipment_id}"])
        writer.writerow([""])

        excluded_key = "no_rec_found_msg" 
        filtered_context = {key: value for key, value in new_context.items() if key != excluded_key}
    
        headers = []
        
        if "origin_context" in filtered_context and len(filtered_context["origin_context"]) > 0:
            headers.extend(["Origin: Field", "Grower"])

        if "t1_processor" in filtered_context and len(filtered_context["t1_processor"]) > 0:
            headers.extend(["Inbound Mill: Shipment ID", "Crop", "Weight", "Date", "Grower"])
        
        if "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"]) > 0 and "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"])> 0:
            headers.extend(["In Mill: Mill", "Shipment ID", "Crop", "Weight", "Lot Number"])
        
        elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0 and "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"])> 0:
            headers.extend(["In Mill: Mill", "Shipment ID", "Crop", "Weight", "Lot Number"])

        elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0 and "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"])> 0:
            headers.extend(["In Mill: Mill", "Shipment ID", "Crop", "Weight","Lot Number"]) 

        elif "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"]) > 0:
            headers.extend(["In Mill: Mill", "Shipment ID","Crop", "Weight", "Lot Number"])

        elif "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"]) > 0:
            headers.extend(["In Mill: Mill", "Shipment ID","Crop", "Weight", "Lot Number"])

        elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0:
            headers.extend(["In Mill: Mill", "Shipment ID", "Crop", "Weight","Lot Number"])

        if "outbound5_wip" in filtered_context and len(filtered_context["outbound5_wip"]) > 0:
            headers.extend(["Assigned Lot Number: Mill", "Crop", "Weight","Lot Number", "Shipment ID"])
            headers.extend(["Shipped To Warehouse/Customer: Shipment ID", "Crop", "Weight", "Transit ID", "New Lot Number", "Date"])

        if "inbound5_wip" in filtered_context and len(filtered_context["inbound5_wip"]) > 0:
            headers.extend(["Received By Warehouse: Warehouse Name", "Warehouse ID", "Receive Date", "Crop", "Weight", "Shipment ID"])

        if "outbound6_wip" in filtered_context and len(filtered_context["outbound6_wip"]) > 0:
            headers.extend(["Shipped To Customer: Shipment ID", "Crop", "Weight", "Transit ID", "New Lot Number", "Date"])

        if "inbound6_wip" in filtered_context and len(filtered_context["inbound6_wip"]) > 0:
            headers.extend(["Received By Customer: Customer Name", "Customer ID", "Receive Date", "Crop", "Weight", "Shipment ID"])

        writer.writerow(headers)
        writer.writerow([""])
        
        origin_context = new_context.get("origin_context", [])
        t1_processor = new_context.get("t1_processor", [])
        outbound5 = new_context.get("outbound5_wip", [])
        inbound5 = new_context.get("inbound5_wip", [])
        outbound6 = new_context.get("outbound6_wip", [])
        inbound6 = new_context.get("inbound6_wip", [])
        in_mill_data = []

        if "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"]) > 0 and "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"])> 0 :
            in_mill_data = new_context.get("inbound4_wip")

        elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0 and "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"])> 0 :
            in_mill_data = new_context.get("inbound4_wip")

        elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0 and "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"])> 0:
            in_mill_data = new_context.get("inbound3_wip")   

        elif "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"]) > 0:
            in_mill_data = new_context.get("inbound4_wip")  

        elif "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"]) > 0 :
            in_mill_data = new_context.get("inbound3_wip")   
        
        elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0:
            in_mill_data = new_context.get("inbound2_wip")
        
        max_rows = max(len(origin_context), len(t1_processor),len(in_mill_data),len(outbound5), len(inbound5), len(outbound6), len(inbound6))
        
    # Populate rows dynamically
        for i in range(max_rows):
            row = []

            # Origin Data
            if "Origin: Field" in headers and "Grower" in headers:
                if i < len(origin_context):
                    origin = origin_context[i]
                    row.extend([
                        origin.get("field_name", ""), origin.get("grower_name", "")
                    ])
                else:
                    row.extend([""] * 2)

            # T1 Processor Data
            if "Inbound Mill: Shipment ID" in headers:
                if i < len(t1_processor):
                    t1_processor_data = t1_processor[i]
                    crop_data = f'{t1_processor_data.get("crop", "")}'
                    weight_data = f'{t1_processor_data.get("pounds_received") if t1_processor_data.get("pounds_received") not in ["None", None, "", "null"] else t1_processor_data.get("pounds_shipped")} {t1_processor_data.get("unit", "")}'
                    row.extend([
                        t1_processor_data.get("shipment_id", ""), crop_data, weight_data, format_date(t1_processor_data.get("date", "")), t1_processor_data.get("grower", "")
                    ])
                else:
                    row.extend([""] * 5)

            # In Mill Data
            if "In Mill: Mill" in headers:
                if i < len(in_mill_data):
                    mill_data = in_mill_data[i]
                    crop_data = f'{mill_data.get("crop", "")}'
                    weight_data = f'{mill_data.get("received_weight") if mill_data.get("received_weight") else mill_data.get("weight_or_product")} {mill_data.get("weight_of_product_unit", "")}'
                    row.extend([
                        mill_data.get("processor2_name", ""), mill_data.get("shipment_id", ""), crop_data, weight_data, mill_data.get("lot_number", "")
                    ])
                else:
                    row.extend([""] * 5)
            
            # Outbound5 Data
            if "Assigned Lot Number: Mill" in headers:
                if i < len(outbound5):
                    outbound5_data = outbound5[i]
                    crop_data = "\n".join(
                        f"{crop['crop_name']}" 
                        for crop in outbound5_data.get("crops", [])
                    )
                    weight_data = "\n".join(
                        f"{crop['net_weight']} {crop['weight_unit']}"
                        for crop in outbound5_data.get("crops", [])
                    )
                    lot_number_data = "\n".join(
                        f"{crop['lot_number']}"
                        for crop in outbound5_data.get("crops", [])
                    )
                    row.extend([
                        outbound5_data.get("processor_entity_name", ""), crop_data, weight_data, lot_number_data, outbound5_data.get("shipment_id")
                    ])
                else:
                    row.extend([""] * 5)
                    
            if "Shipped To Warehouse/Customer: Shipment ID" in headers:
                if i < len(outbound5):
                    outbound5_data = outbound5[i]                
                    crop_data = "\n".join(
                        f"{crop['crop_name']}" 
                        for crop in outbound5_data.get("crops", [])
                    )
                    weight_data = "\n".join(
                        f"{crop['net_weight']} {crop['weight_unit']}"
                        for crop in outbound5_data.get("crops", [])
                    )
                    new_lot_number_data = "\n".join(
                        f"{crop['additional_lot_number']}"
                        for crop in outbound5_data.get("crops", [])
                    )
                    row.extend([
                        outbound5_data.get("shipment_id", ""), crop_data, weight_data, outbound5_data.get("carrier_id", ""), 
                        new_lot_number_data, format_date(outbound5_data.get("date_pulled", ""))
                    ])
                else:
                    row.extend([""] * 6)

            # Inbound5 Data
            if "Received By Warehouse: Warehouse Name" in headers:
                if i < len(inbound5):
                    inbound5_data = inbound5[i]
                    crop_data = "\n".join(
                        f"{crop['crop_name']}" 
                        for crop in inbound5_data.get("crops", [])
                    )
                    weight_data = "\n".join(
                        f"{crop['net_weight']} {crop['weight_unit']}"
                        for crop in inbound5_data.get("crops", [])
                    )
                    row.extend([
                        inbound5_data.get("warehouse_name", ""), inbound5_data.get("warehouse_id", ""), 
                        format_date(inbound5_data.get("distributor_receive_date", "")), crop_data, weight_data, inbound5_data.get("shipment_id", "")
                    ])
                else:
                    row.extend([""] * 6)

            # Outbound6 Data
            if "Shipped To Customer: Shipment ID" in headers:
                if i < len(outbound6):
                    outbound6_data = outbound6[i]
                    crop_data = "\n".join(
                        f"{crop['crop_name']}" 
                        for crop in outbound6_data.get("crops", [])
                    )
                    weight_data = "\n".join(
                        f"{crop['net_weight']} {crop['weight_unit']}"
                        for crop in outbound6_data.get("crops", [])
                    )
                    new_lot_number_data = "\n".join(
                        f"{crop['additional_lot_number']}"
                        for crop in outbound6_data.get("crops", [])
                    )
                    row.extend([
                        outbound6_data.get("shipment_id", ""), crop_data, weight_data, outbound6_data.get("carrier_id", ""), 
                        new_lot_number_data, format_date(outbound6_data.get("date_pulled", ""))
                    ])
                else:
                    row.extend([""] * 6)

            # Inbound6 Data
            if "Received By Customer: Customer Name" in headers:
                if i < len(inbound6):
                    inbound6_data = inbound6[i]
                    crop_data = "\n".join(
                        f"{crop['crop_name']}" 
                        for crop in inbound6_data.get("crops", [])
                    )
                    weight_data = "\n".join(
                        f"{crop['net_weight']} {crop['weight_unit']}"
                        for crop in inbound6_data.get("crops", [])
                    )
                    row.extend([
                        inbound6_data.get("customer_name", ""), inbound6_data.get("customer_id", ""), 
                        format_date(inbound6_data.get("customer_receive_date", "")), crop_data, weight_data, inbound6_data.get("shipment_id", "")
                    ])
                else:
                    row.extend([""] * 6)

            # Write the row to the CSV
            writer.writerow(row)
            
    return response


@login_required()
def generate_csv_for_recent_shipments(request, from_date, to_date):
    new_context = {}
    filename = 'RECENT SHIPMENTS TRACEABILITY.csv'
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
    )
    writer = csv.writer(response)

    grower_shipments = GrowerShipment.objects.values(
        'id', 'date_time', 'shipment_id', 'grower__name','grower_id','processor__id', 'processor__entity_name', 'approval_date', 'status', 'crop'
    ).annotate(
        date_field=F('date_time'),
        shipment_type=Value('GrowerShipment')
    )
    
    processor_shipments = ShipmentManagement.objects.values(
        'id', 'date_pulled', 'shipment_id', 'processor_idd', 'processor_e_name', 'processor2_idd', 'processor2_name', 'recive_delivery_date', 'crop', 'status', 'lot_number'
    ).annotate(
        date_field=F('date_pulled'),
        shipment_type=Value('ShipmentManagement')
    )
   
    contract_processor_shipments = ProcessorWarehouseShipment.objects.values(
        'id', 'date_pulled', 'shipment_id', 'processor_id', 'processor_entity_name', 'warehouse_id', 'warehouse_name', 'customer_id', 'customer_name', 'status', 'distributor_receive_date'
    ).annotate(
        date_field=F('date_pulled'),
        shipment_type=Value('ProcessorWarehouseShipment')
    )
   
    contract_warehouse_shipments = WarehouseCustomerShipment.objects.values(
        'id', 'date_pulled', 'shipment_id', 'warehouse_id', 'warehouse_name', 'customer_id', 'customer_name', 'status', 'customer_receive_date', 
    ).annotate(
        date_field=F('date_pulled'),
        shipment_type=Value('WarehouseCustomerShipment')
    )
   
    combined_shipments = chain(
        grower_shipments,
        processor_shipments,
        contract_processor_shipments,
        contract_warehouse_shipments,
    )
    sorted_shipments = sorted(combined_shipments, key=itemgetter('date_field'), reverse=True)

    recent_shipments = sorted_shipments[:10]
    first_shipment = GrowerShipment.objects.order_by('date_time').first()
    if first_shipment:
        from_date = first_shipment.date_time.date() 
    else:
        from_date = None  
    to_date = date.today()  
    

    shipment_ids = []
    for shipment in recent_shipments:
        shipment_ids.append(shipment['shipment_id'])
    for shipment_id in shipment_ids:
        
        context = shipmentid_response(shipment_id, from_date, to_date)
        new_context.update(context)
        writer.writerow([""])
        writer.writerow([f"Shipment ID = {shipment_id}"])
        writer.writerow([""])

        excluded_key = "no_rec_found_msg" 
        filtered_context = {key: value for key, value in new_context.items() if key != excluded_key}
    
        headers = []

        if "origin_context" in filtered_context and len(filtered_context["origin_context"]) > 0:
            headers.extend(["Origin: Field", "Grower"])

        if "t1_processor" in filtered_context and len(filtered_context["t1_processor"]) > 0:
            headers.extend(["Inbound Mill: Shipment ID", "Crop", "Weight", "Date", "Grower"])
        
        if "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"]) > 0 and "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"])> 0:
            headers.extend(["In Mill: Mill", "Shipment ID", "Crop", "Weight", "Lot Number"])
        
        elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0 and "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"])> 0:
            headers.extend(["In Mill: Mill", "Shipment ID", "Crop", "Weight", "Lot Number"])

        elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0 and "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"])> 0:
            headers.extend(["In Mill: Mill", "Shipment ID", "Crop", "Weight","Lot Number"]) 

        elif "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"]) > 0:
            headers.extend(["In Mill: Mill", "Shipment ID","Crop", "Weight", "Lot Number"])

        elif "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"]) > 0:
            headers.extend(["In Mill: Mill", "Shipment ID","Crop", "Weight", "Lot Number"])

        elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0:
            headers.extend(["In Mill: Mill", "Shipment ID", "Crop", "Weight","Lot Number"])

        if "outbound5_wip" in filtered_context and len(filtered_context["outbound5_wip"]) > 0:
            headers.extend(["Assigned Lot Number: Mill", "Crop", "Weight","Lot Number", "Shipment ID"])
            headers.extend(["Shipped To Warehouse/Customer: Shipment ID", "Crop", "Weight", "Transit ID", "New Lot Number", "Date"])

        if "inbound5_wip" in filtered_context and len(filtered_context["inbound5_wip"]) > 0:
            headers.extend(["Received By Warehouse: Warehouse Name", "Warehouse ID", "Receive Date", "Crop", "Weight", "Shipment ID"])

        if "outbound6_wip" in filtered_context and len(filtered_context["outbound6_wip"]) > 0:
            headers.extend(["Shipped To Customer: Shipment ID", "Crop", "Weight", "Transit ID", "New Lot Number", "Date"])

        if "inbound6_wip" in filtered_context and len(filtered_context["inbound6_wip"]) > 0:
            headers.extend(["Received By Customer: Customer Name", "Customer ID", "Receive Date", "Crop", "Weight", "Shipment ID"])

        writer.writerow(headers)
        writer.writerow([""])
        
        origin_context = new_context.get("origin_context", [])
        t1_processor = new_context.get("t1_processor", [])
        outbound5 = new_context.get("outbound5_wip", [])
        inbound5 = new_context.get("inbound5_wip", [])
        outbound6 = new_context.get("outbound6_wip", [])
        inbound6 = new_context.get("inbound6_wip", [])
        in_mill_data = []

        if "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"]) > 0 and "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"])> 0 :
            in_mill_data = new_context.get("inbound4_wip")

        elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0 and "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"])> 0 :
            in_mill_data = new_context.get("inbound4_wip")

        elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0 and "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"])> 0:
            in_mill_data = new_context.get("inbound3_wip")   

        elif "inbound4_wip" in filtered_context and len(filtered_context["inbound4_wip"]) > 0:
            in_mill_data = new_context.get("inbound4_wip")  

        elif "inbound3_wip" in filtered_context and len(filtered_context["inbound3_wip"]) > 0 :
            in_mill_data = new_context.get("inbound3_wip")   
        
        elif "inbound2_wip" in filtered_context and len(filtered_context["inbound2_wip"]) > 0:
            in_mill_data = new_context.get("inbound2_wip")
        
        max_rows = max(len(origin_context), len(t1_processor),len(in_mill_data),len(outbound5), len(inbound5), len(outbound6), len(inbound6))
        
    # Populate rows dynamically
        for i in range(max_rows):
            row = []

            # Origin Data
            if "Origin: Field" in headers and "Grower" in headers:
                if i < len(origin_context):
                    origin = origin_context[i]
                    row.extend([
                        origin.get("field_name", ""), origin.get("grower_name", "")
                    ])
                else:
                    row.extend([""] * 2)

            # T1 Processor Data
            if "Inbound Mill: Shipment ID" in headers:
                if i < len(t1_processor):
                    t1_processor_data = t1_processor[i]
                    crop_data = f'{t1_processor_data.get("crop", "")}'
                    weight_data = f'{t1_processor_data.get("pounds_received") if t1_processor_data.get("pounds_received") not in ["None", None, "", "null"] else t1_processor_data.get("pounds_shipped")} {t1_processor_data.get("unit", "")}'
                    row.extend([
                        t1_processor_data.get("shipment_id", ""), crop_data, weight_data, format_date(t1_processor_data.get("date", "")), t1_processor_data.get("grower", "")
                    ])
                else:
                    row.extend([""] * 5)

            # In Mill Data
            if "In Mill: Mill" in headers:
                if i < len(in_mill_data):
                    mill_data = in_mill_data[i]
                    crop_data = f'{mill_data.get("crop", "")}'
                    weight_data = f'{mill_data.get("received_weight") if mill_data.get("received_weight") else mill_data.get("weight_or_product")} {mill_data.get("weight_of_product_unit", "")}'
                    row.extend([
                        mill_data.get("processor2_name", ""), mill_data.get("shipment_id", ""), crop_data, weight_data, mill_data.get("lot_number", "")
                    ])
                else:
                    row.extend([""] * 5)
            
            # Outbound5 Data
            if "Assigned Lot Number: Mill" in headers:
                if i < len(outbound5):
                    outbound5_data = outbound5[i]
                    crop_data = "\n".join(
                        f"{crop['crop_name']}" 
                        for crop in outbound5_data.get("crops", [])
                    )
                    weight_data = "\n".join(
                        f"{crop['net_weight']} {crop['weight_unit']}"
                        for crop in outbound5_data.get("crops", [])
                    )
                    lot_number_data = "\n".join(
                        f"{crop['lot_number']}"
                        for crop in outbound5_data.get("crops", [])
                    )
                    row.extend([
                        outbound5_data.get("processor_entity_name", ""), crop_data, weight_data, lot_number_data, outbound5_data.get("shipment_id")
                    ])
                else:
                    row.extend([""] * 5)
                    
            if "Shipped To Warehouse/Customer: Shipment ID" in headers:
                if i < len(outbound5):
                    outbound5_data = outbound5[i]                
                    crop_data = "\n".join(
                        f"{crop['crop_name']}" 
                        for crop in outbound5_data.get("crops", [])
                    )
                    weight_data = "\n".join(
                        f"{crop['net_weight']} {crop['weight_unit']}"
                        for crop in outbound5_data.get("crops", [])
                    )
                    new_lot_number_data = "\n".join(
                        f"{crop['additional_lot_number']}"
                        for crop in outbound5_data.get("crops", [])
                    )
                    row.extend([
                        outbound5_data.get("shipment_id", ""), crop_data, weight_data, outbound5_data.get("carrier_id", ""), 
                        new_lot_number_data, format_date(outbound5_data.get("date_pulled", ""))
                    ])
                else:
                    row.extend([""] * 6)

            # Inbound5 Data
            if "Received By Warehouse: Warehouse Name" in headers:
                if i < len(inbound5):
                    inbound5_data = inbound5[i]
                    crop_data = "\n".join(
                        f"{crop['crop_name']}" 
                        for crop in inbound5_data.get("crops", [])
                    )
                    weight_data = "\n".join(
                        f"{crop['net_weight']} {crop['weight_unit']}"
                        for crop in inbound5_data.get("crops", [])
                    )
                    row.extend([
                        inbound5_data.get("warehouse_name", ""), inbound5_data.get("warehouse_id", ""), 
                        format_date(inbound5_data.get("distributor_receive_date", "")), crop_data, weight_data, inbound5_data.get("shipment_id", "")
                    ])
                else:
                    row.extend([""] * 6)

            # Outbound6 Data
            if "Shipped To Customer: Shipment ID" in headers:
                if i < len(outbound6):
                    outbound6_data = outbound6[i]
                    crop_data = "\n".join(
                        f"{crop['crop_name']}" 
                        for crop in outbound6_data.get("crops", [])
                    )
                    weight_data = "\n".join(
                        f"{crop['net_weight']} {crop['weight_unit']}"
                        for crop in outbound6_data.get("crops", [])
                    )
                    new_lot_number_data = "\n".join(
                        f"{crop['additional_lot_number']}"
                        for crop in outbound6_data.get("crops", [])
                    )
                    row.extend([
                        outbound6_data.get("shipment_id", ""), crop_data, weight_data, outbound6_data.get("carrier_id", ""), 
                        new_lot_number_data, format_date(outbound6_data.get("date_pulled", ""))
                    ])
                else:
                    row.extend([""] * 6)

            # Inbound6 Data
            if "Received By Customer: Customer Name" in headers:
                if i < len(inbound6):
                    inbound6_data = inbound6[i]
                    crop_data = "\n".join(
                        f"{crop['crop_name']}" 
                        for crop in inbound6_data.get("crops", [])
                    )
                    weight_data = "\n".join(
                        f"{crop['net_weight']} {crop['weight_unit']}"
                        for crop in inbound6_data.get("crops", [])
                    )
                    row.extend([
                        inbound6_data.get("customer_name", ""), inbound6_data.get("customer_id", ""), 
                        format_date(inbound6_data.get("customer_receive_date", "")), crop_data, weight_data, inbound6_data.get("shipment_id", "")
                    ])
                else:
                    row.extend([""] * 6)

            # Write the row to the CSV
            writer.writerow(row)
    return response
