# Generated by Django 3.1.13 on 2021-09-05 09:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userthread',
            name='is_sender',
            field=models.BooleanField(default=False),
        ),
    ]
