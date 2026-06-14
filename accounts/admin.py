from io import BytesIO
import random
import string

from django.contrib import admin
from django.http import FileResponse

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):

    list_display = (
        'student_name',
        'username',
        'class_level',
        'email',
    )

    list_filter = (
        'class_level',
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'class_level__name',
    )

    actions = [
        'reset_passwords_and_download_pdf'
    ]

    def student_name(self, obj):
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()

        if full_name:
            return full_name

        return obj.user.username

    student_name.short_description = "Student Name"

    def username(self, obj):
        return obj.user.username

    username.short_description = "Username"

    def email(self, obj):
        return obj.user.email

    email.short_description = "Email"

    def generate_password(self):
        digits = ''.join(
            random.choices(
                string.digits,
                k=4
            )
        )

        return f"MXA@{digits}"

    def reset_passwords_and_download_pdf(self, request, queryset):

        students = queryset.select_related(
            'user',
            'class_level'
        ).order_by(
            'class_level__name',
            'user__first_name',
            'user__username'
        )

        student_data = []

        for student_profile in students:
            user = student_profile.user

            new_password = self.generate_password()

            user.set_password(new_password)
            user.save()

            student_name = f"{user.first_name} {user.last_name}".strip()

            if not student_name:
                student_name = user.username

            student_data.append({
                'class_name': str(student_profile.class_level),
                'student_name': student_name,
                'username': user.username,
                'password': new_password,
                'email': user.email,
            })

        buffer = BytesIO()

        pdf = canvas.Canvas(buffer, pagesize=A4)

        width, height = A4

        def draw_header():
            y = height - 45

            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawCentredString(
                width / 2,
                y,
                "Master X's Academy"
            )

            y -= 22

            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawCentredString(
                width / 2,
                y,
                "Student Login Details"
            )

            y -= 22

            pdf.setFont("Helvetica", 9)
            pdf.drawCentredString(
                width / 2,
                y,
                "Note: Passwords shown here are newly reset passwords."
            )

            return y - 35

        y = draw_header()

        current_class = None
        serial_no = 0

        for student in student_data:

            class_name = student['class_name']

            if current_class != class_name:

                current_class = class_name
                serial_no = 0

                if y < 140:
                    pdf.showPage()
                    y = draw_header()

                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(
                    40,
                    y,
                    f"Class: {class_name}"
                )

                y -= 24

                pdf.setFont("Helvetica-Bold", 9)

                pdf.drawString(40, y, "No")
                pdf.drawString(75, y, "Student Name")
                pdf.drawString(230, y, "Username")
                pdf.drawString(360, y, "Password")
                pdf.drawString(465, y, "Email")

                y -= 8

                pdf.line(40, y, 555, y)

                y -= 18

            if y < 60:
                pdf.showPage()
                y = draw_header()

                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(
                    40,
                    y,
                    f"Class: {class_name}"
                )

                y -= 24

                pdf.setFont("Helvetica-Bold", 9)

                pdf.drawString(40, y, "No")
                pdf.drawString(75, y, "Student Name")
                pdf.drawString(230, y, "Username")
                pdf.drawString(360, y, "Password")
                pdf.drawString(465, y, "Email")

                y -= 8

                pdf.line(40, y, 555, y)

                y -= 18

            serial_no += 1

            pdf.setFont("Helvetica", 9)

            pdf.drawString(40, y, str(serial_no))
            pdf.drawString(75, y, student['student_name'][:22])
            pdf.drawString(230, y, student['username'][:18])
            pdf.drawString(360, y, student['password'])
            pdf.drawString(465, y, student['email'][:20])

            y -= 20

        pdf.save()

        buffer.seek(0)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename="student_login_details.pdf",
            content_type="application/pdf"
        )

    reset_passwords_and_download_pdf.short_description = (
        "Reset selected student passwords and download login PDF"
    )