from django.db import models
from django.contrib.auth.models import User

from materials.models import ClassLevel, Subject


class Exam(models.Model):

    EXAM_TYPE_CHOICES = [
        ('mcq', 'Multiple Choice'),
        ('one_line', 'One Line Answer'),
        ('photo_upload', 'Photo Upload Answer'),
        ('question_paper_upload', 'Question Paper + Bulk Answer Upload'),
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
        max_length=30,
        choices=EXAM_TYPE_CHOICES
    )

    duration_minutes = models.PositiveIntegerField(default=30)

    total_marks = models.PositiveIntegerField(default=0)

    question_paper_file = models.FileField(
        upload_to='exam_question_papers/',
        blank=True,
        null=True,
        max_length=255,
        help_text='Use only for Question Paper + Bulk Answer Upload exam. Upload PDF or image.'
    )

    allowed_students = models.ManyToManyField(
        User,
        blank=True
    )

    is_published = models.BooleanField(default=False)

    result_published = models.BooleanField(default=False)

    # New MCQ exams default to private results. Existing exams are backfilled in 0010.
    publish_marks = models.BooleanField(default=False)
    publish_ranks = models.BooleanField(default=False)
    publish_answer_keys = models.BooleanField(default=False)

    instructions_enabled = models.BooleanField(default=False)
    declaration_required = models.BooleanField(default=True)
    candidate_instructions = models.TextField(blank=True, default='')

    question_bank = models.ManyToManyField(
        'Question', through='ExamQuestion', related_name='mapped_exams', blank=True
    )

    allow_reattempt = models.BooleanField(default=False)

    show_answer_review = models.BooleanField(default=False)

    answer_pdf = models.FileField(
        upload_to='exam_answer_pdfs/',
        blank=True,
        null=True,
        max_length=255
    )

    show_answer_pdf = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def question_paper_is_pdf(self):
        if not self.question_paper_file:
            return False

        return self.question_paper_file.name.lower().endswith('.pdf')

    @property
    def question_paper_is_image(self):
        if not self.question_paper_file:
            return False

        lower_name = self.question_paper_file.name.lower()

        return lower_name.endswith((
            '.jpg',
            '.jpeg',
            '.png',
            '.webp',
            '.gif'
        ))


class Question(models.Model):

    # Legacy link retained for backwards compatibility with existing rows.
    # New questions are independently created in the reusable bank.
    exam = models.ForeignKey(
        Exam, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='legacy_questions'
    )

    question_text = models.TextField()

    question_image = models.FileField(
        upload_to='exam_question_images/',
        blank=True,
        null=True,
        max_length=255
    )

    mark = models.PositiveIntegerField(default=1)
    class_level = models.ForeignKey(ClassLevel, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='bank_questions')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='bank_questions')
    topic = models.CharField(max_length=120, blank=True, default='')
    difficulty = models.CharField(
        max_length=10, default='medium',
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
    )

    def __str__(self):
        return self.question_text[:50]


class ExamQuestion(models.Model):
    """Many-to-many link: reusable question + exam-specific mark/order."""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_questions')
    question = models.ForeignKey('Question', on_delete=models.PROTECT, related_name='exam_links')
    position = models.PositiveIntegerField(default=0)
    mark = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['exam', 'question'], name='unique_exam_question')]
        ordering = ('position', 'id')

    def __str__(self):
        return f'{self.exam.title}: {self.question}'


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

    instructions_accepted_at = models.DateTimeField(null=True, blank=True)
    # Per-attempt immutable MCQ definitions (including marking scheme), never sent in full to client.
    question_snapshot = models.JSONField(default=list, blank=True)

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

    submitted_answer_pdf = models.FileField(
        upload_to='exam_submitted_answer_pdfs/',
        blank=True,
        null=True,
        max_length=255,
        help_text='Auto-generated PDF created from the student uploaded answer images.'
    )

    teacher_corrected_pdf = models.FileField(
        upload_to='exam_teacher_corrected_pdfs/',
        blank=True,
        null=True,
        max_length=255,
        help_text='Upload the teacher-valued/corrected PDF after marking the student answer PDF.'
    )

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

    # Keep attempted questions intact for historical result review.
    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT
    )

    # IDs survive updates to the reusable bank's choices.
    selected_choice_id_snapshot = models.BigIntegerField(null=True, blank=True)
    client_revision = models.PositiveIntegerField(default=0)

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
        null=True,
        max_length=255
    )

    marks_awarded = models.FloatField(default=0)

    def __str__(self):
        return f"{self.result.student.username} - {self.question.question_text[:30]}"


class BulkAnswerImage(models.Model):

    result = models.ForeignKey(
        ExamResult,
        on_delete=models.CASCADE,
        related_name='bulk_answer_images'
    )

    answer_image = models.FileField(
        upload_to='exam_bulk_answer_images/',
        max_length=255
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Bulk Answer Image'
        verbose_name_plural = 'Bulk Answer Images'

    def __str__(self):
        return f"{self.result.student.username} - {self.result.exam.title} - Page {self.order}"
