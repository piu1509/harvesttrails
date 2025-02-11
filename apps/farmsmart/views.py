from django.shortcuts import render, HttpResponse
from rest_framework.decorators import api_view
# from rest_framework import PageNumberPagination
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.processor.models import *
from apps.processor.serializer import *
from apps.storage.models import ShapeFileDataCo as StorageShapeFileDataCo, Storage
from apps.field.models import Field, FieldUpdated, ShapeFileDataCo, FieldActivity
from apps.field.serializers import FieldListSerializer
from apps.farms.models import Farm
from apps.accounts.models import VersionUpdate
from apps.farms.serializers import FarmSerializer
from apps.growersurvey.models import SustainabilitySurvey,TypeSurvey,NameSurvey
# from apps.growersurvey.serializer import SustainabilitySurveySerializer
from apps.grower.models import Grower, Consultant, GrowerChecklist
from apps.assistantapp.models import *
from apps.processor2.models import *
from django.core.mail import send_mail
from django.db.models import Avg
from django.http import FileResponse
from qrcode import *
import json
import time
from django.conf import settings
from django.db.models import Q
from datetime import datetime, date
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.serializers import AuthTokenSerializer
from django.contrib.auth import authenticate, login, logout
from apps.accounts.models import User, Role, LogTable
from apps.growerpayments.models import GrowerPayments, EntryFeeds, GrowerPayee
# import jwt, datetime
import jwt
from django.http import JsonResponse
import string
import random
from django.db.models import Count, Sum
import openai
import requests
from timezonefinder import TimezoneFinder
from pytz import timezone
from geopy.geocoders import Nominatim
from apps.growerpayments.models import NasdaqApiData
from apps.farmsmart.serializers import *
from django.urls import reverse
import qrcode
from django.core.files.base import ContentFile
from io import BytesIO
import base64
import shapefile
from mimetypes import guess_type
from django.contrib.auth.hashers import make_password
from apps.processor.views import get_sku_list, create_sku_list, calculate_milled_volume, generate_random_password
from apps.warehouseManagement.models import *
from apps.accounts.models import ShowNotification
from apps.warehouseManagement.views import find_changes, find_changes_for_customer_shipment
import stripe
import pdfkit
from django.core.mail import EmailMessage
from django.core.exceptions import ObjectDoesNotExist
# Create your views here.


def qr_code_view(pk):
    grower_shipment1 = GrowerShipment.objects.get(id=pk)
    processor_name = grower_shipment1.processor.entity_name
    grower_name = grower_shipment1.grower.name
    storage_name = 'N/A' if grower_shipment1.storage_id is None else grower_shipment1.storage.storage_name
    echelon_number = 'N/A' if grower_shipment1.field.eschlon_id is None else grower_shipment1.field.eschlon_id
    field_name = grower_shipment1.field.name
    crop_name = grower_shipment1.crop
    variety_name = grower_shipment1.variety
    sustainability = grower_shipment1.sustainability_score
    shipment_id = grower_shipment1.shipment_id
    module_tag_no = grower_shipment1.module_number

    if grower_shipment1.amount2 is None:
        a1 = grower_shipment1.amount
        unit_type1 = grower_shipment1.unit_type
        amount1 = f"{a1} {unit_type1}"
        amount2 = 'Null'
    else:
        a1 = grower_shipment1.amount
        a2 = grower_shipment1.amount2
        unit_type1 = grower_shipment1.unit_type
        unit_type2 = grower_shipment1.unit_type2
        amount1 = f"{a1} {unit_type1}"
        amount2 = f"{a2} {unit_type2}"

    total = f"{grower_shipment1.total_amount} LBS"
    shipment_date = grower_shipment1.date_time.strftime("%m-%d-%Y %H:%M:%S")

    datapy = {
        "amount1": amount1, "amount2": amount2, "total_amount": total, "shipment_id": shipment_id,
        "module_tag_no": module_tag_no, "processor_name": processor_name, "grower_name": grower_name,
        "storage_name": storage_name, "field_name": field_name, "crop_name": crop_name, "variety_name": variety_name,
        "echelon_number": echelon_number, "sustainability": sustainability, "shipment_date": shipment_date
    }
    data = json.dumps(datapy)           
    img = qrcode.make(data)
    img_name = 'qr1_' + str(int(time.time())) + '.png'         
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)            
    file = ContentFile(buffer.read(), name=img_name)

    grower_shipment1.qr_code.save(img_name, file, save=True)
    img_name = grower_shipment1.qr_code
    print(img_name)
    return True

def qr_code_processor(pk):
    shipment = ShipmentManagement.objects.filter(id=pk).first()
        
    # Convert the datetime to a string
    shipment_date_str = shipment.date_pulled.strftime('%Y-%m-%dT%H:%M:%S') if shipment.date_pulled else None

    datapy = {
        "shipment_id": shipment.shipment_id,
        "send_processor_name": shipment.processor_e_name,
        "sustainability": "under development",
        "shipment_date": shipment_date_str,
    }
    # data = json.dumps(datapy)

    # # Generate QR code
    # img = make(data)
    # buffer = BytesIO()
    # img.save(buffer, format='PNG')
    # buffer.seek(0)

    # # Encode the image as Base64
    # img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # return img_base64
    data = json.dumps(datapy)           
    img = qrcode.make(data)
    img_name = 'qr1_' + str(int(time.time())) + '.png'         
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)            
    file = ContentFile(buffer.read(), name=img_name)

    shipment.qr_code_processor.save(img_name, file, save=True)
    img_name = shipment.qr_code_processor
    print(img_name)
    return True


characters2 = list(string.ascii_letters + string.digits)
def generate_shipment_id():
	length = 12

	random.shuffle(characters2)

	shipment_id = []
	for i in range(length):
		shipment_id.append(random.choice(characters2))

	return "".join(shipment_id)


@api_view(('POST',))
def login_user_api(request):
    # using JWT Authentication
    username = request.data['username']
    password = request.data['password']
    user = authenticate(username=username, password=password)
  
    if user is not None and user.is_processor:
        p = ProcessorUser.objects.get(contact_email=user.email)       
        payload = {
            'id': user.id
        }
        token = jwt.encode(payload, 'secret', algorithm='HS256')
        data = {
            'jwt': token,
            'status': 1,
            "message":"Successfully logged in as processor",
            "type":"processor",
            "processor_type": "Tier 1 Processor",
            "userid":user.id,
            "username":user.username,
            "processor_name":p.processor.entity_name,
            "email":user.email,
        }
        return Response(data)
    
    elif user is not None and 'Grower' in user.get_role() and not user.is_superuser:
        grower = Grower.objects.get(id=user.grower_id)
        payload = {
            'id': user.id
        }
        token = jwt.encode(payload, 'secret', algorithm='HS256')
        data = {
            'jwt': token,
            'status': 1,
            "message":"Successfully logged in as grower",
            "type":"grower",
            "processor_type": None,
            "userid":user.id,
            "username":user.username,
            "grower_name":grower.name,
            "email":user.email,
        }
        return Response(data)
    
    elif user is not None and 'Processor' in user.get_role() and user.is_processor2 and not user.is_superuser:
        payload = {
            'id': user.id
        }
        token = jwt.encode(payload, 'secret', algorithm='HS256')
        p = ProcessorUser2.objects.get(contact_email=user.email)
        
        if p.processor2.processor_type.all().first().type_name == "T2":
            data = {
                'jwt': token,
                'status': 1,
                "message":"Successfully logged in as Tier 2 Processor",
                "type":"tier2_processor",
                "processor_type": "Tier 2 Processor",
                "userid":user.id,
                "username":user.username,
                "processor_name":p.processor2.entity_name,
                "email":user.email,
                "full_name":user.first_name,
            }
        
        elif p.processor2.processor_type.all().first().type_name == "T3":
            data = {
                'jwt': token,
                'status': 1,
                "message":"Successfully logged in as Tier 3 Processor",
                "type":"tier2_processor",
                "processor_type": "Tier 3 Processor",
                "userid":user.id,
                "username":user.username,
                "processor_name":p.processor2.entity_name,
                "email":user.email,
                "full_name":user.first_name,
            }
        
        elif p.processor2.processor_type.all().first().type_name == "T4": 
            data = {
                'jwt': token,
                'status': 1,
                "message":"Successfully logged in as Tier 4 Processor",
                "type":"tier2_processor",
                "processor_type": "Tier 4 Processor",
                "userid":user.id,
                "username":user.username,
                "processor_name":p.processor2.entity_name,
                "email":user.email,
                "full_name":user.first_name,
            }
        else:
            data = {
                'jwt': None,
                'status': 0,
                "message":"Processor does not exist",
                "type":None,
                "processor_type": None,
                "userid":None,
                "username":None,
                "email":None,
                "full_name":None,
            }
        return Response(data)
    
    elif user.is_distributor:
        d = DistributorUser.objects.get(contact_email=user.email)        
        payload = {
            'id': user.id
        }
        token = jwt.encode(payload, 'secret', algorithm='HS256')
        data = {
            'jwt': token,
            'status': 1,
            "message":"Successfully logged in as distributor",
            "type":"distributor",
            "processor_type": None,
            "userid":user.id,
            "username":user.username, 
            "distributor_name":d.distributor.entity_name,          
            "email":user.email,
        }
        return Response(data)
    
    elif user.is_warehouse_manager:
        w = WarehouseUser.objects.get(contact_email=user.email)        
        payload = {
            'id': user.id
        }
        token = jwt.encode(payload, 'secret', algorithm='HS256')
        data = {
            'jwt': token,
            'status': 1,
            "message":"Successfully logged in as warehouse manager",
            "type":"warehouse_manager",
            "processor_type": None,
            "userid":user.id,
            "username":user.username, 
            "warehouse_name":w.warehouse.name,           
            "email":user.email,
        }
        return Response(data)
    
    elif user.is_customer:        
        c = CustomerUser.objects.get(contact_email=user.email)        
        payload = {
            'id': user.id
        }
        token = jwt.encode(payload, 'secret', algorithm='HS256')
        data = {
            'jwt': token,
            'status': 1,
            "message":"Successfully logged in as customer",
            "type":"customer",
            "processor_type": None,
            "userid":user.id,
            "username":user.username, 
            "customer_name":c.customer.name,           
            "email":user.email,
        }
        return Response(data)

    elif user is None:
        return Response({"message":"Auth Failed"})
    
    else:
        return Response({"message":"Auth Failed",'status': 1})


# @api_view(('POST',))
# def grower_dashboard_api(request):
#     userid = request.data['userid']
#     user = User.objects.get(id=userid)
#     grower = Grower.objects.get(id=user.grower_id)
#     # grower_id = grower.id
#     # grower_id = grower.id
#     #done
#     survey_count = NameSurvey.objects.all().count()
#     survey_taken_user = SustainabilitySurvey.objects.filter(grower_id=grower.id).order_by('-id')[:10]
#     survey_lst = SustainabilitySurveySerializer(survey_taken_user, many=True)

#     SustainabilitySurvey_data = SustainabilitySurvey.objects.filter(grower_id=user.grower.id)
#     # ssserializer= SustainabilitySurveySerializer(SustainabilitySurvey_data, many=True)
#     if SustainabilitySurvey_data.count() == 0:
#         Avg_Percentage_Score = 'N/A'
#         SustainabilitySurvey_data_latest = 'N/A'
#     else:
#         Avg_Percentage_Score_data = SustainabilitySurvey_data.aggregate(Avg('sustainabilityscore'))
#         Avg_Percentage_Score = int(Avg_Percentage_Score_data['sustainabilityscore__avg'])
#         SustainabilitySurvey_data_latest = SustainabilitySurvey_data.order_by('-id')[0].sustainabilityscore


#     g_checklist = GrowerChecklist.objects.filter(grower_id=grower.id)
#     checklist = GrowerChecklistSerializer(g_checklist, many=True)
#     data = {
#         "grower_id":grower.id,
#         "grower_name":grower.name,
#         "total_survey_taken":survey_count,
#         "Avg_Percentage_Score":Avg_Percentage_Score,
#         "SustainabilitySurvey_data_latest":SustainabilitySurvey_data_latest,
#         "survey_lst":survey_lst,
#         "checklist":checklist,
        
#     }
#     return Response({"survey_lst":survey_lst.data})

@api_view(('POST',))
def grower_dashboard_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    grower = Grower.objects.get(id=user.grower_id)
    survey_count = NameSurvey.objects.all().count()
    survey_taken_user = SustainabilitySurvey.objects.filter(grower_id=grower.id).order_by('-id')[:10]
    slst = {"survey_lst":[]}
    for i in survey_taken_user:
        survey = '{} {}'.format(i.namesurvey.typesurvey,i.namesurvey.surveyyear)
        status = i.status
        created_date = i.created_date
        completed_date = i.modified_date
        # slst["survey_name"].append(survey)
        # slst["survey_status"].append(status)
        slst_dic = {"survey_name":survey,"survey_status":status,"survey_created_date":created_date,"survey_completed_date":completed_date}
        slst["survey_lst"].append(slst_dic)
        # slst.append(slst)

    SustainabilitySurvey_data = SustainabilitySurvey.objects.filter(grower_id=user.grower.id)
    if SustainabilitySurvey_data.count() == 0:
        Avg_Percentage_Score = 'N/A'
        SustainabilitySurvey_data_latest = 'N/A'
    else:
        Avg_Percentage_Score_data = SustainabilitySurvey_data.aggregate(Avg('sustainabilityscore'))
        Avg_Percentage_Score = int(Avg_Percentage_Score_data['sustainabilityscore__avg'])
        SustainabilitySurvey_data_latest = SustainabilitySurvey_data.order_by('-id')[0].sustainabilityscore


    g_checklist = GrowerChecklist.objects.filter(grower_id=grower.id)
    lst = []
    for i in g_checklist:
        item_name = i.item_name
        checkstatus = i.checkstatus
        module = i.module
        status = [module,item_name,checkstatus]
        lst.append(status)
    data = {
        "grower_id":grower.id,
        "grower_name":grower.name,
        "total_survey_taken":survey_count,
        "Avg_Percentage_Score":Avg_Percentage_Score,
        "SustainabilitySurvey_data_latest":SustainabilitySurvey_data_latest,
        "survey_lst":slst,
        "checklist":lst,
        
    }
    return Response(data)



# @api_view(['GET',])

# @permission_classes([AllowAny,])

# def PersonView(request):

#     paginator = PageNumberPagination()
#     paginator.page_size = 10
#     person_objects = Person.objects.all()
#     result_page = paginator.paginate_queryset(person_objects, request)
#     serializer = PersonSerializer(result_page, many=True)
#     return paginator.get_paginated_response(serializer.data)

@api_view(['POST',])
def grower_shipment_list_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    grower_shipment = GrowerShipment.objects.filter(grower_id=user.grower.id)
    
    if grower_shipment.count() == 0:
        data = []
        return Response({"status":"No recordes for You","data":data})
    else:
        grower_shipment = GrowerShipment.objects.filter(grower_id=user.grower.id)
        serializer = GrowerShipmentSerializer(grower_shipment, many=True)
        return Response({"data":serializer.data})

        # paginator = PageNumberPagination()
        # paginator.page_size = 10
        # result_page = paginator.paginate_queryset(grower_shipment, request)
        # serializer = GrowerShipmentSerializer(result_page, many=True)
        # return paginator.get_paginated_response({"data":serializer.data})
        # lst = []
        # for i in range(len(grower_shipment)):
        #     if grower_shipment[i].storage == None :
        #         storage_name = ""
        #     else:
        #         storage_name = grower_shipment[i].storage.storage_name

        #     if grower_shipment[i].variety == None :
        #         variety = ""
        #     else:
        #         variety = grower_shipment[i].variety
        #     img = qr_code_view(grower_shipment[i].id)
        #     data = {
        #         "message":"grower_shipment_list_api , with recordes",
        #         "type":"grower",
        #         "userid":user.id,
        #         "username":user.username,
        #         "email":user.email,
        #         "GrowerShipment_Id":grower_shipment[i].id,
        #         "status":grower_shipment[i].status,
        #         "shipment_id":grower_shipment[i].shipment_id,
        #         "module_number":grower_shipment[i].module_number,
        #         "storage_name":storage_name,
        #         "field_name":grower_shipment[i].field.name,
        #         "amount":grower_shipment[i].amount,
        #         "amount2":grower_shipment[i].amount2,
        #         "unit_type":grower_shipment[i].unit_type,
        #         "unit_type2":grower_shipment[i].unit_type2,
        #         "total_amount":grower_shipment[i].total_amount,
        #         "crop":grower_shipment[i].crop,
        #         "variety":variety,
        #         "echelon_id":grower_shipment[i].echelon_id,
        #         "sustainability_score":grower_shipment[i].sustainability_score,
        #         "qr_code":img,
        #     }
        #     lst.append(data)
        # return Response({'data':lst})

@api_view(['POST',])
def grower_shipment_list_search_api(request):
    userid = request.data['userid']
    search_keyword = request.data['search_keyword']
    # userid = request.GET.get('userid')
    user = User.objects.get(id=userid)  
    grower_shipment = GrowerShipment.objects.filter(grower_id=user.grower.id).filter(shipment_id__icontains=search_keyword)
    serializer = GrowerShipmentSerializer(grower_shipment, many=True)
    return Response({"data":serializer.data})

@api_view(('POST',))
def grower_shipment_qrcode_api(request):
    shipment_id = request.data.get('shipment_id')
    userid = request.data.get("userid")
    user = User.objects.get(id=userid)
    if user.is_processor:
        qr = qr_code_view(shipment_id)
        shipment = GrowerShipment.objects.get(id=shipment_id)
        qr_code = shipment.qr_code.url
    elif user.is_processor2:
        qr = qr_code_processor(shipment_id)
        shipment = ShipmentManagement.objects.get(id=shipment_id)
        qr_code = shipment.qr_code_processor.url
    else:
        qr_code = None
    return Response({'data':qr_code})

    
@api_view(('POST',))
def grower_send_shipment_storage_name_api(request):
    userid = request.data['userid']
    grower_id= User.objects.get(id=userid).grower.id
    storage = Storage.objects.filter(grower_id=grower_id)
    lst = []
    for i in range(len(storage)):
        data = {
            "storage_name":storage[i].storage_name,
            "storage_id":storage[i].id,
        }
        lst.append(data)
    return Response({'data':lst})

@api_view(('POST',))
def grower_send_shipment_field_name_api(request):
    userid = request.data['userid']
    grower_id= User.objects.get(id=userid).grower.id
    field = Field.objects.filter(grower_id=grower_id)
    lst = []
    for i in range(len(field)):
        data = {
            "field_name":field[i].name,
            "field_id":field[i].id,
        }
        lst.append(data)
    return Response({'data':lst})

@api_view(('POST',))
def grower_shipment_view_api(request):
    shipment_id = request.data['shipment_id']
    grower_shipment = GrowerShipment.objects.get(id=shipment_id)
    if grower_shipment.storage == None :
        storage_name = "N/A"
    else:
        storage_name = grower_shipment.storage.storage_name

    if grower_shipment.variety == None :
        variety = "N/A"
    else:
        variety = grower_shipment.variety
    if grower_shipment.echelon_id == None :
        echelon_id = "N/A"
    else:
        echelon_id = grower_shipment.echelon_id
    if grower_shipment.sustainability_score == None :
        sustainability_score = "N/A"
    else:
        sustainability_score = grower_shipment.sustainability_score

    img = qr_code_view(shipment_id)
    data = {
        "GrowerShipment_Id":grower_shipment.id,
        "shipment_id":grower_shipment.shipment_id,
        "module_number":grower_shipment.module_number,
        "status":grower_shipment.status,
        "grower_name":grower_shipment.grower.name,
        "processor_name":grower_shipment.processor.entity_name,
        "storage_name":storage_name,
        "field_name":grower_shipment.field.name,
        "amount":grower_shipment.amount,
        "amount2":grower_shipment.amount2,
        "unit_type":grower_shipment.unit_type,
        "unit_type2":grower_shipment.unit_type2,
        "total_amount":grower_shipment.total_amount,
        "crop":grower_shipment.crop,
        "variety":variety,
        "echelon_id":echelon_id,
        "sustainability_score":sustainability_score,
        "date":grower_shipment.date_time,
        "qr_code":img,
    }
    return Response({'data':data})

@api_view(('POST',))
def grower_send_shipment_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    grower_id= user.grower.id
    id_storage = request.data['id_storage']
    field_id = request.data['field_id']
    module_number = request.data['module_number']
    amount1 = request.data['amount1']
    amount2 = request.data['amount2']
    id_unit1 = request.data['type1']
    id_unit2 = request.data['type2']
    get_output = request.data['get_toatal']
    status = ""
    if LinkGrowerToProcessor.objects.filter(grower_id=grower_id).count() == 0:
        return Response({"message":"You are not assigned to any processor"})
    else:
        grower_processor = LinkGrowerToProcessor.objects.get(grower_id=grower_id)
        processor_id = grower_processor.processor.id
        sustainabilitySurvey = SustainabilitySurvey.objects.filter(grower_id=grower_id)

        if len(sustainabilitySurvey) == 0:
            surveyscore = 0
        else:
            surveyscore = [i.surveyscore for i in sustainabilitySurvey][0]
        if len(amount1) > 0 and len(amount2) == 0:
            if id_unit1 == '1':
                id_unit1 = 'LBS'
                id_unit2 = ''
            if id_unit1 == '38000':
                id_unit1 = 'MODULES (8 ROLLS)'
                id_unit2 = ''
            if id_unit1 == '19000':
                id_unit1 = 'SETS (4 ROLLS)'
                id_unit2 = ''
            if id_unit1 == '4750':
                id_unit1 = 'ROLLS'
                id_unit2 = ''
        if len(amount1) > 0 and len(amount2) > 0:
            if id_unit1 == '1':
                id_unit1 = 'LBS'
            if id_unit1 == '38000':
                id_unit1 = 'MODULES (8 ROLLS)'
            if id_unit1 == '19000':
                id_unit1 = 'SETS (4 ROLLS)'
            if id_unit1 == '4750':
                id_unit1 = 'ROLLS'
            if id_unit2 == '1':
                id_unit2 = 'LBS'
            if id_unit2 == '38000':
                id_unit2 = 'MODULES (8 ROLLS)'
            if id_unit2 == '19000':
                id_unit2 = 'SETS (4 ROLLS)'
            if id_unit2 == '4750':
                id_unit2 = 'ROLLS'

        if field_id:
            field = Field.objects.get(id=field_id)
            field_eschlon_id = field.eschlon_id
            crop = field.crop
            
            if crop == "COTTON":
                status = "APPROVED"
            else:
                status = ""
            
            variety = field.variety 
            shipment_id = generate_shipment_id()
            if id_storage == None :
                id_storage = None

            else:
                id_storage = id_storage
                # s = Storage.objects.get(id=id_storage)
                # storage_name = s.storage_name
            shipment = GrowerShipment(status=status,total_amount=get_output,unit_type2=id_unit2,amount2=amount2,shipment_id=shipment_id,processor_id=processor_id,grower_id=grower_id,storage_id=id_storage,field_id=field_id,crop=crop,variety=variety,amount=amount1,sustainability_score=surveyscore,echelon_id=field_eschlon_id,module_number=module_number,unit_type=id_unit1)
            shipment.save()
            # 07-04-23 Log Table
            log_type, log_status, log_device = "GrowerShipment", "Added", "App"
            log_idd, log_name = shipment.id, shipment.shipment_id
            log_details = f"status = {status} | total_amount = {get_output} | unit_type2 = {id_unit2} | amount2 = {amount2} | echelon_id = {shipment.echelon_id} | sustainability_score = {shipment.sustainability_score} | amount = {amount1} | variety = {shipment.variety} | crop = {shipment.crop} | shipment_id = {shipment.shipment_id} | processor_id = {shipment.processor.id} | grower_id = {shipment.grower.id} | storage_id = {id_storage} | field_id = {shipment.field.id} | module_number = {module_number} | unit_type = {id_unit1} | "
            
            action_by_userid = user.id
            user_role = user.role.all()
            action_by_username = f'{user.first_name} {user.last_name}'
            action_by_email = user.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                log_device=log_device)
            logtable.save()
        return Response({"message":"shipment is added"})


@api_view(('POST',))
def grower_shipment_delete_api(request):
    shipment_id = request.data['shipment_id']
    shipment = GrowerShipment.objects.get(id=shipment_id)
    # 07-04-23 Log Table
    log_type, log_status, log_device = "GrowerShipment", "Deleted", "App"
    log_idd, log_name = shipment.id, shipment.shipment_id
    storage_id = shipment.storage.id if shipment.storage else None
    log_details = f"status = {shipment.status} | total_amount = {shipment.total_amount} | unit_type2 = {shipment.unit_type2} | amount2 = {shipment.amount2} | echelon_id = {shipment.echelon_id} | sustainability_score = {shipment.sustainability_score} | amount = {shipment.amount} | variety = {shipment.variety} | crop = {shipment.crop} | shipment_id = {shipment.shipment_id} | processor_id = {shipment.processor.id} | grower_id = {shipment.grower.id} | storage_id = {storage_id} | field_id = {shipment.field.id} | module_number = {shipment.module_number} | unit_type = {shipment.unit_type} | "
    
    user= User.objects.get(grower_id=shipment.grower.id)
    action_by_userid = user.id
    user_role = user.role.all()
    action_by_username = f'{user.first_name} {user.last_name}'
    action_by_email = user.username
    if user.id == 1 :
        action_by_role = "superuser"
    else:
        action_by_role = str(','.join([str(i.role) for i in user_role]))
    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                        log_device=log_device)
    logtable.save()
    shipment.delete()
    return Response({"message":"shipment is deleted"})


@api_view(('GET',))
def processor_inbound_list_api(request):
    data = {"status":"","previous":None,"next":None,"data":[]}
    userid = request.GET.get('userid')
    user = User.objects.get(id=userid)
    if user.is_processor:
        p = ProcessorUser.objects.get(contact_email=user.email)
        processor_id = Processor.objects.get(id=p.processor_id).id
        processor_shipment = GrowerShipment.objects.filter(processor_id=processor_id)
        var_id = []
        for i in range(len(processor_shipment)):
            location = processor_shipment[i].location
            if location == None:
                var = processor_shipment[i].id
                var_id.append(var)

        inbound_shipment = GrowerShipment.objects.filter(id__in = var_id).filter(status="APPROVED")

        if processor_shipment.count() == 0:
            data = []
            return Response({"status":"No recordes for You","data":data})
        else:
            inbound_shipment = GrowerShipment.objects.filter(id__in = var_id).filter(status="APPROVED")
            serializer = GrowerShipmentSerializer(inbound_shipment, many=True)
            result = serializer.data
            paginator = PageNumberPagination()
            paginator.page_size = 10  # Set the page size to 20
            result_data = paginator.paginate_queryset(result, request)
            paginated_response = paginator.get_paginated_response(result_data)
            data["status"] = "200"
            data["count"] = paginated_response.data["count"]
            data["previous"] = paginated_response.data["previous"]
            data["next"] = paginated_response.data["next"]
            data["data"] = paginated_response.data["results"]

    elif user.is_processor2:
        p = ProcessorUser2.objects.get(contact_email=user.email)
        processor_id = Processor2.objects.get(id=p.processor2_id).id
        processor_shipment = ShipmentManagement.objects.filter(processor2_idd=processor_id, status="APPROVED")
        if processor_shipment.count() == 0:
            data = []
            return Response({"status":"No recordes for You","data":data})
        else:
            inbound_shipment = processor_shipment
            serializer = ShipmentManagementSerializer(inbound_shipment, many=True)
            result = serializer.data
            paginator = PageNumberPagination()
            paginator.page_size = 10  # Set the page size to 20
            result_data = paginator.paginate_queryset(result, request)
            paginated_response = paginator.get_paginated_response(result_data)
            data["status"] = "200"
            data["count"] = paginated_response.data["count"]
            data["previous"] = paginated_response.data["previous"]
            data["next"] = paginated_response.data["next"]
            data["data"] = paginated_response.data["results"]
    else:
        data = []
    return Response({"data":data})


@api_view(('GET',))
def processor_inbound_list_search_api(request):
    data = {"status":"","previous":None,"next":None,"data":[]}
    userid = request.GET.get('userid')
    search_keyword = request.GET.get('search_keyword')
    user = User.objects.get(id=userid)
    if user.is_processor:
        p = ProcessorUser.objects.get(contact_email=user.email)
        processor_id = Processor.objects.get(id=p.processor_id).id
        processor_shipment = GrowerShipment.objects.filter(processor_id=processor_id)
        var_id = []
        for i in range(len(processor_shipment)):
            location = processor_shipment[i].location
            if location == None:
                var = processor_shipment[i].id
                var_id.append(var)
        if search_keyword:
            inbound_shipment = GrowerShipment.objects.filter(id__in = var_id).filter(status="APPROVED").filter(shipment_id__icontains=search_keyword)
        else:
            inbound_shipment = GrowerShipment.objects.filter(id__in = var_id).filter(status="APPROVED")
        serializer = GrowerShipmentSerializer(inbound_shipment, many=True)
        result = serializer.data
        paginator = PageNumberPagination()
        paginator.page_size = 10  # Set the page size to 20
        result_data = paginator.paginate_queryset(result, request)
        paginated_response = paginator.get_paginated_response(result_data)
        data["status"] = "200"
        data["count"] = paginated_response.data["count"]
        data["previous"] = paginated_response.data["previous"]
        data["next"] = paginated_response.data["next"]
        data["data"] = paginated_response.data["results"]
        
    elif user.is_processor2:
        p = ProcessorUser2.objects.get(contact_email=user.email)
        processor_id = Processor2.objects.get(id=p.processor2_id).id
        processor_shipment = ShipmentManagement.objects.filter(processor2_idd=processor_id, status="APPROVED")
        if search_keyword:
            inbound_shipment = processor_shipment.filter(shipment_id__icontains=search_keyword)
        else:
            inbound_shipment = processor_shipment
        serializer = ShipmentManagementSerializer(inbound_shipment, many=True)
        result = serializer.data
        paginator = PageNumberPagination()
        paginator.page_size = 10  # Set the page size to 20
        result_data = paginator.paginate_queryset(result, request)
        paginated_response = paginator.get_paginated_response(result_data)
        data["status"] = "200"
        data["count"] = paginated_response.data["count"]
        data["previous"] = paginated_response.data["previous"]
        data["next"] = paginated_response.data["next"]
        data["data"] = paginated_response.data["results"]
    else:
        data = []
    return Response({"data":data})


