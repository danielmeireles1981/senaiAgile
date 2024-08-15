import uuid
from django.db import models
from django.utils import timezone  # Certifique-se de importar corretamente
from django.contrib.auth.views import LoginView as BaseLoginView
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.db.models import Count
from .forms import LoginForm, InteresseForm, CursoForm, EditarInteresseForm
import logging
from django.db.models import OuterRef, Subquery
import csv
from django.contrib import messages
import chardet  # Biblioteca para detectar codificação
from django.db.models import Exists, OuterRef, Q, Value
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from datetime import datetime, time
from django.db.models import Count
from django.shortcuts import render
from django.views import View
from .models import Interesse, Curso, RegistroEdicaoInteresse

# Configure o logger
logger = logging.getLogger(__name__)

class LoginView(BaseLoginView):
    form_class = LoginForm
    template_name = 'core/login.html'

class InteresseCreateView(LoginRequiredMixin, CreateView):
    model = Interesse
    form_class = InteresseForm
    template_name = 'core/interesse_form.html'
    success_url = reverse_lazy('cadastrar-interesse')

    def get_initial(self):
        initial = super().get_initial()
        initial['data_envio'] = timezone.now().date()  # Define a data atual
        return initial

    def form_valid(self, form):
        try:
            # Log antes de salvar
            logger.debug('Tentando salvar o formulário com os dados: %s', form.cleaned_data)

            # Salva o interesse
            interesse = form.save()

            # Cria o primeiro registro de edição com realizado_contato como "não"
            RegistroEdicaoInteresse.objects.create(
                interesse=interesse,
                realizada_contato='nao',  # Define o valor padrão como "não"
                forma_contato='',  # Deixe em branco ou ajuste conforme necessário
                numero_atendimento=uuid.uuid4(),
                observacoes='',  # Ajuste conforme necessário
                usuario=self.request.user.username  # Adiciona o nome do usuário logado
            )

            # Log após salvar com sucesso
            logger.debug('Formulário salvo com sucesso.')

            messages.success(self.request, 'Interesse cadastrado com sucesso!')
            return redirect(self.success_url)
        except Exception as e:
            # Log se houver um erro
            logger.error('Erro ao salvar o formulário: %s', e)
            messages.error(self.request, 'Erro ao cadastrar interesse.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        # Log quando o formulário é inválido
        logger.warning('Formulário inválido: %s', form.errors)
        return super().form_invalid(form)

class CursoCreateView(LoginRequiredMixin, CreateView):
    model = Curso
    form_class = CursoForm
    template_name = 'core/curso_form.html'
    success_url = reverse_lazy('cadastrar-curso')

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'core/home.html'


class ListarDadosView ( LoginRequiredMixin, ListView ):
    model = Interesse
    template_name = 'core/listar_dados.html'
    context_object_name = 'interesses'


    def get_queryset(self):
        # Inicializando o queryset
        queryset = super ().get_queryset ()

        # Subquery para obter o status mais recente de "realizado_contato" para cada Interesse
        latest_edicao = RegistroEdicaoInteresse.objects.filter (
            interesse_id=OuterRef ( 'pk' )
        ).order_by ( '-data_hora_registro' )

        queryset = queryset.annotate (
            realizado_contato=Subquery ( latest_edicao.values ( 'realizada_contato' )[:1] )
        ).order_by ( 'data_envio' )

        # Filtros existentes de data
        data_inicio = self.request.GET.get ( 'data_inicio' )
        data_fim = self.request.GET.get ( 'data_fim' )

        if data_inicio and data_fim:
            try:
                data_inicio = datetime.combine ( datetime.strptime ( data_inicio, "%Y-%m-%d" ).date (), time.min )
                data_fim = datetime.combine ( datetime.strptime ( data_fim, "%Y-%m-%d" ).date (), time.max )
                queryset = queryset.filter ( data_envio__range=[data_inicio, data_fim] )
            except Exception as e:
                logger.error ( f"Erro ao processar as datas: {e}" )

        # Filtro por curso
        curso = self.request.GET.get ( 'curso' )
        if curso:
            queryset = queryset.filter ( curso__id=curso )

        # Filtro por realizado_contato
        realizado_contato = self.request.GET.get ( 'realizado_contato' )

        if realizado_contato == 'nao':
            queryset = queryset.filter (
                models.Q ( realizado_contato__iexact='nao' ) | models.Q ( realizado_contato__isnull=True )
            )
        elif realizado_contato:
            queryset = queryset.filter ( realizado_contato__iexact=realizado_contato )

        # Substituindo valores 'None' por 'NÃO' para o campo realizado_contato
        for interesse in queryset:
            if interesse.realizado_contato is None:
                interesse.realizado_contato = 'não'

        return queryset

    def get_context_data(self, **kwargs):
        context = super ().get_context_data ( **kwargs )
        context['cursos'] = Curso.objects.all ().order_by ( 'nome_curso' )
        context['realizado_contato_choices'] = RegistroEdicaoInteresse.REALIZADO_CONTATO_CHOICES
        return context


class VisualizarInteresseView ( LoginRequiredMixin, DetailView ):
    model = Interesse
    template_name = 'core/visualizar_interesse.html'
    context_object_name = 'interesse'

    def get_context_data(self, **kwargs):
        context = super ().get_context_data ( **kwargs )
        ultimo_registro = RegistroEdicaoInteresse.objects.filter ( interesse=self.object ).order_by (
            '-data_hora_registro' ).first ()

        context['realizado_contato'] = ultimo_registro.realizada_contato if ultimo_registro else 'Não'
        context['forma_contato'] = ultimo_registro.forma_contato if ultimo_registro else 'N/A'
        context['observacoes'] = ultimo_registro.observacoes if ultimo_registro else 'Nenhuma observação'

        return context

class EditarInteresseView(LoginRequiredMixin, CreateView):
    model = RegistroEdicaoInteresse
    form_class = EditarInteresseForm
    template_name = 'core/editar_interesse.html'
    success_url = reverse_lazy('listar-dados')

    def form_valid(self, form):
        interesse_id = self.kwargs.get('pk')
        interesse = Interesse.objects.get(id=interesse_id)
        registro = form.save(commit=False)
        registro.interesse = interesse
        registro.numero_atendimento = uuid.uuid4()  # Gerar número de atendimento
        registro.usuario = self.request.user.username  # Adiciona o nome do usuário logado
        registro.data_hora_registro = timezone.now()  # Adicionar data/hora do registro
        registro.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        interesse_id = self.kwargs.get('pk')
        context['interesse'] = Interesse.objects.get(id=interesse_id)
        context['numero_atendimento'] = uuid.uuid4()  # Gera um novo número de atendimento para exibição
        context['data_hora_registro'] = timezone.now()  # Data/hora atual para exibição
        return context

class RelatoriosView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Aplicar filtros
        interesses = Interesse.objects.all()

        # Filtro de data
        data_inicio = request.GET.get('data_inicio')
        data_fim = request.GET.get('data_fim')

        if data_inicio and data_fim:
            try:
                data_inicio = datetime.combine(datetime.strptime(data_inicio, "%Y-%m-%d").date(), time.min)
                data_fim = datetime.combine(datetime.strptime(data_fim, "%Y-%m-%d").date(), time.max)
                interesses = interesses.filter(data_envio__range=[data_inicio, data_fim])
            except Exception as e:
                print(f"Erro ao processar as datas: {e}")

        # Filtro de curso
        curso_id = request.GET.get('curso')
        if curso_id:
            interesses = interesses.filter(curso_id=curso_id)

        # Filtro de realizado_contato
        realizado_contato = request.GET.get('realizado_contato')
        if realizado_contato:
            if realizado_contato == 'nao':
                interesses = interesses.annotate(
                    contato_existe=Exists(
                        RegistroEdicaoInteresse.objects.filter(
                            interesse_id=OuterRef('pk'),
                            realizada_contato='sim'
                        )
                    )
                ).filter(Q(contato_existe=False) | Q(contato_existe=None))
            else:
                interesses = interesses.annotate(
                    contato_existe=Exists(
                        RegistroEdicaoInteresse.objects.filter(
                            interesse_id=OuterRef('pk'),
                            realizada_contato='sim'
                        )
                    )
                ).filter(contato_existe=True)

        # Contagem de interesses por curso
        interesses_por_curso = interesses.values('curso__nome_curso').annotate(total=Count('id')).order_by('-total')

        cursos = [item['curso__nome_curso'] for item in interesses_por_curso]
        totais = [item['total'] for item in interesses_por_curso]

        # Obter a lista de cursos e valores de realizado_contato para o formulário
        context = {
            'cursos': Curso.objects.all().order_by('nome_curso'),
            'realizado_contato_choices': [
                ('sim', 'Sim'),
                ('nao', 'Não')
            ],
            'labels': cursos,  # Labels dos cursos para o gráfico
            'data': totais  # Dados dos totais para o gráfico
        }

        return render(request, 'core/relatorios.html', context)


class LogoutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, 'Você saiu do sistema com sucesso.')
        return redirect('login')


