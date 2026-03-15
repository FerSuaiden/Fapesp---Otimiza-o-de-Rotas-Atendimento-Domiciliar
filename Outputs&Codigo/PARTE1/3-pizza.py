import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from pathlib import Path

# Caminhos dos arquivos (Fonte: CNES/DataSUS - competência 2025/08)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
arquivo_equipes = PROJECT_ROOT / 'CNES_DATA' / 'tbEquipe202508.csv'

# --- Dicionários de Mapeamento ---
MAP_EQUIPES = {
    '22': 'EMAD I',
    '46': 'EMAD II',
    '23': 'EMAP',
    '77': 'EMAP-R'
}
CODIGOS_RELEVANTES = ['22', '46', '23', '77']

try:
    # Carregamento das bases de dados
    df_equipes = pd.read_csv(
        arquivo_equipes, 
        sep=';', 
        encoding='latin-1', 
        dtype=str, 
        usecols=['CO_UNIDADE', 'TP_EQUIPE', 'DT_DESATIVACAO']
    )

    # Filtragem e mapeamento
    df_equipes['DT_DESATIVACAO'] = pd.to_datetime(
        df_equipes['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce'
    )
    df_equipes_ativas = df_equipes[df_equipes['DT_DESATIVACAO'].isna()].copy()

    df_equipes_filtradas = df_equipes_ativas[df_equipes_ativas['TP_EQUIPE'].isin(CODIGOS_RELEVANTES)].copy()
    df_equipes_filtradas['Tipo_Equipe'] = df_equipes_filtradas['TP_EQUIPE'].map(MAP_EQUIPES)

    # Gráfico de pizza (composição nacional)
    df_composicao_nacional = df_equipes_filtradas['Tipo_Equipe'].value_counts()
    fig_pie, ax_pie = plt.subplots(figsize=(10, 8))
    
    # Define cores para consistência
    cores = ['cornflowerblue', 'forestgreen', 'mediumpurple', 'lightcoral']
    
    wedges, texts, autotexts = ax_pie.pie(
        df_composicao_nacional, 
        startangle=90,
        autopct=lambda p: f'{p:.1f}%',
        colors=cores[:len(df_composicao_nacional)]
    )
    
    # Adiciona um "buraco" no meio para criar um gráfico de "donut"
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig_pie.gca().add_artist(centre_circle)
    
    ax_pie.axis('equal')  # Garante que a pizza seja um círculo
    ax_pie.set_title('Composição Nacional das Equipes de Atenção Domiciliar', fontsize=16, pad=20, weight='bold')
    
    # Adiciona legenda com descrições detalhadas
    legend_labels_map = {
        'EMAD I': 'EMAD I - Equipe Multiprofissional (maior porte)',
        'EMAD II': 'EMAD II - Equipe Multiprofissional (menor porte)',
        'EMAP': 'EMAP - Equipe Multiprofissional de Apoio',
        'EMAP-R': 'EMAP-R - Equipe Multiprofissional de Apoio para Reabilitação'
    }
    detailed_labels = [legend_labels_map.get(label, label) for label in df_composicao_nacional.index]
    
    ax_pie.legend(
        wedges, 
        detailed_labels, 
        title="Tipo de Equipe (Programa Melhor em Casa)",
        loc="center left",
        bbox_to_anchor=(0.9, 0, 0.5, 1),
        fontsize=9
    )
    
    # Adicionar nota de fonte
    fig_pie.text(0.5, 0.02, 'Fonte: CNES/DataSUS - Competência 2025/08 | Portaria GM/MS nº 3.005/2024', 
                 ha='center', va='bottom', fontsize=9, style='italic', color='gray')
    
    plt.tight_layout()
    nome_grafico = 'composicao_nacional_pizza.png'
    plt.savefig(nome_grafico, bbox_inches='tight')
    print(f"Gráfico salvo: {nome_grafico}")


except FileNotFoundError as e:
    print(f"\nERRO: O arquivo '{e.filename}' não foi encontrado.")
    print("Por favor, verifique se os caminhos e nomes dos arquivos estão corretos.")
    sys.exit(1)
except KeyError as e:
    print(f"\nERRO: A coluna {e} não foi encontrada.")
    print("Verifique se os nomes das colunas ('CO_UNIDADE', 'CO_UF', 'TP_EQUIPE') estão corretos nos seus arquivos CSV.")
    sys.exit(1)
except Exception as e:
    print(f"\nOcorreu um erro inesperado: {e}")
    sys.exit(1)