"""
Script para obter dados de DEMANDA do IBGE - Setores Censitários e População
================================================================================

Este script automatiza o processo de:
1. Baixar a malha de setores censitários (polígonos geográficos)
2. Baixar os dados agregados por setores censitários (população)
3. Processar e filtrar os dados para a área de interesse
4. Identificar a população-alvo (ex: idosos) por setor censitário

Autor: Gerado automaticamente para o projeto de Otimização de Rotas AD
Data: Dezembro 2025
"""

import os
import requests
import zipfile
import geopandas as gpd
import pandas as pd
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

# Código da UF (35 = São Paulo)
CODIGO_UF = "35"
SIGLA_UF = "SP"

# Pasta para salvar os downloads
PASTA_IBGE = "./IBGE_DATA"

# URLs do IBGE para download
URLS_IBGE = {
    # Malha de Setores Censitários do Censo 2022 por UF
    "malha_setores_shp": f"https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/setores/shp/UF/{SIGLA_UF}_setores_CD2022.zip",
    
    # Dados agregados por setores censitários (CSV) - contém população
    # Os arquivos estão organizados por UF ou Brasil
    "agregados_setores_csv_brasil": "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/Agregados_por_Setor_csv/",
    
    # Dicionário de dados
    "dicionario_dados": "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/dicionario_de_dados_agregados_por_setores.xlsx",
    
    # Malha com atributos já integrados (alternativa mais prática)
    "malha_com_atributos": "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/malha_com_atributos/"
}

# ============================================================================
# FUNÇÕES DE DOWNLOAD
# ============================================================================

def criar_pasta_dados():
    """Cria a pasta para armazenar os dados do IBGE"""
    if not os.path.exists(PASTA_IBGE):
        os.makedirs(PASTA_IBGE)
        print(f"✓ Pasta '{PASTA_IBGE}' criada com sucesso!")
    else:
        print(f"✓ Pasta '{PASTA_IBGE}' já existe.")
    return PASTA_IBGE


