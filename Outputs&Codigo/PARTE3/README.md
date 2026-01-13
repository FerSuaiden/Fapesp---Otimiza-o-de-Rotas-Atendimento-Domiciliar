# PARTE 3 - Análise de Demanda de Atenção Domiciliar

## Objetivo
Estimar a demanda de Atenção Domiciliar (AD) para o município de São Paulo, utilizando diferentes metodologias e fontes de dados.

## Scripts Disponíveis

### 1. `10-demanda_censo2022_real.py`
**Metodologia:** Proxy baseado na população idosa (60+) do Censo 2022.

- **Premissa:** Usa 100% da população idosa como demanda potencial
- **Limitação:** Superestima significativamente a demanda real (~20x)
- **Uso:** Identificar áreas com maior concentração de idosos

**Saídas:**
- `mapa_demanda_idosos_sp_censo2022.html` - Mapa interativo

---

### 2. `11-demanda_corrigida.py`
**Metodologia:** Cenários de sensibilidade com taxas de utilização de AD.

- **Cenários:**
  - 1% dos idosos → Demanda conservadora
  - 3% dos idosos → Demanda moderada
  - 5% dos idosos → Demanda otimista
  
- **Ponderação por idade:**
  - 60-69 anos: peso 1.0
  - 70+ anos: peso 2.5 (maior necessidade de AD)

⚠️ **IMPORTANTE:** Essas taxas são HIPOTÉTICAS para análise de sensibilidade.
Não são baseadas em literatura científica específica.

**Saídas:**
- `comparacao_metodologias_demanda.png` - Gráfico comparativo
- `mapa_demanda_corrigida_cenario_3pct.html` - Mapa do cenário moderado

---

### 3. `14-demanda_real_sia_final.py` ⭐ **RECOMENDADO**
**Metodologia:** Dados REAIS de produção ambulatorial do SIA/SUS.

- **Fonte:** DATASUS - Sistema de Informação Ambulatorial
- **Procedimentos:** Grupo 03.01.05 (Atenção Domiciliar)
- **Vantagem:** Dados de produção efetiva, não estimativas

**Procedimentos de AD incluídos:**
| Código | Descrição |
|--------|-----------|
| 0301050023 | Assist. Dom. Profissional Nível Médio - AD1 |
| 0301050031 | Assist. Dom. Profissional Nível Superior - AD1 |
| 0301050040 | Assist. Dom. Equipe Multiprofissional - AD2 |
| 0301050058 | Assist. Dom. Equipe Multiprofissional - AD3 |
| 0301050147 | Atendimento Fisioterapêutico em AD |
| 0301050155 | Atendimento Multiprofissional em AD |

**Limitação:** Representa demanda ATENDIDA, não demanda total (demanda reprimida não capturada).

**Saídas:**
- `demanda_ad_real_por_municipio.csv` - Produção por município
- `../../SIA_DATA/producao_ad_sp_*.parquet` - Dados brutos processados

---

## Resultados Obtidos (Nov/2025)

### Dados Reais do SIA/SUS (1 mês)
| Métrica | Valor |
|---------|-------|
| **Total de atendimentos AD em SP** | 3.563 |
| **Registros processados** | 530 |
| **Municípios com produção AD** | 15 |

### Comparação de Metodologias
| Metodologia | Demanda Estimada SP Capital |
|-------------|----------------------------|
| Censo 100% idosos | ~3,4 milhões (irreal) |
| Cenário 1% | ~34.000 |
| Cenário 3% | ~102.000 |
| Cenário 5% | ~170.000 |
| **SIA Real (mensal)** | ~3.500 (atendida) |

> **Nota:** A demanda real atendida (~3.500/mês) é muito menor que as estimativas,
> indicando possível demanda reprimida significativa ou diferenças metodológicas.

---

## Como Usar

### Opção 1: Usar dados já processados
```python
import pandas as pd

# Carregar dados reais do SIA
df = pd.read_parquet("../../SIA_DATA/producao_ad_sp_202511.parquet")
print(df.head())
```

### Opção 2: Baixar novos dados
```bash
cd Outputs&Codigo/PARTE3
source ../../venv/bin/activate
python 14-demanda_real_sia_final.py
```

---

## Fontes de Dados

1. **IBGE Censo 2022** - População por setor censitário e faixa etária
2. **DATASUS SIA/SUS** - Produção ambulatorial (procedimentos realizados)
3. **SIGTAP** - Tabela de procedimentos do SUS

---

## Próximos Passos

1. Baixar série temporal completa do SIA (12 meses)
2. Analisar sazonalidade nos atendimentos
3. Cruzar com dados de equipes EMAD/EMAP do CNES
4. Estimar gap entre oferta e demanda

---

*Última atualização: Janeiro 2025*
