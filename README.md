# Home Care Analysis (Melhor em Casa)

The Melhor em Casa Program structures Home Care within SUS and supports follow-up for patients with different levels of clinical complexity at home. Its operation relies on multidisciplinary teams and combines treatment, rehabilitation, and palliative care actions to improve continuity of care across territories.

This repository contains the analytical infrastructure of the study, with extraction, processing, and integration pipelines for public data to produce territorial and operational indicators for the program. The main workflow integrates CNES/DATASUS, CBO, and IBGE/DTB datasets for national, state, and municipal analyses.

Consolidated results are published at https://otimhomecare.icmc.usp.br/, with tables, charts, and interactive visualizations that support transparency, planning, and continuous indicator monitoring.

## Video Presentation

https://github.com/user-attachments/assets/5812a9b7-c9b5-4732-9a7a-48a96754784b

## FAPESP Project

- Process number: 2025/21835-0
- Scholarship/project page: https://bv.fapesp.br/pt/bolsas/232802/metodos-de-solucao-para-o-agendamento-e-roteamento-de-equipes-para-a-assistencia-domiciliar/
- Student: Fernando Alee Suaiden
- Advisor: Maristela Oliveira dos Santos

## Data Sources (Official Links)

- CNES/DATASUS (CNES datasets): https://cnes.datasus.gov.br/pages/downloads/arquivosBaseDados.jsp
- IBGE (DTB 2024): https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/divisao_territorial/2024/DTB_2024.zip
	- IBGE reference page for municipality codes: https://www.ibge.gov.br/explica/codigos-dos-municipios.php
  - Exact source file used to build `IBGE_DATA/municipios_ibge.csv`: `RELATORIO_DTB_BRASIL_2024_MUNICIPIOS.ods` (or `.xls`) inside the ZIP.
  - Field mapping used in this project: `CO_MUNICIPIO <- Codigo Municipio Completo`, `NO_MUNICIPIO <- Nome_Municipio`, `UF <- UF code converted to state acronym`.
- CBO (Brazilian Classification of Occupations): http://www.mtecbo.gov.br/cbosite/pages/downloads.jsf

## Main Structure

```text
CNES_DATA/                         # CNES datasets (2025-08 reference period)
CBO_DATA/                          # CBO dictionaries
IBGE_DATA/                         # Municipal support data (e.g., municipios_ibge.csv)
Outputs&Codigo/
	OFERTA/                          # Supply, maps, distributions, and time series
	COMPOSICAO/                      # Potential capacity and workforce composition
	CONFORMIDADE/                    # Coverage and legal compliance
	OPINIAO_PUBLICA/                 # SerpAPI collection + lexical mention analysis
map_server/                        # Static website and Docker publishing
README.md
requirements.txt
```

## Requirements

- Python 3.10+
- Virtual environment (`venv`)
- Dependencies listed in `requirements.txt`

Recommended setup:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Running the Scripts

Always run commands from the repository root:

```bash
source venv/bin/activate
```

### OFERTA - spatial visualization and time series

- `1-visuazacaoMapa.py`: builds interactive maps by state.
- `2-equipes_por_estado.py`: builds team distribution by state/type.
- `3-pizza.py`: builds national composition by team type.
- `serie_temporal_cobertura/scripts/gerar_serie_temporal_cobertura_por_regiao.py`: builds regional coverage time series.

```bash
python "Outputs&Codigo/OFERTA/1-visuazacaoMapa.py"
python "Outputs&Codigo/OFERTA/2-equipes_por_estado.py"
python "Outputs&Codigo/OFERTA/3-pizza.py"
python "Outputs&Codigo/OFERTA/serie_temporal_cobertura/scripts/gerar_serie_temporal_cobertura_por_regiao.py"
```

### COMPOSICAO - potential capacity and skills

- `4-capacidade.py`: computes potential-capacity statistics by team/state.
- `5-heatMap.py`: builds the national potential-capacity heatmap.
- `6-sunburst.py`: builds workforce composition visualization by team type.

```bash
python "Outputs&Codigo/COMPOSICAO/4-capacidade.py"
python "Outputs&Codigo/COMPOSICAO/5-heatMap.py"
python "Outputs&Codigo/COMPOSICAO/6-sunburst.py"
```

### CONFORMIDADE - coverage and legal compliance

- `analise_nacional_brasil_v2.py`: produces national indicators and visual outputs.
- `gerar_visualizacoes_estados_v2.py`: produces state-level charts and auxiliary outputs.

```bash
python "Outputs&Codigo/CONFORMIDADE/scripts/analise_nacional_brasil_v2.py"
python "Outputs&Codigo/CONFORMIDADE/scripts/gerar_visualizacoes_estados_v2.py"
```

### OPINIAO_PUBLICA - web collection and lexical inference

- `scripts/coleta_serpapi_opiniao.py`: collects public mentions by profile.
- `scripts/classificar_gemini_percepcao.py`: performs cleaning, TF-IDF, sentiment/bottleneck inference, and visualizations.

```bash
# Collection (balanced profile)
python "Outputs&Codigo/OPINIAO_PUBLICA/scripts/coleta_serpapi_opiniao.py" \
	--perfil balanced

# Collection (problem-oriented profile)
python "Outputs&Codigo/OPINIAO_PUBLICA/scripts/coleta_serpapi_opiniao.py" \
	--perfil problem-oriented

# Lexical analysis (run once per profile)
python "Outputs&Codigo/OPINIAO_PUBLICA/scripts/classificar_gemini_percepcao.py" \
	--perfil balanced

python "Outputs&Codigo/OPINIAO_PUBLICA/scripts/classificar_gemini_percepcao.py" \
	--perfil problem-oriented
```

Detailed documentation (step-by-step and formulas):
- `Outputs&Codigo/OPINIAO_PUBLICA/README.md`

## Local Website Publishing

```bash
cd map_server
docker compose up -d --build --force-recreate
```

Website: `http://localhost:8080`
