'''Classes and functions for Grower Dashboard'''
#pylint: disable=no-member
import os
import pandas as pd
from django.db.models import Avg, Count, Q
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from apps.field.models import Field
from apps.grower.models import Consultant, Grower, GrowerChecklist
from apps.farms.models import Farm
from agfarm.settings import MEDIA_ROOT, MEDIA_URL
from apps.accounts.models import User, Role, SubSuperUser
from apps.contracts.models import GrowerContracts, SignedContracts
from apps.field.models import Field, ShapeFileDataCo
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
                shp = ShapeFileDataCo.objects.filter(field_id__in=field_id)
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
                shp = ShapeFileDataCo.objects.filter(field_id__in=field_id)
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
                shp = ShapeFileDataCo.objects.filter(field_id__in=field_id)
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
                shp = ShapeFileDataCo.objects.filter(field_id__in=field_id)
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
            context['grower'] = grower
        elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            context = {}
            grower = Grower.objects.all().order_by('name')
            context['grower'] = grower
        return render(request,'grower/checklist_comparison.html',context)
    else:
        return redirect('login')


class GorwerDashboardViewMain(View):
    '''For displaying main page of Grower Dashboard'''

    def get(self, request):
        '''Default function for get request'''

        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
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

        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
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

        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
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
            if len([i.id for i in grower_fields]) > 0  and chat_field_id == None :
                context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart([i.id for i in grower_fields][0])
                context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart([i.id for i in grower_fields][0])
                context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details([i.id for i in grower_fields][0])
                # grower_surveys
                context['grower_surveys'] = grower_Field_Surveys_Details([i.id for i in grower_fields][0])
            else:
                if chat_field_id :
                    check_field = Field.objects.filter(id=chat_field_id,grower_id=get_grower)
                    if len(check_field) == 1 :
                        context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart(chat_field_id)
                        context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart(chat_field_id)
                        context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details(chat_field_id)
                        context['grower_surveys'] = grower_Field_Surveys_Details(chat_field_id)
                        context['selcted_filed'] = Field.objects.get(id=chat_field_id)

        # /all/    
        else:
            if request.method == 'POST' :
                get_grower = request.POST.get('get_grower')
                chat_field_id = request.POST.get('chat_field_id')
                context['show_grower'] = get_grower
                
                # Dropdown Grower Search
                if get_grower and get_grower != '' :
                    check_grower = Grower.objects.filter(id = get_grower)
                    
                    if len(check_grower) == 1 :
                        grower_id = [i.id for i in check_grower][0]
                        context['select_get_grower_id'] = grower_id
                        context['select_get_grower_name'] = [i.name for i in check_grower][0]
                        grower_farms = get_Grower_Farms(grower_id)
                        context['grower_farms'] = grower_farms
                        grower_fields = get_Grower_Fields(grower_id)
                        context['grower_fields'] = grower_fields
                        grower_storages = get_Grower_Stogares(grower_id)
                        context['grower_storages'] = grower_storages
                        # grower_payments
                        grower_payments = get_Grower_Payments(grower_id)
                        context['grower_payments'] = grower_payments
        
                        if len([i.id for i in grower_fields]) > 0  and chat_field_id == None :
                            context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart([i.id for i in grower_fields][0])
                            context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart([i.id for i in grower_fields][0])
                            context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details([i.id for i in grower_fields][0])
                            # grower_surveys
                            context['grower_surveys'] = grower_Field_Surveys_Details([i.id for i in grower_fields][0])
                        else:
                            if chat_field_id :
                                check_field = Field.objects.filter(id=chat_field_id,grower_id=get_grower)
                                if len(check_field) == 1 :
                                    context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart(chat_field_id)
                                    context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart(chat_field_id)
                                    context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details(chat_field_id)
                                    context['grower_surveys'] = grower_Field_Surveys_Details(chat_field_id)
                                    context['selcted_filed'] = Field.objects.get(id=chat_field_id)
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
            if len([i.id for i in grower_fields]) > 0  and chat_field_id == None :
                context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart([i.id for i in grower_fields][0])
                context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart([i.id for i in grower_fields][0])
                context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details([i.id for i in grower_fields][0])
                # grower_surveys
                context['grower_surveys'] = grower_Field_Surveys_Details([i.id for i in grower_fields][0])
            else:
                if chat_field_id :
                    check_field = Field.objects.filter(id=chat_field_id,grower_id=get_grower)
                    if len(check_field) == 1 :
                        context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart(chat_field_id)
                        context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart(chat_field_id)
                        context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details(chat_field_id)
                        context['grower_surveys'] = grower_Field_Surveys_Details(chat_field_id)
                        context['selcted_filed'] = Field.objects.get(id=chat_field_id)
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
                    check_grower = growers.filter(id=get_grower)
                    if len(check_grower) == 1 :
                        grower_id = [i.id for i in check_grower][0]
                        context['select_get_grower_id'] = grower_id
                        context['select_get_grower_name'] = [i.name for i in check_grower][0]
                        grower_farms = get_Grower_Farms(grower_id)
                        context['grower_farms'] = grower_farms
                        grower_fields = get_Grower_Fields(grower_id)
                        context['grower_fields'] = grower_fields
                        grower_storages = get_Grower_Stogares(grower_id)
                        context['grower_storages'] = grower_storages
                        # grower_payments
                        grower_payments = get_Grower_Payments(grower_id)
                        context['grower_payments'] = grower_payments
        
                        if len([i.id for i in grower_fields]) > 0  and chat_field_id == None :
                            context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart([i.id for i in grower_fields][0])
                            context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart([i.id for i in grower_fields][0])
                            context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details([i.id for i in grower_fields][0])
                            # grower_surveys
                            context['grower_surveys'] = grower_Field_Surveys_Details([i.id for i in grower_fields][0])
                        else:
                            if chat_field_id :
                                check_field = Field.objects.filter(id=chat_field_id,grower_id=get_grower)
                                if len(check_field) == 1 :
                                    context['grower_Field_Vegetation_Chart'] = grower_Field_Vegetation_Chart(chat_field_id)
                                    context['grower_Field_Shipment_Chart'] = grower_Field_Shipment_Chart(chat_field_id)
                                    context['grower_Field_Shipment_Details'] = grower_Field_Shipment_Details(chat_field_id)
                                    context['grower_surveys'] = grower_Field_Surveys_Details(chat_field_id)
                                    context['selcted_filed'] = Field.objects.get(id=chat_field_id)
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
    for i in entry :
        g_payment_option.append({"payment_option":i.contracted_payment_option,"payment_option_from_date":i.from_date,"payment_option_to_date":i.to_date})
      
    # payment_option = [i.contracted_payment_option for i in entry]
    # payment_option_from_date = [i.from_date for i in entry]
    # payment_option_to_date = [i.to_date for i in entry]
    
    lst_delivery_lbs =[]
    for i in g_payment :
        if i.delivery_lbs :
            lst_delivery_lbs.append(float(i.delivery_lbs))
    
    # g_payee = GrowerPayee.objects.filter(grower_id=g_id)
    # lien_holder_count = g_payee.filter(lien_holder_status='YES')
    # payment_split_count = g_payee.filter(payment_split_status='YES')
    sum_delivery_lbs = f'{sum(lst_delivery_lbs)} LBS'
    sum_delivered_value = f'$ {sum([int(float(i.payment_amount)) for i in g_payment])}'

    res = {"sum_delivery_lbs":sum_delivery_lbs,"sum_deliverys_count":g_payment.count(),"sum_deliverd_value":sum_delivered_value,"g_payment_option":g_payment_option}

           


    return res

def grower_Field_Surveys_Details(f_id) :
    sus = SustainabilitySurvey.objects.filter(field_id=f_id)
    res = []
    for i in sus :
        if i.field.crop == 'COTTON' :
            pass
        elif i.field.crop == 'RICE' :
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
            
            print("finale_date",finale_date,type(finale_date))

            
            res.append({'name':name,'shipment_wt':i.net_wt,'shipment_dt':str_date,
                        'payment_status':payment_status,'payment_amount':payment_amount,
                        'level':i.level,'shipment_id':i.bale_id,'finale_date':finale_date,
                        "yyyy":yyyy,"mm":mm,"dd":dd})
        return res
    
    else:
        return [{'name':name}]
    
