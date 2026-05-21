from io import BytesIO

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from accounts.models import StudentProfile
from .models import (
    Subject,
    PDFMaterial,
    VideoMaterial,
    PDFAccessLog
)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip


def create_watermark(width, height, text):
    packet = BytesIO()

    c = canvas.Canvas(packet, pagesize=(width, height))
    c.saveState()

    c.setFillAlpha(0.18)

    # Move watermark to center
    c.translate(width / 2, height / 2)

    # Straight watermark, no rotation
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(
        0,
        20,
        f"Downloaded by : {text}"
    )

    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(
        0,
        -5,
        "Content belongs to Master X's Academy"
    )

    c.drawCentredString(
        0,
        -25,
        "Do not share"
    )

    c.restoreState()
    c.save()

    packet.seek(0)

    return PdfReader(packet).pages[0]

@login_required
def dashboard(request):
    student_profile = StudentProfile.objects.get(
        user=request.user
    )

    subjects = Subject.objects.filter(
        class_level=student_profile.class_level
    )

    return render(request, 'dashboard.html', {
        'subjects': subjects
    })


@login_required
def subject_materials(request, subject_id):
    student_profile = StudentProfile.objects.get(
        user=request.user
    )

    subject = get_object_or_404(
        Subject,
        id=subject_id,
        class_level=student_profile.class_level
    )

    pdfs = PDFMaterial.objects.filter(
        subject=subject,
        class_level=student_profile.class_level
    )

    videos = VideoMaterial.objects.filter(
        subject=subject,
        class_level=student_profile.class_level
    )

    return render(request, 'subject_materials.html', {
        'subject': subject,
        'pdfs': pdfs,
        'videos': videos
    })


@login_required
def view_pdf(request, pdf_id):
    student_profile = StudentProfile.objects.get(
        user=request.user
    )

    pdf = get_object_or_404(
        PDFMaterial,
        id=pdf_id,
        class_level=student_profile.class_level
    )

    PDFAccessLog.objects.create(
        user=request.user,
        pdf=pdf,
        ip_address=get_client_ip(request)
    )

    return render(request, 'view_pdf.html', {
        'pdf': pdf
    })


@login_required
def protected_pdf_file(request, pdf_id):
    student_profile = StudentProfile.objects.get(
        user=request.user
    )

    pdf = get_object_or_404(
        PDFMaterial,
        id=pdf_id,
        class_level=student_profile.class_level
    )

    user = request.user

    student_name = f"{user.first_name} {user.last_name}".strip()

    if not student_name:
        student_name = user.username

    original_pdf = pdf.pdf_file.open('rb')

    reader = PdfReader(original_pdf)
    writer = PdfWriter()

    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        watermark = create_watermark(
            width,
            height,
            student_name
        )

        page.merge_page(watermark)
        writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)

    response = FileResponse(
        output,
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'inline; filename="{pdf.title}.pdf"'
    )

    response['X-Frame-Options'] = 'SAMEORIGIN'

    # Prevent browser cache so watermark changes for each logged-in student
    response['Cache-Control'] = (
        'no-store, no-cache, must-revalidate, max-age=0'
    )
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response