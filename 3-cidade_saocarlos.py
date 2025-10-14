import pandas as pd
from pysus.online_data import CNES
import folium
from geopy.geocoders import Nominatim
import time

# --- DADOS VERIFICADOS ---
# Dicionário com os endereços exatos que encontramos para cada CNES.
enderecos_exatos = {
    '9030026': 'Rua Sete de Setembro, 2241, Centro, São Carlos, SP',
    '2083515': 'Rua Gipsita, 150, Jardim Santa Eufemia, São Carlos, SP',
    '5045614': 'Rua Herbert de Souza, 111, Romeu Santini, São Carlos, SP'
}

# --- CARREGAMENTO E FILTRAGEM DOS DADOS ---
print("Carregando dados de SP e filtrando para São Carlos...")
try:
    parquet_set_sp = CNES.download('ST', 'SP', 2024, 11)
    df_sp = parquet_set_sp.to_dataframe()
    df_sp['CODUFMUN'] = df_sp['CODUFMUN'].astype(str)
    df_cidade_sc = df_sp[df_sp['CODUFMUN'] == '354890'].copy()
    df_domiciliar = df_cidade_sc[df_cidade_sc['TP_UNID'] == '70'].copy()
    print(f"Encontrados {len(df_domiciliar)} estabelecimentos de Atenção Domiciliar.")
except Exception as e:
    print(f"Erro ao carregar dados: {e}")
    exit()

# --- GEOCODIFICAÇÃO PRECISA POR ENDEREÇO ---
if not df_domiciliar.empty:
    print("\nIniciando geocodificação precisa por endereço (será rápido)...")
    geolocator = Nominatim(user_agent="projeto_ic_fernando_endereco_preciso")
    
    # Adicionar a coluna de endereço ao nosso dataframe
    df_domiciliar['ENDERECO_COMPLETO'] = df_domiciliar['CNES'].map(enderecos_exatos)

    coords_dict = {}
    for endereco in df_domiciliar['ENDERECO_COMPLETO'].dropna().unique():
        print(f"Buscando coordenadas para: '{endereco}'")
        try:
            location = geolocator.geocode(endereco, timeout=10)
            time.sleep(1) # Pausa obrigatória de 1 segundo
            if location:
                coords_dict[endereco] = (location.latitude, location.longitude)
        except Exception:
            time.sleep(1)

    df_domiciliar['coords'] = df_domiciliar['ENDERECO_COMPLETO'].map(coords_dict)
    df_mapeamento_preciso = df_domiciliar.dropna(subset=['coords']).copy()
    print(f"Geocodificação concluída. {len(df_mapeamento_preciso)} estabelecimentos foram localizados.")
else:
    df_mapeamento_preciso = pd.DataFrame()

# --- GERAÇÃO DO MAPA FINAL ---
print("\nGerando o mapa final com pinpoint exato...")
mapa_final_preciso = folium.Map(location=[-22.0178, -47.8914], zoom_start=13)

if not df_mapeamento_preciso.empty:
    for index, row in df_mapeamento_preciso.iterrows():
        popup_text = f"<b>CNES:</b> {row.get('CNES', 'N/A')}<br>" \
                     f"<b>Endereço:</b> {row.get('ENDERECO_COMPLETO', 'N/A')}"
        folium.Marker(
            location=row['coords'],
            popup=popup_text,
            icon=folium.Icon(color='green', icon='glyphicon-pushpin', prefix='glyphicon')
        ).add_to(mapa_final_preciso)
else:
    print("Nenhum estabelecimento para plotar no mapa.")

nome_arquivo = 'mapa_sao_carlos_precisao_maxima.html'
mapa_final_preciso.save(nome_arquivo)
print(f"\nSUCESSO! Mapa salvo em: '{nome_arquivo}'")