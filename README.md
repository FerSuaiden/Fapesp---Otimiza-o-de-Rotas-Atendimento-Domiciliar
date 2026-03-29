# Analise de Atencao Domiciliar (Melhor em Casa)

Repositorio de Iniciacao Cientifica (IC/FAPESP) para analise de dados do programa Melhor em Casa, com foco em oferta de equipes, capacidade potencial, cobertura municipal e conformidade normativa.

## Objetivo cientifico

- Medir a distribuicao espacial e estadual das equipes AD.
- Estimar capacidade potencial de atendimento com base em CHS SUS.
- Avaliar composicao profissional das equipes.
- Quantificar cobertura municipal e densidade por populacao.
- Verificar conformidade com a Portaria GM/MS no 3.005/2024.

## Estrutura principal

```text
CNES_DATA/                         # Bases CNES (competencia 2025-08)
CBO_DATA/                          # Dicionarios CBO
IBGE_DATA/                         # Bases de municipios e populacao
Outputs&Codigo/
	PARTE1/                          # Oferta, mapas, distribuicoes e serie temporal
	PARTE2/                          # Capacidade potencial e composicao profissional
	PARTE3/                          # Geracao de instancias para modelagem
	PARTE4/                          # Cobertura e conformidade legal
	PARTE5/                          # Coleta e classificacao de percepcao publica
map_server/                        # Site estatico e publicacao via Docker
README.md
requirements.txt
```

Nota: o conteudo da antiga PARTE6 foi incorporado em `Outputs&Codigo/PARTE1/serie_temporal_cobertura/`.

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

### PARTE1 - oferta e visualizacao espacial

- `1-visuazacaoMapa.py`: gera mapas interativos por UF.
- `2-equipes_por_estado.py`: gera distribuicao de equipes por estado/tipo.
- `3-pizza.py`: gera composicao nacional por tipo.
- `serie_temporal_cobertura/scripts/gerar_serie_temporal_cobertura_por_regiao.py`: gera serie temporal da cobertura regional.

```bash
python "Outputs&Codigo/PARTE1/1-visuazacaoMapa.py"
python "Outputs&Codigo/PARTE1/2-equipes_por_estado.py"
python "Outputs&Codigo/PARTE1/3-pizza.py"
python "Outputs&Codigo/PARTE1/serie_temporal_cobertura/scripts/gerar_serie_temporal_cobertura_por_regiao.py"
```

### PARTE2 - capacidade potencial e habilidades

- `4-capacidade.py`: estatisticas de capacidade potencial por equipe/UF.
- `5-heatMap.py`: mapa de calor nacional da capacidade potencial.
- `6-sunburst.py`: visualizacao de composicao profissional por tipo de equipe.

```bash
python "Outputs&Codigo/PARTE2/4-capacidade.py"
python "Outputs&Codigo/PARTE2/5-heatMap.py"
python "Outputs&Codigo/PARTE2/6-sunburst.py"
```

### PARTE3 - instancias de modelagem

- `15-gerador_instancias.py`: prepara instancias para otimizacao/roteamento.

```bash
python "Outputs&Codigo/PARTE3/15-gerador_instancias.py"
```

### PARTE4 - cobertura e conformidade legal

- `analise_nacional_brasil_v2.py`: gera indicadores nacionais e visualizacoes.
- `gerar_visualizacoes_estados_v2.py`: gera graficos por estado e arquivos auxiliares.

```bash
python "Outputs&Codigo/PARTE4/scripts/analise_nacional_brasil_v2.py"
python "Outputs&Codigo/PARTE4/scripts/gerar_visualizacoes_estados_v2.py"
```

### PARTE5 - percepcao publica

- `coleta_serpapi_opiniao.py`: coleta resultados da web.
- `classificar_gemini_percepcao.py`: classifica temas/sentimento e gera visualizacoes.

Exemplo:

```bash
export SERPAPI_API_KEY="SUA_CHAVE"
export GEMINI_API_KEY="SUA_CHAVE"
python "Outputs&Codigo/PARTE5/scripts/coleta_serpapi_opiniao.py"
python "Outputs&Codigo/PARTE5/scripts/classificar_gemini_percepcao.py"
```

## Publicacao local do site

```bash
cd map_server
docker compose up -d --build --force-recreate
```

Site em: `http://localhost:8080`

## Saidas esperadas

- PNG/HTML em `Outputs&Codigo/PARTE1`, `Outputs&Codigo/PARTE2` e `Outputs&Codigo/PARTE4/visualizacoes`.
- CSV em `Outputs&Codigo/PARTE4/dados_csv`.
- Artefatos de percepcao em `Outputs&Codigo/PARTE5`.

## Fontes de dados

- CNES/DATASUS (competencia 2025-08)
- CBO 2002
- IBGE (municipios e populacao)
