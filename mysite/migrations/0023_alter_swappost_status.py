# Generated by Django 5.0.4 on 2024-07-23 17:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("mysite", "0022_swappost_swapper"),
    ]

    operations = [
        migrations.AlterField(
            model_name="swappost",
            name="status",
            field=models.CharField(
                choices=[
                    ("WAITING", "待交換"),
                    ("IN_PROGRESS", "進行中"),
                    ("COMPLETED", "已完成"),
                    ("CANCELLED", "已取消"),
                ],
                default="WAITING",
                max_length=20,
            ),
        ),
    ]
