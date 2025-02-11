from django.shortcuts import render, HttpResponse
from rest_framework.decorators import api_view
# from rest_framework import PageNumberPagination
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.processor.models import Processor, ProcessorUser, Location, LinkGrowerToProcessor, GrowerShipment, ClassingReport, BaleReportFarmField, ProductionManagement, ShipmentManagement
from apps.processor.serializer import GrowerShipmentSerializer
from apps.storage.models import ShapeFileDataCo as StorageShapeFileDataCo, Storage
from apps.field.models import Field, FieldUpdated, ShapeFileDataCo, FieldActivity
from apps.field.serializers import FieldListSerializer
from apps.farms.models import Farm
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
# Create your views here.

def qr_code_view(pk):
    grower_shipment1 = GrowerShipment.objects.get(id =pk)
    processor_name = grower_shipment1.processor.entity_name
    grower_name = grower_shipment1.grower.name
    if grower_shipment1.storage_id == None:
        storage_name = 'N/A'
    else:
        storage_name = grower_shipment1.storage.storage_name
    if grower_shipment1.field.eschlon_id == None:
        echelon_number = "N/A"
    else:
        echelon_number = grower_shipment1.field.eschlon_id
    field_name = grower_shipment1.field.name
    crop_name = grower_shipment1.crop
    variety_name = grower_shipment1.variety
    sustainability = grower_shipment1.sustainability_score
    shipment_id = grower_shipment1.shipment_id
    module_tag_no = grower_shipment1.module_number

    if grower_shipment1.amount2 == None:
        a1 = grower_shipment1.amount
        unit_type1 = grower_shipment1.unit_type
        amount1 = a1 + ' ' + unit_type1
        amount2 = 'Null'
        # total = amount1 + ' LBS'
        total = str(grower_shipment1.total_amount) + ' LBS'
    else:
        a1 = grower_shipment1.amount
        a2 = grower_shipment1.amount2
        
        unit_type1 = grower_shipment1.unit_type
        unit_type2 = grower_shipment1.unit_type2

        amount1 = a1 + ' ' + unit_type1
        amount2 = a2 + ' ' + unit_type2
        total = str(grower_shipment1.total_amount) + ' LBS'

    shipment_date = grower_shipment1.date_time.strftime("%m-%d-%Y %H:%M:%S")
    datapy = {"amount1": amount1,"amount2": amount2,"total_amount": total,"shipment_id": shipment_id,"module_tag_no": module_tag_no,
    "processor_name": processor_name,"grower_name": grower_name,"storage_name": storage_name,"field_name": field_name,
    "crop_name": crop_name,"variety_name": variety_name,"echelon_number": echelon_number,"sustainability": sustainability,
    "shipment_date": shipment_date}
    data=json.dumps(datapy)
    # data = f"amount1: {amount1} \namount2: {amount2} \ntotal: {total} \nshipment_id: {shipment_id} \nmodule_tag_no: {module_tag_no} \nprocessor_name: {processor_name} \ngrower_name: {grower_name} \nstorage_name: {storage_name} \nfield_name: {field_name} \ncrop_name: {crop_name} \nvariety_name: {variety_name} \nechelon_number: {echelon_number} \nsustainability: {sustainability} \nshipment_date: {shipment_date}"
    img = make(data)
    img_name = 'qr' + str(time.time()) + '.png'
    img.save(settings.MEDIA_ROOT + '/' + img_name)
    
    img = open('media/{}'.format(img_name), 'rb')
    # response = FileResponse(img)
    return img_name



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
        processor_name = p.contact_name
        payload = {
            'id': user.id
        }
        token = jwt.encode(payload, 'secret', algorithm='HS256')
        data = {
            'jwt': token,
            'status': 1,
            "message":"Successfully logged in as processor",
            "type":"processor",
            "userid":user.id,
            "username":user.username,
            "processor_name":processor_name,
            "email":user.email,
        }
        return Response(data)
    
    elif user is not None and 'Grower' in user.get_role() and not user.is_superuser:
        payload = {
            'id': user.id
        }
        token = jwt.encode(payload, 'secret', algorithm='HS256')
        data = {
            'jwt': token,
            'status': 1,
            "message":"Successfully logged in as grower",
            "type":"grower",
            "userid":user.id,
            "username":user.username,
            "email":user.email,
        }
        return Response(data)
    # 23-05-23 Login For Tier2 Procesor
    elif user is not None and 'Processor2' in user.get_role() and user.is_processor2 and not user.is_superuser:
        payload = {
            'id': user.id
        }
        token = jwt.encode(payload, 'secret', algorithm='HS256')
        data = {
            'jwt': token,
            'status': 1,
            "message":"Successfully logged in as Tier 2 Processor",
            "type":"tier2_processor",
            "userid":user.id,
            "username":user.username,
            "email":user.email,
            "full_name":user.first_name,
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
    shipment_id = request.data['shipment_id']
    qr = qr_code_view(shipment_id)
    return Response({'data':qr})

    
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
            if crop == "RICE":
                status = ""
            if crop == "WHEAT":
                status = ""
            if crop == "COTTON":
                status = "APPROVED"
            
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

@api_view(('POST',))
def processor_inbound_list_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    user_email = user.email
    p = ProcessorUser.objects.get(contact_email=user_email)
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
        return Response({"data":serializer.data})

        # paginator = PageNumberPagination()
        # paginator.page_size = 10
        # result_page = paginator.paginate_queryset(inbound_shipment, request)
        # serializer = GrowerShipmentSerializer(result_page, many=True)
        # return paginator.get_paginated_response({"data":serializer.data})
        # lst = []
        # for i in range(len(inbound_shipment)):
        #     processor_shipment[i].id
        #     img = qr_code_view(inbound_shipment[i].id)


        #     if inbound_shipment[i].storage != None :
        #         storage_name = inbound_shipment[i].storage.storage_name
        #     else:
        #         storage_name = "N/A"

        #     if inbound_shipment[i].field != None :
        #         field_name = inbound_shipment[i].field.name
        #     else:
        #         field_name = "N/A"

        #     if inbound_shipment[i].echelon_id != None :
        #         echelon_id = inbound_shipment[i].echelon_id
        #     else:
        #         echelon_id = "N/A"

        #     data = {
        #         "message":"processor_inbound , with recordes",
        #         "type": "processor",
        #         "GrowerShipment_Id":inbound_shipment[i].id,
        #         "grower_name":inbound_shipment[i].grower.name,
        #         "date_time":inbound_shipment[i].date_time,
        #         "shipment_id":inbound_shipment[i].shipment_id,
        #         "status":inbound_shipment[i].status,
        #         "module_number":inbound_shipment[i].module_number,
        #         "storage_name":storage_name,
        #         "field_name":field_name,
        #         "amount":inbound_shipment[i].amount,
        #         "amount2":inbound_shipment[i].amount2,
        #         "unit_type":inbound_shipment[i].unit_type,
        #         "unit_type2":inbound_shipment[i].unit_type2,
        #         "total_amount":inbound_shipment[i].total_amount,
        #         "crop":inbound_shipment[i].crop,
        #         "variety":inbound_shipment[i].variety,
        #         "echelon_id":echelon_id,
        #         "sustainability_score":inbound_shipment[i].sustainability_score,
        #         # "qr url":'/processor/qr_code_view/{}'.format(grower_shipment[i].id),
        #         "qr_code":img,
        #     }
        #     lst.append(data)
        # return Response({'data':lst})
@api_view(('POST',))
def processor_inbound_list_search_api(request):
    userid = request.data['userid']
    search_keyword = request.data['search_keyword']
    user = User.objects.get(id=userid)
    user_email = user.email
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor_id = Processor.objects.get(id=p.processor_id).id
    processor_shipment = GrowerShipment.objects.filter(processor_id=processor_id)
    var_id = []
    for i in range(len(processor_shipment)):
        location = processor_shipment[i].location
        if location == None:
            var = processor_shipment[i].id
            var_id.append(var)

    inbound_shipment = GrowerShipment.objects.filter(id__in = var_id).filter(status="APPROVED").filter(shipment_id__icontains=search_keyword)
    serializer = GrowerShipmentSerializer(inbound_shipment, many=True)
    return Response({"data":serializer.data})


@api_view(('POST',))
def processor_upcomming_inbound_list_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    user_email = user.email
    p = ProcessorUser.objects.get(contact_email=user_email)
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
        return Response({"data":serializer.data})

        # paginator = PageNumberPagination()
        # paginator.page_size = 10
        # result_page = paginator.paginate_queryset(inbound_shipment, request)
        # serializer = GrowerShipmentSerializer(result_page, many=True)
        # return paginator.get_paginated_response({"data":serializer.data})


@api_view(('POST',))
def processor_upcomming_inbound_list_search_api(request):
    userid = request.data['userid']
    search_keyword = request.data['search_keyword']
    user = User.objects.get(id=userid)
    user_email = user.email
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor_id = Processor.objects.get(id=p.processor_id).id
    processor_shipment = GrowerShipment.objects.filter(processor_id=processor_id)
    var_id = []
    for i in range(len(processor_shipment)):
        location = processor_shipment[i].location
        if location == None:
            var = processor_shipment[i].id
            var_id.append(var)
   
    inbound_shipment = GrowerShipment.objects.filter(id__in = var_id).filter(status="").filter(shipment_id__icontains=search_keyword)
    serializer = GrowerShipmentSerializer(inbound_shipment, many=True)
    return Response({"data":serializer.data})




@api_view(('POST',))
def processor_inbound_view_api(request):
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
    if grower_shipment.received_amount == None :
        received_amount = "N/A"
    else:
        received_amount = grower_shipment.received_amount
    if grower_shipment.token_id == None :
        token_id = "N/A"
    else:
        token_id = grower_shipment.token_id
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
        "received_amount":received_amount,
        "token_id":token_id,
        "qr_code":img,
    }
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
    shipment_id = request.data['shipment_id']
    # 17-04-23
    userid = request.data['userid']
    shipment = GrowerShipment.objects.get(id=shipment_id)
    user = User.objects.get(id=userid)
    # 07-04-23 Log Table
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
    return Response({"message":"shipment is deleted"})
    

