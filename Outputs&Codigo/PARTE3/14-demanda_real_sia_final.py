"""
DEMANDA REAL DE ATENÇÃO DOMICILIAR - DADOS DO SIA/DATASUS
==========================================================

Script para download e processamento de dados REAIS de produção
ambulatorial de Atenção Domiciliar do SIA/SUS.

FONTE DOS DADOS:
================
- FTP: ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados
- Arquivos: PASP<AAMM>.dbc (Produção Ambulatorial São Paulo)
- Grupo de procedimentos: 03.01.05 - ATENDIMENTO DOMICILIAR

PROCEDIMENTOS DE AD (SIGTAP):
=============================
- 0301050015: Assistência Domiciliar por Equipe Multiprofissional Atenção Especializada
- 0301050023: Assistência Domiciliar por Profissional de Nível Médio - AD1
- 0301050031: Assistência Domiciliar por Profissional de Nível Superior - AD1
- 0301050040: Assistência Domiciliar por Equipe Multiprofissional - AD2
- 0301050058: Assistência Domiciliar por Equipe Multiprofissional - AD3
- 0301050066: Visita Domiciliar por Profissional de Nível Médio
- 0301050074: Visita Domiciliar por Profissional de Nível Superior

VANTAGEM:
=========
- Dados de produção REAL (atendimentos efetivamente registrados)
- Permite análise temporal
- Detalhamento por procedimento, município, idade, sexo

LIMITAÇÃO:
==========
- Representa demanda ATENDIDA, não demanda total (reprimida não capturada)
- Pode haver subnotificação
- Download pode demorar devido ao tamanho dos arquivos

Autor: Análise Exploratória - IC FAPESP
Data: Janeiro 2025
"""

import os
import sys
import pandas as pd
import pyreaddbc
from dbfread import DBF
from pathlib import Path

# Diretórios
BASE_DIR = Path(__file__).parent.parent.parent
SIA_DIR = BASE_DIR / "SIA_DATA"
OUTPUT_DIR = Path(__file__).parent

# Nomes dos procedimentos de AD
PROCEDIMENTOS_AD = {
    "0301050015": "Assist. Dom. Equipe Multiprofissional - Atenção Especializada",
    "0301050023": "Assist. Dom. Profissional Nível Médio - AD1",
    "0301050031": "Assist. Dom. Profissional Nível Superior - AD1",
    "0301050040": "Assist. Dom. Equipe Multiprofissional - AD2",
    "0301050058": "Assist. Dom. Equipe Multiprofissional - AD3",
    "0301050066": "Visita Domiciliar Profissional Nível Médio",
    "0301050074": "Visita Domiciliar Profissional Nível Superior",
    "0301050082": "Assistência Domiciliar - Cuidados Paliativos",
    "0301050090": "Atendimento Domiciliar por Profissional ACS/ACE",
    "0301050104": "Visita Domiciliar por ACS/ACE",
    "0301050112": "Consulta Médica em Atenção Domiciliar",
    "0301050120": "Consulta de Profissional de Nível Superior em AD",
    "0301050139": "Atendimento de Enfermagem em AD",
    "0301050147": "Atendimento Fisioterapêutico em AD",
    "0301050155": "Atendimento Multiprofissional em AD",
}


