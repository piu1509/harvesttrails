"""classes and functions for survey app"""

from datetime import datetime
from zipfile import ZipFile
import os
import pandas as pd

from django.views.generic.base import View
from django.template.loader import render_to_string
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.core.mail import EmailMessage
from django.db.models import Q, Sum, Count
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from main.settings import DEFAULT_FROM_EMAIL
from main.settings import MEDIA_ROOT, MEDIA_URL
from main.settings import DEFAULT_FROM_EMAIL

from apps.survey.models import QuestionAnswer, Survey, SurveyType, QuestionFile
from apps.questions.models import Option, Question
from apps.accounts.models import User
#pylint: disable=no-member, no-self-use, too-many-ancestors, bare-except, too-many-locals
from apps.grower.models import Grower
from apps.questions.models import QUESTION_CATEGORIES

class LoadFarms(LoginRequiredMixin,View):
    """For loading farm select dropdown in /survey/sustainability/
    Args:
        LoginRequiredMixin : For login required functionality
        View [View Class]: Generic base class view
    """

    def get(self,request):
        """Function for get request"""

        grower_id = request.GET.get('grower_id')
        obj = QuestionAnswer.objects.filter(survey__grower_id=grower_id).\
            values_list('survey__farm__id','survey__farm__name',flat=False).\
                distinct().order_by('survey__farm__name')
        return render(request, 'survey/load_farms.html', {'objs': obj})


class LoadFields(LoginRequiredMixin,View):
    """For loading Fields select dropdown in /survey/sustainability/

    Args:
        LoginRequiredMixin : For login required functionality
        View [View Class]: Generic base class view
    """
    def get(self,request):
        """Function for get request"""

        grower_id = request.GET.get('grower_id')
        farm_id = request.GET.get('farm_id')
        obj = QuestionAnswer.objects.filter(Q (survey__grower_id=grower_id) & \
            Q(survey__farm_id=farm_id)).\
                values_list('survey__field__id','survey__field__name',flat=False).\
                    distinct().order_by('survey__field__name')
        return render(request, 'survey/load_fields.html', {'objs': obj})


class LoadYears(LoginRequiredMixin,View):
    """For loading years select dropdown in /survey/sustainability/
    Args:
        LoginRequiredMixin : For login required functionality
        View [View Class]: Generic base class view
    """
    def get(self,request):
        """Function for get request"""

        grower_id = request.GET.get('grower_id')
        farm_id = request.GET.get('farm_id')
        field_id = request.GET.get('field_id')
        obj = QuestionAnswer.objects.filter(Q (survey__grower_id=grower_id) & \
            Q(survey__farm_id=farm_id) & Q(survey__field_id=field_id)).\
                values_list('survey__year',flat=False).\
                    distinct().order_by('-survey__year')
        return render(request, 'survey/load_years.html', {'objs': obj})


class LoadPopup(LoginRequiredMixin,View):
    """For loading content in popup /survey/sustainability/
        Args:
        LoginRequiredMixin : For login required functionality
        View [View Class]: Generic base class view
    """
    def get(self,request):
        """Function for get request"""

        pk = request.GET.get('pk')
        obj = QuestionFile.objects.filter(question_answer=pk)
        doc_list = []
        for item in obj:
            doc_list.append(item.file.name)
        if len(doc_list)==1:
            download_link = os.path.join(MEDIA_URL,doc_list[0])
        else:
            #Creating download.zip of all files
            os.chdir(MEDIA_ROOT)
            zip_file_name = 'download_' + str(request.user.pk) + '.zip'
            zip_file_path = os.path.join(MEDIA_ROOT,zip_file_name)
            with ZipFile(zip_file_path, 'w') as zipObj:
                for item in doc_list:
                    zipObj.write(item)
            download_link = os.path.join(MEDIA_URL,zip_file_name)
        ansObj = QuestionAnswer.objects.filter(pk=pk)
        return render(request, 'survey/load_popup.html', {'objs': obj, 'doc_count' : len(obj), 'ansObj':ansObj,
            'download_link': download_link})


