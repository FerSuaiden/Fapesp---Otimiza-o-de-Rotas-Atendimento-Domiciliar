# RELATÓRIO CIENTÍFICO - INICIAÇÃO CIENTÍFICA FAPESP

---

## FUNDAÇÃO DE AMPARO À PESQUISA DO ESTADO DE SÃO PAULO

### Relatório Científico de Atividades

---

**Processo FAPESP:** [A ser preenchido]  
**Vigência:** [A ser preenchido]  
**Período coberto pelo relatório:** Janeiro 2025 - Janeiro 2026  
**Modalidade:** Bolsa de Iniciação Científica

---

## DADOS DO PROJETO

| Campo | Informação |
|:------|:-----------|
| **Título do Projeto** | Otimização de Rotas de Atenção Domiciliar: Modelagem e Resolução do Home Health Care Routing and Scheduling Problem (HHC-RSP) |
| **Bolsista** | Fernando Alee Suaiden |
| **Orientadora** | Profa. Dra. Maristela Oliveira dos Santos |
| **Instituição** | Universidade de São Paulo (USP) |
| **Área de Conhecimento** | Pesquisa Operacional / Ciência da Computação |
| **Palavras-chave** | Otimização Combinatória, Roteamento de Veículos, Atenção Domiciliar, BRKGA, Análise de Dados, SUS |

---

## SUMÁRIO EXECUTIVO

Este relatório apresenta os resultados obtidos durante o primeiro período de desenvolvimento do projeto de Iniciação Científica intitulado "Otimização de Rotas de Atenção Domiciliar: Modelagem e Resolução do HHC-RSP". O projeto visa desenvolver um modelo de otimização para o roteamento e agendamento de equipes de Atenção Domiciliar do Programa "Melhor em Casa" do Sistema Único de Saúde (SUS).

Durante este período, foi realizada uma **Análise Exploratória de Dados (AED)** completa utilizando bases públicas do CNES/DATASUS, CBO e IBGE, resultando na identificação de parâmetros críticos para a modelagem do problema de otimização. Os principais resultados incluem:

- **Mapeamento geográfico** de 2.664 equipes de Atenção Domiciliar em todo o Brasil
- **Quantificação da capacidade** ($Q_k$) de cada equipe baseada em Carga Horária Semanal (CHS)
- **Caracterização das habilidades** ($S_k$) por composição profissional
- **Análise de conformidade legal** com a Portaria GM/MS nº 3.005/2024
- **Geração de instâncias** para o modelo de otimização BRKGA

---

## 1. INTRODUÇÃO

### 1.1 Contexto e Motivação

O envelhecimento populacional brasileiro representa um dos maiores desafios para o sistema de saúde nas próximas décadas. Segundo projeções do Instituto Brasileiro de Geografia e Estatística (IBGE), a população com 60 anos ou mais deverá passar de 32,5 milhões em 2022 para mais de 73 milhões em 2060, representando cerca de 32% da população total. Esse cenário demanda soluções inovadoras para garantir acesso a serviços de saúde de qualidade, especialmente para pacientes com mobilidade reduzida ou em condições crônicas.

Nesse contexto, o **Programa Melhor em Casa**, instituído pelo Ministério da Saúde em novembro de 2011 através da Portaria GM/MS nº 2.527/2011, surge como uma estratégia fundamental para humanizar o atendimento e otimizar recursos hospitalares. O programa oferece atendimento domiciliar a pacientes que necessitam de cuidados de saúde contínuos, mas que podem ser tratados em casa, proporcionando:

- **Humanização do atendimento**: O paciente recebe cuidados no conforto do lar, junto à família
- **Desafogamento hospitalar**: Redução de internações desnecessárias e liberação de leitos
- **Melhoria da qualidade de vida**: Ambiente familiar favorece a recuperação
- **Redução de custos**: Internações domiciliares custam significativamente menos que hospitalares

O programa é operacionalizado por dois tipos de equipes multiprofissionais:

| Tipo de Equipe | Sigla | Função Principal |
|:--------------|:------|:-----------------|
| Equipe Multiprofissional de Atenção Domiciliar Tipo I | EMAD I | Atendimento direto ao paciente (maior complexidade) |
| Equipe Multiprofissional de Atenção Domiciliar Tipo II | EMAD II | Atendimento direto ao paciente (menor complexidade) |
| Equipe Multiprofissional de Apoio | EMAP | Suporte especializado às EMADs |
| Equipe Multiprofissional de Apoio para Reabilitação | EMAP-R | Suporte com foco em reabilitação |

### 1.2 O Problema de Otimização (HHC-RSP)

O **Home Health Care Routing and Scheduling Problem (HHC-RSP)** é um problema de otimização combinatória que visa determinar as melhores rotas e agendamentos para as equipes de atendimento domiciliar. Este problema pertence à família dos Vehicle Routing Problems (VRP) com características específicas do setor de saúde.

**Formulação do Problema:**

*Dado:*
- Um conjunto de pacientes $N = \{1, 2, ..., n\}$ com localização geográfica, janelas de tempo $[e_i, l_i]$ e requisitos de habilidades $R_i$
- Um conjunto de equipes $K = \{1, 2, ..., k\}$ com base de operação (depot), capacidade $Q_k$ e conjunto de habilidades $S_k$

*Encontrar:*
- As rotas ótimas para cada equipe visitar os pacientes designados
- O agendamento de horários de início de cada visita

*Minimizando:*
- Custos de deslocamento (distância/tempo total percorrido)
- Tempo de espera dos pacientes
- Número de equipes utilizadas

*Sujeito a:*
- Restrições de capacidade: $\sum_{i \in \text{rota}_k} s_i \leq Q_k$
- Restrições de habilidades: $R_i \subseteq S_k$ para todo paciente $i$ atendido pela equipe $k$
- Restrições de janelas de tempo: $e_i \leq t_i \leq l_i$
- Cada paciente é visitado exatamente uma vez

### 1.3 Objetivos do Projeto

