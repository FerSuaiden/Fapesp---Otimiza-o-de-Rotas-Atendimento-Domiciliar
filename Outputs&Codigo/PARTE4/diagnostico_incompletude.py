"""
Script de diagnóstico para investigar causas de incompletude das equipes AD.
"""

import pandas as pd
import os

# Configurações
CNES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "CNES_DATA")
SP_CAPITAL = 355030

TIPOS_EQUIPE_AD = {
    22: 'EMAD I',
    46: 'EMAD II', 
    23: 'EMAP',
    77: 'EMAP-R',
    47: 'ECD'
}

CHS_MINIMA_INDIVIDUAL = 20

# Listas de NS
PROFISSIONAIS_NS_EMAP = ['FISIOTERAPEUTA', 'ASSISTENTE_SOCIAL', 'FONOAUDIOLOGO', 
                         'NUTRICIONISTA', 'PSICOLOGO', 'TERAPEUTA_OCUPACIONAL',
                         'ODONTOLOGO', 'FARMACEUTICO']

def categorizar_cbo(cbo):
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
    if cbo_str.startswith('2238'):
        return 'FONOAUDIOLOGO'
    if cbo_str.startswith('2237'):
        return 'NUTRICIONISTA'
    if cbo_str.startswith('2515'):
        return 'PSICOLOGO'
    if cbo_str.startswith('2239'):
        return 'TERAPEUTA_OCUPACIONAL'
    if cbo_str.startswith('2232'):
        return 'ODONTOLOGO'
    if cbo_str.startswith('2234'):
        return 'FARMACEUTICO'
    return 'OUTRO'


