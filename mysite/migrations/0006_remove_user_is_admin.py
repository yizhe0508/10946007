# Generated by Django 5.0.4 on 2024-06-30 16:16

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("mysite", "0005_user_is_admin"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="is_admin",
        ),
    ]
