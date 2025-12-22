"""
DEMANDA DE IDOSOS POR SETOR CENSITÁRIO - CENSO 2022 (DADOS REAIS)
=================================================================

Este script utiliza os dados REAIS do Censo Demográfico 2022 do IBGE
para calcular a demanda de idosos por setor censitário.

VARIÁVEIS DO CENSO 2022 UTILIZADAS:
- V01006: Quantidade de moradores (total)
- V01040: 60 a 69 anos (total ambos sexos)
- V01041: 70 anos ou mais (total ambos sexos)

FONTE: IBGE - Agregados por Setores Censitários 2022
URL: https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/

Autor: Gerado automaticamente
Data: 2025
"""

import pandas as pd
import geopandas as gpd
import os
import requests
import zipfile
import folium
from folium.plugins import HeatMap
import json

# Configurações
IBGE_DIR = "../../IBGE_DATA"
OUTPUT_DIR = "../../IBGE_DATA"

# URLs de download
URL_DEMOGRAFIA_CSV = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/Agregados_por_Setor_csv/Agregados_por_setores_demografia_BR.zip"
URL_MALHA_SP = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/malha_com_atributos/setores/shp/UF/SP/SP_setores_CD2022.zip"


def baixar_arquivo(url, destino_zip, destino_extracao):
    """Baixa e extrai arquivo ZIP do IBGE."""
    if os.path.exists(destino_extracao) and os.listdir(destino_extracao):
        print(f"  ✓ Dados já existem em: {destino_extracao}")
        return True
    
    os.makedirs(destino_extracao, exist_ok=True)
    
    if not os.path.exists(destino_zip):
        print(f"  Baixando: {url}")
        response = requests.get(url, stream=True)
        total = int(response.headers.get('content-length', 0))
        
        with open(destino_zip, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded / total * 100
                    print(f"\r    {pct:.1f}% ({downloaded/1024/1024:.1f} MB)", end='')
        print()
    
    print(f"  Extraindo para: {destino_extracao}")
    with zipfile.ZipFile(destino_zip, 'r') as z:
        z.extractall(destino_extracao)
    
    return True


def carregar_dados_demografia():
    """Carrega dados demográficos do Censo 2022 por setor."""
    
    print("\n[1/5] CARREGANDO DADOS DEMOGRÁFICOS DO CENSO 2022")
    print("="*60)
    
    zip_path = os.path.join(IBGE_DIR, "censo2022_demografia_setores.zip")
    extract_path = os.path.join(IBGE_DIR, "censo2022_setores_demografia")
    
    baixar_arquivo(URL_DEMOGRAFIA_CSV, zip_path, extract_path)
    
    csv_path = os.path.join(extract_path, "Agregados_por_setores_demografia_BR.csv")
    
    print(f"  Lendo CSV: {csv_path}")
    df = pd.read_csv(csv_path, sep=';', encoding='latin-1')
    
    print(f"  ✓ Total de setores no Brasil: {len(df):,}")
    
    return df


def carregar_malha_sp():
    """Carrega a malha de setores censitários de SP do Censo 2022."""
    
    print("\n[2/5] CARREGANDO MALHA DE SETORES CENSITÁRIOS DE SP")
    print("="*60)
    
    zip_path = os.path.join(IBGE_DIR, "SP_Setores_CD2022.zip")
    extract_path = os.path.join(IBGE_DIR, "SP_Setores_CD2022")
    
    baixar_arquivo(URL_MALHA_SP, zip_path, extract_path)
    
    # Encontrar shapefile
    shp_path = None
    for root, dirs, files in os.walk(extract_path):
        for f in files:
            if f.endswith('.shp') and 'setor' in f.lower():
                shp_path = os.path.join(root, f)
                break
    
    if not shp_path:
        # Procurar qualquer shapefile
        for root, dirs, files in os.walk(extract_path):
            for f in files:
                if f.endswith('.shp'):
                    shp_path = os.path.join(root, f)
                    break
    
    print(f"  Lendo shapefile: {shp_path}")
    gdf = gpd.read_file(shp_path)
    
    print(f"  ✓ Total de setores em SP: {len(gdf):,}")
    print(f"  Colunas: {gdf.columns.tolist()}")
    
    return gdf


def filtrar_sp_capital(df_demografia, gdf_malha):
    """Filtra dados para São Paulo Capital."""
    
    print("\n[3/5] FILTRANDO DADOS PARA SÃO PAULO CAPITAL")
    print("="*60)
    
    # Código do município de São Paulo Capital
    COD_SP_CAPITAL = "3550308"
    
    # Filtrar malha para SP Capital
    # Verificar qual coluna tem o código do município
    col_mun = None
    for col in ['CD_MUN', 'cd_mun', 'GEOCODIGO', 'CD_SETOR']:
        if col in gdf_malha.columns:
            col_mun = col
            break
    
    print(f"  Coluna identificadora: {col_mun}")
    
    # Filtrar por município - os 7 primeiros dígitos do setor identificam o município
    if col_mun == 'CD_SETOR':
        gdf_sp = gdf_malha[gdf_malha[col_mun].astype(str).str[:7] == COD_SP_CAPITAL].copy()
    else:
        gdf_sp = gdf_malha[gdf_malha[col_mun].astype(str).str.startswith(COD_SP_CAPITAL)].copy()
    
    print(f"  ✓ Setores em SP Capital (malha): {len(gdf_sp):,}")
    
    # Filtrar demografia para SP Capital
    df_sp = df_demografia[df_demografia['CD_setor'].astype(str).str[:7] == COD_SP_CAPITAL].copy()
    print(f"  ✓ Setores em SP Capital (demografia): {len(df_sp):,}")
    
    return df_sp, gdf_sp


def calcular_demanda_idosos(df_demografia, gdf_malha):
    """Calcula a demanda de idosos por setor usando dados reais do Censo 2022."""
    
    print("\n[4/5] CALCULANDO DEMANDA DE IDOSOS")
    print("="*60)
    
    # Variáveis do Censo 2022:
    # V01006: Quantidade de moradores (total)
    # V01040: 60 a 69 anos (total)
    # V01041: 70 anos ou mais (total)
    
    # IMPORTANTE: Alguns valores são "X" (dado sigiloso/suprimido pelo IBGE)
    # Converter para numérico, tratando "X" como NaN
    def safe_to_numeric(series):
        return pd.to_numeric(series, errors='coerce').fillna(0).astype(int)
    
    # Calcular população idosa (60+)
    df_demografia['populacao_total'] = safe_to_numeric(df_demografia['V01006'])
    df_demografia['pop_60_69'] = safe_to_numeric(df_demografia['V01040'])
    df_demografia['pop_70_mais'] = safe_to_numeric(df_demografia['V01041'])
    df_demografia['populacao_idosa'] = df_demografia['pop_60_69'] + df_demografia['pop_70_mais']
    
    # Calcular proporção de idosos em cada setor
    df_demografia['proporcao_idosos'] = 0.0
    mask = df_demografia['populacao_total'] > 0
    df_demografia.loc[mask, 'proporcao_idosos'] = (
        df_demografia.loc[mask, 'populacao_idosa'] / df_demografia.loc[mask, 'populacao_total']
    )
    
    # Converter código do setor para string
    df_demografia['CD_setor'] = df_demografia['CD_setor'].astype(str)
    
    # Encontrar coluna do setor na malha
    col_setor_malha = None
    for col in ['CD_SETOR', 'cd_setor', 'GEOCODIGO']:
        if col in gdf_malha.columns:
            col_setor_malha = col
            break
    
    gdf_malha[col_setor_malha] = gdf_malha[col_setor_malha].astype(str)
    
    # Merge dos dados
    print(f"  Coluna de junção na malha: {col_setor_malha}")
    
    gdf_resultado = gdf_malha.merge(
        df_demografia[['CD_setor', 'populacao_total', 'pop_60_69', 'pop_70_mais', 
                       'populacao_idosa', 'proporcao_idosos']],
        left_on=col_setor_malha,
        right_on='CD_setor',
        how='left'
    )
    
    # Preencher valores ausentes
    for col in ['populacao_total', 'populacao_idosa', 'pop_60_69', 'pop_70_mais', 'proporcao_idosos']:
        gdf_resultado[col] = gdf_resultado[col].fillna(0)
    
    # Estatísticas
    total_pop = gdf_resultado['populacao_total'].sum()
    total_idosos = gdf_resultado['populacao_idosa'].sum()
    prop_media = total_idosos / total_pop * 100 if total_pop > 0 else 0
    
    print(f"\n  📊 ESTATÍSTICAS SP CAPITAL (CENSO 2022 REAL):")
    print(f"     - População total: {total_pop:,.0f}")
    print(f"     - População 60-69 anos: {gdf_resultado['pop_60_69'].sum():,.0f}")
    print(f"     - População 70+ anos: {gdf_resultado['pop_70_mais'].sum():,.0f}")
    print(f"     - Total de idosos (60+): {total_idosos:,.0f}")
    print(f"     - Proporção média de idosos: {prop_media:.2f}%")
    print(f"     - Setores com dados: {(gdf_resultado['populacao_total'] > 0).sum():,}")
    
    # Estatísticas por setor
    setores_com_idosos = gdf_resultado[gdf_resultado['populacao_idosa'] > 0]
    print(f"\n  📈 DISTRIBUIÇÃO POR SETOR:")
    print(f"     - Setores com idosos: {len(setores_com_idosos):,}")
    print(f"     - Média de idosos/setor: {setores_com_idosos['populacao_idosa'].mean():.1f}")
    print(f"     - Máximo idosos/setor: {setores_com_idosos['populacao_idosa'].max():.0f}")
    print(f"     - Mediana idosos/setor: {setores_com_idosos['populacao_idosa'].median():.0f}")
    
    return gdf_resultado


def gerar_mapa_calor(gdf, output_file):
    """Gera mapa de calor da demanda de idosos."""
    
    print("\n[5/5] GERANDO MAPA DE CALOR")
    print("="*60)
    
    # Centro de SP
    centro_sp = [-23.55, -46.63]
    
    # Criar mapa
    m = folium.Map(location=centro_sp, zoom_start=11, tiles='CartoDB positron')
    
    # Preparar dados para heatmap (centroide de cada setor + peso = pop idosa)
    heat_data = []
    
    gdf_valid = gdf[gdf['populacao_idosa'] > 0].copy()
    
    for idx, row in gdf_valid.iterrows():
        try:
            centroid = row.geometry.centroid
            lat, lon = centroid.y, centroid.x
            # Peso proporcional à população idosa
            weight = row['populacao_idosa']
            heat_data.append([lat, lon, weight])
        except:
            continue
    
    print(f"  ✓ Pontos para heatmap: {len(heat_data):,}")
    
    # Adicionar heatmap
    HeatMap(
        heat_data,
        radius=15,
        blur=10,
        max_zoom=18,
        gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}
    ).add_to(m)
    
    # Adicionar título
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 450px; 
                background-color: white; 
                border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px;
                border-radius: 5px;">
        <b>🗺️ Mapa de Calor - Demanda de Idosos (60+)</b><br>
        <span style="font-size:12px;">
            São Paulo Capital - <b>Censo 2022 (Dados Reais)</b><br>
            Fonte: IBGE - Agregados por Setores Censitários 2022<br>
            <span style="color: red;">🔴 Vermelho</span> = Alta concentração de idosos<br>
            <span style="color: blue;">🔵 Azul</span> = Baixa concentração de idosos
        </span>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Salvar
    m.save(output_file)
    print(f"  ✓ Mapa salvo em: {output_file}")
    
    return m


