"""[Singls for Grower app"""
import threading
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


from apps.grower.models import Grower
from apps.accounts.models import User, Role, SubSuperUser 
from apps.grower.models import Consultant
from apps.grower.randompass import generate_random_password
from main.settings import DEFAULT_FROM_EMAIL
from apps.survey.models import Survey, ConsultantNotification, GrowerNotification
from functools import wraps

#pylint: disable=no-member, no-self-use, too-many-ancestors, bare-except, too-many-locals, unused-argument

def disable_for_loaddata(signal_handler):
    """
    Decorator that turns off signal handlers when loading fixture data.
    """

    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if kwargs.get('raw'):
            return
        signal_handler(*args, **kwargs)
    return wrapper

def send_notification(instance,created, email,username,password):
    """[Function for sending email notification to the Consultant]

    Args:
        instance (Model instance ): SurveyInfo model object
        consultant_emails (list): list of email IDs
        created (Boolean): [True if new model object is created,
            false if model object is modified
    """

    html_message = render_to_string('grower/consultant_cred_notifi.html',\
        {'obj': instance, 'username' :username, 'password' :password})

    if created:
        msg = EmailMessage("Consultant credentials", html_message, DEFAULT_FROM_EMAIL,
            email)
    else:
        msg = EmailMessage("Consultant credentials updated", html_message,
            DEFAULT_FROM_EMAIL, email)

    msg.content_subtype = "html"
    msg.send(fail_silently=True)

def send_user_login_notification(instance,created, email,username,password):
    """[Function for sending email notification to the Grower's email ID]

    Args:
        instance (Model instance ): SurveyInfo model object
        consultant_emails (list): list of email IDs
        created (Boolean): [True if new model object is created,
            false if model object is modified
    """

    html_message = render_to_string('grower/login_account_notifi.html',\
        {'obj': instance, 'username' :username, 'password' :password})

    if created:
        msg = EmailMessage("Consultant credentials", html_message, DEFAULT_FROM_EMAIL,
            email)
    else:
        msg = EmailMessage("Consultant credentials updated", html_message,
            DEFAULT_FROM_EMAIL, email)

    msg.content_subtype = "html"
    msg.send(fail_silently=True)


def notifi_to_consultant(pk,old_emails):
    """Function to send email notification whenever a consultant is changed or modified

    Args:
        pk (int): grower id
        old_emails (set): old email IDs of consultant which was assigned to the grower
    """
    new_emails = set(Grower.objects.get(pk=pk).consultant.values_list('email',flat=True))
    obj = Grower.objects.get(pk=pk)
    to_email = new_emails-old_emails
    if len(to_email) > 0:
        html_message = render_to_string('grower/grower_change_notifi.html',{'obj': obj})
        msg = EmailMessage("Grower assigned", html_message, DEFAULT_FROM_EMAIL,to_email)
        msg.content_subtype = "html"
        msg.send(fail_silently=True)


@receiver(post_save, sender=Consultant)
@disable_for_loaddata
def create_consultant_user(sender, instance, created , **kwargs):
    """Post save signal for Consultant model

    Args:
        sender (Object): signal sender
        instance ([Object]): Object instance
        created ([Boolean]): True if new record is created, False if updated
    """
    if created:
        #print('hello')
        password = generate_random_password()
        email = instance.email
        username = instance.email
        # username = f"{instance.name.split(' ')[0].lower()}_{instance.id}"
        user = User.objects.create(email=email, username=username)
        user.is_active=True
        #add value in many to many field
        user.role.add(Role.objects.get(role='Consultant'))
        user.is_consultant = True
        user.set_password(password)
        if(" " in instance.name ):
            name_split = instance.name.rsplit(' ', 1)
            user.first_name = name_split[0]
            user.last_name = name_split[1]
        else:
            user.first_name=instance.name
            user.last_name= ""
        user.password_raw = password
        user.save()
        send_notification(instance,created,[email],username,password)


