# Generated by Django 5.1 on 2024-11-09 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='IntegrationsModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(blank=True, max_length=5000, null=True)),
                ('access_token', models.CharField(blank=True, max_length=5000, null=True)),
                ('access_expire', models.DateTimeField(blank=True, null=True)),
                ('refresh_token', models.CharField(blank=True, max_length=5000, null=True)),
                ('platform', models.CharField(choices=[('X', 'X'), ('LinkedIn', 'LinkedIn'), ('Facebook', 'Facebook'), ('Instagram', 'Instagram'), ('Threads', 'Threads'), ('TikTok', 'TikTok'), ('YouTube', 'YouTube')], max_length=1000)),
            ],
            options={
                'verbose_name_plural': 'integrations',
            },
        ),
    ]
