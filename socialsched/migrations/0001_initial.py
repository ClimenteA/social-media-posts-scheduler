# Generated by Django 5.2 on 2025-04-18 09:01

import django.utils.timezone
import socialsched.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PostModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.TextField(max_length=63206)),
                ('scheduled_on_date', models.DateField()),
                ('scheduled_on_time', models.TimeField()),
                ('scheduled_on', models.DateTimeField(blank=True, null=True)),
                ('media_file', models.FileField(blank=True, max_length=100000, null=True, upload_to=socialsched.models.get_filename)),
                ('post_on_x', models.BooleanField(blank=True, default=False, null=True)),
                ('post_on_instagram', models.BooleanField(blank=True, default=False, null=True)),
                ('post_on_facebook', models.BooleanField(blank=True, default=False, null=True)),
                ('post_on_linkedin', models.BooleanField(blank=True, default=False, null=True)),
                ('link_x', models.CharField(blank=True, max_length=50000, null=True)),
                ('link_instagram', models.CharField(blank=True, max_length=50000, null=True)),
                ('link_facebook', models.CharField(blank=True, max_length=50000, null=True)),
                ('link_linkedin', models.CharField(blank=True, max_length=50000, null=True)),
                ('created_at', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('posted', models.BooleanField(blank=True, default=False, null=True)),
            ],
            options={
                'verbose_name_plural': 'scheduled',
            },
        ),
    ]
