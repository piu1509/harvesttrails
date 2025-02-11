'''Views Classes and Functions for gallery'''
# pylint: disable=no-member, no-self-use, anomalous-backslash-in-string
import re
from django.http.response import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.views import View
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from main.settings import DEFAULT_FROM_EMAIL, MEDIA_URL

# from apps.survey.models import SurveyType
from apps.gallery.models import Document, Gallery
from apps.grower.models import Grower
from apps.farms.models import Farm
from apps.field.models import Field
from apps.survey.models import SurveyType


from .forms import GalleryForm, FileForm

def email_id_validation(email=None):
    '''Function for Email ID validation
    This function fill accept string as parameter
    where string will be comma separated multiple email IDs'''

    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if isinstance(email, str):
        email_list = email.replace(" ", "").split(",")
        valid_emails = []
        for email_id in email_list:
            if (re.search(regex, email_id)):
                valid_emails.append(email_id)
        return valid_emails
    return []

class GalleryCreateView(LoginRequiredMixin,CreateView):
    '''For uploading files in Gallery'''

    form_class = GalleryForm
    template_name = 'gallery/upload.html'
    success_url = reverse_lazy('gallery')


    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context ['file_form'] = FileForm
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        gallery = Gallery.objects.get(id=self.object.pk)

        files = self.request.FILES.getlist('file')

        for file in files:
            doc = Document.objects.create(gallery=gallery, file=file)
            doc.save()
        messages.success(self.request, f'File(s) Uploaded Successfully!')
        return response


class GalleryView(LoginRequiredMixin,View):
    """ View for Gallery """

    def get(self, request):
        '''Default function for get request'''

        try:

            grower_list = Grower.objects.all()

            if request.user.is_superuser :
                selected_grower = Grower.objects.first()


            elif request.user.is_anonymous:
                return render(request, "gallery/missing_details.html")

            else:
                selected_grower = Grower.objects.get(pk = request.user.grower.pk)

        except:
            return render(request, "gallery/missing_details.html")

        # To get farm data
        farm_list = Farm.objects.filter(grower_id=selected_grower.pk)
        selected_farm_list = list(farm_list.values_list('id',flat=True))

        # To get Field data
        field_list = Field.objects.filter(grower_id=selected_grower.pk)
        selected_field_list = list(field_list.values_list('id',flat=True))

        # # To get SurveyType data
        survey_type_list = SurveyType.objects.all()
        survey_type_list = SurveyType.objects.all()
        selected_survey_type = list(SurveyType.objects.values_list('id',flat=True))

        #To get year data
        selected_year_list = year_list = list(Gallery.objects.values_list('year', flat=True).distinct())


        return render(request, 'gallery/gallery.html', {"grower_list": grower_list,
            'farm_list': farm_list, 'field_list': field_list, 'survey_type_list': survey_type_list,
            'selected_grower': selected_grower, 'year_list' : year_list,
            'selected_survey_type' : selected_survey_type,
            'selected_farm_list':selected_farm_list,
            'selected_field_list':selected_field_list,
            'selected_year_list' : selected_year_list})

    def post(self, request):
        '''Default function for post request'''


        try:
            if request.user.is_superuser :
                grower_list = Grower.objects.all()
                selected_grower = int(request.POST.get('grower'))

            elif request.user.is_anonymous:
                return render(request, "gallery/missing_details.html")
            else:
                selected_grower = int(request.POST.get('grower',request.user.grower.pk))
                grower_list = Grower.objects.filter(pk=selected_grower)
        except:
            return render(request, "gallery/missing_details.html")

        grower_id = request.POST.get('grower')
        if grower_id is None:
            grower_id = request.user.grower.pk

        farm_name = request.POST.getlist('farm')
        selected_farm_list = [int(item) for item in farm_name]
        field_name = request.POST.getlist('field')
        selected_field_list = [int(item) for item in field_name]
        survey_type_list = SurveyType.objects.all()
        selected_survey_type = request.POST.getlist('survey_type')
        selected_survey_type = [int(item) for item in selected_survey_type]
        year = request.POST.getlist('year')
        display = request.POST['btn']

        # To get farm data
        farm_list = Farm.objects.filter(grower_id=selected_grower)


        # To get Field data
        field_list = Field.objects.filter(grower_id=selected_grower)

        ##field_list = list(Field.objects.values_list('name', flat=True))

        # # To get SurveyType data
        survey_type_list = SurveyType.objects.all()

        #To get year data
        selected_year_list = [int(item) for item in year]
        year_list = list(Gallery.objects.values_list('year', flat=True).distinct())


        #object_list = Gallery.objects.all().order_by('-id')
        docs = Document.objects.filter(gallery__grower_id=selected_grower)

        if selected_farm_list == [] or selected_field_list == [] or selected_survey_type == [] \
            or selected_year_list == []:
            return render(request, 'gallery/gallery.html', {'display': display,
            "grower_list": grower_list,
            'farm_list': farm_list, 'field_list': field_list, 'survey_type_list': survey_type_list,
            'selected_grower': selected_grower, 'year_list':year_list,
            'selected_survey_type' : selected_survey_type,
            'selected_farm_list': selected_farm_list,
            'selected_field_list': selected_field_list,
            'selected_year_list' : selected_year_list})

        if selected_farm_list != []:
            docs = docs.filter(gallery__farm_id__in=selected_farm_list)

        if selected_field_list != []:
            docs = docs.filter(gallery__field_id__in=selected_field_list)

        if selected_survey_type != []:
            docs = docs.filter(gallery__survey_type__in=selected_survey_type)

        if selected_year_list != []:
            docs = docs.filter(gallery__year__in=selected_year_list)
        media_url = MEDIA_URL
        if display == 'photos':
            docs = docs.filter(is_image=True)
        elif display == 'files':
            docs = docs.filter(is_image=False)

        return render(request, 'gallery/gallery.html', {'display': display,
            'object_list': docs, "media_url": media_url, "grower_list": grower_list,
            'farm_list': farm_list, 'field_list': field_list, 'survey_type_list': survey_type_list,
            'selected_grower': selected_grower, 'year_list':year_list,
            'selected_survey_type' : selected_survey_type,
            'selected_farm_list': selected_farm_list,
            'selected_field_list': selected_field_list,
            'selected_year_list' : selected_year_list})


