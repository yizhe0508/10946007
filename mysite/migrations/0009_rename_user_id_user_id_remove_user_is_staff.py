# Generated by Django 5.0.4 on 2024-07-01 17:46

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("mysite", "0008_user_is_staff"),
    ]

    operations = [
        migrations.RenameField(
            model_name="user",
            old_name="user_id",
            new_name="id",
        ),
        migrations.RemoveField(
            model_name="user",
            name="is_staff",
        ),
    ]