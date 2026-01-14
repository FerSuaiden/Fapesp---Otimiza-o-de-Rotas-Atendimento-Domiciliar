#!/usr/bin/env python3
"""
Visualizacao Temporal da Conformidade Legal - Equipes AD Estado de SP

Analisa: quantas equipes e municipios tem equipes CONFORMES com a
Portaria 3.005/2024 ao longo do tempo.

Usa o resultado ja calculado em conformidade_legal_sp_estado.csv
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

# Configuracao
BASE_DIR = '/home/fersuaiden/Área de trabalho/Faculdade/IC'
CNES_DIR = os.path.join(BASE_DIR, 'CNES_DATA')
OUTPUT_DIR = os.path.join(BASE_DIR, 'Outputs&Codigo/PARTE4')

TIPOS_EQUIPE_AD = {
    22: 'EMAD I',
    46: 'EMAD II',
    23: 'EMAP',
    77: 'EMAP-R',
}


def main():
    print("=" * 70)
    print("EVOLUCAO TEMPORAL DA CONFORMIDADE LEGAL")
    print("Portaria GM/MS 3.005/2024")
    print("=" * 70)
    
    # 1. Carregar resultado de conformidade ja calculado
    print("\n[1] Carregando resultado de conformidade...")
    df_conformidade = pd.read_csv(
        os.path.join(OUTPUT_DIR, "conformidade_legal_sp_estado.csv"),
        sep=';'
    )
    print(f"    Equipes com conformidade calculada: {len(df_conformidade)}")
    
    # Criar dicionario de conformidade
    conformidade_por_seq = dict(zip(df_conformidade['SEQ_EQUIPE'], df_conformidade['CONFORME']))
    
    # 2. Carregar equipes AD de SP com datas
    print("\n[2] Carregando equipes AD do estado de SP...")
    df_equipes = pd.read_csv(
        os.path.join(CNES_DIR, "tbEquipe202508.csv"),
        sep=';', encoding='latin-1', low_memory=False
    )
    
    df_equipes['CO_MUN_STR'] = df_equipes['CO_MUNICIPIO'].astype(str)
    df_equipes_sp = df_equipes[df_equipes['CO_MUN_STR'].str.startswith('35')].copy()
    df_equipes_ad = df_equipes_sp[df_equipes_sp['TP_EQUIPE'].isin(TIPOS_EQUIPE_AD.keys())].copy()
    
    # Converter datas
    df_equipes_ad['DT_ATIVACAO'] = pd.to_datetime(
        df_equipes_ad['DT_ATIVACAO'], format='%d/%m/%Y', errors='coerce')
    df_equipes_ad['DT_DESATIVACAO'] = pd.to_datetime(
        df_equipes_ad['DT_DESATIVACAO'], format='%d/%m/%Y', errors='coerce')
    
    print(f"    Total equipes AD SP (historico): {len(df_equipes_ad)}")
    
    # Mapear conformidade (equipes desativadas = nao avaliadas, assumir False)
    df_equipes_ad['CONFORME'] = df_equipes_ad['SEQ_EQUIPE'].map(conformidade_por_seq).fillna(False)
    
    n_conformes_atual = df_equipes_ad[df_equipes_ad['DT_DESATIVACAO'].isna()]['CONFORME'].sum()
    print(f"    Equipes ativas conformes: {n_conformes_atual}")
    
    # 3. Calcular evolucao temporal
    print("\n[3] Calculando evolucao temporal...")
    
    # Periodo: 2011 (inicio Melhor em Casa) ate agosto 2025
    data_inicio = datetime(2011, 1, 1)
    data_fim = datetime(2025, 8, 31)
    meses = pd.date_range(start=data_inicio, end=data_fim, freq='MS')
    
    evolucao = []
    
    for mes in meses:
        fim_mes = mes + pd.offsets.MonthEnd(0)
        
        # Equipes ativas no mes
        ativas = df_equipes_ad[
            (df_equipes_ad['DT_ATIVACAO'] <= fim_mes) &
            ((df_equipes_ad['DT_DESATIVACAO'].isna()) | (df_equipes_ad['DT_DESATIVACAO'] > fim_mes))
        ]
        
        # Equipes conformes (usando estado atual de profissionais)
        conformes = ativas[ativas['CONFORME'] == True]
        
        # Municipios com pelo menos 1 equipe conforme
        mun_conformes = conformes['CO_MUNICIPIO'].nunique()
        mun_total = ativas['CO_MUNICIPIO'].nunique()
        
        evolucao.append({
            'data': mes,
            'total_equipes': len(ativas),
            'equipes_conformes': len(conformes),
            'taxa_conformidade': len(conformes) / len(ativas) * 100 if len(ativas) > 0 else 0,
            'municipios_total': mun_total,
            'municipios_conformes': mun_conformes,
        })
    
    df_evolucao = pd.DataFrame(evolucao)
    
    # 4. Gerar visualizacao
    print("\n[4] Gerando visualizacao...")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Evolucao da Conformidade Legal (Portaria 3.005/2024)\nEstado de Sao Paulo',
                 fontsize=14, fontweight='bold')
    
    # Grafico 1: Total de equipes vs conformes
    ax1 = axes[0, 0]
    ax1.fill_between(df_evolucao['data'], df_evolucao['total_equipes'], alpha=0.3, color='#3498db', label='Total')
    ax1.fill_between(df_evolucao['data'], df_evolucao['equipes_conformes'], alpha=0.5, color='#27ae60', label='Conformes')
    ax1.plot(df_evolucao['data'], df_evolucao['total_equipes'], linewidth=2, color='#2980b9')
    ax1.plot(df_evolucao['data'], df_evolucao['equipes_conformes'], linewidth=2, color='#1e8449')
    ax1.set_title('Equipes Ativas vs Conformes')
    ax1.set_xlabel('Ano')
    ax1.set_ylabel('Numero de Equipes')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Marcar Portaria 3.005/2024
    portaria_date = datetime(2024, 1, 5)
    ax1.axvline(portaria_date, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
    ax1.annotate('Portaria\n3.005/2024', xy=(portaria_date, ax1.get_ylim()[1]*0.85),
                fontsize=8, ha='center', color='red')
    
    # Grafico 2: Taxa de conformidade
    ax2 = axes[0, 1]
    ax2.fill_between(df_evolucao['data'], df_evolucao['taxa_conformidade'], alpha=0.3, color='#9b59b6')
    ax2.plot(df_evolucao['data'], df_evolucao['taxa_conformidade'], linewidth=2, color='#8e44ad')
    ax2.set_title('Taxa de Conformidade ao Longo do Tempo')
    ax2.set_xlabel('Ano')
    ax2.set_ylabel('Taxa de Conformidade (%)')
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3)
    ax2.axvline(portaria_date, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
    
    # Valor atual
    ultimo = df_evolucao.iloc[-1]
    ax2.annotate(f'{ultimo["taxa_conformidade"]:.1f}%', 
                xy=(ultimo['data'], ultimo['taxa_conformidade']),
                xytext=(10, 10), textcoords='offset points',
                fontsize=10, fontweight='bold')
    
    # Grafico 3: Municipios total vs com equipes conformes
    ax3 = axes[1, 0]
    ax3.fill_between(df_evolucao['data'], df_evolucao['municipios_total'], alpha=0.3, color='#e67e22', label='Com AD')
    ax3.fill_between(df_evolucao['data'], df_evolucao['municipios_conformes'], alpha=0.5, color='#27ae60', label='Com Equipe Conforme')
    ax3.plot(df_evolucao['data'], df_evolucao['municipios_total'], linewidth=2, color='#d35400')
    ax3.plot(df_evolucao['data'], df_evolucao['municipios_conformes'], linewidth=2, color='#1e8449')
    ax3.set_title('Municipios com Cobertura AD')
    ax3.set_xlabel('Ano')
    ax3.set_ylabel('Numero de Municipios')
    ax3.legend(loc='upper left')
    ax3.grid(True, alpha=0.3)
    ax3.axvline(portaria_date, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
    
    # Grafico 4: Tabela resumo
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # Dados para tabela
    anos_ref = [2015, 2020, 2024, 2025]
    dados_tabela = []
    for ano in anos_ref:
        rows_ano = df_evolucao[df_evolucao['data'].dt.year == ano]
        if len(rows_ano) > 0:
            row = rows_ano.iloc[-1]
            dados_tabela.append([
                str(ano),
                f"{int(row['total_equipes'])}",
                f"{int(row['equipes_conformes'])}",
                f"{row['taxa_conformidade']:.1f}%",
                f"{int(row['municipios_total'])}",
                f"{int(row['municipios_conformes'])}"
            ])
    
    tabela = ax4.table(
        cellText=dados_tabela,
        colLabels=['Ano', 'Total', 'Conformes', 'Taxa', 'Mun. AD', 'Mun. Conf.'],
        loc='center',
        cellLoc='center'
    )
    tabela.auto_set_font_size(False)
    tabela.set_fontsize(10)
    tabela.scale(1.2, 1.8)
    
    # Colorir header
    for i in range(6):
        tabela[(0, i)].set_facecolor('#3498db')
        tabela[(0, i)].set_text_props(color='white', fontweight='bold')
    
    ax4.set_title('Resumo por Ano', fontsize=11, pad=20)
    
    # Nota explicativa
    fig.text(0.5, 0.02, 
             'NOTA: Conformidade calculada com composicao atual de profissionais (Ago/2025). '
             'A Portaria 3.005/2024 entrou em vigor em janeiro/2024.',
             ha='center', fontsize=9, style='italic', color='gray')
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    
    output_file = os.path.join(OUTPUT_DIR, 'evolucao_conformidade_temporal.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"\n    Grafico salvo em: {output_file}")
    
    # 5. Salvar dados
    output_csv = os.path.join(OUTPUT_DIR, 'evolucao_conformidade_temporal.csv')
    df_evolucao.to_csv(output_csv, index=False)
    print(f"    Dados salvos em: {output_csv}")
    
    # Resumo final
    print("\n" + "=" * 70)
    print("RESUMO - CONFORMIDADE ATUAL (Ago/2025)")
    print("=" * 70)
    print(f"  Equipes ativas: {int(ultimo['total_equipes'])}")
    print(f"  Equipes conformes: {int(ultimo['equipes_conformes'])}")
    print(f"  Taxa de conformidade: {ultimo['taxa_conformidade']:.1f}%")
    print(f"  Municipios com AD: {int(ultimo['municipios_total'])}")
    print(f"  Municipios com equipe conforme: {int(ultimo['municipios_conformes'])}")


if __name__ == "__main__":
    main()