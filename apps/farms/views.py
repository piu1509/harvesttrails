"""Views related to farm model"""
from multiprocessing import context
from django.http.response import HttpResponse
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.utils import IntegrityError
from apps.accounts.models import User, LogTable
from apps.farms.forms import FarmForm
from apps.grower.models import Grower, Consultant
from apps.farms.models import Farm, FarmGrouping, CsvToFarm
from apps.field.models import Field, ShapeFileDataCo, Crop
from apps.farms.serializers import FarmSerializer, FarmJsonList
from apps.grower.serializers import GrowerListSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from apps.storage.models import ShapeFileDataCo as StorageShapeFileDataCo, Storage
import json
from django.db.models import Q
from apps.field.models import Crop, CropVariety, CropType
from apps.farms.forms import *
from rest_framework import serializers
# pylint: disable=no-member,expression-not-assigned, too-many-locals, too-many-ancestors, too-many-ancestors, bare-except


def farmlocationview(request):
    return render(request, 'farms/farm_location.html')


class FarmCreateView(LoginRequiredMixin, CreateView):  # pylint: disable=too-many-ancestors
    """View to create a field"""
    model = Farm
    form_class = FarmForm
    template_name = 'farms/farm_create.html'
    success_url = reverse_lazy('farm-list')

    def get_context_data(self, **kwargs):
        context = super(FarmCreateView, self).get_context_data(**kwargs)
        context['crops'] = Crop.objects.all()
        
        if 'Grower' in self.request.user.get_role() and not self.request.user.is_superuser:
            # do something grower

            context["growers_dpdwn"] = Grower.objects.filter(
                id=self.request.user.grower.id).order_by('name')
            return context
        else:
            if self.request.user.is_consultant:
                # do something consultant
                consultant_id = Consultant.objects.get(
                    email=self.request.user.email).id
                get_growers = Grower.objects.filter(consultant=consultant_id)
                grower_ids = [data.id for data in get_growers]
                context["growers_dpdwn"] = Grower.objects.filter(
                    id__in=grower_ids).order_by('name')
                return context

            else:
                # do something allpower
                context["growers_dpdwn"] = Grower.objects.all().order_by('name')
                return context

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new farm"""
        name = form.cleaned_data.get('name')

        cultivation_year = form.cleaned_data.get('cultivation_year')
        area = form.cleaned_data.get('area')
        land_type = form.cleaned_data.get('land_type')
        zipcode = form.cleaned_data.get('zipcode')
        grower = form.cleaned_data.get('grower')
        
        log_type, log_status, log_device = "Farm", "Added", "Web"
        log_idd, log_name = None, name
        log_details = f"name = {name} | cultivation_year = {cultivation_year} | area = {area} | land_type = {land_type} | zipcode = {zipcode} | grower = {grower}"
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
                            action_by_email=action_by_email,action_by_role=action_by_role,
                            log_details=log_details,log_device=log_device)
        logtable.save()
        messages.success(self.request, f'Farm {name} Created Successfully!')
        return super().form_valid(form)


class FarmListView(LoginRequiredMixin, ListView):  # pylint: disable=too-many-ancestors
    """View to list farm"""
    model = Farm
    form_class = FarmForm
    context_object_name = "farms"
    template_name = 'farms/farm_list.html'

    # def get_queryset(self):
    #     """returns all farms for superuser and farms mapped to grower for other users"""
    #     # if self.request.user.is_superuser or 'Farm Management' in self.request.user.get_role_perm():
    #     #     return self.model.objects.all().order_by('-created_date')
    #     # return self.model.objects.filter(grower=self.request.user.grower).order_by('-created_date')

    #     # if self.request.user.is_consultant:
    #     #     consultant_id = Consultant.objects.get(email=self.request.user.email).id
    #     #     data = Grower.objects.raw("select id,grower_id from grower_grower_consultant where consultant_id=%s",[consultant_id])
    #     #     grower_ids = [id.grower_id for id in data]
    #     #     grower_data = Grower.objects.filter(id__in=grower_ids)
    #     #     return self.model.objects.filter(grower__in=grower_data).order_by('-created_date')
    #     # return self.model.objects.all().order_by('-created_date')

    #     if 'Grower' in self.request.user.get_role() and not self.request.user.is_superuser:
    #         # do something grower
    #         # SustainabilitySurvey_data = SustainabilitySurvey.objects.filter(grower_id=self.request.user.grower.id)
    #         return self.model.objects.filter(grower_id=self.request.user.grower.id).order_by('-created_date')

    #     else:
    #         if self.request.user.is_consultant:
    #             # do something consultant
    #             consultant_id = Consultant.objects.get(
    #                 email=self.request.user.email).id
    #             get_growers = Grower.objects.filter(consultant=consultant_id)
    #             grower_ids = [data.id for data in get_growers]
    #             grower_data = Grower.objects.filter(id__in=grower_ids)

    #             if self.request.GET.get('farm_name'):
    #                 farm_name_search = self.request.GET.get('farm_name')
    #                 return self.model.objects.filter(name__icontains=farm_name_search).filter(grower__in=grower_data).order_by('-created_date')
                        
    #             if self.request.GET.get('farm_name_all'):
    #                 return self.model.objects.filter(grower__in=grower_data).order_by('-created_date')

    #             return self.model.objects.filter(grower__in=grower_data).order_by('-created_date')

    #         else:
    #             # do something allpower
    #             # growers = Grower.objects.all().order_by('name')
    #             # context = {'growers':growers}
    #             # farms = self.model.objects.all().order_by('-created_date')
    #             # context['farms'] = farms
    #             return self.model.objects.all().order_by('-created_date')
    #             # return context

    def get_context_data(self, **kwargs):
        """filter farms as per grower selected in dropdown"""
        context = super().get_context_data(**kwargs)
        # Grower...
        if 'Grower' in self.request.user.get_role() and not self.request.user.is_superuser:
            farms = self.model.objects.filter(grower_id=self.request.user.grower.id).order_by('-created_date')
            grower = Grower.objects.filter(id=self.request.user.grower.id)
            context['farms'] = farms
            context['growers'] = grower


        # consultant
        elif self.request.user.is_consultant:
            consultant_id = Consultant.objects.get(
            email=self.request.user.email).id
            get_growers = Grower.objects.filter(consultant=consultant_id)
            grower_ids = [data.id for data in get_growers]
            grower_data = Grower.objects.filter(id__in=grower_ids)

            context['farms'] = self.model.objects.filter(grower__in=grower_data).order_by('-created_date')
            context['growers'] = grower_data
            
            all_farm_name = context['farms'].values('name').order_by('name')
            g_name = grower_data.values('name')
            g_name_lst = [i['name'] for i in g_name]
            all_farm_name_lst = [i['name'] for i in all_farm_name]
            
            all_select_search = g_name_lst + all_farm_name_lst
            select_search_json = json.dumps(all_select_search)
            context['select_search_json'] = select_search_json

            if self.request.GET.get('farm_name'):
                farm_name_search = self.request.GET.get('farm_name')
                context['farms'] = self.model.objects.filter(Q(name__icontains=farm_name_search) | Q(grower__name__icontains=farm_name_search)).filter(grower__in=grower_data).order_by('-created_date')
                context['get_farm_name'] = farm_name_search
                # return self.model.objects.filter(name__icontains=farm_name_search).filter(grower__in=grower_data).order_by('-created_date')
                                
            if self.request.GET.get('grower_id'):
                grower_id = int(self.request.GET.get('grower_id'))
                if grower_id != 0:
                    context['selectedGrower'] = Grower.objects.get(
                        pk=grower_id)                    
                    context['farms'] = self.model.objects.filter(grower_id=grower_id).order_by('-created_date')                     

                else:
                    context['farms'] = self.model.objects.filter(grower__in=grower_data).order_by('-created_date')
                                
        
        # all power ...........
        elif self.request.user.is_superuser or 'SubAdmin' in self.request.user.get_role() or 'SuperUser' in self.request.user.get_role():
            context['growers'] = Grower.objects.all().order_by('name')
            all_farm_name = self.model.objects.values('name').order_by('name')
            g_name = context['growers'].values('name')
            g_name_lst = [i['name'] for i in g_name]
            all_farm_name_lst = [i['name'] for i in all_farm_name]
            
            all_select_search = g_name_lst + all_farm_name_lst
            select_search_json = json.dumps(all_select_search)
            context['select_search_json'] = select_search_json
            if self.request.GET.get('grower_id'):
                grower_id = int(self.request.GET.get('grower_id'))
                if grower_id != 0:
                    context['selectedGrower'] = Grower.objects.get(
                        pk=grower_id)
                    servicedata_final = self.model.objects.filter(
                        grower=grower_id).order_by('-created_date')

                else:
                    servicedata_final = self.model.objects.all().order_by(
                        '-created_date')

            else:

                servicedata_final = self.model.objects.all().order_by(
                    '-created_date')
                # servicedata_final = self.model.objects.all().order_by('-created_date')
                
                page = self.request.GET.get('page', 1)
                

                # context['farms'] = paginator.get_page(page)
                if self.request.GET.get('farm_name'):
                    farm_name_search = self.request.GET.get('farm_name')
                    servicedata_final = self.model.objects.filter(Q(name__icontains=farm_name_search) | Q(grower__name__icontains=farm_name_search)).order_by('-created_date')
                    context['get_farm_name'] = farm_name_search
                if self.request.GET.get('farm_name_all'):
                    servicedata_final = self.model.objects.all().order_by('-created_date')
                
            paginator = Paginator(servicedata_final, 50)
            page = self.request.GET.get('page', 1)
            try:
                field_list = paginator.page(page)
            except PageNotAnInteger:
                field_list = paginator.page(page)
            except EmptyPage:
                field_list = paginator.page(paginator.num_pages)
            context['farms'] = field_list
        return context


def testing(request):
    return render(request, 'farms/testing.html')


class FarmUpdateView(LoginRequiredMixin, UpdateView):  # pylint: disable=too-many-ancestors
    """Update view for farm"""
    model = Farm
    form_class = FarmForm
    template_name = 'farms/farm_update.html'
    success_url = reverse_lazy('farm-list')

    def get_context_data(self, **kwargs):
        context = super(FarmUpdateView, self).get_context_data(**kwargs)
        context['crops'] = Crop.objects.all()

        pk = self.kwargs.get('pk')

        current_farm = self.model.objects.get(pk=pk)
        context['selected_grower'] = current_farm.grower_id
        context['selected_landtype'] = current_farm.land_type
        context['selected_state'] = current_farm.state
        if 'Grower' in self.request.user.get_role() and not self.request.user.is_superuser:
            # do something grower

            context["growers_dpdwn"] = Grower.objects.filter(
                id=self.request.user.grower.id).order_by('name')
            return context
        else:
            if self.request.user.is_consultant:
                # do something consultant
                consultant_id = Consultant.objects.get(
                    email=self.request.user.email).id
                get_growers = Grower.objects.filter(consultant=consultant_id)
                grower_ids = [data.id for data in get_growers]
                context["growers_dpdwn"] = Grower.objects.filter(
                    id__in=grower_ids).order_by('name')
                return context

            else:
                # do something allpower
                context["growers_dpdwn"] = Grower.objects.all().order_by('name')
                return context

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new farm"""
        name = form.cleaned_data.get('name')
        cultivation_year = form.cleaned_data.get('cultivation_year')
        land_type = form.cleaned_data.get('land_type')
        area = form.cleaned_data.get('area')
        zipcode = form.cleaned_data.get('zipcode')
        grower = form.cleaned_data.get('grower')
        log_type, log_status, log_device = "Farm", "Edited", "Web"
        log_idd, log_name = self.kwargs.get('pk'), name
        log_details = f"name = {name} | cultivation_year = {cultivation_year} | area = {area} | land_type = {land_type} | zipcode = {zipcode} | grower = {grower}"
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
        messages.success(self.request, f'Farm {name} Updated Successfully!')
        return super().form_valid(form)


