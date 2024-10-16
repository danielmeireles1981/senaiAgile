from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
from reportlab.lib.units import inch
from django.utils import timezone
import unittest
import io
import logging
import re

logger = logging.getLogger(__name__)


def executar_testes():
    try:
        # Capturar os resultados dos testes
        resultado = io.StringIO()
        runner = unittest.TextTestRunner(stream=resultado, verbosity=2)

        # Carregar e executar os testes
        loader = unittest.TestLoader()
        tests = loader.discover('core.tests')
        result = runner.run(tests)

        # Capturar o status baseado nos resultados
        total_tests = result.testsRun
        failed_tests = len(result.failures) + len(result.errors)

        # Obter o log completo dos resultados dos testes
        resultado.seek(0)
        resultado_texto = resultado.read()

        # Processar os resultados do log para extrair nome, status e mensagens dos testes
        detalhes = []
        regex_teste = re.compile(r'(\w+\.\w+\.\w+) \((\w+\.\w+\.\w+)\) \.\.\. (ok|ERROR|FAIL)', re.MULTILINE)
        matches = regex_teste.findall(resultado_texto)

        for match in matches:
            nome_teste = match[0]
            status_teste = match[2].lower()
            mensagem = ""

            # Se o status for erro ou falha, procure a mensagem no log
            if status_teste in ['error', 'fail']:
                regex_mensagem = re.compile(r'Traceback \(most recent call last\):.*?(?=(\w+\.\w+|\Z))', re.DOTALL)
                mensagem_match = regex_mensagem.search(resultado_texto)
                if mensagem_match:
                    mensagem = mensagem_match.group(0)

            detalhes.append({
                'nome': nome_teste,
                'status': status_teste,
                'mensagem': mensagem if mensagem else "Nenhuma mensagem de erro disponível."
            })

        # Verificar se houve falhas ou erros
        status = 'sucesso' if failed_tests == 0 else 'falha'

        return {
            'resultado_texto': resultado_texto,
            'total_tests': total_tests,
            'failed_tests': failed_tests,
            'status': status,
            'detalhes': detalhes,  # Lista de detalhes dos testes
            'data_geracao': timezone.now().strftime('%d/%m/%Y %H:%M')
        }

    except Exception as e:
        logger.error(f"Erro ao executar os testes: {str(e)}")
        return {
            'resultado_texto': f"Erro ao executar os testes: {str(e)}",
            'total_tests': 0,
            'failed_tests': 0,
            'status': 'falha',
            'detalhes': [],  # Lista vazia em caso de erro
            'data_geracao': timezone.now().strftime('%d/%m/%Y %H:%M')
        }


def gerar_pdf_resultados_testes(resultados_teste):
    # Definir o arquivo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="relatorio_testes.pdf"'

    # Configurar o PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Definir estilos
    styles = getSampleStyleSheet()
    titulo_style = styles['Heading1']
    normal_style = styles['Normal']

    # Cabeçalho
    elements.append(Paragraph("Relatório de Testes Automatizados", titulo_style))
    elements.append(Paragraph("Resultado dos testes realizados:", normal_style))

    # Organizar resultados dos testes
    dados_tabela = [['Nome do Teste', 'Status', 'Mensagem']]

    # Iterar sobre a lista de resultados do teste
    for resultado in resultados_teste:
        nome_teste = str(resultado.get('nome', 'Teste Desconhecido'))  # Garantir que o nome seja uma string
        status = str(resultado.get('status', 'falha'))  # Garantir que o status seja uma string
        mensagem = str(
            resultado.get('mensagem', 'Nenhuma mensagem fornecida.'))  # Garantir que a mensagem seja uma string

        # Definir cor do status
        if 'sucesso' in status:
            color = colors.green
        else:
            color = colors.red

        # Adicionar linha à tabela
        dados_tabela.append([
            Paragraph(nome_teste, normal_style),
            Paragraph(f"<font color={color}>{status}</font>", normal_style),
            Paragraph(mensagem, normal_style)
        ])

    # Definir estilo da tabela
    tabela = Table(dados_tabela, colWidths=[2.5 * inch, 1 * inch, 3.5 * inch])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(tabela)

    # Rodapé
    elements.append(Paragraph(f"Data de Geração: {timezone.now().strftime('%d/%m/%Y %H:%M')}", normal_style))

    # Construir o PDF
    doc.build(elements)
    return response