class EmailSender(LoginRequiredMixin,View):
    """For sending email from Document and Photos gallery"""

    def get(self, request):
        '''For sending an email on post request'''
        uid = request.GET.get('id')
        to_email = request.GET.get('emailid')
        to_email = email_id_validation(to_email)
        print(uid,to_email)
        if len(to_email) == 0:
            return HttpResponse(0)
        remark = request.GET.get('remark')

        if len(remark) == 0:
            remark = "None"
        obj = Document.objects.get(pk=uid)
        file_name = str(obj.file.path)


        email_body = render_to_string(
            'gallery/single_file_mail.html', {'obj': obj, 'remark': remark})

        for email in to_email:
            msg = EmailMessage(file_name.rsplit(
                '/',maxsplit=1)[-1].upper(), email_body, DEFAULT_FROM_EMAIL, [email])
            msg.content_subtype = "html"
            msg.attach_file(file_name)

        try:
            msg.send(fail_silently=True)
            return HttpResponse(1)
        except:
            return HttpResponse(0)


class MultiEmailSender(LoginRequiredMixin,View):
    '''For sending email to multiple email ids at once'''

    def get(self, request):

        '''Function for sending email'''

        ids = request.GET.get('id').split(",")

        remark = request.GET.get('remark')
        if len(remark) == 0:
            remark = 'None'

        email_list = email_id_validation(request.GET.get('emailid'))
        print("multil email sender get ",ids,remark,email_list)
        if len(email_list) == 0:

            return HttpResponse(0)

        list_objects = []
        for item in ids:
            obj = Document.objects.get(pk=int(item))
            list_objects.append(obj)

        grower_name = obj.gallery.grower.name

        file_name = []
        for item in list_objects:
            file_name.append(str(item.file.path))


        html_message = render_to_string('gallery/multi_file_mail.html',
            {'list_objects': list_objects,
            'grower_name': grower_name,
            'remark': remark})
        for email in email_list:
            msg = EmailMessage("Download Files : "+str(grower_name),
                               html_message, DEFAULT_FROM_EMAIL, [email])
            msg.content_subtype = "html"
            for file in file_name:
                msg.attach_file(file)
            msg.send(fail_silently=True)

        return HttpResponse(1)



class GrowerDetails(LoginRequiredMixin,View):
    '''For serving grower details in Gallery Uploadfor JS function'''

    def get(self, request):
        '''For dynamically populating dropdown list in upload view'''

        grower_id = int(request.GET.get('growerid'))

        farm_id = list(Farm.objects.filter(
            grower_id=grower_id).values_list('pk', flat=True))
        farm_names = list(Farm.objects.filter(
            grower_id=grower_id).values_list('name', flat=True))
        field_id = list(Field.objects.filter(
            grower_id=grower_id).values_list('pk', flat=True))
        field_names = list(Field.objects.filter(
            grower_id=grower_id).values_list('name', flat=True))
        return JsonResponse(data={
            'farm_id': farm_id,
            'farm': farm_names,
            'field_id': field_id,
            'field': field_names,
        })

