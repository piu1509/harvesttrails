from django.views.generic.base import View
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.core.mail import EmailMessage
from django.db.models import Q, Sum, Count, Max
from django.contrib import messages
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import include, path

from apps.survey.models import QuestionAnswer, Survey, SurveyType, QuestionFile
from apps.questions.models import Option, Question
from apps.accounts.models import User
from apps.farms.models import Farm
from apps.field.models import Field
from apps.grower.models import Consultant, Grower
from apps.growersurvey.models import TypeSurvey, QuestionSurvey, OptionSurvey, SustainabilitySurvey, NameSurvey, Evidence
import json
from apps.growersurvey.models import InputSurvey
from django.db.models import Sum
#from .models import NameSurvey
from django.core import serializers
from urllib.parse import urlparse
import datetime
from django.db.models import Count
from django.db.models import Avg
import csv
from reportlab.pdfgen    import canvas
from reportlab.lib.utils import ImageReader

from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    #context = Context(context_dict)
    html  = template.render(context_dict)
    result = BytesIO()

    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse('We had some errors')

# Create your views here.


class GrowerSurveyView(LoginRequiredMixin, CreateView):
    '''Generic Class Based view of type survey '''
    model = TypeSurvey
    fields = "__all__"
    template_name = 'growersurvey/growers-take-survey.html'
    success_url = reverse_lazy('type-survey')

    def get_context_data(self, **kwargs):
        grower_id = Grower.objects.get(email=self.request.user.email).id
        farms_list = Farm.objects.filter(grower=grower_id)
        type_survey = TypeSurvey.objects.all()
        context = {'farms_lists': farms_list}
        # print(context)
        context['type_surveys'] = type_survey
        return context


class GrowerSurveyCreate(LoginRequiredMixin, CreateView):
    #model = TypeSurvey
    #fields = "__all__"
    #template_name = 'growersurvey/create-survey.html'
    #success_url = reverse_lazy('create-survey')

    def get(self, request):
        '''Default function for get request'''
        type_survey = TypeSurvey.objects.all()
        year_dropdown = []
        for y in range(2020, (datetime.datetime.now().year + 29)):
            year_dropdown.append(y)

        return render(request, 'growersurvey/create-survey.html', {
            'type_survey': type_survey,
            'year_dropdown': year_dropdown,
        })


class GetQuestion(LoginRequiredMixin, CreateView):

    def get(self, request):
        '''Default function for get request'''
        namesurvey_id = int(request.GET.get('namesurvey_id', 0))
        question_data = QuestionSurvey.objects.filter(
            namesurvey_id=namesurvey_id).order_by('questionorder')
        return render(request, 'growersurvey/get-question.html', {
            'question_data': question_data
        })

class CheckSurveyStatus(LoginRequiredMixin, CreateView):

    def get(self, request):
        '''Default function for get request'''
        namesurvey_id = int(request.GET.get('survey_year', 0))
        farm_id = int(request.GET.get('farm_id', 0))
        field_id = int(request.GET.get('field_id', 0))
        logged_grower_id = int(request.GET.get('logged_grower_id', 0))
        first_question_id = int(request.GET.get('first_question_id', 0))

        check_status_data = SustainabilitySurvey.objects.filter(grower_id=logged_grower_id, namesurvey_id=namesurvey_id, farm_id=farm_id, field_id=field_id)

        if check_status_data.count() > 0:
            status = check_status_data[0].status
            last_question_id = check_status_data[0].last_question_id
            if status == 'completed':
                # do something
                message = "This survey is already completed/closed by you."
                next_question = ""
            else:
                message =""
                next_question_data = QuestionSurvey.objects.filter(namesurvey_id=namesurvey_id, id__gt=last_question_id).order_by('id')[0:1]

                if next_question_data.count() > 0:
                    next_question = next_question_data[0].id
                    message =""
                else:
                    message =""
                    next_question = first_question_id
        else:
            message =""
            next_question = first_question_id


        return JsonResponse({'message': message, 'next_question': next_question})


class EditViewQuestionOptions(LoginRequiredMixin, UpdateView):

    def get(self, request):
        '''Default function for get request'''
        question_id = int(request.GET.get('question_id', 0))

        Question_Survey_data = QuestionSurvey.objects.get(id=question_id)
        Option_Survey_data = OptionSurvey.objects.filter(
            questionsurvey_id=question_id).order_by('id')
        Option_Survey_data_count = OptionSurvey.objects.filter(
            questionsurvey_id=question_id).count()

        if Option_Survey_data_count == 0:
            option_count = 1
        else:
            option_count = Option_Survey_data_count

        return render(request, 'growersurvey/get-question-options.html', {
            'Question_Survey_data': Question_Survey_data,
            'Option_Survey_data': Option_Survey_data,
            'Option_Survey_data_count': option_count
        })


class GetAllSurvey(LoginRequiredMixin, ListView):
    def get(self, request):
        '''Default function for get request'''
        survey_data = NameSurvey.objects.all().order_by('id')
        # print(survey_data)
        return render(request, 'growersurvey/survey-listing.html', {
            'survey_data': survey_data
        })


