# Analise de Atencao Domiciliar (Melhor em Casa)

Repositorio de Iniciacao Cientifica (IC/FAPESP) para analise de dados do programa Melhor em Casa, com foco em oferta de equipes, capacidade potencial, cobertura municipal e conformidade normativa.

## Projeto FAPESP

- Processo: 2025/21835-0
- Bolsa/projeto: https://bv.fapesp.br/pt/bolsas/232802/metodos-de-solucao-para-o-agendamento-e-roteamento-de-equipes-para-a-assistencia-domiciliar/
- Aluno: Fernando Alee Suaiden
- Orientadora: Maristela Oliveira dos Santos

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
Outputs&Codigo/
	OFERTA/                          # Oferta, mapas, distribuicoes e serie temporal
	COMPOSICAO/                      # Capacidade potencial e composicao profissional
	CONFORMIDADE/                    # Cobertura e conformidade legal
map_server/                        # Site estatico e publicacao via Docker
README.md
requirements.txt
```

Nota: o conteudo da antiga PARTE6 foi incorporado em `Outputs&Codigo/OFERTA/serie_temporal_cobertura/`.

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

## Publicacao local do site

```bash
cd map_server
docker compose up -d --build --force-recreate
```

Site em: `http://localhost:8080`

## Saidas esperadas

- PNG/HTML em `Outputs&Codigo/OFERTA`, `Outputs&Codigo/COMPOSICAO` e `Outputs&Codigo/CONFORMIDADE/visualizacoes`.
- CSV em `Outputs&Codigo/CONFORMIDADE/dados_csv`.
- Bases atualmente utilizadas: CNES/DATASUS (competencia 2025-08) e CBO.
