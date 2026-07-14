from io import BytesIO

from django.contrib import admin
from django.urls import path, reverse
from django.http import FileResponse
from django.utils.html import format_html
from django.utils.http import urlencode

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .models import (
    Exam,
    Question,
    Choice,
    ExamResult,
    StudentAnswer
)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'question_text',
        'exam',
        'mark',
        'image_preview',
    )

    search_fields = (
        'question_text',
        'exam__title',
    )

    list_filter = (
        'exam',
    )

    readonly_fields = (
        'image_preview',
    )

    fields = (
        'exam',
        'question_text',
        'question_image',
        'image_preview',
        'mark',
    )

    inlines = [
        ChoiceInline
    ]

    def image_preview(self, obj):
        if obj.question_image:
            return format_html(
                '<img src="{}" style="max-height:120px; max-width:220px; border:1px solid #ccc; padding:4px;" />',
                obj.question_image.url
            )

        return "No image"

    image_preview.short_description = "Question Image Preview"

    class Media:
        js = (
            'admin/js/paste_question_image.js',
        )


class ExamAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'class_level',
        'subject',
        'exam_type',
        'duration_minutes',
        'total_marks',
        'question_paper_available',
        'attempted_count',
        'evaluated_count',
        'is_published',
        'result_published',
        'allow_reattempt',
        'show_answer_review',
        'show_answer_pdf',
        'answer_pdf_available',
        'view_results_link',
        'download_rank_pdf_link',
    )

    list_filter = (
        'class_level',
        'subject',
        'exam_type',
        'is_published',
        'result_published',
        'allow_reattempt',
        'show_answer_review',
        'show_answer_pdf',
    )

    search_fields = (
        'title',
    )

    filter_horizontal = (
        'allowed_students',
    )

    fieldsets = (
        ('Exam Details', {
            'fields': (
                'title',
                'class_level',
                'subject',
                'exam_type',
                'duration_minutes',
                'total_marks',
                'question_paper_file',
            )
        }),
        ('Student Access', {
            'fields': (
                'allowed_students',
            )
        }),
        ('Publish Settings', {
            'fields': (
                'is_published',
                'result_published',
                'allow_reattempt',
                'show_answer_review',
            )
        }),
        ('Answer PDF / Solution', {
            'fields': (
                'answer_pdf',
                'show_answer_pdf',
            )
        }),
    )

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                '<int:exam_id>/download-rank-pdf/',
                self.admin_site.admin_view(self.download_rank_pdf),
                name='exam_download_rank_pdf'
            ),
        ]

        return custom_urls + urls

    def attempted_count(self, obj):
        return ExamResult.objects.filter(
            exam=obj,
            is_submitted=True
        ).count()

    attempted_count.short_description = "Attempted"

    def evaluated_count(self, obj):
        return ExamResult.objects.filter(
            exam=obj,
            is_evaluated=True
        ).count()

    evaluated_count.short_description = "Evaluated"

    def answer_pdf_available(self, obj):
        if obj.answer_pdf:
            return "Yes"

        return "No"

    answer_pdf_available.short_description = "Answer PDF"

    def question_paper_available(self, obj):
        if obj.question_paper_file:
            return "Yes"

        return "No"

    question_paper_available.short_description = "Question Paper"

    def view_results_link(self, obj):
        url = (
            reverse('admin:exams_examresult_changelist')
            + '?'
            + urlencode({'exam__id__exact': obj.id})
        )

        return format_html(
            '<a href="{}">View students & marks</a>',
            url
        )

    view_results_link.short_description = "Student marks"

    def download_rank_pdf_link(self, obj):
        url = reverse(
            'admin:exam_download_rank_pdf',
            args=[obj.id]
        )

        return format_html(
            '<a href="{}" target="_blank">Download Rank PDF</a>',
            url
        )

    download_rank_pdf_link.short_description = "Rank PDF"

    def download_rank_pdf(self, request, exam_id):
        exam = Exam.objects.get(id=exam_id)

        results = ExamResult.objects.filter(
            exam=exam,
            is_submitted=True,
            is_evaluated=True
        ).order_by(
            '-score',
            'submitted_at'
        )

        buffer = BytesIO()

        pdf = canvas.Canvas(buffer, pagesize=A4)

        width, height = A4

        y = height - 50

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawCentredString(
            width / 2,
            y,
            "Master X's Academy"
        )

        y -= 25

        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawCentredString(
            width / 2,
            y,
            "Exam Rank Report"
        )

        y -= 35

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(50, y, f"Exam: {exam.title}")

        y -= 18
        pdf.drawString(50, y, f"Class: {exam.class_level}")

        y -= 18
        pdf.drawString(50, y, f"Subject: {exam.subject.name}")

        y -= 18
        pdf.drawString(50, y, f"Total Marks: {exam.total_marks}")

        y -= 18
        pdf.drawString(50, y, f"Students Attempted: {results.count()}")

        y -= 35

        pdf.setFont("Helvetica-Bold", 10)

        pdf.drawString(50, y, "Rank")
        pdf.drawString(110, y, "Student Name")
        pdf.drawString(330, y, "Mark")
        pdf.drawString(410, y, "Submitted Time")

        y -= 10

        pdf.line(50, y, 550, y)

        y -= 20

        pdf.setFont("Helvetica", 10)

        previous_score = None
        current_rank = 0
        student_position = 0

        for result in results:
            student_position += 1

            if previous_score != result.score:
                current_rank = student_position
                previous_score = result.score

            student = result.student

            student_name = f"{student.first_name} {student.last_name}".strip()

            if not student_name:
                student_name = student.username

            submitted_time = ""

            if result.submitted_at:
                submitted_time = result.submitted_at.strftime(
                    "%d-%m-%Y %I:%M %p"
                )

            pdf.drawString(50, y, str(current_rank))
            pdf.drawString(110, y, student_name[:30])
            pdf.drawString(
                330,
                y,
                f"{result.score:g} / {exam.total_marks}"
            )
            pdf.drawString(410, y, submitted_time)

            y -= 22

            if y < 60:
                pdf.showPage()

                y = height - 50

                pdf.setFont("Helvetica-Bold", 10)

                pdf.drawString(50, y, "Rank")
                pdf.drawString(110, y, "Student Name")
                pdf.drawString(330, y, "Mark")
                pdf.drawString(410, y, "Submitted Time")

                y -= 10

                pdf.line(50, y, 550, y)

                y -= 20

                pdf.setFont("Helvetica", 10)

        pdf.save()

        buffer.seek(0)

        filename = f"{exam.title}_rank_report.pdf"

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type='application/pdf'
        )


