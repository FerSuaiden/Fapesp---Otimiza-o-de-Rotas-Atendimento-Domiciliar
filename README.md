# Analise de Atencao Domiciliar (Melhor em Casa)

O Programa Melhor em Casa e uma politica publica do Ministerio da Saude que organiza o cuidado domiciliar no SUS com equipes multiprofissionais, reduzindo deslocamentos desnecessarios e apoiando a continuidade do tratamento no territorio.

Este repositorio reune os scripts, bases processadas e visualizacoes da Iniciacao Cientifica (IC/FAPESP), com foco em oferta de equipes, capacidade potencial, cobertura municipal e conformidade normativa.

Os resultados consolidados sao publicados no site do projeto: https://otimhomecare.icmc.usp.br/. Essa publicacao aberta facilita a transparencia, amplia o acesso da sociedade aos indicadores e permite acompanhamento continuo da evolucao analitica do trabalho.

## Apresentacao em video

No GitHub, o player inline da apresentacao pode ser acessado pela URL abaixo:

https://github.com/user-attachments/assets/5812a9b7-c9b5-4732-9a7a-48a96754784b

Link direto para abrir em nova aba:

- [Assistir apresentacao (GitHub Attachments)](https://github.com/user-attachments/assets/5812a9b7-c9b5-4732-9a7a-48a96754784b)

Fallback local:

- [Assistir apresentacao (MP4)](./Grava%C3%A7%C3%A3o%20de%20ecr%C3%A3%207%20(online-video-cutter.com)(4).mp4)

## Projeto FAPESP

- Processo: 2025/21835-0
- Bolsa/projeto: https://bv.fapesp.br/pt/bolsas/232802/metodos-de-solucao-para-o-agendamento-e-roteamento-de-equipes-para-a-assistencia-domiciliar/
- Aluno: Fernando Alee Suaiden
- Orientadora: Maristela Oliveira dos Santos

## Fontes de dados (links oficiais)

- CNES/DATASUS (bases CNES): https://cnes.datasus.gov.br/pages/downloads/arquivosBaseDados.jsp
- IBGE (tabela oficial de codigos de municipios usada em `IBGE_DATA/municipios_ibge.csv`): https://www.ibge.gov.br/explica/codigos-dos-municipios.php
- IBGE (download direto da DTB 2024; arquivo usado: `RELATORIO_DTB_BRASIL_2024_MUNICIPIOS.xls`): https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/divisao_territorial/2024/DTB_2024.zip
- IBGE (Censo 2022, usado para denominadores demograficos): https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-demografico-2022.html
- CBO (Classificacao Brasileira de Ocupacoes): http://www.mtecbo.gov.br/cbosite/pages/downloads.jsf

## Objetivo cientifico

- Medir a distribuicao espacial e estadual das equipes AD.
- Estimar capacidade potencial de atendimento com base em CHS SUS.
- Avaliar composicao profissional das equipes.
- Quantificar cobertura municipal e densidade por populacao.
- Verificar conformidade com a Portaria GM/MS no 3.005/2024.
- Explorar sinais de percepcao publica e gargalos operacionais via analise textual.

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
RELATORIO_FAPESP_AJUSTADO.tex      # Relatorio semestral consolidado
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

## Saidas esperadas

- PNG/HTML em `Outputs&Codigo/OFERTA`, `Outputs&Codigo/COMPOSICAO` e `Outputs&Codigo/CONFORMIDADE/visualizacoes`.
- CSV em `Outputs&Codigo/CONFORMIDADE/dados_csv`.
- CSV/PNG da analise social em `Outputs&Codigo/OPINIAO_PUBLICA/<perfil>/`.
- Bases atualmente utilizadas: CNES/DATASUS (competencia 2025-08), CBO e IBGE (apoio municipal/denominadores).

## Materiais de apoio

- Relatorio semestral: `RELATORIO_FAPESP_AJUSTADO.tex`
