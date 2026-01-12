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
  - [PARTE 2: Quantificação de Capacidade e Habilidades](#parte-2-quantificação-de-capacidade-qk-e-habilidades-sk)
  - [PARTE 3: Análise de Demanda (Censo 2022)](#parte-3-análise-de-demanda-censo-2022)
  - [PARTE 4: Análise de Saturação e Conformidade Legal](#parte-4-análise-de-saturação-e-conformidade-legal)
- [Principais Descobertas](#principais-descobertas)
- [Visualizações Geradas](#visualizações-geradas)
- [Como Executar](#como-executar)
- [Controle de Versão (Git)](#controle-de-versão-git)
- [Referências Legais](#referências-legais)
- [Licença](#licença)

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

| Arquivo | Descrição | Chaves Principais |
|:---|:---|:---|
| `tbEstabelecimento202508.csv` | Cadastro de clínicas, hospitais e unidades de saúde | `CO_UNIDADE`, `NU_LATITUDE`, `NU_LONGITUDE`, `CO_ESTADO_GESTOR` |
| `tbEquipe202508.csv` | Vínculo das equipes de saúde aos estabelecimentos | `CO_UNIDADE`, `SEQ_EQUIPE`, `TP_EQUIPE` |
| `rlEstabEquipeProf202508.csv` | Tabela-ponte: liga profissionais às equipes | `SEQ_EQUIPE`, `CO_PROFISSIONAL_SUS`, `CO_CBO` |
| `tbCargaHorariaSus202508.csv` | Carga horária de cada profissional | `CO_PROFISSIONAL_SUS`, `CO_CBO`, `QT_CARGA_HORARIA_*` |

### CBO - Classificação Brasileira de Ocupações

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

A filtragem foi realizada com base na documentação oficial e **Portaria GM/MS nº 3.005/2024** para garantir rastreabilidade:

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

> **Pergunta-guia:** *"Onde estão localizados os pontos de partida das equipes do programa 'Melhor em Casa' em São Paulo?"*

#### Scripts

| Script | Descrição | Output |
|:---|:---|:---|
| [1-visuazacaoMapa.py](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py) | Mapa interativo das equipes AD em SP | `mapa_Equipes_Atencao_Domiciliar_SP.html` |
| [2-equipes_por_estado.py](Outputs%26Codigo/PARTE1/2-equipes_por_estado.py) | Distribuição por estado (barras empilhadas) | `distribuicao_equipes_por_estado_empilhado.png` |
| [3-pizza.py](Outputs%26Codigo/PARTE1/3-pizza.py) | Composição nacional (gráfico donut) | `composicao_nacional_pizza.png` |

#### Fluxo de Dados

```mermaid
graph LR
    A[tbEstabelecimento] -->|CO_UNIDADE| C{Merge}
    B[tbEquipe] -->|CO_UNIDADE| C
    C --> D[Filtro: TP_EQUIPE ∈ {22,46,23,77}]
    D --> E[Filtro: CO_ESTADO_GESTOR = 35]
    E --> F[Limpeza: LAT/LONG]
    F --> G[Mapa Folium]
```

#### Legenda de Marcadores do Mapa

| Cor | Significado |
|:---:|:---|
| Azul | Estabelecimento com apenas equipes de **Atendimento** (EMAD) |
| Verde | Estabelecimento com apenas equipes de **Apoio** (EMAP) |
| Roxo | Estabelecimento com **ambos** os tipos de equipe |

#### Detalhes Técnicos

**[1-visuazacaoMapa.py](Outputs%26Codigo/PARTE1/1-visuazacaoMapa.py):**
- Carrega as bases `tbEstabelecimento` e `tbEquipe`
- Separa equipes de atendimento (EMAD I=22, EMAD II=46) e apoio (EMAP=23, EMAP-R=77)
- Aplica filtro geográfico `CO_ESTADO_GESTOR = '35'` (São Paulo)
- Trata coordenadas (conversão vírgula para ponto, remoção de nulos/zeros)
- Classifica estabelecimentos: apenas atendimento, apenas apoio, ou ambos
- Gera mapa Folium com MarkerCluster e legenda HTML

**[2-equipes_por_estado.py](Outputs%26Codigo/PARTE1/2-equipes_por_estado.py):**
- Otimiza leitura com `usecols`
- Mapeia códigos de equipe para nomes legíveis
- Converte códigos UF IBGE para siglas dos estados
- Gera gráfico de barras empilhadas dos Top 15 estados

**[3-pizza.py](Outputs%26Codigo/PARTE1/3-pizza.py):**
- Combina gráfico de barras + pizza donut
- Calcula contagem nacional por tipo de equipe
- Estilo "donut" com círculo central branco

---

### PARTE 2: Quantificação de Capacidade ($Q_k$) e Habilidades ($S_k$)

> **Pergunta-guia:** *"Qual a capacidade de trabalho e quais as habilidades de cada equipe?"*

#### Scripts

| Script | Descrição | Output |
|:---|:---|:---|
| [4-capacidade.py](Outputs%26Codigo/PARTE2/4-capacidade.py) | Cálculo de $Q_k$ por equipe | `capacidade_total_chs_por_estado.png`, `distribuicao_capacidade_Qk_histograma.png` |
| [5-heatMap.py](Outputs%26Codigo/PARTE2/5-heatMap.py) | Mapa de calor de capacidade (Brasil) | `mapa_calor_chs_brasil.html` |
| [6-sunburst.py](Outputs%26Codigo/PARTE2/6-sunburst.py) | Decomposição hierárquica de habilidades | `habilidades_sunburst.html` |

#### Cálculo da Capacidade ($Q_k$)

A capacidade de cada equipe é calculada através do cruzamento de 4 tabelas:

```mermaid
graph TD
    A[tbEquipe<br/>TP_EQUIPE ∈ {22,46,23,77}] -->|SEQ_EQUIPE, CO_UNIDADE| B[rlEstabEquipeProf]
    B -->|CO_PROFISSIONAL_SUS, CO_UNIDADE, CO_CBO| C[tbCargaHorariaSus]
    C --> D[Cálculo Individual]
    D --> E[Agregação por Equipe]
    E --> F[Qk = Capacidade Total]
```

**Fórmula de Carga Horária Individual:**
$$CHS_{individual} = QT\_CARGA\_HORARIA\_AMBULATORIAL + QT\_CARGA\_HORARIA\_OUTROS + QT\_CARGA\_HOR\_HOSP\_SUS$$

**Capacidade da Equipe:**
$$Q_k = \sum_{i \in Equipe_k} CHS_{individual_i}$$

#### Cálculo das Habilidades ($S_k$)

As habilidades são obtidas através da tradução dos códigos CBO:

```mermaid
graph LR
    A[CO_CBO do Profissional] -->|Merge| B[CBO2002 - Ocupacao.csv]
    B --> C[TITULO = Nome da Profissão]
    C --> D[Agregação por Equipe]
    D --> E[Sk = Médico, Enfermeiro, Fisio, ...]
```

#### Detalhes Técnicos

**[4-capacidade.py](Outputs%26Codigo/PARTE2/4-capacidade.py):**
- Carrega 4 bases: estabelecimentos, equipes, profissionais por equipe, carga horária
- Merge encadeado: Equipes → Profissionais → Carga Horária (chave tripla)
- Chave composta: `(CO_UNIDADE, CO_PROFISSIONAL_SUS, CO_CBO)`
- Trata valores nulos com `fillna(0)`
- Gera histograma para visualizar distribuição de capacidades

**[5-heatMap.py](Outputs%26Codigo/PARTE2/5-heatMap.py):**
- Agregação por estabelecimento (não por equipe)
- Carrega coordenadas geográficas
- Usa plugin `HeatMap` do Folium
- Parâmetros ajustados: radius, blur, min_opacity

**[6-sunburst.py](Outputs%26Codigo/PARTE2/6-sunburst.py):**
- Adiciona 5ª fonte: `CBO2002 - Ocupacao.csv`
- Traduz códigos CBO para profissões legíveis
- Agrega profissões minoritárias (<0.5%) em "Outras Profissões"
- Gráfico Sunburst (Plotly): anel interno = tipo equipe, anel externo = profissões

---

### PARTE 3: Análise de Demanda (Censo 2022)

> **Pergunta-guia:** *"Onde estão os pacientes que necessitam de atenção domiciliar?"*

#### Scripts

| Script | Descrição | Output |
|:---|:---|:---|
| [10-demanda_censo2022_real.py](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py) | Demanda de idosos por setor censitário | `mapa_demanda_idosos_sp_censo2022.html` |

#### Variáveis do Censo Utilizadas

| Código | Descrição |
|:---|:---|
| V01006 | Quantidade de moradores (total) |
| V01040 | Moradores com 60 a 69 anos |
| V01041 | Moradores com 70 anos ou mais |

**Demanda por setor censitário:**
$$D_i = V01040_i + V01041_i$$

#### Detalhes Técnicos

**[10-demanda_censo2022_real.py](Outputs%26Codigo/PARTE3/10-demanda_censo2022_real.py):**
- Baixa automaticamente dados do FTP do IBGE (se necessário)
- Usa agregados por setores censitários
- Carrega malha shapefile de setores de SP
- Gera mapa de calor da população idosa (60+)

---

### PARTE 4: Análise de Saturação e Conformidade Legal

> **Pergunta-guia:** *"Quantas equipes realmente cumprem os requisitos legais de composição?"*

#### Scripts

| Script | Descrição | Output |
|:---|:---|:---|
| [8-analise_saturacao_ad.py](Outputs%26Codigo/PARTE4/8-analise_saturacao_ad.py) | Análise de completude normativa | Dashboards de conformidade |

#### Base Legal

- **Portaria de Consolidação GM/MS nº 5/2017**
- **Portaria GM/MS nº 3.005 de 02/05/2024** (atualização)

#### Requisitos de Composição por Tipo de Equipe

| Tipo | Médico | Enfermeiro | Téc. Enfermagem | Fisio/AS |
|:---:|:---:|:---:|:---:|:---:|
| **EMAD I** | ≥40h | ≥60h | ≥120h | ≥30h |
| **EMAD II** | ≥20h | ≥30h | ≥120h | ≥30h |
| **EMAP** | - | - | - | 3+ prof. NS, ≥90h total |
| **EMAP-R** | - | ≥30h | - | 3+ prof. NS, ≥60h total |

> **Nota:** Profissionais com CHS < 20h são descartados do cálculo de completude (Art. 547, §1º)

#### Categorização de CBOs

O script implementa uma função de categorização baseada nas famílias CBO:

| Prefixo CBO | Categoria |
|:---|:---|
| 2251, 2252, 2253 | MEDICO |
| 2235 | ENFERMEIRO |
| 3222 | TECNICO_ENFERMAGEM |
| 2236 | FISIOTERAPEUTA |
| 2516 | ASSISTENTE_SOCIAL |
| 2238 | FONOAUDIOLOGO |
| 2237 | NUTRICIONISTA |
| 2515 | PSICOLOGO |
| 2239 | TERAPEUTA_OCUPACIONAL |
| 2232 | ODONTOLOGO |
| 2234 | FARMACEUTICO |

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

## Controle de Versão (Git)

### Baixar atualizações do repositório remoto

```bash
# Atualizar o repositório local com as mudanças do remoto
git pull origin main
```

### Enviar alterações para o repositório remoto

```bash
# Adicionar todas as alterações
git add .

# Criar commit com mensagem descritiva
git commit -m "Descrição das alterações"

# Enviar para o repositório remoto
git push origin main
```

### Forçar envio (sobrescrever repositório remoto)

> **Atenção:** Use apenas quando tiver certeza de que deseja sobrescrever o histórico remoto.

```bash
# Forçar push - SOBRESCREVE o repositório remoto
git push --force origin main

# Alternativa mais segura (falha se houver commits novos no remoto)
git push --force-with-lease origin main
```

### Resolver conflitos (pull com rebase)

```bash
# Baixar e reaplicar commits locais sobre os remotos
git pull --rebase origin main

# Se houver conflitos, resolver e continuar
git rebase --continue
```

### Descartar alterações locais e sincronizar com remoto

```bash
# Descartar tudo e usar a versão do remoto
git fetch origin
git reset --hard origin/main
```

---

## Referências Legais

| Documento | Descrição |
|:---|:---|
| **Portaria GM/MS nº 825/2016** | Redefine a Atenção Domiciliar no âmbito do SUS |
| **Portaria de Consolidação nº 5/2017** | Consolidação das normas sobre ações e serviços de saúde |
| **Portaria GM/MS nº 3.005/2024** | Atualização dos requisitos de composição das equipes AD |

---

## Referências Técnicas

- **CNES/DATASUS:** [https://cnes.datasus.gov.br/](https://cnes.datasus.gov.br/)
- **CBO - Ministério do Trabalho:** [http://www.mtecbo.gov.br/](http://www.mtecbo.gov.br/)
- **IBGE Censo 2022:** [https://censo2022.ibge.gov.br/](https://censo2022.ibge.gov.br/)

---

## Autores

- **Orientando:** [Seu Nome]
- **Orientador:** [Nome do Orientador]
- **Instituição:** [Sua Universidade]
- **Financiamento:** FAPESP

---

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<p align="center">
  <i>Desenvolvido como parte de Iniciação Científica para otimização de rotas do Programa Melhor em Casa</i>
</p>
