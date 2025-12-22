import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

print("Iniciando a geração do gráfico de distribuição de equipes por estado...")

# --- Nomes dos arquivos ---
# Fonte: CNES/DataSUS - tbEstabelecimento (competência 2025/08)
arquivo_estabelecimentos = '../../CNES_DATA/tbEstabelecimento202508.csv'
arquivo_equipes = '../../CNES_DATA/tbEquipe202508.csv'

# --- Dicionários de Mapeamento ---
# Mapeia códigos de equipe para nomes legíveis
MAP_EQUIPES = {
    '22': 'EMAD I',
    '46': 'EMAD II',
    '23': 'EMAP',
    '77': 'EMAP-R'
}
# Lista das equipes que nos interessam
CODIGOS_RELEVANTES = ['22', '46', '23', '77']

# Mapeia código IBGE (CO_UF) para Sigla (UF)
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
    # Otimização: Carregar apenas as colunas que realmente vamos usar
    # CO_ESTADO_GESTOR = Código IBGE da UF (equivalente ao CO_UF)
    df_estabelecimentos = pd.read_csv(
        arquivo_estabelecimentos, 
        sep=';', 
        encoding='latin-1', 
        dtype=str, 
        usecols=['CO_UNIDADE', 'CO_ESTADO_GESTOR']
    )
    # Renomear para manter compatibilidade com o restante do código
    df_estabelecimentos = df_estabelecimentos.rename(columns={'CO_ESTADO_GESTOR': 'CO_UF'})

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
    
    # Mapeia os códigos para nomes (ex: '22' -> 'EMAD I')
    df_equipes_filtradas['Tipo_Equipe'] = df_equipes_filtradas['TP_EQUIPE'].map(MAP_EQUIPES)
    
    print("Cruzando dados de equipes com estabelecimentos para identificar o estado (UF)...")
    # Juntar os dataframes para associar cada equipe a um CO_UF
    df_merged = pd.merge(
        df_equipes_filtradas,
        df_estabelecimentos,
        on='CO_UNIDADE',
        how='left'
    )
    
    # Mapeia os códigos de UF para siglas (ex: '35' -> 'SP')
    df_merged['Estado_UF'] = df_merged['CO_UF'].map(IBGE_UF_MAP)
    
    # Lidar com possíveis dados nulos
    df_merged = df_merged.dropna(subset=['Estado_UF', 'Tipo_Equipe'])

    # --- ETAPA 3: PREPARAR DADOS PARA O GRÁFICO (PIVOT) ---
    print("Preparando dados para o gráfico (contagem por Estado e Tipo)...")
    # Cria uma tabela de contagem com Estados nas linhas e Tipos de Equipe nas colunas
    df_plot_data = pd.crosstab(df_merged['Estado_UF'], df_merged['Tipo_Equipe'])
    
    # Garante que todas as 4 colunas de equipe existam (mesmo que com valor 0)
    for col in MAP_EQUIPES.values():
        if col not in df_plot_data:
            df_plot_data[col] = 0
            
    # Reordena as colunas para uma ordem lógica na legenda
    df_plot_data = df_plot_data[['EMAD I', 'EMAD II', 'EMAP', 'EMAP-R']]
    
    # Adiciona uma coluna 'Total' para ordenação
    df_plot_data['Total'] = df_plot_data.sum(axis=1)
    
    # Ordenar por total de equipes (do maior para o menor)
    df_plot_data = df_plot_data.sort_values(by='Total', ascending=False)
    
    # Pegar os Top 15 estados para um gráfico mais limpo
    df_plot_data_top15 = df_plot_data.head(15)
    
    print(f"Dados prontos. Top 5 estados:\n{df_plot_data_top15.head()}")

    # --- ETAPA 4: GERAR O GRÁFICO DE BARRAS EMPILHADAS ---
    print("Gerando o gráfico de barras...")
    
    # Define as colunas que serão empilhadas
    plot_cols = ['EMAD I', 'EMAD II', 'EMAP', 'EMAP-R']
    
    # Cria a figura e os eixos
    fig, ax = plt.subplots(figsize=(18, 10))
    
    # Plota o gráfico de barras empilhadas
    df_plot_data_top15[plot_cols].plot(
        kind='bar', 
        stacked=True, 
        ax=ax, 
        width=0.8
    )
    
    # --- ETAPA 5: FORMATAÇÃO E ESTILO DO GRÁFICO ---
    ax.set_title('Top 15 Estados por Nº de Equipes de Atenção Domiciliar (Melhor em Casa)', fontsize=18, pad=20, weight='bold')
    ax.set_xlabel('Estado (UF)', fontsize=14, labelpad=10)
    ax.set_ylabel('Número Total de Equipes', fontsize=14, labelpad=10)
    
    # Rotaciona os labels do eixo X para melhor legibilidade
    plt.xticks(rotation=45, ha='right', fontsize=12)
    plt.yticks(fontsize=12)
    
    # Ajusta a legenda com descrições detalhadas
    legend_labels = [
        'EMAD I - Equipe Multidisciplinar (maior porte)',
        'EMAD II - Equipe Multidisciplinar (menor porte)',  
        'EMAP - Equipe Multiprofissional de Apoio',
        'EMAP-R - EMAP para Reabilitação'
    ]
    handles, _ = ax.get_legend_handles_labels()
    ax.legend(handles, legend_labels, title='Tipo de Equipe', title_fontsize='13', fontsize='10', loc='upper right')
    
    # Adicionar nota de fonte
    fig.text(0.99, 0.01, 'Fonte: CNES/DataSUS - Competência 2025/08 | Programa Melhor em Casa', 
             ha='right', va='bottom', fontsize=9, style='italic', color='gray')
    
    # Remove bordas desnecessárias
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Adiciona gridlines horizontais para facilitar a leitura
    ax.yaxis.grid(color='gray', linestyle='dashed', alpha=0.5)
    ax.set_axisbelow(True) # Garante que o grid fique atrás das barras

    # Ajusta o layout para não cortar os labels
    plt.tight_layout()
    
    # Salvar o gráfico
    nome_grafico = 'distribuicao_equipes_por_estado_empilhado.png'
    plt.savefig(nome_grafico)
    
    print(f"\nSUCESSO! Gráfico salvo como '{nome_grafico}'")
    print(f"O gráfico mostra os 15 estados com maior número de equipes.")

except FileNotFoundError as e:
    print(f"ERRO: O arquivo {e.filename} não foi encontrado.")
    print("Por favor, verifique se os arquivos 'tbEstabelecimento202508.csv' e 'tbEquipe202508.csv' estão na pasta CNES_DATA.")
except KeyError as e:
    print(f"ERRO: A coluna {e} não foi encontrada.")
    print("Verifique se os nomes das colunas ('CO_UNIDADE', 'CO_UF', 'TP_EQUIPE'")