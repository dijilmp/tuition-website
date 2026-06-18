from django.contrib import admin

from .models import (
    DemoCategory,
    DemoOption,
    DemoRequest,
    DemoNotice,
    DemoStudyMaterial,
    DemoMockTest,
    DemoOnlineTest,
    DemoOnlineQuestion,
    DemoOnlineChoice,
    DemoOnlineAttempt,
    DemoOnlineAnswer,
)


@admin.register(DemoCategory)
class DemoCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'display_name',
        'category_type',
        'is_active',
        'order',
    ]

    list_filter = [
        'category_type',
        'is_active',
    ]

    search_fields = [
        'display_name',
        'description',
    ]


@admin.register(DemoOption)
class DemoOptionAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'category',
        'class_name',
        'subject_name',
        'syllabus',
        'medium',
        'is_active',
        'order',
    ]

    list_filter = [
        'category',
        'syllabus',
        'medium',
        'is_active',
        'class_name',
        'subject_name',
    ]

    search_fields = [
        'title',
        'class_name',
        'subject_name',
        'description',
    ]

    fields = [
        'category',
        'title',
        'class_name',
        'subject_name',
        'syllabus',
        'medium',
        'description',
        'is_active',
        'order',
    ]


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'mobile_number',
        'demo_option',
        'view_count',
        'last_viewed_at',
        'is_contacted',
    ]

    list_filter = [
        'demo_option__category',
        'demo_option',
        'is_contacted',
    ]

    search_fields = [
        'name',
        'mobile_number',
        'school_name',
        'address',
    ]

    readonly_fields = [
        'view_count',
        'first_viewed_at',
        'last_viewed_at',
    ]


@admin.register(DemoNotice)
class DemoNoticeAdmin(admin.ModelAdmin):
    list_display = [
        'demo_option',
        'heading',
        'exam_date',
        'scholarship_amount',
        'registration_end_date',
        'is_active',
        'updated_at',
    ]

    list_filter = [
        'demo_option__category',
        'is_active',
    ]

    search_fields = [
        'heading',
        'message',
        'demo_option__title',
    ]


@admin.register(DemoStudyMaterial)
class DemoStudyMaterialAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'demo_option',
        'chapter_name',
        'is_published',
        'order',
    ]

    list_filter = [
        'demo_option__category',
        'demo_option',
        'is_published',
    ]

    search_fields = [
        'title',
        'chapter_name',
        'description',
        'demo_option__title',
    ]


@admin.register(DemoMockTest)
class DemoMockTestAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'demo_option',
        'mock_number',
        'chapter_name',
        'is_published',
        'order',
    ]

    list_filter = [
        'demo_option__category',
        'demo_option',
        'mock_number',
        'is_published',
    ]

    search_fields = [
        'title',
        'chapter_name',
        'description',
        'demo_option__title',
    ]


class DemoOnlineChoiceInline(admin.TabularInline):
    model = DemoOnlineChoice
    extra = 4
    fields = [
        'order',
        'choice_text',
        'is_correct',
    ]


class DemoOnlineQuestionInline(admin.StackedInline):
    model = DemoOnlineQuestion
    extra = 1
    fields = [
        'order',
        'question_text',
        'question_image',
        'marks',
    ]


@admin.register(DemoOnlineTest)
class DemoOnlineTestAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'demo_option',
        'duration_minutes',
        'total_marks',
        'is_published',
        'allow_reattempt',
        'order',
    ]

    list_filter = [
        'demo_option__category',
        'demo_option',
        'is_published',
        'allow_reattempt',
    ]

    search_fields = [
        'title',
        'chapter_name',
        'description',
        'demo_option__title',
    ]

    fields = [
        'demo_option',
        'title',
        'chapter_name',
        'description',
        'duration_minutes',
        'total_marks',
        'show_result_after_submit',
        'allow_reattempt',
        'is_published',
        'order',
    ]

    inlines = [
        DemoOnlineQuestionInline,
    ]


@admin.register(DemoOnlineQuestion)
class DemoOnlineQuestionAdmin(admin.ModelAdmin):
    list_display = [
        'online_test',
        'order',
        'question_preview',
        'marks',
    ]

    list_filter = [
        'online_test__demo_option__category',
        'online_test',
    ]

    search_fields = [
        'question_text',
        'online_test__title',
    ]

    inlines = [
        DemoOnlineChoiceInline,
    ]

    def question_preview(self, obj):
        return obj.question_text[:80]

    question_preview.short_description = 'Question'


@admin.register(DemoOnlineChoice)
class DemoOnlineChoiceAdmin(admin.ModelAdmin):
    list_display = [
        'question',
        'order',
        'choice_text',
        'is_correct',
    ]

    list_filter = [
        'is_correct',
        'question__online_test',
    ]

    search_fields = [
        'choice_text',
        'question__question_text',
    ]


class DemoOnlineAnswerInline(admin.TabularInline):
    model = DemoOnlineAnswer
    extra = 0
    readonly_fields = [
        'question',
        'selected_choice',
        'is_correct',
        'marks_awarded',
    ]

    fields = [
        'question',
        'selected_choice',
        'is_correct',
        'marks_awarded',
    ]


@admin.register(DemoOnlineAttempt)
class DemoOnlineAttemptAdmin(admin.ModelAdmin):
    list_display = [
        'demo_request',
        'online_test',
        'score',
        'is_submitted',
        'submitted_at',
    ]

    list_filter = [
        'online_test__demo_option__category',
        'online_test',
        'is_submitted',
    ]

    search_fields = [
        'demo_request__name',
        'demo_request__mobile_number',
        'online_test__title',
    ]

    readonly_fields = [
        'started_at',
        'submitted_at',
    ]

    inlines = [
        DemoOnlineAnswerInline,
    ]


@admin.register(DemoOnlineAnswer)
class DemoOnlineAnswerAdmin(admin.ModelAdmin):
    list_display = [
        'attempt',
        'question',
        'selected_choice',
        'is_correct',
        'marks_awarded',
    ]

    list_filter = [
        'is_correct',
        'attempt__online_test',
    ]
