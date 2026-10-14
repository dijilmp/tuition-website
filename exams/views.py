from datetime import timedelta
import json
from io import BytesIO
import re

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.files.base import ContentFile
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse

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
    BulkAnswerImage, ExamQuestion
)
from .mcq_service import (ensure_snapshot, public_questions, save_batch_locked,
    finalize_locked, finalize_expired, past_deadline, deadline)


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


def make_safe_filename_part(value, max_chars=30):
    value = str(value).strip()
    value = re.sub(r'[^A-Za-z0-9_-]+', '_', value)
    value = value.strip('_')

    if not value:
        return 'file'

    return value[:max_chars]


def get_answer_pdf_filename(result, suffix='answer_sheet.pdf'):
    # Keep generated filename short enough for database/storage, but still readable.
    # Full path also includes upload_to folder, so do not use very long exam names here.
    student_name = make_safe_filename_part(
        get_student_display_name(result.student),
        max_chars=25
    )

    class_name = make_safe_filename_part(result.exam.class_level, max_chars=15)
    exam_name = make_safe_filename_part(result.exam.title, max_chars=35)
    result_id = result.id or 'new'

    return f"result_{result_id}_{student_name}_{class_name}_{exam_name}_{suffix}"


def create_submitted_answer_pdf(result, uploaded_images):
    """
    Converts uploaded answer images into a single PDF in the same order selected/uploaded
    by the student.

    Important:
    - No silent skipping. If student selects 6 images, PDF must get 6 pages.
    - If any page fails, raise an error and show message to student.
    - Memory-safe for Render Starter: resize/compress before ReportLab.
    """

    page_width, page_height = A4
    margin = 0.8 * cm
    first_page_header_height = 0.8 * cm

    max_image_dimension = 1600
    jpeg_quality = 70

    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=A4)

    student_name = get_student_display_name(result.student)
    class_name = str(result.exam.class_level)
    exam_title = result.exam.title

    uploaded_images = list(uploaded_images)

    if not uploaded_images:
        raise ValueError('No answer images selected.')

    created_pages = 0

    for page_number, uploaded_image in enumerate(uploaded_images, start=1):
        temp_image_buffer = None
        image = None

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

            image.thumbnail(
                (max_image_dimension, max_image_dimension),
                Image.Resampling.LANCZOS
            )

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

        except Exception as exc:
            raise ValueError(
                f'Page {page_number} could not be added to PDF. '
                'Please reselect this image or take the photo again.'
            ) from exc

        finally:
            try:
                if image:
                    image.close()
            except Exception:
                pass

            try:
                if temp_image_buffer:
                    temp_image_buffer.close()
            except Exception:
                pass

    if created_pages != len(uploaded_images):
        raise ValueError(
            f'Selected {len(uploaded_images)} images, but only {created_pages} pages were created. '
            'Please select the images again.'
        )

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

    return created_pages


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
    # Single query for the user's current attempts rather than one per exam.
    result_by_exam = {r.exam_id: r for r in ExamResult.objects.filter(
        student=request.user, exam__in=exams
    ).select_related('exam')}

    for exam in exams:
        result = result_by_exam.get(exam.pk)
        if result and result.started_at and not result.is_submitted and past_deadline(result):
            if finalize_expired(result):
                result.refresh_from_db()

        exam_items.append({
            'exam': exam,
            'result': result
        })

    return render(request, 'exam_list.html', {
        'exam_items': exam_items
    })


@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not student_has_exam_access(request.user, exam):
        return redirect('exam_list')

    result = ExamResult.objects.filter(student=request.user, exam=exam).first()
    if result and result.is_submitted:
        return redirect('exam_result', result_id=result.id)

    # Do not start the clock just for reading instructions.
    if (not result or result.started_at is None) and exam.instructions_enabled:
        return render(request, 'exam_instructions.html', {'exam': exam})

    # Preserve direct-start behavior for exams with instructions disabled.
    if not result or result.started_at is None:
        result = start_exam_attempt(request.user, exam, accepted=False)

    if get_remaining_seconds(result) <= 0:
        finalize_expired(result)
        return redirect('exam_result', result_id=result.id)

    if exam.exam_type == 'mcq':
        with transaction.atomic():
            locked = ExamResult.objects.select_for_update().select_related('exam').get(pk=result.pk)
            if locked.is_submitted:
                return redirect('exam_result', result_id=locked.id)
            snapshot = ensure_snapshot(locked)
        questions = public_questions(snapshot)
        saved_answers = [{
            'question_id': a.question_id,
            'choice_id': a.selected_choice_id_snapshot,
            'revision': a.client_revision,
        } for a in StudentAnswer.objects.filter(result=result).exclude(
            selected_choice_id_snapshot__isnull=True
        )]
    else:
        questions = [link.question for link in ExamQuestion.objects.filter(
            exam=exam).select_related('question').order_by('position', 'pk')]
        saved_answers = []

    return render(request, 'take_exam.html', {
        'exam': exam, 'questions': questions,
        'remaining_seconds': get_remaining_seconds(result), 'result': result,
        'deadline_ms': int(deadline(result).timestamp() * 1000),
        'server_now_ms': int(timezone.now().timestamp() * 1000),
        'saved_answers': saved_answers,
    })


