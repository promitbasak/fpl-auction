# Generated by Django 3.2.6 on 2021-09-01 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0002_manager_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Deadlines',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField()),
                ('gw', models.IntegerField()),
                ('finished', models.BooleanField(blank=True, default=False)),
            ],
        ),
    ]
