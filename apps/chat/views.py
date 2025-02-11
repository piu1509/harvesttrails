from django.shortcuts import render, HttpResponse, redirect
from apps.processor.models import *
from apps.processor2.models import *
from apps.warehouseManagement.models import *
from apps.grower.models import *
from apps.chat.models import ProcessorMsgboard, ProcessorMessage
from apps.accounts.models import User
from django.http import JsonResponse
from datetime import datetime, date, timedelta
from django.contrib.auth.decorators import login_required

# Create your views here.

def check_GrowerMsgboard(grower_id,chat_with,reciver_id):
  all_board = ProcessorMsgboard.objects.filter(grower_id=grower_id)
  board_id,name,last_msg,unread_count,last_unread_msg_time  = "","","", 0, ""
  if chat_with == "Grower-Consultant" :
    check_G_C = all_board.filter(chat_with=chat_with,consultant_id=reciver_id)
    if check_G_C.exists():
        get_G_C = check_G_C.first()
        board_id = get_G_C.id
        name = f"{get_G_C.consultant.name} [Consultant]"
        msg_G_C = ProcessorMessage.objects.filter(board_id=board_id)
        if msg_G_C.exists():
          unread_msg = msg_G_C.filter(receiver_id=grower_id,read_status="UNREAD")
          unread_count = unread_msg.count()
          last_msg_obj = msg_G_C.last()
          last_msg = f'{last_msg_obj.msg[:20]}...' if len(last_msg_obj.msg) > 20 else last_msg_obj.msg
          last_unread_msg_time = f"{last_msg_obj.msg_date} {last_msg_obj.msg_time}" if last_msg_obj else ""
    else:
      get_G_C = ProcessorMsgboard(grower_id=grower_id,consultant_id=reciver_id,chat_with="Grower-Consultant")
      get_G_C.save()
      board_id = get_G_C.id
      name = f"{get_G_C.consultant.name} [Consultant]"
  elif chat_with == "Grower-Processor" :
    check_G_P = all_board.filter(chat_with=chat_with,processor_id=reciver_id)
    if check_G_P.exists():
        get_G_P = check_G_P.first()
        board_id = get_G_P.id
        name = f"{get_G_P.processor.entity_name} [Processor]"
        msg_G_P = ProcessorMessage.objects.filter(board_id=board_id)
        if msg_G_P.exists():
          unread_msg = msg_G_P.filter(receiver_id=grower_id,read_status="UNREAD")
          unread_count = unread_msg.count()
          last_msg_obj = msg_G_P.last()
          last_msg = f'{last_msg_obj.msg[:20]}...' if len(last_msg_obj.msg) > 20 else last_msg_obj.msg
          last_unread_msg_time = f"{last_msg_obj.msg_date} {last_msg_obj.msg_time}" if last_msg_obj else ""
    else:
      get_G_P = ProcessorMsgboard(grower_id=grower_id,processor_id=reciver_id,chat_with="Grower-Consultant")
      get_G_P.save()
      board_id = get_G_P.id
      name = f"{get_G_P.processor.entity_name} [Processor]"
  elif chat_with == "Grower-Admin" :
    check_G_A = all_board.filter(chat_with=chat_with,admin_id=reciver_id)
    if check_G_A.exists():
      get_G_A = check_G_A.first()
      board_id = get_G_A.id
      msg_G_P = ProcessorMessage.objects.filter(board_id=board_id)
      if get_G_A.admin.is_superuser :
        name = f"{get_G_A.admin.full_name()} [MainAdmin]"
      else:
        name = f"{get_G_A.admin.full_name()} {get_G_A.admin.get_role()}"
      if msg_G_P.exists():
        unread_msg = msg_G_P.filter(receiver_id=grower_id,read_status="UNREAD")
        unread_count = unread_msg.count()
        last_unread_msg_time = f"{unread_msg.last().msg_date} {unread_msg.last().msg_time}" if unread_msg.exists() else ""
        last_msg_obj = msg_G_P.last()
        last_msg = f'{last_msg_obj.msg[:20]}...' if len(last_msg_obj.msg) > 20 else last_msg_obj.msg
        last_unread_msg_time = f"{last_msg_obj.msg_date} {last_msg_obj.msg_time}" if last_msg_obj else ""
    else:
      get_G_A = ProcessorMsgboard(grower_id=grower_id,admin_id=reciver_id,chat_with="Grower-Admin")
      get_G_A.save()
      board_id = get_G_A.id
      if reciver_id == 1 :
        name = f"{get_G_A.admin.full_name()} [MainAdmin]"
      else:
        name = f"{get_G_A.admin.full_name()} [Admin]"
  return ({"id":board_id,"name":name,"last_msg":last_msg,"unread_count":unread_count,"last_unread_msg_time":last_unread_msg_time})

def check_ProcessorMsgboard(p_id,chat_with,reciver_id):
  board_id,name,last_msg,unread_count,last_unread_msg_time  = "","","",0,""
  all_board = ProcessorMsgboard.objects.filter(processor_id=p_id)
  if chat_with == "Grower-Processor" :
    check_G_P = all_board.filter(chat_with=chat_with,grower_id=reciver_id)
    if check_G_P.exists():
        get_G_P = check_G_P.first()
        board_id = get_G_P.id
        name = f"{get_G_P.grower.name} [Grower]"
        msg_G_P = ProcessorMessage.objects.filter(board_id=board_id).order_by("id")
        # 
        if msg_G_P.exists():
          unread_count = msg_G_P.filter(receiver_id=p_id,read_status="UNREAD").count()
          last_msg_obj = msg_G_P.last()
          # last_msg = f"{last_msg_G_P.msg}"
          # last_msg = f'{last_msg[:20]}...' if len(last_msg) > 20 else last_msg 
          last_msg = f'{last_msg_obj.msg[:20]}...' if len(last_msg_obj.msg) > 20 else last_msg_obj.msg
          last_unread_msg_time = f"{last_msg_obj.msg_date} {last_msg_obj.msg_time}" if last_msg_obj else ""
          
    else:
      get_G_P = ProcessorMsgboard(grower_id=reciver_id,processor_id=p_id,chat_with="Grower-Processor")
      get_G_P.save()
      board_id = get_G_P.id
      name = f"{get_G_P.grower.name} [Grower]"
  return ({"id":board_id,"name":name,"last_msg":last_msg,"unread_count":unread_count,"last_unread_msg_time":last_unread_msg_time})

