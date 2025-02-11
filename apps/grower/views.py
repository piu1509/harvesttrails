'''Classes and functions for Grower Dashboard'''
#pylint: disable=no-member
import os
import pandas as pd
from django.db.models import Avg, Count, Q
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from apps.grower.models import Consultant, Grower, GrowerChecklist
from apps.farms.models import Farm
from main.settings import MEDIA_ROOT, MEDIA_URL
from apps.accounts.models import User, Role, SubSuperUser
from apps.contracts.models import GrowerContracts, SignedContracts
from apps.field.models import Field,FieldUpdated,FieldActivity
from apps.field.models import ShapeFileDataCo as ShapeFile
from apps.growersurvey.models import TypeSurvey, QuestionSurvey, OptionSurvey, SustainabilitySurvey, NameSurvey
from django.shortcuts import HttpResponse
import csv
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.storage.models import *
from apps.processor.models import *
from apps.growerpayments.models import *
from datetime import datetime, timedelta, date
from django.db.models import Sum
from apps.growersurvey.models import *
import re
from django.db.models import ExpressionWrapper, F, FloatField
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

savings_types = ('Water Use Savings', 'Land Use Savings', 'Co2 Savings')

def grower_details_csv(request):
    # Create the HttpResponse object with the appropriate CSV header.
    filename = 'Grower Details.csv'
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
    )
    grower = Grower.objects.all().order_by('name')
    writer = csv.writer(response)
    writer.writerow(['Grower Name','Grower ID', 'Physical Address','Mailing Address','Phone','Email','Farm Name','Grower ID','Farm ID','FSA Number for Farm','Consultant Name','Consultant Phone','Consultant Email'])

    for i in grower:
        grower_id = i.id
        farm= Farm.objects.filter(grower_id=grower_id)
        obj = Grower.objects.get(id=grower_id)
        consultant_obj = obj.consultant.all()
        consultant_name = [i.name for i in consultant_obj]
        consultant_phone = [i.phone for i in consultant_obj]
        consultant_email = [i.email for i in consultant_obj]
        print(consultant_name)
        if len(farm) > 0:
            farm_name = [i.name for i in farm]
            farm_id = [i.id for i in farm]

            if len(farm_id) > 0 :
                field= Field.objects.filter(farm_id__in=farm_id)
                farm_fsa = [i.fsa_farm_number for i in field]

        
        else:
            farm_name = 'None'
            farm_id = 'None'
            farm_fsa = 'None'

        writer.writerow([i.name,i.id,i.physical_address(),i.mailing_address(),i.phone,
        i.email,farm_name,i.id,farm_id,farm_fsa,consultant_name,consultant_phone,consultant_email])

    return response


