from django.db import models

class LEAD_STATUS(models.TextChoices):
    NEW='new','New'
    PROCESS='process','Process'
    CANSELED='canseled','Canseled'
    SOLD='sold','Sold'



class LEAD_TEMPERATURE(models.TextChoices):
    HOT='hot','Hot'
    COOL='cool','Cool'
    WORM='worm','Worm'
    