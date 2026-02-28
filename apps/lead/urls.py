from django.urls import path
from apps.lead.views import LeadAddGroupAPIView, LeadCreateAPIView, LeadDeleteAPIView, LeadExportExcelAPIView, LeadListAPIView, MonthlyLeadSourceComparisonAPIView, SourceListAPIView



urlpatterns = [

    path('create/',LeadCreateAPIView.as_view(),name='lead-create'),

    path('list/',LeadListAPIView.as_view(),name='lead-list'),
    path(
        'stats/monthly-comparison/',
        MonthlyLeadSourceComparisonAPIView.as_view(),
        name='monthly-lead-source-comparison'
    ),
    path(
        'source/create',
        SourceListAPIView.as_view(),
        name='source-create'
    ),
    path(
        'lead-add-group/<int:id>',
        LeadAddGroupAPIView.as_view(),
        name='lead-add-group'
    ),
    path(
        'lead/delete/<int:id>',
        LeadDeleteAPIView.as_view(),
        name='lead-delete'
    ),
    path(
        'api/leads/export/',
        LeadExportExcelAPIView.as_view(),
        name='lead-exel-export'
    )
]
