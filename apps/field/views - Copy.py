'''View Functions for Field app'''
from dataclasses import field
from sys import float_repr_style
import warnings
from threading import Thread

from django import forms
import pandas as pd
from apps.field.field_column import FieldColoumChoices
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.db.utils import IntegrityError
import csv
from apps.field.models import CsvToField, ShapeFileDataCo, FieldActivity, FieldUpdated
from apps.accounts.models import User, LogTable
from apps.farms.models import Farm
from apps.field.models import Field
from apps.grower.models import Consultant, Grower
from . import forms
import shapefile
from django.http import JsonResponse
import json
import requests
import datetime
import time
from datetime import date, timedelta
from django.utils.dateformat import DateFormat
from django.utils.formats import get_format
from django.contrib.auth.decorators import login_required
import geojson
import numpy as np
# import geopandas as gpd
import matplotlib.pyplot as plt
from descartes import PolygonPatch
import matplotlib.patches as mpatches

# code ..
from apps.field.serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

warnings.simplefilter(action='ignore', category=FutureWarning)


# pylint: disable=no-member,expression-not-assigned, too-many-locals, too-many-ancestors, too-many-ancestors, bare-except


def test(request):
    print('ok')
    
    
    # 07-04-23
    log_type, log_status, log_device = "Field", "Added", "Web"
    log_idd, log_name = None, request.POST.get('name')
    name = log_name
    farm = Farm.objects.get(id=request.POST.get('farm')).name if  request.POST.get('farm') else None
    grower = Grower.objects.get(id=request.POST.get('grower')).name if request.POST.get('grower') else None
    acreage = request.POST.get('acreage')
    crop = request.POST.get('crop')
    variety = request.POST.get('variety')

    log_details = f"name = {name} | farm = {farm} | grower = {grower} | acreage = {acreage} | crop = {crop} | variety = {variety}"
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
    
    name = request.POST.get('name')
    farm = request.POST.get('farm')
    grower = request.POST.get('grower')
    acreage = request.POST.get('acreage')
    

    batch_id = request.POST.get('batch_id')
    batch_id = batch_id if batch_id else None

    fsa_farm_number = request.POST.get('fsa_farm_number')
    fsa_farm_number = fsa_farm_number if fsa_farm_number else None

    fsa_tract_number = request.POST.get('fsa_tract_number')
    fsa_tract_number = fsa_tract_number if fsa_tract_number else None

    fsa_field_number = request.POST.get('fsa_field_number')
    fsa_field_number = fsa_field_number if fsa_field_number else None

    latitude = request.POST.get('latitude')
    latitude = latitude if latitude else None

    longitude = request.POST.get('longitude')
    longitude = longitude if longitude else None

    crop = request.POST.get('crop')
    crop = crop if crop else None

    variety = request.POST.get('variety')
    variety = variety if variety else None

    yield_per_acre = request.POST.get('yield_per_acre')
    yield_per_acre = yield_per_acre if yield_per_acre else None

    total_yield = request.POST.get('total_yield')
    total_yield = total_yield if total_yield else None

    crop_tech = request.POST.get('crop_tech')
    crop_tech = crop_tech if crop_tech else None


    # print(name,farm,grower,acreage,crop, batch_id, fsa_farm_number,fsa_tract_number,fsa_field_number,latitude,longitude,crop,variety,yield_per_acre,total_yield,crop_tech)
    Field(name=name,farm_id=farm,grower_id=grower,acreage=acreage,crop=crop,batch_id=batch_id,fsa_farm_number=fsa_farm_number,fsa_tract_number=fsa_tract_number,
    fsa_field_number=fsa_field_number,latitude=latitude,longitude=longitude,variety=variety,yield_per_acre=yield_per_acre,total_yield=total_yield,crop_tech=crop_tech).save()
    
    # field_Obj = Field.objects.all()[::-1]
    # print(field_Obj)
    # field_id = (field_Obj[0])
    # print('field_id', field_id)

    field = Field.objects.filter(name=name,farm_id=farm,grower_id=grower,acreage=acreage,crop=crop,batch_id=batch_id,fsa_farm_number=fsa_farm_number,fsa_tract_number=fsa_tract_number,
    fsa_field_number=fsa_field_number,latitude=latitude,longitude=longitude,variety=variety,yield_per_acre=yield_per_acre,total_yield=total_yield,crop_tech=crop_tech)
    field_obj= [i for i in field][-1]
    messages.success(request, '{} Created Successfully!'.format(field_obj.name))
    return redirect('field-update',pk=field_obj.id)



class FieldCreateView(LoginRequiredMixin, CreateView):
    '''Generic Class Based view to create a new field'''
    model = Field
    # fields = "__all__"
    form_class = forms.FarmForm
    template_name = 'field/field_create.html'
    # success_url = reverse_lazy('field-list')
    
    
    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new Field"""
        name = form.cleaned_data.get('name')
        # code ..
        plant_date = form.cleaned_data.get('plant_date')
        harvest_date = form.cleaned_data.get('harvest_date')
        
        messages.success(self.request, f'Field {name} Created Successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(FieldCreateView, self).get_context_data(**kwargs)
        
        if 'Grower' in self.request.user.get_role() and not self.request.user.is_superuser:
            # do something grower

            context["growers_dpdwn"] = Grower.objects.filter(
                id=self.request.user.grower.id).order_by('name')
            farms_data = Farm.objects.filter(
                grower_id=self.request.user.grower.id).order_by('name')
            context["farms"] = farms_data
            return context
        
        elif self.request.user.is_consultant:
            # do something consultant
            consultant_id = Consultant.objects.get(
                email=self.request.user.email).id
            get_growers = Grower.objects.filter(consultant=consultant_id)
            grower_ids = [data.id for data in get_growers]
            context["growers_dpdwn"] = Grower.objects.filter(
                id__in=grower_ids).order_by('name')
            farms_data = Farm.objects.filter(
                grower_id__in=grower_ids).order_by('name')
            context["farms"] = farms_data
            return context

        # do something allpower
        elif self.request.user.is_superuser or 'SubAdmin' in self.request.user.get_role() or 'SuperUser' in self.request.user.get_role():
            context["growers_dpdwn"] = Grower.objects.all().order_by('name')
            farms_data = Farm.objects.all().order_by('name')
            context["farms"] = farms_data
            return context



# class FieldListView(LoginRequiredMixin, ListView):
#     '''Generic Class Based view to list all the field objects in database'''
#     model = Field
#     template_name = 'field/field_list.html'
    

    # def get_queryset(self):
    #     """overriding the queryset to return all the fields in the database when a superuser is logged in,
    #     and to get only the fields mapped to the logged in user's grower"""
    #     # if self.request.user.is_superuser:
    #     #     return Field.objects.all().order_by('-created_date')
    #     # return Field.objects.filter(grower=self.request.user.grower).order_by('-created_date')
    #     # if self.request.user.is_consultant:
    #     #     consultant_id = Consultant.objects.get(email=self.request.user.email).id
    #     #     data = Grower.objects.raw("select id,grower_id from grower_grower_consultant where consultant_id=%s",[consultant_id])
    #     #     grower_ids = [id.grower_id for id in data]
    #     #     grower_data = Grower.objects.filter(id__in=grower_ids)
    #     #     return self.model.objects.filter(grower__in=grower_data).order_by('-created_date')
    #     # return self.model.objects.all().order_by('-created_date')
    #     if 'Grower' in self.request.user.get_role() and not self.request.user.is_superuser:
    #         # do something grower
    #         # SustainabilitySurvey_data = SustainabilitySurvey.objects.filter(grower_id=request.user.grower.id)
    #         return self.model.objects.filter(grower_id=self.request.user.grower.id).order_by('-created_date')

    #     else:
    #         if self.request.user.is_consultant:
    #             # do something consultant
    #             consultant_id = Consultant.objects.get(
    #                 email=self.request.user.email).id
    #             get_growers = Grower.objects.filter(consultant=consultant_id)
    #             grower_ids = [data.id for data in get_growers]
    #             grower_data = Grower.objects.filter(id__in=grower_ids)
    #             if self.request.GET.get('field_name'):
    #                 consultant_id = Consultant.objects.get(email=self.request.user.email).id
                    
    #                 get_growers = Grower.objects.filter(consultant=consultant_id)
    #                 grower_ids = [data.id for data in get_growers]
    #                 grower_data = Grower.objects.filter(id__in=grower_ids)
    #                 field_name_search = self.request.GET.get('field_name')
    #                 object_list = self.model.objects.filter(name__icontains=field_name_search).filter(grower__in=grower_data).order_by('-created_date')
    #                 if object_list.count() == 0 :
    #                     consultant_id = Consultant.objects.get(email=self.request.user.email).id
    #                     get_growers = Grower.objects.filter(consultant=consultant_id)
    #                     grower_ids = [data.id for data in get_growers]
    #                     grower_data = Grower.objects.filter(id__in=grower_ids)
    #                     field_name_search = self.request.GET.get('field_name')
    #                     farms = (Farm.objects.filter(name__icontains=field_name_search).order_by('-created_date'))
    #                     object_list = self.model.objects.filter(farm__in=farms).filter(grower__in=grower_data).order_by('-created_date')
    #                     return object_list
    #                 return object_list
    #             return self.model.objects.filter(grower__in=grower_data).order_by('-created_date')

    #         else:
    #             # do something allpower
    #             if self.request.GET.get('field_name'):
    #                 field_name_search = self.request.GET.get('field_name')
    #                 object_list = self.model.objects.filter(name__icontains=field_name_search).order_by('-created_date')
    #                 if object_list.count() == 0 :
    #                     farms = (Farm.objects.filter(name__icontains=field_name_search).order_by('-created_date'))
    #                     object_list = self.model.objects.filter(farm__in=farms)
                        
    #                 # print(self.model.objects.filter(farm_id__in__icontains=field_name_search).order_by('-created_date'))
    #                 return object_list
    #             if self.request.GET.get('field_name_all'):
    #                 object_list = self.model.objects.all().order_by('-created_date')
    #                 return object_list
    #             servicedata = self.model.objects.all().order_by('-created_date')
                
    #             page = self.request.GET.get('page', 1)
    #             paginator = Paginator(servicedata, 100)
    #             try:
    #                 farm_list = paginator.page(page)
    #             except PageNotAnInteger:
    #                 farm_list = paginator.page(page)
    #             except EmptyPage:
    #                 farm_list = paginator.page(paginator.num_pages)
    #             servicedata_final = paginator.get_page(page)
                

    #             return servicedata_final
            
                # return self.model.objects.all().order_by('-created_date')
   
class FieldListView(LoginRequiredMixin, ListView):
    '''Generic Class Based view to list all the field objects in database'''
    model = Field
    template_name = 'field/field_list.html'
                
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Grower ....
        if 'Grower' in self.request.user.get_role() and not self.request.user.is_superuser:
            context['object_list'] = self.model.objects.filter(grower_id=self.request.user.grower.id).order_by('-created_date')
            return context
        
        # consultant ...
        elif self.request.user.is_consultant:
            # do something consultant
            consultant_id = Consultant.objects.get(email=self.request.user.email).id
            get_growers = Grower.objects.filter(consultant=consultant_id).order_by('name')
            object_list = self.model.objects.filter(grower__in=get_growers).order_by('-created_date')
            # context['object_list'] = object_list     
            context['growers'] = get_growers
            context['field_data'] = object_list.only('name')
            farm_data=Farm.objects.filter(grower__in=get_growers).only('name').order_by('name')
            context['farm_data'] = farm_data
            servicedata = object_list
            if self.request.GET.get('field_name') and self.request.GET.get('field_name') != 'all' :
                consultant_id = Consultant.objects.get(email=self.request.user.email).id
                get_growers = Grower.objects.filter(consultant=consultant_id).order_by('name')
                grower_ids = [data.id for data in get_growers]
                grower_data = Grower.objects.filter(id__in=grower_ids).order_by('name')
                field_name_search = self.request.GET.get('field_name')                
                object_list = self.model.objects.filter(name__icontains=field_name_search).filter(grower__in=grower_data).order_by('-created_date')
                context['field_name'] = field_name_search
                servicedata = object_list

            elif self.request.GET.get('farms_name') and self.request.GET.get('farms_name') != 'all' :
                farm_name_search = self.request.GET.get('farms_name')
                consultant_id = Consultant.objects.get(email=self.request.user.email).id
                get_growers = Grower.objects.filter(consultant=consultant_id).order_by('name')
                grower_ids = [data.id for data in get_growers]
                grower_data = Grower.objects.filter(id__in=grower_ids)
                field_name_search = self.request.GET.get('field_name')
                farms = Farm.objects.filter(name__icontains=farm_name_search).order_by('-created_date')
                object_list = self.model.objects.filter(farm__in=farms).filter(grower__in=grower_data).order_by('-created_date')
                servicedata = object_list
                context['farms_name'] = farm_name_search
                
            elif self.request.GET.get('crop_name') and self.request.GET.get('crop_name') != 'all' :
                crop_name_search = self.request.GET.get('crop_name')
                consultant_id = Consultant.objects.get(email=self.request.user.email).id
                get_growers = Grower.objects.filter(consultant=consultant_id).order_by('name')
                grower_ids = [data.id for data in get_growers]
                grower_data = Grower.objects.filter(id__in=grower_ids)
                object_list = self.model.objects.filter(grower__in=grower_data).filter(crop__icontains=crop_name_search).order_by('-created_date')
                servicedata = object_list
                context['crop_name'] = crop_name_search

            if self.request.GET.get('grower_id'):
                grower = int(self.request.GET.get('grower_id'))
                if grower != 0:
                    context['selectedGrower'] = Grower.objects.get(pk=grower)
                    object_list3 = object_list.filter(grower__id=grower)
                    servicedata = object_list3
            
            paginator = Paginator(servicedata, 100)
            page = self.request.GET.get('page', 1)
            farm_list = paginator.get_page(page)
            try:
                farm_list = paginator.page(page)
            except PageNotAnInteger:
                farm_list = paginator.page(page)
            except EmptyPage:
                farm_list = paginator.page(paginator.num_pages)
                
            servicedata_final=farm_list
            context['object_list'] = servicedata_final
            return context

        # all power ...
        elif self.request.user.is_superuser or 'SubAdmin' in self.request.user.get_role() or 'SuperUser' in self.request.user.get_role():
            # do something allpower
            growers = Grower.objects.all().order_by('name')
            field_data = Field.objects.only('name').order_by('name')           
            context['field_data'] = field_data
            farm_data=Farm.objects.only('name').order_by('name')
            context['farm_data'] = farm_data
            context['growers'] = growers
            servicedata = field_data
            if self.request.GET.get('field_name') and self.request.GET.get('field_name') != 'all' :
                field_name_search = self.request.GET.get('field_name')
                context['field_name'] = field_name_search
                object_list = self.model.objects.filter(name__icontains=field_name_search).order_by('-created_date')
                servicedata = object_list
                

            elif self.request.GET.get('farms_name') and self.request.GET.get('farms_name') != 'all' :
                farm_name_search = self.request.GET.get('farms_name')
                context['farms_name'] = farm_name_search
                farms = Farm.objects.filter(name__icontains=farm_name_search).order_by('-created_date')
                object_list1 = self.model.objects.filter(farm__in=farms).order_by('-created_date')
                servicedata = object_list1
                
            
            elif self.request.GET.get('crop_name') and self.request.GET.get('crop_name') != 'all' :
                crop_name_search = self.request.GET.get('crop_name')
                context['crop_name'] = crop_name_search
                object_list = self.model.objects.filter(crop__icontains=crop_name_search).order_by('-created_date')
                servicedata = object_list
                

            elif self.request.GET.get('field_name_all'):
                object_list2 = self.model.objects.all().order_by('-created_date')
                servicedata = object_list2
            
            elif self.request.GET.get('grower_id'):
                grower = int(self.request.GET.get('grower_id'))
                context['selectedGrower'] = Grower.objects.get(pk=grower)                
                object_list3 = self.model.objects.filter(grower__id=grower)
                servicedata = object_list3

        paginator = Paginator(servicedata, 100)
        page = self.request.GET.get('page', 1)
        farm_list = paginator.get_page(page)
        try:
            farm_list = paginator.page(page)
        except PageNotAnInteger:
            farm_list = paginator.page(page)
        except EmptyPage:
            farm_list = paginator.page(paginator.num_pages)
        servicedata_final=farm_list
        context['object_list'] = servicedata_final
            
        return context

            
