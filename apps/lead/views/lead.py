from rest_framework import generics
from apps.lead.serializers import LeadModelSerializer
from apps.lead.serializers.lead import LeadSituationUpdateSerializer
from drf_spectacular.types import OpenApiTypes
from apps.lead.serializers import LeadAddGroupSerializer
from openpyxl import Workbook
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.http import HttpResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from apps.lead.models import Lead
from apps.lead.serializers import LeadListModelSerializer
from apps.lead.views.utils import LeadPagination, parse_bool
from apps.user.models import Operator





@extend_schema(tags=['Lead'])
class LeadSituationUpdateView(generics.UpdateAPIView):
    queryset = Lead.objects.filter(is_archived=False)
    serializer_class = LeadSituationUpdateSerializer
    lookup_field='id'



@extend_schema(
    tags=["Lead"],
    parameters=[
        OpenApiParameter(
            name="branch_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Branch ID for filtering leads",
        ),
        OpenApiParameter(
            name="is_active",
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            required=False,
        ),
        OpenApiParameter(
            name="is_archived",
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            required=False,
        ),
    ],
)
class LeadListAPIView(generics.ListAPIView):
    serializer_class = LeadListModelSerializer
    pagination_class = LeadPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        base_queryset = (
            Lead.objects.select_related("operator__user", "situation")
            .only(
                "id",
                "full_name",
                "phone_number",
                "created_at",
                "is_active",
                "is_archived",
                "situation_id",
                "operator_id",
                "operator__user__first_name",
                "operator__user__last_name",
            )
            .order_by("-created_at")
        )

        organizations = user.organization.all()
        if organizations.exists():
            queryset = base_queryset.filter(center__in=organizations)
        else:
            try:
                operator = user.operator
            except Operator.DoesNotExist:
                operator = None
            if operator:
                queryset = base_queryset.filter(operator__user=user)
            else:
                return Lead.objects.none()

        is_active = self.request.query_params.get("is_active")
        is_archived = self.request.query_params.get("is_archived")
        branch_id = self.request.query_params.get("branch_id")

        if is_active is not None:
            queryset = queryset.filter(is_active=parse_bool(is_active))

        if is_archived is not None:
            queryset = queryset.filter(is_archived=parse_bool(is_archived))
        if branch_id:
            queryset = queryset.filter(course__branchs=branch_id)
        return queryset

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)



@extend_schema(tags=['Lead'])
class LeadExportExcelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        organizations = user.organization.all()

        if organizations.exists():
            leads = Lead.objects.filter(center__in=organizations)
        else:
            try:
                operator = user.operator
            except Operator.DoesNotExist:
                operator = None
            if operator:
                leads = Lead.objects.filter(center=operator.center)
            else:
                leads = Lead.objects.none()

        leads = leads.select_related("operator__user", "center")

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Leads"

        headers = [
            "ID",
            "Full Name",
            "Phone",
            "Operator",
            "Center",
            "Created At",
            "Status",
        ]
        sheet.append(headers)

        for lead in leads:
            sheet.append(
                [
                    lead.id,
                    lead.full_name,
                    lead.phone_number,
                    (
                        f"{lead.operator.user.first_name} {lead.operator.user.last_name}".strip()
                        if lead.operator and lead.operator.user
                        else ""
                    ),
                    lead.center.name if lead.center else "",
                    lead.created_at.strftime("%Y-%m-%d %H:%M"),
                    lead.status,
                ]
            )

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = "attachment; filename=leads.xlsx"

        workbook.save(response)
        return response
    


@extend_schema(tags=['Lead'])
class LeadDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Lead.objects.all()
    lookup_field = "id"


@extend_schema(tags=['Lead'])
class LeadCreateAPIView(generics.CreateAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadModelSerializer
    permission_classes = [IsAuthenticated]





@extend_schema(tags=['Lead'])
class LeadAddGroupAPIView(generics.UpdateAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadAddGroupSerializer
    permission_classes=[IsAuthenticated]
    lookup_field = "id"
