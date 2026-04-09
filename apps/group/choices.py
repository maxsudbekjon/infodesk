from django.db import models


class GROUP_DAYS_CHOICES(models.TextChoices):
    ODD_DAYS='odd_days','Toq kunlar'
    EVEN_DAYS='even_days','Juft kunlar'
    EVERAY_DAY='every_day', 'Har kuni'

class GROUP_STATUS(models.TextChoices):
    ACTIVE='active','Faol'
    ARCHIVED='archived','Arxiv'
    TEST_LESSON='test_lesson','Sinov darsi'
    FROZEN='frozen','To\'xtatilgan'
    