class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0

    fields = (
        'question',
        'selected_choice',
        'one_line_answer',
        'answer_photo_link',
        'marks_awarded',
    )

    readonly_fields = (
        'question',
        'selected_choice',
        'one_line_answer',
        'answer_photo_link',
    )

    def answer_photo_link(self, obj):
        if obj.answer_photo:
            return format_html(
                '<a href="{}" target="_blank">Open Answer Photo</a>',
                obj.answer_photo.url
            )

        return "No photo uploaded"

    answer_photo_link.short_description = "Answer Photo"


class ExamResultAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'exam',
        'score',
        'is_submitted',
        'is_evaluated',
        'submitted_answer_pdf_available',
        'started_at',
        'submitted_at',
    )

    list_filter = (
        'exam',
        'is_submitted',
        'is_evaluated',
        'submitted_at',
    )

    search_fields = (
        'student__username',
        'student__first_name',
        'student__last_name',
        'exam__title',
    )

    fields = (
        'student',
        'exam',
        'started_at',
        'submitted_at',
        'is_submitted',
        'submitted_answer_pdf_link',
        'score',
        'is_evaluated',
        'manual_feedback',
    )

    readonly_fields = (
        'submitted_answer_pdf_link',
    )

    inlines = [
        StudentAnswerInline,
    ]

    def submitted_answer_pdf_available(self, obj):
        if obj.submitted_answer_pdf:
            return "Yes"

        return "No"

    submitted_answer_pdf_available.short_description = "Answer PDF"

    def submitted_answer_pdf_link(self, obj):
        if obj.submitted_answer_pdf:
            return format_html(
                '<iframe src="{}#toolbar=0&navpanes=0&scrollbar=1" style="width:100%; min-height:700px; border:1px solid #ddd; border-radius:8px;"></iframe><br><a href="{}" target="_blank">Open answer PDF in new tab</a>',
                obj.submitted_answer_pdf.url,
                obj.submitted_answer_pdf.url
            )

        return "Answer PDF not generated yet."

    submitted_answer_pdf_link.short_description = "Student Answer PDF"

    actions = [
        'recalculate_score',
        'mark_as_evaluated',
    ]

    def recalculate_score(self, request, queryset):
        for result in queryset:
            total_score = 0

            for answer in result.answers.all():
                total_score += answer.marks_awarded

            result.score = total_score
            result.is_evaluated = True
            result.save()

        self.message_user(
            request,
            "Score recalculated and marked as evaluated."
        )

    recalculate_score.short_description = "Recalculate score after valuation"

    def mark_as_evaluated(self, request, queryset):
        updated_count = queryset.update(
            is_evaluated=True
        )

        self.message_user(
            request,
            f"{updated_count} result(s) marked as evaluated."
        )

    mark_as_evaluated.short_description = "Mark selected results as evaluated"


class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = (
        'result',
        'question',
        'selected_choice',
        'answer_photo_link',
        'marks_awarded',
    )

    list_filter = (
        'result__exam',
    )

    search_fields = (
        'result__student__username',
        'question__question_text',
    )

    readonly_fields = (
        'answer_photo_link',
    )

    actions = [
        'clear_answer_photos'
    ]

    def answer_photo_link(self, obj):
        if obj.answer_photo:
            return format_html(
                '<a href="{}" target="_blank">Open Answer Photo</a>',
                obj.answer_photo.url
            )

        return "No photo uploaded"

    answer_photo_link.short_description = "Answer Photo"

    def clear_answer_photos(self, request, queryset):
        cleared_count = 0

        for answer in queryset:
            if answer.answer_photo:
                answer.answer_photo.delete(save=False)
                answer.answer_photo = None
                answer.save()
                cleared_count += 1

        self.message_user(
            request,
            f"{cleared_count} answer photo(s) cleared successfully."
        )

    clear_answer_photos.short_description = "Clear selected answer photos after valuation"


admin.site.register(Exam, ExamAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(ExamResult, ExamResultAdmin)
admin.site.register(StudentAnswer, StudentAnswerAdmin)
