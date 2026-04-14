from django.db import models

class LEAD_STATUS(models.TextChoices):
    NEW='new','Yangi'
    PROCESS='process','Bog\'langan'
    CANCELED='canceled','Bekor qilingan'
    SOLD='sold','Sotilgan'



class LEAD_TEMPERATURE(models.TextChoices):
    HOT='hot','Issiq'
    COOL='cool','Iliq'
    COLD='cold','Sovuq'
    