class FieldDetailView(LoginRequiredMixin, DetailView):
    '''Generic Class Based View get the field details of a field created'''
    model = Field
    # code
    def get_context_data(self, **kwargs):
        the_field_id= self.kwargs.get('pk')
        pk= the_field_id
        data = self.model.objects.filter(id=the_field_id)
        context = {'data':data}
         # code ..
        field_Pre_Fert = FieldActivity.objects.filter(field_activity='Pre_Fert').filter(field_id = pk).order_by('-date_of_activity')
        field_activity_Early_Post_Fert =FieldActivity.objects.filter(field_activity='Early_Post_Fert').filter(field_id = pk).order_by('-date_of_activity')
        field_activity_Foliar_Fert_App =FieldActivity.objects.filter(field_activity='Foliar_Fert_App').filter(field_id = pk).order_by('-date_of_activity')
        field_activity_Pre_Flood_Fert =FieldActivity.objects.filter(field_activity='Pre_Flood_Fert').filter(field_id = pk).order_by('-date_of_activity')
        field_activity_Post_Flood_Mid_Season_Fert =FieldActivity.objects.filter(field_activity='Post_Flood_Mid_Season_Fert').filter(field_id = pk).order_by('-date_of_activity')
        field_activity_Boot_Fertilizer =FieldActivity.objects.filter(field_activity='Boot_Fertilizer').filter(field_id = pk).order_by('-date_of_activity')
        field_activity_Burndown_Chemical =FieldActivity.objects.filter(field_activity='Burndown_Chemical').filter(field_id = pk).order_by('-date_of_activity')
        field_activity_Preemergence_Chemical =FieldActivity.objects.filter(field_activity='Preemergence_Chemical').filter(field_id = pk).order_by('-date_of_activity')
        field_activity_Post_Emergence_Chemical =FieldActivity.objects.filter(field_activity='Post_Emergence_Chemical').filter(field_id = pk).order_by('-date_of_activity')
        field_activity_Fungicide_Micro_Nutrients =FieldActivity.objects.filter(field_activity='Fungicide_Micro_Nutrients').filter(field_id = pk).order_by('-date_of_activity')
        field_activity_Insecticide_Application =FieldActivity.objects.filter(field_activity='Insecticide_Application').filter(field_id = pk).order_by('-date_of_activity')
        field_activity_Litter =FieldActivity.objects.filter(field_activity='Litter').filter(field_id = pk).order_by('-date_of_activity')
        field_activity_Sodium_Chlorate =FieldActivity.objects.filter(field_activity='Sodium_Chlorate').filter(field_id = pk).order_by('-date_of_activity')

        field_activity_npk =FieldActivity.objects.filter(field_activity='NPK_Application').filter(field_id = pk).order_by('-date_of_activity')

        
        context["field_Pre_Fert"] = field_Pre_Fert
        context["field_activity_Early_Post_Fert"] = field_activity_Early_Post_Fert
        context["field_activity_Foliar_Fert_App"] = field_activity_Foliar_Fert_App
        context["field_activity_Pre_Flood_Fert"] = field_activity_Pre_Flood_Fert
        context["field_activity_Post_Flood_Mid_Season_Fert"] = field_activity_Post_Flood_Mid_Season_Fert
        context["field_activity_Boot_Fertilizer"] = field_activity_Boot_Fertilizer
        context["field_activity_Burndown_Chemical"] = field_activity_Burndown_Chemical
        context["field_activity_Preemergence_Chemical"] = field_activity_Preemergence_Chemical
        context["field_activity_Post_Emergence_Chemical"] = field_activity_Post_Emergence_Chemical
        context["field_activity_Fungicide_Micro_Nutrients"] = field_activity_Fungicide_Micro_Nutrients
        context["field_activity_Insecticide_Application"] = field_activity_Insecticide_Application
        context["field_activity_Litter"] = field_activity_Litter
        context["field_activity_Sodium_Chlorate"] = field_activity_Sodium_Chlorate

        context["field_activity_npk"] = field_activity_npk
        
        sum_Pre_Fert = sum([i.amount_per_acre for i in field_Pre_Fert])
        context["sum_Pre_Fert"] = sum_Pre_Fert

        sum_Early_Post_Fert = sum([i.amount_per_acre for i in field_activity_Early_Post_Fert])
        context["sum_Early_Post_Fert"] = sum_Early_Post_Fert

        sum_Foliar_Fert_App = sum([i.amount_per_acre for i in field_activity_Foliar_Fert_App])
        context["sum_Foliar_Fert_App"] = sum_Foliar_Fert_App

        sum_Pre_Flood_Fert = sum([i.amount_per_acre for i in field_activity_Pre_Flood_Fert])
        context["sum_Pre_Flood_Fert"] = sum_Pre_Flood_Fert

        sum_Flood_Mid_Season_Fert = sum([i.amount_per_acre for i in field_activity_Post_Flood_Mid_Season_Fert])
        context["sum_Flood_Mid_Season_Fert"] = sum_Flood_Mid_Season_Fert

        sum_Boot_Fertilizer = sum([i.amount_per_acre for i in field_activity_Boot_Fertilizer])
        context["sum_Boot_Fertilizer"] = sum_Boot_Fertilizer

        sum_Burndown_Chemical = sum([i.amount_per_acre for i in field_activity_Burndown_Chemical])
        context["sum_Burndown_Chemical"] = sum_Burndown_Chemical

        sum_Preemergence_Chemical = sum([i.amount_per_acre for i in field_activity_Preemergence_Chemical])
        context["sum_Preemergence_Chemical"] = sum_Preemergence_Chemical

        sum_Post_Emergence_Chemical = sum([i.amount_per_acre for i in field_activity_Post_Emergence_Chemical])
        context["sum_Post_Emergence_Chemical"] = sum_Post_Emergence_Chemical

        sum_Fungicide_Micro_Nutrients = sum([i.amount_per_acre for i in field_activity_Fungicide_Micro_Nutrients])
        context["sum_Fungicide_Micro_Nutrients"] = sum_Fungicide_Micro_Nutrients

        sum_Insecticide_Application = sum([i.amount_per_acre for i in field_activity_Insecticide_Application])
        context["sum_Insecticide_Application"] = sum_Insecticide_Application

        sum_Litter = sum([i.amount_per_acre for i in field_activity_Litter])
        context["sum_Litter"] = sum_Litter

        sum_Sodium_Chlorate = sum([i.amount_per_acre for i in field_activity_Sodium_Chlorate])
        context["sum_Sodium_Chlorate"] = sum_Sodium_Chlorate

        sum_nitrogen = sum([i.n_nitrogen for i in field_activity_npk])
        context["sum_nitrogen"] = sum_nitrogen

        sum_phosporus = sum([i.p_phosporus for i in field_activity_npk])
        context["sum_phosporus"] = sum_phosporus

        sum_potassium = sum([i.k_potassium for i in field_activity_npk])
        context["sum_potassium"] = sum_potassium
        
        return context

# fieldActivity Delete ...
def fieldActivity_delete(request,pk):
    fati = FieldActivity.objects.get(id=pk)
    # 25-04-23 LogTable
    log_type, log_status, log_device = "FieldActivity", "Deleted", "Web"
    log_idd, log_name = fati.id, fati.field.name
    log_details = f"field = {fati.field.name} | field_id = {fati.field.id} | grower = {fati.field.grower.name} | grower_id = {fati.field.grower.id} | crop = {fati.field.crop} | field_activity = {fati.field_activity} | date_of_activity = {fati.date_of_activity} | type_of_application = {fati.type_of_application} | mode_of_application = {fati.mode_of_application} | label_name = {fati.label_name} | amount_per_acre = {fati.amount_per_acre} | unit_of_acre = {fati.unit_of_acre} | n_nitrogen = {fati.n_nitrogen} | p_phosporus = {fati.p_phosporus} | k_potassium = {fati.k_potassium} | special_notes = {fati.special_notes} |"
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
    fati.delete()
    return HttpResponse(1)


def fieldEditLogTable(userid, log_idd, edited_field):
    # 21-06-23 LogTable
    log = Field.objects.get(id=log_idd)
    log_type, log_status, log_device = "Field", "Edited", "Web"
    log_idd, log_name = log_idd, log.name
    log_details = f"field = {log.name} | field_id = {log_idd} | edited_field = {edited_field} | grower = {log.grower.name} | grower_id = {log.grower.id} | crop = {log.crop} |"
    action_by_userid = userid
    user = User.objects.get(pk=action_by_userid)
    user_role = user.role.all()
    action_by_username = f'{user.first_name} {user.last_name}'
    action_by_email = user.username
    if userid == 1 :
        action_by_role = "superuser"
    else:
        action_by_role = str(','.join([str(i.role) for i in user_role]))
    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                        log_device=log_device)
    logtable.save()