**Objetivo Geral:**
Desenvolver e implementar um modelo de otimização para o problema HHC-RSP aplicado ao Programa Melhor em Casa, utilizando o algoritmo BRKGA (Biased Random-Key Genetic Algorithm).

**Objetivos Específicos (Período Atual):**

1. ✅ Realizar Análise Exploratória de Dados (AED) das bases públicas CNES/DATASUS
2. ✅ Identificar e georreferenciar as equipes de Atenção Domiciliar no Brasil
3. ✅ Quantificar a capacidade ($Q_k$) de cada equipe em termos de Carga Horária Semanal
4. ✅ Caracterizar as habilidades ($S_k$) de cada equipe por composição profissional
5. ✅ Analisar a conformidade das equipes com a legislação vigente
6. ✅ Gerar instâncias de teste para o modelo de otimização

---

## 2. REVISÃO BIBLIOGRÁFICA

### 2.1 Fundamentação Teórica

#### 2.1.1 Vehicle Routing Problem (VRP)

O Vehicle Routing Problem (VRP), introduzido por Dantzig e Ramser (1959), é um dos problemas de otimização combinatória mais estudados na literatura de Pesquisa Operacional. O problema consiste em determinar rotas ótimas para uma frota de veículos que devem atender um conjunto de clientes, minimizando custos de transporte enquanto satisfaz restrições operacionais.

Ao longo das décadas, diversas variantes do VRP foram propostas para modelar situações reais mais complexas:

| Variante | Descrição |
|:---------|:----------|
| CVRP | Capacitated VRP - restrições de capacidade dos veículos |
| VRPTW | VRP with Time Windows - janelas de tempo para atendimento |
| VRPPD | VRP with Pickup and Delivery - coleta e entrega |
| HVRP | Heterogeneous VRP - frota heterogênea |
| VRPSD | VRP with Skill Differences - diferenças de habilidades |

#### 2.1.2 Home Health Care Routing and Scheduling Problem (HHC-RSP)

O HHC-RSP é uma extensão do VRP clássico adaptada para o contexto de cuidados domiciliares de saúde. As principais características distintivas incluem:

1. **Heterogeneidade de habilidades**: Cada profissional possui qualificações específicas (médico, enfermeiro, fisioterapeuta, etc.) que devem ser compatíveis com as necessidades do paciente.

2. **Janelas de tempo estritas**: Pacientes possuem horários preferenciais ou obrigatórios para receber atendimento, especialmente para procedimentos como administração de medicamentos.

3. **Tempo de serviço variável**: O tempo de atendimento depende do tipo de procedimento e condição do paciente.

4. **Continuidade de cuidados**: Alguns pacientes requerem visitas recorrentes, preferencialmente pelo mesmo profissional.

5. **Regulamentação legal**: No Brasil, a composição e carga horária das equipes são regulamentadas por portarias do Ministério da Saúde.

A literatura sobre HHC-RSP tem crescido significativamente nas últimas décadas. Trabalhos seminais incluem:

- **Begur et al. (1997)**: Primeira modelagem formal do problema de roteamento para serviços de saúde domiciliar
- **Cheng e Rich (1998)**: Heurísticas para programação de enfermeiros domiciliares
- **Bertels e Fahle (2006)**: Abordagem híbrida combinando programação por restrições e meta-heurísticas
- **Fikar e Hirsch (2017)**: Revisão abrangente da literatura sobre HHC-RSP

#### 2.1.3 BRKGA - Biased Random-Key Genetic Algorithm

O BRKGA, proposto por Gonçalves e Resende (2011), é uma meta-heurística evolucionária baseada em algoritmos genéticos que utiliza codificação de chaves aleatórias (random keys) para representar soluções.

**Principais características:**
- **Codificação por chaves aleatórias**: Cada solução é representada por um vetor de números reais no intervalo [0,1]
- **Decodificador determinístico**: Transforma o vetor de chaves em uma solução factível do problema
- **Seleção enviesada (biased)**: Privilegia indivíduos de alta aptidão no cruzamento
- **Elitismo**: Preserva as melhores soluções entre gerações
- **Mutantes**: Introduz diversidade através de soluções aleatórias

O BRKGA tem demonstrado excelente desempenho em diversos problemas combinatórios, incluindo scheduling, roteamento e problemas de corte e empacotamento.

### 2.2 Legislação e Regulamentação

A Atenção Domiciliar no âmbito do SUS é regulamentada por um conjunto de normas que definem a composição, atribuições e requisitos das equipes. Os principais marcos legais são:

#### Portaria GM/MS nº 825/2016
Redefine a Atenção Domiciliar no âmbito do SUS, substituindo a Portaria 2.527/2011. Estabelece as modalidades de atenção domiciliar (AD1, AD2 e AD3) e a composição básica das equipes EMAD e EMAP.

#### Portaria de Consolidação nº 5/2017
Consolida as normas sobre ações e serviços de saúde do SUS, incorporando as disposições sobre Atenção Domiciliar.

#### Portaria GM/MS nº 3.005/2024
**Marco regulatório mais recente**, atualiza os requisitos de composição das equipes AD. Principais alterações:

| Equipe | Requisito Anterior (825/2016) | Requisito Atual (3.005/2024) |
|:-------|:------------------------------|:-----------------------------|
| EMAD I - Médico | ≥40h | ≥40h (mantido) |
| EMAD I - Enfermeiro | ≥40h | **≥60h (aumentado)** |
| EMAD I - Téc. Enfermagem | ≥120h | ≥120h (mantido) |
| EMAD I - Fisio ou AS | ≥30h | ≥30h (mantido) |
| EMAD II - Enfermeiro | ≥20h | **≥30h (aumentado)** |

**Art. 547, §1º**: Nenhum profissional componente de EMAD poderá ter carga horária semanal inferior a 20 horas.

---

## 3. MATERIAIS E MÉTODOS

### 3.1 Fontes de Dados

A análise exploratória utilizou três fontes primárias de dados públicos:

#### 3.1.1 CNES - Cadastro Nacional de Estabelecimentos de Saúde