class FarmDetailView(LoginRequiredMixin, DetailView):
    '''Generic Class Based View get the farm details of a Farm created'''
    model = Farm


class FarmDeleteView(LoginRequiredMixin, View):  # pylint: disable=too-many-ancestors
    """View to delete a farm object"""

    def get(self, request, pk):
        obj = Farm.objects.get(pk=pk)
        # 06-04-23
        log_type, log_status, log_device = "Farm", "Deleted", "Web"
        log_idd, log_name = pk, obj.name
        name = obj.name
        cultivation_year = obj.cultivation_year
        land_type = obj.land_type
        area = obj.area
        zipcode = obj.zipcode
        grower = obj.grower.name
        log_details = f"name = {name} | cultivation_year = {cultivation_year} | area = {area} | land_type = {land_type} | zipcode = {zipcode} | grower = {grower}"
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


class FarmGroupingListView(LoginRequiredMixin, ListView):  # pylint: disable=too-many-ancestors
    """View to list the farm groupping criteria"""
    model = FarmGrouping
    fields = ('grouping_criteria',)
    template_name = 'farms/grouping.html'


class FarmGroupingCreateView(LoginRequiredMixin, CreateView):  # pylint: disable=too-many-ancestors
    """View to create a new group"""
    model = FarmGrouping
    fields = ('grouping_criteria',)
    template_name = 'farms/grouping_create.html'
    success_url = reverse_lazy('grouping')

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new farm"""
        grouping_criteria = form.cleaned_data.get('grouping_criteria')
        messages.success(
            self.request, f'{grouping_criteria} Group Created Successfully!')
        return super().form_valid(form)


class FarmGroupingUpdateView(LoginRequiredMixin, UpdateView):  # pylint: disable=too-many-ancestors
    """Update view for farm grouping object"""
    model = FarmGrouping
    fields = ('grouping_criteria',)
    template_name = 'farms/grouping_update.html'
    success_url = reverse_lazy('grouping')

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new farm"""
        grouping_criteria = form.cleaned_data.get('grouping_criteria')
        messages.success(
            self.request, f'{grouping_criteria} Group Updated Successfully!')
        return super().form_valid(form)