class GetSurveyScoreType(LoginRequiredMixin,View):
    """For survey score calculation
    Args:
        LoginRequiredMixin : For login required functionality
        View [View Class]: Generic base class view
    """
    def get(self,request):
        """Function will get GET request from AJAX call
        and will return final Score or Provisional Score"""

        grower_id = request.GET.get('grower_id')
        farm_id = request.GET.get('farm_id')
        field_id = request.GET.get('field_id')
        year = request.GET.get('year')
        if not all([int(grower_id),int(farm_id),int(field_id),int(year)]):
            return HttpResponse ('')

        questions = QuestionAnswer.objects.filter(
                    Q(survey__grower_id=grower_id) &
                    Q(survey__farm_id=farm_id) &
                    Q(survey__field_id=field_id) &
                    Q(survey__year=year))#.order_by('question__order')

        questions = questions.annotate(farmer_points=Sum('option_chosen__points'))
        questions = questions.annotate(max_points=Sum('question__max_points'))
        questions = questions.annotate(doc_count=Count('files'))

        total_score = questions.aggregate(sum=Sum('farmer_points'))['sum'] / \
            questions.aggregate(sum=Sum('max_points'))['sum'] *100
        total_score = round(total_score,2)
        total_score = round(total_score,2)
        #Creating pandas dataframe from queryset
        answers_df = pd.DataFrame(columns=["Grower","Farm","Field","Survey type",\
                "Question","Answers","Year","Farmer Points","Max Points","Score"])
        for i in questions:
            ans = ""
            for j in i.option_chosen.all():
                ans = ans + str(j) +"\n"
            new_row = {"Grower": i.survey.grower.name,
                "Farm": i.survey.farm.name,
                "Field": i.survey.field.name,
                "Survey type": i.survey.survey_type,
                "Question": i.question,
                "Answers" : ans,
                "Year": i.survey.year,
                "Farmer Points":i.farmer_points,
                "Max Points":i.max_points,
                "Score" : total_score
                }
            answers_df = answers_df.append(new_row, ignore_index=True)
            excel_file = os.path.join(MEDIA_ROOT, 'Survey Data_' + str(request.user.pk) +'.xlsx')
            print('excel_file ',excel_file)
            answers_df.to_excel(excel_file, index=None)

        survey_obj = Survey.objects.filter(Q(grower_id=grower_id) &
                    Q(farm_id=farm_id) &
                    Q(field_id=field_id) &
                    Q(year=year))
        if survey_obj[0].is_accepted:
            return HttpResponse (f'Final Score : {total_score}%')
        return HttpResponse (f'Provisional Score : {total_score}%')


def getSurveyScore(grower_id,farm_id,field_id,year):
    """[For survey score calculation

    Args:
        grower_id (str): grower id
        farm_id (str): farm id
        field_id (str): field id
        year (str):  year

    Returns:
        survey_types - list of string
        new_score : list of score
    """
    survey_types = ['Entry SmartRice Survey',
        'Complete SmartRice Survey',
        'Sales SmartRice Survey']
    # survey_types = ['entry_smartrice_survey',
    #     'complete_smartrice_survey',
    #     'sales_smartrice_survey']

    if not all([int(grower_id),int(farm_id),int(field_id),int(year)]):
        return survey_types, [0,0,0]

    questions = QuestionAnswer.objects.filter(
                    Q(survey__grower_id=grower_id) &
                    Q(survey__farm_id=farm_id) &
                    Q(survey__field_id=field_id) &
                    Q(survey__year=year))


    questions = questions.annotate(farmer_points=Sum('option_chosen__points'))
    questions = questions.annotate(max_points=Sum('question__max_points'))
    questions = questions.annotate(doc_count=Count('files'))

    total_score = questions.aggregate(sum=Sum('farmer_points'))['sum'] / \
        questions.aggregate(sum=Sum('max_points'))['sum'] *100

    survey_score = []

    for survey_type in survey_types:
        s_questions = questions.filter(survey__survey_type__name=survey_type)
        s_farmer_points_sum = s_questions.aggregate(sum=Sum('farmer_points'))['sum']
        s_max_points_sum = s_questions.aggregate(sum=Sum('max_points'))['sum']
        if s_farmer_points_sum is not None or s_max_points_sum is not None:
            score = (s_farmer_points_sum / s_max_points_sum) * 100
            survey_score.append(score)
        else:
            survey_score.append(0.0)
    new_score = []
    for sur in survey_score:
        try:
            temp = sur / sum(survey_score) *100
            temp = round(total_score*temp/100,2)
            new_score.append(temp)
        except ZeroDivisionError:
            new_score.append(0)
    survey_types = ['Entry SmartRice Survey',
        'Complete SmartRice Survey',
        'Sales SmartRice Survey']
    return survey_types,new_score


