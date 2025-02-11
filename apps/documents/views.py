from django.shortcuts import render
from django.views.generic.base import View
from django.template.loader import render_to_string
from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.documents.models import DocumentFolder, DocumentFile
from apps.accounts.models import User
from django.db import IntegrityError
from apps.grower.models import Grower, Consultant
from apps.growersurvey.models import TypeSurvey
from django.contrib import messages
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import datetime
from apps.field.models import Field
import csv
from apps.field.models import SustainabilitySurvey
from django.contrib.auth.decorators import login_required
# Create your views here.

# Test Code ..................

@login_required()
def reports_csv_all(request):
    # Create the HttpResponse object with the appropriate CSV header.
    filename = 'Reports.csv'
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
    )
    field_all = Field.objects.all().order_by('-created_date')
 
    writer = csv.writer(response)
    writer.writerow(['GROWER', 'FARM', 'FIELD', 'CROP','CONTRACT RCVD','Consultant','FSA','SURVEY 1','SURVEY 2','SURVEY 3','SURVEY COMPOSITE SCORE','ACREAGE','FIELD ESCHLON ID','FIELD SHAPE FILES','STORAGE SHAPE FILES','TISSUE 1','TISSUE 2','TISSUE 3','WATER','SOIL'])
    grower = []
    farm = []
    field = []
    crop= []
    contract = []
    consultant_name= []
    fsa = []
    survey1 = []
    survey2 = []
    survey3 = []
    composite = []
    acreage = []
    eschlon = []
    storage_shapefile_name = []
    field_shapefile_name = []
    tissue_1 = []
    tissue_2 = []
    tissue_3 = []
    water = []
    soil = []
    for i in range(len(field_all)):
        grower_name = field_all[i].grower.name
        grower.append(grower_name)
        farm_name = field_all[i].farm.name
        farm.append(farm_name)
        field_name = field_all[i].name
        field.append(field_name)
        crop_name = field_all[i].crop
        crop.append(crop_name)

        get_c = field_all[i].get_contract()
        contract.append(get_c)

        get_consultant = field_all[i].get_consultant_name()
        consultant_name.append(get_consultant)
        
        fsa_field= field_all[i].fsa_field_number
        fsa.append(fsa_field)
       
        get_survey1 = field_all[i].get_survey1()
        if get_survey1 == "":
            get_survey1 = 0
        elif int(get_survey1) > 100:
            get_survey1 = 100
        else:
            get_survey1 = get_survey1
        survey1.append(get_survey1)

        get_survey2 = field_all[i].get_survey2()
        if get_survey2 == "":
            get_survey2 = 0
        elif int(get_survey2) > 100:
            get_survey2 = 100
        else:
            get_survey2 = get_survey2
        survey2.append(get_survey2)

        get_survey3 = field_all[i].get_survey3()
        if get_survey3 == "":
            get_survey3 = 0
        elif int(get_survey3) > 100:
            get_survey3 = 100
        else:
            get_survey3 = get_survey3
        survey3.append(get_survey3)
        
        composite_score = field_all[i].get_composite_score()
        if int(composite_score) == 0:
            composite_score = ''
        elif int(composite_score) > 100:
            composite_score = 100
        else:
            composite_score = composite_score
        composite.append(composite_score)

        acre = field_all[i].acreage
        acreage.append(acre)
        
        eschlon_id = field_all[i].eschlon_id
        eschlon.append(eschlon_id)
        
        field_shapefile = field_all[i].get_field_shapefile()
        field_shapefile_name.append(field_shapefile)

        storage_shapefile = field_all[i].get_storage_shapefile()
        storage_shapefile_name.append(storage_shapefile)

        get_tissue_1 = field_all[i].get_tissue_1()
        if get_tissue_1 == 0:
            gettissue_1 = 'No'
        elif get_tissue_1 !=0:
            gettissue_1 = 'Yes x  {}' .format(get_tissue_1)
        tissue_1.append(gettissue_1)

        get_tissue_2 = field_all[i].get_tissue_2()
        if get_tissue_2 == 0:
            gettissue_2 = 'No'
        elif get_tissue_2 !=0:
            gettissue_2 = 'Yes x  {}' .format(get_tissue_2)
        tissue_2.append(gettissue_2)

        get_tissue_3 = field_all[i].get_tissue_3()
        if get_tissue_3 == 0:
            gettissue_3 = 'No'
        elif get_tissue_3 !=0:
            gettissue_3 = 'Yes x  {}' .format(get_tissue_3)
        tissue_3.append(gettissue_3)
        
        get_water = field_all[i].get_water()
        if get_water == 0:
            getwater = 'No'
        elif get_water !=0:
            getwater = 'Yes' 
        water.append(getwater)

        get_soil = field_all[i].get_soil()
        if get_soil == 0:
            getsoil = 'No'
        elif get_soil !=0:
            getsoil = 'Yes'
        soil.append(getsoil)

    for i in range(len(field_all)):
        writer.writerow([grower[i], farm[i], field[i], crop[i], contract[i], consultant_name[i],fsa[i],
        survey1[i],survey2[i],survey3[i],composite[i],acreage[i],eschlon[i],field_shapefile_name[i],storage_shapefile_name[i],
        tissue_1[i],tissue_2[i],tissue_3[i],water[i],soil[i]])

    return response


