#!/usr/bin/env python3
"""
===============================================================================
ANÁLISE DE CONFORMIDADE LEGAL - ESTADO DE SÃO PAULO INTEIRO (V2)
===============================================================================

Verifica quais equipes EMAD/EMAP estão em conformidade com a 
Portaria GM/MS nº 3.005/2024 para TODO o estado de SP.

Versão otimizada para processar arquivo CHS completo.
===============================================================================
"""

import pandas as pd
import os
import warnings
from collections import Counter
warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

BASE_DIR = '/home/fersuaiden/Área de trabalho/Faculdade/IC'
CNES_DIR = os.path.join(BASE_DIR, 'CNES_DATA')
OUTPUT_DIR = os.path.join(BASE_DIR, 'Outputs&Codigo/PARTE4')
CHS_MINIMA_INDIVIDUAL = 20  # Art. 547, §1º

# CÓDIGOS CORRETOS DO CNES (tbTipoEquipe202508.csv):
# 22 = EMAD I - EQUIPE MULTIPROFISSIONAL DE ATENCAO DOMICILIAR I
# 46 = EMAD II - EQUIPE MULTIPROFISSIONAL DE ATENCAO DOMICILIAR II
# 23 = EMAP - EQUIPE MULTIDISCIPLINAR DE APOIO
# 77 = EMAP-R - EQ. MULTIPROFISSIONAIS DE APOIO PARA REABILITACAO
TIPOS_EQUIPE_AD = {
    22: 'EMAD I',
    46: 'EMAD II', 
    23: 'EMAP',
    77: 'EMAP-R',
}

# Regras por tipo de equipe (Portaria 3.005/2024)
# EMAD I (Art. 547, I): 1 médico (40h), 1 enfermeiro (60h), 3 téc/aux enfermagem (120h), 
#                       1 fisioterapeuta ou assistente social (30h)
# EMAD II (Art. 547, II): 1 médico (20h), 1 enfermeiro (30h), 3 téc/aux enfermagem (120h),
#                         1 fisioterapeuta ou assistente social (30h)
REGRAS_EMAD = {
    22: {'MEDICO': 40, 'ENFERMEIRO': 60, 'TECNICO_ENFERMAGEM': 120, 'FISIO_OU_AS': 30},
    46: {'MEDICO': 20, 'ENFERMEIRO': 30, 'TECNICO_ENFERMAGEM': 120, 'FISIO_OU_AS': 30},
}

# EMAP (Art. 548): mínimo 3 profissionais NS diferentes, CHS total 90h
# EMAP-R (Art. 548): mínimo 3 profissionais NS diferentes, CHS total 60h
REGRAS_EMAP = {
    23: {'MIN_PROF_NS': 3, 'CHS_TOTAL': 90},
    77: {'MIN_PROF_NS': 3, 'CHS_TOTAL': 60},
}

# Profissionais NS elegíveis para EMAP (Art. 548, I)
PROF_NS_EMAP = ['FISIOTERAPEUTA', 'ASSISTENTE_SOCIAL', 'FONOAUDIOLOGO', 
                'NUTRICIONISTA', 'PSICOLOGO', 'TERAPEUTA_OCUPACIONAL',
                'ODONTOLOGO', 'FARMACEUTICO']
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


