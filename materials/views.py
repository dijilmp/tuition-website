from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse

from accounts.models import StudentProfile
from .models import Subject, PDFMaterial


# Dashboard page
@login_required
def dashboard(request):

    student_profile = StudentProfile.objects.get(user=request.user)

    subjects = Subject.objects.filter(
        class_level=student_profile.class_level
    )

    return render(request, 'dashboard.html', {
        'subjects': subjects
    })


# Subject materials page
@login_required
def subject_materials(request, subject_id):

    student_profile = StudentProfile.objects.get(user=request.user)

    subject = get_object_or_404(
        Subject,
        id=subject_id,
        class_level=student_profile.class_level
    )

    pdfs = PDFMaterial.objects.filter(
        subject=subject,
        class_level=student_profile.class_level
    )

    return render(request, 'subject_materials.html', {
        'subject': subject,
        'pdfs': pdfs
    })


# PDF Viewer page
@login_required
def view_pdf(request, pdf_id):

    student_profile = StudentProfile.objects.get(user=request.user)

    pdf = get_object_or_404(
        PDFMaterial,
        id=pdf_id,
        class_level=student_profile.class_level
    )

    return render(request, 'view_pdf.html', {
        'pdf': pdf
    })


# Protected PDF file
@login_required
def protected_pdf_file(request, pdf_id):

    student_profile = StudentProfile.objects.get(user=request.user)

    pdf = get_object_or_404(
        PDFMaterial,
        id=pdf_id,
        class_level=student_profile.class_level
    )

    response = FileResponse(
        pdf.pdf_file.open('rb'),
        content_type='application/pdf'
    )

    response['X-Frame-Options'] = 'SAMEORIGIN'

    return response