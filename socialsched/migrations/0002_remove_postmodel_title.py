# Generated by Django 5.2 on 2025-04-18 14:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('socialsched', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postmodel',
            name='title',
        ),
    ]
