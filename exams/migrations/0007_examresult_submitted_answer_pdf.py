from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0006_question_paper_bulk_answer_upload'),
    ]

    operations = [
        migrations.AddField(
            model_name='examresult',
            name='submitted_answer_pdf',
            field=models.FileField(
                blank=True,
                help_text='Auto-generated PDF created from the student uploaded answer images.',
                null=True,
                upload_to='exam_submitted_answer_pdfs/'
            ),
        ),
    ]
