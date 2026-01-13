"""
DEMANDA CORRIGIDA DE ATENÇÃO DOMICILIAR - METODOLOGIA APRIMORADA
=================================================================

Este script aplica uma metodologia mais realista para estimar a demanda
de Atenção Domiciliar, corrigindo as limitações do script anterior.

CORREÇÕES METODOLÓGICAS:
========================
1. TAXA DE ELEGIBILIDADE: Aplica taxa epidemiológica de literatura
   (2-5% dos idosos precisam de AD, não 100%)

2. PONDERAÇÃO POR IDADE: Idosos mais velhos (70+) têm peso maior
   que idosos mais jovens (60-69)

3. CENÁRIOS: Gera 3 cenários (conservador, moderado, otimista)
   para análise de sensibilidade

LIMITAÇÕES RECONHECIDAS:
========================
- Não temos dados de 80+ ou 90+ separados (IBGE só fornece 70+)
- Idealmente usaríamos dados de produção real (SIA/SISAB)
- A taxa de elegibilidade é uma estimativa baseada em literatura

REFERÊNCIAS:
============
- Portaria GM/MS 825/2016 - Critérios de elegibilidade para AD
- IBGE Censo 2022 - Agregados por Setores Censitários
- Literatura internacional sobre Home Health Care (ver README)

Autor: Análise Exploratória - IC FAPESP
Data: 2025
"""

import pandas as pd
import geopandas as gpd
import os
import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import numpy as np

# Configurações
IBGE_DIR = "../../IBGE_DATA"
OUTPUT_DIR = "."

# =============================================================================
# PARÂMETROS METODOLÓGICOS
# =============================================================================

# Taxa de elegibilidade para AD (% dos idosos que precisam de cuidados domiciliares)
# Baseado em literatura internacional e brasileira
TAXAS_ELEGIBILIDADE = {
    'conservador': 0.02,   # 2% - limite inferior
    'moderado': 0.035,     # 3.5% - estimativa central
    'otimista': 0.05       # 5% - limite superior (maior demanda)
}

# Pesos por faixa etária (reflete maior necessidade de AD com a idade)
# Baseado em curva exponencial de dependência funcional
PESOS_IDADE = {
    '60_69': 1.0,   # Referência
    '70_mais': 2.5  # 70+ tem 2.5x mais probabilidade de precisar de AD
}


def carregar_dados_existentes():
    """Carrega os dados já processados do script anterior."""
    
    print("\n[1/4] CARREGANDO DADOS DO CENSO 2022")
    print("="*60)
    
    # Verificar se dados já existem
    csv_path = os.path.join(IBGE_DIR, "demanda_idosos_sp_censo2022.csv")
    
    if not os.path.exists(csv_path):
        print("  ⚠ Dados não encontrados. Execute primeiro 10-demanda_censo2022_real.py")
        return None, None
    
    # Carregar CSV - forçar CD_setor como string para evitar problemas de tipo
    df = pd.read_csv(csv_path, dtype={'CD_setor': str})
    # Remover .0 se houver (caso CSV tenha sido salvo com float)
    df['CD_setor'] = df['CD_setor'].str.replace(r'\.0$', '', regex=True)
    print(f"  ✓ Dados carregados: {len(df):,} setores")
    
    # Carregar GeoJSON para mapa
    geojson_path = os.path.join(IBGE_DIR, "demanda_idosos_sp_censo2022.geojson")
    gdf = gpd.read_file(geojson_path)
    # Garantir que CD_setor é string
    gdf['CD_setor'] = gdf['CD_setor'].astype(str)
    print(f"  ✓ Geometrias carregadas: {len(gdf):,} setores")
    
    return df, gdf


