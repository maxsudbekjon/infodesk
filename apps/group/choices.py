from django.db import models


class GROUP_DAYS_CHOICES(models.TextChoices):
    ODD_DAYS='odd_days','Odd days'
    EVEN_DAYS='even_days','Even days'
    EVERAY_DAY='every_day', 'Every day'

class GROUP_STATUS(models.TextChoices):
    ACTIVE='active','Active'
    ARCHIVED='archived','Archived'
    TEST_LESSON='test_lesson','Test lesson'
    FROZEN='frozen','Frozen'
    