class FarmGroupingDeleteView(LoginRequiredMixin, View):  # pylint: disable=too-many-ancestors
    """View to delete a farm grouping object"""

    def get(self, request, pk):
        obj = FarmGrouping.objects.get(pk=pk)
        obj.delete()
        return HttpResponse(1)


class CsvFarmCreateView(LoginRequiredMixin, CreateView):  # pylint: disable=too-many-ancestors
    """View to create a Farms via CSV file"""
    model = CsvToFarm
    fields = "__all__"
    template_name = 'farms/csv_farm_create.html'
    #success_url = reverse_lazy('farm-list')


class CsvFarmMappingView(LoginRequiredMixin, View):
    '''View for displaing CSV header for mapping'''
    #pylint: disable=protected-access
    #model_fields = [farm.name for farm in Farm._meta.get_fields()]
    model_fields = ['name', 'cultivation_year', 'area', 'land_type',
                    'state', 'county', 'village', 'town', 'street', 'zip']
    model_fields_show = [i.replace('_', ' ').title() for i in model_fields]

    def get(self, request, pk):
        '''Function for get request
        Displaying CSV headers for mapping'''

        grower_names = Grower.objects.all()
        file_name = CsvToFarm.objects.get(pk=pk).csv_file
        try:
            df_file = pd.read_csv(file_name)
        except:
            messages.error(request, "CSV file format is invalid. \
                \nPlease check the format and try again")
            return redirect('csv-farm-create')

        # If CSV file havin only header
        if df_file.shape[0] == 0:
            messages.error(request, "Rows are missing in your CSV file, \
                please upload the file with data.")
            return redirect('csv-farm-create')

        df_file.insert(0, 'Blank', None)
        map_col = df_file.columns.tolist()

        return render(request, 'farms/csv_farm_mapping.html', {"file_name": file_name,
                                                               'model_fields': self.model_fields_show,
                                                               'map_col': map_col, 'grower_names': grower_names})

    def post(self, request, pk):
        '''Function for post request
        Displaying import status'''

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
        file_name = CsvToFarm.objects.get(pk=pk).csv_file
        # Opening file using pandas dataframe
        df_file = pd.read_csv(file_name)
        df_file.insert(0, 'Blank', None)
        # Arrangin columns names in order
        #pylint: disable=unsubscriptable-object
        df_file = df_file[new_col_list].copy()

        # Changing the columns names as per model fields
        df_file.columns = self.model_fields

        # Removing nan and duplicate values
        df_file.dropna(subset=['name'], how='any', inplace=True)
        df_file.drop_duplicates(
            subset=['name'], ignore_index=True, inplace=True)

        # Empty list for storing objects for bulk creation
        myobj = []

        # Creating object for every row and appending it on 'myobj' list
        for row in df_file.index:
            area = df_file.iloc[row, 2]
            if not isinstance(area, float):
                try:
                    area = float(area)
                except:
                    area = None

            zip_ = df_file.iloc[row, 9]
            if not isinstance(zip_, int):
                try:
                    zip_ = int(zip_)
                except:
                    zip_ = None

            myobj.append(Farm(name=df_file.iloc[row, 0],
                              cultivation_year=df_file.iloc[row, 1],
                              area=area,
                              land_type=df_file.iloc[row, 3],
                              state=df_file.iloc[row, 4],
                              county=df_file.iloc[row, 5],
                              village=df_file.iloc[row, 6],
                              town=df_file.iloc[row, 7],
                              street=df_file.iloc[row, 8],
                              zipcode=zip_,
                              grower=Grower.objects.get(pk=grower_id))
                         )
        # Saving all the objects in database
        try:
            Farm.objects.bulk_create(myobj)
        except IntegrityError:
            messages.error(
                request, "Some farms name(s) already exists with the same name.")
            return redirect('csv-farm-create')
        except:
            messages.error(request, "Data is not in a proper format in the CSV file.\
                Please check the data and try again.")
            return redirect('csv-farm-create')

        messages.success(
            request, f"{len(myobj)} Farm(s) created successfully.")
        return redirect('farm-list')


