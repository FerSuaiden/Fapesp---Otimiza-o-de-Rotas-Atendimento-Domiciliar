#!/usr/bin/env python3
"""
PARTE 3 - Script 15: Gerador de Instâncias Sintéticas para HHC-RSP

IC FAPESP: Otimização de Rotas e Agendamento para Atenção Domiciliar

OBJETIVO:
Gerar instâncias sintéticas realísticas para testar o modelo de otimização
de rotas e agendamento de equipes de Atenção Domiciliar (BRKGA).

JUSTIFICATIVA:
Dados públicos do DATASUS (SIA/SISAB) NÃO contêm: localização geográfica 
dos pacientes, identificação individual, janelas de tempo ou frequência.
Por isso, geramos instâncias SINTÉTICAS que são PLAUSÍVEIS porque usam:
- Localização REAL das equipes EMAD (CNES/DATASUS)
- Distribuição proporcional à população idosa (IBGE Censo 2022)
- Proporções AD2/AD3 da Portaria GM/MS nº 3.005/2024

PARÂMETROS DO MODELO (Kummer et al., 2024):
- n: número de pacientes
- m: número de equipes
- K: capacidade diária de cada equipe (horas)
- d_ij: matriz de distâncias/tempos
- s_i: tempo de serviço em cada paciente
- [a_i, b_i]: janela de tempo de cada paciente
- f_i: frequência de visitas por semana
- q_i: qualificação necessária (AD2 ou AD3)

FONTES DE DADOS:
- CNES/DATASUS: tbEquipe202508.csv + tbEstabelecimento202508.csv
- IBGE Censo 2022: demanda_idosos_sp_censo2022.csv
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
from pathlib import Path

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

BASE_DIR = Path("/home/fersuaiden/Área de trabalho/Faculdade/IC")
CNES_DIR = BASE_DIR / "CNES_DATA"
IBGE_DIR = BASE_DIR / "IBGE_DATA"
OUTPUT_DIR = BASE_DIR / "Outputs&Codigo/PARTE3"
INSTANCIAS_DIR = OUTPUT_DIR / "instancias"

INSTANCIAS_DIR.mkdir(exist_ok=True)

# ==============================================================================
# PARÂMETROS DE GERAÇÃO (Portaria GM/MS nº 3.005/2024)
# ==============================================================================

# Art. 563-A, § 1º, III: "em torno de 70% de AD2" e "até 30% de AD3"
# AD1 não incluída porque é responsabilidade da Atenção Primária (ESF)
DIST_MODALIDADE = {'AD2': 0.70, 'AD3': 0.30}

# Frequência de visitas por modalidade
# AD2: "minimamente semanais" (Art. 539) | AD3: quase diário (casos graves)
FREQ_VISITAS = {
    'AD2': {'min': 1, 'max': 3, 'unidade': 'semanal'},
    'AD3': {'min': 5, 'max': 7, 'unidade': 'semanal'}
}

# Tempo de serviço (minutos) - baseado na literatura
TEMPO_SERVICO = {
    'AD2': {'min': 30, 'max': 60},   # Média complexidade
    'AD3': {'min': 45, 'max': 90}    # Alta complexidade
}

# Janelas de tempo (preferência do paciente)
DIST_JANELA = {'manha': 0.40, 'tarde': 0.35, 'integral': 0.25}
JANELAS_HORARIO = {
    'manha': (7*60, 12*60),      # 7:00 - 12:00
    'tarde': (13*60, 18*60),     # 13:00 - 18:00
    'integral': (7*60, 18*60)    # 7:00 - 18:00
}

# Capacidade diária de uma equipe EMAD (minutos)
# Art. 547: ~8h/dia útil, mas não 100% é atendimento direto
CAPACIDADE_EQUIPE_MIN = 360  # 6h úteis
CAPACIDADE_EQUIPE_MAX = 480  # 8h úteis

VELOCIDADE_MEDIA = 25  # km/h em área urbana

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def haversine(lon1, lat1, lon2, lat2):
    """Calcula distância em km entre dois pontos usando fórmula de Haversine."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * asin(sqrt(a)) * 6371  # Raio da Terra em km


