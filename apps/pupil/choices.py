from django.db import models

class STUDENT_PAYMENT(models.TextChoices):
    NEAR_PAYMENT = 'near payment','To\'lov yaqin'
    DEBTOR = 'debtor','Qarzdor'
    NO_DEBT= 'no debt', 'To\'langan'
    OVER_PAYMENT='over payment','Ortiqcha to\'lov'
    
class STUDENT_STATUS(models.TextChoices):
    ACTIVE='avtive','Faol'
    FROZEN='frozen','To\'xtatilgan'
    ARCHIVED='archived','Arxiv'
    LEAD='lead','Lid'

class TRANSFER_REASON(models.TextChoices):
    FAR='far','Uzoq'

class DISCOUNT_TYPE(models.TextChoices):
    COURSE_END='course_end','Kurs oxiri'
    SPECIFIC_MONTH='specific_month','Aniq oy'