def checklist_comparison_update(request, pk):
    if request.user.is_authenticated:
        if 'Grower' in request.user.get_role() and not request.user.is_superuser:
            context = {}
            pass
        elif request.user.is_consultant:
            context = {}
            consultant_id = Consultant.objects.get(email=request.user.email).id
            grower = Grower.objects.filter(consultant=consultant_id)
            context['grower'] = grower
            # Grower Checklist =============
            grower_id = pk

            # at starting Grower Contract ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Grower_Contract').count() == 0:
                if SignedContracts.objects.filter(grower_id=grower_id).count() == 0:
                    GrowerChecklist(grower_id=pk, item_name='Grower_Contract',
                                    checkstatus=False, module='onboarding').save()
                else:
                    GrowerChecklist(grower_id=pk, item_name='Grower_Contract',
                                    checkstatus=True, module='onboarding').save()

                var = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Grower_Contract')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                onboarding_Grower_contract = grower_obj

            # UPDATE Grower Contract ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Grower_Contract').count() != 0:
                grower_checklist_obj = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Grower_Contract')
                grower_checklist_id = [obj.id for obj in grower_checklist_obj][0]
                grower_obj = GrowerChecklist.objects.get(id=grower_checklist_id)
                if SignedContracts.objects.filter(grower_id=grower_id).count() == 0:
                    grower_obj.checkstatus = False
                    grower_obj.save()
                else:
                    grower_obj.checkstatus = True
                    grower_obj.save()

                onboarding_Grower_contract = grower_obj

            # at starting Onboarding Survey 1 ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Onboarding_Survey_1').count() == 0:
                rice_id = TypeSurvey.objects.get(name='Entry Survey - Rice')
                cotton_id = TypeSurvey.objects.get(name='Entry Survey - Cotton')
                namesurvey_rice_id = NameSurvey.objects.get(typesurvey_id=rice_id)
                namesurvey_cotton_id = NameSurvey.objects.get(
                    typesurvey_id=cotton_id)
                rice_check = SustainabilitySurvey.objects.filter(
                    grower_id=grower_id).filter(namesurvey_id=namesurvey_rice_id)
                cotton_check = SustainabilitySurvey.objects.filter(
                    grower_id=grower_id).filter(namesurvey_id=namesurvey_cotton_id)
                if rice_check.count() == 0 or cotton_check.count() == 0:
                    GrowerChecklist(grower_id=pk, item_name='Onboarding_Survey_1',
                                    checkstatus=False, module='onboarding').save()
                else:
                    GrowerChecklist(grower_id=pk, item_name='Onboarding_Survey_1',
                                    checkstatus=True, module='onboarding').save()

                var = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Onboarding_Survey_1')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                onboarding_Grower_Onboarding_Survey_1 = grower_obj

            # UPDATE Onboarding Survey 1 ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Onboarding_Survey_1').count() != 0:
                rice_id = TypeSurvey.objects.get(name='Entry Survey - Rice')
                cotton_id = TypeSurvey.objects.get(name='Entry Survey - Cotton')
                namesurvey_rice_id = NameSurvey.objects.get(typesurvey_id=rice_id)
                namesurvey_cotton_id = NameSurvey.objects.get(
                    typesurvey_id=cotton_id)
                rice_check = SustainabilitySurvey.objects.filter(
                    grower_id=grower_id).filter(namesurvey_id=namesurvey_rice_id)
                cotton_check = SustainabilitySurvey.objects.filter(
                    grower_id=grower_id).filter(namesurvey_id=namesurvey_cotton_id)
                grower_checklist_obj = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Onboarding_Survey_1')
                grower_checklist_id = [obj.id for obj in grower_checklist_obj][0]
                grower_obj = GrowerChecklist.objects.get(id=grower_checklist_id)
                if rice_check.count() == 0 or cotton_check == 0:
                    grower_obj.checkstatus = False
                    grower_obj.save()
                else:
                    grower_obj.checkstatus = True
                    grower_obj.save()

                onboarding_Grower_Onboarding_Survey_1 = grower_obj

            # at starting FSA ID information ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='FSA_ID_information').count() == 0:
                field = Field.objects.filter(grower_id=grower_id)
                fsa_farm_number = [field.fsa_farm_number for field in field]

                fsa_field_number = [field.fsa_field_number for field in field]
                if field.count() !=0 :

                    if None in fsa_farm_number or None in fsa_field_number:
                        GrowerChecklist(grower_id=pk, item_name='FSA_ID_information',
                                        checkstatus=False, module='onboarding').save()

                    elif not None in fsa_farm_number and not None in fsa_field_number:
                        GrowerChecklist(grower_id=pk, item_name='FSA_ID_information',
                                        checkstatus=True, module='onboarding').save()
                else:
                    GrowerChecklist(grower_id=pk, item_name='FSA_ID_information',
                                        checkstatus=False, module='onboarding').save()
                var = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='FSA_ID_information')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                onboarding_Grower_FSA_ID_information = grower_obj

            # UPDATE FSA ID information ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='FSA_ID_information').count() != 0:
                field = Field.objects.filter(grower_id=grower_id)
                fsa_farm_number = [field.fsa_farm_number for field in field]
                fsa_field_number = [field.fsa_field_number for field in field]

                grower_checklist_obj = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='FSA_ID_information')
                grower_checklist_id = [obj.id for obj in grower_checklist_obj][0]
                grower_obj = GrowerChecklist.objects.get(id=grower_checklist_id)

                if field.count() !=0 :

                    if None in fsa_farm_number or None in fsa_field_number:
                        grower_obj.checkstatus = False
                        grower_obj.save()

                    if not None in fsa_farm_number and not None in fsa_field_number:
                        grower_obj.checkstatus = True
                        grower_obj.save()
                else:
                    grower_obj.checkstatus = False
                    grower_obj.save()

                onboarding_Grower_FSA_ID_information = grower_obj

            # # at starting Account information  ......
            # if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Account_information ').count() == 0:
            #     print('No Account information ')

            # # Update Account information  ......
            # if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Account_information ').count() != 0:
            #     print('Exsist Account information  ')

            # at starting Farm fully set up  ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Farm_fully_set_up').count() == 0:
                if Farm.objects.filter(grower_id=grower_id).count() == 0:
                    GrowerChecklist(grower_id=pk, item_name='Farm_fully_set_up',
                                    checkstatus=False, module='onboarding').save()
                else:

                    farm_list = Farm.objects.filter(grower_id=grower_id)
                    for farm in range(len(farm_list)):

                        name = farm_list[farm].name
                        grower = farm_list[farm].grower
                        area = farm_list[farm].area
                        land_type = farm_list[farm].land_type
                        state = farm_list[farm].state
                        county = farm_list[farm].county
                        village = farm_list[farm].village
                        town = farm_list[farm].town
                        street = farm_list[farm].street
                        zipcode = farm_list[farm].zipcode
                        print('name===', name)
                        if name != None and grower != None and area != None and land_type != None and state != None and county != None and village != None and town != None and street != None and zipcode != None:
                            GrowerChecklist(grower_id=pk, item_name='Farm_fully_set_up',
                                            checkstatus=True, module='onboarding').save()
                            break
                        else:
                            GrowerChecklist(grower_id=pk, item_name='Farm_fully_set_up',
                                            checkstatus=False, module='onboarding').save()
                            break

                var = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Farm_fully_set_up')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                onboarding_Grower_Farm_fully_set_up = grower_obj

            # Update Farm fully set up  ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Farm_fully_set_up').count() != 0:
                var = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Farm_fully_set_up')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                if Farm.objects.filter(grower_id=grower_id).count() == 0:
                    grower_obj.checkstatus = False
                    grower_obj.save()
                else:
                    farm_list = Farm.objects.filter(grower_id=grower_id)
                    for farm in range(len(farm_list)):

                        name = farm_list[farm].name
                        grower = farm_list[farm].grower
                        area = farm_list[farm].area
                        land_type = farm_list[farm].land_type
                        state = farm_list[farm].state
                        county = farm_list[farm].county
                        village = farm_list[farm].village
                        town = farm_list[farm].town
                        street = farm_list[farm].street
                        zipcode = farm_list[farm].zipcode

                        if name != None and grower != None and area != None and land_type != None and state != None and county != None and village != None and town != None and street != None and zipcode != None:
                            grower_obj.checkstatus = True
                            grower_obj.save()
                        else:
                            grower_obj.checkstatus = False
                            grower_obj.save()
                onboarding_Grower_Farm_fully_set_up = grower_obj

            # at starting Field fully set up  ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Field_fully_set_up').count() == 0:
                if Field.objects.filter(grower_id=grower_id).count() == 0:
                    GrowerChecklist(grower_id=pk, item_name='Field_fully_set_up',
                                    checkstatus=False, module='onboarding').save()

                else:
                    # GrowerChecklist(grower_id=pk,item_name='Field_fully_set_up',checkstatus=True,module='onboarding').save()

                    field_list = Field.objects.filter(grower_id=grower_id)
                    for field in range(len(field_list)):
                        name = field_list[field].name
                        farm = field_list[field].farm
                        grower = field_list[field].grower
                        acreage = field_list[field].acreage
                        fsa_farm_number = field_list[field].fsa_farm_number
                        fsa_field_number = field_list[field].fsa_field_number
                        crop = field_list[field].crop
                        variety = field_list[field].variety
                        if name != None and farm != None and grower != None and acreage != None and fsa_farm_number != None and fsa_field_number != None and crop != None and variety != None:
                            GrowerChecklist(grower_id=pk, item_name='Field_fully_set_up',
                                            checkstatus=True, module='onboarding').save()
                            break
                        else:
                            GrowerChecklist(grower_id=pk, item_name='Field_fully_set_up',
                                            checkstatus=False, module='onboarding').save()
                            break

                var = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Field_fully_set_up')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                onboarding_Grower_Field_fully_set_up = grower_obj

            # UPDATE Field fully set up ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Field_fully_set_up').count() != 0:
                var = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Field_fully_set_up')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                if Field.objects.filter(grower_id=grower_id).count() == 0:
                    grower_obj.checkstatus = False
                    grower_obj.save()
                else:
                    field_list = Field.objects.filter(grower_id=grower_id)
                    for field in range(len(field_list)):
                        name = field_list[field].name
                        farm = field_list[field].farm
                        grower = field_list[field].grower
                        acreage = field_list[field].acreage
                        fsa_farm_number = field_list[field].fsa_farm_number
                        fsa_field_number = field_list[field].fsa_field_number
                        crop = field_list[field].crop
                        variety = field_list[field].variety
                        if name != None and farm != None and grower != None and acreage != None and fsa_farm_number != None and fsa_field_number != None and crop != None and variety != None:
                            grower_obj.checkstatus = True
                            grower_obj.save()
                        else:
                            grower_obj.checkstatus = False
                            grower_obj.save()

                onboarding_Grower_Field_fully_set_up = grower_obj

            # at starting .....
            # Shapefile upload for all fields  ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Shapefile_upload_for_all_fields').count() == 0:
                field_id = Field.objects.filter(grower_id=grower_id)
                shp = ShapeFile.objects.filter(field_id__in=field_id)
                if field_id.count() == shp.count() and shp.count() > 0:
                    GrowerChecklist(grower_id=pk, item_name='Shapefile_upload_for_all_fields',
                                    checkstatus=True, module='onboarding').save()
                else:
                    GrowerChecklist(grower_id=pk, item_name='Shapefile_upload_for_all_fields',
                                    checkstatus=False, module='onboarding').save()

                var = GrowerChecklist.objects.filter(grower_id=grower_id).filter(
                    item_name='Shapefile_upload_for_all_fields')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                onboarding_Grower_Shapefile_upload_for_all_fields = grower_obj

            # at exsiting ......
            # Shapefile upload for all fields  ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Shapefile_upload_for_all_fields').count() != 0:
                field_id = Field.objects.filter(grower_id=grower_id)
                shp = ShapeFile.objects.filter(field_id__in=field_id)
                var = GrowerChecklist.objects.filter(grower_id=grower_id).filter(
                    item_name='Shapefile_upload_for_all_fields')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                if field_id.count() == shp.count() and shp.count() > 0:
                    grower_obj.checkstatus = True
                    grower_obj.save()
                else:
                    grower_obj.checkstatus = False
                    grower_obj.save()

                onboarding_Grower_Shapefile_upload_for_all_fields = grower_obj

            # For all check ....
            all_check = GrowerChecklist.objects.filter(grower_id=grower_id).filter(
                checkstatus=False).filter(module='onboarding').count()
            print(all_check)
            flag = ''
            if all_check == 0:
                flag = 'True'
            # end .....
            context['grower'] = Grower.objects.filter(id=pk)
            return render(request,'grower/unique_checklist_comparison.html',context)

        elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            # Grower Checklist =============
            context ={}
            grower_id = pk

            # at starting Grower Contract ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Grower_Contract').count() == 0:
                if SignedContracts.objects.filter(grower_id=grower_id).count() == 0:
                    GrowerChecklist(grower_id=pk, item_name='Grower_Contract',
                                    checkstatus=False, module='onboarding').save()
                else:
                    GrowerChecklist(grower_id=pk, item_name='Grower_Contract',
                                    checkstatus=True, module='onboarding').save()

                var = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Grower_Contract')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                onboarding_Grower_contract = grower_obj

            # UPDATE Grower Contract ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Grower_Contract').count() != 0:
                grower_checklist_obj = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Grower_Contract')
                grower_checklist_id = [obj.id for obj in grower_checklist_obj][0]
                grower_obj = GrowerChecklist.objects.get(id=grower_checklist_id)
                if SignedContracts.objects.filter(grower_id=grower_id).count() == 0:
                    grower_obj.checkstatus = False
                    grower_obj.save()
                else:
                    grower_obj.checkstatus = True
                    grower_obj.save()

                onboarding_Grower_contract = grower_obj

            # at starting Onboarding Survey 1 ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Onboarding_Survey_1').count() == 0:
                rice_id = TypeSurvey.objects.get(name='Entry Survey - Rice')
                cotton_id = TypeSurvey.objects.get(name='Entry Survey - Cotton')
                namesurvey_rice_id = NameSurvey.objects.get(typesurvey_id=rice_id)
                namesurvey_cotton_id = NameSurvey.objects.get(
                    typesurvey_id=cotton_id)
                rice_check = SustainabilitySurvey.objects.filter(
                    grower_id=grower_id).filter(namesurvey_id=namesurvey_rice_id)
                cotton_check = SustainabilitySurvey.objects.filter(
                    grower_id=grower_id).filter(namesurvey_id=namesurvey_cotton_id)
                if rice_check.count() == 0 or cotton_check.count() == 0:
                    GrowerChecklist(grower_id=pk, item_name='Onboarding_Survey_1',
                                    checkstatus=False, module='onboarding').save()
                else:
                    GrowerChecklist(grower_id=pk, item_name='Onboarding_Survey_1',
                                    checkstatus=True, module='onboarding').save()

                var = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Onboarding_Survey_1')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                onboarding_Grower_Onboarding_Survey_1 = grower_obj

            # UPDATE Onboarding Survey 1 ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Onboarding_Survey_1').count() != 0:
                rice_id = TypeSurvey.objects.get(name='Entry Survey - Rice')
                cotton_id = TypeSurvey.objects.get(name='Entry Survey - Cotton')
                namesurvey_rice_id = NameSurvey.objects.get(typesurvey_id=rice_id)
                namesurvey_cotton_id = NameSurvey.objects.get(
                    typesurvey_id=cotton_id)
                rice_check = SustainabilitySurvey.objects.filter(
                    grower_id=grower_id).filter(namesurvey_id=namesurvey_rice_id)
                cotton_check = SustainabilitySurvey.objects.filter(
                    grower_id=grower_id).filter(namesurvey_id=namesurvey_cotton_id)
                grower_checklist_obj = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Onboarding_Survey_1')
                grower_checklist_id = [obj.id for obj in grower_checklist_obj][0]
                grower_obj = GrowerChecklist.objects.get(id=grower_checklist_id)
                if rice_check.count() == 0 or cotton_check == 0:
                    grower_obj.checkstatus = False
                    grower_obj.save()
                else:
                    grower_obj.checkstatus = True
                    grower_obj.save()

                onboarding_Grower_Onboarding_Survey_1 = grower_obj

            # at starting FSA ID information ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='FSA_ID_information').count() == 0:
                field = Field.objects.filter(grower_id=grower_id)
                fsa_farm_number = [field.fsa_farm_number for field in field]

                fsa_field_number = [field.fsa_field_number for field in field]
                if field.count() !=0 :

                    if None in fsa_farm_number or None in fsa_field_number:
                        GrowerChecklist(grower_id=pk, item_name='FSA_ID_information',
                                        checkstatus=False, module='onboarding').save()

                    elif not None in fsa_farm_number and not None in fsa_field_number:
                        GrowerChecklist(grower_id=pk, item_name='FSA_ID_information',
                                        checkstatus=True, module='onboarding').save()
                else:
                    GrowerChecklist(grower_id=pk, item_name='FSA_ID_information',
                                        checkstatus=False, module='onboarding').save()
                var = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='FSA_ID_information')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                onboarding_Grower_FSA_ID_information = grower_obj

            # UPDATE FSA ID information ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='FSA_ID_information').count() != 0:
                field = Field.objects.filter(grower_id=grower_id)
                fsa_farm_number = [field.fsa_farm_number for field in field]
                fsa_field_number = [field.fsa_field_number for field in field]

                grower_checklist_obj = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='FSA_ID_information')
                grower_checklist_id = [obj.id for obj in grower_checklist_obj][0]
                grower_obj = GrowerChecklist.objects.get(id=grower_checklist_id)

                if field.count() !=0 :

                    if None in fsa_farm_number or None in fsa_field_number:
                        grower_obj.checkstatus = False
                        grower_obj.save()

                    if not None in fsa_farm_number and not None in fsa_field_number:
                        grower_obj.checkstatus = True
                        grower_obj.save()
                else:
                    grower_obj.checkstatus = False
                    grower_obj.save()

                onboarding_Grower_FSA_ID_information = grower_obj

            # # at starting Account information  ......
            # if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Account_information ').count() == 0:
            #     print('No Account information ')

            # # Update Account information  ......
            # if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Account_information ').count() != 0:
            #     print('Exsist Account information  ')

            # at starting Farm fully set up  ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Farm_fully_set_up').count() == 0:
                if Farm.objects.filter(grower_id=grower_id).count() == 0:
                    GrowerChecklist(grower_id=pk, item_name='Farm_fully_set_up',
                                    checkstatus=False, module='onboarding').save()
                else:

                    farm_list = Farm.objects.filter(grower_id=grower_id)
                    for farm in range(len(farm_list)):

                        name = farm_list[farm].name
                        grower = farm_list[farm].grower
                        area = farm_list[farm].area
                        land_type = farm_list[farm].land_type
                        state = farm_list[farm].state
                        county = farm_list[farm].county
                        village = farm_list[farm].village
                        town = farm_list[farm].town
                        street = farm_list[farm].street
                        zipcode = farm_list[farm].zipcode
                        print('name===', name)
                        if name != None and grower != None and area != None and land_type != None and state != None and county != None and village != None and town != None and street != None and zipcode != None:
                            GrowerChecklist(grower_id=pk, item_name='Farm_fully_set_up',
                                            checkstatus=True, module='onboarding').save()
                            break
                        else:
                            GrowerChecklist(grower_id=pk, item_name='Farm_fully_set_up',
                                            checkstatus=False, module='onboarding').save()
                            break

                var = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Farm_fully_set_up')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                onboarding_Grower_Farm_fully_set_up = grower_obj

            # Update Farm fully set up  ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Farm_fully_set_up').count() != 0:
                var = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Farm_fully_set_up')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                if Farm.objects.filter(grower_id=grower_id).count() == 0:
                    grower_obj.checkstatus = False
                    grower_obj.save()
                else:
                    farm_list = Farm.objects.filter(grower_id=grower_id)
                    for farm in range(len(farm_list)):

                        name = farm_list[farm].name
                        grower = farm_list[farm].grower
                        area = farm_list[farm].area
                        land_type = farm_list[farm].land_type
                        state = farm_list[farm].state
                        county = farm_list[farm].county
                        village = farm_list[farm].village
                        town = farm_list[farm].town
                        street = farm_list[farm].street
                        zipcode = farm_list[farm].zipcode

                        if name != None and grower != None and area != None and land_type != None and state != None and county != None and village != None and town != None and street != None and zipcode != None:
                            grower_obj.checkstatus = True
                            grower_obj.save()
                        else:
                            grower_obj.checkstatus = False
                            grower_obj.save()
                onboarding_Grower_Farm_fully_set_up = grower_obj

            # at starting Field fully set up  ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Field_fully_set_up').count() == 0:
                if Field.objects.filter(grower_id=grower_id).count() == 0:
                    GrowerChecklist(grower_id=pk, item_name='Field_fully_set_up',
                                    checkstatus=False, module='onboarding').save()

                else:
                    # GrowerChecklist(grower_id=pk,item_name='Field_fully_set_up',checkstatus=True,module='onboarding').save()

                    field_list = Field.objects.filter(grower_id=grower_id)
                    for field in range(len(field_list)):
                        name = field_list[field].name
                        farm = field_list[field].farm
                        grower = field_list[field].grower
                        acreage = field_list[field].acreage
                        fsa_farm_number = field_list[field].fsa_farm_number
                        fsa_field_number = field_list[field].fsa_field_number
                        crop = field_list[field].crop
                        variety = field_list[field].variety
                        if name != None and farm != None and grower != None and acreage != None and fsa_farm_number != None and fsa_field_number != None and crop != None and variety != None:
                            GrowerChecklist(grower_id=pk, item_name='Field_fully_set_up',
                                            checkstatus=True, module='onboarding').save()
                            break
                        else:
                            GrowerChecklist(grower_id=pk, item_name='Field_fully_set_up',
                                            checkstatus=False, module='onboarding').save()
                            break

                var = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Field_fully_set_up')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                onboarding_Grower_Field_fully_set_up = grower_obj

            # UPDATE Field fully set up ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Field_fully_set_up').count() != 0:
                var = GrowerChecklist.objects.filter(
                    grower_id=grower_id).filter(item_name='Field_fully_set_up')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                if Field.objects.filter(grower_id=grower_id).count() == 0:
                    grower_obj.checkstatus = False
                    grower_obj.save()
                else:
                    field_list = Field.objects.filter(grower_id=grower_id)
                    for field in range(len(field_list)):
                        name = field_list[field].name
                        farm = field_list[field].farm
                        grower = field_list[field].grower
                        acreage = field_list[field].acreage
                        fsa_farm_number = field_list[field].fsa_farm_number
                        fsa_field_number = field_list[field].fsa_field_number
                        crop = field_list[field].crop
                        variety = field_list[field].variety
                        if name != None and farm != None and grower != None and acreage != None and fsa_farm_number != None and fsa_field_number != None and crop != None and variety != None:
                            grower_obj.checkstatus = True
                            grower_obj.save()
                        else:
                            grower_obj.checkstatus = False
                            grower_obj.save()

                onboarding_Grower_Field_fully_set_up = grower_obj

            # at starting .....
            # Shapefile upload for all fields  ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Shapefile_upload_for_all_fields').count() == 0:
                field_id = Field.objects.filter(grower_id=grower_id)
                shp = ShapeFile.objects.filter(field_id__in=field_id)
                if field_id.count() == shp.count() and shp.count() > 0:
                    GrowerChecklist(grower_id=pk, item_name='Shapefile_upload_for_all_fields',
                                    checkstatus=True, module='onboarding').save()
                else:
                    GrowerChecklist(grower_id=pk, item_name='Shapefile_upload_for_all_fields',
                                    checkstatus=False, module='onboarding').save()

                var = GrowerChecklist.objects.filter(grower_id=grower_id).filter(
                    item_name='Shapefile_upload_for_all_fields')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                onboarding_Grower_Shapefile_upload_for_all_fields = grower_obj

            # at exsiting ......
            # Shapefile upload for all fields  ......
            if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Shapefile_upload_for_all_fields').count() != 0:
                field_id = Field.objects.filter(grower_id=grower_id)
                shp = ShapeFile.objects.filter(field__in=field_id)
                var = GrowerChecklist.objects.filter(grower_id=grower_id).filter(
                    item_name='Shapefile_upload_for_all_fields')
                var_id = [i.id for i in var][0]
                grower_obj = GrowerChecklist.objects.get(id=var_id)
                if field_id.count() == shp.count() and shp.count() > 0:
                    grower_obj.checkstatus = True
                    grower_obj.save()
                else:
                    grower_obj.checkstatus = False
                    grower_obj.save()

                onboarding_Grower_Shapefile_upload_for_all_fields = grower_obj

            # For all check ....
            all_check = GrowerChecklist.objects.filter(grower_id=grower_id).filter(
                checkstatus=False).filter(module='onboarding').count()
            print(all_check)
            flag = ''
            if all_check == 0:
                flag = 'True'
            # end .....
            context['grower'] = Grower.objects.filter(id=pk)
        return render(request,'grower/unique_checklist_comparison.html',context)
    else:
        return redirect('login')


