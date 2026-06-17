from django.db import models
from django.contrib.auth.models import User

from materials.models import ClassLevel, Subject


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    class_level = models.ForeignKey(
        ClassLevel,
        on_delete=models.CASCADE
    )

    subjects = models.ManyToManyField(
        Subject,
        blank=True
    )

    def __str__(self):
        return self.user.username


class RegistrationEnquiry(models.Model):

    TRAINING_CHOICES = [
        ('uss', 'USS Exam'),
        ('nmms', 'National Means-cum-Merit'),
        ('school_subjects', 'School Subjects'),
    ]

    SYLLABUS_CHOICES = [
        ('state', 'State'),
        ('cbse', 'CBSE'),
        ('icse', 'ICSE'),
    ]

    MEDIUM_CHOICES = [
        ('english', 'English'),
        ('malayalam', 'Malayalam'),
        ('kannada', 'Kannada'),
        ('tamil', 'Tamil'),
    ]

    CLASS_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('group', 'Group'),
    ]

    training_needed = models.CharField(
        max_length=30,
        choices=TRAINING_CHOICES
    )

    name = models.CharField(max_length=150)

    phone_number = models.CharField(max_length=20)

    address = models.TextField()

    student_class = models.CharField(max_length=50)

    syllabus = models.CharField(
        max_length=20,
        choices=SYLLABUS_CHOICES
    )

    medium = models.CharField(
        max_length=20,
        choices=MEDIUM_CHOICES,
        blank=True,
        null=True
    )

    school_name = models.CharField(max_length=200)

    class_type = models.CharField(
        max_length=20,
        choices=CLASS_TYPE_CHOICES
    )

    created_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='registration_enquiries'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    is_contacted = models.BooleanField(default=False)

    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = [
            'training_needed',
            'student_class',
            '-created_at',
        ]

    def __str__(self):
        return f"{self.name} - {self.get_training_needed_display()}"
