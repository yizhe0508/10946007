# Generated by Django 5.0.4 on 2024-07-07 09:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mysite", "0012_remove_user_unique_email_constraint_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_email_verified",
            field=models.BooleanField(default=False, verbose_name="信箱已驗證"),
        ),
    ]