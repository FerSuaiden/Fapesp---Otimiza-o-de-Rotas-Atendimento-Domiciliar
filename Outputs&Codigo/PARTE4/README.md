# PARTE 4 - Conformidade Legal das Equipes AD

## 🎯 Resumo

Verifica se as equipes EMAD/EMAP de São Paulo estão em **conformidade com a Portaria GM/MS nº 3.005/2024**.

---

## 📊 RESULTADOS PRINCIPAIS (Janeiro 2025)

### Estado de São Paulo - 412 equipes AD ativas

| Tipo | Total | Conformes | Não-Conformes | Taxa |
|:----:|:-----:|:---------:|:-------------:|:----:|
| EMAD I | 251 | 150 | 101 | **59.8%** |
| EMAD II | 26 | 20 | 6 | **76.9%** |
| EMAP | 124 | 113 | 11 | **91.1%** |
| EMAP-R | 11 | 9 | 2 | **81.8%** |
| **TOTAL** | **412** | **292** | **120** | **70.9%** |

> **70.9% das equipes estão em conformidade** com a nova legislação.

### São Paulo Capital - 82 equipes AD ativas

- **61% em conformidade** (50 equipes)
- Principal problema: Enfermeiros em EMAD I

### Por que algumas equipes não estão conformes?

A **Portaria 3.005/2024** (janeiro de 2024) **aumentou** o requisito de enfermeiro:
- **Antes**: 40h (Portaria 825/2016)
- **Agora**: 60h (Portaria 3.005/2024)

As equipes não-conformes têm exatamente **40h de enfermeiro** - estavam conformes com a lei antiga.

---

## 📁 Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `verificacao_conformidade_legal.py` | Análise SP Capital (82 equipes) |
| `analise_conformidade_sp_estado_v2.py` | Análise Estado SP (412 equipes) |
| `conformidade_legal_equipes.csv` | Resultado detalhado SP Capital |
| `conformidade_legal_sp_estado.csv` | Resultado detalhado Estado SP |
| `v2_dashboard_saturacao_oferta.png` | Dashboard de saturação |

---

## ▶️ Como rodar

```bash
cd Outputs&Codigo/PARTE4

# SP Capital
python verificacao_conformidade_legal.py

# Estado SP (completo)
python analise_conformidade_sp_estado_v2.py
```

---

## 🔢 Códigos de Tipo de Equipe AD

| Código | Tipo | Descrição |
|:------:|:----:|:----------|
| 22 | EMAD I | Equipe Multiprofissional de Atenção Domiciliar Tipo I |
| 46 | EMAD II | Equipe Multiprofissional de Atenção Domiciliar Tipo II |
| 23 | EMAP | Equipe Multiprofissional de Apoio |
| 77 | EMAP-R | Equipe Multiprofissional de Apoio - Rural |

---

## 📚 Base Legal

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
