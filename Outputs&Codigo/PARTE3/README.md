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

| Arquivo | Descrição |
|---------|-----------|
| `SP_Capital_Pequena.json` | Instância reduzida para testes rápidos |
| `SP_Capital_Completa.json` | Instância completa de SP Capital |
| `equipes_sp_capital.csv` | Dados tabulares das equipes |
| `pacientes_sinteticos.csv` | Pacientes sintéticos para testes |

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

*Última atualização: Janeiro 2025*
