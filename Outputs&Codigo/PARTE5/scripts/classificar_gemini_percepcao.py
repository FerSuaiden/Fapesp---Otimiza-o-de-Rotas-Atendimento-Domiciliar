#!/usr/bin/env python3
"""
Etapa 2: Classifica menções com Gemini (Foco Logístico), 
limpa dados (sem truncar) e gera rede semântica profissional.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import requests

# Configurações de API
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
MODELOS_PREFERIDOS = ["gemini-2.0-flash", "gemini-1.5-flash"]

# Configurações de Validação
SENTIMENTOS_VALIDOS = {"positivo", "negativo", "neutro", "misto"}
GARGALOS_VALIDOS = {"frota", "pessoal", "escala", "tempo de deslocamento", "nenhum"}

# Lista de limpeza de ruído institucional e de sites
TERMOS_BANIDOS_GRAFO = {
    "atendimento", "servico", "servicos", "paciente", "pacientes", "programa", 
    "saude", "casa", "melhor", "prefeitura", "governo", "ministerio", 
    "secretaria", "unidade", "municipio", "estado", "federal", "usuarios", 
    "home", "care", "reclame", "aqui", "lista", "empresa", "visualizacoes", 
    "reclamar", "clique", "saiba", "contato", "link", "brasília", "brasil"
}

UF_LISTA = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", 
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
]

PROJETO_ROOT = Path(__file__).resolve().parents[3]

def carregar_env_arquivo() -> None:
    """Carrega chaves do .env sem dependências externas."""
    for caminho in [Path.cwd() / ".env", PROJETO_ROOT / ".env"]:
        if caminho.exists():
            with caminho.open("r", encoding="utf-8") as f:
                for linha in f:
                    linha = linha.strip()
                    if linha and not linha.startswith("#") and "=" in linha:
                        chave, valor = linha.split("=", 1)
                        os.environ[chave.strip()] = valor.strip().strip('"').strip("'")

def resolver_caminho(caminho: Path) -> Path:
    if caminho.is_absolute(): return caminho
    return (PROJETO_ROOT / caminho).resolve()

def limpar_texto_profissional(texto: str) -> str:
    """Remove acentos sem cortar palavras e limpa ruído."""
    if not texto or pd.isna(texto): return ""
    # 1. Remover URLs
    texto = re.sub(r"https?://\S+|www\.\S+", " ", texto)
    # 2. Normalizar Unicode (Transforma 'á' em 'a' em vez de apagar)
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    # 3. Limpeza de caracteres não alfabéticos
    texto = re.sub(r"[^a-zA-Z\s]", " ", texto).lower()
    # 4. Tokenização e remoção de ruído
    tokens = [t for t in texto.split() if t not in TERMOS_BANIDOS_GRAFO and len(t) > 2]
    return " ".join(tokens)

def construir_prompt_logistico(titulo: str, resumo: str) -> str:
    return f"""
Analise como especialista em logística de saúde:
Título: {titulo}
Resumo: {resumo}

Retorne APENAS um JSON:
{{
  "sentimento": "positivo|negativo|neutro|misto",
  "estado": "UF ou NA",
  "gargalo": "frota|pessoal|escala|tempo de deslocamento|nenhum",
  "termos_chave": ["substantivo_concreto_logistico1", "2", "3"]
}}

