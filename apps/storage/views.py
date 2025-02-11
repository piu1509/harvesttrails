from multiprocessing import context
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from apps.grower.models import Consultant, Grower
from apps.field.models import *
from apps.storage.models import *
from apps.accounts.models import User, LogTable
from apps.storage.models import ShapeFileDataCo as ShapeFilelatlon , Storage
from apps.storage.forms import StorageForm, ShapeFileDataCo
from django import forms
from . import forms
from django.urls import reverse_lazy
from django.contrib import messages
import shapefile
from django.http import JsonResponse
import os
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
import pandas as pd
# Create your views here.


def reverseTuple(lstOfTuple):
    return [tup[::-1] for tup in lstOfTuple]


def StorageCreateView(request):
    if request.user.is_authenticated:
        context={}
    # Grower ................................
        if 'Grower' in request.user.get_role() and not request.user.is_superuser:
            form = StorageForm()
            context = {'form': form}
            grower_id = request.user.grower.id
            grower = Grower.objects.filter(id=int(grower_id))
            context['grower'] = grower
            field = Field.objects.values_list('crop', flat=True)
            print(field)
            crop_list = set(field) 
            available_crops = set(Crop.objects.values_list('code', flat=True)) 
            print(available_crops)

            crop = list(crop_list.intersection(available_crops))
            context["crop"] = crop

            if request.method == 'POST':
                context = {'form': form}
                name = request.POST.get('storage_name')
                storage_uniqueid = request.POST.get('storage_uniqueid')
                grower = int(request.POST.get('grower_id'))  # Getting grower id
                upload_type = request.POST.get('upload_type')
                grower_crop = request.POST.get('grower_crop')

                if request.FILES.get('zip_file'):
                    form = StorageForm()
                    context = {'form': form}
                    name = request.POST.get('storage_name')
                    grower = Grower.objects.filter(id=int(grower_id))
                    grower_crop = request.POST.get('grower_crop') # grower-crop
                    context['grower'] = grower
                    field = Field.objects.values_list('crop', flat=True)
                    crop_list = set(field) 
                    available_crops = set(Crop.objects.values_list('code', flat=True)) 

                    crop = list(crop_list.intersection(available_crops))
                    context["crop"] = crop

                    storage_uniqueid = request.POST.get('storage_uniqueid')
                    grower_id = int(request.POST.get('grower_id'))
                    zip_file = request.FILES.get('zip_file')
                    strge = Storage(storage_name=name, storage_uniqueid=storage_uniqueid,
                            grower_id=grower_id,crop=grower_crop, upload_type=upload_type, shapefile_id=zip_file)
                    strge.save()
                    
                    # read shapefile esc_id .
                    storage_obj = Storage.objects.filter(storage_name=name).filter(grower_id=grower_id)
                    storage_var = [i.id for i in storage_obj][0]
                    storage_id = Storage.objects.get(id=storage_var)
                    sf = shapefile.Reader(storage_id.shapefile_id.path)

                    features = sf.shapeRecords()
                    for feat in features:
                        eschlon_id = feat.record["id"]
                        storage_id.eschlon_id = eschlon_id
                        storage_id.save()

                    rec = sf.shapeRecords()[0]
                    points = rec.shape.points
                    lat_lon_set = reverseTuple(points)

                    ShapeFilelatlon(coordinates=lat_lon_set,storage_id=storage_id.id).save()
                    # 20-04-23 Log Table
                    log_type, log_status, log_device = "Storage", "Added", "Web"
                    log_idd, log_name = storage_id.id, storage_id.storage_name
                    log_details = f"storage_id = {storage_id.id} | storage_name = {storage_id.storage_name} | storage_uniqueid = {storage_id.storage_uniqueid} | grower_id = {storage_id.grower.id} | grower_name = {storage_id.grower.name} | upload_type = {storage_id.upload_type} | shapefile_id = {zip_file} | latitude = | longitude =  | eschlon_id = {storage_id.eschlon_id} |"
                    
                    action_by_userid = request.user.id
                    user = User.objects.get(id=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()
                    return redirect('storage-list')
                
                if request.POST.get('latitude') and request.POST.get('longitude'):
                    form = StorageForm()
                    context = {'form': form}
                    grower = Grower.objects.filter(id=int(grower_id))
                    context['grower'] = grower
                    field = Field.objects.values_list('crop', flat=True)
                    crop_list = set(field) 
                    available_crops = set(Crop.objects.values_list('code', flat=True)) 

                    crop = list(crop_list.intersection(available_crops))
                    context["crop"] = crop

                    latitude = request.POST.get('latitude')
                    longitude = request.POST.get('longitude')
                    grower_id = int(request.POST.get('grower_id'))
                    grower_crop = request.POST.get('grower_crop')
                    storage_id = Storage(storage_name=name, storage_uniqueid=storage_uniqueid, grower_id=grower_id,crop=grower_crop,
                            upload_type=upload_type, latitude=latitude, longitude=longitude)
                    storage_id.save()
                    
                    # 20-04-23 Log Table
                    log_type, log_status, log_device = "Storage", "Added", "Web"
                    log_idd, log_name = storage_id.id, storage_id.storage_name
                    log_details = f"storage_id = {storage_id.id} | storage_name = {storage_id.storage_name} | storage_uniqueid = {storage_id.storage_uniqueid} | grower_id = {storage_id.grower.id} | grower_name = {storage_id.grower.name} | upload_type = {storage_id.upload_type} | shapefile_id = | latitude = {storage_id.latitude} | longitude = {storage_id.longitude} | eschlon_id = |"
                    
                    action_by_userid = request.user.id
                    user = User.objects.get(id=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()
                    return redirect('storage-list')

                return render(request, 'storage/storage_create.html', context)

            return render(request, 'storage/storage_create.html', context)

        
            # consultant ..........................
        elif request.user.is_consultant:
            form = StorageForm()
            context = {'form': form}
            consultant_id = Consultant.objects.get(email=request.user.email).id
            grower = Grower.objects.filter(consultant=consultant_id)
            context['grower'] = grower
            field = Field.objects.values_list('crop', flat=True)
            crop_list = set(field) 
            available_crops = set(Crop.objects.values_list('code', flat=True)) 

            crop = list(crop_list.intersection(available_crops))
            context["crop"] = crop

            if request.method == 'POST':
                context = {'form': form}
                name = request.POST.get('storage_name')
                storage_uniqueid = request.POST.get('storage_uniqueid')
                grower = int(request.POST.get('grower_id'))  # Getting grower id
                grower_crop = request.POST.get('grower_crop') # grower_crop
                upload_type = request.POST.get('upload_type')

                if request.FILES.get('zip_file'):
                    form = StorageForm()
                    context = {'form': form}
                    name = request.POST.get('storage_name')
                    grower = Grower.objects.filter(consultant=consultant_id)
                    context['grower'] = grower
                    storage_uniqueid = request.POST.get('storage_uniqueid')
                    grower_id = int(request.POST.get('grower_id'))
                    grower_crop = request.POST.get('grower_crop')
                    zip_file = request.FILES.get('zip_file')
                    field = Field.objects.values_list('crop', flat=True)
                    crop_list = set(field) 
                    available_crops = set(Crop.objects.values_list('code', flat=True)) 

                    crop = list(crop_list.intersection(available_crops))
                    context["crop"] = crop
                    
                    Storage(storage_name=name, storage_uniqueid=storage_uniqueid,
                            grower_id=grower_id,crop=grower_crop, upload_type=upload_type, shapefile_id=zip_file).save()
                    
                    # read shapefile esc_id .
                    storage_obj = Storage.objects.filter(storage_name=name).filter(grower_id=grower_id)
                    storage_var = [i.id for i in storage_obj][0]
                    storage_id = Storage.objects.get(id=storage_var)
                    sf = shapefile.Reader(storage_id.shapefile_id.path)

                    features = sf.shapeRecords()
                    for feat in features:
                        eschlon_id = feat.record["id"]
                        storage_id.eschlon_id = eschlon_id
                        storage_id.save()

                    rec = sf.shapeRecords()[0]
                    points = rec.shape.points
                    lat_lon_set = reverseTuple(points)
                    ShapeFilelatlon(coordinates=lat_lon_set,storage_id=storage_id.id).save()
                    # 20-04-23 Log Table
                    log_type, log_status, log_device = "Storage", "Added", "Web"
                    log_idd, log_name = storage_id.id, storage_id.storage_name
                    log_details = f"storage_id = {storage_id.id} | storage_name = {storage_id.storage_name} | storage_uniqueid = {storage_id.storage_uniqueid} | grower_id = {storage_id.grower.id} | grower_name = {storage_id.grower.name} | upload_type = {storage_id.upload_type} | shapefile_id = {zip_file} | latitude = | longitude =  | eschlon_id = {storage_id.eschlon_id} |"
                    
                    action_by_userid = request.user.id
                    user = User.objects.get(id=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()
                    return redirect('storage-list')


                if request.POST.get('latitude') and request.POST.get('longitude'):
                    form = StorageForm()
                    context = {'form': form}
                    grower = Grower.objects.filter(consultant=consultant_id)
                    context['grower'] = grower
                    field = Field.objects.values_list('crop', flat=True)
                    crop_list = set(field) 
                    available_crops = set(Crop.objects.values_list('code', flat=True)) 

                    crop = list(crop_list.intersection(available_crops))
                    context["crop"] = crop
                    latitude = request.POST.get('latitude')
                    longitude = request.POST.get('longitude')
                    grower_id = int(request.POST.get('grower_id'))
                    grower_crop = request.POST.get('grower_crop')
                    storage_id = Storage(storage_name=name, storage_uniqueid=storage_uniqueid, grower_id=grower_id,crop=grower_crop,
                            upload_type=upload_type, latitude=latitude, longitude=longitude)
                    storage_id.save()
                    
                    # 20-04-23 Log Table
                    log_type, log_status, log_device = "Storage", "Added", "Web"
                    log_idd, log_name = storage_id.id, storage_id.storage_name
                    log_details = f"storage_id = {storage_id.id} | storage_name = {storage_id.storage_name} | storage_uniqueid = {storage_id.storage_uniqueid} | grower_id = {storage_id.grower.id} | grower_name = {storage_id.grower.name} | upload_type = {storage_id.upload_type} | shapefile_id = | latitude = {storage_id.latitude} | longitude = {storage_id.longitude} | eschlon_id = |"
                    
                    action_by_userid = request.user.id
                    user = User.objects.get(id=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()
                    
                    return redirect('storage-list')

                return render(request, 'storage/storage_create.html', context)

            return render(request, 'storage/storage_create.html', context)
                
        # superadmin and others ................
        elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():

            # past code
            form = StorageForm()
            context = {'form': form}
            grower = Grower.objects.all().order_by('name')
            context['grower'] = grower
            field = Field.objects.values_list('crop', flat=True)
            crop_list = set(field) 
            available_crops = set(Crop.objects.values_list('code', flat=True)) 

            crop = list(crop_list.intersection(available_crops))
            context["crop"] = crop

            if request.method == 'POST':
                context = {'form': form}
                name = request.POST.get('storage_name')
                storage_uniqueid = request.POST.get('storage_uniqueid')
                grower = int(request.POST.get('grower_id'))  # Getting grower id
                upload_type = request.POST.get('upload_type')
                grower_crop = request.POST.get('grower_crop')

                if request.FILES.get('zip_file'):
                    form = StorageForm()
                    context = {'form': form}
                    name = request.POST.get('storage_name')
                    grower = Grower.objects.all().order_by('name')
                    context['grower'] = grower
                    field = Field.objects.values_list('crop', flat=True)
                    crop_list = set(field) 
                    available_crops = set(Crop.objects.values_list('code', flat=True)) 

                    crop = list(crop_list.intersection(available_crops))
                    context["crop"] = crop
            
                    storage_uniqueid = request.POST.get('storage_uniqueid')
                    grower_id = int(request.POST.get('grower_id'))
                    grower_crop = request.POST.get('grower_crop')
                    uploaded_file = request.FILES.get('zip_file')
                    
                    Storage(storage_name=name, storage_uniqueid=storage_uniqueid,
                            grower_id=grower_id,crop=grower_crop,upload_type=upload_type, shapefile_id=uploaded_file).save()
                    
                    # read shapefile esc_id .
                    storage_obj = Storage.objects.filter(storage_name=name).filter(grower_id=grower_id)
                    storage_var = [i.id for i in storage_obj][0]
                    storage_id = Storage.objects.get(id=storage_var)
                    sf = shapefile.Reader(storage_id.shapefile_id.path)

                    features = sf.shapeRecords()
                    for feat in features:
                        eschlon_id = feat.record["id"]
                        storage_id.eschlon_id = eschlon_id
                        storage_id.save()

                    rec = sf.shapeRecords()[0]
                    points = rec.shape.points
                    lat_lon_set = reverseTuple(points)
                    ShapeFilelatlon(coordinates=lat_lon_set,storage_id=storage_id.id).save()

                    # 20-04-23 Log Table
                    log_type, log_status, log_device = "Storage", "Added", "Web"
                    log_idd, log_name = storage_id.id, storage_id.storage_name
                    log_details = f"storage_id = {storage_id.id} | storage_name = {storage_id.storage_name} | storage_uniqueid = {storage_id.storage_uniqueid} | grower_id = {storage_id.grower.id} | grower_name = {storage_id.grower.name} | upload_type = {storage_id.upload_type} | shapefile_id = {zip_file} | latitude = | longitude =  | eschlon_id = {storage_id.eschlon_id} |"
                    
                    action_by_userid = request.user.id
                    user = User.objects.get(id=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()
                    return redirect('storage-list')

                if request.POST.get('latitude') and request.POST.get('longitude'):
                    form = StorageForm()
                    context = {'form': form}
                    grower = Grower.objects.all().order_by('name')
                    context['grower'] = grower
                    field = Field.objects.values_list('crop', flat=True)
                    crop_list = set(field) 
                    available_crops = set(Crop.objects.values_list('code', flat=True)) 

                    crop = list(crop_list.intersection(available_crops))
                    context["crop"] = crop
                    
                    latitude = request.POST.get('latitude')
                    longitude = request.POST.get('longitude')
                    grower_id = int(request.POST.get('grower_id'))
                    grower_crop = request.POST.get('grower_crop')
                    storage_id = Storage(storage_name=name, storage_uniqueid=storage_uniqueid, grower_id=grower_id,
                            upload_type=upload_type,crop=grower_crop, latitude=latitude, longitude=longitude)
                    storage_id.save()
                    
                    # 20-04-23 Log Table
                    log_type, log_status, log_device = "Storage", "Added", "Web"
                    log_idd, log_name = storage_id.id, storage_id.storage_name
                    log_details = f"storage_id = {storage_id.id} | storage_name = {storage_id.storage_name} | storage_uniqueid = {storage_id.storage_uniqueid} | grower_id = {storage_id.grower.id} | grower_name = {storage_id.grower.name} | upload_type = {storage_id.upload_type} | shapefile_id = | latitude = {storage_id.latitude} | longitude = {storage_id.longitude} | eschlon_id = |"
                    
                    action_by_userid = request.user.id
                    user = User.objects.get(id=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()
                    # return render(request,'storage/storage_create.html',context)
                    # storage_id = Storage.objects.get(storage_uniqueid=storage_uniqueid)                       
                    # print(storage_id)
                    return redirect('storage-list')

                return render(request, 'storage/storage_create.html', context)

            return render(request, 'storage/storage_create.html', context)
        else:
            return redirect('login')  
    else:
        return redirect('login')


def StorageListView(request):
    if request.user.is_authenticated:
        context ={}
    # Grower ................................
        if 'Grower' in request.user.get_role() and not request.user.is_superuser:
            grower_id = request.user.grower.id
            storage = Storage.objects.filter(grower=int(grower_id)).order_by('id')
            context = {'storage': storage}
            growers = Grower.objects.filter(id=int(grower_id))
            context['growers'] = growers
            if request.POST.get('storage_name'):
                    storage_name = request.POST.get('storage_name')
                    storage = Storage.objects.filter(storage_name__icontains=storage_name).filter(grower=int(grower_id)).order_by('id')
                    context = {'storage': storage}
                    growers = Grower.objects.filter(id=int(grower_id))
                    context['growers'] = growers
                    return render(request, 'storage/storage_list.html', context)
            
            if request.POST.get('storage_id'):
                    storage_id = request.POST.get('storage_id')
                    storage = Storage.objects.filter(storage_uniqueid__icontains=storage_id).filter(grower=int(grower_id)).order_by('id')
                    context = {'storage': storage}
                    growers = Grower.objects.filter(id=int(grower_id))
                    context['growers'] = growers
                    return render(request, 'storage/storage_list.html', context)
            
            return render(request, 'storage/storage_list.html', context)

        
            # consultant ..........................
        elif request.user.is_consultant :
            consultant_id = Consultant.objects.get(email=request.user.email).id
            growers = Grower.objects.filter(consultant=consultant_id)
            context['growers'] = growers
            grower_ids = [data.id for data in growers]
            storage = Storage.objects.filter(grower_id__in=grower_ids).order_by('id')
            context['storage_all'] = storage.order_by('storage_name')
            
            if request.GET.get('growerSelction') and request.GET.get('growerSelction') != 'all':
                grower_id = int(request.GET.get('growerSelction'))
                if grower_id != 0:
                    context['selectedGrower'] = Grower.objects.get(
                        pk=grower_id)
                    storage = Storage.objects.filter(grower_id=grower_id).filter(grower_id__in=grower_ids).order_by('id')
                    context['storage'] = storage
                    
            elif request.GET.get('storage_name') and request.GET.get('storage_name') != 'all' :
                storage_name = request.GET.get('storage_name')
                storage = Storage.objects.filter(storage_name__icontains=storage_name).filter(grower__in=grower_ids).order_by('id')
                growers = Grower.objects.filter(consultant=consultant_id)
                context['growers'] = growers
                context['get_storage_name'] = storage_name
                
        
            elif request.GET.get('storage_id') and request.GET.get('storage_id') != 'all' :
                    storage_id = request.GET.get('storage_id')
                    storage = Storage.objects.filter(storage_uniqueid__icontains=storage_id).filter(grower__in=grower_ids).order_by('id')
                    growers = Grower.objects.filter(consultant=consultant_id)
                    context['growers'] = growers
                    context['get_storage_id'] = storage_id
                    
            paginator = Paginator(storage, 100)  # Show 10 items per page
            page = request.GET.get('page',1)
            storage_page = paginator.get_page(page)
           
            try:
                storage_page = paginator.page(page)
            except PageNotAnInteger:
                storage_page = paginator.page(1)
            except EmptyPage:
                storage_page = paginator.page(paginator.num_pages)
            storage = storage_page
            context['storage'] = storage
            return render(request, 'storage/storage_list.html', context)
            # superadmin and others ................
        elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():

            id = request.user.id

            storage = Storage.objects.all().order_by('id')
            context['storage_all'] = storage.order_by('storage_name')
            growers = Grower.objects.all().order_by('name')
            context['growers'] = growers
            storage = Storage.objects.all().order_by('id')
            context['storage_ids'] = storage.order_by('storage_uniqueid')

            if request.GET.get('growerSelction') and request.GET.get('growerSelction') != "all" :
                grower_id = int(request.GET.get('growerSelction'))
                if grower_id != 0:
                    context['selectedGrower'] = Grower.objects.get(pk=grower_id)
                    storage = Storage.objects.filter(grower_id=grower_id).order_by('id')
                    
            elif request.GET.get('storage_name') and request.GET.get('storage_name') != "all" :
                storage_name = request.GET.get('storage_name')
                storage = Storage.objects.filter(storage_name__icontains=storage_name).order_by('id')
                context['get_storage_name'] = storage_name
                growers = Grower.objects.all().order_by('name')
                context['growers'] = growers
                
            elif request.GET.get('storage_id') and request.GET.get('storage_id') != "all" :
         
                storage_id = request.GET.get('storage_id')
                storage = Storage.objects.filter(storage_uniqueid__icontains=storage_id).order_by('id')
                context['get_storage_id'] = storage_id
                growers = Grower.objects.all().order_by('name')
                context['growers'] = growers
                
            paginator = Paginator(storage, 100)  # Show 10 items per page
            page = request.GET.get('page',1)
            storage_page = paginator.get_page(page)
        
            try:
                storage_page = paginator.page(page)
            except PageNotAnInteger:
                storage_page = paginator.page(1)
            except EmptyPage:
                storage_page = paginator.page(paginator.num_pages)
            storage = storage_page
            context['storage'] = storage
            return render(request, 'storage/storage_list.html', context)
        else:
            return redirect('login')
    else:
        return redirect('login')


def StorageUpdateView(request, pk):
    if request.user.is_authenticated:
        # Grower ................................
        if 'Grower' in request.user.get_role() and not request.user.is_superuser:
            grower_id = request.user.grower.id
            storage_update = Storage.objects.get(id=pk)
            storage = Storage.objects.filter(id=pk)
            form = StorageForm(instance=storage_update)
            context = {'form':form}
            growers = Grower.objects.filter(id=int(grower_id))
            context['growers'] = growers
            selectedGrower = [data.id for data in growers]
            context['selectedGrower'] = selectedGrower
            context['storage'] = storage
            context['uploadtypeselect']=storage_update.upload_type
            if request.method =='POST':
                storage_name = request.POST.get('storage_name')
                storage_uniqueid = request.POST.get('storage_uniqueid')
                uploadtypeSelction = request.POST.get('uploadtypeSelction')
                shapefile_id = request.FILES.get('zip_file')
                latitude = request.POST.get('latitude')
                longitude = request.POST.get('longitude')

                if uploadtypeSelction == 'shapefile':
                    storage_update = Storage.objects.get(id=pk)
                    storage_update.storage_name = storage_name
                    storage_update.storage_uniqueid = storage_uniqueid
                    storage_update.upload_type = 'shapefile'
                    storage_update.shapefile_id = shapefile_id
                    storage_update.latitude = None
                    storage_update.longitude = None
                    storage_update.save()

                    storage_id = Storage.objects.get(id=pk)
                    if ShapeFilelatlon.objects.filter(storage_id=storage_id.id).count() != 0:
                        ShapeFilelatlon.objects.get(storage_id=storage_id.id).delete()
                                         
                    
                    if request.FILES.get('zip_file'):
                        sf = shapefile.Reader(storage_id.shapefile_id.path)

                        features = sf.shapeRecords()
                        for feat in features:
                            eschlon_id = feat.record["id"]
                            storage_id.eschlon_id = eschlon_id
                            storage_id.save()

                        rec = sf.shapeRecords()[0]
                        points = rec.shape.points
                        lat_lon_set = reverseTuple(points)
                        ShapeFilelatlon(coordinates=lat_lon_set,storage_id=storage_id.id).save()
                        # 20-04-23 Log Table
                        log_type, log_status, log_device = "Storage", "Edited", "Web"
                        log_idd, log_name = storage_id.id, storage_id.storage_name
                        log_details = f"storage_id = {storage_id.id} | storage_name = {storage_id.storage_name} | storage_uniqueid = {storage_id.storage_uniqueid} | grower_id = {storage_id.grower.id} | grower_name = {storage_id.grower.name} | upload_type = {storage_id.upload_type} | shapefile_id = {shapefile_id} | latitude = | longitude =  | eschlon_id = {storage_id.eschlon_id} |"
                        
                        action_by_userid = request.user.id
                        user = User.objects.get(id=action_by_userid)
                        user_role = user.role.all()
                        action_by_username = f'{user.first_name} {user.last_name}'
                        action_by_email = user.username
                        if user.id == 1 :
                            action_by_role = "superuser"
                        else:
                            action_by_role = str(','.join([str(i.role) for i in user_role]))
                        logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                            action_by_userid=action_by_userid,action_by_username=action_by_username,
                                            action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                            log_device=log_device)
                        logtable.save()
                    return redirect('storage-list')
                else:
                    storage_update = Storage.objects.get(id=pk)
                    storage_update.storage_name = storage_name
                    storage_update.storage_uniqueid = storage_uniqueid
                    storage_update.upload_type = 'coordinates'
                    storage_update.shapefile_id = None
                    storage_update.eschlon_id = None
                    storage_update.latitude = latitude
                    storage_update.longitude = longitude
                    storage_update.save()
                    # 20-04-23 Log Table
                    log_type, log_status, log_device = "Storage", "Edited", "Web"
                    log_idd, log_name = storage_update.id, storage_update.storage_name
                    log_details = f"storage_id = {storage_update.id} | storage_name = {storage_update.storage_name} | storage_uniqueid = {storage_update.storage_uniqueid} | grower_id = {storage_update.grower.id} | grower_name = {storage_update.grower.name} | upload_type = {storage_update.upload_type} | shapefile_id = | latitude = {storage_update.latitude} | longitude = {storage_update.longitude} | eschlon_id = |"
                    
                    action_by_userid = request.user.id
                    user = User.objects.get(id=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()
                    if ShapeFilelatlon.objects.filter(storage_id=storage_id.id).count() != 0:
                        ShapeFilelatlon.objects.get(storage_id=storage_id.id).delete()
                    return redirect('storage-list')
            
            return render(request, 'storage/storage_update.html',context)
    
            # consultant ..........................
        elif request.user.is_consultant:
            consultant_id = Consultant.objects.get(email=request.user.email).id
            storage_update = Storage.objects.get(id=pk)
            storage = Storage.objects.filter(id=pk)
            form = StorageForm(instance=storage_update)
            context = {'form':form}
            growers = Grower.objects.filter(consultant=consultant_id)
            context['growers'] = growers
            selectedGrower = [data.grower_id for data in storage]
            context['selectedGrower'] = selectedGrower[0]
            context['storage'] = storage
            context['uploadtypeselect']=storage_update.upload_type

            if request.method =='POST':
                storage_name = request.POST.get('storage_name')
                storage_uniqueid = request.POST.get('storage_uniqueid')
                growerSelction = int(request.POST.get('growerSelction'))
                uploadtypeSelction = request.POST.get('uploadtypeSelction')
                shapefile_id = request.FILES.get('zip_file')
                latitude = request.POST.get('latitude')
                longitude = request.POST.get('longitude')

                if uploadtypeSelction == 'shapefile':
                    storage_update = Storage.objects.get(id=pk)
                    storage_update.storage_name = storage_name
                    storage_update.storage_uniqueid = storage_uniqueid
                    storage_update.grower_id = growerSelction
                    storage_update.upload_type = 'shapefile'
                    storage_update.shapefile_id = shapefile_id
                    storage_update.latitude = None
                    storage_update.longitude = None
                    storage_update.save()

                    storage_id = Storage.objects.get(id=pk)
                    if ShapeFilelatlon.objects.filter(storage_id=storage_id.id).count() != 0:
                        ShapeFilelatlon.objects.get(storage_id=storage_id.id).delete()
                    # 20-04-23 Log Table
                    log_type, log_status, log_device = "Storage", "Edited", "Web"
                    log_idd, log_name = storage_update.id, storage_update.storage_name
                    log_details = f"storage_id = {storage_update.id} | storage_name = {storage_update.storage_name} | storage_uniqueid = {storage_update.storage_uniqueid} | grower_id = {storage_update.grower.id} | grower_name = {storage_update.grower.name} | upload_type = {storage_update.upload_type} | shapefile_id = {storage_update.shapefile_id} | latitude = {storage_update.latitude} | longitude = {storage_update.longitude} | eschlon_id = {storage_update.eschlon_id} |"
                    
                    action_by_userid = request.user.id
                    user = User.objects.get(id=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()                      
                    
                    if request.FILES.get('zip_file'):
                        sf = shapefile.Reader(storage_id.shapefile_id.path)

                        features = sf.shapeRecords()
                        for feat in features:
                            eschlon_id = feat.record["id"]
                            storage_id.eschlon_id = eschlon_id
                            storage_id.save()

                        rec = sf.shapeRecords()[0]
                        points = rec.shape.points
                        lat_lon_set = reverseTuple(points)
                        ShapeFilelatlon(coordinates=lat_lon_set,storage_id=storage_id.id).save()
                        # 20-04-23 Log Table
                        log_type, log_status, log_device = "Storage", "Edited", "Web"
                        log_idd, log_name = storage_id.id, storage_id.storage_name
                        log_details = f"storage_id = {storage_id.id} | storage_name = {storage_id.storage_name} | storage_uniqueid = {storage_id.storage_uniqueid} | grower_id = {storage_id.grower.id} | grower_name = {storage_id.grower.name} | upload_type = {storage_id.upload_type} | shapefile_id = {storage_id.shapefile_id} | latitude = {storage_id.latitude} | longitude = {storage_id.longitude} | eschlon_id = {storage_id.eschlon_id} |"
                        
                        action_by_userid = request.user.id
                        user = User.objects.get(id=action_by_userid)
                        user_role = user.role.all()
                        action_by_username = f'{user.first_name} {user.last_name}'
                        action_by_email = user.username
                        if user.id == 1 :
                            action_by_role = "superuser"
                        else:
                            action_by_role = str(','.join([str(i.role) for i in user_role]))
                        logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                            action_by_userid=action_by_userid,action_by_username=action_by_username,
                                            action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                            log_device=log_device)
                        logtable.save() 
                    return redirect('storage-list')
                else:
                    storage_update = Storage.objects.get(id=pk)
                    storage_update.storage_name = storage_name
                    storage_update.storage_uniqueid = storage_uniqueid
                    storage_update.grower_id = growerSelction
                    storage_update.upload_type = 'coordinates'
                    storage_update.shapefile_id = None
                    storage_update.eschlon_id = None
                    storage_update.latitude = latitude
                    storage_update.longitude = longitude
                    storage_update.save()
                    # 20-04-23 Log Table
                    log_type, log_status, log_device = "Storage", "Edited", "Web"
                    log_idd, log_name = storage_update.id, storage_update.storage_name
                    log_details = f"storage_id = {storage_update.id} | storage_name = {storage_update.storage_name} | storage_uniqueid = {storage_update.storage_uniqueid} | grower_id = {storage_update.grower.id} | grower_name = {storage_update.grower.name} | upload_type = {storage_update.upload_type} | shapefile_id = | latitude = {storage_update.latitude} | longitude = {storage_update.longitude} | eschlon_id = |"
                    
                    action_by_userid = request.user.id
                    user = User.objects.get(id=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()
                    if ShapeFilelatlon.objects.filter(storage_id=storage_id.id).count() != 0:
                        ShapeFilelatlon.objects.get(storage_id=storage_id.id).delete()
                    return redirect('storage-list')
                
            return render(request, 'storage/storage_update.html', context)


            # superadmin and others ................
        elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():

            storage_update = Storage.objects.get(id=pk)
            storage = Storage.objects.filter(id=pk)
            form = StorageForm(instance=storage_update)
            context = {'form':form}
            growers = Grower.objects.all().order_by('name')
            context['growers'] = growers
            selectedGrower = [data.grower_id for data in storage]
            context['selectedGrower'] = selectedGrower[0]
            context['storage'] = storage
            context['uploadtypeselect']=storage_update.upload_type
            
            if request.method =='POST':
                storage_name = request.POST.get('storage_name')
                storage_uniqueid = request.POST.get('storage_uniqueid')
                growerSelction = int(request.POST.get('growerSelction'))
                uploadtypeSelction = request.POST.get('uploadtypeSelction')
                shapefile_id = request.FILES.get('zip_file')
                latitude = request.POST.get('latitude')
                longitude = request.POST.get('longitude')
                storage_update = Storage.objects.get(id=pk)
                               
                if uploadtypeSelction == 'shapefile':
                    storage_update = Storage.objects.get(id=pk)
                    storage_update.storage_name = storage_name
                    storage_update.storage_uniqueid = storage_uniqueid
                    storage_update.grower_id = growerSelction
                    storage_update.upload_type = 'shapefile'
                    storage_update.shapefile_id = shapefile_id
                    storage_update.latitude = None
                    storage_update.longitude = None
                    storage_update.save()

                    storage_id = Storage.objects.get(id=pk)
                    if ShapeFilelatlon.objects.filter(storage_id=storage_id.id).count() != 0:
                        ShapeFilelatlon.objects.get(storage_id=storage_id.id).delete()                     
                    
                    if request.FILES.get('zip_file'):
                        sf = shapefile.Reader(storage_id.shapefile_id.path)

                        features = sf.shapeRecords()
                        for feat in features:
                            eschlon_id = feat.record["id"]
                            storage_id.eschlon_id = eschlon_id
                            storage_id.save()

                        rec = sf.shapeRecords()[0]
                        points = rec.shape.points
                        lat_lon_set = reverseTuple(points)
                        ShapeFilelatlon(coordinates=lat_lon_set,storage_id=storage_id.id).save()
                    # 20-04-23 Log Table
                    log_type, log_status, log_device = "Storage", "Edited", "Web"
                    log_idd, log_name = storage_id.id, storage_id.storage_name
                    log_details = f"storage_id = {storage_id.id} | storage_name = {storage_id.storage_name} | storage_uniqueid = {storage_id.storage_uniqueid} | grower_id = {storage_id.grower.id} | grower_name = {storage_id.grower.name} | upload_type = {storage_id.upload_type} | shapefile_id = {storage_id.shapefile_id} | latitude = | longitude =  | eschlon_id = {storage_id.eschlon_id} |"
                    
                    action_by_userid = request.user.id
                    user = User.objects.get(id=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()
                    return redirect('storage-list')

                else:
                    storage_update = Storage.objects.get(id=pk)
                    storage_update.storage_name = storage_name
                    storage_update.storage_uniqueid = storage_uniqueid
                    storage_update.grower_id = growerSelction
                    storage_update.upload_type = 'coordinates'
                    storage_update.shapefile_id = None
                    storage_update.eschlon_id = None
                    storage_update.latitude = latitude
                    storage_update.longitude = longitude
                    storage_update.save()
                    storage_id = Storage.objects.get(id=pk)

                    # 20-04-23 Log Table
                    log_type, log_status, log_device = "Storage", "Edited", "Web"
                    log_idd, log_name = storage_update.id, storage_update.storage_name
                    log_details = f"storage_id = {storage_update.id} | storage_name = {storage_update.storage_name} | storage_uniqueid = {storage_update.storage_uniqueid} | grower_id = {storage_update.grower.id} | grower_name = {storage_update.grower.name} | upload_type = {storage_update.upload_type} | shapefile_id = | latitude = {storage_update.latitude} | longitude = {storage_update.longitude} | eschlon_id = |"
                    
                    action_by_userid = request.user.id
                    user = User.objects.get(id=action_by_userid)
                    user_role = user.role.all()
                    action_by_username = f'{user.first_name} {user.last_name}'
                    action_by_email = user.username
                    if user.id == 1 :
                        action_by_role = "superuser"
                    else:
                        action_by_role = str(','.join([str(i.role) for i in user_role]))
                    logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                                        action_by_userid=action_by_userid,action_by_username=action_by_username,
                                        action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                                        log_device=log_device)
                    logtable.save()

                    if ShapeFilelatlon.objects.filter(storage_id=storage_id.id).count() != 0:
                        ShapeFilelatlon.objects.get(storage_id=storage_id.id).delete()
                    
                    return redirect('storage-list')
                
            return render(request, 'storage/storage_update.html', context)
        else:
            return redirect('login')
    else:
        return redirect('login')


def storageDeleteView(request,pk):
    if request.user.is_authenticated:
        storage = Storage.objects.get(id=pk)
        # 20-04-23 Log Table
        log_type, log_status, log_device = "Storage", "Deleted", "Web"
        log_idd, log_name = storage.id, storage.storage_name
        log_details = f"storage_id = {storage.id} | storage_name = {storage.storage_name} | storage_uniqueid = {storage.storage_uniqueid} | grower_id = {storage.grower.id} | grower_name = {storage.grower.name} | upload_type = {storage.upload_type} | shapefile_id = {storage.shapefile_id} | latitude = {storage.latitude} | longitude = {storage.longitude} | eschlon_id = {storage.eschlon_id} |"
        
        action_by_userid = request.user.id
        user = User.objects.get(id=action_by_userid)
        user_role = user.role.all()
        action_by_username = f'{user.first_name} {user.last_name}'
        action_by_email = user.username
        if user.id == 1 :
            action_by_role = "superuser"
        else:
            action_by_role = str(','.join([str(i.role) for i in user_role]))
        logtable = LogTable(log_type=log_type,log_status=log_status,log_idd=log_idd,log_name=log_name,
                            action_by_userid=action_by_userid,action_by_username=action_by_username,
                            action_by_email=action_by_email,action_by_role=action_by_role,log_details=log_details,
                            log_device=log_device)
        logtable.save()
        if ShapeFileDataCo.objects.filter(storage_id =storage.id):
            ShapeFileDataCo.objects.filter(storage_id =storage.id).delete()
        storage.delete()
        
        return redirect('storage-list')
    else:
        return redirect('login')


@login_required
def storage_feed_list(request):
    try:
        if request.user.is_authenticated:
            context={}
            if 'Grower' in request.user.get_role() and not request.user.is_superuser: 
                grower_id = request.user.grower.id
                if grower_id:
                    storage_feed_data = StorageFeed.objects.filter(grower_id = grower_id ).order_by('-id')
                    crops = Crop.objects.all()
                    context = {'storage_feed_data': storage_feed_data, 'crops':crops}
                
                return render(request,"storage/storage_feed_list.html",context)

            elif request.user.is_consultant:
                consultant_id = Consultant.objects.get(email=request.user.email).id
                # print("consultant_id==========",consultant_id)
                growers = Grower.objects.filter(consultant=consultant_id)
                context['growers'] = growers
                grower_ids = [data.id for data in growers]
                # print("grower_ids===============",grower_ids)
                storage = Storage.objects.filter(grower_id__in=grower_ids).order_by('id')
                # print("storage===============",storage)
                context['storage_name'] = storage.order_by('storage_name')
                field_name = Field.objects.filter(grower_id__in=grower_ids).order_by('id')
                context['field_name'] = field_name.order_by('name')
                storage_feed_data = StorageFeed.objects.filter(grower_id__in=grower_ids ).order_by('-id')
                # context['storage_feed_data'] = storage_feed_data
                crops = Crop.objects.all()
                context['crops'] = crops
                if request.method == "GET":
                    grower_id = request.GET.get("grower_id")
                    storage_id = request.GET.get("storage_id")
                    field_id = request.GET.get("field_id")
                    grower_crop = request.GET.get("grower_crop")
                    if grower_id and grower_id != "all":
                        context["selectedGrower"] = Grower.objects.filter(id=grower_id).first()
                        storage_feed_data = storage_feed_data.filter(grower__id__icontains=grower_id)
                    if storage_id and storage_id !="all" :
                        storage_name = Storage.objects.filter(id=storage_id).order_by('storage_name')
                        context['selectedStorage'] = storage_name.first()
                        storage_feed_data = storage_feed_data.filter(storage__id__icontains=storage_id)
                    if  field_id and field_id !="all" : 
                        field_name = Field.objects.filter(id=field_id).order_by('id')
                        context['selectedField'] = field_name.first()  
                        storage_feed_data = storage_feed_data.filter(field__id__icontains=field_id)
                    if grower_crop and grower_crop!="all" :
                        context['selectedCrop'] = grower_crop   
                        storage_feed_data = storage_feed_data.filter(crop=grower_crop)
                paginator = Paginator(storage_feed_data, 100)  # Show 10 items per page
                page = request.GET.get('page',1)
                storage_page = paginator.get_page(page)
                try:
                    storage_page = paginator.page(page)
                except PageNotAnInteger:
                    storage_page = paginator.page(1)
                except EmptyPage:
                    storage_page = paginator.page(paginator.num_pages)
                storage_feed_data = storage_page
                context['storage_feed_data'] = storage_feed_data  
                
                return render(request,"storage/storage_feed_list.html",context)
                
            elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
                storage = Storage.objects.all().order_by('id')
                context['storage_name'] = storage.order_by('storage_name')
                field_name = Field.objects.all().order_by('id')
                context['field_name'] = field_name.order_by('name')
                storage_feed_data = StorageFeed.objects.all().order_by('-id')
                grower = Grower.objects.all().order_by('name')
                context['growers'] = grower
                crops = Crop.objects.all()
                context['crops'] = crops

                if request.method == "GET":
                    grower_id = request.GET.get("grower_id")
                    storage_id = request.GET.get("storage_id")
                    field_id = request.GET.get("field_id")
                    grower_crop = request.GET.get("grower_crop")
                    if grower_id and grower_id != "all":
                        context["selectedGrower"] = grower.filter(id=grower_id).first()
                        storage_feed_data = storage_feed_data.filter(grower__id__icontains=grower_id)
                    if storage_id and storage_id !="all" :
                        storage_name = Storage.objects.filter(id=storage_id).order_by('storage_name')
                        context['selectedStorage'] = storage_name.first()
                        storage_feed_data = storage_feed_data.filter(storage__id__icontains=storage_id)
                    if  field_id and field_id !="all" : 
                        field_name = Field.objects.filter(id=field_id).order_by('id')
                        context['selectedField'] = field_name.first()  
                        storage_feed_data = storage_feed_data.filter(field__id__icontains=field_id)
                    if grower_crop and grower_crop!="all" :
                        context['selectedCrop'] = grower_crop   
                        storage_feed_data = storage_feed_data.filter(crop=grower_crop)
                paginator = Paginator(storage_feed_data, 100)  # Show 10 items per page
                page = request.GET.get('page',1)
                storage_page = paginator.get_page(page)
                try:
                    storage_page = paginator.page(page)
                except PageNotAnInteger:
                    storage_page = paginator.page(1)
                except EmptyPage:
                    storage_page = paginator.page(paginator.num_pages)
                storage_feed_data = storage_page
                context['storage_feed_data'] = storage_feed_data  
                
                return render(request,"storage/storage_feed_list.html",context)
            else:
                return redirect('login')
        else:
            return redirect('login')   
    except Exception as e:
        messages = str(e)
        return render(request,"storage/storage_feed_list.html",{"messages":messages})


@login_required
def storage_feed_add(request):
    try:
        if request.user.is_authenticated:
            context={}
            error_msg = []
            if 'Grower' in request.user.get_role() and not request.user.is_superuser: 
                grower_id = request.user.grower.id if request.user.grower else None
                context['growers'] = Grower.objects.filter(id=grower_id)
                context.update({
                    'selectedStorage': None,
                    'selectedField': None,
                    'selectedCrop': None,
                    'quantity': None,
                    'unit_id': None
                    
                    })
                if request.method == "POST":                    
                    context.update({
                    'storage_id': request.POST.get('storage_id'),
                    'field_id': request.POST.get('field_id'),
                    'grower_crop': request.POST.get('grower_crop'),
                    'quantity': request.POST.get('quantity'),
                    'unit_id': request.POST.get('unit_id')
                    
                    })
                    
                    if grower_id and grower_id != "all" and not request.POST.get('save'):
                        context["selectedGrower"] =  Grower.objects.filter(id=grower_id).first()
                        storage_name = Storage.objects.filter(grower_id=grower_id).order_by('storage_name')

                        if request.POST.get('storage_id') and request.POST.get('storage_id') != 'all':
                            context['storage_name'] = storage_name
                            context['selectedStorage'] = storage_name.filter(id=storage_id).first()
                        else:
                            context['storage_name'] = storage_name

                        field_name = Field.objects.filter(grower_id=grower_id).order_by('id')
                        if request.POST.get('field_id') and request.POST.get('field_id') != 'all':
                            context['field_name'] = field_name
                            context['selectedField'] = field_name.filter(id=field_id).first()
                        else:
                            context['field_name'] = field_name
                        
                        field = Field.objects.filter(grower_id=grower_id).values_list('crop', flat=True)
                        available_crops = set(Crop.objects.values_list('code', flat=True))
                        crop = list(set(field).intersection(available_crops))

                        if request.POST.get('field_id') and request.POST.get('field_id') != 'all':
                            context["crops"] = crop  
                            context["selectedCrop"] = Crop.objects.filter(crop_code=crop).first() 
                        else:
                            context["crops"] = crop                      
                        
                    else:                       
                        storage_id = context.get('storage_id') 
                        field_id = context.get('field_id')
                        grower_crop = context.get('grower_crop')
                        quantity = context.get('quantity')    
                        unit_id = context.get('unit_id')                                             
                        quantity = error_msg.append("Quantity") if not quantity or len(quantity) <=0 else quantity
                        
                        if len(error_msg) == 0:
                            save_crop = context['selectedField'].crop if context['selectedField'] else grower_crop
                            if unit_id == "LBS" :
                                cal_quantity = round(float(quantity),2)
                            if unit_id == "BU" :
                                cal_quantity = round(float(quantity) * 45,2)
                            final_quantity = cal_quantity
                            check_final_quantity = StorageFeed.objects.filter(grower_id = grower_id,crop=save_crop,
                                                    storage_id = storage_id)
                            if check_final_quantity.exists():
                                check_final_quantity = check_final_quantity.last()
                                final_quantity = round(float(check_final_quantity.final_quantity) + float(cal_quantity),2)
                                
                            save_feed_data = StorageFeed(grower_id = grower_id,crop=save_crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = quantity,quantity=cal_quantity,status = "quantity_in",
                                        unit=unit_id,final_quantity=final_quantity)
                            save_feed_data.save()
                            return redirect ("storage_feed_list")
                        else:
                            context['messages'] = error_msg       
                return render(request,"storage/storage_feed_add.html",context)
            elif request.user.is_consultant:
                consultant_id = Consultant.objects.get(email=request.user.email).id
                # print("consultant_id==========",consultant_id)
                growers = Grower.objects.filter(consultant=consultant_id)
                context['growers'] = growers

                context.update({
                    'selectedStorage': None,
                    'selectedField': None,
                    'selectedCrop': None,
                    'quantity': None,
                    'unit_id': None
                    
                    })
                if request.method == "POST":
                    grower_id = request.POST.get('grower_id')                    
                    context.update({
                        'grower_id': request.POST.get('grower_id'),
                        'storage_id': request.POST.get('storage_id'),
                        'field_id': request.POST.get('field_id'),
                        'grower_crop': request.POST.get('grower_crop'),
                        'quantity': request.POST.get('quantity'),
                        'unit_id': request.POST.get('unit_id')
                        
                        })
                    
                    if grower_id and grower_id != "all" and not request.POST.get('save'):
                        context["selectedGrower"] =  Grower.objects.filter(id=grower_id).first()
                        storage_name = Storage.objects.filter(grower_id=grower_id).order_by('storage_name')

                        if request.POST.get('storage_id') and request.POST.get('storage_id') != 'all':
                            context['storage_name'] = storage_name
                            context['selectedStorage'] = storage_name.filter(id=storage_id).first()
                        else:
                            context['storage_name'] = storage_name

                        field_name = Field.objects.filter(grower_id=grower_id).order_by('id')
                        if request.POST.get('field_id') and request.POST.get('field_id') != 'all':
                            context['field_name'] = field_name
                            context['selectedField'] = field_name.filter(id=field_id).first()
                        else:
                            context['field_name'] = field_name
                        
                        field = Field.objects.filter(grower_id=grower_id).values_list('crop', flat=True)
                        available_crops = set(Crop.objects.values_list('code', flat=True))
                        crop = list(set(field).intersection(available_crops))

                        if request.POST.get('field_id') and request.POST.get('field_id') != 'all':
                            context["crops"] = crop  
                            context["selectedCrop"] = Crop.objects.filter(crop_code=crop).first() 
                        else:
                            context["crops"] = crop                      
                        
                    else:
                        grower_id = context.get('grower_id')  
                        grower_id = Grower.objects.filter(id=int(grower_id)).first().id                    
                        storage_id = context.get('storage_id') 
                        field_id = context.get('field_id')
                        grower_crop = context.get('grower_crop')
                        quantity = context.get('quantity')    
                        unit_id = context.get('unit_id')                                             
                        quantity = error_msg.append("Quantity") if not quantity or len(quantity) <=0 else quantity
                        
                        if len(error_msg) == 0:
                            save_crop = context['selectedField'].crop if context['selectedField'] else grower_crop
                            if unit_id == "LBS" :
                                cal_quantity = round(float(quantity),2)
                            if unit_id == "BU" :
                                cal_quantity = round(float(quantity) * 45,2)
                            final_quantity = cal_quantity
                            check_final_quantity = StorageFeed.objects.filter(grower_id = grower_id,crop=save_crop,
                                                    storage_id = storage_id)
                            if check_final_quantity.exists():
                                check_final_quantity = check_final_quantity.last()
                                final_quantity = round(float(check_final_quantity.final_quantity) + float(cal_quantity),2)
                                
                            save_feed_data = StorageFeed(grower_id = grower_id,crop=save_crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = quantity,quantity=cal_quantity,status = "quantity_in",
                                        unit=unit_id,final_quantity=final_quantity)
                            save_feed_data.save()
                            return redirect ("storage_feed_list")
                        else:
                            context['messages'] = error_msg     
                return render(request,"storage/storage_feed_add.html",context)
            
            
            elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
                grower = Grower.objects.all().order_by('name')
                context['growers'] = grower
                context.update({
                    'selectedStorage': None,
                    'selectedField': None,
                    'selectedCrop': None,
                    'quantity': None,
                    'unit_id': None
                    
                    })
                if request.method == "POST":
                    grower_id = request.POST.get('grower_id')                    
                    context.update({
                        'grower_id': request.POST.get('grower_id'),
                        'storage_id': request.POST.get('storage_id'),
                        'field_id': request.POST.get('field_id'),
                        'grower_crop': request.POST.get('grower_crop'),
                        'quantity': request.POST.get('quantity'),
                        'unit_id': request.POST.get('unit_id')
                        
                        })
                    
                    if grower_id and grower_id != "all" and not request.POST.get('save'):
                        context["selectedGrower"] =  Grower.objects.filter(id=grower_id).first()
                        storage_name = Storage.objects.filter(grower_id=grower_id).order_by('storage_name')

                        if request.POST.get('storage_id') and request.POST.get('storage_id') != 'all':
                            context['storage_name'] = storage_name
                            context['selectedStorage'] = storage_name.filter(id=storage_id).first()
                        else:
                            context['storage_name'] = storage_name

                        field_name = Field.objects.filter(grower_id=grower_id).order_by('id')
                        if request.POST.get('field_id') and request.POST.get('field_id') != 'all':
                            context['field_name'] = field_name
                            context['selectedField'] = field_name.filter(id=field_id).first()
                        else:
                            context['field_name'] = field_name
                        
                        field = Field.objects.filter(grower_id=grower_id).values_list('crop', flat=True)
                        available_crops = set(Crop.objects.values_list('code', flat=True))
                        crop = list(set(field).intersection(available_crops))

                        if request.POST.get('field_id') and request.POST.get('field_id') != 'all':
                            context["crops"] = crop  
                            context["selectedCrop"] = Crop.objects.filter(crop_code=crop).first() 
                        else:
                            context["crops"] = crop                      
                        
                    else:
                        grower_id = context.get('grower_id')  
                        grower_id = Grower.objects.filter(id=int(grower_id)).first().id                    
                        storage_id = context.get('storage_id') 
                        field_id = context.get('field_id')
                        grower_crop = context.get('grower_crop')
                        quantity = context.get('quantity')    
                        unit_id = context.get('unit_id')                                             
                        quantity = error_msg.append("Quantity") if not quantity or len(quantity) <=0 else quantity
                        
                        if len(error_msg) == 0:
                            save_crop = context['selectedField'].crop if context['selectedField'] else grower_crop
                            if unit_id == "LBS" :
                                cal_quantity = round(float(quantity),2)
                            if unit_id == "BU" :
                                cal_quantity = round(float(quantity) * 45,2)
                            final_quantity = cal_quantity
                            check_final_quantity = StorageFeed.objects.filter(grower_id = grower_id,crop=save_crop,
                                                    storage_id = storage_id)
                            if check_final_quantity.exists():
                                check_final_quantity = check_final_quantity.last()
                                final_quantity = round(float(check_final_quantity.final_quantity) + float(cal_quantity),2)
                                
                            save_feed_data = StorageFeed(grower_id = grower_id,crop=save_crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = quantity,quantity=cal_quantity,status = "quantity_in",
                                        unit=unit_id,final_quantity=final_quantity)
                            save_feed_data.save()
                            return redirect ("storage_feed_list")
                        else:
                            context['messages'] = error_msg     
                                
                return render(request,"storage/storage_feed_add.html",context)
            else:
                return redirect('login') 
        else:
            return redirect('login')  
    except Exception as e:
        messages = str(e)
        return render(request,"storage/storage_feed_add.html",{"messages":messages})


@login_required
def storage_feed_update(request):
    try:
        context={}
        error_msg = []
        if 'Grower' in request.user.get_role() and not request.user.is_superuser: 
            try:
                grower_id = request.user.grower.id if request.user.grower else None
                context['growers'] = Grower.objects.filter(id=grower_id)
                context.update({
                        "selectedGrower":None,
                        "selectedStorage":None,
                        "selectedCrop":None,

                    })
                if request.method == "POST":
                    data = request.POST
                    grower_id = data.get("grower_id")                 
                    context.update({
                        "grower_id": data.get("grower_id"),
                        "storage_id": data.get("storage_id"),
                        "grower_crop":data.get("grower_crop"),
                        "quantity":data.get("quantity"),
                        "unit_id":data.get("unit_id")
                    })               
                
                    if grower_id and grower_id != "all" and not data.get("save"):
                        storage_id = data.get('storage_id') 
                        grower_crop = data.get('grower_crop')
                        context["selectedGrower"] = grower.filter(id=grower_id).first()
                        storage_name = Storage.objects.filter(grower_id=grower_id).order_by('storage_name')
                        context['storage_name'] = storage_name
                        if storage_id and storage_id != "all" :
                            context['selectedStorage'] = storage_name.filter(id=storage_id).first()
                        if grower_crop :
                            context["selectedCrop"] = grower_crop
                        if storage_id and storage_id != "all" and grower_crop :
                            check_amt = StorageFeed.objects.filter(grower_id=grower_id,storage_id=storage_id)
                            if check_amt.exists():
                                check_amt = check_amt.last()
                                context["total_quantity"] = check_amt.final_quantity
                                context["amount_unit"] = check_amt.unit
                                
                            else:
                                context["total_quantity"] = 0
                                context["amount_unit"] = None
                                
                        field_name = Field.objects.filter(grower_id=grower_id).order_by('id')
                        context['field_name'] = field_name
                        field = Field.objects.filter(grower_id=grower_id).values_list('crop', flat=True)

                        available_crops = set(Crop.objects.values_list('code', flat=True))
                        crop = list(set(field).intersection(available_crops))

                        context["crop"] = crop
                        return render(request,"storage/storage_feed_update.html",context)
                    else:
                        storage_id = context.get('storage_id')                
                        grower_crop = context.get('grower_crop')
                        quantity = context.get('quantity')
                        unit_id = context.get('unit_id')
                        
                        if unit_id == "LBS" :
                            cal_quantity = round(float(quantity),2)
                        if unit_id == "BU" :
                            cal_quantity = round(float(quantity) * 45,2)
                        final_quantity = cal_quantity                    
                                    
                        save_feed_data = StorageFeed(grower_id = grower_id,crop=grower_crop,storage_id = storage_id,
                                                    quantity_raw = quantity,quantity=cal_quantity,status = "quantity_edit",
                                                    unit=unit_id,final_quantity=final_quantity)
                        save_feed_data.save()
                        return redirect ("storage_feed_list")
                else:
                    return render(request,"storage/storage_feed_update.html",context)    
            except Exception as e:
                context["error_messages"] = str(e)
                return render(request,"storage/storage_feed_update.html",context)
        elif request.user.is_consultant:
            try:
                consultant_id = Consultant.objects.get(email=request.user.email).id
                # print("consultant_id==========",consultant_id)
                growers = Grower.objects.filter(consultant=consultant_id)
                context['growers'] = growers
                context.update({
                        "selectedGrower":None,
                        "selectedStorage":None,
                        "selectedCrop":None,

                    })
                if request.method == "POST":
                    data = request.POST
                    grower_id = data.get("grower_id")                 
                    context.update({
                        "grower_id": data.get("grower_id"),
                        "storage_id": data.get("storage_id"),
                        "grower_crop":data.get("grower_crop"),
                        "quantity":data.get("quantity"),
                        "unit_id":data.get("unit_id")
                    })               
                
                    if grower_id and grower_id != "all" and not data.get("save"):
                        storage_id = data.get('storage_id') 
                        grower_crop = data.get('grower_crop')
                        context["selectedGrower"] = grower.filter(id=grower_id).first()
                        storage_name = Storage.objects.filter(grower_id=grower_id).order_by('storage_name')
                        context['storage_name'] = storage_name
                        if storage_id and storage_id != "all" :
                            context['selectedStorage'] = storage_name.filter(id=storage_id).first()
                        if grower_crop :
                            context["selectedCrop"] = grower_crop
                        if storage_id and storage_id != "all" and grower_crop :
                            check_amt = StorageFeed.objects.filter(grower_id=grower_id,storage_id=storage_id)
                            if check_amt.exists():
                                check_amt = check_amt.last()
                                context["total_quantity"] = check_amt.final_quantity
                                context["amount_unit"] = check_amt.unit
                                
                            else:
                                context["total_quantity"] = 0
                                context["amount_unit"] = None
                                
                        field_name = Field.objects.filter(grower_id=grower_id).order_by('id')
                        context['field_name'] = field_name
                        field = Field.objects.filter(grower_id=grower_id).values_list('crop', flat=True)

                        available_crops = set(Crop.objects.values_list('code', flat=True))
                        crop = list(set(field).intersection(available_crops))

                        context["crop"] = crop
                        return render(request,"storage/storage_feed_update.html",context)
                    else:
                        storage_id = context.get('storage_id')                
                        grower_crop = context.get('grower_crop')
                        quantity = context.get('quantity')
                        unit_id = context.get('unit_id')
                        
                        if unit_id == "LBS" :
                            cal_quantity = round(float(quantity),2)
                        if unit_id == "BU" :
                            cal_quantity = round(float(quantity) * 45,2)
                        final_quantity = cal_quantity                    
                                    
                        save_feed_data = StorageFeed(grower_id = grower_id,crop=grower_crop,storage_id = storage_id,
                                                    quantity_raw = quantity,quantity=cal_quantity,status = "quantity_edit",
                                                    unit=unit_id,final_quantity=final_quantity)
                        save_feed_data.save()
                        return redirect ("storage_feed_list")
                else:
                    return render(request,"storage/storage_feed_update.html",context)    
            except Exception as e:
                context["error_messages"] = str(e)
                return render(request,"storage/storage_feed_update.html",context)
        elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            try:
                grower = Grower.objects.all().order_by('name')
                context['growers'] = grower
                context.update({
                    "selectedGrower":None,
                    "selectedStorage":None,
                    "selectedCrop":None,

                })
                if request.method == "POST":
                    data = request.POST
                    grower_id = data.get("grower_id")                 
                    context.update({
                        "grower_id": data.get("grower_id"),
                        "storage_id": data.get("storage_id"),
                        "grower_crop":data.get("grower_crop"),
                        "quantity":data.get("quantity"),
                        "unit_id":data.get("unit_id")
                    })               
                
                    if grower_id and grower_id != "all" and not data.get("save"):
                        storage_id = data.get('storage_id') 
                        grower_crop = data.get('grower_crop')
                        context["selectedGrower"] = grower.filter(id=grower_id).first()
                        storage_name = Storage.objects.filter(grower_id=grower_id).order_by('storage_name')
                        context['storage_name'] = storage_name
                        if storage_id and storage_id != "all" :
                            context['selectedStorage'] = storage_name.filter(id=storage_id).first()
                        if grower_crop :
                            context["selectedCrop"] = grower_crop
                        if storage_id and storage_id != "all" and grower_crop :
                            check_amt = StorageFeed.objects.filter(grower_id=grower_id,storage_id=storage_id)
                            if check_amt.exists():
                                check_amt = check_amt.last()
                                context["total_quantity"] = check_amt.final_quantity
                                context["amount_unit"] = check_amt.unit
                                
                            else:
                                context["total_quantity"] = 0
                                context["amount_unit"] = None
                                
                        field_name = Field.objects.filter(grower_id=grower_id).order_by('id')
                        context['field_name'] = field_name
                        field = Field.objects.filter(grower_id=grower_id).values_list('crop', flat=True)

                        available_crops = set(Crop.objects.values_list('code', flat=True))
                        crop = list(set(field).intersection(available_crops))

                        context["crop"] = crop
                        return render(request,"storage/storage_feed_update.html",context)
                    else:
                        storage_id = context.get('storage_id')                
                        grower_crop = context.get('grower_crop')
                        quantity = context.get('quantity')
                        unit_id = context.get('unit_id')
                        
                        if unit_id == "LBS" :
                            cal_quantity = round(float(quantity),2)
                        if unit_id == "BU" :
                            cal_quantity = round(float(quantity) * 45,2)
                        final_quantity = cal_quantity                    
                                    
                        save_feed_data = StorageFeed(grower_id = grower_id,crop=grower_crop,storage_id = storage_id,
                                                    quantity_raw = quantity,quantity=cal_quantity,status = "quantity_edit",
                                                    unit=unit_id,final_quantity=final_quantity)
                        save_feed_data.save()
                        return redirect ("storage_feed_list")
                else:
                    return render(request,"storage/storage_feed_update.html",context) 
            except Exception as e:
                context["error_messages"] = str(e)  
                return render(request,"storage/storage_feed_update.html",context)      
            
        else:
            return redirect('login')
    except Exception as e:
        context["error_messages"] = str(e)
        return render(request,"storage/storage_feed_update.html",context)
    

@login_required()
def assign_storage_feed_csv(request):
    context={}
    error_msg = {"grower": [], "storage": [], "field": [], "qnt_add": []}
    try:
        if 'Grower' in request.user.get_role() and not request.user.is_superuser: 
            grower_id = request.user.grower.id if request.user.grower else None
            context['growers'] = Grower.objects.filter(id=grower_id)
            if request.method == "POST":
                csv_file = request.FILES.get("csv_file")
                if csv_file == None:
                    uploadcsv = 0
                else:
                    uploadcsv = pd.read_csv(csv_file).dropna(how='all')
                    for i in range(len(uploadcsv)):
                        grower_name = uploadcsv.iloc[i, 0]
                        grower_id = uploadcsv.iloc[i, 1]
                        crop = uploadcsv.iloc[i, 2]
                        storage_name = uploadcsv.iloc[i, 3]
                        storage_id = uploadcsv.iloc[i, 4]
                        field_name = uploadcsv.iloc[i, 5]
                        field_id = uploadcsv.iloc[i, 6]
                        status  = uploadcsv.iloc[i, 7]
                        qnt  = uploadcsv.iloc[i, 8]
                        unit_id  = uploadcsv.iloc[i, 9]
                        shp_ip  = uploadcsv.iloc[i, 10]
                        print("grower_name",grower_name)
                        print("grower_id",grower_id)
                        grower_obj = Storage.objects.filter(grower_id=grower_id,grower__name__icontains=grower_name)
                        storage_obj = Storage.objects.filter(id=storage_id,storage_name__icontains=storage_name)
                        field_obj = Field.objects.filter(id=field_id,name__icontains=field_name,
                                                            grower_id=grower_id,grower__name__icontains=grower_name)

                        get_csv_file = StorageFeedCsv(csv_path=csv_file,upload_by_id=request.user.id)
                        get_csv_file.save()
                        error_flag = False
                        if grower_obj.exists(): 
                            print("exists")
                        else:
                            error_flag = True
                            error_msg["grower"].append(f"grower id : {grower_id}, grower name : {grower_name}")

                        if storage_obj.exists(): 
                            print("exists")
                        else:
                            error_msg["storage"].append(f"storage id : {storage_id}, storage name : {storage_name}")
                            error_flag = True
                            
                        if field_obj.exists(): 
                            print("exists")
                        else:
                                error_msg["field"].append(f"field id : {field_id}, field name : {field_name}")
                                error_flag = True
                        try:
                            qnt_val = float(qnt)
                        except:
                            error_msg["qnt"].append(f"value : {qnt}")
                            error_flag = True
                        # print("error_flag",error_flag)    
                        if not error_flag :
                            if unit_id == "LBS" :
                                cal_quantity = round(float(qnt_val),2)
                            if unit_id == "BU" :
                                cal_quantity = round(float(qnt_val) * 45,2)
                            final_quantity = cal_quantity
                            check_final_qunt = StorageFeed.objects.filter(grower_id = grower_id,storage_id = storage_id)
                            # print("check_final_qunt",check_final_qunt)
                            
                            if check_final_qunt.exists():
                                check_final_qunt = check_final_qunt.last()
                                if str(status).lower() == "add" :
                                    final_quantity = round(float(check_final_qunt.final_quantity) + float(cal_quantity),2)
                                    save_feed_data = StorageFeed(grower_id = grower_id,crop=crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = qnt,quantity=cal_quantity,
                                        unit=unit_id,final_quantity=final_quantity,status="quantity_in",
                                        csv_file_id=get_csv_file.id,created_by_id=request.user.id)
                                    save_feed_data.save()
                                elif str(status).lower() == "remove" :
                                    final_quantity = round(float(check_final_qunt.final_quantity) - float(cal_quantity),2)
                                    save_feed_data = StorageFeed(grower_id = grower_id,crop=crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = qnt,quantity=cal_quantity,
                                        unit=unit_id,final_quantity=final_quantity,status="quantity_out",
                                        csv_file_id=get_csv_file.id,created_by_id=request.user.id,
                                        shipment_id=shp_ip)
                                    save_feed_data.save()
                                else:
                                    continue
                                # print("qnt",qnt)
                                # print("final_quantity",final_quantity)
                            else:
                                if str(status).lower() == "add" :
                                    # final_quantity = round(float(check_final_qunt.final_quantity) + float(cal_quantity),2)
                                    save_feed_data = StorageFeed(grower_id = grower_id,crop=crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = qnt,quantity=cal_quantity,
                                        unit=unit_id,final_quantity=qnt,status="quantity_in",
                                        csv_file_id=get_csv_file.id,created_by_id=request.user.id)
                                    save_feed_data.save()
                                elif str(status).lower() == "remove" :
                                    final_quantity = round(float(check_final_qunt.final_quantity) - float(cal_quantity),2)
                                    save_feed_data = StorageFeed(grower_id = grower_id,crop=crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = qnt,quantity=cal_quantity,
                                        unit=unit_id,final_quantity=final_quantity,status="quantity_out",
                                        csv_file_id=get_csv_file.id,created_by_id=request.user.id,
                                        shipment_id=shp_ip)
                                    save_feed_data.save()
                                else:
                                    continue
                    # For Error MSG .............
                    if not error_flag :
                        context["success_messages"] = "Csv File Uploaded Successfully."
                    else:
                        custom_error_msg = {key: value for key, value in error_msg.items() if value}
                        context["error_messages"] = custom_error_msg
            return render(request,"storage/assign_storage_feed_csv.html",context) 
        elif request.user.is_consultant:
            if request.method == "POST":
                csv_file = request.FILES.get("csv_file")
                if csv_file == None:
                    uploadcsv = 0
                else:
                    uploadcsv = pd.read_csv(csv_file).dropna(how='all')
                    # print(uploadcsv)
                    for i in range(len(uploadcsv)):
                        grower_name = uploadcsv.iloc[i, 0]
                        grower_id = uploadcsv.iloc[i, 1]
                        crop = uploadcsv.iloc[i, 2]
                        storage_name = uploadcsv.iloc[i, 3]
                        storage_id = uploadcsv.iloc[i, 4]
                        field_name = uploadcsv.iloc[i, 5]
                        field_id = uploadcsv.iloc[i, 6]
                        status  = uploadcsv.iloc[i, 7]
                        qnt  = uploadcsv.iloc[i, 8]
                        unit_id  = uploadcsv.iloc[i, 9]
                        shp_ip  = uploadcsv.iloc[i, 10]
                        # print("grower_name",grower_name)
                        # print("grower_id",grower_id)
                        grower_obj = Storage.objects.filter(grower_id=grower_id,grower__name__icontains=grower_name)
                        storage_obj = Storage.objects.filter(id=storage_id,storage_name__icontains=storage_name)
                        field_obj = Field.objects.filter(id=field_id,name__icontains=field_name,
                                                        grower_id=grower_id,grower__name__icontains=grower_name)
                        # print("grower_obj",grower_obj)
                        # print("storage_obj",storage_obj)
                        # print("field_obj",field_obj)
                        get_csv_file = StorageFeedCsv(csv_path=csv_file,upload_by_id=request.user.id)
                        get_csv_file.save()
                        error_flag = False
                        if grower_obj.exists(): 
                            print("exists")
                        else:
                            error_flag = True
                            error_msg["grower"].append(f"grower id : {grower_id}, grower name : {grower_name}")

                        if storage_obj.exists(): 
                            print("exists")
                        else:
                            error_msg["storage"].append(f"storage id : {storage_id}, storage name : {storage_name}")
                            error_flag = True
                            
                        if field_obj.exists(): 
                            print("exists")
                        else:
                            error_msg["field"].append(f"field id : {field_id}, field name : {field_name}")
                            error_flag = True
                        try:
                            qnt_val = float(qnt)
                        except:
                            error_msg["qnt"].append(f"value : {qnt}")
                            error_flag = True
                        # print("error_flag",error_flag) 
                        if not error_flag :
                            if unit_id == "LBS" :
                                cal_quantity = round(float(qnt_val),2)
                            if unit_id == "BU" :
                                cal_quantity = round(float(qnt_val) * 45,2)
                            final_quantity = cal_quantity
                            check_final_qunt = StorageFeed.objects.filter(grower_id = grower_id,storage_id = storage_id)
                            # print("check_final_qunt",check_final_qunt) 
                            if check_final_qunt.exists():
                                check_final_qunt = check_final_qunt.last()
                                if str(status).lower() == "add" :
                                    final_quantity = round(float(check_final_qunt.final_quantity) + float(cal_quantity),2)
                                    save_feed_data = StorageFeed(grower_id = grower_id,crop=crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = qnt,quantity=cal_quantity,
                                        unit=unit_id,final_quantity=final_quantity,status="quantity_in",
                                        csv_file_id=get_csv_file.id,created_by_id=request.user.id)
                                    save_feed_data.save()
                                elif str(status).lower() == "remove" :
                                    final_quantity = round(float(check_final_qunt.final_quantity) - float(cal_quantity),2)
                                    save_feed_data = StorageFeed(grower_id = grower_id,crop=crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = qnt,quantity=cal_quantity,
                                        unit=unit_id,final_quantity=final_quantity,status="quantity_out",
                                        csv_file_id=get_csv_file.id,created_by_id=request.user.id,
                                        shipment_id=shp_ip)
                                    save_feed_data.save()
                                else:
                                    continue  
                            else:
                                if str(status).lower() == "add" :
                                    # final_quantity = round(float(check_final_qunt.final_quantity) + float(cal_quantity),2)
                                    save_feed_data = StorageFeed(grower_id = grower_id,crop=crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = qnt,quantity=cal_quantity,
                                        unit=unit_id,final_quantity=qnt,status="quantity_in",
                                        csv_file_id=get_csv_file.id,created_by_id=request.user.id)
                                    save_feed_data.save()
                                elif str(status).lower() == "remove" :
                                    
                                    final_quantity = round(float(check_final_qunt.final_quantity) - float(cal_quantity),2)
                                    save_feed_data = StorageFeed(grower_id = grower_id,crop=crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = qnt,quantity=cal_quantity,
                                        unit=unit_id,final_quantity=final_quantity,status="quantity_out",
                                        csv_file_id=get_csv_file.id,created_by_id=request.user.id,
                                        shipment_id=shp_ip)
                                    save_feed_data.save()
                                
                                # if str(status).lower() == "add":
                                #     save_feed_data = StorageFeed(grower_id=grower_id, crop=crop, storage_id=storage_id,
                                #                                 field_id=field_id, quantity_raw=qnt, quantity=cal_quantity,
                                #                                 unit=unit_id, final_quantity=qnt, status="quantity_in",
                                #                                 csv_file_id=get_csv_file.id, created_by_id=request.user.id)
                                #     save_feed_data.save()
                                # elif str(status).lower() == "remove":
                                #     try:
                                #         final_quantity = round(float(check_final_qunt.final_quantity) - float(cal_quantity), 2)
                                #         save_feed_data = StorageFeed(grower_id=grower_id, crop=crop, storage_id=storage_id,
                                #                                     field_id=field_id, quantity_raw=qnt, quantity=cal_quantity,
                                #                                     unit=unit_id, final_quantity=final_quantity, status="quantity_out",
                                #                                     csv_file_id=get_csv_file.id, created_by_id=request.user.id,
                                #                                     shipment_id=shp_ip)
                                #         save_feed_data.save()
                                #     except AttributeError:  # check_final_qunt doesn't exist
                                #         context["error_messages"] = "remove not possible!!"
                                
                                else:
                                    continue   
                    # For Error MSG .............
                    if not error_flag :
                        context["success_messages"] = "Csv File Uploaded Successfully."
                    else:
                        custom_error_msg = {key: value for key, value in error_msg.items() if value}
                        context["error_messages"] = custom_error_msg
            return render(request,"storage/assign_storage_feed_csv.html",context) 
            # return render(request,"storage/assign_storage_feed_csv.html") 
        elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
            if request.method == "POST":
                csv_file = request.FILES.get("csv_file")
                if csv_file == None:
                    uploadcsv = 0
                else:
                    uploadcsv = pd.read_csv(csv_file).dropna(how='all')
                    for i in range(len(uploadcsv)):
                        grower_name = uploadcsv.iloc[i, 0]
                        grower_id = uploadcsv.iloc[i, 1]
                        crop = uploadcsv.iloc[i, 2]
                        storage_name = uploadcsv.iloc[i, 3]
                        storage_id = uploadcsv.iloc[i, 4]
                        field_name = uploadcsv.iloc[i, 5]
                        field_id = uploadcsv.iloc[i, 6]
                        status  = uploadcsv.iloc[i, 7]
                        qnt  = uploadcsv.iloc[i, 8]
                        unit_id  = uploadcsv.iloc[i, 9]
                        shp_ip  = uploadcsv.iloc[i, 10]
                        print("grower_name",grower_name)
                        print("grower_id",grower_id)
                        grower_obj = Storage.objects.filter(grower_id=grower_id,grower__name__icontains=grower_name)
                        storage_obj = Storage.objects.filter(id=storage_id,storage_name__icontains=storage_name)
                        field_obj = Field.objects.filter(id=field_id,name__icontains=field_name,
                                                        grower_id=grower_id,grower__name__icontains=grower_name)

                        get_csv_file = StorageFeedCsv(csv_path=csv_file,upload_by_id=request.user.id)
                        get_csv_file.save()
                        error_flag = False
                        if grower_obj.exists(): 
                            print("exists")
                        else:
                            error_flag = True
                            error_msg["grower"].append(f"grower id : {grower_id}, grower name : {grower_name}")

                        if storage_obj.exists(): 
                            print("exists")
                        else:
                            error_msg["storage"].append(f"storage id : {storage_id}, storage name : {storage_name}")
                            error_flag = True
                            
                        if field_obj.exists(): 
                            print("exists")
                        else:
                            error_msg["field"].append(f"field id : {field_id}, field name : {field_name}")
                            error_flag = True
                        try:
                            qnt_val = float(qnt)
                        except:
                            error_msg["qnt"].append(f"value : {qnt}")
                            error_flag = True
                        # print("error_flag",error_flag)    
                        if not error_flag :
                            if unit_id == "LBS" :
                                cal_quantity = round(float(qnt_val),2)
                            if unit_id == "BU" :
                                cal_quantity = round(float(qnt_val) * 45,2)
                            final_quantity = cal_quantity
                            check_final_qunt = StorageFeed.objects.filter(grower_id = grower_id,storage_id = storage_id)
                            # print("check_final_qunt",check_final_qunt)
                            
                            if check_final_qunt.exists():
                                check_final_qunt = check_final_qunt.last()
                                if str(status).lower() == "add" :
                                    final_quantity = round(float(check_final_qunt.final_quantity) + float(cal_quantity),2)
                                    save_feed_data = StorageFeed(grower_id = grower_id,crop=crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = qnt,quantity=cal_quantity,
                                        unit=unit_id,final_quantity=final_quantity,status="quantity_in",
                                        csv_file_id=get_csv_file.id,created_by_id=request.user.id)
                                    save_feed_data.save()
                                elif str(status).lower() == "remove" :
                                    final_quantity = round(float(check_final_qunt.final_quantity) - float(cal_quantity),2)
                                    save_feed_data = StorageFeed(grower_id = grower_id,crop=crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = qnt,quantity=cal_quantity,
                                        unit=unit_id,final_quantity=final_quantity,status="quantity_out",
                                        csv_file_id=get_csv_file.id,created_by_id=request.user.id,
                                        shipment_id=shp_ip)
                                    save_feed_data.save()
                                else:
                                    continue
                                # print("qnt",qnt)
                                # print("final_quantity",final_quantity)
                            else:
                                if str(status).lower() == "add" :
                                    # final_quantity = round(float(check_final_qunt.final_quantity) + float(cal_quantity),2)
                                    save_feed_data = StorageFeed(grower_id = grower_id,crop=crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = qnt,quantity=cal_quantity,
                                        unit=unit_id,final_quantity=qnt,status="quantity_in",
                                        csv_file_id=get_csv_file.id,created_by_id=request.user.id)
                                    save_feed_data.save()
                                elif str(status).lower() == "remove" :
                                    final_quantity = round(float(check_final_qunt.final_quantity) - float(cal_quantity),2)
                                    save_feed_data = StorageFeed(grower_id = grower_id,crop=crop,storage_id = storage_id,
                                        field_id = field_id,quantity_raw = qnt,quantity=cal_quantity,
                                        unit=unit_id,final_quantity=final_quantity,status="quantity_out",
                                        csv_file_id=get_csv_file.id,created_by_id=request.user.id,
                                        shipment_id=shp_ip)
                                    save_feed_data.save()
                                else:
                                    continue
                    # For Error MSG .............
                    if not error_flag :
                        context["success_messages"] = "Csv File Uploaded Successfully."
                    else:
                        custom_error_msg = {key: value for key, value in error_msg.items() if value}
                        context["error_messages"] = custom_error_msg
            return render(request,"storage/assign_storage_feed_csv.html",context)    
        else:
            return redirect('login')
    except Exception as e:
        messages = str(e)
        return render(request,"storage/assign_storage_feed_csv.html",context)      