class SurveyUpdateView(LoginRequiredMixin, UpdateView):
    def get(self, request, pk):
        '''Default function for get request'''
        name_survey_data = NameSurvey.objects.get(pk=pk)

        type_survey = TypeSurvey.objects.all()
        year_dropdown = []
        for y in range(2020, (datetime.datetime.now().year + 29)):
            year_dropdown.append(y)

        return render(request, 'growersurvey/update-survey.html', {
            'type_survey': type_survey,
            'year_dropdown': year_dropdown,
            'name_survey_data': name_survey_data,
        })


def CheckSurveyDb(request):
    nmsurv_id = int(request.GET.get('nmsurv_id', 0))
    type_survey = int(request.GET.get('type_survey', 0))
    survey_year = request.GET.get('survey_year', '')

    #print(nmsurv_id)

    if nmsurv_id == 0:
        chk_survey_data = NameSurvey.objects.filter(typesurvey_id=type_survey, surveyyear=survey_year).count()
    else:
        chk_survey_data = NameSurvey.objects.exclude(id=nmsurv_id).filter(typesurvey_id=type_survey, surveyyear=survey_year).count()

    print(chk_survey_data)
    
    return HttpResponse(chk_survey_data)

def get_first_question(request):
    name_survey_id = int(request.GET.get('name_survey_id', 0))
    first_question = QuestionSurvey.objects.filter(namesurvey=name_survey_id)[0]

    return HttpResponse(first_question.id)


def SurveyDelete(request):
    namesurvey_id = int(request.POST.get('namesurvey_id', 0))
    name_survey = NameSurvey.objects.get(id=namesurvey_id)
    name_survey.delete()
    return HttpResponse(1)


def QuestionDelete(request):
    question_id = int(request.POST.get('question_id', 0))
    Question_Survey = QuestionSurvey.objects.get(id=question_id)
    Question_Survey.delete()
    return HttpResponse(1)


def SaveSurvey(request):
    data = json.loads(request.body)
    type_survey = int(data['type_survey'])
    survey_year = data['survey_year']
    survey_end_date = data['survey_end_date']
    survey_start_date = data['survey_start_date']

    namesurvey = NameSurvey(typesurvey_id=type_survey, surveyyear=survey_year,
                            start_date=survey_start_date, end_date=survey_end_date)
    namesurvey.save()

    try:
        getdata = NameSurvey.objects.filter(
            typesurvey_id=type_survey, surveyyear=survey_year).latest('id')
    except NameSurvey.DoesNotExist:
        getdata = None

    return JsonResponse({'id': getdata.id})

def SaveSurveyEdit(request):
    data = json.loads(request.body)
    nmsurv_id = int(data['nmsurv_id'])
    type_survey = int(data['type_survey'])
    survey_year = data['survey_year']
    survey_end_date = data['survey_end_date']
    survey_start_date = data['survey_start_date']

    print(nmsurv_id)

    namesurvey = NameSurvey(id=nmsurv_id,typesurvey_id=type_survey, surveyyear=survey_year,
                            start_date=survey_start_date, end_date=survey_end_date)
    namesurvey.save()

    try:
        getdata = NameSurvey.objects.filter(
            typesurvey_id=type_survey, surveyyear=survey_year).latest('id')
    except NameSurvey.DoesNotExist:
        getdata = None

    return JsonResponse({'id': getdata.id})


def save_question_option(request):
    mydata = dict(request.POST)
    question = mydata['question'][0]
    selction_type = mydata['selction_type'][0]
    max_score = int(mydata['max_score'][0])
    namesurvey_id = int(mydata['namesurvey_id'][0])
    evidence_requird = mydata.get('evidence_requird', 0)

    if evidence_requird == 0:
        evidence_requird_chk = False
        evidence_descr_chk = ""
    else:
        evidence_requird_chk = True
        evidence_descr_chk = mydata['evidence_descr'][0]

    try:
        get_max_order = QuestionSurvey.objects.filter(
            namesurvey_id=namesurvey_id).aggregate(Max('questionorder'))
        get_max_order_number = get_max_order['questionorder__max']
    except QuestionSurvey.DoesNotExist:
        get_max_order_number = None

    if get_max_order_number:
        get_next_order_to_db = get_max_order_number + 1
    else:
        get_next_order_to_db = 1

    Question_Survey = QuestionSurvey(questionname=question, namesurvey_id=namesurvey_id, questiontotalscore=max_score,
                                     questionorder=get_next_order_to_db, selection_type=selction_type, evidence_requird=evidence_requird_chk, evidence_descr=evidence_descr_chk)
    Question_Survey.save()

    inserted_question = QuestionSurvey.objects.latest('id')
    inserted_question_id = inserted_question.id

    # OptionSurvey
    option_name = mydata['option_name']
    points = mydata['points']

    for counter, opt in enumerate(option_name):
        Option_Survey = OptionSurvey(
            optionname=opt, questionsurvey_id=inserted_question_id, optionscore=points[counter])
        Option_Survey.save()

    return HttpResponse(namesurvey_id)


