# Generated for Master X's Academy long upload filename fix

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0008_examresult_teacher_corrected_pdf'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exam',
            name='question_paper_file',
            field=models.FileField(
                blank=True,
                help_text='Use only for Question Paper + Bulk Answer Upload exam. Upload PDF or image.',
                max_length=255,
                null=True,
                upload_to='exam_question_papers/'
            ),
        ),
        migrations.AlterField(
            model_name='exam',
            name='answer_pdf',
            field=models.FileField(
                blank=True,
                max_length=255,
                null=True,
                upload_to='exam_answer_pdfs/'
            ),
        ),
        migrations.AlterField(
            model_name='question',
            name='question_image',
            field=models.FileField(
                blank=True,
                max_length=255,
                null=True,
                upload_to='exam_question_images/'
            ),
        ),
        migrations.AlterField(
            model_name='examresult',
            name='submitted_answer_pdf',
            field=models.FileField(
                blank=True,
                help_text='Auto-generated PDF created from the student uploaded answer images.',
                max_length=255,
                null=True,
                upload_to='exam_submitted_answer_pdfs/'
            ),
        ),
        migrations.AlterField(
            model_name='examresult',
            name='teacher_corrected_pdf',
            field=models.FileField(
                blank=True,
                help_text='Upload the teacher-valued/corrected PDF after marking the student answer PDF.',
                max_length=255,
                null=True,
                upload_to='exam_teacher_corrected_pdfs/'
            ),
        ),
        migrations.AlterField(
            model_name='studentanswer',
            name='answer_photo',
            field=models.FileField(
                blank=True,
                max_length=255,
                null=True,
                upload_to='exam_answers/'
            ),
        ),
        migrations.AlterField(
            model_name='bulkanswerimage',
            name='answer_image',
            field=models.FileField(
                max_length=255,
                upload_to='exam_bulk_answer_images/'
            ),
        ),
    ]