def checklist_comparison(request):
    if request.user.is_authenticated:
        if 'Grower' in request.user.get_role() and not request.user.is_superuser:
            context = {}
            pass
        elif request.user.is_consultant:
            context = {}
            consultant_id = Consultant.objects.get(email=request.user.email).id
            grower = Grower.objects.filter(consultant=consultant_id)
            paginator = Paginator(grower, 100)  
            page_number = request.GET.get('page')
            grower_page = paginator.get_page(page_number)
            context['growers'] = grower_page
        elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            context = {}
            grower = Grower.objects.all().order_by('name')
            paginator = Paginator(grower, 100)  
            page_number = request.GET.get('page')
            grower_page = paginator.get_page(page_number)
            context['growers'] = grower_page
        return render(request,'grower/checklist_comparison.html',context)
    else:
        return redirect('login')


class GorwerDashboardViewMain(View):
    '''For displaying main page of Grower Dashboard'''

    def get(self, request):
        '''Default function for get request'''

        if request.user.is_superuser :
            grower_names = Grower.objects.values_list(
                'name', flat=True).distinct().order_by('name')

        if request.user.is_consultant:
            consultant_id = Consultant.objects.get(email=self.request.user.email).id
            data = Grower.objects.raw("select id,grower_id from grower_grower_consultant where consultant_id=%s",[consultant_id])
            grower_ids = [id.grower_id for id in data]
            grower_names = Grower.objects.filter(id__in=grower_ids)
            #grower_names = [request.user.grower.name]

        return render(request, 'grower/grower_dashboard_main.html', {
            'grower_names': grower_names, 'savings_types': savings_types})


class GorwerDashboardView1(View):
    '''For displaying second detailed chart view of Grower Dashboard'''

    def get(self, request):
        '''Default function for get request'''

        if request.user.is_superuser :
            grower_names = Grower.objects.values_list(
                'name', flat=True).distinct().order_by('name')
            default_grower = grower_names[0]
        else:
            grower_names = [request.user.grower.name]
            default_grower = grower_names[0]
        if request.GET.get('growername') is not None:
            default_grower = request.GET.get('growername')
        grower_id = Grower.objects.get(name=default_grower).pk
        state_names = Farm.objects.values_list(
            'state', flat=True).distinct().order_by('state')
        farm_names = Farm.objects.filter(grower_id=grower_id).values_list(
            'name', flat=True).distinct().order_by('name')
        field_names = Field.objects.filter(grower_id=grower_id).values_list(
            'name', flat=True).distinct().order_by('name')

        cultivation_year = Farm.objects.values_list('cultivation_year',
            flat=True).distinct().order_by('cultivation_year')
        excel_file_path = os.path.join(MEDIA_URL, 'Chart Data.xlsx')
        return render(request, 'grower/grower_dashboard1.html',
                      {'grower_names': grower_names,
                       'state_names': state_names,
                       'farm_names': farm_names,
                       'field_names':  field_names,
                       "cultivation_year": cultivation_year,
                       'excel_file_path': excel_file_path,
                       'savings_types': savings_types,
                       'default_grower': default_grower})


class GorwerDashboardView2(View):
    '''For displaying detailed chart view of Grower Dashboard'''

    def get(self, request):
        '''Default function for get request'''

        if request.user.is_superuser:
            grower_names = Grower.objects.values_list(
                'name', flat=True).distinct().order_by('name')
            default_grower = grower_names[0]
        else:
            grower_names = [request.user.grower.name]
            default_grower = grower_names[0]
        if request.GET.get('growername') is not None:
            default_grower = request.GET.get('growername')
        grower_id = Grower.objects.get(name=default_grower).pk
        state_names = Farm.objects.values_list(
            'state', flat=True).distinct().order_by('state')
        farm_names = Farm.objects.filter(grower_id=grower_id).values_list(
            'name', flat=True).distinct().order_by('name')
        field_names = Field.objects.filter(grower_id=grower_id).values_list(
            'name', flat=True).distinct().order_by('name')

        cultivation_year = Farm.objects.values_list('cultivation_year',
            flat=True).distinct().order_by('cultivation_year')
        excel_file_path = os.path.join(MEDIA_URL, 'Chart Data.xlsx')
        return render(request, 'grower/grower_dashboard2.html',
                      {'grower_names': grower_names,
                       'state_names': state_names,
                       'farm_names': farm_names,
                       'field_names':  field_names,
                       "cultivation_year": cultivation_year,
                       'excel_file_path': excel_file_path,
                       'savings_types': savings_types,
                       'default_grower': default_grower})


def chart1(request):
    '''For serving data for "Most Savings Variety" chart in customchart.js'''

    grower_name = request.GET.get('growername')
    savings_type = request.GET.get('savings')
    if savings_type == 'Water':
        savings = 'Pounds / Acre'
    elif savings_type == 'Land':
        savings = 'Land savings %'
    else:
        savings = 'Co2 Emission savings %'

    years = request.GET.get('year', None)
    if years == '':
        years = None
    elif years is not None:
        years = years.split(",")

    farm_names = request.GET.get('farmname', None)

    if farm_names == '':
        farm_names = None
    elif farm_names is not None:
        farm_names = farm_names.split(",")

    field_names = request.GET.get('fieldname', None)

    if field_names == '':
        field_names = None
    elif field_names is not None:
        field_names = field_names.split(",")

    state_names = request.GET.get('statename', None)
    if state_names == '':
        state_names = None
    elif state_names is not None:
        state_names = state_names.split(",")

    if years is None and farm_names is None and \
            field_names is None and state_names is None:

        obj = Field.objects.exclude(Q (variety__isnull=True) & \
            Q(acreage__isnull=True)).filter(grower=Grower.objects.
            get(name=grower_name)).values_list('variety').\
            annotate(Avg('acreage'))

        label_data = []
        value_data = []
        for i in obj:
            label_data.append(str(i[0]))
            value_data.append(float(i[1]))
        return JsonResponse(data={
            'label': label_data,
            'data': value_data,
            'year': 2022,
            'savings': savings,
        })

    df_chart = pd.DataFrame(
        columns=['Variety', 'Acreage', 'Field', 'Farm', 'State', 'Year'])
    farm_obj = Farm.objects
    obj = Field.objects.filter(
        grower=Grower.objects.get(name=grower_name)).\
        exclude(variety__isnull=True).exclude(acreage__isnull=True)
    for i in obj:
        new_row = {"Variety": i.variety,
                   "Acreage": i.acreage,
                   "Field": i.name,
                   "Farm": i.farm,
                   "State": farm_obj.get(name=i.farm).state,
                   "Year": farm_obj.get(name=i.farm).cultivation_year,
                   }
        # append row to the dataframe
        df_chart = df_chart.append(new_row, ignore_index=True)
    df_chart = df_chart.astype({'Variety': str, 'Acreage': float, 'Field': str,
        'Farm': str, 'State': str, 'Year': str})

    if years is not None:
        filt_year = df_chart['Year'].str.contains("|".join(years))
    else:
        filt_year = True

    if farm_names is not None:
        filt_farm = df_chart['Farm'].str.contains("|".join(farm_names))
    else:
        filt_farm = True
    if field_names is not None:
        filt_field = df_chart['Field'].str.contains("|".join(field_names))
    else:
        filt_field = True

    if state_names is not None:
        filt_state = df_chart['State'].str.contains("|".join(state_names))
    else:
        filt_state = True
        # Data fram for filtered data
    df_filt = df_chart[filt_year & filt_state & filt_farm & filt_field].copy()

    label_data = list(df_filt['Variety'].unique())

    value_data = []
    for i in label_data:
        temp_df = df_filt[df_filt['Variety'] == i]
        value_data.append(temp_df['Acreage'].mean())

    df_filt.to_excel(os.path.join(MEDIA_ROOT, 'Chart Data.xlsx'), index=None)

    return JsonResponse(data={
        'label': label_data,
        'data': value_data,
        'savings': savings,
    })


def chart2(request):
    '''Function for Highest Yield Variety Chart in customchart.js
    Created for JS get request '''

    grower_name = request.GET.get('growername')

    obj = Field.objects.filter(grower=Grower.objects.get(name=grower_name))\


    obj = Field.objects.filter(
        grower=Grower.objects.get(name=grower_name)).\
        exclude(variety__isnull=True).exclude(yield_per_acre__isnull=True)\
        .values_list('variety').annotate(Avg('yield_per_acre'))

    label_data = []
    value_data = []
    for i in obj:
        label_data.append(str(i[0]))
        value_data.append(float(i[1]))
    return JsonResponse(data={
        'label': label_data,
        'data': value_data,
        'year': 2021,
        })


def chart2_detail(request):
    '''Function for detailed view of Highest Yield Variety Chart
    Created for JS get request '''

    grower_name = request.GET.get('growername')

    years = request.GET.get('year', None)
    if years == '':
        years = None
    elif years is not None:
        years = years.split(",")

    farm_names = request.GET.get('farmname', None)

    if farm_names == '':
        farm_names = None
    elif farm_names is not None:
        farm_names = farm_names.split(",")

    field_names = request.GET.get('fieldname', None)

    if field_names == '':
        field_names = None
    elif field_names is not None:
        field_names = field_names.split(",")

    state_names = request.GET.get('statename', None)
    if state_names == '':
        state_names = None
    elif state_names is not None:
        state_names = state_names.split(",")

    df_chart = pd.DataFrame(
        columns=['Variety', 'Yield per acre', 'Field', 'Farm', 'State', 'Year'])
    farm_obj = Farm.objects
    obj = Field.objects.filter(
        grower=Grower.objects.get(name=grower_name)).\
        exclude(variety__isnull=True).exclude(yield_per_acre__isnull=True)
    for i in obj:
        new_row = {"Variety": i.variety,
                   "Yield per acre": i.yield_per_acre,
                   "Field": i.name,
                   "Farm": i.farm,
                   "State": farm_obj.get(name=i.farm).state,
                   "Year": farm_obj.get(name=i.farm).cultivation_year,
                   }
        # append row to the dataframe
        df_chart = df_chart.append(new_row, ignore_index=True)
        df_chart = df_chart.astype({'Variety': str, 'Yield per acre': float, 'Field': str,
                                    'Farm': str, 'State': str, 'Year': str})

    if years is not None:
        filt_year = df_chart['Year'].str.contains("|".join(years))
    else:
        filt_year = df_chart['Year'] != None

    if farm_names is not None:
        filt_farm = df_chart['Farm'].str.contains("|".join(farm_names))
    else:
        filt_farm = df_chart['Farm'] != None

    if field_names is not None:
        filt_field = df_chart['Field'].str.contains("|".join(field_names))
    else:
        filt_field = df_chart['Field'] != None

    if state_names is not None:
        filt_state = df_chart['State'].str.contains("|".join(state_names))
    else:
        filt_state = df_chart['Field'] != None

    # Data frame for filtered data
    df_filt = df_chart[filt_year & filt_state & filt_farm & filt_field].copy()

    label_data = list(df_filt['Variety'].unique())

    value_data = []
    for i in label_data:
        temp_df = df_filt[df_filt['Variety'] == i]
        value_data.append(temp_df['Yield per acre'].mean())

    df_filt.to_excel(os.path.join(MEDIA_ROOT, 'Chart Data.xlsx'), index=None)

    return JsonResponse(data={
        'label': label_data,
        'data': value_data,

    })


def chart3(request):
    '''Most savings across by region customchart.js
    Created for JS get request '''

    #grower_name = request.GET.get('growername')
    savings_type = request.GET.get('savings')
    if savings_type == 'Water':
        savings = 'Pounds / Acre'
    elif savings_type == 'Land':
        savings = 'Land savings %'
    else:
        savings = 'Co2 Emission savings %'

    obj = Grower.objects.values_list('state1').annotate(Count('name'))
    label_data = []
    value_data = []
    for i in obj:
        if i[0] is not None:
            label_data.append(str(i[0]))
            value_data.append(int(i[1]))

    return JsonResponse(data={
        'label': label_data,
        'data': value_data,
        'savings': savings,
    })