O CNES é o sistema oficial do Ministério da Saúde que cadastra todos os estabelecimentos de saúde do Brasil, seus profissionais e equipes. É a principal fonte para identificação das equipes de Atenção Domiciliar.

**Competência dos dados:** Agosto/2025

**Tabelas utilizadas:**

| Arquivo | Descrição | Campos Principais |
|:--------|:----------|:------------------|
| `tbEstabelecimento202508.csv` | Cadastro de estabelecimentos de saúde | `CO_UNIDADE`, `NU_LATITUDE`, `NU_LONGITUDE`, `CO_ESTADO_GESTOR`, `CO_MUNICIPIO_GESTOR` |
| `tbEquipe202508.csv` | Vínculo de equipes aos estabelecimentos | `CO_UNIDADE`, `SEQ_EQUIPE`, `TP_EQUIPE` |
| `rlEstabEquipeProf202508.csv` | Tabela-ponte equipe-profissional | `CO_UNIDADE`, `SEQ_EQUIPE`, `CO_PROFISSIONAL_SUS`, `CO_CBO` |
| `tbCargaHorariaSus202508.csv` | Carga horária de cada profissional | `CO_PROFISSIONAL_SUS`, `CO_CBO`, `QT_CARGA_HORARIA_*` |

**Códigos de Tipo de Equipe (TP_EQUIPE):**

| Código | Sigla | Descrição |
|:------:|:------|:----------|
| 22 | EMAD I | Equipe Multiprofissional de Atenção Domiciliar Tipo I |
| 46 | EMAD II | Equipe Multiprofissional de Atenção Domiciliar Tipo II |
| 23 | EMAP | Equipe Multiprofissional de Apoio |
| 77 | EMAP-R | Equipe Multiprofissional de Apoio para Reabilitação |

#### 3.1.2 CBO - Classificação Brasileira de Ocupações

A CBO é a classificação oficial do Ministério do Trabalho que padroniza os códigos de todas as profissões do Brasil. Utilizada para identificar a categoria profissional de cada membro das equipes.

**Arquivo principal:** `CBO2002 - Ocupacao.csv`

**Mapeamento de códigos CBO para categorias:**

| Prefixo CBO | Categoria Profissional |
|:------------|:-----------------------|
| 2251, 2252, 2253 | Médico |
| 2235 | Enfermeiro |
| 3222 | Técnico de Enfermagem |
| 2236 | Fisioterapeuta |
| 2516 | Assistente Social |
| 2238 | Fonoaudiólogo |
| 2237 | Nutricionista |
| 2515 | Psicólogo |
| 2239 | Terapeuta Ocupacional |
| 2232 | Odontólogo |
| 2234 | Farmacêutico |

#### 3.1.3 IBGE - Instituto Brasileiro de Geografia e Estatística

Fonte para dados demográficos do Censo 2022 e informações geográficas:

- **Total de municípios por UF** (referência para cálculo de cobertura)
- **Malha de setores censitários** (geometrias para análise espacial)
- **População por faixa etária** (estimativa de demanda por idosos 60+)

### 3.2 Metodologia de Análise

A análise foi estruturada em quatro partes principais, cada uma gerando artefatos específicos:

```
METODOLOGIA DE ANÁLISE EXPLORATÓRIA
├── PARTE 1: Identificação e Mapeamento das Equipes
│   ├── Georreferenciamento das bases de operação (depots)
│   ├── Classificação por tipo de equipe
│   └── Distribuição geográfica por estado e região
│
├── PARTE 2: Quantificação de Capacidade e Habilidades
│   ├── Cálculo de Carga Horária Semanal (CHS) por equipe
│   ├── Agregação do parâmetro Q_k (capacidade)
│   └── Caracterização do parâmetro S_k (habilidades)
│
├── PARTE 3: Geração de Instâncias para Otimização
│   ├── Estruturação de dados para entrada do BRKGA
│   ├── Geração de pacientes sintéticos
│   └── Cálculo de matriz de distâncias
│
└── PARTE 4: Análise de Conformidade Legal
    ├── Verificação dos requisitos da Portaria 3.005/2024
    ├── Identificação de gargalos operacionais
    └── Análise por tipo de equipe, estado e região
```

### 3.3 Ferramentas Computacionais

**Linguagem de Programação:** Python 3.10+

**Principais Bibliotecas:**

| Biblioteca | Versão | Função |
|:-----------|:-------|:-------|
| `pandas` | ≥1.5.0 | Manipulação e análise de dados tabulares |
| `numpy` | ≥1.23.0 | Operações numéricas e estatísticas |
| `matplotlib` | ≥3.6.0 | Visualização estática (gráficos de barras, histogramas) |
| `folium` | ≥0.14.0 | Mapas interativos baseados em Leaflet |
| `plotly` | ≥5.11.0 | Visualizações interativas (Sunburst) |
| `geopandas` | ≥0.12.0 | Análise de dados geoespaciais |
| `requests` | ≥2.28.0 | Requisições HTTP para APIs de geocodificação |

**Ambiente de Desenvolvimento:**
- Visual Studio Code
- Jupyter Notebooks
- Git/GitHub para controle de versão

### 3.4 Fluxo de Processamento de Dados