def check_AdminMsgboard(user_id,chat_with,reciver_id):
  board_id,name,last_msg,unread_count,last_unread_msg_time  = "","","",0,""
  check_G_A = ProcessorMsgboard.objects.filter(admin_id=user_id,grower_id=reciver_id,chat_with="Grower-Admin")
  if check_G_A.exists():
    get_G_A = check_G_A.first()
    board_id = get_G_A.id
    name = f"{get_G_A.grower.name} [Grower]"
    msg_G_A = ProcessorMessage.objects.filter(board_id=board_id).order_by("id")
    
    if msg_G_A.exists():
      unread_count = msg_G_A.filter(receiver_id=user_id,read_status="UNREAD").count()
      last_msg_obj = msg_G_A.last()
      last_msg = f'{last_msg_obj.msg[:20]}...' if len(last_msg_obj.msg) > 20 else last_msg_obj.msg
      last_unread_msg_time = f"{last_msg_obj.msg_date} {last_msg_obj.msg_time}" if last_msg_obj else "" 
  else:
    get_G_A = ProcessorMsgboard(grower_id=reciver_id,admin_id=user_id,chat_with="Grower-Admin")
    get_G_A.save()
    board_id = get_G_A.id
    name = f"{get_G_A.grower.name} [Grower]"
  return ({"id":board_id,"name":name,"last_msg":last_msg,"unread_count":unread_count,"last_unread_msg_time":last_unread_msg_time})
  
def check_ConsultantMsgboard(consultant_id,chat_with,reciver_id):
  board_id,name,last_msg,unread_count,last_unread_msg_time  = "","","",0,""
  check_G_C = ProcessorMsgboard.objects.filter(consultant_id=consultant_id,grower_id=reciver_id,chat_with="Grower-Consultant")
  if check_G_C.exists():
    get_G_C = check_G_C.first()
    board_id = get_G_C.id
    name = f"{get_G_C.grower.name} [Grower]"
    msg_G_C = ProcessorMessage.objects.filter(board_id=board_id).order_by("id")
    
    if msg_G_C.exists():
      unread_count = msg_G_C.filter(receiver_id=consultant_id,read_status="UNREAD").count()
      last_msg_obj = msg_G_C.last()
      last_msg = f'{last_msg_obj.msg[:20]}...' if len(last_msg_obj.msg) > 20 else last_msg_obj.msg
      last_unread_msg_time = f"{last_msg_obj.msg_date} {last_msg_obj.msg_time}" if last_msg_obj else "" 
  else:
    get_G_C = ProcessorMsgboard(grower_id=reciver_id,consultant_id=consultant_id,chat_with="Grower-Consultant")
    get_G_C.save()
    board_id = get_G_C.id
    name = f"{get_G_C.grower.name} [Grower]"
  return ({"id":board_id,"name":name,"last_msg":last_msg,"unread_count":unread_count,"last_unread_msg_time":last_unread_msg_time})



login_required()
def chat_ag(request):
  context = {}
  if request.user.is_processor :
    user_email = request.user.email
    receiver = []
    ### ...................
    if request.method == "POST":
      get_reciver = request.POST.get('get_reciver')
      if get_reciver and len(get_reciver) != 0 :
        return redirect ('chatroom_ag', pk=int(get_reciver))
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor = Processor.objects.get(id=p.processor_id)
    processor_grower_obj = LinkGrowerToProcessor.objects.filter(processor_id=processor.id)
    grower_id_all= [i.grower_id for i in processor_grower_obj]
    grower = Grower.objects.filter(id__in=grower_id_all).order_by("name")
    for i in grower :
      receiver.append(check_ProcessorMsgboard(processor.id,"Grower-Processor",i.id))

    sorted_data = sorted(receiver, key=lambda x: x['unread_count'], reverse=True)
    ordered_list = sorted(sorted_data, key=lambda x: x['last_unread_msg_time'], reverse=True)
    context['receiver'] = ordered_list
  elif 'Grower' in request.user.get_role() and not request.user.is_superuser:
    grower_id= request.user.grower.id
    receiver = []
    ### ...................
    if request.method == "POST":
      get_reciver = request.POST.get('get_reciver')
      if get_reciver and len(get_reciver) != 0 :
        return redirect ('chatroom_ag', pk=int(get_reciver))
    ### ...................
    ### Processor name
    processor_grower_obj = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).values("processor_id")
    processor_id = [i['processor_id'] for i in processor_grower_obj]
    get_processor = Processor.objects.filter(id__in=processor_id)
    for i in get_processor :
      receiver.append(check_GrowerMsgboard(grower_id,"Grower-Processor",i.id))
    ### Consuntalt name
    consultant_obj = Grower.objects.filter(id=grower_id).values("consultant__id")
    consultant_id = [i['consultant__id'] for i in consultant_obj]
    get_consultant = Consultant.objects.filter(id__in=consultant_id)
    for i in get_consultant :
      receiver.append(check_GrowerMsgboard(grower_id,"Grower-Consultant",i.id))
    ### Admin name
    admin_obj1 = list(User.objects.filter(is_superuser=True).order_by("first_name").values("id"))
    admin_obj2 = list(User.objects.filter(role__role__in=['SuperUser']).order_by("first_name").values("id"))
    admin_obj3 = list(User.objects.filter(role__role__in=['SubAdmin']).order_by("first_name").values("id"))
    
    admin_obj = admin_obj1 + admin_obj2 + admin_obj3
    for i in admin_obj :
      print(i['id'])
      receiver.append(check_GrowerMsgboard(grower_id,"Grower-Admin",i['id']))  
    
    
    sorted_data = sorted(receiver, key=lambda x: x['unread_count'], reverse=True)
    ordered_list = sorted(sorted_data, key=lambda x: x['last_unread_msg_time'], reverse=True)
    context['receiver'] = ordered_list

  elif request.user.is_consultant:
    receiver = []
    user_id= request.user.id
    user_email= request.user.email
    get_user = User.objects.get(id=user_id)
    consultant = Consultant.objects.filter(email=user_email)
    if consultant.exists() :
      ### ...................
      if request.method == "POST":
        get_reciver = request.POST.get('get_reciver')
        if get_reciver and len(get_reciver) != 0 :
          return redirect ('chatroom_ag', pk=int(get_reciver))
      ### ...................
      all_grower = Grower.objects.filter(consultant__id=consultant.first().id).order_by("name").values("id","consultant__id")
      for i in all_grower :
        receiver.append(check_ConsultantMsgboard(i["consultant__id"],"Grower-Consultant",i["id"]))
      
      sorted_data = sorted(receiver, key=lambda x: x['unread_count'], reverse=True)
      ordered_list = sorted(sorted_data, key=lambda x: x['last_unread_msg_time'], reverse=True)
      context['receiver'] = ordered_list
      
  elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
    user_id= request.user.id
    get_user = User.objects.get(id=user_id)
    receiver = []
    ### ...................
    if request.method == "POST":
      get_reciver = request.POST.get('get_reciver')
      if get_reciver and len(get_reciver) != 0 :
        return redirect ('chatroom_ag', pk=int(get_reciver))
    ### Grower name
    grower_obj = Grower.objects.all().order_by("name").values("id")
    for i in grower_obj :
      receiver.append(check_AdminMsgboard(user_id,"Grower-Admin",i['id']))
    
    sorted_data = sorted(receiver, key=lambda x: x['unread_count'], reverse=True)
    ordered_list = sorted(sorted_data, key=lambda x: x['last_unread_msg_time'], reverse=True)
    context['receiver'] = ordered_list
  return render(request, 'chat/messageboard.html',context)

