# Generated by Django 5.0.4 on 2024-07-01 18:30

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("mysite", "0011_user_unique_email_constraint"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="user",
            name="unique_email_constraint",
        ),
        migrations.RenameField(
            model_name="user",
            old_name="id",
            new_name="user_id",
        ),
    ]