@api_view(('GET',))
def processor_upcomming_inbound_list_api(request):
    data = {"status":"","previous":None,"next":None,"data":[]}
    userid = request.GET.get('userid')
    user = User.objects.get(id=userid)
    if user.is_processor:   
        p = ProcessorUser.objects.get(contact_email=user.email)
        processor_id = Processor.objects.get(id=p.processor_id).id
        processor_shipment = GrowerShipment.objects.filter(processor_id=processor_id)
        var_id = []
        for i in range(len(processor_shipment)):
            location = processor_shipment[i].location
            if location == None:
                var = processor_shipment[i].id
                var_id.append(var)

        inbound_shipment = GrowerShipment.objects.filter(id__in = var_id).filter(status="")

        if processor_shipment.count() == 0:
            data = []
            return Response({"status":"No recordes for You","data":data})
        else:
            
            inbound_shipment = GrowerShipment.objects.filter(id__in = var_id).filter(status="")
            serializer = GrowerShipmentSerializer(inbound_shipment, many=True)
            result = serializer.data
            paginator = PageNumberPagination()
            paginator.page_size = 10  # Set the page size to 20
            result_data = paginator.paginate_queryset(result, request)
            paginated_response = paginator.get_paginated_response(result_data)
            data["status"] = "200"
            data["count"] = paginated_response.data["count"]
            data["previous"] = paginated_response.data["previous"]
            data["next"] = paginated_response.data["next"]
            data["data"] = paginated_response.data["results"]

    elif user.is_processor2:   
        p = ProcessorUser2.objects.get(contact_email=user.email)
        processor_id = Processor2.objects.get(id=p.processor2_id).id
        processor_shipment = ShipmentManagement.objects.filter(processor2_idd=processor_id, status=None)
        if processor_shipment.count() == 0:
            data = []
            return Response({"status":"No recordes for You","data":data})
        else:
            
            inbound_shipment = processor_shipment
            serializer = ShipmentManagementSerializer(inbound_shipment, many=True)
            result = serializer.data
            paginator = PageNumberPagination()
            paginator.page_size = 10  # Set the page size to 20
            result_data = paginator.paginate_queryset(result, request)
            paginated_response = paginator.get_paginated_response(result_data)
            data["status"] = "200"
            data["count"] = paginated_response.data["count"]
            data["previous"] = paginated_response.data["previous"]
            data["next"] = paginated_response.data["next"]
            data["data"] = paginated_response.data["results"]
    else:
        data= []
    return Response({"data":data})


@api_view(('GET',))
def processor_upcomming_inbound_list_search_api(request):
    data = {"status":"","previous":None,"next":None,"data":[]}
    userid = request.GET.get('userid')
    search_keyword = request.GET.get('search_keyword')
    user = User.objects.get(id=userid)
    if user.is_processor:
        p = ProcessorUser.objects.get(contact_email=user.email)
        processor_id = Processor.objects.get(id=p.processor_id).id
        processor_shipment = GrowerShipment.objects.filter(processor_id=processor_id)
        var_id = []
        for i in range(len(processor_shipment)):
            location = processor_shipment[i].location
            if location == None:
                var = processor_shipment[i].id
                var_id.append(var)
        if search_keyword:
            inbound_shipment = GrowerShipment.objects.filter(id__in = var_id).filter(status="").filter(shipment_id__icontains=search_keyword)
        else:
            inbound_shipment = GrowerShipment.objects.filter(id__in = var_id).filter(status="")
        serializer = GrowerShipmentSerializer(inbound_shipment, many=True)
        result = serializer.data
        paginator = PageNumberPagination()
        paginator.page_size = 10  # Set the page size to 20
        result_data = paginator.paginate_queryset(result, request)
        paginated_response = paginator.get_paginated_response(result_data)
        data["status"] = "200"
        data["count"] = paginated_response.data["count"]
        data["previous"] = paginated_response.data["previous"]
        data["next"] = paginated_response.data["next"]
        data["data"] = paginated_response.data["results"]

    elif user.is_processor2:
        p = ProcessorUser2.objects.get(contact_email=user.email)
        processor_id = Processor2.objects.get(id=p.processor2_id).id
        processor_shipment = ShipmentManagement.objects.filter(processor2_idd=processor_id, status="")
        if search_keyword:
            inbound_shipment = processor_shipment.filter(shipment_id__icontains=search_keyword)
        else:
            inbound_shipment = processor_shipment
        serializer = ShipmentManagementSerializer(inbound_shipment, many=True)
        result = serializer.data
        paginator = PageNumberPagination()
        paginator.page_size = 10  # Set the page size to 20
        result_data = paginator.paginate_queryset(result, request)
        paginated_response = paginator.get_paginated_response(result_data)
        data["status"] = "200"
        data["count"] = paginated_response.data["count"]
        data["previous"] = paginated_response.data["previous"]
        data["next"] = paginated_response.data["next"]
        data["data"] = paginated_response.data["results"]
    else:
        data = []
    return Response({"data":data})


@api_view(('GET',))
def processor_inbound_view_api(request):
    shipment_id = request.GET.get('shipment_id')
    userid = request.GET.get('userid')
    user = User.objects.get(id=userid)
    if user.is_processor:
        check_grower_shipment = GrowerShipment.objects.filter(id=shipment_id)
        if check_grower_shipment.exists():
            grower_shipment = check_grower_shipment.first()
            if grower_shipment.storage == None :
                storage_name = "N/A"
            else:
                storage_name = grower_shipment.storage.storage_name

            if grower_shipment.variety == None :
                variety = "N/A"
            else:
                variety = grower_shipment.variety
            if grower_shipment.echelon_id == None :
                echelon_id = "N/A"
            else:
                echelon_id = grower_shipment.echelon_id
            if grower_shipment.sustainability_score == None :
                sustainability_score = "N/A"
            else:
                sustainability_score = grower_shipment.sustainability_score
            if grower_shipment.received_amount == None :
                received_amount = "N/A"
            else:
                received_amount = grower_shipment.received_amount
            if grower_shipment.token_id == None :
                token_id = "N/A"
            else:
                token_id = grower_shipment.token_id
            if grower_shipment.moisture_level == None:
                moisture_percentage = "N/A"
            else:
                moisture_percentage = grower_shipment.moisture_level
            if grower_shipment.head_count:
                head_count = "N/A"
            else:
                head_count = grower_shipment.head_count
            if grower_shipment.fancy_count:
                fancy_count = "N/A"
            else:
                fancy_count = grower_shipment.fancy_count
            files = grower_shipment.files.all()
            file_data = [
                {
                    "url": file.file.url,
                    "name": file.file.name.split('/')[-1],  # Extract file name from the path
                    "type": guess_type(file.file.url)[0].split('/')[1] if guess_type(file.file.url)[0] else "unknown"
                } 
                for file in files
            ]
            
            img = qr_code_view(shipment_id)
            data = {
                "GrowerShipment_Id":grower_shipment.id,
                "shipment_id":grower_shipment.shipment_id,
                "sku": grower_shipment.sku if grower_shipment.sku else None,
                "status":grower_shipment.status,
                "processor_name":grower_shipment.processor.entity_name,
                "date_time":grower_shipment.date_time,
                "grower_name":grower_shipment.grower.name,
                "module_number":grower_shipment.module_number,
                "storage_name":storage_name,
                "field_name":grower_shipment.field.name,
                "amount":grower_shipment.amount,
                "amount2":grower_shipment.amount2,
                "type":grower_shipment.unit_type,
                "type2":grower_shipment.unit_type2,
                "total_amount":grower_shipment.total_amount,
                "crop":grower_shipment.crop,
                "variety":variety,
                "echelon_id":echelon_id,
                "sustainability_score":sustainability_score,
                "received_amount":received_amount,
                "approval_date":grower_shipment.approval_date,
                "token_id":token_id,
                "moisture_percentage":moisture_percentage,
                "head_count": head_count,
                "fancy_count": fancy_count,
                "qr_code":grower_shipment.qr_code.url,
                "files":file_data
            }
        else:
            data = []
    elif user.is_processor2:
        check_shipment = ShipmentManagement.objects.filter(id=shipment_id)
        if check_shipment.exists():
            shipment = check_shipment.first()
            files = shipment.files.all()
            file_data = [
                {
                    "url": file.file.url,
                    "name": file.file.name.split('/')[-1],  # Extract file name from the path
                    "type": guess_type(file.file.url)[0].split('/')[1] if guess_type(file.file.url)[0] else "unknown"
                } 
                for file in files
            ]
            qr_code = qr_code_processor(shipment_id)
            print(qr_code)
            data = {
                "shipment_id":shipment.shipment_id,
                "sender_processor_id":shipment.processor2_idd,
                "sender_processor_name":shipment.processor_e_name,
                "sender_processor_type":shipment.sender_processor_type,
                "receiver_processor_id":shipment.processor2_idd,
                "receiver_processor_name":shipment.processor2_name,
                "receiver_processor_type":shipment.receiver_processor_type,
                "milled_volume":shipment.milled_volume,
                "volume_shipped":shipment.volume_shipped,
                "volume_left":shipment.volume_left,
                "weight_of_product":shipment.weight_of_product,
                "weight_of_product_unit":shipment.weight_of_product_unit,
                "expected_yield":shipment.excepted_yield,
                "expected_yield_unit":shipment.excepted_yield_unit,
                "moisture_percentage":shipment.moisture_percent,
                "equipment_type":shipment.equipment_type,
                "equipment_id":shipment.equipment_id,
                "purchase_order_number":shipment.purchase_order_number,
                "lot_number":shipment.lot_number,
                "date_pulled":shipment.date_pulled,
                "status":shipment.status,
                "sender_sku_id":shipment.storage_bin_send,
                "receiving_date":shipment.recive_delivery_date,
                "receiver_sku_id":shipment.storage_bin_recive,
                "received_weight":shipment.received_weight,
                "ticket_number":shipment.ticket_number,
                "qr_code":shipment.qr_code_processor.url,
                "files":file_data
            }
        else:
            data = []
    else:
        data = []
    return Response({'data':data})


@api_view(('POST',))
def processor_outbound_view_api(request):
    shipment_id = request.data['shipment_id']
    grower_shipment = GrowerShipment.objects.get(id=shipment_id)
    if grower_shipment.storage == None :
        storage_name = "N/A"
    else:
        storage_name = grower_shipment.storage.storage_name

    if grower_shipment.variety == None :
        variety = "N/A"
    else:
        variety = grower_shipment.variety
    if grower_shipment.echelon_id == None :
        echelon_id = "N/A"
    else:
        echelon_id = grower_shipment.echelon_id
    if grower_shipment.sustainability_score == None :
        sustainability_score = "N/A"
    else:
        sustainability_score = grower_shipment.sustainability_score
    
    location_name = Location.objects.get(id=grower_shipment.location_id).name

    img = qr_code_view(shipment_id)
    data = {
        "GrowerShipment_Id":grower_shipment.id,
        "shipment_id":grower_shipment.shipment_id,
        "status":grower_shipment.status,
        "processor_name":grower_shipment.processor.entity_name,
        "date_time":grower_shipment.date_time,
        "grower_name":grower_shipment.grower.name,
        "module_number":grower_shipment.module_number,
        "storage_name":storage_name,
        "field_name":grower_shipment.field.name,
        "amount":grower_shipment.amount,
        "amount2":grower_shipment.amount2,
        "type":grower_shipment.unit_type,
        "type2":grower_shipment.unit_type2,
        "total_amount":grower_shipment.total_amount,
        "crop":grower_shipment.crop,
        "variety":variety,
        "echelon_id":echelon_id,
        "sustainability_score":sustainability_score,
        "location":location_name,
        "qr_code":img,
    }
    return Response({'data':data})

@api_view(('POST',))
def processor_inbound_delete_api(request):
    shipment_id = request.data.get('shipment_id')
    userid = request.data.get('userid') 
    user = User.objects.get(id=userid) 
    if user.is_processor: 
        check_shipment = GrowerShipment.objects.filter(id=shipment_id)
        if check_shipment.exists():
            shipment = check_shipment.first()

            log_type, log_status, log_device = "GrowerShipment", "Deleted", "App"
            log_idd, log_name = shipment.id, shipment.shipment_id
            echelon_id = shipment.echelon_id if shipment.echelon_id else None
            storage_id = shipment.storage.id if shipment.storage else None
            log_details = f"status = {shipment.status} | total_amount = {shipment.total_amount} | unit_type2 = {shipment.unit_type2} | amount2 = {shipment.amount2} | echelon_id = {echelon_id} | sustainability_score = {shipment.sustainability_score} | amount = {shipment.amount} | variety = {shipment.variety} | crop = {shipment.crop} | shipment_id = {shipment.shipment_id} | processor_id = {shipment.processor.id} | grower_id = {shipment.grower.id} | storage_id = {storage_id} | field_id = {shipment.field.id} | module_number = {shipment.module_number} | unit_type = {shipment.unit_type} | "
            
            action_by_userid = user.id
            user_role = user.role.all()
            action_by_username = f'{user.first_name} {user.last_name}'
            action_by_email = user.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                log_device=log_device)
            logtable.save()
            shipment.delete()
        else:
            return Response({"message":"Shipment does not exist"})
    elif user.is_processor2:
        check_shipment = ShipmentManagement.objects.filter(id=shipment_id)
        if check_shipment.exists():
            shipment = check_shipment.first()
            log_type, log_status, log_device = "ProcessorShipment", "Deleted", "App"
            log_idd, log_name = shipment.id, shipment.shipment_id
            log_details = f"shipment_id = {shipment.shipment_id} | status = {shipment.status} | sender_processor_id = {shipment.processor_idd} | receiver_processor_id = {shipment.processor2_idd}"
            
            action_by_userid = user.id
            user_role = user.role.all()
            action_by_username = f'{user.first_name} {user.last_name}'
            action_by_email = user.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                log_device=log_device)
            logtable.save()
            shipment.delete()
        else:
            return Response({"message":"Shipment does not exist"})
    else:
        return Response({"message":"Shipment does not exist"})
    return Response({"status":"200","message":"Shipment is deleted"})
      

@api_view(('POST',))
def processor_linked_grower_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    user_email = user.email
    p = ProcessorUser.objects.filter(contact_email=user_email).first()
    if p:
        processor_id = p.processor.id
        procesoor_grower = LinkGrowerToProcessor.objects.filter(processor_id=processor_id)
        # shipment = GrowerShipment.objects.filter(processor_id = processor_id)
        # var_id = []
        # for i in range(len(shipment)):
        #     location = shipment[i].location
        #     if location == None:
        #         var = shipment[i].id
        #         var_id.append(var)

        grower_id = [i.grower_id for i in procesoor_grower]

        grower = Grower.objects.filter(id__in=grower_id)
        lst = []
        for i in grower:
            data = {
                "grower_name":i.name,
                "grower_id":i.id,
            }
            lst.append(data)
        return Response({'status':'200', 'message':'Linked grower fteched successfully.', 'data':lst})
    else:
        return Response({'status':'200', 'message':'Processor not found.', 'data':[]})

@api_view(('POST',))
def processor_linked_grower_field_api(request):
    growerid = request.data['growerid']
    grower = Grower.objects.get(id=growerid)
    field = Field.objects.filter(grower_id=grower.id)
    lst = []
    for i in field:
        if i.name != None:
            field_name = i.name
            field_id = i.id
            fdd = {"field_name":field_name,"field_id":field_id}
            lst.append(fdd)
    return Response({'data':lst})

@api_view(('POST',))
def processor_linked_grower_storage_api(request):
    growerid = request.data['growerid']
    grower = Grower.objects.get(id=growerid)
    storage = Storage.objects.filter(grower_id=grower.id)
    lst = []
    for i in storage:
        if i.storage_name != None:
            storage_name = i.storage_name
            storage_id = i.id
            stt = {"storage_name":storage_name,"storage_id":storage_id}
            lst.append(stt)
    return Response({'data':lst})

@api_view(("GET",))
def receive_delivery_source_list_api(request):
    response = {"status":"", "message":"","data":[]}
    userid = request.GET.get('userid')
    user = User.objects.get(id=userid)
    if user.is_processor:
        p = ProcessorUser.objects.get(contact_email=user.email)
        linked_grower = LinkGrowerToProcessor.objects.filter(processor_id=p.processor.id)
        data = []
        for i in linked_grower:
            grower_email = i.grower.email
            user = User.objects.get(email=grower_email)
            lst = {
                "grower_name":i.grower.name,
                "grower_id":i.grower.id,
                "user_id":user.id
                
            }
            data.append(lst)
    elif user.is_processor2:
        p = ProcessorUser2.objects.get(contact_email=user.email)
        linked_processor1 = LinkProcessor1ToProcessor.objects.filter(processor2_id=p.processor2.id)
        other_linked_pro = LinkProcessorToProcessor.objects.filter(linked_processor_id=p.processor2.id)
        data = []
        if linked_processor1:
            for i in linked_processor1:
               
                user = User.objects.filter(email=i.processor1)
                lst = {
                    "processor_name":i.processor1.entity_name,
                    "processor_id":i.processor1.id,
                    "processor_type":"T1"
                }
                data.append(lst)
        if other_linked_pro:
            for i in other_linked_pro:
                lst = {
                    "processor_name":i.processor.entity_name,
                    "processor_id":i.processor.id,
                    "processor_type":i.processor.processor_type.all().first().type_name
                }
                data.append(lst)
    else:
        data = []
    response["status"] = "200"
    response["message"] = "Source list fetched successfully"
    response["data"] = data
    return Response(response)


@api_view(('POST',))
def processor_receive_delivery_api(request):
    response = {"status":"", "message":"", "data":[]}
    userid = request.data.get('userid')
    user = User.objects.get(id=userid)
    if user.is_processor:
        p = ProcessorUser.objects.get(contact_email=user.email)
        processor_id = p.processor.id
        grower_id = request.data.get('grower_id')
        id_storage = request.data.get('storage_id')
        field_id = request.data.get('field_id')
        module_number = request.data['module_number']
        amount1 = request.data.get('amount1')
        amount2 = request.data.get('amount2')
        id_unit1 = request.data.get('type1')
        id_unit2 = request.data.get('type2')
        get_total = request.data.get('get_total')
        files = request.FILES.getlist('files')                        
        received_weight= request.data.get('received_weight')
        sku_id = request.data.get('sku_id')
        ticket_number= request.data.get('ticket_number')
        approval_date= request.data.get('approval_date')

        moisture_level= request.data.get('moist_percentage')
        fancy_count= request.data.get('fancy_count')
        head_count= request.data.get('head_count')
        bin_location_processor= request.data.get('bin_location_processor')
        approval_date = datetime.strptime(approval_date, '%m/%d/%Y').strftime('%Y-%m-%d')

        status = ""
        sustainabilitySurvey = SustainabilitySurvey.objects.filter(grower_id=grower_id)
        if len(sustainabilitySurvey) == 0:
            surveyscore = 0
        else:
            surveyscore = [i.surveyscore for i in sustainabilitySurvey][0]
        if len(amount1) > 0 and len(amount2) == 0:
            if id_unit1 == '1':
                id_unit1 = 'LBS'
                id_unit2 = ''
            if id_unit1 == '38000':
                id_unit1 = 'MODULES (8 ROLLS)'
                id_unit2 = ''
            if id_unit1 == '19000':
                id_unit1 = 'SETS (4 ROLLS)'
                id_unit2 = ''
            if id_unit1 == '4750':
                id_unit1 = 'ROLLS'
                id_unit2 = ''
        if len(amount1) > 0 and len(amount2) > 0:
            if id_unit1 == '1':
                id_unit1 = 'LBS'
            if id_unit1 == '38000':
                id_unit1 = 'MODULES (8 ROLLS)'
            if id_unit1 == '19000':
                id_unit1 = 'SETS (4 ROLLS)'
            if id_unit1 == '4750':
                id_unit1 = 'ROLLS'
            if id_unit2 == '1':
                id_unit2 = 'LBS'
            if id_unit2 == '38000':
                id_unit2 = 'MODULES (8 ROLLS)'
            if id_unit2 == '19000':
                id_unit2 = 'SETS (4 ROLLS)'
            if id_unit2 == '4750':
                id_unit2 = 'ROLLS'

        get_output = get_total

        if field_id:
            field = Field.objects.get(id=field_id)
            field_eschlon_id = field.eschlon_id
            crop = field.crop
            
            if crop == "WHEAT":
                status = ""
            else:
                status = "APPROVED"
            variety = field.variety 
            shipment_id = generate_shipment_id()
            if id_storage == None :
                id_storage = None
               
            else:
                id_storage = id_storage
            
            shipment = GrowerShipment(status=status,total_amount=get_output,unit_type2=id_unit2,amount2=amount2,echelon_id=field.eschlon_id,
                                                            sustainability_score=surveyscore,amount=amount1,shipment_id=shipment_id,processor_id=processor_id,grower_id=grower_id,
                                                            storage_id=id_storage,field_id=field_id,variety=field.variety,crop=field.crop,module_number=module_number,unit_type=id_unit1,received_amount =received_weight,sku = sku_id,token_id=ticket_number,
                                                            approval_date = approval_date,moisture_level=moisture_level,fancy_count=fancy_count,head_count=head_count,bin_location_processor=bin_location_processor)
            shipment.save()
            for file in files:
                new_file = GrowerShipmentFile.objects.create(file=file)
                shipment.files.add(new_file)
            shipment.save()
            log_type, log_status, log_device = "GrowerShipment", "Added", "App"
            log_idd, log_name = shipment.id, shipment.shipment_id
            log_details = f"status = {status} | total_amount = {get_output} | unit_type2 = {id_unit2} | amount2 = {amount2} | echelon_id = {shipment.echelon_id} | sustainability_score = {shipment.sustainability_score} | amount = {shipment.amount} | variety = {shipment.variety} | crop = {shipment.crop} | shipment_id = {shipment.shipment_id} | processor_id = {shipment.processor.id} | grower_id = {shipment.grower.id} | storage_id = {id_storage} | field_id = {shipment.field.id} | module_number = {shipment.module_number} | unit_type = {shipment.unit_type} | "
            
            action_by_userid = user.id
            user_role = user.role.all()
            action_by_username = f'{user.first_name} {user.last_name}'
            action_by_email = user.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                log_device=log_device)
            logtable.save()
        response["status"], response["message"] = "200", "Delivery received successfully."
    elif user.is_processor2:
        p = ProcessorUser2.objects.get(contact_email=user.email)
        processor_id = p.processor2.id
        processor_type = p.processor2.processor_type.all().first().type_name
        selected_processor_id = request.data.get("selected_processor_id")
        selected_processor_type = request.data.get("selected_processor_type")
        selected_processor_name = request.data.get("selected_processor_name")
        selected_crop = request.data.get('selected_crop')
        variety = request.data.get('variety')
        milled_volume = request.data.get("milled_volume")
        sender_sku_id = request.data.get("sender_sku_id")
        receiver_sku_id = request.data.get("receiver_sku_id")
        volume_shipped = request.data.get("volume_shipped")
        lot_number = request.data.get("lot_number")
        purchase_number = request.data.get("purchase_number")
        equipment_type = request.data.get("equipment_type")
        equipment_id = request.data.get("equipment_id")
        weight_product = request.data.get("weight_product")
        weight_prod_unit = request.data.get("weight_prod_unit")
        exp_yield = request.data.get("exp_yield")
        exp_yield_unit = request.data.get("exp_yield_unit")
        status = "APPROVED"
        received_weight = request.data.get("received_weight")
        ticket_number = request.data.get("ticket_number")
        approval_date = request.data.get("approval_date")
        moist_percentage = request.data.get("moist_percentage")
        files = request.FILES.getlist("files")
        approval_date = datetime.strptime(approval_date, '%m/%d/%Y').strftime('%Y-%m-%d')
        try:
            milled_value = float(milled_volume)
        except ValueError as e:
            response["status"], response["message"] = "500", f"500, {e}"
        try:
            volume_shipped = float(volume_shipped)
        except ValueError as e:
            response["status"], response["message"] = "500", f"500, {e}"
        if milled_value < volume_shipped:
            response["status"], response["message"] = "500", f"Volume shipped cannot be greater than milled volume."

        else:
            if weight_prod_unit == "LBS" :
                cal_weight = round(float(weight_product),2)
            if weight_prod_unit == "BU" :
                cal_weight = round(float(weight_product) * 45,2)
            if exp_yield_unit == "LBS" :
                cal_exp_yield = round(float(exp_yield),2)
            if exp_yield_unit == "BU" :
                cal_exp_yield = round(float(exp_yield) * 45,2)
            
            volume_left = float(milled_volume) - float(volume_shipped)
            shipment_id = generate_shipment_id()
            
            save_shipment_management = ShipmentManagement(shipment_id=shipment_id,processor_idd=selected_processor_id,processor_e_name=selected_processor_name, sender_processor_type=selected_processor_type, bin_location=selected_processor_id,crop=selected_crop, variety=variety,
                    equipment_type=equipment_type,equipment_id=equipment_id,storage_bin_send=sender_sku_id,moisture_percent = moist_percentage,weight_of_product_raw = weight_product,
                    weight_of_product=cal_weight,weight_of_product_unit=weight_prod_unit, excepted_yield_raw =exp_yield,excepted_yield=cal_exp_yield,excepted_yield_unit=exp_yield_unit,recive_delivery_date=approval_date,
                    purchase_order_number=purchase_number,lot_number=lot_number,volume_shipped=volume_shipped,milled_volume=milled_volume,volume_left=volume_left,editable_obj=True,status=status,
                    storage_bin_recive=receiver_sku_id,ticket_number=ticket_number,received_weight=received_weight,processor2_idd=processor_id,processor2_name=p.processor2.entity_name, receiver_processor_type=processor_type)
            save_shipment_management.save()
            create_sku_list(selected_processor_id, selected_processor_type, sender_sku_id)
            create_sku_list(processor_id, processor_type, receiver_sku_id)
            
            for file in files:
                new_file = File.objects.create(file=file)
                save_shipment_management.files.add(new_file)
            save_shipment_management.save()
            #logtable
            log_type, log_status, log_device = "ShipmentManagement", "Added", "Web"
            log_idd, log_name = save_shipment_management.id, save_shipment_management.bin_location
            log_details = f"processor2 = {save_shipment_management.processor_e_name} | processor2_id = {save_shipment_management.processor_idd} | date_pulled = {save_shipment_management.date_pulled} | bin_location = {save_shipment_management.bin_location} | milled_volume = {save_shipment_management.milled_volume} | equipment_type = {save_shipment_management.equipment_type} | equipment_id = {save_shipment_management.equipment_id} | purchase_order_number = {save_shipment_management.purchase_order_number} | lot_number = {save_shipment_management.lot_number} | volume_shipped = {save_shipment_management.volume_shipped} | volume_left = {save_shipment_management.volume_left} | editable_obj = {save_shipment_management.editable_obj} "
            action_by_userid = user.id
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
            update_obj = ShipmentManagement.objects.filter(processor_idd=int(selected_processor_id)).exclude(id=save_shipment_management.id).values('id','editable_obj')
            
            if update_obj.exists():
                for i in update_obj :
                    get_obj = ShipmentManagement.objects.get(id=i['id'])
                    get_obj.editable_obj = False
                    get_obj.save()
            else:
                pass
        response["status"], response["message"] = "200", "Delivery received successfully."
    return Response(response)
  

@api_view(('POST',))
def processor_inbound_management_location_add_api(request):
    userid = request.data.get('userid')
    shipment_id = request.data.get('shipment_id')
    location_id = request.data.get('location_id')

    user = User.objects.get(id=userid)
    p = ProcessorUser.objects.get(contact_email=user.email)
    processor_id = Processor.objects.get(id=p.processor_id).id

    processor_shipment = GrowerShipment.objects.get(pk=shipment_id)
    processor_shipment.location_id = location_id
    processor_shipment.save()

    return Response({"message":"location is added to processor inbound"})


@api_view(('POST',))
def processor_outbound_list_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    p = ProcessorUser.objects.get(contact_email=user.email)
    processor_id = Processor.objects.get(id=p.processor_id).id
    grower_shipment = GrowerShipment.objects.filter(processor_id=processor_id)
    grower_shipment_outbound = []
    for i in range(len(grower_shipment)):
        location = grower_shipment[i].location
        if location != None :
            grower_shipment_outbound.append(grower_shipment[i].id)

    outbound_obj = GrowerShipment.objects.filter(id__in = grower_shipment_outbound)
    serializer = GrowerShipmentSerializer(outbound_obj, many=True)
    return Response({"data":serializer.data})

    # paginator = PageNumberPagination()
    # paginator.page_size = 10
    # result_page = paginator.paginate_queryset(outbound_obj, request)
    # serializer = GrowerShipmentSerializer(result_page, many=True)
    # return paginator.get_paginated_response({"data":serializer.data})
    # lst = []
    # for i in range(len(outbound_obj)):
    #     if outbound_obj[i].storage != None :
    #         storage_name = outbound_obj[i].storage.storage_name
    #     else:
    #         storage_name = "N/A"

    #     if outbound_obj[i].field != None :
    #         field_name = outbound_obj[i].field.name
    #     else:
    #         field_name = ""
        
    #     if outbound_obj[i].echelon_id != None :
    #         echelon_id = outbound_obj[i].echelon_id
    #     else:
    #         echelon_id = "N/A"

    #     loc = outbound_obj[i].location.name

    #     data = {
    #         "message":"processor_outbound , with recordes",
    #         "type": "processor",
    #         "GrowerShipment_Id":outbound_obj[i].id,
    #         "status":outbound_obj[i].status,
    #         "shipment_id":outbound_obj[i].shipment_id,
    #         "grower_name":outbound_obj[i].grower.name,
    #         "date_time":outbound_obj[i].date_time,
    #         "location":loc,
    #         "processor_name":outbound_obj[i].processor.entity_name,
    #         "grower_name":outbound_obj[i].grower.name,
    #         "module_number":outbound_obj[i].module_number,
    #         "storage_name":storage_name,
    #         "field_name":field_name,
    #         "amount":outbound_obj[i].amount,
    #         "amount2":outbound_obj[i].amount2,
    #         "unit_type":outbound_obj[i].unit_type,
    #         "unit_type2":outbound_obj[i].unit_type2,
    #         "total_amount":outbound_obj[i].total_amount,
    #         "crop":outbound_obj[i].crop,
    #         "variety":outbound_obj[i].variety,
    #         "echelon_id":echelon_id,
    #         "sustainability_score":outbound_obj[i].sustainability_score,            
    #     }
    #     lst.append(data)
    # return Response({'data':lst})

@api_view(('POST',))
def processor_outbound_list_search_api(request):
    userid = request.data['userid']
    search_keyword = request.data['search_keyword']
    user = User.objects.get(id=userid)
    p = ProcessorUser.objects.get(contact_email=user.email)
    processor_id = Processor.objects.get(id=p.processor_id).id
    grower_shipment = GrowerShipment.objects.filter(processor_id=processor_id)
    grower_shipment_outbound = []
    for i in range(len(grower_shipment)):
        location = grower_shipment[i].location
        if location != None :
            grower_shipment_outbound.append(grower_shipment[i].id)

    outbound_obj = GrowerShipment.objects.filter(id__in = grower_shipment_outbound).filter(shipment_id__icontains=search_keyword)
    serializer = GrowerShipmentSerializer(outbound_obj, many=True)
    return Response({"data":serializer.data})


