from datetime import timedelta
from io import BytesIO
import re

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.contrib import messages

from PIL import Image, ImageOps

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from accounts.models import StudentProfile
from .models import (
    Exam,
    Question,
    Choice,
    ExamResult,
    StudentAnswer,
    BulkAnswerImage
)


def student_has_exam_access(user, exam):

    student_profile = StudentProfile.objects.get(
        user=user
    )

    if exam.class_level != student_profile.class_level:
        return False

    if not exam.is_published:
        return False

    if not exam.allowed_students.filter(id=user.id).exists():
        return False

    return True


def get_exam_end_time(result):

    return result.started_at + timedelta(
        minutes=result.exam.duration_minutes
    )


def get_remaining_seconds(result):

    end_time = get_exam_end_time(result)

    remaining_time = end_time - timezone.now()

    remaining_seconds = int(
        remaining_time.total_seconds()
    )

    if remaining_seconds < 0:
        remaining_seconds = 0

    return remaining_seconds



def get_student_display_name(user):
    full_name = f"{user.first_name} {user.last_name}".strip()

    if full_name:
        return full_name

    return user.username


def make_safe_filename_part(value):
    value = str(value).strip()
    value = re.sub(r'[^A-Za-z0-9_-]+', '_', value)
    value = value.strip('_')

    if not value:
        return 'file'

    return value[:70]


def get_answer_pdf_filename(result, suffix='answer_sheet.pdf'):
    student_name = make_safe_filename_part(
        get_student_display_name(result.student)
    )

    class_name = make_safe_filename_part(result.exam.class_level)
    exam_name = make_safe_filename_part(result.exam.title)

    return f"{student_name}_{class_name}_{exam_name}_{suffix}"


def create_submitted_answer_pdf(result, uploaded_images):
    """
    Converts uploaded answer images into a single PDF in the same order selected/uploaded
    by the student.

    Memory-safe version for Render 512 MB:
    - resizes large mobile photos before putting them into PDF
    - compresses images as JPEG
    - keeps compact header only on the first page
    """

    page_width, page_height = A4
    margin = 0.8 * cm
    first_page_header_height = 0.8 * cm

    # Keep this moderate for Render Starter memory.
    # A4 at this resolution is enough for answer-sheet viewing/valuation.
    max_image_dimension = 1600
    jpeg_quality = 70

    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=A4)

    student_name = get_student_display_name(result.student)
    class_name = str(result.exam.class_level)
    exam_title = result.exam.title

    created_pages = 0

    for page_number, uploaded_image in enumerate(uploaded_images, start=1):
        temp_image_buffer = None

        try:
            uploaded_image.seek(0)
            image = Image.open(uploaded_image)
            image = ImageOps.exif_transpose(image)

            if image.mode in ("RGBA", "LA", "P"):
                if image.mode == "P":
                    image = image.convert("RGBA")

                background = Image.new("RGB", image.size, "white")
                background.paste(
                    image,
                    mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None
                )
                image = background
            else:
                image = image.convert("RGB")

            # Resize very large mobile photos before ReportLab processes them.
            image.thumbnail(
                (max_image_dimension, max_image_dimension),
                Image.Resampling.LANCZOS
            )

            # Compress to JPEG first. This avoids ReportLab spending too much
            # memory/time encoding huge original images.
            temp_image_buffer = BytesIO()
            image.save(
                temp_image_buffer,
                format="JPEG",
                quality=jpeg_quality,
                optimize=True
            )
            temp_image_buffer.seek(0)

            image_reader = ImageReader(temp_image_buffer)
            image_width, image_height = image.size

            available_width = page_width - (2 * margin)

            if page_number == 1:
                available_height = page_height - (2 * margin) - first_page_header_height
            else:
                available_height = page_height - (2 * margin)

            scale = min(
                available_width / image_width,
                available_height / image_height
            )

            draw_width = image_width * scale
            draw_height = image_height * scale
            image_x = (page_width - draw_width) / 2

            if page_number == 1:
                image_y = margin
            else:
                image_y = (page_height - draw_height) / 2

            if page_number == 1:
                header_text = (
                    f"Master X's Academy | Name: {student_name} | "
                    f"Class: {class_name} | Exam: {exam_title} | Page: 1"
                )

                pdf.setFont("Helvetica-Bold", 8)
                pdf.drawString(
                    margin,
                    page_height - 0.45 * cm,
                    header_text[:145]
                )

                pdf.line(
                    margin,
                    page_height - 0.62 * cm,
                    page_width - margin,
                    page_height - 0.62 * cm
                )

            pdf.drawImage(
                image_reader,
                image_x,
                image_y,
                width=draw_width,
                height=draw_height,
                preserveAspectRatio=True,
                mask='auto'
            )

            pdf.showPage()
            created_pages += 1

            # Release memory page by page
            image.close()
            temp_image_buffer.close()

        except Exception:
            try:
                if temp_image_buffer:
                    temp_image_buffer.close()
            except Exception:
                pass
            continue

    if created_pages == 0:
        return False

    pdf.save()
    pdf_buffer.seek(0)

    filename = get_answer_pdf_filename(
        result,
        suffix='answer_sheet.pdf'
    )

    result.submitted_answer_pdf.save(
        filename,
        ContentFile(pdf_buffer.read()),
        save=False
    )

    pdf_buffer.close()

    return True


