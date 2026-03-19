#!/usr/bin/env python3
"""
===============================================================================
MONITOR DE PERCEPCAO PUBLICA - PROGRAMA MELHOR EM CASA
===============================================================================

Pipeline simples para coletar mencoes sobre um tema em saude publica e classificar
percepcao/sentimento para apresentacao.

Fluxo:
1) Coleta de resultados via SerpAPI
2) Classificacao via Gemini API (somente API)
3) Exportacao de CSV, JSON e graficos PNG

Saidas:
- Outputs&Codigo/PARTE5/dados_csv/mencoes_coletadas.csv
- Outputs&Codigo/PARTE5/dados_csv/mencoes_classificadas.csv
- Outputs&Codigo/PARTE5/resultados/resumo_opiniao.json
- Outputs&Codigo/PARTE5/visualizacoes/sentimento_barras.png
- Outputs&Codigo/PARTE5/visualizacoes/top_temas_barras.png
===============================================================================
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter
from datetime import datetime
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd
import requests

BASE_DIR = "/home/fersuaiden/Área de trabalho/Faculdade/IC"
PARTE5_DIR = os.path.join(BASE_DIR, "Outputs&Codigo", "PARTE5")
CSV_DIR = os.path.join(PARTE5_DIR, "dados_csv")
VIS_DIR = os.path.join(PARTE5_DIR, "visualizacoes")
RESULT_DIR = os.path.join(PARTE5_DIR, "resultados")

SERPAPI_URL = "https://serpapi.com/search.json"
GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Sem fallback de chave em codigo para evitar exposicao acidental.
SERPAPI_API_KEY_DEFAULT = ""
GEMINI_API_KEY_DEFAULT = ""

# Modelos Gemini com maior chance de disponibilidade no tier gratuito.
GEMINI_MODELOS_GRATUITOS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemma-3-4b-it",
    "gemma-3-12b-it",
]


def normalizar_modelo_gemini(model: str) -> str:
    model = (model or "").strip()
    return model[len("models/"):] if model.startswith("models/") else model


def garantir_dirs() -> None:
    for d in (CSV_DIR, VIS_DIR, RESULT_DIR):
        os.makedirs(d, exist_ok=True)


def queries_padrao(tema: str) -> List[str]:
    base = [
        f'"{tema}"',
        tema,
        f'{tema} SUS',
        f'{tema} pacientes',
        f'{tema} atendimento domiciliar',
        f'{tema} internação domiciliar',
        f'{tema} programa',
        f'{tema} resultados',
        f'{tema} municípios',
        f'Programa Melhor em Casa notícia',
        f'Programa Melhor em Casa prefeitura',
        f'Programa Melhor em Casa saúde',
    ]
    return base


def queries_opiniao_publica(tema: str) -> List[str]:
    return [
        f'"{tema}" reclamacoes',
        f'"{tema}" e bom?',
        f'"{tema}" depoimento paciente',
        f'"{tema}" critica',
        f'"{tema}" problema',
        f'"{tema}" avaliacao',
        f'"Melhor em Casa" reclamacoes',
        f'"Melhor em Casa" e bom?',
        f'"Melhor em Casa" depoimento paciente',
    ]


def coletar_serpapi(
    queries: List[str],
    serpapi_key: str,
    max_total: int,
    max_paginas: int,
    num_por_pagina: int,
) -> List[Dict]:
    resultados: List[Dict] = []

    for q in queries:
        if len(resultados) >= max_total:
            break

        for pagina in range(max_paginas):
            if len(resultados) >= max_total:
                break

            inicio = pagina * num_por_pagina
            params = {
                "engine": "google",
                "q": q,
                "gl": "br",
                "hl": "pt-br",
                "num": num_por_pagina,
                "start": inicio,
                "api_key": serpapi_key,
            }

            try:
                resp = requests.get(SERPAPI_URL, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                print(f"    Aviso SerpAPI web ({q}, pag {pagina + 1}): {exc}")
                break

            organicos = data.get("organic_results", [])
            if not organicos and pagina > 0:
                break

            for item in organicos:
                resultados.append(
                    {
                        "query": q,
                        "fonte_coleta": "serpapi",
                        "titulo": str(item.get("title", "")).strip(),
                        "url": str(item.get("link", "")).strip(),
                        "resumo": str(item.get("snippet", "")).strip(),
                        "data_publicacao": str(item.get("date", "")).strip(),
                        "veiculo": str(item.get("source", "")).strip(),
                    }
                )
                if len(resultados) >= max_total:
                    break

            time.sleep(0.25)

        if len(resultados) >= max_total:
            break

        # Complementa com engine de noticias para aumentar diversidade.
        params_news = {
            "engine": "google_news",
            "q": q,
            "gl": "BR",
            "hl": "pt-BR",
            "api_key": serpapi_key,
        }
        try:
            resp_news = requests.get(SERPAPI_URL, params=params_news, timeout=30)
            resp_news.raise_for_status()
            data_news = resp_news.json()
            for item in data_news.get("news_results", []):
                resultados.append(
                    {
                        "query": q,
                        "fonte_coleta": "serpapi_news_engine",
                        "titulo": str(item.get("title", "")).strip(),
                        "url": str(item.get("link", "")).strip(),
                        "resumo": str(item.get("snippet", "")).strip(),
                        "data_publicacao": str(item.get("date", "")).strip(),
                        "veiculo": str(item.get("source", "")).strip(),
                    }
                )
                if len(resultados) >= max_total:
                    break
        except Exception as exc:
            print(f"    Aviso SerpAPI news ({q}): {exc}")

        time.sleep(0.25)

    return resultados[:max_total]


def deduplicar_mencoes(mencoes: List[Dict], max_total: int) -> List[Dict]:
    vistos = set()
    unicos: List[Dict] = []

    for m in mencoes:
        chave = (m.get("url", "").strip().lower(), m.get("titulo", "").strip().lower())
        if chave in vistos:
            continue
        vistos.add(chave)
        unicos.append(m)
        if len(unicos) >= max_total:
            break

    return unicos


def extrair_json_texto(texto: str) -> Dict:
    texto = texto.strip()
    bloco = re.search(r"\{.*\}", texto, flags=re.DOTALL)
    if not bloco:
        return {}

    candidato = bloco.group(0)
    try:
        return json.loads(candidato)
    except json.JSONDecodeError:
        return {}


def classificar_gemini(mencao: Dict, api_key: str, model: str) -> Dict:
    model = normalizar_modelo_gemini(model)
    prompt = (
        "Classifique a percepcao do texto sobre politica publica em saude. "
        "Retorne APENAS JSON valido com as chaves: "
        "sentimento (positivo|negativo|neutro|misto), "
        "posicionamento (apoio|critica|informativo|indefinido), "
        "tema (string curta), "
        "confianca (0 a 1), "
        "justificativa (max 20 palavras)."
    )

    conteudo = (
        f"Titulo: {mencao.get('titulo', '')}\n"
        f"Resumo: {mencao.get('resumo', '')}\n"
        f"Veiculo: {mencao.get('veiculo', '')}"
    )

    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"{prompt}\n\n{conteudo}",
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "topP": 0.9,
            "maxOutputTokens": 220,
        },
    }

    try:
        url = GEMINI_URL_TEMPLATE.format(model=model)
        resp = requests.post(url, headers=headers, params={"key": api_key}, json=payload, timeout=(5, 8))
        if resp.status_code >= 400:
            try:
                erro_json = resp.json()
                msg = erro_json.get("error", {}).get("message", str(erro_json))
                code = erro_json.get("error", {}).get("code", "sem_code")
            except Exception:
                msg = resp.text
                code = "sem_code"
            raise RuntimeError(
                f"Gemini ({model}) retornou HTTP {resp.status_code} | code={code}: {msg}"
            )

        data = resp.json()
        candidatos = data.get("candidates", [])
        if not candidatos:
            raise RuntimeError(f"Gemini ({model}) retornou sem candidates.")

        partes = candidatos[0].get("content", {}).get("parts", [])
        texto = "\n".join(p.get("text", "") for p in partes if p.get("text"))
        if not texto:
            raise RuntimeError(f"Gemini ({model}) retornou texto vazio.")

        parsed = extrair_json_texto(texto)
        if not parsed:
            raise RuntimeError(f"Gemini ({model}) nao retornou JSON valido.")

        parsed["metodo_classificacao"] = "gemini"
        parsed["modelo_usado"] = model
        return parsed
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc


def classificar_mencoes(mencoes: List[Dict], gemini_key: str, model: str) -> List[Dict]:
    classificadas = []

    if not gemini_key:
        raise RuntimeError("GEMINI_API_KEY ausente. A classificacao depende exclusivamente do Gemini.")

    modelos_tentativa = [model] + [m for m in GEMINI_MODELOS_GRATUITOS if m != model]
    quota_bloqueada = False
    ultimo_erro_global = ""

    for i, mencao in enumerate(mencoes, start=1):
        classe = None
        ultimo_erro = None

        if not quota_bloqueada:
            for modelo in modelos_tentativa:
                # Retry/backoff curto para erros transientes.
                for tentativa in range(2):
                    try:
                        classe = classificar_gemini(mencao, gemini_key, modelo)
                        break
                    except Exception as exc:
                        ultimo_erro = str(exc)
                        ultimo_erro_global = ultimo_erro
                        # Em cota estourada, evitar espera longa e tentativas repetitivas.
                        if "HTTP 429" in ultimo_erro and "Quota exceeded" in ultimo_erro:
                            quota_bloqueada = True
                            break
                        if tentativa < 1:
                            time.sleep((tentativa + 1) * 1.0)
                if classe or quota_bloqueada:
                    break

        if not classe:
            # Mantem o pipeline API-only e sinaliza os itens sem resposta do Gemini.
            linha = dict(mencao)
            linha.update(
                {
                    "sentimento": "nao_classificado",
                    "posicionamento": "indefinido",
                    "tema": "classificacao_pendente",
                    "justificativa": "Gemini indisponivel ou sem cota no momento.",
                    "metodo_classificacao": "gemini",
                    "modelo_usado": "indisponivel",
                    "erro_classificacao": (ultimo_erro or "falha_sem_detalhes")[:500],
                }
            )
            linha["id_mencao"] = i
            classificadas.append(linha)
        else:
            linha = dict(mencao)
            linha.update(classe)
            linha["id_mencao"] = i
            classificadas.append(linha)

        if i % 10 == 0:
            print(f"    Classificadas {i}/{len(mencoes)} mencoes...")

        time.sleep(0.05)

    if quota_bloqueada:
        print(
            "    Aviso: Gemini reportou cota esgotada (HTTP 429). "
            "Itens restantes foram marcados como nao_classificado."
        )
        if ultimo_erro_global:
            print(f"    Ultimo erro Gemini: {ultimo_erro_global[:220]}")

    return classificadas


def salvar_graficos(df: pd.DataFrame) -> None:
    if df.empty:
        return

    plt.style.use("ggplot")

    # Grafico de sentimento
    sentimentos_ordem = ["positivo", "neutro", "misto", "negativo"]
    c = Counter(df["sentimento"].fillna("neutro"))
    valores = [c.get(s, 0) for s in sentimentos_ordem]

    fig, ax = plt.subplots(figsize=(9, 5))
    barras = ax.bar(sentimentos_ordem, valores, color=["#2ecc71", "#3498db", "#f39c12", "#e74c3c"])
    ax.set_title("Percepcao das mencoes sobre o programa")
    ax.set_ylabel("Numero de mencoes")
    for b in barras:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.2, f"{int(b.get_height())}", ha="center")
    fig.tight_layout()
    fig.savefig(os.path.join(VIS_DIR, "sentimento_barras.png"), dpi=140)
    plt.close(fig)

    # Grafico de temas
    top_temas = df["tema"].fillna("percepcao geral").value_counts().head(8)
    fig, ax = plt.subplots(figsize=(10, 5))
    top_temas.sort_values().plot(kind="barh", ax=ax, color="#1f77b4")
    ax.set_title("Temas mais frequentes nas mencoes")
    ax.set_xlabel("Numero de mencoes")
    fig.tight_layout()
    fig.savefig(os.path.join(VIS_DIR, "top_temas_barras.png"), dpi=140)
    plt.close(fig)


def gerar_resumo(df: pd.DataFrame, fonte: str, modelo: str) -> Dict:
    if df.empty:
        return {
            "timestamp": datetime.now().isoformat(),
            "total_mencoes": 0,
            "fonte_coleta_principal": fonte,
            "modelo_classificacao": modelo,
        }

    sentimentos = df["sentimento"].fillna("neutro").value_counts().to_dict()
    posicionamentos = df["posicionamento"].fillna("indefinido").value_counts().to_dict()
    top_temas = df["tema"].fillna("percepcao geral").value_counts().head(5).to_dict()
    top_veiculos = df["veiculo"].fillna("").replace("", "veiculo_nao_informado").value_counts().head(8).to_dict()

    return {
        "timestamp": datetime.now().isoformat(),
        "total_mencoes": int(len(df)),
        "fonte_coleta_principal": fonte,
        "modelo_classificacao": modelo,
        "sentimentos": sentimentos,
        "posicionamentos": posicionamentos,
        "top_temas": top_temas,
        "top_veiculos": top_veiculos,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitor simples de percepcao publica")
    parser.add_argument("--tema", type=str, default="Programa Melhor em Casa")
    parser.add_argument("--max-itens", type=int, default=80)
    parser.add_argument("--max-paginas-serpapi", type=int, default=4)
    parser.add_argument("--num-por-pagina-serpapi", type=int, default=10)
    parser.add_argument(
        "--foco-opiniao-publica",
        action="store_true",
        help="adiciona queries focadas em reclamacoes/depoimentos para capturar percepcao publica",
    )
    parser.add_argument(
        "--gemini-model",
        type=str,
        default=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    )
    args = parser.parse_args()

    garantir_dirs()

    serpapi_key = os.getenv("SERPAPI_API_KEY", SERPAPI_API_KEY_DEFAULT).strip()
    gemini_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY_DEFAULT).strip()

    if not serpapi_key:
        raise RuntimeError("SERPAPI_API_KEY ausente. Este script agora exige SerpAPI sem fallback.")
    if not gemini_key:
        raise RuntimeError("GEMINI_API_KEY ausente. Este script agora exige Gemini sem fallback.")

    print("=" * 80)
    print("MONITOR DE PERCEPCAO PUBLICA - MELHOR EM CASA")
    print("=" * 80)
    print(f"Tema: {args.tema}")
    print(f"Maximo de mencoes: {args.max_itens}")

    qlist = queries_padrao(args.tema)
    if args.foco_opiniao_publica:
        # Prioriza queries de percepcao para evitar que o limite seja consumido
        # apenas por termos institucionais mais amplos.
        qlist = queries_opiniao_publica(args.tema) + qlist
        # Remove duplicatas preservando ordem.
        qlist = list(dict.fromkeys(qlist))
        print("Dica para sua AED: foco-opiniao-publica ativado.")
        print("  Exemplos de query usadas:")
        print(f"  - \"{args.tema}\" reclamacoes")
        print(f"  - \"{args.tema}\" e bom?")
        print(f"  - \"{args.tema}\" depoimento paciente")

    print("\n[1] Coletando mencoes...")
    mencoes: List[Dict] = []
    fonte = "serpapi"

    print("    Usando SerpAPI...")
    mencoes = coletar_serpapi(
        qlist,
        serpapi_key,
        args.max_itens,
        max_paginas=args.max_paginas_serpapi,
        num_por_pagina=args.num_por_pagina_serpapi,
    )
    print(f"    Mencoes brutas via SerpAPI: {len(mencoes)}")

    mencoes = deduplicar_mencoes(mencoes, args.max_itens)
    print(f"    Mencoes unicas: {len(mencoes)}")
    if len(mencoes) < args.max_itens:
        print(
            f"    Aviso: volume final abaixo do solicitado ({len(mencoes)}/{args.max_itens}). "
            "Isso depende da disponibilidade/duplicidade dos resultados publicos."
        )

    if not mencoes:
        print("\nNenhuma mencao encontrada. Encerrando.")
        return

    df_bruto = pd.DataFrame(mencoes)
    bruto_path = os.path.join(CSV_DIR, "mencoes_coletadas.csv")
    df_bruto.to_csv(bruto_path, sep=";", index=False, encoding="utf-8")

    print("\n[2] Classificando percepcao (somente Gemini)...")
    print(f"    Modelo preferido: {args.gemini_model}")
    print("    Modelos de contingencia (Gemini):")
    for m in GEMINI_MODELOS_GRATUITOS:
        print(f"      - {m}")

    try:
        mencoes_cls = classificar_mencoes(mencoes, gemini_key, args.gemini_model)
    except RuntimeError as exc:
        print("\n" + "=" * 80)
        print("FALHA NA CLASSIFICACAO GEMINI")
        print("=" * 80)
        print(str(exc))
        print("Sem fallback local e sem arquivo de erro adicional.")
        raise SystemExit(1)
    df_cls = pd.DataFrame(mencoes_cls)

    cls_path = os.path.join(CSV_DIR, "mencoes_classificadas.csv")
    df_cls.to_csv(cls_path, sep=";", index=False, encoding="utf-8")

    print("\n[3] Gerando resumo e visualizacoes...")
    salvar_graficos(df_cls)

    modelo_resumo = df_cls["modelo_usado"].mode().iloc[0] if "modelo_usado" in df_cls.columns else args.gemini_model
    resumo = gerar_resumo(df_cls, fonte, modelo_resumo)
    resumo_path = os.path.join(RESULT_DIR, "resumo_opiniao.json")
    with open(resumo_path, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("CONCLUIDO")
    print("=" * 80)
    print(f"Mencoes analisadas: {len(df_cls)}")
    print(f"CSV bruto: {bruto_path}")
    print(f"CSV classificado: {cls_path}")
    print(f"Resumo JSON: {resumo_path}")
    print(f"Grafico 1: {os.path.join(VIS_DIR, 'sentimento_barras.png')}")
    print(f"Grafico 2: {os.path.join(VIS_DIR, 'top_temas_barras.png')}")


if __name__ == "__main__":
    main()
