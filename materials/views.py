from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import PDFMaterial, Subject
from accounts.models import StudentProfile


@login_required
def dashboard(request):

    student_profile = StudentProfile.objects.get(user=request.user)

    subjects = Subject.objects.filter(
        class_level=student_profile.class_level
    )

    return render(request, 'dashboard.html', {
        'subjects': subjects
    })


@login_required
def subject_materials(request, subject_id):

    pdfs = PDFMaterial.objects.filter(subject_id=subject_id)

    subject = Subject.objects.get(id=subject_id)

    return render(request, 'subject_materials.html', {
        'pdfs': pdfs,
        'subject': subject
    })