@api_view(('POST',))
def processor_process_material_api(request):
    # userid = request.data['userid']
    shipment_id = request.data['shipment_id']
    amount = request.data['amount']
    date = request.data['date']
    time = request.data['time']
    sku = request.data['sku']
    # user = User.objects.get(id=userid)
    # p = ProcessorUser.objects.get(contact_email=user.email)
    # processor_id = Processor.objects.get(id=p.processor_id).id

    grower_shipment = GrowerShipment.objects.get(id=shipment_id)
    grower_shipment.process_amount = amount
    grower_shipment.process_date = date
    grower_shipment.process_time = time
    grower_shipment.sku = sku
    grower_shipment.save()
    return Response({"message":"shipment is added to process material"})

# @api_view(('POST',))
# def processor_scan_qr_code_api(request):
#     userid = request.data['userid']
#     shipment_id = request.data['shipment_id']
#     status = request.data['status']
#     if status == "APPROVED":
#         msg = "shipment is Approved"
#     if status == "DISAPPROVED":
#         msg = "shipment is Disapproved"
#     shipment = GrowerShipment.objects.get(shipment_id=shipment_id)
#     shipment.status = status
#     shipment.save()
#     return Response({"message":msg})


@api_view(('POST',))
def processor_scan_qr_code_api(request):
    # userid = request.data['userid']
    shipment_id = request.data['shipment_id']
    if GrowerShipment.objects.filter(shipment_id=shipment_id).count() != 0:
        shipment = GrowerShipment.objects.get(shipment_id=shipment_id)
        msg = "error"
        status = "error"
        if shipment.status == "APPROVED":
            msg = "shipment is Approved"
            status ="APPROVED"
        if shipment.status == "DISAPPROVED":
            msg = "shipment is Disapproved"
            status ="DISAPPROVED"
        if shipment.status == "":
            msg = "blank"
            status ="blank"
        return Response({"message":msg,"status":status})
    else:
        msg = "shipment has been deleted"
        status = "shipment has been deleted"
        return Response({"message":msg,"status":status})

@api_view(('POST',))
def processor_scanqrcode_status_approved_api(request):
    try:
        shipment_id = request.data['shipment_id']
        getstatus = request.data['status']
        received_amount = request.data['received_amount']
        token_id = request.data['token_id']
        approval_date = request.data['approval_date']
        # 02-02-23
        reason_for_disapproval = request.data['reason_for_disapproval']
        moisture_level = request.data['moisture_level']
        fancy_count = request.data['fancy_count']
        head_count = request.data['head_count']
        bin_location_processor = request.data['bin_location_processor']

        received_amount = str(received_amount).replace(",", "")
        received_amount = received_amount.replace("-", "")
        msg = ""
        if len(GrowerShipment.objects.filter(shipment_id=shipment_id)) > 0:
            if getstatus == "APPROVED":
                shipment = GrowerShipment.objects.get(shipment_id=shipment_id)
                shipment.status = "APPROVED"
                shipment.received_amount = received_amount
                shipment.token_id = token_id
                if approval_date :
                    shipment.approval_date = approval_date
                else:
                    shipment.approval_date = date.today()
                shipment.moisture_level = moisture_level
                shipment.fancy_count = fancy_count
                shipment.head_count = head_count
                shipment.bin_location_processor = bin_location_processor
                shipment.save()
                msg = "shipment is Approved"

                # 03-04-2023
                msg_subject = 'Shipment is received as Approved'
                msg_body = f'Dear Admin,\n\nA new shipment has been approved.\n\nThe details of the same are as below: \n\nShipment ID: {shipment.shipment_id} \nGrower: {shipment.grower.name} \nField: {shipment.field.name} \nReceived weight: {received_amount} LBS \nReceived date: {shipment.approval_date} \n\nRegards\nCustomer Service\nAgreeta'
                from_email = 'techsupportUS@agreeta.com'
                to_email = ['customerservice@agreeta.com']
                send_mail(
                msg_subject,
                msg_body,
                from_email,
                to_email,
                fail_silently=False,
                )
            if getstatus == "DISAPPROVED":
                shipment = GrowerShipment.objects.get(shipment_id=shipment_id)
                shipment.status = "DISAPPROVED"
                shipment.reason_for_disapproval = reason_for_disapproval
                shipment.moisture_level = moisture_level
                shipment.fancy_count = fancy_count
                shipment.head_count = head_count
                shipment.bin_location_processor = bin_location_processor
                if approval_date :
                    shipment.approval_date = approval_date
                else:
                    shipment.approval_date = date.today()
                shipment.save()
                msg = "shipment is Disapproved"

            return Response({"message":msg})
        else:
            msg = "shipment Not Found"
            return Response({"message":msg})
    except:   
        shipment_id = request.data['shipment_id']
        getstatus = request.data['status']
        received_amount = request.data['received_amount']
        token_id = request.data['token_id']
        approval_date = request.data['approval_date']
        received_amount = received_amount.replace(",", "")
        if len(GrowerShipment.objects.filter(shipment_id=shipment_id)) > 0:
            if getstatus == "APPROVED":
                shipment = GrowerShipment.objects.get(shipment_id=shipment_id)
                shipment.status = "APPROVED"
                shipment.received_amount = received_amount
                shipment.token_id = token_id
                if approval_date :
                    shipment.approval_date = approval_date
                else:
                    shipment.approval_date = date.today()
                shipment.save()
                msg = "shipment is Approved"
                # 03-04-2023
                msg_subject = 'Shipment is received as Approved'
                msg_body = f'Dear Admin,\n\nA new shipment has been approved.\n\nThe details of the same are as below: \n\nShipment ID: {shipment.shipment_id} \nGrower: {shipment.grower.name} \nField: {shipment.field.name} \nReceived weight: {received_amount} LBS \nReceived date: {shipment.approval_date} \n\nRegards\nCustomer Service\nAgreeta'
                from_email = 'techsupportUS@agreeta.com'
                to_email = ['customerservice@agreeta.com']
                send_mail(
                msg_subject,
                msg_body,
                from_email,
                to_email,
                fail_silently=False,
                )
            if getstatus == "DISAPPROVED":
                shipment = GrowerShipment.objects.get(shipment_id=shipment_id)
                shipment.status = "DISAPPROVED"
                if approval_date :
                    shipment.approval_date = approval_date
                else:
                    shipment.approval_date = date.today()
                shipment.save()
                msg = "shipment is Disapproved"

            return Response({"message":msg})
        else:
            msg = "shipment Not Found"
            return Response({"message":msg})
            
    # shipment_id = request.data['shipment_id']
    # getstatus = request.data['status']
    # received_amount = request.data['received_amount']
    # token_id = request.data['token_id']
    # approval_date = request.data['approval_date']
    # msg = ""
    # if len(GrowerShipment.objects.filter(shipment_id=shipment_id)) > 0:
    #     if getstatus == "APPROVED":
    #         shipment = GrowerShipment.objects.get(shipment_id=shipment_id)
    #         shipment.status = "APPROVED"
    #         shipment.received_amount = received_amount
    #         shipment.token_id = token_id
    #         shipment.approval_date = approval_date
    #         shipment.save()
    #         msg = "shipment is Approved"

    #     if getstatus == "DISAPPROVED":
    #         shipment = GrowerShipment.objects.get(shipment_id=shipment_id)
    #         shipment.status = "DISAPPROVED"
    #         shipment.save()
    #         msg = "shipment is Disapproved"

    #     return Response({"message":msg})
    # else:
    #     msg = "shipment Not Found"
    #     return Response({"message":msg})


# @api_view(('POST',))
# def processor_scan_qrcode_statuscheck_api(request):
#     shipment_id = request.data['shipment_id']
#     shipment = GrowerShipment.objects.get(shipment_id=shipment_id)
#     msg = "error"
#     if shipment.status == "APPROVED":
#         msg = "shipment is Approved"
#     if shipment.status == "DISAPPROVED":
#         msg = "shipment is Disapproved"
#     if shipment.status == "":
#         msg ="blank"
    
#     return Response({"message":msg})

# Grower Field Management
@api_view(('POST',))
def grower_field_list_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    grower_field = Field.objects.filter(grower_id=user.grower.id)
    if grower_field.count() == 0:
        data = []
        return Response({"status":"No recordes for You","data":data})
    else:
        grower_field = Field.objects.filter(grower_id=user.grower.id)
        serializer = FieldListSerializer(grower_field, many=True)
        return Response({"data":serializer.data})

        # paginator = PageNumberPagination()
        # paginator.page_size = 10
        # result_page = paginator.paginate_queryset(grower_field, request)
        # serializer = FieldListSerializer(result_page, many=True)
        # return paginator.get_paginated_response({"data":serializer.data})
        

@api_view(('POST',))
def grower_field_list_search_api(request):
    userid = request.data['userid']
    search_keyword = request.data['search_keyword']
    user = User.objects.get(id=userid)
    grower_field = Field.objects.filter(grower_id=user.grower.id).filter(name__icontains=search_keyword)
    serializer = FieldListSerializer(grower_field, many=True)
    return Response({"data":serializer.data})

@api_view(('POST',))
def grower_field_view_api(request):
    field_id = request.data['field_id']
    field = Field.objects.get(id=field_id)
    if field.eschlon_id != None:
        eschlon_id = field.eschlon_id
    else:
        eschlon_id = "N/A"
    
    if field.batch_id != None:
        batch_id = field.batch_id
    else:
        batch_id = "N/A"
    
    if field.fsa_farm_number != None:
        fsa_farm_number = field.fsa_farm_number
    else:
        fsa_farm_number = "N/A"
    if field.fsa_tract_number != None:
        fsa_tract_number = field.fsa_tract_number
    else:
        fsa_tract_number = "N/A"
    if field.fsa_field_number != None:
        fsa_field_number = field.fsa_field_number
    else:
        fsa_field_number = "N/A"
    if field.latitude != None:
        latitude = field.latitude
    else:
        latitude = "N/A"
    if field.longitude != None:
        longitude = field.longitude
    else:
        longitude = "N/A"
    if field.variety != None:
        variety = field.variety
    else:
        variety = "N/A"
    if field.yield_per_acre != None:
        yield_per_acre = field.yield_per_acre
    else:
        yield_per_acre = "N/A"
    if field.total_yield != None:
        total_yield = field.total_yield
    else:
        total_yield = "N/A"
    if field.crop_tech != None:
        crop_tech = field.crop_tech
    else:
        crop_tech = "N/A"
    

    # 21-12-22
    if field.previous_crop != None:
        previous_crop = field.previous_crop
    else:
        previous_crop = "N/A"
    
    if field.stand_count != None:
        stand_count = "{}".format(field.stand_count)
    else:
        stand_count = "N/A"
    if field.plant_date != None:
        plant_date = field.plant_date
    else:
        plant_date = "Select Date"
    if field.harvest_date != None:
        harvest_date = field.harvest_date
    else:
        harvest_date = "Select Date"
    
    data = {
        "field_id":field.id,
        "field_name":field.name,
        "farm_name":field.farm.name,
        "farm_id":field.farm.id,
        "acreage":str(field.acreage),
        "eschlon_id":eschlon_id,
        "batch_id":str(batch_id),
        "fsa_farm_number":fsa_farm_number,
        "fsa_tract_number":fsa_tract_number,
        "fsa_field_number":fsa_field_number,
        "latitude":str(latitude),
        "longitude":str(longitude),
        "crop":field.crop,
        "variety":variety,
        "yield_per_acre":str(yield_per_acre),
        "total_yield":str(total_yield),
        "crop_tech":crop_tech,
        "created_date":field.created_date,
        "modified_date":field.modified_date,

        "previous_crop":previous_crop,
        "stand_count":stand_count,
        "plant_date":plant_date,
        "harvest_date":harvest_date,
    }
    return Response({'data':data})
    # data = {
    #     "field_id":field.id,
    #     "field_name":field.name,
    #     "farm_name":field.farm.name,
    #     "farm_id":field.farm.id,
    #     "acreage":str(field.acreage),
    #     "eschlon_id":field.eschlon_id,
    #     "batch_id":str(field.batch_id),
    #     "fsa_farm_number":field.fsa_farm_number,
    #     "fsa_tract_number":field.fsa_tract_number,
    #     "fsa_field_number":field.fsa_field_number,
    #     "latitude":str(field.latitude),
    #     "longitude":str(field.longitude),
    #     "crop":field.crop,
    #     "variety":field.variety,
    #     "yield_per_acre":str(field.yield_per_acre),
    #     "total_yield":str(field.total_yield),
    #     "crop_tech":field.crop_tech,
    #     "created_date":field.created_date,
    #     "modified_date":field.modified_date,
    # }
    # return Response({'data':data})

@api_view(('POST',))
def grower_field_create_api(request):
    userid = request.data['userid']
    name = request.data['name']
    farm_id = request.data['farm_id']
    # grower_id = request.data['grower_id']
    batch_id = request.data['batch_id']
    acreage = request.data['acreage']
    fsa_farm_number = request.data['fsa_farm_number']
    fsa_tract_number = request.data['fsa_tract_number']
    fsa_field_number = request.data['fsa_field_number']
    latitude = request.data['latitude']
    longitude = request.data['longitude']
    crop = request.data['crop']
    variety = request.data['variety']
    yield_per_acre = request.data['yield_per_acre']
    total_yield = request.data['total_yield']
    crop_tech = request.data['crop_tech']
    eschlon_id = request.data['eschlon_id']
    # 21-12-22
    previous_crop = request.data['previous_crop']
    stand_count = request.data['stand_count']
    plant_date = request.data['plant_date']
    harvest_date = request.data['harvest_date']

    # field_activity = request.data['field_activity']
    # date_of_activity = request.data['date_of_activity']
    # type_of_application = request.data['type_of_application']
    # mode_of_application = request.data['mode_of_application']

    # label_name = request.data['label_name']
    # amount_per_acre = request.data['amount_per_acre']
    # unit_of_acre = request.data['unit_of_acre']
    # n_nitrogen = request.data['n_nitrogen']
    # p_phosporus = request.data['p_phosporus']
    # k_potassium = request.data['k_potassium']
    # special_notes = request.data['special_notes']

    user = User.objects.get(id=userid)
    grower_id = user.grower.id

    field = Field(name=name,farm_id=farm_id,grower_id=grower_id,batch_id=batch_id,acreage=acreage,
    fsa_farm_number=fsa_farm_number,fsa_tract_number=fsa_tract_number,fsa_field_number=fsa_field_number,
    latitude=latitude,longitude=longitude,crop=crop,variety=variety,yield_per_acre=yield_per_acre,
    total_yield=total_yield,crop_tech=crop_tech,eschlon_id=eschlon_id,previous_crop=previous_crop,stand_count=stand_count,
    plant_date=plant_date,harvest_date=harvest_date)
    field.save()
    # 14-04-23 Log Table
    log_type, log_status, log_device = "Field", "Added", "App"
    log_idd, log_name = field.id, field.name
    farm = Farm.objects.get(id=farm_id)
    grower = Grower.objects.get(id=grower_id)    
    log_details = f"name = {log_name} | farm = {farm.name} | grower = {grower.name} | acreage = {field.acreage} | crop = {field.crop} | variety = {field.variety}"
    action_by_userid = user.id
    user_role = user.role.all()
    action_by_username = f'{user.first_name} {user.last_name}'
    action_by_email = user.username
    if user.id == 1 :
        action_by_role = "superuser"
    else:
        action_by_role = str(','.join([str(i.role) for i in user_role]))
    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                        log_device=log_device)
    logtable.save()
    return Response({'message':"field is created"})


# @api_view(('POST',))
# def grower_field_activity_api(request):
#     userid = request.data['userid']



@api_view(('POST',))
def grower_farmdwopdown_forfield_api(request):
    userid = request.data['userid']
    grower_id= User.objects.get(id=userid).grower.id
    farm = Farm.objects.filter(grower_id=grower_id)
    lst = []
    for i in range(len(farm)):
        data = {
            "farm_name":farm[i].name,
            "farm_id":farm[i].id,
        }
        lst.append(data)
    return Response({'data':lst})




@api_view(('POST',))
def grower_field_edit_api(request):
    userid = request.data['userid']
    field_id = request.data['field_id']
    name = request.data['name']
    farm_id = request.data['farm_id']
    # grower_id = request.data['grower_id']
    batch_id = request.data['batch_id']
    acreage = request.data['acreage']
    fsa_farm_number = request.data['fsa_farm_number']
    fsa_tract_number = request.data['fsa_tract_number']
    fsa_field_number = request.data['fsa_field_number']
    latitude = request.data['latitude']
    longitude = request.data['longitude']
    crop = request.data['crop']
    variety = request.data['variety']
    yield_per_acre = request.data['yield_per_acre']
    total_yield = request.data['total_yield']
    crop_tech = request.data['crop_tech']
    eschlon_id = request.data['eschlon_id']
    user = User.objects.get(id=userid)
    grower_id = user.grower.id

    # 21-12-22
    previous_crop = request.data['previous_crop']
    stand_count = request.data['stand_count']
    plant_date = request.data['plant_date']
    harvest_date = request.data['harvest_date']

    field = Field.objects.get(id=field_id)
    field.name=name
    field.farm_id=farm_id
    field.batch_id=batch_id
    field.acreage=acreage
    field.fsa_farm_number=fsa_farm_number
    field.fsa_tract_number=fsa_tract_number
    field.fsa_field_number=fsa_field_number
    field.latitude=latitude
    field.longitude=longitude
    field.crop=crop
    field.variety=variety
    field.yield_per_acre=yield_per_acre
    field.total_yield=total_yield
    field.crop_tech=crop_tech
    field.eschlon_id=eschlon_id
    # 21-12-22
    field.previous_crop=previous_crop
    field.stand_count=stand_count
    field.plant_date=plant_date
    field.harvest_date=harvest_date
    field.save()
    # 14-04-23 Log Table
    log_type, log_status, log_device = "Field", "Edited", "App"
    log_idd, log_name = field.id, field.name
    farm = Farm.objects.get(id=farm_id)
    grower = Grower.objects.get(id=grower_id)    
    log_details = f"name = {log_name} | farm = {farm.name} | grower = {grower.name} | acreage = {field.acreage} | crop = {field.crop} | variety = {field.variety}"
    action_by_userid = user.id
    user_role = user.role.all()
    action_by_username = f'{user.first_name} {user.last_name}'
    action_by_email = user.username
    if user.id == 1 :
        action_by_role = "superuser"
    else:
        action_by_role = str(','.join([str(i.role) for i in user_role]))
    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                        log_device=log_device)
    logtable.save()
    return Response({'message':"field is edited"})

@api_view(('POST',))
def grower_field_delete_api(request):
    field_id = request.data['field_id']
    field = Field.objects.get(id=field_id)
    # 14-04-23 Log Table
    log_type, log_status, log_device = "Field", "Deleted", "App"
    log_idd, log_name = field.id, field.name
    farm = Farm.objects.get(id=field.farm.id)
    grower = Grower.objects.get(id=field.grower.id)    
    log_details = f"name = {log_name} | farm = {farm.name} | grower = {grower.name} | acreage = {field.acreage} | crop = {field.crop} | variety = {field.variety}"
    user= User.objects.get(grower_id=field.grower.id)
    action_by_userid = user.id
    user_role = user.role.all()
    action_by_username = f'{user.first_name} {user.last_name}'
    action_by_email = user.username
    if user.id == 1 :
        action_by_role = "superuser"
    else:
        action_by_role = str(','.join([str(i.role) for i in user_role]))
    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                        log_device=log_device)
    logtable.save()
    field.delete()
    return Response({"message":"field is deleted"})


# Grower Farm Management
@api_view(('POST',))
def grower_farm_list_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    grower_farm = Farm.objects.filter(grower_id=user.grower.id)
    if grower_farm.count() == 0:
        data = []
        return Response({"status":"No recordes for You","data":data})
    else:
        
        grower_farm = Farm.objects.filter(grower_id=user.grower.id)
        serializer = FarmSerializer(grower_farm, many=True)
        return Response({"data":serializer.data})
        # paginator = PageNumberPagination()
        # paginator.page_size = 10
        # result_page = paginator.paginate_queryset(grower_farm, request)
        # serializer = FarmSerializer(result_page, many=True)
        
        # return paginator.get_paginated_response({"data":serializer.data})
        # lst = []
        # for i in range(len(grower_farm)):
        #     data = {
        #         "message":"grower_farm_list_api , with recordes",
        #         "type":"grower",
        #         "userid":user.id,
        #         "username":user.username,
        #         "email":user.email,
        #         "farm_id":grower_farm[i].id,
        #         "farm_name":grower_farm[i].name,
        #     }
        #     lst.append(data)
        # return Response({'data':lst})

@api_view(('POST',))
def grower_farm_list_search_api(request):
    userid = request.data['userid']
    search_keyword = request.data['search_keyword']
    user = User.objects.get(id=userid)
    # grower_farm = Farm.objects.filter(grower_id=user.grower.id)
    grower_farm = Farm.objects.filter(grower_id=user.grower.id).filter(name__icontains=search_keyword)
    
    serializer = FarmSerializer(grower_farm, many=True)
    return Response({'data':serializer.data})

@api_view(('POST',))
def grower_farm_view_api(request):
    farm_id = request.data['farm_id']
    farm = Farm.objects.get(id=farm_id)
    if farm.cultivation_year != None:
        cultivation_year = farm.cultivation_year
    else:
        cultivation_year = "N/A"

    if farm.area != None:
        area = farm.area
    else:
        area = "N/A"
    if farm.land_type != None:
        crop = farm.land_type
    else:
        crop = "N/A"
    if farm.state != None:
        state = farm.state
    else:
        state = "N/A"
    if farm.county != None:
        county = farm.county
    else:
        county = "N/A"

    if farm.village != None:
        address_2 = farm.village
    else:
        address_2 = "N/A"
    
    if farm.town != None:
        city = farm.town
    else:
        city = "N/A"

    if farm.street != None:
        mailing_address_1 = farm.street
    else:
        mailing_address_1 = "N/A"

    if farm.nutrien_account_id != None:
        nutrien_account_id = farm.nutrien_account_id
    else:
        nutrien_account_id = "N/A"
    
    if farm.zipcode != None:
        zipcode = farm.zipcode
    else:
        zipcode = "N/A"

    data = {
        "farm_id":farm.id,
        "farm_name":farm.name,
        "cultivation_year":cultivation_year,
        "area":str(area),
        "crop":crop,
        "state":state,
        "county":county,
        "address_2":address_2,
        "city":city,
        "mailing_address_1":mailing_address_1,
        "nutrien_account_id":nutrien_account_id,
        "zipcode":str(zipcode),
        "created_date":farm.created_date,
        "modified_date":farm.modified_date,
    }
    return Response({'data':data})


@api_view(('POST',))
def grower_farm_create_api(request):
    userid = request.data['userid']
    name = request.data['name']
    cultivation_year = request.data['cultivation_year']
    # grower_id = request.data['grower_id']
    # 3 area
    area = request.data['area']
    # 4 crop as land_type
    land_type = request.data['crop']
    # 5 street as Mailing Address 1
    street = request.data['mailing_address_1']
    # 6 village as "Address 2"
    village = request.data['address_2']
    # 7 "town" as "City"
    town = request.data['city']
    # 8 state
    state = request.data['state']
    # 9 zipcode
    zipcode = request.data['zipcode']
    # 10 county
    county = request.data['county']
    # 11 nutrien_account_id
    nutrien_account_id = request.data['nutrien_account_id']

    user = User.objects.get(id=userid)
    grower_id = user.grower.id

    make_farm = Farm(name=name,grower_id=grower_id,cultivation_year=cultivation_year,area=area,land_type=land_type,
    state=state,county=county,village=village,town=town,street=street,zipcode=zipcode,nutrien_account_id=nutrien_account_id)
    make_farm.save()
    # Log Table 14-04-23
    log_type, log_status, log_device = "Farm", "Added", "App"
    log_idd, log_name = make_farm.id, name
    log_details = f"name = {name} | cultivation_year = {cultivation_year} | area = {area} | land_type = {land_type} | zipcode = {zipcode} | grower = {user.first_name} {user.last_name}"
    action_by_userid = userid
    user_role = user.role.all()
    action_by_username = f'{user.first_name} {user.last_name}'
    action_by_email = user.username
    if userid == 1 :
        action_by_role = "superuser"
    else:
        action_by_role = str(','.join([str(i.role) for i in user_role]))
    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                        action_by_email=action_by_email,action_by_role=action_by_role,
                        log_details=log_details,log_device=log_device)
    logtable.save()

    return Response({'message':"farm is created"})


@api_view(('POST',))
def grower_farm_edit_api(request):
    userid = request.data['userid']
    farm_id = request.data['farm_id']
    name = request.data['name']
    cultivation_year = request.data['cultivation_year']
    # grower_id = request.data['grower_id']
    # 3 area
    area = request.data['area']
    # 4 crop as land_type
    land_type = request.data['crop']
    # 5 street as Mailing Address 1
    street = request.data['mailing_address_1']
    # 6 village as "Address 2"
    village = request.data['address_2']
    # 7 "town" as "City"
    town = request.data['city']
    # 8 state
    state = request.data['state']
    # 9 zipcode
    zipcode = request.data['zipcode']
    # 10 county
    county = request.data['county']
    # 11 nutrien_account_id
    nutrien_account_id = request.data['nutrien_account_id']

    user = User.objects.get(id=userid)
    grower_id = user.grower.id

    farm = Farm.objects.get(id=farm_id)
    farm.name = name
    farm.cultivation_year = cultivation_year
    farm.area = area
    farm.land_type = land_type
    farm.street = street
    farm.village = village
    farm.town = town
    farm.state = state
    farm.zipcode = zipcode
    farm.county = county
    farm.nutrien_account_id = nutrien_account_id
    farm.save()
    # Log Table 14-04-23
    log_type, log_status, log_device = "Farm", "Edited", "App"
    log_idd, log_name = farm.id, farm.name
    log_details = f"name = {farm.name} | cultivation_year = {farm.cultivation_year} | area = {farm.area} | land_type = {farm.land_type} | zipcode = {farm.zipcode} | grower = {user.first_name} {user.last_name}"
    action_by_userid = userid
    user_role = user.role.all()
    action_by_username = f'{user.first_name} {user.last_name}'
    action_by_email = user.username
    if userid == 1 :
        action_by_role = "superuser"
    else:
        action_by_role = str(','.join([str(i.role) for i in user_role]))
    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                        action_by_email=action_by_email,action_by_role=action_by_role,
                        log_details=log_details,log_device=log_device)
    logtable.save()
    return Response({'message':"farm is edited"})


@api_view(('POST',))
def grower_farm_delete_api(request):
    farm_id = request.data['farm_id']
    farm = Farm.objects.get(id=farm_id)
    # Log Table 14-04-23
    log_type, log_status, log_device = "Farm", "Deleted", "App"
    log_idd, log_name = farm.id, farm.name
    log_details = f"name = {farm.name} | cultivation_year = {farm.cultivation_year} | area = {farm.area} | land_type = {farm.land_type} | zipcode = {farm.zipcode} | grower = {farm.grower.name}"
    
    user= User.objects.get(grower_id=farm.grower.id)
    action_by_userid = user.id
    user_role = user.role.all()
    action_by_username = f'{user.first_name} {user.last_name}'
    action_by_email = user.username
    if user.id == 1 :
        action_by_role = "superuser"
    else:
        action_by_role = str(','.join([str(i.role) for i in user_role]))
    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                        action_by_email=action_by_email,action_by_role=action_by_role,
                        log_details=log_details,log_device=log_device)
    logtable.save()
    farm.delete()
    return Response({"message":"farm is deleted"})


@api_view(('POST',))
def classing_list_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    user_email = user.email
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor_id = Processor.objects.get(id=p.processor_id).id
    grower = LinkGrowerToProcessor.objects.filter(processor_id=processor_id)
    grower_id = [i.grower_id for i in grower]
    classing = ClassingReport.objects.filter(grower_id__in=grower_id)
    class_list = []
    for i in classing :
        bale = BaleReportFarmField.objects.filter(classing_id = i.id)[:1]
        if bale :
            field_name = [i.field_name for i in bale][0]
            
        else:
            field_name = 'N/A'
        csv_name = str(i.csv_path).split('/')[1]
        data = {
            "processor":i.processor.entity_name,
            "grower":i.grower.name,
            "fieldName":field_name,
            "fileName":csv_name,
            "reportname":i.csv_type,
        }
        class_list.append(data)
    return Response({'data':class_list})


@api_view(('POST',))
def classing_csv_list_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    user_email = user.email
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor_id = Processor.objects.get(id=p.processor_id).id
    cr = ClassingReport.objects.filter(processor_id=processor_id)
    rp = [i.id for i in cr]
    report_data = BaleReportFarmField.objects.filter(classing_id__in=rp)
    class_list = []
    for i in report_data :
        if i.farm_name :
            farm = str(i.farm_name).strip('.0')
        else:
            farm = 'N/A'
        if i.field_name :
            field = i.field_name
        else:
            field = 'N/A'
        if i.ob5 :
            certificate = i.ob5
        else:
            certificate = 'N/A'

        data = {
            "grower":i.ob3,
            "bale_id":i.bale_id,
            "field":field,
            "farm":farm,
            "certificate":certificate,
            "level":i.level,
            "warehouse_wh_id":i.warehouse_wh_id,
            "date":i.dt_class,
            "net_wt":i.net_wt,
            "value":i.value,
            "view":i.id,
        }
        class_list.append(data)
    return Response({'data':class_list})


@api_view(('POST',))
def classing_csv_list_view_api(request):
    dataid = request.data['dataid']
    report_data =  BaleReportFarmField.objects.get(id=int(dataid))
    csv_name = str(report_data.classing.csv_path).split('/')[1]
    if report_data.farm_name :
        farm = str(report_data.farm_name).strip('.0')
    else:
        farm = report_data.farm_name
    responce = {
        "prod_id":report_data.prod_id,
        "farm":farm,
        "grower":report_data.ob3,
        "wh_id":report_data.wh_id,
        "bale_id":report_data.bale_id,
        "warehouse_wt":report_data.warehouse_wh_id,
        "dt_class":report_data.dt_class,
        "net_wt":report_data.net_wt,
        "farm_id":report_data.farm_id,
        "load_id":report_data.load_id,
        "field":report_data.field_name,
        "crop_variety": report_data.crop_variety,
        "certificate":report_data.ob5,
        "level":report_data.level,
        "pk_num":report_data.pk_num,
        "gr":report_data.gr,
        "lf":report_data.lf,
        "st":report_data.st,
        "mic":report_data.mic,
        "ex":report_data.ex,
        "rm":report_data.rm,
        "str_no":report_data.str_no,
        "cgr":report_data.cgr,
        "rd":report_data.rd,
        "ob1":report_data.ob1,
        "tr":report_data.tr,
        "unif":report_data.unif,
        "len_num":report_data.len_num,
        "elong":report_data.elong,
        "value":report_data.value,
        "csv_type":report_data.classing.csv_type,
        "csv_name":csv_name,
        }
    return Response({'data':responce})


