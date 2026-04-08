# PARTE5 - Opiniao Publica e Gargalos Operacionais (Melhor em Casa)

Pipeline em 2 etapas, sem LLM:

1. Coleta SerpAPI (mencoes brutas).
2. Analise lexical deterministica (limpeza + TF-IDF + heuristicas + visualizacoes).

## Requisitos

Instale dependencias no ambiente Python:

```bash
pip install requests pandas matplotlib networkx scikit-learn wordcloud
```

## Variaveis de ambiente

Os scripts carregam automaticamente o .env na raiz do projeto.

```bash
export SERPAPI_API_KEY="SUA_CHAVE_SERPAPI"
```

## Etapa 1 - Coleta SerpAPI

```bash
python "Outputs&Codigo/PARTE5/scripts/coleta_serpapi_opiniao.py" \
  --max-resultados-por-consulta 20 \
  --sleep-segundos 1.5
```

Saida:
- Outputs&Codigo/PARTE5/resultados/mencoes_serpapi_brutas.csv

## Etapa 2 - Analise lexical (estilo notebook)

```bash
python "Outputs&Codigo/PARTE5/scripts/classificar_gemini_percepcao.py"
```

Saidas:
- Outputs&Codigo/PARTE5/percepcao_operacional.csv
- Outputs&Codigo/PARTE5/resultados/resumo_analise_tfidf.txt
- Outputs&Codigo/PARTE5/visualizacoes/top_termos_tfidf.png
- Outputs&Codigo/PARTE5/visualizacoes/nuvem_palavras_tfidf.png
- Outputs&Codigo/PARTE5/visualizacoes/rede_gargalos.png

## Metodo (passo a passo)

1. Limpa e normaliza titulo + resumo de cada mencao.
2. Calcula TF-IDF global (unigramas e bigramas).
3. Extrai termos mais relevantes por mencao.
4. Infere sentimento (positivo, negativo, neutro, misto) por regras lexicais.
5. Infere gargalo logistico (pessoal, frota, escala, tempo de deslocamento, nenhum).
6. Gera resumo textual e visualizacoes para leitura rapida.

## Observacoes

- Esta etapa nao usa LLM externa.
- O campo erro_classificacao e mantido no CSV para compatibilidade, mas fica vazio no fluxo atual.
- Como a inferencia e heuristica, os resultados devem ser lidos como sinal exploratorio.
