# PARTE5 - Opiniao Publica e Gargalos Operacionais (Melhor em Casa)

Pipeline em 2 etapas para reduzir risco de bloqueio por limite de API:

1. Coleta SerpAPI (mencoes brutas).
2. Classificacao Gemini + limpeza + rede semantica.

## Requisitos

Instale dependencias no seu ambiente Python:

```bash
pip install requests pandas matplotlib networkx
```

## Variaveis de ambiente

Os scripts carregam automaticamente o `.env` na raiz do projeto.

```bash
export SERPAPI_API_KEY="SUA_CHAVE_SERPAPI"
export GEMINI_API_KEY="SUA_CHAVE_GEMINI"
export GEMINI_MODEL="gemini-2.0-flash"
```

## Etapa 1 - Coleta SerpAPI

```bash
python "Outputs&Codigo/PARTE5/scripts/coleta_serpapi_opiniao.py" \
  --max-resultados-por-consulta 20 \
  --sleep-segundos 1.5
```

Saida:
- `Outputs&Codigo/PARTE5/resultados/mencoes_serpapi_brutas.csv`

## Etapa 2 - Classificacao + limpeza + rede

```bash
python "Outputs&Codigo/PARTE5/scripts/classificar_gemini_percepcao.py"
```

Saidas:
- `Outputs&Codigo/PARTE5/percepcao_operacional.csv`
- `Outputs&Codigo/PARTE5/visualizacoes/rede_coocorrencia_tematica_percepcao_operacional.png`

## Politica de falhas do Gemini

- Em `HTTP 429`, o script espera e tenta novamente a mesma linha.
- Se `429` persistir, o script registra erro em `erro_classificacao` e segue sem travar.
- Se houver erro de autenticacao/permissao do Gemini, o script registra erro e continua o processamento.
- O grafo e removido automaticamente quando nao ha classificacoes validas (evita artefato antigo enganoso).

Se receber `403 PERMISSION_DENIED` (ex.: chave marcada como vazada), gere uma nova chave e atualize o `.env`.