# fieldActivity..
def fieldActivity(request):
    # var_select 
    userid = request.user.id
    context = {}
    variety = request.POST.get('variety')
    hidden_field_id = request.POST.get('hidden_field_id')
    
    # Field Update Data.. 
    hidden_field_name = request.POST.get('hidden_field_name')
    hidden_field_farm = request.POST.get('hidden_field_farm')
    hidden_field_grower = request.POST.get('hidden_field_grower')
    hidden_field_batch_id = request.POST.get('hidden_field_batch_id')
    hidden_field_acreage = request.POST.get('hidden_field_acreage')
    hidden_field_fsa_farm_number = request.POST.get('hidden_field_fsa_farm_number')
    hidden_field_fsa_tract_number = request.POST.get('hidden_field_fsa_tract_number')
    hidden_field_fsa_field_number = request.POST.get('hidden_field_fsa_field_number')
    hidden_field_latitude = request.POST.get('hidden_field_latitude')
    hidden_field_longitude = request.POST.get('hidden_field_longitude')
    hidden_field_crop = request.POST.get('hidden_field_crop')
    hidden_field_yield_per_acre = request.POST.get('hidden_field_yield_per_acre')
    hidden_field_total_yield = request.POST.get('hidden_field_total_yield')
    hidden_field_crop_tech = request.POST.get('hidden_field_crop_tech')
    hidden_field_plant_date = request.POST.get('hidden_field_plant_date')
    hidden_field_harvest_date = request.POST.get('hidden_field_harvest_date')

    hidden_field_stand_count = request.POST.get('hidden_field_stand_count')
    hidden_field_previous_crop = request.POST.get('hidden_field_previous_crop')

    hidden_field_crop_year = request.POST.get('hidden_field_crop_year')
    hidden_field_updated_field_id = request.POST.get('hidden_field_updated_field_id')
    hidden_field_crop_variety = request.POST.get('hidden_field_crop_variety')

    field_obj = Field.objects.get(id=int(hidden_field_id))

    if hidden_field_crop_year and len(hidden_field_crop_year) != 0 :
        context['selected_scrop_year'] = hidden_field_crop_year

    if hidden_field_updated_field_id and hidden_field_crop_year :
        field_save_old = FieldUpdated.objects.get(id=hidden_field_updated_field_id)
        if len(hidden_field_crop_variety) != 0 :
            field_save_old.variety = hidden_field_crop_variety
            field_save_old.save()
            fieldEditLogTable(userid, hidden_field_id, f'variety = {hidden_field_crop_variety}, crop_year = {hidden_field_crop_year}')

        if len(hidden_field_yield_per_acre) != 0 :
            field_save_old.yield_per_acre = hidden_field_yield_per_acre
            field_save_old.save()
            fieldEditLogTable(userid, hidden_field_id, f'yield_per_acre = {hidden_field_yield_per_acre}, crop_year = {hidden_field_crop_year}')

        if len(hidden_field_total_yield) != 0 :
            field_save_old.total_yield = hidden_field_total_yield
            field_save_old.save()
            fieldEditLogTable(userid, hidden_field_id, f'total_yield = {hidden_field_total_yield}, crop_year = {hidden_field_crop_year}')

        if len(hidden_field_crop_tech) != 0 :
            field_save_old.crop_tech = hidden_field_crop_tech
            field_save_old.save()
            fieldEditLogTable(userid, hidden_field_id, f'crop_tech = {hidden_field_total_yield}, crop_year = {hidden_field_crop_year}')

        if len(hidden_field_previous_crop) != 0 :
            field_save_old.previous_crop = hidden_field_previous_crop
            field_save_old.save()
            fieldEditLogTable(userid, hidden_field_id, f'previous_crop = {hidden_field_previous_crop}, crop_year = {hidden_field_crop_year}')

        if len(hidden_field_stand_count) != 0 :
            field_save_old.stand_count = hidden_field_stand_count
            field_save_old.save()
            fieldEditLogTable(userid, hidden_field_id, f'stand_count = {hidden_field_stand_count}, crop_year = {hidden_field_crop_year}')

        if len(hidden_field_plant_date) != 0 :
            field_save_old.plant_date = hidden_field_plant_date
            field_save_old.save()
            fieldEditLogTable(userid, hidden_field_id, f'plant_date = {hidden_field_plant_date}, crop_year = {hidden_field_crop_year}')

        if len(hidden_field_harvest_date) != 0 :
            field_save_old.harvest_date = hidden_field_harvest_date
            field_save_old.save()
            fieldEditLogTable(userid, hidden_field_id, f'harvest_date = {hidden_field_harvest_date}, crop_year = {hidden_field_crop_year}')

        field_updated_id = hidden_field_updated_field_id
    else:
        hidden_field_yield_per_acre = hidden_field_yield_per_acre if hidden_field_yield_per_acre else field_obj.yield_per_acre
        hidden_field_total_yield = hidden_field_total_yield if hidden_field_total_yield else field_obj.total_yield
        hidden_field_stand_count = hidden_field_stand_count if hidden_field_stand_count else None
        hidden_field_plant_date = hidden_field_plant_date if hidden_field_plant_date else None
        hidden_field_harvest_date = hidden_field_harvest_date if hidden_field_harvest_date else None
        hidden_field_crop = field_obj.crop
        field_save_new = FieldUpdated(field_id=hidden_field_id,name=hidden_field_name,crop_year="2023",fsa_farm_number=hidden_field_fsa_farm_number,
                     fsa_tract_number=hidden_field_fsa_tract_number,fsa_field_number=hidden_field_fsa_field_number,crop=hidden_field_crop,
                     yield_per_acre=hidden_field_yield_per_acre,total_yield=hidden_field_total_yield,crop_tech=hidden_field_crop_tech,
                     previous_crop=hidden_field_previous_crop,stand_count=hidden_field_stand_count,plant_date=hidden_field_plant_date,
                     harvest_date=hidden_field_harvest_date,variety=hidden_field_crop_variety)
        field_save_new.save()
        fieldEditLogTable(userid, hidden_field_id, f'crop_year = 2023, Data Added')
        field_updated_id = field_save_new.id

        

    

    # if len(hidden_field_previous_crop) !=0:
    #     field_obj.previous_crop = hidden_field_previous_crop
    #     field_obj.save()

    # if len(hidden_field_stand_count) !=0:
    #     field_obj.stand_count = hidden_field_stand_count
    #     field_obj.save()

    # if len(hidden_field_plant_date) !=0:
    #     field_obj.plant_date = hidden_field_plant_date
    #     field_obj.save()

    # if len(hidden_field_harvest_date) !=0:
    #     field_obj.harvest_date = hidden_field_harvest_date
    #     field_obj.save()

    if len(hidden_field_name) != 0 :
        field_obj.name = hidden_field_name
        field_obj.save()
        fieldEditLogTable(userid, hidden_field_id, f'field_name = {hidden_field_name}, crop_year = {hidden_field_crop_year}')

    if len(hidden_field_farm) != 0 :
        field_obj.farm_id = int(hidden_field_farm)
        field_obj.save()
        fieldEditLogTable(userid, hidden_field_id, f'farm_id = {hidden_field_farm}, crop_year = {hidden_field_crop_year}')
    
    if len(hidden_field_grower) != 0 :
        field_obj.grower_id = int(hidden_field_grower)
        field_obj.save()
        fieldEditLogTable(userid, hidden_field_id, f'grower_id = {hidden_field_grower}, crop_year = {hidden_field_crop_year}')
    
    if len(hidden_field_batch_id) != 0 :
        field_obj.batch_id = int(hidden_field_batch_id)
        field_obj.save()
        fieldEditLogTable(userid, hidden_field_id, f'batch_id = {hidden_field_batch_id}, crop_year = {hidden_field_crop_year}')

    
    if len(hidden_field_acreage) != 0 :
        field_obj.acreage = float(hidden_field_acreage)
        field_obj.save()
        fieldEditLogTable(userid, hidden_field_id, f'acreage = {hidden_field_acreage}, crop_year = {hidden_field_crop_year}')

    if len(hidden_field_fsa_farm_number) != 0 :
        field_obj.fsa_farm_number = int(hidden_field_fsa_farm_number)
        field_obj.save()
        fieldEditLogTable(userid, hidden_field_id, f'fsa_farm_number = {hidden_field_fsa_farm_number}, crop_year = {hidden_field_crop_year}')

    if len(hidden_field_fsa_tract_number) != 0 :
        field_obj.fsa_tract_number = int(hidden_field_fsa_tract_number)
        field_obj.save()
        fieldEditLogTable(userid, hidden_field_id, f'fsa_tract_number = {hidden_field_fsa_tract_number}, crop_year = {hidden_field_crop_year}')

    if len(hidden_field_fsa_field_number) != 0 :
        field_obj.fsa_field_number = int(hidden_field_fsa_field_number)
        field_obj.save()
        fieldEditLogTable(userid, hidden_field_id, f'fsa_field_number = {hidden_field_fsa_field_number}, crop_year = {hidden_field_crop_year}')

    if len(hidden_field_latitude) != 0 :
        field_obj.latitude = float(hidden_field_latitude)
        field_obj.save()
        fieldEditLogTable(userid, hidden_field_id, f'latitude = {hidden_field_latitude}, crop_year = {hidden_field_crop_year}')

    if len(hidden_field_longitude) != 0 :
        field_obj.longitude = float(hidden_field_longitude)
        field_obj.save()
        fieldEditLogTable(userid, hidden_field_id, f'longitude = {hidden_field_longitude}, crop_year = {hidden_field_crop_year}')

    # if len(hidden_field_crop) != 0 :
    #     field_obj.crop = hidden_field_crop
    #     field_obj.save()
    #     fieldEditLogTable(userid, hidden_field_id, f'crop = {hidden_field_crop}, crop_year = {hidden_field_crop_year}')

    # if len(hidden_field_yield_per_acre) != 0 :
    #     field_obj.yield_per_acre = float(hidden_field_yield_per_acre)
    #     field_obj.save()

    # if len(hidden_field_total_yield) != 0 :
    #     field_obj.total_yield = float(hidden_field_total_yield)
    #     field_obj.save()

    # if len(hidden_field_crop_tech) != 0 :
    #     field_obj.crop_tech = hidden_field_crop_tech
    #     field_obj.save()

    ##
    date_temp = request.POST.get('date')
    mode_of_application_temp = request.POST.get('mode_of_application')
    label_name_temp = request.POST.get('label_name')
    amount_per_acre_temp = request.POST.get('amount_per_acre')
    unit_of_acre_temp = request.POST.get('unit_of_acre')
    special_notes_temp = request.POST.get('special_notes')

    #NTK
    date_temp_2 = request.POST.get('date_2')
    mode_of_application_temp_2 = request.POST.get('mode_of_application_2')
    type_of_application_temp = request.POST.get('type_of_application')
    n_nitrogen_temp = request.POST.get('nitrogen')
    p_phosporus_temp = request.POST.get('phosporus')
    k_potassium_temp = request.POST.get('potassium')
    special_notes_temp_2 = request.POST.get('special_notes_2')
        
    # condition 20-06-23
    if variety == 'NPK_Application':
        fati_NPK = FieldActivity(field_id=int(hidden_field_id),field_activity=variety,date_of_activity=date_temp_2,mode_of_application=mode_of_application_temp_2,n_nitrogen=n_nitrogen_temp,p_phosporus=p_phosporus_temp,k_potassium=k_potassium_temp,special_notes=special_notes_temp_2,type_of_application=type_of_application_temp,field_updated_id=field_updated_id)
        fati_NPK.save()
        # 25-04-23 LogTable
        log_type, log_status, log_device = "FieldActivity", "Added", "Web"
        log_idd, log_name = fati_NPK.id, fati_NPK.field.name
        log_details = f"field = {fati_NPK.field.name} | field_id = {fati_NPK.field.id} | grower = {fati_NPK.field.grower.name} | grower_id = {fati_NPK.field.grower.id} | crop = {fati_NPK.field.crop} | field_activity = {fati_NPK.field_activity} | date_of_activity = {fati_NPK.date_of_activity} | type_of_application = {fati_NPK.type_of_application} | mode_of_application = {fati_NPK.mode_of_application} | label_name = | amount_per_acre = | unit_of_acre = | n_nitrogen = {fati_NPK.n_nitrogen} | p_phosporus = {fati_NPK.p_phosporus} | k_potassium = {fati_NPK.k_potassium} | special_notes = {fati_NPK.special_notes} |"
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
    else:
        fati = FieldActivity(field_id=int(hidden_field_id),field_activity=variety,date_of_activity=date_temp,mode_of_application=mode_of_application_temp,label_name=label_name_temp,amount_per_acre=amount_per_acre_temp,special_notes=special_notes_temp,unit_of_acre=unit_of_acre_temp,field_updated_id=field_updated_id)
        try:
            fati.save()
            # 25-04-23 LogTable
            log_type, log_status, log_device = "FieldActivity", "Added", "Web"
            log_idd, log_name = fati.id, fati.field.name
            log_details = f"field = {fati.field.name} | field_id = {fati.field.id} | grower = {fati.field.grower.name} | grower_id = {fati.field.grower.id} | crop = {fati.field.crop} | field_activity = {fati.field_activity} | date_of_activity = {fati.date_of_activity} | type_of_application = | mode_of_application = {fati.mode_of_application} | label_name = {fati.label_name} | amount_per_acre = {fati.amount_per_acre} | unit_of_acre = {fati.amount_per_acre} | n_nitrogen = | p_phosporus = | k_potassium = | special_notes = {fati.special_notes} |"
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
        except:
            pass 
       
    messages.success(request, f'Field {field_obj.name} Updated Successfully!')
    return redirect('field-update', hidden_field_id)


