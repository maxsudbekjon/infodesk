from django.db import models

class GENDER(models.TextChoices):
    MALE='male','Erkak'
    FEMALE='female','Ayol'
    
class ROLE(models.TextChoices):
    USER='user','Foydalanuvchi'
    ADMIN='admin','Administrator'
    MANAGER='meneger','Menejer'
    CEO='ceo','Direktor'
    TEACHER='teacher','O\'qituvchi'
    STUDENT='student','O\'quvchi'
