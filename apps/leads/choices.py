from django.db import models

class LEAD_STATUS(models.TextChoices):
    NEW='new','New'

class LEAD_SOURCE(models.TextChoices):
    TELEGRAM='telegram','Telergam'
    INSTAGRAM='instagram','Instagram'
    FACEBOOK='facebook','Facebook'
    WHATSAPP='whatsapp','Whatsapp'
    OTHER='other','Other'

class LEAD_TEMPERATURE(models.TextChoices):
    HOT='hot','Hot'
    COOL='cool','Cool'
    WORM='worm','Worm'
    