@api_view(('POST',))
def processor_linked_grower_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    user_email = user.email
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor_id = Processor.objects.get(id=p.processor_id).id
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
    return Response({'data':lst})

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

@api_view(('POST',))
def processor_receive_delivery_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    p = ProcessorUser.objects.get(contact_email=user.email)
    processor_id = Processor.objects.get(id=p.processor_id).id
    grower_id = request.data['grower_id']
    id_storage = request.data['storage_id']
    field_id = request.data['field_id']
    module_number = request.data['module_number']
    amount1 = request.data['amount1']
    amount2 = request.data['amount2']
    id_unit1 = request.data['type1']
    id_unit2 = request.data['type2']
    get_toatal = request.data['get_toatal']

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

    get_output = get_toatal

    if field_id:
        field = Field.objects.get(id=field_id)
        field_eschlon_id = field.eschlon_id
        crop = field.crop
        if crop == "RICE":
            status = ""
        if crop == "WHEAT":
            status = ""
        if crop == "COTTON":
            status = "APPROVED"
        variety = field.variety 
        shipment_id = generate_shipment_id()
        if id_storage == None :
            id_storage = None
            # storage_name = ''
        else:
            id_storage = id_storage
            # s = Storage.objects.get(id=id_storage)
            # storage_name = s.storage_name
        shipment = GrowerShipment(status=status,total_amount=get_output,unit_type2=id_unit2,amount2=amount2,shipment_id=shipment_id,processor_id=processor_id,grower_id=grower_id,storage_id=id_storage,field_id=field_id,crop=crop,variety=variety,amount=amount1,sustainability_score=surveyscore,echelon_id=field_eschlon_id,module_number=module_number,unit_type=id_unit1)
        shipment.save()
        # 17-04-23 Log Table
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
    return Response({"message":"recive delivery is added"})
    