@api_view(('POST',))
def production_management_list_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    user_email = user.email
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor_id = Processor.objects.get(id=p.processor_id).id
    output = ProductionManagement.objects.filter(processor_id=processor_id).order_by('-id').values('processor_e_name','date_pulled','bin_location','total_volume','volume_pulled','milled_volume','volume_left','milled_storage_bin')
    return Response({'data':output})

@api_view(('POST',))
def get_total_rice_volume_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    user_email = user.email
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor_id = Processor.objects.get(id=p.processor_id).id
    shipment = GrowerShipment.objects.filter(processor_id = processor_id).filter(status ="APPROVED").filter(crop ="RICE").values('received_amount')
    total_receive_weight = []
    total_volume_pulled_till_now = []
    if shipment.exists() :
        for i in shipment :
            try:
                total_receive_weight.append(float(i['received_amount']))
            except:
                total_receive_weight.append(float(0))
        total_receive_weight = sum(total_receive_weight)
    else:
        final_total_volume = 0
        total_volume_pulled_till_now = 0
        total_receive_weight = 0


    volume_pulled_till_now = ProductionManagement.objects.filter(processor_id = processor_id).values('volume_pulled')
    for i in volume_pulled_till_now :
        total_volume_pulled_till_now.append(float(i['volume_pulled']))
    
    try:
        sum_volume_pulled_till_now = sum(total_volume_pulled_till_now)
    except:
        sum_volume_pulled_till_now = 0
    
    output = total_receive_weight - sum_volume_pulled_till_now
    return Response({'data':output})


@api_view(('POST',))
def add_volume_pulled_api(request):
    userid = request.data['userid']
    id_date = request.data['id_date']
    bin_location = request.data['bin_location']
    volume_pulled = request.data['volume_pulled']
    milled_volume = request.data['milled_volume']
    milled_storage_bin = request.data['milled_storage_bin']
    user = User.objects.get(id=userid)
    user_email = user.email
    
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor_id = Processor.objects.get(id=p.processor_id).id
    
    if volume_pulled!= "" and id_date!= "" and milled_volume!= "" :
        volume_pulled = str(volume_pulled).replace(",","")
        milled_volume = str(milled_volume).replace(",","")
        shipment = GrowerShipment.objects.filter(processor_id = processor_id).filter(status ="APPROVED").filter(crop ="RICE").values('received_amount')
        total_receive_weight = []
        total_volume_pulled_till_now = []
        if shipment.exists() :
            for i in shipment :
                try:
                    total_receive_weight.append(float(i['received_amount']))
                except:
                    total_receive_weight.append(float(0))
            total_receive_weight = sum(total_receive_weight)
        else:
            final_total_volume = 0
            total_volume_pulled_till_now = 0
            total_receive_weight = 0


        volume_pulled_till_now = ProductionManagement.objects.filter(processor_id = processor_id).values('volume_pulled')
        for i in volume_pulled_till_now :
            total_volume_pulled_till_now.append(float(i['volume_pulled']))
        
        try:
            sum_volume_pulled_till_now = sum(total_volume_pulled_till_now)
        except:
            sum_volume_pulled_till_now = 0
        
        final_total_volume = total_receive_weight - sum_volume_pulled_till_now

        volume_left = float(final_total_volume) - float(volume_pulled)
        processor_e_name = Processor.objects.get(id=processor_id).entity_name
        save_production_management=ProductionManagement(processor_id=processor_id,processor_e_name=processor_e_name,
        total_volume=final_total_volume,date_pulled=id_date,bin_location=bin_location,volume_pulled=volume_pulled,
        milled_volume=milled_volume,volume_left=volume_left,milled_storage_bin=milled_storage_bin,editable_obj=True)
        save_production_management.save()
        update_obj = ProductionManagement.objects.filter(processor_id=processor_id).exclude(id=save_production_management.id).values('id','editable_obj')
                
        if update_obj.exists():
            for i in update_obj :
                get_obj = ProductionManagement.objects.get(id=i['id'])
                get_obj.editable_obj = False
                get_obj.save()
        else:
            pass
        return Response({'msg':"added"})
    else:
        return Response({'msg':"error"})
    

@api_view(('POST',))
def outbound_shipment_management_list_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    user_email = user.email
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor_id = Processor.objects.get(id=p.processor_id).id
    output = ShipmentManagement.objects.filter(processor_idd=processor_id).order_by('bin_location').values('bin_location','processor_e_name','milled_volume',
                                                                                                           'date_pulled','volume_shipped','volume_left')
    return Response({'data':output})


@api_view(('POST',))
def get_rice_volume_from_bin_location_pulled_api(request):
    userid = request.data['userid']
    id_bin_location_pull = request.data['bin_location_pull']
    user = User.objects.get(id=userid)
    user_email = user.email
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor_id = Processor.objects.get(id=p.processor_id).id
    get_bin_location = ProductionManagement.objects.filter(milled_storage_bin=id_bin_location_pull,processor_id=processor_id).values('milled_volume','id','processor_id','processor_e_name')
    shiped_volume = ShipmentManagement.objects.filter(bin_location=id_bin_location_pull).values('volume_shipped')
    output = ''
    if id_bin_location_pull != '' and get_bin_location.exists() :
        total_bin_location_milled_volume = []
        total_shiped_volume = []
        for i in get_bin_location :
            total_bin_location_milled_volume.append(float(i['milled_volume']))
        for i in shiped_volume :
            total_shiped_volume.append(float(i['volume_shipped']))
        
        sum_total__volume = sum(total_bin_location_milled_volume)
        sum_shiped_volume = sum(total_shiped_volume)
        sum_total_bin_location_milled_volume = float(sum_total__volume) - float(sum_shiped_volume)
        output = sum_total_bin_location_milled_volume
    else:
        output = "Bin Location Pulled from not exists"
    
    return Response({'data':output})

@api_view(('POST',))
def add_outbound_shipment_management_api(request):
    userid = request.data['userid']
    id_bin_location_pull = request.data['bin_location_pull']
    id_date = request.data['id_date']
    equipment_type = request.data['equipment_type']
    equipment_id = request.data['equipment_id']
    purchase_number = request.data['purchase_number']
    lot_number = request.data['lot_number']
    volume_shipped = request.data['volume_shipped']
    msg = ''
    user = User.objects.get(id=userid)
    user_email = user.email
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor_id = Processor.objects.get(id=p.processor_id).id
    get_bin_location = ProductionManagement.objects.filter(milled_storage_bin=id_bin_location_pull,processor_id=processor_id).values('milled_volume','id','processor_id','processor_e_name')
    shiped_volume = ShipmentManagement.objects.filter(bin_location=id_bin_location_pull).values('volume_shipped')
    if id_bin_location_pull != '' and get_bin_location.exists() and id_date and volume_shipped :
        volume_shipped = str(volume_shipped).replace(",","")
        total_bin_location_milled_volume = []
        total_shiped_volume = []
        for i in get_bin_location :
            total_bin_location_milled_volume.append(float(i['milled_volume']))
        for i in shiped_volume :
            total_shiped_volume.append(float(i['volume_shipped']))
        
        sum_total__volume = sum(total_bin_location_milled_volume)
        sum_shiped_volume = sum(total_shiped_volume)
        sum_total_bin_location_milled_volume = float(sum_total__volume) - float(sum_shiped_volume)

        bin_location = id_bin_location_pull
        processor_id = [i['processor_id'] for i in get_bin_location][0]
        processor_e_name = [i['processor_e_name'] for i in get_bin_location][0]
        milled_volume = sum_total_bin_location_milled_volume
        volume_left = float(milled_volume) - float(volume_shipped)
        if equipment_type and equipment_type != "" :
            equipment_type = equipment_type
        else:
            equipment_type = None

        save_shipment_management = ShipmentManagement(processor_idd=processor_id,processor_e_name=processor_e_name,bin_location=bin_location,
        date_pulled=id_date,equipment_type=equipment_type,equipment_id=equipment_id,purchase_order_number=purchase_number,
        lot_number=lot_number,volume_shipped=volume_shipped,milled_volume=milled_volume,volume_left=volume_left,editable_obj=True)
        save_shipment_management.save()
        update_obj = ShipmentManagement.objects.filter(processor_idd=processor_id).exclude(id=save_shipment_management.id).values('id','editable_obj')
        
        if update_obj.exists():
            for i in update_obj :
                get_obj = ShipmentManagement.objects.get(id=i['id'])
                get_obj.editable_obj = False
                get_obj.save()
        else:
            pass
        msg = 'added'
    else:
        msg = 'error'
    return Response({'msg':msg})



@api_view(('POST',))
def grower_grower_payments_list(request):
    userid = request.data['userid']
    try:
        user = User.objects.get(id=userid)
        grower_id=user.grower.id
        gpay = GrowerPayments.objects.filter(grower_id=grower_id).values('delivery_id').order_by('-id')
    except :
        gpay = []
    return Response({'data':gpay})

@api_view(('POST',))
def grower_grower_payments_view(request):
    delivery_id = request.data['delivery_id']
    try:
        gpay = GrowerPayments.objects.get(delivery_id=delivery_id)
        # gpay = GrowerPayments.objects.filter(grower_id=grower_id).values('delivery_date','delivery_id',
        #                                     'grower__name','crop','variety','farm_name','field_name',
        #                                     'level','delivery_lbs','total_price','delivered_value',
        #                                     'payment_due_date','payment_amount','payment_date','payment_type',
        #                                     'payment_confirmation')
        if gpay.crop == "COTTON" :
            delivery_date = gpay.delivery_date
        else :
            if GrowerShipment.objects.filter(shipment_id=delivery_id).exists():
                get_shipment = GrowerShipment.objects.get(shipment_id=delivery_id)
                delivery_date = get_shipment.approval_date.strftime("%m/%d/%y")
        responce = {
            "delivery_date":delivery_date,
            "delivery_id":gpay.delivery_id,
            "grower_name":gpay.grower.name,
            "crop":gpay.crop,
            "variety":gpay.variety,
            "farm_name":gpay.farm_name,
            "field_name":gpay.field_name,
            "level":gpay.level,
            "delivery_lbs":gpay.delivery_lbs,
            "total_price":"{0:.4f}".format(float(gpay.total_price)),
            "delivered_value":"{0:.4f}".format(float(gpay.delivered_value)),
            "payment_due_date":gpay.payment_due_date,
            "payment_amount":gpay.payment_amount,
            "payment_date":gpay.payment_date,
            "payment_type":gpay.payment_type,
            "payment_confirmation":gpay.payment_confirmation,
            }
    except :
        responce = []
    
    return Response({'data':responce})


@api_view(('POST',))
def grower_grower_payments_cal_details(request):
    responce = []
    userid = request.data['userid']
    try:
        user = User.objects.get(id=userid)
        grower_id=user.grower.id
        # gpay = GrowerPayments.objects.filter(grower_id=grower_id).values('delivery_lbs','delivered_value','payment_amount')
        res_queryset = GrowerPayments.objects.filter(grower_id=grower_id).values('delivery_lbs','delivered_value','payment_amount')
        sum_delivery_lbs = sum(float(item['delivery_lbs']) for item in res_queryset)
        sum_delivered_value = "{0:.4f}".format(sum(float(item['delivered_value']) for item in res_queryset))
        sum_payment_amount = "{0:.4f}".format(sum(int(float(item['payment_amount'])) for item in res_queryset))
        responce = {'total_no_of_deliveries_paid':res_queryset.count(),'total_delivery_lbs':sum_delivery_lbs,'total_delivered_value':sum_delivered_value,'total_payment_amount':sum_payment_amount}
    except:
        pass
    return Response({'data':responce})

@api_view(('POST',))
def t2_processor_dashboard_api(request):
    responce = []
    userid = request.data['userid']
    try:
        user = User.objects.get(id=userid)
        if user.is_processor2 :
            t2_p2 = ProcessorUser2.objects.get(contact_email=user.email)
            responce = {
                "fein" : t2_p2.processor2.fein,
                "entity_name": t2_p2.processor2.entity_name,
                "billing_address" : t2_p2.processor2.billing_address,
                "shipping_address" : t2_p2.processor2.shipping_address,
                "main_number" : t2_p2.processor2.main_number,
                "main_fax" : t2_p2.processor2.main_fax,
                "website" : t2_p2.processor2.website,
                "contact_name" : t2_p2.contact_name,
                "contact_email" : t2_p2.contact_email,
                "contact_phone" : t2_p2.contact_phone,
                "contact_fax" : t2_p2.contact_fax
            }
        else:
            pass
    except:
        pass
    return Response({'data':responce})

@api_view(('POST',))
def t2_processor_EWR_reprt_download(request):
    response = Response({'data':[]})
    userid = request.data['userid']
    try:
        user = User.objects.get(id=userid)
        if user.is_processor2 :
            processor_user2 = ProcessorUser2.objects.get(contact_email=user.email)
            report = AssignedBaleProcessor2.objects.filter(processor2__id=processor_user2.processor2.id).values('warehouse_wh_id','assigned_bale')
            response = HttpResponse(content_type='text/plain')
            current_date = date.today().strftime("%m-%d-%Y")
            report_name = f"{processor_user2.processor2.entity_name}_EWR_Report_{current_date}"
            response['Content-Disposition'] = 'attachment; filename="{}.txt"'.format(report_name)
            for i in report:
                response.write("{}{}{}\n".format(i['warehouse_wh_id'],i['assigned_bale'],2023))
        else:
            pass
    except:
        pass
    return response

@api_view(('POST',))
def processor_EWR_reprt_download(request):
    response = Response({'data':[]})
    userid = request.data['userid']
    try:
        user = User.objects.get(id=userid)
        if user.is_processor :
            processor = ProcessorUser.objects.get(contact_email=user.email)
            cr = ClassingReport.objects.filter(processor_id=processor.id)
            rp = [i.id for i in cr]
            report = BaleReportFarmField.objects.filter(classing_id__in=rp).values('warehouse_wh_id','bale_id')
            response = HttpResponse(content_type='text/plain')
            current_date = date.today().strftime("%m-%d-%Y")
            report_name = f"{processor.processor.entity_name}_EWR_Report_{current_date}"
            response['Content-Disposition'] = 'attachment; filename="{}.txt"'.format(report_name)
            for i in report:
                response.write("{}{}{}\n".format(i['warehouse_wh_id'],i['bale_id'],2022))
        else:
            pass
    except:
        pass
    return response



@api_view(('POST',))
def t2_processor_classing_list_api(request):
    response = Response({'data':[]})
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    try:
        if user.is_processor2 :
            processor_user2 = ProcessorUser2.objects.get(contact_email=user.email)
            report = AssignedBaleProcessor2.objects.filter(processor2__id=processor_user2.processor2.id).values('assigned_bale','warehouse_wh_id',
                                                            'farm_name','field_name','mark_id','grower_name').order_by('-id')
            response = Response({'data':report})
    except:
        pass
    return response


@api_view(('POST',))
def t2_processor_classing_view_api(request):
    response = Response({'data':[]})
    assigned_bale = request.data['assigned_bale']
    warehouse_wh_id = request.data['warehouse_wh_id']
    try:
        check_report = AssignedBaleProcessor2.objects.filter(assigned_bale=assigned_bale,warehouse_wh_id=warehouse_wh_id)       
        if check_report.exists():
            check_report_id = [i.id for i in check_report][0]
            gRpot = AssignedBaleProcessor2.objects.get(id=check_report_id)
            try:
                bale = BaleReportFarmField.objects.get(bale_id=assigned_bale)
                csv_name = str(bale.classing.csv_path).split('/')[1]
            except:
                csv_name = ""
            report = {'prod_id':gRpot.id,'farm_name':gRpot.farm_name,'grower_name':gRpot.grower_name,'assigned_bale':gRpot.assigned_bale,
                      'warehouse_wh_id':gRpot.warehouse_wh_id,'dt_class':gRpot.dt_class,'net_wt':gRpot.net_wt,'load_id':gRpot.load_id,
                      'field_name':gRpot.field_name,'certificate':gRpot.certificate,'level':gRpot.level,'crop_variety':gRpot.crop_variety,
                      'mark_id':gRpot.mark_id,'gin_id':gRpot.gin_id,'cgr':gRpot.cgr,'lf':gRpot.lf,'st':gRpot.st,'mic':gRpot.mic,'str_no':gRpot.str_no,
                      'unif':gRpot.unif,'len_num':gRpot.len_num,'gr':gRpot.gr,"csv_name":csv_name,"value":gRpot.value,"ex":gRpot.ex,
                      "elong":gRpot.elong,"rm":gRpot.rm,"tr":gRpot.tr,"rd":gRpot.rd,"variety":gRpot.crop_variety,"ob1":gRpot.ob1}
 
            response = Response(report)
    except:
        pass
    return response

@api_view(('POST',))
def t2_processor_grower_dropdown_api(request):
    response = Response({'data':[]})
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    try:
        if user.is_processor2 :
            processor_user2 = ProcessorUser2.objects.get(contact_email=user.email)
            report = AssignedBaleProcessor2.objects.filter(processor2__id=processor_user2.processor2.id).values('grower_name','grower_idd').distinct().order_by('grower_name')
            response = Response({'data':report})
    except:
        pass
    return response

@api_view(('POST',))
def grower_dashboard_graph_api(request):
    response = Response({'data':[]})
    userid = request.data['userid']
    field_id = request.data['field_id']
    user = User.objects.get(id=userid)
    # try:
    data = {'farms':[],'fields':[],'storages':[],'payment_summary':[],'shipment':[],'survey_summary':[],'field_info_vegetation_report':[],'shipment_chart':[]}
    g_id = user.grower.id
    if user.grower_id and field_id != 'all' :
        check_field = Field.objects.filter(id=field_id,grower_id=user.grower.id)
        if check_field.exists() :
            shipment = grower_Field_Shipment_Details(field_id)
            vegetation_chart = grower_Field_Vegetation_Chart(field_id)
            shipment_chart = grower_Field_Shipment_Chart(field_id)

            sus = SustainabilitySurvey.objects.filter(field_id=field_id)
            get_crop = [i.crop for i in check_field][0]
            # shipment details ...payment_amount, shipment_paid_amount
            data['shipment']+=[{'total_weight_of_shipment':shipment['shipment_wt'],'total_number_of_delivered_shipment':shipment['shipment_count'],
                                'total_weight_of_delivered_shipment':shipment['shipment_delivered_wt'],'projected_yield':shipment['projected_yield'],
                                'actual_yield':shipment['actual_yield'],'yield_delta':shipment['yield_delta'],'number_of_payee':shipment['g_payee_count'],
                                'number_of_lien_holder':shipment['lien_holder_count'],'number_of_split_payee':shipment['payment_split_count']}]
                                
            if get_crop == 'COTTON':
                    data['shipment']+=[{'per_lls':shipment['per_lls'],'per_gold':shipment['per_gold'],'per_silver':shipment['per_silver'],'per_bronze':shipment['per_bronze'],
                                        'per_nonee':shipment['per_nonee'],'per_delivered':shipment['per_delivered']}]
            else:
                data['shipment']+=[{'per_approved_shipment':shipment['per_approved_shipment'],'per_disapproved_shipment':shipment['per_disapproved_shipment'],
                                    'per_noStatus__shipment':shipment['per_noStatus__shipment'],'shipment_paid_amount':shipment['shipment_paid_amount']}]
            # survey_summary details ...
            for i in sus :
                data['survey_summary']+=[[{'survey_name':f'{i.namesurvey}','survey_score':i.surveyscore}]]
                
            # vegetation_chart report ....
            data['field_info_vegetation_report']+=[{'gal_water_saved':vegetation_chart[0]['gal_water_saved'],'water_lbs_saved':vegetation_chart[0]['water_lbs_saved'],
                                                    'co2_eq_reduced':vegetation_chart[0]['co2_eq_reduced'],'increase_nitrogen':vegetation_chart[0]['increase_nitrogen'],
                                                    'ghg_reduction':vegetation_chart[0]['ghg_reduction'],'land_use_efficiency':vegetation_chart[0]['land_use_efficiency'],
                                                    'grower_premium_percentage':vegetation_chart[0]['grower_premium_percentage'],'grower_dollar_premium':vegetation_chart[0]['grower_dollar_premium']}]
            
            # shipment_chart .....
            data['shipment_chart']+=shipment_chart
        else:
            pass
    else:
        pass
    get_farms = Farm.objects.filter(grower_id=g_id).order_by('name').values('name','state','county','village','town','street','zipcode')
    get_fields = Field.objects.filter(grower_id=g_id).order_by('name').values('name','farm__name','crop','acreage')
    get_storages = Storage.objects.filter(grower_id=g_id).order_by('storage_name').values('storage_name','upload_type')
    g_payment = GrowerPayments.objects.filter(grower_id=g_id)
    entry = EntryFeeds.objects.filter(grower_id=g_id)
    for i in get_farms :
        data['farms']+=[{'name':i['name'],'state':i['state'],'county':i['county'],'village':i['village'],'town':i['town'],'street':i['street'],'zipcode':i['zipcode']}]
    for i in get_fields :
        data['fields']+=[{'name':i['name'],'farm__name':i['farm__name'],'crop':i['crop'],'acreage':i['acreage']}]
    for i in get_storages :
        ShapeFileDataCo.objects.filter()
        data['storages']+=[{'storage_name':i['storage_name'],'upload_type':i['upload_type']}]

    lst_delivery_lbs =[]
    for i in g_payment :
        if i.delivery_lbs :
            lst_delivery_lbs.append(float(i.delivery_lbs))
    sum_delivery_lbs = f'{sum(lst_delivery_lbs)} LBS'
    sum_delivered_value = f'$ {sum([int(float(i.payment_amount)) for i in g_payment])}'
    data['payment_summary']+=[[{'total_delivered_lBS':sum_delivery_lbs,'total_number_of_deliveries':g_payment.count(),'total_delivered_value':sum_delivered_value}]]
    for i in entry :
        data['payment_summary']+=[[{'entry_feeds':i.contracted_payment_option,'from_date':i.from_date,'to_date':i.to_date}]]

    response = Response({'data':[data]})
    # except:
    #     pass
    return response



def grower_Field_Shipment_Chart(f_id):
    field = Field.objects.get(id=f_id)
    name = field.name
    
    if field.crop == 'COTTON' :
        shipment = BaleReportFarmField.objects.filter(ob4=f_id).order_by('-id')
        res = []
        for i in shipment :
            if i.level == 'None' :
                payment_status = 'N/A ( None )'
                payment_amount = 'N/A'
            else :
                if GrowerPayments.objects.filter(delivery_id=i.bale_id).exists():
                    payment_status = 'Paid'
                    payment_amount = f'$ {[i.payment_amount for i in GrowerPayments.objects.filter(delivery_id=i.bale_id)][0]}' 
                else:
                    payment_status = 'Due'
                    payment_amount = 'Due'

            str_date = str(i.dt_class)
            finale_date = ''
            if '-' in str_date : 
                try :
                    var_str_date = str_date.split('-')
                    mm = var_str_date[0]
                    dd = var_str_date[1]
                    yy = var_str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = date(int(yyyy), int(mm), int(dd))
                    
                except :
                    continue
            elif '/' in str_date :
                try :
                    var_str_date = str_date.split('/')
                    mm = var_str_date[0]
                    dd = var_str_date[1]
                    yy = var_str_date[2]
                    yyyy = f'20{yy}' if len(yy) == 2 else yy
                    finale_date = date(int(yyyy), int(mm), int(dd))
                    
                except :
                    continue
                        
            res.append({'name':name,'shipment_wt':i.net_wt,'shipment_dt':str_date,
                        'payment_status':payment_status,'payment_amount':payment_amount,
                        'level':i.level,'shipment_id':i.bale_id,'finale_date':finale_date,
                        "yyyy":yyyy,"mm":mm,"dd":dd})
        return res
    
    else:        
        shipment = GrowerShipment.objects.filter(field_id=f_id)
        res = []
        for i in shipment :
            finale_date = i.date_time
            if GrowerPayments.objects.filter(delivery_id=i.shipment_id).exists():
                payment_status = 'Paid'
                payment_amount = f'$ {[i.payment_amount for i in GrowerPayments.objects.filter(delivery_id=i.shipment_id)][0]}'
            elif i.status == "DISAPPROVED" :
                payment_status = 'N/A ( DISAPPROVED )'
                payment_amount = 'N/A'
            else:
                payment_status = 'Due'
                payment_amount = 'Due'

            if i.status == "APPROVED" :
                shipment_wt = i.received_amount
            else :
                shipment_wt = i.total_amount

            res.append({'name':name,'shipment_wt':shipment_wt,'shipment_dt':i.approval_date,
                        'payment_status':payment_status,'payment_amount':payment_amount,
                        'stats':i.status,'shipment_id':i.shipment_id,"finale_date":finale_date})
        return res
    


def grower_Field_Shipment_Details(f_id) :
    field = Field.objects.get(id=f_id)
    name = field.name
    projected_yield = field.total_yield
    # 29-05-23 Grower Splict payeee
    g_payee = GrowerPayee.objects.filter(field_id=f_id)
    g_payee_count = g_payee.count()
    lien_holder_count = g_payee.filter(lien_holder_status='YES').count()
    payment_split_count = g_payee.filter(payment_split_status='YES').count()
    # shipment_delivered_count
    
    if field.crop == 'COTTON' :
        shipment = BaleReportFarmField.objects.filter(ob4=f_id)
        shipment_wt = [float(i.net_wt) for i in shipment]
        lls = shipment.filter(level='Llano Super').count()
        gold = shipment.filter(level='Gold').count()
        silver = shipment.filter(level='Silver').count()
        bronze = shipment.filter(level='Bronze').count()
        nonee = shipment.filter(level='None').count()

        delivered_shipment = shipment.exclude(level='None')
        shipment_delivered_count = delivered_shipment.count()

        shipment_delivered_wt = [float(i.net_wt) for i in delivered_shipment]

        per_lls = round((lls / shipment_delivered_count), 4) * 100 if lls !=0 else 0
        per_gold = round((gold / shipment_delivered_count), 4) * 100 if gold !=0 else 0
        per_silver = round((silver / shipment_delivered_count), 4) * 100 if silver !=0 else 0
        per_bronze = round((bronze / shipment_delivered_count), 4) * 100 if bronze !=0 else 0

        per_nonee = round((nonee / shipment.count()), 4) * 100 if nonee !=0 else 0
        per_delivered = 100 - per_nonee

        if projected_yield :
            actual_yield = sum(shipment_delivered_wt)
            yield_delta =  float(actual_yield) - float(projected_yield)

        else:
            projected_yield = None
            actual_yield = sum(shipment_wt)
            yield_delta = 'N/A'

        chartShipmentDeliverdText = "Shipments Info - Delivered Level vs None Level"
        shipmentLevelText = "Shipments Info - Delivered Level"

        res = {"name":name,"crop":"COTTON","shipment_count":shipment.count(),"shipment_wt": f"{sum(shipment_wt)} LBS",
               "lls":lls,"gold":gold,"silver":silver,"bronze":bronze,"nonee":nonee,"shipment_delivered_count":shipment_delivered_count,
               "shipment_delivered_wt":f"{sum(shipment_delivered_wt)} LBS","per_lls":per_lls,"per_gold":per_gold,"per_silver":per_silver,
               "per_bronze":per_bronze,"shipmentLevelText":shipmentLevelText,"chartShipmentDeliverdText":chartShipmentDeliverdText,
               "per_nonee":per_nonee,"per_delivered":per_delivered,"projected_yield":projected_yield,"actual_yield":actual_yield,
               "yield_delta":yield_delta,"g_payee_count":g_payee_count,"lien_holder_count":lien_holder_count,"payment_split_count":payment_split_count}
               
        return res
    
    else:        
        shipment = GrowerShipment.objects.filter(field_id=f_id)
        approved_shipment = shipment.filter(status='APPROVED')
        disapproved_shipment = shipment.filter(status='DISAPPROVED')
        noStatus__shipment = shipment.filter(status='')

        count_shipment = shipment.count()
        count_approved_shipment = approved_shipment.count()
        count_disapproved_shipment = disapproved_shipment.count()
        count_noStatus__shipment = noStatus__shipment.count()

        per_approved_shipment = round((count_approved_shipment / count_shipment), 4) * 100 if count_approved_shipment !=0 else 0
        per_disapproved_shipment = round((count_disapproved_shipment / count_shipment), 4) * 100 if count_disapproved_shipment !=0 else 0
        per_noStatus__shipment = round((count_noStatus__shipment / count_shipment), 4) * 100 if count_noStatus__shipment !=0 else 0

        shipment_wt = []
        for i in shipment :
            if i.total_amount :
                shipment_wt.append(int(float(i.total_amount)))

        if projected_yield :
            actual_yield = sum(shipment_wt)
            yield_delta =  float(actual_yield) - float(projected_yield)

        else:
            projected_yield = None
            actual_yield = sum(shipment_wt)
            yield_delta = 'N/A'

        shipment_delivered_wt = [int(float(i.received_amount)) for i in approved_shipment]

        g_payment = GrowerPayments.objects.filter(field_name=name)

        shipment_paid_amount = f'$ {sum([int(float(i.payment_amount)) for i in g_payment])}'

        shipmentLevelText = "Shipments Info - Status (APPROVED vs DISAPPROVED vs PENDING)"
        res = {"name":name,"crop":field.crop,"shipmentLevelText":shipmentLevelText,"per_approved_shipment":per_approved_shipment,
               "per_disapproved_shipment":per_disapproved_shipment,"per_noStatus__shipment":per_noStatus__shipment,
               "shipment_wt": f'{sum(shipment_wt)} LBS',"shipment_count":count_shipment,"shipment_approved":count_approved_shipment,
               "shipment_disapproved":count_disapproved_shipment,"shipment_pending":count_noStatus__shipment,
               "shipment_delivered_wt":f'{sum(shipment_delivered_wt)} LBS',"shipment_paid_amount":shipment_paid_amount,
               "projected_yield":projected_yield,"actual_yield":actual_yield,"yield_delta":yield_delta,"g_payee_count":g_payee_count,
               "lien_holder_count":lien_holder_count,"payment_split_count":payment_split_count,"shipment_delivered_count":count_approved_shipment}
        return res
    
    
