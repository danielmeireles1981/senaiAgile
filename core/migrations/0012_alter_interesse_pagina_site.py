# Generated by Django 5.0.7 on 2024-08-14 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_alter_registroedicaointeresse_usuario'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interesse',
            name='pagina_site',
            field=models.CharField(blank=True, default='Origem', max_length=100),
        ),
    ]
