# PARTE 3 - Geração de Instâncias para Otimização

## 🎯 Objetivo

Gerar instâncias de entrada para o modelo de otimização de rotas de Atenção Domiciliar (BRKGA - Biased Random-Key Genetic Algorithm).

---

## 📁 Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `15-gerador_instancias.py` | Script principal - gera instâncias |
| `instancias/` | Diretório com instâncias geradas |
| `RESUMO_APRESENTACAO.md` | Resumo da apresentação |

### Instâncias Geradas

| Arquivo | Pacientes | Equipes | Seed | Uso |
|---------|:---------:|:-------:|:----:|-----|
| `pequena_10.json` | 10 | 1 | 42 | Debug rápido |
| `pequena_20.json` | 20 | 2 | 123 | Debug |
| `media_50.json` | 50 | 3 | 456 | Testes |
| `media_100.json` | 100 | 5 | 789 | Testes |
| `grande_200.json` | 200 | 8 | 1000 | Experimentos |
| `grande_500.json` | 500 | 15 | 2000 | Experimentos |

Cada instância gera 4 arquivos: `.json` (completo), `_equipes.csv`, `_pacientes.csv`, `_matriz.csv`.

O campo **seed** garante reprodutibilidade: rodar o script com a mesma seed gera exatamente os mesmos pacientes sintéticos.

---

## ▶️ Como rodar

```bash
cd Outputs&Codigo/PARTE3
python 15-gerador_instancias.py
```

---

## 📊 Estrutura das Instâncias

As instâncias seguem o formato requerido pelo modelo BRKGA:

### Equipes ($K$)
- Identificador único
- Capacidade $Q_k$ (CHS total disponível)
- Conjunto de habilidades $S_k$ (profissionais disponíveis)
- Coordenadas do estabelecimento base

### Pacientes ($N$)
- Identificador único
- Janela de tempo $[e_i, l_i]$ (início mais cedo, fim mais tarde)
- Tempo de serviço $s_i$
- Requisitos de habilidades $R_i$
- Coordenadas geográficas

### Distâncias
- Matriz de tempos de viagem entre localizações
- Baseada em dados de OpenStreetMap

---

## 📚 Fontes de Dados

1. **CNES/DATASUS** - Equipes AD, profissionais, carga horária
2. **IBGE** - Coordenadas geográficas dos estabelecimentos
3. **OpenStreetMap** - Malha viária para cálculo de distâncias

---

*Última atualização: Fevereiro 2026*
