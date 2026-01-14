#!/usr/bin/env python3
"""
===============================================================================
PARTE 3 - Script 15: Gerador de Instâncias Sintéticas para HHC-RSP
===============================================================================

IC FAPESP: Otimização de Rotas e Agendamento para Atenção Domiciliar
Candidato: Fernando Su Aiden
Orientador: Prof. Chaovalitwongse

OBJETIVO:
---------
Gerar instâncias sintéticas realísticas para testar o modelo de otimização
de rotas e agendamento de equipes de Atenção Domiciliar (BRKGA), baseado
em Kummer et al. (2024).

JUSTIFICATIVA:
--------------
Os dados públicos do DATASUS (SIA/SISAB) NÃO contêm as informações necessárias
para o modelo de otimização:
- ❌ Localização geográfica dos pacientes (só município)
- ❌ Identificação individual dos pacientes (agregado)
- ❌ Janelas de tempo preferidas
- ❌ Frequência específica de visitas

Por isso, seguindo a metodologia padrão na literatura de Home Health Care,
geramos INSTÂNCIAS SINTÉTICAS que são PLAUSÍVEIS porque:
1. Usam localização REAL das equipes EMAD (do CNES/DATASUS)
2. Distribuem pacientes proporcionalmente à população idosa (do IBGE Censo 2022)
3. Seguem perfil de demanda e tipos de AD reais (da Portaria GM/MS nº 3.005/2024)
4. Usam parâmetros de frequência baseados na legislação vigente

IMPORTANTE - O QUE É UMA "INSTÂNCIA"?
-------------------------------------
Uma INSTÂNCIA é UM problema específico para resolver. Não confundir com paciente!
- Modelo: receita genérica (equações matemáticas)
- Instância: ingredientes específicos (N pacientes, M equipes, distâncias, etc.)
Exemplo: "grande_500" = 1 instância com 500 pacientes e 15 equipes

PARÂMETROS DO MODELO (Kummer et al., 2024):
-------------------------------------------
- n: número de pacientes
- m: número de equipes
- K: capacidade diária de cada equipe (horas)
- d_ij: matriz de distâncias/tempos
- s_i: tempo de serviço em cada paciente
- [a_i, b_i]: janela de tempo de cada paciente
- f_i: frequência de visitas por semana
- q_i: qualificação necessária (AD2 ou AD3 - modalidade de Atenção Domiciliar)

FONTES DE DADOS UTILIZADAS:
---------------------------
- CNES/DATASUS: Coordenadas das equipes EMAD/EMAP (tbEquipe + tbEstabelecimento)
- IBGE Censo 2022: População idosa por setor censitário
- SIA/DATASUS: Perfil de demanda (tipos de procedimento, volumes)

COMO O GERADOR FUNCIONA:
------------------------
1. Carregar dados de equipes EMAD com coordenadas
2. Carregar dados demográficos por setor censitário
3. Para cada instância:
   a. Selecionar equipes para atender (baseado em município)
   b. Gerar N pacientes:
      - Localização: sorteio proporcional à população idosa por setor
      - Coordenadas: ponto aleatório dentro do setor
      - Modalidade: distribuição conforme Portaria 3.005/2024 (AD2 70%, AD3 30%)
      - Janela de tempo: manhã (7-12h), tarde (13-18h), integral
      - Frequência: AD2 semanal (1-3x), AD3 quase diária (5-7x)
      - Tempo de serviço: 30-60 min conforme complexidade
4. Calcular matriz de distâncias (Haversine ou OSRM)
5. Exportar em formato JSON/CSV

===============================================================================
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
SIA_DIR = BASE_DIR / "SIA_DATA"
OUTPUT_DIR = BASE_DIR / "Outputs&Codigo/PARTE3"
INSTANCIAS_DIR = OUTPUT_DIR / "instancias"

# Criar diretório de instâncias se não existir
INSTANCIAS_DIR.mkdir(exist_ok=True)

# ==============================================================================
# PARÂMETROS DE GERAÇÃO (baseados em Portaria GM/MS nº 3.005/2024 e literatura)
# ==============================================================================

# Distribuição de modalidades (conforme Art. 563-A, § 1º, inciso III da Portaria 3.005/2024)
# 
# A portaria define que, para as equipes EMAD do Programa Melhor em Casa:
# - "em torno de 70% de AD2"
# - "até 30% de AD3"
#
# NOTA: AD1 não é incluída porque:
# - AD1 é responsabilidade da Atenção Primária (ESF nos postos de saúde)
# - O modelo HHC-RSP otimiza rotas das EMAD, que atendem apenas AD2 e AD3
# - O SIA/DATASUS registra AD2 e AD3 porque são procedimentos especializados
#
DIST_MODALIDADE = {
    'AD2': 0.70,  # 70% - média complexidade (maioria das visitas EMAD)
    'AD3': 0.30   # 30% - alta complexidade (EMAD+EMAP, casos mais graves)
}

# Frequência de visitas por modalidade (Portaria GM/MS nº 3.005/2024)
#
# Conforme a legislação:
# - AD2: "cuidados multiprofissionais, transitórios e intensificados, 
#         minimamente semanais" (Art. 539)
# - AD3: "cuidados predominantemente multiprofissionais" + 
#        "equipamentos ou procedimentos de maior complexidade" (Art. 540)
#        Exemplos: ventilação mecânica, diálise, cuidados paliativos em fase final
#
# Na prática, AD3 requer visitas quase diárias (5-7x por semana)
#
FREQ_VISITAS = {
    'AD2': {'min': 1, 'max': 3, 'unidade': 'semanal'},     # 1-3x/semana
    'AD3': {'min': 5, 'max': 7, 'unidade': 'semanal'}      # 5-7x/semana (quase diário)
}

# Tempo de serviço (atendimento) em minutos
#
# Baseado na literatura e prática clínica:
# - AD2: Procedimentos de média complexidade (curativos, medicações IV, 
#        fisioterapia, troca de sondas, orientações ao cuidador)
# - AD3: Procedimentos complexos (ventilação mecânica, diálise peritoneal,
#        transfusão, cuidados paliativos intensivos)
#
# Obs: AD3 demora mais porque envolve equipamentos e múltiplos procedimentos
#
TEMPO_SERVICO = {
    'AD2': {'min': 30, 'max': 60},   # Procedimentos de média complexidade
    'AD3': {'min': 45, 'max': 90}    # Procedimentos complexos (mais tempo)
}

# Distribuição de janelas de tempo (preferência do paciente)
DIST_JANELA = {
    'manha': 0.40,      # 7:00 - 12:00
    'tarde': 0.35,      # 13:00 - 18:00
    'integral': 0.25    # 7:00 - 18:00 (flexível)
}

JANELAS_HORARIO = {
    'manha': (7*60, 12*60),      # 420 - 720 minutos
    'tarde': (13*60, 18*60),     # 780 - 1080 minutos
    'integral': (7*60, 18*60)    # 420 - 1080 minutos
}

# Capacidade diária de uma equipe EMAD (em minutos)
#
# Conforme Portaria 3.005/2024 (Art. 547), composição mínima de uma EMAD tipo I:
# - Médico(s): mínimo 40h/semana
# - Enfermeiro(s): mínimo 60h/semana
# - Técnicos de enfermagem: mínimo 120h/semana
# - Fisioterapeuta OU Assistente Social: 30h/semana
#
# Considerando que a equipe trabalha ~8h/dia útil (480 min), mas não 100%
# do tempo é atendimento direto (há deslocamentos, documentação, reuniões):
# - Tempo útil de atendimento: ~360-480 min/dia por equipe
#
CAPACIDADE_EQUIPE_MIN = 360  # minutos (6h úteis)
CAPACIDADE_EQUIPE_MAX = 480  # minutos (8h úteis)

# Velocidade média de deslocamento urbano (km/h)
VELOCIDADE_MEDIA = 25  # km/h em área urbana

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def haversine(lon1, lat1, lon2, lat2):
    """
    Calcula a distância em km entre dois pontos usando a fórmula de Haversine.
    
    A fórmula de Haversine é uma das mais usadas para calcular distâncias
    entre coordenadas geográficas na superfície de uma esfera (Terra).
    
    Parâmetros:
    - lon1, lat1: longitude e latitude do ponto 1 (em graus decimais)
    - lon2, lat2: longitude e latitude do ponto 2 (em graus decimais)
    
    Retorna:
    - Distância em quilômetros
    """
    # Converter graus para radianos
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Diferenças
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    
    # Fórmula de Haversine
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Raio da Terra em km
    r = 6371
    
    return c * r


def distancia_para_tempo(distancia_km, velocidade_kmh=VELOCIDADE_MEDIA):
    """
    Converte distância em tempo de viagem (minutos).
    
    Usa velocidade média urbana de 25 km/h, considerando:
    - Trânsito moderado
    - Paradas em semáforos
    - Velocidade típica em áreas residenciais
    """
    return (distancia_km / velocidade_kmh) * 60


def gerar_ponto_aleatorio_em_bbox(min_lat, max_lat, min_lon, max_lon):
    """
    Gera um ponto aleatório dentro de uma bounding box.
    
    Para setores censitários, usamos a bbox do setor para
    gerar coordenadas do paciente dentro do setor.
    """
    lat = np.random.uniform(min_lat, max_lat)
    lon = np.random.uniform(min_lon, max_lon)
    return lat, lon


def sortear_modalidade():
    """
    Sorteia modalidade de AD baseado na Portaria GM/MS nº 3.005/2024.
    
    Conforme Art. 563-A, § 1º, inciso III:
    - AD2: 70% (média complexidade) - maioria dos casos EMAD
    - AD3: 30% (alta complexidade) - casos graves com equipamentos
    
    NOTA: AD1 não é incluída porque é responsabilidade da Atenção Primária (ESF),
    não das equipes EMAD que estamos otimizando.
    """
    r = np.random.random()
    if r < DIST_MODALIDADE['AD2']:
        return 'AD2'
    else:
        return 'AD3'


def sortear_janela_tempo():
    """
    Sorteia janela de tempo preferida pelo paciente.
    
    Distribuição típica:
    - Manhã (40%): idosos preferem atendimento cedo
    - Tarde (35%): segunda preferência
    - Integral (25%): pacientes flexíveis
    """
    r = np.random.random()
    if r < DIST_JANELA['manha']:
        return 'manha'
    elif r < DIST_JANELA['manha'] + DIST_JANELA['tarde']:
        return 'tarde'
    else:
        return 'integral'


def gerar_frequencia(modalidade):
    """
    Gera frequência de visitas baseada na modalidade.
    
    Conforme Portaria GM/MS nº 3.005/2024:
    - AD2: 1-3 visitas por semana (Art. 539: "minimamente semanais")
    - AD3: 5-7 visitas por semana (casos graves, quase diário)
    """
    params = FREQ_VISITAS[modalidade]
    freq = np.random.randint(params['min'], params['max'] + 1)
    return freq, params['unidade']


def gerar_tempo_servico(modalidade):
    """
    Gera tempo de serviço (atendimento) baseado na modalidade.
    
    Tempos típicos estimados com base na literatura:
    - AD2: 30-60 min (curativos, medicamentos IV, fisioterapia, orientações)
    - AD3: 45-90 min (ventilação mecânica, diálise, cuidados paliativos)
    """
    params = TEMPO_SERVICO[modalidade]
    return np.random.randint(params['min'], params['max'] + 1)


# ==============================================================================
# FUNÇÕES PRINCIPAIS
# ==============================================================================

# Códigos CORRETOS das equipes de Atenção Domiciliar (tbTipoEquipe)
# Verificados em tbTipoEquipe202508.csv
CODIGOS_EQUIPE_AD = {
    22: 'EMAD I',    # Equipe Multiprofissional de Atenção Domiciliar Tipo I
    46: 'EMAD II',   # Equipe Multiprofissional de Atenção Domiciliar Tipo II  
    23: 'EMAP',      # Equipe Multiprofissional de Apoio
    77: 'EMAP-R'     # Equipe Multiprofissional de Apoio - Rural
}


def carregar_equipes_emad(municipio_codigo=None):
    """
    Carrega equipes EMAD/EMAP com coordenadas diretamente do CNES.
    
    Os dados vêm do CNES (Cadastro Nacional de Estabelecimentos de Saúde),
    cruzando tbEquipe202508.csv (cadastro de equipes) com 
    tbEstabelecimento202508.csv (coordenadas).
    
    Códigos CORRETOS de tipo de equipe AD (tbTipoEquipe):
    - 22: EMAD I (maior)
    - 46: EMAD II (menor)
    - 23: EMAP (apoio)
    - 77: EMAP-R (apoio rural)
    
    Parâmetros:
    - municipio_codigo: str, código IBGE do município (ex: '355030' para SP capital)
                       Se None, carrega todas de SP (códigos começando com 35)
    
    Retorna:
    - DataFrame com equipes e coordenadas
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
    """
    Carrega dados de população idosa por setor censitário.
    
    Os dados vêm do Censo 2022 (IBGE) e contêm:
    - CD_setor: código do setor censitário (15 dígitos)
    - populacao_total: população total do setor
    - pop_60_69: população de 60-69 anos
    - pop_70_mais: população de 70+ anos
    - populacao_idosa: total de idosos (60+)
    - proporcao_idosos: % de idosos no setor
    
    Retorna:
    - DataFrame com setores e população
    """
    arquivo = IBGE_DIR / "demanda_idosos_sp_censo2022.csv"
    
    if not arquivo.exists():
        raise FileNotFoundError(
            f"Arquivo {arquivo} não encontrado. "
            "Os dados são apenas do município de São Paulo capital."
        )
    
    df = pd.read_csv(arquivo)
    
    # Remover setores sem idosos
    df = df[df['populacao_idosa'] > 0].copy()
    
    print(f"  Setores censitários: {len(df)}")
    print(f"  População idosa total: {df['populacao_idosa'].sum():,.0f}")
    
    return df