def download_sia_ftp(uf='SP', anos=[2024], meses=range(1, 13)):
    """
    Baixa arquivos do SIA via FTP do DATASUS.
    
    Parâmetros:
    -----------
    uf : str - Sigla do estado (ex: 'SP')
    anos : list - Anos para download
    meses : range - Meses para download
    
    Retorna:
    --------
    list : Lista de caminhos dos arquivos baixados
    """
    import ftplib
    import socket
    
    print("\n" + "="*70)
    print("DOWNLOAD DE DADOS SIA VIA FTP")
    print("="*70)
    
    SIA_DIR.mkdir(parents=True, exist_ok=True)
    
    arquivos_baixados = []
    
    # Configurar timeout
    socket.setdefaulttimeout(180)
    
    try:
        print("\n1. Conectando ao FTP do DATASUS...")
        ftp = ftplib.FTP()
        ftp.connect('ftp.datasus.gov.br', 21, timeout=180)
        ftp.login()
        ftp.set_pasv(True)
        print("   ✓ Conectado!")
        
        ftp.cwd('/dissemin/publicos/SIASUS/200801_/Dados')
        print("   ✓ Pasta SIA encontrada!")
        
        # Listar arquivos disponíveis
        print("\n2. Listando arquivos...")
        arquivos_ftp = []
        ftp.retrlines('NLST', arquivos_ftp.append)
        
        # Filtrar arquivos PA do estado desejado
        arquivos_uf = [f for f in arquivos_ftp if f.startswith(f'PA{uf}')]
        print(f"   Arquivos PA de {uf}: {len(arquivos_uf)}")
        
        # Filtrar por ano/mês
        for ano in anos:
            for mes in meses:
                sufixo = f"{str(ano)[2:]}{mes:02d}"
                arquivos_mes = [f for f in arquivos_uf if sufixo in f]
                
                for arq in arquivos_mes:
                    local_path = SIA_DIR / arq
                    
                    if local_path.exists():
                        print(f"   ⏭ {arq} (já existe)")
                        arquivos_baixados.append(local_path)
                        continue
                    
                    print(f"   ⬇ Baixando {arq}...", end=" ", flush=True)
                    try:
                        with open(local_path, 'wb') as f:
                            ftp.retrbinary(f'RETR {arq}', f.write, 32768)
                        size_mb = local_path.stat().st_size / 1024 / 1024
                        print(f"✓ ({size_mb:.1f} MB)")
                        arquivos_baixados.append(local_path)
                    except Exception as e:
                        print(f"✗ ({e})")
        
        ftp.quit()
        
    except Exception as e:
        print(f"   ✗ Erro FTP: {e}")
    
    return arquivos_baixados


def converter_dbc_para_dbf(arquivo_dbc):
    """
    Converte arquivo DBC para DBF.
    """
    arquivo_dbf = arquivo_dbc.with_suffix('.dbf')
    
    if not arquivo_dbf.exists():
        print(f"   Convertendo {arquivo_dbc.name} -> DBF...")
        pyreaddbc.dbc2dbf(str(arquivo_dbc), str(arquivo_dbf))
    
    return arquivo_dbf


def filtrar_procedimentos_ad(arquivo_dbf):
    """
    Filtra procedimentos de Atenção Domiciliar do arquivo DBF.
    
    Procedimentos do grupo 03.01.05 começam com "030105".
    """
    print(f"   Processando {arquivo_dbf.name}...")
    
    dbf = DBF(str(arquivo_dbf), encoding='latin1', load=False)
    
    colunas = ['PA_UFMUN', 'PA_MUNPCN', 'PA_PROC_ID', 'PA_QTDPRO', 'PA_QTDAPR',
               'PA_VALPRO', 'PA_VALAPR', 'PA_IDADE', 'PA_SEXO', 'PA_CIDPRI',
               'PA_INE', 'PA_CMP']
    
    registros_ad = []
    total = 0
    
    for rec in dbf:
        total += 1
        proc = str(rec.get('PA_PROC_ID', ''))
        
        if proc.startswith('030105'):
            registros_ad.append({k: rec.get(k) for k in colunas if k in rec})
    
    print(f"      {total:,} registros processados, {len(registros_ad):,} de AD")
    
    return registros_ad


def processar_arquivos_sia(arquivos_dbc):
    """
    Processa lista de arquivos DBC e extrai procedimentos de AD.
    """
    print("\n" + "="*70)
    print("PROCESSANDO ARQUIVOS DO SIA")
    print("="*70)
    
    todos_registros = []
    
    for arquivo in arquivos_dbc:
        if arquivo.suffix.lower() == '.dbc':
            try:
                arquivo_dbf = converter_dbc_para_dbf(arquivo)
                registros = filtrar_procedimentos_ad(arquivo_dbf)
                todos_registros.extend(registros)
            except Exception as e:
                print(f"   ✗ Erro em {arquivo.name}: {e}")
    
    if todos_registros:
        df = pd.DataFrame(todos_registros)
        print(f"\n   Total de registros de AD: {len(df):,}")
        return df
    
    return None


