from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import (
    DemoOption,
    DemoRequest,
    DemoNotice,
    DemoStudyMaterial,
    DemoMockTest,
    DemoOnlineTest,
    DemoOnlineAttempt,
    DemoOnlineAnswer,
    DemoOnlineChoice,
)


def normalize_mobile(mobile_number):
    return ''.join(ch for ch in mobile_number if ch.isdigit())


def view_demo(request):

    demo_options = DemoOption.objects.filter(
        is_active=True,
        category__is_active=True
    ).select_related(
        'category'
    ).order_by(
        'category__order',
        'order',
        'class_name',
        'subject_name',
        'title',
    )

    if request.method == 'POST':

        demo_option = get_object_or_404(
            DemoOption,
            id=request.POST.get('demo_option'),
            is_active=True,
            category__is_active=True
        )

        mobile_number = normalize_mobile(
            request.POST.get('mobile_number', '').strip()
        )

        request_obj, created = DemoRequest.objects.get_or_create(
            demo_option=demo_option,
            mobile_number=mobile_number,
            defaults={
                'name': request.POST.get('name', '').strip(),
                'school_name': request.POST.get('school_name', '').strip(),
                'address': request.POST.get('address', '').strip(),
                'view_count': 1,
            }
        )

        if not created:
            request_obj.name = request.POST.get('name', '').strip()
            request_obj.school_name = request.POST.get('school_name', '').strip()
            request_obj.address = request.POST.get('address', '').strip()
            request_obj.view_count = request_obj.view_count + 1
            request_obj.last_viewed_at = timezone.now()
            request_obj.save()

        request.session['demo_request_id'] = request_obj.id
        request.session['demo_option_id'] = demo_option.id

        return redirect('demo_content')

    return render(request, 'demo/view_demo_form.html', {
        'demo_options': demo_options,
    })


def demo_content(request):

    demo_option_id = request.session.get('demo_option_id')

    if not demo_option_id:
        return redirect('view_demo')

    demo_option = get_object_or_404(
        DemoOption,
        id=demo_option_id,
        is_active=True,
        category__is_active=True
    )

    notice = DemoNotice.objects.filter(
        demo_option=demo_option,
        is_active=True
    ).first()

    materials = DemoStudyMaterial.objects.filter(
        demo_option=demo_option,
        is_published=True
    ).order_by('order', 'title')

    mock_tests = DemoMockTest.objects.filter(
        demo_option=demo_option,
        is_published=True
    ).order_by('order', 'mock_number', 'title')

    online_tests = DemoOnlineTest.objects.filter(
        demo_option=demo_option,
        is_published=True
    ).order_by('order', 'title')

    return render(request, 'demo/demo_content.html', {
        'demo_option': demo_option,
        'category': demo_option.category,
        'notice': notice,
        'materials': materials,
        'mock_tests': mock_tests,
        'online_tests': online_tests,
    })


def take_demo_online_test(request, test_id):

    demo_request_id = request.session.get('demo_request_id')
    demo_option_id = request.session.get('demo_option_id')

    if not demo_request_id or not demo_option_id:
        return redirect('view_demo')

    online_test = get_object_or_404(
        DemoOnlineTest,
        id=test_id,
        demo_option_id=demo_option_id,
        is_published=True
    )

    demo_request = get_object_or_404(
        DemoRequest,
        id=demo_request_id,
        demo_option_id=demo_option_id
    )

    attempt, created = DemoOnlineAttempt.objects.get_or_create(
        demo_request=demo_request,
        online_test=online_test
    )

    if attempt.is_submitted and not online_test.allow_reattempt:
        return redirect('demo_online_result', attempt_id=attempt.id)

    if attempt.is_submitted and online_test.allow_reattempt:
        attempt.answers.all().delete()
        attempt.score = 0
        attempt.is_submitted = False
        attempt.submitted_at = None
        attempt.started_at = timezone.now()
        attempt.save()

    questions = online_test.questions.prefetch_related('choices').all()

    return render(request, 'demo/take_online_test.html', {
        'online_test': online_test,
        'questions': questions,
        'attempt': attempt,
    })


def submit_demo_online_test(request, test_id):

    if request.method != 'POST':
        return redirect('demo_content')

    demo_request_id = request.session.get('demo_request_id')
    demo_option_id = request.session.get('demo_option_id')

    if not demo_request_id or not demo_option_id:
        return redirect('view_demo')

    online_test = get_object_or_404(
        DemoOnlineTest,
        id=test_id,
        demo_option_id=demo_option_id,
        is_published=True
    )

    demo_request = get_object_or_404(
        DemoRequest,
        id=demo_request_id,
        demo_option_id=demo_option_id
    )

    attempt, created = DemoOnlineAttempt.objects.get_or_create(
        demo_request=demo_request,
        online_test=online_test
    )

    if attempt.is_submitted and not online_test.allow_reattempt:
        return redirect('demo_online_result', attempt_id=attempt.id)

    attempt.answers.all().delete()

    score = 0

    for question in online_test.questions.all():

        choice_id = request.POST.get(f'question_{question.id}')

        answer = DemoOnlineAnswer.objects.create(
            attempt=attempt,
            question=question
        )

        if choice_id:
            try:
                choice = DemoOnlineChoice.objects.get(
                    id=choice_id,
                    question=question
                )
                answer.selected_choice = choice
                answer.is_correct = choice.is_correct

                if choice.is_correct:
                    answer.marks_awarded = question.marks
                    score += question.marks

            except DemoOnlineChoice.DoesNotExist:
                pass

        answer.save()

    attempt.score = score
    attempt.is_submitted = True
    attempt.submitted_at = timezone.now()
    attempt.save()

    return redirect('demo_online_result', attempt_id=attempt.id)


def demo_online_result(request, attempt_id):

    demo_request_id = request.session.get('demo_request_id')

    if not demo_request_id:
        return redirect('view_demo')

    attempt = get_object_or_404(
        DemoOnlineAttempt,
        id=attempt_id,
        demo_request_id=demo_request_id
    )

    answers = attempt.answers.select_related(
        'question',
        'selected_choice'
    ).all()

    return render(request, 'demo/online_result.html', {
        'attempt': attempt,
        'online_test': attempt.online_test,
        'answers': answers,
    })
