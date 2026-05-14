import requests
import polars as pl
import mysql.connector
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Carrega as variáveis ocultas do arquivo .env
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', 3306))
}# Configurações de acesso para o banco de dados

def get_conexao():
    return mysql.connector.connect(**DB_CONFIG)
#Retorna a conexão com o banco

def popular_dimensoes_se_vazio():
    """Garante que a tabela de dimensões tenha os dados iniciais."""
    conn = get_conexao()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM dim_series")
    qtd = cursor.fetchone()[0]
    
    if qtd == 0:
        print("Banco vazio detectado. Populando tabela de dimensões...")
        query = """
            INSERT INTO dim_series (codigo_bcb, nome, unidade_medida, periodicidade) VALUES 
            (432, 'Taxa de juros - Selic', 'Porcentagem anual', 'Diária'),
            (433, 'IPCA', 'Variacao mensal', 'Mensal'),
            (1, 'Taxa de câmbio - Livre - Dólar (compra)', 'R$', 'Diária');
        """
        cursor.execute(query)
        conn.commit()
    
    conn.close()

def series_ativas():
    conn = get_conexao()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_serie, codigo_bcb, nome FROM dim_series")
    series = cursor.fetchall()
    conn.close()
    return series

def mais_recente(id_serie):
    conn = get_conexao()
    cursor = conn.cursor()
    cursor.execute(f"SELECT MAX(data_referencia) FROM fato_valores WHERE id_serie = {id_serie}")
    resultado = cursor.fetchone()[0]
    conn.close()
    return resultado

def extrair_dados_banco(codigo_bcb, data_inicial):
    dt_str = data_inicial.strftime('%d/%m/%Y')
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_bcb}/dados?formato=json&dataInicial={dt_str}"
    
    resposta = requests.get(url)
    if resposta.status_code == 200 and resposta.json():
        return resposta.json()
    return []

def transformar_dados(dados_brutos):
    df = pl.DataFrame(dados_brutos)
    df = df.with_columns([
        pl.col('data').str.to_date('%d/%m/%Y'),
        pl.col('valor').cast(pl.Float64)
    ])
    return df

def carregar_dados(cursor, id_serie, df_transformado):
    query_insercao = """
        INSERT INTO fato_valores (id_serie, data_referencia, valor) 
        VALUES (%s, %s, %s)
    """
    valores_para_banco = [
        (id_serie, linha['data'], linha['valor']) 
        for linha in df_transformado.to_dicts()
    ]
    cursor.executemany(query_insercao, valores_para_banco)
    return len(valores_para_banco)

def processar_serie(cursor, serie):
    id_serie = serie['id_serie']
    codigo_bcb = serie['codigo_bcb']
    nome_serie = serie['nome']
    
    ultima_data = mais_recente(id_serie)
    
    # Define a data de busca
    if ultima_data:
        data_busca = ultima_data + timedelta(days=1)
    else:
        data_busca = datetime(2020, 1, 1).date()
        
    hoje = datetime.now().date()
    
    if data_busca > hoje:
        print(f" {nome_serie}: está atualizada!")
        return
        
    print(f" Extraindo {nome_serie} a partir de {data_busca}...")
    dados_brutos = extrair_dados_banco(codigo_bcb, data_busca)
    
    if not dados_brutos:
        print(f" Sem dados novos na API para {nome_serie} nesta data.")
        return
        
    
    df = transformar_dados(dados_brutos)
    qtd_inserida = carregar_dados(cursor, id_serie, df)
    
    print(f" Sucesso! {qtd_inserida} novos registros inseridos.")


def main():
    print("Iniciando Extração de Dados do BCB...")

    popular_dimensoes_se_vazio()
    
    

    series = series_ativas()

    print(f" Encontrei {len(series)} séries para processar.")

    conn = get_conexao()
    cursor = conn.cursor()

    for serie in series:
        processar_serie(cursor, serie)
        conn.commit()

    conn.close()
    print("Finalizado!")

if __name__ == '__main__':
    main()