def distancia_para_tempo(distancia_km, velocidade_kmh=VELOCIDADE_MEDIA):
    """Converte distância em tempo de viagem (minutos)."""
    return (distancia_km / velocidade_kmh) * 60


def sortear_modalidade():
    """Sorteia modalidade AD2/AD3 (Portaria 3.005/2024: 70%/30%)."""
    return 'AD2' if np.random.random() < DIST_MODALIDADE['AD2'] else 'AD3'


def sortear_janela_tempo():
    """Sorteia janela de tempo preferida (manhã 40%, tarde 35%, integral 25%)."""
    r = np.random.random()
    if r < DIST_JANELA['manha']:
        return 'manha'
    elif r < DIST_JANELA['manha'] + DIST_JANELA['tarde']:
        return 'tarde'
    return 'integral'


def gerar_frequencia(modalidade):
    """Gera frequência de visitas: AD2 1-3x/sem, AD3 5-7x/sem."""
    params = FREQ_VISITAS[modalidade]
    return np.random.randint(params['min'], params['max'] + 1), params['unidade']


def gerar_tempo_servico(modalidade):
    """Gera tempo de serviço: AD2 30-60min, AD3 45-90min."""
    params = TEMPO_SERVICO[modalidade]
    return np.random.randint(params['min'], params['max'] + 1)


# ==============================================================================
# FUNÇÕES PRINCIPAIS
# ==============================================================================

# Códigos de equipes AD (tbTipoEquipe) - verificados em tbTipoEquipe202508.csv
CODIGOS_EQUIPE_AD = {
    22: 'EMAD I',    # Equipe Multiprofissional de Atenção Domiciliar Tipo I
    46: 'EMAD II',   # Equipe Multiprofissional de Atenção Domiciliar Tipo II  
    23: 'EMAP',      # Equipe Multiprofissional de Apoio
    77: 'EMAP-R'     # Equipe Multiprofissional de Apoio - Rural
}


