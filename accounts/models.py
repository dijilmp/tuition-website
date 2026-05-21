from django.db import models
from django.contrib.auth.models import User
from materials.models import ClassLevel


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username