def main():
    print("="*70)
    print("DIAGNÓSTICO DE INCOMPLETUDE DE EQUIPES AD")
    print("="*70)
    
    # 1. Carregar equipes
    print("\n[1] Carregando equipes...")
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
    print(f"   Equipes ativas: {len(df_ativas)}")
    
    # 2. Carregar profissionais
    print("\n[2] Carregando profissionais...")
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
    seq_equipes_ad = df_equipes['SEQ_EQUIPE'].unique()
    df_prof_ad = df_prof[df_prof['SEQ_EQUIPE'].isin(seq_equipes_ad)]
    print(f"   Vínculos em equipes AD: {len(df_prof_ad)}")
    
    # 3. Carregar CHS
    print("\n[3] Carregando CHS...")
    profissionais_ad = set(df_prof_ad['CO_PROFISSIONAL_SUS'].unique())
    
    filepath_cache = os.path.join(CNES_DIR, "chs_ad_sp.csv")
    df_chs = pd.read_csv(filepath_cache, sep=';', encoding='latin-1', low_memory=False)
    df_chs = df_chs[df_chs['CO_PROFISSIONAL_SUS'].isin(profissionais_ad)]
    
    for col in ['QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']:
        if col in df_chs.columns:
            df_chs[col] = pd.to_numeric(df_chs[col], errors='coerce').fillna(0)
        else:
            df_chs[col] = 0
    
    df_chs['CHS_REAL'] = (df_chs['QT_CARGA_HORARIA_AMBULATORIAL'] + 
                          df_chs['QT_CARGA_HORARIA_OUTROS'] + 
                          df_chs['QT_CARGA_HOR_HOSP_SUS'])
    
    df_chs_agg = df_chs.groupby('CO_PROFISSIONAL_SUS').agg({'CHS_REAL': 'sum'}).reset_index()
    print(f"   Profissionais com CHS: {len(df_chs_agg)}")
    
    # 4. Enriquecer profissionais
    print("\n[4] Enriquecendo dados...")
    df_prof_chs = df_prof_ad.merge(
        df_chs_agg[['CO_PROFISSIONAL_SUS', 'CHS_REAL']],
        on='CO_PROFISSIONAL_SUS',
        how='left'
    )
    df_prof_chs['CHS_REAL'] = df_prof_chs['CHS_REAL'].fillna(0)
    df_prof_chs['CATEGORIA_CBO'] = df_prof_chs['CO_CBO'].apply(categorizar_cbo)
    df_prof_chs['VALIDO_PORTARIA'] = df_prof_chs['CHS_REAL'] >= CHS_MINIMA_INDIVIDUAL
    
    # Profissionais ativos e válidos
    df_prof_validos = df_prof_chs[
        (df_prof_chs['DT_DESLIGAMENTO'].isna()) &
        (df_prof_chs['VALIDO_PORTARIA'] == True)
    ]
    
    print(f"   Profissionais válidos (ativos + CHS>=20h): {len(df_prof_validos)}")
    
    # 5. DIAGNÓSTICO POR TIPO
    print("\n" + "="*70)
    print("ANÁLISE DETALHADA POR TIPO DE EQUIPE")
    print("="*70)
    
    total_completas = 0
    total_incompletas = 0
    
    for tp_equipe, nome_tipo in TIPOS_EQUIPE_AD.items():
        equipes_tipo = df_ativas[df_ativas['TP_EQUIPE'] == tp_equipe]
        if len(equipes_tipo) == 0:
            continue
        
        print(f"\n{'='*60}")
        print(f"{nome_tipo} ({len(equipes_tipo)} equipes)")
        print('='*60)
        
        completas = 0
        incompletas = 0
        motivos = {}
        exemplos_detalhados = []
        
        for _, equipe in equipes_tipo.iterrows():
            seq = equipe['SEQ_EQUIPE']
            prof_equipe = df_prof_validos[df_prof_validos['SEQ_EQUIPE'] == seq]
            
            # Calcular métricas
            if tp_equipe in [22, 46]:  # EMAD I ou II
                chs_medico = prof_equipe[prof_equipe['CATEGORIA_CBO'] == 'MEDICO']['CHS_REAL'].sum()
                chs_enfermeiro = prof_equipe[prof_equipe['CATEGORIA_CBO'] == 'ENFERMEIRO']['CHS_REAL'].sum()
                chs_tecnico = prof_equipe[prof_equipe['CATEGORIA_CBO'] == 'TECNICO_ENFERMAGEM']['CHS_REAL'].sum()
                chs_fisio = prof_equipe[prof_equipe['CATEGORIA_CBO'] == 'FISIOTERAPEUTA']['CHS_REAL'].sum()
                chs_as = prof_equipe[prof_equipe['CATEGORIA_CBO'] == 'ASSISTENTE_SOCIAL']['CHS_REAL'].sum()
                chs_fisio_as = chs_fisio + chs_as
                
                if tp_equipe == 22:  # EMAD I
                    min_med, min_enf, min_tec = 40, 60, 120
                else:  # EMAD II
                    min_med, min_enf, min_tec = 20, 30, 120
                
                completa = (chs_medico >= min_med and chs_enfermeiro >= min_enf and 
                           chs_tecnico >= min_tec and chs_fisio_as >= 30)
                
                if not completa:
                    incompletas += 1
                    if chs_medico < min_med:
                        motivos['MEDICO'] = motivos.get('MEDICO', 0) + 1
                    if chs_enfermeiro < min_enf:
                        motivos['ENFERMEIRO'] = motivos.get('ENFERMEIRO', 0) + 1
                    if chs_tecnico < min_tec:
                        motivos['TECNICO_ENFERMAGEM'] = motivos.get('TECNICO_ENFERMAGEM', 0) + 1
                    if chs_fisio_as < 30:
                        motivos['FISIO_OU_AS'] = motivos.get('FISIO_OU_AS', 0) + 1
                    
                    if len(exemplos_detalhados) < 3:
                        exemplos_detalhados.append({
                            'SEQ': seq,
                            'MEDICO': f'{chs_medico:.0f}h (min={min_med}h)',
                            'ENFERMEIRO': f'{chs_enfermeiro:.0f}h (min={min_enf}h)',
                            'TEC_ENF': f'{chs_tecnico:.0f}h (min={min_tec}h)',
                            'FISIO_AS': f'{chs_fisio_as:.0f}h (min=30h)',
                            'N_PROF': len(prof_equipe)
                        })
                else:
                    completas += 1
            
            elif tp_equipe == 23:  # EMAP
                prof_ns = prof_equipe[prof_equipe['CATEGORIA_CBO'].isin(PROFISSIONAIS_NS_EMAP)]
                n_prof_ns = prof_ns['CO_PROFISSIONAL_SUS'].nunique()
                chs_total = prof_ns['CHS_REAL'].sum()
                
                completa = (n_prof_ns >= 3 and chs_total >= 90)
                
                if not completa:
                    incompletas += 1
                    if n_prof_ns < 3:
                        motivos['PROF_NS'] = motivos.get('PROF_NS', 0) + 1
                    if chs_total < 90:
                        motivos['CHS_TOTAL'] = motivos.get('CHS_TOTAL', 0) + 1
                    
                    if len(exemplos_detalhados) < 3:
                        categorias = prof_ns.groupby('CATEGORIA_CBO')['CHS_REAL'].sum().to_dict()
                        exemplos_detalhados.append({
                            'SEQ': seq,
                            'N_PROF_NS': n_prof_ns,
                            'CHS_TOTAL': f'{chs_total:.0f}h',
                            'CATEGORIAS': categorias
                        })
                else:
                    completas += 1
            
            elif tp_equipe == 47:  # ECD
                chs_total = prof_equipe['CHS_REAL'].sum()
                if chs_total >= 40:
                    completas += 1
                else:
                    incompletas += 1
                    motivos['CHS_TOTAL'] = motivos.get('CHS_TOTAL', 0) + 1
            
            else:  # EMAP-R e outros
                completas += 1  # Simplificação
        
        total_completas += completas
        total_incompletas += incompletas
        
        pct = completas / len(equipes_tipo) * 100 if len(equipes_tipo) > 0 else 0
        print(f"✅ Completas: {completas} ({pct:.1f}%)")
        print(f"❌ Incompletas: {incompletas} ({100-pct:.1f}%)")
        
        if motivos:
            print(f"\nMotivos de falha:")
            for m, c in sorted(motivos.items(), key=lambda x: -x[1]):
                print(f"   - {m}: {c} equipes")
        
        if exemplos_detalhados:
            print(f"\nExemplos de equipes incompletas:")
            for ex in exemplos_detalhados:
                print(f"   Equipe {ex['SEQ']}:")
                for k, v in ex.items():
                    if k != 'SEQ':
                        print(f"      {k}: {v}")
    
    # 6. INVESTIGAÇÃO ESPECIAL: Filtro de 20h
    print("\n" + "="*70)
    print("INVESTIGAÇÃO: IMPACTO DO FILTRO DE 20h")
    print("="*70)
    
    # Comparar com e sem filtro
    df_prof_ativos = df_prof_chs[df_prof_chs['DT_DESLIGAMENTO'].isna()]
    df_prof_validos = df_prof_ativos[df_prof_ativos['VALIDO_PORTARIA'] == True]
    
    print(f"\nProfissionais ativos total: {len(df_prof_ativos)}")
    print(f"Profissionais válidos (CHS>=20h): {len(df_prof_validos)}")
    print(f"Descartados pelo filtro: {len(df_prof_ativos) - len(df_prof_validos)}")
    
    # Distribuição de CHS dos descartados
    descartados = df_prof_ativos[df_prof_ativos['VALIDO_PORTARIA'] == False]
    if len(descartados) > 0:
        print(f"\nDistribuição de CHS dos descartados:")
        print(f"   CHS média: {descartados['CHS_REAL'].mean():.1f}h")
        print(f"   CHS máxima: {descartados['CHS_REAL'].max():.1f}h")
        print(f"   Categorias: {descartados['CATEGORIA_CBO'].value_counts().to_dict()}")
    
    # 7. RESUMO FINAL
    print("\n" + "="*70)
    print("RESUMO FINAL")
    print("="*70)
    total = total_completas + total_incompletas
    print(f"\nTotal de equipes analisadas: {total}")
    print(f"✅ Completas: {total_completas} ({total_completas/total*100:.1f}%)")
    print(f"❌ Incompletas: {total_incompletas} ({total_incompletas/total*100:.1f}%)")


if __name__ == "__main__":
    main()