def SaveQuestionOptionEdit(request):
    mydata = dict(request.POST)
    question_id_edit = int(mydata['question_id_edit'][0])
    # Question_Survey = QuestionSurvey.objects.get(id=question_id_edit)
    # Question_Survey.delete()

    namesurvey_id_edit = int(mydata['namesurvey_id_edit'][0])
    question_edit = mydata['question_edit'][0]
    selction_type_edit = mydata['selction_type_edit'][0]
    max_score_edit = int(mydata['max_score_edit'][0])

    evidence_requird_edit = mydata.get('evidence_requird_edit', 0)

    if evidence_requird_edit == 0:
        evidence_requird_chk = False
        evidence_descr_chk = ""
    else:
        evidence_requird_chk = True
        evidence_descr_chk = mydata['evidence_descr_edit'][0]

    # try:
    #     get_max_order = QuestionSurvey.objects.filter(namesurvey_id=namesurvey_id_edit).aggregate(Max('questionorder'))
    #     get_max_order_number = get_max_order['questionorder__max']
    # except QuestionSurvey.DoesNotExist:
    #     get_max_order_number = None

    # if get_max_order_number:
    #     get_next_order_to_db = get_max_order_number + 1
    # else:
    #     get_next_order_to_db = 1

    get_cur_order = QuestionSurvey.objects.get(id=question_id_edit)

    Question_Survey = QuestionSurvey(id=question_id_edit, questionname=question_edit, namesurvey_id=namesurvey_id_edit, questiontotalscore=max_score_edit,
                                     questionorder=get_cur_order.questionorder, selection_type=selction_type_edit, evidence_requird=evidence_requird_chk, evidence_descr=evidence_descr_chk)
    Question_Survey.save()

    # inserted_question = QuestionSurvey.objects.latest('id')
    # inserted_question_id = inserted_question.id

    inserted_question_id = question_id_edit

    option_delete = OptionSurvey.objects.filter(
        questionsurvey_id=inserted_question_id)
    option_delete.delete()

    # OptionSurvey
    #option_id_edit = int(mydata['option_id_edit'])
    option_name_edit = mydata['option_name_edit']
    points_edit = mydata['points_edit']

    for counter, opt in enumerate(option_name_edit):
        Option_Survey = OptionSurvey(
            optionname=opt, questionsurvey_id=inserted_question_id, optionscore=points_edit[counter])
        Option_Survey.save()

    return HttpResponse(namesurvey_id_edit)


class GrowerSurveyQuestionsView(LoginRequiredMixin, CreateView):
    '''Generic Class Based view for question survey '''
    model = QuestionSurvey
    fields = "__all__"
    template_name = 'growersurvey/growers-take-survey-questions.html'
    success_url = reverse_lazy('type-questions')

    def get_context_data(self, **kwargs):
        pk = self.kwargs.get('pk')
        frmid = self.kwargs.get('frmid')
        fldid = self.kwargs.get('fldid')
        nmsrvid = self.kwargs.get('nmsrvid')

        # getting URL ID

        context = super(GrowerSurveyQuestionsView,
                        self).get_context_data(**kwargs)
        questionnewid = pk
        context["questionnewid"] = pk
        namesurvey_id = nmsrvid
        context["namesurvey_id"] = namesurvey_id
        # for survey type name

        survey_data = NameSurvey.objects.get(id=namesurvey_id)
        context["surveytypename"] = survey_data.typesurvey
        context["surveyyear"] = survey_data.surveyyear
        context["total_questions"] = QuestionSurvey.objects.filter(namesurvey=namesurvey_id).count()

        # data0 = QuestionSurvey.objects.raw(
        #     "select id,name from growersurvey_typesurvey where id=1")
        # sname_ids = [id.id for id in data0]
        # sname_names = [id.name for id in data0]
        # surveytypename = sname_names[0]
        # context["surveytypename"] = surveytypename

        # data1 = QuestionSurvey.objects.raw(
        #     "select * from growersurvey_namesurvey where typesurvey_id=%s", (sname_ids))
        # syear_ids = [id.surveyyear for id in data1]
        # surveyyear = syear_ids[0]
        # context["surveyyear"] = surveyyear

        # for question name, order and id
        # data = QuestionSurvey.objects.raw("select * from growersurvey_questionsurvey where namesurvey_id=%s and id=%s order by id ASC limit 0,1", (namesurvey_id, questionnewid))

        data = QuestionSurvey.objects.filter(id=questionnewid, namesurvey_id=namesurvey_id)[0:1]

        question_ids = [id.id for id in data]
        question_names = [id for id in data]
        
        
        options = OptionSurvey.objects.filter(
            questionsurvey_id__in=question_ids)
        context["question_names"] = question_names[0]
        context["option"] = options

        if self.request.user.is_superuser:
            context['logged_grower_id'] = ""
        elif self.request.user.is_consultant:
            context['logged_grower_id'] = ""
        else:
            context['logged_grower_id'] = Grower.objects.get(
                email=self.request.user.email).id
        # print(context['logged_grower_id'])

        # for next question ID
        # data2 = QuestionSurvey.objects.raw("select * from growersurvey_questionsurvey where namesurvey_id=%s and id>%s order by id ASC limit 0,1", (namesurvey_id, question_ids[0]))
        data2 = QuestionSurvey.objects.filter(id__gt=question_ids[0],namesurvey_id=namesurvey_id)[0:1]
        question2_ids = [id.id for id in data2]
        if(question2_ids):
            nextquestion = question2_ids[0]
            context["nextquestion"] = nextquestion
        else:
            context["nextquestion"] = ""

        context["growersurvey_farm_id"] = frmid
        context["growersurvey_feild_id"] = fldid
        growersurvey_farm_names = Farm.objects.filter(id=frmid)
        growersurvey_field_names = Field.objects.filter(id=fldid)

        context["growersurvey_farm_name"] = growersurvey_farm_names
        context["growersurvey_field_name"] = growersurvey_field_names

        return context


