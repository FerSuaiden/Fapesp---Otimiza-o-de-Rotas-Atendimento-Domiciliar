import pandas as pd
from pysus.online_data import CNES
import folium
from geopy.geocoders import Nominatim
import time

# --- PASSO 1: CARREGAR DADOS DO ESTADO DE SÃO PAULO ---
print("Carregando dados para o estado de São Paulo...")
try:
    parquet_set_sp = CNES.download('ST', 'SP', 2024, 11)
    df_sp = parquet_set_sp.to_dataframe()
    print("Dados de SP carregados.")
except Exception as e:
    print(f"Erro ao carregar dados: {e}")
    exit()

# --- PASSO 2: FILTRAR PARA A CIDADE DE SÃO PAULO E DEPOIS PARA O SERVIÇO ---
print("\nFiltrando estabelecimentos...")

# Código IBGE de 6 dígitos para a CIDADE de São Paulo
codigo_municipio_sp = '355030'

# Garantir que a coluna do município seja string para a comparação
df_sp['CODUFMUN'] = df_sp['CODUFMUN'].astype(str)

# Primeiro, filtre apenas para a cidade de São Paulo
df_cidade_sp = df_sp[df_sp['CODUFMUN'] == codigo_municipio_sp].copy()
print(f"Total de estabelecimentos na cidade de SP: {len(df_cidade_sp)}")

# Agora, filtre apenas os de Atenção Domiciliar
df_domiciliar = df_cidade_sp[df_cidade_sp['TP_UNID'] == '70'].copy()
print(f"Total de estabelecimentos de Atenção Domiciliar na cidade de SP: {len(df_domiciliar)}")

# --- PASSO 3: GEOCODIFICAÇÃO ONLINE (AGORA RÁPIDO) ---
if not df_domiciliar.empty:
    print("\nIniciando geocodificação online por CEP (será rápido)...")
    geolocator = Nominatim(user_agent="projeto_ic_fernando_sp_map")
    cep_cache = {}

    def get_coords(cep):
        cep = str(cep).zfill(8)
        if cep in cep_cache:
            return cep_cache[cep]
        try:
            location = geolocator.geocode(f"{cep[:5]}-{cep[5:]}, Brasil", timeout=10)
            time.sleep(1) # Pausa obrigatória de 1 segundo
            if location:
                coords = (location.latitude, location.longitude)
                cep_cache[cep] = coords
                return coords
            return None
        except Exception:
            time.sleep(1)
            return None

    df_domiciliar['coords'] = df_domiciliar['COD_CEP'].apply(get_coords)
    df_mapeamento_preciso = df_domiciliar.dropna(subset=['coords']).copy()
    print(f"Geocodificação concluída. {len(df_mapeamento_preciso)} estabelecimentos foram localizados.")
else:
    df_mapeamento_preciso = pd.DataFrame() # Cria um DF vazio se não encontrar nada

# --- PASSO 4: GERAR O MAPA DETALHADO ---
print("\nGerando o mapa detalhado para a cidade de São Paulo...")
# Centralizando o mapa na cidade de São Paulo com mais zoom
mapa_preciso_sp = folium.Map(location=[-23.5505, -46.6333], zoom_start=11)

if not df_mapeamento_preciso.empty:
    for index, row in df_mapeamento_preciso.iterrows():
        popup_text = f"<b>CNES:</b> {row.get('CNES', 'N/A')}<br><b>CEP:</b> {row.get('COD_CEP', 'N/A')}"
        folium.Marker(
            location=row['coords'],
            popup=popup_text,
            icon=folium.Icon(color='red', icon='glyphicon-map-marker', prefix='glyphicon')
        ).add_to(mapa_preciso_sp)
else:
    print("Nenhum estabelecimento para plotar no mapa.")

nome_arquivo = 'mapa_detalhado_cidade_sp.html'
mapa_preciso_sp.save(nome_arquivo)

print(f"\nSUCESSO! Mapa salvo em: '{nome_arquivo}'")