# def reports_all(request):
#     if request.user.is_authenticated:
#         if request.user.is_consultant:
#             pass
#         elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
#         # elif request.user.is_superuser:
#             context = {}
#             field = Field.objects.all().order_by('-created_date')
#             # code
       
#             growers = Grower.objects.all().order_by('name')
#             context['growers'] = growers
#             if request.method == 'POST':
#                 grower_id = request.POST.get('grower_id')
#                 if grower_id != 'all' :
#                     field = Field.objects.filter(grower_id = grower_id)
#                     selectedGrower = Grower.objects.get(id=grower_id)
#                     context['selectedGrower'] = selectedGrower
#                 else:
#                     field = Field.objects.all().order_by('-created_date')

#             page = request.GET.get('page', 1)
#             paginator = Paginator(field, 100)     
#             try:
#                 field = paginator.page(page)
#             except PageNotAnInteger:
#                 field = paginator.page(page)
#             except EmptyPage:
#                 field = paginator.page(paginator.num_pages)

#             field= paginator.get_page(page)
#             context['field'] = field

#             return render(request,'documents/reports_all.html',context)
#     else:
#         return redirect('login')


# Live code ............................
@login_required()
def reports_csv(request,selectedGrower):
    # Create the HttpResponse object with the appropriate CSV header.
    grower_name = Grower.objects.get(id=selectedGrower).name
    filename = '{} Reports.csv'.format(grower_name)
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="{}"'.format(filename)},
    )
    field_all = Field.objects.filter(grower_id=selectedGrower)

    writer = csv.writer(response)
    writer.writerow(['GROWER', 'FARM', 'FIELD', 'CROP','CONTRACT RCVD','Consultant','FSA','SURVEY 1','SURVEY 2','SURVEY 3','SURVEY COMPOSITE SCORE','ACREAGE','FIELD ESCHLON ID','FIELD SHAPE FILES','STORAGE SHAPE FILES','TISSUE 1','TISSUE 2','TISSUE 3','WATER','SOIL'])
    grower = []
    farm = []
    field = []
    crop= []
    contract = []
    consultant_name= []
    fsa = []
    survey1 = []
    survey2 = []
    survey3 = []
    composite = []
    acreage = []
    eschlon = []
    storage_shapefile_name = []
    field_shapefile_name = []
    tissue_1 = []
    tissue_2 = []
    tissue_3 = []
    water = []
    soil = []
    for i in range(len(field_all)):
        grower_name = field_all[i].grower.name
        grower.append(grower_name)
        farm_name = field_all[i].farm.name
        farm.append(farm_name)
        field_name = field_all[i].name
        field.append(field_name)
        crop_name = field_all[i].crop
        crop.append(crop_name)

        get_c = field_all[i].get_contract()
        contract.append(get_c)

        get_consultant = field_all[i].get_consultant_name()
        consultant_name.append(get_consultant)
        
        fsa_field= field_all[i].fsa_field_number
        fsa.append(fsa_field)
       
        get_survey1 = field_all[i].get_survey1()
        
        
        if get_survey1 == "":
            get_survey1 = 0
        elif int(get_survey1) > 100:
            get_survey1 = 100
        else:
            get_survey1 = get_survey1
        survey1.append(get_survey1)

        get_survey2 = field_all[i].get_survey2()
        print('get_survey2',get_survey2,type(get_survey2))
        
        if get_survey2 == "":
            get_survey2 = 0
        elif int(get_survey2) > 100:
            get_survey2 = 100
        else:
            get_survey2 = get_survey2
        survey2.append(get_survey2)

        get_survey3 = field_all[i].get_survey3()
        print('get_survey3',get_survey3,type(get_survey3))
        
        if get_survey3 == "":
            get_survey3 = 0
        elif int(get_survey3) > 100:
            get_survey3 = 100
        else:
            get_survey3 = get_survey3
        survey3.append(get_survey3)
        
        composite_score = field_all[i].get_composite_score()
        if int(composite_score) == 0:
            composite_score = ''
        elif int(composite_score) > 100:
            composite_score = 100
        else:
            composite_score = composite_score
        composite.append(composite_score)

        acre = field_all[i].acreage
        acreage.append(acre)
        
        eschlon_id = field_all[i].eschlon_id
        eschlon.append(eschlon_id)
        
        field_shapefile = field_all[i].get_field_shapefile()
        field_shapefile_name.append(field_shapefile)

        storage_shapefile = field_all[i].get_storage_shapefile()
        storage_shapefile_name.append(storage_shapefile)

        get_tissue_1 = field_all[i].get_tissue_1()
        if get_tissue_1 == 0:
            gettissue_1 = 'No'
        elif get_tissue_1 !=0:
            gettissue_1 = 'Yes x  {}' .format(get_tissue_1)
        tissue_1.append(gettissue_1)

        get_tissue_2 = field_all[i].get_tissue_2()
        if get_tissue_2 == 0:
            gettissue_2 = 'No'
        elif get_tissue_2 !=0:
            gettissue_2 = 'Yes x  {}' .format(get_tissue_2)
        tissue_2.append(gettissue_2)

        get_tissue_3 = field_all[i].get_tissue_3()
        if get_tissue_3 == 0:
            gettissue_3 = 'No'
        elif get_tissue_3 !=0:
            gettissue_3 = 'Yes x  {}' .format(get_tissue_3)
        tissue_3.append(gettissue_3)
        
        get_water = field_all[i].get_water()
        if get_water == 0:
            getwater = 'No'
        elif get_water !=0:
            getwater = 'Yes' 
        water.append(getwater)

        get_soil = field_all[i].get_soil()
        if get_soil == 0:
            getsoil = 'No'
        elif get_soil !=0:
            getsoil = 'Yes'
        soil.append(getsoil)

    for i in range(len(field_all)):
        writer.writerow([grower[i], farm[i], field[i], crop[i], contract[i], consultant_name[i],fsa[i],
        survey1[i],survey2[i],survey3[i],composite[i],acreage[i],eschlon[i],field_shapefile_name[i],storage_shapefile_name[i],
        tissue_1[i],tissue_2[i],tissue_3[i],water[i],soil[i]])

    return response