def InsertoptValue(request):
    # data = json.loads(request.body)
    # growerid_val = data['growerid']
    # question_id_val = data['question_id']
    # optionvalue_val = data['optionvalue']
    # namesurvey_id_val = data['namesurvey_id']
    # nextquestionid_val = data['nextquestionid']
    # growersurvey_farm_id_val = data['growersurvey_farm_id']
    # growersurvey_feild_id_val = data['growersurvey_feild_id']
    # questionspkvalue = data['questionspkvalue']
    # print(request.POST)
    #mydata = dict(request.POST)
    #print(mydata)
    evidence_requird= request.POST['evidence_requird']
    uploaded_files = request.FILES.getlist('file')
    


    


    growerid_val= request.POST['growerid']
    
    question_id_val= request.POST['question_id']
    optionvalue_val= request.POST['optionvalue']
    option_id = request.POST['option_id']

    print(option_id)

    namesurvey_id_val= request.POST['namesurvey_id']
    nextquestionid_val= request.POST['nextquestionid']
    growersurvey_farm_id_val= request.POST['growersurvey_farm_id']
    growersurvey_feild_id_val= request.POST['growersurvey_feild_id']
    questionspkvalue= request.POST['questionspkvalue']

    questionspkvalue = int(questionspkvalue)
    # print(questionspkvalue)
    status = request.POST['status']
    save_status = int(request.POST['save_status'])

    check_input_survey = InputSurvey.objects.filter(grower_id=growerid_val,namesurvey_id=namesurvey_id_val,farm_id=growersurvey_farm_id_val, field_id=growersurvey_feild_id_val, questionsurvey_id=question_id_val)

    # print(check_input_survey[0])

    if check_input_survey.count() == 0:
        inputsurvey = InputSurvey(optionscore=optionvalue_val, questionsurvey_id=question_id_val, grower_id=growerid_val, namesurvey_id=namesurvey_id_val, farm_id=growersurvey_farm_id_val, field_id=growersurvey_feild_id_val, status=status, optionscore_ids=option_id)
        inputsurvey.save()
        
    else:
        input_survey_id = check_input_survey[0].id
        inputsurvey = InputSurvey(id=input_survey_id, optionscore=optionvalue_val, questionsurvey_id=question_id_val, grower_id=growerid_val, namesurvey_id=namesurvey_id_val, farm_id=growersurvey_farm_id_val, field_id=growersurvey_feild_id_val, status=status, optionscore_ids=option_id)
        inputsurvey.save()

    del_eve_file = Evidence.objects.filter(inputsurvey_id=inputsurvey.id)
    del_eve_file.delete()


    for evd_file in uploaded_files:
        set_evd_files = Evidence(inputsurvey_id=inputsurvey.id, file=evd_file)
        set_evd_files.save()
    


    

    #opt_score_minor = InputSurvey.objects.filter(namesurvey_id=namesurvey_id_val,grower_id=growerid_val).latest('id')[:8]
    # print(opt_score_minor)
    #optionscore_val_sum = opt_score_minor.aggregate(Sum('optionscore'))
    #opscoresum = optionscore_val_sum['optionscore__sum']

    # if nextquestionid_val == "":
    #     actual_status = 'completed'
    # else:
    #     actual_status = status

    last_eight = InputSurvey.objects.filter(namesurvey_id=namesurvey_id_val, grower_id=growerid_val, farm_id=growersurvey_farm_id_val, field_id=growersurvey_feild_id_val)
    optionscore_val_sum = last_eight.aggregate(Sum('optionscore'))
    # print(len(last_eight))
    opscoresum = optionscore_val_sum['optionscore__sum']
    # print(opscoresum)

    totalscore_val_sum = QuestionSurvey.objects.filter(
        namesurvey_id=namesurvey_id_val).aggregate(Sum('questiontotalscore'))
    totalscoresum = totalscore_val_sum['questiontotalscore__sum']
    # print(totalscoresum)

    suspercentage_calc = (opscoresum/totalscoresum)*100
    suspercentage = round(suspercentage_calc, 0)

    chk_sustainabilitysurvey = SustainabilitySurvey.objects.filter(farm_id=growersurvey_farm_id_val, field_id=growersurvey_feild_id_val, grower_id=growerid_val, namesurvey_id=namesurvey_id_val)
    
    if chk_sustainabilitysurvey.count() == 0:

        sustainabilitysurvey = SustainabilitySurvey(surveyscore=opscoresum, totalscore=totalscoresum, sustainabilityscore=suspercentage, farm_id=growersurvey_farm_id_val, field_id=growersurvey_feild_id_val, grower_id=growerid_val, namesurvey_id=namesurvey_id_val, status=status, last_question_id=question_id_val)
        sustainabilitysurvey.save()

    else:
        sustainabilitysurvey_id = chk_sustainabilitysurvey[0].id
        sustainabilitysurvey = SustainabilitySurvey(id=sustainabilitysurvey_id, surveyscore=opscoresum, totalscore=totalscoresum, sustainabilityscore=suspercentage, farm_id=growersurvey_farm_id_val, field_id=growersurvey_feild_id_val, grower_id=growerid_val, namesurvey_id=namesurvey_id_val, status=status, last_question_id=question_id_val)
        sustainabilitysurvey.save()

    if save_status > 0:
        grower_data = Grower.objects.get(id=growerid_val)
        survey_type_data = NameSurvey.objects.get(id=namesurvey_id_val)
        type_survey_data = TypeSurvey.objects.get(id=survey_type_data.typesurvey_id)

        return JsonResponse({'status': True, 'grower_name': grower_data.name, 'survey_type_name': type_survey_data.name, 'survey_year': survey_type_data.surveyyear, 'suspercentage': suspercentage, 'exit_status': save_status})

    return JsonResponse({'status': True, 'exit_status': save_status})


