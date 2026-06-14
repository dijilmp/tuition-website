from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import StudentProfile
from .models import (
    Exam,
    Question,
    Choice,
    ExamResult,
    StudentAnswer
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

    if result.is_evaluated:
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
        'answers': answers
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
