import pandas as pd
import folium
from folium.plugins import MarkerCluster

print("Iniciando o mapeamento completo: EMAD (I/II), EMAP e EMAP-R...")

try:
    # --- ETAPA 1: CARREGAR AS BASES DE DADOS ---
    print("\n--- ETAPA 1: Carregando Arquivos ---")
    df_estabelecimentos = pd.read_csv('cnes_completo.csv', sep=';', encoding='latin-1', dtype=str)    
    df_equipes = pd.read_csv('./CNES_DATA/tbEquipe202508.csv', sep=';', encoding='latin-1', dtype=str)

    # --- ETAPA 2: IDENTIFICAR EQUIPES ---    
    codigos_atendimento = ['22', '46'] # EMAD I e EMAD II
    codigos_apoio = ['23', '77']       # EMAP e EMAP-R

    # Cria os conjuntos de CNES para cada categoria
    cnes_com_atendimento = set(df_equipes[df_equipes['TP_EQUIPE'].isin(codigos_atendimento)]['CO_UNIDADE'].unique())
    print(f"  - Total de estabelecimentos com equipes de ATENDIMENTO (EMAD): {len(cnes_com_atendimento)}")

    cnes_com_apoio = set(df_equipes[df_equipes['TP_EQUIPE'].isin(codigos_apoio)]['CO_UNIDADE'].unique())
    print(f"  - Total de estabelecimentos com equipes de APOIO (EMAP/EMAP-R): {len(cnes_com_apoio)}")

    # Lista total de CNES relevantes (união dos dois conjuntos)
    lista_cnes_total = list(cnes_com_atendimento.union(cnes_com_apoio))
    print(f"  - Total de estabelecimentos únicos com pelo menos uma das equipes: {len(lista_cnes_total)}")

    # --- ETAPA 3: FILTRAR PARA SÃO PAULO ---
    print("\n--- ETAPA 3: Filtrando para São Paulo ---")
    df_estabelecimentos_filtrados = df_estabelecimentos[df_estabelecimentos['CO_UNIDADE'].isin(lista_cnes_total)].copy()
    df_sp = df_estabelecimentos_filtrados[df_estabelecimentos_filtrados['CO_UF'] == '35'].copy()
    print(f"  - Total de estabelecimentos relevantes encontrados em SP: {len(df_sp)}")

    # --- ETAPA 4: PREPARAR COORDENADAS ---
    print("\n--- ETAPA 4: Preparando Coordenadas ---")
    df_sp['NU_LATITUDE'] = pd.to_numeric(df_sp['NU_LATITUDE'].str.replace(',', '.'), errors='coerce')
    df_sp['NU_LONGITUDE'] = pd.to_numeric(df_sp['NU_LONGITUDE'].str.replace(',', '.'), errors='coerce')

    df_mapeamento = df_sp.dropna(subset=['NU_LATITUDE', 'NU_LONGITUDE'])
    df_mapeamento = df_mapeamento[df_mapeamento['NU_LATITUDE'] != 0]
    print(f"  - Total de estabelecimentos com coordenadas válidas para o mapa: {len(df_mapeamento)}")

    # --- ETAPA 5: DIAGNÓSTICO DAS CATEGORIAS EM SP ---
    print("\n--- ETAPA 5: DIAGNÓSTICO FINAL DAS CATEGORias EM SP ---")
    contador = {'Apenas Atendimento': 0, 'Apenas Apoio': 0, 'Ambos': 0}
    
    for index, row in df_mapeamento.iterrows():
        cnes_atual = row['CO_UNIDADE']
        tem_atendimento = cnes_atual in cnes_com_atendimento
        tem_apoio = cnes_atual in cnes_com_apoio
        
        if tem_atendimento and tem_apoio:
            contador['Ambos'] += 1
        elif tem_atendimento:
            contador['Apenas Atendimento'] += 1
        elif tem_apoio:
            contador['Apenas Apoio'] += 1
            
    print(f"  - RESULTADO: Estabelecimentos com AMBOS (Roxo): {contador['Ambos']}")
    print(f"  - RESULTADO: Estabelecimentos com APENAS ATENDIMENTO (Azul): {contador['Apenas Atendimento']}")
    print(f"  - RESULTADO: Estabelecimentos com APENAS APOIO (Verde): {contador['Apenas Apoio']}")
    print("---------------------------------------------------------")

    # --- ETAPA 6: GERAR O MAPA ---
    print("\n--- ETAPA 6: Gerando o mapa... ---")
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

    # --- ETAPA 7: ADICIONAR LEGENDA AO MAPA ---
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 260px; height: 100px; 
                border:2px solid grey; z-index:9999; font-size:14px;
                background-color:white; opacity: .85;
                ">&nbsp; <b>Legenda - Tipos de Equipe</b><br>
                &nbsp; <i class="fa fa-map-marker fa-2x" style="color:purple"></i>&nbsp; Atendimento e Apoio<br>
                &nbsp; <i class="fa fa-map-marker fa-2x" style="color:blue"></i>&nbsp; Apenas Atendimento (EMAD)<br>
                &nbsp; <i class="fa fa-map-marker fa-2x" style="color:green"></i>&nbsp; Apenas Apoio (EMAP/EMAP-R)
    </div>
    """
    mapa_final.get_root().html.add_child(folium.Element(legend_html))

    nome_arquivo = 'mapa_Equipes_Atencao_Domiciliar_SP.html'
    mapa_final.save(nome_arquivo)

    print(f"\nSUCESSO! O mapa atualizado foi salvo no arquivo: '{nome_arquivo}'")

except FileNotFoundError as e:
    print(f"ERRO: O arquivo {e.filename} não foi encontrado.")
except KeyError as e:
    print(f"ERRO: A coluna {e} não foi encontrada.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")