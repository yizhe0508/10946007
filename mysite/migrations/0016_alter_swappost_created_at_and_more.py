# Generated by Django 5.0.4 on 2024-07-10 14:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "mysite",
            "0015_alter_message_options_chatroom_topic_alter_role_name_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="swappost",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="建立時間"),
        ),
        migrations.AlterField(
            model_name="swappost",
            name="desired_item",
            field=models.CharField(max_length=100, verbose_name="需求物品"),
        ),
        migrations.AlterField(
            model_name="swappost",
            name="item",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="swap_posts",
                to="mysite.item",
                verbose_name="物品",
            ),
        ),
        migrations.AlterField(
            model_name="swappost",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "等待交換"),
                    ("in_progress", "交換進行中"),
                    ("completed", "交換已完成"),
                    ("canceled", "交換已取消"),
                ],
                default="pending",
                max_length=12,
                verbose_name="狀態",
            ),
        ),
        migrations.AlterField(
            model_name="swappost",
            name="swap_location",
            field=models.CharField(max_length=100, verbose_name="交換地點"),
        ),
        migrations.AlterField(
            model_name="swappost",
            name="swap_role_name",
            field=models.CharField(max_length=100, verbose_name="交換角色名稱"),
        ),
        migrations.AlterField(
            model_name="swappost",
            name="swap_time",
            field=models.DateTimeField(verbose_name="交換時間"),
        ),
        migrations.AlterField(
            model_name="swappost",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="更新時間"),
        ),
        migrations.AlterField(
            model_name="swappost",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="swap_posts",
                to=settings.AUTH_USER_MODEL,
                verbose_name="使用者",
            ),
        ),
    ]