class FarmLocationMap(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):

        if 'Grower' in request.user.get_role() and not request.user.is_superuser :
            # do something grower
            grower_id = request.user.grower.id
            get_growers = Grower.objects.filter(id=grower_id).order_by('name')
        else:
            if request.user.is_consultant:
                # do something consultant
                consultant_id = Consultant.objects.get(
                    email=request.user.email).id
                get_growers = Grower.objects.filter(
                    consultant=consultant_id).order_by('name')
            else:
                # do something allpower
                get_growers = Grower.objects.all().order_by('name')

        selected_grower = self.kwargs.get('grower_id')

        if selected_grower > 0:
            field_obj = Field.objects.filter(
                farm=pk, grower_id=selected_grower)
        else:
            field_obj = Field.objects.filter(farm=pk)

        shape_obj = ShapeFileDataCo.objects.filter(field__in=field_obj)

        polydata_n = '<subdivisions>'
        for shape in shape_obj:
            coordinates = shape.coordinates
            polydata_n += '<subdivision fieldId="' + \
                str(shape.field.id) + '" name="' + \
                shape.field.name.replace("'", "") + '">'

            for coord in coordinates:
                polydata_n += '<coord lat="' + \
                    str(coord[0]) + '" lng="' + str(coord[1]) + '"/>'

            polydata_n += '</subdivision>'
        polydata_n += '<subdivisions>'

        return render(request, 'farms/farm-location-map.html', {
            'polydata_n': polydata_n,
            'get_growers': get_growers,
            'selected_grower': selected_grower,
        })


