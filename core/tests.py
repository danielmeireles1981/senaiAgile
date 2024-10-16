from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import uuid  # Para gerar um nome de usuário único

from .models import Interesse, Curso


class InteresseCreateViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.curso = Curso.objects.create(codigo_curso="001", nome_curso="Curso Teste")
        # Usar um nome de usuário único
        unique_username = f'admin_{uuid.uuid4()}'
        self.user = self.client.force_login(User.objects.create_user(username=unique_username, password='ti@801-23'))
        self.url = reverse('cadastrar-interesse')

    def test_create_interesse_valid(self):
        response = self.client.post(self.url, {
            'razao_social': 'Empresa Teste',
            'email': 'email@teste.com',
            'pagina_site': 'site',
            'data_envio': timezone.now().date(),
            'telefone_comercial': '(00) 0000-0000',
            'celular': '(00) 99999-9999',
            'nome_representante': 'Representante Teste',
            'cnpj': '12345678900',
            'cep': '00000-000',
            'cidade': 'Cidade Teste',
            'mensagem': 'noite',
            'curso': self.curso.id,
        })
        if response.status_code == 302 and Interesse.objects.filter(email="email@teste.com").exists():
            print('✔️ Teste de criação de interesse com dados válidos: sucesso')
            print('\n')
        else:
            print('❌ Teste de criação de interesse com dados válidos: falha')
            print('\n')

    def test_create_interesse_invalid(self):
        response = self.client.post(self.url, {
            'razao_social': 'Empresa Teste',
            'pagina_site': 'site',
            'data_envio': timezone.now().date(),
            'telefone_comercial': '(00) 0000-0000',
            'celular': '(00) 99999-9999',
            'nome_representante': 'Representante Teste',
            'cnpj': '12345678900',
            'cep': '00000-000',
            'cidade': 'Cidade Teste',
            'mensagem': 'Padrão',
            'curso': self.curso.id,
        })
        if response.status_code == 200 and not Interesse.objects.filter(razao_social="Empresa Teste").exists():
            print('✔️ Teste de criação de interesse com dados inválidos (sem email): sucesso')
            print('\n')
        else:
            print('❌ Teste de criação de interesse com dados inválidos (sem email): falha')
            print('\n')
