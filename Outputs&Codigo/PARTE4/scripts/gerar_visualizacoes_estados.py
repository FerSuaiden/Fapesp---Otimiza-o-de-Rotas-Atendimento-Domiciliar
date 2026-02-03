#!/usr/bin/env python3
"""
===============================================================================
GERADOR DE VISUALIZAÇÕES POR CIDADE PARA CADA ESTADO
===============================================================================

Para cada um dos 27 estados brasileiros, gera:
1. Top 15 cidades por número de equipes AD
2. Top 15 cidades por equipes per capita (por 100 mil hab.)

Organiza os outputs em pastas por estado.

Fontes:
- CNES/DATASUS (competência 08/2025)
- IBGE Censo 2022 (população por município)

===============================================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

BASE_DIR = '/home/fersuaiden/Área de trabalho/Faculdade/IC'
CNES_DIR = os.path.join(BASE_DIR, 'CNES_DATA')
IBGE_DIR = os.path.join(BASE_DIR, 'IBGE_DATA')
OUTPUT_DIR = os.path.join(BASE_DIR, 'Outputs&Codigo/PARTE4/visualizacoes/estados')

# Mapeamento UF
IBGE_UF_MAP = {
    '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO',
    '21': 'MA', '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL',
    '28': 'SE', '29': 'BA',
    '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
    '41': 'PR', '42': 'SC', '43': 'RS',
    '50': 'MS', '51': 'MT', '52': 'GO', '53': 'DF',
}

# Nome completo dos estados
NOME_UF = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
    'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
    'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
    'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
    'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
    'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins',
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

CORES_REGIAO = {
    'Norte': '#1abc9c', 
    'Nordeste': '#f39c12', 
    'Sudeste': '#3498db', 
    'Sul': '#27ae60', 
    'Centro-Oeste': '#9b59b6'
}

TIPOS_EQUIPE_AD = {22: 'EMAD I', 46: 'EMAD II', 23: 'EMAP', 77: 'EMAP-R'}


def extrair_uf(codigo_municipio):
    """Extrai sigla UF do código IBGE do município."""
    prefixo = str(codigo_municipio).strip()[:2]
    return IBGE_UF_MAP.get(prefixo, 'DESCONHECIDO')


def carregar_populacao_municipios():
    """
    Carrega população por município do IBGE.
    Tenta carregar arquivo existente ou usa estimativas.
    """
    arquivo_pop = os.path.join(IBGE_DIR, 'populacao_municipios_2022.csv')
    
    if os.path.exists(arquivo_pop):
        print("    Carregando população do arquivo existente...")
        df_pop = pd.read_csv(arquivo_pop, sep=';', dtype={'CO_MUNICIPIO': str})
        return df_pop
    
    # Se não existe, vamos carregar do arquivo de estabelecimentos e estimar
    # Isso é uma aproximação - idealmente deve-se baixar os dados do IBGE
    print("    AVISO: Arquivo de população não encontrado.")
    print("    Gerando estimativas baseadas em dados disponíveis...")
    
    # Carrega arquivo de municípios do IBGE se existir
    arquivo_mun = os.path.join(IBGE_DIR, 'municipios_ibge.csv')
    if os.path.exists(arquivo_mun):
        df_pop = pd.read_csv(arquivo_mun, sep=';', dtype=str)
        if 'POPULACAO' in df_pop.columns:
            return df_pop
    
    return None


def carregar_nomes_municipios():
    """Carrega nomes dos municípios do arquivo de estabelecimentos."""
    print("    Carregando nomes dos municípios...")
    
    # Tenta carregar tabela de municípios do IBGE primeiro
    arquivo_mun = os.path.join(IBGE_DIR, 'municipios_ibge.csv')
    if os.path.exists(arquivo_mun):
        df = pd.read_csv(arquivo_mun, sep=';', dtype=str)
        if 'CO_MUNICIPIO' in df.columns and 'NO_MUNICIPIO' in df.columns:
            return dict(zip(df['CO_MUNICIPIO'], df['NO_MUNICIPIO']))
    
    # Se não existir, extrair dos estabelecimentos
    df_estab = pd.read_csv(
        os.path.join(CNES_DIR, "tbEstabelecimento202508.csv"),
        sep=';', encoding='latin-1', low_memory=False,
        usecols=['CO_MUNICIPIO_GESTOR', 'NO_FANTASIA'],
        dtype=str
    )
    
    # Usar o código do município para criar um dicionário básico
    # Como não temos nome do município, usamos o código
    return {}


def main():
    print("=" * 80)
    print("GERADOR DE VISUALIZAÇÕES POR CIDADE - TODOS OS ESTADOS")
    print("=" * 80)
    
    # =========================================================================
    # ETAPA 1: CARREGAR DADOS
    # =========================================================================
    
    print("\n[1] Carregando dados...")
    
    # Equipes AD
    df_equipes = pd.read_csv(
        os.path.join(CNES_DIR, "tbEquipe202508.csv"),
        sep=';', encoding='latin-1', low_memory=False
    )
    
    df_equipes_ad = df_equipes[df_equipes['TP_EQUIPE'].isin(TIPOS_EQUIPE_AD.keys())].copy()
    df_equipes_ad['DT_DESATIVACAO'] = pd.to_datetime(
        df_equipes_ad['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce'
    )
    df_ativas = df_equipes_ad[df_equipes_ad['DT_DESATIVACAO'].isna()].copy()
    df_ativas['CO_MUNICIPIO'] = df_ativas['CO_MUNICIPIO'].astype(str)
    df_ativas['UF'] = df_ativas['CO_MUNICIPIO'].apply(extrair_uf)
    df_ativas['TIPO_NOME'] = df_ativas['TP_EQUIPE'].map(TIPOS_EQUIPE_AD)
    
    print(f"    Total de equipes AD ativas: {len(df_ativas):,}")
    
    # Carregar tabela de municípios do IBGE (se existir)
    arquivo_mun_ibge = os.path.join(IBGE_DIR, 'municipios_ibge.csv')
    df_municipios = None
    
    if os.path.exists(arquivo_mun_ibge):
        print("    Carregando tabela de municípios IBGE...")
        df_municipios = pd.read_csv(arquivo_mun_ibge, sep=';', dtype=str, encoding='utf-8')
        print(f"    Colunas encontradas: {df_municipios.columns.tolist()}")
    else:
        print(f"    AVISO: Arquivo de municípios não encontrado: {arquivo_mun_ibge}")
    
    # Carregar população dos municípios
    arquivo_pop = os.path.join(IBGE_DIR, 'populacao_municipios_2022.csv')
    df_populacao = None
    
    if os.path.exists(arquivo_pop):
        print("    Carregando população dos municípios...")
        df_populacao = pd.read_csv(arquivo_pop, sep=';', dtype=str)
        df_populacao['POPULACAO'] = pd.to_numeric(df_populacao['POPULACAO'], errors='coerce')
    else:
        print("    AVISO: Arquivo de população não encontrado. Usando estimativas.")
        # Criar estimativas baseadas no tamanho do município (por nome)
        # Isso é uma aproximação grosseira
    
    # =========================================================================
    # ETAPA 2: AGREGAR DADOS POR MUNICÍPIO
    # =========================================================================
    
    print("\n[2] Agregando dados por município...")
    
    # Contar equipes por município e tipo
    df_por_mun = df_ativas.groupby(['CO_MUNICIPIO', 'UF']).agg({
        'SEQ_EQUIPE': 'count',
        'TIPO_NOME': lambda x: ', '.join(sorted(x.unique()))
    }).reset_index()
    df_por_mun.columns = ['CO_MUNICIPIO', 'UF', 'N_EQUIPES', 'TIPOS']
    
    # Adicionar nome do município (se disponível)
    # NOTA: O IBGE usa código de 7 dígitos (com DV), CNES usa 6 dígitos (sem DV)
    # Precisamos fazer o matching pelos primeiros 6 dígitos
    if df_municipios is not None and 'CO_MUNICIPIO' in df_municipios.columns:
        # Criar código de 6 dígitos para matching
        df_municipios['CO_MUNICIPIO_6'] = df_municipios['CO_MUNICIPIO'].astype(str).str[:6]
        nome_map = dict(zip(df_municipios['CO_MUNICIPIO_6'], 
                           df_municipios['NO_MUNICIPIO']))
        df_por_mun['NO_MUNICIPIO'] = df_por_mun['CO_MUNICIPIO'].astype(str).str[:6].map(nome_map)
        print(f"    Municípios com nome identificado: {df_por_mun['NO_MUNICIPIO'].notna().sum()}")
    else:
        df_por_mun['NO_MUNICIPIO'] = df_por_mun['CO_MUNICIPIO']  # Usar código como fallback
    
    # Adicionar população (se disponível)
    if df_populacao is not None:
        pop_map = dict(zip(df_populacao['CO_MUNICIPIO'].astype(str), 
                          df_populacao['POPULACAO']))
        df_por_mun['POPULACAO'] = df_por_mun['CO_MUNICIPIO'].map(pop_map)
        df_por_mun['EQUIPES_POR_100K'] = (df_por_mun['N_EQUIPES'] / df_por_mun['POPULACAO'] * 100000).round(2)
    else:
        df_por_mun['POPULACAO'] = np.nan
        df_por_mun['EQUIPES_POR_100K'] = np.nan
    
    print(f"    Municípios com equipes AD: {len(df_por_mun):,}")
    
    # =========================================================================
    # ETAPA 3: GERAR VISUALIZAÇÕES POR ESTADO
    # =========================================================================
    
    print("\n[3] Gerando visualizações por estado...")
    
    ufs_ordenadas = sorted(df_por_mun['UF'].unique())
    print(f"    Estados a processar: {len(ufs_ordenadas)}")
    
    for uf in ufs_ordenadas:
        df_uf = df_por_mun[df_por_mun['UF'] == uf].copy()
        
        if len(df_uf) == 0:
            print(f"    {uf}: Sem dados")
            continue
        
        # Criar pasta do estado
        pasta_uf = os.path.join(OUTPUT_DIR, uf)
        os.makedirs(pasta_uf, exist_ok=True)
        
        nome_estado = NOME_UF.get(uf, uf)
        regiao = UF_REGIAO.get(uf, 'Desconhecida')
        cor_regiao = CORES_REGIAO.get(regiao, '#95a5a6')
        
        total_equipes_uf = df_uf['N_EQUIPES'].sum()
        total_municipios_uf = len(df_uf)
        
        # Decidir orientação dos gráficos: vertical se até 10, horizontal se mais
        usar_vertical = len(df_uf) <= 10
        
        # Criar figura com 1 subplot apenas (sem per capita sem dados de população)
        fig, ax1 = plt.subplots(1, 1, figsize=(14, 8) if usar_vertical else (14, 9))
        fig.suptitle(f'{nome_estado} ({uf}) - Distribuição de Equipes AD por Município\n'
                     f'Total: {total_equipes_uf} equipes em {total_municipios_uf} municípios | Região {regiao}',
                     fontsize=14, fontweight='bold', y=0.98)
        
        # ----- GRÁFICO: Por número de equipes -----
        top_bruto = df_uf.nlargest(min(15, len(df_uf)), 'N_EQUIPES')
        
        if len(top_bruto) > 0:
            # Labels: usar nome do município ou código
            labels = top_bruto['NO_MUNICIPIO'].fillna(top_bruto['CO_MUNICIPIO']).tolist()
            # Truncar nomes muito longos
            labels = [l[:20] + '...' if len(str(l)) > 23 else str(l) for l in labels]
            
            if usar_vertical:
                # GRÁFICO VERTICAL (barras em pé)
                x_pos = np.arange(len(top_bruto))
                bars = ax1.bar(x_pos, top_bruto['N_EQUIPES'], color=cor_regiao, alpha=0.85, width=0.7)
                
                ax1.set_xticks(x_pos)
                ax1.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
                ax1.set_ylabel('Número de Equipes AD')
                ax1.set_title(f'Municípios com Equipes AD em {uf}', fontsize=12, fontweight='bold')
                
                # Anotações acima das barras
                for i, (_, row) in enumerate(top_bruto.iterrows()):
                    ax1.text(i, row['N_EQUIPES'] + 0.3, f"{int(row['N_EQUIPES'])}", 
                            ha='center', fontsize=10, fontweight='bold')
                
                ax1.grid(True, alpha=0.3, axis='y')
                ax1.set_ylim(0, top_bruto['N_EQUIPES'].max() * 1.2)
            else:
                # GRÁFICO HORIZONTAL (barras deitadas)
                y_pos = np.arange(len(top_bruto))
                bars = ax1.barh(y_pos, top_bruto['N_EQUIPES'], color=cor_regiao, alpha=0.85)
                
                ax1.set_yticks(y_pos)
                ax1.set_yticklabels(labels, fontsize=9)
                ax1.invert_yaxis()
                ax1.set_xlabel('Número de Equipes AD')
                ax1.set_title(f'Top 15 Municípios com Equipes AD em {uf}', fontsize=12, fontweight='bold')
                
                # Anotações
                for i, (_, row) in enumerate(top_bruto.iterrows()):
                    ax1.text(row['N_EQUIPES'] + 0.3, i, f"{int(row['N_EQUIPES'])}", 
                            va='center', fontsize=9, fontweight='bold')
                
                ax1.grid(True, alpha=0.3, axis='x')
                ax1.set_xlim(0, top_bruto['N_EQUIPES'].max() * 1.15)
        else:
            ax1.text(0.5, 0.5, 'Sem dados', ha='center', va='center', fontsize=14)
            ax1.set_title('Municípios com Equipes AD', fontsize=11, fontweight='bold')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        fig.text(0.5, 0.01, 
                f'Fonte: CNES/DATASUS (Agosto 2025) | Programa Melhor em Casa',
                ha='center', fontsize=9, style='italic', color='gray')
        
        # Salvar
        output_file = os.path.join(pasta_uf, f'{uf}_municipios_equipes_ad.png')
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        # Salvar CSV com dados do estado
        csv_file = os.path.join(pasta_uf, f'{uf}_dados_municipios.csv')
        df_uf.to_csv(csv_file, sep=';', index=False)
        
        print(f"    {uf}: {total_municipios_uf} municípios, {total_equipes_uf} equipes → {pasta_uf}/")
    
    # =========================================================================
    # ETAPA 4: GERAR RESUMO CONSOLIDADO
    # =========================================================================
    
    print("\n[4] Gerando resumo consolidado...")
    
    # CSV com todos os municípios
    df_por_mun.to_csv(
        os.path.join(OUTPUT_DIR, 'todos_municipios_brasil.csv'), 
        sep=';', index=False
    )
    
    # Resumo por estado
    resumo_estados = df_por_mun.groupby('UF').agg({
        'N_EQUIPES': 'sum',
        'CO_MUNICIPIO': 'count'
    }).reset_index()
    resumo_estados.columns = ['UF', 'TOTAL_EQUIPES', 'MUNICIPIOS_COM_AD']
    resumo_estados['NOME_ESTADO'] = resumo_estados['UF'].map(NOME_UF)
    resumo_estados['REGIAO'] = resumo_estados['UF'].map(UF_REGIAO)
    resumo_estados = resumo_estados.sort_values('TOTAL_EQUIPES', ascending=False)
    
    resumo_estados.to_csv(
        os.path.join(OUTPUT_DIR, 'resumo_por_estado.csv'),
        sep=';', index=False
    )
    
    print(f"\n    Resumo salvo em: {OUTPUT_DIR}/resumo_por_estado.csv")
    
    # =========================================================================
    # RESUMO FINAL
    # =========================================================================
    
    print("\n" + "=" * 80)
    print("CONCLUÍDO!")
    print("=" * 80)
    print(f"""
    Visualizações geradas para {len(ufs_ordenadas)} estados.
    
    Estrutura de pastas:
    {OUTPUT_DIR}/
    ├── resumo_por_estado.csv
    ├── todos_municipios_brasil.csv
    ├── AC/
    │   ├── AC_municipios_equipes_ad.png
    │   └── AC_dados_municipios.csv
    ├── AL/
    │   ├── AL_municipios_equipes_ad.png
    │   └── AL_dados_municipios.csv
    ... (27 estados)
    └── TO/
        ├── TO_municipios_equipes_ad.png
        └── TO_dados_municipios.csv
    """)


if __name__ == '__main__':
    main()
