#!/usr/bin/env python3
"""
===============================================================================
ANÁLISE NACIONAL V2 - COBERTURA E CONFORMIDADE DO PROGRAMA MELHOR EM CASA
===============================================================================

Versão melhorada com:
1. Gráfico de cobertura municipal corrigido (números + porcentagem claros)
2. Análise per capita (equipes por 100 mil habitantes)
3. Visualizações mais informativas

Fontes de dados:
- CNES/DATASUS (competência 08/2025)
- IBGE (municípios e população por estado)
- Portaria GM/MS nº 3.005/2024

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
OUTPUT_VIS_DIR = os.path.join(OUTPUT_DIR, 'visualizacoes/nacional')
OUTPUT_CSV_DIR = os.path.join(OUTPUT_DIR, 'dados_csv')
CHS_MINIMA_INDIVIDUAL = 20

# Mapeamento UF
IBGE_UF_MAP = {
    '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
    '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL',
    '28': 'SE', '29': 'BA',
    '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
    '41': 'PR', '42': 'SC', '43': 'RS',
    '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF',
}

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
MUNICIPIOS_POR_UF = {
    'RO': 52, 'AC': 22, 'AM': 62, 'RR': 15, 'PA': 144, 'AP': 16, 'TO': 139,
    'MA': 217, 'PI': 224, 'CE': 184, 'RN': 167, 'PB': 223, 'PE': 185, 'AL': 102, 'SE': 75, 'BA': 417,
    'MG': 853, 'ES': 78, 'RJ': 92, 'SP': 645,
    'PR': 399, 'SC': 295, 'RS': 497,
    'MS': 79, 'MT': 141, 'GO': 246, 'DF': 1,
}

# População por UF (IBGE Censo 2022 - em milhares)
# Fonte: https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-demografico-2022.html
POPULACAO_POR_UF = {
    'RO': 1815, 'AC': 830, 'AM': 3942, 'RR': 636, 'PA': 8120, 'AP': 733, 'TO': 1512,
    'MA': 6775, 'PI': 3269, 'CE': 8794, 'RN': 3303, 'PB': 3975, 'PE': 9058, 'AL': 3128, 'SE': 2210, 'BA': 14136,
    'MG': 20539, 'ES': 3834, 'RJ': 16055, 'SP': 44411,
    'PR': 11444, 'SC': 7610, 'RS': 10882,
    'MS': 2757, 'MT': 3658, 'GO': 7055, 'DF': 2817,
}

TOTAL_MUNICIPIOS_BRASIL = sum(MUNICIPIOS_POR_UF.values())
TOTAL_POPULACAO_BRASIL = sum(POPULACAO_POR_UF.values())  # ~203 milhões

TIPOS_EQUIPE_AD = {
    22: 'EMAD I',
    46: 'EMAD II',
    23: 'EMAP',
    77: 'EMAP-R',
}

# Regras de conformidade (Portaria 3.005/2024)
REGRAS_EMAD = {
    22: {'MEDICO': 40, 'ENFERMEIRO': 60, 'TECNICO_ENFERMAGEM': 120, 'FISIO_OU_AS': 30},
    46: {'MEDICO': 20, 'ENFERMEIRO': 30, 'TECNICO_ENFERMAGEM': 120, 'FISIO_OU_AS': 30},
}

REGRAS_EMAP = {
    23: {'MIN_CATEGORIAS_NS': 3, 'CHS_TOTAL': 90},
    77: {'MIN_CATEGORIAS_NS': 3, 'CHS_TOTAL': 60},
}

PROF_NS_EMAP = ['FISIOTERAPEUTA', 'ASSISTENTE_SOCIAL', 'FONOAUDIOLOGO', 
                'NUTRICIONISTA', 'PSICOLOGO', 'TERAPEUTA_OCUPACIONAL',
                'ODONTOLOGO', 'FARMACEUTICO']
PROF_NS_EMAP_R = PROF_NS_EMAP + ['ENFERMEIRO']


def categorizar_cbo(cbo):
    """Categoriza código CBO em categoria profissional."""
    cbo_str = str(cbo).strip()
    if cbo_str.startswith(('2251', '2252', '2253')): return 'MEDICO'
    if cbo_str.startswith('2235'): return 'ENFERMEIRO'
    if cbo_str.startswith('3222'): return 'TECNICO_ENFERMAGEM'
    if cbo_str.startswith('2236'): return 'FISIOTERAPEUTA'
    if cbo_str.startswith('2516'): return 'ASSISTENTE_SOCIAL'
    if cbo_str.startswith('2238'): return 'FONOAUDIOLOGO'
    if cbo_str.startswith('2237'): return 'NUTRICIONISTA'
    if cbo_str.startswith('2515'): return 'PSICOLOGO'
    if cbo_str.startswith('2239'): return 'TERAPEUTA_OCUPACIONAL'
    if cbo_str.startswith('2232'): return 'ODONTOLOGO'
    if cbo_str.startswith('2234'): return 'FARMACEUTICO'
    return 'OUTRO'


def extrair_uf(codigo_municipio):
    """Extrai sigla UF do código IBGE do município."""
    prefixo = str(codigo_municipio).strip()[:2]
    return IBGE_UF_MAP.get(prefixo, 'DESCONHECIDO')


def verificar_conformidade_equipe(df_prof, tipo_equipe):
    """Verifica conformidade de uma equipe com a Portaria 3.005/2024."""
    problemas = []
    
    if tipo_equipe in [22, 46]:
        regras = REGRAS_EMAD[tipo_equipe]
        for categoria, minimo in regras.items():
            if categoria == 'FISIO_OU_AS':
                chs = df_prof[df_prof['CATEGORIA'].isin(
                    ['FISIOTERAPEUTA', 'ASSISTENTE_SOCIAL']
                )]['CHS_TOTAL'].sum()
            else:
                chs = df_prof[df_prof['CATEGORIA'] == categoria]['CHS_TOTAL'].sum()
            if chs < minimo:
                problemas.append(categoria)
    else:
        regras = REGRAS_EMAP[tipo_equipe]
        lista_ns = PROF_NS_EMAP_R if tipo_equipe == 77 else PROF_NS_EMAP
        prof_ns = df_prof[df_prof['CATEGORIA'].isin(lista_ns)]
        n_categorias = prof_ns['CATEGORIA'].nunique()
        chs_total = prof_ns['CHS_TOTAL'].sum()
        if n_categorias < regras['MIN_CATEGORIAS_NS']:
            problemas.append('POUCAS_CATEGORIAS_NS')
        if chs_total < regras['CHS_TOTAL']:
            problemas.append('CHS_TOTAL_INSUFICIENTE')
    
    return len(problemas) == 0, problemas


def main():
    print("=" * 80)
    print("ANÁLISE NACIONAL V2 - PROGRAMA MELHOR EM CASA")
    print("Cobertura Municipal, Conformidade Legal e Análise Per Capita")
    print("=" * 80)
    
    # =========================================================================
    # ETAPA 1: CARREGAR EQUIPES AD
    # =========================================================================
    
    print("\n[1] Carregando equipes de Atenção Domiciliar...")
    
    df_equipes = pd.read_csv(
        os.path.join(CNES_DIR, "tbEquipe202508.csv"),
        sep=';', encoding='latin-1', low_memory=False
    )
    
    df_equipes_ad = df_equipes[df_equipes['TP_EQUIPE'].isin(TIPOS_EQUIPE_AD.keys())].copy()
    df_equipes_ad['DT_DESATIVACAO'] = pd.to_datetime(
        df_equipes_ad['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce'
    )
    df_ativas = df_equipes_ad[df_equipes_ad['DT_DESATIVACAO'].isna()].copy()
    df_ativas['UF'] = df_ativas['CO_MUNICIPIO'].apply(extrair_uf)
    df_ativas['REGIAO'] = df_ativas['UF'].map(UF_REGIAO)
    df_ativas['TIPO_NOME'] = df_ativas['TP_EQUIPE'].map(TIPOS_EQUIPE_AD)
    
    print(f"    Total de equipes AD ativas: {len(df_ativas):,}")
    
    # =========================================================================
    # ETAPA 2: ANÁLISE DE COBERTURA MUNICIPAL
    # =========================================================================
    
    print("\n[2] Analisando cobertura municipal...")
    
    # Por UF
    municipios_ad = df_ativas.groupby('UF').agg({
        'CO_MUNICIPIO': 'nunique',
        'SEQ_EQUIPE': 'count'
    }).reset_index()
    municipios_ad.columns = ['UF', 'MUN_COM_AD', 'N_EQUIPES']
    municipios_ad['MUN_TOTAL'] = municipios_ad['UF'].map(MUNICIPIOS_POR_UF)
    municipios_ad['POPULACAO'] = municipios_ad['UF'].map(POPULACAO_POR_UF)
    municipios_ad['COBERTURA_%'] = (municipios_ad['MUN_COM_AD'] / municipios_ad['MUN_TOTAL'] * 100).round(1)
    municipios_ad['EQUIPES_POR_100K'] = (municipios_ad['N_EQUIPES'] / municipios_ad['POPULACAO'] * 100).round(2)
    municipios_ad['REGIAO'] = municipios_ad['UF'].map(UF_REGIAO)
    
    total_mun_ad = df_ativas['CO_MUNICIPIO'].nunique()
    total_equipes = len(df_ativas)
    cobertura_nacional = (total_mun_ad / TOTAL_MUNICIPIOS_BRASIL) * 100
    
    print(f"    Municípios com AD: {total_mun_ad:,} de {TOTAL_MUNICIPIOS_BRASIL:,} ({cobertura_nacional:.1f}%)")
    
    # Por região
    cobertura_regiao = df_ativas.groupby('REGIAO').agg({
        'CO_MUNICIPIO': 'nunique',
        'SEQ_EQUIPE': 'count'
    }).reset_index()
    cobertura_regiao.columns = ['REGIAO', 'MUN_COM_AD', 'N_EQUIPES']
    
    mun_por_regiao = {}
    pop_por_regiao = {}
    for uf in MUNICIPIOS_POR_UF:
        regiao = UF_REGIAO[uf]
        mun_por_regiao[regiao] = mun_por_regiao.get(regiao, 0) + MUNICIPIOS_POR_UF[uf]
        pop_por_regiao[regiao] = pop_por_regiao.get(regiao, 0) + POPULACAO_POR_UF[uf]
    
    cobertura_regiao['MUN_TOTAL'] = cobertura_regiao['REGIAO'].map(mun_por_regiao)
    cobertura_regiao['POPULACAO'] = cobertura_regiao['REGIAO'].map(pop_por_regiao)
    cobertura_regiao['COBERTURA_%'] = (cobertura_regiao['MUN_COM_AD'] / cobertura_regiao['MUN_TOTAL'] * 100).round(1)
    cobertura_regiao['EQUIPES_POR_100K'] = (cobertura_regiao['N_EQUIPES'] / cobertura_regiao['POPULACAO'] * 100).round(2)
    
    # =========================================================================
    # ETAPA 3-5: CARREGAR PROFISSIONAIS, CHS E VERIFICAR CONFORMIDADE
    # =========================================================================
    
    print("\n[3] Carregando profissionais...")
    seq_equipes_ad = set(df_ativas['SEQ_EQUIPE'].unique())
    
    chunks_prof = []
    for chunk in pd.read_csv(
        os.path.join(CNES_DIR, "rlEstabEquipeProf202508.csv"),
        sep=';', encoding='latin-1', chunksize=100000, low_memory=False
    ):
        filtered = chunk[chunk['SEQ_EQUIPE'].isin(seq_equipes_ad)]
        if len(filtered) > 0:
            chunks_prof.append(filtered)
    
    df_prof = pd.concat(chunks_prof, ignore_index=True)
    df_prof['DT_DESLIGAMENTO'] = pd.to_datetime(
        df_prof['DT_DESLIGAMENTO'], format='%d/%m/%Y', errors='coerce'
    )
    df_prof = df_prof[df_prof['DT_DESLIGAMENTO'].isna()].copy()
    prof_ids = set(df_prof['CO_PROFISSIONAL_SUS'].unique())
    print(f"    Profissionais únicos: {len(prof_ids):,}")
    
    print("\n[4] Carregando CHS...")
    chunks_chs = []
    for chunk in pd.read_csv(
        os.path.join(CNES_DIR, "tbCargaHorariaSus202508.csv"),
        sep=';', encoding='latin-1', chunksize=500000, low_memory=False
    ):
        filtered = chunk[chunk['CO_PROFISSIONAL_SUS'].isin(prof_ids)]
        if len(filtered) > 0:
            chunks_chs.append(filtered)
    
    df_chs = pd.concat(chunks_chs, ignore_index=True)
    for col in ['QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']:
        if col in df_chs.columns:
            df_chs[col] = pd.to_numeric(df_chs[col], errors='coerce').fillna(0)
    
    df_chs['CHS_TOTAL'] = (
        df_chs.get('QT_CARGA_HORARIA_AMBULATORIAL', 0) + 
        df_chs.get('QT_CARGA_HORARIA_OUTROS', 0) + 
        df_chs.get('QT_CARGA_HOR_HOSP_SUS', 0)
    )
    df_chs = df_chs.groupby('CO_PROFISSIONAL_SUS')['CHS_TOTAL'].sum().reset_index()
    
    df_prof = df_prof.merge(df_chs, on='CO_PROFISSIONAL_SUS', how='left')
    df_prof['CHS_TOTAL'] = df_prof['CHS_TOTAL'].fillna(0)
    df_prof['CATEGORIA'] = df_prof['CO_CBO'].apply(categorizar_cbo)
    
    print("\n[5] Verificando conformidade...")
    resultados = []
    
    for _, equipe in df_ativas.iterrows():
        seq = equipe['SEQ_EQUIPE']
        tipo = equipe['TP_EQUIPE']
        uf = equipe['UF']
        regiao = equipe['REGIAO']
        
        prof_equipe = df_prof[
            (df_prof['SEQ_EQUIPE'] == seq) & 
            (df_prof['CHS_TOTAL'] >= CHS_MINIMA_INDIVIDUAL)
        ]
        
        conforme, problemas = verificar_conformidade_equipe(prof_equipe, tipo)
        
        resultados.append({
            'SEQ_EQUIPE': seq,
            'UF': uf,
            'REGIAO': regiao,
            'TIPO': TIPOS_EQUIPE_AD[tipo],
            'CONFORME': conforme,
        })
    
    df_resultados = pd.DataFrame(resultados)
    total_conformes = df_resultados['CONFORME'].sum()
    taxa_nacional = 100 * total_conformes / total_equipes
    
    print(f"    Conformidade: {total_conformes:,} de {total_equipes:,} ({taxa_nacional:.1f}%)")
    
    # =========================================================================
    # ETAPA 6: VISUALIZAÇÕES MELHORADAS
    # =========================================================================
    
    print("\n[6] Gerando visualizações...")
    
    cores_tipo = {'EMAD I': '#2ecc71', 'EMAD II': '#3498db', 'EMAP': '#e74c3c', 'EMAP-R': '#9b59b6'}
    cores_regiao = {'Norte': '#1abc9c', 'Nordeste': '#f39c12', 'Sudeste': '#3498db', 
                    'Sul': '#27ae60', 'Centro-Oeste': '#9b59b6'}
    
    # =========================================================================
    # VISUALIZAÇÃO 1: COBERTURA MUNICIPAL (MELHORADA)
    # =========================================================================
    
    fig1, axes1 = plt.subplots(1, 2, figsize=(18, 9))
    fig1.suptitle('Programa Melhor em Casa - Cobertura Municipal no Brasil\n'
                  f'{total_mun_ad:,} municípios com equipes AD ({cobertura_nacional:.1f}% do Brasil)',
                  fontsize=14, fontweight='bold', y=1.02)
    
    # ----- GRÁFICO 1.1: Top 15 UFs ORDENADO POR COBERTURA PERCENTUAL -----
    ax1 = axes1[0]
    
    # Ordenar por PORCENTAGEM de cobertura (não por números brutos)
    top_ufs_pct = municipios_ad.nlargest(15, 'COBERTURA_%').copy()
    
    y_pos = np.arange(len(top_ufs_pct))
    
    # Barras: proporção coberta vs não coberta
    bars_total = ax1.barh(y_pos, top_ufs_pct['MUN_TOTAL'], color='#ecf0f1', 
                          edgecolor='#bdc3c7', label='Sem cobertura')
    bars_ad = ax1.barh(y_pos, top_ufs_pct['MUN_COM_AD'], color='#27ae60', 
                       alpha=0.85, label='Com equipes AD')
    
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(top_ufs_pct['UF'])
    ax1.invert_yaxis()
    ax1.set_xlabel('Número de Municípios')
    ax1.set_title('Top 15 UFs por Cobertura Percentual\n(ordenado pela % de municípios cobertos)', 
                  fontsize=11, fontweight='bold', pad=10)
    ax1.legend(loc='lower right', fontsize=9)
    
    # Anotações com AMBOS os valores
    for i, (_, row) in enumerate(top_ufs_pct.iterrows()):
        # Texto no final da barra cinza (total)
        ax1.text(row['MUN_TOTAL'] + 5, i, 
                 f"{int(row['MUN_COM_AD'])}/{int(row['MUN_TOTAL'])} = {row['COBERTURA_%']:.0f}%", 
                 va='center', fontsize=9, fontweight='bold', color='#2c3e50')
    
    ax1.grid(True, alpha=0.3, axis='x')
    ax1.set_xlim(0, top_ufs_pct['MUN_TOTAL'].max() * 1.35)
    
    # ----- GRÁFICO 1.2: Top 15 UFs ORDENADO POR NÚMERO BRUTO -----
    ax2 = axes1[1]
    
    # Ordenar por NÚMERO BRUTO de equipes
    top_ufs_bruto = municipios_ad.nlargest(15, 'N_EQUIPES').copy()
    
    y_pos = np.arange(len(top_ufs_bruto))
    
    bars = ax2.barh(y_pos, top_ufs_bruto['N_EQUIPES'], color='#3498db', alpha=0.85)
    
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(top_ufs_bruto['UF'])
    ax2.invert_yaxis()
    ax2.set_xlabel('Número de Equipes AD')
    ax2.set_title('Top 15 UFs por Número de Equipes\n(ordenado pelo total de equipes)', 
                  fontsize=11, fontweight='bold', pad=10)
    
    # Anotações com número de equipes E cobertura percentual
    for i, (_, row) in enumerate(top_ufs_bruto.iterrows()):
        ax2.text(row['N_EQUIPES'] + 3, i, 
                 f"{int(row['N_EQUIPES'])} equipes ({row['COBERTURA_%']:.0f}% mun.)", 
                 va='center', fontsize=9, fontweight='bold', color='#2c3e50')
    
    ax2.grid(True, alpha=0.3, axis='x')
    ax2.set_xlim(0, top_ufs_bruto['N_EQUIPES'].max() * 1.4)
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig1.text(0.5, 0.01, 
             f'Fonte: CNES/DATASUS (Agosto 2025) | Total Brasil: {TOTAL_MUNICIPIOS_BRASIL:,} municípios',
             ha='center', fontsize=9, style='italic', color='gray')
    
    output_fig1 = os.path.join(OUTPUT_VIS_DIR, 'cobertura_municipal_brasil_v2.png')
    plt.savefig(output_fig1, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig1)
    print(f"    1. Cobertura municipal: {output_fig1}")
    
    # =========================================================================
    # VISUALIZAÇÃO 2: ANÁLISE PER CAPITA (NOVA!)
    # =========================================================================
    
    fig2, axes2 = plt.subplots(1, 2, figsize=(16, 8))
    fig2.suptitle('Programa Melhor em Casa - Análise Per Capita\n'
                  f'Equipes por 100 mil habitantes - Brasil ({total_equipes:,} equipes)',
                  fontsize=14, fontweight='bold', y=1.02)
    
    # ----- GRÁFICO 2.1: Equipes por 100k por REGIÃO -----
    ax3 = axes2[0]
    
    ordem_regioes = cobertura_regiao.sort_values('EQUIPES_POR_100K', ascending=True)
    
    cores_barras = [cores_regiao[r] for r in ordem_regioes['REGIAO']]
    bars = ax3.barh(ordem_regioes['REGIAO'], ordem_regioes['EQUIPES_POR_100K'], 
                    color=cores_barras, alpha=0.85)
    
    ax3.set_xlabel('Equipes por 100 mil habitantes')
    ax3.set_title('Densidade de Equipes AD por Região\n(equipes por 100 mil habitantes)', 
                  fontsize=11, fontweight='bold', pad=10)
    
    # Linha de média nacional
    media_nacional = total_equipes / TOTAL_POPULACAO_BRASIL * 100
    ax3.axvline(media_nacional, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax3.text(media_nacional + 0.02, 4.5, f'Média Brasil\n{media_nacional:.2f}', 
             fontsize=9, color='red', va='top')
    
    # Anotações
    for i, (_, row) in enumerate(ordem_regioes.iterrows()):
        ax3.text(row['EQUIPES_POR_100K'] + 0.03, i, 
                 f"{row['EQUIPES_POR_100K']:.2f}\n({int(row['N_EQUIPES'])} eq.)", 
                 va='center', fontsize=9, fontweight='bold')
    
    ax3.grid(True, alpha=0.3, axis='x')
    ax3.set_xlim(0, ordem_regioes['EQUIPES_POR_100K'].max() * 1.25)
    
    # ----- GRÁFICO 2.2: Top 15 UFs por equipes per capita -----
    ax4 = axes2[1]
    
    top_ufs_percapita = municipios_ad.nlargest(15, 'EQUIPES_POR_100K').copy()
    
    y_pos = np.arange(len(top_ufs_percapita))
    cores_uf = [cores_regiao[UF_REGIAO[uf]] for uf in top_ufs_percapita['UF']]
    
    bars = ax4.barh(y_pos, top_ufs_percapita['EQUIPES_POR_100K'], color=cores_uf, alpha=0.85)
    
    ax4.set_yticks(y_pos)
    ax4.set_yticklabels(top_ufs_percapita['UF'])
    ax4.invert_yaxis()
    ax4.set_xlabel('Equipes por 100 mil habitantes')
    ax4.set_title('Top 15 UFs por Densidade de Equipes\n(equipes per capita)', 
                  fontsize=11, fontweight='bold', pad=10)
    
    # Linha de média
    ax4.axvline(media_nacional, color='red', linestyle='--', linewidth=2, alpha=0.7)
    
    # Anotações
    for i, (_, row) in enumerate(top_ufs_percapita.iterrows()):
        ax4.text(row['EQUIPES_POR_100K'] + 0.05, i, 
                 f"{row['EQUIPES_POR_100K']:.2f} ({int(row['N_EQUIPES'])} eq.)", 
                 va='center', fontsize=9, fontweight='bold')
    
    ax4.grid(True, alpha=0.3, axis='x')
    ax4.set_xlim(0, top_ufs_percapita['EQUIPES_POR_100K'].max() * 1.25)
    
    # Legenda de regiões
    handles = [mpatches.Patch(color=cores_regiao[r], label=r) for r in cores_regiao]
    ax4.legend(handles=handles, title='Região', loc='lower right', fontsize=8)
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig2.text(0.5, 0.01, 
             f'Fonte: CNES/DATASUS (Agosto 2025) + IBGE Censo 2022 | População Brasil: {TOTAL_POPULACAO_BRASIL:,} mil',
             ha='center', fontsize=9, style='italic', color='gray')
    
    output_fig2 = os.path.join(OUTPUT_VIS_DIR, 'analise_percapita_brasil.png')
    plt.savefig(output_fig2, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig2)
    print(f"    2. Análise per capita: {output_fig2}")
    
    # =========================================================================
    # VISUALIZAÇÃO 3: CONFORMIDADE LEGAL
    # =========================================================================
    
    fig3, axes3 = plt.subplots(1, 2, figsize=(16, 7))
    fig3.suptitle('Programa Melhor em Casa - Conformidade Legal (Portaria 3.005/2024)\n'
                  f'{total_conformes:,} de {total_equipes:,} equipes em conformidade ({taxa_nacional:.1f}%)',
                  fontsize=14, fontweight='bold', y=1.02)
    
    # Por tipo
    ax5 = axes3[0]
    stats_tipo = df_resultados.groupby('TIPO').agg({
        'CONFORME': ['count', 'sum']
    }).reset_index()
    stats_tipo.columns = ['TIPO', 'TOTAL', 'CONFORMES']
    stats_tipo['NAO_CONFORMES'] = stats_tipo['TOTAL'] - stats_tipo['CONFORMES']
    stats_tipo['TAXA_%'] = (100 * stats_tipo['CONFORMES'] / stats_tipo['TOTAL']).round(1)
    
    tipos_ordem = ['EMAD I', 'EMAD II', 'EMAP', 'EMAP-R']
    stats_tipo = stats_tipo.set_index('TIPO').loc[tipos_ordem].reset_index()
    
    x_pos = np.arange(len(stats_tipo))
    ax5.bar(x_pos, stats_tipo['CONFORMES'], 0.6, label='Conformes', color='#27ae60')
    ax5.bar(x_pos, stats_tipo['NAO_CONFORMES'], 0.6, bottom=stats_tipo['CONFORMES'],
            label='Não Conformes', color='#e74c3c', alpha=0.7)
    
    ax5.set_xticks(x_pos)
    ax5.set_xticklabels(stats_tipo['TIPO'])
    ax5.set_ylabel('Número de Equipes')
    ax5.set_title('Conformidade por Tipo de Equipe', fontsize=11, fontweight='bold')
    ax5.legend(loc='upper right')
    
    for i, row in stats_tipo.iterrows():
        ax5.text(i, row['TOTAL'] + 15, f"{int(row['TOTAL'])}\n({row['TAXA_%']:.0f}%)", 
                ha='center', fontsize=9, fontweight='bold')
    
    ax5.grid(True, alpha=0.3, axis='y')
    
    # Por região
    ax6 = axes3[1]
    stats_regiao = df_resultados.groupby('REGIAO').agg({
        'CONFORME': ['count', 'sum']
    }).reset_index()
    stats_regiao.columns = ['REGIAO', 'TOTAL', 'CONFORMES']
    stats_regiao['TAXA_%'] = (100 * stats_regiao['CONFORMES'] / stats_regiao['TOTAL']).round(1)
    stats_regiao = stats_regiao.sort_values('TOTAL', ascending=False)
    
    x_pos = np.arange(len(stats_regiao))
    ax6.bar(x_pos - 0.2, stats_regiao['TOTAL'], 0.35, label='Total', color='#3498db', alpha=0.7)
    ax6.bar(x_pos + 0.2, stats_regiao['CONFORMES'], 0.35, label='Conformes', color='#27ae60')
    
    ax6.set_xticks(x_pos)
    ax6.set_xticklabels(stats_regiao['REGIAO'])
    ax6.set_ylabel('Número de Equipes')
    ax6.set_title('Conformidade por Região', fontsize=11, fontweight='bold')
    ax6.legend(loc='upper right')
    
    # CORRIGIDO: usar enumerate para posição correta
    for idx, (_, row) in enumerate(stats_regiao.iterrows()):
        ax6.text(idx + 0.2, row['CONFORMES'] + 10, f"{row['TAXA_%']:.0f}%", 
                ha='center', fontsize=9, fontweight='bold', color='#27ae60')
    
    ax6.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig3.text(0.5, 0.01, 
             f'Fonte: CNES/DATASUS (Agosto 2025) | Portaria GM/MS nº 3.005/2024',
             ha='center', fontsize=9, style='italic', color='gray')
    
    output_fig3 = os.path.join(OUTPUT_VIS_DIR, 'conformidade_legal_brasil_v2.png')
    plt.savefig(output_fig3, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig3)
    print(f"    3. Conformidade legal: {output_fig3}")
    
    # =========================================================================
    # SALVAR CSVs
    # =========================================================================
    
    print("\n[7] Salvando CSVs...")
    
    municipios_ad.to_csv(os.path.join(OUTPUT_CSV_DIR, 'cobertura_municipal_brasil_v2.csv'), sep=';', index=False)
    cobertura_regiao.to_csv(os.path.join(OUTPUT_CSV_DIR, 'cobertura_regiao_brasil_v2.csv'), sep=';', index=False)
    df_resultados.to_csv(os.path.join(OUTPUT_CSV_DIR, 'conformidade_legal_brasil_v2.csv'), sep=';', index=False)
    
    # =========================================================================
    # RESUMO FINAL
    # =========================================================================
    
    print("\n" + "=" * 80)
    print("RESUMO EXECUTIVO")
    print("=" * 80)
    
    print(f"""
    COBERTURA MUNICIPAL:
      Municípios com AD: {total_mun_ad:,} de {TOTAL_MUNICIPIOS_BRASIL:,} ({cobertura_nacional:.1f}%)
      Total de equipes: {total_equipes:,}
    
    ANÁLISE PER CAPITA:
      Média nacional: {media_nacional:.2f} equipes por 100 mil habitantes
      Melhor região: {cobertura_regiao.loc[cobertura_regiao['EQUIPES_POR_100K'].idxmax(), 'REGIAO']} ({cobertura_regiao['EQUIPES_POR_100K'].max():.2f}/100k)
    
    CONFORMIDADE LEGAL (Portaria 3.005/2024):
      Equipes conformes: {total_conformes:,} de {total_equipes:,} ({taxa_nacional:.1f}%)
    """)
    
    print("Arquivos gerados em:", OUTPUT_DIR)


if __name__ == '__main__':
    main()
