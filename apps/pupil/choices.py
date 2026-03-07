from django.db import models

class STUDENT_PAYMENT(models.TextChoices):
    NEAR_PAYMENT = 'near payment','Near payment'
    DEBTOR = 'debtor','Debtor'
    NO_DEBT= 'no debt', 'No debt'
    OVER_PAYMENT='over payment','Over payment'
    
class STUDENT_STATUS(models.TextChoices):
    ACTIVE='avtive','Active'
    FROZEN='frozen','Frozen'
    ARCHIVED='archived','Archived'
    LEAD='lead','Lead'

class TRANSFER_REASON(models.TextChoices):
    FAR='far','Far'

class DISCOUNT_TYPE(models.TextChoices):
    COURSE_END='course_end','Course_end'
    SPECIFIC_MONTH='specific_month','Specific_month'