def start_exam_attempt(student, exam, *, accepted):
    with transaction.atomic():
        result, created = ExamResult.objects.select_for_update().get_or_create(
            student=student, exam=exam,
            defaults={'started_at': timezone.now(), 'instructions_accepted_at':
                      timezone.now() if accepted else None},
        )
        if result.started_at is None and not result.is_submitted:
            result.started_at = timezone.now()
            result.instructions_accepted_at = timezone.now() if accepted else None
            result.save(update_fields=['started_at', 'instructions_accepted_at'])
        if exam.exam_type == 'mcq' and not result.is_submitted:
            ensure_snapshot(result)
        return result


@login_required
@require_POST
def begin_exam(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    if not student_has_exam_access(request.user, exam):
        return redirect('exam_list')
    if exam.instructions_enabled and exam.declaration_required and request.POST.get('accepted') != 'yes':
        messages.error(request, 'Please accept the declaration before starting.')
        return redirect('take_exam', exam_id=exam.id)
    start_exam_attempt(request.user, exam, accepted=exam.instructions_enabled and request.POST.get('accepted') == 'yes')
    return redirect('take_exam', exam_id=exam.id)


@login_required
@require_POST
def autosave_mcq(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, exam_type='mcq')
    if not student_has_exam_access(request.user, exam):
        return JsonResponse({'error': 'Access denied'}, status=403)
    if len(request.body) > 65536:
        return JsonResponse({'error': 'Answer batch is too large'}, status=413)
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError('Invalid request')
        with transaction.atomic():
            result = (ExamResult.objects.select_for_update().select_related('exam')
                      .get(student=request.user, exam=exam))
            if result.is_submitted:
                return JsonResponse({'submitted': True}, status=409)
            if not result.started_at:
                return JsonResponse({'error': 'Attempt not started'}, status=409)
            if past_deadline(result):
                finalize_locked(result)
                return JsonResponse({'submitted': True, 'error': 'Deadline passed'}, status=409)
            batch = payload.get('answers', [])
            saved = save_batch_locked(result, batch)
            requested = {int(entry['question_id']) for entry in batch}
            persisted = list(StudentAnswer.objects.filter(result=result, question_id__in=requested)
                             .values('question_id', 'selected_choice_id_snapshot', 'client_revision'))
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    except ExamResult.DoesNotExist:
        return JsonResponse({'error': 'Attempt not found'}, status=404)
    return JsonResponse({'saved': True, 'count': saved, 'confirmed': persisted})


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

    if exam.exam_type == 'mcq':
        with transaction.atomic():
            result = (ExamResult.objects.select_for_update().select_related('exam')
                      .get(pk=result.pk))
            if result.is_submitted:
                return redirect('exam_result', result_id=result.id)
            if not result.started_at:
                return redirect('take_exam', exam_id=exam.id)
            if past_deadline(result):
                finalize_locked(result)
                return redirect('exam_result', result_id=result.id)
            # Full form POST is reliable fallback when a background save failed.
            updates = []
            for q in ensure_snapshot(result):
                choice = request.POST.get(f"question_{q['id']}")
                if choice:
                    updates.append({'question_id': q['id'], 'choice_id': choice,
                                    'revision': request.POST.get(f"revision_{q['id']}", 0)})
            try:
                save_batch_locked(result, updates)
            except (ValueError, TypeError):
                messages.error(request, 'Invalid response. Please retry submission.')
                return redirect('take_exam', exam_id=exam.id)
            finalize_locked(result)
        return redirect('exam_result', result_id=result.id)

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

        answer_action = request.POST.get('answer_action', '')

        if answer_action == 'final_submit':

            if not result.submitted_answer_pdf:
                messages.error(
                    request,
                    'Please generate and verify your answer PDF before final submission.'
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

        if answer_action != 'generate_pdf':
            messages.error(
                request,
                'Please select answer images and click Generate Answer PDF first.'
            )

            return redirect(
                'take_exam',
                exam_id=exam.id
            )

        answer_images = request.FILES.getlist('answer_images')
        camera_images = request.FILES.getlist('camera_images')

        all_images = list(answer_images) + list(camera_images)

        if not all_images:
            messages.error(
                request,
                'Please select answer images before generating the PDF.'
            )

            return redirect(
                'take_exam',
                exam_id=exam.id
            )

        # Remove old generated PDF before making a new one.
        # This avoids accidentally submitting an older PDF if a new generation fails.
        if result.submitted_answer_pdf:
            result.submitted_answer_pdf.delete(save=False)
            result.submitted_answer_pdf = None
            result.save(update_fields=['submitted_answer_pdf'])

        try:
            created_pages = create_submitted_answer_pdf(
                result,
                all_images
            )
        except ValueError as exc:
            messages.error(
                request,
                str(exc)
            )

            return redirect(
                'take_exam',
                exam_id=exam.id
            )

        result.is_submitted = False
        result.submitted_at = None
        result.is_evaluated = False
        result.score = 0
        result.save()

        messages.success(
            request,
            f'Answer PDF generated successfully with {created_pages} pages. Please verify the PDF below and click Final Submit Answer.'
        )

        return redirect(
            'take_exam',
            exam_id=exam.id
        )

    questions = [link.question for link in ExamQuestion.objects.filter(
        exam=exam).select_related('question').order_by('position', 'pk')]

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
    result = get_object_or_404(ExamResult.objects.select_related('exam'),
                               id=result_id, student=request.user)
    exam = result.exam
    if not result.is_submitted:
        finalize_expired(result)
        result.refresh_from_db()
    if not result.is_submitted:
        return redirect('take_exam', exam_id=exam.id)

    is_mcq = exam.exam_type == 'mcq'
    marks_visible = result.is_evaluated and (exam.publish_marks if is_mcq else exam.result_published)
    rank_visible = result.is_evaluated and (exam.publish_ranks if is_mcq else exam.result_published)
    keys_visible = is_mcq and exam.publish_answer_keys
    rank = None
    if rank_visible:
        rank = ExamResult.objects.filter(
            exam=exam, is_submitted=True, is_evaluated=True,
            score__gt=result.score
        ).count() + 1
    attempted_count = ExamResult.objects.filter(exam=exam, is_submitted=True).count()
    answers = []
    answer_reviews = []
    if keys_visible:
        answers = list(StudentAnswer.objects.filter(result=result).select_related(
            'question', 'selected_choice').prefetch_related('question__choices'))
        by_question = {a.question_id: a for a in answers}
        snapshot = result.question_snapshot or []
        if snapshot:
            for q in snapshot:
                a = by_question.get(q['id'])
                chosen = a.selected_choice_id_snapshot if a else None
                answer_reviews.append({
                    'question_text': q['question_text'],
                    'question_image': q.get('question_image', ''),
                    'selected_text': next((c['choice_text'] for c in q['choices']
                                           if c['id'] == chosen), ''),
                    'correct_texts': [c['choice_text'] for c in q['choices'] if c.get('correct')],
                    'marks_awarded': a.marks_awarded if (a and exam.publish_marks) else None,
                })
        else:  # Attempts saved before this upgrade.
            for a in answers:
                answer_reviews.append({
                    'question_text': a.question.question_text,
                    'question_image': a.question.question_image.url if a.question.question_image else '',
                    'selected_text': a.selected_choice.choice_text if a.selected_choice else '',
                    'correct_texts': [c.choice_text for c in a.question.choices.all() if c.is_correct],
                    'marks_awarded': a.marks_awarded if exam.publish_marks else None,
                })

    return render(request, 'exam_result.html', {
        'result': result, 'exam': exam, 'rank': rank,
        'marks_visible': marks_visible, 'rank_visible': rank_visible,
        'keys_visible': keys_visible, 'attempted_count': attempted_count,
        'answers': answers, 'answer_reviews': answer_reviews,
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