# class AllFarmLocationMap(LoginRequiredMixin, View):
#     def get(self, request, *args, **kwargs):

#         selected_grower = self.kwargs.get('grower_id')

#         if 'Grower' in request.user.get_role() and not request.user.is_superuser:
#             # do something grower
#             grower_id = request.user.grower.id
#             get_growers = Grower.objects.filter(id=grower_id).order_by('name')

#             if selected_grower == 0:
#                 farm_obj = Farm.objects.filter(grower__in=get_growers)
#             else:
#                 farm_obj = Farm.objects.filter(grower_id=selected_grower)

#             field_obj = Field.objects.filter(farm__in=farm_obj)
#             shape_obj = ShapeFileDataCo.objects.filter(field__in=field_obj)
#         else:
#             if request.user.is_consultant:
#                 # do something consultant
#                 consultant_id = Consultant.objects.get(
#                     email=request.user.email).id
#                 get_growers = Grower.objects.filter(
#                     consultant=consultant_id).order_by('name')

#                 if selected_grower == 0:
#                     farm_obj = Farm.objects.filter(grower__in=get_growers)
#                 else:
#                     farm_obj = Farm.objects.filter(grower_id=selected_grower)

#                 field_obj = Field.objects.filter(farm__in=farm_obj)
#                 shape_obj = ShapeFileDataCo.objects.filter(field__in=field_obj)
#             else:
#                 # do something allpower
#                 get_growers = Grower.objects.all().order_by('name')

#                 if selected_grower == 0:
#                     farm_obj = Farm.objects.filter(grower__in=get_growers)
#                 else:
#                     farm_obj = Farm.objects.filter(grower_id=selected_grower)

#                 field_obj = Field.objects.filter(farm__in=farm_obj)
#                 shape_obj = ShapeFileDataCo.objects.filter(field__in=field_obj)

#         polydata_n = '<subdivisions>'
#         for shape in shape_obj:
#             coordinates = shape.coordinates
#             polydata_n += '<subdivision fieldId="' + \
#                 str(shape.field.id) + '" name="' + \
#                 shape.field.name.replace("'", "") + '">'

#             for coord in coordinates:
#                 polydata_n += '<coord lat="' + \
#                     str(coord[0]) + '" lng="' + str(coord[1]) + '"/>'

#             polydata_n += '</subdivision>'
#         polydata_n += '<subdivisions>'

        

#         return render(request, 'farms/all-farm-location-map.html', {
#             'polydata_n': polydata_n,
#             'get_growers': get_growers,
#             'selected_grower': selected_grower,
#         })


# class AllFarmLocationMap(LoginRequiredMixin, View):
#     def get(self, request, *args, **kwargs):

#         selected_grower = self.kwargs.get('grower_id')

#         if 'Grower' in request.user.get_role() and not request.user.is_superuser:
#             # do something grower
#             grower_id = request.user.grower.id
#             get_growers = Grower.objects.filter(id=grower_id).order_by('name')

#             if selected_grower == 0:
#                 farm_obj = Farm.objects.filter(grower__in=get_growers)
#             else:
#                 farm_obj = Farm.objects.filter(grower_id=selected_grower)

#             field_obj = Field.objects.filter(farm__in=farm_obj)
#             shape_obj = ShapeFileDataCo.objects.filter(field__in=field_obj)

#         # Consultant ......
#         elif request.user.is_consultant:
#             # do something consultant
#             consultant_id = Consultant.objects.get(
#                 email=request.user.email).id
#             get_growers = Grower.objects.filter(
#                 consultant=consultant_id).order_by('name')

#             if selected_grower == 0:
#                 farm_obj = Farm.objects.filter(grower__in=get_growers)
#             else:
#                 farm_obj = Farm.objects.filter(grower_id=selected_grower)

#             field_obj = Field.objects.filter(farm__in=farm_obj)
#             shape_obj = ShapeFileDataCo.objects.filter(field__in=field_obj)

#         # # do something allpower
#         elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            
#             get_growers = Grower.objects.all().order_by('name')

#             if selected_grower == 0:
#                 farm_obj = Farm.objects.filter(grower__in=get_growers)
#             else:
#                 farm_obj = Farm.objects.filter(grower_id=selected_grower)

#             field_obj = Field.objects.filter(farm__in=farm_obj)
#             shape_obj1 = ShapeFileDataCo.objects.filter(field__in=field_obj)
        
        
#         polydata_n1 = '<subdivisions>'
#         for shape in shape_obj1:
#             coordinates = shape.coordinates
#             polydata_n1 += '<subdivision fieldId="' + \
#                 str(shape.field.id) + '" name="' + \
#                 shape.field.name.replace("'", "") + '">'

