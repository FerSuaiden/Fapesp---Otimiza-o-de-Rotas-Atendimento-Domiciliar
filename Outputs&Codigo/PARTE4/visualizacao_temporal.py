#!/usr/bin/env python3
"""
Visualizacao Temporal - Evolucao das Equipes AD no Estado de SP

Analisa a evolucao ao longo do tempo:
1. Crescimento do numero de equipes ativas
2. Numero de municipios com cobertura AD
3. Distribuicao por tipo de equipe ao longo dos anos

Dados: CNES/DATASUS - Acumulado ate Agosto/2025
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os

# Configuracao
BASE_DIR = '/home/fersuaiden/Área de trabalho/Faculdade/IC'
CNES_DIR = os.path.join(BASE_DIR, 'CNES_DATA')
OUTPUT_DIR = os.path.join(BASE_DIR, 'Outputs&Codigo/PARTE4')

TIPOS_EQUIPE_AD = {
    22: 'EMAD I',
    46: 'EMAD II',
    23: 'EMAP',
    77: 'EMAP-R',
}

# Cores para cada tipo
CORES = {
    'EMAD I': '#2ecc71',
    'EMAD II': '#3498db',
    'EMAP': '#e74c3c',
    'EMAP-R': '#9b59b6',
}


def carregar_equipes():
    """Carrega equipes AD do estado de SP com datas."""
    print("Carregando equipes AD de SP...")
    
    df = pd.read_csv(
        os.path.join(CNES_DIR, "tbEquipe202508.csv"),
        sep=';', encoding='latin-1', low_memory=False
    )
    
    # Filtrar equipes AD de SP
    df_ad = df[df['TP_EQUIPE'].isin(TIPOS_EQUIPE_AD.keys())].copy()
    df_ad = df_ad[df_ad['CO_MUNICIPIO'].astype(str).str.startswith('35')]
    
    # Converter datas
    df_ad['DT_ATIVACAO'] = pd.to_datetime(df_ad['DT_ATIVACAO'], format='%d/%m/%Y', errors='coerce')
    df_ad['DT_DESATIVACAO'] = pd.to_datetime(df_ad['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce')
    
    # Mapear tipo
    df_ad['TIPO_NOME'] = df_ad['TP_EQUIPE'].map(TIPOS_EQUIPE_AD)
    
    print(f"  Total de equipes AD SP (historico): {len(df_ad)}")
    print(f"  Ativas atualmente: {df_ad['DT_DESATIVACAO'].isna().sum()}")
    
    return df_ad


def calcular_evolucao_mensal(df):
    """Calcula numero de equipes ativas em cada mes."""
    
    # Gerar serie de meses desde primeira ativacao ate hoje
    data_inicio = df['DT_ATIVACAO'].min().replace(day=1)
    data_fim = datetime(2025, 8, 31)  # Dados ate agosto 2025
    
    meses = pd.date_range(start=data_inicio, end=data_fim, freq='MS')
    
    evolucao = []
    
    for mes in meses:
        fim_mes = mes + pd.offsets.MonthEnd(0)
        
        # Equipes ativas no fim do mes:
        # - Ativadas antes ou durante o mes
        # - Nao desativadas OU desativadas depois do mes
        ativas = df[
            (df['DT_ATIVACAO'] <= fim_mes) &
            ((df['DT_DESATIVACAO'].isna()) | (df['DT_DESATIVACAO'] > fim_mes))
        ]
        
        # Contar por tipo
        por_tipo = ativas.groupby('TIPO_NOME').size().to_dict()
        
        # Contar municipios unicos
        n_municipios = ativas['CO_MUNICIPIO'].nunique()
        
        evolucao.append({
            'data': mes,
            'total': len(ativas),
            'n_municipios': n_municipios,
            **{tipo: por_tipo.get(tipo, 0) for tipo in TIPOS_EQUIPE_AD.values()}
        })
    
    return pd.DataFrame(evolucao)


def plot_evolucao_total(df_evolucao, ax):
    """Grafico de evolucao do total de equipes."""
    
    ax.fill_between(df_evolucao['data'], df_evolucao['total'], alpha=0.3, color='#3498db')
    ax.plot(df_evolucao['data'], df_evolucao['total'], linewidth=2, color='#2980b9')
    
    ax.set_title('Evolucao do Numero de Equipes AD Ativas\nEstado de Sao Paulo', fontsize=12, fontweight='bold')
    ax.set_xlabel('Ano')
    ax.set_ylabel('Numero de Equipes')
    ax.grid(True, alpha=0.3)
    
    # Marcar a data da Portaria 3.005/2024
    portaria_date = datetime(2024, 1, 5)
    ax.axvline(portaria_date, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.annotate('Portaria\n3.005/2024', xy=(portaria_date, ax.get_ylim()[1]*0.9),
                fontsize=8, ha='center', color='red')
    
    # Valor atual
    ultimo = df_evolucao.iloc[-1]
    ax.annotate(f'{int(ultimo["total"])} equipes\n(Ago/2025)', 
                xy=(ultimo['data'], ultimo['total']),
                xytext=(10, -20), textcoords='offset points',
                fontsize=9, fontweight='bold')


def plot_evolucao_por_tipo(df_evolucao, ax):
    """Grafico de area empilhada por tipo de equipe."""
    
    tipos = ['EMAD I', 'EMAD II', 'EMAP', 'EMAP-R']
    cores = [CORES[t] for t in tipos]
    
    ax.stackplot(df_evolucao['data'], 
                 [df_evolucao[t] for t in tipos],
                 labels=tipos, colors=cores, alpha=0.8)
    
    ax.set_title('Composicao por Tipo de Equipe ao Longo do Tempo', fontsize=12, fontweight='bold')
    ax.set_xlabel('Ano')
    ax.set_ylabel('Numero de Equipes')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)


def plot_municipios(df_evolucao, ax):
    """Grafico de evolucao de municipios com cobertura."""
    
    ax.fill_between(df_evolucao['data'], df_evolucao['n_municipios'], alpha=0.3, color='#27ae60')
    ax.plot(df_evolucao['data'], df_evolucao['n_municipios'], linewidth=2, color='#1e8449')
    
    ax.set_title('Municipios de SP com Equipes AD', fontsize=12, fontweight='bold')
    ax.set_xlabel('Ano')
    ax.set_ylabel('Numero de Municipios')
    ax.grid(True, alpha=0.3)
    
    # Valor atual
    ultimo = df_evolucao.iloc[-1]
    ax.annotate(f'{int(ultimo["n_municipios"])} municipios\n(de 645 no estado)', 
                xy=(ultimo['data'], ultimo['n_municipios']),
                xytext=(10, -20), textcoords='offset points',
                fontsize=9, fontweight='bold')


def plot_ativacoes_por_ano(df, ax):
    """Grafico de barras de novas equipes por ano."""
    
    df['ANO_ATIVACAO'] = df['DT_ATIVACAO'].dt.year
    
    # Agrupar por ano e tipo
    por_ano_tipo = df.groupby(['ANO_ATIVACAO', 'TIPO_NOME']).size().unstack(fill_value=0)
    
    # Filtrar anos relevantes (2011+)
    por_ano_tipo = por_ano_tipo[por_ano_tipo.index >= 2011]
    
    # Ordenar colunas
    tipos_ordem = ['EMAD I', 'EMAD II', 'EMAP', 'EMAP-R']
    por_ano_tipo = por_ano_tipo[[t for t in tipos_ordem if t in por_ano_tipo.columns]]
    
    por_ano_tipo.plot(kind='bar', ax=ax, color=[CORES[t] for t in por_ano_tipo.columns], 
                      width=0.8, alpha=0.8)
    
    ax.set_title('Novas Equipes Ativadas por Ano', fontsize=12, fontweight='bold')
    ax.set_xlabel('Ano')
    ax.set_ylabel('Novas Equipes')
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Ajustar labels do eixo x
    ax.set_xticklabels([str(int(x.get_text())) for x in ax.get_xticklabels()], rotation=45)


def main():
    print("="*70)
    print("VISUALIZACAO TEMPORAL - EQUIPES AD ESTADO DE SP")
    print("="*70)
    
    # Carregar dados
    df = carregar_equipes()
    
    # Calcular evolucao mensal
    print("\nCalculando evolucao mensal...")
    df_evolucao = calcular_evolucao_mensal(df)
    print(f"  Periodo: {df_evolucao['data'].min().strftime('%m/%Y')} a {df_evolucao['data'].max().strftime('%m/%Y')}")
    
    # Criar figura com subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Evolucao Temporal das Equipes de Atencao Domiciliar\nEstado de Sao Paulo (2003-2025)', 
                 fontsize=14, fontweight='bold', y=1.02)
    
    # Plot 1: Evolucao total
    plot_evolucao_total(df_evolucao, axes[0, 0])
    
    # Plot 2: Por tipo (area empilhada)
    plot_evolucao_por_tipo(df_evolucao, axes[0, 1])
    
    # Plot 3: Municipios com cobertura
    plot_municipios(df_evolucao, axes[1, 0])
    
    # Plot 4: Ativacoes por ano (barras)
    plot_ativacoes_por_ano(df, axes[1, 1])
    
    plt.tight_layout()
    
    # Salvar
    output_file = os.path.join(OUTPUT_DIR, 'evolucao_temporal_ad_sp.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"\nGrafico salvo em: {output_file}")
    
    # Imprimir estatisticas
    print("\n" + "="*70)
    print("ESTATISTICAS DA EVOLUCAO")
    print("="*70)
    
    # Anos selecionados para comparacao
    anos_ref = [2015, 2020, 2024, 2025]
    print("\nEquipes ativas por ano:")
    for ano in anos_ref:
        dados = df_evolucao[df_evolucao['data'].dt.year == ano]
        if len(dados) > 0:
            ultimo = dados.iloc[-1]
            print(f"  {ano}: {int(ultimo['total'])} equipes em {int(ultimo['n_municipios'])} municipios")
    
    # Crescimento
    inicio_2020 = df_evolucao[df_evolucao['data'] == '2020-01-01']
    fim_2025 = df_evolucao.iloc[-1]
    if len(inicio_2020) > 0:
        crescimento = (fim_2025['total'] - inicio_2020.iloc[0]['total']) / inicio_2020.iloc[0]['total'] * 100
        print(f"\nCrescimento 2020-2025: {crescimento:.1f}%")


if __name__ == '__main__':
    main()