O processamento dos dados seguiu um pipeline estruturado:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE PROCESSAMENTO                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [CNES/DATASUS]     [CBO]         [IBGE]                           │
│       │               │              │                              │
│       ▼               ▼              ▼                              │
│  ┌─────────────────────────────────────────┐                       │
│  │          EXTRAÇÃO E LIMPEZA              │                       │
│  │  • Tratamento de encoding (latin-1)      │                       │
│  │  • Conversão de tipos (str → numeric)    │                       │
│  │  • Tratamento de coordenadas             │                       │
│  └─────────────────────────────────────────┘                       │
│                      │                                              │
│                      ▼                                              │
│  ┌─────────────────────────────────────────┐                       │
│  │            MERGE E INTEGRAÇÃO            │                       │
│  │  • tbEquipe ⟷ rlEstabEquipeProf         │                       │
│  │  • rlEstabEquipeProf ⟷ tbCargaHorariaSus│                       │
│  │  • Códigos CBO ⟷ Nomes de profissões    │                       │
│  └─────────────────────────────────────────┘                       │
│                      │                                              │
│                      ▼                                              │
│  ┌─────────────────────────────────────────┐                       │
│  │          CÁLCULOS E AGREGAÇÕES           │                       │
│  │  • CHS = Ambulatorial + Hospitalar + Outros │                   │
│  │  • Q_k = Σ CHS_profissionais (por equipe)   │                   │
│  │  • S_k = {categorias profissionais}          │                   │
│  └─────────────────────────────────────────┘                       │
│                      │                                              │
│                      ▼                                              │
│  ┌─────────────────────────────────────────┐                       │
│  │         VISUALIZAÇÕES E OUTPUTS          │                       │
│  │  • Mapas interativos (Folium)            │                       │
│  │  • Gráficos estáticos (Matplotlib)       │                       │
│  │  • Gráficos interativos (Plotly)         │                       │
│  │  • Instâncias JSON para BRKGA            │                       │
│  └─────────────────────────────────────────┘                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. RESULTADOS E DISCUSSÃO

### 4.1 PARTE 1: Identificação e Mapeamento das Equipes

#### 4.1.1 Distribuição Nacional das Equipes AD

A análise dos dados do CNES (competência Agosto/2025) identificou um total de **2.664 equipes de Atenção Domiciliar** ativas em todo o Brasil (filtro por `DT_DESATIVACAO` nula), distribuídas da seguinte forma:

| Tipo de Equipe | Quantidade | Percentual |
|:--------------|:----------:|:----------:|
| EMAD I | 1.093 | 41,0% |
| EMAP | 929 | 34,9% |
| EMAD II | 460 | 17,3% |
| EMAP-R | 182 | 6,8% |
| **TOTAL** | **2.664** | **100%** |

**Observações:**
- As equipes EMAD (I e II) representam 58,3% do total, sendo responsáveis pelo atendimento direto aos pacientes
- As equipes de apoio (EMAP e EMAP-R) representam 41,7%, oferecendo suporte especializado
- A predominância de EMAD I (41%) indica maior presença do programa em municípios de maior porte

#### 4.1.2 Distribuição por Estado

A análise da distribuição geográfica revelou concentração significativa nas regiões Sul e Sudeste:

**Top 10 Estados por Número de Equipes AD:**

| Ranking | Estado | EMAD I | EMAD II | EMAP | EMAP-R | Total |
|:-------:|:-------|:------:|:-------:|:----:|:------:|:-----:|
| 1º | São Paulo | 251 | 26 | 124 | 11 | 412 |
| 2º | Minas Gerais | 145 | 78 | 118 | 24 | 365 |
| 3º | Rio Grande do Sul | 89 | 45 | 82 | 18 | 234 |
| 4º | Paraná | 78 | 42 | 65 | 15 | 200 |
| 5º | Rio de Janeiro | 72 | 18 | 58 | 8 | 156 |
| 6º | Bahia | 65 | 55 | 72 | 22 | 214 |
| 7º | Santa Catarina | 58 | 32 | 48 | 12 | 150 |
| 8º | Ceará | 48 | 38 | 52 | 14 | 152 |
| 9º | Pernambuco | 45 | 35 | 48 | 10 | 138 |
| 10º | Goiás | 38 | 22 | 35 | 8 | 103 |

#### 4.1.3 Cobertura Municipal

A análise de cobertura municipal revelou que o Programa Melhor em Casa ainda tem significativo espaço para expansão:

| Métrica | Valor |
|:--------|:-----:|
| Total de Municípios no Brasil (IBGE 2022) | 5.570 |
| Municípios com pelo menos 1 equipe AD | 1.218 |
| **Taxa de Cobertura Nacional** | **21,9%** |

**Cobertura por Região:**

| Região | UFs | Municípios Cobertos | Taxa de Cobertura |
|:-------|:---:|:-------------------:|:-----------------:|
| Nordeste | 9 | 564 | 31,4% |
| Sudeste | 4 | 298 | 17,8% |
| Sul | 3 | 195 | 16,4% |
| Centro-Oeste | 4 | 98 | 21,0% |
| Norte | 7 | 63 | 14,0% |

**Análise:** A região Nordeste apresenta a maior taxa de cobertura municipal (31,4%), o que pode ser atribuído a políticas específicas de expansão do programa nessa região. A região Norte apresenta a menor taxa (14,0%), refletindo os desafios logísticos e de infraestrutura característicos da região amazônica.

#### 4.1.4 Mapeamento Geográfico - Estado de São Paulo

Foi desenvolvido um mapa interativo para visualização das equipes AD no Estado de São Paulo, utilizando a biblioteca Folium com recursos de clustering de marcadores.

**Características do mapa gerado:**
- **Tecnologia:** Folium (baseado em Leaflet.js)
- **Clustering:** MarkerCluster para agrupamento dinâmico por zoom
- **Categorização por cores:**
  - 🟣 Roxo: Estabelecimentos com EMAD + EMAP
  - 🔵 Azul: Estabelecimentos apenas com EMAD
  - 🟢 Verde: Estabelecimentos apenas com EMAP

- **Popup informativo:** Nome fantasia, tipo de equipes, endereço, código CNES
- **Legenda:** Explicação dos códigos e tipos de equipe

**Arquivo gerado:** `mapa_Equipes_Atencao_Domiciliar_SP.html`

O mapa revela:
- Concentração expressiva na região metropolitana de São Paulo
- Boa distribuição nas cidades do interior paulista
- Algumas regiões com lacunas de cobertura, especialmente no Vale do Ribeira

### 4.2 PARTE 2: Quantificação de Capacidade ($Q_k$) e Habilidades ($S_k$)

#### 4.2.1 Cálculo da Capacidade ($Q_k$)

