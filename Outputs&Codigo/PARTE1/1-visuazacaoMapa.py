import pandas as pd
import folium
from folium.plugins import MarkerCluster

try:
    # Carregamento das bases de dados
    # Fonte: CNES/DataSUS (competência 2025/08)
    df_estabelecimentos = pd.read_csv('../../CNES_DATA/tbEstabelecimento202508.csv', sep=';', encoding='latin-1', dtype=str)    
    df_equipes = pd.read_csv('../../CNES_DATA/tbEquipe202508.csv', sep=';', encoding='latin-1', dtype=str)

    # Identificação das equipes AD por categoria
    codigos_atendimento = ['22', '46']  # EMAD I e EMAD II
    codigos_apoio = ['23', '77']        # EMAP e EMAP-R

    cnes_com_atendimento = set(df_equipes[df_equipes['TP_EQUIPE'].isin(codigos_atendimento)]['CO_UNIDADE'].unique())
    cnes_com_apoio = set(df_equipes[df_equipes['TP_EQUIPE'].isin(codigos_apoio)]['CO_UNIDADE'].unique())
    lista_cnes_total = list(cnes_com_atendimento.union(cnes_com_apoio))

    # Filtro geográfico para São Paulo (CO_ESTADO_GESTOR = '35')
    df_estabelecimentos_filtrados = df_estabelecimentos[df_estabelecimentos['CO_UNIDADE'].isin(lista_cnes_total)].copy()
    df_sp = df_estabelecimentos_filtrados[df_estabelecimentos_filtrados['CO_ESTADO_GESTOR'] == '35'].copy()

    # Tratamento de coordenadas
    df_sp['NU_LATITUDE'] = pd.to_numeric(df_sp['NU_LATITUDE'].str.replace(',', '.'), errors='coerce')
    df_sp['NU_LONGITUDE'] = pd.to_numeric(df_sp['NU_LONGITUDE'].str.replace(',', '.'), errors='coerce')
    df_mapeamento = df_sp.dropna(subset=['NU_LATITUDE', 'NU_LONGITUDE'])
    df_mapeamento = df_mapeamento[df_mapeamento['NU_LATITUDE'] != 0]

    # Classificação por categoria para visualização

    # Geração do mapa interativo
    mapa_final = folium.Map(location=[-22.5647, -48.6351], zoom_start=7)
    marker_cluster = MarkerCluster(options={'disableClusteringAtZoom': 17, 'maxClusterRadius': 40}).add_to(mapa_final)

    for index, row in df_mapeamento.iterrows():
        cnes_atual = row['CO_UNIDADE']
        tem_atendimento = cnes_atual in cnes_com_atendimento
        tem_apoio = cnes_atual in cnes_com_apoio
        
        cor = 'gray' # Cor padrão para caso de erro
        categoria = 'Indefinido'
        
        if tem_atendimento and tem_apoio:
            cor = 'purple'; categoria = 'Atendimento (EMAD) e Apoio (EMAP/EMAP-R)'
        elif tem_atendimento:
            cor = 'blue'; categoria = 'Apenas Atendimento (EMAD I/II)'
        elif tem_apoio:
            cor = 'green'; categoria = 'Apenas Apoio (EMAP/EMAP-R)'
            
        popup_text = f"<b>{row.get('NO_FANTASIA', 'N/A')}</b><br>" \
                     f"<b>Equipes:</b> {categoria}<br>" \
                     f"<b>Endereço:</b> {row.get('NO_LOGRADOURO', '')}, {row.get('NU_ENDERECO', '')}<br>" \
                     f"<b>CNES:</b> {row.get('CO_CNES', 'N/A')}"
        
        folium.Marker(
            location=[row['NU_LATITUDE'], row['NU_LONGITUDE']],
            popup=popup_text,
            icon=folium.Icon(color=cor, icon='plus-sign')
        ).add_to(marker_cluster)

    # Legenda HTML
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 380px; height: auto; 
                border:2px solid grey; z-index:9999; font-size:12px;
                background-color:white; opacity: .92; padding: 12px;
                line-height: 1.5;
                ">
                <b style="font-size:14px;">Legenda - Programa Melhor em Casa</b><br><br>
                <i class="fa fa-map-marker fa-2x" style="color:purple"></i>&nbsp; <b>Atendimento + Apoio</b> (EMAD + EMAP)<br>
                <i class="fa fa-map-marker fa-2x" style="color:blue"></i>&nbsp; <b>Apenas EMAD</b> (Equipe de Atendimento)<br>
                <i class="fa fa-map-marker fa-2x" style="color:green"></i>&nbsp; <b>Apenas EMAP</b> (Equipe de Apoio)<br>
                <hr style="margin: 10px 0;">
                <small style="line-height: 1.6;">
                <b>EMAD I/II:</b> Equipe Multidisciplinar de Atenção Domiciliar<br>
                <b>EMAP:</b> Equipe Multiprofissional de Apoio<br>
                <b>EMAP-R:</b> EMAP para Reabilitação<br>
                <i>Fonte: CNES/DataSUS - Competência 2025/08</i>
                </small>
    </div>
    """
    mapa_final.get_root().html.add_child(folium.Element(legend_html))

    nome_arquivo = 'mapa_Equipes_Atencao_Domiciliar_SP.html'
    mapa_final.save(nome_arquivo)
    print(f"Mapa salvo: {nome_arquivo}")

except FileNotFoundError as e:
    print(f"ERRO: O arquivo {e.filename} não foi encontrado.")
except KeyError as e:
    print(f"ERRO: A coluna {e} não foi encontrada.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")