def gerar_pacientes(n_pacientes, setores_df, centro_lat, centro_lon, raio_km=10):
    """
    Gera N pacientes sintéticos com localizações plausíveis.
    
    Metodologia:
    1. Filtra setores dentro do raio de operação
    2. Sorteia setores proporcionalmente à população idosa
    3. Para cada paciente:
       - Gera coordenadas dentro do setor
       - Atribui modalidade (AD2/AD3, conforme Portaria 3.005/2024)
       - Define janela de tempo
       - Define frequência e tempo de serviço
    
    Parâmetros:
    - n_pacientes: int, número de pacientes a gerar
    - setores_df: DataFrame com setores censitários
    - centro_lat, centro_lon: coordenadas do centro (base da equipe)
    - raio_km: float, raio máximo de operação em km
    
    Retorna:
    - Lista de dicionários com dados dos pacientes
    """
    pacientes = []
    
    # Definir bbox aproximada do setor (simplificação)
    # Em uma implementação completa, usaríamos o shapefile dos setores
    # Aqui vamos usar perturbação gaussiana a partir do centro
    
    for i in range(n_pacientes):
        # Gerar coordenadas com distribuição gaussiana ao redor do centro
        # Desvio padrão proporcional ao raio
        lat = centro_lat + np.random.normal(0, raio_km/111) # ~111 km por grau
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
            'janela_inicio': janela_inicio,  # minutos desde 00:00
            'janela_fim': janela_fim,
            'frequencia': freq,
            'frequencia_unidade': freq_unidade,
            'tempo_servico': tempo_servico,
            'prioridade': 3 if modalidade == 'AD3' else (2 if modalidade == 'AD2' else 1)
        }
        
        pacientes.append(paciente)
    
    return pacientes


