# Generated by Django 5.0.4 on 2024-07-01 16:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mysite", "0007_user_is_admin"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_staff",
            field=models.BooleanField(default=False),
        ),
    ]