login_required()
def chatroom_ag(request,pk):
  context = {}
  if request.user.is_processor :
    user_email = request.user.email
    receiver = []
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor = Processor.objects.get(id=p.processor_id)
    processor_id = processor.id
    check_room = ProcessorMsgboard.objects.filter(id=pk,processor_id=processor_id)
    
    if not check_room.exists():
      return redirect ('chat_ag')
    
    processor_grower_obj = LinkGrowerToProcessor.objects.filter(processor_id=processor_id)
    grower_id_all= [i.grower_id for i in processor_grower_obj]
    grower = Grower.objects.filter(id__in=grower_id_all).order_by("name")
    for i in grower :
      receiver.append(check_ProcessorMsgboard(processor_id,"Grower-Processor",i.id))
    
    for i in receiver :
        if i["id"] == pk :
          context['selected_reciver'] = i
          db_message = ProcessorMessage.objects.filter(board_id=i["id"]).order_by("id")
          all_db_message = []
          for j in db_message :
            if j.sender_is == 'processor' :
              classs = "my_message"
            else :
              classs = "client_message"
              cheang_status = ProcessorMessage.objects.get(id=j.id)
              cheang_status.read_status = "READ"
              cheang_status.save()
            all_db_message.append({"msg":j.msg,"classs":classs,"msg_date":j.msg_date,"msg_time":j.msg_time})

          context['all_db_message'] = all_db_message

    sorted_data = sorted(receiver, key=lambda x: x['unread_count'], reverse=True)
    ordered_list = sorted(sorted_data, key=lambda x: x['last_unread_msg_time'], reverse=True)
    context['receiver'] = ordered_list
    context['chat_with'] = check_room.first().chat_with
  elif 'Grower' in request.user.get_role() and not request.user.is_superuser :
    grower_id= request.user.grower.id
    receiver = []
    # ...............................
    check_room = ProcessorMsgboard.objects.filter(id=pk,grower_id=grower_id)
    if not check_room.exists():
      return redirect ('chat_ag')
    # ...............................
    ### processor name
    processor_grower_obj = LinkGrowerToProcessor.objects.filter(grower_id=grower_id).values("processor_id")
    processor_id = [i['processor_id'] for i in processor_grower_obj]
    get_processor = Processor.objects.filter(id__in=processor_id)
    for i in get_processor :
      receiver.append(check_GrowerMsgboard(grower_id,"Grower-Processor",i.id))
    
    ### consuntalt name
    consultant_obj = Grower.objects.filter(id=grower_id).values("consultant__id")
    consultant_id = [i['consultant__id'] for i in consultant_obj]
    get_consultant = Consultant.objects.filter(id__in=consultant_id)
    for i in get_consultant :
      receiver.append(check_GrowerMsgboard(grower_id,"Grower-Consultant",i.id))
      
    ### Admin name
    # admin_obj = User.objects.filter(role__role__in=['SubAdmin','SuperUser'],is_superuser=True).order_by("first_name").values("id")
    admin_obj1 = list(User.objects.filter(is_superuser=True).order_by("first_name").values("id"))
    admin_obj2 = list(User.objects.filter(role__role__in=['SuperUser']).order_by("first_name").values("id"))
    admin_obj3 = list(User.objects.filter(role__role__in=['SubAdmin']).order_by("first_name").values("id"))
    
    admin_obj = admin_obj1 + admin_obj2 + admin_obj3
    for i in admin_obj :
      receiver.append(check_GrowerMsgboard(grower_id,"Grower-Admin",i['id']))    
    # ...............................
    for i in receiver :
        if i["id"] == pk :
          context['selected_reciver'] = i
          db_message = ProcessorMessage.objects.filter(board_id=i["id"]).order_by("id")
          all_db_message = []
          for j in db_message :
            if j.receiver_is == 'grower' :
              classs = "client_message"
              cheang_status = ProcessorMessage.objects.get(id=j.id)
              cheang_status.read_status = "READ"
              cheang_status.save()
            else :
              classs = "my_message"
              
            all_db_message.append({"msg":j.msg,"classs":classs,"msg_date":j.msg_date,"msg_time":j.msg_time})
            
            all_db_message.append({"message":j.msg})
          context['all_db_message'] = all_db_message
    # ...............................
    sorted_data = sorted(receiver, key=lambda x: x['unread_count'], reverse=True)
    ordered_list = sorted(sorted_data, key=lambda x: x['last_unread_msg_time'], reverse=True)
    context['receiver'] = ordered_list
    context['chat_with'] = check_room.first().chat_with
  elif request.user.is_consultant:
    receiver = []
    user_id= request.user.id
    user_email= request.user.email
    get_user = User.objects.get(id=user_id)
    consultant = Consultant.objects.filter(email=user_email)
    if consultant.exists() :
      # ...............................
      check_room = ProcessorMsgboard.objects.filter(id=pk,consultant_id=consultant.first().id,chat_with="Grower-Consultant")
      if not check_room.exists():
        return redirect ('chat_ag')
      # ...............................
      all_grower = Grower.objects.filter(consultant__id=consultant.first().id).order_by("name").values("id","consultant__id")
      for i in all_grower :
        receiver.append(check_ConsultantMsgboard(i["consultant__id"],"Grower-Consultant",i["id"]))
      
      # ...............................
      for i in receiver :
        if i["id"] == pk :
          context['selected_reciver'] = i
          db_message = ProcessorMessage.objects.filter(board_id=i["id"]).order_by("id")
          all_db_message = []
          for j in db_message :
            if j.receiver_is == 'consultant' :
              classs = "client_message"
              cheang_status = ProcessorMessage.objects.get(id=j.id)
              cheang_status.read_status = "READ"
              cheang_status.save()
            else :
              classs = "my_message"
            all_db_message.append({"msg":j.msg,"classs":classs,"msg_date":j.msg_date,"msg_time":j.msg_time})
          context['all_db_message'] = all_db_message
      
      sorted_data = sorted(receiver, key=lambda x: x['unread_count'], reverse=True)
      ordered_list = sorted(sorted_data, key=lambda x: x['last_unread_msg_time'], reverse=True)
      context['receiver'] = ordered_list
      context['chat_with'] = check_room.first().chat_with
  elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role():
    user_id= request.user.id
    get_user = User.objects.get(id=user_id)
    receiver = []
    check_room = ProcessorMsgboard.objects.filter(id=pk,admin_id=user_id)
    if not check_room.exists():
      return redirect ('chat_ag')
    ### Grower name
    grower_obj = Grower.objects.all().order_by("name").values("id")
    for i in grower_obj :
      receiver.append(check_AdminMsgboard(user_id,"Grower-Admin",i['id']))
    
    # ...............................
    for i in receiver :
      if i["id"] == pk :
        context['selected_reciver'] = i
        db_message = ProcessorMessage.objects.filter(board_id=i["id"]).order_by("id")
        all_db_message = []
        for j in db_message :
          if j.receiver_is == 'admin' :
            classs = "client_message"
            cheang_status = ProcessorMessage.objects.get(id=j.id)
            cheang_status.read_status = "READ"
            cheang_status.save()
          else :
            classs = "my_message"
          all_db_message.append({"msg":j.msg,"classs":classs,"msg_date":j.msg_date,"msg_time":j.msg_time})

        context['all_db_message'] = all_db_message
    sorted_data = sorted(receiver, key=lambda x: x['unread_count'], reverse=True)
    ordered_list = sorted(sorted_data, key=lambda x: x['last_unread_msg_time'], reverse=True)
    context['receiver'] = ordered_list
    context['chat_with'] = check_room.first().chat_with
  return render(request, 'chat/messageboard_room.html',context)