def mark_exam_submitted(result):

    result.is_submitted = True
    result.submitted_at = timezone.now()

    if result.exam.exam_type == 'mcq':
        result.is_evaluated = True

    result.save()


@login_required
def exam_list(request):

    student_profile = StudentProfile.objects.get(
        user=request.user
    )

    exams = Exam.objects.filter(
        class_level=student_profile.class_level,
        is_published=True,
        allowed_students=request.user
    )

    exam_items = []

    for exam in exams:
        result = ExamResult.objects.filter(
            student=request.user,
            exam=exam
        ).first()

        exam_items.append({
            'exam': exam,
            'result': result
        })

    return render(request, 'exam_list.html', {
        'exam_items': exam_items
    })


@login_required
def take_exam(request, exam_id):

    exam = get_object_or_404(
        Exam,
        id=exam_id
    )

    if not student_has_exam_access(request.user, exam):
        return redirect('exam_list')

    result, created = ExamResult.objects.get_or_create(
        student=request.user,
        exam=exam,
        defaults={
            'started_at': timezone.now(),
            'score': 0,
            'is_evaluated': False,
            'is_submitted': False,
        }
    )

    if result.started_at is None:
        result.started_at = timezone.now()
        result.save()

    if result.is_submitted:
        return redirect(
            'exam_result',
            result_id=result.id
        )

    remaining_seconds = get_remaining_seconds(result)

    if remaining_seconds <= 0:
        mark_exam_submitted(result)

        return redirect(
            'exam_result',
            result_id=result.id
        )

    questions = Question.objects.filter(
        exam=exam
    )

    return render(request, 'take_exam.html', {
        'exam': exam,
        'questions': questions,
        'remaining_seconds': remaining_seconds
    })


