"""
DEMANDA REAL DE ATENÇÃO DOMICILIAR - DADOS DO SIA/DATASUS
==========================================================

Este script utiliza dados REAIS de produção ambulatorial do Sistema de
Informação Ambulatorial (SIA) do SUS para obter a demanda efetiva de
atendimentos de Atenção Domiciliar.

FONTE DOS DADOS:
================
- SIA/SUS (Sistema de Informação Ambulatorial)
- Grupo de procedimentos: 03.01.05 - ATENDIMENTO DOMICILIAR
- Via biblioteca PySUS para download direto do DATASUS

VANTAGEM SOBRE METODOLOGIA ANTERIOR:
====================================
- Dados de produção REAL (atendimentos realizados)
- Não é estimativa ou proxy
- Contabiliza procedimentos efetivamente registrados no SUS

LIMITAÇÃO:
==========
- Representa demanda ATENDIDA, não demanda total
- Pode haver subnotificação
- Demanda reprimida não é capturada

Autor: Análise Exploratória - IC FAPESP
Data: 2025
"""

import pandas as pd
import os
import sys

# Tentar importar PySUS
try:
    from pysus.online_data.SIA import download as download_sia
    from pysus.online_data import parquets_to_dataframe
    PYSUS_DISPONIVEL = True
except ImportError:
    PYSUS_DISPONIVEL = False
    print("⚠ PySUS não disponível. Tentando método alternativo...")

# Configurações
OUTPUT_DIR = "."
SIA_DIR = "../../SIA_DATA"


def baixar_dados_sia_pysus(uf='SP', ano=2024, meses=range(1, 13)):
    """
    Baixa dados do SIA usando PySUS.
    
    Parâmetros:
    -----------
    uf : str - Sigla do estado (ex: 'SP')
    ano : int - Ano de referência
    meses : range - Meses para download
    """
    
    print("\n[1/4] BAIXANDO DADOS DO SIA VIA PYSUS")
    print("="*60)
    
    if not PYSUS_DISPONIVEL:
        print("  ⚠ PySUS não disponível")
        return None
    
    os.makedirs(SIA_DIR, exist_ok=True)
    
    dfs = []
    for mes in meses:
        try:
            print(f"  Baixando {uf} {ano}/{mes:02d}...", end=" ")
            
            # Download dos arquivos PA (Produção Ambulatorial)
            files = download_sia(
                uf, 
                ano, 
                mes, 
                group='PA'  # Produção Ambulatorial
            )
            
            if files:
                df = parquets_to_dataframe(files)
                dfs.append(df)
                print(f"✓ {len(df):,} registros")
            else:
                print("(sem dados)")
                
        except Exception as e:
            print(f"✗ Erro: {str(e)[:50]}")
            continue
    
    if dfs:
        df_completo = pd.concat(dfs, ignore_index=True)
        print(f"\n  Total de registros: {len(df_completo):,}")
        return df_completo
    
    return None


def filtrar_procedimentos_ad(df):
    """
    Filtra procedimentos específicos de Atenção Domiciliar.
    
    Códigos de procedimento de AD (Grupo 03.01.05):
    - 03.01.05.001-1 - Assistência domiciliar por equipe multiprofissional
    - 03.01.05.002-0 - Assistência domiciliar por profissional de nível médio
    - 03.01.05.003-8 - Assistência domiciliar por profissional de nível superior
    - E outros relacionados...
    """
    
    print("\n[2/4] FILTRANDO PROCEDIMENTOS DE ATENÇÃO DOMICILIAR")
    print("="*60)
    
    if df is None:
        return None
    
    # Procedimentos do grupo 03.01.05 (Atenção Domiciliar)
    # O código do procedimento está na coluna PA_PROC_ID ou similar
    
    # Identificar coluna de procedimento
    col_proc = None
    for col in ['PA_PROC_ID', 'PROC_ID', 'CO_PROCEDIMENTO', 'PA_PROCED']:
        if col in df.columns:
            col_proc = col
            break
    
    if col_proc is None:
        print(f"  ⚠ Coluna de procedimento não encontrada")
        print(f"  Colunas disponíveis: {df.columns.tolist()[:20]}")
        return None
    
    print(f"  Coluna de procedimento: {col_proc}")
    
    # Filtrar por procedimentos que começam com 030105 (grupo de AD)
    df[col_proc] = df[col_proc].astype(str)
    
    # Padrões de códigos de AD
    padroes_ad = ['030105', '0301050']
    
    mask = df[col_proc].str.startswith(tuple(padroes_ad))
    df_ad = df[mask].copy()
    
    print(f"  Procedimentos de AD encontrados: {len(df_ad):,}")
    
    if len(df_ad) > 0:
        # Mostrar procedimentos únicos
        procs_unicos = df_ad[col_proc].value_counts().head(10)
        print(f"\n  Top 10 procedimentos de AD:")
        for proc, count in procs_unicos.items():
            print(f"    {proc}: {count:,}")
    
    return df_ad


