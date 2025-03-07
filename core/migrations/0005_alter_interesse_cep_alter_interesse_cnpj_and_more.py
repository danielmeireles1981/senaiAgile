# Generated by Django 5.0.7 on 2024-08-09 16:21

import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_registroedicaointeresse'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interesse',
            name='cep',
            field=models.CharField(blank=True, default='00000-000', max_length=9),
        ),
        migrations.AlterField(
            model_name='interesse',
            name='cnpj',
            field=models.CharField(blank=True, max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name='interesse',
            name='data_envio',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='interesse',
            name='mensagem',
            field=models.TextField(blank=True, default='Mensagem padrão'),
        ),
        migrations.AlterField(
            model_name='interesse',
            name='pagina_site',
            field=models.URLField(blank=True, default='http://www.site.com.br'),
        ),
        migrations.AlterField(
            model_name='interesse',
            name='telefone_comercial',
            field=models.CharField(blank=True, default='(00) 0000-0000', max_length=20),
        ),
        migrations.AlterField(
            model_name='registroedicaointeresse',
            name='data_hora_registro',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='registroedicaointeresse',
            name='numero_atendimento',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AlterField(
            model_name='registroedicaointeresse',
            name='realizada_contato',
            field=models.CharField(choices=[('sim', 'Sim'), ('nao', 'Não')], default='nao', max_length=10),
        ),
    ]