def calcular_demanda_ponderada(df):
    """
    Calcula demanda de AD com ponderação por idade e taxa de elegibilidade.
    
    Fórmula:
    Demanda_Ponderada = (pop_60_69 × peso_60_69 + pop_70_mais × peso_70_mais) × taxa_elegibilidade
    """
    
    print("\n[2/4] CALCULANDO DEMANDA PONDERADA")
    print("="*60)
    
    # Calcular demanda bruta ponderada (sem taxa de elegibilidade)
    df['demanda_bruta_ponderada'] = (
        df['pop_60_69'] * PESOS_IDADE['60_69'] + 
        df['pop_70_mais'] * PESOS_IDADE['70_mais']
    )
    
    # Calcular demanda para cada cenário
    for cenario, taxa in TAXAS_ELEGIBILIDADE.items():
        col_name = f'demanda_{cenario}'
        df[col_name] = df['demanda_bruta_ponderada'] * taxa
    
    # Estatísticas
    print(f"\n  COMPARAÇÃO METODOLÓGICA:")
    print(f"  {'-'*56}")
    print(f"  {'Método':<30} {'Demanda Total':>15}")
    print(f"  {'-'*56}")
    
    # Método original (100% dos idosos)
    demanda_original = df['populacao_idosa'].sum()
    print(f"  {'Script original (100%)':<30} {demanda_original:>15,.0f}")
    
    # Método corrigido - cenários
    for cenario, taxa in TAXAS_ELEGIBILIDADE.items():
        col = f'demanda_{cenario}'
        demanda = df[col].sum()
        print(f"  {f'Corrigido - {cenario} ({taxa*100:.1f}%)':<30} {demanda:>15,.0f}")
    
    print(f"  {'-'*56}")
    
    # Fator de correção
    demanda_moderada = df['demanda_moderado'].sum()
    fator = demanda_original / demanda_moderada
    print(f"\n  ⚠ O método original SUPERESTIMA em {fator:.1f}x")
    
    return df


def gerar_grafico_comparativo(df):
    """Gera gráfico comparando metodologias."""
    
    print("\n[3/4] GERANDO VISUALIZAÇÃO COMPARATIVA")
    print("="*60)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Gráfico 1: Comparação de totais
    ax1 = axes[0]
    
    metodos = ['Original\n(100%)', 'Conservador\n(2%)', 'Moderado\n(3.5%)', 'Otimista\n(5%)']
    valores = [
        df['populacao_idosa'].sum(),
        df['demanda_conservador'].sum(),
        df['demanda_moderado'].sum(),
        df['demanda_otimista'].sum()
    ]
    cores = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
    
    bars = ax1.bar(metodos, valores, color=cores, edgecolor='black', linewidth=1)
    
    # Adicionar valores nas barras
    for bar, valor in zip(bars, valores):
        height = bar.get_height()
        ax1.annotate(f'{valor:,.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax1.set_ylabel('Demanda Estimada (pacientes)', fontsize=12)
    ax1.set_title('Comparação de Metodologias\nEstimativa de Demanda para Atenção Domiciliar', 
                  fontsize=13, fontweight='bold')
    ax1.set_ylim(0, max(valores) * 1.15)
    
    # Adicionar linha de referência
    ax1.axhline(y=valores[2], color='gray', linestyle='--', alpha=0.5, label='Cenário Moderado')
    
    # Gráfico 2: Composição da demanda ponderada
    ax2 = axes[1]
    
    # Contribuição por faixa etária (cenário moderado)
    contrib_60_69 = df['pop_60_69'].sum() * PESOS_IDADE['60_69'] * TAXAS_ELEGIBILIDADE['moderado']
    contrib_70_mais = df['pop_70_mais'].sum() * PESOS_IDADE['70_mais'] * TAXAS_ELEGIBILIDADE['moderado']
    
    labels = ['60-69 anos\n(peso 1.0)', '70+ anos\n(peso 2.5)']
    sizes = [contrib_60_69, contrib_70_mais]
    colors = ['#a8e6cf', '#ff8b94']
    explode = (0, 0.05)
    
    wedges, texts, autotexts = ax2.pie(sizes, labels=labels, colors=colors,
                                       autopct=lambda p: f'{p:.1f}%\n({int(p*sum(sizes)/100):,})',
                                       explode=explode, startangle=90,
                                       wedgeprops={'edgecolor': 'black', 'linewidth': 1})
    
    ax2.set_title('Composição da Demanda Ponderada\n(Cenário Moderado)', 
                  fontsize=13, fontweight='bold')
    
    # Adicionar nota explicativa
    fig.text(0.5, 0.02, 
             'Nota: A ponderação reflete que idosos 70+ têm ~2.5x mais probabilidade de necessitar de AD que idosos 60-69.',
             ha='center', fontsize=9, style='italic', color='gray')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)
    
    output_file = os.path.join(OUTPUT_DIR, "comparacao_metodologias_demanda.png")
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"  ✓ Gráfico salvo: {output_file}")
    
    return output_file


