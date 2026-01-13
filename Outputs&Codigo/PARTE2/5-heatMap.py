import pandas as pd
import folium
from folium.plugins import HeatMap
import sys

print("Iniciando geração do MAPA DE CALOR de Carga Horária (CHS) - Brasil...")

# --- Nomes dos arquivos ---
# Fonte: CNES/DataSUS (competência 2025/08)
arquivo_estabelecimentos = '../../CNES_DATA/tbEstabelecimento202508.csv'
arquivo_equipes = '../../CNES_DATA/tbEquipe202508.csv'
arquivo_profissionais_equipe = '../../CNES_DATA/rlEstabEquipeProf202508.csv'
arquivo_cargas_horarias = '../../CNES_DATA/tbCargaHorariaSus202508.csv'

# Códigos das equipes AD (EMAD I/II, EMAP, EMAP-R)
CODIGOS_RELEVANTES = ['22', '46', '23', '77']

try:
    # Carregamento das bases de dados
    # Fonte: CNES/DataSUS (competência 2025/08)
    df_estab = pd.read_csv(
        arquivo_estabelecimentos, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'NU_LATITUDE', 'NU_LONGITUDE']
    )
    
    # Base de Equipes (para filtrar EMAD/EMAP)
    df_equipes = pd.read_csv(
        arquivo_equipes, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'SEQ_EQUIPE', 'TP_EQUIPE']
    )
    
    # Base de Profissionais por Equipe
    df_prof_equipe = pd.read_csv(
        arquivo_profissionais_equipe, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'SEQ_EQUIPE', 'CO_PROFISSIONAL_SUS', 'CO_CBO']
    )
    
    # Base de Carga Horária
    df_chs = pd.read_csv(
        arquivo_cargas_horarias, sep=';', encoding='latin-1', dtype=str,
        usecols=['CO_UNIDADE', 'CO_PROFISSIONAL_SUS', 'CO_CBO', 
                 'QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']
    )

    # Filtragem e merge
    df_equipes_filtradas = df_equipes[df_equipes['TP_EQUIPE'].isin(CODIGOS_RELEVANTES)]

    df_merge1 = pd.merge(
        df_equipes_filtradas,
        df_prof_equipe,
        on=['CO_UNIDADE', 'SEQ_EQUIPE'],
        how='inner'
    )
    
    df_completo = pd.merge(
        df_merge1,
        df_chs,
        on=['CO_UNIDADE', 'CO_PROFISSIONAL_SUS', 'CO_CBO'],
        how='left'
    )

    # Cálculo da CHS por profissional
    cols_chs = ['QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']
    
    for col in cols_chs:
        df_completo[col] = pd.to_numeric(df_completo[col], errors='coerce').fillna(0)
        
    df_completo['CHS_PROFISSIONAL_TOTAL'] = df_completo[cols_chs].sum(axis=1)

    # Agregação por estabelecimento
    df_capacidade_estab = df_completo.groupby('CO_UNIDADE')['CHS_PROFISSIONAL_TOTAL'].sum().reset_index()
    df_capacidade_estab = df_capacidade_estab.rename(columns={'CHS_PROFISSIONAL_TOTAL': 'CHS_TOTAL_ESTABELECIMENTO'})
    df_capacidade_estab = df_capacidade_estab[df_capacidade_estab['CHS_TOTAL_ESTABELECIMENTO'] > 0]

    # Merge com coordenadas
    df_heatmap_data = pd.merge(
        df_capacidade_estab,
        df_estab,
        on='CO_UNIDADE',
        how='left'
    )

    # Limpeza de coordenadas
    df_heatmap_data['NU_LATITUDE'] = pd.to_numeric(df_heatmap_data['NU_LATITUDE'].str.replace(',', '.'), errors='coerce')
    df_heatmap_data['NU_LONGITUDE'] = pd.to_numeric(df_heatmap_data['NU_LONGITUDE'].str.replace(',', '.'), errors='coerce')
    df_heatmap_data = df_heatmap_data.dropna(subset=['NU_LATITUDE', 'NU_LONGITUDE', 'CHS_TOTAL_ESTABELECIMENTO'])

    # Geração do mapa de calor
    mapa_calor = folium.Map(location=[-14.2350, -51.9253], zoom_start=4)
    
    # Prepara a lista de dados no formato [latitude, longitude, peso]
    heatmap_list = df_heatmap_data[['NU_LATITUDE', 'NU_LONGITUDE', 'CHS_TOTAL_ESTABELECIMENTO']].values.tolist()
    
    # Adiciona a camada de Mapa de Calor
    HeatMap(
        heatmap_list,
        name='Capacidade (CHS) de Atenção Domiciliar',
        min_opacity=0.2,
        max_val=float(df_heatmap_data['CHS_TOTAL_ESTABELECIMENTO'].max()), # Define o máximo com base nos dados
        radius=15,
        blur=10
    ).add_to(mapa_calor)

    nome_arquivo = 'mapa_calor_chs_brasil.html'
    mapa_calor.save(nome_arquivo)
    print(f"Mapa salvo: {nome_arquivo}")

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