from django.db import migrations, models
import django.db.models.deletion


def create_default_categories(apps, schema_editor):
    DemoCategory = apps.get_model('demo', 'DemoCategory')

    defaults = [
        {
            'category_type': 'uss',
            'display_name': 'USS',
            'description': 'USS demo section',
            'order': 1,
        },
        {
            'category_type': 'nmms',
            'display_name': 'NMMS / NMCM',
            'description': 'NMMS / NMCM demo section',
            'order': 2,
        },
        {
            'category_type': 'school_tuition',
            'display_name': 'School Tuition',
            'description': 'School tuition demo section',
            'order': 3,
        },
    ]

    for item in defaults:
        DemoCategory.objects.get_or_create(
            category_type=item['category_type'],
            defaults=item
        )


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DemoCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category_type', models.CharField(choices=[('uss', 'USS'), ('nmms', 'NMMS / NMCM'), ('school_tuition', 'School Tuition')], max_length=30, unique=True)),
                ('display_name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=1)),
            ],
            options={
                'verbose_name': 'Demo Category',
                'verbose_name_plural': 'Demo Categories',
                'ordering': ['order', 'display_name'],
            },
        ),
        migrations.CreateModel(
            name='DemoOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Example: State Class 10 Maths Demo / USS Demo / NMMS Class 8 Demo', max_length=200)),
                ('class_name', models.CharField(help_text='Example: Class 8, Class 9, Class 10', max_length=50)),
                ('subject_name', models.CharField(blank=True, help_text='Example: Maths, Physics, Chemistry. Leave blank for USS/NMMS if not needed.', max_length=100, null=True)),
                ('syllabus', models.CharField(choices=[('state', 'State'), ('cbse', 'CBSE'), ('icse', 'ICSE')], default='state', max_length=20)),
                ('medium', models.CharField(blank=True, choices=[('english', 'English'), ('malayalam', 'Malayalam'), ('tamil', 'Tamil'), ('kannada', 'Kannada')], max_length=20, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=1)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='demo.democategory')),
            ],
            options={
                'verbose_name': 'Available Demo',
                'verbose_name_plural': 'Available Demos',
                'ordering': ['category', 'order', 'class_name', 'subject_name', 'title'],
            },
        ),
        migrations.CreateModel(
            name='DemoRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('mobile_number', models.CharField(max_length=20)),
                ('address', models.TextField()),
                ('school_name', models.CharField(max_length=200)),
                ('view_count', models.PositiveIntegerField(default=1)),
                ('first_viewed_at', models.DateTimeField(auto_now_add=True)),
                ('last_viewed_at', models.DateTimeField(auto_now=True)),
                ('is_contacted', models.BooleanField(default=False)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('demo_option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to='demo.demooption')),
            ],
            options={
                'verbose_name': 'Demo Request',
                'verbose_name_plural': 'Demo Requests',
                'ordering': ['-last_viewed_at'],
                'unique_together': {('demo_option', 'mobile_number')},
            },
        ),
        migrations.CreateModel(
            name='DemoNotice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('heading', models.CharField(default='Important Updates', max_length=200)),
                ('exam_date', models.CharField(blank=True, max_length=100, null=True)),
                ('scholarship_amount', models.CharField(blank=True, max_length=150, null=True)),
                ('registration_start_date', models.CharField(blank=True, max_length=100, null=True)),
                ('registration_end_date', models.CharField(blank=True, max_length=100, null=True)),
                ('message', models.TextField(blank=True, help_text='Admin can update this message frequently.', null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('demo_option', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notice', to='demo.demooption')),
            ],
            options={
                'verbose_name': 'Demo Notice',
                'verbose_name_plural': 'Demo Notices',
            },
        ),
        migrations.CreateModel(
            name='DemoStudyMaterial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('chapter_name', models.CharField(blank=True, max_length=200, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('pdf_file', models.FileField(blank=True, null=True, upload_to='demo/study_materials/')),
                ('external_link', models.URLField(blank=True, help_text='Optional YouTube/Drive/link', null=True)),
                ('is_published', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('demo_option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='study_materials', to='demo.demooption')),
            ],
            options={
                'verbose_name': 'Demo Study Material',
                'verbose_name_plural': 'Demo Study Materials',
                'ordering': ['demo_option', 'order', 'title'],
            },
        ),
        migrations.CreateModel(
            name='DemoMockTest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('chapter_name', models.CharField(blank=True, max_length=200, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('mock_number', models.PositiveIntegerField(default=1)),
                ('question_pdf', models.FileField(blank=True, null=True, upload_to='demo/mock_tests/questions/')),
                ('answer_key_pdf', models.FileField(blank=True, null=True, upload_to='demo/mock_tests/answer_keys/')),
                ('external_test_link', models.URLField(blank=True, help_text='Optional online test link. This will not touch existing exam system.', null=True)),
                ('is_published', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('demo_option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mock_tests', to='demo.demooption')),
            ],
            options={
                'verbose_name': 'Demo Mock Test',
                'verbose_name_plural': 'Demo Mock Tests',
                'ordering': ['demo_option', 'order', 'mock_number', 'title'],
            },
        ),
        migrations.RunPython(create_default_categories),
    ]