def gerar_mapa_calor_corrigido(gdf, df, cenario='moderado'):
    """Gera mapa de calor com demanda corrigida."""
    
    print("\n[4/4] GERANDO MAPA DE CALOR (METODOLOGIA CORRIGIDA)")
    print("="*60)
    
    col_demanda = f'demanda_{cenario}'
    
    # Merge com dados de demanda corrigida - garantir tipos compatíveis
    # Encontrar coluna de código do setor no GeoDataFrame
    col_setor_gdf = None
    for col in ['CD_setor', 'CD_SETOR', 'cd_setor']:
        if col in gdf.columns:
            col_setor_gdf = col
            break
    
    if col_setor_gdf is None:
        print("  ⚠ Não foi possível encontrar coluna de código do setor")
        return None
    
    # Garantir que ambos são strings para o merge funcionar
    gdf = gdf.copy()
    gdf[col_setor_gdf] = gdf[col_setor_gdf].astype(str)
    df = df.copy()
    df['CD_setor'] = df['CD_setor'].astype(str)
    
    # Fazer merge
    gdf_merged = gdf.merge(
        df[['CD_setor', 'demanda_conservador', 'demanda_moderado', 'demanda_otimista']],
        left_on=col_setor_gdf,
        right_on='CD_setor',
        how='left',
        suffixes=('', '_df')
    )
    
    # Preencher NaN com 0
    for col in ['demanda_conservador', 'demanda_moderado', 'demanda_otimista']:
        if col in gdf_merged.columns:
            gdf_merged[col] = gdf_merged[col].fillna(0)
    
    print(f"  Setores com demanda > 0: {(gdf_merged[col_demanda] > 0).sum():,}")
    
    # Centro de SP
    centro_sp = [-23.55, -46.63]
    
    # Criar mapa
    m = folium.Map(location=centro_sp, zoom_start=11, tiles='CartoDB positron')
    
    # Preparar dados para heatmap - usar gdf_merged que tem os dados de demanda
    heat_data = []
    gdf_valid = gdf_merged[gdf_merged[col_demanda] > 0].copy()
    
    for idx, row in gdf_valid.iterrows():
        try:
            centroid = row.geometry.centroid
            lat, lon = centroid.y, centroid.x
            weight = row[col_demanda]
            heat_data.append([lat, lon, weight])
        except:
            continue
    
    print(f"  Pontos para heatmap: {len(heat_data):,}")
    
    # Adicionar heatmap
    HeatMap(
        heat_data,
        radius=15,
        blur=10,
        max_zoom=18,
        gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}
    ).add_to(m)
    
    taxa_pct = TAXAS_ELEGIBILIDADE[cenario] * 100
    
    # Título com metodologia explicada
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 500px; 
                background-color: white; 
                border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px;
                border-radius: 5px;">
        <b>Mapa de Calor - Demanda Estimada de Atenção Domiciliar</b><br>
        <span style="font-size:12px;">
            São Paulo Capital - Censo 2022 - <b>Metodologia Corrigida</b><br>
            <hr style="margin: 5px 0;">
            <b>Cenário:</b> {cenario.capitalize()} (taxa de elegibilidade: {taxa_pct}%)<br>
            <b>Ponderação:</b> 60-69 anos (peso 1.0) | 70+ anos (peso 2.5)<br>
            <hr style="margin: 5px 0;">
            <span style="color: red;">Vermelho</span> = Alta demanda estimada<br>
            <span style="color: blue;">Azul</span> = Baixa demanda estimada
        </span>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Salvar
    output_file = os.path.join(OUTPUT_DIR, f"mapa_demanda_corrigida_{cenario}.html")
    m.save(output_file)
    print(f"  ✓ Mapa salvo: {output_file}")
    
    return m


