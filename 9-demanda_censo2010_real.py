"""
Estimativa de demanda de idosos 60+ por setor censitário de SP Capital
USANDO ESTRUTURA ETÁRIA REAL DO CENSO 2010 + POPULAÇÃO CENSO 2022

Este script:
1. Carrega a estrutura etária por setor do Censo 2010 (pessoa01)
2. Calcula a proporção de idosos 60+ REAL de cada setor
3. Aplica essa proporção à população total do Censo 2022
4. Gera mapa de calor com a demanda estimada

VANTAGEM sobre o script anterior:
- NÃO assume distribuição etária uniforme entre setores
- Usa dados reais de idade por setor do Censo 2010
- Projeta para população 2022 mantendo a estrutura etária relativa

Autor: Assistente IA para projeto FAPESP
Data: Dezembro 2024
"""

import os
import zipfile
import requests
import geopandas as gpd
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
from tqdm import tqdm

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

# Diretórios
DATA_DIR = "IBGE_DATA"
CENSO2010_DIR = os.path.join(DATA_DIR, "censo2010_sp_capital")
CENSO2022_DIR = os.path.join(DATA_DIR, "SP_malha_atributos")

# URLs
URL_CENSO2022_SETORES = "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__702702/censo_2022/uf/sp/SP_Malha_Preliminar_e_Atributos_de_setores_CD2022.zip"
URL_CENSO2010_SP_CAPITAL = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_do_Universo/Agregados_por_Setores_Censitarios/SP_Capital_20231030.zip"

# Arquivos
# pessoa03 contém população TOTAL por faixa etária e cor/raça
ARQUIVO_PESSOA03_CSV = os.path.join(CENSO2010_DIR, "Base informaçoes setores2010 universo SP_Capital", "CSV", "pessoa03_sp1.csv")
ARQUIVO_SETORES_2022 = os.path.join(CENSO2022_DIR, "SP_setores_CD2022.shp")

# Código do município de São Paulo
COD_SP_CAPITAL = "3550308"


# ============================================================================
# FUNÇÕES DE DOWNLOAD
# ============================================================================

