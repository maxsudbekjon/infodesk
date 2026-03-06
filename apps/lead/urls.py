from django.urls import path
from apps.lead.views import LeadAddGroupAPIView, LeadCreateAPIView, LeadDeleteAPIView, LeadExportExcelAPIView, LeadListAPIView, MonthlyLeadSourceComparisonAPIView, SituationCreateAPIView, SourceCreateAPIView
from apps.lead.views.lead import LeadSituationUpdateView
from apps.lead.views.situation import SituationListAPIView



urlpatterns = [

    path(
        'create/',
        LeadCreateAPIView.as_view(),
        name='lead-create'
    ),
    path(
        'list/',
        LeadListAPIView.as_view(),
        name='lead-list'
    ),
    path(
        'stats/monthly-comparison/',
        MonthlyLeadSourceComparisonAPIView.as_view(),
        name='monthly-lead-source-comparison'
    ),
    path(
        'source/create/',
        SourceCreateAPIView.as_view(),
        name='source-create'
    ),
    path(
        'lead-add-group/<int:id>/',
        LeadAddGroupAPIView.as_view(),
        name='lead-add-group'
    ),
    path(
        'lead/delete/<int:id>/',
        LeadDeleteAPIView.as_view(),
        name='lead-delete'
    ),
    path(
        'api/leads/export/',
        LeadExportExcelAPIView.as_view(),
        name='lead-exel-export'
    ),
    path(
        'situation/create/',
        SituationCreateAPIView.as_view(),
        name='situation-create'
    ),
    path(
        'situation-list/',
        SituationListAPIView.as_view(),
        name='situation-list'
    ),
    path("situation/<int:id>/", 
         LeadSituationUpdateView.as_view(), 
         name="lead-situation-update"),
]
