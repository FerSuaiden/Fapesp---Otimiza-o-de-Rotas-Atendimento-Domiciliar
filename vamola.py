import pandas as pd
import folium
from folium.plugins import MarkerCluster

print("Carregando a base de dados local 'cnes_completo.csv'...")
try:
    df_brasil = pd.read_csv('cnes_completo.csv', sep=';', encoding='latin-1', dtype=str)
    print("Base de dados carregada.")
    
    df_domiciliar_br = df_brasil[df_brasil['TP_UNIDADE'] == '22'].copy()
    print(f"Total de estabelecimentos de Atenção Domiciliar: {len(df_domiciliar_br)}")
    
    df_domiciliar_br['NU_LATITUDE'] = pd.to_numeric(df_domiciliar_br['NU_LATITUDE'].str.replace(',', '.'), errors='coerce')
    df_domiciliar_br['NU_LONGITUDE'] = pd.to_numeric(df_domiciliar_br['NU_LONGITUDE'].str.replace(',', '.'), errors='coerce')
    
    df_mapeamento = df_domiciliar_br.dropna(subset=['NU_LATITUDE', 'NU_LONGITUDE'])
    df_mapeamento = df_mapeamento[df_mapeamento['NU_LATITUDE'] != 0]
    print(f"Total de estabelecimentos com coordenadas válidas: {len(df_mapeamento)}")
except Exception as e:
    print(f"Ocorreu um erro: {e}")
    exit()

print("\nGerando o mapa interativo com cluster menos agressivo...")
mapa_final = folium.Map(location=[-14.2350, -51.9253], zoom_start=4)

# Aumentamos o nível de zoom para desativar e diminuímos o raio de agrupamento.
marker_cluster = MarkerCluster(
    options={
        'disableClusteringAtZoom': 17, 
        'maxClusterRadius': 40      
    }
).add_to(mapa_final)

for index, row in df_mapeamento.iterrows():
    popup_text = f"<b>{row.get('NO_FANTASIA', 'N/A')}</b><br>" \
                 f"<b>Endereço:</b> {row.get('NO_LOGRADOURO', '')}, {row.get('NU_ENDERECO', '')}<br>" \
                 f"<b>CNES:</b> {row.get('CO_CNES', 'N/A')}"
    
    folium.Marker(
        location=[row['NU_LATITUDE'], row['NU_LONGITUDE']],
        popup=popup_text,
    ).add_to(marker_cluster)

nome_arquivo = 'mapa_cluster_super_detalhado.html'
mapa_final.save(nome_arquivo)

print(f"\nSUCESSO! Mapa final salvo no arquivo: '{nome_arquivo}'")