# def reports(request):
#     if request.user.is_authenticated:
#         if request.user.is_consultant:
#             pass
#         elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
#         # elif request.user.is_superuser:
#             context = {}
#             field = Field.objects.all().order_by('-created_date')
#             # code           
#             growers = Grower.objects.all().order_by('name')
#             context['growers'] = growers
#             if request.method == 'POST':
#                 grower_id = request.POST.get('grower_id')
#                 if grower_id != 'all' :
#                     field = Field.objects.filter(grower_id = grower_id)
#                     selectedGrower = Grower.objects.get(id=grower_id)
#                     context['selectedGrower'] = selectedGrower
#                 else:
#                     field = Field.objects.all().order_by('-created_date')

#             page = request.GET.get('page', 1)
#             paginator = Paginator(field, 100)     
#             try:
#                 field = paginator.page(page)
#             except PageNotAnInteger:
#                 field = paginator.page(page)
#             except EmptyPage:
#                 field = paginator.page(paginator.num_pages)

#             field= paginator.get_page(page)
#             context['field'] = field

#             return render(request,'documents/reports.html',context)
#     else:
#         return redirect('login')


def reports(request):
    if request.user.is_authenticated:
        if request.user.is_consultant:
            pass  
        elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            context = {}
            growers = Grower.objects.all().order_by('name')
            context['growers'] = growers

            field_queryset = Field.objects.all().order_by('-created_date')

            if request.method == 'POST':
                grower_id = request.POST.get('grower_id')
                if grower_id != 'all':
                    field_queryset = Field.objects.filter(grower_id=grower_id).order_by('-created_date')
                    selectedGrower = Grower.objects.get(id=grower_id)
                    context['selectedGrower'] = selectedGrower
            
            paginator = Paginator(field_queryset, 100) 
            page = request.GET.get('page', 1)
            field_page = paginator.get_page(page)

            context['fields'] = field_page

            return render(request, 'documents/reports.html', context)
    else:
        return redirect('login')


class FolderList(LoginRequiredMixin, ListView):
    def get(self, request):
        '''Default function for get request'''

        folder_data = DocumentFolder.objects.all().order_by('name')
        paginator = Paginator(folder_data, 100) 
        page = request.GET.get('page', 1)
        folder_page = paginator.get_page(page)

        return render(request, 'documents/folder-list.html', {
            'folder_data':folder_page
        })
        

class GetFolder(LoginRequiredMixin, UpdateView):
    def get(self, request):
        '''Default function for get request'''
        id = int(request.GET.get('folder_id'))
        result = DocumentFolder.objects.get(id=id)
        return JsonResponse({'data':result.name})

