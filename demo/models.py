from django.db import models
from django.utils import timezone


class DemoCategory(models.Model):

    CATEGORY_CHOICES = [
        ('uss', 'USS'),
        ('nmms', 'NMMS / NMCM'),
        ('school_tuition', 'School Tuition'),
    ]

    category_type = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        unique=True
    )

    display_name = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'display_name']
        verbose_name = 'Demo Category'
        verbose_name_plural = 'Demo Categories'

    def __str__(self):
        return self.display_name


class DemoOption(models.Model):

    SYLLABUS_CHOICES = [
        ('state', 'State'),
        ('cbse', 'CBSE'),
        ('icse', 'ICSE'),
    ]

    MEDIUM_CHOICES = [
        ('english', 'English'),
        ('malayalam', 'Malayalam'),
        ('tamil', 'Tamil'),
        ('kannada', 'Kannada'),
    ]

    category = models.ForeignKey(
        DemoCategory,
        on_delete=models.CASCADE,
        related_name='options'
    )

    title = models.CharField(
        max_length=200,
        help_text='Example: State Class 10 Maths Demo / USS Demo / NMMS Class 8 Demo'
    )

    class_name = models.CharField(
        max_length=50,
        help_text='Example: Class 8, Class 9, Class 10'
    )

    subject_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Example: Maths, Physics, Chemistry. Leave blank for USS/NMMS if not needed.'
    )

    syllabus = models.CharField(
        max_length=20,
        choices=SYLLABUS_CHOICES,
        default='state'
    )

    medium = models.CharField(
        max_length=20,
        choices=MEDIUM_CHOICES,
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = [
            'category',
            'order',
            'class_name',
            'subject_name',
            'title',
        ]
        verbose_name = 'Available Demo'
        verbose_name_plural = 'Available Demos'

    def __str__(self):
        parts = [
            self.category.display_name,
            self.class_name,
        ]

        if self.subject_name:
            parts.append(self.subject_name)

        parts.append(self.get_syllabus_display())

        if self.medium:
            parts.append(self.get_medium_display() + ' Medium')

        return ' - '.join(parts)


class DemoRequest(models.Model):

    demo_option = models.ForeignKey(
        DemoOption,
        on_delete=models.CASCADE,
        related_name='requests'
    )

    name = models.CharField(max_length=150)

    mobile_number = models.CharField(max_length=20)

    address = models.TextField()

    school_name = models.CharField(max_length=200)

    view_count = models.PositiveIntegerField(default=1)

    first_viewed_at = models.DateTimeField(auto_now_add=True)

    last_viewed_at = models.DateTimeField(auto_now=True)

    is_contacted = models.BooleanField(default=False)

    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('demo_option', 'mobile_number')
        ordering = ['-last_viewed_at']
        verbose_name = 'Demo Request'
        verbose_name_plural = 'Demo Requests'

    def __str__(self):
        return f'{self.name} - {self.mobile_number} - {self.demo_option}'


class DemoNotice(models.Model):

    demo_option = models.OneToOneField(
        DemoOption,
        on_delete=models.CASCADE,
        related_name='notice'
    )

    heading = models.CharField(
        max_length=200,
        default='Important Updates'
    )

    exam_date = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    scholarship_amount = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    registration_start_date = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    registration_end_date = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    message = models.TextField(
        blank=True,
        null=True,
        help_text='Admin can update this message frequently.'
    )

    is_active = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Demo Notice'
        verbose_name_plural = 'Demo Notices'

    def __str__(self):
        return f'Notice - {self.demo_option}'


class DemoStudyMaterial(models.Model):

    demo_option = models.ForeignKey(
        DemoOption,
        on_delete=models.CASCADE,
        related_name='study_materials'
    )

    title = models.CharField(max_length=200)

    chapter_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    description = models.TextField(blank=True, null=True)

    pdf_file = models.FileField(
        upload_to='demo/study_materials/',
        blank=True,
        null=True
    )

    external_link = models.URLField(
        blank=True,
        null=True,
        help_text='Optional YouTube/Drive/link'
    )

    is_published = models.BooleanField(default=True)

    order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['demo_option', 'order', 'title']
        verbose_name = 'Demo Study Material'
        verbose_name_plural = 'Demo Study Materials'

    def __str__(self):
        return f'{self.demo_option} - {self.title}'


class DemoMockTest(models.Model):

    demo_option = models.ForeignKey(
        DemoOption,
        on_delete=models.CASCADE,
        related_name='mock_tests'
    )

    title = models.CharField(max_length=200)

    chapter_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    description = models.TextField(blank=True, null=True)

    mock_number = models.PositiveIntegerField(
        default=1
    )

    question_pdf = models.FileField(
        upload_to='demo/mock_tests/questions/',
        blank=True,
        null=True
    )

    answer_key_pdf = models.FileField(
        upload_to='demo/mock_tests/answer_keys/',
        blank=True,
        null=True
    )

    external_test_link = models.URLField(
        blank=True,
        null=True,
        help_text='Optional online test link. This will not touch existing exam system.'
    )

    is_published = models.BooleanField(default=True)

    order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['demo_option', 'order', 'mock_number', 'title']
        verbose_name = 'Demo Mock Test'
        verbose_name_plural = 'Demo Mock Tests'

    def __str__(self):
        return f'{self.demo_option} - {self.title}'


class DemoOnlineTest(models.Model):

    demo_option = models.ForeignKey(
        DemoOption,
        on_delete=models.CASCADE,
        related_name='online_tests'
    )

    title = models.CharField(max_length=200)

    chapter_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    description = models.TextField(blank=True, null=True)

    duration_minutes = models.PositiveIntegerField(default=30)

    total_marks = models.PositiveIntegerField(default=0)

    show_result_after_submit = models.BooleanField(default=True)

    allow_reattempt = models.BooleanField(default=False)

    is_published = models.BooleanField(default=True)

    order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['demo_option', 'order', 'title']
        verbose_name = 'Demo Online MCQ Test'
        verbose_name_plural = 'Demo Online MCQ Tests'

    def __str__(self):
        return f'{self.demo_option} - {self.title}'


class DemoOnlineQuestion(models.Model):

    online_test = models.ForeignKey(
        DemoOnlineTest,
        on_delete=models.CASCADE,
        related_name='questions'
    )

    question_text = models.TextField()

    question_image = models.FileField(
        upload_to='demo/online_questions/',
        blank=True,
        null=True
    )

    marks = models.PositiveIntegerField(default=1)

    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Demo Online Question'
        verbose_name_plural = 'Demo Online Questions'

    def __str__(self):
        return self.question_text[:80]


class DemoOnlineChoice(models.Model):

    question = models.ForeignKey(
        DemoOnlineQuestion,
        on_delete=models.CASCADE,
        related_name='choices'
    )

    choice_text = models.CharField(max_length=400)

    is_correct = models.BooleanField(default=False)

    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Demo Online Choice'
        verbose_name_plural = 'Demo Online Choices'

    def __str__(self):
        return self.choice_text


class DemoOnlineAttempt(models.Model):

    demo_request = models.ForeignKey(
        DemoRequest,
        on_delete=models.CASCADE,
        related_name='online_attempts'
    )

    online_test = models.ForeignKey(
        DemoOnlineTest,
        on_delete=models.CASCADE,
        related_name='attempts'
    )

    started_at = models.DateTimeField(auto_now_add=True)

    submitted_at = models.DateTimeField(
        blank=True,
        null=True
    )

    is_submitted = models.BooleanField(default=False)

    score = models.FloatField(default=0)

    class Meta:
        ordering = ['-started_at']
        unique_together = ('demo_request', 'online_test')
        verbose_name = 'Demo Online Attempt'
        verbose_name_plural = 'Demo Online Attempts'

    def __str__(self):
        return f'{self.demo_request.mobile_number} - {self.online_test.title}'


class DemoOnlineAnswer(models.Model):

    attempt = models.ForeignKey(
        DemoOnlineAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )

    question = models.ForeignKey(
        DemoOnlineQuestion,
        on_delete=models.CASCADE
    )

    selected_choice = models.ForeignKey(
        DemoOnlineChoice,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    is_correct = models.BooleanField(default=False)

    marks_awarded = models.FloatField(default=0)

    class Meta:
        unique_together = ('attempt', 'question')
        verbose_name = 'Demo Online Answer'
        verbose_name_plural = 'Demo Online Answers'

    def __str__(self):
        return f'{self.attempt} - {self.question.id}'
