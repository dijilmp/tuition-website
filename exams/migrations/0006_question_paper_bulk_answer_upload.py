from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0005_question_question_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exam',
            name='exam_type',
            field=models.CharField(
                choices=[
                    ('mcq', 'Multiple Choice'),
                    ('one_line', 'One Line Answer'),
                    ('photo_upload', 'Photo Upload Answer'),
                    ('question_paper_upload', 'Question Paper + Bulk Answer Upload'),
                ],
                max_length=30
            ),
        ),
        migrations.AddField(
            model_name='exam',
            name='question_paper_file',
            field=models.FileField(
                blank=True,
                help_text='Use only for Question Paper + Bulk Answer Upload exam. Upload PDF or image.',
                null=True,
                upload_to='exam_question_papers/'
            ),
        ),
        migrations.CreateModel(
            name='BulkAnswerImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_image', models.FileField(upload_to='exam_bulk_answer_images/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.PositiveIntegerField(default=1)),
                ('result', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bulk_answer_images', to='exams.examresult')),
            ],
            options={
                'verbose_name': 'Bulk Answer Image',
                'verbose_name_plural': 'Bulk Answer Images',
                'ordering': ['order', 'id'],
            },
        ),
    ]
