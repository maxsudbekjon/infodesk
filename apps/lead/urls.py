from django.urls import path

from apps.lead.views import LeadCreateAPIView

urlpatterns = [
    path('create/',LeadCreateAPIView.as_view(),name='lead-create')
]
