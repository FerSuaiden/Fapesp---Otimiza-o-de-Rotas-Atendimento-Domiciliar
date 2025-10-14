import pandas as pd
from pysus.online_data import CNES
import folium

# --- PASSO 1: CARREGAR DADOS DE TODO O BRASIL (usará o cache) ---
print("Iniciando a coleta de dados para todo o Brasil...")
estados_br = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 
              'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 
              'SP', 'SE', 'TO']

lista_dfs = []
for estado in estados_br:
    try:
        #print(f"Carregando dados para o estado: {estado}...") # Opcional
        parquet_set = CNES.download('ST', estado, 2024, 11)
        df_estado = parquet_set.to_dataframe()
        lista_dfs.append(df_estado)
    except Exception as e:
        #print(f"Não foi possível carregar os dados para {estado}. Pulando.") # Opcional
        pass

df_brasil = pd.concat(lista_dfs, ignore_index=True)
print("\nDados do Brasil carregados.")

# --- PASSO 2: FILTRAR E AGRUPAR OS DADOS DE INTERESSE ---
df_domiciliar_br = df_brasil[df_brasil['TP_UNID'] == '70'].copy()
contagem_por_municipio = df_domiciliar_br.groupby('CODUFMUN').size().reset_index(name='contagem')
print(f"Encontrados serviços em {len(contagem_por_municipio)} municípios diferentes.")

# --- PASSO 3: GEOCODIFICAÇÃO LOCAL (COM CHAVE CORRIGIDA) ---
print("\nIniciando geocodificação local a partir do arquivo 'municipios.csv'...")

try:
    df_municipios = pd.read_csv('municipios.csv')
except FileNotFoundError:
    print("\nERRO: Arquivo 'municipios.csv' não encontrado!")
    exit()

# --- CORREÇÃO CRUCIAL AQUI ---
# Garantir que a chave de junção seja uma STRING DE 6 DÍGITOS em ambas as tabelas.

# Na tabela do DATASUS, 'CODUFMUN' já parece ser um código de 6 dígitos. Apenas garantimos que é string.
contagem_por_municipio['chave_merge'] = contagem_por_municipio['CODUFMUN'].astype(str)

# Na sua tabela de municípios, 'codigo_ibge' é um número de 7 dígitos. Convertemos para string e pegamos os 6 primeiros.
df_municipios['chave_merge'] = df_municipios['codigo_ibge'].astype(str).str[:6]

# Juntar as duas tabelas usando a nova 'chave_merge'
dados_para_mapa = pd.merge(contagem_por_municipio, df_municipios, on='chave_merge', how='inner')

# Print de verificação
print(f"Geocodificação concluída. {len(dados_para_mapa)} municípios foram localizados com sucesso.")
if len(dados_para_mapa) == 0:
    print("ALERTA: A junção dos dados falhou. Nenhum ponto será desenhado no mapa.")
    exit()


# --- PASSO 4: GERAR O MAPA COMPLETO ---
print("\nGerando o mapa interativo completo...")
mapa_completo = folium.Map(location=[-14.2350, -51.9253], zoom_start=4)

for index, row in dados_para_mapa.iterrows():
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=3 + (row['contagem'] / 2),
        popup=f"<b>{row['nome']}</b><br>Serviços: {row['contagem']}",
        color='#003366',
        fill=True,
        fill_opacity=0.7
    ).add_to(mapa_completo)

nome_arquivo = 'mapa_completo_brasil.html'
mapa_completo.save(nome_arquivo)

print(f"\nSUCESSO! Mapa completo salvo no arquivo: '{nome_arquivo}'")