#             for coord in coordinates:
#                 polydata_n1 += '<coord lat="' + \
#                     str(coord[0]) + '" lng="' + str(coord[1]) + '"/>'

#             polydata_n1 += '</subdivision>'
#         polydata_n1 += '<subdivision>'

#         get_growers = Grower.objects.all().order_by('name')
#         storage_obj = Storage.objects.filter(grower_id__in=get_growers)
#         shape_obj = StorageShapeFileDataCo.objects.filter(storage__in=storage_obj)

#         polydata_n = '<subdivisions>'
#         for shape in shape_obj:
#             coordinates = shape.coordinates
#             polydata_n += '<subdivision storageId="' + \
#                 str(shape.storage.id) + '" name="' + \
#                 shape.storage.storage_name.replace("'", "") + '">'

#             for coord in coordinates:
#                 polydata_n += '<coord lat="' + \
#                     str(coord[0]) + '" lng="' + str(coord[1]) + '"/>'

#             polydata_n += '</subdivision>'
#         polydata_n += '<subdivisions>'
#         # print(polydata_n)
#         polydata_n2 = polydata_n1 + polydata_n
#         # print(polydata_n2)
#         return render(request, 'farms/all-farm-location-map.html', {
#             'polydata_n': polydata_n2,
#             'get_growers': get_growers,
#             'selected_grower': selected_grower,
#         })


