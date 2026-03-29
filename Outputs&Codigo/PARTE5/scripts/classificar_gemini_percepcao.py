#!/usr/bin/env python3
"""
Etapa 2: Classifica menções com Gemini (Foco Logístico), 
limpa dados (sem truncar) e gera rede semântica profissional.
COM CHECKPOINT, SALVAMENTO EM TEMPO REAL E PROTEÇÃO DE COTA DIÁRIA.
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
MODELOS_PREFERIDOS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]

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


class GeminiQuotaExauridaError(RuntimeError):
    """Erro para cota indisponivel (limite diário ou total)."""

class GeminiBadRequestError(RuntimeError):
    """Erro para requests invalidas (HTTP 400)."""


def carregar_env_arquivo() -> None:
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

def listar_modelos_generate_content(chave: str) -> List[str]:
    resp = requests.get(f"{GEMINI_API_BASE}?key={chave}", timeout=30)
    if resp.status_code >= 400:
        raise RuntimeError(f"Falha ao listar modelos Gemini (HTTP {resp.status_code}): {resp.text[:260]}")

    modelos = []
    for item in resp.json().get("models", []):
        metodos = item.get("supportedGenerationMethods", [])
        if "generateContent" not in metodos:
            continue
        nome = str(item.get("name", ""))
        if nome.startswith("models/"):
            nome = nome.split("/", 1)[1]
        if nome:
            modelos.append(nome)
    return modelos

def escolher_modelo(chave: str, modelo_env: str) -> str:
    modelos = listar_modelos_generate_content(chave)
    if not modelos:
        raise RuntimeError("Nenhum modelo com generateContent disponivel para a chave atual.")

    if modelo_env and modelo_env in modelos:
        return modelo_env

    for m in MODELOS_PREFERIDOS:
        if m in modelos:
            return m
    return modelos[0]

def extrair_retry_seconds(texto_erro: str, padrao: int = 60) -> int:
    match = re.search(r"retry in\s+([0-9]+(?:\.[0-9]+)?)s", texto_erro, re.IGNORECASE)
    if match:
        return max(1, int(float(match.group(1))) + 1)
    return padrao

def limpar_texto_profissional(texto: str) -> str:
    if not texto or pd.isna(texto): return ""
    texto = re.sub(r"https?://\S+|www\.\S+", " ", texto)
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    texto = re.sub(r"[^a-zA-Z\s]", " ", texto).lower()
    tokens = [t for t in texto.split() if t not in TERMOS_BANIDOS_GRAFO and len(t) > 2]
    return " ".join(tokens)

def construir_prompt_logistico(titulo: str, resumo: str) -> str:
    titulo = str(titulo)[:280]
    resumo = str(resumo)[:700]
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
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0, "response_mime_type": "application/json"}, # Ajustado para 0.0 para maior precisão de JSON
    }
    
    max_tentativas = 3
    ultimo_erro = ""
    for i in range(max_tentativas):
        try:
            resp = requests.post(url, json=payload, timeout=30)
            
            # Checagem de Rate Limit (429)
            if resp.status_code == 429:
                texto_erro = resp.text or ""
                
                # NOVO: Detecta se a cota DIÁRIA acabou, não apenas o limite por minuto
                if "limit: 0" in texto_erro.lower() or "exceeded your current quota" in texto_erro.lower() or "billing" in texto_erro.lower():
                    raise GeminiQuotaExauridaError("Quota diária esgotada. Retorne amanhã ou verifique o faturamento da conta.")
                
                ultimo_erro = f"HTTP 429: {texto_erro[:260]}"
                espera = extrair_retry_seconds(texto_erro, padrao=60)
                print(f"  [!] Cota por minuto atingida. Pausando {espera}s para tentar novamente... (Tentativa {i+1}/{max_tentativas})")
                time.sleep(espera)
                continue

            if resp.status_code == 400:
                raise GeminiBadRequestError(f"HTTP 400 BadRequest: {resp.text[:400]}")

            if resp.status_code == 403:
                raise RuntimeError(f"HTTP 403 Gemini: {resp.text[:400]}")

            if resp.status_code == 404:
                raise RuntimeError(f"HTTP 404 Modelo nao encontrado ({modelo}): {resp.text[:240]}")
            
            resp.raise_for_status()
            res_json = resp.json()
            texto_saida = res_json['candidates'][0]['content']['parts'][0]['text']
            
            match = re.search(r"\{.*\}", texto_saida, re.DOTALL)
            if not match:
                raise ValueError(f"Gemini retornou resposta sem JSON parseavel: {texto_saida[:220]}")
            return json.loads(match.group(0))
            
        except (GeminiQuotaExauridaError, GeminiBadRequestError):
            raise
        except Exception as e:
            ultimo_erro = str(e)
            print(f"  [!] Falha na tentativa {i+1}/{max_tentativas}: {ultimo_erro[:100]}")
            if i == max_tentativas - 1: raise e
            time.sleep(5)
            
    raise RuntimeError(f"Falha apos {max_tentativas} tentativas: {ultimo_erro}")

def processar_df(df_bruto: pd.DataFrame, caminho_saida: Path, sleep_padrao: float) -> pd.DataFrame:
    carregar_env_arquivo()
    chave = os.getenv("GEMINI_API_KEY")
    if not chave:
        raise RuntimeError("GEMINI_API_KEY nao encontrada no ambiente/.env")

    modelo = escolher_modelo(chave, os.getenv("GEMINI_MODEL", "").strip())
    print(f"Modelo Gemini em uso: {modelo}")
    
    resultados_em_memoria = []
    titulos_processados = set()
    
    # ---------------------------------------------------------
    # SISTEMA DE CHECKPOINT
    # ---------------------------------------------------------
    if caminho_saida.exists():
        try:
            df_existente = pd.read_csv(caminho_saida)
            # Filtra linhas válidas
            df_sucesso = df_existente[
                df_existente["sentimento"].notna() & 
                (df_existente["sentimento"] != "nao_classificado")
            ]
            titulos_processados = set(df_sucesso["titulo"].tolist())
            resultados_em_memoria = df_sucesso.to_dict('records')
            print(f"✅ Checkpoint: {len(titulos_processados)} registros já classificados carregados com sucesso.")
        except Exception as e:
            print(f"⚠️ Erro ao ler checkpoint ({e}). Processando do zero.")
    
    # Filtra o que falta
    df_pendente = df_bruto[~df_bruto["titulo"].isin(titulos_processados)]
    total_pendente = len(df_pendente)
    
    if total_pendente == 0:
        print("🎉 Todos os registros já foram processados! Nenhum consumo extra de cota necessário.")
        return pd.DataFrame(resultados_em_memoria)

    print(f"🚀 Iniciando classificação de {total_pendente} registros pendentes...\n")
    
    # ---------------------------------------------------------
    # LOOP DE PROCESSAMENTO COM SALVAMENTO EM TEMPO REAL
    # ---------------------------------------------------------
    for i, row in enumerate(df_pendente.itertuples(), 1):
        print(f"[{i}/{total_pendente}] Processando: {row.titulo[:50]}...")
        texto_limpo = limpar_texto_profissional(f"{row.titulo} {row.resumo}")

        try:
            classif = chamar_gemini_com_retry(chave, modelo, construir_prompt_logistico(row.titulo, row.resumo))
            
            estado = str(classif.get("estado", "NA")).upper()
            if estado not in UF_LISTA: estado = "NA"
            
            termos = [limpar_texto_profissional(t) for t in classif.get("termos_chave", [])]
            termos = [t for t in termos if t and t not in TERMOS_BANIDOS_GRAFO]

            novo_registro = {
                **row._asdict(),
                "sentimento": classif.get("sentimento", "neutro"),
                "estado": estado,
                "gargalo": classif.get("gargalo", "nenhum"),
                "texto_limpo": texto_limpo,
                "termos_relevantes": ", ".join(termos),
                "erro_classificacao": ""
            }
            
            # Adiciona na memória para o grafo final
            resultados_em_memoria.append(novo_registro)
            
            # Salva instantaneamente no CSV
            precisa_cabecalho = not caminho_saida.exists()
            pd.DataFrame([novo_registro]).to_csv(
                caminho_saida, mode='a', header=precisa_cabecalho, index=False, encoding="utf-8"
            )
            
        except GeminiQuotaExauridaError as e:
            print(f"\n🛑 [CRÍTICO] A cota do seu projeto esgotou: {e}")
            print("🛑 Interrompendo a execução de forma segura. O progresso até aqui já está salvo no CSV.")
            break # Interrompe o loop
            
        except Exception as e:
            print(f"  [Erro Definitivo] Pulo do registro. Falha: {str(e)[:150]}")
            
            registro_erro = {
                **row._asdict(),
                "sentimento": "nao_classificado",
                "estado": "NA",
                "gargalo": "nenhum",
                "texto_limpo": texto_limpo,
                "termos_relevantes": "",
                "erro_classificacao": str(e)
            }
            resultados_em_memoria.append(registro_erro)
            
            # Salva o erro também em tempo real
            precisa_cabecalho = not caminho_saida.exists()
            pd.DataFrame([registro_erro]).to_csv(
                caminho_saida, mode='a', header=precisa_cabecalho, index=False, encoding="utf-8"
            )

        time.sleep(sleep_padrao)
        
    return pd.DataFrame(resultados_em_memoria)

def plotar_grafo_profissional(df: pd.DataFrame, caminho: Path):
    df_validos = df[df["sentimento"] != "nao_classificado"].copy()
    if df_validos.empty: 
        print("⚠️ Sem dados válidos para plotar o grafo.")
        return

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

    remover = [n for n, d in G.degree() if d < 2]
    G.remove_nodes_from(remover)

    if G.number_of_nodes() == 0: 
        print("⚠️ Grafo vazio após poda de termos isolados.")
        return

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
    parser.add_argument("--pacing", type=float, default=6.0) 
    args = parser.parse_args()

    args.entrada = resolver_caminho(args.entrada)
    args.saida = resolver_caminho(args.saida)
    
    if not args.entrada.exists():
        print(f"Erro: Arquivo {args.entrada} não encontrado.")
        return

    df_bruto = pd.read_csv(args.entrada)
    
    # Processa (ou continua o processamento) salvando dinamicamente
    df_final = processar_df(df_bruto, args.saida, args.pacing)
    
    # Gera o Grafo com os dados consolidados da memória
    caminho_grafo = resolver_caminho(Path("Outputs&Codigo/PARTE5/visualizacoes/rede_gargalos.png"))
    plotar_grafo_profissional(df_final, caminho_grafo)
    
    print(f"\n✅ Concluído! Dados consolidados em: {args.saida}")

if __name__ == "__main__":
    main()