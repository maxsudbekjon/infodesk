from apps.lead.models import Lead
from apps.lead.choices import LEAD_STATUS
from apps.settings.choices import LEAD_CONSOLIDATION
from apps.settings.models import Organization
from apps.user.models import Operator
from django.db import models, transaction



# lead tushishi bilan operator biriktiradi.
def auto_assign(lead: Lead):
    if not lead.center:
        return None
    if lead.center.lead_consolidation != LEAD_CONSOLIDATION.AUTO:
        return lead

    operator = (
        Operator.objects
        .filter(
            is_archived=False,
            center=lead.center   # 🔥 MUHIM
        )
        .annotate(
            new_leads_count=models.Count(
                'leads',
                filter=models.Q(leads__status=LEAD_STATUS.NEW)
            )
        )
        .order_by('new_leads_count', 'id')
        .first()
    )

    if operator:
        lead.operator = operator
        lead.save(update_fields=['operator'])

    return lead

def once_a_day():
    centers = Organization.objects.filter(
        lead_consolidation=LEAD_CONSOLIDATION.ONCE_A_DAY
    ).values_list('id', flat=True)

    with transaction.atomic():

        for center_id in centers:

            operators = list(
                Operator.objects.filter(
                    center_id=center_id,
                    is_archived=False
                )
            )

            if not operators:
                continue

            leads = Lead.objects.filter(
                center_id=center_id,
                status=LEAD_STATUS.NEW,
                operator__isnull=True
            )

            operator_count = len(operators)

            for index, lead in enumerate(leads):
                operator = operators[index % operator_count]
                lead.operator = operator
                lead.save(update_fields=['operator'])


def assign_for_new_lead(lead: Lead):
    if not lead.center:
        return lead
    if lead.center.lead_consolidation == LEAD_CONSOLIDATION.AUTO:
        return auto_assign(lead)
    return lead