login_required()
def save_msg(request,user_id,main_id,chat_with,sender,roomName,message):
  read_status = "UNREAD"
  if sender == 'Consultant' and chat_with == "Grower-Consultant" :      
    main_board = ProcessorMsgboard.objects.filter(chat_with=chat_with,id=main_id)
    receiver_obj = main_board.first()
    sender_is = "consultant"
    sender_id = receiver_obj.consultant.id
    sender_name = receiver_obj.consultant.name
    receiver = "grower"
    receiver_id = receiver_obj.grower.id 
    receiver_name = receiver_obj.grower.name
    save_msg = ProcessorMessage(board_id=main_id,sender_is=sender_is,sender_id=sender_id,sender_name=sender_name,
                      receiver_is=receiver,receiver_id=receiver_id,receiver_name=receiver_name,msg=message,
                      read_status = read_status)
    save_msg.save() 
  elif sender == 'Admin':
    sender_is = "admin"
    sender_id = request.user.id
    sender_name = request.user.full_name()
    if chat_with == "Grower-Admin":
      receiver = "grower"
      main_board = ProcessorMsgboard.objects.filter(chat_with=chat_with,id=main_id)
      receiver_obj = main_board.first()
      receiver_id = receiver_obj.grower.id 
      receiver_name = receiver_obj.grower.name
      save_msg = ProcessorMessage(board_id=main_id,sender_is=sender_is,sender_id=sender_id,sender_name=sender_name,
                       receiver_is=receiver,receiver_id=receiver_id,receiver_name=receiver_name,msg=message,
                       read_status = read_status)
      save_msg.save() 
  elif sender == "Grower":
    sender_is = "grower"
    sender_id = request.user.grower.id
    sender_name = request.user.grower.name
    if chat_with == "Grower-Consultant":
      receiver = "consultant"
      main_board = ProcessorMsgboard.objects.filter(chat_with=chat_with,id=main_id)
      receiver_obj = main_board.first()
      receiver_id = receiver_obj.consultant.id 
      receiver_name = receiver_obj.consultant.name 
      save_msg = ProcessorMessage(board_id=main_id,sender_is=sender_is,sender_id=sender_id,sender_name=sender_name,
                       receiver_is=receiver,receiver_id=receiver_id,receiver_name=receiver_name,msg=message,
                       read_status = read_status)
      save_msg.save()
    if chat_with == "Grower-Admin":
      receiver = "admin"
      main_board = ProcessorMsgboard.objects.filter(chat_with=chat_with,id=main_id)
      receiver_obj = main_board.first()
      receiver_id = receiver_obj.admin.id 
      receiver_name = receiver_obj.admin.full_name() 
      save_msg = ProcessorMessage(board_id=main_id,sender_is=sender_is,sender_id=sender_id,sender_name=sender_name,
                       receiver_is=receiver,receiver_id=receiver_id,receiver_name=receiver_name,msg=message,
                       read_status = read_status)
      save_msg.save()
      
    elif chat_with == "Grower-Processor":
      receiver = "processor"
      main_board = ProcessorMsgboard.objects.filter(chat_with=chat_with,id=main_id)
      receiver_obj = main_board.first()
      receiver_id = receiver_obj.processor.id 
      receiver_name = receiver_obj.processor.entity_name
      save_msg = ProcessorMessage(board_id=main_id,sender_is=sender_is,sender_id=sender_id,sender_name=sender_name,
                       receiver_is=receiver,receiver_id=receiver_id,receiver_name=receiver_name,msg=message,
                       read_status = read_status)
      save_msg.save()
  elif sender == "Processor" and chat_with == "Grower-Processor" :
    receiver = "grower"
    sender_is = "processor"
    main_board = ProcessorMsgboard.objects.filter(chat_with=chat_with,id=main_id)
    receiver_obj = main_board.first()
    receiver_id = receiver_obj.grower.id 
    receiver_name = receiver_obj.grower.name 
    sender_id = receiver_obj.processor.id
    sender_name = receiver_obj.processor.entity_name
    save_msg = ProcessorMessage(board_id=main_id,sender_is=sender_is,sender_id=sender_id,sender_name=sender_name,
                      receiver_is=receiver,receiver_id=receiver_id,receiver_name=receiver_name,msg=message,
                      read_status = read_status)
    save_msg.save()
  
  return HttpResponse(1)