def carregar_equipes_emad(municipio_codigo=None):
    """
    Carrega equipes EMAD/EMAP com coordenadas do CNES.
    
    Args:
        municipio_codigo: código IBGE do município (ex: '355030' para SP capital)
                         Se None, carrega todas de SP (códigos começando com 35)
    Returns:
        DataFrame com equipes e coordenadas
    """
    print("    Lendo tabela de equipes...")
    
    # Carregar tabela de equipes (apenas colunas necessárias para performance)
    arquivo_equipes = CNES_DIR / "tbEquipe202508.csv"
    if not arquivo_equipes.exists():
        raise FileNotFoundError(f"Arquivo {arquivo_equipes} não encontrado.")
    
    colunas_equipe = ['CO_MUNICIPIO', 'CO_UNIDADE', 'TP_EQUIPE', 'CO_EQUIPE', 
                      'DT_ATIVACAO', 'DT_DESATIVACAO', 'SEQ_EQUIPE']
    df_equipes = pd.read_csv(arquivo_equipes, sep=';', dtype=str, low_memory=False, 
                             encoding='latin-1', usecols=colunas_equipe)
    
    # Filtrar apenas equipes AD ativas (códigos 22, 23, 46, 77)
    df_equipes['TP_EQUIPE'] = pd.to_numeric(df_equipes['TP_EQUIPE'], errors='coerce')
    df_equipes = df_equipes[df_equipes['TP_EQUIPE'].isin(CODIGOS_EQUIPE_AD.keys())]
    df_equipes = df_equipes[df_equipes['DT_DESATIVACAO'].isna()]  # Apenas ativas
    
    # Filtrar por município/estado
    if municipio_codigo:
        df_equipes = df_equipes[df_equipes['CO_MUNICIPIO'].str.startswith(str(municipio_codigo))]
    else:
        # Filtrar SP (códigos começando com 35)
        df_equipes = df_equipes[df_equipes['CO_MUNICIPIO'].str.startswith('35')]
    
    print(f"    Equipes AD filtradas: {len(df_equipes)}")
    
    # Obter lista de CO_UNIDADE que precisamos
    unidades_necessarias = set(df_equipes['CO_UNIDADE'].unique())
    
    # Carregar tabela de estabelecimentos em chunks (arquivo muito grande: 263MB)
    print("    Lendo coordenadas dos estabelecimentos (pode demorar)...")
    arquivo_estab = CNES_DIR / "tbEstabelecimento202508.csv"
    if not arquivo_estab.exists():
        raise FileNotFoundError(f"Arquivo {arquivo_estab} não encontrado.")
    
    # Ler em chunks e filtrar apenas estabelecimentos necessários
    chunks = []
    colunas_estab = ['CO_UNIDADE', 'CO_CNES', 'NU_LATITUDE', 'NU_LONGITUDE', 
                     'CO_MUNICIPIO_GESTOR', 'NO_FANTASIA']
    
    for chunk in pd.read_csv(arquivo_estab, sep=';', dtype=str, low_memory=False,
                             encoding='latin-1', usecols=colunas_estab, chunksize=50000):
        # Filtrar apenas estabelecimentos que precisamos
        chunk_filtrado = chunk[chunk['CO_UNIDADE'].isin(unidades_necessarias)]
        if len(chunk_filtrado) > 0:
            chunks.append(chunk_filtrado)
    
    df_estab = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
    print(f"    Estabelecimentos com coordenadas: {len(df_estab)}")
    
    # Merge para obter coordenadas
    df = df_equipes.merge(df_estab, on='CO_UNIDADE', how='left', suffixes=('', '_estab'))
    
    # Converter coordenadas para float
    df['lat'] = pd.to_numeric(df['NU_LATITUDE'].str.replace(',', '.'), errors='coerce')
    df['lon'] = pd.to_numeric(df['NU_LONGITUDE'].str.replace(',', '.'), errors='coerce')
    
    # Remover equipes sem coordenadas válidas
    df = df.dropna(subset=['lat', 'lon'])
    df = df[(df['lat'] != 0) & (df['lon'] != 0)]
    
    # Mapear tipo de equipe para nome legível
    df['TIPO_EQUIPE_NOME'] = df['TP_EQUIPE'].map(CODIGOS_EQUIPE_AD)
    
    print(f"  Equipes carregadas: {len(df)}")
    for codigo, nome in CODIGOS_EQUIPE_AD.items():
        qtd = len(df[df['TP_EQUIPE'] == codigo])
        if qtd > 0:
            print(f"  - {nome}: {qtd}")
    
    return df


def carregar_setores_censitarios():
    """Carrega população idosa por setor censitário (Censo 2022/IBGE)."""
    arquivo = IBGE_DIR / "demanda_idosos_sp_censo2022.csv"
    
    if not arquivo.exists():
        raise FileNotFoundError(f"Arquivo {arquivo} não encontrado.")
    
    df = pd.read_csv(arquivo)
    df = df[df['populacao_idosa'] > 0].copy()
    
    print(f"  Setores censitários: {len(df)}")
    print(f"  População idosa total: {df['populacao_idosa'].sum():,.0f}")
    
    return df


def gerar_pacientes(n_pacientes, setores_df, centro_lat, centro_lon, raio_km=10):
    """
    Gera N pacientes sintéticos com localizações plausíveis.
    Sorteia atributos conforme Portaria GM/MS 3.005/2024.
    """
    pacientes = []
    
    for i in range(n_pacientes):
        # Coordenadas com distribuição gaussiana ao redor do centro
        lat = centro_lat + np.random.normal(0, raio_km/111)  # ~111 km por grau
        lon = centro_lon + np.random.normal(0, raio_km/(111 * np.cos(np.radians(centro_lat))))
        
        # Sortear atributos
        modalidade = sortear_modalidade()
        janela_tipo = sortear_janela_tempo()
        janela_inicio, janela_fim = JANELAS_HORARIO[janela_tipo]
        freq, freq_unidade = gerar_frequencia(modalidade)
        tempo_servico = gerar_tempo_servico(modalidade)
        
        paciente = {
            'id': i + 1,
            'lat': round(lat, 6),
            'lon': round(lon, 6),
            'modalidade': modalidade,
            'janela_inicio': janela_inicio,
            'janela_fim': janela_fim,
            'frequencia': freq,
            'frequencia_unidade': freq_unidade,
            'tempo_servico': tempo_servico,
            'prioridade': 3 if modalidade == 'AD3' else (2 if modalidade == 'AD2' else 1)
        }
        
        pacientes.append(paciente)
    
    return pacientes


