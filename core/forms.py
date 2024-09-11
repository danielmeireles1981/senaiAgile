from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Interesse, Curso, RegistroEdicaoInteresse
from django.utils import timezone

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
    class Meta:
        model = Curso
        fields = ['codigo_curso', 'nome_curso']
        widgets = {
            'codigo_curso': forms.TextInput(attrs={'class': 'form-control'}),
            'nome_curso': forms.TextInput(attrs={'class': 'form-control'}),
        }

class EditarInteresseForm(forms.ModelForm):
    FORMA_CONTATO_CHOICES = [
        ('telefone', 'Telefone'),
        ('whatsapp', 'Whatsapp'),
        ('email', 'Email'),
    ]

    forma_contato = forms.ChoiceField(
        choices=FORMA_CONTATO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Forma de Contato"
    )

    class Meta:
        model = RegistroEdicaoInteresse
        fields = ['realizada_contato', 'forma_contato', 'observacoes', 'arquivo_evidencia']  # Incluindo o campo arquivo_evidencia
        widgets = {
            'realizada_contato': forms.Select(choices=RegistroEdicaoInteresse.REALIZADO_CONTATO_CHOICES, attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control'}),
            'arquivo_evidencia': forms.FileInput(attrs={'class': 'form-control'})  # Novo widget para upload de arquivo
        }

    def __init__(self, *args, **kwargs):
        super(EditarInteresseForm, self).__init__(*args, **kwargs)
        self.fields['realizada_contato'].label = 'Realizado Contato?'