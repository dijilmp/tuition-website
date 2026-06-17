from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistrationEnquiry',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'training_needed',
                    models.CharField(
                        choices=[
                            ('uss', 'USS Exam'),
                            ('nmms', 'National Means-cum-Merit'),
                            ('school_subjects', 'School Subjects')
                        ],
                        max_length=30
                    )
                ),
                (
                    'name',
                    models.CharField(max_length=150)
                ),
                (
                    'phone_number',
                    models.CharField(max_length=20)
                ),
                (
                    'address',
                    models.TextField()
                ),
                (
                    'student_class',
                    models.CharField(max_length=50)
                ),
                (
                    'syllabus',
                    models.CharField(
                        choices=[
                            ('state', 'State'),
                            ('cbse', 'CBSE'),
                            ('icse', 'ICSE')
                        ],
                        max_length=20
                    )
                ),
                (
                    'school_name',
                    models.CharField(max_length=200)
                ),
                (
                    'class_type',
                    models.CharField(
                        choices=[
                            ('individual', 'Individual'),
                            ('group', 'Group')
                        ],
                        max_length=20
                    )
                ),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True)
                ),
                (
                    'is_contacted',
                    models.BooleanField(default=False)
                ),
                (
                    'remarks',
                    models.TextField(
                        blank=True,
                        null=True
                    )
                ),
            ],
            options={
                'ordering': [
                    'training_needed',
                    'student_class',
                    '-created_at',
                ],
            },
        ),
    ]
