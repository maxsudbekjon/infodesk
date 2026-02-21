from django.db import models


class GROUP_DAYS_CHOICES(models.TextChoices):
    ODD_DAYS='odd days','Odd days'
    EVEN_DAYS='even days','Even days'

class GROUP_STATUS(models.TextChoices):
    ACTIVE='active','Active'
    ARCHIVED='archived','Archived'
    TEST_LESSON='test lesson','Test lesson'
    FROZEN='frozen','Frozen'
    