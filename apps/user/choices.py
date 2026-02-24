from django.db import models

class GENDER(models.TextChoices):
    MALE='male','Male'
    FEMALE='female','Female'
    
class ROLE(models.TextChoices):
    USER='user','User'
    ADMIN='admin','Admin'
    OPERATOR='operator','Operator'
    MANAGER='meneger','Meneger'
    CEO='ceo','Ceo'
    STUDENT='student','Student'