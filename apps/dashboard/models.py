from datetime import date
from django.db import models
from django.conf import settings
# from apps import managers
from apps.base_models import TimeStampedModel


class Center(TimeStampedModel):
    # class PAYMENT_TYPE(models.TextChoices):
    #     ROLLING_MONTH='polling month','Rolling Month' #Rolling Month = pay every 30 days from your start date.
    #     LESSON_12_PACKAGE='lesson 12 package','Lesson 12 package' # pay per 12 classes.
    #     CALENDAR_MONTH='calendar month','Calendar Month' # Calendar Month = pay on the 1st of each month.
        
    # payment_type=models.CharField(max_length=20,choices=PAYMENT_TYPE.choices,default=PAYMENT_TYPE.ROLLING_MONTH)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='centers'
    )
    title = models.CharField(
        max_length=31,
    )
    description = models.TextField(
        blank=True,
        null=True
    )
    image = models.ImageField(
        upload_to='center/%Y/%m/%d',
        blank=True,
        null=True
    )
    # pay_per_hour = models.DecimalField(
    #     max_digits=10,
    #     decimal_places=2,
    #     null=True,
    #     blank=True,
    #     help_text="O'qituvchi soatiga oladigan summa"
    # )
    # pay_per_student = models.DecimalField(
    #     max_digits=10,
    #     decimal_places=2,
    #     null=True,
    #     blank=True,
    #     help_text="Har bir o'quvchi uchun beriladigan summa"
    # )
    # percentage_of_income = models.DecimalField(
    #     max_digits=5,
    #     decimal_places=2,
    #     null=True,
    #     blank=True,
    #     help_text="O'quvchi to'lovidan o'qituvchi ulushi (%)")
    payday=models.DateField(default=date.today)
    class Meta:
        ordering = ('-created_at',)
        unique_together = ('owner', 'title')


    def __str__(self):
        return self.title


class Branch(TimeStampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='branches'
    )
    center = models.ForeignKey(
        Center,
        on_delete=models.CASCADE,
        related_name='branches'
    )
    title = models.CharField(
        max_length=31,
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Filial haqida qo'shimcha ma'lumot"
    )
    address = models.CharField(
        max_length=255,
        blank=True,

    )

    objects = models.Manager()
    # exists = managers.ExistsManager()
    class Meta:
        ordering = ('-created_at',)
        unique_together = ('center', 'title')

    def __str__(self):
        return self.title
