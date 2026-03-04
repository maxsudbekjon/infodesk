from openpyxl import Workbook
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from apps.lead.models import Lead
from apps.user.models import Operator

@extend_schema(tags=['Lead'])
class LeadExportExcelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        organizations = user.organization_set.all()

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