def calcular_matriz_distancias(equipes, pacientes):
    """
    Calcula matriz de distâncias/tempos entre todos os nós.
    
    Nós incluem:
    - Depósito (base da equipe): índice 0
    - Pacientes: índices 1 a n
    
    A matriz é simétrica para simplificação.
    Em uma implementação real, poderia usar OSRM para tempos realistas.
    
    Parâmetros:
    - equipes: DataFrame com equipes (usamos a primeira como depósito)
    - pacientes: lista de dicts com dados dos pacientes
    
    Retorna:
    - numpy array (n+1 x n+1) com tempos em minutos
    """
    n = len(pacientes)
    matriz = np.zeros((n + 1, n + 1))
    
    # Coordenadas do depósito (primeira equipe)
    dep_lat = equipes.iloc[0]['lat']
    dep_lon = equipes.iloc[0]['lon']
    
    # Distância do depósito para cada paciente
    for i, p in enumerate(pacientes):
        dist = haversine(dep_lon, dep_lat, p['lon'], p['lat'])
        tempo = distancia_para_tempo(dist)
        matriz[0, i+1] = tempo
        matriz[i+1, 0] = tempo
    
    # Distância entre cada par de pacientes
    for i, p1 in enumerate(pacientes):
        for j, p2 in enumerate(pacientes):
            if i < j:
                dist = haversine(p1['lon'], p1['lat'], p2['lon'], p2['lat'])
                tempo = distancia_para_tempo(dist)
                matriz[i+1, j+1] = tempo
                matriz[j+1, i+1] = tempo
    
    return matriz


