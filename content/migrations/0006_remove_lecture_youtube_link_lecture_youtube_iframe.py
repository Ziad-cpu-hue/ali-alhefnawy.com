# Generated by Django 5.1.6 on 2025-03-10 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0005_lecture_youtube_link'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lecture',
            name='youtube_link',
        ),
        migrations.AddField(
            model_name='lecture',
            name='youtube_iframe',
            field=models.TextField(blank=True, null=True, verbose_name='كود تضمين فيديو YouTube'),
        ),
    ]