def main():
    print("=" * 70)
    print("ANÁLISE DE CONFORMIDADE LEGAL - ESTADO DE SÃO PAULO")
    print("Portaria GM/MS nº 3.005/2024")
    print("=" * 70)
    
    # 1. Carregar equipes AD do estado de SP
    print("\n[1] Carregando equipes AD do estado de SP...")
    
    df_equipes = pd.read_csv(
        os.path.join(CNES_DIR, "tbEquipe202508.csv"),
        sep=';', encoding='latin-1', low_memory=False
    )
    
    # Filtrar por estado de SP usando código do município (começa com 35)
    df_equipes['CO_MUN_STR'] = df_equipes['CO_MUNICIPIO'].astype(str)
    df_equipes_sp = df_equipes[df_equipes['CO_MUN_STR'].str.startswith('35')].copy()
    
    # Filtrar por tipo de equipe AD
    df_equipes_ad = df_equipes_sp[df_equipes_sp['TP_EQUIPE'].isin(TIPOS_EQUIPE_AD.keys())].copy()
    
    # Filtrar apenas ativas
    df_equipes_ad['DT_DESATIVACAO'] = pd.to_datetime(
        df_equipes_ad['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce'
    )
    df_ativas = df_equipes_ad[df_equipes_ad['DT_DESATIVACAO'].isna()].copy()
    
    print(f"    Equipes ativas no estado: {len(df_ativas)}")
    for tp, nome in TIPOS_EQUIPE_AD.items():
        qtd = len(df_ativas[df_ativas['TP_EQUIPE'] == tp])
        if qtd > 0:
            print(f"      - {nome}: {qtd}")
    
    # Obter CO_UNIDADE das equipes para filtrar profissionais
    cnes_sp = set(df_ativas['CO_UNIDADE'].unique())
    seq_equipes = set(df_ativas['SEQ_EQUIPE'].unique())
    
    # 2. Carregar profissionais das equipes
    print("\n[2] Carregando profissionais das equipes...")
    chunks = []
    for chunk in pd.read_csv(
        os.path.join(CNES_DIR, "rlEstabEquipeProf202508.csv"),
        sep=';', encoding='latin-1', chunksize=200000, low_memory=False
    ):
        # Filtrar por equipes AD de SP
        filtered = chunk[chunk['SEQ_EQUIPE'].isin(seq_equipes)]
        if len(filtered) > 0:
            chunks.append(filtered)
    
    if not chunks:
        print("    ERRO: Nenhum profissional encontrado!")
        return
        
    df_prof = pd.concat(chunks, ignore_index=True)
    df_prof['DT_DESLIGAMENTO'] = pd.to_datetime(
        df_prof['DT_DESLIGAMENTO'], format='%d/%m/%Y', errors='coerce'
    )
    # Apenas profissionais ativos
    df_prof = df_prof[df_prof['DT_DESLIGAMENTO'].isna()].copy()
    print(f"    Vínculos ativos em equipes AD: {len(df_prof)}")
    
    # Conjunto de profissionais para filtrar CHS
    prof_ids = set(df_prof['CO_PROFISSIONAL_SUS'].unique())
    print(f"    Profissionais únicos: {len(prof_ids)}")
    
    # 3. Carregar CHS dos profissionais
    print("\n[3] Carregando Carga Horária SUS dos profissionais...")
    chunks_chs = []
    for chunk in pd.read_csv(
        os.path.join(CNES_DIR, "tbCargaHorariaSus202508.csv"),
        sep=';', encoding='latin-1', chunksize=500000, low_memory=False
    ):
        filtered = chunk[chunk['CO_PROFISSIONAL_SUS'].isin(prof_ids)]
        if len(filtered) > 0:
            chunks_chs.append(filtered)
    
    if not chunks_chs:
        print("    AVISO: Nenhuma CHS encontrada para profissionais!")
        df_chs = pd.DataFrame(columns=['CO_PROFISSIONAL_SUS', 'CHS_TOTAL'])
    else:
        df_chs = pd.concat(chunks_chs, ignore_index=True)
        
        # Calcular CHS total por profissional
        for col in ['QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']:
            if col in df_chs.columns:
                df_chs[col] = pd.to_numeric(df_chs[col], errors='coerce').fillna(0)
        
        df_chs['CHS_TOTAL'] = (
            df_chs.get('QT_CARGA_HORARIA_AMBULATORIAL', 0) + 
            df_chs.get('QT_CARGA_HORARIA_OUTROS', 0) + 
            df_chs.get('QT_CARGA_HOR_HOSP_SUS', 0)
        )
        
        # Agregar por profissional (pode ter múltiplos vínculos)
        df_chs = df_chs.groupby('CO_PROFISSIONAL_SUS')['CHS_TOTAL'].sum().reset_index()
        
    print(f"    Registros de CHS encontrados: {len(df_chs)}")
    
    # 4. Enriquecer profissionais com CHS e categoria
    print("\n[4] Processando dados...")
    df_prof = df_prof.merge(df_chs, on='CO_PROFISSIONAL_SUS', how='left')
    df_prof['CHS_TOTAL'] = df_prof['CHS_TOTAL'].fillna(0)
    df_prof['CATEGORIA'] = df_prof['CO_CBO'].apply(categorizar_cbo)
    
    # Estatísticas de CHS
    chs_stats = df_prof['CHS_TOTAL'].describe()
    print(f"    CHS média: {chs_stats['mean']:.1f}h, max: {chs_stats['max']:.0f}h")
    print(f"    Profissionais com CHS >= 20h: {len(df_prof[df_prof['CHS_TOTAL'] >= 20])}")
    
    # NÃO filtrar por CHS mínima individual aqui - vamos verificar por equipe
    # A regra de 20h mínimo é para contabilizar o profissional, mas vamos ver
    # a composição real das equipes
    
    # 5. Verificar conformidade de cada equipe
    print("\n[5] Verificando conformidade legal de cada equipe...")
    
    resultados = []
    problemas_por_tipo = {tp: Counter() for tp in TIPOS_EQUIPE_AD.keys()}
    
    for _, equipe in df_ativas.iterrows():
        seq = equipe['SEQ_EQUIPE']
        tipo = equipe['TP_EQUIPE']
        nome_tipo = TIPOS_EQUIPE_AD[tipo]
        
        # Profissionais desta equipe com CHS >= 20h (regra do Art. 547, §1º)
        prof_equipe = df_prof[(df_prof['SEQ_EQUIPE'] == seq) & (df_prof['CHS_TOTAL'] >= CHS_MINIMA_INDIVIDUAL)]
        
        conforme = True
        problemas = []
        
        if tipo in [22, 46]:  # EMAD I ou II
            regras = REGRAS_EMAD[tipo]
            for cat, minimo in regras.items():
                if cat == 'FISIO_OU_AS':
                    chs = prof_equipe[prof_equipe['CATEGORIA'].isin(['FISIOTERAPEUTA', 'ASSISTENTE_SOCIAL'])]['CHS_TOTAL'].sum()
                else:
                    chs = prof_equipe[prof_equipe['CATEGORIA'] == cat]['CHS_TOTAL'].sum()
                
                if chs < minimo:
                    conforme = False
                    problemas.append(cat)
                    problemas_por_tipo[tipo][cat] += 1
        else:  # EMAP ou EMAP-R
            regras = REGRAS_EMAP[tipo]
            lista_ns = PROF_NS_EMAP_R if tipo == 77 else PROF_NS_EMAP
            
            prof_ns = prof_equipe[prof_equipe['CATEGORIA'].isin(lista_ns)]
            n_prof_cat = prof_ns['CATEGORIA'].nunique()  # Categorias diferentes, não profissionais
            chs_total = prof_ns['CHS_TOTAL'].sum()
            
            if n_prof_cat < regras['MIN_PROF_NS']:
                conforme = False
                problemas.append('N_PROF_NS')
                problemas_por_tipo[tipo]['N_PROF_NS'] += 1
            if chs_total < regras['CHS_TOTAL']:
                conforme = False
                problemas.append('CHS_TOTAL')
                problemas_por_tipo[tipo]['CHS_TOTAL'] += 1
        
        resultados.append({
            'SEQ_EQUIPE': seq,
            'CO_MUNICIPIO': equipe['CO_MUNICIPIO'],
            'TIPO': nome_tipo,
            'CONFORME': conforme,
            'PROBLEMAS': ','.join(problemas) if problemas else ''
        })
    
    df_resultados = pd.DataFrame(resultados)
    
    # 6. Imprimir resultados
    print("\n" + "=" * 70)
    print("RESULTADOS POR TIPO DE EQUIPE - ESTADO DE SÃO PAULO")
    print("=" * 70)
    
    for tp, nome in TIPOS_EQUIPE_AD.items():
        df_tipo = df_resultados[df_resultados['TIPO'] == nome]
        if len(df_tipo) == 0:
            continue
            
        total = len(df_tipo)
        conformes = df_tipo['CONFORME'].sum()
        nao_conformes = total - conformes
        
        print(f"\n{nome}:")
        print(f"    Total: {total}")
        print(f"    Em conformidade: {conformes} ({100*conformes/total:.1f}%)")
        print(f"    Fora de conformidade: {nao_conformes} ({100*nao_conformes/total:.1f}%)")
        
        if problemas_por_tipo[tp]:
            print(f"    Problemas mais frequentes:")
            for prob, count in problemas_por_tipo[tp].most_common(5):
                print(f"        - {prob}: {count} equipes")
    
    # 7. Resumo geral
    print("\n" + "=" * 70)
    print("RESUMO GERAL - ESTADO DE SÃO PAULO")
    print("=" * 70)
    
    total_geral = len(df_resultados)
    conformes_geral = df_resultados['CONFORME'].sum()
    
    print(f"\nTotal de equipes ativas: {total_geral}")
    print(f"Em conformidade com Portaria 3.005/2024: {conformes_geral} ({100*conformes_geral/total_geral:.1f}%)")
    print(f"Fora de conformidade: {total_geral - conformes_geral} ({100*(total_geral-conformes_geral)/total_geral:.1f}%)")
    
    # 8. Análise por município (top 10 com mais equipes)
    print("\n" + "=" * 70)
    print("TOP 10 MUNICÍPIOS COM MAIS EQUIPES AD")
    print("=" * 70)
    
    mun_stats = df_resultados.groupby('CO_MUNICIPIO').agg({
        'CONFORME': ['count', 'sum']
    })
    mun_stats.columns = ['TOTAL', 'CONFORMES']
    mun_stats['TAXA_CONFORM'] = 100 * mun_stats['CONFORMES'] / mun_stats['TOTAL']
    mun_stats = mun_stats.sort_values('TOTAL', ascending=False).head(10)
    
    print(f"\n{'MUNICÍPIO':<12} {'TOTAL':<8} {'CONFORMES':<10} {'TAXA %':<8}")
    print("-" * 40)
    for mun, row in mun_stats.iterrows():
        print(f"{mun:<12} {int(row['TOTAL']):<8} {int(row['CONFORMES']):<10} {row['TAXA_CONFORM']:.1f}%")
    
    # 9. Salvar resultados
    output_file = os.path.join(OUTPUT_DIR, 'conformidade_legal_sp_estado.csv')
    df_resultados.to_csv(output_file, sep=';', index=False)
    print(f"\nResultado detalhado salvo em: {output_file}")
    
    print("\n" + "-" * 70)
    print("REFERÊNCIA LEGAL:")
    print("  Portaria GM/MS nº 3.005, de 2 de janeiro de 2024")
    print("  Consolida as normas sobre Atenção Domiciliar")
    print("-" * 70)


if __name__ == '__main__':
    main()
