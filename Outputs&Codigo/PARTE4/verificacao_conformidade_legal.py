#!/usr/bin/env python3
"""
===============================================================================
PARTE 4 - Verificação de Conformidade Legal das Equipes AD
===============================================================================

Verifica quais equipes EMAD/EMAP estão em conformidade com a 
Portaria GM/MS nº 3.005/2024 (publicada em 05/01/2024).

REQUISITOS LEGAIS (Art. 547):
────────────────────────────────────────────────────────────────────
| Tipo     | Médico | Enfermeiro | Fisio/AS | Téc.Enf | CHS Individual |
|----------|--------|------------|----------|---------|----------------|
| EMAD I   | ≥40h   | ≥60h       | ≥30h     | ≥120h   | ≥20h cada      |
| EMAD II  | ≥20h   | ≥30h       | ≥30h     | ≥120h   | ≥20h cada      |
| EMAP     | 3 prof. NS | -      | -        | -       | CHS total ≥90h |
| EMAP-R   | 3 prof. NS | -      | -        | -       | CHS total ≥60h |
────────────────────────────────────────────────────────────────────

Autor: IC FAPESP - Programa Melhor em Casa
===============================================================================
"""

import pandas as pd
import os

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CNES_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "CNES_DATA")
SP_CAPITAL = 355030
CHS_MINIMA_INDIVIDUAL = 20  # Art. 547, §1º

TIPOS_EQUIPE_AD = {
    22: 'EMAD I',
    46: 'EMAD II', 
    23: 'EMAP',
    77: 'EMAP-R',
}

# Regras por tipo de equipe (Portaria 3.005/2024)
REGRAS = {
    22: {'MEDICO': 40, 'ENFERMEIRO': 60, 'TECNICO_ENFERMAGEM': 120, 'FISIO_OU_AS': 30},
    46: {'MEDICO': 20, 'ENFERMEIRO': 30, 'TECNICO_ENFERMAGEM': 120, 'FISIO_OU_AS': 30},
    23: {'MIN_PROF_NS': 3, 'CHS_TOTAL': 90},
    77: {'MIN_PROF_NS': 3, 'CHS_TOTAL': 60},
}

# Profissionais NS elegíveis para EMAP (Médico e Enfermeiro NÃO contam)
PROF_NS_EMAP = ['FISIOTERAPEUTA', 'ASSISTENTE_SOCIAL', 'FONOAUDIOLOGO', 
                'NUTRICIONISTA', 'PSICOLOGO', 'TERAPEUTA_OCUPACIONAL',
                'ODONTOLOGO', 'FARMACEUTICO']

# EMAP-R: Enfermeiro conta (Art. 548-A)
PROF_NS_EMAP_R = PROF_NS_EMAP + ['ENFERMEIRO']


def categorizar_cbo(cbo):
    """Categoriza CBO em categoria profissional."""
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


def verificar_emad(df_prof, tipo):
    """Verifica completude de EMAD I ou II."""
    regra = REGRAS[tipo]
    detalhes = {}
    conforme = True
    
    for categoria, minimo in regra.items():
        if categoria == 'FISIO_OU_AS':
            chs = df_prof[df_prof['CATEGORIA'].isin(['FISIOTERAPEUTA', 'ASSISTENTE_SOCIAL'])]['CHS_REAL'].sum()
        else:
            chs = df_prof[df_prof['CATEGORIA'] == categoria]['CHS_REAL'].sum()
        
        atende = chs >= minimo
        detalhes[categoria] = {'CHS': chs, 'Mínimo': minimo, 'OK': atende}
        if not atende:
            conforme = False
    
    return conforme, detalhes


