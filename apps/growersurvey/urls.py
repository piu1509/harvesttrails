from django.urls import path

from apps.growersurvey import views

urlpatterns = [
    path('type/', views.GrowerSurveyView.as_view(), name='type-survey'),
    path('questions/<int:pk>/<int:frmid>/<int:fldid>/<int:nmsrvid>', views.GrowerSurveyQuestionsView.as_view(), name='type-questions'),
    path('questions/insertopt_value/', views.InsertoptValue, name='insertopt-value'),
    path('sustainabilityresult/', views.GrowerSurveyResultScore.as_view(), name='sustainresultnew-value'),
    path('type/getyear/', views.SurveytypeGetyear, name='surveytype-getyear'),
    path('type/getfarm/', views.SurveytypeGetfarm, name='surveytype-getfarm'),
    path('create_survey/', views.GrowerSurveyCreate.as_view(), name='create-survey'),
    path('create_survey/save_survey/', views.SaveSurvey, name='save-survey'),
    path('create_survey/save_question_option/', views.save_question_option, name='save-question-option'),
    path('create_survey/get_question/', views.GetQuestion.as_view(), name='get-question'),
    path('survey-list/', views.GetAllSurvey.as_view(), name='survey-listing'),
    path('create_survey/check_survey_db/', views.CheckSurveyDb, name='check-survey-db'),
    path('survey_delete/', views.SurveyDelete, name='survey-delete'),
    path('question_delete/', views.QuestionDelete, name='question-delete'),
    path('edit_view_question_options/', views.EditViewQuestionOptions.as_view(), name='edit-view-question-options'),
    path('save_question_option_edit/', views.SaveQuestionOptionEdit, name='save-question-option-edit'),
    path('survey-list/<int:pk>/update/', views.SurveyUpdateView.as_view(), name='survey-update'),
    path('create_survey/save_survey_edit/', views.SaveSurveyEdit, name='edit-survey'),
    path('get_first_question/', views.get_first_question, name='get-first-question'),
    path('check_survey_status/', views.CheckSurveyStatus.as_view(), name='check-survey-status'),
    path('grower_sustainabilty/', views.GrowerSustainabilty.as_view(), name='grower-sustainability'),
    path('get_all_farm/', views.GetAllFarm.as_view(), name='get-all-farm'),
    path('get_all_field/', views.GetAllField.as_view(), name='get-all-field'),
    path('get_sustainability_result/', views.GetSustainabilityResult.as_view(), name='get-sustainability-result'),
    path('get_chart_result/', views.GetChartResult.as_view(), name='get-chart-result'),
    path('gen_pdf_result/', views.pdf_dw, name='gen-pdf-result'),
    path('myview/<int:apply_growers>/<int:apply_farm>/<int:apply_field>/<int:apply_year>', views.MyView.as_view(), name='myview'),
    path('set_chart_image/', views.SetChartImage, name='set-chart-image'),
    path('grower_sustainabilty_comparison/', views.GrowerSustainComparison.as_view(), name='grower-sustain-comparison'),

    # sdp
    path('survey-list/change_qoestion_order/', views.change_qoestion_order, name='change_qoestion_order'),
    path('download_all_survey_record', views.download_all_survey_record, name='download_all_survey_record'),
    path('updatesurvey_forcsv', views.updatesurvey_forcsv, name='updatesurvey_forcsv'),
    # 02-08-23
    path('field_level_sustainability', views.field_level_sustainability, name='field_level_sustainability'),
    path('field_level_sustainability_csv/<str:field_id>/<str:yearid>/', views.field_level_sustainability_csv, name='field_level_sustainability_csv'),
    path('field_autocomplete_suggestions/', views.field_autocomplete_suggestions, name='field_autocomplete_suggestions'),
       
    
]