def grower_Field_Vegetation_Chart(f_id):
    field = Field.objects.get(id=f_id)
    
    name = field.name
    gal_water_saved  = str(field.gal_water_saved).strip().replace(',','') if field.gal_water_saved and field.gal_water_saved != 'nan' and field.gal_water_saved != 'None' else 0
    water_lbs_saved = str(field.water_lbs_saved).strip().replace(',','') if field.water_lbs_saved and field.water_lbs_saved != 'nan' and field.water_lbs_saved != 'None' else 0
    co2_eq_reduced = str(field.co2_eq_reduced).strip().replace(',','') if field.co2_eq_reduced and field.co2_eq_reduced != 'nan' and field.co2_eq_reduced != 'None' else 0
    increase_nitrogen = str(field.increase_nitrogen).strip().replace(',','') if field.increase_nitrogen and field.increase_nitrogen != 'nan' and field.increase_nitrogen != 'None' else 0
    ghg_reduction = str(field.ghg_reduction).strip().replace(',','') if field.ghg_reduction and field.ghg_reduction != 'nan' and field.ghg_reduction != 'None' else 0
    land_use_efficiency = str(field.land_use_efficiency).strip().replace(',','') if field.land_use_efficiency and field.land_use_efficiency != 'nan' and field.land_use_efficiency != 'None' else 0
    grower_premium_percentage = str(field.grower_premium_percentage).strip().replace(',','') if field.grower_premium_percentage and field.grower_premium_percentage != 'nan' and field.grower_premium_percentage != 'None' else 0
    grower_dollar_premium = str(field.grower_dollar_premium).strip().replace(',','') if field.grower_dollar_premium and field.grower_dollar_premium != 'nan' and field.grower_dollar_premium != 'None' else 0
    return [{'name':name,'gal_water_saved':gal_water_saved,'water_lbs_saved':water_lbs_saved,'co2_eq_reduced':co2_eq_reduced,
             'increase_nitrogen':increase_nitrogen,'ghg_reduction':ghg_reduction,'land_use_efficiency':land_use_efficiency,
             'grower_premium_percentage':grower_premium_percentage,'grower_dollar_premium':grower_dollar_premium}]



# 31-07-23
def get_current_time(latitude, longitude):
    obj = TimezoneFinder()
    get_timezone = obj.timezone_at(lng=longitude, lat=latitude)
    # Get the current time in the specified timezone
    current_time = datetime.now(timezone(get_timezone))
    return current_time

def get_climate_report_current(latitude, longitude):
    send_data = []
    api_key = "869bf5c36bd136408ba382cd5fea0f1e"  # Replace with your OpenWeatherMap API key
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    # Create the API request URL
    url = f"{base_url}?lat={latitude}&lon={longitude}&appid={api_key}"
    # Send the GET request to the API
    response = requests.get(url)
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        # Extract the relevant climate information
        temperature = float(data['main']['temp']) - 273.15
        humidity = data['main']['humidity']
        description = data['weather'][0]['description']
        wind = data['wind']['speed']
        send_data =  [{"f_temperature":round(temperature, 2),"f_humidity":humidity,"f_wind":wind,"f_description":description}]
    else:
        send_data =  [{"f_temperature":None,"f_humidity":None,"f_wind":None,"f_description":None}]
    
    return send_data

def get_climate_report_forecast(latitude, longitude):
    send_data = []
    base_url = f"https://api.weather.gov/points/{latitude},{longitude}"
    response = requests.get(base_url)
    if response.status_code == 200:
        data = response.json()
        forecast_url = data['properties']['forecast']
        send_data.append(forecast_url)
    return send_data
        # forecast_response = requests.get(forecast_url)
        # if forecast_response.status_code == 200:
        #     forecast_data = forecast_response.json()
        #     get_forecast_data = forecast_data["properties"]["periods"]
        #     for i in get_forecast_data :
        #         temperature = i["temperature"]
        #         startTime, shortForecast = i["startTime"], i["shortForecast"]
        #         relativeHumidity, windSpeed = i["relativeHumidity"]["value"], i["windSpeed"]
        #         # f_temperature =round(float(i["temperature"]), 2) 
        #         # c_temperature = round((5/9) * (f_temperature-32))
        #         if "Cloudy" in shortForecast :
        #             get_shortForecast="cloudy"
        #         elif "Sunny" or "Clear" in shortForecast :
        #             get_shortForecast="sunny"
        #         elif "Rainy" in shortForecast :
        #             get_shortForecast="rainy"
        #         else:
        #             get_shortForecast="sunny"
        #         send_data.append({"startTime":startTime,"temperature":temperature,"shortForecast":shortForecast,"get_shortForecast":get_shortForecast,"relativeHumidity":relativeHumidity,"windSpeed":windSpeed})
    # return send_data

def location_details(lat,lon):
    # geolocator = Nominatim(user_agent="MyApp")
    geolocator = Nominatim(user_agent="timezone_app")
    coordinates = f"{lat} , {lon}"
    location = geolocator.reverse(coordinates)
    address = location.raw['address']
    return address

def generate_image(climate_report):
    response = openai.Image.create(
    prompt=climate_report,
    n=1,
    size="1024x1024"
    )
    image_url = response['data'][0]['url']
    return image_url

@api_view(('POST',))
def grower_digital_crop_consultant_api(request):
    response = Response({'data':[]})
    userid = request.data['userid']
    field_id = request.data['field_id']
    data = {"crop_details":[],"current_time":"","climate_report_current":[],"climate_report_forecast":"","address_details":[],"climate_img":""}
    try:
        user = User.objects.get(id=userid)
        check_field = Field.objects.filter(id=field_id,grower_id=user.grower_id)
        shapfile = ShapeFileDataCo.objects.filter(field_id=field_id)
        if len(check_field) == 1 and shapfile.exists() :
            lat_lon = [i.coordinates for i in shapfile][0][0]
            lat = lat_lon[0]
            lon = lat_lon[1]
            crop = [i.crop for i in check_field][0]
            acreage = [i.acreage for i in check_field][0]
            variety = [i.variety for i in check_field][0]
            previous_crop = [i.previous_crop for i in check_field][0]
            fsa_farm_number = [i.fsa_farm_number for i in check_field][0]
            f_fsa_tract_number = [i.fsa_tract_number for i in check_field][0]
            f_fsa_field_number = [i.fsa_field_number for i in check_field][0]
            f_eschlon_id = [i.eschlon_id for i in check_field][0]
            crop_details = [{'crop':crop,'acreage':acreage,'variety':variety,'previous_crop':previous_crop,'fsa_farm_number':fsa_farm_number,
                            'f_fsa_tract_number':f_fsa_tract_number,'f_fsa_field_number':f_fsa_field_number,'f_eschlon_id':f_eschlon_id}]
            data['crop_details']+=crop_details
        elif len(check_field) == 1 :
            lat = [i.latitude for i in check_field][0]
            lon = [i.longitude for i in check_field][0]
            crop_details = [{'crop':crop,'acreage':acreage,'variety':variety,'previous_crop':previous_crop,'fsa_farm_number':fsa_farm_number,
                            'f_fsa_tract_number':f_fsa_tract_number,'f_fsa_field_number':f_fsa_field_number,'f_eschlon_id':f_eschlon_id}]
            data['crop_details']+=crop_details
        current_time = get_current_time(lat, lon)
        f_climate_current = get_climate_report_current(lat, lon)
        
        data['current_time']=current_time
        data['climate_report_current']=f_climate_current
        given_time = f"{current_time}"
        time_obj = datetime.strptime(given_time, "%Y-%m-%d %H:%M:%S.%f%z")
        time_in_am_pm = time_obj.strftime('%I:%M:%S %p')
        weather_description = f_climate_current[0]['f_description']
        climate_img = generate_image(f'Generate an image of {weather_description}, time is {time_in_am_pm}.')
        data['climate_img']=climate_img
        try:
            f_climate_forecast = get_climate_report_forecast(lat, lon)
        except:
            f_climate_forecast = []
        data['climate_report_forecast']=f_climate_forecast
        try:
            f_loc = location_details(lat,lon)
        except:
            pass
        try:
            f_county = f_loc['county']
        except:
            f_county = []
        try:
            f_state = f_loc['state']
        except:
            f_state = []
        try:
            f_country = f_loc['country']
        except:
            f_country = []
        try:
            f_postcode = f_loc['postcode']
        except:
            f_postcode = []
        address_details = {'f_county':f_county,'f_state':f_state,'f_country':f_country,'f_postcode':f_postcode}
        data['address_details']+=[address_details]
        response = Response({'data':data})
    
    except:
        pass
    return response


def chatGptApi(question):
    generated_text = ''
    response = openai.Completion.create(
    engine="text-davinci-003",
    prompt=question,
    temperature=0.5,
    max_tokens=200,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0.5
    )

    if response.choices:
        generated_text = response.choices[0].text
        # def stream_response():
        #     yield f'{generated_text}'
    return generated_text

@api_view(('POST',))
def grower_digital_crop_consultant_chat_api(request):
    response = Response({'data':[]})
    userid = request.data['userid']
    questionText = request.data['questionText']
    try:
        user = User.objects.get(id=userid)
    except:
        user = None
    if user != None and questionText and len(questionText) > 0 :
        ans = chatGptApi(questionText)
        response = Response({'data':[{'questionText':questionText,'ans':ans}]})
        user_name = f"{user.first_name} {user.last_name}"
        save_qus_ans = AssistantApp(user_id=userid,user_name=user_name,user_role='Grower',question=questionText,answer=ans)
        save_qus_ans.save()
    return response

@api_view(('POST',))
def grower_digital_crop_consultant_get_chat_api(request):
    response = Response({'data':[]})
    userid = request.data['userid']
    try:
        user = User.objects.get(id=userid)
    except:
        user = None
    if user != None :
        get_chat = AssistantApp.objects.filter(user_id=userid).order_by('-asking_datetime')[:10][::-1]
        chat_data = [{'question':[],'answer':[],'datetime':[]}]
        for i in get_chat :
            
            chat_data[0]['question'].append(i.question)
            chat_data[0]['answer'].append(i.answer)
            chat_data[0]['datetime'].append(i.asking_datetime)
        response = Response({'data':chat_data})
        
    return response

@api_view(('POST',))
def grower_profile_api(request):
    response = Response({'data':[]})
    userid = request.data['userid']
    try:
        user = User.objects.get(id=userid)
    except:
        user = None
    if user != None and user.grower.id :
        grower = Grower.objects.get(id=user.grower.id)
        consultant_all = grower.consultant.all()
        consultant = [i.name for i in consultant_all][0]

        data = [{'phone':grower.phone,'physical_address1':grower.physical_address1,'physical_address2':grower.physical_address2,
                'city1':grower.city1,'state1':grower.state1,'zip_code1':grower.zip_code1,'mailing_address1':grower.mailing_address1,
                'mailing_address2':grower.mailing_address2,'city2':grower.city2,'state2':grower.state2,'zip_code2':grower.zip_code2,
                'zip_code2':grower.zip_code2,'consultant':consultant,'full_physical_address':grower.physical_address(),
                'full_mailing_address':grower.mailing_address()}]
        response = Response({'data':data})
    return response


@api_view(('POST',))
def grower_storage_list_api(request):
    response = Response({'data':[]})
    userid = request.data['userid']
    try:
        user = User.objects.get(id=userid)
    except:
        user = None
    if user != None and user.grower.id :
        grower = Grower.objects.get(id=user.grower.id)
        storage = Storage.objects.filter(grower_id=grower.id).values('id','storage_name','storage_uniqueid','upload_type')
        data = [{"grower_name" : grower.name}]
        if storage.exists():
            storage_id = [i["id"] for i in storage]
            storage_name = [i["storage_name"] for i in storage]
            storage_uniqueid = [i["storage_uniqueid"] for i in storage]
            upload_type = [i["upload_type"] for i in storage]
            data.append({"get_storage":[{"storage_id":storage_id,"storage_name":storage_name,"storage_uniqueid":storage_uniqueid,"upload_type":upload_type}]})
        else :
            data.append({"get_storage":[]})
        response = Response({'data':data})
    return response


@api_view(('POST',))
def grower_storage_map_api(request):
    response = Response({'data':[]})
    userid = request.data['userid']
    storage_id = request.data['storage_id']
    try:
        user = User.objects.get(id=userid)
    except:
        user = None
    if user != None and user.grower.id :
        try:
            grower = Grower.objects.get(id=user.grower.id)
            storage = Storage.objects.filter(grower_id=grower.id,id=storage_id).values('id','latitude','longitude','upload_type')
            upload_type = [i["upload_type"] for i in storage]
            check_coordinates_data = StorageShapeFileDataCo.objects.filter(storage_id=storage_id)
            check_lat_data = [i["latitude"] for i in storage]
            check_long_data = [i["longitude"] for i in storage]
            if storage.exists() and check_coordinates_data.exists() and upload_type == ["shapefile"]:
                data = [i.coordinates for i in check_coordinates_data]
                get_cor_total = []
                for i in data[0]:
                    get_cor_total.append({ "latitude": i[0], "longitude": i[1] })
                
                response = Response({'status':'shapeFile','data':get_cor_total})
            elif storage.exists() and len(check_lat_data) > 0 and len(check_long_data) > 0 :
                response = Response({'status':'coordinates','data':[{ "latitude": check_lat_data[0], "longitude": check_long_data[0] }]})
            else:
                pass
        except:
            pass
    return response



@api_view(('POST',))
def grower_field_map_api(request):
    response = Response({'data':[]})
    userid = request.data['userid']
    field_id = request.data['field_id']
    try:
        user = User.objects.get(id=userid)
    except:
        user = None
    if user != None and user.grower.id :
        try:
            grower = Grower.objects.get(id=user.grower.id)
            check_field = Field.objects.filter(grower_id=grower.id,id=field_id).values('latitude','longitude')
            check_lat_data = [i["latitude"] for i in check_field]
            check_long_data = [i["longitude"] for i in check_field]
            shapfile = ShapeFileDataCo.objects.filter(field_id=field_id)
            if len(check_field) == 1 and shapfile.exists() :
                data = [i.coordinates for i in shapfile]
                get_cor_total = []
                for i in data[0]:
                    get_cor_total.append({ "latitude": i[0], "longitude": i[1] })
                response = Response({'status':'shapeFile','data':get_cor_total})
            elif len(check_field) == 1 and len(check_lat_data) > 0 and len(check_long_data) > 0 :
                response = Response({'status':'coordinates','data':[{ "latitude": check_lat_data[0], "longitude": check_long_data[0] }]})
        except:
            pass
    return response


@api_view(('POST',))
def processor_profile_api(request):
    response = Response({'data':[]})
    userid = request.data['userid']
    try:
        user = User.objects.get(id=userid)
        user_email = user.email
        processorUser = ProcessorUser.objects.get(contact_email=user_email)
        processor = Processor.objects.get(id=processorUser.processor_id)
        response = Response({'processor':[{'fein':processor.fein,'entity_name':processor.entity_name,
                                           'billing_address':processor.billing_address,'shipping_address':processor.shipping_address,
                                           'main_number':processor.main_number,'main_email': processor.main_email, 'main_fax':processor.main_fax,
                                           'website':processor.website}],
                             'processorUser':[{'contact_name':processorUser.contact_name,'contact_email':processorUser.contact_email,
                                               'contact_phone':processorUser.contact_phone,'contact_fax':processorUser.contact_fax}]})
    except:
        pass
    return response


@api_view(('POST',))
def tier2_processor_profile_api(request):
    response = Response({'data':[]})
    userid = request.data['userid']
    try:
        user = User.objects.get(id=userid)
        user_email = user.email
        processorUser2 = ProcessorUser2.objects.get(contact_email=user_email)
        processor2 = Processor2.objects.get(id=processorUser2.processor2_id)
        response = Response({'processor':[{'fein':processor2.fein,'entity_name':processor2.entity_name,
                                           'billing_address':processor2.billing_address,'shipping_address':processor2.shipping_address,
                                           'main_number':processor2.main_number,'main_email': processor2.main_email,'main_fax':processor2.main_fax,
                                           'website':processor2.website}],
                             'processorUser2':[{'contact_name':processorUser2.contact_name,'contact_email':processorUser2.contact_email,
                                               'contact_phone':processorUser2.contact_phone,'contact_fax':processorUser2.contact_fax}]})
    except:
        pass
    return response


@api_view(('POST',))
def application_update_api(request):
    try:
        data = {'app_version':"","android_link":"","ios_link":"","android_version":""}
        userid = request.data.get('userid')
        user = User.objects.filter(id=userid)
        if user.exists() :
            data["app_version"] = "1.9"
            data["android_link"] = "https://play.google.com/store/apps/details?id=com.farmsmart"
            data["ios_link"] = "https://apps.apple.com/us/app/farmsmart-app/id6444606959"
            data["android_version"] = "10"
    except Exception as e :
        data = {"error":f"{e}"}
    return Response(data)


#-----------------------------------------------------------------------------------------
def grower_payments_list_fun1(bale):
    grower_payment_bale = []
    total_deliverd_lbs = []
    total_deliverd_values = []
    payment_am = []
 
    for i in bale :
        delivery_date = i.dt_class
        delivery_id = i.bale_id
        grower_name = i.ob3
        crop = "COTTON"
        field = i.field_name
        delivery_lbs = i.net_wt
        classs = i.level
        
        payment_amount = ''
        payment_date = ''
        payment_type = ''
        payment_confirmation = ''
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
                var = EntryFeeds.objects.get(id = [i.id for i in check_entry_with_date][0])
            elif check_entry_with_no_date.exists() :
                var = EntryFeeds.objects.get(id = [i.id for i in check_entry_with_no_date][0])
    
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
                # specific_date = datetime(yyyy, mm, dd)
                # new_date = specific_date + timedelta(60)
                new_date = (datetime(yyyy, mm, dd)) + timedelta(60)
                payment_due_date = new_date.strftime("%m/%d/%y")
            else:
                payment_due_date ="N/A"
        else:
            total_price , delivered_value = 0.00
            payment_due_date ="N/A"
        gpay = GrowerPayments.objects.filter(delivery_id=delivery_id)
        if gpay.exists() :
            get_gpay = GrowerPayments.objects.get(delivery_id=delivery_id)
            payment_amount = get_gpay.payment_amount
            payment_date = get_gpay.payment_date
            payment_type = get_gpay.payment_type
            payment_confirmation = get_gpay.payment_confirmation
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
                'class':classs,
                'total_price':"{0:.5f}".format(total_price),
                'delivered_value':"{0:.4f}".format(delivered_value),
                'payment_due_date':payment_due_date,
                'payment_amount':payment_amount,
                'payment_date':payment_date,
                'payment_type':payment_type,
                'payment_confirmation':payment_confirmation,    
            }
        grower_payment_bale.append(data)
    total_deliverd_lbs = sum(total_deliverd_lbs)
    count = len(grower_payment_bale)
    total_deliverd_values = round(sum(total_deliverd_values),4)
    paid_amount = sum(payment_am)
    amount_open_for_payments = round(total_deliverd_values - paid_amount,4)

    summary_bale= {
        'Cropyear': '2022-2023',
        'TotalDeliveredLBS':total_deliverd_lbs,
        'TotalNumberofDeliveries':count,
        'TotalDeliveredValue':total_deliverd_values,
        'AmountPaid':paid_amount,
        'Amountopenforpayments':amount_open_for_payments,
    }    
    return summary_bale
#-------------------------------------------------------------------

def grower_payments_list_fun2(grower_shipment):
    grower_payment_shipment = []
    total_deliverd_lbs = []
    total_deliverd_values = []
    payment_am = []
   
    for i in grower_shipment :
        delivery_id = i.shipment_id
        grower_name = i.grower.name
        grower_id = i.grower.id
        crop = i.crop
        variety = i.variety
        field = i.field.name
        if i.approval_date == None:
            process_date_int  = i.process_date.strftime("%m/%d/%y")
            payment_due_date = (i.process_date + timedelta(60)).strftime("%m/%d/%y")

            check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i.process_date,to_date__gte=i.process_date)
            check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
            if check_entry_with_date.exists() :
                var = EntryFeeds.objects.get(id=[i.id for i in check_entry_with_date][0])
            elif check_entry_with_no_date.exists() :
                var = EntryFeeds.objects.get(id = [i.id for i in check_entry_with_no_date][0])
        else:

            process_date_int = i.approval_date.strftime("%m/%d/%y")
            payment_due_date = (i.approval_date + timedelta(60)).strftime("%m/%d/%y")
            check_entry_with_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__lte=i.approval_date,to_date__gte=i.approval_date)
            check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = grower_id,from_date__isnull=True,to_date__isnull=True)
            if check_entry_with_date.exists() :
                var = EntryFeeds.objects.get(id=[i.id for i in check_entry_with_date][0])  
            elif check_entry_with_no_date.exists() :
                var = EntryFeeds.objects.get(id = [i.id for i in check_entry_with_no_date][0])

        if var.contracted_payment_option == 'Fixed Price' :
            cpb_lbs = var.contract_base_price
            sp_lbs = var.sustainability_premium
            total_price =  float(cpb_lbs) + float(sp_lbs)
        elif var.contracted_payment_option == 'Acreage Release' :
            cpb_lbs = var.contract_base_price
            sp_lbs = var.sustainability_premium
            total_price = float(cpb_lbs) + float(sp_lbs)
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
        gpay = GrowerPayments.objects.filter(delivery_id=delivery_id)#
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
            
        total_deliverd_lbs.append(int(float(delivery_lbs)))
        total_deliverd_values.append(float(delivered_value))
        total_price = "{0:.5f}".format(total_price)
        delivered_value = "{0:.4f}".format(delivered_value)
        
        data ={
            'delivery_date':process_date_int,
            'delivery_id':delivery_id,
            'grower_name':grower_name,
            'crop':crop,
            'variety':variety,
            'field':field,
            'delivery_lbs':delivery_lbs,
            'class':'-',
            'total_price':total_price,
            'delivered_value':delivered_value,
            'payment_due_date':payment_due_date,
            'payment_amount':payment_amount,
            'payment_date':payment_date,
            'payment_type':payment_type,
            'payment_confirmation':payment_confirmation,  
        }
        grower_payment_shipment.append(data)
    total_deliverd_lbs = sum(total_deliverd_lbs)
    count = len(grower_payment_shipment)
    total_deliverd_values = round(sum(total_deliverd_values),4)
    paid_amount = sum(payment_am)
    amount_open_for_payments = round(total_deliverd_values - paid_amount, 4)
    summary_shipment= {
        'Cropyear': '2022-2023',
        'TotalDeliveredLBS':total_deliverd_lbs,
        'TotalNumberofDeliveries':count,
        'TotalDeliveredValue':total_deliverd_values,
        'AmountPaid':paid_amount,
        'Amountopenforpayments':amount_open_for_payments,
    }
    return summary_shipment
#-------------------------------------------------------------------


# @api_view(['POST',])
# def growerpaymentdetails_api(request):
#     response = {"status": "", "message": "","count":"","current_link":"","previous_link":"","next_link":"","start_index":"","end_index":"", "summary": [], "data": []}
#     userid = request.data.get('userid')
#     get_page_no = request.query_params.get('page')

#     try:
#         user = User.objects.get(id=userid)
#         grower_id = user.grower_id
#         print(user.username)
#         if grower_id is not None:
#             if EntryFeeds.objects.filter(grower_id=grower_id).count() > 0:
#                 bale = BaleReportFarmField.objects.filter(ob2=grower_id).exclude(level='None')
#                 grower_shipment = GrowerShipment.objects.filter(grower_id=grower_id ,status='APPROVED')
#                 total_obj_query = len(bale) + len(grower_shipment)
#                 print(total_obj_query)
#                 total_no_page = (total_obj_query // 100)+ 1

#                 if get_page_no is not None:
#                     if bale:
#                         get_page_no = int(get_page_no)
#                         paginator = PageNumberPagination()
#                         paginator.page_size = 100  # per page 100
#                         result_page = paginator.paginate_queryset(bale, request)
#                         serializer = BaleReportFarmFieldSerializer(result_page, many=True)
#                         summary_bale = grower_payments_list_fun1(bale)  
#                         response['summary']= summary_bale
#                     else: 
#                         get_page_no = int(get_page_no)
#                         paginator = PageNumberPagination()
#                         paginator.page_size = 100  # per page 100
#                         result_page = paginator.paginate_queryset(grower_shipment, request)
#                         serializer = GrowerShipmentSerializer(result_page, many=True)
#                         summary_shipment  = grower_payments_list_fun2(grower_shipment)
#                         response['summary']= summary_shipment

#                     start_index = (get_page_no - 1) * 100
#                     end_index = start_index + len(result_page)

#                     response["status"], response["message"] = 1, "Grower exists and showing all data"
#                     response['count'] = total_obj_query
#                     response['data'] = serializer.data
#                     response['start_index'] = start_index + 1
#                     response['end_index'] = end_index
#                     response['current_link'] = reverse('growerpaymentdetails_api') + f"?page={get_page_no}"
#                     response['previous_link'] = reverse('growerpaymentdetails_api') + f"?page={get_page_no - 1}" if get_page_no > 1 else None
#                     response['next_link'] = reverse('growerpaymentdetails_api') + f"?page={get_page_no + 1}" if get_page_no < total_no_page else None
#                     return Response(response)
#             else:
#                 response["status"], response["message"] = 0, "query does not exist"
#                 return Response(response)
#         else:
#             response["status"], response["message"] = 0, "Grower does not exist"
#             return Response(response)
#     except Exception as e:
#         response["status"], response["message"] = "500", f"500, {e}"
#         return Response(response)


@api_view(['POST'])
def growerpaymentdetails_api(request):
    response = {
        "status": "",
        "message": "",
        "count": "",
        "current_link": "",
        "previous_link": "",
        "next_link": "",
        "start_index": "",
        "end_index": "",
        "summary": [],
        "data": []
    }

    userid = request.data.get('userid')
    get_page_no = request.query_params.get('page', 1)  # Default to page 1

    try:
        user = User.objects.get(id=userid)
        grower_id = user.grower_id
        print(user.username)

        if grower_id:
            if EntryFeeds.objects.filter(grower_id=grower_id).exists():
                bale = BaleReportFarmField.objects.filter(ob2=grower_id).exclude(level='None')
                grower_shipment = GrowerShipment.objects.filter(grower_id=grower_id, status='APPROVED')

                total_obj_query = len(bale) + len(grower_shipment)
                print(total_obj_query)

                if total_obj_query > 0:
                    total_no_page = (total_obj_query // 100) + (1 if total_obj_query % 100 != 0 else 0)
                    get_page_no = int(get_page_no)

                    paginator = PageNumberPagination()
                    paginator.page_size = 100  # Items per page

                    if bale:
                        result_page = paginator.paginate_queryset(bale, request)
                        serializer = BaleReportFarmFieldSerializer(result_page, many=True)
                        summary_bale = grower_payments_list_fun1(bale)
                        response['summary'] = summary_bale
                    else:
                        result_page = paginator.paginate_queryset(grower_shipment, request)
                        serializer = GrowerShipmentSerializer(result_page, many=True)
                        summary_shipment = grower_payments_list_fun2(grower_shipment)
                        response['summary'] = summary_shipment

                    start_index = (get_page_no - 1) * paginator.page_size
                    end_index = start_index + len(result_page)

                    response.update({
                        "status": 1,
                        "message": "Grower exists and showing all data",
                        "count": total_obj_query,
                        "data": serializer.data,
                        "start_index": start_index + 1,
                        "end_index": end_index,
                        "current_link": reverse('growerpaymentdetails_api') + f"?page={get_page_no}",
                        "previous_link": (
                            reverse('growerpaymentdetails_api') + f"?page={get_page_no - 1}"
                            if get_page_no > 1 else None
                        ),
                        "next_link": (
                            reverse('growerpaymentdetails_api') + f"?page={get_page_no + 1}"
                            if get_page_no < total_no_page else None
                        )
                    })
                    return Response(response)
                else:
                    response["status"], response["message"] = 0, "No data available for the grower."
                    return Response(response)
            else:
                response["status"], response["message"] = 0, "Query does not exist."
                return Response(response)
        else:
            response["status"], response["message"] = 0, "Grower does not exist."
            return Response(response)
    except ObjectDoesNotExist:
        response["status"], response["message"] = 0, "User does not exist."
        return Response(response)
    except Exception as e:
        response["status"], response["message"] = "500", f"Internal server error: {e}"
        return Response(response)
    

#---------------------------------------------------------------------------------
@api_view(['POST',])
def growerbale_list_api(request):

    response = {"status": "", "message": "","count":"","data": []}
    userid = request.data.get('userid')
    try:
        user = User.objects.get(id=userid)
        grower_id= user.grower_id
        if grower_id is not None:
            if EntryFeeds.objects.filter(grower_id=grower_id).count() > 0:
                
                bale = BaleReportFarmField.objects.filter(ob2=grower_id).exclude(level='None').values('bale_id')
                grower_shipment = GrowerShipment.objects.filter(grower_id=grower_id  ,status='APPROVED').values('shipment_id')
                if bale.exists():
                    count = len(bale)
                    grower_bale_id=[i['bale_id'] for i in bale]
                    response["count"] = count
                    response["data"] = grower_bale_id
                    response["status"], response["message"] = 1, "bale_id exist and show all data"
                else:
                    count = len(grower_shipment)
                    grower_shipment_id=[i['shipment_id'] for i in grower_shipment]
                    response["count"] = count
                    response["data"] = grower_shipment_id
                    response["status"], response["message"] = 1, "shipment_id exist and show all data"
            else:
                response["status"], response["message"] = 0, "query does not exist" 
        else:
            response["status"], response["message"] = 0, "Grower does not exist"
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)

#---------------------------------------------------------------------------------
@api_view(['POST',])
def growerbale_details_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.data.get('userid')
    delivery_id = request.data.get('delivery_id')
    try:
        user = User.objects.get(id=userid)
        grower_id = user.grower_id
        
        if grower_id is not None:
            if EntryFeeds.objects.filter(grower_id=grower_id).count() > 0:
                bale = BaleReportFarmField.objects.filter(ob2=grower_id, bale_id=delivery_id).exclude(level='None')
                grower_shipment = GrowerShipment.objects.filter(grower_id=grower_id ,shipment_id=delivery_id ,status='APPROVED')
                if bale.exists():
                    paginator = PageNumberPagination()
                    result_page = paginator.paginate_queryset(bale, request)
                    serializer = BaleReportFarmFieldSerializer(result_page, many=True)
                    response["status"], response["message"] = 1, "grower & bale_id exist and show all data"
                    response['data'] = serializer.data
                else:
                    response["status"], response["message"] = 0, "query does not exist"
                      
                if grower_shipment.exists():
                    paginator = PageNumberPagination()
                    result_page = paginator.paginate_queryset(grower_shipment, request)
                    serializer = GrowerShipmentSerializer(result_page, many=True)
                    response["status"], response["message"] = 1, "grower & shipment_id exist and show all data"
                    response['data'] = serializer.data  
                else:
                    response["status"], response["message"] = 0, "query does not exist"         
            else:
                response["status"], response["message"] = 0, "query does not exist"         
        else:
            response["status"], response["message"] = 0, "grower not exist"
              
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)

    