class FieldUpdateView(LoginRequiredMixin, UpdateView):
    '''Generic Class Based View to update a field created'''
    model = Field
    # fields = "__all__"
    form_class = forms.FarmForm
    template_name = 'field/field_update.html'
    success_url = reverse_lazy('field-list')

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new farm"""
        name = form.cleaned_data.get('name')
        farm = form.cleaned_data.get('farm')
        grower = form.cleaned_data.get('grower')
        acreage = form.cleaned_data.get('acreage')
        crop = form.cleaned_data.get('crop')
        variety = form.cleaned_data.get('variety')
        

        # 07-04-23
        log_type, log_status, log_device = "Field", "Edited", "Web"
        log_idd, log_name = self.kwargs.get('pk'), name
        log_details = f"name = {name} | farm = {farm} | grower = {grower} | acreage = {acreage} | crop = {crop} | variety = {variety}"
        action_by_userid = self.request.user.id
        user = User.objects.get(pk=action_by_userid)
        user_role = user.role.all()
        action_by_username = f'{user.first_name} {user.last_name}'
        action_by_email = user.username
        if self.request.user.id == 1 :
            action_by_role = "superuser"
        else:
            action_by_role = str(','.join([str(i.role) for i in user_role]))
        logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                            action_by_userid=action_by_userid,action_by_username=action_by_username,
                            action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                            log_device=log_device)
        logtable.save()

        messages.success(self.request, f'Field {name} Updated Successfully!')

        return super().form_valid(form)

    def get_context_data(self, **kwargs,):
        context = super(FieldUpdateView, self).get_context_data(**kwargs)
        pk = self.kwargs.get('pk')

        current_farm = self.model.objects.get(pk=pk)
        context['selected_grower'] = current_farm.grower_id
        context['selected_farm'] = current_farm.farm_id

              
        if 'Grower' in self.request.user.get_role() and not self.request.user.is_superuser:
            # do something grower

            context["growers_dpdwn"] = Grower.objects.filter(
                id=self.request.user.grower.id).order_by('name')
            farms_data = Farm.objects.filter(
                grower_id=self.request.user.grower.id).order_by('name')
            context["farms"] = farms_data
            # 21-06-23
            update_field = Field.objects.get(id = pk)
            context["update_field"] = update_field
            context["variety_list"] = ['DG-263L','DG-Wheat','DG3605','DG 1464','DG 2425 XF','DG 3215 B3XF','DG 3450 B2XF',
                                       'DG 3470 B3XF','DG 3570 B3XF','DG 3635 B2XF','DG 3544 B2XF','DG 3651NR B2XF','DG 3109 B2XF',
                                       'DG 3387 B3XF','DG 3421 B3XF','DG H929 B3XF','DG 3555 B3XF','DG 3402 B3XF','DG H959 B3XF',
                                       'DG 3469 B3XF','DG 3615 B3XF','DG P224 B3XF','DG 3385 B2XF','DG 3422 B3XF','DG 3799 B3XF']
            if self.request.method == 'POST':
                scrop_year = self.request.POST.get('scrop_year')
                fld_name = self.request.POST.get('fname')
                farm_id = self.request.POST.get('farm')
                grower_id = self.request.POST.get('grower')
                batch_id = self.request.POST.get('batch_id')
                acreage = self.request.POST.get('acreage')
                fsa_farm_number = self.request.POST.get('fsa_farm_number')
                fsa_tract_number = self.request.POST.get('fsa_tract_number')
                fsa_field_number = self.request.POST.get('fsa_field_number')
                latitude = self.request.POST.get('latitude')
                longitude = self.request.POST.get('longitude')
                crop = self.request.POST.get('crop')

                btnvariable = self.request.POST.get('btnvariable')

                if btnvariable == 'updateField' :
                    # save field Update Field Name ........
                    if fld_name and len(fld_name) > 0 and fld_name != update_field.name :
                        print('update name')
                        update_field.name = fld_name
                        update_field.save()
                    # save field Update Farm ID ........
                    if farm_id and len(farm_id) > 0 and str(farm_id) != str(update_field.farm.id) :
                        print('update Farm')
                        update_field.farm_id = farm_id
                        update_field.save()
                    # save field Update Grower ID ........
                    if grower_id and len(grower_id) > 0 and str(grower_id) != str(update_field.grower.id) :
                        print('update Grower')
                        update_field.grower_id = grower_id
                        update_field.save()
                    # save field Update Batch id ........
                    if batch_id and len(batch_id) > 0 and float(batch_id) != update_field.batch_id:
                        print('update Batch id')
                        update_field.batch_id = batch_id
                        update_field.save()
                    # save field Update Acreage ........
                    if acreage and len(acreage) > 0 and float(acreage) != update_field.acreage :
                        print('update Acreage')
                        update_field.acreage = acreage
                        update_field.save()
                    # save field Update FSA Farm Number ........
                    if fsa_farm_number and len(fsa_farm_number) > 0 and fsa_farm_number != update_field.fsa_farm_number :
                        print('update FSA Farm Number')
                        update_field.fsa_farm_number = fsa_farm_number
                        update_field.save()
                    # save field Update FSA Tract Number ........
                    if fsa_tract_number and len(fsa_tract_number) > 0 and fsa_tract_number != update_field.fsa_tract_number :
                        print('update FSA Tract Number')
                        update_field.fsa_tract_number = fsa_tract_number
                        update_field.save()
                    # save field Update FSA Field Number ........
                    if fsa_field_number and len(fsa_field_number) > 0 and fsa_field_number != update_field.fsa_field_number :
                        print('update FSA Field Numberr')
                        update_field.fsa_field_number = fsa_field_number
                        update_field.save()
                    # save field Update Latitude ........
                    if latitude and len(latitude) > 0 :
                        print('update Latitude')
                        update_field.latitude = latitude
                        update_field.save()
                    # save field Update Longitude ........
                    if longitude and len(longitude) > 0 :
                        print('update Longitude')
                        update_field.longitude = longitude
                        update_field.save()
                    # if crop and len(crop) > 0 and crop != update_field.crop :
                    #     print('update crop')
                    #     update_field.crop = crop
                    #     update_field.save()
                    messages.success(self.request, f'Field {fld_name} Updated Successfully!')
                    # 20-06-23
                    log_type, log_status, log_device = "Field", "Edited", "Web"
                    log_idd, log_name = pk, fld_name
                    farm_name = Farm.objects.get(id=farm_id)
                    grower_name = Grower.objects.get(id=grower_id)
                    log_details = f"name = {fld_name} | farm = {farm_name.name} | grower = {grower_name.name} | acreage = {acreage} | crop = {crop}"
                    action_by_userid = self.request.user.id
                    user = User.objects.get(pk=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if self.request.user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()
               
                context["update_field"] = update_field
                id_checkUpdate_field = []
                if scrop_year and scrop_year != "" :
                    context["selected_scrop_year"] = scrop_year
                    checkUpdate_field = FieldUpdated.objects.filter(field_id=pk,crop_year=scrop_year).values('id')
                    if checkUpdate_field.exists() and len(checkUpdate_field) == 1 :
                        id_checkUpdate_field = [i['id'] for i in checkUpdate_field]
                        new_update_field = FieldUpdated.objects.get(id__in=id_checkUpdate_field)
                        context["new_update_field"] = new_update_field
                        context["hidden_field_updated_field_id"] = new_update_field.id
                        context["crop_plant_date"] = str(context["new_update_field"].plant_date) if context["new_update_field"].plant_date  else None
                        context["crop_harvest_date"] = str(context["new_update_field"].harvest_date) if context["new_update_field"].harvest_date  else None
                    else:
                        pass
                # field_Pre_Fert = FieldActivity.objects.filter(field_activity='Pre_Fert',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                # code ..
                field_Pre_Fert = FieldActivity.objects.filter(field_activity='Pre_Fert',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_Early_Post_Fert =FieldActivity.objects.filter(field_activity='Early_Post_Fert',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_Foliar_Fert_App =FieldActivity.objects.filter(field_activity='Foliar_Fert_App',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_Pre_Flood_Fert =FieldActivity.objects.filter(field_activity='Pre_Flood_Fert',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_Post_Flood_Mid_Season_Fert =FieldActivity.objects.filter(field_activity='Post_Flood_Mid_Season_Fert',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_Boot_Fertilizer =FieldActivity.objects.filter(field_activity='Boot_Fertilizer',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_Burndown_Chemical =FieldActivity.objects.filter(field_activity='Burndown_Chemical',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_Preemergence_Chemical =FieldActivity.objects.filter(field_activity='Preemergence_Chemical',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_Post_Emergence_Chemical =FieldActivity.objects.filter(field_activity='Post_Emergence_Chemical',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_Fungicide_Micro_Nutrients =FieldActivity.objects.filter(field_activity='Fungicide_Micro_Nutrients',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_Insecticide_Application =FieldActivity.objects.filter(field_activity='Insecticide_Application',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_Litter =FieldActivity.objects.filter(field_activity='Litter',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_Sodium_Chlorate =FieldActivity.objects.filter(field_activity='Sodium_Chlorate',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_Emergence_Chemical =FieldActivity.objects.filter(field_activity='Emergence_Chemical',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_Measure_Water =FieldActivity.objects.filter(field_activity='Measure_Water',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                field_activity_npk =FieldActivity.objects.filter(field_activity='NPK_Application',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')

                
                context["field_Pre_Fert"] = field_Pre_Fert
                context["field_activity_Early_Post_Fert"] = field_activity_Early_Post_Fert
                context["field_activity_Foliar_Fert_App"] = field_activity_Foliar_Fert_App
                context["field_activity_Pre_Flood_Fert"] = field_activity_Pre_Flood_Fert
                context["field_activity_Post_Flood_Mid_Season_Fert"] = field_activity_Post_Flood_Mid_Season_Fert
                context["field_activity_Boot_Fertilizer"] = field_activity_Boot_Fertilizer
                context["field_activity_Burndown_Chemical"] = field_activity_Burndown_Chemical
                context["field_activity_Preemergence_Chemical"] = field_activity_Preemergence_Chemical
                context["field_activity_Post_Emergence_Chemical"] = field_activity_Post_Emergence_Chemical
                context["field_activity_Fungicide_Micro_Nutrients"] = field_activity_Fungicide_Micro_Nutrients
                context["field_activity_Insecticide_Application"] = field_activity_Insecticide_Application
                context["field_activity_Litter"] = field_activity_Litter
                context["field_activity_Sodium_Chlorate"] = field_activity_Sodium_Chlorate
                context["field_activity_Emergence_Chemical"] = field_activity_Emergence_Chemical
                context["field_activity_Measure_Water"] = field_activity_Measure_Water

                context["field_activity_npk"] = field_activity_npk
                
                sum_Pre_Fert = sum([i.amount_per_acre for i in field_Pre_Fert])
                context["sum_Pre_Fert"] = sum_Pre_Fert

                sum_Early_Post_Fert = sum([i.amount_per_acre for i in field_activity_Early_Post_Fert])
                context["sum_Early_Post_Fert"] = sum_Early_Post_Fert

                sum_Foliar_Fert_App = sum([i.amount_per_acre for i in field_activity_Foliar_Fert_App])
                context["sum_Foliar_Fert_App"] = sum_Foliar_Fert_App

                sum_Pre_Flood_Fert = sum([i.amount_per_acre for i in field_activity_Pre_Flood_Fert])
                context["sum_Pre_Flood_Fert"] = sum_Pre_Flood_Fert

                sum_Flood_Mid_Season_Fert = sum([i.amount_per_acre for i in field_activity_Post_Flood_Mid_Season_Fert])
                context["sum_Flood_Mid_Season_Fert"] = sum_Flood_Mid_Season_Fert

                sum_Boot_Fertilizer = sum([i.amount_per_acre for i in field_activity_Boot_Fertilizer])
                context["sum_Boot_Fertilizer"] = sum_Boot_Fertilizer

                sum_Burndown_Chemical = sum([i.amount_per_acre for i in field_activity_Burndown_Chemical])
                context["sum_Burndown_Chemical"] = sum_Burndown_Chemical

                sum_Preemergence_Chemical = sum([i.amount_per_acre for i in field_activity_Preemergence_Chemical])
                context["sum_Preemergence_Chemical"] = sum_Preemergence_Chemical

                sum_Post_Emergence_Chemical = sum([i.amount_per_acre for i in field_activity_Post_Emergence_Chemical])
                context["sum_Post_Emergence_Chemical"] = sum_Post_Emergence_Chemical

                sum_Fungicide_Micro_Nutrients = sum([i.amount_per_acre for i in field_activity_Fungicide_Micro_Nutrients])
                context["sum_Fungicide_Micro_Nutrients"] = sum_Fungicide_Micro_Nutrients

                sum_Insecticide_Application = sum([i.amount_per_acre for i in field_activity_Insecticide_Application])
                context["sum_Insecticide_Application"] = sum_Insecticide_Application

                sum_Litter = sum([i.amount_per_acre for i in field_activity_Litter])
                context["sum_Litter"] = sum_Litter

                sum_Sodium_Chlorate = sum([i.amount_per_acre for i in field_activity_Sodium_Chlorate])
                context["sum_Sodium_Chlorate"] = sum_Sodium_Chlorate

                sum_nitrogen = sum([i.n_nitrogen for i in field_activity_npk])
                context["sum_nitrogen"] = sum_nitrogen

                sum_phosporus = sum([i.p_phosporus for i in field_activity_npk])
                context["sum_phosporus"] = sum_phosporus

                sum_potassium = sum([i.k_potassium for i in field_activity_npk])
                context["sum_potassium"] = sum_potassium
            return context
        
        elif self.request.user.is_consultant:
            # do something consultant
            consultant_id = Consultant.objects.get(
                email=self.request.user.email).id
            get_growers = Grower.objects.filter(consultant=consultant_id)
            grower_ids = [data.id for data in get_growers]
            context["growers_dpdwn"] = Grower.objects.filter(
                id__in=grower_ids).order_by('name')
            farms_data = Farm.objects.filter(
                grower_id__in=grower_ids).order_by('name')
            context["farms"] = farms_data
            # 21-06-23
            update_field = Field.objects.get(id = pk)
            context["update_field"] = update_field
            context["variety_list"] = ['DG-263L','DG-Wheat','DG3605','DG 1464','DG 2425 XF','DG 3215 B3XF','DG 3450 B2XF',
                                       'DG 3470 B3XF','DG 3570 B3XF','DG 3635 B2XF','DG 3544 B2XF','DG 3651NR B2XF','DG 3109 B2XF',
                                       'DG 3387 B3XF','DG 3421 B3XF','DG H929 B3XF','DG 3555 B3XF','DG 3402 B3XF','DG H959 B3XF',
                                       'DG 3469 B3XF','DG 3615 B3XF','DG P224 B3XF','DG 3385 B2XF','DG 3422 B3XF','DG 3799 B3XF']
            if self.request.method == 'POST':
                scrop_year = self.request.POST.get('scrop_year')
                fld_name = self.request.POST.get('fname')
                farm_id = self.request.POST.get('farm')
                grower_id = self.request.POST.get('grower')
                batch_id = self.request.POST.get('batch_id')
                acreage = self.request.POST.get('acreage')
                fsa_farm_number = self.request.POST.get('fsa_farm_number')
                fsa_tract_number = self.request.POST.get('fsa_tract_number')
                fsa_field_number = self.request.POST.get('fsa_field_number')
                latitude = self.request.POST.get('latitude')
                longitude = self.request.POST.get('longitude')
                crop = self.request.POST.get('crop')

                btnvariable = self.request.POST.get('btnvariable')

                if btnvariable == 'updateField' :
                    # save field Update Field Name ........
                    if fld_name and len(fld_name) > 0 and fld_name != update_field.name :
                        print('update name')
                        update_field.name = fld_name
                        update_field.save()
                    # save field Update Farm ID ........
                    if farm_id and len(farm_id) > 0 and str(farm_id) != str(update_field.farm.id) :
                        print('update Farm')
                        update_field.farm_id = farm_id
                        update_field.save()
                    # save field Update Grower ID ........
                    if grower_id and len(grower_id) > 0 and str(grower_id) != str(update_field.grower.id) :
                        print('update Grower')
                        update_field.grower_id = grower_id
                        update_field.save()
                    # save field Update Batch id ........
                    if batch_id and len(batch_id) > 0 and float(batch_id) != update_field.batch_id:
                        print('update Batch id')
                        update_field.batch_id = batch_id
                        update_field.save()
                    # save field Update Acreage ........
                    if acreage and len(acreage) > 0 and float(acreage) != update_field.acreage :
                        print('update Acreage')
                        update_field.acreage = acreage
                        update_field.save()
                    # save field Update FSA Farm Number ........
                    if fsa_farm_number and len(fsa_farm_number) > 0 and fsa_farm_number != update_field.fsa_farm_number :
                        print('update FSA Farm Number')
                        update_field.fsa_farm_number = fsa_farm_number
                        update_field.save()
                    # save field Update FSA Tract Number ........
                    if fsa_tract_number and len(fsa_tract_number) > 0 and fsa_tract_number != update_field.fsa_tract_number :
                        print('update FSA Tract Number')
                        update_field.fsa_tract_number = fsa_tract_number
                        update_field.save()
                    # save field Update FSA Field Number ........
                    if fsa_field_number and len(fsa_field_number) > 0 and fsa_field_number != update_field.fsa_field_number :
                        print('update FSA Field Numberr')
                        update_field.fsa_field_number = fsa_field_number
                        update_field.save()
                    # save field Update Latitude ........
                    if latitude and len(latitude) > 0 :
                        print('update Latitude')
                        update_field.latitude = latitude
                        update_field.save()
                    # save field Update Longitude ........
                    if longitude and len(longitude) > 0 :
                        print('update Longitude')
                        update_field.longitude = longitude
                        update_field.save()
                    # if crop and len(crop) > 0 and crop != update_field.crop :
                    #     print('update crop')
                    #     update_field.crop = crop
                    #     update_field.save()
                    messages.success(self.request, f'Field {fld_name} Updated Successfully!')
                    # 20-06-23
                    log_type, log_status, log_device = "Field", "Edited", "Web"
                    log_idd, log_name = pk, fld_name
                    farm_name = Farm.objects.get(id=farm_id)
                    grower_name = Grower.objects.get(id=grower_id)
                    log_details = f"name = {fld_name} | farm = {farm_name.name} | grower = {grower_name.name} | acreage = {acreage} | crop = {crop}"
                    action_by_userid = self.request.user.id
                    user = User.objects.get(pk=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if self.request.user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()
               
                context["update_field"] = update_field
                
                id_checkUpdate_field = []
                if scrop_year and scrop_year != "" :
                    context["selected_scrop_year"] = scrop_year
                    checkUpdate_field = FieldUpdated.objects.filter(field_id=pk,crop_year=scrop_year).values('id')
                    if checkUpdate_field.exists() and len(checkUpdate_field) == 1 :
                        id_checkUpdate_field = [i['id'] for i in checkUpdate_field]
                        new_update_field = FieldUpdated.objects.get(id__in=id_checkUpdate_field)
                        context["new_update_field"] = new_update_field
                        context["hidden_field_updated_field_id"] = new_update_field.id
                        context["crop_plant_date"] = str(context["new_update_field"].plant_date) if context["new_update_field"].plant_date  else None
                        context["crop_harvest_date"] = str(context["new_update_field"].harvest_date) if context["new_update_field"].harvest_date  else None
                    else:
                        pass
                    # field_Pre_Fert = FieldActivity.objects.filter(field_activity='Pre_Fert',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    # code ..
                    field_Pre_Fert = FieldActivity.objects.filter(field_activity='Pre_Fert',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Early_Post_Fert =FieldActivity.objects.filter(field_activity='Early_Post_Fert',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Foliar_Fert_App =FieldActivity.objects.filter(field_activity='Foliar_Fert_App',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Pre_Flood_Fert =FieldActivity.objects.filter(field_activity='Pre_Flood_Fert',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Post_Flood_Mid_Season_Fert =FieldActivity.objects.filter(field_activity='Post_Flood_Mid_Season_Fert',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Boot_Fertilizer =FieldActivity.objects.filter(field_activity='Boot_Fertilizer',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Burndown_Chemical =FieldActivity.objects.filter(field_activity='Burndown_Chemical',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Preemergence_Chemical =FieldActivity.objects.filter(field_activity='Preemergence_Chemical',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Post_Emergence_Chemical =FieldActivity.objects.filter(field_activity='Post_Emergence_Chemical',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Fungicide_Micro_Nutrients =FieldActivity.objects.filter(field_activity='Fungicide_Micro_Nutrients',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Insecticide_Application =FieldActivity.objects.filter(field_activity='Insecticide_Application',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Litter =FieldActivity.objects.filter(field_activity='Litter',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Sodium_Chlorate =FieldActivity.objects.filter(field_activity='Sodium_Chlorate',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Emergence_Chemical =FieldActivity.objects.filter(field_activity='Emergence_Chemical',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Measure_Water =FieldActivity.objects.filter(field_activity='Measure_Water',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_npk =FieldActivity.objects.filter(field_activity='NPK_Application',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')

                    
                    context["field_Pre_Fert"] = field_Pre_Fert
                    context["field_activity_Early_Post_Fert"] = field_activity_Early_Post_Fert
                    context["field_activity_Foliar_Fert_App"] = field_activity_Foliar_Fert_App
                    context["field_activity_Pre_Flood_Fert"] = field_activity_Pre_Flood_Fert
                    context["field_activity_Post_Flood_Mid_Season_Fert"] = field_activity_Post_Flood_Mid_Season_Fert
                    context["field_activity_Boot_Fertilizer"] = field_activity_Boot_Fertilizer
                    context["field_activity_Burndown_Chemical"] = field_activity_Burndown_Chemical
                    context["field_activity_Preemergence_Chemical"] = field_activity_Preemergence_Chemical
                    context["field_activity_Post_Emergence_Chemical"] = field_activity_Post_Emergence_Chemical
                    context["field_activity_Fungicide_Micro_Nutrients"] = field_activity_Fungicide_Micro_Nutrients
                    context["field_activity_Insecticide_Application"] = field_activity_Insecticide_Application
                    context["field_activity_Litter"] = field_activity_Litter
                    context["field_activity_Sodium_Chlorate"] = field_activity_Sodium_Chlorate
                    context["field_activity_Emergence_Chemical"] = field_activity_Emergence_Chemical
                    context["field_activity_Measure_Water"] = field_activity_Measure_Water
                    

                    context["field_activity_npk"] = field_activity_npk
                    
                    sum_Pre_Fert = sum([i.amount_per_acre for i in field_Pre_Fert])
                    context["sum_Pre_Fert"] = sum_Pre_Fert

                    sum_Early_Post_Fert = sum([i.amount_per_acre for i in field_activity_Early_Post_Fert])
                    context["sum_Early_Post_Fert"] = sum_Early_Post_Fert

                    sum_Foliar_Fert_App = sum([i.amount_per_acre for i in field_activity_Foliar_Fert_App])
                    context["sum_Foliar_Fert_App"] = sum_Foliar_Fert_App

                    sum_Pre_Flood_Fert = sum([i.amount_per_acre for i in field_activity_Pre_Flood_Fert])
                    context["sum_Pre_Flood_Fert"] = sum_Pre_Flood_Fert

                    sum_Flood_Mid_Season_Fert = sum([i.amount_per_acre for i in field_activity_Post_Flood_Mid_Season_Fert])
                    context["sum_Flood_Mid_Season_Fert"] = sum_Flood_Mid_Season_Fert

                    sum_Boot_Fertilizer = sum([i.amount_per_acre for i in field_activity_Boot_Fertilizer])
                    context["sum_Boot_Fertilizer"] = sum_Boot_Fertilizer

                    sum_Burndown_Chemical = sum([i.amount_per_acre for i in field_activity_Burndown_Chemical])
                    context["sum_Burndown_Chemical"] = sum_Burndown_Chemical

                    sum_Preemergence_Chemical = sum([i.amount_per_acre for i in field_activity_Preemergence_Chemical])
                    context["sum_Preemergence_Chemical"] = sum_Preemergence_Chemical

                    sum_Post_Emergence_Chemical = sum([i.amount_per_acre for i in field_activity_Post_Emergence_Chemical])
                    context["sum_Post_Emergence_Chemical"] = sum_Post_Emergence_Chemical

                    sum_Fungicide_Micro_Nutrients = sum([i.amount_per_acre for i in field_activity_Fungicide_Micro_Nutrients])
                    context["sum_Fungicide_Micro_Nutrients"] = sum_Fungicide_Micro_Nutrients

                    sum_Insecticide_Application = sum([i.amount_per_acre for i in field_activity_Insecticide_Application])
                    context["sum_Insecticide_Application"] = sum_Insecticide_Application

                    sum_Litter = sum([i.amount_per_acre for i in field_activity_Litter])
                    context["sum_Litter"] = sum_Litter

                    sum_Sodium_Chlorate = sum([i.amount_per_acre for i in field_activity_Sodium_Chlorate])
                    context["sum_Sodium_Chlorate"] = sum_Sodium_Chlorate

                    sum_nitrogen = sum([i.n_nitrogen for i in field_activity_npk])
                    context["sum_nitrogen"] = sum_nitrogen

                    sum_phosporus = sum([i.p_phosporus for i in field_activity_npk])
                    context["sum_phosporus"] = sum_phosporus

                    sum_potassium = sum([i.k_potassium for i in field_activity_npk])
                    context["sum_potassium"] = sum_potassium
            return context

        elif self.request.user.is_superuser or 'SubAdmin' in self.request.user.get_role() or 'SuperUser' in self.request.user.get_role():
            context["growers_dpdwn"] = Grower.objects.all().order_by('name')
            farms_data = Farm.objects.all().order_by('name')
            context["farms"] = farms_data
            update_field = Field.objects.get(id = pk)
            context["update_field"] = update_field
            context["variety_list"] = ['DG-263L','DG-Wheat','DG3605','DG 1464','DG 2425 XF','DG 3215 B3XF','DG 3450 B2XF',
                                       'DG 3470 B3XF','DG 3570 B3XF','DG 3635 B2XF','DG 3544 B2XF','DG 3651NR B2XF','DG 3109 B2XF',
                                       'DG 3387 B3XF','DG 3421 B3XF','DG H929 B3XF','DG 3555 B3XF','DG 3402 B3XF','DG H959 B3XF',
                                       'DG 3469 B3XF','DG 3615 B3XF','DG P224 B3XF','DG 3385 B2XF','DG 3422 B3XF','DG 3799 B3XF']
            if self.request.method == 'POST':
                scrop_year = self.request.POST.get('scrop_year')
                fld_name = self.request.POST.get('fname')
                farm_id = self.request.POST.get('farm')
                grower_id = self.request.POST.get('grower')
                batch_id = self.request.POST.get('batch_id')
                acreage = self.request.POST.get('acreage')
                fsa_farm_number = self.request.POST.get('fsa_farm_number')
                fsa_tract_number = self.request.POST.get('fsa_tract_number')
                fsa_field_number = self.request.POST.get('fsa_field_number')
                latitude = self.request.POST.get('latitude')
                longitude = self.request.POST.get('longitude')
                crop = self.request.POST.get('crop')

                btnvariable = self.request.POST.get('btnvariable')

                if btnvariable == 'updateField' :
                    # save field Update Field Name ........
                    if fld_name and len(fld_name) > 0 and fld_name != update_field.name :
                        print('update name')
                        update_field.name = fld_name
                        update_field.save()
                    # save field Update Farm ID ........
                    if farm_id and len(farm_id) > 0 and str(farm_id) != str(update_field.farm.id) :
                        print('update Farm')
                        update_field.farm_id = farm_id
                        update_field.save()
                    # save field Update Grower ID ........
                    if grower_id and len(grower_id) > 0 and str(grower_id) != str(update_field.grower.id) :
                        print('update Grower')
                        update_field.grower_id = grower_id
                        update_field.save()
                    # save field Update Batch id ........
                    if batch_id and len(batch_id) > 0 and float(batch_id) != update_field.batch_id:
                        print('update Batch id')
                        update_field.batch_id = batch_id
                        update_field.save()
                    # save field Update Acreage ........
                    if acreage and len(acreage) > 0 and float(acreage) != update_field.acreage :
                        print('update Acreage')
                        update_field.acreage = acreage
                        update_field.save()
                    # save field Update FSA Farm Number ........
                    if fsa_farm_number and len(fsa_farm_number) > 0 and fsa_farm_number != update_field.fsa_farm_number :
                        print('update FSA Farm Number')
                        update_field.fsa_farm_number = fsa_farm_number
                        update_field.save()
                    # save field Update FSA Tract Number ........
                    if fsa_tract_number and len(fsa_tract_number) > 0 and fsa_tract_number != update_field.fsa_tract_number :
                        print('update FSA Tract Number')
                        update_field.fsa_tract_number = fsa_tract_number
                        update_field.save()
                    # save field Update FSA Field Number ........
                    if fsa_field_number and len(fsa_field_number) > 0 and fsa_field_number != update_field.fsa_field_number :
                        print('update FSA Field Numberr')
                        update_field.fsa_field_number = fsa_field_number
                        update_field.save()
                    # save field Update Latitude ........
                    if latitude and len(latitude) > 0 :
                        print('update Latitude')
                        update_field.latitude = latitude
                        update_field.save()
                    # save field Update Longitude ........
                    if longitude and len(longitude) > 0 :
                        print('update Longitude')
                        update_field.longitude = longitude
                        update_field.save()
                    # if crop and len(crop) > 0 and crop != update_field.crop :
                    #     print('update crop')
                    #     update_field.crop = crop
                    #     update_field.save()
                    messages.success(self.request, f'Field {fld_name} Updated Successfully!')
                    # 20-06-23
                    log_type, log_status, log_device = "Field", "Edited", "Web"
                    log_idd, log_name = pk, fld_name
                    farm_name = Farm.objects.get(id=farm_id)
                    grower_name = Grower.objects.get(id=grower_id)
                    log_details = f"name = {fld_name} | farm = {farm_name.name} | grower = {grower_name.name} | acreage = {acreage} | crop = {crop}"
                    action_by_userid = self.request.user.id
                    user = User.objects.get(pk=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if self.request.user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()
               
                context["update_field"] = update_field
                
                id_checkUpdate_field = []
                if scrop_year and scrop_year != "" :
                    context["selected_scrop_year"] = scrop_year
                    checkUpdate_field = FieldUpdated.objects.filter(field_id=pk,crop_year=scrop_year).values('id')
                    if checkUpdate_field.exists() and len(checkUpdate_field) == 1 :
                        id_checkUpdate_field = [i['id'] for i in checkUpdate_field]
                        new_update_field = FieldUpdated.objects.get(id__in=id_checkUpdate_field)
                        context["new_update_field"] = new_update_field
                        context["hidden_field_updated_field_id"] = new_update_field.id
                        context["crop_plant_date"] = str(context["new_update_field"].plant_date) if context["new_update_field"].plant_date  else None
                        context["crop_harvest_date"] = str(context["new_update_field"].harvest_date) if context["new_update_field"].harvest_date  else None
                    else:
                        pass
                    # code ..
                    field_Pre_Fert = FieldActivity.objects.filter(field_activity='Pre_Fert',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Early_Post_Fert =FieldActivity.objects.filter(field_activity='Early_Post_Fert',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Foliar_Fert_App =FieldActivity.objects.filter(field_activity='Foliar_Fert_App',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Pre_Flood_Fert =FieldActivity.objects.filter(field_activity='Pre_Flood_Fert',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Post_Flood_Mid_Season_Fert =FieldActivity.objects.filter(field_activity='Post_Flood_Mid_Season_Fert',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Boot_Fertilizer =FieldActivity.objects.filter(field_activity='Boot_Fertilizer',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Burndown_Chemical =FieldActivity.objects.filter(field_activity='Burndown_Chemical',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Preemergence_Chemical =FieldActivity.objects.filter(field_activity='Preemergence_Chemical',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Post_Emergence_Chemical =FieldActivity.objects.filter(field_activity='Post_Emergence_Chemical',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    
                    field_activity_Emergence_Chemical =FieldActivity.objects.filter(field_activity='Emergence_Chemical',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    
                    field_activity_Fungicide_Micro_Nutrients =FieldActivity.objects.filter(field_activity='Fungicide_Micro_Nutrients',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Insecticide_Application =FieldActivity.objects.filter(field_activity='Insecticide_Application',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Litter =FieldActivity.objects.filter(field_activity='Litter',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    field_activity_Sodium_Chlorate =FieldActivity.objects.filter(field_activity='Sodium_Chlorate',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')
                    
                    field_activity_Measure_Water =FieldActivity.objects.filter(field_activity='Measure_Water',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')

                    field_activity_npk =FieldActivity.objects.filter(field_activity='NPK_Application',field_id = pk,field_updated_id__in=id_checkUpdate_field).order_by('-date_of_activity')

                    
                    context["field_Pre_Fert"] = field_Pre_Fert
                    context["field_activity_Early_Post_Fert"] = field_activity_Early_Post_Fert
                    context["field_activity_Foliar_Fert_App"] = field_activity_Foliar_Fert_App
                    context["field_activity_Pre_Flood_Fert"] = field_activity_Pre_Flood_Fert
                    context["field_activity_Post_Flood_Mid_Season_Fert"] = field_activity_Post_Flood_Mid_Season_Fert
                    context["field_activity_Boot_Fertilizer"] = field_activity_Boot_Fertilizer
                    context["field_activity_Burndown_Chemical"] = field_activity_Burndown_Chemical
                    context["field_activity_Preemergence_Chemical"] = field_activity_Preemergence_Chemical
                    context["field_activity_Post_Emergence_Chemical"] = field_activity_Post_Emergence_Chemical

                    context["field_activity_Emergence_Chemical"] = field_activity_Emergence_Chemical

                    context["field_activity_Fungicide_Micro_Nutrients"] = field_activity_Fungicide_Micro_Nutrients
                    context["field_activity_Insecticide_Application"] = field_activity_Insecticide_Application
                    context["field_activity_Litter"] = field_activity_Litter
                    context["field_activity_Sodium_Chlorate"] = field_activity_Sodium_Chlorate

                    context["field_activity_Measure_Water"] = field_activity_Measure_Water

                    context["field_activity_npk"] = field_activity_npk
                    
                    sum_Pre_Fert = sum([i.amount_per_acre for i in field_Pre_Fert])
                    context["sum_Pre_Fert"] = sum_Pre_Fert

                    sum_Early_Post_Fert = sum([i.amount_per_acre for i in field_activity_Early_Post_Fert])
                    context["sum_Early_Post_Fert"] = sum_Early_Post_Fert

                    sum_Foliar_Fert_App = sum([i.amount_per_acre for i in field_activity_Foliar_Fert_App])
                    context["sum_Foliar_Fert_App"] = sum_Foliar_Fert_App

                    sum_Pre_Flood_Fert = sum([i.amount_per_acre for i in field_activity_Pre_Flood_Fert])
                    context["sum_Pre_Flood_Fert"] = sum_Pre_Flood_Fert

                    sum_Flood_Mid_Season_Fert = sum([i.amount_per_acre for i in field_activity_Post_Flood_Mid_Season_Fert])
                    context["sum_Flood_Mid_Season_Fert"] = sum_Flood_Mid_Season_Fert

                    sum_Boot_Fertilizer = sum([i.amount_per_acre for i in field_activity_Boot_Fertilizer])
                    context["sum_Boot_Fertilizer"] = sum_Boot_Fertilizer

                    sum_Burndown_Chemical = sum([i.amount_per_acre for i in field_activity_Burndown_Chemical])
                    context["sum_Burndown_Chemical"] = sum_Burndown_Chemical

                    sum_Preemergence_Chemical = sum([i.amount_per_acre for i in field_activity_Preemergence_Chemical])
                    context["sum_Preemergence_Chemical"] = sum_Preemergence_Chemical

                    sum_Post_Emergence_Chemical = sum([i.amount_per_acre for i in field_activity_Post_Emergence_Chemical])
                    context["sum_Post_Emergence_Chemical"] = sum_Post_Emergence_Chemical

                    sum_Fungicide_Micro_Nutrients = sum([i.amount_per_acre for i in field_activity_Fungicide_Micro_Nutrients])
                    context["sum_Fungicide_Micro_Nutrients"] = sum_Fungicide_Micro_Nutrients

                    sum_Insecticide_Application = sum([i.amount_per_acre for i in field_activity_Insecticide_Application])
                    context["sum_Insecticide_Application"] = sum_Insecticide_Application

                    sum_Litter = sum([i.amount_per_acre for i in field_activity_Litter])
                    context["sum_Litter"] = sum_Litter

                    sum_Sodium_Chlorate = sum([i.amount_per_acre for i in field_activity_Sodium_Chlorate])
                    context["sum_Sodium_Chlorate"] = sum_Sodium_Chlorate

                    sum_nitrogen = sum([i.n_nitrogen for i in field_activity_npk])
                    context["sum_nitrogen"] = sum_nitrogen

                    sum_phosporus = sum([i.p_phosporus for i in field_activity_npk])
                    context["sum_phosporus"] = sum_phosporus

                    sum_potassium = sum([i.k_potassium for i in field_activity_npk])
                    context["sum_potassium"] = sum_potassium

            return context



class FieldDeleteView(LoginRequiredMixin, DeleteView):
    """Generic Class Based View to delete a field"""

    def get(self, request, pk):
        obj = Field.objects.get(pk=pk)
        # 07-04-23
        log_type, log_status, log_device = "Field", "Deleted", "Web"
        log_idd, log_name = pk, obj.name
        log_details = f"name = {obj.name} | farm = {obj.farm.name} | grower = {obj.grower.name} | acreage = {obj.acreage} | crop = {obj.crop} | variety = {obj.variety}"
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
        obj.delete()
        return HttpResponse(1)


class CsvFieldCreateView(LoginRequiredMixin, CreateView):  # pylint: disable=too-many-ancestors
    """View to create a Farms via CSV file"""

    model = CsvToField
    fields = "__all__"
    template_name = 'field/csv_field_create.html'


class CsvFieldMappingView(LoginRequiredMixin, View):
    model_fields = FieldColoumChoices().field_coloum

    model_fields_show = [i.replace('_', ' ').title() for i in model_fields]

    def get(self, request, pk):
        '''Function for get request
        Displaying CSV headers for mapping'''

        grower_names = Grower.objects.all()
        file_name = CsvToField.objects.get(pk=pk).csv_file
        try:
            df_file = pd.read_csv(file_name)
        except:
            messages.error(request, "CSV file format is invalid. \
                \nPlease check the format and try again")
            return redirect('csv-field-create')
        # If CSV file havin only header
        if df_file.shape[0] == 0:
            messages.error(request, "Rows are missing in your CSV file, \
                please upload the file with data.")
            return redirect('csv-field-create')

        df_file.insert(0, 'Blank', None)
        map_col = df_file.columns.tolist()

        return render(request, 'field/csv_field_mapping.html', {"file_name": file_name,
                                                                'model_fields': self.model_fields_show,
                                                                'map_col': map_col, 'grower_names': grower_names})

    def post(self, request, pk):
        '''Function for post request
        Displaying import status'''

        # farm_obj = Farm()
        column_data = request.POST
        new_col_list = []

        for i in column_data.keys():
            new_col_list.append(column_data[i])

        # Removing CSRF token value
        new_col_list.pop(0)
        # Storing grower ID
        grower_id = new_col_list[0]
        # Removing Grower ID from list
        new_col_list.pop(0)

        # Getting file name from database
        file_name = CsvToField.objects.get(pk=pk).csv_file
        # Opening file using pandas dataframe
        df_file = pd.read_csv(file_name)
        df_file.insert(0, 'Blank', None)
        # Arrangin columns names in order
        df_file = df_file[new_col_list].copy()

        # Changing the columns names as per model fields
        df_file.columns = self.model_fields

        # Removing nan and duplicate values
        df_file.dropna(subset=['farm', 'name'], how='any', inplace=True)
        df_file.drop_duplicates(
            subset=['farm', 'name'], ignore_index=True, inplace=True)

        # Assigning data type for Area and Zip Fields
        # df_file = df_file.astype({'area': float, 'zip': int})

        # Creating Farms which are not in DB but listed in CSV
        farm_in_csv = set(df_file.iloc[:, 0])
        farm_in_db = set(Farm.objects.values_list('name', flat=True))
        new_farms = farm_in_csv - farm_in_db
        for _ in new_farms:
            obj = Farm(name=_, grower_id=grower_id)
            obj.save()

        # Creating an empty list for storing objects for bulk creation
        myobj = []

        # Creating object for every row and appending it on 'myobj' list
        for row in df_file.index:
            myobj.append(Field(
                grower=Grower.objects.get(pk=grower_id),
                farm=Farm.objects.filter(name=df_file.iloc[row, 0])[0],
                name=df_file.iloc[row, 1],
                batch_id=df_file.iloc[row, 2],
                acreage=df_file.iloc[row, 3],
                fsa_farm_number=df_file.iloc[row, 4],
                fsa_tract_number=df_file.iloc[row, 5],
                fsa_field_number=df_file.iloc[row, 6],
                latitude=df_file.iloc[row, 7],
                longitude=df_file.iloc[row, 8],
                crop=df_file.iloc[row, 9],
                variety=df_file.iloc[row, 10],
                yield_per_acre=df_file.iloc[row, 11],
                total_yield=df_file.iloc[row, 12],
                crop_tech=df_file.iloc[row, 13],
                burndown_chemical=df_file.iloc[row, 14],
                burndown_chemical_date=df_file.iloc[row, 15],
                plant_date=df_file.iloc[row, 16],
                preemergence_chemical=df_file.iloc[row, 17],
                preemergence_chemical_date=df_file.iloc[row, 18],
                stand_count=df_file.iloc[row, 19],
                emergence_date=df_file.iloc[row, 20],
                post_emergence_chemical_1=df_file.iloc[row, 21],
                post_emergence_chemical_1_date=df_file.iloc[row, 22],
                post_emergence_chemical_2=df_file.iloc[row, 23],
                post_emergence_chemical_2_date=df_file.iloc[row, 24],
                post_emergence_chemical_3=df_file.iloc[row, 25],
                post_emergence_chemical_3_date=df_file.iloc[row, 26],
                post_emergence_chemical_4=df_file.iloc[row, 27],
                post_emergence_chemical_4_date=df_file.iloc[row, 28],
                flood_date=df_file.iloc[row, 29],
                awd_drydown_date=df_file.iloc[row, 30],
                fungicide_micronutrients=df_file.iloc[row, 31],
                fungicide_micronutrients_date=df_file.iloc[row, 32],
                insecticide_application=df_file.iloc[row, 33],
                insecticide_application_date=df_file.iloc[row, 34],
                drain_date=df_file.iloc[row, 35],
                sodium_chlorate_date=df_file.iloc[row, 36],
                harvest_date=df_file.iloc[row, 37],
                soil_sample_date=df_file.iloc[row, 38],
                litter=df_file.iloc[row, 39],
                pre_fert_rate=df_file.iloc[row, 40],
                pre_fert_product=df_file.iloc[row, 41],
                early_post_fert_rate=df_file.iloc[row, 42],
                early_post_fert_product=df_file.iloc[row, 43],
                early_post_fert_date=df_file.iloc[row, 44],
                foliar_fert_app_rate=df_file.iloc[row, 45],
                foliar_fert_app_product=df_file.iloc[row, 46],
                foliar_fert_app_date=df_file.iloc[row, 47],
                pre_flood_fert_rate=df_file.iloc[row, 48],
                pre_flood_fert_product=df_file.iloc[row, 49],
                pre_flood_fert_date=df_file.iloc[row, 50],
                post_flood_midseason_fert_rate=df_file.iloc[row, 51],
                post_flood_midseason_fert_product=df_file.iloc[row, 52],
                post_flood_midseason_fert_date=df_file.iloc[row, 53],
                post_flood_midseason_fert_rate2=df_file.iloc[row, 54],
                post_flood_midseason_fert_product2=df_file.iloc[row, 55],
                post_flood_midseason_fert_date2=df_file.iloc[row, 56],
                post_flood_midseason_fert_rate3=df_file.iloc[row, 57],
                post_flood_midseason_fert_product3=df_file.iloc[row, 58],
                post_flood_midseason_fert_date3=df_file.iloc[row, 59],
                boot_fertilizer_rate=df_file.iloc[row, 60],
                boot_fertilizer_product=df_file.iloc[row, 61],
                boot_fertilizer_date=df_file.iloc[row, 62],
                total_n_applied_lbs_ac=df_file.iloc[row, 63],
                flow_meter_beginning_reading=df_file.iloc[row, 64],
                flow_meter_multiplier=df_file.iloc[row, 65],
                flow_meter_end_reading=df_file.iloc[row, 66],
                water_source=df_file.iloc[row, 67],
                total_n_applied=df_file.iloc[row, 68],
                measured_water_use=df_file.iloc[row, 69],
                field_design_and_use_of_plastic_pipe=df_file.iloc[row, 70],
                soil_clay_percentage=df_file.iloc[row, 71],
                previous_crop=df_file.iloc[row, 72],
                straw_burnt_or_residue_removed=df_file.iloc[row, 73],
                straw_residue_tillage_and_cover_crop_management=df_file.iloc[row, 74],
                tillage_equipment_and_passes_or_fuel_usage_for_tillage=df_file.iloc[row, 75],
                water_saving=df_file.iloc[row, 76],
                # co2_equivalents_reduced=df_file.iloc[row,77],
            )
            )
        # Saving all the objects in database
        try:
            Field.objects.bulk_create(myobj)
        except IntegrityError:
            messages.error(
                request, "Some field(s) already exists with the same name.")
            return redirect('csv-field-create')
        except:
            messages.error(request, "Date-time related data is not in a proper \
                format in the CSV file. Valid format is \"YYYY-MM-DD\".\
                     Please check the file and try again.")
            return redirect('csv-field-create')

        messages.success(
            request, f"{len(myobj)} Field(s) created successfully.")
        return redirect('field-list')


class ReadShapeFile(LoginRequiredMixin, CreateView):
    def get(self, request):
        sf = shapefile.Reader("media/shape_files/south_inman_field_export.zip")
        rec = sf.shapeRecords()[0]
        # geom = rec.shape.__geo_interface__
        # coords = geom['coordinates'][0] # or directly rec.shape.__geo_interface__['coordinates']

        # records = sf.records()
        # print(records) # GeoJSON format

        points = rec.shape.points
        lat_lon_set = reverseTuple(points)
        # polygon_json = json.dumps(lat_lon_set)
        # shape_file_data = ShapeFileDataCo(coordinates=lat_lon_set)
        # shape_file_data.save()
        # print(polygon_json)
        # for p in lat_lon_set:
        #     print(str(p[0]) + "," + str(p[1]))

        # get_data = ShapeFileDataCo.objects.get(id=2).coordinates
        # for p in get_data:
        #     print(p)

        # print(get_data)

        return JsonResponse({'data': []})


def reverseTuple(lstOfTuple):
    return [tup[::-1] for tup in lstOfTuple]


class SaveShapeFile(LoginRequiredMixin, CreateView):
    def post(self, request):
        uploaded_file = request.FILES.get('shape_file')
        field_id = int(request.POST.get('field_id'))
        sf = shapefile.Reader(uploaded_file.temporary_file_path())

        # Reading shapeFile id & update fields eschlon_id point 
        features = sf.shapeRecords()
        for feat in features:
            eschlon_id = feat.record["id"]
            
        Field.objects.filter(id=field_id).update(eschlon_id=eschlon_id)

        rec = sf.shapeRecords()[0]
        points = rec.shape.points
        lat_lon_set = reverseTuple(points)
        chk_poly_data = ShapeFileDataCo.objects.filter(field_id=field_id)
    
        if chk_poly_data.count() == 0:

            shape_file_data = ShapeFileDataCo(
                coordinates=lat_lon_set, field_id=field_id)
            shape_file_data.save()

        
        else:

            shape_file_data = ShapeFileDataCo(
                id=chk_poly_data[0].id, coordinates=lat_lon_set, field_id=field_id)
            shape_file_data.save()

        return JsonResponse({'data': field_id})


class GetCoordinates(LoginRequiredMixin, ListView):
    def get(self, request):
        field_id = int(request.GET.get('field_id'))

        try:
            poly_data = ShapeFileDataCo.objects.get(field_id=field_id)
            return JsonResponse({'data': poly_data.coordinates})
        except ShapeFileDataCo.DoesNotExist:
            poly_data = None
            return JsonResponse({'data': []})


class EosCreateTask(LoginRequiredMixin, ListView):
    def get(self, request):
        # field_id = int(request.GET.get('field_id'))

        field_id = 431
        poly_data = ShapeFileDataCo.objects.get(field_id=field_id)

        # apk.bb21f18277c357fe1a7bcaaaf90b0141f5e452038292448723c9b423c46a021f

        url = "https://gate.eos.com/api/gdw/api?api_key=apk.d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"

        payload = {
            "type": "mt_stats",
            "params": {
                "bm_type": "NDVI",
                "date_start": "2022-06-01",
                "date_end": "2022-06-07",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [reverseTuple(poly_data.coordinates)]
                },
                "reference": str(field_id),
                "sensors": [
                    "sentinel2"
                ],
                "max_cloud_cover_in_aoi": 0,
                "limit": 100
            }
        }

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request(
            "POST", url, headers=headers, data=json.dumps(payload))
        results = json.loads(response.text)
        return JsonResponse({'data': results})


class EosTaskStatus(LoginRequiredMixin, ListView):
    def get(self, request):
        # https://gate.eos.com/api/gdw/api/<task_id>?api_key=<your api key>

        task_id = '51758419-3158-4900-bb02-3ae85e8b604f'

        url = "https://gate.eos.com/api/gdw/api/" + task_id + \
            "?api_key=apk.d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"

        payload = {}

        headers = {}

        response = requests.request(
            "GET", url, headers=headers, data=json.dumps(payload))
        results = json.loads(response.text)
        return JsonResponse({'data': results})


class EosSearchTask(LoginRequiredMixin, ListView):
    def get(self, request):
        # field_id = int(request.GET.get('field_id'))

        field_id = 431
        poly_data = ShapeFileDataCo.objects.get(field_id=field_id)

        url = "https://gate.eos.com/api/lms/search/v2/sentinel2?api_key=apk.d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"

        payload = {
            "fields": ["sceneID", "cloudCoverage"],
            "limit": 2,
            "page": 1,
            "search": {
                "date": {"from": "2022-06-01", "to": "2022-06-07"},
                "cloudCoverage": {"from": 0, "to": 100},
                "shape": {
                    "type": "Polygon",
                    "coordinates": [reverseTuple(poly_data.coordinates)]
                }
            },
            "sort": {"date": "desc"}
        }

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request(
            "POST", url, headers=headers, data=json.dumps(payload))
        results = json.loads(response.text)
        return JsonResponse({'data': results})


# soil moisture step 1 task creation
class EosSoilmoistureCreateTask(LoginRequiredMixin, ListView):
    def get(self, request):
        # field_id = int(request.GET.get('field_id'))
        current_datetime = datetime.datetime.now()

        field_id = 431
        poly_data = ShapeFileDataCo.objects.get(field_id=field_id)

        url = "https://gate.eos.com/api/gdw/api?api_key=apk.d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"

        payload = {
            "type": "mt_stats",
            "params": {
                "bm_type": "soilmoisture",
                "date_start": "2022-06-01",
                "date_end": "2022-06-07",
                "geometry":
                    {
                        "coordinates": [reverseTuple(poly_data.coordinates)],
                        "type": "Polygon"
                    },
                "reference": "ref_" + str(current_datetime),
                "sensors": ["soilmoisture"],
                "limit": 10

            }
        }

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request(
            "POST", url, headers=headers, data=json.dumps(payload))
        results = json.loads(response.text)
        return JsonResponse({'data': results})


# soil moisture step 2 getting data and view id by task id
class EosSoilMoistureData(LoginRequiredMixin, ListView):
    def get(self, request):
        # https://gate.eos.com/api/gdw/api/<task_id>?api_key=<your api key>

        task_id = 'edab6bf9-3c0f-4d7c-a561-27756f274f6b'

        url = "https://gate.eos.com/api/gdw/api/" + task_id + \
            "?api_key=apk.d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"

        payload = {}

        headers = {}

        response = requests.request(
            "GET", url, headers=headers, data=json.dumps(payload))
        results = json.loads(response.text)
        return JsonResponse({'data': results})


# soil moisture step 3 creating task for download visual by view id
class EosDownloadVisualDataCreateTask(LoginRequiredMixin, ListView):
    def get(self, request):
        # https://gate.eos.com/api/gdw/api/<task_id>?api_key=<your api key>
        current_datetime = datetime.datetime.now()

        view_id = "S2/15/S/YA/2022/6/4/0"  # soilmoisture/sm_250m_20220603_39194_usa

        field_id = 431
        poly_data = ShapeFileDataCo.objects.get(field_id=field_id)

        url = "https://gate.eos.com/api/gdw/api?api_key=?api_key=apk.d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"

        # payload = {
        #             "type": "jpeg",
        #             "params": {
        #                     "view_id": view_id,
        #                     "bm_type": "NDVI",
        #                     "geometry":{
        #                             "type": "Polygon",
        #                             "coordinates": [reverseTuple(poly_data.coordinates)]
        #                             },
        #                 "px_size": 2,
        #                 "format":"png",
        #                 "reference": "ref_ddddddddd" + str(current_datetime)
        #             }
        #         }

        payload = {
            "type": "jpeg",
            "params": {
                "view_id": "soilmoisture/sm_250m_20220603_39194_usa",
                "bm_type": "NDVI",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-1.531048, 5.578849],
                            [-1.530683, 5.575411],
                            [-1.521606, 5.576286],
                            [-1.522036, 5.579767],
                            [-1.531048, 5.578849]
                        ]
                    ]
                },
                "px_size": 2,
                "format": "tiff",
                "reference": "ref_datetime"
            }
        }

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request(
            "POST", url, headers=headers, data=json.dumps(payload))
        print(response)
        # results = json.loads(response.text)
        return JsonResponse({'data': []})


def get_image_url(one_year_ago_date, today, poly_data, minute_in_second, rate_limit, index="NDVI"):
    url = "https://gate.eos.com/api/lms/search/v2/sentinel2?api_key=apk" \
          ".d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"

    payload = {
        "search": {
            "date": {"from": one_year_ago_date, "to": today},
            "shape": {
                "type": "Polygon",
                "coordinates": [reverseTuple(poly_data.coordinates)]
            }
        },
        "sort": {"date": "desc"},
        "max_cloud_cover_in_aoi": 100,
        "limit": 1
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request(
        "POST", url, headers=headers, data=json.dumps(payload))
    print(response.json())
    bm_type = index
    results = json.loads(response.text)
    url_1 = "https://gate.eos.com/api/gdw/api?api_key=apk" \
            ".d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"
    payload_1 = {
        "type": "jpeg",
        "params": {
            "view_id": results['results'][0]['view_id'],
            "bm_type": bm_type,
            "geometry":
                {
                    "coordinates": [reverseTuple(poly_data.coordinates)],
                    "type": "Polygon"
            },
            "px_size": 1,
            "format": "png"
        }
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response_1 = requests.request(
        "POST", url_1, headers=headers, data=json.dumps(payload_1))
    print(f" response 1 is {response_1.json()}")
    url_2 = f"https://gate.eos.com/api/gdw/api/{response_1.json()['task_id']}?api_key=apk" \
            f".d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"
    payload_2 = {}
    headers_2 = {
        'Content-Type': 'application/octet-stream'
    }
    response_2 = requests.request(
        "GET", url_2, headers=headers_2, data=payload_2)
    while response_2.headers['Content-Type'] == 'application/json':
        time.sleep(minute_in_second / rate_limit)
        response_2 = requests.request(
            "GET", url_2, headers=headers_2, data=payload_2)
        print('inside while loop')
        print(response_2.url)
    final_response = response_2
    return final_response


def get_statistics_data(one_year_ago_date, today, poly_data, minute_in_second, rate_limit, index="NDVI"):
    url = "https://gate.eos.com/api/gdw/api?api_key=apk" \
          ".d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"

    payload = {
        "type": "mt_stats",
        "params": {
            "bm_type": index,
            "date_start": one_year_ago_date,
            "date_end": today,
            "geometry":
                {
                    "coordinates": [reverseTuple(poly_data.coordinates)],
                    "type": "Polygon"
                },
            "reference": "ref_" + datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S"),
            "sensors": ["sentinel2"] if index != 'soilmoisture' else ['soilmoisture'],
            "limit": 10

        }
    }
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request(
        "POST", url, headers=headers, data=json.dumps(payload))
    print(response.json())
    results = json.loads(response.text)
    url_2 = f"https://gate.eos.com/api/gdw/api/{results['task_id']}?api_key=apk" \
            f".d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"
    payload_2 = {}

    response_2 = requests.request(
        "GET", url_2, headers=headers, data=payload_2)
    final_response = response_2.json()
    while final_response.get('status') == 'created':
        time.sleep(minute_in_second / rate_limit)
        response_2 = requests.request(
            "GET", url_2, headers=headers, data=payload_2)
        print('inside while loop')
        print(response_2)
        print(response_2.json())
        final_response = response_2
    print(final_response)
    return final_response


# custom thread
class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                        **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return


def threaded_process_range(one_year_ago_date, today, poly_data, MINUTE_IN_SECONDS, RATE_LIMIT, bm_type):
    """process the id range in a specified number of threads"""
    threads = []
    # create the threads
    t1 = ThreadWithReturnValue(target=get_image_url,
                               args=(one_year_ago_date, today, poly_data, MINUTE_IN_SECONDS, RATE_LIMIT, bm_type))
    threads.append(t1)
    # t2 = ThreadWithReturnValue(target=get_statistics_data,
    #                            args=(one_year_ago_date, today, poly_data, MINUTE_IN_SECONDS, RATE_LIMIT, bm_type))
    # threads.append(t2)
    # start the threads
    [t.start() for t in threads]
    # wait for the threads to finish
    output = [t.join() for t in threads]
    return output[0], None


class FieldLocationMapVegetation(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        field_obj = Field.objects.get(pk=pk)
        if ShapeFileDataCo.objects.filter(field=field_obj).count() > 0:
            shape_obj = ShapeFileDataCo.objects.get(field=field_obj)
            field_coordinates = shape_obj.coordinates[0]
            field_name = shape_obj.field.name
            field_id = shape_obj.field.id
            coordinates = shape_obj.coordinates
        else:
            field_coordinates = 'N/A'
            field_name = field_obj.name
            field_id = field_obj.id
            coordinates = 'N/A'

        polydata_n = '<subdivisions>'
        polydata_n += '<subdivision fieldId="' + \
            str(field_id) + '" name="' + field_name.replace("'", "") + '">'

        for coord in coordinates:
            polydata_n += '<coord lat="' + \
                str(coord[0]) + '" lng="' + str(coord[1]) + '"/>'

        polydata_n += '</subdivision>'
        polydata_n += '<subdivisions>'
        RATE_LIMIT = 10  # ten requests per minute
        MINUTE_IN_SECONDS = 60
        bm_type = "NDVI"
        if request.GET.get("index_name"):
            bm_type = request.GET.get("index_name")
        poly_data = ShapeFileDataCo.objects.get(field_id=field_id)
        one_year_ago_date = (datetime.datetime.now(
        ) - datetime.timedelta(days=1 * 365)).strftime("%Y-%m-%d")
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if request.GET.get("date"):
            today = request.GET.get("date")
        response_2, response_3 = threaded_process_range(one_year_ago_date, today, poly_data, MINUTE_IN_SECONDS,
                                                        RATE_LIMIT, bm_type)
        return render(request, 'field/field-location-map-vegetation.html', {
            'field_obj': field_obj,
            'polydata_n': polydata_n,
            # 'field_img': response_2.url,
            'index_selected': bm_type,
            'date_selected': today,
            'result_obj': None,
            'field_coordinates':field_coordinates
        })


class FieldLocationMapMoisture(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        field_obj = Field.objects.get(pk=pk)
        shape_obj = ShapeFileDataCo.objects.get(field=field_obj)
        field_name = shape_obj.field.name
        field_id = shape_obj.field.id
        coordinates = shape_obj.coordinates

        polydata_n = '<subdivisions>'
        polydata_n += '<subdivision fieldId="' + \
            str(field_id) + '" name="' + field_name.replace("'", "") + '">'

        for coord in coordinates:
            polydata_n += '<coord lat="' + \
                str(coord[0]) + '" lng="' + str(coord[1]) + '"/>'

        polydata_n += '</subdivision>'
        polydata_n += '<subdivisions>'
        RATE_LIMIT = 10  # ten requests per minute
        MINUTE_IN_SECONDS = 60
        bm_type = "soilmoisture"
        poly_data = ShapeFileDataCo.objects.get(field_id=field_id)
        one_year_ago_date = (datetime.datetime.now(
        ) - datetime.timedelta(days=1 * 365)).strftime("%Y-%m-%d")
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if request.GET.get("date"):
            today = request.GET.get("date")
        # response_2, response_3 = threaded_process_range(one_year_ago_date, today, poly_data, MINUTE_IN_SECONDS,
        #                                                 RATE_LIMIT, bm_type)
        # response_3 = get_statistics_data(
        #     one_year_ago_date, today, poly_data, MINUTE_IN_SECONDS, RATE_LIMIT, bm_type)
        # print(response_3)
        # url_1 = "https://gate.eos.com/api/gdw/api?api_key=apk" \
        #         ".d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"
        # payload_1 = {
        #     "type": "png",
        #     "params": {
        #         "view_id": response_3['result'][0]['view_id'],
        #         "bm_type": bm_type,
        #         "geometry":
        #             {
        #                 "coordinates": [reverseTuple(poly_data.coordinates)],
        #                 "type": "Polygon"
        #             },
        #         "px_size": 1,
        #         "format": "png"
        #     }
        # }
        #
        # headers = {
        #     'Content-Type': 'application/json'
        # }
        #
        # response_1 = requests.request(
        #     "POST", url_1, headers=headers, data=json.dumps(payload_1))
        # print(f" response 1 is {response_1.json()}")
        # url_2 = f"https://gate.eos.com/api/gdw/api/{response_1.json()['task_id']}?api_key=apk" \
        #         f".d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"
        # # https://gate.eos.com/api/gdw/api/96bb9cb9-564d-4e7c-85f3-53c81e4e6317?api_key=apk.d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c
        # payload_2 = {}

        # response_2 = requests.request("GET", url_2, headers=headers, data=payload_2)
        # while response_2.json()['status'] == 'created':
        #     time.sleep(MINUTE_IN_SECONDS / RATE_LIMIT)
        #     response_2 = requests.request("GET", url_2, headers=headers, data=payload_2)
        #     print('inside while loop')
        #     print(response_2.text)
        # print(response_2)
        # print(response_2.text)
        # print(response_2.json())
        # response_3 = {}
        result_obj = None
        # if get('result') and len(get('result')) > 0:
        #     result_obj = response_3['result'][0]
        return render(request, 'field/field-location-map-moisture.html', {
            'field_obj': field_obj,
            'polydata_n': polydata_n,
            'result_obj': result_obj,
            'field_img': None,
        })


class EosTestTask(LoginRequiredMixin, ListView):
    def get(self, request):
        # field_id = int(request.GET.get('field_id'))
        current_datetime = datetime.datetime.now()
        field_id = 431
        poly_data = ShapeFileDataCo.objects.get(field_id=field_id)

        # apk.bb21f18277c357fe1a7bcaaaf90b0141f5e452038292448723c9b423c46a021f

        url = "https://gate.eos.com/api/gdw/api?api_key=apk.d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"

        RATE_LIMIT = 10  # ten requests per minute
        MINUTE_IN_SECONDS = 60
        payload = {
            "type": "mt_stats",
            "params":
                {
                    "bm_type": "NDVI",
                    "date_start": "2020-01-01",
                    "date_end": "2020-09-20",
                    "geometry":
                        {
                            "coordinates":
                                [reverseTuple(poly_data.coordinates)],
                            "type": "Polygon"
                        },
                    "reference": "ref_" + str(current_datetime),
                    "sensors": ["sentinel2"],
                    "limit": 10
                }
        }
        headers = {
            'Content-Type': 'application/json'
        }
        for request in range(10):
            response = requests.request(
                "POST", url, headers=headers, json=payload)
            time.sleep(MINUTE_IN_SECONDS / RATE_LIMIT)
            print(response.status_code, response.json())
        return JsonResponse({'data': []})


class EosCreateTasksForDateList(LoginRequiredMixin, View):
    def post(self, request):
        current_datetime = datetime.datetime.now()
        current_date = date.today().isoformat()
        days_before = (date.today() - timedelta(days=365)).isoformat()

        field_id_val = int(request.POST.get('field_id_val'))
        index_name_val = request.POST.get('index_name_val')
        poly_data = ShapeFileDataCo.objects.get(field_id=field_id_val)
        create_task_url = "https://gate.eos.com/api/gdw/api?api_key=apk.d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"

        RATE_LIMIT = 10  # ten requests per minute
        MINUTE_IN_SECONDS = 60

        create_task_payload = {
            "type": "mt_stats",
            "params": {
                "bm_type": index_name_val,
                "date_start": days_before,
                "date_end": current_date,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [reverseTuple(poly_data.coordinates)]
                },
                "reference": "ref_" + str(current_datetime),
                "sensors": [
                    "sentinel2"
                ],
                "max_cloud_cover_in_aoi": 0,
                "limit": 100
            }
        }

        create_task_headers = {
            'Content-Type': 'application/json'
        }

        task_response = requests.request(
            "POST", create_task_url, headers=create_task_headers, json=create_task_payload)

        final_res = []
        if task_response.status_code == 202:
            task_data = task_response.json()
            task_id = task_data['task_id']

            task_status_url = "https://gate.eos.com/api/gdw/api/" + task_id + \
                "?api_key=apk.d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c"

            task_status_payload = {}

            task_status_headers = {}

            # print(task_status_data)

            for request in range(10):
                task_status_response = requests.request("GET", task_status_url, headers=task_status_headers,
                                                        json=task_status_payload)
                task_status_response_data = task_status_response

                status = task_status_response_data.get("status", None)
                if status:
                    time.sleep(MINUTE_IN_SECONDS / RATE_LIMIT)
                else:
                    json_list_res = task_status_response_data['result']
                    sorted_date_res = sorted(json_list_res,
                                             key=lambda x: datetime.datetime.strptime(
                                                 x['date'], "%Y-%m-%d"),
                                             reverse=True)
                    # print(sorted_date_res)
                    for date_res in sorted_date_res:
                        # print(date_res)

                        formatted_date = datetime.datetime.strptime(
                            date_res['date'], "%Y-%m-%d").date()
                        df = DateFormat(formatted_date)
                        formatted_date_new = df.format(
                            get_format('DATE_FORMAT'))
                        res = {
                            'date_val': date_res['date'],
                            'date_text': formatted_date_new + " cloud: " + str(date_res['cloud']) + "%",
                        }

                        final_res.append(res)

                    return JsonResponse({'data': final_res})

        print(f'date response : {final_res}')
        return JsonResponse({'data': final_res})


class SearchViewId(LoginRequiredMixin, ListView):
    def get(self, request):
        # field_id = int(request.GET.get('field_id'))
        field_id = 1042
        poly_data = ShapeFileDataCo.objects.get(field_id=field_id)

        url = "https://gate.eos.com/api/lms/search/v2/sentinel2?api_key=apk" \
              ".d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c "

        payload = {
            "search": {
                "date": {"from": "2020-01-01", "to": "2020-03-10"},
                "shape": {
                    "type": "Polygon",
                    "coordinates": [reverseTuple(poly_data.coordinates)]
                }
            },
            "sort": {"date": "desc"},
            "max_cloud_cover_in_aoi": 100,
            "limit": 1
        }

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request(
            "POST", url, headers=headers, data=json.dumps(payload))
        results = json.loads(response.text)
        return JsonResponse({'data': results})


class GettingTaskIdForNdviImage(LoginRequiredMixin, ListView):
    def get(self, request):
        # field_id = int(request.GET.get('field_id'))
        field_id = 1042
        poly_data = ShapeFileDataCo.objects.get(field_id=field_id)
        url = "https://gate.eos.com/api/gdw/api?api_key=apk" \
              ".d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c "

        payload = {
            "type": "jpeg",
            "params": {
                "view_id": "S2/15/S/YA/2020/3/9/0",
                "bm_type": "NDVI",
                "date": {"from": "2020-06-22", "to": "2020-06-22"},
                "geometry":
                    {
                        "coordinates": [reverseTuple(poly_data.coordinates)],
                        "type": "Polygon"
                },
                "px_size": 1,
                "format": "png"
            }
        }

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request(
            "POST", url, headers=headers, data=json.dumps(payload))
        results = json.loads(response.text)
        return JsonResponse({'data': results})


class GettingNdviImage(LoginRequiredMixin, ListView):
    def get(self, request):
        url = "https://gate.eos.com/api/gdw/api/86f4fff1-ee1b-44ac-9d3e-4f967d917054?api_key=apk" \
              ".d48c3b959a25a1a7e7a7b37a2d0f7ffab2ccc1234272b1946eef68f1fec9398c "

        headers = {
            'Content-Type': 'application/octet-stream'
        }

        response = requests.request("GET", url, headers=headers)
        return HttpResponse(response.headers)


@login_required()
def upload_field_vegetation_csv(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        if request.method == "POST":
            csv = request.FILES.get("csv_file")
            df = pd.read_csv(csv)
            for i in range(len(df)):
                line = df.iloc[i]
                field_id = line[0]
                gal_water_saved = line[1]
                water_lbs_saved = line[2]
                co2_eq_reduced = line[3]
                increase_nitrogen = line[4]
                ghg_reduction = line[5]
                land_use_efficiency = line[6]
                grower_premium_percentage = line[7]
                grower_dollar_premium = line[8]
                if Field.objects.filter(id=field_id).count() != 0 :
                    field = Field.objects.get(id=field_id)
                    field.gal_water_saved = gal_water_saved
                    field.water_lbs_saved = water_lbs_saved
                    field.co2_eq_reduced = co2_eq_reduced
                    field.increase_nitrogen = increase_nitrogen
                    field.ghg_reduction = ghg_reduction
                    field.land_use_efficiency = land_use_efficiency
                    field.grower_premium_percentage = grower_premium_percentage
                    field.grower_dollar_premium = grower_dollar_premium
                    field.save()
            messages.success(request,"CSV Uploaded Successfully")
        return render(request, "field/upload_field_vegetation_csv.html",context)



@login_required
def field_csv_download(request):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        filename = 'Field_Details.csv'
        response = HttpResponse(
               content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
        )
        writer = csv.writer(response)
        writer.writerow(['Field name','Grower','Farm name','Field Variety', 'Nitrogen','Phosphorous','Acres'])
        field_details = Field.objects.filter(crop='COTTON').order_by('name')
        for i in field_details: 
           field_id =  i.id
           field_chems = FieldActivity.objects.filter(field=field_id).filter(field_activity='NPK_Application')
           if field_chems.exists():
               for j in field_chems :
                    writer.writerow([i.name,i.grower.name,i.farm.name,i.variety,j.n_nitrogen,j.p_phosporus,i.acreage])
           else :
               writer.writerow([i.name,i.grower.name,i.farm.name,i.variety,'','',i.acreage])
           

        return response
    else:
        return redirect('/')
    

@login_required
def field_data_update(request):
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        fields = Field.objects.all().order_by('name').values('id')
        for i in fields :
            old_field = Field.objects.get(id=i['id'])
            
            update_field = FieldUpdated(field_id=old_field.id,name=old_field.name,crop_year="2022",
                            fsa_farm_number=old_field.fsa_farm_number,fsa_tract_number=old_field.fsa_tract_number,
                            fsa_field_number=old_field.fsa_field_number,crop=old_field.crop,variety=old_field.variety,
                            yield_per_acre=old_field.yield_per_acre,total_yield=old_field.total_yield,crop_tech=old_field.crop_tech,
                            previous_crop=old_field.previous_crop,stand_count=old_field.stand_count,plant_date=old_field.plant_date,
                            harvest_date=old_field.harvest_date)
            update_field.save()
            activity = FieldActivity.objects.filter(field_id=i['id']).values('id')
            for i in activity :
                get_activity = FieldActivity.objects.get(id=i['id'])
                get_activity.field_updated = update_field
                get_activity.save()
        return HttpResponse ("Field Updated.")
    else:
        return redirect('/')