class SaveFolder(LoginRequiredMixin, CreateView):
    def post(self, request):
        '''Default function for get request'''
        folder_id = int(request.POST.get('folder_id'))
        folder_name = request.POST.get('folder_name')
        created_by = self.request.user.id
        user = User.objects.get(id=created_by)
        if folder_id > 0:
            save_folder = DocumentFolder(id=folder_id,name=folder_name,created_by=user)
            save_folder.save()
            return HttpResponse(1)
        else:
            try:
                save_folder = DocumentFolder(name=folder_name,created_by=user)
                save_folder.save()
                return HttpResponse(1)
            except IntegrityError as e:
                return HttpResponse('Already exists!')

        

class DeleteFolder(LoginRequiredMixin, ListView):
    def post(self, request):
        '''Default function for get request'''
        folder_id = int(request.POST.get('id'))
        save_folder = DocumentFolder(id=folder_id)
        save_folder.delete()
        return HttpResponse(1)

class UploadDocumentPhoto(LoginRequiredMixin, CreateView):
    def get(self, request):
        folder_data = DocumentFolder.objects.all().order_by('name')
        type_survey_data = TypeSurvey.objects.all().order_by('name')

        year_dropdown = []
        for y in range(2020, (datetime.datetime.now().year + 29)):
            year_dropdown.append(y)

        if 'Grower' in request.user.get_role() and not request.user.is_superuser:
            # do something grower
            grower_id=request.user.grower.id
            get_growers = Grower.objects.filter(id=grower_id).order_by('name')
        else:
            if request.user.is_consultant:
                # do something consultant
                consultant_id = Consultant.objects.get(email= request.user.email).id
                get_growers = Grower.objects.filter(consultant=consultant_id).order_by('name')
            else:
                # do something allpower
                get_growers = Grower.objects.all().order_by('name')

        return render(request, 'documents/create-document.html', {
            'folder_data':folder_data,
            'get_growers':get_growers,
            'type_survey_data':type_survey_data,
            'year_dropdown':year_dropdown,
        })

    def post(self, request):
        File = request.FILES.get('File')
        Folder = request.POST.get('Folder')
        Grower = request.POST.get('Grower')
        Farm = request.POST.get('Farm')
        Field = request.POST.get('Field')
        Corp_Year = request.POST.get('Corp_Year')
        
        Tag = request.POST.get('Tag')
        if Tag:
            Tag_json = json.loads(Tag)
            # for T in Tag_json:
            #     for key, value in T.items():
            #         print(value)
            all_tags_arr = []
            for T in Tag_json:
                all_tags_arr.append(T['value'])
            all_tags_comma = ','.join(all_tags_arr)
        else:
            all_tags_comma = ''

        Keyword = request.POST.get('Keyword')
        Survey_Type = request.POST.get('Survey_Type')
        created_by = self.request.user.id
        user = User.objects.get(id=created_by)

        create_doc = DocumentFile(file=File,folder_id=Folder,grower_id=Grower,farm_id=Farm,field_id=Field,corp_year=Corp_Year,tag=all_tags_comma,keyword=Keyword,survey_type_id=Survey_Type,created_by=user)
        create_doc.save()

        messages.success(request, 'Successfully saved.')
        return redirect('document-list')