def baixar_arquivo(url, nome_arquivo, pasta_destino):
    """Baixa um arquivo da URL especificada"""
    caminho_completo = os.path.join(pasta_destino, nome_arquivo)
    
    if os.path.exists(caminho_completo):
        print(f"✓ Arquivo '{nome_arquivo}' já existe. Pulando download...")
        return caminho_completo
    
    print(f"⏳ Baixando '{nome_arquivo}'...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Mostrar progresso
        tamanho_total = int(response.headers.get('content-length', 0))
        tamanho_baixado = 0
        
        with open(caminho_completo, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                tamanho_baixado += len(chunk)
                if tamanho_total > 0:
                    progresso = (tamanho_baixado / tamanho_total) * 100
                    print(f"\r   Progresso: {progresso:.1f}%", end="")
        
        print(f"\n✓ Download concluído: {caminho_completo}")
        return caminho_completo
        
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Erro no download: {e}")
        return None


def extrair_zip(caminho_zip, pasta_destino):
    """Extrai um arquivo ZIP"""
    print(f"⏳ Extraindo '{caminho_zip}'...")
    
    try:
        with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
            zip_ref.extractall(pasta_destino)
        print(f"✓ Arquivo extraído para '{pasta_destino}'")
        return True
    except Exception as e:
        print(f"✗ Erro na extração: {e}")
        return False


# ============================================================================
# FUNÇÕES PARA DOWNLOAD DA MALHA DE SETORES CENSITÁRIOS
# ============================================================================

def baixar_malha_setores(uf=SIGLA_UF):
    """
    Baixa a malha de setores censitários do estado especificado.
    
    Retorna o caminho para o arquivo .shp baixado.
    """
    pasta = criar_pasta_dados()
    
    # URL para download da malha de setores
    url = f"https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/setores/shp/UF/{uf}_setores_CD2022.zip"
    
    nome_zip = f"{uf}_setores_CD2022.zip"
    caminho_zip = baixar_arquivo(url, nome_zip, pasta)
    
    if caminho_zip:
        # Extrair o ZIP
        pasta_extracao = os.path.join(pasta, f"{uf}_setores")
        if not os.path.exists(pasta_extracao):
            os.makedirs(pasta_extracao)
        extrair_zip(caminho_zip, pasta_extracao)
        
        # Encontrar o arquivo .shp
        for arquivo in os.listdir(pasta_extracao):
            if arquivo.endswith('.shp'):
                return os.path.join(pasta_extracao, arquivo)
    
    return None


# ============================================================================
# FUNÇÕES PARA DOWNLOAD DOS DADOS AGREGADOS
# ============================================================================

def listar_arquivos_agregados_disponiveis():
    """
    Lista os arquivos de agregados disponíveis no FTP do IBGE.
    
    IMPORTANTE: Os dados de idade estão disponíveis em divulgações específicas.
    Os agregados preliminares contêm apenas população total e domicílios.
    Para dados de idade por setor, use a malha com atributos ou microdados.
    """
    print("\n" + "="*70)
    print("ARQUIVOS DE AGREGADOS POR SETORES CENSITÁRIOS DISPONÍVEIS NO IBGE:")
    print("="*70)
    
    print("""
📁 Agregados por Setores Censitários (Censo 2022)
   URL Base: https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/

   Conteúdo disponível:
   ├── Agregados_por_Setor_csv/     - Dados em formato CSV por UF
   ├── Agregados_por_Setor_xlsx/    - Dados em formato Excel por UF
   ├── malha_com_atributos/         - Shapefiles com dados já integrados
   └── dicionario_de_dados_agregados_por_setores.xlsx

   ⚠️  NOTA IMPORTANTE:
   Os agregados por setores censitários disponíveis publicamente contêm:
   - População total residente
   - Domicílios por espécie
   - Média de moradores por domicílio
   
   Para dados de POPULAÇÃO POR IDADE (idosos, etc.):
   - Use a API SIDRA (nível municipal apenas): https://sidra.ibge.gov.br
   - Ou aguarde a divulgação completa dos agregados definitivos
   - Ou use os microdados do Censo 2022 (requer processamento pesado)
    """)


def baixar_agregados_setores(uf=SIGLA_UF):
    """
    Baixa os dados agregados por setores censitários do estado especificado.
    
    Os dados incluem: população total, domicílios, etc.
    """
    pasta = criar_pasta_dados()
    
    # Tenta várias URLs possíveis (o IBGE muda a estrutura às vezes)
    urls_tentativas = [
        f"https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/Agregados_por_Setor_csv/Agregados_por_setores_censitarios_{uf}.zip",
        f"https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/Agregados_por_Setor_csv/Agregados_por_setores_{uf}.zip",
        f"https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios_preliminares/agregados_por_setores_censitarios_UF/{uf}/",
    ]
    
    for url in urls_tentativas:
        nome_arquivo = url.split('/')[-1]
        if nome_arquivo.endswith('.zip'):
            resultado = baixar_arquivo(url, nome_arquivo, pasta)
            if resultado:
                # Extrair
                pasta_extracao = os.path.join(pasta, f"agregados_{uf}")
                if not os.path.exists(pasta_extracao):
                    os.makedirs(pasta_extracao)
                extrair_zip(resultado, pasta_extracao)
                return pasta_extracao
    
    print("⚠️  Não foi possível baixar os agregados automaticamente.")
    print("    Tente baixar manualmente de:")
    print("    https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/")
    return None


def baixar_malha_com_atributos(uf=SIGLA_UF):
    """
    Baixa a malha de setores com atributos já integrados (mais prático).
    
    Este arquivo já contém os polígonos + dados de população.
    A estrutura correta é:
    ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/
    malha_com_atributos/setores/shp/UF/{UF}/{UF}_setores_CD2022.zip
    """
    pasta = criar_pasta_dados()
    
    # URL correta da malha com atributos (estrutura: setores/shp/UF/{UF}/)
    url = f"https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/malha_com_atributos/setores/shp/UF/{uf}/{uf}_setores_CD2022.zip"
    
    nome_zip = f"{uf}_setores_atributos_CD2022.zip"  # Nome diferente para não confundir com a malha sem atributos
    resultado = baixar_arquivo(url, nome_zip, pasta)
    
    if resultado:
        pasta_extracao = os.path.join(pasta, f"{uf}_malha_atributos")
        if not os.path.exists(pasta_extracao):
            os.makedirs(pasta_extracao)
        extrair_zip(resultado, pasta_extracao)
        
        # Procurar o shapefile
        for arquivo in os.listdir(pasta_extracao):
            if arquivo.endswith('.shp'):
                return os.path.join(pasta_extracao, arquivo)
    
    return None


# ============================================================================
# FUNÇÕES PARA USAR A API SIDRA (DADOS POR IDADE - NÍVEL MUNICIPAL)
# ============================================================================

def obter_proporcao_idosos_uf(uf="35"):
    """
    Obtém a proporção de idosos (60+ anos) no estado usando a API SIDRA.
    
    Retorna a proporção de idosos em relação à população total.
    Esta proporção será usada para estimar a população de idosos por setor censitário.
    """
    print(f"\n⏳ Obtendo proporção de idosos para UF {uf} via API SIDRA...")
    
    # Tabela 9514: População residente, por sexo e idade
    # Variável 93 = População residente
    # Classificação 2 (Sexo): 0 = Total
    # Classificação 287 (Idade): vamos buscar Total e idosos separadamente
    
    # Primeiro: população total (todas as idades)
    # c287=0 significa "Total" na classificação de idade
    url_total = f"https://apisidra.ibge.gov.br/values/t/9514/v/93/p/last/c2/0/c287/0/N3/{uf}"
    
    try:
        response = requests.get(url_total, timeout=60)
        response.raise_for_status()
        dados = response.json()
        
        if len(dados) > 1:
            pop_total = float(dados[1]['V'])
            print(f"   População total: {pop_total:,.0f}")
        else:
            print("   ⚠️ Não foi possível obter população total")
            return 0.15  # Valor padrão
            
    except Exception as e:
        print(f"   ⚠️ Erro ao buscar população total: {e}")
        return 0.15
    
    # Segundo: população de idosos (60+ anos)
    # Categorias de idade 60+: 93087 a 93095
    categorias_idosos = "93087,93088,93089,93090,93091,93092,93093,93094,93095"
    url_idosos = f"https://apisidra.ibge.gov.br/values/t/9514/v/93/p/last/c2/0/c287/{categorias_idosos}/N3/{uf}"
    
    try:
        response = requests.get(url_idosos, timeout=60)
        response.raise_for_status()
        dados = response.json()
        
        if len(dados) > 1:
            # Somar todas as faixas etárias
            pop_idosos = sum(float(row['V']) for row in dados[1:] if row['V'] and row['V'] != '-')
            print(f"   População 60+ anos: {pop_idosos:,.0f}")
            
            proporcao = pop_idosos / pop_total if pop_total > 0 else 0.15
            print(f"   Proporção de idosos: {proporcao*100:.2f}%")
            return proporcao
            
    except Exception as e:
        print(f"   ⚠️ Erro ao buscar população de idosos: {e}")
    
    return 0.15  # Valor padrão se falhar


def consultar_sidra_populacao_idade(codigo_municipio=None, uf="35"):
    """
    Consulta a API SIDRA do IBGE para obter dados de população por idade.
    
    LIMITAÇÃO: A API SIDRA fornece dados no nível MUNICIPAL, não por setor censitário.
    
    Parâmetros:
    - codigo_municipio: código IBGE do município (7 dígitos). Se None, busca UF.
    - uf: código da UF (ex: "35" para SP)
    
    Tabela 9514: População residente, por sexo, idade
    """
    base_url = "https://apisidra.ibge.gov.br/values"
    
    if codigo_municipio:
        # Nível municipal
        localidade = f"N6/{codigo_municipio}"
    else:
        # Nível UF
        localidade = f"N3/{uf}"
    
    # Buscar população total por faixas etárias
    # c2/0 = sexo total, c287/all = todas as idades
    url = f"{base_url}/t/9514/v/93/p/last/c2/0/c287/all/{localidade}"
    
    print(f"⏳ Consultando API SIDRA...")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        dados = response.json()
        
        if len(dados) > 1:
            # Criar DataFrame
            colunas = {k: v for k, v in dados[0].items()}
            df = pd.DataFrame(dados[1:])
            df.columns = list(colunas.values())
            print(f"✓ Dados obtidos: {len(df)} registros")
            return df
        
    except Exception as e:
        print(f"✗ Erro ao consultar SIDRA: {e}")
        print("\n   💡 DICA: Use o Query Builder do SIDRA para montar sua consulta:")
        print("   https://sidra.ibge.gov.br/tabela/9514")
        
    return None


def obter_populacao_idosos_municipio(codigo_municipio):
    """
    Obtém a população de idosos (60+ anos) de um município específico.
    
    Usa a API SIDRA do IBGE.
    Retorna: (DataFrame com detalhes, total de idosos, população total, proporção)
    """
    print(f"\n⏳ Buscando dados demográficos para o município {codigo_municipio}...")
    
    # Categorias de idade 60+: 93087 (60-64) até 93095 (100+)
    categorias_idosos = "93087,93088,93089,93090,93091,93092,93093,93094,93095"
    
    # URL para idosos
    url_idosos = f"https://apisidra.ibge.gov.br/values/t/9514/v/93/p/last/c2/0/c287/{categorias_idosos}/N6/{codigo_municipio}"
    
    # URL para total
    url_total = f"https://apisidra.ibge.gov.br/values/t/9514/v/93/p/last/c2/0/c287/0/N6/{codigo_municipio}"
    
    pop_total = 0
    total_idosos = 0
    df_resultado = None
    
    try:
        # Buscar população total
        response = requests.get(url_total, timeout=60)
        response.raise_for_status()
        dados = response.json()
        if len(dados) > 1 and dados[1].get('V'):
            pop_total = float(dados[1]['V'])
            
        # Buscar idosos
        response = requests.get(url_idosos, timeout=60)
        response.raise_for_status()
        dados = response.json()
        
        if len(dados) > 1:
            # Criar DataFrame
            colunas = {k: v for k, v in dados[0].items()}
            df_resultado = pd.DataFrame(dados[1:])
            df_resultado.columns = list(colunas.values())
            
            # Somar todas as faixas etárias de idosos
            total_idosos = sum(float(row['V']) for row in dados[1:] if row.get('V') and row['V'] != '-')
            
        proporcao = total_idosos / pop_total if pop_total > 0 else 0
        
        print(f"   População total: {pop_total:,.0f}")
        print(f"   População 60+ anos: {total_idosos:,.0f}")
        print(f"   Proporção de idosos: {proporcao*100:.2f}%")
        
        return df_resultado, total_idosos, pop_total, proporcao
            
    except Exception as e:
        print(f"   ⚠️ Erro: {e}")
    
    return None, 0, 0, 0


# ============================================================================
# FUNÇÃO PRINCIPAL: PROCESSAR DEMANDA
# ============================================================================

def carregar_e_processar_malha_setores(caminho_shp, codigo_municipio=None):
    """
    Carrega a malha de setores censitários e processa os dados.
    
    Parâmetros:
    - caminho_shp: caminho para o arquivo .shp da malha
    - codigo_municipio: filtrar por município (opcional)
    
    Retorna: GeoDataFrame com os setores censitários
    """
    print(f"\n⏳ Carregando malha de setores: {caminho_shp}")
    
    gdf = gpd.read_file(caminho_shp)
    
    print(f"✓ Malha carregada: {len(gdf)} setores censitários")
    print(f"  Colunas disponíveis: {list(gdf.columns)}")
    print(f"  CRS: {gdf.crs}")
    
    # Mostrar amostra dos dados
    print("\n📊 Amostra dos dados:")
    print(gdf.head())
    
    # Filtrar por município se especificado
    if codigo_municipio:
        # O código do setor começa com o código do município
        col_setor = None
        for col in ['CD_SETOR', 'COD_SETOR', 'codigo', 'GEOCODIGO']:
            if col in gdf.columns:
                col_setor = col
                break
        
        if col_setor:
            gdf_filtrado = gdf[gdf[col_setor].str.startswith(str(codigo_municipio))]
            print(f"\n✓ Filtrado para município {codigo_municipio}: {len(gdf_filtrado)} setores")
            return gdf_filtrado
    
    return gdf


def estimar_demanda_por_setor(gdf_setores, proporcao_idosos=0.15, taxa_atencao_domiciliar=0.05):
    """
    Estima a demanda por atenção domiciliar em cada setor censitário.
    
    MÉTODO: Como os dados de idade por setor não estão disponíveis publicamente,
    estimamos usando a proporção média de idosos da população.
    
    Parâmetros:
    - gdf_setores: GeoDataFrame com os setores censitários
    - proporcao_idosos: proporção estimada de idosos na população (padrão: 15%)
    - taxa_atencao_domiciliar: proporção de idosos que precisam de AD (padrão: 5%)
    
    Fórmula: Demanda = População_Total × Proporção_Idosos × Taxa_AD
    """
    # Encontrar coluna de população
    col_pop = None
    colunas_populacao = ['v0001', 'POP', 'POPULACAO', 'POP_TOTAL', 'v001', 'TOTAL_POP']
    
    for col in colunas_populacao:
        if col in gdf_setores.columns:
            col_pop = col
            break
    
    if col_pop is None:
        print("⚠️  Coluna de população não encontrada!")
        print(f"   Colunas disponíveis: {list(gdf_setores.columns)}")
        return gdf_setores
    
    print(f"\n📊 Estimando demanda por setor censitário...")
    print(f"   Coluna de população: {col_pop}")
    print(f"   Proporção de idosos estimada: {proporcao_idosos*100:.1f}%")
    print(f"   Taxa de necessidade de AD: {taxa_atencao_domiciliar*100:.1f}%")
    
    # Converter para numérico
    gdf_setores['POPULACAO'] = pd.to_numeric(gdf_setores[col_pop], errors='coerce').fillna(0)
    
    # Estimar população de idosos
    gdf_setores['POP_IDOSOS_ESTIMADA'] = gdf_setores['POPULACAO'] * proporcao_idosos
    
    # Estimar demanda por atenção domiciliar
    gdf_setores['DEMANDA_AD_ESTIMADA'] = gdf_setores['POP_IDOSOS_ESTIMADA'] * taxa_atencao_domiciliar
    
    # Estatísticas
    pop_total = gdf_setores['POPULACAO'].sum()
    idosos_estimados = gdf_setores['POP_IDOSOS_ESTIMADA'].sum()
    demanda_estimada = gdf_setores['DEMANDA_AD_ESTIMADA'].sum()
    
    print(f"\n📈 Estatísticas:")
    print(f"   População total: {pop_total:,.0f}")
    print(f"   Idosos estimados (60+): {idosos_estimados:,.0f}")
    print(f"   Demanda estimada de AD: {demanda_estimada:,.0f} pacientes")
    
    return gdf_setores


# ============================================================================
# VISUALIZAÇÃO
# ============================================================================

def criar_mapa_demanda(gdf_setores, coluna_demanda='DEMANDA_AD_ESTIMADA', output='mapa_demanda_setores.html'):
    """
    Cria um mapa interativo mostrando a demanda por setor censitário.
    """
    import folium
    from folium.plugins import HeatMap
    
    print(f"\n🗺️  Criando mapa de demanda...")
    
    # Calcular centroide de cada setor
    gdf_centroides = gdf_setores.copy()
    gdf_centroides['geometry'] = gdf_centroides.geometry.centroid
    
    # Reprojetar para WGS84 se necessário
    if gdf_centroides.crs != 'EPSG:4326':
        gdf_centroides = gdf_centroides.to_crs('EPSG:4326')
    
    # Centro do mapa
    centro_lat = gdf_centroides.geometry.y.mean()
    centro_lon = gdf_centroides.geometry.x.mean()
    
    # Criar mapa base
    mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=10)
    
    # Preparar dados para o heatmap
    dados_heatmap = []
    for idx, row in gdf_centroides.iterrows():
        if row[coluna_demanda] > 0:
            lat = row.geometry.y
            lon = row.geometry.x
            peso = row[coluna_demanda]
            dados_heatmap.append([lat, lon, peso])
    
    # Adicionar heatmap
    HeatMap(dados_heatmap, radius=15, blur=10, max_zoom=13).add_to(mapa)
    
    # Salvar
    mapa.save(output)
    print(f"✓ Mapa salvo em: {output}")
    
    return mapa


# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("DOWNLOAD E PROCESSAMENTO DE DADOS DE DEMANDA - IBGE CENSO 2022")
    print("="*70)
    
    # 1. Listar arquivos disponíveis
    listar_arquivos_agregados_disponiveis()
    
    # 2. Criar pasta para dados
    pasta = criar_pasta_dados()
    
    # 3. Obter proporção real de idosos via API SIDRA
    print("\n" + "-"*70)
    print("PASSO 1: Obtendo proporção real de idosos via API SIDRA...")
    print("-"*70)
    
    proporcao_idosos_real = obter_proporcao_idosos_uf(CODIGO_UF)
    
    # 4. Tentar baixar a malha de setores de SP
    print("\n" + "-"*70)
    print("PASSO 2: Baixando malha de setores censitários de São Paulo...")
    print("-"*70)
    
    caminho_malha = baixar_malha_setores(SIGLA_UF)
    
    # 5. Tentar baixar malha com atributos (mais completa)
    print("\n" + "-"*70)
    print("PASSO 3: Tentando baixar malha com atributos integrados...")
    print("-"*70)
    
    caminho_malha_atributos = baixar_malha_com_atributos(SIGLA_UF)
    
    # 6. Carregar e processar os dados
    print("\n" + "-"*70)
    print("PASSO 4: Processando dados...")
    print("-"*70)
    
    # Usar a malha que conseguimos baixar
    caminho_usar = caminho_malha_atributos or caminho_malha
    
    if caminho_usar:
        gdf = carregar_e_processar_malha_setores(caminho_usar)
        
        # 7. Estimar demanda usando proporção real de idosos
        print("\n" + "-"*70)
        print("PASSO 5: Estimando demanda por atenção domiciliar...")
        print("-"*70)
        
        gdf_demanda = estimar_demanda_por_setor(gdf, proporcao_idosos=proporcao_idosos_real)
        
        # 8. Salvar resultado
        output_file = os.path.join(pasta, f"demanda_setores_{SIGLA_UF}.csv")
        
        # Selecionar colunas relevantes
        colunas_salvar = [col for col in gdf_demanda.columns if col != 'geometry']
        gdf_demanda[colunas_salvar].to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✓ Dados salvos em: {output_file}")
        
        # 9. Criar mapa
        print("\n" + "-"*70)
        print("PASSO 6: Criando mapa de calor da demanda...")
        print("-"*70)
        try:
            criar_mapa_demanda(gdf_demanda)
        except Exception as e:
            print(f"⚠️  Não foi possível criar o mapa: {e}")
    
    else:
        print("\n⚠️  Não foi possível baixar os dados automaticamente.")
        print("   Por favor, baixe manualmente de:")
        print("   1. Malha de Setores: https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/26565-malhas-de-setores-censitarios-divisoes-intramunicipais.html")
        print("   2. Agregados: https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/")
    
    # 10. Demonstrar uso da API SIDRA para um município específico
    print("\n" + "-"*70)
    print("PASSO 7: Demonstração da API SIDRA (dados municipais)...")
    print("-"*70)
    
    # Código de São Paulo capital: 3550308
    print("\nBuscando dados de idosos para São Paulo capital (código 3550308)...")
    df_sidra, total_idosos, pop_total, proporcao = obter_populacao_idosos_municipio("3550308")
    
    if df_sidra is not None and len(df_sidra) > 0:
        print("\n📊 Dados obtidos do SIDRA:")
        print(f"   Colunas: {list(df_sidra.columns)}")
        print(df_sidra.head(10).to_string())
    
    print("\n" + "="*70)
    print("PROCESSAMENTO CONCLUÍDO!")
    print("="*70)
    print(f"""
📊 RESUMO:
   - Proporção de idosos em SP: {proporcao_idosos_real*100:.2f}%
   - Arquivos gerados: {PASTA_IBGE}/demanda_setores_{SIGLA_UF}.csv
   - Mapa de calor: mapa_demanda_setores.html

💡 VARIÁVEIS DA MALHA DE SETORES:
   - v0001: Total de pessoas (POPULAÇÃO)
   - v0002: Total de Domicílios
   - v0003: Total de Domicílios Particulares
   - v0004: Total de Domicílios Coletivos
   - v0005: Média de moradores por domicílio
   - v0006: Percentual de domicílios imputados
   - v0007: Total de Domicílios Particulares Ocupados

💡 PRÓXIMOS PASSOS:

1. Abra o mapa de calor 'mapa_demanda_setores.html' no navegador

2. Para integrar com seu projeto de Atenção Domiciliar:
   - Importe as funções deste script em seus outros scripts
   - Use os centroides dos setores como pontos de demanda
   - Cruze com os dados de oferta (CNES) que você já tem

3. Para dados mais detalhados de população por idade por setor:
   - Aguarde a divulgação definitiva dos agregados do Censo 2022
   - Ou processe os microdados (requer muito processamento)
    """)