class GrowerSurveyResultScore(LoginRequiredMixin, CreateView):
    model = SustainabilitySurvey
    fields = "__all__"
    template_name = 'growersurvey/growers-sustain-result.html'

    def get_context_data(self, **kwargs):
        context = super(GrowerSurveyResultScore,
                        self).get_context_data(**kwargs)

        if self.request.user.is_superuser:
            context['logged_grower_id'] = ""
            growerId = ""

        elif self.request.user.is_consultant:
            context['logged_grower_id'] = ""
            growerId = ""
        else:
            growerId = Grower.objects.get(email=self.request.user.email).id
            context['logged_grower_id'] = growerId
            # print(growerId)

            #"select * from growersurvey_sustainabilitysurvey where grower_id=%s", (46)
        try:
            data = SustainabilitySurvey.objects.filter(
                grower_id=growerId).latest('id')
        except SustainabilitySurvey.DoesNotExist:
            data = None

        # print(data)
        #sustaindata = [id.surveyscore for id in data]
        # surveyscorefinal=sustaindata[0]

        if(data):
            sustainabilityscorefinal = data.sustainabilityscore
            namesurvey_id = data.namesurvey_id
            # print(namesurvey_id)
            #survey_type_data = TypeSurvey.objects.get(id=namesurvey_id)
            #year_data = NameSurvey.objects.filter(typesurvey=namesurvey_id)

            survey_data = NameSurvey.objects.get(id=namesurvey_id)

            grower_data = Grower.objects.get(id=growerId)
            context["survey_year"] = survey_data.surveyyear
            context["survey_name"] = survey_data.typesurvey
            context["grower_name"] = grower_data.name
            context["sustainabilityscorefinal"] = sustainabilityscorefinal
            farmfield = SustainabilitySurvey.objects.filter(
                grower_id=growerId).latest('id')
            # print(farmfield)
            farmnamevar = farmfield.farm_id
            fieldnamevar = farmfield.field_id
            growersurvey_farm_names = Farm.objects.filter(id=farmnamevar)
            growersurvey_field_names = Field.objects.filter(id=fieldnamevar)
            context["growersurvey_farm_name"] = growersurvey_farm_names
            context["growersurvey_field_name"] = growersurvey_field_names
            context["hasdata"] = True
        else:
            context["hasdata"] = False

        return context


def SurveytypeGetyear(request):
    some_date = datetime.date.today()
    Survey_Type_ID = request.GET.get('surveyTypeid')
    name_survey = NameSurvey.objects.filter(typesurvey=Survey_Type_ID, start_date__lte=some_date, end_date__gte=some_date)
    name_survey_data = [(data.surveyyear, data.id) for data in name_survey]
    return JsonResponse({'status': True, 'data': name_survey_data})