@api_view(["GET",])
def processor_outbound_shipment_list_api(request):
    data = {"status":"","message":"","previous":None,"next":None,"data":[]}
    userid = request.GET.get("userid")
    try:
        user = User.objects.get(id=userid)
        if user.is_processor:
            processor = ProcessorUser.objects.filter(contact_email=user.email).first()
            processor_id = Processor.objects.get(id=processor.processor_id).id
            shipments = ShipmentManagement.objects.filter(processor_idd=processor_id)
            serializer = ShipmentManagementSerializer(shipments, many=True)
            result = serializer.data
            paginator = PageNumberPagination()
            paginator.page_size = 10  # Set the page size to 20
            result_data = paginator.paginate_queryset(result, request)
            paginated_response = paginator.get_paginated_response(result_data)
            data["status"] = "200"
            data["count"] = paginated_response.data["count"]
            data["previous"] = paginated_response.data["previous"]
            data["next"] = paginated_response.data["next"]
            data["data"] = paginated_response.data["results"]

        elif user.is_processor2:
            processor = ProcessorUser2.objects.filter(contact_email=user.email).first()
            processor_id = Processor2.objects.get(id=processor.processor2_id).id
            shipments = ShipmentManagement.objects.filter(processor_idd=processor_id)
            serializer = ShipmentManagementSerializer(shipments, many=True)
            result = serializer.data
            paginator = PageNumberPagination()
            paginator.page_size = 10  # Set the page size to 20
            result_data = paginator.paginate_queryset(result, request)
            paginated_response = paginator.get_paginated_response(result_data)
            data["status"] = "200"
            data["count"] = paginated_response.data["count"]
            data["previous"] = paginated_response.data["previous"]
            data["next"] = paginated_response.data["next"]
            data["data"] = paginated_response.data["results"]
        else:
            data = []
        
    except Exception as e:
        data["status"], data["message"], data["data"] = "500", f"500, {e}", []
    return Response(data)


@api_view(["GET",])
def processor_outbound_shipment_list_search_api(request):
    data = {"status":"","message":"","previous":None,"next":None,"data":[]}
    userid = request.GET.get("userid")
    search_keyword = request.GET.get('search_keyword')
    try:
        user = User.objects.get(id=userid)
        if user.is_processor:
            processor = ProcessorUser.objects.filter(contact_email=user.email).first()
            processor_id = Processor.objects.get(id=processor.processor_id).id
            shipments = ShipmentManagement.objects.filter(processor_idd=processor_id)
            if search_keyword:
                shipment_list = shipments.filter(shipment_id__icontains=search_keyword)
            else:
                shipment_list = shipments
            serializer = ShipmentManagementSerializer(shipment_list, many=True)
            result = serializer.data
            paginator = PageNumberPagination()
            paginator.page_size = 10  # Set the page size to 20
            result_data = paginator.paginate_queryset(result, request)
            paginated_response = paginator.get_paginated_response(result_data)
            data["status"] = "200"
            data["count"] = paginated_response.data["count"]
            data["previous"] = paginated_response.data["previous"]
            data["next"] = paginated_response.data["next"]
            data["data"] = paginated_response.data["results"]

        elif user.is_processor2:
            processor = ProcessorUser2.objects.filter(contact_email=user.email).first()
            processor_id = Processor2.objects.get(id=processor.processor2_id).id
            shipments = ShipmentManagement.objects.filter(processor_idd=processor_id)
            if search_keyword:
                shipment_list = shipments.filter(shipment_id__icontains=search_keyword)
            else:
                shipment_list = shipments
            serializer = ShipmentManagementSerializer(shipment_list, many=True)
            result = serializer.data
            paginator = PageNumberPagination()
            paginator.page_size = 10  # Set the page size to 20
            result_data = paginator.paginate_queryset(result, request)
            paginated_response = paginator.get_paginated_response(result_data)
            data["status"] = "200"
            data["count"] = paginated_response.data["count"]
            data["previous"] = paginated_response.data["previous"]
            data["next"] = paginated_response.data["next"]
            data["data"] = paginated_response.data["results"]
        else:
            data = []        
        
    except Exception as e:
        data["status"], data["message"], data["data"] = "500", f"500, {e}", []
    return Response(data)


@api_view(["GET",])
def processor_outbound_shipment_view_api(request):
    response = {"status": "", "message": "", "data": []}
    shipment_id = request.GET.get('shipment_id') 
    try:
        shipment = ShipmentManagement.objects.filter(id=shipment_id).first()
        qr_code = qr_code_processor(shipment.id)        
        if shipment.recive_delivery_date:
            approval_date = shipment.recive_delivery_date
        else:
            approval_date = "N/A"
        if shipment.status == "APPROVED":
            receiver_sku_id = shipment.storage_bin_recive
            ticket_number = shipment.ticket_number
            received_weight = shipment.received_weight
        else:
            receiver_sku_id = "N/A"
            ticket_number = "N/A"
            received_weight = "N/A"
        if shipment.status == "DISAPPROVED":
            reason_for_disapproval = shipment.reason_for_disapproval
        else:
            reason_for_disapproval = "N/A"
        data = {
            "shipment_id":shipment.shipment_id,
            "sender_processor_id":shipment.processor2_idd,
            "sender_processor_name":shipment.processor_e_name,
            "sender_processor_type":shipment.sender_processor_type,
            "receiver_processor_id":shipment.processor2_idd,
            "receiver_processor_name":shipment.processor2_name,
            "receiver_processor_type":shipment.receiver_processor_type,
            "crop": shipment.crop,
            "variety":shipment.variety,
            "milled_volume":shipment.milled_volume,
            "volume_shipped":shipment.volume_shipped,
            "volume_left":shipment.volume_left,
            "weight_of_product":shipment.weight_of_product,
            "weight_of_product_unit":shipment.weight_of_product_unit,
            "expected_yield":shipment.excepted_yield,
            "expected_yield_unit":shipment.excepted_yield_unit,
            "moisture_percentage":shipment.moisture_percent,
            "equipment_type":shipment.equipment_type,
            "equipment_id":shipment.equipment_id,
            "purchase_order_number":shipment.purchase_order_number,
            "lot_number":shipment.lot_number,
            "date_pulled":shipment.date_pulled,
            "status":shipment.status,
            "sender_sku_id":shipment.storage_bin_send,
            "receiving_date":approval_date,
            "receiver_sku_id":receiver_sku_id,
            "received_weight":received_weight,
            "ticket_number":ticket_number,
            "reason_for_disapproval":reason_for_disapproval,
            "qr_code":qr_code,
        }
        response["status"] = "200"
        response["message"] = "Data fetched successfully"
        response["data"] = data
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(["GET"])
def add_outbound_shipment_processor_destination_api(request):
    response = {"status": "", "message": "", "data": {"processor2": [], "processor3": [], "processor4": []}}
    userid = request.GET.get("userid")
    
    try:
        user = User.objects.get(id=userid)
        
        if user.is_processor:
            p = ProcessorUser.objects.get(contact_email=user.email)
            processor2 = LinkProcessor1ToProcessor.objects.filter(
                processor1_id=p.processor.id, processor2__processor_type__type_name="T2"
            ).values("processor2__id", "processor2__entity_name")
            processor3 = LinkProcessor1ToProcessor.objects.filter(
                processor1_id=p.processor.id, processor2__processor_type__type_name="T3"
            ).values("processor2__id", "processor2__entity_name")
            processor4 = LinkProcessor1ToProcessor.objects.filter(
                processor1_id=p.processor.id, processor2__processor_type__type_name="T4"
            ).values("processor2__id", "processor2__entity_name")

            response['data']['processor2'] = list(processor2) if processor2 else []
            response['data']['processor3'] = list(processor3) if processor3 else []
            response['data']['processor4'] = list(processor4) if processor4 else []

        elif user.is_processor2:
            p = ProcessorUser2.objects.get(contact_email=user.email)
            processor_3 = LinkProcessorToProcessor.objects.filter(
                processor_id=p.processor2.id, linked_processor__processor_type__type_name="T3"
            ).values("linked_processor__id", "linked_processor__entity_name")
            processor3 = []
            for i in processor_3:
                data = {
                    "processor2__id":i["linked_processor__id"],
                    "processor2__entity_name": i["linked_processor__entity_name"]
                }
                processor3.append(data)
            processor_4 = LinkProcessorToProcessor.objects.filter(
                processor_id=p.processor2.id, linked_processor__processor_type__type_name="T4"
            ).values("linked_processor__id", "linked_processor__entity_name")
            processor4 = []
            for i in processor_4:
                data = {
                    "processor2__id":i["linked_processor__id"],
                    "processor2__entity_name": i["linked_processor__entity_name"]
                }
                processor3.append(data)
            response['data']['processor3'] = list(processor3) if processor3 else []
            response['data']['processor4'] = list(processor4) if processor4 else []

        else:
            response['message'] = "User is neither a processor nor processor2"

        response['status'] = "200"
        response['message'] = "Linked processors fetched successfully"

    except User.DoesNotExist:
        response["status"], response["message"] = "404", "User not found"
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"

    return Response(response)


@api_view(("GET",))
def processor_details_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.GET.get("userid")
    user = User.objects.get(id=userid)
    if user.is_processor:
        p = ProcessorUser.objects.get(contact_email=user.email)
        data = {
            "processor_entity_name":p.processor.entity_name,
            "processor_id":p.processor.id,
            "processor_type":"T1"
        }
        response["status"], response["message"], response["data"] = "200", f"Processor details fetched successfully.", data
    elif user.is_processor2:
        p = ProcessorUser2.objects.get(contact_email=user.email)
        data = {
            "processor_entity_name":p.processor2.entity_name,
            "processor_id":p.processor2.id,
            "processor_type":p.processor2.processor_type.all().first().type_name
        }
        response["status"], response["message"], response["data"] = "200", f"Processor details fetched successfully.", data
    else:
        data = []
        response["status"], response["message"], response["data"] = "400", f"Processor not found.", data
    return Response(response)


@api_view(["GET",])
def add_outbound_shipment_processor_squ_list_api(request):
    response = {"status": "", "message": "", "data": []}
    processor_id = request.GET.get("processor_id")
    processor_type = request.GET.get("processor_type")
    try:    
        
        data = get_sku_list(int(processor_id), processor_type)["data"]

        response["status"] = "200"
        response["message"] = "SKU Id list fetched successfully."
        response["data"] = data
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)       


@api_view(["GET",])
def add_outbound_shipment_processor_milled_volume(request):
    response = {"status": "", "message": "", "data": []}
    selected_crop = request.GET.get("selected_crop")
    processor_id = request.GET.get("processor_id")
    processor_type = request.GET.get("processor_type")
    sku_id = request.GET.get("sku_id")
    try:                 
        data = calculate_milled_volume(selected_crop, int(processor_id), processor_type, sku_id)
        response["status"] = "200"
        response["message"] = "Milled volume fetched successfully."
        response["data"] = data
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(["POST",])
def add_outbound_shipment_processor_api(request):
    response = {"status": "", "message": ""}
    userid = request.data.get("userid")
    processor2_id = request.data.get("processor2_id")
    selected_crop = request.data.get('selected_crop'),
    variety = request.data.get('variety') 
    sender_sku_id = request.data.get("sender_sku_id") 
    milled_volume = request.data.get("milled_volume")
    volume_shipped = request.data.get("volume_shipped")
    weight_product = request.data.get("weight_product")  
    weight_prod_unit_id = request.data.get("weight_prod_unit_id")
    exp_yield = request.data.get("exp_yield")
    exp_yield_unit_id = request.data.get("exp_yield_unit_id")
    purchase_number = request.data.get("purchase_number")
    lot_number = request.data.get("lot_number")
    equipment_type = request.data.get("equipment_type")
    equipment_id = request.data.get("equipment_id")
    moist_percentage = request.data.get("moist_percentage")
    files = request.FILES.getlist("files")
    try:
        user = User.objects.get(id=userid)
        if user.is_processor:
            p = ProcessorUser.objects.get(contact_email=user.email) 
            processor_id = p.processor.id
            processor_name = p.processor.entity_name
            sender_processor_type = "T1"
            processor2_name = Processor2.objects.filter(id=processor2_id).first().entity_name
            processor2_type = Processor2.objects.filter(id=processor2_id).first().processor_type.all().first().type_name
            try:
                milled_value = float(milled_volume)
            except ValueError as e:
                response["status"], response["message"] = "500", f"500, {e}"
            try:
                volume_shipped = float(volume_shipped)
            except ValueError as e:
                response["status"], response["message"] = "500", f"500, {e}"
            if milled_value < volume_shipped:
                response["status"], response["message"] = "500", f"Volume shipped cannot be greater than milled volume."
            if weight_prod_unit_id == "LBS" :
                cal_weight = round(float(weight_product),2)
            if weight_prod_unit_id == "BU" :
                cal_weight = round(float(weight_product) * 45,2)
            if exp_yield_unit_id == "LBS" :
                cal_exp_yield = round(float(exp_yield),2)
            if exp_yield_unit_id == "BU" :
                cal_exp_yield = round(float(exp_yield) * 45,2)
            volume_left = float(milled_value) - float(volume_shipped)
            shipment_id = generate_shipment_id()

            save_shipment_management = ShipmentManagement(shipment_id=shipment_id,processor_idd=processor_id,processor_e_name=processor_name, sender_processor_type=sender_processor_type, bin_location=processor_id,crop=selected_crop, variety=variety,
                            equipment_type=equipment_type,equipment_id=equipment_id,storage_bin_send=sender_sku_id,moisture_percent = moist_percentage,
                            weight_of_product_raw = weight_product,weight_of_product=cal_weight,weight_of_product_unit=weight_prod_unit_id, excepted_yield_raw =exp_yield,excepted_yield=cal_exp_yield,
                            excepted_yield_unit=exp_yield_unit_id,purchase_order_number=purchase_number,lot_number=lot_number,volume_shipped=volume_shipped,milled_volume=milled_volume,
                            volume_left=volume_left,editable_obj=True,processor2_idd=processor2_id,processor2_name=processor2_name, receiver_processor_type=processor2_type)
            save_shipment_management.save()
            create_sku_list(processor_id, sender_processor_type, sender_sku_id)
            for file in files:
                new_file = File.objects.create(file=file)
                save_shipment_management.files.add(new_file)
            save_shipment_management.save()

            log_type, log_status, log_device = "ShipmentManagement", "Added", "App"
            log_idd, log_name = save_shipment_management.id, save_shipment_management.bin_location
            log_details = f"processor = {save_shipment_management.processor_e_name} | processor_id = {save_shipment_management.processor_idd} | date_pulled = {save_shipment_management.date_pulled} | bin_location = {save_shipment_management.bin_location} | milled_volume = {save_shipment_management.milled_volume} | equipment_type = {save_shipment_management.equipment_type} | equipment_id = {save_shipment_management.equipment_id} | purchase_order_number = {save_shipment_management.purchase_order_number} | lot_number = {save_shipment_management.lot_number} | volume_shipped = {save_shipment_management.volume_shipped} | volume_left = {save_shipment_management.volume_left} | editable_obj = {save_shipment_management.editable_obj} "
            action_by_userid = user.id
            user = User.objects.get(pk=action_by_userid)
            user_role = user.role.all()
            action_by_username = f'{user.first_name} {user.last_name}'
            action_by_email = user.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                log_device=log_device)
            logtable.save()
            update_obj = ShipmentManagement.objects.filter(processor_idd=int(processor_id)).exclude(id=save_shipment_management.id).values('id','editable_obj')
            
            if update_obj.exists():
                for i in update_obj :
                    get_obj = ShipmentManagement.objects.get(id=i['id'])
                    get_obj.editable_obj = False
                    get_obj.save()
            else:
                pass
            response["status"] = "200"
            response["message"] = f"Outbound shipment created successfully."
        elif user.is_processor2:
            p = ProcessorUser2.objects.get(contact_email=user.email) 
            processor_id = p.processor2.id
            processor_name = p.processor2.entity_name
            sender_processor_type = Processor2.objects.filter(id=processor_id).first().processor_type.all().first().type_name
            processor2_name = Processor2.objects.filter(id=processor2_id).first().entity_name
            processor2_type = Processor2.objects.filter(id=processor2_id).first().processor_type.all().first().type_name
            try:
                milled_value = float(milled_volume)
            except ValueError as e:
                response["status"], response["message"] = "500", f"500, {e}"
            try:
                volume_shipped = float(volume_shipped)
            except ValueError as e:
                response["status"], response["message"] = "500", f"500, {e}"
            if milled_value < volume_shipped:
                response["status"], response["message"] = "500", f"Volume shipped cannot be greater than milled volume."
            if weight_prod_unit_id == "LBS" :
                cal_weight = round(float(weight_product),2)
            if weight_prod_unit_id == "BU" :
                cal_weight = round(float(weight_product) * 45,2)
            if exp_yield_unit_id == "LBS" :
                cal_exp_yield = round(float(exp_yield),2)
            if exp_yield_unit_id == "BU" :
                cal_exp_yield = round(float(exp_yield) * 45,2)
            volume_left = float(milled_value) - float(volume_shipped)
            shipment_id = generate_shipment_id()

            save_shipment_management = ShipmentManagement(shipment_id=shipment_id,processor_idd=processor_id,processor_e_name=processor_name, sender_processor_type=sender_processor_type, bin_location=processor_id,crop=selected_crop, variety=variety,
                            equipment_type=equipment_type,equipment_id=equipment_id,storage_bin_send=sender_sku_id,moisture_percent = moist_percentage,
                            weight_of_product_raw = weight_product,weight_of_product=cal_weight,weight_of_product_unit=weight_prod_unit_id, excepted_yield_raw =exp_yield,excepted_yield=cal_exp_yield,
                            excepted_yield_unit=exp_yield_unit_id,purchase_order_number=purchase_number,lot_number=lot_number,volume_shipped=volume_shipped,milled_volume=milled_volume,
                            volume_left=volume_left,editable_obj=True,processor2_idd=processor2_id,processor2_name=processor2_name, receiver_processor_type=processor2_type)
            save_shipment_management.save()
            create_sku_list(processor_id, sender_processor_type, sender_sku_id)
            for file in files:
                new_file = File.objects.create(file=file)
                save_shipment_management.files.add(new_file)
            save_shipment_management.save()

            log_type, log_status, log_device = "ShipmentManagement", "Added", "App"
            log_idd, log_name = save_shipment_management.id, save_shipment_management.bin_location
            log_details = f"processor = {save_shipment_management.processor_e_name} | processor_id = {save_shipment_management.processor_idd} | date_pulled = {save_shipment_management.date_pulled} | bin_location = {save_shipment_management.bin_location} | milled_volume = {save_shipment_management.milled_volume} | equipment_type = {save_shipment_management.equipment_type} | equipment_id = {save_shipment_management.equipment_id} | purchase_order_number = {save_shipment_management.purchase_order_number} | lot_number = {save_shipment_management.lot_number} | volume_shipped = {save_shipment_management.volume_shipped} | volume_left = {save_shipment_management.volume_left} | editable_obj = {save_shipment_management.editable_obj} "
            action_by_userid = user.id
            user = User.objects.get(pk=action_by_userid)
            user_role = user.role.all()
            action_by_username = f'{user.first_name} {user.last_name}'
            action_by_email = user.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                log_device=log_device)
            logtable.save()
            update_obj = ShipmentManagement.objects.filter(processor_idd=int(processor_id)).exclude(id=save_shipment_management.id).values('id','editable_obj')
            
            if update_obj.exists():
                for i in update_obj :
                    get_obj = ShipmentManagement.objects.get(id=i['id'])
                    get_obj.editable_obj = False
                    get_obj.save()
            else:
                pass
            response["status"] = "200"
            response["message"] = f"Outbound shipment created successfully."
        else:
            response["status"], response["message"] = "500", f"500, {e}"   
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(["GET",])
def processor_management_list_api(request):
    data = {"status":"","message":"","previous":None,"next":None,"data":[]}
    userid = request.GET.get("userid")
    try:
        user = User.objects.get(id=userid)
        if user.is_processor:
            pro = ProcessorUser.objects.filter(contact_email=user.email).first()
            entity_name = pro.processor
            processor = ProcessorUser.objects.filter(processor=entity_name)
            serializer = ProcessorUserSerializer(processor, many=True)
            result = serializer.data
            paginator = PageNumberPagination()
            paginator.page_size = 10  # Set the page size to 20
            result_data = paginator.paginate_queryset(result, request)
            paginated_response = paginator.get_paginated_response(result_data)
            data["status"] = "200"
            data["count"] = paginated_response.data["count"]
            data["previous"] = paginated_response.data["previous"]
            data["next"] = paginated_response.data["next"]
            data["data"] = paginated_response.data["results"]

        elif user.is_processor2:
            pro = ProcessorUser2.objects.filter(contact_email=user.email).first()
            entity_name = pro.processor2
            processor = ProcessorUser2.objects.filter(processor2=entity_name)
            serializer = ProcessorUser2Serializer(processor, many=True)
            result = serializer.data
            paginator = PageNumberPagination()
            paginator.page_size = 10  # Set the page size to 20
            result_data = paginator.paginate_queryset(result, request)
            paginated_response = paginator.get_paginated_response(result_data)
            data["status"] = "200"
            data["count"] = paginated_response.data["count"]
            data["previous"] = paginated_response.data["previous"]
            data["next"] = paginated_response.data["next"]
            data["data"] = paginated_response.data["results"]
        else:
            data = []
        
    except Exception as e:
        data["status"], data["message"], data["data"]= "500", f"500, {e}", []
    return Response(data)


@api_view(["GET",])
def processor_management_list_search_api(request):
    data = {"status":"","message":"","previous":None,"next":None,"data":[]}
    userid = request.GET.get("userid")
    search_keyword = request.GET.get('search_keyword')
    try:
        user = User.objects.get(id=userid)
        if user.is_processor:
            pro = ProcessorUser.objects.filter(contact_email=user.email).first()
            entity_name = pro.processor
            processor = ProcessorUser.objects.filter(processor=entity_name)
            if search_keyword:
                processor = processor.filter(Q(contact_name__icontains=search_keyword) | Q(processor__entity_name__icontains=search_keyword)| Q(processor__fein__icontains=search_keyword)| Q(contact_email__icontains=search_keyword))
            else:
                processor = processor
            serializer = ProcessorUserSerializer(processor, many=True)
            result = serializer.data
            paginator = PageNumberPagination()
            paginator.page_size = 10  # Set the page size to 20
            result_data = paginator.paginate_queryset(result, request)
            paginated_response = paginator.get_paginated_response(result_data)
            data["status"] = "200"
            data["count"] = paginated_response.data["count"]
            data["previous"] = paginated_response.data["previous"]
            data["next"] = paginated_response.data["next"]
            data["data"] = paginated_response.data["results"]

        elif user.is_processor2:
            pro = ProcessorUser2.objects.filter(contact_email=user.email).first()
            entity_name = pro.processor2
            processor = ProcessorUser2.objects.filter(processor2=entity_name)
            if search_keyword:
                processor = processor.filter(Q(contact_name__icontains=search_keyword) | Q(processor2__entity_name__icontains=search_keyword)| Q(processor2__fein__icontains=search_keyword)| Q(contact_email__icontains=search_keyword))
            else:
                processor = processor
            serializer = ProcessorUser2Serializer(processor, many=True)
            result = serializer.data
            paginator = PageNumberPagination()
            paginator.page_size = 10  # Set the page size to 20
            result_data = paginator.paginate_queryset(result, request)
            paginated_response = paginator.get_paginated_response(result_data)
            data["status"] = "200"
            data["count"] = paginated_response.data["count"]
            data["previous"] = paginated_response.data["previous"]
            data["next"] = paginated_response.data["next"]
            data["data"] = paginated_response.data["results"]
        else:
            data = []
    
    except Exception as e:
        data["status"], data["message"], data["data"] = "500", f"500, {e}", []
    return Response(data)


@api_view(["POST",])
def add_processor_user_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.data.get("userid")
    contact_name = request.data.get("contact_name")
    contact_email = request.data.get("contact_email")
    contact_phone = request.data.get("contact_phone")
    contact_fax = request.data.get("contact_fax")
    try:
        user = User.objects.get(id=userid)
        if user.is_processor:
            p = ProcessorUser.objects.filter(contact_email=user.email).first()
            processor_id = p.processor.id
            if User.objects.filter(email=contact_email).exists():
                response["status"], response["message"] = "400", f"User with this email already exists."

            password = generate_random_password()                            
            puser = ProcessorUser(processor_id = processor_id,contact_name=contact_name,contact_email=contact_email,contact_phone=contact_phone,contact_fax=contact_fax,p_password_raw=password)
            puser.save()
            user = User.objects.create(email=contact_email, username=contact_email,first_name=contact_name)
            user.role.add(Role.objects.get(role='Processor'))
            user.is_processor=True
            user.is_active=True
            user.set_password(password)
            user.password_raw = password
            user.save()

            # 07-04-23 Log Table
            log_type, log_status, log_device = "ProcessorUser", "Added", "App"
            log_idd, log_name = puser.id, contact_name
            log_email = contact_email
            log_details = f"processor_id = {processor_id} | processor = {p.processor.entity_name}  | contact_name= {contact_name} | contact_email = {contact_email} | contact_phone = {contact_phone} | contact_fax = {contact_fax}"
            
            action_by_userid = user.id
            userr = User.objects.get(pk=action_by_userid)
            user_role = userr.role.all()
            action_by_username = f'{userr.first_name} {userr.last_name}'
            action_by_email = userr.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                log_details=log_details,log_device=log_device)
            logtable.save()
            response["status"], response["message"] = "200", f"Processor User added successfully."
        elif user.is_processor2:
            p = ProcessorUser2.objects.filter(contact_email=user.email).first()
            processor_id = p.processor2.id
            if User.objects.filter(email=contact_email).exists():
                response["status"], response["message"] = "400", f"User with this email already exists."

            password = generate_random_password()                            
            puser = ProcessorUser2(processor2_id = processor_id,contact_name=contact_name,contact_email=contact_email,contact_phone=contact_phone,contact_fax=contact_fax,p_password_raw=password)
            puser.save()
            user = User.objects.create(email=contact_email, username=contact_email,first_name=contact_name)
            user.role.add(Role.objects.get(role='Processor'))
            user.is_processor2=True
            user.is_active=True
            user.set_password(password)
            user.password_raw = password
            user.save()

            # 07-04-23 Log Table
            log_type, log_status, log_device = "ProcessorUser", "Added", "App"
            log_idd, log_name = puser.id, contact_name
            log_email = contact_email
            log_details = f"processor_id = {processor_id} | processor = {p.processor2.entity_name}  | contact_name= {contact_name} | contact_email = {contact_email} | contact_phone = {contact_phone} | contact_fax = {contact_fax}"
            
            action_by_userid = user.id
            userr = User.objects.get(pk=action_by_userid)
            user_role = userr.role.all()
            action_by_username = f'{userr.first_name} {userr.last_name}'
            action_by_email = userr.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                log_details=log_details,log_device=log_device)
            logtable.save()
            response["status"], response["message"] = "200", f"Processor User added successfully."
        else:
            response["status"], response["message"] = "400", "Processor does not exists."
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(["POST",])
def processor_edit_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.data.get("userid")
    entity_name = request.data.get("entity_name")
    fein = request.data.get("fein")
    billing_add = request.data.get("billing_add")
    shipping_add = request.data.get("shipping_add")
    main_phn_number = request.data.get("main_phn_number")
    main_email = request.data.get('main_email')
    main_fax = request.data.get("main_fax")
    website = request.data.get("website")
    contact_email = request.data.get("contact_email")
    contact_name = request.data.get("contact_name")
    contact_phone = request.data.get("contact_phone")
    contact_fax = request.data.get("contact_fax")
    try:
        user = User.objects.get(id=userid)
        if user.is_processor:
            p = ProcessorUser.objects.filter(contact_email=user.email).first()
            p.contact_email = contact_email
            p.contact_name = contact_name
            p.contact_phone = contact_phone
            p.contact_fax = contact_fax
            p.processor.entity_name = entity_name
            p.processor.fein = fein
            p.processor.billing_address = billing_add
            p.processor.shipping_address = shipping_add
            p.processor.main_number = main_phn_number
            p.processor.main_email = main_email
            p.processor.main_fax = main_fax
            p.processor.website = website
            p.processor.save()
            p.save()
            if contact_email != user.email:
                f_name = contact_name
                user.email = contact_email
                user.username = contact_email
                user.first_name = f_name
                user.save()
            
            else :
                f_name = contact_name
                user.first_name = f_name
                user.save()
            log_type, log_status, log_device = "ProcessorUser", "Edited", "Web"
            log_idd, log_name, log_email = p.id, contact_name, contact_email
            log_details = f"processor_id = {p.processor.id} | processor = {p.processor.entity_name} | contact_name= {contact_name} | contact_email = {contact_email} | contact_phone = {contact_phone} | contact_fax = {contact_fax}"
            action_by_userid = user.id
            userr = User.objects.get(pk=action_by_userid)
            user_role = userr.role.all()
            action_by_username = f'{userr.first_name} {userr.last_name}'
            action_by_email = userr.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                log_details=log_details,log_device=log_device)
            logtable.save()
            response["status"], response["message"] = "200", f"Processor Updated successfully."
        elif user.is_processor2:
            p = ProcessorUser2.objects.filter(contact_email=user.email).first()
            p.contact_email = contact_email
            p.contact_name = contact_name
            p.contact_phone = contact_phone
            p.contact_fax = contact_fax
            p.processor2.entity_name = entity_name
            p.processor2.fein = fein
            p.processor2.billing_address = billing_add
            p.processor2.shipping_address = shipping_add
            p.processor2.main_number = main_phn_number
            p.processor2.main_email = main_email
            p.processor2.main_fax = main_fax
            p.processor2.website = website
            p.processor2.save()
            p.save()
            if contact_email != user.email:
                f_name = contact_name
                user.email = contact_email
                user.username = contact_email
                user.first_name = f_name
                user.save()
            
            else :
                f_name = contact_name
                user.first_name = f_name
                user.save()
            log_type, log_status, log_device = "ProcessorUser2", "Edited", "Web"
            log_idd, log_name, log_email = p.id, contact_name, contact_email
            log_details = f"processor_id = {p.processor2.id} | processor = {p.processor2.entity_name} | contact_name= {contact_name} | contact_email = {contact_email} | contact_phone = {contact_phone} | contact_fax = {contact_fax}"
            action_by_userid = user.id
            userr = User.objects.get(pk=action_by_userid)
            user_role = userr.role.all()
            action_by_username = f'{userr.first_name} {userr.last_name}'
            action_by_email = userr.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                log_details=log_details,log_device=log_device)
            logtable.save()
            response["status"], response["message"] = "200", f"Processor Updated successfully."
        else:
            response["status"], response["message"] = "400", "Processor does not exists."
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(('POST',))
def processor_password_change_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.data.get('userid')
    password = request.data.get('passowrd')
    confirm_password = request.data.get('confirm_password')
    user = User.objects.get(id=userid)
    if user.is_processor:
        p = ProcessorUser.objects.get(contact_email=user.email)
        if password == confirm_password:
            password = make_password(password)
            user.password = password
            user.password_raw = password
            user.save()
            p.p_password_raw = password
            p.save()
            log_type, log_status, log_device = "ProcessorUser", "Password changed", "Web"
            log_idd, log_name = p.id, p.contact_name
            log_email = p.contact_email
            log_details = f"processor_id = {p.processor.id} | processor = {p.processor.entity_name} | contact_name= {p.contact_name} | contact_email = {p.contact_email} | contact_phone = {p.contact_phone} | contact_fax = {p.contact_fax}"
            action_by_userid = user.id
            user = User.objects.get(pk=action_by_userid)
            user_role = user.role.all()
            action_by_username = f'{user.first_name} {user.last_name}'
            action_by_email = user.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                log_details=log_details, log_device=log_device)
            logtable.save()
            response["status"], response["message"] = "200", f"Processor Updated successfully."
        else:
            response["status"], response["message"] = "400", f"Password and confirm password does not match."
    elif user.is_processor2:
        p = ProcessorUser2.objects.get(contact_email=user.email)
        if password == confirm_password:
            password = make_password(password)
            user.password = password
            user.password_raw = password
            user.save()
            p.p_password_raw = password
            p.save()
            log_type, log_status, log_device = "ProcessorUser2", "Password changed", "Web"
            log_idd, log_name = p.id, p.contact_name
            log_email = p.contact_email
            log_details = f"processor_id = {p.processor2.id} | processor = {p.processor2.entity_name} | contact_name= {p.contact_name} | contact_email = {p.contact_email} | contact_phone = {p.contact_phone} | contact_fax = {p.contact_fax}"
            action_by_userid = user.id
            user = User.objects.get(pk=action_by_userid)
            user_role = user.role.all()
            action_by_username = f'{user.first_name} {user.last_name}'
            action_by_email = user.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                log_details=log_details, log_device=log_device)
            logtable.save()
            response["status"], response["message"] = "200", f"Processor Updated successfully."
        else:
            response["status"], response["message"] = "400", f"Password and confirm password does not match."
    else:
        response["status"], response["message"] = "400", f"Processor does not exist."
    return Response(response)


