import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
import sys

print("Iniciando a geração de gráficos de Atenção Domiciliar...")

# --- Nomes dos arquivos ---
arquivo_estabelecimentos = 'cnes_completo.csv'
# Certifique-se que o caminho para seu arquivo de equipe está correto
arquivo_equipes = './CNES_DATA/tbEquipe202508.csv' 

# --- Dicionários de Mapeamento ---
MAP_EQUIPES = {
    '22': 'EMAD I',
    '46': 'EMAD II',
    '23': 'EMAP',
    '77': 'EMAP-R'
}
CODIGOS_RELEVANTES = ['22', '46', '23', '77']
IBGE_UF_MAP = {
    '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
    '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL', '28': 'SE', '29': 'BA',
    '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
    '41': 'PR', '42': 'SC', '43': 'RS',
    '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF'
}

try:
    # --- ETAPA 1: CARREGAR AS BASES DE DADOS ---
    print(f"Carregando base de estabelecimentos ({arquivo_estabelecimentos})...")
    df_estabelecimentos = pd.read_csv(
        arquivo_estabelecimentos, 
        sep=';', 
        encoding='latin-1', 
        dtype=str, 
        usecols=['CO_UNIDADE', 'CO_UF']
    )

    print(f"Carregando base de equipes ({arquivo_equipes})...")
    df_equipes = pd.read_csv(
        arquivo_equipes, 
        sep=';', 
        encoding='latin-1', 
        dtype=str, 
        usecols=['CO_UNIDADE', 'TP_EQUIPE']
    )
    print("Bases de dados carregadas com sucesso.")

    # --- ETAPA 2: FILTRAR, MAPEAR E JUNTAR ---
    print("Filtrando equipes relevantes (EMAD, EMAP, EMAP-R)...")
    df_equipes_filtradas = df_equipes[df_equipes['TP_EQUIPE'].isin(CODIGOS_RELEVANTES)].copy()
    
    df_equipes_filtradas['Tipo_Equipe'] = df_equipes_filtradas['TP_EQUIPE'].map(MAP_EQUIPES)
    
    print("Cruzando dados de equipes com estabelecimentos para identificar o estado (UF)...")
    df_merged = pd.merge(
        df_equipes_filtradas,
        df_estabelecimentos,
        on='CO_UNIDADE',
        how='left'
    )
    
    df_merged['Estado_UF'] = df_merged['CO_UF'].map(IBGE_UF_MAP)
    df_merged = df_merged.dropna(subset=['Estado_UF', 'Tipo_Equipe'])

    # --- ETAPA 3: GRÁFICO 1 - BARRAS EMPILHADAS (POR ESTADO) ---
    print("\n--- GRÁFICO 1: Preparando dados (Top 15 Estados)... ---")
    df_plot_data = pd.crosstab(df_merged['Estado_UF'], df_merged['Tipo_Equipe'])
    
    for col in MAP_EQUIPES.values():
        if col not in df_plot_data:
            df_plot_data[col] = 0
            
    df_plot_data = df_plot_data[['EMAD I', 'EMAD II', 'EMAP', 'EMAP-R']]
    df_plot_data['Total'] = df_plot_data.sum(axis=1)
    df_plot_data = df_plot_data.sort_values(by='Total', ascending=False)
    df_plot_data_top15 = df_plot_data.head(15)
    
    print(f"Dados prontos. Top 5 estados:\n{df_plot_data_top15.head()}")

    print("Gerando Gráfico 1 (Barras Empilhadas)...")
    fig, ax_bar = plt.subplots(figsize=(18, 10))
    plot_cols = ['EMAD I', 'EMAD II', 'EMAP', 'EMAP-R']
    
    df_plot_data_top15[plot_cols].plot(
        kind='bar', 
        stacked=True, 
        ax=ax_bar, 
        width=0.8
    )
    
    ax_bar.set_title('Top 15 Estados por Nº de Equipes de Atenção Domiciliar (Melhor em Casa)', fontsize=18, pad=20, weight='bold')
    ax_bar.set_xlabel('Estado (UF)', fontsize=14, labelpad=10)
    ax_bar.set_ylabel('Número Total de Equipes', fontsize=14, labelpad=10)
    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(fontsize=12)
    ax_bar.legend(title='Tipo de Equipe', title_fontsize='13', fontsize='12', loc='upper right')
    ax_bar.spines['top'].set_visible(False)
    ax_bar.spines['right'].set_visible(False)
    ax_bar.yaxis.grid(color='gray', linestyle='dashed', alpha=0.5)
    ax_bar.set_axisbelow(True)

    plt.tight_layout()
    nome_grafico_barras = 'distribuicao_equipes_por_estado_empilhado.png'
    plt.savefig(nome_grafico_barras)
    print(f"SUCESSO! Gráfico de barras salvo como '{nome_grafico_barras}'")

    # --- ETAPA 4: GRÁFICO 2 - PIZZA (COMPOSIÇÃO NACIONAL) ---
    print("\n--- GRÁFICO 2: Preparando dados (Composição Nacional)... ---")
    
    # Contagem nacional de cada tipo de equipe (usando o df_equipes_filtradas)
    df_composicao_nacional = df_equipes_filtradas['Tipo_Equipe'].value_counts()
    print(f"Composição nacional:\n{df_composicao_nacional}")

    print("Gerando Gráfico 2 (Pizza)...")
    fig_pie, ax_pie = plt.subplots(figsize=(10, 8))
    
    # Define cores para consistência
    cores = ['cornflowerblue', 'forestgreen', 'mediumpurple', 'lightcoral']
    
    wedges, texts, autotexts = ax_pie.pie(
        df_composicao_nacional, 
        autopct='%1.1f%%',  # Formato da porcentagem
        startangle=90,
        pctdistance=0.85,   # Posição do texto de porcentagem
        colors=cores[:len(df_composicao_nacional)]
    )
    
    # Adiciona um "buraco" no meio para criar um gráfico de "donut"
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig_pie.gca().add_artist(centre_circle)
    
    # Formatação do texto
    plt.setp(autotexts, size=12, weight="bold", color="white")
    
    ax_pie.axis('equal')  # Garante que a pizza seja um círculo
    ax_pie.set_title('Composição Nacional das Equipes de Atenção Domiciliar', fontsize=16, pad=20, weight='bold')
    
    # Adiciona legenda
    ax_pie.legend(
        wedges, 
        df_composicao_nacional.index, 
        title="Tipo de Equipe",
        loc="center left",
        bbox_to_anchor=(0.9, 0, 0.5, 1)
    )
    
    plt.tight_layout()
    nome_grafico_pizza = 'composicao_nacional_pizza.png'
    plt.savefig(nome_grafico_pizza)
    print(f"SUCESSO! Gráfico de pizza salvo como '{nome_grafico_pizza}'")


except FileNotFoundError as e:
    print(f"\nERRO: O arquivo '{e.filename}' não foi encontrado.")
    print("Por favor, verifique se os caminhos e nomes dos arquivos estão corretos.")
    sys.exit()
except KeyError as e:
    print(f"\nERRO: A coluna {e} não foi encontrada.")
    print("Verifique se os nomes das colunas ('CO_UNIDADE', 'CO_UF', 'TP_EQUIPE') estão corretos nos seus arquivos CSV.")
    sys.exit()
except Exception as e:
    print(f"\nOcorreu um erro inesperado: {e}")
    sys.exit()