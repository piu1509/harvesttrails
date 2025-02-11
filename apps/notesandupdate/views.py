from platform import release
from django.views.generic.base import View
from django.template.loader import render_to_string
from django.shortcuts import render, HttpResponse, redirect
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
from django.core import serializers
from urllib.parse import urlparse
import datetime
from django.db.models import Count
from django.db.models import Avg
from django.contrib.auth.decorators import login_required
from apps.notesandupdate.models import ReleaseNote, UpcomingDate, HelpAndGuide
from django.db import models
from django.db.models import F


# Create your views here.
class ReleaseNotesList(LoginRequiredMixin, ListView):
    def get(self, request):
        '''Default function for get request'''
        release_notes = ReleaseNote.objects.all().order_by('id')
        return render(request, 'notesandupdate/ReleaseNotesList.html', {
            'release_notes': release_notes
        })


class UpcomingDateList(LoginRequiredMixin, ListView):
    def get(self, request):
        '''Default function for get request'''
        some_date = datetime.date.today()
        #upcoming_dates = UpcomingDate.objects.all().order_by('show_date')

        upcoming_dates = (UpcomingDate.objects.annotate(
        relevance=models.Case(
            models.When(show_date__gte=some_date, then=1),
            models.When(show_date__lt=some_date, then=2),
            output_field=models.IntegerField(),
        )).annotate(
        timediff=models.Case(
            models.When(show_date__gte=some_date, then=F('show_date') - some_date),
            models.When(show_date__lt=some_date, then=some_date - F('show_date')),
            output_field=models.DurationField(),
        )).order_by('relevance', 'timediff'))
        
        
        return render(request, 'notesandupdate/UpcomingDateList.html', {
            'upcoming_dates': upcoming_dates
        })


class ReleaseNotesCreate(LoginRequiredMixin, CreateView):
    def get(self, request):
        return render(request, 'notesandupdate/ReleaseNotesCreate.html', {
            
        })


class UpcomingDateCreate(LoginRequiredMixin, CreateView):
    def get(self, request):
        return render(request, 'notesandupdate/UpcomingDateCreate.html', {
            
        })


def ReleaseNotesCreateSave(request):
    note = request.POST.get('note')
    status = request.POST.get('status')

    save_note = ReleaseNote(description=note,status=status)
    save_note.save()
    messages.success(request, 'Successfully saved.')
    return redirect('release-notes-list')


def UpcomingDateCreateSave(request):
    note = request.POST.get('note')
    status = request.POST.get('status')
    showdate = request.POST.get('showdate')

    save_note = UpcomingDate(description=note,status=status,show_date=showdate)
    save_note.save()
    messages.success(request, 'Successfully saved.')
    return redirect('upcoming-date-list')


class ReleaseNotesUpdate(LoginRequiredMixin, UpdateView):
    def get(self, request, pk):
        release_note_data = ReleaseNote.objects.get(pk=pk)


        return render(request, 'notesandupdate/ReleaseNotesUpdate.html', {
            'release_note_data':release_note_data
        })


def ReleaseNotesUpdateSave(request):
    note = request.POST.get('note')
    status = request.POST.get('status')
    note_id = request.POST.get('note_id')

    save_note = ReleaseNote(description=note,status=status,id=note_id)
    save_note.save()
    messages.success(request, 'Successfully saved.')
    return redirect('release-notes-list')


def UpcomingDateUpdateSave(request):
    note = request.POST.get('note')
    status = request.POST.get('status')
    showdate = request.POST.get('showdate')
    note_id = request.POST.get('note_id')

    save_note = UpcomingDate(description=note,status=status,show_date=showdate,id=note_id)
    save_note.save()
    messages.success(request, 'Successfully saved.')
    return redirect('upcoming-date-list')


class UpcomingDateUpdate(LoginRequiredMixin, UpdateView):
    def get(self, request, pk):
        upcoming_date_data = UpcomingDate.objects.get(pk=pk)


        return render(request, 'notesandupdate/UpcomingDateUpdate.html', {
            'upcoming_date_data':upcoming_date_data
        })


def UpcomingDateDelete(request):
    id = request.POST.get('id')
    release_note_data = UpcomingDate.objects.get(id=id)
    release_note_data.delete()
    return HttpResponse(1)


def ReleaseNotesDelete(request):
    id = request.POST.get('id')
    upcoming_date_data = ReleaseNote.objects.get(id=id)
    upcoming_date_data.delete()
    return HttpResponse(1)


@login_required()
def HelpAndGuideCreate(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        pdf_file = request.FILES.get('pdf_file')
        description = request.POST.get('description')
        if title and pdf_file and description :
            help_guide = HelpAndGuide(title=title,upload_file=pdf_file,description=description)
            help_guide.save()
            return redirect ('HelpAndGuideList')
    return render(request, 'notesandupdate/HelpAndGuideCreate.html', {})


@login_required()
def HelpAndGuideList(request):
    context = {}
    help_guide = HelpAndGuide.objects.all()
    context['help_guide'] = help_guide
    data_len = len(help_guide)
    if data_len == 0:
        data_text = 'No Record Found'
        context['data_text'] = data_text
    else:
        data_text = ''
        context['data_text'] = data_text
    return render(request, 'notesandupdate/HelpAndGuideList.html', context)


@login_required()
def HelpAndGuideEdit(request,pk):
    context = {}
    help_guide = HelpAndGuide.objects.get(id=pk)
    context['help_guide'] = help_guide
    if request.method == 'POST':
        title = request.POST.get('title')
        pdf_file = request.FILES.get('pdf_file')
        description = request.POST.get('description')
        if title and description :
            help_guide.title = title
            help_guide.description = description
            # help_guide.pdf_file = pdf_file
            help_guide.save()
            if pdf_file :
                help_guide.upload_file = pdf_file
                help_guide.save()
        return redirect ('HelpAndGuideList')
    return render(request, 'notesandupdate/HelpAndGuideEdit.html', context)


@login_required()
def HelpAndGuideDelete(request):
    id = request.POST.get('id')
    help_guide = HelpAndGuide.objects.get(id=id)
    help_guide.delete()
    return HttpResponse(1)


@login_required()
def HelpAndGuideView(request):
    context = {}
    help_guide = HelpAndGuide.objects.all().order_by('-created_date')
    context['help_guide'] = help_guide
    if request.method == 'POST':
        search_key = request.POST.get('search_key')
        search_data = HelpAndGuide.objects.filter(Q(title__icontains=search_key) | Q(description__icontains=search_key)).distinct()
        context['help_guide'] = search_data
        return render(request, 'notesandupdate/HelpAndGuideView.html', context)
            
    return render(request, 'notesandupdate/HelpAndGuideView.html', context)


@login_required()
def HelpAndGuideDetails(request,pk):
    context = {}
    help_guide = HelpAndGuide.objects.get(id=pk)
    context['help_guide'] = help_guide
    return render(request, 'notesandupdate/HelpAndGuideDetails.html', context)
