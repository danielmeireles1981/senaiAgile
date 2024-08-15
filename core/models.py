from django.db import models
import uuid
from django.utils import timezone  # Importação necessária para usar a data e hora atual

class Curso(models.Model):
    codigo_curso = models.CharField(max_length=10, unique=True)
    nome_curso = models.CharField(max_length=100)

    def __str__(self):
        return self.nome_curso

class Interesse(models.Model):
    razao_social = models.CharField(max_length=100, default='Razão Social Padrão')
    email = models.EmailField()
    pagina_site = models.CharField(max_length=100, default='Origem', blank=True)
    data_envio = models.DateTimeField(default=timezone.now, null=True, blank=True)
    telefone_comercial = models.CharField(max_length=20, default='(00) 0000-0000', blank=True)
    celular = models.CharField(max_length=20, null=True, blank=True)
    nome_representante = models.CharField(max_length=100, default='Nome Padrão')
    cnpj = models.CharField(max_length=20, blank=True)
    cep = models.CharField(max_length=9, default='00000-000', blank=True)
    cidade = models.CharField(max_length=100)
    mensagem = models.TextField(default='Mensagem padrão', blank=True)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)

    @property
    def codigo_curso(self):
        return self.curso.codigo_curso
    def __str__(self):
        return self.nome_representante

class RegistroEdicaoInteresse(models.Model):
    REALIZADO_CONTATO_CHOICES = [
        ('sim', 'Sim'),
        ('nao', 'Não'),
    ]
    interesse = models.ForeignKey(Interesse, on_delete=models.CASCADE, related_name='edicoes')
    realizada_contato = models.CharField(max_length=10, choices=REALIZADO_CONTATO_CHOICES, default='nao')
    forma_contato = models.CharField(max_length=100)
    numero_atendimento = models.UUIDField(default=uuid.uuid4, editable=False)  # Gera automaticamente
    data_hora_registro = models.DateTimeField(auto_now_add=True)  # Data/hora de criação do registro
    observacoes = models.TextField()
    editado_em = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=150)  # Novo campo para armazenar o nome do usuário

    def __str__(self):
        return f'Edição de {self.interesse.nome_representante} em {self.editado_em}'
