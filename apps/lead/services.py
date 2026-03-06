from django.db import transaction
from django.db.models import Count, Q

from apps.lead.models import Lead
from apps.lead.choices import LEAD_STATUS
from apps.settings.choices import LEAD_CONSOLIDATION
from apps.settings.models import Organization
from apps.user.models import Operator
PENALTY_THRESHOLD = 10      # Shu baldan past = "yaxshi" operator
LEAD_COUNT_THRESHOLD = 7   # Shu sondan ko'p lead bo'lsa, jarimalini ham ko'rib chiq


# operatorlarni hozirgi load bo'yicha olish
def get_operators_by_load(center_id):
    return list(
        Operator.objects
        .filter(
            center_id=center_id,
            is_archived=False
        )
        .annotate(
            new_leads_count=Count(
                "leads",
                filter=Q(leads__status=LEAD_STATUS.NEW)
            )
        )
        .order_by("new_leads_count", "id")
        .only("id")
    )


# lead tushishi bilan operator biriktiradi
def auto_assign(lead: Lead):
    if not lead.center:
        return lead
    if lead.center.lead_consolidation != LEAD_CONSOLIDATION.AUTO:
        return lead

    base_qs = (
        Operator.objects
        .filter(
            is_archived=False,
            center=lead.center
        )
        .annotate(
            new_leads_count=Count(
                "leads",
                filter=Q(leads__status=LEAD_STATUS.NEW)
            )
        )
    )

    # 1-qadam: Jarima bali yo'q yoki threshold dan past operatorlar
    good_operators = (
        base_qs
        .filter(penalty_point__lt=PENALTY_THRESHOLD)
        .order_by("new_leads_count", "-bonus_point", "id")  # ← teng bo'lsa bonus_point ko'piga
    )

    operator = None
    best_good = good_operators.first()

    if best_good and best_good.new_leads_count < LEAD_COUNT_THRESHOLD:
        operator = best_good
    else:
        operator = (
            base_qs
            .order_by("new_leads_count", "-bonus_point", "id")  # ← bu yerda ham
            .first()
        )

    if not operator:
        return lead

    # Race condition oldini olish
    updated = (
        Lead.objects
        .filter(
            id=lead.id,
            operator__isnull=True
        )
        .update(operator=operator)
    )

    if updated:
        lead.operator = operator

    return lead


# kuniga bir marta leadlarni operatorlarga taqsimlaydi
def once_a_day(batch_size=2000):

    centers = (
        Organization.objects
        .filter(
            lead_consolidation=LEAD_CONSOLIDATION.ONCE_A_DAY
        )
        .values_list("id", flat=True)
    )

    for center_id in centers:

        operators = get_operators_by_load(center_id)

        if not operators:
            continue

        operator_count = len(operators)

        while True:

            with transaction.atomic():

                leads = list(
                    Lead.objects
                    .select_for_update(skip_locked=True)
                    .filter(
                        center_id=center_id,
                        status=LEAD_STATUS.NEW,
                        operator__isnull=True
                    )
                    .only("id")
                    .order_by("id")[:batch_size]
                )

                if not leads:
                    break

                for index, lead in enumerate(leads):
                    lead.operator_id = operators[index % operator_count].id

                Lead.objects.bulk_update(leads, ["operator"])


def assign_for_new_lead(lead: Lead):

    if not lead.center:
        return lead

    if lead.center.lead_consolidation == LEAD_CONSOLIDATION.AUTO:
        return auto_assign(lead)

    return lead