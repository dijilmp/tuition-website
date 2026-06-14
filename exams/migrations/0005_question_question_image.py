from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0004_exam_answer_pdf_exam_show_answer_pdf'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='question_image',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='exam_question_images/'
            ),
        ),
    ]