Regras Estritas:
1. 'estado': Apenas se estiver explícito. Se incerto, use "NA".
2. 'termos_chave': Apenas objetos reais (ex: ambulancia, oxigenio, medico, transito, espera). 
3. Proibido usar termos genéricos como 'atendimento' ou 'serviço'.
""".strip()

def chamar_gemini_com_retry(chave: str, modelo: str, prompt: str) -> Dict:
    url = f"{GEMINI_API_BASE}/{modelo}:generateContent?key={chave}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.1}}
    
    max_tentativas = 3
    for i in range(max_tentativas):
        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 429:
                # Se for erro de cota, espera 60s (tempo para o tier gratuito resetar)
                print(f"  [!] Cota atingida. Pausando 60s para resetar limite...")
                time.sleep(60)
                continue
            
            resp.raise_for_status()
            res_json = resp.json()
            texto_saida = res_json['candidates'][0]['content']['parts'][0]['text']
            # Extrair JSON do texto (proteção contra Markdown)
            match = re.search(r"\{.*\}", texto_saida, re.DOTALL)
            return json.loads(match.group(0))
        except Exception as e:
            if i == max_tentativas - 1: raise e
            time.sleep(5)
    return {}

def processar_df(df: pd.DataFrame, sleep_padrao: float) -> pd.DataFrame:
    carregar_env_arquivo()
    chave = os.getenv("GEMINI_API_KEY")
    modelo = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    resultados = []
    total = len(df)
    
    print(f"Iniciando classificação de {total} registros...")
    
    for i, row in enumerate(df.itertuples(), 1):
        print(f"[{i}/{total}] Processando: {row.titulo[:40]}...")
        
        texto_limpo = limpar_texto_profissional(f"{row.titulo} {row.resumo}")
        
        try:
            classif = chamar_gemini_com_retry(chave, modelo, construir_prompt_logistico(row.titulo, row.resumo))
            
            # Normalização de Saída
            estado = str(classif.get("estado", "NA")).upper()
            if estado not in UF_LISTA: estado = "NA"
            
            termos = [limpar_texto_profissional(t) for t in classif.get("termos_chave", [])]
            termos = [t for t in termos if t and t not in TERMOS_BANIDOS_GRAFO]

            resultados.append({
                **row._asdict(),
                "sentimento": classif.get("sentimento", "neutro"),
                "estado": estado,
                "gargalo": classif.get("gargalo", "nenhum"),
                "texto_limpo": texto_limpo,
                "termos_relevantes": ", ".join(termos),
                "erro_classificacao": ""
            })
        except Exception as e:
            print(f"  [Erro] Falha ao processar linha {i}: {e}")
            resultados.append({**row._asdict(), "sentimento": "nao_classificado", "erro_classificacao": str(e)})

        # Intervalo de segurança para não estourar 15 RPM (4s é seguro)
        time.sleep(sleep_padrao)
        
    return pd.DataFrame(resultados)

def plotar_grafo_profissional(df: pd.DataFrame, caminho: Path):
    df_validos = df[df["sentimento"] != "nao_classificado"].copy()
    if df_validos.empty: return

    G = nx.Graph()
    for _, row in df_validos.iterrows():
        gargalo = row['gargalo']
        if gargalo == 'nenhum': continue
        
        G.add_node(gargalo, tipo='gargalo', color='#e74c3c')
        
        termos = [t.strip() for t in str(row['termos_relevantes']).split(",") if t.strip()]
        for t in termos:
            G.add_node(t, tipo='termo', color='#2ecc71')
            if G.has_edge(gargalo, t):
                G[gargalo][t]['weight'] += 1
            else:
                G.add_edge(gargalo, t, weight=1)

    # PODA: Remove nós isolados ou com pouca relevância (Grau < 2)
    remover = [n for n, d in G.degree() if d < 2]
    G.remove_nodes_from(remover)

    if G.number_of_nodes() == 0: return

    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=1.5, seed=42)
    
    cores = [data['color'] for n, data in G.nodes(data=True)]
    pesos = [G[u][v]['weight'] for u, v in G.edges()]
    
    nx.draw_networkx_nodes(G, pos, node_color=cores, node_size=1500, alpha=0.8)
    nx.draw_networkx_edges(G, pos, width=pesos, alpha=0.4)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')
    
    plt.title("Mapa de Gargalos Logísticos - Programa Melhor em Casa", fontsize=15)
    plt.axis('off')
    plt.savefig(caminho, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--entrada", type=Path, default=Path("Outputs&Codigo/PARTE5/resultados/mencoes_serpapi_brutas.csv"))
    parser.add_argument("--saida", type=Path, default=Path("Outputs&Codigo/PARTE5/percepcao_operacional.csv"))
    parser.add_argument("--pacing", type=float, default=4.0) # 4 segundos entre chamadas
    args = parser.parse_args()

    args.entrada = resolver_caminho(args.entrada)
    args.saida = resolver_caminho(args.saida)
    
    if not args.entrada.exists():
        print(f"Erro: Arquivo {args.entrada} não encontrado.")
        return

    df_bruto = pd.read_csv(args.entrada)
    df_final = processar_df(df_bruto, args.pacing)
    
    df_final.to_csv(args.saida, index=False, encoding="utf-8")
    
    caminho_grafo = resolver_caminho(Path("Outputs&Codigo/PARTE5/visualizacoes/rede_gargalos.png"))
    plotar_grafo_profissional(df_final, caminho_grafo)
    print(f"Sucesso! CSV salvo em {args.saida} e Grafo em {caminho_grafo}")

if __name__ == "__main__":
    main()