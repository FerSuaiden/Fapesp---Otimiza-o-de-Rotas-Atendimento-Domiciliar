# 🚑 Otimização de Rotas de Atenção Domiciliar (HHC-RSP)

> **Projeto de Iniciação Científica (FAPESP)** > Análise Exploratória de Dados (AED) aplicada ao programa "Melhor em Casa" usando dados do CNES/DATASUS.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Libraries](https://img.shields.io/badge/Lib-Pandas%20%7C%20Folium%20%7C%20Matplotlib-orange)
![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-green)

## 🎯 Objetivo
Este repositório contém a etapa de **Análise Exploratória de Dados** para modelagem de um problema de otimização de rotas (*Home Health Care Routing and Scheduling Problem*). 

O objetivo é extrair parâmetros-chave das bases públicas do governo para identificar:
1.  📍 **Depots:** Localização das bases das equipes (Latitude/Longitude).
2.  ⚙️ **Capacidade e Habilidades:** Quantidade e tipologia das equipes ($Q_k$ e $S_k$).

---

## 🗃️ Dados Utilizados (CNES)
Os dados foram extraídos do Cadastro Nacional de Estabelecimentos de Saúde (competência 08/2025).

| Arquivo Base | Descrição | Chaves Principais |
| :--- | :--- | :--- |
| `tbEstabelecimento` | Cadastro de clínicas e hospitais. | `CO_UNIDADE`, `NU_LATITUDE`, `NU_LONGITUDE` |
| `tbEquipe` | Vínculo das equipes de saúde. | `CO_UNIDADE`, `TP_EQUIPE` |

### 🏥 Filtros de Equipes (Programa Melhor em Casa)
A filtragem foi realizada com base na documentação oficial e portarias do Ministério da Saúde para garantir a rastreabilidade:

| Cód | Sigla | Descrição | Categoria |
| :---: | :--- | :--- | :--- |
| **22** | EMAD I | Eq. Multiprofissional de Atenção Domiciliar I | 🩺 Atendimento |
| **46** | EMAD II | Eq. Multiprofissional de Atenção Domiciliar II | 🩺 Atendimento |
| **23** | EMAP | Eq. Multiprofissional de Apoio | 🤝 Apoio |
| **77** | EMAP-R | Eq. Multiprofissional de Apoio (Reabilitação) | 🤝 Apoio |

---

## 📂 Scripts e Visualizações

Aqui estão os scripts desenvolvidos para o processamento e visualização geográfica.

### 1. Mapa Interativo (São Paulo)
Gera uma visualização geoespacial das equipes no estado de SP.
- **Arquivo:** [`src/1-visuazacaoMapa.py`](src/1-visuazacaoMapa.py)
- **Funcionalidades:**
    - Limpeza de coordenadas (conversão e remoção de nulos).
    - [Ver lógica de Filtro Geográfico (SP = 35)](src/1-visuazacaoMapa.py#L20-L25)
    - Clusterização de marcadores com `Folium`.
    - Diferenciação por cor: 🔵 Atendimento, 🟢 Apoio, 🟣 Misto.

### 2. Distribuição por Estado (Barras Empilhadas)
Analisa a presença do programa em todo o território nacional.
- **Arquivo:** [`src/2-equipes_por_estado.py`](src/2-equipes_por_estado.py)
- **Otimização:** Uso de `usecols` para leitura eficiente de memória.
- **Output:** Gráfico dos Top 15 estados com maior cobertura.

### 3. Composição Nacional (Pizza/Donut)
Visão consolidada da proporção entre equipes de Atendimento vs. Apoio no Brasil.
- **Arquivo:** [`src/3-pizza.py`](src/3-pizza.py)
- **Detalhes:**
    - [Ver cálculo de contagem nacional](src/3-pizza.py#L40)
    - Estilização visual para manter consistência com relatórios técnicos.

---

## 📊 Exemplos de Resultados

| Mapa de Calor (SP) | Distribuição Nacional |
| :---: | :---: |
| *Insira um print do mapa.html aqui* | *Insira um print do grafico.png aqui* |
| `mapa_Equipes_SP.html` | `composicao_nacional.png` |

---

## 🚀 Como Executar

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/seu-repo.git](https://github.com/seu-usuario/seu-repo.git)
