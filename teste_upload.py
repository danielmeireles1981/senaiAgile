import csv
import mysql.connector

def conectar_banco():
    try:
        conexao = mysql.connector.connect(
            host="localhost",  # Alterar conforme necessário
            user="root",  # Alterar conforme necessário
            password="123456",  # Alterar conforme necessário
            database="senaiagile"  # Alterar conforme necessário
        )
        return conexao
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        return None

def upload_csv(caminho_csv, conexao):
    try:
        cursor = conexao.cursor()

        with open(caminho_csv, mode='r', encoding='utf-8-sig') as arquivo_csv:  # 'utf-8-sig' remove o BOM automaticamente
            leitor_csv = csv.DictReader(arquivo_csv, delimiter=';')

            # Verificar os cabeçalhos do CSV
            cabecalhos = leitor_csv.fieldnames
            print(f"Cabecalhos encontrados no CSV: {cabecalhos}")
            if 'codigo_curso' not in cabecalhos or 'nome_curso' not in cabecalhos:
                raise ValueError("CSV inválido: faltando 'codigo_curso' ou 'nome_curso'.")

            for linha in leitor_csv:
                codigo_curso = linha['codigo_curso'].strip()
                nome_curso = linha['nome_curso'].strip()

                # Verificando se o curso já existe
                cursor.execute("SELECT COUNT(*) FROM core_curso WHERE codigo_curso = %s", (codigo_curso,))
                resultado = cursor.fetchone()

                if resultado[0] == 0:
                    # Inserindo o curso no banco de dados
                    cursor.execute(
                        "INSERT INTO core_curso (codigo_curso, nome_curso) VALUES (%s, %s)",
                        (codigo_curso, nome_curso)
                    )
                    print(f"Curso {nome_curso} inserido com sucesso.")
                else:
                    print(f"Curso {nome_curso} já existe, ignorado.")

        conexao.commit()

    except Exception as e:
        print(f"Erro ao processar o arquivo CSV: {e}")
    finally:
        cursor.close()

if __name__ == "__main__":
    caminho_csv = 'texto.csv'  # Caminho para o seu arquivo CSV
    conexao = conectar_banco()

    if conexao:
        upload_csv(caminho_csv, conexao)
        conexao.close()
