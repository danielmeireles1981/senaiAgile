from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Interesse, Curso, RegistroEdicaoInteresse
from django.utils import timezone
from django.forms import modelformset_factory


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Usuário', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Senha', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class InteresseForm(forms.ModelForm):
    PAGINA_SITE_CHOICES = [
        ('site', 'Site'),
        ('presencial', 'Presencial'),
        ('telefone', 'Telefone'),
        ('whatsapp', 'Whatsapp'),
        ('email', 'Email'),
    ]

    MENSAGEM_CHOICES = [
        ('manha', 'Manhã'),
        ('tarde', 'Tarde'),
        ('noite', 'Noite'),
        ('sabadomanha', 'Sábado Manhã'),
        ('sabadotarde', 'Sábado Tarde')
    ]

    pagina_site = forms.ChoiceField(
        choices=PAGINA_SITE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Origem do Contato:"
    )

    mensagem = forms.MultipleChoiceField(
        choices=MENSAGEM_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Disponibilidade de Turno:"
    )

    data_envio = forms.DateField(
        label='Data',
        initial=timezone.now().date,  # Inicializa com a data atual
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    class Meta:
        model = Interesse
        fields = [
            'razao_social', 'email', 'pagina_site', 'data_envio', 'telefone_comercial',
            'celular', 'nome_representante', 'cnpj', 'cep', 'cidade', 'mensagem', 'curso'
        ]
        widgets = {
            'razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone_comercial': forms.TextInput(attrs={'class': 'form-control'}),
            'celular': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_representante': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'curso': forms.Select(attrs={'class': 'form-control'}),
        }

    razao_social = forms.CharField(label='Nome')
    email = forms.EmailField(label='E-mail')
    telefone_comercial = forms.CharField(label='Telefone', required=False)
    celular = forms.CharField(label='Celular', required=False)
    nome_representante = forms.CharField(label='Nome do Representante')
    cnpj = forms.CharField(label='CPF', required=False)
    cep = forms.CharField(label='CEP', required=False)
    cidade = forms.CharField(label='Cidade')
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.all().order_by('nome_curso'),
        label='Curso',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class CursoForm(forms.ModelForm):
    csv_file = forms.FileField(
        required=False,
        label='Upload de CSV',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Curso
        fields = ['codigo_curso', 'nome_curso', 'csv_file']  # Inclui o campo csv_file
        widgets = {
            'codigo_curso': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_curso': forms.TextInput(attrs={'class': 'form-control'}),
        }


class EditarInteresseForm(forms.ModelForm):
    FORMA_CONTATO_CHOICES = [
        ('telefone', 'Telefone'),
        ('whatsapp', 'Whatsapp'),
        ('email', 'Email'),
        ('outros', 'Outros'),
        ('inativo', 'Inativo')
    ]

    forma_contato = forms.ChoiceField(
        choices=FORMA_CONTATO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Forma de Contato",
        required=False
    )

    motivo_inativacao = forms.ChoiceField(
        choices=[
            ('desistencia', 'Desistência'),
            ('matriculado', 'Já Matriculado'),
            ('concluiu', 'Já Fez o Curso'),
            ('nao_interesse', 'Não Tem Interesse'),
            ('outros', 'Outros'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Motivo da Inativação"
    )

    class Meta:
        model = RegistroEdicaoInteresse
        fields = ['realizada_contato', 'forma_contato', 'observacoes', 'arquivo_evidencia', 'motivo_inativacao']
        widgets = {
            'realizada_contato': forms.Select(choices=RegistroEdicaoInteresse.REALIZADO_CONTATO_CHOICES,
                                              attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control'}),
            'arquivo_evidencia': forms.FileInput(attrs={'class': 'form-control'})
        }


# Formulário padrão para RegistroEdicaoInteresse
class RegistroEdicaoInteresseForm(forms.ModelForm):
    class Meta:
        model = RegistroEdicaoInteresse
        fields = ['realizada_contato', 'forma_contato', 'observacoes', 'arquivo_evidencia']


# Formset para gerenciar múltiplos registros de atendimento
RegistroEdicaoInteresseFormSet = modelformset_factory(
    RegistroEdicaoInteresse,
    form=RegistroEdicaoInteresseForm,
    extra=1,  # Número de formulários extras vazios
    can_delete=True  # Permite a exclusão de registros existentes
)