@login_required
def submit_exam(request, exam_id):

    if request.method != 'POST':
        return redirect('exam_list')

    exam = get_object_or_404(
        Exam,
        id=exam_id
    )

    if not student_has_exam_access(request.user, exam):
        return redirect('exam_list')

    result = get_object_or_404(
        ExamResult,
        student=request.user,
        exam=exam
    )

    if result.is_submitted:
        return redirect(
            'exam_result',
            result_id=result.id
        )

    if result.started_at is None:
        result.started_at = timezone.now()
        result.save()

    end_time = get_exam_end_time(result)

    grace_time = end_time + timedelta(seconds=10)

    if timezone.now() > grace_time:
        mark_exam_submitted(result)

        return redirect(
            'exam_result',
            result_id=result.id
        )

    total_score = 0

    if exam.exam_type == 'question_paper_upload':

        answer_images = request.FILES.getlist('answer_images')
        camera_images = request.FILES.getlist('camera_images')

        all_images = list(answer_images) + list(camera_images)

        if not all_images:
            messages.error(
                request,
                'Please upload at least one answer image before submitting.'
            )

            return redirect(
                'take_exam',
                exam_id=exam.id
            )

        # Remove old generated PDF if this result is being reused locally.
        if result.submitted_answer_pdf:
            result.submitted_answer_pdf.delete(save=False)
            result.submitted_answer_pdf = None

        pdf_created = create_submitted_answer_pdf(
            result,
            all_images
        )

        if not pdf_created:
            messages.error(
                request,
                'Unable to create answer PDF. Please upload clear JPG or PNG images.'
            )

            return redirect(
                'take_exam',
                exam_id=exam.id
            )

        result.is_submitted = True
        result.submitted_at = timezone.now()
        result.is_evaluated = False
        result.score = 0
        result.save()

        return redirect(
            'exam_result',
            result_id=result.id
        )

    questions = Question.objects.filter(
        exam=exam
    )

    for question in questions:

        if exam.exam_type == 'mcq':

            selected_choice_id = request.POST.get(
                f'question_{question.id}'
            )

            selected_choice = None
            marks_awarded = 0

            if selected_choice_id:
                selected_choice = Choice.objects.filter(
                    id=selected_choice_id,
                    question=question
                ).first()

                if selected_choice and selected_choice.is_correct:
                    marks_awarded = question.mark

            StudentAnswer.objects.create(
                result=result,
                question=question,
                selected_choice=selected_choice,
                marks_awarded=marks_awarded
            )

            total_score += marks_awarded

        elif exam.exam_type == 'one_line':

            answer_text = request.POST.get(
                f'question_{question.id}',
                ''
            )

            StudentAnswer.objects.create(
                result=result,
                question=question,
                one_line_answer=answer_text,
                marks_awarded=0
            )

        elif exam.exam_type == 'photo_upload':

            answer_photo = request.FILES.get(
                f'question_{question.id}'
            )

            StudentAnswer.objects.create(
                result=result,
                question=question,
                answer_photo=answer_photo,
                marks_awarded=0
            )

    result.is_submitted = True
    result.submitted_at = timezone.now()

    if exam.exam_type == 'mcq':
        result.score = total_score
        result.is_evaluated = True

    result.save()

    return redirect(
        'exam_result',
        result_id=result.id
    )


@login_required
def exam_result(request, result_id):

    result = get_object_or_404(
        ExamResult,
        id=result_id,
        student=request.user
    )

    exam = result.exam

    rank = None

    if result.is_evaluated and exam.result_published:
        higher_score_count = ExamResult.objects.filter(
            exam=exam,
            is_evaluated=True,
            score__gt=result.score
        ).count()

        rank = higher_score_count + 1

    if result.is_evaluated and exam.exam_type == 'mcq':
        higher_score_count = ExamResult.objects.filter(
            exam=exam,
            is_evaluated=True,
            score__gt=result.score
        ).count()

        rank = higher_score_count + 1

    attempted_count = ExamResult.objects.filter(
        exam=exam,
        is_submitted=True
    ).count()

    answers = StudentAnswer.objects.filter(
        result=result
    ).select_related(
        'question',
        'selected_choice'
    )

    return render(request, 'exam_result.html', {
        'result': result,
        'exam': exam,
        'rank': rank,
        'attempted_count': attempted_count,
        'answers': answers,
    })


@login_required
@require_POST
def reattempt_exam(request, result_id):

    result = get_object_or_404(
        ExamResult,
        id=result_id,
        student=request.user
    )

    exam = result.exam

    if not student_has_exam_access(request.user, exam):
        return redirect('exam_list')

    if not exam.allow_reattempt:
        return redirect(
            'exam_result',
            result_id=result.id
        )

    result.delete()

    return redirect(
        'take_exam',
        exam_id=exam.id
    )
