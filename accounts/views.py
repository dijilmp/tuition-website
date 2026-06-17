from django.shortcuts import render, redirect

from .models import RegistrationEnquiry


def register_training(request):
    return render(request, 'register_training.html')


def register_form(request, training_type):

    valid_training_types = [
        'uss',
        'nmms',
        'school_subjects',
    ]

    if training_type not in valid_training_types:
        return redirect('register_training')

    training_labels = {
        'uss': 'USS Exam',
        'nmms': 'National Means-cum-Merit',
        'school_subjects': 'School Subjects',
    }

    if request.method == 'POST':

        syllabus = request.POST.get('syllabus', '').strip()
        medium = request.POST.get('medium', '').strip()

        if syllabus != 'state':
            medium = ''

        RegistrationEnquiry.objects.create(
            training_needed=training_type,
            name=request.POST.get('name', '').strip(),
            phone_number=request.POST.get('phone_number', '').strip(),
            address=request.POST.get('address', '').strip(),
            student_class=request.POST.get('student_class', '').strip(),
            syllabus=syllabus,
            medium=medium,
            school_name=request.POST.get('school_name', '').strip(),
            class_type=request.POST.get('class_type', '').strip(),
        )

        return redirect('register_success')

    return render(request, 'register_form.html', {
        'training_type': training_type,
        'training_label': training_labels[training_type],
    })


def register_success(request):
    return render(request, 'register_success.html')
