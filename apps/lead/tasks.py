from celery import shared_task

from apps.lead.services import once_a_day

@shared_task
def daily_lead_job():

    once_a_day()