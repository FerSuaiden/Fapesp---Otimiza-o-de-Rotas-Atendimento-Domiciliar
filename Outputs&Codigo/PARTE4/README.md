# PARTE 4 - Cobertura Municipal e Conformidade Legal das Equipes AD

## Resumo

Analisa a **cobertura municipal** do Programa Melhor em Casa e verifica se as equipes EMAD/EMAP estão em **conformidade com a Portaria GM/MS nº 3.005/2024**.

---

## 📁 Estrutura de Pastas

```
PARTE4/
├── README.md                          # Este arquivo
├── scripts/                           # Scripts Python
│   ├── analise_nacional_brasil.py     # Análise nacional V1 (com rastreamento de problemas)
│   ├── analise_nacional_brasil_v2.py  # Análise nacional V2 (com per capita, imagens separadas)
│   ├── gerar_visualizacoes_estados.py     # Visualizações por estado V1
│   └── gerar_visualizacoes_estados_v2.py  # Visualizações por estado V2 (+ conformidade)
├── dados_csv/                         # Dados gerados em CSV
│   ├── cobertura_municipal_brasil.csv
│   ├── cobertura_municipal_brasil_v2.csv
│   ├── cobertura_regiao_brasil_v2.csv
│   ├── conformidade_legal_brasil.csv
│   ├── conformidade_legal_brasil_v2.csv
│   ├── conformidade_legal_sp_estado.csv
│   └── resumo_por_regiao_brasil.csv
└── visualizacoes/
    ├── nacional/                      # Visualizações nacionais (organizadas)
    │   ├── cobertura_municipal/       # Cobertura do programa por UF
    │   │   ├── distribuicao_por_regiao.png       (V1: pizza por região)
    │   │   └── top15_cobertura_percentual.png   (V1+V2: top 15 UFs por %)
    │   ├── analise_percapita/         # Equipes por 100k habitantes
    │   │   ├── densidade_por_regiao.png         (V2: por região)
    │   │   └── top15_percapita_ufs.png          (V2: top 15 UFs)
    │   ├── conformidade_legal/        # Conformidade com Portaria 3.005/2024
    │   │   ├── conformidade_por_tipo.png        (V1+V2: por tipo de equipe)
    │   │   └── conformidade_por_regiao.png      (V1+V2: por região)
    │   └── resumo/                    # Indicadores resumidos
    │       ├── conformidade_nacional_donut.png  (76.7% conformes)
    │       └── cobertura_nacional_donut.png     (21.9% cobertos)
    └── estados/                       # Visualizações por estado (27 pastas)
        ├── resumo_por_estado.csv
        ├── resumo_por_estado_v2.csv
        ├── todos_municipios_brasil.csv
        ├── AC/
        │   ├── AC_equipes_conformidade.png
        │   ├── AC_conformidade.csv
        │   └── AC_dados_municipios.csv
        └── ... (27 estados)
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

---

## Como rodar

```bash
cd "Outputs&Codigo/PARTE4/scripts"

# Análise Nacional V2 (gera imagens separadas em subpastas organizadas)
python analise_nacional_brasil_v2.py

# Análise Nacional V1 (com rastreamento detalhado de problemas)
python analise_nacional_brasil.py

# Gerar visualizações por estado (27 estados)
python gerar_visualizacoes_estados_v2.py
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

*Última atualização: Fevereiro 2026*
