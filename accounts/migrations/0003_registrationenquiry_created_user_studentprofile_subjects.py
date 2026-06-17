from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('materials', '0001_initial'),
        ('accounts', '0002_registrationenquiry'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrationenquiry',
            name='created_user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='registration_enquiries',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='subjects',
            field=models.ManyToManyField(
                blank=True,
                to='materials.subject'
            ),
        ),
    ]
