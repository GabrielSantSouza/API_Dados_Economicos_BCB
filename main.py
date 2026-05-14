from fastapi import FastAPI, HTTPException, Query
import mysql.connector
from typing import List, Optional
from datetime import date
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
}

app = FastAPI(
    title="API de Dados Macroeconômicos - BCB",
    description="API para consultar histórico da Selic, IPCA e Dólar extraídos do Banco Central.",
    version="1.0.0"
)


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)



@app.get("/", tags=["Home"])
def home():
    """Boas-vindas e redirecionamento."""
    return {
        "mensagem": "API BCB Pipeline ativa!",
        "documentacao": "/docs",
        "status": "online"
    }

@app.get("/series", tags=["Metadados"])
def listar_series():
    """Retorna a lista de todas as séries disponíveis no catálogo (dim_series)."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_serie, codigo_bcb, nome, unidade_medida FROM dim_series")
    series = cursor.fetchall()
    conn.close()
    return series

@app.get("/valores/{id_serie}", tags=["Dados Históricos"])
def obter_valores(
    id_serie: int, 
    data_inicio: Optional[date] = None, 
    data_fim: Optional[date] = None
):
    """
    Retorna os valores históricos de uma série específica.
    Permite filtrar por intervalo de datas (AAAA-MM-DD).
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT data_referencia as data, valor FROM fato_valores WHERE id_serie = %s"
    params = [id_serie]
    

    if data_inicio:
        query += " AND data_referencia >= %s"
        params.append(data_inicio)
    if data_fim:
        query += " AND data_referencia <= %s"
        params.append(data_fim)
    
    query += " ORDER BY data_referencia DESC"
    
    cursor.execute(query, tuple(params))
    dados = cursor.fetchall()
    conn.close()
    
    if not dados:
        raise HTTPException(status_code=404, detail="Dados não encontrados para esta série ou intervalo.")
    
    return dados