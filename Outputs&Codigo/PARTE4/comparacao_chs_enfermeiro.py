"""
COMPARAÇÃO: Impacto do Requisito de CHS de Enfermeiro na Completude
=====================================================================

Este script compara a taxa de completude das equipes EMAD I considerando:
- Cenário LEGAL (Portaria 3.005/2024): Enfermeiro ≥ 60h
- Cenário HIPOTÉTICO: Enfermeiro ≥ 40h

Objetivo: Demonstrar quantitativamente o impacto do requisito de 60h
na classificação de equipes como "incompletas".

Autor: Análise Comparativa - Projeto FAPESP
Data: Dezembro 2025
"""

import pandas as pd
import numpy as np
import os

# Configurações
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CNES_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "CNES_DATA")
SP_CAPITAL = 355030
CHS_MINIMA_INDIVIDUAL = 20  # Art. 547, §1º


def categorizar_cbo(cbo):
    """Categoriza CBO em tipo de profissional."""
    cbo_str = str(cbo).strip()
    if cbo_str.startswith(('2251', '2252', '2253')):
        return 'MEDICO'
    if cbo_str.startswith('2235'):
        return 'ENFERMEIRO'
    if cbo_str.startswith('3222'):
        return 'TECNICO_ENFERMAGEM'
    if cbo_str.startswith('2236'):
        return 'FISIOTERAPEUTA'
    if cbo_str.startswith('2516'):
        return 'ASSISTENTE_SOCIAL'
    return 'OUTRO'


def verificar_completude_emad_i(prof_equipe, chs_enfermeiro_min):
    """
    Verifica completude de uma equipe EMAD I.
    
    Parâmetros fixos (Portaria 3.005/2024):
    - Médico: ≥40h
    - Técnico Enfermagem: ≥120h
    - Fisio OU AS: ≥30h (soma)
    
    Parâmetro variável:
    - Enfermeiro: chs_enfermeiro_min (40h ou 60h)
    """
    chs_medico = prof_equipe[prof_equipe['CATEGORIA_CBO'] == 'MEDICO']['CHS_REAL'].sum()
    chs_enfermeiro = prof_equipe[prof_equipe['CATEGORIA_CBO'] == 'ENFERMEIRO']['CHS_REAL'].sum()
    chs_tecnico = prof_equipe[prof_equipe['CATEGORIA_CBO'] == 'TECNICO_ENFERMAGEM']['CHS_REAL'].sum()
    chs_fisio = prof_equipe[prof_equipe['CATEGORIA_CBO'] == 'FISIOTERAPEUTA']['CHS_REAL'].sum()
    chs_as = prof_equipe[prof_equipe['CATEGORIA_CBO'] == 'ASSISTENTE_SOCIAL']['CHS_REAL'].sum()
    chs_fisio_as = chs_fisio + chs_as
    
    completa = (
        chs_medico >= 40 and 
        chs_enfermeiro >= chs_enfermeiro_min and 
        chs_tecnico >= 120 and 
        chs_fisio_as >= 30
    )
    
    motivos = []
    if chs_medico < 40:
        motivos.append(f"MÉDICO: {chs_medico:.0f}h < 40h")
    if chs_enfermeiro < chs_enfermeiro_min:
        motivos.append(f"ENFERMEIRO: {chs_enfermeiro:.0f}h < {chs_enfermeiro_min}h")
    if chs_tecnico < 120:
        motivos.append(f"TÉC.ENF: {chs_tecnico:.0f}h < 120h")
    if chs_fisio_as < 30:
        motivos.append(f"FISIO/AS: {chs_fisio_as:.0f}h < 30h")
    
    return completa, chs_enfermeiro, motivos


