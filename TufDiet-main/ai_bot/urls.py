from django.urls import path
from . import views

urlpatterns = [
    path('chat-response/', views.chat_response, name='chat-response'),
    path('chat-hub/', views.chat_hub_view, name='chat-hub'),
    path('progress-data/', views.get_progress_data, name='progress-data'),
    path('progress-data/<str:period>/', views.get_progress_data, name='progress-data-period'),
]
