from rest_framework import routers

from apps.accounts.apis import AuthViewSet
from apps.farms.apis import FarmViewSet
from apps.field.apis import FieldViewSet

from apps.survey.apis import (
    SurveyViewSet, QuestionAnswerViewSet, ConsultantNotificationViewSet, GrowerNotificationViewSet,
    SustainabilityViewSet
)

from apps.grower.apis import GrowerViewSet, ConsultantViewSet
from apps.gallery.apis import GalleryViewSet

from apps.questions.apis import QuestionViewSet

router = routers.SimpleRouter()



router.register('auth', AuthViewSet, basename="auth")
router.register('grower', GrowerViewSet, basename="grower")
router.register('consultant', ConsultantViewSet, basename="consultant")

router.register('farm', FarmViewSet, basename="farm")
router.register('field', FieldViewSet, basename="field")

router.register('gallery', GalleryViewSet, basename="gallery")
router.register('questions', QuestionViewSet, basename="questions")
router.register('survey', SurveyViewSet, basename="survey")
router.register('question_answer', QuestionAnswerViewSet, basename="question-answer")
router.register('consultant_notification', ConsultantNotificationViewSet, basename="consultant-notification")
router.register('grower_notification', GrowerNotificationViewSet, basename="grower-notification")
router.register('sustainability', SustainabilityViewSet, basename="sustainability")
