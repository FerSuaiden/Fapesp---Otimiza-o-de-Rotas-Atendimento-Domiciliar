"""
Script para estimar demanda de Atenção Domiciliar usando dados REAIS de idade por setor censitário.

SOLUÇÃO: Utiliza a estrutura etária do Censo 2010 (disponível por setor) para calcular
proporções REAIS de idosos por setor, projetando para a população do Censo 2022.

Diferente do script 7, este NÃO assume distribuição uniforme de idosos.
Cada setor terá sua própria proporção de idosos baseada nos dados reais de 2010.

Autor: Assistente (baseado em requisitos do projeto FAPESP)
Data: 2025
"""

import os
import requests
import zipfile
import io
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import HeatMap
import warnings
warnings.filterwarnings('ignore')

# Diretório de trabalho
DATA_DIR = "IBGE_DATA"
os.makedirs(DATA_DIR, exist_ok=True)


def baixar_censo2010_sp_capital():
    """Baixa os dados de pessoas por faixa etária do Censo 2010 para SP Capital."""
    
    output_dir = os.path.join(DATA_DIR, "censo2010_sp_capital")
    csv_dir = os.path.join(output_dir, "Base informaçoes setores2010 universo SP_Capital", "CSV")
    
    # Verificar se já existe
    if os.path.exists(csv_dir) and os.path.exists(os.path.join(csv_dir, "pessoa01_sp1.csv")):
        print("✓ Dados do Censo 2010 (SP Capital) já baixados")
        return csv_dir
    
    print("Baixando dados do Censo 2010 para SP Capital...")
    print("(Este arquivo tem ~30MB, pode demorar alguns minutos)")
    
    url = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_do_Universo/Agregados_por_Setores_Censitarios/SP_Capital_20231030.zip"
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    os.makedirs(output_dir, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        zf.extractall(output_dir)
    
    print(f"✓ Dados extraídos em: {csv_dir}")
    return csv_dir


def baixar_censo2010_sp_exceto_capital():
    """Baixa os dados de pessoas por faixa etária do Censo 2010 para SP (exceto Capital)."""
    
    output_dir = os.path.join(DATA_DIR, "censo2010_sp_exceto_capital")
    
    # O arquivo pode ter estrutura diferente
    if os.path.exists(output_dir):
        # Procurar o diretório CSV
        for root, dirs, files in os.walk(output_dir):
            if "pessoa01" in str(files).lower():
                print("✓ Dados do Censo 2010 (SP exceto Capital) já baixados")
                return root
    
    print("Baixando dados do Censo 2010 para SP (exceto Capital)...")
    print("(Este arquivo é grande ~150MB, pode demorar vários minutos)")
    
    url = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_do_Universo/Agregados_por_Setores_Censitarios/SP_Exceto_Capital_20231030.zip"
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    os.makedirs(output_dir, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        zf.extractall(output_dir)
    
    # Encontrar o diretório CSV
    for root, dirs, files in os.walk(output_dir):
        if any("pessoa01" in f.lower() for f in files):
            print(f"✓ Dados extraídos em: {root}")
            return root
    
    return output_dir


def carregar_estrutura_etaria_2010(csv_dir):
    """
    Carrega dados de estrutura etária por setor do Censo 2010.
    
    Estrutura dos arquivos (baseado na análise empírica):
    - pessoa01: V001=Total geral, V002-V085=Homens por idade (0-83 anos)
    - pessoa02: V086=Total mulheres, V087-V170=Mulheres por idade (0-83 anos)
    
    Para idosos (60+), precisamos somar:
    - Homens 60+: V062 a V085 (pessoa01) - colunas 62 a 85 = idades 60 a 83+
    - Mulheres 60+: V147 a V170 (pessoa02) - colunas 147 a 170 = idades 60 a 83+
    
    Retorna DataFrame com: Cod_setor, pop_total_2010, pop_idosos_2010, proporcao_idosos_2010
    """
    print("Carregando estrutura etária do Censo 2010...")
    
    # Encontrar os arquivos pessoa01 e pessoa02
    pessoa01_path = None
    pessoa02_path = None
    for root, dirs, files in os.walk(csv_dir):
        for f in files:
            if 'pessoa01' in f.lower() and f.endswith('.csv'):
                pessoa01_path = os.path.join(root, f)
            if 'pessoa02' in f.lower() and f.endswith('.csv'):
                pessoa02_path = os.path.join(root, f)
    
    if pessoa01_path is None:
        raise FileNotFoundError(f"Arquivo pessoa01 não encontrado em {csv_dir}")
    
    print(f"  Lendo: {pessoa01_path}")
    df1 = pd.read_csv(pessoa01_path, sep=';', encoding='latin1')
    
    if pessoa02_path:
        print(f"  Lendo: {pessoa02_path}")
        df2 = pd.read_csv(pessoa02_path, sep=';', encoding='latin1')
    else:
        df2 = None
    
    # Converter todas as colunas V para numérico
    for col in df1.columns:
        if col.startswith('V'):
            df1[col] = pd.to_numeric(df1[col], errors='coerce').fillna(0)
    
    if df2 is not None:
        for col in df2.columns:
            if col.startswith('V'):
                df2[col] = pd.to_numeric(df2[col], errors='coerce').fillna(0)
    
    # V001 = população total do setor
    df1['pop_total_2010'] = df1['V001']
    
    # Idosos homens (60+): V062 a V085 (24 colunas)
    # Interpretação: V002=0 anos, V003=1 ano, ..., V062=60 anos, ..., V085=83+ anos
    idosos_homens_cols = [f'V{str(i).zfill(3)}' for i in range(62, 86)]
    idosos_homens_cols = [c for c in idosos_homens_cols if c in df1.columns]
    df1['idosos_homens'] = df1[idosos_homens_cols].sum(axis=1)
    
    # Idosos mulheres (60+): V147 a V170 (pessoa02)
    # Interpretação: V087=0 anos mulheres, ..., V147=60 anos, ..., V170=83+ anos
    df1['idosos_mulheres'] = 0
    if df2 is not None:
        idosos_mulheres_cols = [f'V{str(i).zfill(3)}' for i in range(147, 171)]
        idosos_mulheres_cols = [c for c in idosos_mulheres_cols if c in df2.columns]
        
        if idosos_mulheres_cols:
            # Merge com df1
            df2_subset = df2[['Cod_setor'] + idosos_mulheres_cols].copy()
            df2_subset['idosos_mulheres'] = df2_subset[idosos_mulheres_cols].sum(axis=1)
            df1 = df1.merge(df2_subset[['Cod_setor', 'idosos_mulheres']], on='Cod_setor', how='left', suffixes=('', '_y'))
            if 'idosos_mulheres_y' in df1.columns:
                df1['idosos_mulheres'] = df1['idosos_mulheres_y'].fillna(0)
                df1 = df1.drop('idosos_mulheres_y', axis=1)
    
    # Total de idosos
    df1['pop_idosos_2010'] = df1['idosos_homens'] + df1['idosos_mulheres']
    
    # Calcular proporção de idosos
    df1['proporcao_idosos_2010'] = df1['pop_idosos_2010'] / df1['pop_total_2010']
    df1['proporcao_idosos_2010'] = df1['proporcao_idosos_2010'].fillna(0)
    # Limitar a valores válidos (0 a 1)
    df1['proporcao_idosos_2010'] = df1['proporcao_idosos_2010'].clip(0, 1)
    
    # Manter apenas colunas necessárias
    resultado = df1[['Cod_setor', 'pop_total_2010', 'pop_idosos_2010', 'proporcao_idosos_2010']].copy()
    resultado['Cod_setor'] = resultado['Cod_setor'].astype(str)
    
    print(f"  ✓ Carregados {len(resultado)} setores")
    print(f"  Proporção média de idosos: {resultado['proporcao_idosos_2010'].mean()*100:.2f}%")
    print(f"  Proporção mínima: {resultado['proporcao_idosos_2010'].min()*100:.2f}%")
    print(f"  Proporção máxima: {resultado['proporcao_idosos_2010'].max()*100:.2f}%")
    
    return resultado


def baixar_malha_setores_2022(uf="SP"):
    """Baixa a malha de setores censitários do Censo 2022 com atributos populacionais."""
    
    output_dir = os.path.join(DATA_DIR, f"{uf}_malha_atributos")
    
    # Verificar se já existe
    shapefile_path = os.path.join(output_dir, f"{uf}_setores_CD2022.shp")
    if os.path.exists(shapefile_path):
        print(f"✓ Malha 2022 já baixada: {shapefile_path}")
        return shapefile_path
    
    print(f"Baixando malha de setores 2022 para {uf}...")
    
    # URLs do IBGE
    malha_url = f"https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__702930328/Censo_2022/Uf/{uf}/{uf}_setores_CD2022.zip"
    atributos_url = f"https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__702930328/Censo_2022/Uf/{uf}/{uf}_setores_atributos_CD2022.zip"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Baixar malha
    print("  Baixando geometria...")
    response = requests.get(malha_url)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        zf.extractall(output_dir)
    
    # Baixar atributos
    print("  Baixando atributos populacionais...")
    response = requests.get(atributos_url)
    response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        zf.extractall(output_dir)
    
    print(f"✓ Dados 2022 extraídos em: {output_dir}")
    return shapefile_path


def criar_correspondencia_setores_2010_2022(setores_2010, setores_2022):
    """
    Cria correspondência entre setores de 2010 e 2022.
    
    Os códigos de setor podem ter mudado entre os censos.
    Usamos o código do município e distrito para criar uma correspondência aproximada.
    
    Estratégias:
    1. Match exato: mesmo código de setor
    2. Match por município/distrito: usar média da proporção de idosos do município/distrito
    """
    print("Criando correspondência entre setores 2010 e 2022...")
    
    # Extrair código do município (7 primeiros dígitos do código de setor 2010)
    setores_2010['cod_mun'] = setores_2010['Cod_setor'].str[:7]
    setores_2010['cod_distrito'] = setores_2010['Cod_setor'].str[:9]
    
    # Calcular proporção média por município e distrito
    prop_por_municipio = setores_2010.groupby('cod_mun')['proporcao_idosos_2010'].mean().to_dict()
    prop_por_distrito = setores_2010.groupby('cod_distrito')['proporcao_idosos_2010'].mean().to_dict()
    
    # Criar dicionário de proporções por setor
    prop_por_setor = setores_2010.set_index('Cod_setor')['proporcao_idosos_2010'].to_dict()
    
    # Para cada setor 2022, encontrar a proporção de idosos
    def obter_proporcao_idosos(cod_setor_2022):
        cod_setor = str(cod_setor_2022)
        
        # Tentar match exato
        if cod_setor in prop_por_setor:
            return prop_por_setor[cod_setor], 'exato'
        
        # Tentar match por distrito
        cod_distrito = cod_setor[:9]
        if cod_distrito in prop_por_distrito:
            return prop_por_distrito[cod_distrito], 'distrito'
        
        # Tentar match por município
        cod_mun = cod_setor[:7]
        if cod_mun in prop_por_municipio:
            return prop_por_municipio[cod_mun], 'municipio'
        
        # Retornar média geral do estado
        return setores_2010['proporcao_idosos_2010'].mean(), 'estado'
    
    # Aplicar correspondência
    resultados = []
    for _, row in setores_2022.iterrows():
        prop, tipo_match = obter_proporcao_idosos(row['CD_SETOR'])
        resultados.append({
            'CD_SETOR': row['CD_SETOR'],
            'proporcao_idosos_2010': prop,
            'tipo_match': tipo_match
        })
    
    df_correspondencia = pd.DataFrame(resultados)
    
    # Estatísticas de correspondência
    print(f"  Correspondências encontradas:")
    for tipo in ['exato', 'distrito', 'municipio', 'estado']:
        n = (df_correspondencia['tipo_match'] == tipo).sum()
        pct = n / len(df_correspondencia) * 100
        print(f"    {tipo}: {n:,} ({pct:.1f}%)")
    
    return df_correspondencia


def estimar_demanda_projetada(gdf_2022, correspondencia, taxa_utilizacao=0.05):
    """
    Estima a demanda de Atenção Domiciliar usando projeção dos dados de 2010.
    
    Args:
        gdf_2022: GeoDataFrame com setores do Censo 2022 e população total (v0001)
        correspondencia: DataFrame com proporção de idosos por setor (baseada em 2010)
        taxa_utilizacao: proporção de idosos que utilizam AD (padrão 5%)
    
    Returns:
        GeoDataFrame com estimativas de demanda
    """
    print("Estimando demanda com projeção 2010->2022...")
    
    # Merge com correspondência
    gdf = gdf_2022.merge(correspondencia, on='CD_SETOR', how='left')
    
    # Preencher valores faltantes com média
    media_prop = correspondencia['proporcao_idosos_2010'].mean()
    gdf['proporcao_idosos_2010'] = gdf['proporcao_idosos_2010'].fillna(media_prop)
    
    # Estimar população de idosos em 2022
    # Usando proporção de 2010 aplicada à população total de 2022
    gdf['pop_total_2022'] = gdf['v0001']
    gdf['pop_idosos_estimada'] = gdf['pop_total_2022'] * gdf['proporcao_idosos_2010']
    
    # Estimar demanda
    gdf['demanda_estimada'] = gdf['pop_idosos_estimada'] * taxa_utilizacao
    
    # Estatísticas
    total_pop = gdf['pop_total_2022'].sum()
    total_idosos = gdf['pop_idosos_estimada'].sum()
    total_demanda = gdf['demanda_estimada'].sum()
    
    print(f"\n=== RESULTADOS ===")
    print(f"  População total 2022: {total_pop:,.0f}")
    print(f"  Idosos estimados (60+): {total_idosos:,.0f}")
    print(f"  Proporção média de idosos: {total_idosos/total_pop*100:.2f}%")
    print(f"  Demanda estimada (AD): {total_demanda:,.0f}")
    print(f"\n  Taxa de utilização assumida: {taxa_utilizacao*100:.1f}%")
    
    return gdf


def criar_mapa_calor(gdf, output_path):
    """Cria mapa de calor da demanda por setor."""
    print("Criando mapa de calor...")
    
    # Calcular centroide de cada setor
    gdf['centroid'] = gdf.geometry.centroid
    
    # Filtrar setores com demanda > 0
    gdf_demanda = gdf[gdf['demanda_estimada'] > 0].copy()
    
    # Criar dados para heatmap
    heat_data = []
    for _, row in gdf_demanda.iterrows():
        if row['centroid'] is not None:
            lat = row['centroid'].y
            lon = row['centroid'].x
            peso = row['demanda_estimada']
            heat_data.append([lat, lon, peso])
    
    # Calcular centro do mapa
    center_lat = gdf_demanda['centroid'].y.mean()
    center_lon = gdf_demanda['centroid'].x.mean()
    
    # Criar mapa
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
    
    # Adicionar heatmap
    HeatMap(heat_data, 
            radius=15,
            blur=10,
            max_zoom=18,
            gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1: 'red'}
    ).add_to(m)
    
    # Salvar
    m.save(output_path)
    print(f"✓ Mapa salvo em: {output_path}")
    
    return m


def main():
    """Execução principal do script."""
    print("="*60)
    print("ESTIMATIVA DE DEMANDA COM DADOS REAIS DE IDADE (CENSO 2010)")
    print("="*60)
    print()
    
    # 1. Baixar dados do Censo 2010
    csv_dir_capital = baixar_censo2010_sp_capital()
    
    # 2. Carregar estrutura etária
    print()
    estrutura_2010 = carregar_estrutura_etaria_2010(csv_dir_capital)
    
    # 3. Baixar malha do Censo 2022
    print()
    shapefile_2022 = baixar_malha_setores_2022("SP")
    
    # 4. Carregar malha 2022
    print("\nCarregando malha de setores 2022...")
    gdf_2022 = gpd.read_file(shapefile_2022)
    
    # Filtrar apenas SP Capital (código do município = 3550308)
    gdf_sp_capital = gdf_2022[gdf_2022['CD_SETOR'].str.startswith('3550308')].copy()
    print(f"  Setores em SP Capital (2022): {len(gdf_sp_capital)}")
    
    # 5. Criar correspondência entre censos
    print()
    correspondencia = criar_correspondencia_setores_2010_2022(estrutura_2010, gdf_sp_capital)
    
    # 6. Estimar demanda
    print()
    gdf_demanda = estimar_demanda_projetada(gdf_sp_capital, correspondencia)
    
    # 7. Salvar resultados
    print("\nSalvando resultados...")
    
    # Salvar CSV
    csv_path = os.path.join(DATA_DIR, "demanda_projetada_sp_capital.csv")
    cols_salvar = ['CD_SETOR', 'NM_BAIRRO', 'pop_total_2022', 'proporcao_idosos_2010', 
                   'pop_idosos_estimada', 'demanda_estimada', 'tipo_match']
    cols_existentes = [c for c in cols_salvar if c in gdf_demanda.columns]
    gdf_demanda[cols_existentes].to_csv(csv_path, index=False)
    print(f"  ✓ CSV: {csv_path}")
    
    # Criar mapa de calor
    mapa_path = "mapa_demanda_projetada_sp_capital.html"
    criar_mapa_calor(gdf_demanda, mapa_path)
    
    print("\n" + "="*60)
    print("PROCESSO CONCLUÍDO")
    print("="*60)
    print()
    print("IMPORTANTE: Esta estimativa usa a estrutura etária REAL do Censo 2010,")
    print("projetada para a população total de 2022. Setores com mais idosos em 2010")
    print("terão mais demanda estimada do que setores com menos idosos.")
    print()


if __name__ == "__main__":
    main()