def SurveytypeGetfarm(request):
    grower_id = Grower.objects.get(email=request.GET.get('auth_user')).id
    farm_ID = request.GET.get('farmTypeid')
    field_list = Field.objects.filter(farm=farm_ID).filter(grower=grower_id)
    field_lists = [(data.name, data.id) for data in field_list]
    # print(field_lists)
    return JsonResponse({'status': True, 'data': field_lists})

class GetAllFarm(LoginRequiredMixin, ListView):
    def get(self, request):
        '''Default function for get request'''
        grower_id = int(request.GET.get('grower_id', 0))
        farm_data = Farm.objects.filter(grower_id=grower_id)
        farm_list = [(farm.name, farm.id) for farm in farm_data]

        return JsonResponse({'farm_list': farm_list})

class GetAllField(LoginRequiredMixin, ListView):
    def get(self, request):
        '''Default function for get request'''
        farm_id = int(request.GET.get('farm_id', 0))
        field_data = Field.objects.filter(farm_id=farm_id)
        field_list = [(field.name, field.id) for field in field_data]

        return JsonResponse({'field_list': field_list})

class GrowerSustainabilty(LoginRequiredMixin, ListView):
    def get(self, request):
        '''Default function for get request'''

        # survey_year_list = NameSurvey.objects.all()

        survey_year_list = (NameSurvey.objects.values('surveyyear').annotate(dcount=Count('surveyyear')).order_by())

        survey_year_data = NameSurvey.objects.all()
        survey_type = []
        survey_score_data = []
        line_survey_grower_arr = []

        survey_current_year_data = NameSurvey.objects.filter(surveyyear=datetime.datetime.now().year)
        # print(survey_current_year_data)
        
        if 'Grower' in request.user.get_role() and not request.user.is_superuser:
            # do something grower
            
            grower_id=request.user.grower.id
            get_growers = Grower.objects.filter(id=grower_id).order_by('name')
        
            

            for name_survey in survey_year_data:
                survey_type.append(name_survey.typesurvey.name)
                sustain_data = SustainabilitySurvey.objects.filter(grower__in=get_growers,namesurvey=name_survey)

                

                

                
                
                if sustain_data.count() > 0:
                    Avg_Percentage_Score_data = sustain_data.aggregate(Avg('sustainabilityscore'))
                    Avg_Percentage_Score = int(Avg_Percentage_Score_data['sustainabilityscore__avg'])
                else:
                    Avg_Percentage_Score = 0

                survey_score_data.append(Avg_Percentage_Score)
            

            
            
        else:
            if request.user.is_consultant:
                # do something consultant
                consultant_id = Consultant.objects.get(email= request.user.email).id
                get_growers = Grower.objects.filter(consultant=consultant_id).order_by('name')

                for name_survey in survey_year_data:
                    survey_type.append(name_survey.typesurvey.name)
                    sustain_data = SustainabilitySurvey.objects.filter(grower__in=get_growers,namesurvey=name_survey)

                    if sustain_data.count() > 0:
                        Avg_Percentage_Score_data = sustain_data.aggregate(Avg('sustainabilityscore'))
                        Avg_Percentage_Score = int(Avg_Percentage_Score_data['sustainabilityscore__avg'])
                    else:
                        Avg_Percentage_Score = 0

                    survey_score_data.append(Avg_Percentage_Score)
                
            else:
                # do something allpower
                get_growers = Grower.objects.all().order_by('name')

                for name_survey in survey_year_data:
                    survey_type.append(name_survey.typesurvey.name)
                    sustain_data = SustainabilitySurvey.objects.filter(grower__in=get_growers,namesurvey=name_survey)

                    if sustain_data.count() > 0:
                        Avg_Percentage_Score_data = sustain_data.aggregate(Avg('sustainabilityscore'))
                        Avg_Percentage_Score = int(Avg_Percentage_Score_data['sustainabilityscore__avg'])
                    else:
                        Avg_Percentage_Score = 0

                    survey_score_data.append(Avg_Percentage_Score)

                    # line_survey_grower_object = sustain_data.annotate(dcount=Count('grower_id')).order_by()
                    # line_survey_grower_list = [grw_data.grower.name for grw_data in line_survey_grower_object]
                    # print(line_survey_grower_list)

        
        # survey_type.append('')
        # survey_score_data.append(0)
        



        return render(request, 'growersurvey/sustainability-dashboard.html', {
            'get_growers': get_growers,
            'survey_year_list': survey_year_list,
            'survey_type': survey_type,
            'survey_score_data': survey_score_data,
            'line_survey_grower_list': ''
        })