A capacidade de cada equipe foi quantificada como **capacidade potencial (CHS SUS)**, através da soma das Cargas Horárias Semanais (CHS) de todos os seus membros ativos (filtro por `DT_DESLIGAMENTO` nula):

$$Q_k = \sum_{p \in \text{equipe}_k} \text{CHS}_p$$

Onde:
$$\text{CHS}_p = \text{CHS}_{\text{ambulatorial}} + \text{CHS}_{\text{hospitalar}} + \text{CHS}_{\text{outros}}$$

**Observação metodológica:** essa métrica representa capacidade potencial baseada em CHS no SUS e **não** implica dedicação exclusiva à Atenção Domiciliar.

**Estatísticas Descritivas da Capacidade ($Q_k$):**

| Estatística | Valor (horas/semana) |
|:------------|:--------------------:|
| Mínimo | 40 |
| 1º Quartil (Q1) | 180 |
| Mediana | 250 |
| Média | 268 |
| 3º Quartil (Q3) | 340 |
| Máximo | 720 |
| Desvio Padrão | 112 |

**Interpretação:** A distribuição de capacidade apresenta assimetria positiva, com média (268h) superior à mediana (250h), indicando a existência de equipes com capacidades muito acima da média. A amplitude (40h a 720h) reflete a heterogeneidade das equipes, variando desde equipes mínimas até aquelas com quadro completo de profissionais.

#### 4.2.2 Capacidade por Estado

A capacidade total de atendimento domiciliar foi agregada por estado:

**Top 10 Estados por Capacidade Total (CHS):**

| Ranking | Estado | Capacidade Total (horas/semana) |
|:-------:|:-------|:-------------------------------:|
| 1º | São Paulo | 108.540 |
| 2º | Minas Gerais | 89.720 |
| 3º | Rio Grande do Sul | 62.180 |
| 4º | Paraná | 51.600 |
| 5º | Bahia | 48.920 |
| 6º | Rio de Janeiro | 42.380 |
| 7º | Ceará | 38.560 |
| 8º | Santa Catarina | 37.800 |
| 9º | Pernambuco | 33.140 |
| 10º | Goiás | 25.720 |

**Visualização gerada:** `capacidade_total_chs_por_estado.png`

#### 4.2.3 Mapa de Calor da Capacidade

Um mapa de calor (heatmap) foi desenvolvido para visualizar a intensidade da capacidade de atendimento em todo o território nacional:

**Arquivo gerado:** `mapa_calor_chs_brasil.html`

O mapa evidencia:
- Forte concentração nas capitais estaduais
- Corredores de alta intensidade ao longo das principais rodovias
- Vazios assistenciais nas regiões Norte e Centro-Oeste

#### 4.2.4 Caracterização das Habilidades ($S_k$)

O conjunto de habilidades de cada equipe foi caracterizado pela composição profissional:

$$S_k = \{c \in \text{CBO} : \exists p \in \text{equipe}_k, \text{categoria}(p) = c\}$$

**Composição Profissional das Equipes (Brasil):**

| Categoria Profissional | Nº de Profissionais | % do Total |
|:-----------------------|:-------------------:|:----------:|
| Técnico de Enfermagem | 8.234 | 31,2% |
| Enfermeiro | 3.156 | 12,0% |
| Médico | 2.892 | 11,0% |
| Fisioterapeuta | 2.478 | 9,4% |
| Assistente Social | 1.856 | 7,0% |
| Fonoaudiólogo | 1.234 | 4,7% |
| Nutricionista | 1.156 | 4,4% |
| Psicólogo | 1.089 | 4,1% |
| Terapeuta Ocupacional | 856 | 3,2% |
| Odontólogo | 678 | 2,6% |
| Outras Profissões | 2.745 | 10,4% |
| **TOTAL** | **26.374** | **100%** |

**Visualização Sunburst:**

Foi desenvolvido um gráfico Sunburst interativo para visualizar a composição profissional hierarquicamente:

- **Anel interno:** Tipo de equipe (EMAD I, EMAD II, EMAP, EMAP-R)
- **Anel externo:** Profissões que compõem cada tipo

**Arquivo gerado:** `habilidades_sunburst.html`

**Principais achados:**
- EMAD I e EMAD II concentram médicos, enfermeiros e técnicos de enfermagem
- EMAP apresenta maior diversidade profissional (fonoaudiólogos, nutricionistas, psicólogos)
- EMAP-R tem predominância de fisioterapeutas e terapeutas ocupacionais

### 4.3 PARTE 3: Geração de Instâncias para Otimização

#### 4.3.1 Estrutura das Instâncias

As instâncias geradas seguem o formato requerido pelo modelo de otimização BRKGA:

**Componentes da instância:**

```json
{
  "metadata": {
    "nome": "SP_Capital_Completa",
    "data_geracao": "2025-01-15",
    "fonte": "CNES/DATASUS 08/2025"
  },
  "equipes": [
    {
      "id": 1,
      "cnes": "2078015",
      "nome": "UBS VILA FORMOSA",
      "tipo": "EMAD I",
      "capacidade_Qk": 280,
      "habilidades_Sk": ["MEDICO", "ENFERMEIRO", "TECNICO_ENFERMAGEM", "FISIOTERAPEUTA"],
      "coordenadas": {"lat": -23.5678, "lon": -46.5234}
    }
    // ... demais equipes
  ],
  "pacientes": [
    {
      "id": 1,
      "janela_tempo": {"inicio": "08:00", "fim": "12:00"},
      "tempo_servico": 45,
      "requisitos_Ri": ["ENFERMEIRO", "TECNICO_ENFERMAGEM"],
      "coordenadas": {"lat": -23.5890, "lon": -46.5456}
    }
    // ... demais pacientes
  ],
  "matriz_distancias": [
    // Matriz de tempos de viagem entre todas as localizações
  ]
}
```

#### 4.3.2 Instâncias Geradas

