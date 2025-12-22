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

# --- Dicionários de Mapeamento ---
CODIGOS_RELEVANTES = ['22', '46', '23', '77'] # EMAD I/II, EMAP, EMAP-R

try:
    # --- ETAPA 1: CARREGAR AS BASES DE DADOS ---
    print("Carregando bases de dados...")
    
    # Base de Estabelecimentos (para Coordenadas)
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
    
    print("Bases de dados carregadas com sucesso.")

    # --- ETAPA 2: FILTRAR E FAZER MERGE (CRUZAMENTO) ---
    print("Filtrando equipes de Atenção Domiciliar...")
    df_equipes_filtradas = df_equipes[df_equipes['TP_EQUIPE'].isin(CODIGOS_RELEVANTES)]

    print("Cruzando Equipes -> Profissionais...")
    df_merge1 = pd.merge(
        df_equipes_filtradas,
        df_prof_equipe,
        on=['CO_UNIDADE', 'SEQ_EQUIPE'],
        how='inner'
    )
    
    print("Cruzando Profissionais -> Cargas Horárias...")
    df_completo = pd.merge(
        df_merge1,
        df_chs,
        on=['CO_UNIDADE', 'CO_PROFISSIONAL_SUS', 'CO_CBO'],
        how='left'
    )

    # --- ETAPA 3: CALCULAR A CAPACIDADE POR ESTABELECIMENTO ---
    print("Limpando e somando Cargas Horárias (CHS)...")
    cols_chs = ['QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']
    
    for col in cols_chs:
        df_completo[col] = pd.to_numeric(df_completo[col], errors='coerce').fillna(0)
        
    df_completo['CHS_PROFISSIONAL_TOTAL'] = df_completo[cols_chs].sum(axis=1)

    print("Agregando CHS total por Estabelecimento (CO_UNIDADE)...")
    # Agrupa por ESTABELECIMENTO e soma a CHS de todos os profissionais de AD
    df_capacidade_estab = df_completo.groupby('CO_UNIDADE')['CHS_PROFISSIONAL_TOTAL'].sum().reset_index()
    df_capacidade_estab = df_capacidade_estab.rename(columns={'CHS_PROFISSIONAL_TOTAL': 'CHS_TOTAL_ESTABELECIMENTO'})
    
    # Filtra estabelecimentos com CHS > 0
    df_capacidade_estab = df_capacidade_estab[df_capacidade_estab['CHS_TOTAL_ESTABELECIMENTO'] > 0]
    print(f"Total de estabelecimentos com CHS > 0 encontrados: {len(df_capacidade_estab)}")

    # --- ETAPA 4: JUNTAR COM COORDENADAS ---
    print("Cruzando dados de CHS com as coordenadas dos estabelecimentos...")
    df_heatmap_data = pd.merge(
        df_capacidade_estab,
        df_estab,
        on='CO_UNIDADE',
        how='left' # Mantém apenas os estabelecimentos que calculamos a CHS
    )

    # Limpa dados de coordenadas
    df_heatmap_data['NU_LATITUDE'] = pd.to_numeric(df_heatmap_data['NU_LATITUDE'].str.replace(',', '.'), errors='coerce')
    df_heatmap_data['NU_LONGITUDE'] = pd.to_numeric(df_heatmap_data['NU_LONGITUDE'].str.replace(',', '.'), errors='coerce')
    
    df_heatmap_data = df_heatmap_data.dropna(subset=['NU_LATITUDE', 'NU_LONGITUDE', 'CHS_TOTAL_ESTABELECIMENTO'])
    print(f"Total de estabelecimentos prontos para o mapa: {len(df_heatmap_data)}")

    # --- ETAPA 5: GERAR O MAPA DE CALOR ---
    print("Gerando o Mapa de Calor...")
    
    # Centraliza o mapa no Brasil
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

    print(f"\nSUCESSO! Mapa de Calor salvo como '{nome_arquivo}'")

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