class GetSustainabilityResult(LoginRequiredMixin, ListView):
    def get(self, request):
        '''Default function for get request'''
        
        apply_growers = int(request.GET.get('apply_growers', 0))
        apply_farm = int(request.GET.get('apply_farm', 0))
        apply_field = int(request.GET.get('apply_field', 0))
        apply_year = int(request.GET.get('apply_year', 0))
        
        try:
            name_survey_data = NameSurvey.objects.filter(surveyyear=apply_year)
            name_survey_ids = [name_survey.id for name_survey in name_survey_data]
            type_survey_data = [name_survey_type.typesurvey for name_survey_type in name_survey_data]
        except NameSurvey.DoesNotExist:
            name_survey_ids = []
            type_survey_data = []

        try:
            sustain_data = SustainabilitySurvey.objects.filter(grower_id=apply_growers, farm_id=apply_farm, field_id=apply_field, namesurvey_id__in=name_survey_ids)
            conpleted_name_survey_ids = [comp_name_survey.namesurvey_id for comp_name_survey in sustain_data]
        except SustainabilitySurvey.DoesNotExist:
            conpleted_name_survey_ids = []

        completed_input_survey_data = InputSurvey.objects.filter(grower_id=apply_growers, farm_id=apply_farm, field_id=apply_field, namesurvey_id__in=conpleted_name_survey_ids)

        # type_survey_data = TypeSurvey.objects.all().order_by('name')

        # print(type_survey_data)
        grower_data = Grower.objects.get(id=apply_growers)
        farm_data = Farm.objects.get(id=apply_farm)
        field_data = Field.objects.get(id=apply_field)

        return render(request, 'growersurvey/get-question-answer-marks.html', {
            'completed_input_survey_data': completed_input_survey_data,
            'type_survey_data': type_survey_data,
            'grower_data': grower_data,
            'farm_data' : farm_data,
            'field_data': field_data,
            'apply_year':apply_year

        })

class GetChartResult(LoginRequiredMixin, ListView):
    def get(self, request):
        '''Default function for get request'''
        
        apply_growers = int(request.GET.get('apply_growers', 0))
        apply_farm = int(request.GET.get('apply_farm', 0))
        apply_field = int(request.GET.get('apply_field', 0))
        apply_year = int(request.GET.get('apply_year', 0))

        name_survey_data = NameSurvey.objects.filter(surveyyear=apply_year)
        name_survey_ids = [name_survey.id for name_survey in name_survey_data]
        
        sustain_data = SustainabilitySurvey.objects.filter(grower_id=apply_growers, farm_id=apply_farm, field_id=apply_field, namesurvey_id__in=name_survey_ids)

        if sustain_data.count() > 0:
            Avg_Percentage_Score_data = sustain_data.aggregate(Avg('sustainabilityscore'))
            Avg_Percentage_Score = int(Avg_Percentage_Score_data['sustainabilityscore__avg'])
        else:
            Avg_Percentage_Score = 0

        # request.session['fav_color'] = 'blue'
        # fav_color = request.session.get('fav_color', 'red')

        # print(fav_color)
            

        return render(request, 'growersurvey/set-chart-data.html', {
            'sustain_data': sustain_data,
            'Avg_Percentage_Score': Avg_Percentage_Score,
        })


# class SetChartImage(LoginRequiredMixin, ListView):
#     def get(self, request):
#         '''Default function for get request'''
#         chart_data = request.GET.get('chart_data')
#         request.session['chart_data'] = chart_data
#         # chart_data = request.session.get('chart_data', '')

#         # print(fav_color)
#         return HttpResponse(chart_data)

def SetChartImage(request):
    '''Default function for get request'''
    chart_data = request.POST.get('chart_data')
    request.session['chart_data'] = chart_data
    # chart_data = request.session.get('chart_data', '')

    # print(fav_color)
    return HttpResponse(chart_data)



class MyView(LoginRequiredMixin, ListView):
    def get(self, request, **kwargs):
        
        apply_growers = int(self.kwargs.get('apply_growers', 0))
        apply_farm = int(self.kwargs.get('apply_farm', 0))
        apply_field = int(self.kwargs.get('apply_field', 0))
        apply_year = int(self.kwargs.get('apply_year', 0))

        grower_data = Grower.objects.get(id=apply_growers)
        some_date = datetime.date.today()

        print(grower_data)
        print(some_date)
        
        
        #Retrieve data or whatever you need table data
        try:
            name_survey_data = NameSurvey.objects.filter(surveyyear=apply_year)
            name_survey_ids = [name_survey.id for name_survey in name_survey_data]
            type_survey_data = [name_survey_type.typesurvey for name_survey_type in name_survey_data]
        except NameSurvey.DoesNotExist:
            name_survey_ids = []
            type_survey_data = []

        try:
            sustain_data = SustainabilitySurvey.objects.filter(grower_id=apply_growers, farm_id=apply_farm, field_id=apply_field, namesurvey_id__in=name_survey_ids)
            conpleted_name_survey_ids = [comp_name_survey.namesurvey_id for comp_name_survey in sustain_data]
        except SustainabilitySurvey.DoesNotExist:
            conpleted_name_survey_ids = []

        completed_input_survey_data = InputSurvey.objects.filter(grower_id=apply_growers, farm_id=apply_farm, field_id=apply_field, namesurvey_id__in=conpleted_name_survey_ids)


        
        #Retrieve data or whatever you need table data end

        #Retrieve data or whatever you need chart data start

        name_survey_data_chart = NameSurvey.objects.filter(surveyyear=apply_year)
        name_survey_ids_chart = [name_survey.id for name_survey in name_survey_data_chart]
        
        sustain_data_chart = SustainabilitySurvey.objects.filter(grower_id=apply_growers, farm_id=apply_farm, field_id=apply_field, namesurvey_id__in=name_survey_ids_chart)

        if sustain_data_chart.count() > 0:
            Avg_Percentage_Score_data_chart = sustain_data_chart.aggregate(Avg('sustainabilityscore'))
            Avg_Percentage_Score_chart = int(Avg_Percentage_Score_data_chart['sustainabilityscore__avg'])
        else:
            Avg_Percentage_Score_chart = 0

        #Retrieve data or whatever you need chart data end
        chart_data = request.session.get('chart_data', '')
        
        # return render(request,
        #         'growersurvey/mytemplate.html',
        #         {
        #             'pagesize':'A4',
        #             'sustain_data': sustain_data_chart,
        #             'Avg_Percentage_Score': Avg_Percentage_Score_chart,
        #             'completed_input_survey_data': completed_input_survey_data,
        #             'type_survey_data': type_survey_data,
        #             'chart_data': chart_data,
        #         }
        #     )

        

        return render_to_pdf(
                'growersurvey/mytemplate.html',
                {
                    'pagesize':'A4',
                    'sustain_data': sustain_data_chart,
                    'Avg_Percentage_Score': Avg_Percentage_Score_chart,
                    'completed_input_survey_data': completed_input_survey_data,
                    'type_survey_data': type_survey_data,
                    'chart_data': chart_data,
                    'grower_data': grower_data,
                    'some_date': some_date,
                }
            )