@api_view(('GET',))
def processor_location_list_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.GET.get('userid')
    user = User.objects.get(id=userid)
    if user.is_processor:
        p = ProcessorUser.objects.get(contact_email=user.email)
        processor_id = Processor.objects.get(id=p.processor_id).id
        location = Location.objects.filter(processor_id=processor_id)
        lst=[]
        for i in location:
            data = {
                "location_name":i.name,
                "location_id":i.id,
                "upload_type":i.upload_type,
                "latitude":i.latitude,
                "longitude":i.longitude,
                "shapefile":i.shapefile_id if i.shapefile_id else None
            }
            lst.append(data)
        response["status"], response["message"], response["data"] = "200","Location fetched successfully.", lst
    elif user.is_processor2:
        p = ProcessorUser2.objects.get(contact_email=user.email)
        processor_id = Processor2.objects.get(id=p.processor2_id).id
        location = Processor2Location.objects.filter(processor_id=processor_id)
        lst=[]
        for i in location:
            data = {
                "location_name":i.name,
                "location_id":i.id,
                "upload_type":i.upload_type,
                "latitude":i.latitude,
                "longitude":i.longitude,
                "shapefile":i.shapefile_id if i.shapefile_id else None
            }
            lst.append(data)
        response["status"], response["message"], response["data"] = "200","Location fetched successfully.", lst
    else:
        response["status"], response["message"], response["data"] = "400","Processor not found.", []
    return Response(response)


@api_view(('GET',))
def processor_location_view_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.GET.get('userid')
    location_id = request.GET.get('location_id')
    user = User.objects.get(id=userid)
    if user.is_processor:
        p = ProcessorUser.objects.get(contact_email=user.email)
        check_location = Location.objects.filter(processor_id=p.processor.id, id=location_id)
        if check_location:
            location = check_location.first()
            data = {
                "location_name":location.name,
                "location_id": location.id,
                "upload_type":location.upload_type,
                "latitude":location.latitude,
                "longitude":location.longitude,
                "shapefile":location.shapefile_id if location.shapefile_id else None
            }
            response["status"], response["message"], response["data"] = "200","Location fetched successfully.", data
        else:
            response["status"], response["message"], response["data"] = "400","Location not found.", []
    elif user.is_processor2:
        p = ProcessorUser2.objects.get(contact_email=user.email)
        check_location = Processor2Location.objects.filter(processor_id=p.processor2.id, id=location_id)
        if check_location:
            location = check_location.first()
            data = {
                "location_name":location.name,
                "location_id": location.id,
                "upload_type":location.upload_type,
                "latitude":location.latitude,
                "longitude":location.longitude,
                "shapefile":location.shapefile_id if location.shapefile_id else None
            }
            response["status"], response["message"], response["data"] = "200","Location fetched successfully.", data
        else:
            response["status"], response["message"], response["data"] = "400","Location not found.", []
    else:
        response["status"], response["message"], response["data"] = "400","Processor not found.", []
    return Response(response)


@api_view(("POST",))
def processor_location_add_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.data.get("userid")
    name = request.data.get("name")
    upload_type = request.data.get("upload_type")
    zip_file = request.FILES.get("zip_file")
    latitude = request.data.get("latitude")
    longitude = request.data.get("longitude")
    user = User.objects.get(id=userid)
    if user.is_processor:
        p = ProcessorUser.objects.get(contact_email=user.email)
        if upload_type == 'shapefile':
            if request.FILES.get('zip_file'):
                location = Location(processor= p.processor, name=name,upload_type=upload_type,shapefile_id=zip_file)
                location.save()
                sf = shapefile.Reader(location.shapefile_id.path)
                features = sf.shapeRecords()
                for feat in features:
                    eschlon_id = feat.record["id"]
                    location.eschlon_id = eschlon_id
                    location.save()
            else:
                response["status"], response["message"] = "400", "Zip file is necessary."
        else:
            location = Location(processor=p.processor, name=name,upload_type=upload_type,latitude=latitude,longitude=longitude)
            location.save()
        response["status"], response["message"] = "200", "Location added successfully."
    elif user.is_processor2:
        p = ProcessorUser2.objects.get(contact_email=user.email)
        if upload_type == 'shapefile':
            if request.FILES.get('zip_file'):
                location = Processor2Location(processor= p.processor2, name=name,upload_type=upload_type,shapefile_id=zip_file)
                location.save()
                sf = shapefile.Reader(location.shapefile_id.path)
                features = sf.shapeRecords()
                for feat in features:
                    eschlon_id = feat.record["id"]
                    location.eschlon_id = eschlon_id
                    location.save()
            else:
                response["status"], response["message"] = "400", "Zip file is necessary."
        else:
            location = Processor2Location(processor=p.processor2, name=name,upload_type=upload_type,latitude=latitude,longitude=longitude)
            location.save()
        response["status"], response["message"] = "200", "Location added successfully."
    else:
        response["status"], response["message"] = "400", "Processor not found.."
    return Response(response)


@api_view(('POST',))
def processor_location_edit_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.data.get("userid")
    location_id = request.data.get("location_id")
    name = request.data.get("name")
    upload_type = request.data.get("upload_type")
    zip_file = request.FILES.get("zip_file")
    latitude = request.data.get("latitude")
    longitude = request.data.get("longitude")
    try:
        user = User.objects.get(id=userid)
        if user.is_processor:
            check_location = Location.objects.filter(id=location_id)
            if check_location:
                location = check_location.first()
                if upload_type == 'shapefile':
                    if request.FILES.get('zip_file'):
                        location.name = name
                        location.upload_type = 'shapefile'
                        location.shapefile_id = zip_file
                        location.latitude = None
                        location.longitude = None
                        location.save()
                        
                        sf = shapefile.Reader(location.shapefile_id.path)
                        features = sf.shapeRecords()
                        for feat in features:
                            eschlon_id = feat.record["id"]
                            location.eschlon_id = eschlon_id
                            location.save()
                    else:
                        response["status"], response["message"] = "400", "Zip file is necessary."
                else:
                    location.name = name
                    location.upload_type = 'coordinates'
                    location.shapefile_id = None
                    location.eschlon_id = None
                    location.latitude = latitude
                    location.longitude = longitude
                    location.save()
                response["status"], response["message"] = "200", "Location updated successfully."
            else:
                response["status"], response["message"] = "400", "Location not found."
        elif user.is_processor2:
            check_location = Processor2Location.objects.filter(id=location_id)
            if check_location:
                location = check_location.first()
                if upload_type == 'shapefile':
                    if request.FILES.get('zip_file'):
                        location.name = name
                        location.upload_type = 'shapefile'
                        location.shapefile_id = zip_file
                        location.latitude = None
                        location.longitude = None
                        location.save()
                        
                        sf = shapefile.Reader(location.shapefile_id.path)
                        features = sf.shapeRecords()
                        for feat in features:
                            eschlon_id = feat.record["id"]
                            location.eschlon_id = eschlon_id
                            location.save()
                    else:
                        response["status"], response["message"] = "400", "Zip file is necessary."
                else:
                    location.name = name
                    location.upload_type = 'coordinates'
                    location.shapefile_id = None
                    location.eschlon_id = None
                    location.latitude = latitude
                    location.longitude = longitude
                    location.save()
                response["status"], response["message"] = "200", "Location updated successfully."
            else:
                response["status"], response["message"] = "400", "Location not found"
        
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)  


@api_view(("POST",))
def processor_location_delete_api(request):
    response = {"status": "", "message": "", "data": []}
    location_id = request.data.get("location_id")
    userid = request.data.get("userid")
    try:
        user = User.objects.get(id=userid)
        if user.is_processor:
            check_location = Location.objects.filter(id=location_id)
            if check_location:
                location = check_location.first()
                location.delete()
                response["status"], response["message"] = "200", "Location deleted successfully."
            else:
                response["status"], response["message"] = "400", "Location not found."
        elif user.is_processor2:
            check_location = Processor2Location.objects.filter(id=location_id)
            if check_location:
                location = check_location.first()
                location.delete()
                response["status"], response["message"] = "200", "Location deleted successfully."
            else:
                response["status"], response["message"] = "400", "Location not found."
        else:
            response["status"], response["message"] = "400", "Processor not found."
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response) 


@api_view(("GET",))
def processor_to_processor_management_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.GET.get("userid")
    try:
        user = User.objects.get(id=userid)
        if user.is_processor:
            p = ProcessorUser.objects.get(contact_email=user.email)
            linked_processors = LinkProcessor1ToProcessor.objects.filter(processor1_id=p.processor.id)
            data = []
            if linked_processors:
                for i in linked_processors:
                    lst = {
                        "processor_id":i.processor1.id,
                        "processor_entity_name":i.processor1.entity_name,
                        "linked_processor_id":i.processor2.id,
                        "linked_processor_entity_name":i.processor2.entity_name,
                        "linked_processor_type":i.processor2.processor_type.all().first().type_name
                    }
                    data.append(lst)
                response["status"], response["message"], response["data"] = "200", "Linked processors fetched successfully.", data
            else:
                response["status"], response["message"], response["data"] = "400", "Linked processor not found.",[]
        elif user.is_processor2:
            p = ProcessorUser2.objects.get(contact_email=user.email)
            linked_processor1 = LinkProcessor1ToProcessor.objects.filter(processor2_id=p.processor2.id)
            other_linked_pro = LinkProcessorToProcessor.objects.filter(Q(processor_id=p.processor2.id) | Q(linked_processor_id=p.processor2.id))
            data = []
            if linked_processor1:
                for i in linked_processor1:
                    lst = {
                        "processor_id":i.processor2.id,
                        "processor_entity_name":i.processor2.entity_name,
                        "linked_processor_id":i.processor1.id,
                        "linked_processor_entity_name":i.processor1.entity_name,
                        "linked_processor_type":"T1"
                    }
                    data.append(lst)
            if other_linked_pro:
                for i in other_linked_pro:
                    if i.processor.id == p.processor2.id:
                        lst = {
                            "processor_id":i.processor.id,
                            "processor_entity_name":i.processor.entity_name,
                            "linked_processor_id":i.linked_processor.id,
                            "linked_processor_entity_name":i.linked_processor.entity_name,
                            "linked_processor_type":i.linked_processor.processor_type.all().first().type_name
                        }
                        data.append(lst)
                    else:
                        lst = {
                            "processor_id":i.linked_processor.id,
                            "processor_entity_name":i.linked_processor.entity_name,
                            "linked_processor_id":i.processor.id,
                            "linked_processor_entity_name":i.processor.entity_name,
                            "linked_processor_type":i.processor.processor_type.all().first().type_name
                        }
                        data.append(lst)
            response["status"], response["message"], response["data"] = "200", "Linked processors fetched successfully.", data
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("POST",))
def processor_inbound_shipment_edit_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.data.get("userid")
    shipment_id = request.data.get("shipment_id")
    try:
        user = User.objects.get(id=userid)
        if user.is_processor:
            p = ProcessorUser.objects.get(contact_email=user.email)
            check_shipment = GrowerShipment.objects.filter(id=shipment_id)
            status= request.data.get('status')
            received_weight= request.data.get('received_weight')
            sku_id = request.data.get('sku_id')       
            ticket_number= request.data.get('ticket_number')
            approval_date= request.data.get('approval_date')
            reason_for_disapproval= request.data.get('reason_for_disapproval')
            moisture_level= request.data.get('moisture_percent')
            fancy_count= request.data.get('fancy_count')
            head_count= request.data.get('head_count')
            bin_location_processor= request.data.get('bin_location_processor')
            files = request.FILES.getlist("files")
            print(files)
            approval_date = datetime.strptime(approval_date, '%m/%d/%Y').strftime('%Y-%m-%d')
            if check_shipment:
                shipment = check_shipment.first()
                if status == 'APPROVED' and received_weight :
                    shipment.status=status
                    shipment.received_amount=received_weight
                    shipment.sku=sku_id  #add sku
                    shipment.token_id=ticket_number

                    if approval_date :
                        shipment.approval_date = approval_date
                    else:
                        shipment.approval_date= date.today()

                    shipment.moisture_level=moisture_level
                    shipment.fancy_count=fancy_count
                    shipment.head_count=head_count
                    shipment.bin_location_processor=bin_location_processor 
                    for file in files:
                        new_file = GrowerShipmentFile.objects.create(file=file)
                        shipment.files.add(new_file)                   
                    shipment.save()
                    create_sku_list(shipment.processor.id, "T1", sku_id)
                elif status == 'DISAPPROVED' and reason_for_disapproval :
                    shipment.status=status
                    shipment.reason_for_disapproval=reason_for_disapproval
                    shipment.moisture_level=moisture_level
                    shipment.fancy_count=fancy_count
                    shipment.head_count=head_count
                    shipment.bin_location_processor=bin_location_processor
                    shipment.approval_date= date.today()
                    shipment.save()
                response["status"], response["message"] = "200", f"Shipment updated successfully."
            else:
                response["status"], response["message"] = "400", f"Shipment not found."
        elif user.is_processor2:
            p = ProcessorUser2.objects.get(contact_email=user.email)
            check_shipment = ShipmentManagement.objects.filter(id=shipment_id)
            if check_shipment:
                shipment = check_shipment.first()
                status = request.data.get('status')
                approval_date = request.data.get('approval_date')
                received_weight = request.data.get('received_weight')
                ticket_number = request.data.get('ticket_number')
                receiver_sku_id = request.data.get('receiver_sku_id')
                reason_for_disapproval = request.data.get('reason_for_disapproval')
                moisture_percent = request.data.get('moisture_percent')
                files = request.FILES.getlist("files")
                approval_date = datetime.strptime(approval_date, '%m/%d/%Y').strftime('%Y-%m-%d')
                if status == "APPROVED":
                    shipment.status = status
                    shipment.moisture_percent = moisture_percent
                    shipment.received_weight = received_weight
                    shipment.ticket_number = ticket_number
                    shipment.storage_bin_recive = receiver_sku_id
                    shipment.recive_delivery_date = approval_date
                    shipment.save()
                    for file in files:
                        new_file = File.objects.create(file=file)
                        shipment.files.add(new_file) 
                    shipment.save()
                    create_sku_list(p.processor2.id, p.processor2.processor_type.all().first().type_name, receiver_sku_id)
                elif status == "DISAPPROVED":
                    shipment.status = status
                    shipment.reason_for_disapproval = reason_for_disapproval
                    shipment.recive_delivery_date = approval_date
                    shipment.moisture_percent = moisture_percent
                    shipment.save()
                response["status"], response["message"] = "200", f"Shipment updated successfully."
            else:
                response["status"], response["message"] = "400", f"Shipment not found."
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("GET",))
def check_update_status(request):
    response = {"status":"","message":"", "update":True}
    userid = request.GET.get("userid")
    latest_app_version = VersionUpdate.objects.latest('release_date')
    latest_version_user_list = list(latest_app_version.updated_users.all().values_list("id", flat=True))
    if int(userid) in latest_version_user_list:
        response["update"] = False
    else:
        response["update"] = True
    response["status"] = "200"
    response["message"] = "Update status fetched successfully."
    return Response(response)


@api_view(('POST',))
def update_version(request):
    response = {"status":"","message":""}
    userid = request.data.get("userid")
    status = request.data.get("status")
    user = User.objects.get(id=userid)
    if status == "True":
        latest_app_version = VersionUpdate.objects.latest('release_date')
        latest_app_version.updated_users.add(user)
    response["status"] = "200"
    response["message"] = "Version updated succesfully."
    return Response(response)


@api_view(('GET',))
def distributor_profile_api(request):
    response = Response({'data':[]})
    userid = request.GET.get('userid')
    try:
        user = User.objects.get(id=userid)
        user_email = user.email
        distributorUser = DistributorUser.objects.get(contact_email=user_email)
        distributor = distributorUser.distributor
        response = Response({'distributor':[{'entity_name':distributor.entity_name,
                                           'billing_address':distributor.location, 'warehouses': distributor.warehouse.all().values()}],
                             'distributorUser':[{'contact_name':distributorUser.contact_name,'contact_email':distributorUser.contact_email,
                                               'contact_phone':distributorUser.contact_phone,'contact_fax':distributorUser.contact_fax}]})
    except:
        pass
    return response


@api_view(('GET',))
def warehouse_manager_profile_api(request):
    response = Response({'data':[]})
    userid = request.GET.get('userid')
    try:
        user = User.objects.get(id=userid)
        user_email = user.email
        warehouseUser = WarehouseUser.objects.get(contact_email=user_email)
        warehouse = warehouseUser.warehouse
        distributors = Distributor.objects.filter(warehouse=warehouse)
        distributor_data = [
            {
                'entity_name': distributor.entity_name,
                'location': distributor.location,
                'latitude': distributor.latitude,
                'longitude': distributor.longitude,
            }
            for distributor in distributors
        ]
        response = Response({'warehouse':[{'entity_name':warehouse.name,
                                           'billing_address':warehouse.location, 'account_number':warehouse.account_number, 'distributors': distributor_data}],
                             'warehouseUser':[{'contact_name':warehouseUser.contact_name,'contact_email':warehouseUser.contact_email,
                                               'contact_phone':warehouseUser.contact_phone,'contact_fax':warehouseUser.contact_fax}]})
    except:
        pass
    return response


@api_view(('GET',))
def customer_profile_api(request):
    response = Response({'data':[]})
    userid = request.GET.get('userid')
    try:
        user = User.objects.get(id=userid)
        user_email = user.email
        customerUser = CustomerUser.objects.get(contact_email=user_email)
        customer = customerUser.customer
        warehouse_data = {
                'id': customer.warehouse.id,
                'name': customer.warehouse.name,
                'location': customer.warehouse.location,
                'latitude': customer.warehouse.latitude,
                'longitude': customer.warehouse.longitude                
            }
        
        response = Response({'customer':[{'entity_name':customer.name, 'billing_address':customer.billing_address,
                                          'shipping_address':customer.shipping_address, 'credit_terms':customer.credit_terms, 
                                          'tax_payable':customer.is_tax_payable, 'tax_percentage': customer.tax_percentage, 'warehouse':warehouse_data}],
                             'customerUser':[{'contact_name':customerUser.contact_name,'contact_email':customerUser.contact_email,
                                               'contact_phone':customerUser.contact_phone,'contact_fax':customerUser.contact_fax,"location":customer.location, 'latitude': customer.latitude, 'longitude': customer.longitude }]})
    except Exception as e:
        return Response({"data":[], "message":str(e)})
    return response


@api_view(('POST',))
def add_distributor_user(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.data.get("userid")
    contact_name = request.data.get("contact_name")
    contact_email = request.data.get("contact_email")
    contact_phone = request.data.get("contact_phone")
    contact_fax = request.data.get("contact_fax")
    try:
        user = User.objects.get(id=userid)
        if user.is_distributor:
            d = DistributorUser.objects.filter(contact_email=user.email).first()
            distributor_id = d.distributor.id
            if User.objects.filter(email=contact_email).exists():
                response["status"], response["message"] = "400", f"User with this email already exists."

            password = generate_random_password()                            
            distributor_user = DistributorUser(distributor=d.distributor, contact_name=contact_name,contact_email=contact_email,contact_phone=contact_phone,contact_fax=contact_fax,p_password_raw=password)
            distributor_user.save()
            user = User.objects.create(email=contact_email, username=contact_email,first_name=contact_name)
            user.role.add(Role.objects.get(role='Distributor'))
            user.is_distributor=True
            user.is_active=True
            user.set_password(password)
            user.password_raw = password
            user.save()

            # 07-04-23 Log Table
            log_type, log_status, log_device = "DistributorUser", "Added", "App"
            log_idd, log_name = distributor_user.id, contact_name
            log_email = contact_email
            log_details = f"disttributor_id = {distributor_id} | distributor = {distributor_user.distributor.entity_name}  | contact_name= {contact_name} | contact_email = {contact_email} | contact_phone = {contact_phone} | contact_fax = {contact_fax}"
            
            action_by_userid = user.id
            userr = User.objects.get(pk=action_by_userid)
            user_role = userr.role.all()
            action_by_username = f'{userr.first_name} {userr.last_name}'
            action_by_email = userr.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                log_details=log_details,log_device=log_device)
            logtable.save()
            response["status"], response["message"] = "200", f"Distributor User added successfully."
            return Response(response)
        else:
            response["status"], response["message"] = "400", f"400, User is not a distributor."
            return Response(response)
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
        return Response(response)


@api_view(('POST',))
def edit_distributor_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.data.get("userid")
    entity_name = request.data.get("entity_name")
    warehouse_ids  = request.data.getlist('warehouse_ids')
    location = request.data.get('location')
    latitude  = request.data.get('latitude ')
    longitude = request.data.get('longitude')

    contact_email = request.data.get("contact_email")
    contact_name = request.data.get("contact_name")
    contact_phone = request.data.get("contact_phone")
    contact_fax = request.data.get("contact_fax")
    try:
        user = User.objects.get(id=userid)
        if user.is_distributor:
            distributor_user = DistributorUser.objects.filter(contact_email=user.email).first()
            distributor_user.contact_email = contact_email
            distributor_user.contact_name = contact_name
            distributor_user.contact_phone = contact_phone
            distributor_user.contact_fax = contact_fax
            distributor_user.distributor.entity_name = entity_name
            distributor_user.distributor.location = location
            distributor_user.distributor.longitude = longitude
            distributor_user.distributor.latitude = latitude
            
            distributor_user.distributor.save()
            distributor_user.save()
            for warehouse_id in warehouse_ids:
                try:
                    warehouse = Warehouse.objects.get(id=warehouse_id)
                    distributor_user.distributor.warehouse.add(warehouse)
                except Warehouse.DoesNotExist:
                    pass

            if contact_email != user.email:
                f_name = contact_name
                user.email = contact_email
                user.username = contact_email
                user.first_name = f_name
                user.save()
            
            else :
                f_name = contact_name
                user.first_name = f_name
                user.save()
            log_type, log_status, log_device = "DistributorUser", "Edited", "Web"
            log_idd, log_name, log_email = distributor_user.id, contact_name, contact_email
            log_details = f"distributor_id = {distributor_user.distributor.id} | distributor = {distributor_user.distributor.entity_name} | contact_name= {contact_name} | contact_email = {contact_email} | contact_phone = {contact_phone} | contact_fax = {contact_fax}"
            action_by_userid = user.id
            userr = User.objects.get(pk=action_by_userid)
            user_role = userr.role.all()
            action_by_username = f'{userr.first_name} {userr.last_name}'
            action_by_email = userr.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                log_details=log_details,log_device=log_device)
            logtable.save()
            response["status"], response["message"] = "200", f"Distributor Updated successfully."
            return Response(response)
        else:
            response["status"], response["message"] = "400", f"400, User is not a distributor."
            return Response(response)
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(('POST',))
def edit_warehouse_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.data.get("userid")
    entity_name = request.data.get("entity_name")
    distributor_ids  = request.data.getlist('distributor_ids')
    customer_ids  = request.data.getlist('customer_ids')
    location = request.data.get('location')
    latitude  = request.data.get('latitude ')
    longitude = request.data.get('longitude')

    contact_email = request.data.get("contact_email")
    contact_name = request.data.get("contact_name")
    contact_phone = request.data.get("contact_phone")
    contact_fax = request.data.get("contact_fax")
    try:
        user = User.objects.get(id=userid)
        if user.is_warehouse_manager:
            warehouse_user = WarehouseUser.objects.filter(contact_email=user.email).first()
            warehouse_user.contact_email = contact_email
            warehouse_user.contact_name = contact_name
            warehouse_user.contact_phone = contact_phone
            warehouse_user.contact_fax = contact_fax
            warehouse_user.warehouse.name = entity_name
            warehouse_user.warehouse.location = location
            warehouse_user.warehouse.longitude = longitude
            warehouse_user.warehouse.latitude = latitude
            
            warehouse_user.warehouse.save()
            warehouse_user.save()
            customers = Customer.objects.filter(id__in=customer_ids)
            distributors = Distributor.objects.filter(id__in=distributor_ids)

            Customer.objects.filter(warehouse=warehouse_user.warehouse).exclude(id__in=[customer.id for customer in customers]).update(warehouse=None)
            
            # Then, set the current warehouse for each selected customer
            for customer in customers:
                customer.warehouse = warehouse_user.warehouse
                customer.save()                     
            
            current_distributors = warehouse_user.warehouse.distributor_set.all()

            for distributor in current_distributors:
                if distributor not in distributors:
                    distributor.warehouse.remove(warehouse_user.warehouse)

            for distributor in distributors:
                distributor.warehouse.add(warehouse_user.warehouse)

            if contact_email != user.email:
                f_name = contact_name
                user.email = contact_email
                user.username = contact_email
                user.first_name = f_name
                user.save()
            
            else :
                f_name = contact_name
                user.first_name = f_name
                user.save()

            log_type, log_status, log_device = "WarehouseUser", "Edited", "Web"
            log_idd, log_name, log_email = warehouse_user.id, contact_name, contact_email
            log_details = f"warehouse_id = {warehouse_user.warehouse.id} | warehouse = {warehouse_user.warehouse.name} | contact_name= {contact_name} | contact_email = {contact_email} | contact_phone = {contact_phone} | contact_fax = {contact_fax}"
            action_by_userid = user.id
            userr = User.objects.get(pk=action_by_userid)
            user_role = userr.role.all()
            action_by_username = f'{userr.first_name} {userr.last_name}'
            action_by_email = userr.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                log_details=log_details,log_device=log_device)
            logtable.save()
            response["status"], response["message"] = "200", f"Warehouse Updated successfully."
            return Response(response)
        else:
            response["status"], response["message"] = "400", f"400, User is not a warehouse manager."
            return Response(response)
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(('POST',))
def edit_customer_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.data.get("userid")
    entity_name = request.data.get("entity_name")
    warehouse_id = request.data.get('warehouse_id')
    credit_terms = request.data.get('credit_terms')
    is_taxable = request.data.get('is_taxable')
    tax_percentage = request.data.get('tax_percentage')
    location = request.data.get('location')
    latitude  = request.data.get('latitude')
    longitude = request.data.get('longitude')
    contact_email = request.data.get("contact_email")
    contact_name = request.data.get("contact_name")
    contact_phone = request.data.get("contact_phone")
    contact_fax = request.data.get("contact_fax")
    try:
        user = User.objects.get(id=userid)
        if user.is_customer:
            customer_user = CustomerUser.objects.filter(contact_email=user.email).first()
            customer_user.contact_email = contact_email
            customer_user.contact_name = contact_name
            customer_user.contact_phone = contact_phone
            customer_user.contact_fax = contact_fax
            customer_user.customer.name = entity_name
            customer_user.customer.location = location
            customer_user.customer.longitude = longitude
            customer_user.customer.latitude = latitude
            customer_user.customer.is_tax_payable = is_taxable
            customer_user.customer.credit_terms = credit_terms
            customer_user.customer.tax_percentage = tax_percentage          
            
            if warehouse_id not in [None, "", "null", " "]:
                warehouse = Warehouse.objects.filter(id=int(warehouse_id)).first()
                if customer_user.customer.warehouse_id != int(warehouse_id):
                    customer_user.customer.warehouse = warehouse

            customer_user.customer.save()
            customer_user.save()

            if contact_email != user.email:
                f_name = contact_name
                user.email = contact_email
                user.username = contact_email
                user.first_name = f_name
                user.save()
            
            else :
                f_name = contact_name
                user.first_name = f_name
                user.save()

            log_type, log_status, log_device = "CustomerUser", "Edited", "Web"
            log_idd, log_name, log_email = customer_user.id, contact_name, contact_email
            log_details = f"customer_id = {customer_user.customer.id} | customer = {customer_user.customer.name} | contact_name= {contact_name} | contact_email = {contact_email} | contact_phone = {contact_phone} | contact_fax = {contact_fax}"
            action_by_userid = user.id
            userr = User.objects.get(pk=action_by_userid)
            user_role = userr.role.all()
            action_by_username = f'{userr.first_name} {userr.last_name}'
            action_by_email = userr.username
            if user.id == 1 :
                action_by_role = "superuser"
            else:
                action_by_role = str(','.join([str(i.role) for i in user_role]))
            logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                action_by_userid=action_by_userid,action_by_username=action_by_username,
                                action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                log_details=log_details,log_device=log_device)
            logtable.save()
            response["status"], response["message"] = "200", f"Warehouse Updated successfully."
            return Response(response)
        else:
            response["status"], response["message"] = "400", f"400, User is not a customer"
            return Response(response)
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("GET",))
def get_distributor_list(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.GET.get("userid")
    try:
        user = User.objects.get(id=int(userid))
        distributor_list = Distributor.objects.all().values()    
        response["status"], response["message"], response["data"] = "200", "Distributor List fetched successfully.", distributor_list   
    except Exception as e:
        response["status"], response["message"], response["data"] = "500", f"500, {e}", []
    return Response(response)


@api_view(("GET",))
def get_processor_contracts(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.GET.get("userid")
    try:
        user = User.objects.get(id=int(userid))
        if user.is_processor:
            p = ProcessorUser.objects.get(contact_email=user.email) 
            processor_id = p.processor.id
            processor_name = p.processor.entity_name
            processor_type = "T1"
        elif user.is_processor2:
            p = ProcessorUser2.objects.get(contact_email=user.email) 
            processor_id = p.processor2.id
            processor_name = p.processor2.entity_name
            processor_type = Processor2.objects.filter(id=processor_id).first().processor_type.all().first().type_name

        contracts = AdminProcessorContract.objects.filter(processor_id=processor_id, processor_type=processor_type, processor_entity_name=processor_name).values()
        serializer = AdminProcessorContractSerializer(contracts, many=True)

        response["status"], response["message"], response["data"] = "200", "Contracts fetched successfully.", serializer.data
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("GET",))
def get_selected_processor(request):
    response = {"status": "", "message": "", "data": None}
    selected_contract = request.GET.get('selected_contract')
    if not selected_contract:
        response["status"], response["message"] = "400", f"400, No contract selected"
        return Response(response)     
    contract = AdminProcessorContract.objects.filter(id=selected_contract).first()
    if contract:
        data = {"processor_id":contract.processor_id, "processor_type":contract.processor_type, "processor_entity_name":contract.processor_entity_name}
        response["status"], response["message"], response["data"] = "200", "Selected Processor fetched successfully", data
        return Response(response)
    else:
        response["status"], response["message"] = "400", f"400"
        return Response(response)


@api_view(("GET",))
def get_destination_list(request):
    response = {"status": "", "message": "", "data": []}
    destination_type = request.GET.get('destination_type')
    if not destination_type:
        response["status"], response["message"] = "400", f"400, Destination type is not selected."
        return Response(response)
    if destination_type == 'warehouse':
        destination_list = list(Warehouse.objects.all().values('id','name'))
    if destination_type == 'customer':
        destination_list = list(Customer.objects.filter(is_active=True).values('id','name'))
    if destination_list:
        response["status"], response["message"], response["data"] = "200", "Destination fetched successfully", destination_list
        return Response(response)
    else:
        response["status"], response["message"] = "400", f"400"
        return Response(response)


@api_view(("GET",))
def get_processor_contract_crops(request):
    response = {"status": "", "message": "", "data": []}
    selected_contract_id = request.GET.get('selected_contract')
    if not selected_contract_id:
        response["status"], response["message"] = "400", f"400, No contract selected"
        return Response(response)
    
    contract = AdminProcessorContract.objects.filter(id=int(selected_contract_id)).first()
    crops = list(CropDetails.objects.filter(contract=contract).values('id', 'crop', 'crop_type'))
    if crops:
        response["status"], response["message"], response["data"] = "200", "Crops fetched successfully", crops
        return Response(response)
    else:
        response["status"], response["message"] = "400", f"400"
        return Response(response)


@api_view(('POST',))
def create_processor_shipment_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.data.get("userid")

    selected_contract_id = request.data.get("selected_contract")
    outbound_type = request.data.get('outbound_type')
    carrier_type = request.data.get('carrier_type')
    carrier_id = request.data.get('carrier_id')
    purchase_order_name = request.data.get('purchase_order_name')
    purchase_order_number = request.data.get('purchase_order_number')
    
    shipment_type = request.data.get('shipment_type')
    destination_type = request.data.get('selected_destination')
    destination_id = request.data.get('destination_id') 
    customer_contract = request.data.get('customer_contract')
    crop_ids = request.data.getlist('crop_id[]')
    gross_weights = request.data.getlist('gross_weight[]')
    weights = request.data.getlist('weight[]')
    amount_unit = request.data.get('amount_unit')
    ship_weights = request.data.getlist('ship_weight[]')
    ship_quantities = request.data.getlist('ship_quantity[]')
    lot_numbers = request.data.getlist('lot_number[]')

    status = request.data.get('status')
    files = request.FILES.getlist('files')
    final_payment_date = request.data.get('final_payment_date')
    try:
        user = User.objects.get(id=userid)      
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

        shipment = ProcessorWarehouseShipment(
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
        shipment.save()

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
                shipment=shipment,
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
            shipment.final_payment_date=final_payment_date  
        shipment.save()

        if carrier_id:
            CarrierDetails.objects.create(shipment=shipment, carrier_id=carrier_id)      
        
        for file in files:
            ProcessorWarehouseShipmentDocuments.objects.create(shipment=shipment, document_file=file)   

        if shipment.warehouse_id not in [None, 'null', ' ', '']:                            
            all_user = WarehouseUser.objects.filter(warehouse_id=shipment.warehouse_id)                         
            distributors = Distributor.objects.filter(warehouse__id=shipment.warehouse_id)                         
            distributor_users = DistributorUser.objects.filter(distributor__in=distributors)
        else:                            
            all_user = CustomerUser.objects.filter(customer_id=shipment.customer_id)
            distributor_users = []                          
        all_users = list(all_user) + list(distributor_users)

        for user in all_users :
            msg = f'A shipment has been sent  under Contract ID - {shipment.contract.secret_key}'
            get_user = User.objects.get(username=user.contact_email)
            notification_reason = 'New Shipment'
            redirect_url = "/warehouse/list-processor-shipment/"
            save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
                notification_reason=notification_reason)
            save_notification.save()

        response["status"] = "200"
        response["message"] = f"Processor shipment created successfully."
        return Response(response)
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("GET",))
def processor_shipment_list_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.GET.get("userid")
    try:
        user = User.objects.get(id=int(userid))
        if user.is_processor:
            p = ProcessorUser.objects.get(contact_email=user.email) 
            processor_id = p.processor.id
            processor_name = p.processor.entity_name
            processor_type = "T1"
            shipments = ProcessorWarehouseShipment.objects.filter(processor_id=processor_id, processor_type=processor_type, processor_entity_name=processor_name)
        elif user.is_processor2:
            p = ProcessorUser2.objects.get(contact_email=user.email) 
            processor_id = p.processor2.id
            processor_name = p.processor2.entity_name
            processor_type = Processor2.objects.filter(id=processor_id).first().processor_type.all().first().type_name
            shipments = ProcessorWarehouseShipment.objects.filter(processor_id=processor_id, processor_type=processor_type, processor_entity_name=processor_name)
        elif user.is_customer:
            customer = CustomerUser.objects.filter(contact_email=user.email).first()
            shipments = ProcessorWarehouseShipment.objects.filter(customer_id=customer.customer.id)
            print("shipments", shipments)
        else:
            shipments = []
        serializer = ProcessorWarehouseShipmentSerializer(shipments, many=True)
        response["status"], response["message"], response["data"] = "200", "Processor shipments fetched successfully", serializer.data
        return Response(response)

    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("GET",))