class DocumentList(LoginRequiredMixin, ListView):
    def get(self, request):
        '''Default function for get request'''
        folder_data = DocumentFolder.objects.all().order_by('name')
        type_survey_data = TypeSurvey.objects.all().order_by('name')

        if 'Grower' in request.user.get_role() and not request.user.is_superuser:
            # do something grower
            grower_id=request.user.grower.id
            get_growers = Grower.objects.filter(id=grower_id).order_by('name')
            doc_file_obj = DocumentFile.objects.filter(grower__in=get_growers).order_by('-id')
            folder_data = DocumentFolder.objects.all().order_by('name')
            # pagi
            page = self.request.GET.get('page', 1)
            paginator = Paginator(doc_file_obj, 400)
            folder_data = DocumentFolder.objects.all().order_by('name')
                        
                        
            try:
                doc_list = paginator.page(page)
            except PageNotAnInteger:
                doc_list = paginator.page(page)
            except EmptyPage:
                doc_list = paginator.page(paginator.num_pages)
            doc_file_obj= paginator.get_page(page)
            if request.GET.get('folder'):
                folder_name = request.GET.get('folder')
                if folder_name != '0':
                    folder_name = request.GET.get('folder')
                    folder_data1 = DocumentFolder.objects.filter(name=folder_name)
                    doc_file_obj = DocumentFile.objects.filter(grower__in=get_growers).filter(folder__in=folder_data1).order_by('-id')
                    folder_data = DocumentFolder.objects.all().order_by('name')
                    type_survey_data = TypeSurvey.objects.all().order_by('name')
                    # pagi
                    page = self.request.GET.get('page', 1)
                    paginator = Paginator(doc_file_obj, 400)
                    folder_data = DocumentFolder.objects.all().order_by('name')
                        
                        
                    try:
                        doc_list = paginator.page(page)
                    except PageNotAnInteger:
                        doc_list = paginator.page(page)
                    except EmptyPage:
                        doc_list = paginator.page(paginator.num_pages)
                    doc_file_obj= paginator.get_page(page)
                    return render(request, 'documents/document-list.html',{
                    'doc_file_obj':doc_file_obj,
                    'folder_data':folder_data,
                    'type_survey_data':type_survey_data,
                    })
                else:
                    folder_data = DocumentFolder.objects.all().order_by('name')
                    # pagi
                    page = self.request.GET.get('page', 1)
                    paginator = Paginator(doc_file_obj, 400)
                    folder_data = DocumentFolder.objects.all().order_by('name')
                        
                        
                    try:
                        doc_list = paginator.page(page)
                    except PageNotAnInteger:
                        doc_list = paginator.page(page)
                    except EmptyPage:
                        doc_list = paginator.page(paginator.num_pages)
                    doc_file_obj= paginator.get_page(page)
                    return render(request, 'documents/document-list.html',{
                        'doc_file_obj':doc_file_obj,
                        'folder_data':folder_data,
                        'type_survey_data':type_survey_data,
                        })

            if request.GET.get('survey_type'):
                survey_type = request.GET.get('survey_type')
                if survey_type != '0':
                    survey_type = request.GET.get('survey_type')
                    folder_data1 = TypeSurvey.objects.filter(name=survey_type)
                    doc_file_obj = DocumentFile.objects.filter(grower__in=get_growers).filter(survey_type__in=folder_data1)
                    folder_data = DocumentFolder.objects.all().order_by('name')
                    type_survey_data = TypeSurvey.objects.all().order_by('name')
                    # pagi
                    page = self.request.GET.get('page', 1)
                    paginator = Paginator(doc_file_obj, 400)
                    folder_data = DocumentFolder.objects.all().order_by('name')
                        
                        
                    try:
                        doc_list = paginator.page(page)
                    except PageNotAnInteger:
                        doc_list = paginator.page(page)
                    except EmptyPage:
                        doc_list = paginator.page(paginator.num_pages)
                    doc_file_obj= paginator.get_page(page)
                    return render(request, 'documents/document-list.html',{
                    'doc_file_obj':doc_file_obj,
                    'folder_data':folder_data,
                    'type_survey_data':type_survey_data,
                    })
                else:
                    get_growers = Grower.objects.filter(id=grower_id).order_by('name')
                    doc_file_obj = DocumentFile.objects.filter(grower__in=get_growers).order_by('-id')
                    folder_data = DocumentFolder.objects.all().order_by('name')
                    # pagi
                    page = self.request.GET.get('page', 1)
                    paginator = Paginator(doc_file_obj, 400)
                    folder_data = DocumentFolder.objects.all().order_by('name')
                        
                        
                    try:
                        doc_list = paginator.page(page)
                    except PageNotAnInteger:
                        doc_list = paginator.page(page)
                    except EmptyPage:
                        doc_list = paginator.page(paginator.num_pages)
                    doc_file_obj= paginator.get_page(page)
                    return render(request, 'documents/document-list.html',{
                        'doc_file_obj':doc_file_obj,
                        'folder_data':folder_data,
                        'type_survey_data':type_survey_data,
                        })

        else:
            if request.user.is_consultant:
                # do something consultant
                consultant_id = Consultant.objects.get(email= request.user.email).id
                get_growers = Grower.objects.filter(consultant=consultant_id).order_by('name')
                doc_file_obj = DocumentFile.objects.filter(grower__in=get_growers).order_by('-id')
                folder_data = DocumentFolder.objects.all().order_by('name')
                page = self.request.GET.get('page', 1)
                paginator = Paginator(doc_file_obj, 400)
                
                try:
                    doc_list = paginator.page(page)
                except PageNotAnInteger:
                    doc_list = paginator.page(page)
                except EmptyPage:
                    doc_list = paginator.page(paginator.num_pages)
                doc_file_obj= paginator.get_page(page)

                if request.GET.get('folder'):
                    folder_name = request.GET.get('folder')
                    get_growers = Grower.objects.filter(consultant=consultant_id).order_by('name')
                    print(folder_name)
                    if folder_name != '0':
                        folder_data1 = DocumentFolder.objects.filter(name=folder_name)
                        doc_file_obj = DocumentFile.objects.filter(grower__in=get_growers).filter(folder__in=folder_data1).order_by('-id')
                        folder_data = DocumentFolder.objects.all().order_by('name')
                        type_survey_data = TypeSurvey.objects.all().order_by('name')
                        
                        # pagi
                        page = self.request.GET.get('page', 1)
                        paginator = Paginator(doc_file_obj, 400)
                        folder_data = DocumentFolder.objects.all().order_by('name')
                                                
                        try:
                            doc_list = paginator.page(page)
                        except PageNotAnInteger:
                            doc_list = paginator.page(page)
                        except EmptyPage:
                            doc_list = paginator.page(paginator.num_pages)
                        doc_file_obj= paginator.get_page(page)
                        return render(request, 'documents/document-list.html',{
                        'doc_file_obj':doc_file_obj,
                        'folder_data':folder_data,
                        'type_survey_data':type_survey_data,
                        'get_growers':get_growers,
                        })
                    else:
                        # pagi
                        page = self.request.GET.get('page', 1)
                        paginator = Paginator(doc_file_obj, 400)
                        folder_data = DocumentFolder.objects.all().order_by('name')
                        
                        
                        try:
                            doc_list = paginator.page(page)
                        except PageNotAnInteger:
                            doc_list = paginator.page(page)
                        except EmptyPage:
                            doc_list = paginator.page(paginator.num_pages)
                        doc_file_obj= paginator.get_page(page)
                        return render(request, 'documents/document-list.html',{
                        'doc_file_obj':doc_file_obj,
                        'folder_data':folder_data,
                        'type_survey_data':type_survey_data,
                        'get_growers':get_growers,
                        })

                if request.GET.get('survey_type'):
                    survey_type = request.GET.get('survey_type')
                    get_growers = Grower.objects.filter(consultant=consultant_id).order_by('name')
                    if survey_type != '0':
                        folder_data1 = TypeSurvey.objects.filter(name=survey_type)
                        doc_file_obj = DocumentFile.objects.filter(grower__in=get_growers).filter(survey_type__in=folder_data1)
                        folder_data = DocumentFolder.objects.all().order_by('name')
                        type_survey_data = TypeSurvey.objects.all().order_by('name')

                        # pagi
                        page = self.request.GET.get('page', 1)
                        paginator = Paginator(doc_file_obj, 400)
                        folder_data = DocumentFolder.objects.all().order_by('name')
                        
                        
                        try:
                            doc_list = paginator.page(page)
                        except PageNotAnInteger:
                            doc_list = paginator.page(page)
                        except EmptyPage:
                            doc_list = paginator.page(paginator.num_pages)
                        doc_file_obj= paginator.get_page(page)
                        return render(request, 'documents/document-list.html',{
                        'doc_file_obj':doc_file_obj,
                        'folder_data':folder_data,
                        'type_survey_data':type_survey_data,
                        'get_growers':get_growers,
                        })
                    else:
                        # pagi
                        page = self.request.GET.get('page', 1)
                        paginator = Paginator(doc_file_obj, 400)
                        folder_data = DocumentFolder.objects.all().order_by('name')
                        
                        
                        try:
                            doc_list = paginator.page(page)
                        except PageNotAnInteger:
                            doc_list = paginator.page(page)
                        except EmptyPage:
                            doc_list = paginator.page(paginator.num_pages)
                        doc_file_obj= paginator.get_page(page)
                        return render(request, 'documents/document-list.html',{
                        'doc_file_obj':doc_file_obj,
                        'folder_data':folder_data,
                        'type_survey_data':type_survey_data,
                        'get_growers':get_growers,
                        })

                if request.GET.get('grower_id'):
                    grower = int(self.request.GET.get('grower_id'))
                    doc_file_obj = DocumentFile.objects.filter(grower__id=grower)
                    get_growers = Grower.objects.filter(consultant=consultant_id).order_by('name')
                    selectedGrower = 0
                    if grower != 0:
                        doc_file_obj = DocumentFile.objects.filter(grower__id=grower)
                        selectedGrower = Grower.objects.get(pk=grower) 
                    else:
                        return redirect('document-list')
                    # Pagi
                    page = self.request.GET.get('page', 1)
                    paginator = Paginator(doc_file_obj, 400)
                    try:
                        doc_list = paginator.page(page)
                    except PageNotAnInteger:
                        doc_list = paginator.page(page)
                    except EmptyPage:
                        doc_list = paginator.page(paginator.num_pages)
                    doc_file_obj= paginator.get_page(page)
                    return render(request, 'documents/document-list.html',{
                        'doc_file_obj':doc_file_obj,
                        'folder_data':folder_data,
                        'type_survey_data':type_survey_data,
                        'get_growers':get_growers,
                        'selectedGrower':selectedGrower,
                        })

            else:
                # do something allpower ......................................................................
                get_growers = Grower.objects.all().order_by('name')
                doc_file_obj = DocumentFile.objects.filter(grower__in=get_growers).order_by('-id')
                page = self.request.GET.get('page', 1)
                paginator = Paginator(doc_file_obj, 400)
                folder_data = DocumentFolder.objects.all().order_by('name')
                try:
                    doc_list = paginator.page(page)
                except PageNotAnInteger:
                    doc_list = paginator.page(page)
                except EmptyPage:
                    doc_list = paginator.page(paginator.num_pages)
                doc_file_obj= paginator.get_page(page)

                if request.GET.get('folder'):
                    folder_name = request.GET.get('folder')
                    get_growers = Grower.objects.all().order_by('name')
                    if folder_name != '0':
                        selectedfolder = DocumentFolder.objects.filter(name=folder_name)
                        doc_file_obj = DocumentFile.objects.filter(folder__in=selectedfolder).order_by('-id')
                        folder_data = DocumentFolder.objects.all().order_by('name')
                        type_survey_data = TypeSurvey.objects.all().order_by('name')
                        get_growers = Grower.objects.all().order_by('name')
                        # Pagi
                        page = self.request.GET.get('page', 1)
                        paginator = Paginator(doc_file_obj, 400)
                        folder_data = DocumentFolder.objects.all().order_by('name')
                        try:
                            doc_list = paginator.page(page)
                        except PageNotAnInteger:
                            doc_list = paginator.page(page)
                        except EmptyPage:
                            doc_list = paginator.page(paginator.num_pages)
                        doc_file_obj= paginator.get_page(page)
                        return render(request, 'documents/document-list.html',{
                        'doc_file_obj':doc_file_obj,
                        'folder_data':folder_data,
                        'type_survey_data':type_survey_data,
                        'get_growers':get_growers,
                        })
                    else:
                        page = self.request.GET.get('page', 1)
                        paginator = Paginator(doc_file_obj, 400)
                        folder_data = DocumentFolder.objects.all().order_by('name')
                        try:
                            doc_list = paginator.page(page)
                        except PageNotAnInteger:
                            doc_list = paginator.page(page)
                        except EmptyPage:
                            doc_list = paginator.page(paginator.num_pages)
                        doc_file_obj= paginator.get_page(page)
                        folder_data = DocumentFolder.objects.all().order_by('name')
                        return render(request, 'documents/document-list.html',{
                        'doc_file_obj':doc_file_obj,
                        'folder_data':folder_data,
                        'type_survey_data':type_survey_data,
                        'get_growers':get_growers,
                        })

                if request.GET.get('survey_type'):
                    survey_type = request.GET.get('survey_type')
                    get_growers = Grower.objects.all().order_by('name')
                    if survey_type != '0':
                        folder_data1 = TypeSurvey.objects.filter(name=survey_type)
                        doc_file_obj = DocumentFile.objects.filter(survey_type__in=folder_data1)
                        folder_data = DocumentFolder.objects.all().order_by('name')
                        type_survey_data = TypeSurvey.objects.all().order_by('name')
                        get_growers = Grower.objects.all().order_by('name')
                        # pagi
                        page = self.request.GET.get('page', 1)
                        paginator = Paginator(doc_file_obj, 400)
                        folder_data = DocumentFolder.objects.all().order_by('name')                       
                        try:
                            doc_list = paginator.page(page)
                        except PageNotAnInteger:
                            doc_list = paginator.page(page)
                        except EmptyPage:
                            doc_list = paginator.page(paginator.num_pages)
                        doc_file_obj= paginator.get_page(page)
                        folder_data = DocumentFolder.objects.all().order_by('name')
                        return render(request, 'documents/document-list.html',{
                        'doc_file_obj':doc_file_obj,
                        'folder_data':folder_data,
                        'type_survey_data':type_survey_data,
                        'get_growers':get_growers,
                        })
                    else:
                        # pagi
                        page = self.request.GET.get('page', 1)
                        paginator = Paginator(doc_file_obj, 400)
                        folder_data = DocumentFolder.objects.all().order_by('name')
                        get_growers = Grower.objects.all().order_by('name')
                        try:
                            doc_list = paginator.page(page)
                        except PageNotAnInteger:
                            doc_list = paginator.page(page)
                        except EmptyPage:
                            doc_list = paginator.page(paginator.num_pages)
                        doc_file_obj= paginator.get_page(page)
                        folder_data = DocumentFolder.objects.all().order_by('name')

                        return render(request, 'documents/document-list.html',{
                        'doc_file_obj':doc_file_obj,
                        'folder_data':folder_data,
                        'type_survey_data':type_survey_data,
                        'get_growers':get_growers,
                        })
                # Grower Search ......... 
                if request.GET.get('grower_id'):
                    grower = int(self.request.GET.get('grower_id'))
                    doc_file_obj = DocumentFile.objects.filter(grower__id=grower)
                    get_growers = Grower.objects.all().order_by('name')
                    selectedGrower = 0
                    if grower != 0:
                        doc_file_obj = DocumentFile.objects.filter(grower__id=grower)
                        selectedGrower = Grower.objects.get(pk=grower) 
                    else:
                        return redirect('document-list')
                    # Pagi
                    page = self.request.GET.get('page', 1)
                    paginator = Paginator(doc_file_obj, 400)
                    try:
                        doc_list = paginator.page(page)
                    except PageNotAnInteger:
                        doc_list = paginator.page(page)
                    except EmptyPage:
                        doc_list = paginator.page(paginator.num_pages)
                    doc_file_obj= paginator.get_page(page)
                    return render(request, 'documents/document-list.html',{
                        'doc_file_obj':doc_file_obj,
                        'folder_data':folder_data,
                        'type_survey_data':type_survey_data,
                        'get_growers':get_growers,
                        'selectedGrower':selectedGrower,
                        })
                    
                        
        return render(request, 'documents/document-list.html', {
            'doc_file_obj':doc_file_obj,
            'folder_data':folder_data,
            'type_survey_data':type_survey_data,
            'get_growers':get_growers,
        })