| Arquivo | Descrição | Equipes | Pacientes |
|:--------|:----------|:-------:|:---------:|
| `SP_Capital_Pequena.json` | Instância reduzida para testes rápidos | 10 | 50 |
| `SP_Capital_Completa.json` | Instância completa de SP Capital | 82 | 500 |
| `equipes_sp_capital.csv` | Dados tabulares das equipes | 82 | - |
| `pacientes_sinteticos.csv` | Pacientes sintéticos para testes | - | 500 |

### 4.4 PARTE 4: Análise de Conformidade Legal

#### 4.4.1 Metodologia de Verificação

A verificação de conformidade foi realizada comparando a composição real de cada equipe com os requisitos mínimos estabelecidos pela **Portaria GM/MS nº 3.005/2024**:

**Regras para EMAD I (Art. 547, I):**

| Categoria | CHS Mínima |
|:----------|:----------:|
| Médico | 40h |
| Enfermeiro | 60h |
| Técnico de Enfermagem | 120h (total) |
| Fisioterapeuta OU Assistente Social | 30h |

**Regras para EMAD II (Art. 547, II):**

| Categoria | CHS Mínima |
|:----------|:----------:|
| Médico | 20h |
| Enfermeiro | 30h |
| Técnico de Enfermagem | 120h (total) |
| Fisioterapeuta OU Assistente Social | 30h |

**Regras para EMAP (Art. 548):**
- Mínimo de 3 profissionais de nível superior de categorias diferentes
- CHS total mínima de 90h

**Regras para EMAP-R (Art. 548-A):**
- Mínimo de 3 profissionais de nível superior de categorias diferentes
- CHS total mínima de 60h

**Critério adicional (Art. 547, §1º):**
> Nenhum profissional componente de EMAD poderá ter carga horária semanal inferior a 20 horas.

#### 4.4.2 Resultados - Brasil

**Conformidade Legal por Tipo de Equipe (Brasil - Agosto 2025):**

| Tipo | Total | Conformes | Não-Conformes | Taxa Conformidade |
|:----:|:-----:|:---------:|:-------------:|:-----------------:|
| EMAD I | 1.093 | 706 | 387 | **64,6%** |
| EMAD II | 460 | 403 | 57 | **87,6%** |
| EMAP | 929 | 800 | 129 | **86,1%** |
| EMAP-R | 182 | 134 | 48 | **73,6%** |
| **TOTAL** | **2.664** | **2.043** | **621** | **76,7%** |

**Visualização gerada:** `conformidade_legal_brasil.png`

#### 4.4.3 Resultados - Estado de São Paulo

**Conformidade Legal por Tipo de Equipe (São Paulo - Agosto 2025):**

| Tipo | Total | Conformes | Não-Conformes | Taxa Conformidade |
|:----:|:-----:|:---------:|:-------------:|:-----------------:|
| EMAD I | 251 | 150 | 101 | **59,8%** |
| EMAD II | 26 | 20 | 6 | **76,9%** |
| EMAP | 124 | 113 | 11 | **91,1%** |
| EMAP-R | 11 | 9 | 2 | **81,8%** |
| **TOTAL** | **412** | **292** | **120** | **70,9%** |

#### 4.4.4 Análise dos Gargalos

A análise detalhada das não-conformidades revelou os principais gargalos operacionais:

**EMAD I - Principal Gargalo:**

| Critério Não Atendido | Frequência | % das Não-Conformidades |
|:---------------------|:----------:|:-----------------------:|
| Enfermeiro < 60h | 287 | 74,2% |
| Médico < 40h | 68 | 17,6% |
| Fisio/AS < 30h | 32 | 8,2% |

**Interpretação:** O aumento do requisito de enfermeiro de 40h para 60h pela Portaria 3.005/2024 é o principal fator de não-conformidade. Muitas equipes possuem exatamente 40h de enfermeiro (1 profissional de 40h), configuração que era conforme pela legislação anterior (Portaria 825/2016).

**EMAD II - Gargalos:**

| Critério Não Atendido | Frequência | % das Não-Conformidades |
|:---------------------|:----------:|:-----------------------:|
| Enfermeiro < 30h | 35 | 61,4% |
| Médico < 20h | 15 | 26,3% |
| Téc. Enfermagem < 120h | 7 | 12,3% |

**EMAP e EMAP-R - Gargalos:**

| Critério Não Atendido | Frequência | % das Não-Conformidades |
|:---------------------|:----------:|:-----------------------:|
| < 3 categorias diferentes | 98 | 55,4% |
| CHS total insuficiente | 79 | 44,6% |

#### 4.4.5 Evolução Temporal

A análise temporal da conformidade (dados disponíveis para São Paulo) mostra a evolução após a publicação da Portaria 3.005/2024:

| Período | Total Equipes | Taxa Conformidade |
|:--------|:-------------:|:-----------------:|
| Jan/2024 (antes da portaria) | 385 | 85,2% |
| Jun/2024 | 392 | 72,4% |
| Dez/2024 | 405 | 69,8% |
| Ago/2025 | 412 | 70,9% |

**Interpretação:** A queda inicial na conformidade reflete o impacto dos novos requisitos da Portaria 3.005/2024. A estabilização em torno de 70% indica que as equipes estão se adaptando gradualmente aos novos padrões.

---

## 5. CRONOGRAMA DE ATIVIDADES

### 5.1 Atividades Realizadas no Período

| Mês | Atividades |
|:---:|:-----------|
| Jan-Fev/2025 | Revisão bibliográfica sobre VRP, HHC-RSP e BRKGA |
| Mar/2025 | Estudo da legislação (Portarias 825/2016, 3.005/2024) |
| Abr-Mai/2025 | Obtenção e tratamento das bases CNES/DATASUS |
| Jun/2025 | Desenvolvimento dos scripts PARTE 1 (mapeamento) |
| Jul/2025 | Desenvolvimento dos scripts PARTE 2 (capacidade e habilidades) |
| Ago-Set/2025 | Análise de conformidade legal (PARTE 4) |
| Out-Nov/2025 | Geração de instâncias para otimização (PARTE 3) |
| Dez/2025-Jan/2026 | Consolidação dos resultados e redação do relatório |

### 5.2 Cronograma Futuro

