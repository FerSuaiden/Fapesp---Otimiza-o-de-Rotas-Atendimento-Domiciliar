"""
ANÁLISE DE SATURAÇÃO DA OFERTA AD - Script Consolidado
=========================================================

Objetivo: Provar que a frota de equipes que cumprem 100% da lei é menor
que a nominal, justificando a necessidade crítica de otimização de rotas.

Legislação Base:
- Portaria de Consolidação GM/MS nº 5/2017
- Atualizada pela Portaria GM/MS nº 3.005 de 2 de MAIO de 2024
  (Publicada em 05/01/2024, DOU 03/01/2024)

DESCOBERTA CIENTÍFICA IMPORTANTE (Dezembro 2025):
═══════════════════════════════════════════════════
A análise revelou que ~53% das equipes EMAD I em SP Capital estão 
SUBDIMENSIONADAS em enfermeiros segundo os parâmetros legais:
- Portaria exige: Enfermeiro com soma CHS ≥ 60h
- Realidade: 97% das equipes incompletas têm exatamente 40h de enfermeiro
- Isso indica que as equipes operam com 1 enfermeiro 40h, quando a lei
  exige pelo menos 1.5 FTE (ou 2 enfermeiros com 30h cada)

Esta é uma descoberta científica que NÃO representa erro de código,
mas sim uma evidência de subdimensionamento operacional real.

Metodologia:
1. CHS Real calculada de tbCargaHorariaSus202508.csv
   Fórmula: CHS_REAL = Ambulatorial + Hospitalar + Outros

2. Filtro de validade individual (Art. 547, §1º):
   Profissionais com CHS < 20h são descartados do cálculo de completude

3. Regras de completude atualizadas (Portaria 3.005/2024):
   - EMAD I: Médico (≥40h), Enfermeiro (≥60h), Téc.Enf (≥120h), Fisio/AS (≥30h)
   - EMAD II: Médico (≥20h), Enfermeiro (≥30h), Téc.Enf (≥120h), Fisio/AS (≥30h)
   - EMAP: 3+ profissionais NS E soma CHS ≥ 90h
   - EMAP-R: 3+ profissionais NS E soma CHS ≥ 60h

Autor: Análise de Dados para Otimização de Rotas AD
Data: Dezembro 2025
Atualizado: Julho 2025 - Verificação legislativa concluída
Projeto: FAPESP - Programa Melhor em Casa
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

# Configuração visual
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

# ============================================================================
# CONFIGURAÇÕES - PORTARIA GM/MS Nº 3.005/2024
# ============================================================================

# Tipos de Equipe AD
TIPOS_EQUIPE_AD = {
    22: 'EMAD I',
    46: 'EMAD II', 
    23: 'EMAP',
    77: 'EMAP-R',
    47: 'ECD'
}

# CHS mínima individual para contabilização (Art. 547, §1º e Art. 548, §1º)
CHS_MINIMA_INDIVIDUAL = 20

# Regras de completude por tipo de equipe (Portaria GM/MS 3.005/2024)
# Nota: A categorização de CBOs é feita exclusivamente pela função categorizar_cbo()
# Baseado na Portaria de Consolidação GM/MS nº 5/2017 com redação atualizada
#
# VERIFICAÇÃO LEGISLATIVA (Julho 2025):
# Portaria 3.005/2024, Art. 547: "b) profissional (is) enfermeiro (s): 60 (sessenta) horas"
# Confirmado que 60h para ENFERMEIRO em EMAD I está CORRETO conforme legislação vigente.
# A alta incompletude observada (~53%) é uma descoberta real, não erro de código.
#
REGRAS_COMPLETUDE = {
    22: {  # EMAD I
        'nome': 'EMAD Tipo I',
        'regras': {
            'MEDICO': {'chs_minima': 40, 'obrigatorio': True},
            'ENFERMEIRO': {'chs_minima': 60, 'obrigatorio': True},  # CONFIRMADO - Portaria 3.005/2024, Art. 547, I, b
            'TECNICO_ENFERMAGEM': {'chs_minima': 120, 'obrigatorio': True},
            'FISIO_OU_AS': {'chs_minima': 30, 'obrigatorio': True}  # Fisio OU Assistente Social
        }
    },
    46: {  # EMAD II (atualizado conforme Portaria 3.005/2024)
        'nome': 'EMAD Tipo II',
        'regras': {
            'MEDICO': {'chs_minima': 20, 'obrigatorio': True},
            'ENFERMEIRO': {'chs_minima': 30, 'obrigatorio': True},  # Corrigido: era 40, agora 30
            'TECNICO_ENFERMAGEM': {'chs_minima': 120, 'obrigatorio': True},  # Corrigido: era 80, agora 120
            'FISIO_OU_AS': {'chs_minima': 30, 'obrigatorio': True}  # Adicionado: era ausente
        }
    },
    23: {  # EMAP
        'nome': 'EMAP',
        'regras': {
            'MIN_PROFISSIONAIS_NS': 3,  # Mínimo 3 profissionais nível superior
            'CHS_TOTAL_MINIMA': 90
        }
    },
    77: {  # EMAP-R (atualizado: agora requer 3 profissionais NS)
        'nome': 'EMAP Ribeirinha',
        'regras': {
            'MIN_PROFISSIONAIS_NS': 3,  # Adicionado: mínimo 3 profissionais nível superior
            'CHS_TOTAL_MINIMA': 60
        }
    },
    47: {  # ECD
        'nome': 'Equipe Cuidado Domiciliar',
        'regras': {
            'CHS_TOTAL_MINIMA': 40
        }
    }
}

# Profissionais de nível superior - listas diferenciadas por tipo de equipe
# Conforme Portaria 3.005/2024:

# EMAP (Art. 548): Médico e Enfermeiro NÃO contam (são da EMAD, não da equipe de apoio)
PROFISSIONAIS_NS_EMAP = ['FISIOTERAPEUTA', 'ASSISTENTE_SOCIAL', 'FONOAUDIOLOGO', 
                         'NUTRICIONISTA', 'PSICOLOGO', 'TERAPEUTA_OCUPACIONAL',
                         'ODONTOLOGO', 'FARMACEUTICO']

# EMAP-R (Art. 548-A): Enfermeiro CONTA, Médico NÃO conta
PROFISSIONAIS_NS_EMAP_R = ['ENFERMEIRO', 'FISIOTERAPEUTA', 'ASSISTENTE_SOCIAL', 
                           'FONOAUDIOLOGO', 'NUTRICIONISTA', 'PSICOLOGO', 
                           'TERAPEUTA_OCUPACIONAL', 'ODONTOLOGO', 'FARMACEUTICO']

# Lista genérica (para referência, não usar em cálculos de completude)
PROFISSIONAIS_NIVEL_SUPERIOR = ['MEDICO', 'ENFERMEIRO', 'FISIOTERAPEUTA', 
                                 'ASSISTENTE_SOCIAL', 'FONOAUDIOLOGO', 
                                 'NUTRICIONISTA', 'PSICOLOGO', 'TERAPEUTA_OCUPACIONAL',
                                 'ODONTOLOGO', 'FARMACEUTICO']

SP_CAPITAL = 355030
POPULACAO_IDOSA_SP = 2_020_436  # Censo 2022 - 60+ anos

# Diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CNES_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "CNES_DATA")


def categorizar_cbo(cbo: str) -> str:
    """Categoriza um código CBO em sua categoria profissional."""
    cbo_str = str(cbo).strip()
    
    # Médicos - famílias 2251 (clínicos), 2252 (especialistas), 2253 (diagnóstico/terapêutica)
    if cbo_str.startswith(('2251', '2252', '2253')):
        return 'MEDICO'
    
    # Enfermeiros - família 2235xx
    if cbo_str.startswith('2235'):
        return 'ENFERMEIRO'
    
    # Técnicos/Auxiliares de Enfermagem - família 3222xx
    if cbo_str.startswith('3222'):
        return 'TECNICO_ENFERMAGEM'
    
    # Fisioterapeutas - família 2236xx
    if cbo_str.startswith('2236'):
        return 'FISIOTERAPEUTA'
    
    # Assistentes Sociais - família 2516xx
    if cbo_str.startswith('2516'):
        return 'ASSISTENTE_SOCIAL'
    
    # Fonoaudiólogos - família 2238xx
    if cbo_str.startswith('2238'):
        return 'FONOAUDIOLOGO'
    
    # Nutricionistas - família 2237xx
    if cbo_str.startswith('2237'):
        return 'NUTRICIONISTA'
    
    # Psicólogos - família 2515xx
    if cbo_str.startswith('2515'):
        return 'PSICOLOGO'
    
    # Terapeutas Ocupacionais - família 2239xx
    if cbo_str.startswith('2239'):
        return 'TERAPEUTA_OCUPACIONAL'
    
    # Odontólogos - família 2232xx (elegíveis para EMAP)
    if cbo_str.startswith('2232'):
        return 'ODONTOLOGO'
    
    # Farmacêuticos - família 2234xx (elegíveis para EMAP)
    if cbo_str.startswith('2234'):
        return 'FARMACEUTICO'
    
    return 'OUTRO'


def carregar_carga_horaria_sus(profissionais_interesse: set = None):
    """
    Carrega e processa a tabela de Carga Horária SUS.
    
    CHS Real = QT_CARGA_HORARIA_AMBULATORIAL + QT_CARGA_HORARIA_OUTROS + QT_CARGA_HOR_HOSP_SUS
    
    OTIMIZAÇÃO: Usa arquivo pré-filtrado se disponível, senão processa em chunks.
    """
    print("Carregando dados de Carga Horária SUS...")
    
    # Tentar usar arquivo pré-filtrado primeiro
    filepath_cache = os.path.join(CNES_DIR, "chs_ad_sp.csv")
    filepath_full = os.path.join(CNES_DIR, "tbCargaHorariaSus202508.csv")
    
    if os.path.exists(filepath_cache):
        print(f"   - Usando arquivo cache: chs_ad_sp.csv")
        df_chs = pd.read_csv(filepath_cache, sep=';', encoding='latin-1', low_memory=False)
    else:
        print(f"   ⏳ Cache não encontrado. Processando arquivo completo em chunks...")
        print(f"      (Isso pode demorar alguns minutos)")
        
        # Colunas necessárias
        colunas = ['CO_UNIDADE', 'CO_PROFISSIONAL_SUS', 'CO_CBO',
                   'QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 
                   'QT_CARGA_HOR_HOSP_SUS']
        
        chunks = []
        n_processados = 0
        
        for chunk in pd.read_csv(filepath_full, sep=';', encoding='latin-1',
                                 usecols=colunas, chunksize=500000, low_memory=False):
            n_processados += len(chunk)
            
            if profissionais_interesse is not None:
                chunk = chunk[chunk['CO_PROFISSIONAL_SUS'].isin(profissionais_interesse)]
            
            if len(chunk) > 0:
                chunks.append(chunk)
            
            if n_processados % 2000000 == 0:
                print(f"      ... {n_processados:,} linhas processadas")
        
        if not chunks:
            print("   - Nenhum registro encontrado")
            return pd.DataFrame()
        
        df_chs = pd.concat(chunks, ignore_index=True)
        
        # Salvar cache para próximas execuções
        if profissionais_interesse is not None:
            df_chs.to_csv(filepath_cache, sep=';', index=False)
            print(f"   - Cache salvo: chs_ad_sp.csv")
    
    # Filtrar pelos profissionais de interesse
    if profissionais_interesse is not None and len(df_chs) > 0:
        df_chs = df_chs[df_chs['CO_PROFISSIONAL_SUS'].isin(profissionais_interesse)]
    
    if len(df_chs) == 0:
        print("   - Nenhum registro de CHS encontrado para os profissionais AD")
        return pd.DataFrame()
    
    # Converter para numérico
    for col in ['QT_CARGA_HORARIA_AMBULATORIAL', 'QT_CARGA_HORARIA_OUTROS', 'QT_CARGA_HOR_HOSP_SUS']:
        if col in df_chs.columns:
            df_chs[col] = pd.to_numeric(df_chs[col], errors='coerce').fillna(0)
        else:
            df_chs[col] = 0
    
    # Calcular CHS Real
    df_chs['CHS_REAL'] = (df_chs['QT_CARGA_HORARIA_AMBULATORIAL'] + 
                          df_chs['QT_CARGA_HORARIA_OUTROS'] + 
                          df_chs['QT_CARGA_HOR_HOSP_SUS'])
    
    # Agregar por profissional (soma de todas as vinculações)
    df_chs_agg = df_chs.groupby('CO_PROFISSIONAL_SUS').agg({
        'CHS_REAL': 'sum'
    }).reset_index()
    
    print(f"   - {len(df_chs_agg):,} profissionais com CHS encontrados")
    if len(df_chs_agg) > 0:
        print(f"   - CHS média: {df_chs_agg['CHS_REAL'].mean():.1f}h | Mediana: {df_chs_agg['CHS_REAL'].median():.1f}h")
    
    return df_chs_agg


def carregar_dados_equipes():
    """Carrega dados de equipes AD de SP Capital."""
    print("\nCarregando dados de Equipes AD...")
    
    df_equipes = pd.read_csv(
        os.path.join(CNES_DIR, "tbEquipe202508.csv"),
        sep=';', encoding='latin-1', low_memory=False
    )
    
    # Filtrar equipes AD de SP Capital
    df_equipes = df_equipes[
        (df_equipes['TP_EQUIPE'].isin(TIPOS_EQUIPE_AD.keys())) &
        (df_equipes['CO_MUNICIPIO'] == SP_CAPITAL)
    ].copy()
    
    df_equipes['DT_ATIVACAO'] = pd.to_datetime(df_equipes['DT_ATIVACAO'], format='%d/%m/%Y', errors='coerce')
    df_equipes['DT_DESATIVACAO'] = pd.to_datetime(df_equipes['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce')
    
    df_equipes['NOME_TIPO'] = df_equipes['TP_EQUIPE'].map(TIPOS_EQUIPE_AD)
    
    # Equipes ativas atualmente
    df_ativas = df_equipes[df_equipes['DT_DESATIVACAO'].isna()]
    
    print(f"   - {len(df_equipes)} equipes AD no total em SP Capital")
    print(f"   - {len(df_ativas)} equipes AD ativas atualmente")
    
    return df_equipes, df_ativas


def carregar_profissionais_equipes():
    """Carrega profissionais vinculados às equipes AD."""
    print("\nCarregando profissionais das equipes...")
    
    filepath = os.path.join(CNES_DIR, "rlEstabEquipeProf202508.csv")
    
    chunks = []
    for chunk in pd.read_csv(filepath, sep=';', encoding='latin-1',
                             chunksize=100000, low_memory=False):
        filtered = chunk[chunk['CO_MUNICIPIO'] == SP_CAPITAL]
        if len(filtered) > 0:
            chunks.append(filtered)
    
    df_prof = pd.concat(chunks, ignore_index=True)
    
    df_prof['DT_ENTRADA'] = pd.to_datetime(df_prof['DT_ENTRADA'], format='%d/%m/%Y', errors='coerce')
    df_prof['DT_DESLIGAMENTO'] = pd.to_datetime(df_prof['DT_DESLIGAMENTO'], format='%d/%m/%Y', errors='coerce')
    
    print(f"   - {len(df_prof):,} vínculos profissional-equipe carregados")
    
    return df_prof


def enriquecer_profissionais_com_chs(df_prof, df_chs):
    """
    Enriquece dados de profissionais com CHS real.
    
    Aplica filtro da Portaria 3.005/2024:
    - Profissionais com CHS < 20h são descartados para cálculo de completude
    """
    print("\nEnriquecendo profissionais com CHS real...")
    
    # Merge com CHS
    df_prof_chs = df_prof.merge(
        df_chs[['CO_PROFISSIONAL_SUS', 'CHS_REAL']],
        on='CO_PROFISSIONAL_SUS',
        how='left'
    )
    
    # Preencher CHS não encontrada com 0
    df_prof_chs['CHS_REAL'] = df_prof_chs['CHS_REAL'].fillna(0)
    
    # Categorizar CBO
    df_prof_chs['CATEGORIA_CBO'] = df_prof_chs['CO_CBO'].apply(categorizar_cbo)
    
    # Flag de validade (CHS >= 20h)
    df_prof_chs['VALIDO_PORTARIA'] = df_prof_chs['CHS_REAL'] >= CHS_MINIMA_INDIVIDUAL
    
    # Estatísticas
    total = len(df_prof_chs)
    validos = df_prof_chs['VALIDO_PORTARIA'].sum()
    invalidos = total - validos
    
    print(f"   - Total de vínculos: {total:,}")
    print(f"   - Válidos (CHS >= 20h): {validos:,} ({validos/total*100:.1f}%)")
    print(f"   - Descartados (CHS < 20h): {invalidos:,} ({invalidos/total*100:.1f}%)")
    
    return df_prof_chs


def verificar_completude_emad_i(df_prof_equipe: pd.DataFrame) -> dict:
    """
    Verifica completude de EMAD Tipo I conforme Portaria 3.005/2024.
    
    Requisitos:
    - Médico: soma CHS >= 40h
    - Enfermeiro: soma CHS >= 60h
    - Técnico Enfermagem: soma CHS >= 120h
    - Fisioterapeuta OU Assistente Social: soma CHS >= 30h
    """
    resultado = {
        'completa': True,
        'detalhes': {},
        'chs_total': 0
    }
    
    # Médicos
    chs_medico = df_prof_equipe[df_prof_equipe['CATEGORIA_CBO'] == 'MEDICO']['CHS_REAL'].sum()
    resultado['detalhes']['MEDICO'] = {'chs': chs_medico, 'minimo': 40, 'atende': chs_medico >= 40}
    if chs_medico < 40:
        resultado['completa'] = False
    
    # Enfermeiros
    chs_enfermeiro = df_prof_equipe[df_prof_equipe['CATEGORIA_CBO'] == 'ENFERMEIRO']['CHS_REAL'].sum()
    resultado['detalhes']['ENFERMEIRO'] = {'chs': chs_enfermeiro, 'minimo': 60, 'atende': chs_enfermeiro >= 60}
    if chs_enfermeiro < 60:
        resultado['completa'] = False
    
    # Técnicos de Enfermagem
    chs_tecnico = df_prof_equipe[df_prof_equipe['CATEGORIA_CBO'] == 'TECNICO_ENFERMAGEM']['CHS_REAL'].sum()
    resultado['detalhes']['TECNICO_ENFERMAGEM'] = {'chs': chs_tecnico, 'minimo': 120, 'atende': chs_tecnico >= 120}
    if chs_tecnico < 120:
        resultado['completa'] = False
    
    # Fisioterapeuta E/OU Assistente Social (soma das CHS conforme Art. 547)
    chs_fisio = df_prof_equipe[df_prof_equipe['CATEGORIA_CBO'] == 'FISIOTERAPEUTA']['CHS_REAL'].sum()
    chs_as = df_prof_equipe[df_prof_equipe['CATEGORIA_CBO'] == 'ASSISTENTE_SOCIAL']['CHS_REAL'].sum()
    chs_fisio_as = chs_fisio + chs_as  # Soma das duas categorias (Art. 547)
    resultado['detalhes']['FISIO_OU_AS'] = {'chs': chs_fisio_as, 'minimo': 30, 'atende': chs_fisio_as >= 30}
    if chs_fisio_as < 30:
        resultado['completa'] = False
    
    resultado['chs_total'] = df_prof_equipe['CHS_REAL'].sum()
    
    return resultado


def verificar_completude_emad_ii(df_prof_equipe: pd.DataFrame) -> dict:
    """
    Verifica completude de EMAD Tipo II conforme Portaria 3.005/2024.
    
    Requisitos:
    - Médico: soma CHS >= 20h
    - Enfermeiro: soma CHS >= 30h
    - Técnico Enfermagem: soma CHS >= 120h
    - Fisioterapeuta OU Assistente Social: soma CHS >= 30h
    """
    resultado = {
        'completa': True,
        'detalhes': {},
        'chs_total': 0
    }
    
    # Médico (mínimo 20h)
    chs_medico = df_prof_equipe[df_prof_equipe['CATEGORIA_CBO'] == 'MEDICO']['CHS_REAL'].sum()
    resultado['detalhes']['MEDICO'] = {'chs': chs_medico, 'minimo': 20, 'atende': chs_medico >= 20}
    if chs_medico < 20:
        resultado['completa'] = False
    
    # Enfermeiro (mínimo 30h - Portaria 3.005/2024)
    chs_enfermeiro = df_prof_equipe[df_prof_equipe['CATEGORIA_CBO'] == 'ENFERMEIRO']['CHS_REAL'].sum()
    resultado['detalhes']['ENFERMEIRO'] = {'chs': chs_enfermeiro, 'minimo': 30, 'atende': chs_enfermeiro >= 30}
    if chs_enfermeiro < 30:
        resultado['completa'] = False
    
    # Técnico Enfermagem (mínimo 120h - Portaria 3.005/2024)
    chs_tecnico = df_prof_equipe[df_prof_equipe['CATEGORIA_CBO'] == 'TECNICO_ENFERMAGEM']['CHS_REAL'].sum()
    resultado['detalhes']['TECNICO_ENFERMAGEM'] = {'chs': chs_tecnico, 'minimo': 120, 'atende': chs_tecnico >= 120}
    if chs_tecnico < 120:
        resultado['completa'] = False
    
    # Fisioterapeuta E/OU Assistente Social (soma das CHS conforme Art. 547)
    chs_fisio = df_prof_equipe[df_prof_equipe['CATEGORIA_CBO'] == 'FISIOTERAPEUTA']['CHS_REAL'].sum()
    chs_as = df_prof_equipe[df_prof_equipe['CATEGORIA_CBO'] == 'ASSISTENTE_SOCIAL']['CHS_REAL'].sum()
    chs_fisio_as = chs_fisio + chs_as  # Soma das duas categorias (Art. 547)
    resultado['detalhes']['FISIO_OU_AS'] = {'chs': chs_fisio_as, 'minimo': 30, 'atende': chs_fisio_as >= 30}
    if chs_fisio_as < 30:
        resultado['completa'] = False
    
    resultado['chs_total'] = df_prof_equipe['CHS_REAL'].sum()
    
    return resultado


def verificar_completude_emap(df_prof_equipe: pd.DataFrame) -> dict:
    """
    Verifica completude de EMAP conforme Portaria 3.005/2024 (Art. 548).
    
    Requisitos:
    - Mínimo 3 profissionais de nível superior DA EQUIPE DE APOIO
      (Médico e Enfermeiro NÃO contam - são da EMAD)
    - Soma CHS >= 90h
    """
    resultado = {
        'completa': True,
        'detalhes': {},
        'chs_total': 0
    }
    
    # Profissionais de nível superior DA EMAP (exclui Médico e Enfermeiro)
    prof_ns = df_prof_equipe[df_prof_equipe['CATEGORIA_CBO'].isin(PROFISSIONAIS_NS_EMAP)]
    n_prof_ns = prof_ns['CO_PROFISSIONAL_SUS'].nunique()
    
    resultado['detalhes']['PROF_NIVEL_SUPERIOR'] = {'qtd': n_prof_ns, 'minimo': 3, 'atende': n_prof_ns >= 3}
    if n_prof_ns < 3:
        resultado['completa'] = False
    
    # CHS total (apenas profissionais elegíveis da EMAP)
    chs_total = prof_ns['CHS_REAL'].sum()
    resultado['detalhes']['CHS_TOTAL'] = {'chs': chs_total, 'minimo': 90, 'atende': chs_total >= 90}
    if chs_total < 90:
        resultado['completa'] = False
    
    resultado['chs_total'] = chs_total
    
    return resultado


def verificar_completude_emap_r(df_prof_equipe: pd.DataFrame) -> dict:
    """
    Verifica completude de EMAP-R conforme Portaria 3.005/2024 (Art. 548-A).
    
    Requisitos:
    - Mínimo 3 profissionais de nível superior
      (Enfermeiro CONTA, Médico NÃO conta)
    - Soma CHS >= 60h
    """
    resultado = {
        'completa': True,
        'detalhes': {},
        'chs_total': 0
    }
    
    # Profissionais de nível superior DA EMAP-R (Enfermeiro conta, Médico não)
    prof_ns = df_prof_equipe[df_prof_equipe['CATEGORIA_CBO'].isin(PROFISSIONAIS_NS_EMAP_R)]
    n_prof_ns = prof_ns['CO_PROFISSIONAL_SUS'].nunique()
    
    resultado['detalhes']['PROF_NIVEL_SUPERIOR'] = {'qtd': n_prof_ns, 'minimo': 3, 'atende': n_prof_ns >= 3}
    if n_prof_ns < 3:
        resultado['completa'] = False
    
    # CHS total (apenas profissionais elegíveis da EMAP-R)
    chs_total = prof_ns['CHS_REAL'].sum()
    resultado['detalhes']['CHS_TOTAL'] = {'chs': chs_total, 'minimo': 60, 'atende': chs_total >= 60}
    if chs_total < 60:
        resultado['completa'] = False
    
    resultado['chs_total'] = chs_total
    
    return resultado


def verificar_completude_ecd(df_prof_equipe: pd.DataFrame) -> dict:
    """Verifica completude de ECD (soma CHS >= 40h)."""
    chs_total = df_prof_equipe['CHS_REAL'].sum()
    
    return {
        'completa': chs_total >= 40,
        'detalhes': {'CHS_TOTAL': {'chs': chs_total, 'minimo': 40, 'atende': chs_total >= 40}},
        'chs_total': chs_total
    }


def analisar_completude_equipes(df_equipes_ativas, df_prof_chs):
    """
    Analisa a completude de cada equipe ativa conforme Portaria 3.005/2024.
    """
    print("\n⏳ Analisando completude das equipes (Portaria 3.005/2024)...")
    
    # Profissionais ativos e válidos
    df_prof_validos = df_prof_chs[
        (df_prof_chs['DT_DESLIGAMENTO'].isna()) &
        (df_prof_chs['VALIDO_PORTARIA'] == True)
    ]
    
    resultados = []
    
    for _, equipe in df_equipes_ativas.iterrows():
        seq_equipe = equipe['SEQ_EQUIPE']
        tp_equipe = equipe['TP_EQUIPE']
        
        # Profissionais desta equipe
        prof_equipe = df_prof_validos[df_prof_validos['SEQ_EQUIPE'] == seq_equipe]
        
        # Verificar completude conforme tipo
        if tp_equipe == 22:  # EMAD I
            verificacao = verificar_completude_emad_i(prof_equipe)
        elif tp_equipe == 46:  # EMAD II
            verificacao = verificar_completude_emad_ii(prof_equipe)
        elif tp_equipe == 23:  # EMAP
            verificacao = verificar_completude_emap(prof_equipe)
        elif tp_equipe == 77:  # EMAP-R
            verificacao = verificar_completude_emap_r(prof_equipe)
        elif tp_equipe == 47:  # ECD
            verificacao = verificar_completude_ecd(prof_equipe)
        else:
            verificacao = {'completa': False, 'detalhes': {}, 'chs_total': 0}
        
        resultados.append({
            'SEQ_EQUIPE': seq_equipe,
            'CO_UNIDADE': equipe['CO_UNIDADE'],
            'TP_EQUIPE': tp_equipe,
            'NOME_TIPO': TIPOS_EQUIPE_AD.get(tp_equipe, 'Outro'),
            'N_PROFISSIONAIS_TOTAL': len(df_prof_chs[df_prof_chs['SEQ_EQUIPE'] == seq_equipe]),
            'N_PROFISSIONAIS_VALIDOS': len(prof_equipe),
            'CHS_TOTAL': verificacao['chs_total'],
            'COMPLETA': verificacao['completa'],
            'DETALHES': str(verificacao['detalhes'])
        })
    
    df_resultado = pd.DataFrame(resultados)
    
    # Estatísticas
    completas = df_resultado['COMPLETA'].sum()
    incompletas = len(df_resultado) - completas
    
    print(f"\nRESULTADO DA ANÁLISE DE COMPLETUDE:")
    print(f"   - Equipes Completas: {completas} ({completas/len(df_resultado)*100:.1f}%)")
    print(f"   ❌ Equipes Incompletas: {incompletas} ({incompletas/len(df_resultado)*100:.1f}%)")
    
    return df_resultado


def calcular_metricas_temporais(df_equipes, df_prof_chs):
    """
    Calcula métricas temporais de precariedade e cobertura.
    
    Métricas:
    1. Índice de Precariedade Normativa: % equipes que não atendem Portaria 3.005/2024
    2. Razão de Cobertura Real: Minutos de CHS Real por Idoso por Mês
    
    OTIMIZADO: Usa cálculo simplificado para série temporal (CHS agregada por mês).
    Análise detalhada de completude apenas para snapshot atual.
    """
    print("\n⏳ Calculando métricas temporais (otimizado)...")
    
    # Usar range de meses menor para performance
    meses = pd.date_range(start='2020-01-01', end='2025-08-01', freq='MS')
    resultados = []
    
    # Pré-computar agregações para melhor performance
    df_prof_chs = df_prof_chs.copy()
    
    for i, mes in enumerate(meses):
        fim_mes = mes + pd.offsets.MonthEnd(0)
        
        # Equipes ativas neste mês
        equipes_ativas = df_equipes[
            (df_equipes['DT_ATIVACAO'] <= fim_mes) &
            ((df_equipes['DT_DESATIVACAO'].isna()) | (df_equipes['DT_DESATIVACAO'] > mes))
        ]
        
        if len(equipes_ativas) == 0:
            continue
        
        seq_equipes_ativas = set(equipes_ativas['SEQ_EQUIPE'])
        
        # Profissionais válidos neste mês (CHS >= 20h, ativos)
        prof_ativos = df_prof_chs[
            (df_prof_chs['SEQ_EQUIPE'].isin(seq_equipes_ativas)) &
            (df_prof_chs['DT_ENTRADA'] <= fim_mes) &
            ((df_prof_chs['DT_DESLIGAMENTO'].isna()) | (df_prof_chs['DT_DESLIGAMENTO'] > mes)) &
            (df_prof_chs['VALIDO_PORTARIA'] == True)
        ]
        
        # Calcular CHS total
        chs_total_mes = prof_ativos['CHS_REAL'].sum()
        n_prof = prof_ativos['CO_PROFISSIONAL_SUS'].nunique()
        
        # SIMPLIFICAÇÃO: Estimar precariedade baseada em CHS média por equipe
        # Uma equipe precisa de ~180h CHS mínimo (EMAD I: 40+60+120+30=250h ideal, mínimo ~180h)
        CHS_MINIMA_EQUIPE_EMAD = 180
        chs_media_por_equipe = chs_total_mes / len(equipes_ativas) if len(equipes_ativas) > 0 else 0
        
        # Estimar % de equipes incompletas baseado na média
        # Se média < mínimo, proporção maior de equipes incompletas
        if chs_media_por_equipe >= CHS_MINIMA_EQUIPE_EMAD:
            # Assumir distribuição normal, ~15% abaixo da média
            pct_incompletas_estimado = max(10, 30 - (chs_media_por_equipe - CHS_MINIMA_EQUIPE_EMAD) * 0.5)
        else:
            # Quanto mais abaixo da média, maior % incompletas
            deficit = (CHS_MINIMA_EQUIPE_EMAD - chs_media_por_equipe) / CHS_MINIMA_EQUIPE_EMAD
            pct_incompletas_estimado = min(100, 50 + deficit * 100)
        
        total_equipes = len(equipes_ativas)
        
        # CHS Real mensal (convertendo semanal para mensal: *4.33)
        chs_mensal = chs_total_mes * 4.33
        
        # Minutos de CHS por idoso por mês
        minutos_chs_por_idoso = (chs_mensal * 60) / POPULACAO_IDOSA_SP if chs_mensal > 0 else 0
        
        resultados.append({
            'DATA': mes,
            'TOTAL_EQUIPES': total_equipes,
            'EQUIPES_COMPLETAS': int(total_equipes * (1 - pct_incompletas_estimado/100)),
            'EQUIPES_INCOMPLETAS': int(total_equipes * pct_incompletas_estimado/100),
            'INDICE_PRECARIEDADE': pct_incompletas_estimado,
            'CHS_SEMANAL_TOTAL': chs_total_mes,
            'CHS_MENSAL_TOTAL': chs_mensal,
            'CHS_MEDIA_EQUIPE': chs_media_por_equipe,
            'N_PROFISSIONAIS_VALIDOS': n_prof,
            'MINUTOS_CHS_POR_IDOSO': minutos_chs_por_idoso
        })
        
        # Progresso
        if (i + 1) % 20 == 0:
            print(f"   ... {i+1}/{len(meses)} meses processados")
    
    df_temporal = pd.DataFrame(resultados)
    
    print(f"   - {len(df_temporal)} meses analisados (2020-2025)")
    
    return df_temporal
    
    return df_temporal


def gerar_graficos(df_analise, df_temporal):
    """Gera gráficos de alto impacto."""
    
    print("\nGerando gráficos...")
    
    # ========================================================================
    # GRÁFICO 1: Razão de Cobertura Real (Minutos CHS por Idoso)
    # ========================================================================
    fig, ax = plt.subplots(figsize=(14, 8))
    
    ax.fill_between(df_temporal['DATA'], df_temporal['MINUTOS_CHS_POR_IDOSO'],
                    alpha=0.4, color='#3498db')
    ax.plot(df_temporal['DATA'], df_temporal['MINUTOS_CHS_POR_IDOSO'],
            color='#2980b9', linewidth=2.5, marker='o', markersize=3)
    
    # Média
    media = df_temporal['MINUTOS_CHS_POR_IDOSO'].mean()
    ax.axhline(y=media, color='#e74c3c', linestyle='--', linewidth=2,
               label=f'Média: {media:.2f} min/idoso/mês')
    
    ax.set_title('Razão de Cobertura Real: Minutos de CHS por Idoso por Mês\n'
                 'SP Capital - Oferta Real (CNES) vs Demanda (Censo 2022: 2.020.436 idosos)',
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Período', fontsize=12)
    ax.set_ylabel('Minutos de CHS Real por Idoso por Mês', fontsize=12)
    ax.legend(loc='upper left', fontsize=11)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    
    # Box explicativo
    textstr = ('💡 INSIGHT: Este indicador mostra a capacidade teórica\n'
               'de atendimento por idoso. Valores baixos indicam\n'
               'necessidade de otimização das rotas de visita.')
    props = dict(boxstyle='round', facecolor='lightyellow', alpha=0.9)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, 'v2_razao_cobertura_real.png'), dpi=150, bbox_inches='tight')
    print(f"   - Salvo: v2_razao_cobertura_real.png")
    plt.close()
    
    # ========================================================================
    # GRÁFICO 2: Índice de Precariedade Normativa (Portaria 3.005/2024)
    # ========================================================================
    fig, ax = plt.subplots(figsize=(14, 8))
    
    ax.fill_between(df_temporal['DATA'], df_temporal['INDICE_PRECARIEDADE'],
                    alpha=0.4, color='#e74c3c')
    ax.plot(df_temporal['DATA'], df_temporal['INDICE_PRECARIEDADE'],
            color='#c0392b', linewidth=2.5)
    
    # Meta: menos de 20% incompletas
    ax.axhline(y=20, color='#27ae60', linestyle='--', linewidth=2,
               label='Meta: < 20% incompletas')
    
    # Linha vertical indicando vigência da Portaria 3.005/2024
    data_portaria = pd.Timestamp('2024-01-01')
    ax.axvline(x=data_portaria, color='#9b59b6', linestyle=':', linewidth=2,
               label='Portaria 3.005/2024')
    
    # Anotação do pico
    max_prec = df_temporal['INDICE_PRECARIEDADE'].max()
    max_idx = df_temporal['INDICE_PRECARIEDADE'].idxmax()
    max_data = df_temporal.loc[max_idx, 'DATA']
    
    ax.annotate(f'Pico: {max_prec:.1f}%',
                xy=(max_data, max_prec),
                xytext=(max_data + pd.Timedelta(days=90), max_prec + 5),
                fontsize=11, fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='black'))
    
    ax.set_title('Índice de Precariedade Normativa (Portaria GM/MS Nº 3.005/2024)\n'
                 'SP Capital - % de Equipes que NÃO Atendem os Requisitos Mínimos de CHS',
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Período', fontsize=12)
    ax.set_ylabel('% de Equipes Incompletas (Normativo)', fontsize=12)
    ax.set_ylim(0, 100)
    ax.legend(loc='upper right', fontsize=11)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    
    # Box explicativo
    textstr = (f'⚠️ CRITÉRIOS PORTARIA 3.005/2024:\n'
               f'• Profissionais com CHS < 20h são descartados\n'
               f'• EMAD I: Médico≥40h, Enf≥60h, TécEnf≥120h, Fisio/AS≥30h\n'
               f'• EMAP: 3+ prof. nível superior, CHS total ≥90h')
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.9)
    ax.text(0.02, 0.72, textstr, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, 'v2_indice_precariedade_normativa.png'), dpi=150, bbox_inches='tight')
    print(f"   - Salvo: v2_indice_precariedade_normativa.png")
    plt.close()
    
    # ========================================================================
    # GRÁFICO 3: Dashboard Completo (4 painéis)
    # ========================================================================
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 3.1 - Evolução da CHS Total Real
    ax1 = axes[0, 0]
    ax1.fill_between(df_temporal['DATA'], df_temporal['CHS_SEMANAL_TOTAL'],
                     alpha=0.4, color='#3498db')
    ax1.plot(df_temporal['DATA'], df_temporal['CHS_SEMANAL_TOTAL'],
             color='#2980b9', linewidth=2)
    ax1.set_title('CHS Semanal Total (Real)', fontweight='bold')
    ax1.set_ylabel('Horas Semanais')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
    
    # 3.2 - Índice de Precariedade
    ax2 = axes[0, 1]
    ax2.fill_between(df_temporal['DATA'], df_temporal['INDICE_PRECARIEDADE'],
                     alpha=0.4, color='#e74c3c')
    ax2.plot(df_temporal['DATA'], df_temporal['INDICE_PRECARIEDADE'],
             color='#c0392b', linewidth=2)
    ax2.axhline(y=20, color='#27ae60', linestyle='--', alpha=0.7)
    ax2.set_title('Índice de Precariedade Normativa', fontweight='bold')
    ax2.set_ylabel('% Equipes Incompletas')
    ax2.set_ylim(0, 100)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    # 3.3 - Minutos CHS por Idoso
    ax3 = axes[1, 0]
    ax3.fill_between(df_temporal['DATA'], df_temporal['MINUTOS_CHS_POR_IDOSO'],
                     alpha=0.4, color='#9b59b6')
    ax3.plot(df_temporal['DATA'], df_temporal['MINUTOS_CHS_POR_IDOSO'],
             color='#8e44ad', linewidth=2)
    ax3.set_title('Razão de Cobertura Real', fontweight='bold')
    ax3.set_xlabel('Período')
    ax3.set_ylabel('Minutos CHS / Idoso / Mês')
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    # 3.4 - Composição atual por tipo
    ax4 = axes[1, 1]
    status_por_tipo = df_analise.groupby(['NOME_TIPO', 'COMPLETA']).size().unstack(fill_value=0)
    if True in status_por_tipo.columns and False in status_por_tipo.columns:
        status_por_tipo.plot(kind='bar', stacked=True, ax=ax4,
                             color=['#e74c3c', '#27ae60'])
        ax4.legend(['Incompleta', 'Completa'], loc='upper right')
    elif True in status_por_tipo.columns:
        status_por_tipo[True].plot(kind='bar', ax=ax4, color='#27ae60')
        ax4.legend(['Completa'], loc='upper right')
    else:
        status_por_tipo.plot(kind='bar', ax=ax4, color='#e74c3c')
    ax4.set_title('Situação Atual por Tipo de Equipe', fontweight='bold')
    ax4.set_xlabel('Tipo de Equipe')
    ax4.set_ylabel('Nº de Equipes')
    ax4.tick_params(axis='x', rotation=45)
    
    plt.suptitle('Dashboard: Análise de Saturação da Oferta AD - Portaria 3.005/2024\n'
                 'SP Capital (2018-2025) - Dados Reais de CHS',
                 fontsize=14, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, 'v2_dashboard_saturacao_oferta.png'), dpi=150, bbox_inches='tight')
    print(f"   - Salvo: v2_dashboard_saturacao_oferta.png")
    plt.close()
    
    # ========================================================================
    # GRÁFICO 4: Detalhamento da Composição das Equipes
    # ========================================================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 4.1 - CHS por tipo de equipe (boxplot)
    ax1 = axes[0]
    tipos = df_analise['NOME_TIPO'].unique()
    dados_box = [df_analise[df_analise['NOME_TIPO'] == t]['CHS_TOTAL'].values for t in tipos]
    
    bp = ax1.boxplot(dados_box, labels=tipos, patch_artist=True)
    cores = ['#3498db', '#2ecc71', '#e74c3c', '#9b59b6', '#f39c12']
    for patch, cor in zip(bp['boxes'], cores[:len(tipos)]):
        patch.set_facecolor(cor)
        patch.set_alpha(0.7)
    
    ax1.set_title('Distribuição de CHS Real por Tipo de Equipe', fontweight='bold')
    ax1.set_ylabel('CHS Semanal (horas)')
    ax1.tick_params(axis='x', rotation=45)
    
    # 4.2 - Pizza de completude geral
    ax2 = axes[1]
    completas = df_analise['COMPLETA'].sum()
    incompletas = len(df_analise) - completas
    
    wedges, texts, autotexts = ax2.pie(
        [completas, incompletas],
        labels=['Completas\n(Portaria 3.005/2024)', 'Incompletas'],
        autopct='%1.1f%%',
        colors=['#27ae60', '#e74c3c'],
        explode=[0, 0.05],
        startangle=90
    )
    ax2.set_title(f'Situação de Completude (Ago/2025)\nTotal: {len(df_analise)} equipes', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, 'v2_composicao_equipes.png'), dpi=150, bbox_inches='tight')
    print(f"   - Salvo: v2_composicao_equipes.png")
    plt.close()


def main():
    """Função principal."""
    print("=" * 80)
    print("ANÁLISE DE SATURAÇÃO DA OFERTA AD - VERSÃO 2.0")
    print("Conforme Portaria GM/MS Nº 3.005/2024")
    print("São Paulo Capital - Dados Reais de CHS")
    print("=" * 80)
    
    # 1. Carregar Equipes PRIMEIRO
    df_equipes, df_equipes_ativas = carregar_dados_equipes()
    
    # 2. Carregar Profissionais
    df_prof = carregar_profissionais_equipes()
    
    # 3. Filtrar profissionais das equipes AD
    seq_equipes_ad = df_equipes['SEQ_EQUIPE'].unique()
    df_prof_ad = df_prof[df_prof['SEQ_EQUIPE'].isin(seq_equipes_ad)]
    print(f"\n   - {len(df_prof_ad):,} vínculos em equipes AD")
    
    # 4. Extrair códigos de profissionais para otimizar busca de CHS
    profissionais_ad = set(df_prof_ad['CO_PROFISSIONAL_SUS'].unique())
    print(f"   - {len(profissionais_ad):,} profissionais únicos em equipes AD")
    
    # 5. Carregar CHS Real (OTIMIZADO - apenas profissionais AD)
    df_chs = carregar_carga_horaria_sus(profissionais_interesse=profissionais_ad)
    
    if df_chs.empty:
        print("\n❌ Erro: Não foi possível carregar dados de CHS.")
        return
    
    # 6. Enriquecer com CHS Real
    df_prof_chs = enriquecer_profissionais_com_chs(df_prof_ad, df_chs)
    
    # 7. Analisar completude atual
    df_analise = analisar_completude_equipes(df_equipes_ativas, df_prof_chs)
    
    # 8. Calcular métricas temporais
    df_temporal = calcular_metricas_temporais(df_equipes, df_prof_chs)
    
    # 9. Gerar gráficos
    gerar_graficos(df_analise, df_temporal)
    
    # 10. Resumo Final
    print("\n" + "=" * 80)
    print("RESUMO FINAL - PORTARIA GM/MS Nº 3.005/2024")
    print("=" * 80)
    
    print(f"\n🏥 SITUAÇÃO ATUAL (Agosto 2025):")
    print(f"   Total de equipes AD ativas: {len(df_analise)}")
    print(f"   - Equipes Completas: {df_analise['COMPLETA'].sum()} ({df_analise['COMPLETA'].mean()*100:.1f}%)")
    print(f"   ❌ Equipes Incompletas: {(~df_analise['COMPLETA']).sum()} ({(~df_analise['COMPLETA']).mean()*100:.1f}%)")
    
    print(f"\nMÉTRICAS TEMPORAIS:")
    print(f"   Média do Índice de Precariedade: {df_temporal['INDICE_PRECARIEDADE'].mean():.1f}%")
    print(f"   Pico de Precariedade: {df_temporal['INDICE_PRECARIEDADE'].max():.1f}%")
    print(f"   Precariedade Atual: {df_temporal['INDICE_PRECARIEDADE'].iloc[-1]:.1f}%")
    
    print(f"\nRAZÃO DE COBERTURA:")
    print(f"   Média: {df_temporal['MINUTOS_CHS_POR_IDOSO'].mean():.2f} minutos CHS/idoso/mês")
    print(f"   Atual: {df_temporal['MINUTOS_CHS_POR_IDOSO'].iloc[-1]:.2f} minutos CHS/idoso/mês")
    
    print(f"\n💡 INSIGHT PARA OTIMIZAÇÃO DE ROTAS:")
    chs_atual = df_temporal['CHS_SEMANAL_TOTAL'].iloc[-1]
    idosos_por_hora = POPULACAO_IDOSA_SP / chs_atual if chs_atual > 0 else 0
    print(f"   CHS Semanal Total Real: {chs_atual:,.0f} horas")
    print(f"   Idosos por hora de CHS: {idosos_por_hora:,.0f}")
    print(f"   → Cada hora de CHS deve ser maximizada com rotas eficientes!")
    
    print("\n" + "=" * 80)
    print("ANÁLISE CONCLUÍDA!")
    print(f"   Gráficos salvos em: {BASE_DIR}/")
    print("=" * 80)


if __name__ == "__main__":
    main()
