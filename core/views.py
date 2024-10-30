from .forms import LoginForm, InteresseForm, CursoForm, EditarInteresseForm
from .models import Interesse, Curso
from .models import RegistroEdicaoInteresse
from datetime import datetime, time
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.db import models
from django.db.models import Count
from django.db.models import Exists, OuterRef
from django.db.models import Q
from django.db.models import Subquery
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from io import BytesIO
from xhtml2pdf import pisa
import chardet
import csv
import logging
import os
import uuid
from .utils import gerar_pdf_resultados_testes, executar_testes

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


class CursoCreateView(LoginRequiredMixin, View):
    template_name = 'core/curso_form.html'
    success_url = reverse_lazy('cadastrar-curso')

    def get(self, request, *args, **kwargs):
        # Exibe o formulário da página
        form = CursoForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        # Verifica se um arquivo CSV foi enviado
        csv_file = request.FILES.get('csv_file')
        if csv_file:
            # Lógica para importar cursos via CSV
            try:
                # Detecta a codificação do arquivo
                raw_data = csv_file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                logger.info(f"Arquivo CSV detectado com codificação: {encoding}")

                # Decodifica o arquivo com a codificação detectada
                decoded_file = raw_data.decode(encoding).splitlines()

                # Remover BOM, se presente
                if decoded_file[0].startswith('\ufeff'):
                    decoded_file[0] = decoded_file[0].replace('\ufeff', '')
                    logger.info("BOM encontrado e removido do arquivo CSV.")

                reader = csv.DictReader(decoded_file, delimiter=';')

                cursos_criados = 0
                cursos_ignorados = 0

                # Iterando por cada linha do CSV
                for linha in reader:
                    codigo_curso = linha['codigo_curso'].strip()
                    nome_curso = linha['nome_curso'].strip()

                    # Verifica se o curso já existe no banco de dados
                    if not Curso.objects.filter(codigo_curso=codigo_curso).exists():
                        Curso.objects.create(codigo_curso=codigo_curso, nome_curso=nome_curso)
                        cursos_criados += 1
                        logger.info(f"Curso {nome_curso} criado com sucesso.")
                    else:
                        cursos_ignorados += 1
                        logger.warning(f"Curso {nome_curso} já existe, ignorado.")

                messages.success(self.request,
                                 f"{cursos_criados} cursos criados com sucesso, {cursos_ignorados} cursos ignorados.")
                return redirect(self.success_url)

            except csv.Error as e:
                logger.error(f"Erro ao processar o arquivo CSV: {e}")
                messages.error(self.request, f"Erro ao processar o arquivo CSV: {e}")
                return redirect(self.success_url)

            except Exception as e:
                logger.error(f"Erro desconhecido durante a importação: {e}")
                messages.error(self.request, f"Erro desconhecido durante a importação: {e}")
                return redirect(self.success_url)

        else:
            # Lógica para criação manual de cursos
            form = CursoForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(self.request, "Curso criado com sucesso!")
                return redirect(self.success_url)
            else:
                messages.error(self.request, "Erro ao criar o curso. Verifique os dados informados.")
                return render(request, self.template_name, {'form': form})


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'core/home.html'


