# Generated by Django 5.2 on 2025-05-10 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0003_alter_integrationsmodel_platform'),
    ]

    operations = [
        migrations.AlterField(
            model_name='integrationsmodel',
            name='platform',
            field=models.CharField(choices=[('X', 'X'), ('LinkedIn', 'LinkedIn'), ('Facebook', 'Facebook'), ('Instagram', 'Instagram')], max_length=1000),
        ),
    ]