# Main Chat live chat section
login_required()
def get_msg(request,user_id,roomName,chat_with,get_msg_reciver):
  msg_time = ""
  msg_date = ""
  msg = ""
  
  # import time
  # time.sleep(5)
  try:
    if get_msg_reciver == "Consultant":
      get_msgg = ProcessorMessage.objects.filter(board_id=roomName,receiver_is="consultant",read_status="UNREAD")
      if get_msgg.exists():
        get_msgg = get_msgg.last()
        msg = get_msgg.msg 
        
        msg_datetime = datetime.combine(get_msgg.msg_date, datetime.min.time())
        msg_date = msg_datetime.strftime("%b %d %Y")
        
        msg_timedelta = datetime.strptime(f'{get_msgg.msg_time}', '%H:%M:%S.%f').time()
        base_date = datetime(2000, 1, 1)
        msg_datetime = datetime.combine(base_date, msg_timedelta)
        msg_time = msg_datetime.strftime("%I:%M %p")
        
        get_msgg.read_status = "READ"
        get_msgg.save()
    elif get_msg_reciver == "Admin":
      get_msgg = ProcessorMessage.objects.filter(board_id=roomName,receiver_is="admin",read_status="UNREAD")
      if get_msgg.exists():
        get_msgg = get_msgg.last()
        msg = get_msgg.msg 
        
        msg_datetime = datetime.combine(get_msgg.msg_date, datetime.min.time())
        msg_date = msg_datetime.strftime("%b %d %Y")
        
        msg_timedelta = datetime.strptime(f'{get_msgg.msg_time}', '%H:%M:%S.%f').time()
        base_date = datetime(2000, 1, 1)
        msg_datetime = datetime.combine(base_date, msg_timedelta)
        msg_time = msg_datetime.strftime("%I:%M %p")
        
        get_msgg.read_status = "READ"
        get_msgg.save()
        
    elif get_msg_reciver == "Processor":
      get_msgg = ProcessorMessage.objects.filter(board_id=roomName,receiver_is="processor",read_status="UNREAD")
      if get_msgg.exists():
        get_msgg = get_msgg.last()
        msg = get_msgg.msg 
            
        msg_datetime = datetime.combine(get_msgg.msg_date, datetime.min.time())
        msg_date = msg_datetime.strftime("%b %d %Y")
        
        msg_timedelta = datetime.strptime(f'{get_msgg.msg_time}', '%H:%M:%S.%f').time()
        base_date = datetime(2000, 1, 1)
        msg_datetime = datetime.combine(base_date, msg_timedelta)
        msg_time = msg_datetime.strftime("%I:%M %p")
        
        get_msgg.read_status = "READ"
        get_msgg.save()
        
    elif get_msg_reciver == "Grower":
      get_msgg = ProcessorMessage.objects.filter(board_id=roomName,receiver_is="grower",read_status="UNREAD")
      if get_msgg.exists():
        get_msgg = get_msgg.last()
        msg = get_msgg.msg
        
        msg_datetime = datetime.combine(get_msgg.msg_date, datetime.min.time())
        msg_date = msg_datetime.strftime("%b %d %Y")
        
        msg_datetime = datetime.combine(get_msgg.msg_date, datetime.min.time())
        msg_date = msg_datetime.strftime("%b %d %Y")
        msg_timedelta = datetime.strptime(f'{get_msgg.msg_time}', '%H:%M:%S.%f').time()
        base_date = datetime(2000, 1, 1)
        msg_datetime = datetime.combine(base_date, msg_timedelta)
        msg_time = msg_datetime.strftime("%I:%M %p")
        
        get_msgg.read_status = "READ"
        get_msgg.save()
    
    return JsonResponse({'msg':msg,'msg_date':msg_date,'msg_time':msg_time})
  except:
    pass 
  return HttpResponse(1)


# Main Chat section counter
login_required()
def ajax_msg_board(request,user_id):
  # receiver_id == room_id
  lst =[] 
  if 'Grower' in request.user.get_role() and not request.user.is_superuser :
    g_id = request.user.grower.id
    get_msg = ProcessorMessage.objects.filter(receiver_id=g_id,read_status="UNREAD")
    for i in get_msg:
      unread_count = len(get_msg.filter(board_id= i.board.id))
      lst_msg_obj = str(i.msg)
      lst_msg_obj = f'{lst_msg_obj[:20]}...' if len(lst_msg_obj) > 20 else lst_msg_obj
      lst.append({"receiver_id":i.board.id,"lst_msg_obj":lst_msg_obj,"unread_count":unread_count})
    
  elif request.user.is_processor :
    user_email = request.user.email
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor = Processor.objects.get(id=p.processor_id)
    processor_id = processor.id
    get_msg = ProcessorMessage.objects.filter(receiver_id=processor_id,read_status="UNREAD")
    for i in get_msg:
      unread_count = len(get_msg.filter(board_id= i.board.id))
      lst_msg_obj = str(i.msg)
      lst_msg_obj = f'{lst_msg_obj[:20]}...' if len(lst_msg_obj) > 20 else lst_msg_obj
      lst.append({"receiver_id":i.board.id,"lst_msg_obj":lst_msg_obj,"unread_count":unread_count})
    
  elif request.user.is_consultant :
    user_email = request.user.email
    consultant = Consultant.objects.filter(email=user_email)
    if consultant.exists():
      consultant = consultant.first()
      consultant_id = consultant.id
      get_msg = ProcessorMessage.objects.filter(receiver_id=consultant_id,read_status="UNREAD")
      for i in get_msg:
        unread_count = len(get_msg.filter(board_id= i.board.id))
        lst_msg_obj = str(i.msg)
        lst_msg_obj = f'{lst_msg_obj[:20]}...' if len(lst_msg_obj) > 20 else lst_msg_obj
        lst.append({"receiver_id":i.board.id,"lst_msg_obj":lst_msg_obj,"unread_count":unread_count})
      
  elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() :
    user_id = request.user.id
    get_msg = ProcessorMessage.objects.filter(receiver_id=user_id,read_status="UNREAD")
    for i in get_msg:
      unread_count = len(get_msg.filter(board_id= i.board.id))
      lst_msg_obj = str(i.msg)
      lst_msg_obj = f'{lst_msg_obj[:20]}...' if len(lst_msg_obj) > 20 else lst_msg_obj
      lst.append({"receiver_id":i.board.id,"lst_msg_obj":lst_msg_obj,"unread_count":unread_count})
  return JsonResponse({'data':lst}) 


