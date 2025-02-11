from multiprocessing import context
from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from apps.grower.models import Consultant, Grower
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
# Create your views here.


def reverseTuple(lstOfTuple):
    return [tup[::-1] for tup in lstOfTuple]


def StorageCreateView(request):
    if request.user.is_authenticated:
    # Grower ................................
        if 'Grower' in request.user.get_role() and not request.user.is_superuser:
            form = StorageForm()
            context = {'form': form}
            grower_id = request.user.grower.id
            grower = Grower.objects.filter(id=int(grower_id))
            context['grower'] = grower

            if request.method == 'POST':
                context = {'form': form}
                name = request.POST.get('storage_name')
                storage_uniqueid = request.POST.get('storage_uniqueid')
                grower = int(request.POST.get('grower_id'))  # Getting grower id
                upload_type = request.POST.get('upload_type')

                if request.FILES.get('zip_file'):
                    form = StorageForm()
                    context = {'form': form}
                    name = request.POST.get('storage_name')
                    grower = Grower.objects.filter(id=int(grower_id))
                    context['grower'] = grower
                    storage_uniqueid = request.POST.get('storage_uniqueid')
                    grower_id = int(request.POST.get('grower_id'))
                    zip_file = request.FILES.get('zip_file')
                    strge = Storage(storage_name=name, storage_uniqueid=storage_uniqueid,
                            grower_id=grower_id, upload_type=upload_type, shapefile_id=zip_file)
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
                    latitude = request.POST.get('latitude')
                    longitude = request.POST.get('longitude')
                    grower_id = int(request.POST.get('grower_id'))
                    storage_id = Storage(storage_name=name, storage_uniqueid=storage_uniqueid, grower_id=grower_id,
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

            if request.method == 'POST':
                context = {'form': form}
                name = request.POST.get('storage_name')
                storage_uniqueid = request.POST.get('storage_uniqueid')
                grower = int(request.POST.get('grower_id'))  # Getting grower id
                upload_type = request.POST.get('upload_type')

                if request.FILES.get('zip_file'):
                    form = StorageForm()
                    context = {'form': form}
                    name = request.POST.get('storage_name')
                    grower = Grower.objects.filter(consultant=consultant_id)
                    context['grower'] = grower
                    storage_uniqueid = request.POST.get('storage_uniqueid')
                    grower_id = int(request.POST.get('grower_id'))
                    zip_file = request.FILES.get('zip_file')
                    Storage(storage_name=name, storage_uniqueid=storage_uniqueid,
                            grower_id=grower_id, upload_type=upload_type, shapefile_id=zip_file).save()
                    
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
                    latitude = request.POST.get('latitude')
                    longitude = request.POST.get('longitude')
                    grower_id = int(request.POST.get('grower_id'))
                    storage_id = Storage(storage_name=name, storage_uniqueid=storage_uniqueid, grower_id=grower_id,
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

            if request.method == 'POST':
                context = {'form': form}
                name = request.POST.get('storage_name')
                storage_uniqueid = request.POST.get('storage_uniqueid')
                grower = int(request.POST.get('grower_id'))  # Getting grower id
                upload_type = request.POST.get('upload_type')

                if request.FILES.get('zip_file'):
                    form = StorageForm()
                    context = {'form': form}
                    name = request.POST.get('storage_name')
                    grower = Grower.objects.all().order_by('name')
                    context['grower'] = grower
                    storage_uniqueid = request.POST.get('storage_uniqueid')
                    grower_id = int(request.POST.get('grower_id'))
                    uploaded_file = request.FILES.get('zip_file')
                    
                    Storage(storage_name=name, storage_uniqueid=storage_uniqueid,
                            grower_id=grower_id, upload_type=upload_type, shapefile_id=uploaded_file).save()
                    
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
                    latitude = request.POST.get('latitude')
                    longitude = request.POST.get('longitude')
                    grower_id = int(request.POST.get('grower_id'))
                    storage_id = Storage(storage_name=name, storage_uniqueid=storage_uniqueid, grower_id=grower_id,
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
                    # return render(request,'storage/storage_create.html',context)
                    # storage_id = Storage.objects.get(storage_uniqueid=storage_uniqueid)                       
                    # print(storage_id)
                    return redirect('storage-list')

                return render(request, 'storage/storage_create.html', context)

            return render(request, 'storage/storage_create.html', context)

    else:
        return redirect('login')

def StorageListView(request):
    if request.user.is_authenticated:
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
        elif request.user.is_consultant:
            consultant_id = Consultant.objects.get(email=request.user.email).id
            growers = Grower.objects.filter(consultant=consultant_id)
            context = {'growers': growers}
            grower_ids = [data.id for data in growers]
            storage = Storage.objects.filter(grower_id__in=grower_ids).order_by('id')
            context['storage'] = storage

            if request.POST.get('growerSelction'):
                grower_id = int(request.POST.get('growerSelction'))
                if grower_id != 0:
                    context['selectedGrower'] = Grower.objects.get(
                        pk=grower_id)
                    storage = Storage.objects.filter(grower_id=grower_id).order_by('id')
                    context['storage'] = storage
                    return render(request, 'storage/storage_list.html', context)

            if request.POST.get('storage_name'):
                storage_name = request.POST.get('storage_name')
                storage = Storage.objects.filter(storage_name__icontains=storage_name).filter(grower__in=grower_ids).order_by('id')
                context = {'storage': storage}
                growers = Grower.objects.filter(consultant=consultant_id)
                context['growers'] = growers
                return render(request, 'storage/storage_list.html', context)
        
            if request.POST.get('storage_id'):
                    storage_id = request.POST.get('storage_id')
                    storage = Storage.objects.filter(storage_uniqueid__icontains=storage_id).filter(grower__in=grower_ids).order_by('id')
                    context = {'storage': storage}
                    growers = Grower.objects.filter(consultant=consultant_id)
                    context['growers'] = growers
                    return render(request, 'storage/storage_list.html', context)
            
            return render(request, 'storage/storage_list.html', context)
            # superadmin and others ................
        elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():

            id = request.user.id

            storage = Storage.objects.all().order_by('id')
            context = {'storage': storage}
            growers = Grower.objects.all().order_by('name')
            context['growers'] = growers
            if request.POST.get('growerSelction'):
                grower_id = int(request.POST.get('growerSelction'))
                if grower_id != 0:
                    context['selectedGrower'] = Grower.objects.get(
                        pk=grower_id)
                    storage = Storage.objects.filter(grower_id=grower_id).order_by('id')
                    context['storage'] = storage
                    return render(request, 'storage/storage_list.html', context)
            if request.POST.get('storage_name'):
                storage_name = request.POST.get('storage_name')
                storage = Storage.objects.filter(
                    storage_name__icontains=storage_name).order_by('id')
                context = {'storage': storage}
                growers = Grower.objects.all().order_by('name')
                context['growers'] = growers
                return render(request, 'storage/storage_list.html', context)
            # if request.POST.get('storage_name_all'):
            #     storage = Storage.objects.all()
            #     context = {'storage': storage}
            #     growers = Grower.objects.all().order_by('name')
            #     context['growers'] = growers
            #     return render(request, 'storage/storage_list.html', context)
            if request.POST.get('storage_id'):
                storage_id = request.POST.get('storage_id')
                storage = Storage.objects.filter(
                    storage_uniqueid__icontains=storage_id).order_by('id')
                context = {'storage': storage}
                growers = Grower.objects.all().order_by('name')
                context['growers'] = growers
                return render(request, 'storage/storage_list.html', context)
            return render(request, 'storage/storage_list.html', context)
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
