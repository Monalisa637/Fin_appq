from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),
    path('dashboard/<int:doc_id>/', views.dashboard, name='dashboard'),
    path('ask/<int:doc_id>/', views.ask_question, name='ask_question'),
]