class ListarDadosView(LoginRequiredMixin, ListView):
    model = Interesse
    template_name = 'core/listar_dados.html'
    context_object_name = 'interesses'
    paginate_by = 5  # Define 5 registros por página

    def get_queryset(self):
        # Inicializando o queryset
        queryset = super().get_queryset()

        # Subquery para obter o status mais recente de "realizado_contato" para cada Interesse
        latest_edicao = RegistroEdicaoInteresse.objects.filter(
            interesse_id=OuterRef('pk')
        ).order_by('-data_hora_registro')

        queryset = queryset.annotate(
            realizado_contato=Subquery(latest_edicao.values('realizada_contato')[:1])
        ).order_by('data_envio')

        # Filtros existentes de data
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')

        if data_inicio and data_fim:
            try:
                data_inicio = datetime.combine(datetime.strptime(data_inicio, "%Y-%m-%d").date(), time.min)
                data_fim = datetime.combine(datetime.strptime(data_fim, "%Y-%m-%d").date(), time.max)
                queryset = queryset.filter(data_envio__range=[data_inicio, data_fim])
            except Exception as e:
                logger.error(f"Erro ao processar as datas: {e}")

        # Filtro por curso
        curso = self.request.GET.get('curso')
        if curso:
            queryset = queryset.filter(curso__id=curso)

        # Filtro por realizado_contato
        realizado_contato = self.request.GET.get('realizado_contato', 'nao')  # Padrão é 'não'

        if realizado_contato == 'nao':
            queryset = queryset.filter(
                models.Q(realizado_contato__iexact='nao') | models.Q(realizado_contato__isnull=True)
            )
        elif realizado_contato:
            queryset = queryset.filter(realizado_contato__iexact=realizado_contato)

        # Substituindo valores 'None' por 'NÃO' para o campo realizado_contato
        for interesse in queryset:
            if interesse.realizado_contato is None:
                interesse.realizado_contato = 'não'

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cursos'] = Curso.objects.all().order_by('nome_curso')
        context['realizado_contato_choices'] = RegistroEdicaoInteresse.REALIZADO_CONTATO_CHOICES

        # Definir 'realizado_contato' como 'nao' no contexto, caso não tenha sido enviado
        if not self.request.GET.get('realizado_contato'):
            context['selected_realizado_contato'] = 'nao'
        else:
            context['selected_realizado_contato'] = self.request.GET.get('realizado_contato')

        return context