def salvar_dados(gdf, output_csv, output_geojson):
    """Salva dados processados em CSV e GeoJSON."""
    
    print("\n[EXTRA] SALVANDO DADOS PROCESSADOS")
    print("="*60)
    
    # Selecionar colunas relevantes
    cols_export = ['CD_setor', 'populacao_total', 'pop_60_69', 'pop_70_mais', 
                   'populacao_idosa', 'proporcao_idosos']
    
    # Encontrar coluna do setor
    col_setor = None
    for col in ['CD_SETOR', 'cd_setor', 'GEOCODIGO']:
        if col in gdf.columns:
            col_setor = col
            break
    
    if col_setor and 'CD_setor' not in gdf.columns:
        gdf['CD_setor'] = gdf[col_setor]
    
    # Salvar CSV
    df_export = gdf[[c for c in cols_export if c in gdf.columns]].copy()
    df_export.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"  ✓ CSV salvo: {output_csv}")
    
    # Salvar GeoJSON
    gdf_export = gdf[[c for c in cols_export + ['geometry'] if c in gdf.columns]].copy()
    gdf_export.to_file(output_geojson, driver='GeoJSON')
    print(f"  ✓ GeoJSON salvo: {output_geojson}")


def main():
    """Função principal."""
    
    print("="*70)
    print("   DEMANDA DE IDOSOS - CENSO 2022 (DADOS REAIS)")
    print("   São Paulo Capital - Agregados por Setor Censitário")
    print("="*70)
    
    # 1. Carregar dados demográficos
    df_demografia = carregar_dados_demografia()
    
    # 2. Carregar malha de setores
    gdf_malha = carregar_malha_sp()
    
    # 3. Filtrar para SP Capital
    df_sp, gdf_sp = filtrar_sp_capital(df_demografia, gdf_malha)
    
    # 4. Calcular demanda de idosos
    gdf_resultado = calcular_demanda_idosos(df_sp, gdf_sp)
    
    # 5. Gerar mapa de calor
    output_map = "mapa_demanda_idosos_sp_censo2022.html"
    gerar_mapa_calor(gdf_resultado, output_map)
    
    # 6. Salvar dados
    output_csv = os.path.join(OUTPUT_DIR, "demanda_idosos_sp_censo2022.csv")
    output_geojson = os.path.join(OUTPUT_DIR, "demanda_idosos_sp_censo2022.geojson")
    salvar_dados(gdf_resultado, output_csv, output_geojson)
    
    print("\n" + "="*70)
    print("   ✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
    print("="*70)
    print(f"\n   Arquivos gerados:")
    print(f"   - {output_map}")
    print(f"   - {output_csv}")
    print(f"   - {output_geojson}")
    print()


if __name__ == "__main__":
    main()