def getConsultangts(request):
    uconsultant = User.objects.all()
    return render(request, 'accounts/account_create.html', {'ucon':uconsultant})


@login_required()
def grower_dashboard_com(request,web_get_grower) :
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        growers = Grower.objects.all().order_by('name')
        context['growers'] = growers
        
        if web_get_grower != 'all':
            chat_field_id = request.POST.get('chat_field_id')
            get_grower = Grower.objects.get(id=web_get_grower)
            context['growers'] = Grower.objects.filter(id=web_get_grower)
            grower_id = web_get_grower
            context['select_get_grower_id'] = get_grower.id
            context['select_get_grower_name'] = get_grower.name
            context['show_grower'] = get_grower.name


            grower_farms = get_Grower_Farms(grower_id)
            context['grower_farms'] = grower_farms
            grower_fields = get_Grower_Fields(grower_id)
            context['grower_fields'] = grower_fields
            grower_storages = get_Grower_Stogares(grower_id)
            context['grower_storages'] = grower_storages
            # grower_payments
            grower_payments = get_Grower_Payments(grower_id)
            context['grower_payments'] = grower_payments
            if len(grower_fields) > 0  and chat_field_id == None :
                context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart(grower_fields.first().id)
                context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart(grower_fields.first().id)
                context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details(grower_fields.first().id)
                # grower_surveys
                context['grower_surveys'] = grower_Field_Surveys_Details(grower_fields.first().id)
            elif len(grower_fields) == 0  and chat_field_id == None :
                context['grower_Field_Vegetation_Chart'] = None
                context['grower_Field_Shipment_Chart'] = None
                context['grower_Field_Shipment_Details'] = None
                # grower_surveys
                context['grower_surveys'] = None
            else:
                if chat_field_id :
                    check_field = Field.objects.filter(id=chat_field_id,grower_id=get_grower)
                    if len(check_field) == 1 :
                        context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart(chat_field_id)
                        context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart(chat_field_id)
                        context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details(chat_field_id)
                        context['grower_surveys'] = grower_Field_Surveys_Details(chat_field_id)
                        context['selcted_filed'] = Field.objects.get(id=chat_field_id)
            if 'grower_Field_Vegetation_Chart' in context and context['grower_Field_Vegetation_Chart']:
                all_points = list(context['grower_Field_Vegetation_Chart'][0].values())
                all_points.pop(0)
                converted_list = [ int(i) for i in all_points]
                sorted_list = sorted(converted_list, reverse=True)
                min_break_point = int(sorted_list[1] * 1.1)
                max_break_point = int(sorted_list[0] * 0.9)
                context['break_startValue'] = min_break_point 
                context['break_endValue'] = max_break_point 
                context['maximum_y'] = sorted_list[0] + 1000
            else:
                context['break_startValue'] = None
                context['break_endValue'] = None 
                context['maximum_y'] = None
        # /all/    
        else:
            if request.method == 'POST' :
                get_grower = request.POST.get('get_grower')
                chat_field_id = request.POST.get('chat_field_id')
                context['show_grower'] = get_grower
                
                # Dropdown Grower Search
                if get_grower and get_grower != '' :
                    check_grower = Grower.objects.filter(id = int(get_grower))
                    
                    if check_grower.exists() :
                        grower_id = check_grower.first().id
                        context['select_get_grower_id'] = grower_id
                        context['select_get_grower_name'] = check_grower.first().name
                        grower_farms = get_Grower_Farms(grower_id)
                        context['grower_farms'] = grower_farms
                        grower_fields = get_Grower_Fields(grower_id)
                        context['grower_fields'] = grower_fields
                        grower_storages = get_Grower_Stogares(grower_id)
                        context['grower_storages'] = grower_storages
                        # grower_payments
                        grower_payments = get_Grower_Payments(grower_id)
                        context['grower_payments'] = grower_payments
        
                        if len(grower_fields) > 0  and chat_field_id == None :
                            context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart(grower_fields.first().id)
                            context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart(grower_fields.first().id)
                            context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details(grower_fields.first().id)
                            # grower_surveys
                            context['grower_surveys'] = grower_Field_Surveys_Details(grower_fields.first().id)
                        elif len(grower_fields) == 0  and chat_field_id == None :
                            context['grower_Field_Vegetation_Chart'] = None
                            context['grower_Field_Shipment_Chart'] = None
                            context['grower_Field_Shipment_Details'] = None
                            # grower_surveys
                            context['grower_surveys'] = None
                        else:
                            if chat_field_id :
                                check_field = Field.objects.filter(id=chat_field_id,grower_id=get_grower)
                                if len(check_field) == 1 :
                                    context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart(chat_field_id)
                                    context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart(chat_field_id)
                                    context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details(chat_field_id)
                                    context['grower_surveys'] = grower_Field_Surveys_Details(chat_field_id)
                                    context['selcted_filed'] = Field.objects.get(id=chat_field_id)
                        
                        if 'grower_Field_Vegetation_Chart' in context and context['grower_Field_Vegetation_Chart']:
                            all_points = list(context['grower_Field_Vegetation_Chart'][0].values())
                            all_points.pop(0)
                            converted_list = [ int(i) for i in all_points]
                            sorted_list = sorted(converted_list, reverse=True)
                            min_break_point = int(sorted_list[1] * 1.1)
                            max_break_point = int(sorted_list[0] * 0.9)
                            context['break_startValue'] = min_break_point 
                            context['break_endValue'] = max_break_point 
                            context['maximum_y'] = sorted_list[0] + 1000
                        else:
                            context['break_startValue'] = None
                            context['break_endValue'] = None 
                            context['maximum_y'] = None 
                    else:
                        messages.error(request,f' {len(check_grower)} Growers found with same name !!')
                else:
                    pass
            
        return render(request, 'grower/grower_dashboard_com.html', context)
    
    elif 'Grower' in request.user.get_role() and not request.user.is_superuser:
        userid = request.user.id
        try:
            get_user = User.objects.get(id=userid)
            web_get_grower = get_user.grower.id
            context['growers'] = Grower.objects.filter(id=web_get_grower)
            chat_field_id = request.POST.get('chat_field_id')
            get_grower = Grower.objects.get(id=web_get_grower)
            context['growers'] = Grower.objects.filter(id=web_get_grower)
            grower_id = web_get_grower
            context['select_get_grower_id'] = get_grower.id
            context['select_get_grower_name'] = get_grower.name
            context['show_grower'] = get_grower.name

            grower_farms = get_Grower_Farms(grower_id)
            context['grower_farms'] = grower_farms
            grower_fields = get_Grower_Fields(grower_id)
            context['grower_fields'] = grower_fields
            grower_storages = get_Grower_Stogares(grower_id)
            context['grower_storages'] = grower_storages
            # grower_payments
            grower_payments = get_Grower_Payments(grower_id)
            context['grower_payments'] = grower_payments

            if len(grower_fields) > 0  and chat_field_id == None :
                context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart(grower_fields.first().id)
                context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart(grower_fields.first().id)
                context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details(grower_fields.first().id)
                # grower_surveys
                context['grower_surveys'] = grower_Field_Surveys_Details(grower_fields.first().id)
            elif len(grower_fields) == 0  and chat_field_id == None :
                context['grower_Field_Vegetation_Chart'] = None
                context['grower_Field_Shipment_Chart'] = None
                context['grower_Field_Shipment_Details'] = None
                # grower_surveys
                context['grower_surveys'] = None
            else:
                if chat_field_id :
                    check_field = Field.objects.filter(id=chat_field_id,grower_id=get_grower)
                    if len(check_field) == 1 :
                        context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart(chat_field_id)
                        context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart(chat_field_id)
                        context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details(chat_field_id)
                        context['grower_surveys'] = grower_Field_Surveys_Details(chat_field_id)
                        context['selcted_filed'] = Field.objects.get(id=chat_field_id)

            if 'grower_Field_Vegetation_Chart' in context and context['grower_Field_Vegetation_Chart']:
                all_points = list(context['grower_Field_Vegetation_Chart'][0].values())
                all_points.pop(0)
                converted_list = [ int(i) for i in all_points]
                sorted_list = sorted(converted_list, reverse=True)
                min_break_point = int(sorted_list[1] * 1.1)
                max_break_point = int(sorted_list[0] * 0.9)
                context['break_startValue'] = min_break_point 
                context['break_endValue'] = max_break_point 
                context['maximum_y'] = sorted_list[0] + 1000
            else:
                context['break_startValue'] = None
                context['break_endValue'] = None 
                context['maximum_y'] = None 
        except:
            pass
     
        return render(request, 'grower/grower_dashboard_com.html', context)
    elif request.user.is_consultant:
        if web_get_grower == 'all':
            consultant_id = Consultant.objects.get(email=request.user.email).id
            growers = Grower.objects.filter(consultant=consultant_id).order_by('name')
            context['growers'] = growers
            if request.method == 'POST' :
                get_grower = request.POST.get('get_grower')
                chat_field_id = request.POST.get('chat_field_id')
                context['show_grower'] = get_grower
                if get_grower and get_grower != '' :
                    check_grower = growers.filter(id=int(get_grower))
                    if check_grower.exists():
                        grower_id = check_grower.first().id
                        context['select_get_grower_id'] = grower_id
                        context['select_get_grower_name'] = check_grower.first().name
                        grower_farms = get_Grower_Farms(grower_id)
                        context['grower_farms'] = grower_farms
                        grower_fields = get_Grower_Fields(grower_id)
                        context['grower_fields'] = grower_fields
                        grower_storages = get_Grower_Stogares(grower_id)
                        context['grower_storages'] = grower_storages
                        # grower_payments
                        grower_payments = get_Grower_Payments(grower_id)
                        context['grower_payments'] = grower_payments
        
                        if len(grower_fields) > 0  and chat_field_id == None :
                            context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart(grower_fields.first().id)
                            context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart(grower_fields.first().id)
                            context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details(grower_fields.first().id)
                            # grower_surveys
                            context['grower_surveys'] = grower_Field_Surveys_Details(grower_fields.first().id)
                        elif len(grower_fields) == 0  and chat_field_id == None :
                            context['grower_Field_Vegetation_Chart'] = None
                            context['grower_Field_Shipment_Chart'] = None
                            context['grower_Field_Shipment_Details'] = None
                            # grower_surveys
                            context['grower_surveys'] = None
                        else:
                            if chat_field_id :
                                check_field = Field.objects.filter(id=chat_field_id,grower_id=get_grower)
                                if len(check_field) == 1 :
                                    context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart(chat_field_id)
                                    context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart(chat_field_id)
                                    context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details(chat_field_id)
                                    context['grower_surveys'] = grower_Field_Surveys_Details(chat_field_id)
                                    context['selcted_filed'] = Field.objects.get(id=chat_field_id)
                                    
                        if 'grower_Field_Vegetation_Chart' in context and context['grower_Field_Vegetation_Chart']:
                            all_points = list(context['grower_Field_Vegetation_Chart'][0].values())
                            all_points.pop(0)
                            converted_list = [ int(i) for i in all_points]
                            sorted_list = sorted(converted_list, reverse=True)
                            min_break_point = int(sorted_list[1] * 1.1)
                            max_break_point = int(sorted_list[0] * 0.9)
                            context['break_startValue'] = min_break_point 
                            context['break_endValue'] = max_break_point 
                            context['maximum_y'] = sorted_list[0] + 1000
                        else:
                            context['break_startValue'] = None
                            context['break_endValue'] = None 
                            context['maximum_y'] = None 
                    else:
                        messages.error(request,f' {len(check_grower)} Growers found with same name !!')
        else:
            pass
        return render(request, 'grower/grower_dashboard_com.html', context)
    else:
        return redirect ('dashboard')
    

def get_Grower_Farms(g_id):
    farms = Farm.objects.filter(grower_id = g_id).order_by('name')
    return farms


def get_Grower_Fields(g_id):
    fields = Field.objects.filter(grower_id = g_id).order_by('name')
    return fields


def get_Grower_Stogares(g_id):
    storages = Storage.objects.filter(grower_id = g_id).order_by('storage_name')
    return storages


def get_Grower_Payments(g_id):
    g_payment = GrowerPayments.objects.filter(grower_id=g_id)
    entry = EntryFeeds.objects.filter(grower_id=g_id)
    g_payment_option = []
    if entry.exists():
        for i in entry :
            g_payment_option.append({"payment_option":i.contracted_payment_option,"payment_option_from_date":i.from_date,"payment_option_to_date":i.to_date})
    
    lst_delivery_lbs =[]
    if g_payment.exists():
        for i in g_payment :
            if i.delivery_lbs :
                lst_delivery_lbs.append(float(i.delivery_lbs))    
    
    sum_delivery_lbs = f'{sum(lst_delivery_lbs)} LBS'
    sum_delivered_value = f'$ {sum([int(float(i.payment_amount)) for i in g_payment])}' if g_payment.exists() else f'$ 0'

    res = {"sum_delivery_lbs":sum_delivery_lbs,"sum_deliverys_count":g_payment.count(),"sum_deliverd_value":sum_delivered_value,"g_payment_option":g_payment_option} 

    return res


