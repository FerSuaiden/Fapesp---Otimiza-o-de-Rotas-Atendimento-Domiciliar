import pandas as pd
import plotly.express as px
import sys

print("Iniciando análise de HABILIDADES (CBO) por Tipo de Equipe...")

# --- Nomes dos arquivos ---
# Fonte: CNES/DataSUS (competência 2025/08)
arquivo_estabelecimentos = '../../CNES_DATA/tbEstabelecimento202508.csv'
arquivo_equipes = '../../CNES_DATA/tbEquipe202508.csv'
arquivo_profissionais_equipe = '../../CNES_DATA/rlEstabEquipeProf202508.csv'
arquivo_cargas_horarias = '../../CNES_DATA/tbCargaHorariaSus202508.csv'
arquivo_cbo = '../../CBO_DATA/CBO2002 - Ocupacao.csv'

# --- Dicionários de Mapeamento ---
MAP_EQUIPES = {
    '22': 'EMAD I',
    '46': 'EMAD II',
    '23': 'EMAP',
    '77': 'EMAP-R'
}
CODIGOS_RELEVANTES = ['22', '46', '23', '77']

try:
    # --- ETAPA 1: CARREGAR AS 4 BASES DE DADOS ---
    print("Carregando bases de dados (Equipes, Profissionais, CHS e CBO)...")
    
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
    
    # Carrega o dicionário de CBO. O '' indica problema de encoding. 'latin-1' ou 'cp1252' costumam resolver.
    df_cbo = pd.read_csv(
        arquivo_cbo, sep=';', encoding='latin-1', dtype=str,
        usecols=['CODIGO', 'TITULO']
    )
    df_cbo = df_cbo.rename(columns={'CODIGO': 'CO_CBO', 'TITULO': 'Profissao'})
    
    print("Bases de dados carregadas com sucesso.")

    # --- ETAPA 2: FILTRAR E FAZER MERGE (CRUZAMENTO) ---
    print("Filtrando equipes de Atenção Domiciliar...")
    df_equipes_filtradas = df_equipes[df_equipes['TP_EQUIPE'].isin(CODIGOS_RELEVANTES)]

    print("Cruzando Equipes -> Profissionais...")
    df_merge1 = pd.merge(
        df_equipes_filtradas, df_prof_equipe,
        on=['CO_UNIDADE', 'SEQ_EQUIPE'], how='inner'
    )
    
    print("Cruzando Profissionais -> Cargas Horárias...")
    df_merge2 = pd.merge(
        df_merge1, df_chs,
        on=['CO_UNIDADE', 'CO_PROFISSIONAL_SUS', 'CO_CBO'], how='left'
    )
    
    print("Cruzando Dados -> Nomes das Profissões (CBO)...")
    df_final = pd.merge(
        df_merge2, df_cbo,
        on='CO_CBO', how='left'
    )

    # --- ETAPA 3: CALCULAR A CAPACIDADE (CHS) E LIMPAR DADOS ---
    print("Limpando e somando Cargas Horárias (CHS)...")
    cols_chs = ['QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']
    
    for col in cols_chs:
        df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)
        
    df_final['CHS_Profissional'] = df_final[cols_chs].sum(axis=1)
    
    # Mapeia códigos de equipe para nomes
    df_final['Tipo_Equipe'] = df_final['TP_EQUIPE'].map(MAP_EQUIPES)
    
    # Remove dados onde não encontramos CHS ou nome da profissão
    df_final = df_final.dropna(subset=['CHS_Profissional', 'Profissao', 'Tipo_Equipe'])
    df_final = df_final[df_final['CHS_Profissional'] > 0]

    # --- ETAPA 4: PREPARAR DADOS PARA O SUNBURST ---
    print("Agregando dados para o gráfico...")
    
    # Agrupa por Tipo de Equipe e Profissão, somando a CHS
    df_plot_data = df_final.groupby(['Tipo_Equipe', 'Profissao'])['CHS_Profissional'].sum().reset_index()
    
    # Para "beleza" e "utilidade": Agrega profissões menores em "Outros"
    # Calcula a CHS total para encontrar o limite de 1%
    total_chs = df_plot_data['CHS_Profissional'].sum()
    limite = total_chs * 0.005 # 0.5%
    
    # Marca profissões com menos que o limite como "Outros"
    df_plot_data.loc[df_plot_data['CHS_Profissional'] < limite, 'Profissao'] = 'Outras Profissões (<0.5%)'
    
    # Agrupa novamente para somar as "Outras Profissões"
    df_plot_data = df_plot_data.groupby(['Tipo_Equipe', 'Profissao'])['CHS_Profissional'].sum().reset_index()

    print(f"Dados prontos para plotagem:\n{df_plot_data.head()}")

    # --- ETAPA 5: GERAR O GRÁFICO SUNBURST INTERATIVO ---
    print("Gerando o gráfico Sunburst (habilidades_sunburst.html)...")
    
    # Define um "caminho" (path) hierárquico: 1º Nível = Tipo_Equipe, 2º Nível = Profissao
    # O "tamanho" (values) de cada fatia é a soma da CHS
    fig = px.sunburst(
        df_plot_data,
        path=['Tipo_Equipe', 'Profissao'],
        values='CHS_Profissional',
        title='Composição da Carga Horária (Habilidades) na Atenção Domiciliar - Brasil',
        color='Tipo_Equipe', # Colore o anel interno
        color_discrete_map={
            'EMAD I': '#006BA2',
            'EMAD II': '#5EBCD1',
            'EMAP': '#E5323B',
            'EMAP-R': '#F29C38',
            '(?)': 'grey'
        }
    )
    
    # Melhora a legibilidade
    fig.update_layout(
        margin=dict(t=80, l=25, r=25, b=80),
        font_size=12,
        # Adiciona anotações como legenda
        annotations=[
            dict(
                text="<b>Legenda:</b><br>" +
                     "<span style='color:#006BA2'>●</span> EMAD I - Equipe Multidisciplinar (maior porte)<br>" +
                     "<span style='color:#5EBCD1'>●</span> EMAD II - Equipe Multidisciplinar (menor porte)<br>" +
                     "<span style='color:#E5323B'>●</span> EMAP - Equipe Multiprofissional de Apoio<br>" +
                     "<span style='color:#F29C38'>●</span> EMAP-R - EMAP para Reabilitação<br><br>" +
                     "<i>Fonte: CNES/DataSUS - Competência 2025/08 | Programa Melhor em Casa</i>",
                align='left',
                showarrow=False,
                xref='paper', yref='paper',
                x=0, y=-0.15,
                font=dict(size=11)
            )
        ]
    )
    fig.update_traces(
        textinfo='label+percent parent', # Mostra o label e a % em relação ao "pai"
        insidetextorientation='radial'
    )
    
    # Salva como um arquivo HTML interativo
    nome_grafico_sunburst = 'habilidades_sunburst.html'
    fig.write_html(nome_grafico_sunburst)

    print(f"\nSUCESSO! Gráfico Sunburst salvo como '{nome_grafico_sunburst}'")
    print("Abra este arquivo HTML no seu navegador para ver o gráfico interativo.")

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