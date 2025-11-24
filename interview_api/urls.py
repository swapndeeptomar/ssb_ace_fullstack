from django.urls import path
from . import views

urlpatterns = [
    path('wat/', views.get_wat_word, name='get_wat'),
    path('srt/', views.get_srt_situation, name='get_srt'),
    path('interview/', views.get_interview_question, name='get_interview'),
    path('submit/', views.submit_response, name='submit_resp'),
    path('report/', views.get_candidate_report, name='get_report'),
    path('register/', views.register_candidate, name='register'),
    path('oir/', views.get_oir_questions, name='get_oir'),
    path('ppdt/', views.get_ppdt_image, name='get_ppdt'),
    path('oir/submit/', views.submit_oir, name='submit_oir'),
    path('tat/', views.get_tat_images, name='get_tat'),
    path('sdt/', views.get_sdt_questions, name='get_sdt'),
]