def grower_Field_Surveys_Details(f_id) :
    sus = SustainabilitySurvey.objects.filter(field_id=f_id)
    res = []
    for i in sus :
        if i.field.crop == 'COTTON' :
            pass
        else:
            pass        
        res.append({"sus_name":i.namesurvey,"sus_score":i.surveyscore,"crop":i.field.crop})
    # res = [{"sus_count":sus.count()}]
  
    return res


def grower_Field_Vegetation_Chart(f_id):
    field = Field.objects.get(id=f_id)
    print("field",field)
    name = field.name
    gal_water_saved  = str(field.gal_water_saved).strip().replace(',','') if field.gal_water_saved not in ['', ' ', 'None', 'nan', 'null', None] else 0
    water_lbs_saved = str(field.water_lbs_saved).strip().replace(',','') if field.water_lbs_saved not in ['', ' ', 'None', 'nan', 'null', None] else 0
    co2_eq_reduced = str(field.co2_eq_reduced).strip().replace(',','') if field.co2_eq_reduced not in ['', ' ', 'None', 'nan', 'null', None] else 0
    increase_nitrogen = str(field.increase_nitrogen).strip().replace(',','') if field.increase_nitrogen not in ['', ' ', 'None', 'nan', 'null', None] else 0
    ghg_reduction = str(field.ghg_reduction).strip().replace(',','') if field.ghg_reduction not in ['', ' ', 'None', 'nan', 'null', None] else 0
    land_use_efficiency = str(field.land_use_efficiency).strip().replace(',','') if field.land_use_efficiency not in ['', ' ', 'None', 'nan', 'null', None] else 0
    grower_premium_percentage = str(field.grower_premium_percentage).strip().replace(',','') if field.grower_premium_percentage not in ['', ' ', 'None', 'nan', 'null', None] else 0
    grower_dollar_premium = str(field.grower_dollar_premium).strip().replace(',','') if field.grower_dollar_premium not in ['', ' ', 'None', 'nan', 'null', None] else 0

    return [{'name':name,'gal_water_saved':gal_water_saved,'water_lbs_saved':water_lbs_saved,'co2_eq_reduced':co2_eq_reduced,
             'increase_nitrogen':increase_nitrogen,'ghg_reduction':ghg_reduction,'land_use_efficiency':land_use_efficiency,
             'grower_premium_percentage':grower_premium_percentage,'grower_dollar_premium':grower_dollar_premium}]


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
        res = {"name":name,"crop":"RICE","shipmentLevelText":shipmentLevelText,"per_approved_shipment":per_approved_shipment,
               "per_disapproved_shipment":per_disapproved_shipment,"per_noStatus__shipment":per_noStatus__shipment,
               "shipment_wt": f'{sum(shipment_wt)} LBS',"shipment_count":count_shipment,"shipment_approved":count_approved_shipment,
               "shipment_disapproved":count_disapproved_shipment,"shipment_pending":count_noStatus__shipment,
               "shipment_delivered_wt":f'{sum(shipment_delivered_wt)} LBS',"shipment_paid_amount":shipment_paid_amount,
               "projected_yield":projected_yield,"actual_yield":actual_yield,"yield_delta":yield_delta,"g_payee_count":g_payee_count,
               "lien_holder_count":lien_holder_count,"payment_split_count":payment_split_count,"shipment_delivered_count":count_approved_shipment}
        return res
  

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
            
            print("finale_date",finale_date,type(finale_date))

            
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
      

def calculation_water_savings_gal(ans):
    data = []
    acre_inches_pattern = r'(\d{1,2}-\d{1,2}|\d{1,2}) acre inches'
    acre_inches_match = re.search(acre_inches_pattern, ans)
    # gal_lbs_pattern = r'(\d+\s*-\s*\d+)|(\d+)\s*gal\s*/\s*lbs'
    gal_lbs_pattern = r'((\d+\s*-\s*\d+)|(\d+))\s*gal\s*/\s*lbs'
    gal_lbs_match = re.search(gal_lbs_pattern, ans)
    if acre_inches_match:
        # Extract the acre inches value from the match object
        acre_inches_value = acre_inches_match.group(1)
        data.append({'acre_inches_flag':True,'acre_inches_value':acre_inches_value})
    else:
        data.append({'acre_inches_flag':False,'acre_inches_value':''})
    if gal_lbs_match :
        print("gal_lbs_match",gal_lbs_match)
        gal_lbs_value = gal_lbs_match.group(1)

        # gal_lbs_value = re.search(r'(\d+\s*-\s*\d+)', gal_lbs_match.group(0)).group(0)
        data.append({'gal_lbs_flag':True,'gal_lbs_value':gal_lbs_value})
    else:
         data.append({'gal_lbs_flag':False,'gal_lbs_value':''})
    return data


def calculation_co2eq_reduction(ans):
    pattern = r'fuel use:\s*(<\d+\.\d+|\d+\.\d+\s+to\s+\d+\.\d+)\s+gal./a'
    # pattern = r'fuel use:\s*(<?\d+\.\d+\s*(?:to\s+\d+\.\d+)?)\s+gal./a'
    match = re.search(pattern, ans)
    if match:
        value = match.group(1)
        return {"co2eq_reduction_flag":True,"co2eq_reduction_value":value}
    else:
        return {"co2eq_reduction_flag":False,"co2eq_reduction_value":""}


def calculation_less_ghg(ans):
    pattern = r'(\d+-\d+)'
    match = re.search(pattern, ans)
    if match:
        # Extract the matched value
        value = match.group(1)
        print("value",value)
        if value == "50-80" :
            value = 1
        elif value == "80-100" :
            value = 1.5
        elif value == "100-120" :
            value = 2
        elif value == "120-140" :
            value = 2.5
        return {"less_ghg_flag":True,"less_ghg_value":value}
    else:
        return {"less_ghg_flag":False,"less_ghg_value":""}


def calculation_water_savings_gal_rice(ans):
    print("ans",ans)
    data = {'gal_lbs_flag':False,'levees_bs_value':'','bs_value_gal_lb':'','water3_value':'','water1_value':''}
    ans = ans.split(" ")
    levees = f"{ans[0]} {ans[1]}"    
    if levees == "Contour levees" :
        print("levees",levees)
        bs_value = 38
        bs_value_gal_lb = 121
    elif levees+ans[2] == "Straight levees+" :
        print("levees","Straight levees + MRI")
        bs_value = 29
        bs_value_gal_lb = 92
    elif levees == "Straight levees" :
        print("levees","Straight levees")
        bs_value = 37
        bs_value_gal_lb = 118
    elif levees == "Zero grade" :
        print("levees","Zero grade")
        bs_value = 22
        bs_value_gal_lb = 69
    elif levees == "Row rice" :
        print("levees","Row rice")
        bs_value = 29
        bs_value_gal_lb = 92
    else:
        bs_value = 0
        bs_value_gal_lb = 0
    # 31-01-23 ..........................
    data["levees_bs_value"] = bs_value
    data["bs_value_gal_lb"] = bs_value_gal_lb
    # water3 [ Total Gallons Water Savings / field ]
    index_water1 = ans.index('gal')
    index_water3_val = []
    try:
        index_water3 = ans.index('inches')
        index_water3_var = ans[index_water3 -1].split('-')
        index_water3_val.append(index_water3_var[0])
    except:
        pass
    
    if len(index_water3_val) != 0 :
        if len(index_water3_val) > 1 :
            pass
        elif len(index_water3_val) == 1 :
            if "acre" not in index_water3_val :
                data["water3_value"] = index_water3_val[0]
            else:
                try:
                    index_water3 = ans.index('acre')
                    index_water3_var = ans[index_water3 -1].split('-')
                    index_water3_var = int(index_water3_var[0])
                    data["water3_value"] = index_water3_var
                except:
                    pass
        else:
            pass
    else:
        # data["water3_value"] = 0
        data["water3_value"] = 35
    # water1 [ Gal water save / Pound ]
    index_water1_val = ans[index_water1 - 1]
    get_value = index_water1_val.split("-")
    print("get_value",get_value)
    if len(get_value) > 1 :
        # get_value1 = int(get_value[0]) + int(get_value[1]) / 2
        data["water1_value"] = int(get_value[0])
        data["gal_lbs_flag"] = True
    else:
        data["water1_value"] = get_value[0]
        data["gal_lbs_flag"] = True
    print("data.......................",data)
    return data 


def calculation_less_ghg_rice(ans):
    print('..............ans1',ans)
    match = re.search(r'\b\d+\b', ans)

    if match:
        value = int(match.group())
    else:
        value = 0 
    if value:
        return {"less_ghg_flag":True,"less_ghg_value":value}
    else:
        return {"less_ghg_flag":False,"less_ghg_value":""}    