class UpdateUploadDocumentPhoto(LoginRequiredMixin, UpdateView):
    def get(self, request, pk):
        single_doc_obj = DocumentFile.objects.get(pk=pk)
        folder_data = DocumentFolder.objects.all().order_by('name')
        type_survey_data = TypeSurvey.objects.all().order_by('name')

        year_dropdown = []
        for y in range(2020, (datetime.datetime.now().year + 29)):
            year_dropdown.append(y)

        if 'Grower' in request.user.get_role() and not request.user.is_superuser :
            # do something grower
            grower_id=request.user.grower.id
            get_growers = Grower.objects.filter(id=grower_id).order_by('name')
        else:
            if request.user.is_consultant:
                # do something consultant
                consultant_id = Consultant.objects.get(email= request.user.email).id
                get_growers = Grower.objects.filter(consultant=consultant_id).order_by('name')
            else:
                # do something allpower
                get_growers = Grower.objects.all().order_by('name')

        return render(request, 'documents/update-document.html', {
            'folder_data':folder_data,
            'get_growers':get_growers,
            'type_survey_data':type_survey_data,
            'single_doc_obj':single_doc_obj,
            'year_dropdown':year_dropdown,
        })

    def post(self, request, pk):
        doc_id = request.POST.get('doc_id')
        File = request.FILES.get('File')
        print(File)
        Folder = request.POST.get('Folder')
        Grower = request.POST.get('Grower')
        Farm = request.POST.get('Farm')
        Field = request.POST.get('Field')
        Corp_Year = request.POST.get('Corp_Year')
        
        Tag = request.POST.get('Tag')
        if Tag:
            Tag_json = json.loads(Tag)
            # for T in Tag_json:
            #     for key, value in T.items():
            #         print(value)
            all_tags_arr = []
            for T in Tag_json:
                all_tags_arr.append(T['value'])
            all_tags_comma = ','.join(all_tags_arr)
        else:
            all_tags_comma = ''

        Keyword = request.POST.get('Keyword')
        Survey_Type = request.POST.get('Survey_Type')
        created_by = self.request.user.id
        user = User.objects.get(id=created_by)
        if File is not None:
            print('not none')
            create_doc_nn = DocumentFile(id=doc_id,file=File,folder_id=Folder,grower_id=Grower,farm_id=Farm,field_id=Field,corp_year=Corp_Year,tag=all_tags_comma,keyword=Keyword,survey_type_id=Survey_Type,created_by=user)
            create_doc_nn.save()
        else:
            print('none')
            # create_doc_n = DocumentFile(id=doc_id,folder_id=Folder,grower_id=Grower,farm_id=Farm,field_id=Field,corp_year=Corp_Year,tag=all_tags_comma,keyword=Keyword,survey_type_id=Survey_Type,created_by=user)
            # create_doc_n.save()
            create_doc_n = DocumentFile.objects.get(id=doc_id)
            create_doc_n.folder_id = Folder
            create_doc_n.grower_id = Grower
            create_doc_n.farm_id = Farm
            create_doc_n.field_id = Field
            create_doc_n.corp_year = Corp_Year
            create_doc_n.tag = all_tags_comma
            create_doc_n.keyword = Keyword
            create_doc_n.survey_type_id = Survey_Type
            create_doc_n.created_by = user
            create_doc_n.save()

        messages.success(request, 'Successfully saved.')
        return redirect('document-list')

class DocumentDelete(LoginRequiredMixin, ListView):
    def post(self, request):
        '''Default function for get request'''
        doc_id = int(request.POST.get('id'))
        del_doc = DocumentFile(id=doc_id)
        del_doc.delete()
        return HttpResponse(1)