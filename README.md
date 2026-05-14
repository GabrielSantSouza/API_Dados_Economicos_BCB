# 📊 API de Dados Macroeconômicos (BCB Pipeline)

Um pipeline de dados completo (ETL) e API RESTful construídos para extrair, transformar e servir indicadores econômicos (Selic, IPCA e Dólar) do Banco Central do Brasil.

## 🚀 Tecnologias Utilizadas
* **Linguagem:** Python 3
* **Transformação de Dados:** Polars (Alta performance)
* **Banco de Dados:** MySQL (Rodando em Docker)
* **API REST:** FastAPI & Uvicorn

## ⚙️ Como funciona a Arquitetura
1. **Extract:** Consulta a API pública do SGS/Banco Central.
2. **Transform:** Limpeza e conversão de tipagem utilizando a velocidade do Polars.
3. **Load:** Carga incremental no MySQL utilizando o modelo Dimensional (Fato e Dimensão).
4. **Serve:** FastAPI expõe os dados através de endpoints interativos com documentação automática (Swagger).

## 🛣️ Endpoints da API
* `GET /series`: Retorna o catálogo de indicadores disponíveis.
* `GET /valores/{id_serie}`: Retorna o histórico de taxas com filtros opcionais de `data_inicio` e `data_fim`.