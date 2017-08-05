# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-05 11:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0004_auto_20170804_1947'),
    ]

    operations = [
        migrations.CreateModel(
            name='Graph',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('description', models.TextField(verbose_name='Description')),
            ],
            options={
                'verbose_name': 'Graph',
                'verbose_name_plural': 'Graphs',
            },
        ),
        migrations.AlterModelOptions(
            name='item',
            options={'ordering': ['key'], 'verbose_name': 'Item', 'verbose_name_plural': 'Items'},
        ),
        migrations.AddField(
            model_name='graph',
            name='items',
            field=models.ManyToManyField(to='stats.Item', verbose_name='Items'),
        ),
    ]