#  Left Pannel Chat section counter
login_required()
def notification_chat_msg(request,user_id):
  unread_count = 0
  if 'Grower' in request.user.get_role() and not request.user.is_superuser :
    g_id = request.user.grower.id
    get_msg = ProcessorMessage.objects.filter(receiver_id=g_id,read_status="UNREAD")
    unread_count = get_msg.count()
      
  elif request.user.is_processor :
    user_email = request.user.email
    p = ProcessorUser.objects.get(contact_email=user_email)
    processor = Processor.objects.get(id=p.processor_id)
    processor_id = processor.id
    get_msg = ProcessorMessage.objects.filter(receiver_id=processor_id,read_status="UNREAD")
    unread_count = get_msg.count()
  
  elif request.user.is_processor2 :
    # user_email = request.user.email
    # p = ProcessorUser2.objects.get(contact_email=user_email)
    # processor = Processor.objects.get(id=p.processor_id)
    # processor_id = processor.id
    # get_msg = ProcessorMessage.objects.filter(receiver_id=processor_id,read_status="UNREAD")
    # unread_count = get_msg.count()
    unread_count = 0
  
  elif request.user.is_distributor :
    # user_email = request.user.email
    # p = ProcessorUser.objects.get(contact_email=user_email)
    # processor = Processor.objects.get(id=p.processor_id)
    # processor_id = processor.id
    # get_msg = ProcessorMessage.objects.filter(receiver_id=processor_id,read_status="UNREAD")
    # unread_count = get_msg.count()
    unread_count = 0
  
  elif request.user.is_warehouse_manager :
    # user_email = request.user.email
    # p = ProcessorUser.objects.get(contact_email=user_email)
    # processor = Processor.objects.get(id=p.processor_id)
    # processor_id = processor.id
    # get_msg = ProcessorMessage.objects.filter(receiver_id=processor_id,read_status="UNREAD")
    # unread_count = get_msg.count()
    unread_count = 0
  
  elif request.user.is_customer :
    # user_email = request.user.email
    # p = ProcessorUser.objects.get(contact_email=user_email)
    # processor = Processor.objects.get(id=p.processor_id)
    # processor_id = processor.id
    # get_msg = ProcessorMessage.objects.filter(receiver_id=processor_id,read_status="UNREAD")
    # unread_count = get_msg.count()
    unread_count = 0
        
  elif request.user.is_consultant :
    user_email = request.user.email
    consultant = Consultant.objects.filter(email=user_email)
    if consultant.exists():
      consultant = consultant.first()
      consultant_id = consultant.id
      get_msg = ProcessorMessage.objects.filter(receiver_id=consultant_id,read_status="UNREAD")
      unread_count = get_msg.count()

  elif request.user.is_superuser or 'SubAdmin' in request.user.get_role() or 'SuperUser' in request.user.get_role() :
    user_id = request.user.id
    get_msg = ProcessorMessage.objects.filter(receiver_id=user_id,read_status="UNREAD")
    unread_count = get_msg.count()
  return HttpResponse (unread_count)


login_required()
def chat_ag0(request):
  if request.user.is_authenticated:
    context = {}
    # processor ...
    if request.user.is_processor :
      user_email = request.user.email
      p = ProcessorUser.objects.get(contact_email=user_email)
      processor = Processor.objects.get(id=p.processor_id)
      processor_grower_obj = LinkGrowerToProcessor.objects.filter(processor_id=processor.id)
      grower_id_all= [i.grower_id for i in processor_grower_obj]
      grower = Grower.objects.filter(id__in=grower_id_all)
      context['grower'] = grower

      for i in range(len(processor_grower_obj)):
        if ProcessorMsgboard.objects.filter(processor_id=processor_grower_obj[i].processor.id).filter(grower_id=processor_grower_obj[i].grower.id).count() == 0:
          ProcessorMsgboard(processor_id= processor_grower_obj[i].processor.id,grower_id=processor_grower_obj[i].grower.id).save()

      if request.method == 'POST':
          get_grower = request.POST.get('get_grower')
          if get_grower != 'all':
            return redirect ('chatroom_ag', pk=int(get_grower))
          else:
            return redirect ('chat_ag')
      # 11-02-23
      link_gp =   ProcessorMsgboard.objects.filter(grower__id__in=grower_id_all)
      grower_lst = []
      for i in link_gp :
        grower_id = i.grower.id
        grower_name = i.grower.name
        obj_last_msg = ProcessorMessage.objects.filter(board_id=i.id)
        last_msg = [i.msg for i in obj_last_msg][-1:]
                
        if len(last_msg) == 1 :
          last_msg = last_msg[0][:50]
        else:
          last_msg = ''
        data = {
          "grower_id":grower_id,
          "grower_name":grower_name,
          "last_msg":last_msg
        }
        grower_lst.append(data)

      context['grower_lst'] = grower_lst
      return render(request, 'chat/messageboard.html',context)
      
    elif 'Grower' in request.user.get_role() and not request.user.is_superuser:
      grower_id= request.user.grower.id
      processor_grower_obj = LinkGrowerToProcessor.objects.filter(grower_id=grower_id)
      if processor_grower_obj.count() !=0 :
        p_id = [i.processor.id for i in processor_grower_obj][0]
        g_id = grower_id
        if ProcessorMsgboard.objects.filter(grower_id=grower_id).count() == 0:
          ProcessorMsgboard(processor_id= p_id,grower_id=g_id).save()

      return redirect('chatroom_ag', pk=grower_id)

  else:
      return redirect('login')

