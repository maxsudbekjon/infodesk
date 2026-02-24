from django.db import models

class STUDENT_PAYMENT(models.TextChoices):
    NEAR_PAYMENT = 'near payment','Near payment'
    DEBTOR = 'debtor','Debtor'
    NO_DEBT= 'no debt', 'No debt'
    OVER_PAYMENT='over payment','Over payment'
    