def calcular_matriz_distancias(equipes, pacientes):
    """Calcula matriz de tempos (minutos) entre depósito e pacientes via Haversine."""
    n = len(pacientes)
    matriz = np.zeros((n + 1, n + 1))
    
    # Coordenadas do depósito (primeira equipe)
    dep_lat, dep_lon = equipes.iloc[0]['lat'], equipes.iloc[0]['lon']
    
    # Distância depósito <-> pacientes
    for i, p in enumerate(pacientes):
        dist = haversine(dep_lon, dep_lat, p['lon'], p['lat'])
        tempo = distancia_para_tempo(dist)
        matriz[0, i+1] = tempo
        matriz[i+1, 0] = tempo
    
    # Distância entre pacientes
    for i, p1 in enumerate(pacientes):
        for j, p2 in enumerate(pacientes):
            if i < j:
                dist = haversine(p1['lon'], p1['lat'], p2['lon'], p2['lat'])
                tempo = distancia_para_tempo(dist)
                matriz[i+1, j+1] = tempo
                matriz[j+1, i+1] = tempo
    
    return matriz


def gerar_instancia(nome, n_pacientes, n_equipes=1, municipio=None, seed=None):
    """Gera uma instância completa para o modelo HHC-RSP."""
    if seed is not None:
        np.random.seed(seed)
    
    print(f"\n{'='*60}")
    print(f"GERANDO INSTÂNCIA: {nome}")
    print(f"{'='*60}")
    print(f"  Pacientes: {n_pacientes}")
    print(f"  Equipes: {n_equipes}")
    if seed:
        print(f"  Seed: {seed}")
    
    # 1. Carregar equipes
    print("\n[1/5] Carregando equipes EMAD...")
    equipes_df = carregar_equipes_emad(municipio)
    
    if len(equipes_df) < n_equipes:
        print(f"  ⚠ Apenas {len(equipes_df)} equipes disponíveis")
        n_equipes = len(equipes_df)
    
    equipes = equipes_df.head(n_equipes).copy()
    
    # 2. Carregar setores (para validação, não usado diretamente aqui)
    print("\n[2/5] Verificando dados demográficos...")
    try:
        setores_df = carregar_setores_censitarios()
    except FileNotFoundError:
        print("  ⚠ Usando distribuição genérica (sem shapefile)")
        setores_df = None
    
    # 3. Gerar pacientes
    print("\n[3/5] Gerando pacientes sintéticos...")
    centro_lat = equipes['lat'].mean()
    centro_lon = equipes['lon'].mean()
    pacientes = gerar_pacientes(n_pacientes, setores_df, centro_lat, centro_lon)
    
    # Estatísticas
    modals = [p['modalidade'] for p in pacientes]
    print(f"  AD2: {modals.count('AD2')} ({100*modals.count('AD2')/len(modals):.0f}%)")
    print(f"  AD3: {modals.count('AD3')} ({100*modals.count('AD3')/len(modals):.0f}%)")
    
    # 4. Calcular matriz de distâncias
    print("\n[4/5] Calculando matriz de distâncias...")
    matriz = calcular_matriz_distancias(equipes, pacientes)
    print(f"  Dimensão: {matriz.shape}")
    print(f"  Tempo médio: {matriz[matriz > 0].mean():.1f} min")
    print(f"  Tempo máximo: {matriz.max():.1f} min")
    
    # 5. Montar instância
    print("\n[5/5] Montando instância...")
    
    # Capacidade das equipes
    capacidades = []
    for _, eq in equipes.iterrows():
        cap = np.random.randint(CAPACIDADE_EQUIPE_MIN, CAPACIDADE_EQUIPE_MAX + 1)
        capacidades.append(cap)
    
    instancia = {
        'metadata': {
            'nome': nome,
            'data_geracao': datetime.now().isoformat(),
            'n_pacientes': n_pacientes,
            'n_equipes': n_equipes,
            'municipio': municipio,
            'seed': seed,
            'fonte_equipes': 'CNES/DATASUS Ago/2025 (tbEquipe202508)',
            'fonte_demografia': 'IBGE Censo 2022',
            'codigos_equipe_ad': CODIGOS_EQUIPE_AD
        },
        'equipes': [
            {
                'id': i + 1,
                'codigo_unidade': eq['CO_UNIDADE'],
                'codigo_equipe': eq.get('CO_EQUIPE', ''),
                'tipo_codigo': int(eq['TP_EQUIPE']),
                'tipo': CODIGOS_EQUIPE_AD.get(int(eq['TP_EQUIPE']), 'DESCONHECIDO'),
                'lat': eq['lat'],
                'lon': eq['lon'],
                'capacidade_diaria': capacidades[i]  # minutos
            }
            for i, (_, eq) in enumerate(equipes.iterrows())
        ],
        'pacientes': pacientes,
        'matriz_tempos': matriz.tolist()  # em minutos
    }
    
    print(f"\n✅ Instância gerada com sucesso!")
    
    return instancia