login_required()
def chatroom_ag0(request,pk):
  if request.user.is_authenticated:
      context = {}
      if request.user.is_processor :

        user_email = request.user.email
        p = ProcessorUser.objects.get(contact_email=user_email)
        processor = Processor.objects.get(id=p.processor_id)
        grower_obj = ProcessorMsgboard.objects.filter(processor_id=processor.id)


        grower_id_all= [i.grower_id for i in grower_obj]
        if pk in grower_id_all :
          
          grower = Grower.objects.filter(id__in=grower_id_all)
          context['grower'] = grower
          selected_grower = Grower.objects.get(id=pk)
          board_id = ProcessorMsgboard.objects.filter(processor_id=processor.id).filter(grower_id=selected_grower.id)
          context['board_id'] = [i.id for i in board_id][0]
          context['sender_is'] = 'processor'
          context['receiver_is'] = 'grower'
          context['sender_id'] = p.id
          context['sender_name'] = p.contact_name
          context['selected_grower'] = selected_grower
          context['receiver_id'] = [i.grower.id for i in board_id][0]
          context['receiver_name'] = [i.grower.name for i in board_id][0]
  
          read_msg = ProcessorMessage.objects.filter(board_id=[i.id for i in board_id][0]).order_by("id")
          for i in read_msg:
            update_read_status = ProcessorMessage.objects.get(id=i.id)
            update_read_status.read_status = 'READ'
            update_read_status.save()
          last_seen_obj = ProcessorMessage.objects.filter(board_id=[i.id for i in board_id][0]).filter(sender_id=[i.grower.id for i in board_id][0])
          # last_msg_shown_obj = ProcessorMessage.objects.filter(board_id=[i.id for i in board_id])
          if last_seen_obj.exists() :
            last_seen_obj = last_seen_obj.last()
            last_seen_date = last_seen_obj.msg_date
            last_seen_time = last_seen_obj.msg_time
          else:
            last_seen_date = ''
            last_seen_time = ''

          # if last_msg_shown_obj.exists() :
          #   last_msg_shown_obj = last_msg_shown_obj.last()
          # else:
          #   last_msg_shown_obj = ''

          # 11-02-23
          link_gp =   ProcessorMsgboard.objects.filter(grower__id__in=grower_id_all)
          grower_lst = []
          for i in link_gp :
            grower_id = i.grower.id
            grower_name = i.grower.name
            obj_last_msg = ProcessorMessage.objects.filter(board_id=i.id)
            last_msg = [i.msg for i in obj_last_msg][-1:]

            if len(last_msg) == 1 :
              last_msg = last_msg[0][:50]
            else:
              last_msg = ''
            data = {
              "grower_id":grower_id,
              "grower_name":grower_name,
              "last_msg":last_msg
            }
            grower_lst.append(data)
          context['last_seen_date'] = last_seen_date
          context['last_seen_time'] = last_seen_time
          context['grower_lst'] = grower_lst
          context['read_msg'] = read_msg
          return render(request, 'chat/messageboard_room.html',context)
        else:
          return redirect('login')
      if 'Grower' in request.user.get_role() and not request.user.is_superuser :
        grower_id= request.user.grower.id
        pk = pk
        if grower_id == pk and LinkGrowerToProcessor.objects.filter(grower_id=pk).count() != 0:
          grower_id= request.user.grower.id
          selected_grower = Grower.objects.get(id=grower_id)
          context['selected_grower'] = selected_grower
          processor_board = ProcessorMsgboard.objects.get(grower_id=pk)
          processor = processor_board.processor.entity_name
          board_id = ProcessorMsgboard.objects.filter(processor_id=processor_board.processor.id).filter(grower_id=selected_grower.id)
          last_seen_obj = ProcessorMessage.objects.filter(board_id=processor_board.id)
          if last_seen_obj.exists() :
            last_seen_obj = last_seen_obj.last()
            last_seen_date = last_seen_obj.msg_date
            last_seen_time = last_seen_obj.msg_time
          else:
            last_seen_date = ''
            last_seen_time = ''
          context['sender_is'] = 'grower'
          context['receiver_is'] = 'processor'
          context['board_id'] = [i.id for i in board_id][0]
          context['sender_id'] = selected_grower.id
          context['sender_name'] = selected_grower.name
          context['processor_name'] = processor
          context['receiver_id'] = [i.processor.id for i in board_id][0]
          context['receiver_name'] = [i.processor.entity_name for i in board_id][0]
          context['last_seen_date'] = last_seen_date
          context['last_seen_time'] = last_seen_time
          read_msg = ProcessorMessage.objects.filter(board_id=[i.id for i in board_id][0]).order_by("id")
          for i in read_msg:
            update_read_status = ProcessorMessage.objects.get(id=i.id)
            update_read_status.read_status = 'READ'
            update_read_status.save()
          context['read_msg'] = read_msg
          return render(request, 'chat/messageboard_room.html',context)
        else:
          return redirect('login')
        # return render(request, 'chat/messageboard_room.html',context)
  else:
      return redirect('login')

login_required()
def processor_last_login(request,pk):
  processor_board = ProcessorMsgboard.objects.get(grower_id=pk)
  last_seen_obj = ProcessorMessage.objects.filter(board_id=processor_board.id)
  if last_seen_obj.exists() :
    last_seen_obj = last_seen_obj.last()
    last_seen_date = last_seen_obj.msg_date
    last_seen_time = last_seen_obj.msg_time
  else:
    last_seen_date = ''
    last_seen_time = ''
  data = [{"last_seen_date":last_seen_date,"last_seen_time":last_seen_time}]
  return JsonResponse({'data':data}) 


login_required()
def ajax_msg_board0(request,user_id):
  lst = []
  get_user = User.objects.get(id=user_id)
  if get_user.grower :
    
    grower_id = get_user.grower.id
    # board_id = ProcessorMsgboard.objects.get(grower_id=grower_id)
    board_id = []
    lst = {"grower_id":grower_id,"lst_msg_obj":0,"unread_count":0}
  elif get_user.is_processor :
    
    processor_email = get_user.username
    processor_id = ProcessorUser.objects.get(contact_email=processor_email).processor.id
    all_board_id = ProcessorMsgboard.objects.filter(processor_id=processor_id)
    print("sudip..........................",all_board_id)
    
    # all_grower_id = [i.grower.id for i in all_board_id]
    lst = []
    for i in all_board_id :
      
      grower_id = i.grower.id
      # board_id = ProcessorMsgboard.objects.get(board_id=i.id)
      
      lst_msg_obj = ProcessorMessage.objects.filter(board_id=i.id,read_status="UNREAD")
      # unread_count = ProcessorMessage.objects.filter(sender_id=grower_id).filter(read_status="UNREAD")
 
      if lst_msg_obj.exists() :
        
      #   lst_msg_obj = lst_msg_obj.values('msg').last()
      #   data = {"grower_id":grower_id,"lst_msg_obj":lst_msg_obj['msg'][:50],"unread_count":unread_count.count()}
      # elif lst_msg_obj.exists() :
      #   lst_msg = lst_msg_obj[-1]

        # data = {"grower_id":grower_id,"lst_msg_obj":lst_msg_obj['msg'][:50],"unread_count":unread_count.count()}
        data = {"grower_id":grower_id,"lst_msg_obj":"lst_msg_obj","unread_count":1}
      else:
        data = {"grower_id":grower_id,"lst_msg_obj":0,"unread_count":0}
      lst.append(data)
    
  return JsonResponse({'data':lst}) 