def salvar_dados_corrigidos(df):
    """Salva dados com demanda corrigida."""
    
    print("\n[EXTRA] SALVANDO DADOS CORRIGIDOS")
    print("="*60)
    
    # Garantir que CD_setor é string para evitar problemas de tipo
    df = df.copy()
    df['CD_setor'] = df['CD_setor'].astype(str)
    
    # Selecionar colunas relevantes
    cols_export = [
        'CD_setor', 
        'populacao_total', 
        'pop_60_69', 
        'pop_70_mais', 
        'populacao_idosa',
        'demanda_bruta_ponderada',
        'demanda_conservador',
        'demanda_moderado',
        'demanda_otimista'
    ]
    
    output_csv = os.path.join(IBGE_DIR, "demanda_ad_corrigida_sp.csv")
    df[cols_export].to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"  ✓ CSV salvo: {output_csv}")
    
    return output_csv


def imprimir_resumo_final(df):
    """Imprime resumo final da análise."""
    
    print("\n" + "="*70)
    print("   RESUMO DA ANÁLISE DE DEMANDA - METODOLOGIA CORRIGIDA")
    print("="*70)
    
    pop_total = df['populacao_total'].sum()
    pop_idosa = df['populacao_idosa'].sum()
    
    print(f"\n   POPULAÇÃO DE SÃO PAULO CAPITAL (Censo 2022)")
    print(f"   - Total: {pop_total:,.0f}")
    print(f"   - Idosos 60+: {pop_idosa:,.0f} ({pop_idosa/pop_total*100:.1f}%)")
    
    print(f"\n   ESTIMATIVA DE DEMANDA PARA ATENÇÃO DOMICILIAR")
    print(f"   {'-'*50}")
    
    for cenario, taxa in TAXAS_ELEGIBILIDADE.items():
        col = f'demanda_{cenario}'
        demanda = df[col].sum()
        media_setor = df[df[col] > 0][col].mean()
        print(f"   {cenario.upper():15} Taxa {taxa*100:4.1f}% → {demanda:>10,.0f} pacientes")
        print(f"   {'':15} Média/setor: {media_setor:.1f}")
    
    print(f"\n   METODOLOGIA:")
    print(f"   - Ponderação: 60-69 anos (×1.0) | 70+ anos (×2.5)")
    print(f"   - Taxa de elegibilidade baseada em literatura")
    print(f"   - Fórmula: (pop_60_69 × 1.0 + pop_70_mais × 2.5) × taxa")
    
    print("\n" + "="*70)


def main():
    """Função principal."""
    
    print("="*70)
    print("   DEMANDA DE ATENÇÃO DOMICILIAR - METODOLOGIA CORRIGIDA")
    print("   Aplicando taxas epidemiológicas e ponderação por idade")
    print("="*70)
    
    # 1. Carregar dados
    df, gdf = carregar_dados_existentes()
    
    if df is None:
        print("\n⚠ Execute primeiro: python 10-demanda_censo2022_real.py")
        return
    
    # 2. Calcular demanda ponderada
    df = calcular_demanda_ponderada(df)
    
    # 3. Gerar visualização comparativa
    gerar_grafico_comparativo(df)
    
    # 4. Gerar mapa de calor corrigido (cenário moderado)
    gerar_mapa_calor_corrigido(gdf, df, cenario='moderado')
    
    # 5. Salvar dados
    salvar_dados_corrigidos(df)
    
    # 6. Resumo final
    imprimir_resumo_final(df)
    
    print(f"\n   Arquivos gerados:")
    print(f"   - comparacao_metodologias_demanda.png")
    print(f"   - mapa_demanda_corrigida_moderado.html")
    print(f"   - ../../IBGE_DATA/demanda_ad_corrigida_sp.csv")
    print()


if __name__ == "__main__":
    main()