@login_required()
def sustainable_product_claims(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        growers = Grower.objects.all().order_by('name')
        context['growers'] = growers
        growerSelction = request.GET.get('growerSelction')
        fieldSelction = request.GET.get('fieldSelction')
        print("growerSelction================",growerSelction)
        print("fieldSelction================",fieldSelction)
        if growerSelction and growerSelction != "" :
            context['selectedGrower'] = Grower.objects.get(id=growerSelction)
            fields = Field.objects.filter(grower_id=growerSelction).order_by('-name')
            context['fields'] = fields
            # For All Fields ...
            if fieldSelction and fieldSelction != "" and fieldSelction == "all_fields" :
                context["selectedField"] = "all"
                if fields.exists():
                    context["corps"] = fields.first().crop
                    main_data = []
                    color_code = {"1":"#C2FFE1","2":"#ADFFD8","3":"#99FFCE","4":"#85FFC4","5":"#70FFBA","6":"#5CFFB0","7":"#47FFA6","8":"#33FF9C","9":"#1FFF93","10":"#0AFF89",
                                  "11":"#00F57E","12":"#00E074","13":"#00CC69","14":"#00B85F","15":"#00A354","16":"#008243","17":"#007A3F","18":"#006635","19":"#00522A","20":"#003D20",
                                  "21":"#002915"}
                    # color_code = {"1":"#0A6C38","2":"#81A179","3":"#B0C69F","4":"#D3E3BB","5":"#6COA3E","6":"#957292","7":"#B39CC0","8":"#CBBBE3"}
                    counter = 1
                    if context['corps'] and context['corps'] == 'COTTON' :
                        for i in fields :
                            grower_input = InputSurvey.objects.filter(field_id=i.id,questionsurvey_id=165)
                            grower_input_co2 = InputSurvey.objects.filter(field_id=i.id,questionsurvey_id=174)
                            grower_input_no2 = InputSurvey.objects.filter(field_id=i.id,questionsurvey_id=145)
                            grower_input_no22 = InputSurvey.objects.filter(field_id=i.id,questionsurvey_id=169)
                            total_gallons_water_saved = 0
                            water_savings_efficiency = 0
                            land_use_efficiency = 0
                            co2eq_claims = 0
                            grower_premium_percent1 = 0
                            less_ghg_value = 0
                            get_bale = BaleReportFarmField.objects.filter(ob4=i.id).annotate(net_wt_float=ExpressionWrapper(F('net_wt'), output_field=FloatField())).values("net_wt_float")
                            total_net_wt = sum(item['net_wt_float'] for item in get_bale)
                            # Water Efficiency cal
                            if grower_input.exists() :
                                grower_input = grower_input.first()
                                if grower_input.get_options : 
                                    acre_inches = calculation_water_savings_gal(f"{grower_input.get_options}")
                                    if acre_inches[0]['acre_inches_flag'] :
                                        acre_inches_value = acre_inches[0]['acre_inches_value'].split('-')[0]
                                        if len(acre_inches[0]['acre_inches_value'].split('-')) == 2 :
                                            acre_inches_value2 = acre_inches[0]['acre_inches_value'].split('-')[1]
                                            acre_inches_value = round(((int(acre_inches_value) + int(acre_inches_value2)) / 2),2)
                                        else:
                                            acre_inches_value = float(acre_inches_value) - 1
                                        
                                        acre_inches_of_water_savings = (40-round(float(acre_inches_value),2))

                                        total_gallons_water_saved = round(acre_inches_of_water_savings * 27154,2)
                                        if total_net_wt != 0 :
                                            water_savings_efficiency = round(float(total_gallons_water_saved / total_net_wt),2)
                                        else:
                                            pass
                                        # max_total_gallons_water_saved =  round(total_gallons_water_saved + 1,2)  
                                        # water_savings_efficiency_total = round(100 - water_savings_efficiency,2)
                                    else:
                                        pass
                                else:
                                    pass
                            else:
                                pass
                            # Land use efficiency
                            if i.yield_per_acre :
                                yield_per_acre = int(i.yield_per_acre)
                                land_use_efficiency = ((yield_per_acre - 842) / 842 ) * 100
                                land_use_efficiency = round(land_use_efficiency,2)
                            else:
                                pass
                            # CO2EQ calculation
                            if grower_input_co2.exists() :
                                grower_input_co2 = grower_input_co2.first()
                                calculation_co2eq = calculation_co2eq_reduction(f"{grower_input_co2.get_options}")
                                if calculation_co2eq['co2eq_reduction_flag'] :
                                    co2eq_reduction_value = calculation_co2eq['co2eq_reduction_value'].split('to')[0]
                                    if len(calculation_co2eq['co2eq_reduction_value'].split('to')) == 2 :
                                        co2eq_reduction_value = float(str(co2eq_reduction_value).strip())
                                        co2eq_reduction_value2 = float(str(calculation_co2eq['co2eq_reduction_value'].split('to')[1]).replace("gal./a","").strip())
                                        farmers_fuel_use = round((co2eq_reduction_value + co2eq_reduction_value2) / 2, 2)
                                    elif co2eq_reduction_value[0] == '<' :
                                        co2eq_reduction_value = float(co2eq_reduction_value.replace("<", ""))
                                    else:
                                        pass
                                    
                                    farmers_fuel_use = co2eq_reduction_value
                                    fuel_not_used = 6 - farmers_fuel_use
                                    # fuel_not_used = 6 - round(float(farmers_fuel_use),2)
                                    co2eq_claims = round((fuel_not_used * 104.58),2)
                                else:
                                    pass  
                            else:
                                pass
                            # Grower Premium Calculations
                            check_price = EntryFeeds.objects.filter(grower_id=i.grower.id)
                            if check_price.exists():
                                if len(check_price) > 1 :
                                    pass
                                else:
                                    check_price = check_price.first()
                                    cp = float(check_price.contract_base_price) if check_price.contract_base_price else 0
                                    sp = float(check_price.sustainability_premium) if check_price.sustainability_premium else 0
                                    qp = float(check_price.quality_premium) if check_price.quality_premium else 0
                                    get_price = cp + sp+ qp
                                    delta_claim_price = get_price - 0.837
                                    grower_premium = (delta_claim_price / 1.38) * 100
                                    context["grower_premium"] = grower_premium
                                    grower_premium_percent1= round(grower_premium,2) 
                            else:
                                pass
                            # Less GHG emmision
                            if grower_input_no2.exists():
                                grower_input_no2 = grower_input_no2.first()
                            elif grower_input_no22.exists():
                                grower_input_no2 = grower_input_no22.first()
                            
                            if grower_input_no2 :
                                var_less_ghg = calculation_less_ghg(f"{grower_input_no2.get_options}")
                                if var_less_ghg["less_ghg_flag"] :
                                    # less_ghg_value = var_less_ghg["less_ghg_value"]
                                    acreage = float(i.acreage)
                                    base_value = 120
                                    acreage_mul_base_value = acreage * base_value
                                    toatl_pounds = total_net_wt
                                    if toatl_pounds != 0 :
                                        if acreage_mul_base_value > toatl_pounds :
                                            net_value = round(((toatl_pounds - acreage_mul_base_value) / acreage_mul_base_value) * 100,2)
                                        else:
                                            net_value = round(((toatl_pounds - acreage_mul_base_value) / toatl_pounds) * 100,2)
                                        # less_ghg_value = net_value
                                        less_ghg_value = 100 - net_value
                                    
                            else:
                                pass
                            main_data.append({"field_name":i.name,"total_gallons_water_saved":total_gallons_water_saved,
                                            "water_savings_efficiency":water_savings_efficiency,"land_use_efficiency":land_use_efficiency,
                                            "co2eq_claims":co2eq_claims,"grower_premium_percent1":grower_premium_percent1,
                                            "less_ghg_value":less_ghg_value,"color":color_code[str(counter)]})
                            counter+=1
                        context["main_data"]=main_data
                        avg_water_savings_efficiency = round((sum([i["water_savings_efficiency"] for i in main_data])) / (len(main_data)),2)
                        avg_land_use_efficiency = round((sum([i["land_use_efficiency"] for i in main_data])) / (len(main_data)),2)
                        avg_total_gallons_water_saved = round((sum([i["total_gallons_water_saved"] for i in main_data])) / (len(main_data)),2)
                        avg_less_ghg_value = round((sum([i["less_ghg_value"] for i in main_data])) / (len(main_data)),2)
                        avg_co2eq_claims = round((sum([i["co2eq_claims"] for i in main_data])) / (len(main_data)),2)
                        avg_grower_premium_percent1 = round((sum([i["grower_premium_percent1"] for i in main_data])) / (len(main_data)),2)
                        context["avg_water_savings_efficiency"]=avg_water_savings_efficiency
                        context["avg_land_use_efficiency"]=avg_land_use_efficiency
                        context["avg_total_gallons_water_saved"]=avg_total_gallons_water_saved
                        context["avg_less_ghg_value"]=avg_less_ghg_value
                        context["avg_co2eq_claims"]=avg_co2eq_claims
                        context["avg_grower_premium_percent1"]=avg_grower_premium_percent1
                        context["color_code"]= color_code[str(len(main_data)+1)]
                        # print("avg_water_savings_efficiency",avg_water_savings_efficiency)
                        return render(request, 'grower/sustainable_product_claims.html', context)
                    else:
                        for i in fields :
                            grower_input = InputSurvey.objects.filter(field_id=i.id,questionsurvey_id=141)
                            grower_input_co2 = InputSurvey.objects.filter(field_id=i.id,questionsurvey_id=150)
                            grower_input_no2 = InputSurvey.objects.filter(field_id=i.id,questionsurvey_id=145)
                            get_bale = GrowerShipment.objects.filter(grower_id=i.grower.id,field_id=i.id,
                                                                    crop=context['corps'],status="APPROVED").values("received_amount")
                            total_net_wt = sum(float(item['received_amount']) for item in get_bale)
                            total_gallons_water_saved = 0
                            water_savings_efficiency = 0
                            grower_premium_percent1 = 0
                            land_use_efficiency = 0
                            co2eq_claims = 0
                            less_ghg_value = 0
                            if grower_input.exists():
                                # Water savings (gal) RICE 
                                total_gallons_water_saved = 0
                                water_savings_efficiency = 0
                                if grower_input.exists():
                                    grower_input = grower_input.first()
                                    water_savings_val =  calculation_water_savings_gal_rice(str(grower_input.get_options.first().optionname))
                                    if water_savings_val['gal_lbs_flag'] :
                                        if water_savings_val['water3_value'] :
                                            # water3 Total Gallons Water Savings / field
                                            water3_value = water_savings_val['water3_value']
                                            levees_bs_value = water_savings_val['levees_bs_value']
                                            acre_inches_of_water_saving = int(levees_bs_value) - int(water3_value)
                                            number_of_acres = float(i.acreage)
                                            total_acre_inches_water_saved = round(acre_inches_of_water_saving * number_of_acres,2)
                                            total_gallons_water_saved = round(total_acre_inches_water_saved * 27154,2)
                                        if water_savings_val['water1_value'] :
                                            # water1 Gal water save / Pound 
                                            water1_value = water_savings_val['water1_value']
                                            bs_value_gal_lb = water_savings_val['bs_value_gal_lb']
                                            water_savings_efficiency= int(bs_value_gal_lb) - int(water1_value)
                                    else:
                                        pass
                                else:
                                    pass
                            else:
                                pass       
                            # Grower Premium Calculations
                            check_price = EntryFeeds.objects.filter(grower_id=context['selectedGrower'].id)
                            if check_price.exists():
                                if len(check_price) > 1 :
                                    print("grower_premium",len(check_price))
                                else:
                                    check_price = check_price.first()
                                    cp = float(check_price.contract_base_price) if check_price.contract_base_price else 0
                                    sp = float(check_price.sustainability_premium) if check_price.sustainability_premium else 0
                                    qp = float(check_price.quality_premium) if check_price.quality_premium else 0
                                    get_price = cp + sp+ qp
                                    delta_claim_price = get_price - 0.837
                                    grower_premium = (delta_claim_price / 1.38) * 100
                                    grower_premium_percent1 = round(grower_premium,2)

                            # CO2EQ calculation
                            if grower_input_co2.exists() :
                                for j in grower_input_co2 :
                                    calculation_co2eq = calculation_co2eq_reduction(f"{j.get_options.first().optionname}")
                                    if calculation_co2eq['co2eq_reduction_flag'] :
                                        co2eq_reduction_value = calculation_co2eq['co2eq_reduction_value'].split('to')[0]
                                        if len(calculation_co2eq['co2eq_reduction_value'].split('to')) == 2 :
                                            co2eq_reduction_value = float(str(co2eq_reduction_value).strip())
                                            co2eq_reduction_value2 = float(str(calculation_co2eq['co2eq_reduction_value'].split('to')[1]).replace("gal./a","").strip())
                                            farmers_fuel_use = round((co2eq_reduction_value + co2eq_reduction_value2) / 2, 2)
                                        elif co2eq_reduction_value[0] == '<' :
                                            co2eq_reduction_value = float(co2eq_reduction_value.replace("<", ""))
                                        else:
                                            pass
                                        
                                        farmers_fuel_use = co2eq_reduction_value
                                        fuel_not_used = 6 - farmers_fuel_use
                                        # fuel_not_used = 6 - round(float(farmers_fuel_use),2)
                                        co2eq_claims = round((fuel_not_used * 104.58),2)
                                        
                            # Land use efficiency
                            if i.yield_per_acre :
                                yield_per_acre = int(i.yield_per_acre)
                                land_use_efficiency = yield_per_acre * 0.038
                                land_use_efficiency = round(land_use_efficiency,2)
                                
                            # Less GHG emmision
                            if grower_input_no2.exists() :
                                grower_input_no2 = grower_input_no2
                            else:
                                grower_input_no22 = InputSurvey.objects.filter(field_id=i.id,questionsurvey_id=169)
                                if grower_input_no22.exists():
                                    grower_input_no2 = grower_input_no22
                            
                            if grower_input_no2.exists():
                                grower_input_no2 = grower_input_no2.first()
                                var_less_ghg = calculation_less_ghg_rice(f"{grower_input_no2.get_options.first().optionname}")
                                net_value = 0
                                if var_less_ghg["less_ghg_flag"] :
                                    less_ghg_value = var_less_ghg["less_ghg_value"]
                                    acreage = float(i.acreage)
                                    base_value = 120
                                    acreage_mul_base_value = acreage * base_value
                                    toatl_pounds = total_net_wt
                                    if toatl_pounds != 0 :
                                        if acreage_mul_base_value > toatl_pounds :
                                            net_value = round(((toatl_pounds - acreage_mul_base_value) / acreage_mul_base_value) * 100,2)
                                        else:
                                            net_value = round(((toatl_pounds - acreage_mul_base_value) / toatl_pounds) * 100,2)
                                        less_ghg_value = net_value
                                    else:
                                        less_ghg_value = net_value
                                else:
                                    less_ghg_value = net_value
                            main_data.append({"field_name":i.name,"total_gallons_water_saved":total_gallons_water_saved,
                                            "water_savings_efficiency":water_savings_efficiency,"land_use_efficiency":land_use_efficiency,
                                            "co2eq_claims":co2eq_claims,"grower_premium_percent1":grower_premium_percent1,
                                            "less_ghg_value":less_ghg_value,"color":color_code[str(counter)]})
                            counter+=1
                        context["main_data"]=main_data
                        avg_water_savings_efficiency = round((sum([i["water_savings_efficiency"] for i in main_data])) / (len(main_data)),2)
                        avg_land_use_efficiency = round((sum([i["land_use_efficiency"] for i in main_data])) / (len(main_data)),2)
                        avg_total_gallons_water_saved = round((sum([i["total_gallons_water_saved"] for i in main_data])) / (len(main_data)),2)
                        avg_less_ghg_value = round((sum([i["less_ghg_value"] for i in main_data])) / (len(main_data)),2)
                        avg_co2eq_claims = round((sum([i["co2eq_claims"] for i in main_data])) / (len(main_data)),2)
                        avg_grower_premium_percent1 = round((sum([i["grower_premium_percent1"] for i in main_data])) / (len(main_data)),2)
                        context["avg_water_savings_efficiency"]=avg_water_savings_efficiency
                        context["avg_land_use_efficiency"]=avg_land_use_efficiency
                        context["avg_total_gallons_water_saved"]=avg_total_gallons_water_saved
                        context["avg_less_ghg_value"]=avg_less_ghg_value
                        context["avg_co2eq_claims"]=avg_co2eq_claims
                        context["avg_grower_premium_percent1"]=avg_grower_premium_percent1
                        context["color_code"]= color_code[str(len(main_data)+1)]
                        print("main_data",main_data)
                        # context["error_msg"] = "The Rice Field is under development and will be updated soon."
                else:
                    context["error_msg"] = "Field not found."
            # For Indivigual Fields ...
            if fieldSelction and fieldSelction != "" and fieldSelction != "all_fields" :
                check_field = Field.objects.filter(id=fieldSelction,grower_id=context['selectedGrower'].id)
                context['selectedField'] = check_field.first()
                if context['selectedField'] :
                    context['corps'] = context['selectedField'].crop
                    if context['corps'] and context['corps'] == 'COTTON' :
                        grower_input = InputSurvey.objects.filter(field_id=context['selectedField'].id,questionsurvey_id=165)
                        grower_input_co2 = InputSurvey.objects.filter(field_id=context['selectedField'].id,questionsurvey_id=174)
                        grower_input_no2 = InputSurvey.objects.filter(field_id=context['selectedField'].id,questionsurvey_id=145)
                        get_bale = BaleReportFarmField.objects.filter(ob4=fieldSelction).annotate(net_wt_float=ExpressionWrapper(F('net_wt'), output_field=FloatField())).values("net_wt_float")
                        total_net_wt = sum(item['net_wt_float'] for item in get_bale)
                        if grower_input_no2.exists() :
                            grower_input_no2 = grower_input_no2
                        else:
                            grower_input_no22 = InputSurvey.objects.filter(field_id=context['selectedField'].id,questionsurvey_id=169)
                            if grower_input_no22.exists():
                                grower_input_no2 = grower_input_no22
                        
                        if grower_input.exists() :
                            for i in grower_input :
                                '''
                                Water savings (gal) in irrigated cotton  
                                '''
                                if not i.get_options.first() :
                                    context['error_msg'] = "Survey data not found"
                                    continue
                                acre_inches = calculation_water_savings_gal(f"{i.get_options.first().optionname}")
                                if acre_inches[0]['acre_inches_flag'] :
                                    acre_inches_value = acre_inches[0]['acre_inches_value'].split('-')[0]
                                    if len(acre_inches[0]['acre_inches_value'].split('-')) == 2 :
                                        acre_inches_value2 = acre_inches[0]['acre_inches_value'].split('-')[1]
                                        acre_inches_value = round(((int(acre_inches_value) + int(acre_inches_value2)) / 2),2)
                                    else:
                                        acre_inches_value = float(acre_inches_value) - 1

                                    # get_bale = BaleReportFarmField.objects.filter(ob4=fieldSelction).annotate(net_wt_float=ExpressionWrapper(F('net_wt'), output_field=FloatField())).values("net_wt_float")
                                    # total_net_wt = sum(item['net_wt_float'] for item in get_bale)
                                    acre_inches_of_water_savings = (40-round(float(acre_inches_value),2))
                                    total_gallons_water_saved = acre_inches_of_water_savings * 27154
                                    if total_net_wt !=0 :
                                        water_savings_efficiency = float(total_gallons_water_saved / total_net_wt)
                                        max_total_gallons_water_saved = total_gallons_water_saved + 1
                                        context['total_gallons_water_saved'] = round(total_gallons_water_saved,2)
                                        context['max_total_gallons_water_saved'] = round(max_total_gallons_water_saved,2)
                                        context['water_savings_efficiency'] = round(water_savings_efficiency,2)
                                        
                                        context['water_savings_efficiency_total'] = round(100 - water_savings_efficiency,2)
                                    else:
                                        context['total_gallons_water_saved'] = 0
                                        context['max_total_gallons_water_saved'] = 1
                                        context['water_savings_efficiency'] = 0
                                        context['water_savings_efficiency_total'] = 0
                                else:
                                    context['total_gallons_water_saved'] = 0
                                    context['max_total_gallons_water_saved'] = 1
                                    context['water_savings_efficiency'] = 0
                                    context['water_savings_efficiency_total'] = 0
                                                                    
                                # Land use efficiency
                                if context['selectedField'].yield_per_acre :
                                    # print("block 1========================")
                                    yield_per_acre = int(context['selectedField'].yield_per_acre)
                                    # print("yield_per_acre===================",yield_per_acre)
                                    land_use_efficiency = ((yield_per_acre - 842) / 842 ) * 100
                                    context['land_use_efficiency'] = round(land_use_efficiency,2)
                                    context['land_use_efficiency_total'] = round(100- land_use_efficiency,2)
                                else:
                                    context['land_use_efficiency'] = 0
                                    context['land_use_efficiency_total'] = 100

                        else:
                            context['error_msg'] = "Survey data not found"
                        # CO2EQ calculation
                        if grower_input_co2.exists() :
                            for i in grower_input_co2 :
                                calculation_co2eq = calculation_co2eq_reduction(f"{i.get_options.first().optionname}")
                                if calculation_co2eq['co2eq_reduction_flag'] :
                                    co2eq_reduction_value = calculation_co2eq['co2eq_reduction_value'].split('to')[0]
                                    if len(calculation_co2eq['co2eq_reduction_value'].split('to')) == 2 :
                                        co2eq_reduction_value = float(str(co2eq_reduction_value).strip())
                                        co2eq_reduction_value2 = float(str(calculation_co2eq['co2eq_reduction_value'].split('to')[1]).replace("gal./a","").strip())
                                        farmers_fuel_use = round((co2eq_reduction_value + co2eq_reduction_value2) / 2, 2)
                                    elif co2eq_reduction_value[0] == '<' :
                                        co2eq_reduction_value = float(co2eq_reduction_value.replace("<", ""))
                                    else:
                                        pass
                                    
                                    farmers_fuel_use = co2eq_reduction_value
                                    fuel_not_used = 6 - farmers_fuel_use
                                    # fuel_not_used = 6 - round(float(farmers_fuel_use),2)
                                    co2eq_claims = round((fuel_not_used * 104.58),2)
                                    context['co2eq_claims'] = co2eq_claims
                                    context['co2eq_claims_max'] = co2eq_claims + 100
                        else:
                            context['error_msg'] = "Survey data not found"

                        # Grower Premium Calculations
                        check_price = EntryFeeds.objects.filter(grower_id=context['selectedGrower'].id)
                        if check_price.exists():
                            if len(check_price) > 1 :
                                pass
                            else:
                                check_price = check_price.first()
                                cp = float(check_price.contract_base_price) if check_price.contract_base_price else 0
                                sp = float(check_price.sustainability_premium) if check_price.sustainability_premium else 0
                                qp = float(check_price.quality_premium) if check_price.quality_premium else 0
                                get_price = cp + sp+ qp
                                delta_claim_price = get_price - 0.837
                                grower_premium = (delta_claim_price / 1.38) * 100
                                context["grower_premium"] = grower_premium
                                context["grower_premium_percent1"]= round(grower_premium,2)
                                context["grower_premium_percent2"]= 100 - round(grower_premium,2)
                        else:
                            context['error_msg'] = "Survey data not found"
                        # Less GHG emmision
                        if grower_input_no2.exists():
                            grower_input_no2 = grower_input_no2.first()
                            var_less_ghg = calculation_less_ghg(f"{grower_input_no2.get_options.first().optionname}")
                            if var_less_ghg["less_ghg_flag"] :
                                less_ghg_value = var_less_ghg["less_ghg_value"]
                                acreage = float(context['selectedField'].acreage)
                                base_value = 120
                                acreage_mul_base_value = acreage * base_value
                                toatl_pounds = total_net_wt
                                if toatl_pounds != 0 :
                                    if acreage_mul_base_value > toatl_pounds :
                                        net_value = round(((toatl_pounds - acreage_mul_base_value) / acreage_mul_base_value) * 100,2)
                                    else:
                                        net_value = round(((toatl_pounds - acreage_mul_base_value) / toatl_pounds) * 100,2)
                                    context["less_ghg_value"] = net_value
                                    context["total_less_ghg_value"] = 100 - net_value
                        else:
                            context['error_msg'] = "Survey data not found"
                    else:                        
                        grower_input = InputSurvey.objects.filter(field_id=context['selectedField'].id,questionsurvey_id=141)
                        grower_input_co2 = InputSurvey.objects.filter(field_id=context['selectedField'].id,questionsurvey_id=150)
                        # grower_input_no2 = InputSurvey.objects.filter(field_id=context['selectedField'].id,questionsurvey_id=145)
                        grower_input_no2 = InputSurvey.objects.filter(field_id=context['selectedField'].id,questionsurvey_id=144)
                        # grower_input_no2 = InputSurvey.objects.filter(field_id=context['selectedField'].id).values("questionsurvey__id","questionsurvey__questionname")
                        # print("grower_input_no2=================",grower_input_no2)
                        get_bale = GrowerShipment.objects.filter(grower_id=context['selectedGrower'].id,field_id=context['selectedField'].id,
                                                                 crop=context['corps'],status="APPROVED").values("received_amount")
                        
                        total_net_wt = sum(float(item['received_amount']) for item in get_bale)
                        # Water savings (gal) RICE 
                        context['total_gallons_water_saved'] = 0
                        context['max_total_gallons_water_saved'] = 1
                        context['water_savings_efficiency'] = 0
                        context['water_savings_efficiency_total'] = 1
                        if grower_input.exists():
                            print("dhdhdbhbnfhbfhnfh======================")
                            grower_input = grower_input.first()
                            water_savings_val =  calculation_water_savings_gal_rice(str(grower_input.get_options.first().optionname))
                            print("water_savings_val",water_savings_val)
                            total_acre_inches_water_saved = 0
                            water3_value = water_savings_val['water3_value']
                            number_of_acres = round(float(context['selectedField'].acreage),2)
                            if water_savings_val['gal_lbs_flag'] :
                                print("block 1======================")
                                if water_savings_val['water3_value'] and water_savings_val['water3_value'] != 0 :
                                    
                                    # water3 Total Gallons Water Savings / field
                                    print("block 2======================")
                                    
                                    water3_value = water_savings_val['water3_value']
                                    levees_bs_value = 38
                                    acre_inches_of_water_saving = int(levees_bs_value) - int(water3_value)
                                    number_of_acres = float(context['selectedField'].acreage)
                                    total_acre_inches_water_saved = round(acre_inches_of_water_saving * number_of_acres,2)
                                    context['total_gallons_water_saved'] = round(total_acre_inches_water_saved * 27154,2)
                                    context['max_total_gallons_water_saved'] = context['total_gallons_water_saved'] + 1
                                    
                                else:
                                    context['water2_error_msg'] = "Survey data not found"
                                   
                                if water_savings_val['water1_value'] and water_savings_val['water1_value'] != 0 :
                                    print("block 3======================")
                                    # water1 Gal water save / Pound 
                                    
                                    #new logic add 28.03.2024
                                    t_yield = Field.objects.filter(grower_id=growerSelction,id = fieldSelction).values("total_yield").first()
                                    if t_yield:
                                        total_yield = t_yield.get("total_yield", 0)
                                        z_t_yield = total_yield * 45
                                        ws_per_pb = round(total_acre_inches_water_saved * 27154 / z_t_yield, 2)
                                        # print("ws_per_pb",ws_per_pb)
                                    else:
                                        ws_per_pb = None
                                    
                                    water1_value = water_savings_val['water1_value']
                                    bs_value_gal_lb = water_savings_val['bs_value_gal_lb']
                                    # print("water1_value",water1_value)
                                    # print("bs_value_gal_lb",bs_value_gal_lb)
                                    #new logic add 30.03.2024  
                                    water_applied= round(int(water3_value) * number_of_acres * 27154,2)
                                    water_efficiency = round(water_applied/z_t_yield,2)
                                    val = int(bs_value_gal_lb) - water_efficiency
                                    # print(val)
                                    context['water_savings_efficiency'] = round((int(bs_value_gal_lb) - water_efficiency),2)
                                    context['water_savings_efficiency_total'] = ws_per_pb

                                    # context['water_savings_efficiency'] = int(bs_value_gal_lb) - int(water1_value)
                                    # context['water_savings_efficiency_total'] = context['water_savings_efficiency'] + 1 
                                    
                                else:
                                    context['water1_value'] = "Survey data not found"   
                            else:
                                pass
                        else:
                            context['water1_error_msg'] = "Survey data not found"
                       
                        # Grower Premium Calculations
                        context["grower_premium"] = 0
                        check_price = EntryFeeds.objects.filter(grower_id=context['selectedGrower'].id)

                        if check_price.exists():
                            if len(check_price) > 1 :
                                print("grower_premium",len(check_price))
                            else:
                                print("block7========================================")
                                check_price = check_price.first()
                                cp = float(check_price.contract_base_price) if check_price.contract_base_price else 0
                                sp = float(check_price.sustainability_premium) if check_price.sustainability_premium else 0
                                qp = float(check_price.quality_premium) if check_price.quality_premium else 0
                                get_price = cp + sp + qp
                                delta_claim_price = get_price - 0.837
                                grower_premium = (delta_claim_price / 1.38) * 100

                                # new logic add 05.04.2024
                                grower_shipment = GrowerShipment.objects.filter(grower_id=context['selectedGrower'].id,crop=context['corps'],status='APPROVED',field=context['selectedField'].id)
                                if grower_shipment.exists():
                                    for i in grower_shipment:
                                        process_date_int = i.approval_date.strftime("%m/%d/%y")
                                        delivery_date = process_date_int

                                        check_entry_with_date = EntryFeeds.objects.filter(grower_id = context['selectedGrower'].id,from_date__lte=i.approval_date,to_date__gte=i.approval_date)
                                        check_entry_with_no_date = EntryFeeds.objects.filter(grower_id = context['selectedGrower'].id,from_date__isnull=True,to_date__isnull=True)
                                        if check_entry_with_date.exists() :
                                            check_entry_id = [i.id for i in check_entry_with_date][0]
                                            var = EntryFeeds.objects.get(id=check_entry_id)

                                        elif check_entry_with_no_date.exists() :
                                            check_entry_id = [i.id for i in check_entry_with_no_date][0]
                                            var = EntryFeeds.objects.get(id = check_entry_id)
                                        else:
                                            pass    
                                        total_price_init = 0
                                        if var.contracted_payment_option == 'Acreage Release' :
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
                                            delivery_lbs = int(float(i.received_amount)) if i.received_amount != None else int(float(i.total_amount))
                                            total_price2 = float(total_price_init) / 100
                                            total_price = total_price2 + 0.04
    
                                    date_str = delivery_date
                                    formatted_date = datetime.strptime(date_str, "%m/%d/%y").strftime("%Y-%m-%d") 
                                    if NasdaqApiData.objects.filter(date_api=formatted_date).count() !=0 :
                                        total_price_init = NasdaqApiData.objects.get(date_api=formatted_date).close_value_api
                                        
                                    end_pay_rate = total_price if total_price else 0
                                    base_pay_rate = float(total_price_init) /100  if total_price_init else 0
                                    premium_cal = end_pay_rate/base_pay_rate - 1
                                    new_grower_premium = round(premium_cal * 100,2)
                                    
                                    context["grower_premium"] = new_grower_premium
                                    context["grower_premium_percent1"]= round(new_grower_premium,2)
                                    context["grower_premium_percent2"]= 100 - round(new_grower_premium,2)
                               
                                    #     context["grower_premium"] = grower_premium
                                    #     context["grower_premium_percent1"]= round(grower_premium,2)
                                    #     context["grower_premium_percent2"]= 100 - round(grower_premium,2)
                                else:
                                    context['grower_premium_error_msg'] = "Survey data not found"

                        else:
                            context['grower_premium_error_msg'] = "Survey data not found"
                            
                        # CO2EQ calculation
                        context['co2eq_claims'] = 0
                        if grower_input_co2.exists() :
                            print("block5=========================")
                            for i in grower_input_co2 :
                                calculation_co2eq = calculation_co2eq_reduction(f"{i.get_options.first().optionname}")
                                if calculation_co2eq['co2eq_reduction_flag'] :
                                    co2eq_reduction_value = calculation_co2eq['co2eq_reduction_value'].split('to')[0]
                                    if len(calculation_co2eq['co2eq_reduction_value'].split('to')) == 2 :
                                        co2eq_reduction_value = float(str(co2eq_reduction_value).strip())
                                        co2eq_reduction_value2 = float(str(calculation_co2eq['co2eq_reduction_value'].split('to')[1]).replace("gal./a","").strip())
                                        farmers_fuel_use = round((co2eq_reduction_value + co2eq_reduction_value2) / 2, 2)
                                    elif co2eq_reduction_value[0] == '<' :
                                        co2eq_reduction_value = float(co2eq_reduction_value.replace("<", ""))
                                    else:
                                        context['co2eq_reduction_error_msg'] = "Survey data not found"
                                    farmers_fuel_use = co2eq_reduction_value
                                    fuel_not_used = 6 - farmers_fuel_use
                                    co2eq_claims = round((fuel_not_used * 104.58),2)
                                    
                                    #new logic add 30.03.2024
                                    # with_year_field = FieldUpdated.objects.filter(grower_id=growerSelction,field_id=context['selectedField'].id,crop_year='2022').values('id')
                                    # with_year_field = FieldUpdated.objects.filter(grower_id=growerSelction,field_id=context['selectedField'].id).values('id')
                                    with_year_field = FieldUpdated.objects.filter(field_id=context['selectedField'].id).values('id')
                                    with_year_field1 = Field.objects.filter(grower_id=growerSelction,id=context['selectedField'].id).values('id')
                                    # print("with_year_field1",with_year_field1)
                                    # print("with_year_field",with_year_field)
                                    number_of_acres = float(context['selectedField'].acreage)
                                    # print("number_of_acres",number_of_acres)
                                    if with_year_field.exists():
                                        with_year_field_ids = [i['id'] for i in with_year_field]
                                        get_field_activity = FieldActivity.objects.filter(field_updated_id__in=with_year_field_ids)
                                        field_activity_npk = get_field_activity.filter(field_activity='NPK_Application')
                                        sum_nitrogen = sum([i.n_nitrogen for i in field_activity_npk])
                                        # print("sum_nitrogen=======================",sum_nitrogen)
                                        nitrogen_st_1 = 175 - float(sum_nitrogen)
                                        # print("nitrogen_st_1=======================",nitrogen_st_1)
                                        nitrogen_st_2 = float(nitrogen_st_1) * float(number_of_acres)
                                        # print("nitrogen_st_2=======================",nitrogen_st_2)
                                        nitrogen_st_3 = float(nitrogen_st_2) * 0.014
                                        # print("nitrogen_st_3=======================",nitrogen_st_3)
                                        CO2eq_per_lb_final = float(nitrogen_st_3) * 300
                                        # print("CO2eq_per_lb_final=======================",CO2eq_per_lb_final)
                                    
                                        context['co2eq_claims'] = round(CO2eq_per_lb_final,2)
                                        context['co2eq_claims_max'] = CO2eq_per_lb_final + 100 
                                    else:
                                        pass       
                                    # context['co2eq_claims'] = co2eq_claims
                                    # context['co2eq_claims_max'] = co2eq_claims + 100
                                else:
                                    context['co2eq_reduction_error_msg'] = "Survey data not found"
                        else:
                            context['co2eq_reduction_error_msg'] = "Survey data not found"
                        
                        # Land use efficiency
                        context['land_use_efficiency'] = 0
                        if context['selectedField'].yield_per_acre :
                            print("block4=====================")
                            yield_per_acre = int(context['selectedField'].yield_per_acre)
                            number_of_acres = float(context['selectedField'].acreage)
                            land_use_efficiency = yield_per_acre * 0.038
                            
                            t_yield = Field.objects.filter(grower_id=growerSelction,id = fieldSelction).values("total_yield").first()
                                    
                            if t_yield:
                                total_yield = t_yield.get("total_yield", 0)
                                z_t_yield = total_yield * 45
                            
                            field_yield_per_acre = (z_t_yield/number_of_acres)  
                            land_use_efficiency = (field_yield_per_acre/7600)
                            land_percentage_formatted = land_use_efficiency * 100
                            context['land_use_efficiency'] = round(land_percentage_formatted,2)
                            
                            # context['land_use_efficiency'] = round(land_use_efficiency,2)
                            context['land_use_efficiency_total'] = round(100- land_use_efficiency,2)

                            # context['land_use_efficiency'] = round(land_use_efficiency,2)
                            # context['land_use_efficiency_total'] = round(100- land_use_efficiency,2)  
                        else:
                            context['land_use_error_msg'] = "Survey data not found"
                        
                        # Less GHG emmision   # prod problem found
                        context["less_ghg_value"] = 0    
                        if grower_input_no2.exists() :              
                            grower_input_no2 = grower_input_no2
                        else:
                            grower_input_no22 = InputSurvey.objects.filter(field_id=context['selectedField'].id,questionsurvey_id=169)
                            if grower_input_no22.exists():
                                grower_input_no2 = grower_input_no22
                        if grower_input_no2.exists():
                            print("block6=====================")
                            grower_input_no2 = grower_input_no2.first()
                            # print("grower_input_no2",grower_input_no2.get_options)
                            # print("grower_input_no2",grower_input_no2)
                            var_less_ghg = calculation_less_ghg_rice(f"{grower_input_no2.get_options.first().optionname}")
                            print("var_less_ghg",var_less_ghg)
                            multi_drain_value_check = grower_input_no2.get_options.filter(optionname="Alternate wetting and drying is practiced with multiple drain events.").exists()
                            if multi_drain_value_check == True:
                                drain_event = 83
                                print("drain_event",drain_event)
                            else:
                                drain_event = 39
                                print("drain_event",drain_event) 
                            previous_crop_is_present = grower_input_no2.get_options.filter(optionname="The previous crop was either soybean, rice, corn or fallow. The previous residue was removed.")
                            if previous_crop_is_present.exists():
                                # print("yesss")
                                grower_input_no2 = InputSurvey.objects.filter(field_id=context['selectedField'].id,questionsurvey_id=149)
                                select_score = grower_input_no2.first().optionscore
                                select_score1 = grower_input_no2.first().optionscore_ids
                                print("select_score",select_score1)
                                # select_score1 = OptionSurvey.objects.filter(questionsurvey_id=149).values("id","optionname","optionscore")
                                # print("select_score1",select_score1)
                                select_option_lst = list(OptionSurvey.objects.filter(questionsurvey_id=149).values_list("optionscore" , flat =True))
                                # print("select_option_lst_test",select_option_lst_test)
                                list_1 = [select_option_lst[0], select_option_lst[-1]] # FOR[0,5]
                                list_2 = select_option_lst[1:-1] # FOR[1,2,3,4]
                                if select_score in list_2:
                                    ss_value = 0
                                    print("ss_value",ss_value)
                                elif select_score in list_1:  
                                    ss_value = 54 
                                    print("ss_value",ss_value) 
                                else:
                                    pass   
                                
                                if ss_value == 0:
                                    prev_crop = 46
                                    print("prev_crop",prev_crop) 
                                elif ss_value == 54:  
                                    prev_crop = 0  
                                    print("prev_crop",prev_crop)
                                else:
                                    pass 
                            else:
                                ss_value = 0
                                prev_crop = 0

                            if var_less_ghg["less_ghg_flag"] :
                                less_ghg_value = var_less_ghg["less_ghg_value"]
                                print(less_ghg_value)
                                net_value = (272.5-(5.5*less_ghg_value)) - prev_crop - ss_value - drain_event
                                print("net_value",net_value)
                                context["less_ghg_value"] = round(net_value,2)
                                context["total_less_ghg_value"] = 100 - net_value   

                                # net_value = (272.5-(5.5*less_ghg_value)) - prev_crop - ss_value - 39    
                                
                                # acreage = float(context['selectedField'].acreage)
                                # base_value = 120
                                # acreage_mul_base_value = acreage * base_value
                                # toatl_pounds = total_net_wt
                                # if toatl_pounds != 0 :
                                #     if acreage_mul_base_value > toatl_pounds :
                                #         net_value = round(((toatl_pounds - acreage_mul_base_value) / acreage_mul_base_value) * 100,2)
                                #     else:
                                #         net_value = round(((toatl_pounds - acreage_mul_base_value) / toatl_pounds) * 100,2)
                                #     context["less_ghg_value"] = net_value
                                #     context["total_less_ghg_value"] = 100 - net_value  
                                # else:
                                #     context['less_ghg_error_msg'] = "Survey data not found"    
                            else:
                                context['less_ghg_error_msg'] = "Survey data not found"
                        else:
                            context['less_ghg_error_msg'] = "Survey data not found"
                            # context['error_msg'] = "Survey data not found"
        # print("context",context)               
        return render(request, 'grower/sustainable_product_claims.html', context)
    else:
        return redirect ('dashboard')


@login_required()
def sustainable_get_certificate(request,corps,field_id,grower_id):
    context = {}
    scheme = 'https' if request.is_secure() else 'http'
    main_static_url = f"{scheme}://{request.META['HTTP_HOST']}/static"
    get_grower = Grower.objects.get(id=grower_id)
    get_field = Field.objects.get(id=field_id)
    field_name = " ".join(get_field.name.split()) 

    water_savings_efficiency = request.GET.get('water_savings_efficiency')
    land_use_efficiency = request.GET.get('land_use_efficiency')
    total_gallons_water_saved = request.GET.get('total_gallons_water_saved')
    less_ghg_value = request.GET.get('less_ghg_value')
    co2eq_claims = request.GET.get('co2eq_claims')
    grower_premium_percent1 = request.GET.get('grower_premium_percent1')
    if not grower_premium_percent1:
        grower_premium_percent1 = 0
     
    template = get_template('grower/sustainable_get_certificate.html')
    html_content = template.render({'main_static_url': main_static_url,"grower_name":get_grower.name,"field_name":get_field.name,"corp":get_field.crop,
                                    "water_savings_efficiency":water_savings_efficiency,"land_use_efficiency":land_use_efficiency,
                                    "total_gallons_water_saved":round(float(total_gallons_water_saved),2),"less_ghg_value":less_ghg_value,
                                    "co2eq_claims":co2eq_claims,"grower_premium_percent1":grower_premium_percent1})
    response = HttpResponse(content_type='application/pdf')
    
    # response['Content-Disposition'] = f'filename="{get_field.name}.pdf"'
    response['Content-Disposition'] = f'filename="{field_name}.pdf"'

    # Create a BytesIO buffer to receive PDF data.
    buffer = BytesIO()

    # Create the PDF object, using the BytesIO buffer as its "file."
    pisa.CreatePDF(BytesIO(html_content.encode("UTF-8")), buffer)

    # Use response object for the PDF and return
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response
    # return render(request, 'grower/sustainable_get_certificate.html', context)


@login_required()
def seUser(request):
    # alls = User.objects.all().order_by("id").exclude(is_superuser=True)


    # a1 = list(alls.filter(role__role__in=['SuperUser']).values("id","email"))
    # a2 = list(alls.filter(role__role__in=['SubAdmin']).values("id","email"))
    
    # original_list = a1 + a2
    # print(len(original_list))
    # filtered_list1 = [item["id"] for item in original_list if '@agreeta.com' in item['email']]
    # var = alls.exclude(id__in=[1329,1591])
    # var2 = var.exclude(id__in=filtered_list1)
    # filtered_list2 = alls.exclude(id__in=[1329,1591])
    # print(len(filtered_list1),filtered_list1)
    all1 = User.objects.all().order_by("id").exclude(is_superuser=True).values("id","email")
    filtered_list1 = [item["id"] for item in all1 if '@agreeta.com' in item['email']]
    all2 = all1.exclude(id__in=[1329,1591,1460])
    all3 = all2.exclude(id__in=filtered_list1)
    print(all3)
    for i in all3 :
        guser = User.objects.get(id=i["id"])
        guser.is_active = False
        guser.save()
    return HttpResponse (1)