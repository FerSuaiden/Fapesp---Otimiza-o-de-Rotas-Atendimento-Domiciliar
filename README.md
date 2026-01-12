# Otimização de Rotas de Atenção Domiciliar (HHC-RSP)

> **Projeto de Iniciação Científica (FAPESP)**  
> Análise Exploratória de Dados (AED) aplicada ao programa "Melhor em Casa" usando dados do CNES/DATASUS.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Libraries](https://img.shields.io/badge/Lib-Pandas%20%7C%20Folium%20%7C%20Matplotlib%20%7C%20Plotly%20%7C%20GeoPandas-orange)
![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-green)
![CNES](https://img.shields.io/badge/CNES-08%2F2025-purple)
![Censo](https://img.shields.io/badge/Censo-2022-red)

---

## Sumário

- [Objetivo](#objetivo)
- [Contexto do Problema](#contexto-do-problema)
- [Fontes de Dados](#fontes-de-dados)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Metodologia](#metodologia)
  - [PARTE 1: Identificação e Mapeamento das Equipes](#parte-1-identificação-e-mapeamento-das-equipes)
  - [PARTE 2: Quantificação de Capacidade e Habilidades](#parte-2-quantificação-de-capacidade-q_k-e-habilidades-s_k)
  - [PARTE 3: Análise de Demanda (Censo 2022)](#parte-3-análise-de-demanda-censo-2022)
  - [PARTE 4: Análise de Saturação e Conformidade Legal](#parte-4-análise-de-saturação-e-conformidade-legal)
- [Principais Descobertas](#principais-descobertas)
- [Visualizações Geradas](#visualizações-geradas)
- [Como Executar](#como-executar)
- [Referências](#referências)

---

## Objetivo

Este repositório contém a etapa de **Análise Exploratória de Dados (AED)** para a modelagem de um problema de otimização de rotas de Atenção Domiciliar (*Home Health Care Routing and Scheduling Problem - HHC-RSP*).

O objetivo principal é extrair parâmetros-chave das bases públicas do governo para identificar:

| Parâmetro | Descrição | Variável |
|:---:|:---|:---:|
| 1 | **Depots** - Localização das bases das equipes (Lat/Long) | Coordenadas |
| 2 | **Capacidade** - Carga Horária Semanal Total de cada equipe | $Q_k$ |
| 3 | **Habilidades** - Composição profissional de cada equipe | $S_k$ |
| 4 | **Demanda** - População idosa por setor censitário | $D_i$ |

---

## Contexto do Problema

O **Programa Melhor em Casa** é uma política pública do Ministério da Saúde que oferece atendimento domiciliar a pacientes que necessitam de cuidados de saúde contínuos, mas que podem ser tratados em casa. 

O problema de **Roteamento e Agendamento de Cuidados Domiciliares (HHC-RSP)** busca otimizar as rotas das equipes de saúde para:
- Minimizar custos de deslocamento
- Maximizar a cobertura de pacientes
- Respeitar as restrições de capacidade e habilidades das equipes
- Garantir janelas de tempo adequadas para os atendimentos

---

## Fontes de Dados

### CNES - Cadastro Nacional de Estabelecimentos de Saúde

Os dados foram extraídos do CNES (competência **08/2025**) via DATASUS.

- **Download das bases:** [Arquivos de Base de Dados](https://cnes.datasus.gov.br/pages/downloads/arquivosBaseDados.jsp)
- **Documentação (Leia-me):** [Documentação CNES](https://cnes.datasus.gov.br/pages/downloads/documentacao.jsp) - Contém o dicionário de dados com os códigos de equipes (22, 46, 23, 77)

| Arquivo | Descrição | Chaves Principais |
|:---|:---|:---|
| `tbEstabelecimento202508.csv` | Cadastro de clínicas, hospitais e unidades de saúde | `CO_UNIDADE`, `NU_LATITUDE`, `NU_LONGITUDE`, `CO_ESTADO_GESTOR` |
| `tbEquipe202508.csv` | Vínculo das equipes de saúde aos estabelecimentos | `CO_UNIDADE`, `SEQ_EQUIPE`, `TP_EQUIPE` |
| `rlEstabEquipeProf202508.csv` | Tabela-ponte: liga profissionais às equipes | `SEQ_EQUIPE`, `CO_PROFISSIONAL_SUS`, `CO_CBO` |
| `tbCargaHorariaSus202508.csv` | Carga horária de cada profissional | `CO_PROFISSIONAL_SUS`, `CO_CBO`, `QT_CARGA_HORARIA_*` |

### CBO - Classificação Brasileira de Ocupações

- **Download:** [CBO - Downloads](https://cbo.mte.gov.br/cbosite/pages/downloads.jsf)

| Arquivo | Descrição |
|:---|:---|
| `CBO2002 - Ocupacao.csv` | Dicionário para traduzir códigos CBO em nomes de profissões |

### IBGE - Censo Demográfico 2022

| Arquivo | Descrição |
|:---|:---|
| Agregados por Setores Censitários | Dados demográficos por setor (população idosa 60+) |
| Malha de Setores SP | Shapefile com geometrias dos setores censitários |

---

## Filtros de Equipes (Programa Melhor em Casa)

A filtragem foi realizada com base na [documentação oficial do CNES](https://cnes.datasus.gov.br/pages/downloads/documentacao.jsp) (arquivo Leia-me) e **Portaria GM/MS nº 3.005/2024** para garantir rastreabilidade:

| Código | Sigla | Descrição Completa | Categoria |
|:---:|:---|:---|:---:|
| **22** | EMAD I | Equipe Multiprofissional de Atenção Domiciliar Tipo I | Atendimento |
| **46** | EMAD II | Equipe Multiprofissional de Atenção Domiciliar Tipo II | Atendimento |
| **23** | EMAP | Equipe Multiprofissional de Apoio | Apoio |
| **77** | EMAP-R | Equipe Multiprofissional de Apoio para Reabilitação | Apoio |

---

## Estrutura do Projeto

```
IC/
├── CNES_DATA/                       # Dados brutos do CNES/DATASUS
│   ├── tbEstabelecimento202508.csv
│   ├── tbEquipe202508.csv
│   ├── rlEstabEquipeProf202508.csv
│   ├── tbCargaHorariaSus202508.csv
│   └── ...
├── CBO_DATA/                        # Classificação Brasileira de Ocupações
│   ├── CBO2002 - Ocupacao.csv
│   ├── CBO2002 - Familia.csv
│   └── ...
├── IBGE_DATA/                       # Dados do Censo 2022
│   └── ...
├── Outputs&Codigo/                  # Scripts e visualizações
│   ├── PARTE1/                      # Mapeamento de Equipes
│   ├── PARTE2/                      # Capacidade e Habilidades
│   ├── PARTE3/                      # Análise de Demanda
│   └── PARTE4/                      # Análise de Saturação
└── README.md
```

---

## Metodologia

### PARTE 1: Identificação e Mapeamento das Equipes

Esta fase identifica a localização geográfica das equipes do programa "Melhor em Casa" no estado de São Paulo, permitindo visualizar a distribuição espacial dos depots (bases de partida) e a cobertura por tipo de equipe.

#### 1-visuazacaoMapa.py

**Arquivo:** [Outputs&Codigo/PARTE1/1-visuazacaoMapa.py](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py)  
**Output:** `mapa_Equipes_Atencao_Domiciliar_SP.html`

Este script gera um mapa interativo das equipes de Atenção Domiciliar no estado de São Paulo.

**Etapas do processamento:**

1. **Carregamento dos dados** ([linhas 9-13](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py#L9-L13)): Carrega as tabelas `tbEstabelecimento` e `tbEquipe` do CNES.

2. **Identificação das equipes** ([linhas 16-27](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py#L16-L27)): Define os códigos de equipe relevantes e cria conjuntos de CNES únicos para cada categoria:
   - Atendimento: EMAD I (22) e EMAD II (46)
   - Apoio: EMAP (23) e EMAP-R (77)

3. **Filtro geográfico para São Paulo** ([linhas 30-34](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py#L30-L34)): Aplica o filtro `CO_ESTADO_GESTOR = '35'` (código IBGE de SP).

4. **Tratamento de coordenadas** ([linhas 37-42](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py#L37-L42)): Converte vírgulas para pontos decimais e remove registros com coordenadas nulas ou zeradas.

5. **Classificação por categoria** ([linhas 45-55](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py#L45-L55)): Categoriza cada estabelecimento como:
   - Apenas Atendimento (azul)
   - Apenas Apoio (verde)
   - Ambos (roxo)

6. **Geração do mapa** ([linhas 64-90](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py#L64-L90)): Cria o mapa Folium com MarkerCluster e popups informativos.

7. **Legenda HTML** ([linhas 93-112](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py#L93-L112)): Adiciona legenda fixa explicando a codificação de cores.

---

#### 2-equipes_por_estado.py

**Arquivo:** [Outputs&Codigo/PARTE1/2-equipes_por_estado.py](Outputs%26Codigo/PARTE1/2-equipes_por_estado.py)  
**Output:** `distribuicao_equipes_por_estado_empilhado.png`

Este script gera um gráfico de barras empilhadas mostrando a distribuição das equipes de Atenção Domiciliar por estado brasileiro.

**Etapas do processamento:**

1. **Dicionários de mapeamento** ([linhas 14-32](Outputs%26Codigo/PARTE1/2-equipes_por_estado.py#L14-L32)): Define:
   - `MAP_EQUIPES`: Traduz códigos (22, 46, 23, 77) para nomes (EMAD I, EMAD II, EMAP, EMAP-R)
   - `IBGE_UF_MAP`: Converte códigos IBGE para siglas dos estados

2. **Carregamento otimizado** ([linhas 36-54](Outputs%26Codigo/PARTE1/2-equipes_por_estado.py#L36-L54)): Usa `usecols` para ler apenas colunas necessárias, reduzindo consumo de memória.

3. **Merge e mapeamento** ([linhas 57-79](Outputs%26Codigo/PARTE1/2-equipes_por_estado.py#L57-L79)): Junta as tabelas de equipes e estabelecimentos usando `CO_UNIDADE` como chave e aplica os mapeamentos.

4. **Tabela de contingência** ([linhas 82-98](Outputs%26Codigo/PARTE1/2-equipes_por_estado.py#L82-L98)): Usa `pd.crosstab` para criar uma matriz de contagem Estados x Tipos de Equipe, ordenada por total.

5. **Visualização** ([linhas 101-145](Outputs%26Codigo/PARTE1/2-equipes_por_estado.py#L101-L145)): Gera gráfico de barras empilhadas com formatação profissional, legenda detalhada e nota de fonte.

---

#### 3-pizza.py

**Arquivo:** [Outputs&Codigo/PARTE1/3-pizza.py](Outputs%26Codigo/PARTE1/3-pizza.py)  
**Output:** `composicao_nacional_pizza.png`

Este script combina dois gráficos: barras empilhadas por estado e pizza donut da composição nacional.

**Etapas do processamento:**

1. **Gráfico de barras** ([linhas 72-124](Outputs%26Codigo/PARTE1/3-pizza.py#L72-L124)): Replica a lógica do script anterior para os Top 15 estados.

2. **Contagem nacional** ([linhas 127-130](Outputs%26Codigo/PARTE1/3-pizza.py#L127-L130)): Usa `value_counts()` para calcular o total de cada tipo de equipe no Brasil.

3. **Gráfico donut** ([linhas 133-150](Outputs%26Codigo/PARTE1/3-pizza.py#L133-L150)): Cria pizza com círculo branco central para efeito visual de rosquinha.

---

### PARTE 2: Quantificação de Capacidade ($Q_k$) e Habilidades ($S_k$)

Esta fase extrai os parâmetros de capacidade (carga horária semanal disponível) e habilidades (composição profissional) de cada equipe, informações essenciais para a modelagem do problema de otimização de rotas.

#### 4-capacidade.py

**Arquivo:** [Outputs&Codigo/PARTE2/4-capacidade.py](Outputs%26Codigo/PARTE2/4-capacidade.py)  
**Outputs:** `capacidade_total_chs_por_estado.png`, `distribuicao_capacidade_Qk_histograma.png`

Este script calcula a capacidade de atendimento ($Q_k$) das equipes usando a Carga Horária Semanal (CHS).

**Etapas do processamento:**

1. **Carregamento de 4 bases** ([linhas 26-55](Outputs%26Codigo/PARTE2/4-capacidade.py#L26-L55)): 
   - `tbEstabelecimento`: para obter UF
   - `tbEquipe`: para filtrar equipes AD
   - `rlEstabEquipeProf`: tabela-ponte equipe-profissional
   - `tbCargaHorariaSus`: carga horária de cada profissional

2. **Merge encadeado Equipes → Profissionais** ([linhas 62-69](Outputs%26Codigo/PARTE2/4-capacidade.py#L62-L69)): Inner join para obter apenas profissionais que estão em equipes de AD.

3. **Merge Profissionais → Carga Horária** ([linhas 71-78](Outputs%26Codigo/PARTE2/4-capacidade.py#L71-L78)): Left join usando chave composta `(CO_UNIDADE, CO_PROFISSIONAL_SUS, CO_CBO)`.

4. **Cálculo da CHS individual** ([linhas 81-91](Outputs%26Codigo/PARTE2/4-capacidade.py#L81-L91)):
   ```
   CHS_PROFISSIONAL_TOTAL = Ambulatorial + Hospitalar + Outros
   ```

5. **Agregação por equipe** ([linhas 93-96](Outputs%26Codigo/PARTE2/4-capacidade.py#L93-L96)): Agrupa por `SEQ_EQUIPE` e soma as CHS de todos os membros para obter $Q_k$.

6. **Gráfico de capacidade por estado** ([linhas 117-137](Outputs%26Codigo/PARTE2/4-capacidade.py#L117-L137)): Barras horizontais com Top 15 estados, valores formatados em milhares (k).

7. **Histograma de distribuição** ([linhas 140-164](Outputs%26Codigo/PARTE2/4-capacidade.py#L140-L164)): Mostra a distribuição de $Q_k$ entre as equipes com linha de média.

---

#### 5-heatMap.py

**Arquivo:** [Outputs&Codigo/PARTE2/5-heatMap.py](Outputs%26Codigo/PARTE2/5-heatMap.py)  
**Output:** `mapa_calor_chs_brasil.html`

Este script gera um mapa de calor interativo do Brasil mostrando a intensidade da capacidade de Atenção Domiciliar.

**Etapas do processamento:**

1. **Carregamento com coordenadas** ([linhas 20-45](Outputs%26Codigo/PARTE2/5-heatMap.py#L20-L45)): Carrega `NU_LATITUDE` e `NU_LONGITUDE` da tabela de estabelecimentos.

2. **Agregação por estabelecimento** ([linhas 74-79](Outputs%26Codigo/PARTE2/5-heatMap.py#L74-L79)): Agrupa por `CO_UNIDADE` (não por equipe) e soma a CHS total.

3. **Preparação de dados** ([linhas 85-92](Outputs%26Codigo/PARTE2/5-heatMap.py#L85-L92)): Limpa coordenadas e formata como lista de triplas `[lat, long, peso]`.

4. **Mapa de calor** ([linhas 95-107](Outputs%26Codigo/PARTE2/5-heatMap.py#L95-L107)): Centraliza no Brasil e adiciona camada HeatMap com parâmetros otimizados.

---

#### 6-sunburst.py

**Arquivo:** [Outputs&Codigo/PARTE2/6-sunburst.py](Outputs%26Codigo/PARTE2/6-sunburst.py)  
**Output:** `habilidades_sunburst.html`

Este script gera um gráfico Sunburst interativo que decompõe a composição da força de trabalho ($S_k$) por tipo de equipe.

**Etapas do processamento:**

1. **Carregamento de 5 bases** ([linhas 26-51](Outputs%26Codigo/PARTE2/6-sunburst.py#L26-L51)): Adiciona `CBO2002 - Ocupacao.csv` como dicionário de profissões.

2. **Merge com tradução CBO** ([linhas 60-69](Outputs%26Codigo/PARTE2/6-sunburst.py#L60-L69)): Conecta códigos CBO aos nomes legíveis das profissões.

3. **Agregação de profissões minoritárias** ([linhas 86-95](Outputs%26Codigo/PARTE2/6-sunburst.py#L86-L95)): Profissões com menos de 0.5% do total são agrupadas como "Outras Profissões".

4. **Gráfico Sunburst** ([linhas 98-130](Outputs%26Codigo/PARTE2/6-sunburst.py#L98-L130)): Hierarquia de dois níveis:
   - Anel interno: Tipo de equipe (EMAD I, EMAD II, EMAP, EMAP-R)
   - Anel externo: Profissões que compõem cada tipo

---

### PARTE 3: Análise de Demanda (Censo 2022)

Esta fase utiliza dados do Censo Demográfico 2022 para mapear a demanda potencial por atenção domiciliar, identificando a concentração de população idosa (60+) por setor censitário em São Paulo.

#### 10-demanda_censo2022_real.py

**Arquivo:** [Outputs&Codigo/PARTE3/10-demanda_censo2022_real.py](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py)  
**Output:** `mapa_demanda_idosos_sp_censo2022.html`

Este script utiliza dados reais do Censo 2022 para calcular a demanda de idosos por setor censitário.

**Variáveis do Censo utilizadas** ([linhas 8-11](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py#L8-L11)):
- V01006: Quantidade de moradores (total)
- V01040: 60 a 69 anos
- V01041: 70 anos ou mais

**Etapas do processamento:**

1. **Download automático** ([linhas 37-65](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py#L37-L65)): Baixa e extrai arquivos ZIP do FTP do IBGE se não existirem localmente.

2. **Carregamento de dados demográficos** ([linhas 68-84](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py#L68-L84)): Lê o CSV de agregados por setores censitários do Brasil.

3. **Carregamento da malha de SP** ([linhas 87-118](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py#L87-L118)): Lê o shapefile com as geometrias dos setores censitários de São Paulo.

4. **Filtro para SP Capital** ([linhas 123-150](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py#L123-L150)): Usa código do município 3550308 para filtrar apenas a capital.

5. **Cálculo da demanda** ([linhas 153-210](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py#L153-L210)):
   ```
   Demanda = pop_60_69 + pop_70_mais
   ```
   Trata valores sigilosos ("X") do IBGE como zero.

6. **Mapa de calor** ([linhas 213-250](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py#L213-L250)): Gera visualização da concentração de idosos por setor.

---

### PARTE 4: Análise de Saturação e Conformidade Legal

Esta fase avalia se as equipes atendem aos requisitos mínimos de composição definidos pela legislação vigente, identificando o índice de conformidade e possíveis gargalos operacionais.

#### 8-analise_saturacao_ad.py

**Arquivo:** [Outputs&Codigo/PARTE4/8-analise_saturacao_ad.py](Outputs%26Codigo/PARTE4/8-analise_saturacao_ad.py)  
**Outputs:** Dashboards de conformidade

Este script analisa se as equipes atendem aos requisitos normativos da Portaria GM/MS 3.005/2024.

**Base legal** ([linhas 5-42](Outputs%26Codigo/PARTE4/8-analise_saturacao_ad.py#L5-L42)): 
- Portaria de Consolidação GM/MS nº 5/2017
- Portaria GM/MS nº 3.005 de 02/05/2024

**Regras de completude** ([linhas 85-124](Outputs%26Codigo/PARTE4/8-analise_saturacao_ad.py#L85-L124)):

| Tipo | Médico | Enfermeiro | Téc. Enfermagem | Fisio/AS |
|:---:|:---:|:---:|:---:|:---:|
| EMAD I | ≥40h | ≥60h | ≥120h | ≥30h |
| EMAD II | ≥20h | ≥30h | ≥120h | ≥30h |
| EMAP | - | - | - | 3+ prof. NS, ≥90h |
| EMAP-R | - | ≥30h | - | 3+ prof. NS, ≥60h |

**Categorização de CBOs** ([linhas 159-199](Outputs%26Codigo/PARTE4/8-analise_saturacao_ad.py#L159-L199)): Função que categoriza códigos CBO em classes profissionais:
- Prefixo 2251/2252/2253 → MEDICO
- Prefixo 2235 → ENFERMEIRO
- Prefixo 3222 → TECNICO_ENFERMAGEM
- E assim por diante...

**Cálculo da CHS Real** ([linhas 203-280](Outputs%26Codigo/PARTE4/8-analise_saturacao_ad.py#L203-L280)):
```
CHS_REAL = Ambulatorial + Hospitalar + Outros
```
Profissionais com CHS < 20h são descartados (Art. 547, §1º).

---

## Principais Descobertas

### Descoberta Crítica (Dezembro 2025)

A análise revelou que aproximadamente **53% das equipes EMAD I em SP Capital** estão **subdimensionadas em enfermeiros** segundo os parâmetros legais:

| Parâmetro | Exigido | Encontrado |
|:---|:---:|:---:|
| CHS Enfermeiro | ≥ 60h | 40h (97% dos casos) |
| Interpretação | 1.5 FTE | 1 enfermeiro |

Esta é uma **evidência de subdimensionamento operacional real**, não um erro de código.

### Outras Descobertas

- **São Paulo** é o estado com maior capacidade instalada de Atenção Domiciliar
- A distribuição de capacidade entre equipes é **heterogênea** (não uniforme)
- Hotspots de atendimento concentrados em regiões metropolitanas
- Necessidade crítica de otimização de rotas para maximizar eficiência

---

## Visualizações Geradas

### PARTE 1 - Mapeamento

| Visualização | Descrição |
|:---|:---|
| [mapa_Equipes_Atencao_Domiciliar_SP.html](Outputs%26Codigo/PARTE1/mapa_Equipes_Atencao_Domiciliar_SP.html) | Mapa interativo (Folium) com clusters de marcadores coloridos |
| [distribuicao_equipes_por_estado_empilhado.png](Outputs%26Codigo/PARTE1/distribuicao_equipes_por_estado_empilhado.png) | Top 15 estados por número de equipes |
| [composicao_nacional_pizza.png](Outputs%26Codigo/PARTE1/composicao_nacional_pizza.png) | Proporção EMAD I / EMAD II / EMAP / EMAP-R no Brasil |

### PARTE 2 - Capacidade e Habilidades

| Visualização | Descrição |
|:---|:---|
| [capacidade_total_chs_por_estado.png](Outputs%26Codigo/PARTE2/capacidade_total_chs_por_estado.png) | Top 15 estados por CHS total |
| [distribuicao_capacidade_Qk_histograma.png](Outputs%26Codigo/PARTE2/distribuicao_capacidade_Qk_histograma.png) | Histograma de distribuição de $Q_k$ |
| [mapa_calor_chs_brasil.html](Outputs%26Codigo/PARTE2/mapa_calor_chs_brasil.html) | Heatmap de intensidade de CHS no Brasil |
| [habilidades_sunburst.html](Outputs%26Codigo/PARTE2/habilidades_sunburst.html) | Gráfico Sunburst interativo de composição profissional |

### PARTE 3 - Demanda

| Visualização | Descrição |
|:---|:---|
| [mapa_demanda_idosos_sp_censo2022.html](Outputs%26Codigo/PARTE3/mapa_demanda_idosos_sp_censo2022.html) | Mapa de calor da população idosa por setor censitário |

### PARTE 4 - Saturação

| Visualização | Descrição |
|:---|:---|
| [v2_composicao_equipes.png](Outputs%26Codigo/PARTE4/v2_composicao_equipes.png) | Composição real das equipes |
| [v2_dashboard_saturacao_oferta.png](Outputs%26Codigo/PARTE4/v2_dashboard_saturacao_oferta.png) | Dashboard de saturação da oferta |
| [v2_indice_precariedade_normativa.png](Outputs%26Codigo/PARTE4/v2_indice_precariedade_normativa.png) | Índice de precariedade por região |
| [v2_razao_cobertura_real.png](Outputs%26Codigo/PARTE4/v2_razao_cobertura_real.png) | Razão de cobertura efetiva |

---

## Como Executar

### Pré-requisitos

```bash
# Python 3.10+
pip install pandas numpy matplotlib folium plotly geopandas requests
```

### Execução

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/IC-HHC-RSP.git
cd IC-HHC-RSP

# Execute os scripts na ordem
cd "Outputs&Codigo/PARTE1"
python 1-visuazacaoMapa.py
python 2-equipes_por_estado.py
python 3-pizza.py

cd "../PARTE2"
python 4-capacidade.py
python 5-heatMap.py
python 6-sunburst.py

cd "../PARTE3"
python 10-demanda_censo2022_real.py

cd "../PARTE4"
python 8-analise_saturacao_ad.py
```

### Estrutura de Dependências

```
pandas>=1.5.0
numpy>=1.23.0
matplotlib>=3.6.0
folium>=0.14.0
plotly>=5.11.0
geopandas>=0.12.0
requests>=2.28.0
```

---

## Referências

### Fontes de Dados

| Fonte | Link |
|:---|:---|
| CNES - Bases de Dados | [Download](https://cnes.datasus.gov.br/pages/downloads/arquivosBaseDados.jsp) |
| CNES - Documentação (Leia-me) | [Download](https://cnes.datasus.gov.br/pages/downloads/documentacao.jsp) |
| CBO - Classificação Brasileira de Ocupações | [Download](https://cbo.mte.gov.br/cbosite/pages/downloads.jsf) |
| IBGE - Censo 2022 | [Portal](https://censo2022.ibge.gov.br/) |

### Legislação

| Documento | Descrição |
|:---|:---|
| Portaria GM/MS nº 825/2016 | Redefine a Atenção Domiciliar no âmbito do SUS |
| Portaria de Consolidação nº 5/2017 | Consolidação das normas sobre ações e serviços de saúde |
| Portaria GM/MS nº 3.005/2024 | Atualização dos requisitos de composição das equipes AD |

---

## Autores

- **Orientando:** Fernando Alee Suaiden
- **Orientador:** Maristela Oliveira dos Santos
- **Instituição:** Universidade de São Paulo (USP)
- **Financiamento:** FAPESP