def agregar_por_municipio(df_ad):
    """
    Agrega atendimentos de AD por município.
    """
    
    print("\n[3/4] AGREGANDO POR MUNICÍPIO")
    print("="*60)
    
    if df_ad is None or len(df_ad) == 0:
        return None
    
    # Identificar coluna de município
    col_mun = None
    for col in ['PA_MUNPCN', 'MUNPCN', 'CO_MUNICIPIO', 'PA_CODUNI']:
        if col in df_ad.columns:
            col_mun = col
            break
    
    # Identificar coluna de quantidade
    col_qtd = None
    for col in ['PA_QTDPRO', 'QTDPRO', 'QT_APROVADA', 'PA_QTDAPR']:
        if col in df_ad.columns:
            col_qtd = col
            break
    
    if col_mun is None or col_qtd is None:
        print(f"  ⚠ Colunas necessárias não encontradas")
        return None
    
    print(f"  Coluna de município: {col_mun}")
    print(f"  Coluna de quantidade: {col_qtd}")
    
    # Converter quantidade para numérico
    df_ad[col_qtd] = pd.to_numeric(df_ad[col_qtd], errors='coerce').fillna(0)
    
    # Agregar
    df_agregado = df_ad.groupby(col_mun).agg({
        col_qtd: 'sum'
    }).reset_index()
    
    df_agregado.columns = ['CO_MUNICIPIO', 'QTD_ATENDIMENTOS_AD']
    
    # Estatísticas
    total = df_agregado['QTD_ATENDIMENTOS_AD'].sum()
    print(f"\n  Total de atendimentos de AD: {total:,.0f}")
    print(f"  Municípios com AD: {len(df_agregado):,}")
    
    # Top 10 municípios
    top10 = df_agregado.nlargest(10, 'QTD_ATENDIMENTOS_AD')
    print(f"\n  Top 10 municípios:")
    for _, row in top10.iterrows():
        print(f"    {row['CO_MUNICIPIO']}: {row['QTD_ATENDIMENTOS_AD']:,.0f}")
    
    return df_agregado


def calcular_demanda_real_sp(df_agregado):
    """
    Calcula estatísticas de demanda real para São Paulo.
    """
    
    print("\n[4/4] ANÁLISE DE DEMANDA REAL - SÃO PAULO")
    print("="*60)
    
    if df_agregado is None:
        return None
    
    # Filtrar SP Capital (código 355030)
    df_sp = df_agregado[df_agregado['CO_MUNICIPIO'].astype(str).str.startswith('355030')]
    
    if len(df_sp) == 0:
        print("  ⚠ Nenhum dado encontrado para SP Capital")
        return None
    
    demanda_sp = df_sp['QTD_ATENDIMENTOS_AD'].sum()
    
    print(f"\n  DEMANDA REAL (ATENDIDA) - SP CAPITAL:")
    print(f"  {'-'*50}")
    print(f"    Atendimentos de AD registrados: {demanda_sp:,.0f}")
    print(f"  {'-'*50}")
    
    # Comparar com estimativa do Censo
    pop_idosa_sp = 2_020_436  # Do Censo 2022
    
    taxa_real = demanda_sp / pop_idosa_sp * 100
    print(f"\n  COMPARAÇÃO COM POPULAÇÃO IDOSA:")
    print(f"    População 60+ SP Capital: {pop_idosa_sp:,}")
    print(f"    Taxa de atendimento AD: {taxa_real:.2f}%")
    
    return {
        'demanda_sp_capital': demanda_sp,
        'taxa_atendimento': taxa_real
    }


def metodo_alternativo_sem_pysus():
    """
    Método alternativo quando PySUS não está disponível.
    Usa dados já existentes ou instruções para download manual.
    """
    
    print("\n" + "="*60)
    print("   MÉTODO ALTERNATIVO - INSTRUÇÕES PARA DOWNLOAD MANUAL")
    print("="*60)
    
    print("""
    Como PySUS não conseguiu baixar os dados, você pode:
    
    1. ACESSAR O TABNET:
       http://tabnet.datasus.gov.br/cgi/deftohtm.exe?sia/cnv/qauf.def
    
    2. CONFIGURAR A CONSULTA:
       - Linha: Município
       - Coluna: Procedimento
       - Conteúdo: Quantidade aprovada
       - Período: 2024 (ou ano desejado)
       - UF: São Paulo
       - Subgrupo procedimento: 03.01.05 - Atenção Domiciliar
    
    3. CLICAR EM "Mostra" e exportar como CSV
    
    4. SALVAR EM: ../../SIA_DATA/producao_ad_sp.csv
    
    5. EXECUTAR ESTE SCRIPT NOVAMENTE
    """)
    
    # Verificar se existe arquivo manual
    arquivo_manual = os.path.join(SIA_DIR, "producao_ad_sp.csv")
    if os.path.exists(arquivo_manual):
        print(f"\n  ✓ Arquivo encontrado: {arquivo_manual}")
        df = pd.read_csv(arquivo_manual, sep=';', encoding='latin-1')
        return df
    
    return None


def main():
    """Função principal."""
    
    print("="*70)
    print("   DEMANDA REAL DE ATENÇÃO DOMICILIAR")
    print("   Dados do SIA/DATASUS")
    print("="*70)
    
    # Tentar baixar via PySUS
    df = baixar_dados_sia_pysus(uf='SP', ano=2024, meses=[1, 2, 3])
    
    if df is None:
        print("\n  ⚠ Não foi possível baixar dados via PySUS")
        df = metodo_alternativo_sem_pysus()
    
    if df is not None:
        # Processar dados
        df_ad = filtrar_procedimentos_ad(df)
        df_agregado = agregar_por_municipio(df_ad)
        resultado = calcular_demanda_real_sp(df_agregado)
        
        if resultado:
            print("\n" + "="*70)
            print("   CONCLUSÃO")
            print("="*70)
            print(f"""
    A demanda REAL (atendida) de AD em SP Capital é de {resultado['demanda_sp_capital']:,.0f}
    procedimentos registrados no SIA/SUS.
    
    Isso representa {resultado['taxa_atendimento']:.2f}% da população idosa 60+.
    
    IMPORTANTE: Este valor representa a demanda ATENDIDA, não a demanda
    total. A demanda reprimida (pacientes elegíveis sem acesso) não é
    capturada por estes dados.
            """)
    else:
        print("\n  ⚠ Não foi possível processar os dados")
        print("  Siga as instruções acima para download manual")


if __name__ == "__main__":
    main()