@api_view(('POST',))
def processor_location_list_api(request):
    userid = request.data['userid']
    user = User.objects.get(id=userid)
    p = ProcessorUser.objects.get(contact_email=user.email)
    processor_id = Processor.objects.get(id=p.processor_id).id
    location = Location.objects.filter(processor_id=processor_id)
    lst=[]
    for i in location:
        data = {
            "location_name":i.name,
            "location_id":i.id
        }
        lst.append(data)
    return Response(lst)

@api_view(('POST',))
def processor_inbound_management_location_add_api(request):
    userid = request.data['userid']
    shipment_id = request.data['shipment_id']
    location_id = request.data['location_id']

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
        elif gpay.crop == "RICE" :
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
            elif get_crop == 'RICE':
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
    if field.crop == 'RICE' :
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
    
    elif field.crop == 'COTTON' :
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
        return [{'name':name}]


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
    if field.crop == 'RICE' :
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
        res = {"name":name,"crop":"RICE","shipmentLevelText":shipmentLevelText,"per_approved_shipment":per_approved_shipment,
               "per_disapproved_shipment":per_disapproved_shipment,"per_noStatus__shipment":per_noStatus__shipment,
               "shipment_wt": f'{sum(shipment_wt)} LBS',"shipment_count":count_shipment,"shipment_approved":count_approved_shipment,
               "shipment_disapproved":count_disapproved_shipment,"shipment_pending":count_noStatus__shipment,
               "shipment_delivered_wt":f'{sum(shipment_delivered_wt)} LBS',"shipment_paid_amount":shipment_paid_amount,
               "projected_yield":projected_yield,"actual_yield":actual_yield,"yield_delta":yield_delta,"g_payee_count":g_payee_count,
               "lien_holder_count":lien_holder_count,"payment_split_count":payment_split_count,"shipment_delivered_count":count_approved_shipment}
        return res
    elif field.crop == 'COTTON' :
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
        return [{'name':name}]
    
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
                                           'main_number':processor.main_number,'main_fax':processor.main_fax,
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
                                           'main_number':processor2.main_number,'main_fax':processor2.main_fax,
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
            data["app_version"] = "1.8"
            data["android_link"] = "https://play.google.com/store/apps/details?id=com.farmsmart"
            data["ios_link"] = "https://apps.apple.com/us/app/farmsmart-app/id6444606959"
            data["android_version"] = "10"
    except Exception as e :
        data = {"error":f"{e}"}
    return Response(data)