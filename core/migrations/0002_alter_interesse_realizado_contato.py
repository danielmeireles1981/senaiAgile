# Generated by Django 5.0.7 on 2024-08-02 16:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interesse',
            name='realizado_contato',
            field=models.CharField(choices=[('sim', 'Sim'), ('nao', 'Não')], default='nao', max_length=3),
        ),
    ]
