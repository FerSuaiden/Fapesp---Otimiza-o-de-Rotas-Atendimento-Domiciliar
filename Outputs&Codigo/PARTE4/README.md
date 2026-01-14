# PARTE 4 - Conformidade Legal das Equipes AD

## Resumo

Verifica se as equipes EMAD/EMAP do Estado de São Paulo estão em **conformidade com a Portaria GM/MS nº 3.005/2024**.

---

## Resultados Principais (Janeiro 2025)

### Estado de São Paulo - 412 equipes AD ativas

| Tipo | Total | Conformes | Não-Conformes | Taxa |
|:----:|:-----:|:---------:|:-------------:|:----:|
| EMAD I | 251 | 150 | 101 | **59.8%** |
| EMAD II | 26 | 20 | 6 | **76.9%** |
| EMAP | 124 | 113 | 11 | **91.1%** |
| EMAP-R | 11 | 9 | 2 | **81.8%** |
| **TOTAL** | **412** | **292** | **120** | **70.9%** |

> **70.9% das equipes estão em conformidade** com a nova legislação.

### Por que algumas equipes não estão conformes?

A **Portaria 3.005/2024** (janeiro de 2024) **aumentou** o requisito de enfermeiro:
- **Antes**: 40h (Portaria 825/2016)
- **Agora**: 60h (Portaria 3.005/2024)

As equipes não-conformes têm exatamente **40h de enfermeiro** - estavam conformes com a lei antiga.

---

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `analise_conformidade_sp_estado.py` | Análise de conformidade Estado SP (412 equipes) |
| `visualizacao_temporal.py` | Visualização da evolução temporal das equipes |
| `visualizacao_conformidade_temporal.py` | Evolução da conformidade ao longo do tempo |
| `conformidade_legal_sp_estado.csv` | Resultado detalhado por equipe |
| `evolucao_temporal_ad_sp.png` | Gráfico de evolução 2011-2025 |
| `evolucao_conformidade_temporal.png` | Gráfico de conformidade ao longo do tempo |

---

## Evolução da Conformidade Legal

Dos **155 municípios** com equipes AD ativas, **129 municípios (83%)** possuem pelo menos uma equipe conforme com a Portaria 3.005/2024.

| Ano | Equipes | Conformes | Taxa | Mun. AD | Mun. Conformes |
|:---:|:-------:|:---------:|:----:|:-------:|:--------------:|
| 2015 | 167 | 131 | 78.4% | 71 | 62 |
| 2020 | 277 | 205 | 74.0% | 104 | 86 |
| 2024 | 391 | 275 | 70.3% | 139 | 114 |
| 2025 | 412 | 292 | 70.9% | 155 | 129 |

> **Nota**: A conformidade é calculada usando a composição atual de profissionais (Ago/2025).

![Evolução Conformidade](evolucao_conformidade_temporal.png)

---

## Evolução Temporal (2011-2025)

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

![Evolução Temporal](evolucao_temporal_ad_sp.png)

---

## Como rodar

```bash
cd Outputs&Codigo/PARTE4
source ../../venv/bin/activate

# Análise de conformidade
python analise_conformidade_sp_estado.py

# Visualização temporal
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
