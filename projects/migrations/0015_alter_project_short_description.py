# Generated by Django 5.1.5 on 2025-04-22 13:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0014_alter_project_short_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='short_description',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
