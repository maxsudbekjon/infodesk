from celery import shared_task

from apps.lead.choices import LEAD_STATUS
from apps.lead.models.lead import Lead
from apps.lead.services import once_a_day
from celery import shared_task
from django.utils import timezone
from django.db.models import Q, F
from datetime import timedelta

from apps.settings.choices import LEAD_CONSOLIDATION
from apps.user.models.operator import Operator

PENALTY_DAYS_THRESHOLD = 5      # Necha kundan keyin jarima
PENALTY_POINTS = 5 



@shared_task
def daily_lead_job():
    once_a_day()

@shared_task
def penalize_operators_for_stale_leads():
    threshold_date = timezone.now() - timedelta(days=PENALTY_DAYS_THRESHOLD)

    stale_leads = (
        Lead.objects
        .filter(
            status=LEAD_STATUS.NEW,
            operator__isnull=False,
            created_at__lte=threshold_date
        )
        .exclude(
            center__lead_consolidation=LEAD_CONSOLIDATION.MANUAL
        )
    )

    operator_ids = (
        stale_leads
        .values_list("operator_id", flat=True)
        .distinct()
    )

    if not operator_ids:
        return "No stale leads found."

    operators = Operator.objects.filter(id__in=operator_ids)

    for operator in operators:
        if operator.bonus_point >= PENALTY_POINTS:
            # Bonus yetarli → faqat bonusdan ayir
            operator.bonus_point -= PENALTY_POINTS
        elif operator.bonus_point > 0:
            # Bonus bor lekin yetarsiz → bonus 0, qolganini jarimaga yoz
            remaining_penalty = PENALTY_POINTS - operator.bonus_point
            operator.bonus_point = 0
            operator.penalty_point += remaining_penalty
        else:
            # Bonus yo'q → to'liq jarima
            operator.penalty_point += PENALTY_POINTS

    Operator.objects.bulk_update(operators, ["bonus_point", "penalty_point"])

    return f"Penalized {len(operators)} operators for stale leads."


# tasks.py
@shared_task
def process_sold_lead(lead_id: int):
    BONUS_POINTS = 5  # Sotilgan lead uchun bonus

    lead = Lead.objects.select_related("operator").get(id=lead_id)
    
    lead.status = LEAD_STATUS.SOLD
    lead.save(update_fields=["status"])

    operator = lead.operator
    if not operator:
        return f"Lead {lead_id} has no operator, status updated only."

    if operator.penalty_point >= BONUS_POINTS:
        operator.penalty_point -= BONUS_POINTS
    elif operator.penalty_point > 0:
        remaining_bonus = BONUS_POINTS - operator.penalty_point
        operator.penalty_point = 0
        operator.bonus_point += remaining_bonus
    else:
        operator.bonus_point += BONUS_POINTS

    operator.save(update_fields=["bonus_point", "penalty_point"])

    return f"Lead {lead_id} sold, operator {operator.id} points updated."