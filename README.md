# Analise de Atencao Domiciliar (Melhor em Casa)

O Programa Melhor em Casa organiza a Atencao Domiciliar no SUS e apoia o acompanhamento de pacientes com diferentes niveis de complexidade clinica no domicilio. Sua atuacao envolve equipes multiprofissionais e combina acoes de tratamento, reabilitacao e cuidados paliativos para ampliar a continuidade do cuidado no territorio.

Este repositorio concentra a infraestrutura analitica do estudo, com rotinas de extracao, tratamento e integracao de dados publicos para gerar indicadores territoriais e operacionais do programa. O fluxo principal integra bases do CNES/DATASUS, da CBO e da DTB/IBGE para analises em escala nacional, estadual e municipal.

Os resultados consolidados sao publicados em https://otimhomecare.icmc.usp.br/, com tabelas, graficos e visualizacoes que apoiam transparencia, planejamento e acompanhamento continuo dos indicadores.

## Apresentacao em video

https://github.com/user-attachments/assets/5812a9b7-c9b5-4732-9a7a-48a96754784b

## Projeto FAPESP

- Processo: 2025/21835-0
- Bolsa/projeto: https://bv.fapesp.br/pt/bolsas/232802/metodos-de-solucao-para-o-agendamento-e-roteamento-de-equipes-para-a-assistencia-domiciliar/
- Aluno: Fernando Alee Suaiden
- Orientadora: Maristela Oliveira dos Santos

## Fontes de dados (links oficiais)

- CNES/DATASUS (bases CNES): https://cnes.datasus.gov.br/pages/downloads/arquivosBaseDados.jsp
- IBGE (DTB 2024, tabela de codigos de municipios usada em `IBGE_DATA/municipios_ibge.csv`): https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/divisao_territorial/2024/DTB_2024.zip
- CBO (Classificacao Brasileira de Ocupacoes): http://www.mtecbo.gov.br/cbosite/pages/downloads.jsf

## Estrutura principal

```text
CNES_DATA/                         # Bases CNES (competencia 2025-08)
CBO_DATA/                          # Dicionarios CBO
IBGE_DATA/                         # Base municipal de apoio (ex.: municipios_ibge.csv)
Outputs&Codigo/
	OFERTA/                          # Oferta, mapas, distribuicoes e serie temporal
	COMPOSICAO/                      # Capacidade potencial e composicao profissional
	CONFORMIDADE/                    # Cobertura e conformidade legal
	OPINIAO_PUBLICA/                 # Coleta SerpAPI + analise lexical de mencoes
map_server/                        # Site estatico e publicacao via Docker
README.md
requirements.txt
```

## Requisitos

- Python 3.10+
- Ambiente virtual (`venv`)
- Dependencias em `requirements.txt`

Instalacao recomendada:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Como executar os scripts

Sempre a partir da raiz do repositorio:

```bash
source venv/bin/activate
```

### OFERTA - visualizacao espacial e serie temporal

- `1-visuazacaoMapa.py`: gera mapas interativos por UF.
- `2-equipes_por_estado.py`: gera distribuicao de equipes por estado/tipo.
- `3-pizza.py`: gera composicao nacional por tipo.
- `serie_temporal_cobertura/scripts/gerar_serie_temporal_cobertura_por_regiao.py`: gera serie temporal da cobertura regional.

```bash
python "Outputs&Codigo/OFERTA/1-visuazacaoMapa.py"
python "Outputs&Codigo/OFERTA/2-equipes_por_estado.py"
python "Outputs&Codigo/OFERTA/3-pizza.py"
python "Outputs&Codigo/OFERTA/serie_temporal_cobertura/scripts/gerar_serie_temporal_cobertura_por_regiao.py"
```

### COMPOSICAO - capacidade potencial e habilidades

- `4-capacidade.py`: estatisticas de capacidade potencial por equipe/UF.
- `5-heatMap.py`: mapa de calor nacional da capacidade potencial.
- `6-sunburst.py`: visualizacao de composicao profissional por tipo de equipe.

```bash
python "Outputs&Codigo/COMPOSICAO/4-capacidade.py"
python "Outputs&Codigo/COMPOSICAO/5-heatMap.py"
python "Outputs&Codigo/COMPOSICAO/6-sunburst.py"
```

### CONFORMIDADE - cobertura e conformidade legal

- `analise_nacional_brasil_v2.py`: gera indicadores nacionais e visualizacoes.
- `gerar_visualizacoes_estados_v2.py`: gera graficos por estado e arquivos auxiliares.

```bash
python "Outputs&Codigo/CONFORMIDADE/scripts/analise_nacional_brasil_v2.py"
python "Outputs&Codigo/CONFORMIDADE/scripts/gerar_visualizacoes_estados_v2.py"
```

### OPINIAO_PUBLICA - coleta web e inferencia lexical

- `scripts/coleta_serpapi_opiniao.py`: coleta mencoes publicas por perfil.
- `scripts/classificar_gemini_percepcao.py`: limpeza, TF-IDF, inferencia de sentimento/gargalo e visualizacoes.

```bash
# Coleta (perfil balanced)
python "Outputs&Codigo/OPINIAO_PUBLICA/scripts/coleta_serpapi_opiniao.py" \
	--perfil balanced

# Coleta (perfil problem-oriented)
python "Outputs&Codigo/OPINIAO_PUBLICA/scripts/coleta_serpapi_opiniao.py" \
	--perfil problem-oriented

# Analise lexical (executar para cada perfil)
python "Outputs&Codigo/OPINIAO_PUBLICA/scripts/classificar_gemini_percepcao.py" \
	--perfil balanced

python "Outputs&Codigo/OPINIAO_PUBLICA/scripts/classificar_gemini_percepcao.py" \
	--perfil problem-oriented
```

Documentacao detalhada (passo a passo e formulas):
- `Outputs&Codigo/OPINIAO_PUBLICA/README.md`

## Publicacao local do site

```bash
cd map_server
docker compose up -d --build --force-recreate
```

Site em: `http://localhost:8080`
