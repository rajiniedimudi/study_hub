# Generated by Django 4.2.11 on 2024-05-23 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_remove_notes_documents_delete_documents'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParentGuidance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issue_name', models.CharField(max_length=50)),
                ('issue_description', models.TextField()),
            ],
        ),
    ]