class VisualizarInteresseView(LoginRequiredMixin, DetailView):
    model = Interesse
    template_name = 'core/visualizar_interesse.html'
    context_object_name = 'interesse'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ultimo_registro = RegistroEdicaoInteresse.objects.filter(interesse=self.object).order_by(
            '-data_hora_registro').first()

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
        try:
            interesse_id = self.kwargs.get('pk')
            interesse = Interesse.objects.get(id=interesse_id)

            # Log dos dados recebidos no formulário
            logger.info(f"Dados do formulário de edição recebidos: {form.cleaned_data}")

            # Criar um novo registro de atendimento
            registro = form.save(commit=False)
            registro.interesse = interesse
            registro.numero_atendimento = uuid.uuid4()  # Gerar número de atendimento
            registro.usuario = self.request.user.username  # Adiciona o nome do usuário logado
            registro.data_hora_registro = timezone.now()  # Adicionar data/hora do registro

            # Verificar se um arquivo foi enviado e associar ao registro
            if 'arquivo_evidencia' in form.files:
                registro.arquivo_evidencia = form.files['arquivo_evidencia']

            registro.save()
            messages.success(self.request, "Atendimento registrado com sucesso.")
            return super().form_valid(form)

        except Exception as e:
            # Captura qualquer erro que ocorrer durante o processo e registra no log
            logger.error(f"Erro ao salvar o registro de atendimento: {e}")
            messages.error(self.request, "Erro ao atualizar interesse. Verifique os dados e tente novamente.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        # Registrar os erros do formulário para análise
        logger.warning(f"Formulário inválido: {form.errors}")
        messages.error(self.request, "Erro ao atualizar interesse. Verifique os dados e tente novamente.")
        return super().form_invalid(form)

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


class CSVUploadView(View):
    template_name = 'core/csv_upload.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv_file')
        log_messages = []

        if not csv_file.name.endswith('.csv'):
            log_messages.append('Por favor, envie um arquivo CSV.')
            return render(request, self.template_name, {'log_messages': log_messages})

        try:
            # Detectar a codificação do arquivo
            raw_data = csv_file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']

            # Decodificar o arquivo com a codificação detectada
            decoded_file = raw_data.decode(encoding).splitlines()
            reader = csv.DictReader(decoded_file, delimiter=';')

            interesses_importados = 0
            interesses_duplicados = 0
            linha_atual = 1  # Para acompanhar a linha processada

            for row in reader:
                linha_atual += 1
                try:
                    # Verificar se o curso já existe ou criar um novo
                    curso, created = Curso.objects.get_or_create(
                        codigo_curso=row['Id Curso'],
                        defaults={'nome_curso': row['Nome Curso']}
                    )

                    # Verificar se já existe um interesse com o mesmo email e curso (sem verificar data_envio)
                    interesse_exists = Interesse.objects.filter(
                        email=row['E-mail'],
                        curso=curso
                    ).exists()

                    if not interesse_exists:
                        # Criar novo interesse
                        Interesse.objects.create(
                            razao_social=row['Razão Social'],
                            email=row['E-mail'],
                            pagina_site=row.get('Site', ''),
                            telefone_comercial=row.get('Telefone Comercial', ''),
                            celular=row.get('Celular', ''),
                            nome_representante=row.get('Nome Representante', ''),
                            cnpj=row.get('CNPJ', ''),
                            cep=row.get('CEP', ''),
                            cidade=row['Cidade'],
                            mensagem=row.get('Mensagem', ''),
                            data_envio=datetime.now(),  # Adicionando a data e hora atual
                            curso=curso
                        )
                        interesses_importados += 1
                        log_messages.append(f"Interesse de {row['Razão Social']} importado com sucesso.")
                    else:
                        interesses_duplicados += 1
                        log_messages.append(f"Interesse de {row['Razão Social']} já existe e foi ignorado.")

                except KeyError as e:
                    log_messages.append(f"Erro ao processar a linha {linha_atual}: chave ausente - {e}")
                    continue
                except ValueError as e:
                    log_messages.append(f"Erro ao processar a linha {linha_atual}: erro de valor - {e}")
                    continue
                except Exception as e:
                    log_messages.append(f"Erro inesperado na linha {linha_atual}: {e}")
                    continue

            log_messages.append(f"{interesses_importados} interesses importados com sucesso.")
            log_messages.append(f"{interesses_duplicados} interesses duplicados foram ignorados.")
            return render(request, self.template_name, {'log_messages': log_messages})

        except Exception as e:
            log_messages.append(f'Erro ao processar o arquivo: {e}')
            return render(request, self.template_name, {'log_messages': log_messages})


def gerar_pdf(request):
    # Obter os filtros da requisição GET
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    curso_id = request.GET.get('curso')

    # Aplicar os filtros
    interesses = Interesse.objects.all()

    if data_inicio and data_fim:
        interesses = interesses.filter(data_envio__range=[data_inicio, data_fim])

    if curso_id:
        interesses = interesses.filter(curso_id=curso_id)

    # Obter o caminho absoluto das imagens
    logo_caminho = os.path.join(settings.BASE_DIR, 'static', 'images', 'senai-logo.png')
    rodape_caminho = os.path.join(settings.BASE_DIR, 'static', 'images', 'senai-logo.png')

    # Preparar os dados para o template do PDF
    template_path = 'core/relatorio_pdf.html'
    context = {
        'interesses': interesses,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'curso': Curso.objects.get(id=curso_id) if curso_id else 'Todos',
        'logo_caminho': logo_caminho,  # Caminho absoluto da imagem
        'rodape_caminho': rodape_caminho,  # Caminho absoluto da imagem
    }

    # Renderizar o template com os dados para PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="relatorio.pdf"'

    # Renderizar para PDF usando xhtml2pdf
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=response)

    if pisa_status.err:
        return HttpResponse('Erro ao gerar PDF', status=400)

    return response


def exibir_resultados_testes(request):
    # Executar os testes e capturar os resultados
    resultados = executar_testes()
    print(resultados)

    # Renderizar os resultados na página
    return render(request, 'core/resultados_testes.html', {
        'resultados': resultados
    })
