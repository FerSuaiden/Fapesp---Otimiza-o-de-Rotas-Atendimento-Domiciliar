# OPINIAO_PUBLICA - Opiniao Publica e Gargalos Operacionais (Melhor em Casa)

O Programa Melhor em Casa e uma estrategia do Ministerio da Saude para oferecer atencao domiciliar no SUS por equipes multiprofissionais, priorizando continuidade do cuidado e desospitalizacao quando clinicamente indicado.

Este modulo consolida a etapa exploratoria de mencoes publicas sobre o programa.

## Identificacao do projeto

- Processo FAPESP: 2025/21835-0
- Aluno: Fernando Alee Suaiden
- Orientadora: Maristela Oliveira dos Santos

## Fontes de dados (onde obter)

- SerpAPI (Search API): https://serpapi.com/search-api
- Portal oficial do programa Melhor em Casa: https://www.gov.br/saude/pt-br/composicao/saes/melhor-em-casa
- CNES/DATASUS (contexto estrutural do projeto): https://cnes.datasus.gov.br/pages/downloads/arquivosBaseDados.jsp

Pipeline em 2 etapas, sem LLM:

1. Coleta SerpAPI (mencoes brutas).
2. Analise lexical deterministica (limpeza + TF-IDF + heuristicas + nuvem).

## Requisitos

Instale dependencias no ambiente Python:

```bash
pip install requests pandas matplotlib scikit-learn wordcloud
```

## Variaveis de ambiente

Os scripts carregam automaticamente o .env na raiz do projeto.

```bash
export SERPAPI_API_KEY="SUA_CHAVE_SERPAPI"
```

## Etapa 1 - Coleta SerpAPI

```bash
python "Outputs&Codigo/OPINIAO_PUBLICA/scripts/coleta_serpapi_opiniao.py" \
  --perfil balanced \
  --max-resultados-por-consulta 20 \
  --sleep-segundos 1.5
```

Saida:
- Outputs&Codigo/OPINIAO_PUBLICA/<perfil>/mencoes_serpapi_brutas.csv

Perfis disponiveis:
- problem-oriented
- balanced

## Etapa 2 - Analise lexical (estilo notebook)

```bash
python "Outputs&Codigo/OPINIAO_PUBLICA/scripts/classificar_gemini_percepcao.py" \
  --perfil balanced
```

Saidas:
- Outputs&Codigo/OPINIAO_PUBLICA/<perfil>/percepcao_operacional.csv
- Outputs&Codigo/OPINIAO_PUBLICA/<perfil>/nuvem_palavras_tfidf.png

## Metodo (passo a passo)

1. Limpa e normaliza titulo + resumo de cada mencao.
2. Aplica stopwords manuais (pronomes, siglas administrativas e termos de baixo valor semantico).
3. Calcula TF-IDF global (unigramas e bigramas).
4. Filtra termos pouco informativos antes de montar ranking e nuvem.
5. Infere sentimento (positivo, negativo, neutro, misto) por regras lexicais.
6. Infere gargalo logistico (pessoal, frota, escala, tempo de deslocamento, nenhum) usando o texto da mencao.
7. Gera visualizacao de nuvem para leitura rapida (sem rede).

## Observacoes

- Esta etapa nao usa LLM externa.
- O campo erro_classificacao e mantido no CSV para compatibilidade, mas fica vazio no fluxo atual.
- Como a inferencia e heuristica, os resultados devem ser lidos como sinal exploratorio.
- A regra de sentimento foi ajustada para nao penalizar apenas a ocorrencia isolada de "nao".
