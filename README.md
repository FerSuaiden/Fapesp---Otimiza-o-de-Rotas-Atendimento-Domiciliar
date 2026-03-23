# Otimização de Rotas de Atenção Domiciliar (HHC-RSP)

Repositório da IC/FAPESP para análise de dados do programa **Melhor em Casa** e geração de insumos para modelagem de roteamento e agendamento em atenção domiciliar.

## Escopo

- Identificar equipes EMAD/EMAP no CNES.
- Estimar capacidade das equipes ($Q_k$) pela CHS SUS.
- Caracterizar composição profissional/habilidades ($S_k$).
- Preparar dados para geração de instâncias de otimização.
- Analisar cobertura municipal e conformidade legal (Portaria GM/MS nº 3.005/2024).
- Monitorar mencoes e percepcao publica sobre o programa (PARTE5).

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
│   ├── PARTE4/                     # Cobertura e conformidade legal
│   └── PARTE5/                     # Monitor de percepção (coleta + classificação)
├── map_server/
└── README.md                       # ÚNICO README do repositório
```

## Pré-requisitos

- Python 3.10+
- Ambiente virtual ativo
- Bibliotecas: `pandas`, `numpy`, `matplotlib`, `folium`, `plotly`, `requests`

Exemplo:

```bash
python -m venv venv
source venv/bin/activate
pip install pandas numpy matplotlib folium plotly requests
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

### PARTE 5 (monitor de percepção)

Fluxo recomendado em duas etapas (API-only):

1) Coletar mencoes com SerpAPI + classificar via Gemini no mesmo pipeline:

```bash
export SERPAPI_API_KEY="SUA_CHAVE_SERPAPI"
export GEMINI_API_KEY="SUA_CHAVE_GEMINI"
export GEMINI_MODEL="gemini-2.0-flash"
python "Outputs&Codigo/PARTE5/scripts/monitor_opiniao_melhor_em_casa.py" --tema "Programa Melhor em Casa" --max-itens 80 --gemini-model "gemini-2.0-flash"
```

2) Classificar novamente apenas o que ja foi coletado (sem consumir SerpAPI):

```bash
export GEMINI_API_KEY="SUA_CHAVE_GEMINI"
python "Outputs&Codigo/PARTE5/scripts/classificar_mencoes_existentes_gemini.py" --coletadas-csv "Outputs&Codigo/PARTE5/dados_csv/mencoes_coletadas.csv" --classificadas-csv "Outputs&Codigo/PARTE5/dados_csv/mencoes_classificadas.csv" --gemini-model "gemini-2.0-flash"
```

Observacao: o classificador separado espera automaticamente quando o Gemini retorna HTTP 429 e retoma a classificacao depois do tempo de retry. Para evitar execucao indefinida, use limites por item e limite global de duracao:

```bash
python "Outputs&Codigo/PARTE5/scripts/classificar_mencoes_existentes_gemini.py" --max-esperas-429-por-item 3 --max-segundos-espera-por-item 240 --max-minutos-execucao 30
```

Se quiser concluir a rodada sem nenhuma chamada ao Gemini (sem risco de bloqueio por cota), use:

```bash
python "Outputs&Codigo/PARTE5/scripts/classificar_mencoes_existentes_gemini.py" --sem-tentativa-gemini
```

Dica para a analise de opiniao publica no relatorio: rode a coleta com foco em percepcao usando queries de reclamacoes e depoimentos, por exemplo:
- `"Melhor em Casa" reclamacoes`
- `"Melhor em Casa" e bom?`
- `"Melhor em Casa" depoimento paciente`

```bash
python "Outputs&Codigo/PARTE5/scripts/monitor_opiniao_melhor_em_casa.py" --max-itens 80 --foco-opiniao-publica
```

## Dados e filtros principais

- Tipos de equipe AD usados: **22 (EMAD I), 46 (EMAD II), 23 (EMAP), 77 (EMAP-R)**.
- Competência CNES utilizada: **08/2025**.
- Fontes: CNES/DATASUS, CBO, IBGE.

## Saídas esperadas (resumo)

- Visualizações em PNG/HTML nas partes 1, 2 e 4.
- CSVs analíticos em `Outputs&Codigo/PARTE4/dados_csv`.
- Artefatos por estado em `Outputs&Codigo/PARTE4/visualizacoes/estados`.
- CSV/JSON/PNG de percepção em `Outputs&Codigo/PARTE5/`.

## Observações

- Este repositório mantém **apenas este README na raiz**.
- Pastas de dados brutos podem estar fora do versionamento por tamanho.