def baixar_arquivo(url: str, destino: str) -> bool:
    """Baixa um arquivo da URL especificada."""
    if os.path.exists(destino):
        print(f"✓ Arquivo já existe: {destino}")
        return True
    
    print(f"⬇ Baixando: {os.path.basename(destino)}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(destino, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        return True
    except Exception as e:
        print(f"✗ Erro ao baixar: {e}")
        return False


def extrair_zip(arquivo_zip: str, destino: str) -> bool:
    """Extrai um arquivo ZIP."""
    if not os.path.exists(arquivo_zip):
        print(f"✗ Arquivo não encontrado: {arquivo_zip}")
        return False
    
    try:
        print(f"📦 Extraindo: {os.path.basename(arquivo_zip)}...")
        with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
            zip_ref.extractall(destino)
        return True
    except Exception as e:
        print(f"✗ Erro ao extrair: {e}")
        return False


def preparar_dados() -> bool:
    """Baixa e prepara todos os dados necessários."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Baixar Censo 2022 (setores com geometria e população)
    zip_2022 = os.path.join(DATA_DIR, "SP_setores_CD2022.zip")
    if not os.path.exists(ARQUIVO_SETORES_2022):
        if baixar_arquivo(URL_CENSO2022_SETORES, zip_2022):
            os.makedirs(CENSO2022_DIR, exist_ok=True)
            extrair_zip(zip_2022, CENSO2022_DIR)
    
    # Baixar Censo 2010 (estrutura etária)
    zip_2010 = os.path.join(DATA_DIR, "SP_Capital_2010.zip")
    if not os.path.exists(ARQUIVO_PESSOA03_CSV):
        if baixar_arquivo(URL_CENSO2010_SP_CAPITAL, zip_2010):
            os.makedirs(CENSO2010_DIR, exist_ok=True)
            extrair_zip(zip_2010, CENSO2010_DIR)
    
    return os.path.exists(ARQUIVO_PESSOA03_CSV) and os.path.exists(ARQUIVO_SETORES_2022)


# ============================================================================
# FUNÇÕES DE PROCESSAMENTO
# ============================================================================

def carregar_estrutura_etaria_2010() -> pd.DataFrame:
    """
    Carrega dados de estrutura etária do Censo 2010.
    
    O arquivo pessoa03_sp1.csv contém:
    - V001: Total de pessoas residentes no setor
    - V002-V006: Total por cor/raça (branca, preta, amarela, parda, indígena)
    - V007-V086: População por faixa etária e cor/raça
      - V077-V081: 60-69 anos (por cor/raça)
      - V082-V086: 70+ anos (por cor/raça)
    
    Returns:
        DataFrame com código do setor e proporção de idosos 60+
    """
    print("📊 Carregando estrutura etária do Censo 2010...")
    
    df = pd.read_csv(ARQUIVO_PESSOA03_CSV, sep=';', dtype=str)
    print(f"   Setores carregados: {len(df)}")
    
    # Converter colunas numéricas (tratando 'X' como NaN para setores protegidos)
    for col in df.columns:
        if col.startswith('V'):
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # População 60+ = soma de V077-V081 (60-69 anos) + V082-V086 (70+ anos)
    # Cada faixa tem 5 variáveis (uma por cor/raça: branca, preta, amarela, parda, indígena)
    colunas_60_69 = ['V077', 'V078', 'V079', 'V080', 'V081']
    colunas_70plus = ['V082', 'V083', 'V084', 'V085', 'V086']
    colunas_60plus = colunas_60_69 + colunas_70plus
    
    # Calcular população 60+
    df['pop_60plus_2010'] = df[colunas_60plus].sum(axis=1)
    
    # Calcular proporção de idosos
    df['prop_60plus'] = df['pop_60plus_2010'] / df['V001']
    
    # Tratar setores com população zero ou NaN
    df['prop_60plus'] = df['prop_60plus'].fillna(0)
    df.loc[df['V001'] == 0, 'prop_60plus'] = 0
    
    # Limitar proporção a 100% (dados com erro)
    df.loc[df['prop_60plus'] > 1, 'prop_60plus'] = 1
    
    resultado = df[['Cod_setor', 'V001', 'pop_60plus_2010', 'prop_60plus']].copy()
    resultado.columns = ['cd_setor_2010', 'pop_total_2010', 'pop_60plus_2010', 'prop_60plus']
    resultado['cd_setor_2010'] = resultado['cd_setor_2010'].astype(str)
    
    # Estatísticas
    validos = resultado['prop_60plus'].notna() & (resultado['pop_total_2010'] > 0)
    print(f"   Setores com dados válidos: {validos.sum()}")
    print(f"   Proporção 60+ média: {resultado.loc[validos, 'prop_60plus'].mean()*100:.2f}%")
    print(f"   Proporção 60+ mín-máx: {resultado.loc[validos, 'prop_60plus'].min()*100:.2f}% - {resultado.loc[validos, 'prop_60plus'].max()*100:.2f}%")
    
    return resultado


def carregar_setores_2022() -> gpd.GeoDataFrame:
    """
    Carrega setores censitários do Censo 2022 para SP Capital.
    
    Returns:
        GeoDataFrame com geometria e população dos setores
    """
    print("📍 Carregando setores do Censo 2022...")
    
    gdf = gpd.read_file(ARQUIVO_SETORES_2022)
    
    # Filtrar apenas SP Capital
    gdf = gdf[gdf['CD_MUN'] == COD_SP_CAPITAL].copy()
    print(f"   Setores em SP Capital: {len(gdf)}")
    
    # Converter população para numérico
    gdf['v0001'] = pd.to_numeric(gdf['v0001'], errors='coerce').fillna(0)
    
    # Criar código do setor compatível com Censo 2010
    # CD_SETOR no 2022 tem 21 dígitos, no 2010 tem 15 dígitos
    # Formato 2010: UFMMMMMDDSDSSSSSS (15 dígitos)
    # Formato 2022: UFMMMMMDDSDSSSSSS + sufixo (21 dígitos)
    gdf['cd_setor_match'] = gdf['CD_SETOR'].astype(str).str[:15]
    
    print(f"   População total 2022: {gdf['v0001'].sum():,.0f}")
    
    return gdf


def fazer_correspondencia_setores(gdf_2022: gpd.GeoDataFrame, 
                                   df_2010: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Faz a correspondência entre setores de 2022 e 2010.
    
    Os códigos de setor mudaram entre os censos, mas os primeiros 15 dígitos
    geralmente correspondem. Para setores sem correspondência direta,
    usamos a proporção média do distrito/bairro.
    
    Args:
        gdf_2022: GeoDataFrame dos setores 2022
        df_2010: DataFrame com estrutura etária 2010
        
    Returns:
        GeoDataFrame com proporção de idosos atribuída
    """
    print("🔗 Fazendo correspondência entre setores 2010-2022...")
    
    # Merge direto pelos primeiros 15 dígitos
    gdf = gdf_2022.merge(
        df_2010[['cd_setor_2010', 'prop_60plus']],
        left_on='cd_setor_match',
        right_on='cd_setor_2010',
        how='left'
    )
    
    matched = gdf['prop_60plus'].notna().sum()
    print(f"   Correspondência direta: {matched} setores ({matched/len(gdf)*100:.1f}%)")
    
    # Para setores sem correspondência, usar proporção média do distrito
    # Código do distrito = 9 primeiros dígitos
    gdf['cd_distrito'] = gdf['CD_SETOR'].astype(str).str[:9]
    
    # Calcular média por distrito dos setores com dados
    prop_por_distrito = gdf[gdf['prop_60plus'].notna()].groupby('cd_distrito')['prop_60plus'].mean()
    
    # Preencher setores sem correspondência com média do distrito
    mask_sem_dados = gdf['prop_60plus'].isna()
    for idx in gdf[mask_sem_dados].index:
        distrito = gdf.loc[idx, 'cd_distrito']
        if distrito in prop_por_distrito.index:
            gdf.loc[idx, 'prop_60plus'] = prop_por_distrito[distrito]
    
    # Para setores ainda sem dados, usar média geral
    media_geral = gdf['prop_60plus'].mean()
    gdf['prop_60plus'] = gdf['prop_60plus'].fillna(media_geral)
    
    print(f"   Após preencher com média do distrito: {gdf['prop_60plus'].notna().sum()} setores")
    
    return gdf


def calcular_demanda(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Calcula a demanda de idosos 60+ para cada setor.
    
    Usa a proporção de idosos do Censo 2010 aplicada à população
    total do Censo 2022.
    
    Args:
        gdf: GeoDataFrame com setores e proporção de idosos
        
    Returns:
        GeoDataFrame com demanda calculada
    """
    print("📈 Calculando demanda de idosos 60+...")
    
    # Demanda = População 2022 × Proporção 60+ (do Censo 2010)
    gdf['demanda_60plus'] = (gdf['v0001'] * gdf['prop_60plus']).round(0).astype(int)
    
    # Estatísticas
    total_pop = gdf['v0001'].sum()
    total_demanda = gdf['demanda_60plus'].sum()
    prop_media = total_demanda / total_pop if total_pop > 0 else 0
    
    print(f"   População total 2022: {total_pop:,.0f}")
    print(f"   Demanda total 60+: {total_demanda:,.0f}")
    print(f"   Proporção média efetiva: {prop_media*100:.2f}%")
    print(f"   Demanda média por setor: {gdf['demanda_60plus'].mean():.1f}")
    print(f"   Demanda máxima em setor: {gdf['demanda_60plus'].max()}")
    
    return gdf


def gerar_mapa_calor(gdf: gpd.GeoDataFrame, arquivo_saida: str) -> None:
    """
    Gera mapa de calor da demanda de idosos.
    
    Args:
        gdf: GeoDataFrame com demanda calculada
        arquivo_saida: Caminho do arquivo HTML de saída
    """
    print("🗺️ Gerando mapa de calor...")
    
    # Calcular centroides
    gdf_proj = gdf.to_crs(epsg=31983)  # SIRGAS 2000 / UTM zone 23S
    gdf['centroid'] = gdf_proj.geometry.centroid
    gdf['centroid'] = gdf['centroid'].to_crs(epsg=4326)
    
    # Preparar dados para HeatMap
    heat_data = []
    for idx, row in gdf.iterrows():
        if row['demanda_60plus'] > 0 and row['centroid'] is not None:
            lat = row['centroid'].y
            lon = row['centroid'].x
            # Usar demanda como peso
            heat_data.append([lat, lon, row['demanda_60plus']])
    
    print(f"   Pontos no mapa: {len(heat_data)}")
    
    # Criar mapa base
    centro_sp = [-23.55, -46.63]
    mapa = folium.Map(
        location=centro_sp,
        zoom_start=11,
        tiles='cartodbpositron'
    )
    
    # Adicionar camada de calor
    HeatMap(
        heat_data,
        radius=15,
        blur=10,
        max_zoom=18,
        gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1: 'red'}
    ).add_to(mapa)
    
    # Adicionar título
    titulo = f"""
    <div style="position: fixed; 
                top: 10px; left: 50px; 
                background-color: white; 
                padding: 10px; 
                border-radius: 5px;
                z-index: 1000;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
        <h4 style="margin: 0;">Demanda Estimada de Idosos 60+ - SP Capital</h4>
        <p style="margin: 5px 0 0 0; font-size: 12px;">
            Estrutura etária: Censo 2010 | População: Censo 2022<br>
            Total: {gdf['demanda_60plus'].sum():,.0f} idosos estimados
        </p>
    </div>
    """
    mapa.get_root().html.add_child(folium.Element(titulo))
    
    # Salvar
    mapa.save(arquivo_saida)
    print(f"   ✓ Mapa salvo em: {arquivo_saida}")


def gerar_mapa_coropletico(gdf: gpd.GeoDataFrame, arquivo_saida: str) -> None:
    """
    Gera mapa coroplético mostrando proporção de idosos por setor.
    
    Args:
        gdf: GeoDataFrame com demanda calculada
        arquivo_saida: Caminho do arquivo HTML de saída
    """
    print("🗺️ Gerando mapa coroplético...")
    
    # Reprojetar para WGS84
    gdf_map = gdf.to_crs(epsg=4326)
    
    # Criar mapa base
    centro_sp = [-23.55, -46.63]
    mapa = folium.Map(
        location=centro_sp,
        zoom_start=11,
        tiles='cartodbpositron'
    )
    
    # Adicionar setores como polígonos coloridos
    # Usar proporção de idosos para cor
    folium.Choropleth(
        geo_data=gdf_map.to_json(),
        name='Proporção de Idosos 60+',
        data=gdf_map[['CD_SETOR', 'prop_60plus']],
        columns=['CD_SETOR', 'prop_60plus'],
        key_on='feature.properties.CD_SETOR',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Proporção de Idosos 60+ (%)',
        nan_fill_color='gray'
    ).add_to(mapa)
    
    # Salvar
    mapa.save(arquivo_saida)
    print(f"   ✓ Mapa salvo em: {arquivo_saida}")


def exportar_dados(gdf: gpd.GeoDataFrame, arquivo_csv: str, arquivo_geojson: str) -> None:
    """
    Exporta os dados processados para CSV e GeoJSON.
    
    Args:
        gdf: GeoDataFrame com demanda calculada
        arquivo_csv: Caminho do arquivo CSV de saída
        arquivo_geojson: Caminho do arquivo GeoJSON de saída
    """
    print("💾 Exportando dados...")
    
    # CSV (sem geometria)
    colunas_exportar = [
        'CD_SETOR', 'NM_MUN', 'NM_DIST', 'NM_BAIRRO',
        'v0001', 'prop_60plus', 'demanda_60plus'
    ]
    colunas_existentes = [c for c in colunas_exportar if c in gdf.columns]
    df_export = gdf[colunas_existentes].copy()
    df_export.columns = [
        'cd_setor', 'municipio', 'distrito', 'bairro',
        'pop_total_2022', 'prop_60plus', 'demanda_60plus'
    ][:len(colunas_existentes)]
    df_export.to_csv(arquivo_csv, index=False, encoding='utf-8-sig')
    print(f"   ✓ CSV salvo em: {arquivo_csv}")
    
    # GeoJSON
    gdf_export = gdf[colunas_existentes + ['geometry']].copy()
    gdf_export.to_file(arquivo_geojson, driver='GeoJSON')
    print(f"   ✓ GeoJSON salvo em: {arquivo_geojson}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Função principal do script."""
    print("=" * 70)
    print("ESTIMATIVA DE DEMANDA DE IDOSOS 60+ - SP CAPITAL")
    print("Usando estrutura etária REAL do Censo 2010")
    print("=" * 70)
    print()
    
    # 1. Preparar dados (baixar se necessário)
    if not preparar_dados():
        print("✗ Erro ao preparar dados. Verifique sua conexão.")
        return
    print()
    
    # 2. Carregar estrutura etária do Censo 2010
    df_estrutura_2010 = carregar_estrutura_etaria_2010()
    print()
    
    # 3. Carregar setores do Censo 2022
    gdf_setores_2022 = carregar_setores_2022()
    print()
    
    # 4. Fazer correspondência entre setores
    gdf = fazer_correspondencia_setores(gdf_setores_2022, df_estrutura_2010)
    print()
    
    # 5. Calcular demanda
    gdf = calcular_demanda(gdf)
    print()
    
    # 6. Gerar mapas
    gerar_mapa_calor(gdf, "mapa_demanda_idosos_sp_real.html")
    print()
    
    # 7. Exportar dados
    exportar_dados(
        gdf,
        os.path.join(DATA_DIR, "demanda_idosos_sp_capital.csv"),
        os.path.join(DATA_DIR, "demanda_idosos_sp_capital.geojson")
    )
    print()
    
    print("=" * 70)
    print("✓ Processamento concluído!")
    print("=" * 70)
    
    # Resumo final
    print("\n📊 RESUMO:")
    print(f"   • Setores processados: {len(gdf)}")
    print(f"   • População total 2022: {gdf['v0001'].sum():,.0f}")
    print(f"   • Demanda estimada 60+: {gdf['demanda_60plus'].sum():,.0f}")
    print(f"   • Proporção média: {(gdf['demanda_60plus'].sum()/gdf['v0001'].sum())*100:.2f}%")
    print(f"\n⚠️  NOTA: A proporção de 60+ do Censo 2010 (~11.9%) foi aplicada")
    print(f"   à população 2022. Como a população envelheceu desde 2010,")
    print(f"   a demanda real em 2022 pode ser 15-20% maior.")


if __name__ == "__main__":
    main()