def gerar_instancia(nome, n_pacientes, n_equipes=1, municipio=None, seed=None):
    """
    Gera uma instância completa para o modelo HHC-RSP.
    
    Parâmetros:
    - nome: str, identificador da instância
    - n_pacientes: int, número de pacientes
    - n_equipes: int, número de equipes a considerar
    - municipio: str, código IBGE do município (opcional)
    - seed: int, semente para reprodutibilidade (opcional)
    
    Retorna:
    - dict com todos os dados da instância
    """
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
    """
    Salva instância em arquivo.
    
    Formatos suportados:
    - json: formato completo, fácil de ler
    - csv: múltiplos arquivos (equipes.csv, pacientes.csv, matriz.csv)
    """
    nome = instancia['metadata']['nome']
    
    if formato == 'json':
        arquivo = INSTANCIAS_DIR / f"{nome}.json"
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(instancia, f, indent=2, ensure_ascii=False)
        print(f"📁 Salvo: {arquivo}")
        
    elif formato == 'csv':
        # Equipes
        eq_df = pd.DataFrame(instancia['equipes'])
        eq_df.to_csv(INSTANCIAS_DIR / f"{nome}_equipes.csv", index=False)
        
        # Pacientes
        pac_df = pd.DataFrame(instancia['pacientes'])
        pac_df.to_csv(INSTANCIAS_DIR / f"{nome}_pacientes.csv", index=False)
        
        # Matriz
        mat_df = pd.DataFrame(instancia['matriz_tempos'])
        mat_df.to_csv(INSTANCIAS_DIR / f"{nome}_matriz.csv", index=False)
        
        print(f"📁 Salvos: {nome}_equipes.csv, {nome}_pacientes.csv, {nome}_matriz.csv")