class GetSurveyData(LoginRequiredMixin,View):
    """Function for rendering HTML template
    Response on get request from /js/customSurvey.js

    Args:
        LoginRequiredMixin : For login required functionality
        View [View Class]: Generic base class view
    """
    def get(self,request):
        """Default function for get request"""

        grower_id = request.GET.get('grower_id')
        farm_id = request.GET.get('farm_id')
        field_id = request.GET.get('field_id')
        year = request.GET.get('year')
        survey_types, score = getSurveyScore(grower_id,farm_id,field_id,year)
        return render(request, 'survey/survey_data.html',
            {'score' : score,'survey_types' : survey_types})


class SurveyListView(LoginRequiredMixin, ListView):
    """Generic Class based view to list all survey with questions"""
    model = Question
    template_name = 'survey/survey.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ques_categories'] = [category[1] for category in QUESTION_CATEGORIES]

        if self.request.GET.get('questionType_id'):
            questionType_id = self.request.GET.get('questionType_id')
            context['questions'] = Question.objects.filter(category=questionType_id)
        else: context['questions'] = Question.objects.all()

        return context


class OptionCreateView(LoginRequiredMixin, CreateView):
    """Generic Class based view to create option"""
    model = Option
    fields = "__all__"
    queryset = Option.objects.filter(is_active=True)
    template_name = 'survey/option_create.html'
    success_url = reverse_lazy('survey')

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new farm"""
        order = form.cleaned_data.get('order')
        text = form.cleaned_data.get('text')
        messages.success(self.request, f'Option ({order}): {text} Created Successfully!')
        return super().form_valid(form)


class OptionUpdateView(LoginRequiredMixin, UpdateView):
    """Generic Class Based view to update option created"""
    model = Option
    fields = ('question', 'order', 'text', 'points', )
    template_name = 'survey/option_update.html'
    success_url = reverse_lazy('survey')

    def form_valid(self, form):
        """overriding this method to get a message after successfully creating new farm"""
        order = form.cleaned_data.get('order')
        messages.success(self.request, f'Option ({order}) Updated Successfully!')
        return super().form_valid(form)


class SurveyRejectNotification(LoginRequiredMixin,View):
    '''For sending email notification on survey rejection
    Args:
        LoginRequiredMixin : For login required functionality
        View [View Class]: Generic base class view'''

    def get(self,request):
        '''Default function for GET request'''

        grower_id = request.GET.get('id')
        remark = request.GET.get('remark')
        grower_email = Grower.objects.get(pk=grower_id).email
        mail_template = 'survey/survey_reject_mail_notification.html'
        html_message = render_to_string(mail_template,{'remark': remark})

        msg = EmailMessage("Survey Rejected", html_message, DEFAULT_FROM_EMAIL, [grower_email])

        msg.content_subtype = "html"

        try:
            msg.send(fail_silently=False)
            return HttpResponse(1)
        except:
            return HttpResponse(0)

# Survey approve and reject will be from mobile end
# so we have disabled this code, it may required in fucture
# class SurveyStatusUpdate(LoginRequiredMixin,View):
#     """View for updating survey status when approved'''
#     Args:
#         LoginRequiredMixin : For login required functionality
#         View [View Class]: Generic base class view"""

#     def get(self,request):
#         '''Default function for get request'''

#         grower_id = request.GET.get('grower_id',None)
#         year = request.GET.get('year',None)
#         farm_id = request.GET.get('farm_id',None)
#         field_id = request.GET.get('field_id',None)
#         try:
#             survey_info = SurveyInfo.objects.get(grower_id=grower_id,
#                 farm_id=farm_id,field_id=field_id,year=year)
#             survey_info.approve_status = True
#             survey_info.approved_date = datetime.now()
#             survey_info.save()
#             #surveyApprovedMail(grower_id=id,year=year)
#             obj = Grower.objects.get(pk=grower_id)
#             grower_email = obj.email
#             grower_name = obj.name

#             mail_template = 'survey/survey_approved_notification.html'
#             html_message = render_to_string(mail_template,{'grower_name': grower_name,
#                 'year' : year, 'obj': survey_info })

#             msg = EmailMessage("Survey Approved", html_message, DEFAULT_FROM_EMAIL, [grower_email])

#             msg.content_subtype = "html"

#             msg.send(fail_silently=False)
#             return HttpResponse(1)
#         except:
#             return HttpResponse(0)


class SustainabilityListView(LoginRequiredMixin, View):
    """returns all farms for superuser and farms mapped to grower for other users
    Args:
        LoginRequiredMixin : For login required functionality
        View [View Class]: Generic base class view"""

    def get(self,request):
        """filter farms as per grower selected in dropdown"""
        template_name = 'survey/sustainability.html'

        if len(QuestionAnswer.objects.all())<1:
            return render (request,'survey/missing_details.html')


        isConsultant = False
        for role in User.objects.get(username=request.user).role.all():
            if str(role) == 'Consultant':
                isConsultant = True
                break

        if isConsultant:
            email_id = request.user.email
            linked_grower= []
            for _grower in Grower.objects.all():
                for _cons in _grower.consultant.all():
                    if email_id in _cons.email:
                        linked_grower.append((_grower.pk,_grower.name))
            survey_list = QuestionAnswer.objects.values_list('survey__grower__id','survey__grower__name', flat=False).distinct()
            growers = []
            for _linked in linked_grower:
                if _linked in survey_list:
                    growers.append(_linked)
            if len(growers)<1:
                return render (request,'survey/missing_details.html')
        #If user in not linked with any grower
        elif request.user.is_superuser :
            linked_grower= []
            for _grower in Grower.objects.all():
                linked_grower.append((_grower.pk,_grower.name))
            survey_list = QuestionAnswer.objects.values_list('survey__grower__id','survey__grower__name', flat=False).distinct()
            growers = []
            for _linked in linked_grower:
                if _linked in survey_list:
                    growers.append(_linked)
            if len(growers)<1:
                return render (request,'survey/missing_details.html')
            excel_file_path = os.path.join(MEDIA_URL, 'Survey Data_' +str(request.user.pk) +'.xlsx')
            return render(request,template_name,{'excel_file_path':excel_file_path,
            'growers':growers,'isConsultant':True})
        else:
            try:
                if request.user.grower is None:
                    return render (request,'survey/missing_details.html')
                #If user is linked with a grower
                growers = QuestionAnswer.objects.filter(survey__grower_id=request.user.grower_id).values_list(\
                    'survey__grower_id','survey__grower__name', flat=False).distinct()
                #If there is no survey data
                if len(growers) <1:
                    return render (request,'survey/missing_details.html')

            except AttributeError:
                return render (request,'survey/missing_details.html')

        excel_file_path = os.path.join(MEDIA_URL, 'Survey Data.xlsx')
        return render(request,template_name,{'excel_file_path':excel_file_path,
            'growers':growers,'isConsultant':isConsultant})


class LoadQuestions(LoginRequiredMixin,View):
    """For dynamically loading questions"""
    def get(self,request):
        """For dynamically loading questions
        It will return HTML code to JavaScript function in response
        Args:
                LoginRequiredMixin : For login required functionality
                View [View Class]: Generic base class view"""
        grower_id = request.GET.get('grower_id')
        farm_id = request.GET.get('farm_id')
        field_id = request.GET.get('field_id')
        year = request.GET.get('year')

        if not all([int(grower_id),int(farm_id),int(field_id),int(year)]):
            return render (request, 'survey/load_questions_no_record.html')

        questions = QuestionAnswer.objects.filter(
                            Q(survey__grower_id=grower_id) &
                            Q(survey__farm_id=farm_id) &
                            Q(survey__field_id=field_id) &
                            Q(survey__year=year))

        questions = questions.annotate(farmer_points=Sum('option_chosen__points'))
        questions = questions.annotate(max_points=Sum('question__max_points'))
        for item in questions:
            item.doc_count = item.files.all().count()
        return render (request, 'survey/load_questions.html',{'questions' : questions})


def surveyChartData(request):
    '''Most savings across by region customchart.js
    Created for JS get request '''

    grower_id = request.GET.get('grower_id')
    farm_id = request.GET.get('farm_id')
    field_id = request.GET.get('field_id')
    year = request.GET.get('year')

    survey_types, score = getSurveyScore(grower_id,farm_id,field_id,year)
    return JsonResponse(data={
        'label': survey_types,
        'data': score})