class AllFarmLocationMap(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        selected_grower = self.kwargs.get('grower_id')
        shape_obj1 = ''
        
        
        if 'Grower' in request.user.get_role() and not request.user.is_superuser :
            # do something grower
            grower_id = request.user.grower.id
            get_growers = Grower.objects.filter(id=grower_id).order_by('name')

            if selected_grower == 0:
                farm_obj = Farm.objects.filter(grower__in=get_growers)
            else:
                farm_obj = Farm.objects.filter(grower_id=selected_grower)

            field_obj = Field.objects.filter(farm__in=farm_obj)
            shape_obj1 = ShapeFileDataCo.objects.filter(field__in=field_obj)

            storage_obj = Storage.objects.filter(grower_id=grower_id)
            shape_obj = StorageShapeFileDataCo.objects.filter(storage__in=storage_obj)

            # New Code ...
            print(get_growers) 
            # Field shapFile ...........
            polydata_n1 = '<subdivisions>'
            for shape in shape_obj1:
                coordinates = shape.coordinates
                polydata_n1 += '<subdivision fieldId="' + \
                    str(shape.field.id) + '" name="' + \
                    shape.field.name.replace("'", "") + '">'

                for coord in coordinates:
                    polydata_n1 += '<coord lat="' + \
                        str(coord[0]) + '" lng="' + str(coord[1]) + '"/>'

                polydata_n1 += '</subdivision>'
            polydata_n1 += '<subdivisions>'

            # Storage Shapefile ...
            # get_growers = Grower.objects.filter(consultant=consultant_id).order_by('name')
                
            # storage_obj = Storage.objects.filter(grower_id__in=get_growers)
            # shape_obj = StorageShapeFileDataCo.objects.filter(storage__in=storage_obj)

            polydata_n = '<subdivisions>'
            for shape in shape_obj:
                coordinates = shape.coordinates
                polydata_n += '<subdivision storageId="' + \
                    str(shape.storage.id) + '" name="' + \
                    shape.storage.storage_name.replace("'", "") + '">'

                for coord in coordinates:
                    polydata_n += '<coord lat="' + \
                        str(coord[0]) + '" lng="' + str(coord[1]) + '"/>'

                polydata_n += '</subdivision>'
            polydata_n += '<subdivisions>'

            # adding farms + storage .......
            polydata_n2 = polydata_n1 + polydata_n
            
            # For Storage Latitude and Longitude .....
            storage_pin = []
            for item in storage_obj:
                if item.latitude != None:
                    storage_pin.append(item)
            print('storage_pin', storage_pin)


            polydata_n = '<subdivisions>'
            for shape in storage_pin:
                # coordinates = shape.coordinates
                polydata_n += '<subdivision pointerId="' + \
                    str(shape.id) + '" name="' + \
                    shape.storage_name.replace("'", "") + '">'

                for coord in storage_pin:
                    polydata_n += '<coord lat="' + \
                        str(coord.latitude) + '" lng="' + str(coord.longitude) + '"/>'

                polydata_n += '</subdivision>'
            polydata_n += '<subdivisions>' 

        # Consultant ......
        elif request.user.is_consultant:
            # do something consultant
            consultant_id = Consultant.objects.get(
                email=request.user.email).id
            get_growers = Grower.objects.filter(
                consultant=consultant_id).order_by('name')

            storage_obj = Storage.objects.filter(grower_id__in=get_growers)
            
            if selected_grower == 0:
                farm_obj = Farm.objects.filter(grower__in=get_growers)
                field_obj = Field.objects.filter(farm__in=farm_obj)
                shape_obj1 = ShapeFileDataCo.objects.filter(field__in=field_obj)
                storage_obj = Storage.objects.filter(grower_id__in=get_growers)
                shape_obj = StorageShapeFileDataCo.objects.filter(storage__in=storage_obj)

            else:
                farm_obj = Farm.objects.filter(grower_id=selected_grower)

                field_obj = Field.objects.filter(farm__in=farm_obj)
                shape_obj1 = ShapeFileDataCo.objects.filter(field__in=field_obj)

                storage_obj = Storage.objects.filter(grower_id=selected_grower)
                shape_obj = StorageShapeFileDataCo.objects.filter(storage__in=storage_obj)

            # New Code ...
            print(get_growers) 
            # Field shapFile ...........
            polydata_n1 = '<subdivisions>'
            for shape in shape_obj1:
                coordinates = shape.coordinates
                polydata_n1 += '<subdivision fieldId="' + \
                    str(shape.field.id) + '" name="' + \
                    shape.field.name.replace("'", "") + '">'

                for coord in coordinates:
                    polydata_n1 += '<coord lat="' + \
                        str(coord[0]) + '" lng="' + str(coord[1]) + '"/>'

                polydata_n1 += '</subdivision>'
            polydata_n1 += '<subdivisions>'

            # Storage Shapefile ...
            get_growers = Grower.objects.filter(consultant=consultant_id).order_by('name')
                
            # storage_obj = Storage.objects.filter(grower_id__in=get_growers)
            # shape_obj = StorageShapeFileDataCo.objects.filter(storage__in=storage_obj)

            polydata_n = '<subdivisions>'
            for shape in shape_obj:
                coordinates = shape.coordinates
                polydata_n += '<subdivision storageId="' + \
                    str(shape.storage.id) + '" name="' + \
                    shape.storage.storage_name.replace("'", "") + '">'

                for coord in coordinates:
                    polydata_n += '<coord lat="' + \
                        str(coord[0]) + '" lng="' + str(coord[1]) + '"/>'

                polydata_n += '</subdivision>'
            polydata_n += '<subdivisions>'

            # adding farms + storage .......
            polydata_n2 = polydata_n1 + polydata_n
            
            # For Storage Latitude and Longitude .....
            storage_pin = []
            for item in storage_obj:
                if item.latitude != None:
                    storage_pin.append(item)
            print('storage_pin', storage_pin)


            polydata_n = '<subdivisions>'
            for shape in storage_pin:
                # coordinates = shape.coordinates
                polydata_n += '<subdivision pointerId="' + \
                    str(shape.id) + '" name="' + \
                    shape.storage_name.replace("'", "") + '">'

                for coord in storage_pin:
                    polydata_n += '<coord lat="' + \
                        str(coord.latitude) + '" lng="' + str(coord.longitude) + '"/>'

                polydata_n += '</subdivision>'
            polydata_n += '<subdivisions>'   



        # # do something allpower
        elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            
            get_growers = Grower.objects.all().order_by('name')
            storage_obj = Storage.objects.filter(grower_id__in=get_growers)

            if selected_grower == 0:
                farm_obj = Farm.objects.filter(grower__in=get_growers)
                field_obj = Field.objects.filter(farm__in=farm_obj)
                shape_obj1 = ShapeFileDataCo.objects.filter(field__in=field_obj)
                storage_obj = Storage.objects.filter(grower_id__in=get_growers)
                shape_obj = StorageShapeFileDataCo.objects.filter(storage__in=storage_obj)
            else:
                farm_obj = Farm.objects.filter(grower_id=selected_grower)
                field_obj = Field.objects.filter(farm__in=farm_obj)
                shape_obj1 = ShapeFileDataCo.objects.filter(field__in=field_obj)

                storage_obj = Storage.objects.filter(grower_id=selected_grower)
                shape_obj = StorageShapeFileDataCo.objects.filter(storage__in=storage_obj)

            # field_obj = Field.objects.filter(farm__in=farm_obj)
            # shape_obj1 = ShapeFileDataCo.objects.filter(field__in=field_obj)
        
        
            # Field shapFile ...........
            polydata_n1 = '<subdivisions>'
            for shape in shape_obj1:
                coordinates = shape.coordinates
                polydata_n1 += '<subdivision fieldId="' + \
                    str(shape.field.id) + '" name="' + \
                    shape.field.name.replace("'", "") + '">'

                for coord in coordinates:
                    polydata_n1 += '<coord lat="' + \
                        str(coord[0]) + '" lng="' + str(coord[1]) + '"/>'

                polydata_n1 += '</subdivision>'
            polydata_n1 += '<subdivisions>'

            # Storage Shapefile ...
            # get_growers = Grower.objects.all().order_by('name')
            # storage_obj = Storage.objects.filter(grower_id__in=get_growers)
            # shape_obj = StorageShapeFileDataCo.objects.filter(storage__in=storage_obj)

            polydata_n = '<subdivisions>'
            for shape in shape_obj:
                coordinates = shape.coordinates
                polydata_n += '<subdivision storageId="' + \
                    str(shape.storage.id) + '" name="' + \
                    shape.storage.storage_name.replace("'", "") + '">'

                for coord in coordinates:
                    polydata_n += '<coord lat="' + \
                        str(coord[0]) + '" lng="' + str(coord[1]) + '"/>'

                polydata_n += '</subdivision>'
            polydata_n += '<subdivisions>'

            # adding farms + storage .......
            polydata_n2 = polydata_n1 + polydata_n
            
            # For Storage Latitude and Longitude .....
            storage_pin = []
            for item in storage_obj:
                if item.latitude != None:
                    storage_pin.append(item)
            print('storage_pin', storage_pin)


            polydata_n = '<subdivisions>'
            for shape in storage_pin:
                # coordinates = shape.coordinates
                polydata_n += '<subdivision pointerId="' + \
                    str(shape.id) + '" name="' + \
                    shape.storage_name.replace("'", "") + '">'

                for coord in storage_pin:
                    polydata_n += '<coord lat="' + \
                        str(coord.latitude) + '" lng="' + str(coord.longitude) + '"/>'

                polydata_n += '</subdivision>'
            polydata_n += '<subdivisions>'


        return render(request, 'farms/all-farm-location-map.html', {
            'polydata_n': polydata_n2,
            'polydata_n1': polydata_n,
            'get_growers': get_growers,
            'selected_grower': selected_grower,
        })
    


class CropVarietySerializer(serializers.ModelSerializer):
    class Meta:
        model = CropVariety
        fields = ['variety_name', 'variety_code']

class CropTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CropType
        fields = ['type']

class CropSerializer(serializers.ModelSerializer):
    cropVariety = CropVarietySerializer(many=True, read_only=True)  # Nested serializer
    cropType = CropTypeSerializer(many=True, read_only=True)

    class Meta:
        model = Crop
        fields = ['id', 'name', 'code', 'cropVariety', 'cropType']



def crop_management(request):
    crops = Crop.objects.prefetch_related('cropVariety').all()
    if request.method == "POST":
        search_query = request.POST.get("crop_name")
        if search_query:
            crops = crops.filter(name__icontains=search_query)
    crop_serializer = CropSerializer(crops, many=True)
    return render(request, 'farms/crop-management-list.html', {
        'crops': crop_serializer.data,
        'search_query': search_query if request.method == "POST" else ''
    })



def create_crop(request):
    if request.method == 'POST':
        crop_name = request.POST.get('name')
        variety_names = request.POST.getlist('variety_name')
        types = request.POST.getlist('crop_type')
        crop = Crop.objects.create(name=crop_name)
        for variety_name in variety_names:
            if variety_name:  # Only save if the variety name is not empty
                CropVariety.objects.create(crop=crop, variety_name=variety_name)
        for type in types:
            if type:
                CropType.objects.create(crop=crop, type=type)
        return redirect('crop_management_list')
    return render(request, 'farms/create_crop.html')

def edit_crop(request, crop_id):
    crop = get_object_or_404(Crop, id=crop_id)
    varieties = CropVariety.objects.filter(crop=crop).order_by("-id")
    varieties = varieties.reverse
    types = CropType.objects.filter(crop=crop).order_by("-id")
    types = types.reverse
    if request.method == 'POST':
        crop_name = request.POST.get('crop_name')
        variety_names = request.POST.getlist('variety_names')
        types = request.POST.getlist('crop_type')
        crop.name = crop_name
        crop.save()
        CropVariety.objects.filter(crop=crop).delete()
        for variety_name in variety_names:
            if variety_name:
                CropVariety.objects.create(crop=crop, variety_name=variety_name)
        CropType.objects.filter(crop=crop).delete()
        for type in types:
            if type:
                CropType.objects.create(crop=crop, type=type)
        return redirect('crop_management_list')

    return render(request, 'farms/edit_crop.html', {
        'crop': crop,
        'varieties': varieties,
        'types':types,
    })

def view_crop(request, crop_id):
    crop = get_object_or_404(Crop, id=crop_id)
    varieties = CropVariety.objects.filter(crop=crop).order_by("-id")  # Reverse order by ID
    types = CropType.objects.filter(crop=crop).order_by("-id")
    return render(request, 'farms/view_crop.html', {
        'crop': crop,
        'varieties': varieties,
        'types':types
    })

def delete_crop(request, crop_id):
    crop = get_object_or_404(Crop, id=crop_id)
    
    if request.method == 'POST':
        # Delete related varieties first
        varieties = CropVariety.objects.filter(crop=crop)
        for variety in varieties:
            variety.delete()
        types = CropType.objects.filter(crop=crop)
        for type in types:
            type.delete()
        # Delete the crop itself
        crop.delete()

        messages.success(request, 'Crop deleted successfully.')
        return redirect('crop_management_list')  # Redirect to crop list page after deletion

    # If not a POST request, simply redirect to the crop list page
    return redirect('crop_management_list')