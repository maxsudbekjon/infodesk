from django.db import models

class LEAD_CONSOLIDATION(models.TextChoices):
    MANUAL='manual','Manual'
    ONCE_A_DAY='once a day','Once A Day' # kuniga bir marta leadlarga operator biriktiriladi.
    AUTO='auto','Auto' # lead tushishi bilan  operaor biriktiriladi