# PARTE 4 - Cobertura Municipal e Conformidade Legal das Equipes AD

## Resumo

Analisa a **cobertura municipal** do Programa Melhor em Casa e verifica se as equipes EMAD/EMAP estão em **conformidade com a Portaria GM/MS nº 3.005/2024**.

---

## 📁 Estrutura de Pastas

```
PARTE4/
├── README.md                    # Este arquivo
├── scripts/                     # Scripts Python
│   ├── analise_nacional_brasil_v2.py    # Análise nacional (principal)
│   ├── gerar_visualizacoes_estados_v2.py # Visualizações por estado + conformidade
│   ├── visualizacao_temporal.py         # Evolução temporal (SP)
│   └── visualizacao_conformidade_temporal.py
├── dados_csv/                   # Dados gerados em CSV
│   ├── cobertura_municipal_brasil_v2.csv
│   ├── cobertura_regiao_brasil_v2.csv
│   ├── conformidade_legal_brasil_v2.csv
│   └── ...
├── visualizacoes/
│   ├── nacional/                # Visualizações nacionais
│   │   ├── conformidade_cobertura_nacional.png  # NOVO: % conformes + % municípios
│   │   ├── cobertura_municipal_brasil_v2.png
│   │   ├── analise_percapita_brasil.png
│   │   └── conformidade_legal_brasil_v2.png
│   └── estados/                 # Visualizações por estado (27 pastas)
│       ├── resumo_por_estado_v2.csv  # Resumo com conformidade
│       ├── AC/
│       │   ├── AC_equipes_conformidade.png   # Gráfico duplo
│       │   ├── AC_conformidade.csv
│       │   └── AC_dados_municipios.csv
│       ├── SP/
│       │   ├── SP_equipes_conformidade.png
│       │   ├── SP_conformidade.csv
│       │   └── SP_dados_municipios.csv
│       └── ... (27 estados)
└── _obsoletos/                  # Scripts antigos não utilizados
```

---

## 🇧🇷 Resultados Nacionais (Agosto 2025)

### Cobertura Municipal do Programa

| Indicador | Valor |
|-----------|-------|
| Municípios com equipes AD | **1.218** de 5.570 |
| Cobertura Nacional | **21.9%** |
| Total de equipes ativas | **2.664** |

#### Cobertura por Região

| Região | Municípios c/ AD | Total Municípios | Cobertura |
|--------|------------------|------------------|-----------|
| Nordeste | 564 | 1.794 | **31.4%** |
| Norte | 99 | 450 | **22.0%** |
| Sudeste | 359 | 1.668 | **21.5%** |
| Centro-Oeste | 89 | 467 | **19.1%** |
| Sul | 107 | 1.191 | **9.0%** |

### Conformidade Legal Nacional - 2.664 equipes

| Tipo | Total | Conformes | Não-Conformes | Taxa |
|:----:|:-----:|:---------:|:-------------:|:----:|
| EMAD I | 1.093 | 706 | 387 | **64.6%** |
| EMAD II | 460 | 403 | 57 | **87.6%** |
| EMAP | 929 | 800 | 129 | **86.1%** |
| EMAP-R | 182 | 134 | 48 | **73.6%** |
| **TOTAL** | **2.664** | **2.043** | **621** | **76.7%** |

> **76.7% das equipes AD do Brasil estão em conformidade** com a Portaria 3.005/2024.

#### Conformidade por Região

| Região | Equipes | Conformes | Taxa |
|--------|---------|-----------|------|
| Centro-Oeste | 216 | 172 | **79.6%** |
| Norte | 237 | 186 | **78.5%** |
| Nordeste | 1.104 | 855 | **77.4%** |
| Sudeste | 892 | 677 | **75.9%** |
| Sul | 215 | 153 | **71.2%** |

### 📊 Análise Per Capita (equipes por 100 mil hab.)

| Região | Equipes | População (mil) | Equipes/100k |
|--------|---------|-----------------|--------------|
| Nordeste | 1.104 | 56.648 | **1,95** |
| Norte | 237 | 17.588 | **1,35** |
| Centro-Oeste | 216 | 16.287 | **1,33** |
| Sudeste | 892 | 84.839 | **1,05** |
| Sul | 215 | 29.936 | **0,72** |

> **Insight**: O Nordeste, apesar de ter mais equipes em números brutos, também lidera em densidade per capita (1,95 eq/100k). O Sul, mesmo sendo desenvolvido economicamente, tem a menor densidade de equipes per capita.

---

## 📊 Visualizações por Estado (27 estados)

Para **cada estado** foram geradas visualizações individuais mostrando:
1. **Top 15 municípios por número de equipes AD** (gráfico horizontal)
2. **Conformidade por tipo de equipe** (EMAD I, EMAD II, EMAP, EMAP-R)

### Localização: `visualizacoes/estados/[UF]/`

