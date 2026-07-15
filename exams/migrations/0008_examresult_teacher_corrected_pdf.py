# Generated for Master X's Academy answer PDF correction upload

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0007_examresult_submitted_answer_pdf'),
    ]

    operations = [
        migrations.AddField(
            model_name='examresult',
            name='teacher_corrected_pdf',
            field=models.FileField(
                blank=True,
                help_text='Upload the teacher-valued/corrected PDF after marking the student answer PDF.',
                null=True,
                upload_to='exam_teacher_corrected_pdfs/'
            ),
        ),
    ]