def main():
    print("="*70)
    print("COMPARAÇÃO: IMPACTO DO REQUISITO DE CHS DE ENFERMEIRO")
    print("="*70)
    print("\nCenários analisados:")
    print("  • LEGAL (Portaria 3.005/2024): Enfermeiro ≥ 60h")
    print("  • HIPOTÉTICO: Enfermeiro ≥ 40h")
    print()
    
    # 1. Carregar equipes EMAD I ativas
    print("[1] Carregando equipes EMAD I ativas em SP Capital...")
    df_equipes = pd.read_csv(
        os.path.join(CNES_DIR, "tbEquipe202508.csv"),
        sep=';', encoding='latin-1', low_memory=False
    )
    df_equipes = df_equipes[
        (df_equipes['TP_EQUIPE'] == 22) &  # EMAD I
        (df_equipes['CO_MUNICIPIO'] == SP_CAPITAL)
    ].copy()
    df_equipes['DT_DESATIVACAO'] = pd.to_datetime(
        df_equipes['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce'
    )
    df_ativas = df_equipes[df_equipes['DT_DESATIVACAO'].isna()]
    print(f"    Equipes EMAD I ativas: {len(df_ativas)}")
    
    # 2. Carregar profissionais
    print("[2] Carregando profissionais das equipes...")
    df_prof = pd.read_csv(
        os.path.join(CNES_DIR, "rlEstabEquipeProf202508.csv"),
        sep=';', encoding='latin-1', low_memory=False,
        usecols=['SEQ_EQUIPE', 'CO_PROFISSIONAL_SUS', 'CO_CBO', 
                 'CO_MUNICIPIO', 'DT_DESLIGAMENTO']
    )
    df_prof = df_prof[df_prof['CO_MUNICIPIO'] == SP_CAPITAL]
    df_prof['DT_DESLIGAMENTO'] = pd.to_datetime(
        df_prof['DT_DESLIGAMENTO'], format='%d/%m/%Y', errors='coerce'
    )
    
    seq_equipes = set(df_ativas['SEQ_EQUIPE'].unique())
    df_prof = df_prof[df_prof['SEQ_EQUIPE'].isin(seq_equipes)]
    df_prof = df_prof[df_prof['DT_DESLIGAMENTO'].isna()]  # Só ativos
    print(f"    Vínculos ativos: {len(df_prof)}")
    
    # 3. Carregar CHS
    print("[3] Carregando CHS...")
    profissionais = set(df_prof['CO_PROFISSIONAL_SUS'].unique())
    
    df_chs = pd.read_csv(
        os.path.join(CNES_DIR, "chs_ad_sp.csv"),
        sep=';', encoding='latin-1', low_memory=False
    )
    df_chs = df_chs[df_chs['CO_PROFISSIONAL_SUS'].isin(profissionais)]
    
    for col in ['QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']:
        df_chs[col] = pd.to_numeric(df_chs.get(col, 0), errors='coerce').fillna(0)
    
    df_chs['CHS_REAL'] = (df_chs['QT_CARGA_HORARIA_AMBULATORIAL'] + 
                          df_chs['QT_CARGA_HORARIA_OUTROS'] + 
                          df_chs['QT_CARGA_HOR_HOSP_SUS'])
    
    df_chs_agg = df_chs.groupby('CO_PROFISSIONAL_SUS').agg({'CHS_REAL': 'sum'}).reset_index()
    print(f"    Profissionais com CHS: {len(df_chs_agg)}")
    
    # 4. Enriquecer
    print("[4] Preparando análise...")
    df_prof_chs = df_prof.merge(df_chs_agg, on='CO_PROFISSIONAL_SUS', how='left')
    df_prof_chs['CHS_REAL'] = df_prof_chs['CHS_REAL'].fillna(0)
    df_prof_chs['CATEGORIA_CBO'] = df_prof_chs['CO_CBO'].apply(categorizar_cbo)
    
    # Aplicar filtro de 20h (Art. 547, §1º)
    df_prof_validos = df_prof_chs[df_prof_chs['CHS_REAL'] >= CHS_MINIMA_INDIVIDUAL]
    
    # 5. Analisar nos dois cenários
    print("\n" + "="*70)
    print("RESULTADOS DA COMPARAÇÃO")
    print("="*70)
    
    resultados = {
        'legal_60h': {'completas': 0, 'incompletas': 0, 'detalhes': []},
        'hipotetico_40h': {'completas': 0, 'incompletas': 0, 'detalhes': []}
    }
    
    equipes_afetadas = []  # Equipes que mudariam de status
    
    for _, equipe in df_ativas.iterrows():
        seq = equipe['SEQ_EQUIPE']
        prof_eq = df_prof_validos[df_prof_validos['SEQ_EQUIPE'] == seq]
        
        # Cenário LEGAL (60h)
        completa_60, chs_enf, motivos_60 = verificar_completude_emad_i(prof_eq, 60)
        
        # Cenário HIPOTÉTICO (40h)
        completa_40, _, motivos_40 = verificar_completude_emad_i(prof_eq, 40)
        
        if completa_60:
            resultados['legal_60h']['completas'] += 1
        else:
            resultados['legal_60h']['incompletas'] += 1
            
        if completa_40:
            resultados['hipotetico_40h']['completas'] += 1
        else:
            resultados['hipotetico_40h']['incompletas'] += 1
        
        # Identifica equipes que mudariam de status
        if completa_40 and not completa_60:
            equipes_afetadas.append({
                'SEQ_EQUIPE': seq,
                'CHS_ENFERMEIRO': chs_enf,
                'MOTIVO_60H': '; '.join(motivos_60)
            })
    
    total = len(df_ativas)
    
    # Resultados
    print(f"\n📊 CENÁRIO LEGAL (Portaria 3.005/2024): Enfermeiro ≥ 60h")
    print(f"   ✅ Completas: {resultados['legal_60h']['completas']} ({resultados['legal_60h']['completas']/total*100:.1f}%)")
    print(f"   ❌ Incompletas: {resultados['legal_60h']['incompletas']} ({resultados['legal_60h']['incompletas']/total*100:.1f}%)")
    
    print(f"\n📊 CENÁRIO HIPOTÉTICO: Enfermeiro ≥ 40h")
    print(f"   ✅ Completas: {resultados['hipotetico_40h']['completas']} ({resultados['hipotetico_40h']['completas']/total*100:.1f}%)")
    print(f"   ❌ Incompletas: {resultados['hipotetico_40h']['incompletas']} ({resultados['hipotetico_40h']['incompletas']/total*100:.1f}%)")
    
    # Impacto
    print("\n" + "="*70)
    print("ANÁLISE DE IMPACTO")
    print("="*70)
    
    diferenca = resultados['hipotetico_40h']['completas'] - resultados['legal_60h']['completas']
    print(f"\n🔍 IMPACTO DO REQUISITO DE 60h vs 40h:")
    print(f"   Equipes que seriam COMPLETAS com 40h mas são INCOMPLETAS com 60h: {len(equipes_afetadas)}")
    print(f"   Aumento na taxa de completude: +{diferenca/total*100:.1f} pontos percentuais")
    
    if equipes_afetadas:
        print(f"\n📋 DETALHES DAS {len(equipes_afetadas)} EQUIPES AFETADAS:")
        print("   (Seriam completas se o requisito fosse 40h)")
        print()
        
        # Distribuição de CHS de enfermeiro nas equipes afetadas
        chs_values = [eq['CHS_ENFERMEIRO'] for eq in equipes_afetadas]
        print(f"   Distribuição de CHS de Enfermeiro:")
        for chs_val in sorted(set(chs_values)):
            count = chs_values.count(chs_val)
            print(f"      {chs_val:.0f}h: {count} equipe(s)")
    
    # Conclusão
    print("\n" + "="*70)
    print("CONCLUSÃO")
    print("="*70)
    print(f"""
O requisito de 60h para enfermeiros (Portaria 3.005/2024) impacta 
diretamente {len(equipes_afetadas)} equipes EMAD I em SP Capital.

Se o requisito fosse 40h (compatível com 1 enfermeiro 40h/semana):
   - Completude subiria de {resultados['legal_60h']['completas']/total*100:.1f}% para {resultados['hipotetico_40h']['completas']/total*100:.1f}%
   - {len(equipes_afetadas)} equipes deixariam de ser classificadas como "incompletas"

INTERPRETAÇÃO:
   A maioria das equipes incompletas tem exatamente 40h de enfermeiro,
   indicando que operam com 1 enfermeiro em tempo integral.
   
   A Portaria exige 60h, o que requer aproximadamente 1.5 FTE
   (Full-Time Equivalent), ou seja, 1 enfermeiro 40h + 1 enfermeiro 20h.
   
   Esta é uma exigência normativa para garantir cobertura adequada,
   mas na prática muitas equipes não conseguem atender.
""")


if __name__ == "__main__":
    main()