def gerar_conjunto_instancias():
    """
    Gera um conjunto de instâncias de diferentes tamanhos para testes.
    
    Tamanhos:
    - Pequeno: 10-20 pacientes, 1-2 equipes (debug)
    - Médio: 50-100 pacientes, 2-4 equipes (testes)
    - Grande: 200-500 pacientes, 5-10 equipes (experimentos)
    """
    print("\n" + "="*70)
    print("GERANDO CONJUNTO DE INSTÂNCIAS PARA TESTES")
    print("="*70)
    
    instancias_config = [
        # Pequenas (para debug e validação)
        {'nome': 'pequena_10', 'n_pacientes': 10, 'n_equipes': 1, 'seed': 42},
        {'nome': 'pequena_20', 'n_pacientes': 20, 'n_equipes': 2, 'seed': 123},
        
        # Médias (para testes)
        {'nome': 'media_50', 'n_pacientes': 50, 'n_equipes': 3, 'seed': 456},
        {'nome': 'media_100', 'n_pacientes': 100, 'n_equipes': 5, 'seed': 789},
        
        # Grandes (para experimentos finais)
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
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Este gerador cria instâncias PLAUSÍVEIS para o modelo de otimização de     ║
║  rotas e agendamento de equipes de Atenção Domiciliar.                      ║
║                                                                              ║
║  FONTES DE DADOS:                                                           ║
║  • CNES/DATASUS: Localização real das equipes EMAD/EMAP                     ║
║  • IBGE Censo 2022: Distribuição demográfica (população idosa)              ║
║  • Portaria GM/MS nº 3.005/2024: Proporções AD2/AD3 e frequências           ║
║                                                                              ║
║  PARÂMETROS GERADOS:                                                        ║
║  • Localização de pacientes (coordenadas lat/lon)                           ║
║  • Modalidade de AD (AD2: 70%, AD3: 30%)                                    ║
║  • Janela de tempo preferida                                                ║
║  • Frequência de visitas                                                    ║
║  • Tempo de serviço                                                         ║
║  • Matriz de distâncias/tempos                                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Gerar conjunto de instâncias
    gerar_conjunto_instancias()