def processor_shipment_view_api(request):
    response = {"status": "", "message": "", "data": []}
    shipment_id = request.GET.get("shipment_id")
    try:
        check_shipment = ProcessorWarehouseShipment.objects.filter(id=int(shipment_id))
        if check_shipment.exists():
            shipment = check_shipment.first()
            serializer = ProcessorWarehouseShipmentSerializer(shipment)
            response["status"], response["message"], response["data"] = "200", "Processor shipment data fetched successfully", serializer.data
            return Response(response)
        else:
            response["status"], response["message"] = "400", f"400"
            return Response(response)
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("POST", ))
def edit_processor_shipment_api(request):
    response = {"status": "", "message": "", "data": []}
    shipment_id = request.data.get("shipment_id")

    selected_contract_id = request.data.get("selected_contract")
    outbound_type = request.data.get('outbound_type')
    carrier_type = request.data.get('carrier_type')
    carrier_id = request.data.get('carrier_id')
    purchase_order_name = request.data.get('purchase_order_name')
    purchase_order_number = request.data.get('purchase_order_number')
    
    shipment_type = request.data.get('shipment_type')
    destination_type = request.data.get('selected_destination')
    destination_id = request.data.get('destination_id') 
    customer_contract = request.data.get('customer_contract')
    status = request.data.get('status')
    files = request.FILES.getlist('files')
    final_payment_date = request.data.get('final_payment_date')

    crop_ids = request.data.getlist('crop_id[]')
    gross_weights = request.data.getlist('gross_weight[]')
    weights = request.data.getlist('weight[]')
    amount_unit = request.data.get('amount_unit')
    ship_weights = request.data.getlist('ship_weight[]')
    ship_quantities = request.data.getlist('ship_quantity[]')
    lot_numbers = request.data.getlist('lot_number[]')   

    border_receive_date = request.data.get('border_receive_date')
    border_leaving_date = request.data.get('border_leaving_date') 
    final_receive_date = request.data.get('final_receive_date')
    final_leaving_date = request.data.get('final_leaving_date')
    border_receive_date2 = request.data.get('border_receive_date2')  
    border_leaving_date2 = request.data.get('border_leaving_date2') 
    processor_receive_date = request.data.get('processor_receive_date')

    crops = request.data.getlist('crop[]')
    additional_lot_numbers = request.data.getlist('additional_lot_number[]')
    addresses = request.data.getlist('address[]')
    descriptions = request.data.getlist('description[]')

    try:
        check_shipment = ProcessorWarehouseShipment.objects.filter(id=int(shipment_id))
        if check_shipment.exists():
            shipment = check_shipment.first()
            changes = find_changes(request.data, shipment)
            contract = AdminProcessorContract.objects.filter(id=int(selected_contract_id)).first()
            if shipment.processor_type == "T1": 
                processor = Processor.objects.filter(processor_id=int(shipment.processor_id)).first()
                processor_location = Location.objects.filter(processor=processor).first()
                if processor_location:
                    location = processor_location.name
                else:
                    location = "Origin location"
            else:
                processor = Processor2.objects.filter(processor_id=int(shipment.processor_id)).first()
                processor_location = Processor2Location.objects.filter(processor=processor).first()
                if processor_location:
                    location = processor_location.name
                else:
                    location = "Origin location"           

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

            shipment.contract=contract,
            shipment.processor_id=contract.processor_id,
            shipment.processor_type=contract.processor_type,
            shipment.processor_entity_name=contract.processor_entity_name,
            
            shipment.carrier_type=carrier_type,
            shipment.outbound_type=outbound_type,
            shipment.purchase_order_name=purchase_order_name,
            shipment.purchase_order_number=purchase_order_number,           
            shipment.shipment_type=shipment_type,          
            
            shipment.status=status,
            shipment.customer_id=customer_id,
            shipment.warehouse_id=warehouse_id,
            shipment.customer_name=customer_name,
            shipment.warehouse_name=warehouse_name,
            shipment.customer_contract=customer_contract

            if final_payment_date not in [None, '', ' ', 'null']:            
                shipment.final_payment_date=final_payment_date 

            if border_receive_date not in [None, '', ' ', 'null']:            
                shipment.border_receive_date=border_receive_date 

            if border_leaving_date not in [None, '', ' ', 'null']:            
                shipment.border_leaving_date=border_leaving_date 

            if final_receive_date not in [None, '', ' ', 'null']:            
                shipment.distributor_receive_date=final_receive_date 

            if final_leaving_date not in [None, '', ' ', 'null']:            
                shipment.distributor_leaving_date=final_leaving_date 

            if border_receive_date2 not in [None, '', ' ', 'null']:            
                shipment.border_back_receive_date=border_receive_date2 

            if border_leaving_date2 not in [None, '', ' ', 'null']:            
                shipment.border_back_leaving_date=border_leaving_date2 

            if processor_receive_date not in [None, '', ' ', 'null']:            
                shipment.processor_receive_date=processor_receive_date 
            shipment.save()
            
            ProcessorShipmentCrops.objects.filter(shipment=shipment).delete()

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
                    shipment=shipment,
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
            if carrier_id:                     
                carrier_details, created = CarrierDetails.objects.update_or_create(
                    shipment=shipment,
                    defaults={'carrier_id': carrier_id}
                )
            else:                      
                CarrierDetails.objects.filter(shipment=shipment).delete()      
            
            ProcessorWarehouseShipmentDocuments.objects.filter(shipment=shipment).delete()
            for file in files:
                ProcessorWarehouseShipmentDocuments.objects.create(shipment=shipment, document_file=file) 

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
            descriptions = request.data.getlist('description')

            for  description in  descriptions:
                if  description:                    
                    ProcessorShipmentLog.objects.create(
                        shipment=shipment,                           
                        description=description,
                        changes = {"changes":changes},
                        updated_by = request.user
                    )
            response["status"], response["message"] = "200", "Processor shipment is updated successfully."
            return Response(response)
        else:
            response["status"], response["message"] = "400", "Processor shipment not found."
            return Response(response)
                            
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("POST",))
def delete_processor_shipment_api(request):
    response = {"status": "", "message": "", "data": []}
    shipment_id = request.data.get("shipment_id")
    try:
        check_shipment = ProcessorWarehouseShipment.objects.filter(id=int(shipment_id))
        if check_shipment.exists():
            shipment = check_shipment.first()
            shipment.delete()
            response["status"], response["message"] = "200", "Processor shipment deleted successfully."
            return Response(response)
        else:
            response["status"], response["message"] = "400", "Processor shipment not found."
            return Response(response)
                            
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("GET",))
def get_customer_contracts(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.GET.get("userid")
    try:
        user = User.objects.get(id=int(userid))
        if user.is_warehouse_manager:
            w = WarehouseUser.objects.get(contact_email=user.email)             
            customers = Customer.objects.filter(warehouse=w.warehouse)  
            contracts = AdminCustomerContract.objects.filter(customer_id__in=list(customers.values_list('id', flat=True))).values().order_by('-id')

        elif user.is_distributor:
            d = DistributorUser.objects.get(contact_email=user.email)             
            warehouses = d.distributor.warehouse.all().values('id', 'name') 
            warehouse_ids = [warehouse['id'] for warehouse in warehouses]
            customers = Customer.objects.filter(warehouse__id__in=warehouse_ids)  
            contracts = AdminCustomerContract.objects.filter(customer_id__in=list(customers.values_list('id', flat=True))).values().order_by('-id')        
        
        elif user.is_customer:
            c = CustomerUser.objects.get(contact_email=user.email)
            customer_id = Customer.objects.get(id=c.customer.id).id
            contracts = AdminCustomerContract.objects.filter(customer_id=customer_id)

        serializer = AdminCustomerContractSerializer(contracts, many=True)    
        response["status"], response["message"], response["data"] = "200", "Contracts fetched successfully.", serializer.data
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("GET",))
def get_warehouse_list(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.GET.get("userid")
    try:
        user = User.objects.get(id=int(userid))
        if user.is_warehouse_manager:
            warehouse_user = WarehouseUser.objects.get(contact_email=user.email) 
            warehouse = warehouse_user.warehouse
            data = {"id":warehouse.id, "name":warehouse.name}
            response["status"], response["message"], response["data"] = "200", f"Warehouse List fetched successfully", data
            return Response(response)
        
        if user.is_distributor:
            distributor_user = DistributorUser.objects.get(contact_email=user.email) 
            distributor = Distributor.objects.get(id=distributor_user.distributor.id)
            warehouses = distributor.warehouse.all().values('id', 'name')
            response["status"], response["message"], response["data"] = "200", "Warehouse List fetched successfully", warehouses
            return Response(response)
        
    except Exception as e:
        response["status"], response["message"], response["data"] = "500", f"500, {e}", []
    return Response(response)


@api_view(("GET",))
def get_selected_customer(request):
    response = {"status": "", "message": "", "data": None}
    selected_contract = request.GET.get('selected_contract')
    if not selected_contract:
        response["status"], response["message"] = "400", f"400, No contract selected"
        return Response(response)     
    contract = AdminCustomerContract.objects.filter(id=selected_contract).first()
    if contract:
        data = {"customer_id":contract.customer_id, "customer_name":contract.customer_name}
        response["status"], response["message"], response["data"] = "200", "Selected Customer fetched successfully", data
        return Response(response)
    else:
        response["status"], response["message"] = "400", f"400"
        return Response(response)


@api_view(("GET",))
def get_customer_contract_crops(request):
    response = {"status": "", "message": "", "data": []}
    selected_contract_id = request.GET.get('selected_contract')
    if not selected_contract_id:
        response["status"], response["message"] = "400", f"400, No contract selected"
        return Response(response)
    
    contract = AdminCustomerContract.objects.filter(id=int(selected_contract_id)).first()
    crops = list(CustomerContractCropDetails.objects.filter(contract=contract).values('id', 'crop', 'crop_type'))
    if crops:
        response["status"], response["message"], response["data"] = "200", "Crops fetched successfully", crops
        return Response(response)
    else:
        response["status"], response["message"] = "400", f"400"
        return Response(response)


@api_view(("POST",))
def create_warehouse_shipment_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.data.get("userid")

    selected_contract_id = request.data.get("selected_contract")
    selected_warehouse = request.data.get('selected_warehouse')
    outbound_type = request.data.get('outbound_type')
    carrier_type = request.data.get('carrier_type')
    carrier_id = request.data.get('carrier_id')
    purchase_order_name = request.data.get('purchase_order_name')
    purchase_order_number = request.data.get('purchase_order_number')

    shipment_type = request.data.get('shipment_type')  

    crop_ids = request.data.getlist('crop_id[]')
    gross_weights = request.data.getlist('gross_weight[]')
    weights = request.data.getlist('weight[]')
    amount_unit = request.data.get('amount_unit')
    ship_weights = request.data.getlist('ship_weight[]')
    ship_quantities = request.data.getlist('ship_quantity[]')
    lot_numbers = request.data.getlist('lot_number[]')

    status = request.data.get('status')
    files = request.FILES.getlist('files')
    final_payment_date = request.data.get('final_payment_date') 
    try:
        user = User.objects.get(id=userid)      
        contract = AdminCustomerContract.objects.filter(id=int(selected_contract_id)).first()
        warehouse = Warehouse.objects.filter(id=int(selected_warehouse)).first()

        shipment = WarehouseCustomerShipment(
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
        shipment.save()

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
            
        if final_payment_date not in [None, '', ' ', 'null']:                       
            shipment.final_payment_date=final_payment_date  
        shipment.save()                      
        
        if carrier_id:
            CarrierDetails2.objects.create(shipment=shipment, carrier_id=carrier_id)
        
        for file in files:
            WarehouseCustomerShipmentDocuments.objects.create(shipment=shipment, document_file=file)

        all_users = CustomerUser.objects.filter(customer_id=shipment.customer_id)
                    
        for user in all_users :
            msg = f'A shipment has been sent under Contract ID - {shipment.contract.secret_key}'
            get_user = User.objects.get(username=user.contact_email)
            notification_reason = 'New Shipment'
            redirect_url = "/warehouse/list-warehouse-shipment/"
            save_notification = ShowNotification(user_id_to_show=get_user.id,msg=msg,status="UNREAD",redirect_url=redirect_url,
                notification_reason=notification_reason)
            save_notification.save()
        response["status"], response["message"] = "200", "Warehouse Shipment created successfully."
        return Response(response)        
                     
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("GET",))
def warehouse_shipment_list_api(request):
    response = {"status": "", "message": "", "data": []}
    userid = request.GET.get("userid")
    try:
        user = User.objects.get(id=int(userid))
        if user.is_warehouse_manager:
            w = WarehouseUser.objects.get(contact_email=user.email)
            warehouse_id = Warehouse.objects.get(id=w.warehouse.id).id
            shipments = WarehouseCustomerShipment.objects.filter(warehouse_id=warehouse_id)
        elif user.is_distributor:
            d = DistributorUser.objects.get(contact_email=user.email)
            distributor = Distributor.objects.get(id=d.distributor.id)
            warehouses = distributor.warehouse.all().values_list('id', flat=True)
            shipments = []
            for warehouse_id in warehouses:
                check_shipment = WarehouseCustomerShipment.objects.filter(warehouse_id=warehouse_id).order_by('-id')
                if check_shipment:
                    shipments = shipments + list(check_shipment)

        elif user.is_customer:
            customer = CustomerUser.objects.filter(contact_email=user.email).first()
            shipments = WarehouseCustomerShipment.objects.filter(customer_id=customer.customer.id)

        else:
            shipments = []

        serializer = WarehouseCustomerShipmentSerializer(shipments, many=True)
        response["status"], response["message"], response["data"] = "200", "Warehouse shipments fetched successfully", serializer.data
        return Response(response)

    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("GET",))
def warehouse_shipment_view_api(request):
    response = {"status": "", "message": "", "data": []}
    shipment_id = request.GET.get("shipment_id")
    try:
        check_shipment = WarehouseCustomerShipment.objects.filter(id=int(shipment_id))
        if check_shipment.exists():
            shipment = check_shipment.first()
            serializer = WarehouseCustomerShipmentSerializer(shipment)
            response["status"], response["message"], response["data"] = "200", "Warehouse shipment data fetched successfully", serializer.data
            return Response(response)
        else:
            response["status"], response["message"] = "400", f"400"
            return Response(response)
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("POST",))
def edit_warehouse_shipment_api(request):
    response = {"status": "", "message": "", "data": []}
    shipment_id = request.data.get("shipment_id")

    selected_contract_id = request.data.get("selected_contract")
    outbound_type = request.data.get('outbound_type')
    carrier_type = request.data.get('carrier_type')
    carrier_id = request.data.get('carrier_id')
    purchase_order_name = request.data.get('purchase_order_name')
    purchase_order_number = request.data.get('purchase_order_number')
    
    shipment_type = request.data.get('shipment_type')
    selected_warehouse = request.data.get('selected_warehouse')
    status = request.data.get('status')
    files = request.FILES.getlist('files')
    final_payment_date = request.data.get('final_payment_date')

    crop_ids = request.data.getlist('crop_id[]')
    gross_weights = request.data.getlist('gross_weight[]')
    weights = request.data.getlist('weight[]')
    amount_unit = request.data.get('amount_unit')
    ship_weights = request.data.getlist('ship_weight[]')
    ship_quantities = request.data.getlist('ship_quantity[]')
    lot_numbers = request.data.getlist('lot_number[]')   

    border_receive_date = request.data.get('border_receive_date')
    border_leaving_date = request.data.get('border_leaving_date') 
    final_receive_date = request.data.get('final_receive_date')
    final_leaving_date = request.data.get('final_leaving_date')
    border_receive_date2 = request.data.get('border_receive_date2')  
    border_leaving_date2 = request.data.get('border_leaving_date2') 
    processor_receive_date = request.data.get('processor_receive_date')

    crops = request.data.getlist('crop[]')
    additional_lot_numbers = request.data.getlist('additional_lot_number[]')
    addresses = request.data.getlist('address[]')
    descriptions = request.data.getlist('description[]')

    try:
        check_shipment = WarehouseCustomerShipment.objects.filter(id=int(shipment_id))
        if check_shipment.exists():

            shipment = check_shipment.first()
            changes = find_changes_for_customer_shipment(request.data, shipment)

            contract = AdminCustomerContract.objects.filter(id=int(selected_contract_id)).first()
            warehouse = Warehouse.objects.filter(id=int(selected_warehouse)).first()
            shipment.contract=contract,
            shipment.warehouse_id=warehouse.id,            
            shipment.warehouse_name=warehouse.name,
            
            shipment.carrier_type=carrier_type,
            shipment.outbound_type=outbound_type,
            shipment.purchase_order_name=purchase_order_name,
            shipment.purchase_order_number=purchase_order_number,           
            shipment.shipment_type=shipment_type,          
            
            shipment.status=status,
            shipment.customer_id=contract.customer_id,            
            shipment.customer_name=contract.customer_name,
            
            if final_payment_date not in [None, '', ' ', 'null']:            
                shipment.final_payment_date=final_payment_date 

            if border_receive_date not in [None, '', ' ', 'null']:            
                shipment.border_receive_date=border_receive_date 

            if border_leaving_date not in [None, '', ' ', 'null']:            
                shipment.border_leaving_date=border_leaving_date 

            if final_receive_date not in [None, '', ' ', 'null']:            
                shipment.customer_receive_date=final_receive_date 

            if final_leaving_date not in [None, '', ' ', 'null']:            
                shipment.customer_leaving_date=final_leaving_date 

            if border_receive_date2 not in [None, '', ' ', 'null']:            
                shipment.border_back_receive_date=border_receive_date2 

            if border_leaving_date2 not in [None, '', ' ', 'null']:            
                shipment.border_back_leaving_date=border_leaving_date2 

            if processor_receive_date not in [None, '', ' ', 'null']:            
                shipment.warehouse_receive_date=processor_receive_date 
            shipment.save()
            
            WarehouseShipmentCrops.objects.filter(shipment=shipment).delete()

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
                    shipment=shipment,
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
            if carrier_id:                     
                carrier_details, created = CarrierDetails2.objects.update_or_create(
                    shipment=shipment,
                    defaults={'carrier_id': carrier_id}
                )
            else:                      
                CarrierDetails2.objects.filter(shipment=shipment).delete()      
            
            WarehouseCustomerShipmentDocuments.objects.filter(shipment=shipment).delete()
            for file in files:
                WarehouseCustomerShipmentDocuments.objects.create(shipment=shipment, document_file=file) 

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
            descriptions = request.data.getlist('description')

            for  description in  descriptions:
                if  description:                    
                    WarehouseShipmentLog.objects.create(
                        shipment=shipment,                           
                        description=description,
                        changes = {"changes":changes},
                        updated_by = request.user
                    )
            response["status"], response["message"] = "200", "Warehouse shipment is updated successfully."
            return Response(response)
        else:
            response["status"], response["message"] = "400", "Warehouse shipment not found."
            return Response(response)
                            
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("POST",))
def delete_warehouse_shipment_api(request):
    response = {"status": "", "message": "", "data": []}
    shipment_id = request.data.get("shipment_id")
    try:
        check_shipment = WarehouseCustomerShipment.objects.filter(id=int(shipment_id))
        if check_shipment.exists():
            shipment = check_shipment.first()
            shipment.delete()
            response["status"], response["message"] = "200", "Warehouse shipment deleted successfully."
            return Response(response)
        else:
            response["status"], response["message"] = "400", "Warehouse shipment not found."
            return Response(response)
                            
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("GET",))
def processor_shipment_invoice(request):
    response = {"status": "", "message": "", "data": []}
    shipment_id = request.GET.get("shipment_id")
    try:
        check_shipment = ProcessorWarehouseShipment.objects.filter(id=int(shipment_id))
        if check_shipment.exists():
            shipment = check_shipment.first()
            if shipment.customer_id not in ["null", None, " ", ""]:
                customer = Customer.objects.filter(id=shipment.customer_id).first()
                customer_user = CustomerUser.objects.filter(customer=customer).first()
                payment_details = PaymentForShipment.objects.filter(shipment_type='processor', processor_shipment=shipment, status=True).first()
                
                data = {}
                data["shipment"] = check_shipment.values()
                data["payment"] = payment_details       
                data['customer'] = customer
                data['total_amount'] = float(shipment.total_payment)
                data['customer_user'] = customer_user
                shipment_crops = ProcessorShipmentCrops.objects.filter(shipment=shipment).values()           
                
                for crop in shipment_crops:
                    crop_ =CropDetails.objects.filter(id=int(crop["crop_id"])).first()
                    crop["per_unit_rate"] = crop_.per_unit_rate
                data["shipment_crops"] = shipment_crops
                
                due_date = shipment.final_payment_date if shipment.final_payment_date else (shipment.approval_time + timedelta(days=int(customer.credit_terms)))
                data['due_date'] = due_date

                response["status"], response["message"], response["data"] = "200", f"Invoice data fetched successfully.", data
                return Response(response)
            else:
                response["status"], response["message"] = "400", f"400, Invoice not available."
                return Response(response)
        else:
            response["status"], response["message"] = "400", f"400, Shipment not found."
            return Response(response)
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("GET",))
def warehouse_shipment_invoice(request):
    response = {"status": "", "message": "", "data": []}
    shipment_id = request.GET.get("shipment_id")
    try:
        check_shipment = WarehouseCustomerShipment.objects.filter(id=int(shipment_id))
        if check_shipment.exists():
            shipment = check_shipment.first()
            
            customer = Customer.objects.filter(id=shipment.customer_id).first()
            customer_user = CustomerUser.objects.filter(customer=customer).first()
            payment_details = PaymentForShipment.objects.filter(shipment_type='warehouse', warehouse_shipment=shipment, status=True).first()
            
            data = {}
            data["shipment"] = check_shipment.values()
            data["payment"] = payment_details       
            data['customer'] = customer
            data['total_amount'] = float(shipment.total_payment)
            data['customer_user'] = customer_user
            shipment_crops = WarehouseShipmentCrops.objects.filter(shipment=shipment).values()           
            
            for crop in shipment_crops:
                crop_ = CustomerContractCropDetails.objects.filter(id=int(crop["crop_id"])).first()
                crop["per_unit_rate"] = crop_.per_unit_rate
            data["shipment_crops"] = shipment_crops
            
            due_date = shipment.final_payment_date if shipment.final_payment_date else (shipment.approval_time + timedelta(days=int(customer.credit_terms)))
            data['due_date'] = due_date

            response["status"], response["message"], response["data"] = "200", f"Invoice data fetched successfully.", data
            return Response(response)
            
        else:
            response["status"], response["message"] = "400", f"400, Shipment not found."
            return Response(response)
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("POST",))
def create_payment_for_shipment(request):
    response = {"status": "", "message": "", "data": []}
    type = request.data.get('type')
    shipment_id = request.data.get("shipment_id")
    userid = request.data.get("userid")
    try:
        user = User.objects.get(id=int(userid))
        if type == 'warehouse':
            warehouse_shipment = WarehouseCustomerShipment.objects.get(id=int(shipment_id)) 
            customer = Customer.objects.get(id=int(warehouse_shipment.customer_id))     
            amount = float(warehouse_shipment.total_payment)
            currency = 'USD'          
        else:
            processor_shipment = ProcessorWarehouseShipment.objects.get(id=int(shipment_id))  
            customer = Customer.objects.get(id=int(processor_shipment.customer_id))     
            amount = float(processor_shipment.total_payment) 
            currency = 'USD'        

        # Create a Stripe Checkout session
        host = request.get_host()
        current_site = f"http://{host}"
        main_url = f'{current_site}/farmsmart/checkout/{shipment_id}/{type}/'
        user_email = user.email
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
                        'unit_amount': int(amount * 100), 
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
        
            success_url=main_url + "{CHECKOUT_SESSION_ID}" + "/",
            cancel_url=f"{request.build_absolute_uri('/payment-cancelled/')}",
        )
        return Response({"stripe_url":session.url})
    except Exception as e:
        response["status"], response["message"] = "500", f"500, {e}"
    return Response(response)


@api_view(("POST","GET"))
def checkout(request, pk, type, checkout_session_id):
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
        wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"  

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

