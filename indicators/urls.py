from django.urls import path
from . import views

urlpatterns = [
    path('', views.indicator_list, name='indicator_list'),
    path('indicator/<int:pk>/', views.indicator_detail, name='indicator_detail'),
    path('chatbot/', views.chatbot_query, name='chatbot_query'),
    path('chatbot/stream/', views.stream_chatbot_response, name='stream_chatbot_response'),
    path('about/', views.about_rdhs, name='about_rdhs'),
    path('indicator/<int:pk>/insights/', views.indicator_insights, name='indicator_insights'),
    path('indicator/<int:pk>/export/', views.export_indicator_csv, name='export_indicator_csv'),
    path('settings/', views.public_settings, name='public_settings'),
    path('analytics/', views.advanced_analytics, name='correlation_analytics'), # Keeping name for template compatibility
]
