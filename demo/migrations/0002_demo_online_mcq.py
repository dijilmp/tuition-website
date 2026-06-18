from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DemoOnlineTest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('chapter_name', models.CharField(blank=True, max_length=200, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('duration_minutes', models.PositiveIntegerField(default=30)),
                ('total_marks', models.PositiveIntegerField(default=0)),
                ('show_result_after_submit', models.BooleanField(default=True)),
                ('allow_reattempt', models.BooleanField(default=False)),
                ('is_published', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('demo_option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='online_tests', to='demo.demooption')),
            ],
            options={
                'verbose_name': 'Demo Online MCQ Test',
                'verbose_name_plural': 'Demo Online MCQ Tests',
                'ordering': ['demo_option', 'order', 'title'],
            },
        ),
        migrations.CreateModel(
            name='DemoOnlineQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.TextField()),
                ('question_image', models.FileField(blank=True, null=True, upload_to='demo/online_questions/')),
                ('marks', models.PositiveIntegerField(default=1)),
                ('order', models.PositiveIntegerField(default=1)),
                ('online_test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='demo.demoonlinetest')),
            ],
            options={
                'verbose_name': 'Demo Online Question',
                'verbose_name_plural': 'Demo Online Questions',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='DemoOnlineChoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('choice_text', models.CharField(max_length=400)),
                ('is_correct', models.BooleanField(default=False)),
                ('order', models.PositiveIntegerField(default=1)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='demo.demoonlinequestion')),
            ],
            options={
                'verbose_name': 'Demo Online Choice',
                'verbose_name_plural': 'Demo Online Choices',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='DemoOnlineAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('is_submitted', models.BooleanField(default=False)),
                ('score', models.FloatField(default=0)),
                ('demo_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='online_attempts', to='demo.demorequest')),
                ('online_test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='demo.demoonlinetest')),
            ],
            options={
                'verbose_name': 'Demo Online Attempt',
                'verbose_name_plural': 'Demo Online Attempts',
                'ordering': ['-started_at'],
                'unique_together': {('demo_request', 'online_test')},
            },
        ),
        migrations.CreateModel(
            name='DemoOnlineAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_correct', models.BooleanField(default=False)),
                ('marks_awarded', models.FloatField(default=0)),
                ('attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='demo.demoonlineattempt')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='demo.demoonlinequestion')),
                ('selected_choice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='demo.demoonlinechoice')),
            ],
            options={
                'verbose_name': 'Demo Online Answer',
                'verbose_name_plural': 'Demo Online Answers',
                'unique_together': {('attempt', 'question')},
            },
        ),
    ]