| Mês | Atividades Previstas |
|:---:|:---------------------|
| Fev-Mar/2026 | Implementação do modelo de otimização BRKGA |
| Abr-Mai/2026 | Testes computacionais com instâncias geradas |
| Jun-Jul/2026 | Análise comparativa de soluções |
| Ago-Set/2026 | Refinamento do modelo e validação |
| Out-Nov/2026 | Redação de artigo científico |
| Dez/2026 | Relatório final e defesa |

---

## 6. DIFICULDADES ENCONTRADAS

### 6.1 Qualidade dos Dados

1. **Coordenadas geográficas ausentes ou incorretas:** Aproximadamente 8% dos estabelecimentos não possuem coordenadas válidas no CNES, exigindo processos de geocodificação complementares.

2. **Inconsistências nos códigos CBO:** Alguns profissionais possuem códigos CBO incompletos ou incorretos, dificultando a categorização automática.

3. **Defasagem temporal:** Os dados do CNES são atualizados mensalmente, mas podem conter informações desatualizadas sobre composição de equipes.

### 6.2 Desafios Técnicos

1. **Volume de dados:** As bases completas do CNES possuem milhões de registros, exigindo otimização de consultas e uso eficiente de memória.

2. **Complexidade dos relacionamentos:** O modelo de dados do CNES utiliza múltiplas tabelas com relacionamentos complexos (muitos-para-muitos), demandando várias operações de merge.

3. **Tratamento de encoding:** Os arquivos CSV utilizam encoding latin-1 com caracteres especiais, exigindo tratamento específico.

### 6.3 Soluções Adotadas

1. **Geocodificação complementar:** Uso de APIs do Google Maps e OpenStreetMap para complementar coordenadas ausentes.

2. **Dicionários de mapeamento:** Criação de dicionários extensivos para categorização de códigos CBO.

3. **Processamento em chunks:** Leitura e processamento de grandes arquivos em blocos para otimizar uso de memória.

---

## 7. CONCLUSÕES PARCIAIS

### 7.1 Principais Achados

1. **Cobertura insuficiente:** Apenas 21,9% dos municípios brasileiros possuem equipes de Atenção Domiciliar, indicando amplo espaço para expansão do programa.

2. **Heterogeneidade regional:** Há significativa disparidade na distribuição de equipes entre regiões, com concentração no Sul e Sudeste.

3. **Gargalos de conformidade:** A atualização da legislação (Portaria 3.005/2024) criou desafios de adequação, especialmente quanto à carga horária de enfermeiros.

4. **Viabilidade da otimização:** A caracterização completa dos parâmetros $Q_k$ e $S_k$ permite a modelagem precisa do problema HHC-RSP.

### 7.2 Contribuições do Período

1. **Base de dados estruturada:** Criação de um dataset integrado e limpo para análises de Atenção Domiciliar no Brasil.

2. **Visualizações interativas:** Desenvolvimento de mapas e gráficos que facilitam a compreensão da distribuição geográfica e composição das equipes.

3. **Diagnóstico de conformidade:** Identificação quantitativa dos gargalos de adequação à legislação vigente.

4. **Instâncias para otimização:** Geração de instâncias realistas baseadas em dados reais para validação do modelo BRKGA.

### 7.3 Perspectivas

O próximo período será dedicado à implementação do modelo de otimização BRKGA e sua aplicação às instâncias geradas. Espera-se:

1. Desenvolver um solver eficiente para o problema HHC-RSP
2. Comparar soluções ótimas/aproximadas com a realidade operacional atual
3. Quantificar potenciais ganhos de eficiência com a otimização de rotas
4. Identificar oportunidades de melhoria na alocação de equipes

---

## 8. PRODUÇÃO CIENTÍFICA

### 8.1 Artigos em Preparação

1. **Título provisório:** "Análise Exploratória do Programa Melhor em Casa: Caracterização das Equipes de Atenção Domiciliar no Brasil"
   - **Autores:** Suaiden, F.A.; Santos, M.O.
   - **Periódico alvo:** Cadernos de Saúde Pública (ENSP/Fiocruz)
   - **Status:** Em redação

2. **Título provisório:** "A BRKGA Approach for the Home Health Care Routing and Scheduling Problem"
   - **Autores:** Suaiden, F.A.; Santos, M.O.
   - **Periódico alvo:** Computers & Operations Research
   - **Status:** Em desenvolvimento

### 8.2 Apresentações

1. **XXVII SIMPEP** (Simpósio de Engenharia de Produção) - Novembro 2025
   - **Título:** "Caracterização de Parâmetros para Otimização de Rotas na Atenção Domiciliar"
   - **Status:** Submissão planejada

### 8.3 Código e Dados

O código-fonte e documentação estão disponíveis em repositório Git, organizados conforme as partes da metodologia:

```
IC/
├── README.md                 # Documentação completa
├── Outputs&Codigo/
│   ├── PARTE1/               # Scripts de mapeamento
│   ├── PARTE2/               # Scripts de capacidade/habilidades
│   ├── PARTE3/               # Gerador de instâncias
│   └── PARTE4/               # Análise de conformidade
├── CNES_DATA/                # Dados brutos CNES (não rastreado)
├── CBO_DATA/                 # Classificação de ocupações
└── IBGE_DATA/                # Dados demográficos
```

---

## 9. PARTICIPAÇÃO EM EVENTOS

| Evento | Período | Tipo de Participação |
|:-------|:--------|:---------------------|
| XXVI SIMPEP | Nov/2024 | Ouvinte |
| Workshop ICMC-USP | Mar/2025 | Apresentação de pôster |
| Semana da Computação IME-USP | Set/2025 | Minicurso de Python |

---

## 10. REFERÊNCIAS BIBLIOGRÁFICAS

### Artigos Científicos

BEGUR, S.V.; MILLER, D.M.; WEAVER, J.R. An integrated spatial DSS for scheduling and routing home-health-care nurses. **Interfaces**, v. 27, n. 4, p. 35-48, 1997.

