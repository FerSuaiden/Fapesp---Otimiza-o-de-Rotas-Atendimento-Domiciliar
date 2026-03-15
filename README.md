# Otimização de Rotas de Atenção Domiciliar (HHC-RSP)

Repositório da IC/FAPESP para análise de dados do programa **Melhor em Casa** e geração de insumos para modelagem de roteamento e agendamento em atenção domiciliar.

## Escopo

- Identificar equipes EMAD/EMAP no CNES.
- Estimar capacidade das equipes ($Q_k$) pela CHS SUS.
- Caracterizar composição profissional/habilidades ($S_k$).
- Preparar dados para geração de instâncias de otimização.
- Analisar cobertura municipal e conformidade legal (Portaria GM/MS nº 3.005/2024).

## Estrutura do projeto

```text
IC/
├── CNES_DATA/                      # Bases CNES/DATASUS (não versionadas)
├── CBO_DATA/                       # Dicionários CBO (não versionados)
├── IBGE_DATA/                      # Bases IBGE/Censo (não versionadas)
├── Outputs&Codigo/
│   ├── PARTE1/                     # Mapeamento e distribuição de equipes
│   ├── PARTE2/                     # Capacidade e habilidades
│   ├── PARTE3/                     # Geração de instâncias
│   └── PARTE4/                     # Cobertura e conformidade legal
├── map_server/
└── README.md                       # ÚNICO README do repositório
```

## Pré-requisitos

- Python 3.10+
- Ambiente virtual ativo
- Bibliotecas: `pandas`, `numpy`, `matplotlib`, `folium`, `plotly`

Exemplo:

```bash
python -m venv venv
source venv/bin/activate
pip install pandas numpy matplotlib folium plotly
```

## Execução rápida

Na raiz do projeto:

```bash
source venv/bin/activate
```

### PARTE 1

```bash
python "Outputs&Codigo/PARTE1/1-visuazacaoMapa.py"
python "Outputs&Codigo/PARTE1/2-equipes_por_estado.py"
python "Outputs&Codigo/PARTE1/3-pizza.py"
```

### PARTE 2

```bash
python "Outputs&Codigo/PARTE2/4-capacidade.py"
python "Outputs&Codigo/PARTE2/5-heatMap.py"
python "Outputs&Codigo/PARTE2/6-sunburst.py"
```

### PARTE 3

```bash
python "Outputs&Codigo/PARTE3/15-gerador_instancias.py"
```

### PARTE 4 (v2)

```bash
python "Outputs&Codigo/PARTE4/scripts/analise_nacional_brasil_v2.py"
python "Outputs&Codigo/PARTE4/scripts/gerar_visualizacoes_estados_v2.py"
```

## Dados e filtros principais

- Tipos de equipe AD usados: **22 (EMAD I), 46 (EMAD II), 23 (EMAP), 77 (EMAP-R)**.
- Competência CNES utilizada: **08/2025**.
- Fontes: CNES/DATASUS, CBO, IBGE.

## Saídas esperadas (resumo)

- Visualizações em PNG/HTML nas partes 1, 2 e 4.
- CSVs analíticos em `Outputs&Codigo/PARTE4/dados_csv`.
- Artefatos por estado em `Outputs&Codigo/PARTE4/visualizacoes/estados`.

## Observações

- Este repositório mantém **apenas este README na raiz**.
- Pastas de dados brutos podem estar fora do versionamento por tamanho.