def analisar_producao_ad(df):
    """
    Analisa a produção de Atenção Domiciliar.
    """
    print("\n" + "="*70)
    print("ANÁLISE DA PRODUÇÃO DE ATENÇÃO DOMICILIAR")
    print("="*70)
    
    if df is None or len(df) == 0:
        print("   Sem dados para analisar")
        return None
    
    # Converter colunas numéricas
    df['PA_QTDAPR'] = pd.to_numeric(df['PA_QTDAPR'], errors='coerce').fillna(0)
    df['PA_QTDPRO'] = pd.to_numeric(df['PA_QTDPRO'], errors='coerce').fillna(0)
    
    # 1. Procedimentos
    print("\n1. PROCEDIMENTOS DE AD:")
    for proc, count in df['PA_PROC_ID'].value_counts().items():
        nome = PROCEDIMENTOS_AD.get(str(proc), "Outro")
        print(f"   {proc}: {count:,} registros - {nome}")
    
    # 2. Total de atendimentos
    total_aprovado = df['PA_QTDAPR'].sum()
    total_produzido = df['PA_QTDPRO'].sum()
    print(f"\n2. TOTAL DE ATENDIMENTOS:")
    print(f"   Aprovados: {total_aprovado:,.0f}")
    print(f"   Produzidos: {total_produzido:,.0f}")
    
    # 3. Por município
    print("\n3. TOP 10 MUNICÍPIOS:")
    por_mun = df.groupby('PA_MUNPCN').agg({
        'PA_QTDAPR': 'sum',
        'PA_QTDPRO': 'sum'
    }).reset_index()
    por_mun.columns = ['CO_MUNICIPIO', 'QTD_APROVADA', 'QTD_PRODUZIDA']
    por_mun = por_mun.sort_values('QTD_APROVADA', ascending=False)
    
    # Remover município 999999 (não identificado)
    por_mun_valido = por_mun[por_mun['CO_MUNICIPIO'] != '999999']
    
    print(por_mun_valido.head(10).to_string())
    
    # São Paulo capital
    sp_capital = por_mun_valido[por_mun_valido['CO_MUNICIPIO'] == '355030']
    if not sp_capital.empty:
        print(f"\n   ★ SÃO PAULO CAPITAL (355030):")
        print(f"     Atendimentos aprovados: {sp_capital['QTD_APROVADA'].values[0]:,.0f}")
    
    return por_mun


def main():
    """
    Função principal.
    """
    print("="*70)
    print("DEMANDA REAL DE ATENÇÃO DOMICILIAR - SIA/SUS")
    print("="*70)
    print("\nEste script baixa e processa dados REAIS de produção ambulatorial")
    print("de Atenção Domiciliar diretamente do DATASUS.\n")
    
    # Verificar se já existem dados processados
    arquivo_parquet = SIA_DIR / "producao_ad_sp_202511.parquet"
    
    if arquivo_parquet.exists():
        print(f"✓ Dados já processados encontrados: {arquivo_parquet}")
        df = pd.read_parquet(arquivo_parquet)
        por_mun = analisar_producao_ad(df)
        
        if por_mun is not None:
            output_file = OUTPUT_DIR / "demanda_ad_real_por_municipio.csv"
            por_mun.to_csv(output_file, index=False)
            print(f"\n✓ Salvo: {output_file}")
        
        return
    
    # Download e processamento
    print("Iniciando download de dados do SIA...")
    
    # Tentar baixar dados mais recentes
    arquivos = list(SIA_DIR.glob("PASP*.dbc"))
    
    if not arquivos:
        print("Nenhum arquivo DBC encontrado. Tentando download...")
        arquivos = download_sia_ftp(uf='SP', anos=[2024], meses=[12])
    
    if arquivos:
        df = processar_arquivos_sia(arquivos)
        
        if df is not None:
            # Salvar dados processados
            df.to_parquet(SIA_DIR / "producao_ad_completo.parquet")
            df.to_csv(SIA_DIR / "producao_ad_completo.csv", index=False)
            
            por_mun = analisar_producao_ad(df)
            
            if por_mun is not None:
                output_file = OUTPUT_DIR / "demanda_ad_real_por_municipio.csv"
                por_mun.to_csv(output_file, index=False)
                print(f"\n✓ Resultados salvos em: {output_file}")
    else:
        print("\n✗ Não foi possível obter dados do SIA")
        print("  Verifique sua conexão com a internet e tente novamente.")


if __name__ == "__main__":
    main()