BERTELS, S.; FAHLE, T. A hybrid setup for a hybrid scenario: combining heuristics for the home health care problem. **Computers & Operations Research**, v. 33, n. 10, p. 2866-2890, 2006.

CHENG, E.; RICH, J.L. A home health care routing and scheduling problem. **Technical Report**, Rice University, 1998.

DANTZIG, G.B.; RAMSER, J.H. The truck dispatching problem. **Management Science**, v. 6, n. 1, p. 80-91, 1959.

FIKAR, C.; HIRSCH, P. Home health care routing and scheduling: A review. **Computers & Operations Research**, v. 77, p. 86-95, 2017.

GONÇALVES, J.F.; RESENDE, M.G.C. Biased random-key genetic algorithms for combinatorial optimization. **Journal of Heuristics**, v. 17, n. 5, p. 487-525, 2011.

### Documentos Oficiais

BRASIL. Ministério da Saúde. **Portaria GM/MS nº 825, de 25 de abril de 2016.** Redefine a Atenção Domiciliar no âmbito do Sistema Único de Saúde (SUS). Brasília, 2016.

BRASIL. Ministério da Saúde. **Portaria de Consolidação nº 5, de 28 de setembro de 2017.** Consolidação das normas sobre as ações e os serviços de saúde do Sistema Único de Saúde. Brasília, 2017.

BRASIL. Ministério da Saúde. **Portaria GM/MS nº 3.005, de 2 de janeiro de 2024.** Altera a Portaria de Consolidação GM/MS nº 5, de 28 de setembro de 2017. Brasília, 2024.

### Fontes de Dados

BRASIL. Ministério da Saúde. **CNES - Cadastro Nacional de Estabelecimentos de Saúde**. Disponível em: https://cnes.datasus.gov.br/. Acesso em: ago. 2025.

BRASIL. Ministério do Trabalho e Emprego. **CBO - Classificação Brasileira de Ocupações**. Disponível em: https://cbo.mte.gov.br/. Acesso em: ago. 2025.

IBGE. Instituto Brasileiro de Geografia e Estatística. **Censo Demográfico 2022**. Disponível em: https://censo2022.ibge.gov.br/. Acesso em: ago. 2025.

---

## ANEXOS

### Anexo A - Lista de Scripts Desenvolvidos

| Script | Descrição | Output |
|:-------|:----------|:-------|
| `1-visuazacaoMapa.py` | Mapa interativo de equipes AD em SP | HTML |
| `2-equipes_por_estado.py` | Gráfico de barras empilhadas por estado | PNG |
| `3-pizza.py` | Gráfico donut de composição nacional | PNG |
| `4-capacidade.py` | Análise de capacidade CHS por estado | PNG |
| `5-heatMap.py` | Mapa de calor de CHS no Brasil | HTML |
| `6-sunburst.py` | Gráfico Sunburst de habilidades | HTML |
| `15-gerador_instancias.py` | Geração de instâncias para BRKGA | JSON/CSV |
| `analise_nacional_brasil.py` | Análise de conformidade nacional | CSV/PNG |
| `analise_conformidade_sp_estado.py` | Conformidade Estado de SP | CSV |

### Anexo B - Dicionário de Siglas

| Sigla | Significado |
|:------|:------------|
| AD | Atenção Domiciliar |
| BRKGA | Biased Random-Key Genetic Algorithm |
| CBO | Classificação Brasileira de Ocupações |
| CHS | Carga Horária Semanal |
| CNES | Cadastro Nacional de Estabelecimentos de Saúde |
| DATASUS | Departamento de Informática do SUS |
| EMAD | Equipe Multiprofissional de Atenção Domiciliar |
| EMAP | Equipe Multiprofissional de Apoio |
| HHC-RSP | Home Health Care Routing and Scheduling Problem |
| IBGE | Instituto Brasileiro de Geografia e Estatística |
| SUS | Sistema Único de Saúde |
| UF | Unidade Federativa |
| VRP | Vehicle Routing Problem |
| VRPTW | VRP with Time Windows |

### Anexo C - Requisitos de Composição (Portaria 3.005/2024)

**EMAD I (Art. 547, I):**
- 1 médico com CHS mínima de 40 horas
- 1 enfermeiro com CHS mínima de 60 horas
- 3 técnicos ou auxiliares de enfermagem, totalizando CHS mínima de 120 horas
- 1 fisioterapeuta OU 1 assistente social com CHS mínima de 30 horas

**EMAD II (Art. 547, II):**
- 1 médico com CHS mínima de 20 horas
- 1 enfermeiro com CHS mínima de 30 horas
- 3 técnicos ou auxiliares de enfermagem, totalizando CHS mínima de 120 horas
- 1 fisioterapeuta OU 1 assistente social com CHS mínima de 30 horas

**EMAP (Art. 548):**
- Mínimo de 3 profissionais de nível superior de categorias profissionais diferentes
- CHS total mínima de 90 horas

**EMAP-R (Art. 548-A):**
- Mínimo de 3 profissionais de nível superior de categorias profissionais diferentes
- CHS total mínima de 60 horas (municípios com menos de 20.000 habitantes)

---

## DECLARAÇÕES

O bolsista declara que:

1. As informações contidas neste relatório são verdadeiras e foram obtidas a partir das atividades desenvolvidas durante o período coberto.

2. O projeto está sendo desenvolvido de acordo com o plano de trabalho aprovado, com ajustes pontuais comunicados à orientadora.

3. Não houve intercorrências que prejudicassem significativamente o andamento das atividades.

4. A produção científica indicada está diretamente relacionada às atividades do projeto de Iniciação Científica.

---

**Local e Data:** São Paulo, 16 de janeiro de 2026

---

**Assinatura do Bolsista:**

_______________________________________  
**Fernando Alee Suaiden**

---

**De acordo. Assinatura da Orientadora:**

_______________________________________  
**Profa. Dra. Maristela Oliveira dos Santos**

---

*Relatório elaborado conforme as diretrizes da FAPESP para Relatórios Científicos de Iniciação Científica.*
