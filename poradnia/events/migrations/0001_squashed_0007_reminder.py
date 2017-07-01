# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-01 13:59
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [(b'events', '0001_initial'), (b'events', '0002_auto_20150321_1246'), (b'events', '0003_auto_20150321_2014'), (b'events', '0004_auto_20150322_0543'), (b'events', '0005_auto_20150503_1741'), (b'events', '0006_remove_event_for_client'), (b'events', '0007_reminder')]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cases', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alarm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deadline', models.BooleanField(default=False, verbose_name='Dead-line')),
                ('time', models.DateTimeField(verbose_name='Time')),
                ('text', models.CharField(max_length=150, verbose_name='Subject')),
                ('created_on', models.DateTimeField(auto_now_add=True, verbose_name='Created on')),
                ('modified_on', models.DateTimeField(auto_now=True, null=True, verbose_name='Modified on')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Created by')),
                ('modified_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='event_modified_by', to=settings.AUTH_USER_MODEL, verbose_name='Modified by')),
                ('case', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='cases.Case')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Event',
                'verbose_name_plural': 'Events',
            },
        ),
        migrations.AddField(
            model_name='alarm',
            name='event',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='events.Event'),
        ),
        migrations.AddField(
            model_name='alarm',
            name='case',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='cases.Case'),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name='alarm',
            options={'verbose_name': 'Alarm', 'verbose_name_plural': 'Alarms'},
        ),
        migrations.CreateModel(
            name='Reminder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('triggered', models.BooleanField(default=False)),
                ('event', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='user_alarms', to='events.Event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Reminder',
                'verbose_name_plural': 'Reminders',
            },
        ),
    ]
