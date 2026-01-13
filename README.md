# Otimização de Rotas de Atenção Domiciliar (HHC-RSP)

> **Projeto de Iniciação Científica (FAPESP)**  
> Análise Exploratória de Dados (AED) aplicada ao programa "Melhor em Casa" usando dados do CNES/DATASUS.

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
├── CNES_DATA/                       # Dados brutos do CNES/DATASUS (não rastreado)
│   ├── tbEstabelecimento202508.csv
│   ├── tbEquipe202508.csv
│   ├── rlEstabEquipeProf202508.csv
│   ├── tbCargaHorariaSus202508.csv
│   └── ...
├── CBO_DATA/                        # Classificação Brasileira de Ocupações (não rastreado)
│   ├── CBO2002 - Ocupacao.csv
│   ├── CBO2002 - Familia.csv
│   └── ...
├── IBGE_DATA/                       # Dados do Censo 2022 (não rastreado)
│   └── ...
├── Outputs&Codigo/                  # Scripts e visualizações
│   ├── PARTE1/                      # Mapeamento de Equipes
│   ├── PARTE2/                      # Capacidade e Habilidades
│   ├── PARTE3/                      # Análise de Demanda
│   └── PARTE4/                      # Análise de Saturação
└── README.md
```

> **Nota:** As pastas de dados (`CNES_DATA/`, `CBO_DATA/`, `IBGE_DATA/`) não estão rastreadas no repositório devido ao tamanho dos arquivos. Para reproduzir as análises, faça o download das bases nas fontes indicadas na seção [Fontes de Dados](#fontes-de-dados).

---

## Metodologia

### PARTE 1: Identificação e Mapeamento das Equipes

Esta fase identifica a localização geográfica das equipes do programa "Melhor em Casa" no estado de São Paulo, permitindo visualizar a distribuição espacial dos depots (bases de partida) e a cobertura por tipo de equipe.

#### 1-visuazacaoMapa.py

**Arquivo:** [Outputs&Codigo/PARTE1/1-visuazacaoMapa.py](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py)  
**Output:** `mapa_Equipes_Atencao_Domiciliar_SP.html`

Este script gera um mapa interativo das equipes de Atenção Domiciliar no estado de São Paulo.

**Etapas do processamento:**

1. **Carregamento dos dados** ([linhas 5-9](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py#L5-L9)): Carrega as tabelas `tbEstabelecimento` e `tbEquipe` do CNES.

2. **Identificação das equipes** ([linhas 11-17](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py#L11-L17)): Define os códigos de equipe relevantes e cria conjuntos de CNES únicos para cada categoria:
   - Atendimento: EMAD I (22) e EMAD II (46)
   - Apoio: EMAP (23) e EMAP-R (77)

3. **Filtro geográfico para São Paulo** ([linhas 19-21](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py#L19-L21)): Aplica o filtro `CO_ESTADO_GESTOR = '35'` (código IBGE de SP).

4. **Tratamento de coordenadas** ([linhas 23-27](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py#L23-L27)): Converte vírgulas para pontos decimais e remove registros com coordenadas nulas ou zeradas.

5. **Geração do mapa** ([linhas 31-57](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py#L31-L57)): Classificação por categoria, criação do mapa Folium com MarkerCluster e popups.

6. **Legenda HTML** ([linhas 59-76](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py#L59-L76)): Adiciona legenda fixa explicando a codificação de cores.

---

#### 2-equipes_por_estado.py

**Arquivo:** [Outputs&Codigo/PARTE1/2-equipes_por_estado.py](Outputs%26Codigo/PARTE1/2-equipes_por_estado.py)  
**Output:** `distribuicao_equipes_por_estado_empilhado.png`

Este script gera um gráfico de barras empilhadas mostrando a distribuição de equipes de Atenção Domiciliar por estado.

**Etapas do processamento:**

1. **Dicionários de mapeamento** ([linhas 11-24](Outputs%26Codigo/PARTE1/2-equipes_por_estado.py#L11-L24)): Define:
   - `MAP_EQUIPES`: Traduz códigos (22, 46, 23, 77) para nomes (EMAD I, EMAD II, EMAP, EMAP-R)
   - `IBGE_UF_MAP`: Converte códigos IBGE para siglas dos estados

2. **Carregamento e merge** ([linhas 27-55](Outputs%26Codigo/PARTE1/2-equipes_por_estado.py#L27-L55)): Carrega dados CNES, filtra equipes relevantes e junta com estabelecimentos.

3. **Tabela de contingência** ([linhas 57-68](Outputs%26Codigo/PARTE1/2-equipes_por_estado.py#L57-L68)): Usa `pd.crosstab` para criar matriz Estados x Tipos de Equipe, ordenada por total.

4. **Gráfico de barras** ([linhas 70-102](Outputs%26Codigo/PARTE1/2-equipes_por_estado.py#L70-L102)): Gera barras empilhadas do Top 15 estados com legenda detalhada.

---

#### 3-pizza.py

**Arquivo:** [Outputs&Codigo/PARTE1/3-pizza.py](Outputs%26Codigo/PARTE1/3-pizza.py)  
**Output:** `composicao_nacional_pizza.png`

Este script gera um gráfico de pizza (donut) mostrando a composição nacional das equipes de Atenção Domiciliar.

**Etapas do processamento:**

1. **Dicionários de mapeamento** ([linhas 10-16](Outputs%26Codigo/PARTE1/3-pizza.py#L10-L16)): Define `MAP_EQUIPES` para tradução dos códigos.

2. **Carregamento e filtragem** ([linhas 19-30](Outputs%26Codigo/PARTE1/3-pizza.py#L19-L30)): Carrega dados CNES e filtra equipes relevantes.

3. **Gráfico donut** ([linhas 32-73](Outputs%26Codigo/PARTE1/3-pizza.py#L32-L73)): Cria pizza com círculo branco central para efeito visual de rosquinha.

---

### PARTE 2: Quantificação de Capacidade ($Q_k$) e Habilidades ($S_k$)

Esta fase extrai os parâmetros de capacidade (carga horária semanal disponível) e habilidades (composição profissional) de cada equipe, informações essenciais para a modelagem do problema de otimização de rotas.

#### 4-capacidade.py

**Arquivo:** [Outputs&Codigo/PARTE2/4-capacidade.py](Outputs%26Codigo/PARTE2/4-capacidade.py)  
**Outputs:** `capacidade_total_chs_por_estado.png`, `distribuicao_capacidade_Qk_histograma.png`

Este script calcula a capacidade de atendimento ($Q_k$) das equipes usando a Carga Horária Semanal (CHS).

**Etapas do processamento:**

1. **Carregamento de 4 bases** ([linhas 26-49](Outputs%26Codigo/PARTE2/4-capacidade.py#L26-L49)): 
   - `tbEstabelecimento`: para obter UF
   - `tbEquipe`: para filtrar equipes AD
   - `rlEstabEquipeProf`: tabela-ponte equipe-profissional
   - `tbCargaHorariaSus`: carga horária de cada profissional

2. **Merge encadeado** ([linhas 50-68](Outputs%26Codigo/PARTE2/4-capacidade.py#L50-L68)): Inner join para obter apenas profissionais que estão em equipes de AD.

3. **Cálculo da CHS individual** ([linhas 69-79](Outputs%26Codigo/PARTE2/4-capacidade.py#L69-L79)):
   ```
   CHS_PROFISSIONAL_TOTAL = Ambulatorial + Hospitalar + Outros
   ```

4. **Agregação por equipe** ([linhas 80-84](Outputs%26Codigo/PARTE2/4-capacidade.py#L80-L84)): Agrupa por `CO_UNIDADE` + `SEQ_EQUIPE` (identificador único de equipe) e soma as CHS de todos os membros para obter $Q_k$.

5. **Gráfico de capacidade por estado** ([linhas 103-123](Outputs%26Codigo/PARTE2/4-capacidade.py#L103-L123)): Barras horizontais com Top 15 estados, valores formatados em milhares (k).

6. **Histograma de distribuição** ([linhas 125-152](Outputs%26Codigo/PARTE2/4-capacidade.py#L125-L152)): Mostra a distribuição de $Q_k$ entre as equipes com linha de média.

---

#### 5-heatMap.py

**Arquivo:** [Outputs&Codigo/PARTE2/5-heatMap.py](Outputs%26Codigo/PARTE2/5-heatMap.py)  
**Output:** `mapa_calor_chs_brasil.html`

Este script gera um mapa de calor interativo do Brasil mostrando a intensidade da capacidade de Atenção Domiciliar.

**Etapas do processamento:**

1. **Carregamento com coordenadas** ([linhas 19-44](Outputs%26Codigo/PARTE2/5-heatMap.py#L19-L44)): Carrega `NU_LATITUDE` e `NU_LONGITUDE` da tabela de estabelecimentos.

2. **Cálculo da CHS** ([linhas 62-68](Outputs%26Codigo/PARTE2/5-heatMap.py#L62-L68)): Soma das cargas horárias (Ambulatorial + Hospitalar + Outros).

3. **Agregação por estabelecimento** ([linhas 70-74](Outputs%26Codigo/PARTE2/5-heatMap.py#L70-L74)): Agrupa por `CO_UNIDADE` e soma a CHS total.

4. **Preparação de dados** ([linhas 84-86](Outputs%26Codigo/PARTE2/5-heatMap.py#L84-L86)): Limpa coordenadas e formata como lista de triplas `[lat, long, peso]`.

5. **Mapa de calor** ([linhas 88-103](Outputs%26Codigo/PARTE2/5-heatMap.py#L88-L103)): Centraliza no Brasil e adiciona camada HeatMap.

---

#### 6-sunburst.py

**Arquivo:** [Outputs&Codigo/PARTE2/6-sunburst.py](Outputs%26Codigo/PARTE2/6-sunburst.py)  
**Output:** `habilidades_sunburst.html`

Este script gera um gráfico Sunburst interativo que decompõe a composição da força de trabalho ($S_k$) por tipo de equipe.

**Etapas do processamento:**

1. **Carregamento de 5 bases** ([linhas 22-45](Outputs%26Codigo/PARTE2/6-sunburst.py#L22-L45)): Adiciona `CBO2002 - Ocupacao.csv` como dicionário de profissões.

2. **Merge com tradução CBO** ([linhas 46-62](Outputs%26Codigo/PARTE2/6-sunburst.py#L46-L62)): Conecta códigos CBO aos nomes legíveis das profissões.

3. **Agregação de profissões minoritárias** ([linhas 76-83](Outputs%26Codigo/PARTE2/6-sunburst.py#L76-L83)): Profissões com menos de 0.5% do total são agrupadas como "Outras Profissões".

4. **Gráfico Sunburst** ([linhas 85-127](Outputs%26Codigo/PARTE2/6-sunburst.py#L85-L127)): Hierarquia de dois níveis:
   - Anel interno: Tipo de equipe (EMAD I, EMAD II, EMAP, EMAP-R)
   - Anel externo: Profissões que compõem cada tipo

---

### PARTE 3: Análise de Demanda (Censo 2022)

Esta fase utiliza dados do Censo Demográfico 2022 para mapear a demanda potencial por atenção domiciliar, identificando a concentração de população idosa (60+) por setor censitário em São Paulo.

> ⚠️ **ANÁLISE CRÍTICA**: A população idosa (60+) é um **proxy** para demanda de AD, **não a demanda real**. Veja seção [Limitações Metodológicas](#limitações-metodológicas-da-estimativa-de-demanda) abaixo.

#### 10-demanda_censo2022_real.py

**Arquivo:** [Outputs&Codigo/PARTE3/10-demanda_censo2022_real.py](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py)  
**Output:** `mapa_demanda_idosos_sp_censo2022.html`

Este script utiliza dados reais do Censo 2022 para calcular a demanda de idosos por setor censitário.

**Variáveis do Censo utilizadas** ([linhas 8-13](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py#L8-L13)):
- V01006: Quantidade de moradores (total)
- V01040: 60 a 69 anos
- V01041: 70 anos ou mais

**Etapas do processamento:**

1. **Download automático** ([função baixar_arquivo, linhas 38-66](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py#L38-L66)): Baixa e extrai arquivos ZIP do FTP do IBGE se não existirem localmente.

2. **Carregamento de dados demográficos** ([função carregar_dados_demografia, linhas 68-86](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py#L68-L86)): Lê o CSV de agregados por setores censitários do Brasil.

3. **Carregamento da malha de SP** ([função carregar_malha_sp, linhas 89-123](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py#L89-L123)): Lê o shapefile com as geometrias dos setores censitários de São Paulo.

4. **Filtro para SP Capital** ([função filtrar_sp_capital, linhas 125-157](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py#L125-L157)): Usa código do município 3550308 para filtrar apenas a capital.

5. **Cálculo da demanda** ([função calcular_demanda_idosos, linhas 159-237](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py#L159-L237)):
   ```
   Demanda = pop_60_69 + pop_70_mais
   ```
   Trata valores sigilosos ("X") do IBGE como zero.

6. **Mapa de calor** ([função gerar_mapa_calor, linhas 239-300](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py#L239-L300)): Gera visualização da concentração de idosos por setor.

#### 11-demanda_corrigida.py

**Arquivo:** [Outputs&Codigo/PARTE3/11-demanda_corrigida.py](Outputs%26Codigo/PARTE3/11-demanda_corrigida.py)  
**Outputs:** `comparacao_metodologias_demanda.png`, `mapa_demanda_corrigida_moderado.html`

Este script aplica uma **metodologia corrigida** para estimar a demanda real de Atenção Domiciliar, considerando:

1. **Taxa de Elegibilidade** ([linhas 50-55](Outputs%26Codigo/PARTE3/11-demanda_corrigida.py#L50-L55)):
   - Conservador: 2% dos idosos
   - Moderado: 3.5% dos idosos  
   - Otimista: 5% dos idosos

2. **Ponderação por Idade** ([linhas 61-64](Outputs%26Codigo/PARTE3/11-demanda_corrigida.py#L61-L64)):
   - 60-69 anos: peso 1.0
   - 70+ anos: peso 2.5 (maior probabilidade de necessitar AD)

**Fórmula:**
```
Demanda_Corrigida = (pop_60_69 × 1.0 + pop_70_mais × 2.5) × taxa_elegibilidade
```

**Resultados para SP Capital:**
| Cenário | Taxa | Demanda Estimada |
|---------|------|------------------|
| Original (script 10) | 100% | 2.020.436 |
| Conservador | 2% | 68.126 |
| **Moderado** | 3.5% | **119.221** |
| Otimista | 5% | 170.316 |

> O método original **superestima a demanda em ~17x** em relação ao cenário moderado.

---

### Limitações Metodológicas da Estimativa de Demanda

A estimativa de demanda baseada em população idosa possui **limitações importantes** que devem ser consideradas:

| Suposição | Problema | Impacto |
|-----------|----------|---------|
| Todo idoso 60+ precisa de AD | **FALSO** - Apenas 2-5% necessitam | Superestimação em 20-50x |
| Idade é único preditor | **INCOMPLETO** - Ignora condições crônicas e dependência funcional | Distorce distribuição geográfica |
| Peso igual 60-69 e 70+ | **FALSO** - Necessidade aumenta exponencialmente após 80 anos | Subestima áreas com idosos muito velhos |
| Valores "X" = 0 | **VIÉS** - Setores pequenos perdem dados | Introduz viés sistemático |

**Critérios reais de elegibilidade para AD** (Portaria GM/MS 825/2016):
- Condição clínica que demanda cuidados contínuos
- Dependência funcional (AVDs)
- Estabilidade clínica
- Presença de cuidador

**Fontes de dados ideais** (não disponíveis neste projeto):
- SIA (Sistema de Informação Ambulatorial) - Produção real de procedimentos AD
- SISAB (e-SUS Atenção Básica) - Atendimentos na atenção primária
- SIH (Sistema de Internações Hospitalares) - Altas hospitalares elegíveis

---

### PARTE 4: Análise de Saturação e Conformidade Legal

Esta fase avalia se as equipes atendem aos requisitos mínimos de composição definidos pela legislação vigente, identificando o índice de conformidade e possíveis gargalos operacionais.

#### 8-analise_saturacao_ad.py

**Arquivo:** [Outputs&Codigo/PARTE4/8-analise_saturacao_ad.py](Outputs%26Codigo/PARTE4/8-analise_saturacao_ad.py)  
**Outputs:** Dashboards de conformidade

Este script analisa se as equipes atendem aos requisitos normativos da Portaria GM/MS 3.005/2024.

**Base legal** ([linhas 8-45](Outputs%26Codigo/PARTE4/8-analise_saturacao_ad.py#L8-L45)): 
- Portaria de Consolidação GM/MS nº 5/2017
- Portaria GM/MS nº 3.005 de 02/05/2024

**Regras de completude** ([linhas 85-126](Outputs%26Codigo/PARTE4/8-analise_saturacao_ad.py#L85-L126)):

| Tipo | Médico | Enfermeiro | Téc. Enfermagem | Fisio/AS |
|:---:|:---:|:---:|:---:|:---:|
| EMAD I | ≥40h | ≥60h | ≥120h | ≥30h |
| EMAD II | ≥20h | ≥30h | ≥120h | ≥30h |
| EMAP | - | - | - | 3+ prof. NS, ≥90h |
| EMAP-R | - | ≥30h | - | 3+ prof. NS, ≥60h |

**Categorização de CBOs** ([função categorizar_cbo, linhas 153-199](Outputs%26Codigo/PARTE4/8-analise_saturacao_ad.py#L153-L199)): Função que categoriza códigos CBO em classes profissionais:
- Prefixo 2251/2252/2253 → MEDICO
- Prefixo 2235 → ENFERMEIRO
- Prefixo 3222 → TECNICO_ENFERMAGEM
- E assim por diante...

**Cálculo da CHS Real** ([linhas 270-285](Outputs%26Codigo/PARTE4/8-analise_saturacao_ad.py#L270-L285)):
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
| IBGE - Códigos dos Municípios | [Explicação](https://www.ibge.gov.br/explica/codigos-dos-municipios.php) |

### Legislação

| Documento | Descrição | Link |
|:---|:---|:---|
| Portaria GM/MS nº 825/2016 | Redefine a Atenção Domiciliar no âmbito do SUS | [Texto](https://bvsms.saude.gov.br/bvs/saudelegis/gm/2016/prt0825_25_04_2016.html) |
| Portaria de Consolidação nº 5/2017 | Consolidação das normas sobre ações e serviços de saúde | [Texto](https://bvsms.saude.gov.br/bvs/saudelegis/gm/2017/prc0005_03_10_2017.html) |
| Portaria GM/MS nº 3.005/2024 | Atualização dos requisitos de composição das equipes AD | [Texto](https://www.gov.br/saude/pt-br/composicao/saes/melhor-em-casa/legislacao/portaria-gm-ms-no-3-005-de-2-de-janeiro-de-2024) |

---

## Autores

- **Orientando:** Fernando Alee Suaiden
- **Orientadora:** Maristela Oliveira dos Santos
- **Instituição:** Universidade de São Paulo (USP)
- **Financiamento:** FAPESP