def pdf_dw(request):                                  

    # Create the HttpResponse object 
    response = HttpResponse(content_type='application/pdf') 

    # This line force a download
    response['Content-Disposition'] = 'attachment; filename="1.pdf"' 

    # READ Optional GET param
    get_param = request.GET.get('name', 'World')

    # Generate unique timestamp
    # ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')

    p = canvas.Canvas(response)

    # Write content on the PDF 
    p.drawString(100, 500, "Hello " + get_param + " (Dynamic PDF) - " ) 

    # Close the PDF object. 
    p.showPage() 
    p.save() 

    # Show the result to the user    
    return response

class GrowerSustainComparison(LoginRequiredMixin, ListView):
    def get(self, request):
        type_survey_data = TypeSurvey.objects.all().order_by('name')
        if 'Grower' in request.user.get_role() and not request.user.is_superuser:
            # do something grower
            grower_id=request.user.grower.id
            grower_obj = Grower.objects.filter(id=grower_id).order_by('name')
            
        else:
            if request.user.is_consultant:
                # do something consultant
                consultant_id = Consultant.objects.get(email= request.user.email).id
                grower_obj = Grower.objects.filter(consultant=consultant_id).order_by('name')
                
            else:
                # do something allpower
                grower_obj = Grower.objects.all().order_by('name')

        comparison_arr = []
        for grower in grower_obj:
            grower_name = grower.name
            try:
                sustain_obj = SustainabilitySurvey.objects.filter(grower=grower)
            except SustainabilitySurvey.DoesNotExist:
                sustain_obj = None
            if sustain_obj:
                for sustain in sustain_obj:
                    
                    if sustain.field.farm.state:
                        state = sustain.field.farm.state
                    else:
                        state = '-'

                    if sustain.field.farm.town:
                        city = sustain.field.farm.town
                    else:
                        city = '-'

                    sustain_res = {
                        'grower_name' : sustain.grower.name,
                        'survey_type' : sustain.namesurvey.typesurvey.name,
                        'grower_score' : sustain.sustainabilityscore,
                        'grower_farm': sustain.farm.name,
                        'grower_field': sustain.field.name,
                        'survey_year': sustain.namesurvey.surveyyear,
                        'acres': sustain.field.acreage,
                        'grower_id': sustain.grower.id,
                        'name_survey_type_id': sustain.namesurvey.typesurvey.id,
                        'farm_id': sustain.farm.id,
                        'field_id': sustain.field.id,
                        'crop': sustain.field.crop,
                        'state': state,
                        'city': city
                    }

                    comparison_arr.append(sustain_res)  
            else:
                sustain_res = {
                        'grower_name' : grower_name,
                        'survey_type' : '-',
                        'grower_score' : '-',
                        'grower_farm': '-',
                        'grower_field': '-',
                        'survey_year': '-',
                        'acres': '-',
                        'grower_id': grower.id,
                        'name_survey_type_id': '',
                        'farm_id': '',
                        'field_id': '',
                        'crop': '-',
                        'state': '-',
                        'city': '-'

                    }

                comparison_arr.append(sustain_res)

        # print(comparison_arr)

        return render(request, 'growersurvey/grower_comparison.html', {
                    'comparison_arr':comparison_arr,
                    'grower_obj':grower_obj,
                    'type_survey_data':type_survey_data,
                })
        
        


