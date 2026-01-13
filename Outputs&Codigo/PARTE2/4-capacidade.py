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
    # Carregamento das bases de dados
    # Fonte: CNES/DataSUS (competência 2025/08)
    df_estab = pd.read_csv(
        arquivo_estabelecimentos, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'CO_ESTADO_GESTOR']
    )
    df_estab = df_estab.rename(columns={'CO_ESTADO_GESTOR': 'CO_UF'})
    
    df_equipes = pd.read_csv(
        arquivo_equipes, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'SEQ_EQUIPE', 'TP_EQUIPE']
    )
    
    df_prof_equipe = pd.read_csv(
        arquivo_profissionais_equipe, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'SEQ_EQUIPE', 'CO_PROFISSIONAL_SUS', 'CO_CBO']
    )
    
    df_chs = pd.read_csv(
        arquivo_cargas_horarias, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'CO_PROFISSIONAL_SUS', 'CO_CBO', 
                 'QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']
    )

    # Filtragem e merge
    df_equipes_filtradas = df_equipes[df_equipes['TP_EQUIPE'].isin(CODIGOS_RELEVANTES)]

    # Equipes -> Profissionais
    df_merge1 = pd.merge(
        df_equipes_filtradas,
        df_prof_equipe,
        on=['CO_UNIDADE', 'SEQ_EQUIPE'],
        how='inner'
    )
    
    # Profissionais -> Cargas horárias
    df_completo = pd.merge(
        df_merge1,
        df_chs,
        on=['CO_UNIDADE', 'CO_PROFISSIONAL_SUS', 'CO_CBO'],
        how='left'
    )

    # Cálculo da Capacidade (Qk)
    # CHS = Ambulatorial + Hospitalar + Outros
    cols_chs = ['QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']
    
    # Converte todas para numérico, preenchendo N/A ou erros com 0
    for col in cols_chs:
        df_completo[col] = pd.to_numeric(df_completo[col], errors='coerce').fillna(0)
        
    # CHS por profissional
    df_completo['CHS_PROFISSIONAL_TOTAL'] = df_completo[cols_chs].sum(axis=1)

    # Agregação por equipe (CO_UNIDADE + SEQ_EQUIPE identificam uma equipe única)
    df_capacidade_equipe = df_completo.groupby(['CO_UNIDADE', 'SEQ_EQUIPE'])['CHS_PROFISSIONAL_TOTAL'].sum().reset_index()
    df_capacidade_equipe = df_capacidade_equipe.rename(columns={'CHS_PROFISSIONAL_TOTAL': 'Qk_CHS_Equipe'})

    # Junta de volta com df_equipes para saber o TP_EQUIPE de cada equipe
    df_capacidade_final = pd.merge(
        df_capacidade_equipe,
        df_equipes_filtradas,
        on=['CO_UNIDADE', 'SEQ_EQUIPE'],
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

    # Gráfico 1: Capacidade total por estado
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

    # Gráfico 2: Histograma de distribuição de Qk
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
    print(f"Gráficos salvos: {nome_grafico_chs_estado}, {nome_grafico_histograma}")

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