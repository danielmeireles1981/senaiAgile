from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    LoginView, InteresseCreateView, CursoCreateView, HomeView,
    ListarDadosView, RelatoriosView, LogoutView, VisualizarInteresseView,
    EditarInteresseView, CSVUploadView, gerar_pdf, exibir_resultados_testes, PesquisarInteresseView, AlterarSenhaView,
)

urlpatterns = [
    path('relatorios/', RelatoriosView.as_view(), name='relatorios'),
    path('listar-dados/', ListarDadosView.as_view(), name='listar-dados'),
    path('visualizar-interesse/<int:pk>/', VisualizarInteresseView.as_view(), name='visualizar-interesse'),
    path('editar-interesse/<int:pk>/', EditarInteresseView.as_view(), name='editar-interesse'),
    path('home/', HomeView.as_view(), name='home'),
    path('', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('cadastrar-interesse/', InteresseCreateView.as_view(), name='cadastrar-interesse'),
    path('cadastrar-curso/', CursoCreateView.as_view(), name='cadastrar-curso'),
    path('importar-csv/', CSVUploadView.as_view(), name='csv-upload'),
    path('admin/', auth_views.LoginView.as_view(), name='admin'),
    path('relatorios/gerar-pdf/', gerar_pdf, name='gerar-relatorio-pdf'),
    path('testes/', exibir_resultados_testes, name='resultados-testes'),
    path('pesquisar-interesse/', PesquisarInteresseView.as_view(), name='pesquisar-interesse'),
    path('alterar-senha/', AlterarSenhaView.as_view(), name='alterar-senha'),

]
