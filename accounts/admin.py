from io import BytesIO
import random
import string

from django.contrib import admin
from django.contrib.auth.models import User
from django.http import FileResponse
from django.utils.text import slugify

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from materials.models import ClassLevel
from .models import StudentProfile, RegistrationEnquiry


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):

    list_display = (
        'student_name',
        'username',
        'class_level',
        'subject_list',
        'email',
    )

    list_filter = (
        'class_level',
        'subjects',
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'class_level__name',
        'subjects__name',
    )

    filter_horizontal = (
        'subjects',
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

    def subject_list(self, obj):
        subjects = obj.subjects.all()

        if subjects.exists():
            return ", ".join(subject.name for subject in subjects)

        return "All class subjects"

    subject_list.short_description = "Subjects"

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
        ).prefetch_related(
            'subjects'
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

            subjects = student_profile.subjects.all()

            if subjects.exists():
                subject_names = ", ".join(subject.name for subject in subjects)
            else:
                subject_names = "All class subjects"

            student_data.append({
                'class_name': str(student_profile.class_level),
                'student_name': student_name,
                'username': user.username,
                'password': new_password,
                'email': user.email,
                'subjects': subject_names,
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

                pdf.setFont("Helvetica-Bold", 8)

                pdf.drawString(40, y, "No")
                pdf.drawString(65, y, "Student Name")
                pdf.drawString(180, y, "Username")
                pdf.drawString(285, y, "Password")
                pdf.drawString(365, y, "Subjects")
                pdf.drawString(475, y, "Email")

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

                pdf.setFont("Helvetica-Bold", 8)

                pdf.drawString(40, y, "No")
                pdf.drawString(65, y, "Student Name")
                pdf.drawString(180, y, "Username")
                pdf.drawString(285, y, "Password")
                pdf.drawString(365, y, "Subjects")
                pdf.drawString(475, y, "Email")

                y -= 8

                pdf.line(40, y, 555, y)

                y -= 18

            serial_no += 1

            pdf.setFont("Helvetica", 8)

            pdf.drawString(40, y, str(serial_no))
            pdf.drawString(65, y, student['student_name'][:18])
            pdf.drawString(180, y, student['username'][:15])
            pdf.drawString(285, y, student['password'])
            pdf.drawString(365, y, student['subjects'][:18])
            pdf.drawString(475, y, student['email'][:14])

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


@admin.register(RegistrationEnquiry)
class RegistrationEnquiryAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'phone_number',
        'training_needed',
        'student_class',
        'syllabus',
        'medium',
        'class_type',
        'school_name',
        'created_user',
        'is_contacted',
        'created_at',
    )

    list_filter = (
        'training_needed',
        'student_class',
        'syllabus',
        'medium',
        'class_type',
        'is_contacted',
        'created_at',
    )

    search_fields = (
        'name',
        'phone_number',
        'student_class',
        'school_name',
        'address',
        'medium',
    )

    ordering = (
        'training_needed',
        'student_class',
        '-created_at',
    )

    readonly_fields = (
        'created_at',
        'created_user',
    )

    actions = [
        'create_student_accounts',
        'mark_as_contacted',
        'mark_as_not_contacted',
    ]

    def generate_password(self):
        digits = ''.join(
            random.choices(
                string.digits,
                k=4
            )
        )

        return f"MXA@{digits}"

    def get_class_name(self, enquiry):
        syllabus = enquiry.get_syllabus_display()
        student_class = enquiry.student_class.strip()

        if enquiry.syllabus == 'state' and enquiry.medium:
            medium = enquiry.get_medium_display()

            return f"{syllabus} {student_class} {medium} Medium".strip()

        return f"{syllabus} {student_class}".strip()

    def get_unique_username(self, enquiry):
        phone_digits = ''.join(
            character for character in enquiry.phone_number
            if character.isdigit()
        )

        if phone_digits:
            base_username = f"mxa{phone_digits[-10:]}"
        else:
            base_username = slugify(enquiry.name).replace('-', '')

            if not base_username:
                base_username = "student"

        base_username = base_username[:25]

        username = base_username
        count = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{count}"
            count += 1

        return username

    def split_name(self, full_name):
        parts = full_name.strip().split()

        if not parts:
            return "", ""

        first_name = parts[0]
        last_name = " ".join(parts[1:])

        return first_name, last_name

    def create_student_accounts(self, request, queryset):

        enquiries = queryset.order_by(
            'training_needed',
            'student_class',
            'name'
        )

        created_students = []
        skipped_students = []

        for enquiry in enquiries:

            if enquiry.created_user:
                skipped_students.append({
                    'name': enquiry.name,
                    'reason': 'Already created',
                    'username': enquiry.created_user.username,
                })
                continue

            class_name = self.get_class_name(enquiry)

            class_level, created = ClassLevel.objects.get_or_create(
                name=class_name
            )

            username = self.get_unique_username(enquiry)
            password = self.generate_password()

            first_name, last_name = self.split_name(enquiry.name)

            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            StudentProfile.objects.create(
                user=user,
                class_level=class_level
            )

            enquiry.created_user = user
            enquiry.is_contacted = True

            if enquiry.remarks:
                enquiry.remarks += f"\\nStudent account created. Username: {username}"
            else:
                enquiry.remarks = f"Student account created. Username: {username}"

            enquiry.save()

            created_students.append({
                'name': enquiry.name,
                'phone': enquiry.phone_number,
                'class_name': class_name,
                'training': enquiry.get_training_needed_display(),
                'username': username,
                'password': password,
            })

        return self.download_created_students_pdf(
            created_students,
            skipped_students
        )

    create_student_accounts.short_description = (
        "Create student user accounts and download login PDF"
    )

    def download_created_students_pdf(self, created_students, skipped_students):

        buffer = BytesIO()

        pdf = canvas.Canvas(buffer, pagesize=A4)

        width, height = A4

        y = height - 45

        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawCentredString(
            width / 2,
            y,
            "Master X's Academy"
        )

        y -= 24

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawCentredString(
            width / 2,
            y,
            "New Student Accounts Created"
        )

        y -= 35

        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(40, y, "No")
        pdf.drawString(65, y, "Name")
        pdf.drawString(180, y, "Class")
        pdf.drawString(265, y, "Training")
        pdf.drawString(365, y, "Username")
        pdf.drawString(465, y, "Password")

        y -= 8
        pdf.line(40, y, 555, y)
        y -= 18

        pdf.setFont("Helvetica", 8)

        serial_no = 0

        for student in created_students:
            serial_no += 1

            if y < 65:
                pdf.showPage()
                y = height - 45

                pdf.setFont("Helvetica-Bold", 9)
                pdf.drawString(40, y, "No")
                pdf.drawString(65, y, "Name")
                pdf.drawString(180, y, "Class")
                pdf.drawString(265, y, "Training")
                pdf.drawString(365, y, "Username")
                pdf.drawString(465, y, "Password")

                y -= 8
                pdf.line(40, y, 555, y)
                y -= 18

                pdf.setFont("Helvetica", 8)

            pdf.drawString(40, y, str(serial_no))
            pdf.drawString(65, y, student['name'][:18])
            pdf.drawString(180, y, student['class_name'][:16])
            pdf.drawString(265, y, student['training'][:17])
            pdf.drawString(365, y, student['username'][:15])
            pdf.drawString(465, y, student['password'])

            y -= 20

        if skipped_students:
            y -= 20

            if y < 100:
                pdf.showPage()
                y = height - 45

            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(40, y, "Skipped / Already Created")

            y -= 22

            pdf.setFont("Helvetica", 8)

            for student in skipped_students:
                if y < 60:
                    pdf.showPage()
                    y = height - 45
                    pdf.setFont("Helvetica", 8)

                pdf.drawString(
                    40,
                    y,
                    f"{student['name'][:25]} - {student['reason']} - {student['username']}"
                )

                y -= 18

        if not created_students and not skipped_students:
            pdf.setFont("Helvetica", 11)
            pdf.drawString(
                40,
                y,
                "No selected enquiry was processed."
            )

        pdf.save()

        buffer.seek(0)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename="new_student_accounts.pdf",
            content_type="application/pdf"
        )

    def mark_as_contacted(self, request, queryset):
        updated = queryset.update(is_contacted=True)

        self.message_user(
            request,
            f"{updated} registration enquiry/enquiries marked as contacted."
        )

    mark_as_contacted.short_description = "Mark selected enquiries as contacted"

    def mark_as_not_contacted(self, request, queryset):
        updated = queryset.update(is_contacted=False)

        self.message_user(
            request,
            f"{updated} registration enquiry/enquiries marked as not contacted."
        )

    mark_as_not_contacted.short_description = "Mark selected enquiries as not contacted"
