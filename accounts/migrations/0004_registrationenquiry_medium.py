from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_registrationenquiry_created_user_studentprofile_subjects'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrationenquiry',
            name='medium',
            field=models.CharField(
                blank=True,
                choices=[
                    ('english', 'English'),
                    ('malayalam', 'Malayalam'),
                    ('kannada', 'Kannada'),
                    ('tamil', 'Tamil')
                ],
                max_length=20,
                null=True
            ),
        ),
    ]
