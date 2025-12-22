import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import sys

print("Iniciando análise de CAPACIDADE (CHS) das equipes...")

# --- Nomes dos arquivos ---
# Fonte: CNES/DataSUS (competência 2025/08)
arquivo_estabelecimentos = '../../CNES_DATA/tbEstabelecimento202508.csv'
arquivo_equipes = '../../CNES_DATA/tbEquipe202508.csv'
arquivo_profissionais_equipe = '../../CNES_DATA/rlEstabEquipeProf202508.csv'
arquivo_cargas_horarias = '../../CNES_DATA/tbCargaHorariaSus202508.csv'

# --- Dicionários de Mapeamento ---
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
    print("Carregando bases de dados...")
    
    # Base de Estabelecimentos (para UF)
    # CO_ESTADO_GESTOR = Código IBGE da UF (equivalente ao CO_UF)
    df_estab = pd.read_csv(
        arquivo_estabelecimentos, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'CO_ESTADO_GESTOR']
    )
    df_estab = df_estab.rename(columns={'CO_ESTADO_GESTOR': 'CO_UF'})
    
    # Base de Equipes (para filtrar EMAD/EMAP)
    df_equipes = pd.read_csv(
        arquivo_equipes, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'SEQ_EQUIPE', 'TP_EQUIPE']
    )
    
    # Base de Profissionais por Equipe (a "cola" principal)
    df_prof_equipe = pd.read_csv(
        arquivo_profissionais_equipe, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'SEQ_EQUIPE', 'CO_PROFISSIONAL_SUS', 'CO_CBO']
    )
    
    # Base de Carga Horária (a métrica de capacidade)
    df_chs = pd.read_csv(
        arquivo_cargas_horarias, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'CO_PROFISSIONAL_SUS', 'CO_CBO', 
                 'QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']
    )
    
    print("Bases de dados carregadas com sucesso.")

    # --- ETAPA 2: FILTRAR E FAZER MERGE (CRUZAMENTO) ---
    print("Filtrando equipes de Atenção Domiciliar...")
    df_equipes_filtradas = df_equipes[df_equipes['TP_EQUIPE'].isin(CODIGOS_RELEVANTES)]

    print("Cruzando Equipes -> Profissionais...")
    # Junta as equipes (EMAD/EMAP) com os profissionais que as compõem
    df_merge1 = pd.merge(
        df_equipes_filtradas,
        df_prof_equipe,
        on=['CO_UNIDADE', 'SEQ_EQUIPE'],
        how='inner' # Queremos apenas profissionais que estão de fato em equipes de AD
    )
    
    print("Cruzando Profissionais -> Cargas Horárias...")
    # Junta os profissionais da equipe com suas respectivas cargas horárias
    # Usamos CO_UNIDADE, CO_PROFISSIONAL_SUS e CO_CBO para a ligação mais precisa possível
    df_completo = pd.merge(
        df_merge1,
        df_chs,
        on=['CO_UNIDADE', 'CO_PROFISSIONAL_SUS', 'CO_CBO'],
        how='left' # Usamos 'left' para manter o profissional mesmo se a CHS não for encontrada
    )

    # --- ETAPA 3: CALCULAR A CAPACIDADE (Qk) ---
    print("Limpando e somando Cargas Horárias (CHS)...")
    
    # Colunas de CHS para somar
    cols_chs = ['QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']
    
    # Converte todas para numérico, preenchendo N/A ou erros com 0
    for col in cols_chs:
        df_completo[col] = pd.to_numeric(df_completo[col], errors='coerce').fillna(0)
        
    # Soma as colunas para obter a capacidade total de CADA PROFISSIONAL
    df_completo['CHS_PROFISSIONAL_TOTAL'] = df_completo[cols_chs].sum(axis=1)

    print("Calculando a Capacidade Total (Qk) de CADA EQUIPE...")
    # Agrupa por equipe (SEQ_EQUIPE) e soma a CHS de todos os seus membros
    df_capacidade_equipe = df_completo.groupby('SEQ_EQUIPE')['CHS_PROFISSIONAL_TOTAL'].sum().reset_index()
    df_capacidade_equipe = df_capacidade_equipe.rename(columns={'CHS_PROFISSIONAL_TOTAL': 'Qk_CHS_Equipe'})

    # Junta de volta com df_equipes para saber o CO_UNIDADE de cada equipe
    df_capacidade_final = pd.merge(
        df_capacidade_equipe,
        df_equipes_filtradas,
        on='SEQ_EQUIPE',
        how='left'
    )

    # Junta com df_estab para saber o Estado (UF) de cada equipe
    df_dados_plot = pd.merge(
        df_capacidade_final,
        df_estab,
        on='CO_UNIDADE',
        how='left'
    )
    df_dados_plot['Estado_UF'] = df_dados_plot['CO_UF'].map(IBGE_UF_MAP)
    df_dados_plot = df_dados_plot.dropna(subset=['Estado_UF'])
    
    print(f"\nAnálise de Capacidade concluída. Total de equipes analisadas: {len(df_dados_plot)}")
    print(df_dados_plot[['SEQ_EQUIPE', 'Qk_CHS_Equipe', 'Estado_UF']].head())

    # --- ETAPA 4: GRÁFICO 1 - CAPACIDADE TOTAL POR ESTADO ---
    print("\nGerando Gráfico 1: Capacidade Total (Soma de CHS) por Estado...")
    
    # Soma a capacidade (Qk) de todas as equipes de um estado
    df_plot_chs_estado = df_dados_plot.groupby('Estado_UF')['Qk_CHS_Equipe'].sum().sort_values(ascending=False).head(15)
    
    fig, ax1 = plt.subplots(figsize=(18, 10))
    df_plot_chs_estado.sort_values(ascending=True).plot(
        kind='barh', 
        ax=ax1,
        color='darkgreen'
    )
    
    ax1.set_title('Top 15 Estados por Capacidade Total de Atendimento Domiciliar (Soma de CHS das Equipes)', fontsize=18, pad=20, weight='bold')
    ax1.set_xlabel('Capacidade Total (Horas de Trabalho Semanais)', fontsize=14)
    ax1.set_ylabel('Estado (UF)', fontsize=14)
    
    # Formata o eixo X para milhares
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{int(x/1000)}k' if x > 0 else 0))
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    plt.tight_layout()
    
    nome_grafico_chs_estado = 'capacidade_total_chs_por_estado.png'
    plt.savefig(nome_grafico_chs_estado)
    print(f"SUCESSO! Gráfico 1 salvo como '{nome_grafico_chs_estado}'")

    # --- ETAPA 5: GRÁFICO 2 - DISTRIBUIÇÃO DA CAPACIDADE DAS EQUIPES (Qk) ---
    print("\nGerando Gráfico 2: Histograma da Capacidade (Qk) das Equipes...")
    
    # Filtra equipes com capacidade > 0 para um gráfico mais limpo
    Qk_valores = df_dados_plot[df_dados_plot['Qk_CHS_Equipe'] > 0]['Qk_CHS_Equipe']
    
    fig, ax2 = plt.subplots(figsize=(12, 7))
    
    # Cria um histograma para ver a distribuição de Qk
    ax2.hist(Qk_valores, bins=50, edgecolor='black', color='lightblue')
    
    media_chs = Qk_valores.mean()
    ax2.axvline(media_chs, color='red', linestyle='dashed', linewidth=2)
    ax2.text(media_chs * 1.05, ax2.get_ylim()[1] * 0.9, f'Média: {media_chs:.0f} horas', color='red')

    ax2.set_title('Distribuição da Capacidade Semanal (CHS) por Equipe (Qk)', fontsize=16, pad=20, weight='bold')
    ax2.set_xlabel('Capacidade (Qk) - (Total de Horas Semanais da Equipe)', fontsize=12)
    ax2.set_ylabel('Número de Equipes', fontsize=12)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    nome_grafico_histograma = 'distribuicao_capacidade_Qk_histograma.png'
    plt.savefig(nome_grafico_histograma)
    print(f"SUCESSO! Gráfico 2 salvo como '{nome_grafico_histograma}'")

except FileNotFoundError as e:
    print(f"\nERRO: O arquivo '{e.filename}' não foi encontrado.")
    print("Por favor, verifique se os caminhos e nomes dos arquivos estão corretos.")
    sys.exit()
except KeyError as e:
    print(f"\nERRO: A coluna {e} não foi encontrada.")
    print("Verifique se os nomes das colunas estão corretos nos seus arquivos CSV.")
    sys.exit()
except Exception as e:
    print(f"\nOcorreu um erro inesperado: {e}")
    sys.exit()