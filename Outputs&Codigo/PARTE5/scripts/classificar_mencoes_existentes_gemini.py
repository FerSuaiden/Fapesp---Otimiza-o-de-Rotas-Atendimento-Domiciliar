#!/usr/bin/env python3
"""
Classifica mencoes ja coletadas (CSV) usando Gemini, sem nova coleta SerpAPI.

Uso principal:
1) Ter um arquivo de coleta pronto em dados_csv/mencoes_coletadas.csv
2) Rodar este script para classificar pendencias gradualmente
3) O script aguarda automaticamente quando a cota gratuita retorna HTTP 429

Saidas:
- Outputs&Codigo/PARTE5/dados_csv/mencoes_classificadas.csv
- Outputs&Codigo/PARTE5/resultados/resumo_opiniao.json
- Outputs&Codigo/PARTE5/visualizacoes/sentimento_barras.png
- Outputs&Codigo/PARTE5/visualizacoes/top_temas_barras.png
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import Counter
from datetime import datetime
from math import ceil
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import requests

BASE_DIR = "/home/fersuaiden/Área de trabalho/Faculdade/IC"
PARTE5_DIR = os.path.join(BASE_DIR, "Outputs&Codigo", "PARTE5")
CSV_DIR = os.path.join(PARTE5_DIR, "dados_csv")
VIS_DIR = os.path.join(PARTE5_DIR, "visualizacoes")
RESULT_DIR = os.path.join(PARTE5_DIR, "resultados")

GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_API_KEY_DEFAULT = "AIzaSyBI_05nLJNTZ-RQC4ZswMhlEUYWsX6lA5c"

GEMINI_MODELOS_GRATUITOS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemma-3-4b-it",
    "gemma-3-12b-it",
]


def garantir_dirs() -> None:
    for d in (CSV_DIR, VIS_DIR, RESULT_DIR):
        os.makedirs(d, exist_ok=True)


def normalizar_modelo_gemini(model: str) -> str:
    model = (model or "").strip()
    return model[len("models/") :] if model.startswith("models/") else model


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
        raise RuntimeError(f"Gemini ({model}) retornou HTTP {resp.status_code} | code={code}: {msg}")

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
    parsed["erro_classificacao"] = ""
    return parsed


def chave_mencao(m: Dict) -> Tuple[str, str]:
    return (
        str(m.get("url", "")).strip().lower(),
        str(m.get("titulo", "")).strip().lower(),
    )


def ja_classificada_ok(m: Dict, reprocessar_indisponiveis: bool) -> bool:
    sentimento = texto_ou_padrao(m.get("sentimento", ""), "").lower()
    if not sentimento:
        return False

    # Classificacoes com sentimento definido ja sao finais.
    if sentimento != "nao_classificado":
        return True

    if reprocessar_indisponiveis:
        return False

    # Quando nao vamos reprocessar, marcacoes de indisponibilidade tambem contam como finais.
    modelo = texto_ou_padrao(m.get("modelo_usado", ""), "").lower()
    return modelo in {"indisponivel", "pendente"}


def texto_ou_padrao(valor, padrao: str = "") -> str:
    if valor is None:
        return padrao
    try:
        if pd.isna(valor):
            return padrao
    except Exception:
        pass
    v = str(valor).strip()
    return v if v else padrao


def erro_tem_cota(msg: str) -> bool:
    msg_l = msg.lower()
    return "http 429" in msg_l or "quota exceeded" in msg_l or "resource_exhausted" in msg_l


def extrair_retry_segundos(msg: str, padrao: int = 60) -> int:
    achou = re.search(r"please retry in\s*([0-9]+(?:\.[0-9]+)?)s", msg, flags=re.IGNORECASE)
    if not achou:
        return padrao
    return max(1, ceil(float(achou.group(1))))


def classificar_com_espera(
    mencao: Dict,
    api_key: str,
    modelos: List[str],
    espera_padrao: int,
    max_esperas_429: int,
    max_segundos_espera_por_item: int,
) -> Dict:
    ultimo_erro = ""
    esperas_429 = 0
    segundos_esperados = 0

    while True:
        quota_detectada = False
        for modelo in modelos:
            try:
                return classificar_gemini(mencao, api_key, modelo)
            except Exception as exc:
                ultimo_erro = str(exc)
                if erro_tem_cota(ultimo_erro):
                    # Se a conta reporta limite 0, nao adianta aguardar nesta rodada.
                    if "limit: 0" in ultimo_erro.lower():
                        return {
                            "sentimento": "nao_classificado",
                            "posicionamento": "indefinido",
                            "tema": "classificacao_indisponivel",
                            "confianca": 0,
                            "justificativa": "Gemini sem cota disponivel (limit: 0).",
                            "metodo_classificacao": "gemini",
                            "modelo_usado": "indisponivel",
                            "erro_classificacao": ultimo_erro[:500],
                        }

                    segundos = extrair_retry_segundos(ultimo_erro, padrao=espera_padrao)
                    esperas_429 += 1
                    segundos_esperados += segundos

                    if esperas_429 > max_esperas_429 or segundos_esperados > max_segundos_espera_por_item:
                        return {
                            "sentimento": "nao_classificado",
                            "posicionamento": "indefinido",
                            "tema": "classificacao_pendente",
                            "confianca": 0,
                            "justificativa": "Limite de espera por cota atingido.",
                            "metodo_classificacao": "gemini",
                            "modelo_usado": "indisponivel",
                            "erro_classificacao": (
                                f"Aguardou {segundos_esperados}s em {esperas_429} evento(s) de cota. "
                                f"Ultimo erro: {ultimo_erro}"
                            )[:500],
                        }

                    print(f"    Cota/rate limit no Gemini. Aguardando {segundos}s para retomar...")
                    time.sleep(segundos)
                    quota_detectada = True
                    break
                # Erro nao relacionado a cota: tenta proximo modelo.
                continue

        if quota_detectada:
            continue

        return {
            "sentimento": "nao_classificado",
            "posicionamento": "indefinido",
            "tema": "classificacao_pendente",
            "confianca": 0,
            "justificativa": "Falha no Gemini para todos os modelos.",
            "metodo_classificacao": "gemini",
            "modelo_usado": "indisponivel",
            "erro_classificacao": ultimo_erro[:500],
        }


def salvar_graficos(df: pd.DataFrame) -> None:
    if df.empty:
        return

    plt.style.use("ggplot")

    sentimentos_ordem = ["positivo", "neutro", "misto", "negativo", "nao_classificado"]
    c = Counter(df["sentimento"].fillna("nao_classificado"))
    valores = [c.get(s, 0) for s in sentimentos_ordem]

    fig, ax = plt.subplots(figsize=(10, 5))
    barras = ax.bar(
        sentimentos_ordem,
        valores,
        color=["#2ecc71", "#3498db", "#f39c12", "#e74c3c", "#7f8c8d"],
    )
    ax.set_title("Percepcao das mencoes sobre o programa")
    ax.set_ylabel("Numero de mencoes")
    for b in barras:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.2, f"{int(b.get_height())}", ha="center")
    fig.tight_layout()
    fig.savefig(os.path.join(VIS_DIR, "sentimento_barras.png"), dpi=140)
    plt.close(fig)

    top_temas = df["tema"].fillna("percepcao geral").value_counts().head(8)
    fig, ax = plt.subplots(figsize=(10, 6))
    top_temas.sort_values().plot(kind="barh", ax=ax, color="#1f77b4")
    ax.set_title("Temas mais frequentes nas mencoes")
    ax.set_xlabel("Numero de mencoes")
    fig.tight_layout()
    fig.savefig(os.path.join(VIS_DIR, "top_temas_barras.png"), dpi=140)
    plt.close(fig)


def gerar_resumo(df: pd.DataFrame, modelo: str) -> Dict:
    if df.empty:
        return {
            "timestamp": datetime.now().isoformat(),
            "total_mencoes": 0,
            "fonte_coleta_principal": "serpapi",
            "modelo_classificacao": modelo,
        }

    sentimentos = df["sentimento"].fillna("nao_classificado").value_counts().to_dict()
    posicionamentos = df["posicionamento"].fillna("indefinido").value_counts().to_dict()
    top_temas = df["tema"].fillna("percepcao geral").value_counts().head(5).to_dict()
    top_veiculos = df["veiculo"].fillna("").replace("", "veiculo_nao_informado").value_counts().head(8).to_dict()

    return {
        "timestamp": datetime.now().isoformat(),
        "total_mencoes": int(len(df)),
        "fonte_coleta_principal": "serpapi",
        "modelo_classificacao": modelo,
        "sentimentos": sentimentos,
        "posicionamentos": posicionamentos,
        "top_temas": top_temas,
        "top_veiculos": top_veiculos,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Classifica mencoes ja coletadas sem nova busca SerpAPI")
    parser.add_argument(
        "--coletadas-csv",
        type=str,
        default=os.path.join(CSV_DIR, "mencoes_coletadas.csv"),
    )
    parser.add_argument(
        "--classificadas-csv",
        type=str,
        default=os.path.join(CSV_DIR, "mencoes_classificadas.csv"),
    )
    parser.add_argument(
        "--max-processar",
        type=int,
        default=0,
        help="0 = processa todos os pendentes; N = processa no maximo N pendentes nesta execucao",
    )
    parser.add_argument(
        "--gemini-model",
        type=str,
        default=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    )
    parser.add_argument(
        "--espera-padrao-429",
        type=int,
        default=60,
        help="segundos de espera quando o Gemini nao informar explicitamente o retry",
    )
    parser.add_argument(
        "--max-esperas-429-por-item",
        type=int,
        default=3,
        help="quantas vezes esperar por cota para a mesma mencao antes de marcar pendente",
    )
    parser.add_argument(
        "--max-segundos-espera-por-item",
        type=int,
        default=240,
        help="tempo maximo total de espera por cota para a mesma mencao",
    )
    parser.add_argument(
        "--max-minutos-execucao",
        type=int,
        default=30,
        help="limite global de execucao (em minutos) para evitar processamento indefinido",
    )
    parser.add_argument(
        "--reprocessar-indisponiveis",
        action="store_true",
        help="forca nova tentativa Gemini para itens marcados como indisponivel/nao_classificado",
    )
    parser.add_argument(
        "--sem-tentativa-gemini",
        action="store_true",
        help="nao chama Gemini nesta rodada; apenas finaliza pendentes como indisponivel",
    )
    args = parser.parse_args()

    garantir_dirs()

    gemini_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY_DEFAULT).strip()
    if not gemini_key:
        raise RuntimeError("GEMINI_API_KEY ausente.")

    if not os.path.exists(args.coletadas_csv):
        raise FileNotFoundError(f"Arquivo de coleta nao encontrado: {args.coletadas_csv}")

    df_coletadas = pd.read_csv(args.coletadas_csv, sep=";", encoding="utf-8")
    if df_coletadas.empty:
        print("Arquivo de coleta vazio. Nada a classificar.")
        return

    if os.path.exists(args.classificadas_csv):
        df_existente = pd.read_csv(args.classificadas_csv, sep=";", encoding="utf-8")
    else:
        df_existente = pd.DataFrame()

    existentes_por_chave: Dict[Tuple[str, str], Dict] = {}
    if not df_existente.empty:
        for item in df_existente.to_dict(orient="records"):
            existentes_por_chave[chave_mencao(item)] = item

    modelos_tentativa = [args.gemini_model] + [m for m in GEMINI_MODELOS_GRATUITOS if m != args.gemini_model]

    print("=" * 80)
    print("CLASSIFICACAO DE MENCOES JA COLETADAS (SEM SERPAPI)")
    print("=" * 80)
    print(f"Entrada coleta: {args.coletadas_csv}")
    print(f"Saida classificacao: {args.classificadas_csv}")

    resultados: List[Dict] = []
    pendentes: List[Dict] = []

    for item in df_coletadas.to_dict(orient="records"):
        base = dict(item)
        existente = existentes_por_chave.get(chave_mencao(base))
        if existente and ja_classificada_ok(existente, args.reprocessar_indisponiveis):
            base.update(
                {
                    "sentimento": texto_ou_padrao(existente.get("sentimento", ""), "nao_classificado"),
                    "posicionamento": texto_ou_padrao(existente.get("posicionamento", ""), "indefinido"),
                    "tema": texto_ou_padrao(existente.get("tema", ""), "percepcao geral"),
                    "confianca": existente.get("confianca", ""),
                    "justificativa": texto_ou_padrao(existente.get("justificativa", ""), ""),
                    "metodo_classificacao": texto_ou_padrao(existente.get("metodo_classificacao", "gemini"), "gemini"),
                    "modelo_usado": texto_ou_padrao(existente.get("modelo_usado", "indisponivel"), "indisponivel"),
                    "erro_classificacao": texto_ou_padrao(existente.get("erro_classificacao", ""), ""),
                }
            )
            resultados.append(base)
        else:
            pendentes.append(base)

    if args.max_processar > 0:
        pendentes_exec = pendentes[: args.max_processar]
        pendentes_restantes = pendentes[args.max_processar :]
    else:
        pendentes_exec = pendentes
        pendentes_restantes = []

    print(f"Mencoes totais na coleta: {len(df_coletadas)}")
    print(f"Ja classificadas reaproveitadas: {len(resultados)}")
    print(f"Pendentes para esta execucao: {len(pendentes_exec)}")
    if pendentes_restantes:
        print(f"Nao processadas nesta rodada por --max-processar: {len(pendentes_restantes)}")

    inicio_execucao = time.time()
    limite_segundos_execucao = max(1, args.max_minutos_execucao) * 60

    total_pendentes_exec = len(pendentes_exec)
    processadas_nesta_execucao = 0
    for i, mencao in enumerate(pendentes_exec, start=1):
        if (time.time() - inicio_execucao) > limite_segundos_execucao:
            print(
                "    Limite global de execucao atingido. "
                "Itens restantes serao marcados como nao_classificado nesta rodada."
            )
            break

        if args.sem_tentativa_gemini:
            classe = {
                "sentimento": "nao_classificado",
                "posicionamento": "indefinido",
                "tema": "classificacao_indisponivel",
                "confianca": 0,
                "justificativa": "Rodada sem tentativa Gemini.",
                "metodo_classificacao": "gemini",
                "modelo_usado": "indisponivel",
                "erro_classificacao": "",
            }
        else:
            classe = classificar_com_espera(
                mencao,
                gemini_key,
                modelos_tentativa,
                espera_padrao=args.espera_padrao_429,
                max_esperas_429=args.max_esperas_429_por_item,
                max_segundos_espera_por_item=args.max_segundos_espera_por_item,
            )
        mencao_cls = dict(mencao)
        mencao_cls.update(classe)
        resultados.append(mencao_cls)
        processadas_nesta_execucao += 1

        # Persistencia incremental para retomar facilmente caso interrompa,
        # mantendo todas as linhas no arquivo mesmo durante processamento.
        restante_exec = pendentes_exec[i:]
        df_parcial = pd.DataFrame(resultados + restante_exec + pendentes_restantes)
        df_parcial.to_csv(args.classificadas_csv, sep=";", index=False, encoding="utf-8")

        if i % 5 == 0 or i == total_pendentes_exec:
            print(f"    Processadas {i}/{total_pendentes_exec} pendentes nesta execucao...")

        time.sleep(0.05)

    pendentes_nao_processadas = pendentes_exec[processadas_nesta_execucao:] + pendentes_restantes

    # Itens nao processados nesta rodada sao finalizados como nao_classificado.
    for rest in pendentes_nao_processadas:
        rest_out = dict(rest)
        rest_out.update(
            {
                "sentimento": "nao_classificado",
                "posicionamento": "indefinido",
                "tema": "classificacao_indisponivel",
                "confianca": 0,
                "justificativa": "Nao processado nesta rodada (limite de execucao).",
                "metodo_classificacao": "gemini",
                "modelo_usado": "indisponivel",
                "erro_classificacao": "",
            }
        )
        resultados.append(rest_out)

    df_final = pd.DataFrame(resultados)
    df_final = df_final.reset_index(drop=True)
    for col, default in [
        ("sentimento", "nao_classificado"),
        ("posicionamento", "indefinido"),
        ("tema", "classificacao_indisponivel"),
        ("justificativa", ""),
        ("metodo_classificacao", "gemini"),
        ("modelo_usado", "indisponivel"),
        ("erro_classificacao", ""),
    ]:
        if col in df_final.columns:
            df_final[col] = df_final[col].fillna(default).astype(str).replace("", default)

    df_final.insert(0, "id_mencao", range(1, len(df_final) + 1))
    df_final.to_csv(args.classificadas_csv, sep=";", index=False, encoding="utf-8")

    salvar_graficos(df_final)

    modelo_resumo = df_final["modelo_usado"].mode().iloc[0] if "modelo_usado" in df_final.columns else args.gemini_model
    resumo = gerar_resumo(df_final, modelo_resumo)
    resumo_path = os.path.join(RESULT_DIR, "resumo_opiniao.json")
    with open(resumo_path, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("CONCLUIDO")
    print("=" * 80)
    print(f"Mencoes totais no arquivo final: {len(df_final)}")
    print(f"Classificadas CSV: {args.classificadas_csv}")
    print(f"Resumo JSON: {resumo_path}")


if __name__ == "__main__":
    main()