| Estado | Arquivos |
|--------|----------|
| São Paulo | `SP_equipes_conformidade.png`, `SP_conformidade.csv`, `SP_dados_municipios.csv` |
| Minas Gerais | `MG_equipes_conformidade.png`, `MG_conformidade.csv`, `MG_dados_municipios.csv` |
| Rio de Janeiro | `RJ_equipes_conformidade.png`, `RJ_conformidade.csv`, `RJ_dados_municipios.csv` |
| ... | ... (27 estados) |

### Resumo consolidado: `resumo_por_estado_v2.csv`

Contém para cada estado: total de equipes, municípios cobertos, taxa de cobertura e taxa de conformidade.

---

## 🏛️ Resultados Estado de São Paulo (Agosto 2025)

### Estado de São Paulo - 412 equipes AD ativas

| Tipo | Total | Conformes | Não-Conformes | Taxa |
|:----:|:-----:|:---------:|:-------------:|:----:|
| EMAD I | 251 | 150 | 101 | **59.8%** |
| EMAD II | 26 | 20 | 6 | **76.9%** |
| EMAP | 124 | 113 | 11 | **91.1%** |
| EMAP-R | 11 | 9 | 2 | **81.8%** |
| **TOTAL** | **412** | **292** | **120** | **70.9%** |

> **70.9% das equipes de SP estão em conformidade** com a nova legislação.

### Por que algumas equipes não estão conformes?

A **Portaria 3.005/2024** (janeiro de 2024) **aumentou** o requisito de enfermeiro:
- **Antes**: 40h (Portaria 825/2016)
- **Agora**: 60h (Portaria 3.005/2024)

As equipes não-conformes têm exatamente **40h de enfermeiro** - estavam conformes com a lei antiga.

---

## Arquivos

### 🔷 Scripts Principais (use estes!)

| Arquivo | Descrição |
|---------|-----------|
| `analise_nacional_brasil_v2.py` | **Script principal V2** - Cobertura + Conformidade + Per Capita |
| `visualizacao_temporal.py` | Evolução temporal das equipes (SP) |

### 📊 Visualizações Geradas (V2 - Melhoradas)

| Arquivo | Descrição |
|---------|-----------|
| `cobertura_municipal_brasil_v2.png` | **NOVO**: Cobertura por UF (números + porcentagem claros) |
| `analise_percapita_brasil.png` | Equipes por 100 mil habitantes por região e UF |
| `conformidade_legal_brasil_v2.png` | Conformidade por tipo e região |

### 📁 Dados Gerados

| Arquivo | Localização |
|---------|-------------|
| `cobertura_municipal_brasil_v2.csv` | `dados_csv/` |
| `cobertura_regiao_brasil_v2.csv` | `dados_csv/` |
| `conformidade_legal_brasil_v2.csv` | `dados_csv/` |

### 📂 Scripts por Estado

| Script | Descrição |
|--------|-----------|
| `gerar_visualizacoes_estados.py` | Gera visualizações para todos os 27 estados |

---

## Evolução Temporal SP (2011-2025)

O **Programa Melhor em Casa** foi instituído em **novembro de 2011** pela Portaria GM/MS nº 2.527/2011.

> **Nota**: O CNES contém 6 registros de equipes AD anteriores a 2011 (1 em 2003, 5 em 2009), provavelmente de programas precursores de atenção domiciliar que foram reclassificados. A visualização considera o período a partir de 2011.

| Ano | Equipes Ativas | Municípios |
|:---:|:--------------:|:----------:|
| 2011 | 6 | 5 |
| 2015 | 167 | 71 |
| 2020 | 277 | 104 |
| 2024 | 391 | 139 |
| 2025 | 412 | 155 |

**Crescimento 2020-2025: 64.8%**

---

## Como rodar

```bash
cd "Outputs&Codigo/PARTE4/scripts"

# Análise Nacional (Brasil inteiro) - versão melhorada
python analise_nacional_brasil_v2.py

# Gerar visualizações por cidade para cada estado
python gerar_visualizacoes_estados.py

# Visualizações temporais (SP)
python visualizacao_temporal.py
```

---

## Códigos de Tipo de Equipe AD

| Código | Tipo | Descrição |
|:------:|:----:|:----------|
| 22 | EMAD I | Equipe Multiprofissional de Atenção Domiciliar Tipo I |
| 46 | EMAD II | Equipe Multiprofissional de Atenção Domiciliar Tipo II |
| 23 | EMAP | Equipe Multiprofissional de Apoio |
| 77 | EMAP-R | Equipe Multiprofissional de Apoio - Rural |

---

## Base Legal

**Portaria GM/MS nº 3.005, de 2 de janeiro de 2024**

### Art. 547 - Composição mínima EMAD I:
| Profissional | CHS Mínima |
|--------------|------------|
| Médico | 40h |
| **Enfermeiro** | **60h** |
| Fisioterapeuta OU Assistente Social | 30h |
| Técnico de Enfermagem | 120h |

### Art. 547, §1º:
> "Nenhum profissional componente de EMAD poderá ter carga horária inferior a **20 (vinte) horas** de trabalho."

---

*Última atualização: Janeiro 2025*