@receiver(post_save, sender=SubSuperUser)
@disable_for_loaddata
def create_subsuper_user(sender, instance, created , **kwargs):
    """Post save signal for SubSuperUser model

    Args:
        sender (Object): signal sender
        instance ([Object]): Object instance
        created ([Boolean]): True if new record is created, False if updated
    """
    if created:
        password = generate_random_password()
        email = instance.email
        username = instance.email
        user = User.objects.create(email=email, username=username)
        user.is_active=True

        # data = SubSuperUser.objects.raw("select * from accounts_subsuperuser_role where subsuperuser_id=%s",[18])
        # role_ids = [id.role_id for id in data]
        # print(data)
        #print(instance.role)

        
        user.role.add(Role.objects.get(role=instance.role))
        user.set_password(password)
        if(" " in instance.name ):
            name_split = instance.name.rsplit(' ', 1)
            user.first_name = name_split[0]
            user.last_name = name_split[1]
        else:
            user.first_name=instance.name
            user.last_name= ""
        user.password_raw = password
        user.save()
        send_notification(instance,created,[email],username,password)
    


@receiver(post_save, sender=Grower)
@disable_for_loaddata
def create_default_user(sender, instance, created , **kwargs):
    """Post save signal for Grower model

    Args:
        sender (Object): signal sender
        instance ([Object]): Object instance
        created ([Boolean]): True if new record is created, False if updated
    """
    if created:
        password = f"{instance.name.split(' ')[0].lower()}" 
        email = instance.email
        username = instance.email
        #username = f"{instance.name.split(' ')[0].lower()}_{instance.id}"
        user = User.objects.create(email=email, username=username)
        user.grower_id=instance.id
        user.is_active=True
        user.role.add(Role.objects.get(role='Grower'))
        user.set_password(password)
        user.password_raw = password
        if(" " in instance.name ):
            name_split = instance.name.rsplit(' ', 1)
            user.first_name = name_split[0]
            user.last_name = name_split[1]
        else:
            user.first_name=instance.name
            user.last_name= ""
        user.save()
        thr1 = threading.Thread(target=notifi_to_consultant, args=(instance.id,instance.old_emails,))
        thr1.start()
        send_user_login_notification(instance,created,[email],username,password)
        return user

    thr1 = threading.Thread(target=notifi_to_consultant, args=(instance.id,instance.old_emails,))
    thr1.start()


@receiver(pre_save, sender=Grower)
@disable_for_loaddata
def grower_update(sender, instance, **kwargs):
    """Pre save signal for Grower model
    Args:
        sender (Object): signal sender
        instance ([Object]): Object instance
        **kwargs : keyword arguments
    """
    try:
        instance.old_emails = set(Grower.objects.get(pk=instance.id).\
            consultant.values_list('email',flat=True))
    except:
        instance.old_emails = set()


@receiver(post_save, sender=Survey)
@disable_for_loaddata
def create_consultant_notification(sender, instance, created , **kwargs):
    if created:
        if not instance.is_accepted and not instance.is_rejected:
            text = f"New {instance.survey_type.name} has been submitted for your review."
            survey_id = Survey.objects.get(id=instance.id)
            consultant_notification = ConsultantNotification.objects.create(survey=survey_id, text=text)
            consultant_notification.save()


@receiver(post_save, sender=Survey)
@disable_for_loaddata
def create_grower_notification(sender, instance, created , **kwargs):
    for instance in Survey.objects.all():
        if instance.is_accepted and not instance.is_rejected:
            text = f"Your {instance.survey_type.name} has been ACCEPTED."
            survey_id = Survey.objects.get(id=instance.id)
            grower_notification = GrowerNotification.objects.create(survey=survey_id, text=text)
            grower_notification.save()


        if instance.is_rejected and not instance.is_accepted:
            text = f"Your {instance.survey_type.name} has been REJECTED."
            survey_id = Survey.objects.get(id=instance.id)
            grower_notification = GrowerNotification.objects.create(survey=survey_id, text=text)
            grower_notification.save()

        # if instance.is_accepted and instance.is_rejected:
        #     raise ValidationError("Either is_accepted or is_rejected needs to be true, both\
        #         can't be true simultaneously!")



def send_contract_verification_email(instance, email, grower_name, contract_verification_link):

    html_message = render_to_string(
        'contracts/contract_verification_email_template.html',
        {'obj': instance, "grower_name": grower_name, "contract_verification_link": contract_verification_link})

    msg = EmailMessage(
        "Contract Verification",
        html_message,
        DEFAULT_FROM_EMAIL,
        email,
    )

    msg.content_subtype = "html"
    msg.send(fail_silently=True)