login_required()
def read_msg_status(request,username):
  get_user = User.objects.get(username=username)
  if get_user.grower : 
    grower_id = Grower.objects.get(email=username).id
    last_msg_read = ProcessorMessage.objects.filter(sender_id=grower_id)
    for i in last_msg_read :
      last_msg_read_obj = ProcessorMessage.objects.get(id=i.id)
      last_msg_read_obj.read_status = 'READ'
      last_msg_read_obj.save()

  elif get_user.is_processor :
    sender_id = ProcessorUser.objects.get(contact_email=username).id
    last_msg_read = ProcessorMessage.objects.filter(sender_id=sender_id)
    
    for i in last_msg_read :
      last_msg_read_obj = ProcessorMessage.objects.get(id=i.id)
      last_msg_read_obj.read_status = 'READ'
      last_msg_read_obj.save()
  
  return HttpResponse(1)

login_required()
def save_msg0(request,user_id,roomName,message):
  get_user = User.objects.get(id=user_id)
  get_room = ProcessorMsgboard.objects.get(grower_id=roomName)
  board_id = get_room.id
  if get_user.is_processor :
    sender_is = "processor"
    receiver_is = "grower"
    sender_obj = ProcessorUser.objects.get(contact_email=get_user.username)
    sender_id = sender_obj.id
    sender_name = sender_obj.contact_name
    receiver_obj = Grower.objects.get(id=roomName)
    receiver_id = receiver_obj.id
    receiver_name = receiver_obj.name
    msg_date = date.today().strftime("%m/%d/%Y")
    msg_time = datetime.now()
    save_msg = ProcessorMessage(board_id=board_id,sender_is=sender_is,sender_id=sender_id,sender_name=sender_name,
    receiver_is=receiver_is,receiver_id=receiver_id,receiver_name=receiver_name,msg=message,msg_date=msg_date,msg_time=msg_time,read_status="UNREAD")
    save_msg.save()
  if get_user.grower : 
    sender_is = "grower"
    receiver_is = "processor"
    sender_obj = Grower.objects.get(id=roomName)
    sender_id = sender_obj.id
    sender_name = sender_obj.name
    receiver_obj = Processor.objects.get(id=get_room.processor.id)
    receiver_id = receiver_obj.id
    receiver_name = receiver_obj.entity_name
    msg_date = date.today().strftime("%m/%d/%Y")
    msg_time = datetime.now()
    save_msg = ProcessorMessage(board_id=board_id,sender_is=sender_is,sender_id=sender_id,sender_name=sender_name,
    receiver_is=receiver_is,receiver_id=receiver_id,receiver_name=receiver_name,msg=message,msg_date=msg_date,msg_time=msg_time,read_status="UNREAD")
    save_msg.save()
  return HttpResponse(1)

login_required()
def get_msg0(request,user_id,roomName):
  get_user = User.objects.get(id=user_id)
  get_room = ProcessorMsgboard.objects.get(grower_id=roomName)
  board_id = get_room.id
  if get_user.is_processor :
    sender_is = "processor"
    receiver_is = "grower"
    p_user = ProcessorUser.objects.get(contact_email=get_user.username)
    receiver_obj = Processor.objects.get(id=p_user.processor.id)
    receiver_id = receiver_obj.id
    receiver_name = receiver_obj.entity_name
    
    filter_msg_obj = ProcessorMessage.objects.filter(receiver_id=receiver_id).filter(sender_id=roomName).filter(read_status="UNREAD")
    
    try:
      id_get_msg_obj = [i.id for i in filter_msg_obj][0]
      get_msg_obj = ProcessorMessage.objects.get(id=id_get_msg_obj)
      get_msg_obj.read_status = "READ"
      get_msg_obj.save()
      mydate = get_msg_obj.msg_date.strftime("%b %d, %Y")
      # mytime = get_msg_obj.msg_time.strftime("%I:%M %p")
      var_mytime = str(get_msg_obj.msg_time.strftime("%I:%M %p"))
      am_pm = var_mytime[-3:]
      # print(len(am_pm))
      if am_pm == ' PM':
        mytime = var_mytime.replace(' PM', ' P.M.')
      elif am_pm == ' AM':
        mytime = var_mytime.replace(' AM', ' A.M.')
      return JsonResponse({'msg':get_msg_obj.msg,'msg_date':mydate,'msg_time':mytime})
    except:
      pass 

  if get_user.grower : 
    sender_is = "grower"
    receiver_is = "processor"
    receiver_obj = Grower.objects.get(id=roomName)
    receiver_id = receiver_obj.id
  
    filter_msg_obj = ProcessorMessage.objects.filter(receiver_id=receiver_id).filter(read_status="UNREAD")
    
    try:
      id_get_msg_obj = [i.id for i in filter_msg_obj][0]
      get_msg_obj = ProcessorMessage.objects.get(id=id_get_msg_obj)
      get_msg_obj.read_status = "READ"
      get_msg_obj.save()
      mydate = get_msg_obj.msg_date.strftime("%b %d, %Y")
      # mytime = get_msg_obj.msg_time.strftime("%I:%M %p")
      var_mytime = str(get_msg_obj.msg_time.strftime("%I:%M %p"))
      am_pm = var_mytime[-3:]
      if am_pm == ' PM':
        mytime = var_mytime.replace(' PM', ' P.M.')
      elif am_pm == ' AM':
        mytime = var_mytime.replace(' AM', ' A.M.')
  
      return JsonResponse({'msg':get_msg_obj.msg,'msg_date':mydate,'msg_time':mytime})
    except:
      pass 
  return HttpResponse(1)


