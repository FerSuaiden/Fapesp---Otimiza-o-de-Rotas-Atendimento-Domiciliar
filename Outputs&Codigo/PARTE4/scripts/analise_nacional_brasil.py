#!/usr/bin/env python3
"""
===============================================================================
ANÁLISE NACIONAL - COBERTURA E CONFORMIDADE LEGAL DO PROGRAMA MELHOR EM CASA
===============================================================================

Este script realiza duas análises principais para TODO O BRASIL:

1. COBERTURA MUNICIPAL:
   - Quantos municípios participam do programa "Melhor em Casa"?
   - Qual a porcentagem de cobertura por estado e região?
   - Comparação com o total de municípios do IBGE

2. CONFORMIDADE LEGAL:
   - Quantas equipes EMAD/EMAP estão em conformidade com a Portaria 3.005/2024?
   - Quais são os principais gargalos por tipo de equipe?
   - Análise por região geográfica

Fontes de dados:
- CNES/DATASUS (competência 08/2025)
- IBGE (total de municípios por estado)

Referência legal:
- Portaria GM/MS nº 3.005, de 2 de janeiro de 2024

===============================================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import Counter
import os
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

BASE_DIR = '/home/fersuaiden/Área de trabalho/Faculdade/IC'
CNES_DIR = os.path.join(BASE_DIR, 'CNES_DATA')
OUTPUT_DIR = os.path.join(BASE_DIR, 'Outputs&Codigo/PARTE4')
CHS_MINIMA_INDIVIDUAL = 20  # Art. 547, §1º

# Mapeamento UF (código IBGE → sigla)
# Os dois primeiros dígitos do código do município indicam a UF
IBGE_UF_MAP = {
    '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',  # Norte
    '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL',  # Nordeste
    '28': 'SE', '29': 'BA',
    '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',  # Sudeste
    '41': 'PR', '42': 'SC', '43': 'RS',  # Sul
    '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF',  # Centro-Oeste
}

# Mapeamento de UF para Região
UF_REGIAO = {
    'RO': 'Norte', 'AC': 'Norte', 'AM': 'Norte', 'RR': 'Norte', 
    'PA': 'Norte', 'AP': 'Norte', 'TO': 'Norte',
    'MA': 'Nordeste', 'PI': 'Nordeste', 'CE': 'Nordeste', 'RN': 'Nordeste',
    'PB': 'Nordeste', 'PE': 'Nordeste', 'AL': 'Nordeste', 'SE': 'Nordeste', 'BA': 'Nordeste',
    'MG': 'Sudeste', 'ES': 'Sudeste', 'RJ': 'Sudeste', 'SP': 'Sudeste',
    'PR': 'Sul', 'SC': 'Sul', 'RS': 'Sul',
    'MS': 'Centro-Oeste', 'MT': 'Centro-Oeste', 'GO': 'Centro-Oeste', 'DF': 'Centro-Oeste',
}

# Total de municípios por UF (IBGE 2022)
# Fonte: https://www.ibge.gov.br/cidades-e-estados
MUNICIPIOS_POR_UF = {
    'RO': 52, 'AC': 22, 'AM': 62, 'RR': 15, 'PA': 144, 'AP': 16, 'TO': 139,
    'MA': 217, 'PI': 224, 'CE': 184, 'RN': 167, 'PB': 223, 'PE': 185, 'AL': 102, 'SE': 75, 'BA': 417,
    'MG': 853, 'ES': 78, 'RJ': 92, 'SP': 645,
    'PR': 399, 'SC': 295, 'RS': 497,
    'MS': 79, 'MT': 141, 'GO': 246, 'DF': 1,
}
TOTAL_MUNICIPIOS_BRASIL = sum(MUNICIPIOS_POR_UF.values())  # 5.570

# Códigos de tipo de equipe de Atenção Domiciliar (CNES - tbTipoEquipe)
TIPOS_EQUIPE_AD = {
    22: 'EMAD I',   # Equipe Multiprofissional de Atenção Domiciliar Tipo I
    46: 'EMAD II',  # Equipe Multiprofissional de Atenção Domiciliar Tipo II
    23: 'EMAP',     # Equipe Multiprofissional de Apoio
    77: 'EMAP-R',   # Equipe Multiprofissional de Apoio para Reabilitação
}

# ==============================================================================
# REGRAS DE CONFORMIDADE - PORTARIA GM/MS Nº 3.005/2024
# ==============================================================================

# EMAD I (Art. 547, I): 
#   - 1 médico com CHS mínima de 40h
#   - 1 enfermeiro com CHS mínima de 60h
#   - 3 técnicos/auxiliares de enfermagem (totalizando 120h)
#   - 1 fisioterapeuta OU assistente social com CHS mínima de 30h
#
# EMAD II (Art. 547, II):
#   - 1 médico com CHS mínima de 20h
#   - 1 enfermeiro com CHS mínima de 30h  
#   - 3 técnicos/auxiliares de enfermagem (totalizando 120h)
#   - 1 fisioterapeuta OU assistente social com CHS mínima de 30h

REGRAS_EMAD = {
    22: {'MEDICO': 40, 'ENFERMEIRO': 60, 'TECNICO_ENFERMAGEM': 120, 'FISIO_OU_AS': 30},
    46: {'MEDICO': 20, 'ENFERMEIRO': 30, 'TECNICO_ENFERMAGEM': 120, 'FISIO_OU_AS': 30},
}

# EMAP (Art. 548): 
#   - Mínimo de 3 profissionais de nível superior de categorias DIFERENTES
#   - CHS total mínima de 90h
#
# EMAP-R (Art. 548-A):
#   - Mínimo de 3 profissionais de nível superior de categorias DIFERENTES
#   - CHS total mínima de 60h (municípios < 20.000 hab)

REGRAS_EMAP = {
    23: {'MIN_CATEGORIAS_NS': 3, 'CHS_TOTAL': 90},
    77: {'MIN_CATEGORIAS_NS': 3, 'CHS_TOTAL': 60},
}

# Profissionais de Nível Superior elegíveis para EMAP (Art. 548, I)
# Nota: Médico e Enfermeiro NÃO contam para EMAP comum (já estão na EMAD)
PROF_NS_EMAP = [
    'FISIOTERAPEUTA', 'ASSISTENTE_SOCIAL', 'FONOAUDIOLOGO', 
    'NUTRICIONISTA', 'PSICOLOGO', 'TERAPEUTA_OCUPACIONAL',
    'ODONTOLOGO', 'FARMACEUTICO'
]

# Para EMAP-R: Enfermeiro também pode compor a equipe (Art. 548-A)
PROF_NS_EMAP_R = PROF_NS_EMAP + ['ENFERMEIRO']


# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def categorizar_cbo(cbo):
    """
    Categoriza um código CBO em uma categoria profissional padronizada.
    
    Os códigos CBO (Classificação Brasileira de Ocupações) têm 6 dígitos.
    Usamos os 4 primeiros dígitos para identificar a família ocupacional.
    
    Referência: https://cbo.mte.gov.br/
    """
    cbo_str = str(cbo).strip()
    
    # Médicos (família 2251, 2252, 2253)
    if cbo_str.startswith(('2251', '2252', '2253')): 
        return 'MEDICO'
    
    # Enfermeiros (família 2235)
    if cbo_str.startswith('2235'): 
        return 'ENFERMEIRO'
    
    # Técnicos e Auxiliares de Enfermagem (família 3222)
    if cbo_str.startswith('3222'): 
        return 'TECNICO_ENFERMAGEM'
    
    # Fisioterapeutas (família 2236)
    if cbo_str.startswith('2236'): 
        return 'FISIOTERAPEUTA'
    
    # Assistentes Sociais (família 2516)
    if cbo_str.startswith('2516'): 
        return 'ASSISTENTE_SOCIAL'
    
    # Fonoaudiólogos (família 2238)
    if cbo_str.startswith('2238'): 
        return 'FONOAUDIOLOGO'
    
    # Nutricionistas (família 2237)
    if cbo_str.startswith('2237'): 
        return 'NUTRICIONISTA'
    
    # Psicólogos (família 2515)
    if cbo_str.startswith('2515'): 
        return 'PSICOLOGO'
    
    # Terapeutas Ocupacionais (família 2239)
    if cbo_str.startswith('2239'): 
        return 'TERAPEUTA_OCUPACIONAL'
    
    # Cirurgiões-Dentistas (família 2232)
    if cbo_str.startswith('2232'): 
        return 'ODONTOLOGO'
    
    # Farmacêuticos (família 2234)
    if cbo_str.startswith('2234'): 
        return 'FARMACEUTICO'
    
    return 'OUTRO'


def extrair_uf(codigo_municipio):
    """
    Extrai a sigla da UF a partir do código IBGE do município.
    
    Os códigos de município do IBGE têm 7 dígitos, onde os 2 primeiros
    identificam a Unidade da Federação.
    
    Exemplo: 3550308 → '35' → 'SP'
    """
    codigo_str = str(codigo_municipio).strip()
    prefixo_uf = codigo_str[:2]
    return IBGE_UF_MAP.get(prefixo_uf, 'DESCONHECIDO')


def verificar_conformidade_equipe(df_prof, tipo_equipe):
    """
    Verifica se uma equipe está em conformidade com a Portaria 3.005/2024.
    
    Parâmetros:
    -----------
    df_prof : DataFrame
        Profissionais da equipe com CHS >= 20h (filtrados)
    tipo_equipe : int
        Código do tipo de equipe (22, 46, 23 ou 77)
    
    Retorna:
    --------
    tuple : (conforme: bool, problemas: list)
    """
    problemas = []
    
    if tipo_equipe in [22, 46]:  # EMAD I ou EMAD II
        regras = REGRAS_EMAD[tipo_equipe]
        
        for categoria, minimo in regras.items():
            if categoria == 'FISIO_OU_AS':
                # Pode ser cumprido por Fisioterapeuta OU Assistente Social
                chs = df_prof[df_prof['CATEGORIA'].isin(
                    ['FISIOTERAPEUTA', 'ASSISTENTE_SOCIAL']
                )]['CHS_TOTAL'].sum()
            else:
                chs = df_prof[df_prof['CATEGORIA'] == categoria]['CHS_TOTAL'].sum()
            
            if chs < minimo:
                problemas.append(categoria)
    
    else:  # EMAP (23) ou EMAP-R (77)
        regras = REGRAS_EMAP[tipo_equipe]
        lista_ns = PROF_NS_EMAP_R if tipo_equipe == 77 else PROF_NS_EMAP
        
        # Filtra apenas profissionais NS elegíveis
        prof_ns = df_prof[df_prof['CATEGORIA'].isin(lista_ns)]
        
        # Conta CATEGORIAS diferentes (não profissionais)
        n_categorias = prof_ns['CATEGORIA'].nunique()
        chs_total = prof_ns['CHS_TOTAL'].sum()
        
        if n_categorias < regras['MIN_CATEGORIAS_NS']:
            problemas.append('POUCAS_CATEGORIAS_NS')
        
        if chs_total < regras['CHS_TOTAL']:
            problemas.append('CHS_TOTAL_INSUFICIENTE')
    
    conforme = len(problemas) == 0
    return conforme, problemas


# ==============================================================================
# FUNÇÃO PRINCIPAL
# ==============================================================================

def main():
    print("=" * 80)
    print("ANÁLISE NACIONAL - PROGRAMA MELHOR EM CASA")
    print("Cobertura Municipal e Conformidade Legal (Portaria 3.005/2024)")
    print("=" * 80)
    
    # =========================================================================
    # ETAPA 1: CARREGAR EQUIPES AD DE TODO O BRASIL
    # =========================================================================
    
    print("\n" + "─" * 80)
    print("ETAPA 1: Carregando equipes de Atenção Domiciliar de todo o Brasil...")
    print("─" * 80)
    
    df_equipes = pd.read_csv(
        os.path.join(CNES_DIR, "tbEquipe202508.csv"),
        sep=';', encoding='latin-1', low_memory=False
    )
    
    # Filtrar apenas equipes AD (códigos 22, 46, 23, 77)
    df_equipes_ad = df_equipes[df_equipes['TP_EQUIPE'].isin(TIPOS_EQUIPE_AD.keys())].copy()
    
    # Converter datas
    df_equipes_ad['DT_DESATIVACAO'] = pd.to_datetime(
        df_equipes_ad['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce'
    )
    
    # Filtrar apenas equipes ATIVAS (sem data de desativação)
    df_ativas = df_equipes_ad[df_equipes_ad['DT_DESATIVACAO'].isna()].copy()
    
    # Extrair UF e Região
    df_ativas['UF'] = df_ativas['CO_MUNICIPIO'].apply(extrair_uf)
    df_ativas['REGIAO'] = df_ativas['UF'].map(UF_REGIAO)
    df_ativas['TIPO_NOME'] = df_ativas['TP_EQUIPE'].map(TIPOS_EQUIPE_AD)
    
    print(f"\n    Total de equipes AD ativas no Brasil: {len(df_ativas):,}")
    print(f"\n    Distribuição por tipo:")
    for tp, nome in TIPOS_EQUIPE_AD.items():
        qtd = len(df_ativas[df_ativas['TP_EQUIPE'] == tp])
        print(f"      • {nome}: {qtd:,} equipes")
    
    # =========================================================================
    # ETAPA 2: ANÁLISE DE COBERTURA MUNICIPAL
    # =========================================================================
    
    print("\n" + "─" * 80)
    print("ETAPA 2: Analisando cobertura municipal do programa...")
    print("─" * 80)
    
    # Municípios únicos com equipes AD
    municipios_ad = df_ativas.groupby('UF')['CO_MUNICIPIO'].nunique().reset_index()
    municipios_ad.columns = ['UF', 'MUN_COM_AD']
    
    # Adicionar total de municípios por UF
    municipios_ad['MUN_TOTAL'] = municipios_ad['UF'].map(MUNICIPIOS_POR_UF)
    municipios_ad['COBERTURA_%'] = (municipios_ad['MUN_COM_AD'] / municipios_ad['MUN_TOTAL'] * 100).round(1)
    municipios_ad['REGIAO'] = municipios_ad['UF'].map(UF_REGIAO)
    
    # Ordenar por cobertura
    municipios_ad = municipios_ad.sort_values('COBERTURA_%', ascending=False)
    
    # Totais nacionais
    total_mun_ad = df_ativas['CO_MUNICIPIO'].nunique()
    cobertura_nacional = (total_mun_ad / TOTAL_MUNICIPIOS_BRASIL) * 100
    
    print(f"\n    Municípios com equipes AD: {total_mun_ad:,} de {TOTAL_MUNICIPIOS_BRASIL:,}")
    print(f"    Cobertura nacional: {cobertura_nacional:.1f}%")
    
    # Cobertura por região
    cobertura_regiao = df_ativas.groupby('REGIAO').agg({
        'CO_MUNICIPIO': 'nunique',
        'SEQ_EQUIPE': 'count'
    }).reset_index()
    cobertura_regiao.columns = ['REGIAO', 'MUN_COM_AD', 'TOTAL_EQUIPES']
    
    # Total de municípios por região
    mun_por_regiao = {}
    for uf, total in MUNICIPIOS_POR_UF.items():
        regiao = UF_REGIAO[uf]
        mun_por_regiao[regiao] = mun_por_regiao.get(regiao, 0) + total
    
    cobertura_regiao['MUN_TOTAL'] = cobertura_regiao['REGIAO'].map(mun_por_regiao)
    cobertura_regiao['COBERTURA_%'] = (cobertura_regiao['MUN_COM_AD'] / cobertura_regiao['MUN_TOTAL'] * 100).round(1)
    
    print(f"\n    Cobertura por região:")
    for _, row in cobertura_regiao.sort_values('COBERTURA_%', ascending=False).iterrows():
        print(f"      • {row['REGIAO']}: {row['MUN_COM_AD']} de {row['MUN_TOTAL']} municípios ({row['COBERTURA_%']:.1f}%)")
    
    # =========================================================================
    # ETAPA 3: CARREGAR PROFISSIONAIS E CARGA HORÁRIA
    # =========================================================================
    
    print("\n" + "─" * 80)
    print("ETAPA 3: Carregando profissionais das equipes AD...")
    print("─" * 80)
    
    # Obter SEQ_EQUIPE das equipes ativas para filtrar
    seq_equipes_ad = set(df_ativas['SEQ_EQUIPE'].unique())
    print(f"    Equipes a processar: {len(seq_equipes_ad):,}")
    
    # Carregar profissionais em chunks (arquivo grande)
    print("    Carregando vínculos profissionais (pode demorar)...")
    chunks_prof = []
    for chunk in pd.read_csv(
        os.path.join(CNES_DIR, "rlEstabEquipeProf202508.csv"),
        sep=';', encoding='latin-1', chunksize=100000, low_memory=False
    ):
        # Filtrar apenas equipes AD
        filtered = chunk[chunk['SEQ_EQUIPE'].isin(seq_equipes_ad)]
        if len(filtered) > 0:
            chunks_prof.append(filtered)
    
    if not chunks_prof:
        print("    ERRO: Nenhum profissional encontrado!")
        return
    
    df_prof = pd.concat(chunks_prof, ignore_index=True)
    
    # Filtrar profissionais ativos (sem data de desligamento)
    df_prof['DT_DESLIGAMENTO'] = pd.to_datetime(
        df_prof['DT_DESLIGAMENTO'], format='%d/%m/%Y', errors='coerce'
    )
    df_prof = df_prof[df_prof['DT_DESLIGAMENTO'].isna()].copy()
    
    print(f"    Vínculos ativos em equipes AD: {len(df_prof):,}")
    
    # Profissionais únicos para filtrar CHS
    prof_ids = set(df_prof['CO_PROFISSIONAL_SUS'].unique())
    print(f"    Profissionais únicos: {len(prof_ids):,}")
    
    # =========================================================================
    # ETAPA 4: CARREGAR CARGA HORÁRIA (CHS)
    # =========================================================================
    
    print("\n" + "─" * 80)
    print("ETAPA 4: Carregando Carga Horária SUS dos profissionais...")
    print("─" * 80)
    
    print("    Processando arquivo de CHS (6.3 milhões de registros)...")
    chunks_chs = []
    registros_processados = 0
    
    for chunk in pd.read_csv(
        os.path.join(CNES_DIR, "tbCargaHorariaSus202508.csv"),
        sep=';', encoding='latin-1', chunksize=500000, low_memory=False
    ):
        registros_processados += len(chunk)
        filtered = chunk[chunk['CO_PROFISSIONAL_SUS'].isin(prof_ids)]
        if len(filtered) > 0:
            chunks_chs.append(filtered)
        
        # Feedback de progresso
        if registros_processados % 1500000 == 0:
            print(f"      ... {registros_processados:,} registros processados")
    
    if not chunks_chs:
        print("    AVISO: Nenhuma CHS encontrada!")
        df_chs = pd.DataFrame(columns=['CO_PROFISSIONAL_SUS', 'CHS_TOTAL'])
    else:
        df_chs = pd.concat(chunks_chs, ignore_index=True)
        
        # Converter colunas numéricas
        for col in ['QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']:
            if col in df_chs.columns:
                df_chs[col] = pd.to_numeric(df_chs[col], errors='coerce').fillna(0)
        
        # Calcular CHS total por profissional
        df_chs['CHS_TOTAL'] = (
            df_chs.get('QT_CARGA_HORARIA_AMBULATORIAL', 0) + 
            df_chs.get('QT_CARGA_HORARIA_OUTROS', 0) + 
            df_chs.get('QT_CARGA_HOR_HOSP_SUS', 0)
        )
        
        # Agregar por profissional (pode ter múltiplos vínculos)
        df_chs = df_chs.groupby('CO_PROFISSIONAL_SUS')['CHS_TOTAL'].sum().reset_index()
    
    print(f"    Registros de CHS processados: {len(df_chs):,}")
    
    # =========================================================================
    # ETAPA 5: ENRIQUECER DADOS E VERIFICAR CONFORMIDADE
    # =========================================================================
    
    print("\n" + "─" * 80)
    print("ETAPA 5: Verificando conformidade legal de cada equipe...")
    print("─" * 80)
    
    # Merge: profissionais + CHS
    df_prof = df_prof.merge(df_chs, on='CO_PROFISSIONAL_SUS', how='left')
    df_prof['CHS_TOTAL'] = df_prof['CHS_TOTAL'].fillna(0)
    
    # Categorizar profissões
    df_prof['CATEGORIA'] = df_prof['CO_CBO'].apply(categorizar_cbo)
    
    # Estatísticas de CHS
    chs_valida = df_prof[df_prof['CHS_TOTAL'] >= CHS_MINIMA_INDIVIDUAL]
    print(f"    Profissionais com CHS >= 20h: {len(chs_valida):,} de {len(df_prof):,}")
    
    # Verificar cada equipe
    resultados = []
    problemas_por_tipo = {tp: Counter() for tp in TIPOS_EQUIPE_AD.keys()}
    equipes_processadas = 0
    
    for _, equipe in df_ativas.iterrows():
        seq = equipe['SEQ_EQUIPE']
        tipo = equipe['TP_EQUIPE']
        uf = equipe['UF']
        regiao = equipe['REGIAO']
        municipio = equipe['CO_MUNICIPIO']
        
        # Profissionais desta equipe com CHS >= 20h
        prof_equipe = df_prof[
            (df_prof['SEQ_EQUIPE'] == seq) & 
            (df_prof['CHS_TOTAL'] >= CHS_MINIMA_INDIVIDUAL)
        ]
        
        conforme, problemas = verificar_conformidade_equipe(prof_equipe, tipo)
        
        # Registrar problemas
        for prob in problemas:
            problemas_por_tipo[tipo][prob] += 1
        
        resultados.append({
            'SEQ_EQUIPE': seq,
            'CO_MUNICIPIO': municipio,
            'UF': uf,
            'REGIAO': regiao,
            'TIPO': TIPOS_EQUIPE_AD[tipo],
            'CONFORME': conforme,
            'PROBLEMAS': ','.join(problemas) if problemas else ''
        })
        
        equipes_processadas += 1
        if equipes_processadas % 500 == 0:
            print(f"      ... {equipes_processadas:,} equipes verificadas")
    
    df_resultados = pd.DataFrame(resultados)
    print(f"    Total de equipes analisadas: {len(df_resultados):,}")
    
    # =========================================================================
    # ETAPA 6: GERAR ESTATÍSTICAS E VISUALIZAÇÕES
    # =========================================================================
    
    print("\n" + "─" * 80)
    print("ETAPA 6: Gerando estatísticas e visualizações...")
    print("─" * 80)
    
    # ----- RESULTADOS GERAIS -----
    print("\n" + "=" * 80)
    print("RESULTADOS - CONFORMIDADE LEGAL NACIONAL")
    print("Portaria GM/MS nº 3.005/2024")
    print("=" * 80)
    
    total_equipes = len(df_resultados)
    total_conformes = df_resultados['CONFORME'].sum()
    taxa_nacional = 100 * total_conformes / total_equipes
    
    print(f"\n    BRASIL - VISÃO GERAL:")
    print(f"    ─────────────────────────────────────────────────────")
    print(f"    Total de equipes AD ativas: {total_equipes:,}")
    print(f"    Equipes em conformidade: {total_conformes:,} ({taxa_nacional:.1f}%)")
    print(f"    Equipes não conformes: {total_equipes - total_conformes:,} ({100-taxa_nacional:.1f}%)")
    
    # Por tipo de equipe
    print(f"\n    CONFORMIDADE POR TIPO DE EQUIPE:")
    print(f"    ─────────────────────────────────────────────────────")
    stats_tipo = []
    for tp, nome in TIPOS_EQUIPE_AD.items():
        df_tipo = df_resultados[df_resultados['TIPO'] == nome]
        if len(df_tipo) == 0:
            continue
        total = len(df_tipo)
        conformes = df_tipo['CONFORME'].sum()
        taxa = 100 * conformes / total
        stats_tipo.append({
            'TIPO': nome,
            'TOTAL': total,
            'CONFORMES': conformes,
            'NAO_CONFORMES': total - conformes,
            'TAXA_%': taxa
        })
        print(f"      {nome:10} │ Total: {total:5,} │ Conformes: {conformes:5,} │ Taxa: {taxa:5.1f}%")
        
        # Mostrar problemas mais frequentes
        if problemas_por_tipo[tp]:
            top_problemas = problemas_por_tipo[tp].most_common(3)
            problemas_str = ', '.join([f"{p}: {c}" for p, c in top_problemas])
            print(f"                │ Problemas: {problemas_str}")
    
    df_stats_tipo = pd.DataFrame(stats_tipo)
    
    # Por região
    print(f"\n    CONFORMIDADE POR REGIÃO:")
    print(f"    ─────────────────────────────────────────────────────")
    stats_regiao = df_resultados.groupby('REGIAO').agg({
        'CONFORME': ['count', 'sum']
    }).reset_index()
    stats_regiao.columns = ['REGIAO', 'TOTAL', 'CONFORMES']
    stats_regiao['TAXA_%'] = (100 * stats_regiao['CONFORMES'] / stats_regiao['TOTAL']).round(1)
    stats_regiao = stats_regiao.sort_values('TAXA_%', ascending=False)
    
    for _, row in stats_regiao.iterrows():
        print(f"      {row['REGIAO']:12} │ Total: {int(row['TOTAL']):5,} │ Conformes: {int(row['CONFORMES']):5,} │ Taxa: {row['TAXA_%']:5.1f}%")
    
    # Por UF (top 10)
    print(f"\n    TOP 10 UFs COM MAIS EQUIPES AD:")
    print(f"    ─────────────────────────────────────────────────────")
    stats_uf = df_resultados.groupby('UF').agg({
        'CONFORME': ['count', 'sum']
    }).reset_index()
    stats_uf.columns = ['UF', 'TOTAL', 'CONFORMES']
    stats_uf['TAXA_%'] = (100 * stats_uf['CONFORMES'] / stats_uf['TOTAL']).round(1)
    stats_uf = stats_uf.sort_values('TOTAL', ascending=False).head(10)
    
    for _, row in stats_uf.iterrows():
        print(f"      {row['UF']:3} │ Total: {int(row['TOTAL']):5,} │ Conformes: {int(row['CONFORMES']):5,} │ Taxa: {row['TAXA_%']:5.1f}%")
    
    # =========================================================================
    # ETAPA 7: GERAR VISUALIZAÇÕES (2 arquivos separados)
    # =========================================================================
    
    print("\n" + "─" * 80)
    print("ETAPA 7: Gerando visualizações...")
    print("─" * 80)
    
    # Cores consistentes
    cor_total = '#3498db'
    cor_conforme = '#27ae60'
    cor_nao_conforme = '#e74c3c'
    cores_tipo = {'EMAD I': '#2ecc71', 'EMAD II': '#3498db', 'EMAP': '#e74c3c', 'EMAP-R': '#9b59b6'}
    cores_regiao = {'Norte': '#1abc9c', 'Nordeste': '#f39c12', 'Sudeste': '#3498db', 
                    'Sul': '#27ae60', 'Centro-Oeste': '#9b59b6'}
    
    # =========================================================================
    # VISUALIZAÇÃO 1: COBERTURA MUNICIPAL
    # =========================================================================
    
    fig1, axes1 = plt.subplots(1, 2, figsize=(16, 7))
    fig1.suptitle('Programa Melhor em Casa - Cobertura Municipal no Brasil\n'
                  f'{total_mun_ad:,} municípios com equipes AD ({cobertura_nacional:.1f}% do Brasil)',
                  fontsize=14, fontweight='bold', y=1.02)
    
    # ----- GRÁFICO 1.1: Cobertura Municipal por Região (Pizza) -----
    ax1 = axes1[0]
    
    ordem_regioes = ['Sudeste', 'Nordeste', 'Sul', 'Norte', 'Centro-Oeste']
    dados_cobertura = cobertura_regiao.set_index('REGIAO').loc[ordem_regioes]
    
    wedges, texts, autotexts = ax1.pie(
        dados_cobertura['MUN_COM_AD'],
        labels=ordem_regioes,
        autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100*total_mun_ad)})',
        colors=[cores_regiao[r] for r in ordem_regioes],
        explode=[0.02] * 5,
        startangle=90,
        textprops={'fontsize': 10}
    )
    
    ax1.set_title(f'Distribuição de Municípios com AD por Região',
                  fontsize=12, fontweight='bold', pad=10)
    
    # ----- GRÁFICO 1.2: Cobertura por UF (Barras Horizontais) -----
    ax2 = axes1[1]
    
    top_ufs = municipios_ad.nlargest(15, 'MUN_COM_AD')
    
    y_pos = np.arange(len(top_ufs))
    bars1 = ax2.barh(y_pos, top_ufs['MUN_TOTAL'], color='#dfe6e9', label='Total de Municípios')
    bars2 = ax2.barh(y_pos, top_ufs['MUN_COM_AD'], color=cor_conforme, alpha=0.8, label='Com Equipes AD')
    
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(top_ufs['UF'])
    ax2.invert_yaxis()
    ax2.set_xlabel('Número de Municípios')
    ax2.set_title('Top 15 UFs - Cobertura Municipal', 
                  fontsize=12, fontweight='bold', pad=10)
    ax2.legend(loc='lower right', fontsize=9)
    
    for i, (idx, row) in enumerate(top_ufs.iterrows()):
        ax2.text(row['MUN_COM_AD'] + 5, i, f"{row['COBERTURA_%']:.0f}%", 
                va='center', fontsize=9, fontweight='bold', color=cor_conforme)
    
    ax2.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    
    fig1.text(0.5, 0.01, 
             f'Fonte: CNES/DATASUS (Agosto 2025) | Total Brasil: {TOTAL_MUNICIPIOS_BRASIL:,} municípios',
             ha='center', fontsize=9, style='italic', color='gray')
    
    output_cobertura_fig = os.path.join(OUTPUT_DIR, 'cobertura_municipal_brasil.png')
    plt.savefig(output_cobertura_fig, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig1)
    print(f"    1. Cobertura municipal: {output_cobertura_fig}")
    
    # =========================================================================
    # VISUALIZAÇÃO 2: CONFORMIDADE LEGAL
    # =========================================================================
    
    fig2, axes2 = plt.subplots(1, 2, figsize=(16, 7))
    fig2.suptitle('Programa Melhor em Casa - Conformidade Legal (Portaria 3.005/2024)\n'
                  f'{total_conformes:,} de {total_equipes:,} equipes em conformidade ({taxa_nacional:.1f}%)',
                  fontsize=14, fontweight='bold', y=1.02)
    
    # ----- GRÁFICO 2.1: Conformidade por Tipo de Equipe (Barras Empilhadas) -----
    ax3 = axes2[0]
    
    tipos_ordem = ['EMAD I', 'EMAD II', 'EMAP', 'EMAP-R']
    df_stats_tipo_sorted = df_stats_tipo.set_index('TIPO').loc[tipos_ordem].reset_index()
    
    x_pos = np.arange(len(df_stats_tipo_sorted))
    width = 0.6
    
    bars_conf = ax3.bar(x_pos, df_stats_tipo_sorted['CONFORMES'], width, 
                        label='Conformes', color=cor_conforme)
    bars_nconf = ax3.bar(x_pos, df_stats_tipo_sorted['NAO_CONFORMES'], width,
                         bottom=df_stats_tipo_sorted['CONFORMES'],
                         label='Não Conformes', color=cor_nao_conforme, alpha=0.7)
    
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(df_stats_tipo_sorted['TIPO'])
    ax3.set_ylabel('Número de Equipes')
    ax3.set_title(f'Conformidade por Tipo de Equipe',
                  fontsize=12, fontweight='bold', pad=10)
    ax3.legend(loc='upper right', fontsize=9)
    
    for i, (idx, row) in enumerate(df_stats_tipo_sorted.iterrows()):
        total = row['TOTAL']
        taxa = row['TAXA_%']
        ax3.text(i, total + 20, f'{int(total):,}\n({taxa:.0f}%)', 
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax3.grid(True, alpha=0.3, axis='y')
    
    # ----- GRÁFICO 2.2: Conformidade por Região (Barras Agrupadas) -----
    ax4 = axes2[1]
    
    ordem_regioes_graf = ['Sudeste', 'Nordeste', 'Sul', 'Centro-Oeste', 'Norte']
    stats_regiao_sorted = stats_regiao.set_index('REGIAO').loc[ordem_regioes_graf].reset_index()
    
    x_pos = np.arange(len(stats_regiao_sorted))
    width = 0.35
    
    bars_total = ax4.bar(x_pos - width/2, stats_regiao_sorted['TOTAL'], width,
                         label='Total de Equipes', color=cor_total, alpha=0.7)
    bars_conf = ax4.bar(x_pos + width/2, stats_regiao_sorted['CONFORMES'], width,
                        label='Equipes Conformes', color=cor_conforme)
    
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(stats_regiao_sorted['REGIAO'])
    ax4.set_ylabel('Número de Equipes')
    ax4.set_title('Conformidade por Região Geográfica',
                  fontsize=12, fontweight='bold', pad=10)
    ax4.legend(loc='upper right', fontsize=9)
    
    for i, (idx, row) in enumerate(stats_regiao_sorted.iterrows()):
        ax4.text(i + width/2, row['CONFORMES'] + 15, f"{row['TAXA_%']:.0f}%",
                ha='center', va='bottom', fontsize=9, fontweight='bold', color=cor_conforme)
    
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    
    fig2.text(0.5, 0.01, 
             f'Fonte: CNES/DATASUS (Agosto 2025) | Referência: Portaria GM/MS nº 3.005/2024',
             ha='center', fontsize=9, style='italic', color='gray')
    
    output_conformidade_fig = os.path.join(OUTPUT_DIR, 'conformidade_legal_brasil.png')
    plt.savefig(output_conformidade_fig, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig2)
    print(f"    2. Conformidade legal: {output_conformidade_fig}")
    
    # =========================================================================
    # ETAPA 8: SALVAR RESULTADOS EM CSV
    # =========================================================================
    
    print("\n" + "─" * 80)
    print("ETAPA 8: Salvando resultados em arquivos CSV...")
    print("─" * 80)
    
    # CSV 1: Resultado de conformidade por equipe
    output_conformidade = os.path.join(OUTPUT_DIR, 'conformidade_legal_brasil.csv')
    df_resultados.to_csv(output_conformidade, sep=';', index=False)
    print(f"    1. Conformidade por equipe: {output_conformidade}")
    
    # CSV 2: Cobertura municipal por UF
    output_cobertura = os.path.join(OUTPUT_DIR, 'cobertura_municipal_brasil.csv')
    municipios_ad.to_csv(output_cobertura, sep=';', index=False)
    print(f"    2. Cobertura municipal: {output_cobertura}")
    
    # CSV 3: Resumo por região
    output_regiao = os.path.join(OUTPUT_DIR, 'resumo_por_regiao_brasil.csv')
    stats_regiao.to_csv(output_regiao, sep=';', index=False)
    print(f"    3. Resumo por região: {output_regiao}")
    
    # =========================================================================
    # RESUMO FINAL
    # =========================================================================
    
    print("\n" + "=" * 80)
    print("RESUMO EXECUTIVO - PROGRAMA MELHOR EM CASA")
    print("=" * 80)
    
    print(f"""
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                        COBERTURA MUNICIPAL                              │
    ├─────────────────────────────────────────────────────────────────────────┤
    │  Municípios com equipes AD:     {total_mun_ad:>5,} de {TOTAL_MUNICIPIOS_BRASIL:,} ({cobertura_nacional:>5.1f}%)        │
    │  Equipes ativas no Brasil:      {total_equipes:>5,}                                    │
    └─────────────────────────────────────────────────────────────────────────┘
    
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                     CONFORMIDADE LEGAL                                  │
    │                 (Portaria GM/MS nº 3.005/2024)                          │
    ├─────────────────────────────────────────────────────────────────────────┤
    │  Equipes em conformidade:       {total_conformes:>5,} de {total_equipes:,} ({taxa_nacional:>5.1f}%)           │
    │  Equipes não conformes:         {total_equipes - total_conformes:>5,} ({100-taxa_nacional:>5.1f}%)                          │
    └─────────────────────────────────────────────────────────────────────────┘
    """)
    
    print("\n" + "─" * 80)
    print("Referências:")
    print("  • CNES/DATASUS - Competência Agosto/2025")
    print("  • Portaria GM/MS nº 3.005, de 2 de janeiro de 2024")
    print("  • IBGE - Total de municípios por UF (2022)")
    print("─" * 80)


if __name__ == '__main__':
    main()
