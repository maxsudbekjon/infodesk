from django.urls import path
from apps.lead.views import LeadCreateAPIView, LeadListAPIView, MonthlyLeadSourceComparisonAPIView



urlpatterns = [

    path('create/',LeadCreateAPIView.as_view(),name='lead-create'),

    path('list/',LeadListAPIView.as_view(),name='lead-list'),
    path(
        'stats/monthly-comparison/',
        MonthlyLeadSourceComparisonAPIView.as_view(),
        name='monthly-lead-source-comparison'
    ),
]
