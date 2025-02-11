from optparse import Values
from tkinter import Widget
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db.models import fields

from .models import Role, User, SubSuperUser
from apps.grower.models import Grower


class LoginForm(AuthenticationForm):
    """Form to login user"""
    username = forms.CharField(
        max_length=100, required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Username',
                'class': 'form-control',
            }
        )
    )
    remember_me = forms.BooleanField(required = False, label = 'Remember me')
    password = forms.CharField(
        max_length=50, required=True, widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Password',
                'class': 'form-control',
                'data-toggle': 'password',
                'id': 'password',
                'name': 'password'
            }
        )
    )
    class Meta:
        model = User
        fields = (
            'username', 'password', 'remember_me'
        )
        widgets = {
            "password": forms.PasswordInput(attrs={'placeholder':'********','autocomplete': 'off','data-toggle': 'password'}),
        }


class UserCreateForm(UserCreationForm):
    """Form to register user for a grower and to assign a role"""

    class Meta:
        model = User
        
        fields = (
            'username', 'first_name', 'last_name',
            'email', 'grower', 'role', 'password1', 'password2','is_consultant',
        )
     
#CONSULTANT_OPTIONS = [(consultant.id, consultant) for consultant in User.objects.all()]

class AccountRegistrationForm(forms.ModelForm):
    """Model form for growe model to register grower account"""

    class Meta:
        model = Grower
        fields = (
            'name', 'phone', 'email', 'physical_address1', 'physical_address2',
            'city1', 'state1', 'zip_code1', 'mailing_address1', 'mailing_address2',
            'city2', 'state2', 'zip_code2', 'consultant', 'notes'
        )
        labels = {
            'name' : 'Grower Name', 'phone' : 'Phone Number', 'email' : 'Email',
            'physical_address1': 'Physical Address Line 1', 'physical_address2' : 'Physical Address Line 2',
            'city1' : 'Physical Address City', 'state1' : 'Physical Address State',
            'zip_code1' : 'Physical Address Zip Code', 'mailing_address1': 'Mailing Address Line 1',
            'mailing_address2': 'Mailing Address Line 2', 'city2' : 'Mailing Address City',
            'state2' : 'Mailing Address State', 'zip_code2' : 'Mailing Address Zip Code',
            'consultant': 'Select Consultant', 'notes' : 'Additional Notes',
        }

        #consultant = forms.ChoiceField(choices = GEEKS_CHOICES)

        #widgets = {
           #'consultant': forms.CheckboxSelectMultiple(choices=CONSULTANT_OPTIONS)
        #}


class SuperAccountRegistrationForm(forms.ModelForm):

    # role = forms.MultipleChoiceField()

    # def __init__(self, **kwargs):
    #     super(SuperAccountRegistrationForm, self).__init__(**kwargs)
    #     self.fields['role'].queryset = Role.objects.get(role='SuperUser')
    
    class Meta:
        model = SubSuperUser
        fields = (
            'name', 'phone', 'email', 'role'
        )
        labels = {
            'name' : 'Name', 'phone' : 'Phone Number', 'email' : 'Email', 'role' : 'Role'
        }


class CreateRoleForm(forms.ModelForm):
    """Model form to create role and to assign permission for that role for a specific user"""
    
    
    class Meta:
        model = Role
        fields = ['role', 'grower', 'permissions' ]

        widgets = {
            'permissions': forms.CheckboxSelectMultiple,
        }

