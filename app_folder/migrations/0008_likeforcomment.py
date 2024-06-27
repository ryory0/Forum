# Generated by Django 4.1.3 on 2023-03-10 08:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app_folder', '0007_thread_likes'),
    ]

    operations = [
        migrations.CreateModel(
            name='LikeForComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_folder.comment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]