from django.db import models
from django.contrib.auth.models import User

from materials.models import ClassLevel, Subject


class Exam(models.Model):

    EXAM_TYPE_CHOICES = [
        ('mcq', 'Multiple Choice'),
        ('one_line', 'One Line Answer'),
        ('photo_upload', 'Photo Upload Answer'),
    ]

    title = models.CharField(max_length=200)

    class_level = models.ForeignKey(
        ClassLevel,
        on_delete=models.CASCADE
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
    )

    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPE_CHOICES
    )

    duration_minutes = models.PositiveIntegerField(default=30)

    total_marks = models.PositiveIntegerField(default=0)

    allowed_students = models.ManyToManyField(
        User,
        blank=True
    )

    is_published = models.BooleanField(default=False)

    result_published = models.BooleanField(default=False)

    allow_reattempt = models.BooleanField(default=False)

    show_answer_review = models.BooleanField(default=False)

    answer_pdf = models.FileField(
        upload_to='exam_answer_pdfs/',
        blank=True,
        null=True
    )

    show_answer_pdf = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    question_text = models.TextField()

    question_image = models.FileField(
        upload_to='exam_question_images/',
        blank=True,
        null=True
    )

    mark = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.question_text[:50]


class Choice(models.Model):

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices'
    )

    choice_text = models.CharField(max_length=300)

    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.choice_text


class ExamResult(models.Model):

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    is_submitted = models.BooleanField(default=False)

    score = models.FloatField(default=0)

    is_evaluated = models.BooleanField(default=False)

    manual_feedback = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'exam')

    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"


class StudentAnswer(models.Model):

    result = models.ForeignKey(
        ExamResult,
        on_delete=models.CASCADE,
        related_name='answers'
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )

    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    one_line_answer = models.TextField(blank=True, null=True)

    answer_photo = models.FileField(
        upload_to='exam_answers/',
        blank=True,
        null=True
    )

    marks_awarded = models.FloatField(default=0)

    def __str__(self):
        return f"{self.result.student.username} - {self.question.question_text[:30]}"