def verificar_emap(df_prof, tipo):
    """Verifica completude de EMAP ou EMAP-R."""
    regra = REGRAS[tipo]
    lista_ns = PROF_NS_EMAP_R if tipo == 77 else PROF_NS_EMAP
    
    prof_ns = df_prof[df_prof['CATEGORIA'].isin(lista_ns)]
    n_prof = prof_ns['CO_PROFISSIONAL_SUS'].nunique()
    chs_total = prof_ns['CHS_REAL'].sum()
    
    ok_prof = n_prof >= regra['MIN_PROF_NS']
    ok_chs = chs_total >= regra['CHS_TOTAL']
    
    detalhes = {
        'N_PROF_NS': {'valor': n_prof, 'minimo': regra['MIN_PROF_NS'], 'OK': ok_prof},
        'CHS_TOTAL': {'valor': chs_total, 'minimo': regra['CHS_TOTAL'], 'OK': ok_chs}
    }
    
    return ok_prof and ok_chs, detalhes


def main():
    print("=" * 70)
    print("VERIFICAÇÃO DE CONFORMIDADE LEGAL DAS EQUIPES AD")
    print("Portaria GM/MS nº 3.005/2024")
    print("=" * 70)
    
    # 1. Carregar equipes
    print("\n[1] Carregando equipes AD de SP Capital...")
    df_equipes = pd.read_csv(
        os.path.join(CNES_DIR, "tbEquipe202508.csv"),
        sep=';', encoding='latin-1', low_memory=False
    )
    df_equipes = df_equipes[
        (df_equipes['TP_EQUIPE'].isin(TIPOS_EQUIPE_AD.keys())) &
        (df_equipes['CO_MUNICIPIO'] == SP_CAPITAL)
    ].copy()
    df_equipes['DT_DESATIVACAO'] = pd.to_datetime(df_equipes['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce')
    df_ativas = df_equipes[df_equipes['DT_DESATIVACAO'].isna()]
    print(f"    Equipes ativas: {len(df_ativas)}")
    
    # 2. Carregar profissionais
    print("\n[2] Carregando profissionais das equipes...")
    chunks = []
    for chunk in pd.read_csv(
        os.path.join(CNES_DIR, "rlEstabEquipeProf202508.csv"),
        sep=';', encoding='latin-1', chunksize=100000, low_memory=False
    ):
        filtered = chunk[chunk['CO_MUNICIPIO'] == SP_CAPITAL]
        if len(filtered) > 0:
            chunks.append(filtered)
    df_prof = pd.concat(chunks, ignore_index=True)
    df_prof['DT_DESLIGAMENTO'] = pd.to_datetime(df_prof['DT_DESLIGAMENTO'], format='%d/%m/%Y', errors='coerce')
    
    # Filtrar para equipes AD
    seq_equipes = set(df_ativas['SEQ_EQUIPE'])
    df_prof_ad = df_prof[df_prof['SEQ_EQUIPE'].isin(seq_equipes)].copy()
    df_prof_ad = df_prof_ad[df_prof_ad['DT_DESLIGAMENTO'].isna()]  # Apenas ativos
    print(f"    Vínculos ativos em equipes AD: {len(df_prof_ad)}")
    
    # 3. Carregar CHS
    print("\n[3] Carregando Carga Horária SUS...")
    df_chs = pd.read_csv(
        os.path.join(CNES_DIR, "chs_ad_sp.csv"),
        sep=';', encoding='latin-1', low_memory=False
    )
    for col in ['QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']:
        if col in df_chs.columns:
            df_chs[col] = pd.to_numeric(df_chs[col], errors='coerce').fillna(0)
    df_chs['CHS_REAL'] = (df_chs['QT_CARGA_HORARIA_AMBULATORIAL'] + 
                          df_chs['QT_CARGA_HORARIA_OUTROS'] + 
                          df_chs['QT_CARGA_HOR_HOSP_SUS'])
    df_chs_agg = df_chs.groupby('CO_PROFISSIONAL_SUS')['CHS_REAL'].sum().reset_index()
    
    # 4. Enriquecer profissionais
    print("\n[4] Processando dados...")
    df_prof_ad = df_prof_ad.merge(df_chs_agg, on='CO_PROFISSIONAL_SUS', how='left')
    df_prof_ad['CHS_REAL'] = df_prof_ad['CHS_REAL'].fillna(0)
    df_prof_ad['CATEGORIA'] = df_prof_ad['CO_CBO'].apply(categorizar_cbo)
    
    # Filtrar por CHS mínima individual (Art. 547, §1º)
    df_prof_ad = df_prof_ad[df_prof_ad['CHS_REAL'] >= CHS_MINIMA_INDIVIDUAL]
    print(f"    Profissionais válidos (CHS >= 20h): {len(df_prof_ad)}")
    
    # 5. Verificar cada equipe
    print("\n[5] Verificando conformidade legal de cada equipe...")
    print("-" * 70)
    
    resultados = []
    
    for _, equipe in df_ativas.iterrows():
        seq = equipe['SEQ_EQUIPE']
        tipo = equipe['TP_EQUIPE']
        nome_tipo = TIPOS_EQUIPE_AD[tipo]
        
        prof_equipe = df_prof_ad[df_prof_ad['SEQ_EQUIPE'] == seq]
        
        if tipo in [22, 46]:  # EMAD I ou II
            conforme, detalhes = verificar_emad(prof_equipe, tipo)
        else:  # EMAP ou EMAP-R
            conforme, detalhes = verificar_emap(prof_equipe, tipo)
        
        resultados.append({
            'SEQ_EQUIPE': seq,
            'TIPO': nome_tipo,
            'CONFORME': conforme,
            'N_PROF': len(prof_equipe),
            'DETALHES': detalhes
        })
    
    df_resultado = pd.DataFrame(resultados)
    
    # 6. Resultados por tipo
    print("\n" + "=" * 70)
    print("RESULTADOS POR TIPO DE EQUIPE")
    print("=" * 70)
    
    for tipo_code, tipo_nome in TIPOS_EQUIPE_AD.items():
        subset = df_resultado[df_resultado['TIPO'] == tipo_nome]
        if len(subset) == 0:
            continue
        
        conformes = subset['CONFORME'].sum()
        total = len(subset)
        pct = conformes / total * 100 if total > 0 else 0
        
        print(f"\n{tipo_nome}:")
        print(f"    Total: {total}")
        print(f"    ✅ Em conformidade: {conformes} ({pct:.1f}%)")
        print(f"    ❌ Fora de conformidade: {total - conformes} ({100-pct:.1f}%)")
        
        # Detalhar problemas mais comuns
        if total - conformes > 0:
            problemas = []
            for _, row in subset[~subset['CONFORME']].iterrows():
                for cat, info in row['DETALHES'].items():
                    if isinstance(info, dict) and not info.get('OK', True):
                        problemas.append(cat)
            
            if problemas:
                from collections import Counter
                contagem = Counter(problemas)
                print(f"    Problemas mais frequentes:")
                for prob, count in contagem.most_common(3):
                    print(f"        - {prob}: {count} equipes")
    
    # 7. Resumo geral
    print("\n" + "=" * 70)
    print("RESUMO GERAL")
    print("=" * 70)
    
    total_geral = len(df_resultado)
    conformes_geral = df_resultado['CONFORME'].sum()
    pct_conformes = conformes_geral / total_geral * 100
    
    print(f"\nTotal de equipes ativas: {total_geral}")
    print(f"✅ Em conformidade com Portaria 3.005/2024: {conformes_geral} ({pct_conformes:.1f}%)")
    print(f"❌ Fora de conformidade: {total_geral - conformes_geral} ({100-pct_conformes:.1f}%)")
    
    print("\n" + "-" * 70)
    print("REFERÊNCIA LEGAL:")
    print("  Portaria GM/MS nº 3.005, de 2 de janeiro de 2024")
    print("  Art. 547 - Composição mínima das EMAD")
    print("  Art. 548 - Composição mínima das EMAP")
    print("  Art. 548-A - Composição mínima das EMAP-R")
    print("-" * 70)
    
    # Salvar CSV
    df_resultado['DETALHES'] = df_resultado['DETALHES'].astype(str)
    df_resultado.to_csv(os.path.join(BASE_DIR, 'conformidade_legal_equipes.csv'), index=False)
    print(f"\nResultado salvo em: conformidade_legal_equipes.csv")


if __name__ == '__main__':
    main()
