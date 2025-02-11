'''Signal for survey answers'''
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from apps.survey.models import Survey, SurveyInfo
from main.settings import DEFAULT_FROM_EMAIL
from functools import wraps

#pylint: disable=no-member,expression-not-assigned, too-many-locals, too-many-ancestors, too-many-ancestors, bare-except

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

def send_notification(instance,consultant_emails,created):
    """[Function for sending email notification to the Consultant]

    Args:
        instance (Model instance ): SurveyInfo model object
        consultant_emails (list): list of email IDs
        created (Boolean): [True if new model object is created,
            false if model object is modified
    """
    html_message = render_to_string('survey/survey_mail_notification.html',\
        {'obj': instance,'created':created})

    if created:
        msg = EmailMessage("Survey Submitted", html_message, DEFAULT_FROM_EMAIL,
            consultant_emails)
    else:
        msg = EmailMessage("Survey Resubmitted", html_message,
            DEFAULT_FROM_EMAIL, consultant_emails)

    msg.content_subtype = "html"
    msg.send(fail_silently=True)


@receiver(post_save,sender=Survey)
@disable_for_loaddata
def surveySubmit(sender, instance, created, **kwargs):
    """For sending email to the consultants

    Args:
        sender (Signal sender): sender object of signal
        instance (Model): SurveyInfo model object
        created (Boolean): True if new model object is created,
            false if model object is modified
    """
    consultants = instance.grower.consultant.all()
    consultant_emails = []
    for emails in consultants:
        consultant_emails.append(emails.email)
        print(emails.email)
    try:
        info_obj = SurveyInfo.objects.get(grower_id=instance.grower_id,
            farm_id=instance.farm_id,
            field_id=instance.field_id,
            year=instance.year
            )
        if info_obj.survey_date.date() != datetime.today().date():
            send_notification(instance,consultant_emails,created)
            info_obj.survey_date = datetime.today()
            info_obj.approve_status = False
            info_obj.save()
        else:
            info_obj.survey_date = datetime.today()
            info_obj.approve_status = False
            info_obj.save()
    except:
        info_obj = SurveyInfo(grower_id=instance.grower_id,
            farm_id=instance.farm_id,
            field_id=instance.field_id,
            year=instance.year,
            survey_date=datetime.now())
        send_notification(instance,consultant_emails,created)
        info_obj.survey_date = datetime.today()
        info_obj.approve_status = False
        info_obj.save()