class CSVUploadView ( View ):
    template_name = 'core/csv_upload.html'

    def get(self, request, *args, **kwargs):
        return render ( request, self.template_name )

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get ( 'csv_file' )
        log_messages = []

        if not csv_file.name.endswith ( '.csv' ):
            log_messages.append ( 'Por favor, envie um arquivo CSV.' )
            return render ( request, self.template_name, {'log_messages': log_messages} )

        try:
            # Detectar a codificação do arquivo
            raw_data = csv_file.read ()
            result = chardet.detect ( raw_data )
            encoding = result['encoding']

            # Decodificar o arquivo com a codificação detectada
            decoded_file = raw_data.decode ( encoding ).splitlines ()
            reader = csv.DictReader ( decoded_file, delimiter=';' )

            for row in reader:
                try:
                    # Converter a data de envio para o formato correto
                    data_envio = datetime.strptime ( row['Data Envio'], '%d/%m/%Y %H:%M' )

                    curso, created = Curso.objects.get_or_create (
                        codigo_curso=row['Id Curso'],
                        defaults={'nome_curso': row['Nome Curso']}
                    )

                    if created:
                        log_messages.append ( f"Curso {row['Nome Curso']} criado com sucesso." )

                    Interesse.objects.create (
                        razao_social=row['Razão Social'],
                        email=row['E-mail'],
                        pagina_site=row['Site'],
                        data_envio=data_envio,  # Usando a data convertida
                        telefone_comercial=row['Telefone Comercial'],
                        celular=row['Celular'],
                        nome_representante=row['Nome Representante'],
                        cnpj=row['CNPJ'],
                        cep=row['CEP'],
                        cidade=row['Cidade'],
                        mensagem=row['Mensagem'],
                        curso=curso
                    )
                    log_messages.append ( f"Interesse de {row['Razão Social']} importado com sucesso." )
                except Exception as e:
                    log_messages.append ( f"Erro ao importar interesse {row['Razão Social']}: {e}" )

            return render ( request, self.template_name, {'log_messages': log_messages} )

        except Exception as e:
            log_messages.append ( f'Erro ao processar o arquivo: {e}' )
            return render ( request, self.template_name, {'log_messages': log_messages} )