"""
DIAGNÓSTICO RÁPIDO - Análise de Incompletude das Equipes AD
============================================================

Este script documenta as descobertas científicas sobre o subdimensionamento
das equipes EMAD I em São Paulo Capital.

Baseado na verificação da Portaria GM/MS nº 3.005/2024.
"""

import pandas as pd
import os

# Configurações
CNES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "CNES_DATA")
SP_CAPITAL = 355030
CHS_MINIMA_INDIVIDUAL = 20


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


def main():
    print("="*70)
    print("DIAGNÓSTICO RÁPIDO - INCOMPLETUDE DAS EQUIPES AD")
    print("SP Capital - Julho 2025")
    print("="*70)
    
    # 1. Carregar equipes EMAD I ativas
    print("\n[1] Carregando equipes...")
    df_equipes = pd.read_csv(
        os.path.join(CNES_DIR, "tbEquipe202508.csv"),
        sep=';', encoding='latin-1', low_memory=False
    )
    df_equipes = df_equipes[
        (df_equipes['TP_EQUIPE'] == 22) &  # EMAD I
        (df_equipes['CO_MUNICIPIO'] == SP_CAPITAL)
    ].copy()
    df_equipes['DT_DESATIVACAO'] = pd.to_datetime(df_equipes['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce')
    df_ativas = df_equipes[df_equipes['DT_DESATIVACAO'].isna()]
    print(f"   Equipes EMAD I ativas: {len(df_ativas)}")
    
    # 2. Carregar profissionais
    print("\n[2] Carregando profissionais...")
    df_prof = pd.read_csv(
        os.path.join(CNES_DIR, "rlEstabEquipeProf202508.csv"),
        sep=';', encoding='latin-1', low_memory=False,
        usecols=['SEQ_EQUIPE', 'CO_PROFISSIONAL_SUS', 'CO_CBO', 
                 'CO_MUNICIPIO', 'DT_DESLIGAMENTO']
    )
    df_prof = df_prof[df_prof['CO_MUNICIPIO'] == SP_CAPITAL]
    df_prof['DT_DESLIGAMENTO'] = pd.to_datetime(df_prof['DT_DESLIGAMENTO'], format='%d/%m/%Y', errors='coerce')
    
    seq_equipes = set(df_ativas['SEQ_EQUIPE'].unique())
    df_prof = df_prof[df_prof['SEQ_EQUIPE'].isin(seq_equipes)]
    df_prof = df_prof[df_prof['DT_DESLIGAMENTO'].isna()]  # Só ativos
    print(f"   Vínculos ativos: {len(df_prof)}")
    
    # 3. Carregar CHS
    print("\n[3] Carregando CHS...")
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
    print(f"   Profissionais com CHS: {len(df_chs_agg)}")
    
    # 4. Enriquecer
    print("\n[4] Analisando completude...")
    df_prof_chs = df_prof.merge(df_chs_agg, on='CO_PROFISSIONAL_SUS', how='left')
    df_prof_chs['CHS_REAL'] = df_prof_chs['CHS_REAL'].fillna(0)
    df_prof_chs['CATEGORIA_CBO'] = df_prof_chs['CO_CBO'].apply(categorizar_cbo)
    
    # Aplicar filtro de 20h
    df_prof_validos = df_prof_chs[df_prof_chs['CHS_REAL'] >= CHS_MINIMA_INDIVIDUAL]
    
    # 5. Verificar completude de cada equipe EMAD I
    # Regras: Médico ≥40h, Enfermeiro ≥60h, Téc.Enf ≥120h, Fisio/AS ≥30h
    
    print("\n" + "="*70)
    print("ANÁLISE DE COMPLETUDE - EMAD I")
    print("="*70)
    
    resultados = []
    
    for _, equipe in df_ativas.iterrows():
        seq = equipe['SEQ_EQUIPE']
        prof_eq = df_prof_validos[df_prof_validos['SEQ_EQUIPE'] == seq]
        
        chs_medico = prof_eq[prof_eq['CATEGORIA_CBO'] == 'MEDICO']['CHS_REAL'].sum()
        chs_enfermeiro = prof_eq[prof_eq['CATEGORIA_CBO'] == 'ENFERMEIRO']['CHS_REAL'].sum()
        chs_tecnico = prof_eq[prof_eq['CATEGORIA_CBO'] == 'TECNICO_ENFERMAGEM']['CHS_REAL'].sum()
        chs_fisio = prof_eq[prof_eq['CATEGORIA_CBO'] == 'FISIOTERAPEUTA']['CHS_REAL'].sum()
        chs_as = prof_eq[prof_eq['CATEGORIA_CBO'] == 'ASSISTENTE_SOCIAL']['CHS_REAL'].sum()
        chs_fisio_as = chs_fisio + chs_as
        
        completa = (chs_medico >= 40 and chs_enfermeiro >= 60 and 
                   chs_tecnico >= 120 and chs_fisio_as >= 30)
        
        motivos = []
        if chs_medico < 40:
            motivos.append(f"MED:{chs_medico:.0f}h<40h")
        if chs_enfermeiro < 60:
            motivos.append(f"ENF:{chs_enfermeiro:.0f}h<60h")
        if chs_tecnico < 120:
            motivos.append(f"TEC:{chs_tecnico:.0f}h<120h")
        if chs_fisio_as < 30:
            motivos.append(f"FISIO/AS:{chs_fisio_as:.0f}h<30h")
        
        resultados.append({
            'SEQ': seq,
            'COMPLETA': completa,
            'CHS_MED': chs_medico,
            'CHS_ENF': chs_enfermeiro,
            'CHS_TEC': chs_tecnico,
            'CHS_FISIO_AS': chs_fisio_as,
            'MOTIVOS': '; '.join(motivos) if motivos else ''
        })
    
    df_result = pd.DataFrame(resultados)
    
    # Estatísticas
    n_completas = df_result['COMPLETA'].sum()
    n_incompletas = len(df_result) - n_completas
    
    print(f"\n📊 RESULTADOS EMAD I:")
    print(f"   Total de equipes: {len(df_result)}")
    print(f"   ✅ Completas: {n_completas} ({n_completas/len(df_result)*100:.1f}%)")
    print(f"   ❌ Incompletas: {n_incompletas} ({n_incompletas/len(df_result)*100:.1f}%)")
    
    # Análise dos motivos de incompletude
    df_incomp = df_result[~df_result['COMPLETA']]
    
    print(f"\n📋 ANÁLISE DOS MOTIVOS DE INCOMPLETUDE:")
    motivos_count = {'MEDICO': 0, 'ENFERMEIRO': 0, 'TECNICO_ENFERMAGEM': 0, 'FISIO_OU_AS': 0}
    
    for _, row in df_incomp.iterrows():
        if row['CHS_MED'] < 40:
            motivos_count['MEDICO'] += 1
        if row['CHS_ENF'] < 60:
            motivos_count['ENFERMEIRO'] += 1
        if row['CHS_TEC'] < 120:
            motivos_count['TECNICO_ENFERMAGEM'] += 1
        if row['CHS_FISIO_AS'] < 30:
            motivos_count['FISIO_OU_AS'] += 1
    
    for motivo, count in sorted(motivos_count.items(), key=lambda x: -x[1]):
        if count > 0:
            pct = count / n_incompletas * 100 if n_incompletas > 0 else 0
            print(f"   {motivo}: {count} equipes ({pct:.1f}% das incompletas)")
    
    # Análise detalhada de ENFERMEIRO (principal motivo)
    print(f"\n📈 ANÁLISE DETALHADA - ENFERMEIRO:")
    print(f"   Distribuição de CHS de Enfermeiro nas equipes:")
    print(f"   - Média: {df_result['CHS_ENF'].mean():.1f}h")
    print(f"   - Mediana: {df_result['CHS_ENF'].median():.1f}h")
    print(f"   - Mínimo: {df_result['CHS_ENF'].min():.1f}h")
    print(f"   - Máximo: {df_result['CHS_ENF'].max():.1f}h")
    
    # Distribuição de valores
    valores_enf = df_result['CHS_ENF'].value_counts().sort_index()
    print(f"\n   Frequência de CHS por valor:")
    for valor, freq in valores_enf.items():
        status = "✅" if valor >= 60 else "❌"
        print(f"   {status} {valor:.0f}h: {freq} equipes")
    
    # CONCLUSÃO CIENTÍFICA
    print("\n" + "="*70)
    print("CONCLUSÃO CIENTÍFICA")
    print("="*70)
    print(f"""
A análise revela que {n_incompletas} de {len(df_result)} equipes EMAD I ({n_incompletas/len(df_result)*100:.1f}%)
em São Paulo Capital NÃO atendem aos requisitos mínimos da Portaria GM/MS nº 3.005/2024.

CAUSA PRINCIPAL: Subdimensionamento de Enfermeiros
- A Portaria exige soma de CHS de enfermeiros ≥ 60h
- {motivos_count['ENFERMEIRO']} equipes ({motivos_count['ENFERMEIRO']/n_incompletas*100 if n_incompletas > 0 else 0:.1f}% das incompletas) falham neste critério
- Padrão observado: equipes têm 40h (1 enfermeiro 40h) quando precisariam ter 60h

IMPLICAÇÃO PARA O PROJETO FAPESP:
- A "frota efetiva" de equipes é MENOR que a nominal
- Apenas {n_completas} equipes ({n_completas/len(df_result)*100:.1f}%) podem ser consideradas 100% operacionais
- Isso REFORÇA a necessidade crítica de otimização de rotas

REFERÊNCIA LEGISLATIVA:
Portaria GM/MS nº 3.005/2024, Art. 547, I, b:
"profissional(is) enfermeiro(s): 60 (sessenta) horas"
""")
    
    # Salvar resultados
    output_path = os.path.join(os.path.dirname(__file__), "resultado_completude_emad_i.csv")
    df_result.to_csv(output_path, index=False, sep=';')
    print(f"\n📁 Resultados salvos em: resultado_completude_emad_i.csv")


if __name__ == "__main__":
    main()