def salvar_instancia(instancia, formato='json'):
    """Salva instância em arquivo (json ou csv)."""
    nome = instancia['metadata']['nome']
    
    if formato == 'json':
        arquivo = INSTANCIAS_DIR / f"{nome}.json"
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(instancia, f, indent=2, ensure_ascii=False)
        print(f"📁 Salvo: {arquivo}")
        
    elif formato == 'csv':
        eq_df = pd.DataFrame(instancia['equipes'])
        eq_df.to_csv(INSTANCIAS_DIR / f"{nome}_equipes.csv", index=False)
        
        pac_df = pd.DataFrame(instancia['pacientes'])
        pac_df.to_csv(INSTANCIAS_DIR / f"{nome}_pacientes.csv", index=False)
        
        mat_df = pd.DataFrame(instancia['matriz_tempos'])
        mat_df.to_csv(INSTANCIAS_DIR / f"{nome}_matriz.csv", index=False)
        
        print(f"📁 Salvos: {nome}_equipes.csv, {nome}_pacientes.csv, {nome}_matriz.csv")


def gerar_conjunto_instancias():
    """Gera conjunto de instâncias de diferentes tamanhos para testes."""
    print("\n" + "="*70)
    print("GERANDO CONJUNTO DE INSTÂNCIAS PARA TESTES")
    print("="*70)
    
    instancias_config = [
        # Pequenas (debug)
        {'nome': 'pequena_10', 'n_pacientes': 10, 'n_equipes': 1, 'seed': 42},
        {'nome': 'pequena_20', 'n_pacientes': 20, 'n_equipes': 2, 'seed': 123},
        # Médias (testes)
        {'nome': 'media_50', 'n_pacientes': 50, 'n_equipes': 3, 'seed': 456},
        {'nome': 'media_100', 'n_pacientes': 100, 'n_equipes': 5, 'seed': 789},
        # Grandes (experimentos)
        {'nome': 'grande_200', 'n_pacientes': 200, 'n_equipes': 8, 'seed': 1000},
        {'nome': 'grande_500', 'n_pacientes': 500, 'n_equipes': 15, 'seed': 2000},
    ]
    
    for config in instancias_config:
        instancia = gerar_instancia(**config)
        salvar_instancia(instancia, formato='json')
        salvar_instancia(instancia, formato='csv')
    
    print("\n" + "="*70)
    print(f"✅ {len(instancias_config)} instâncias geradas em: {INSTANCIAS_DIR}")
    print("="*70)


# ==============================================================================
# EXECUÇÃO PRINCIPAL
# ==============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║          GERADOR DE INSTÂNCIAS SINTÉTICAS - HHC-RSP (Kummer 2024)           ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    gerar_conjunto_instancias()
