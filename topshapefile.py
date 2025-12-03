import geopandas as gpd

# 1. Substitua pelo caminho CORRETO para o seu arquivo .shp
# Lembre-se: os arquivos .shx e .dbf devem estar na MESMA pasta.
caminho_do_arquivo = "./SP_bairros_CD2022.shp"

try:
    # 2. O GeoPandas lê o shapefile
    gdf = gpd.read_file(caminho_do_arquivo)

    # 3. Agora você pode usar os dados!
    
    # Mostrar as 5 primeiras linhas dos dados (atributos)
    print("Dados carregados com sucesso:")
    print(gdf.head())

    # Mostrar informações sobre o arquivo
    print("\nInformações:")
    print(f"Total de formas (geometrias): {len(gdf)}")
    print(f"Sistema de Coordenadas (CRS): {gdf.crs}")

    # Opcional: Fazer um plot simples (requer matplotlib)
    # Se você quiser visualizar, descomente as linhas abaixo
    
    print("\nGerando um plot simples...")
    gdf.plot()
    import matplotlib.pyplot as plt
    plt.show()


except Exception as e:
    print(f"Ocorreu um erro ao ler o arquivo: {e}")
    print("Verifique se:")
    print("  1. O caminho do arquivo está correto.")
    print("  2. Os arquivos .shp, .shx e .dbf estão todos na mesma pasta.")