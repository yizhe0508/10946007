# Generated by Django 5.0.4 on 2024-07-01 18:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("mysite", "0010_rename_is_admin_user_is_staff_user_groups_and_more"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                fields=("email",), name="unique_email_constraint"
            ),
        ),
    ]