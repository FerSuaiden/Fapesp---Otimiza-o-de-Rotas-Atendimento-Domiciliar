#!/usr/bin/env python3
"""Etapa 1: coleta de mencoes com SerpAPI para opiniao publica do Melhor em Casa."""

from __future__ import annotations

import argparse
import csv
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import requests

SERPAPI_URL = "https://serpapi.com/search"

UF_SIGLAS = {
    "acre": "AC",
    "alagoas": "AL",
    "amapa": "AP",
    "amazonas": "AM",
    "bahia": "BA",
    "ceara": "CE",
    "distrito federal": "DF",
    "espirito santo": "ES",
    "goias": "GO",
    "maranhao": "MA",
    "mato grosso": "MT",
    "mato grosso do sul": "MS",
    "minas gerais": "MG",
    "para": "PA",
    "paraiba": "PB",
    "parana": "PR",
    "pernambuco": "PE",
    "piaui": "PI",
    "rio de janeiro": "RJ",
    "rio grande do norte": "RN",
    "rio grande do sul": "RS",
    "rondonia": "RO",
    "roraima": "RR",
    "santa catarina": "SC",
    "sao paulo": "SP",
    "sergipe": "SE",
    "tocantins": "TO",
}

UF_LISTA = sorted({sigla for sigla in UF_SIGLAS.values()})
UF_RE = re.compile(r"\b(" + "|".join(UF_LISTA) + r")\b", re.IGNORECASE)
DOMINIO_UF_RE = re.compile(r"\b(" + "|".join(sigla.lower() for sigla in UF_LISTA) + r")\.gov\.br\b")


@dataclass
class Mencao:
    consulta: str
    titulo: str
    resumo: str
    link: str
    fonte: str
    data: str
    posicao: int
    estado_heuristico: str


def carregar_env_arquivo() -> None:
    """Carrega variaveis de um .env simples sem depender de biblioteca externa."""
    candidatas = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[3] / ".env",
        Path(__file__).resolve().parent / ".env",
    ]
    for caminho in candidatas:
        if not caminho.exists():
            continue
        with caminho.open("r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, valor = linha.split("=", 1)
                os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


def obter_chave_serpapi() -> str:
    chave = os.getenv("SERPAPI_API_KEY", "").strip()
    if not chave:
        raise RuntimeError(
            "SERPAPI_API_KEY nao definida. Exemplo: export SERPAPI_API_KEY='sua_chave'"
        )
    return chave


def construir_consultas() -> List[str]:
    termos_foco = [
        "reclamacao",
        "depoimento",
        "atraso",
        "falha",
        "avaliacao",
        "demora",
        "falta de equipe",
        "falta de ambulancia",
        "cancelamento",
        "nao atendido",
        "desassistencia",
        "ouvidoria",
    ]
    base = '"Melhor em Casa" OR "atencao domiciliar"'
    return [f"{base} {termo}" for termo in termos_foco]


def extrair_estado_heuristico(texto: str) -> str:
    texto_limpo = (texto or "").lower()

    for nome_estado, uf in UF_SIGLAS.items():
        if nome_estado in texto_limpo:
            return uf

    uf_encontrada = UF_RE.search((texto or "").upper())
    if uf_encontrada:
        return uf_encontrada.group(1).upper()

    dominio_uf = DOMINIO_UF_RE.search(texto_limpo)
    if dominio_uf:
        return dominio_uf.group(1).upper()

    return "NA"


def buscar_organic_results(chave: str, consulta: str, pagina_inicio: int, num: int) -> Dict:
    params = {
        "engine": "google",
        "q": consulta,
        "hl": "pt-br",
        "gl": "br",
        "google_domain": "google.com.br",
        "num": num,
        "start": pagina_inicio,
        "api_key": chave,
    }
    resposta = requests.get(SERPAPI_URL, params=params, timeout=60)
    resposta.raise_for_status()
    return resposta.json()


def coletar_mencoes(
    chave: str,
    consultas: Iterable[str],
    max_resultados_por_consulta: int,
    sleep_segundos: float,
    max_paginas_por_consulta: int,
) -> List[Mencao]:
    mencoes: List[Mencao] = []
    vistos = set()

    for consulta in consultas:
        coletados = 0
        start = 0
        paginas_processadas = 0
        paginas_sem_novos = 0
        print(f"[coleta] consulta: {consulta}")

        while coletados < max_resultados_por_consulta and paginas_processadas < max_paginas_por_consulta:
            lote = min(10, max_resultados_por_consulta - coletados)
            dados = buscar_organic_results(chave, consulta, start, lote)
            organicos = dados.get("organic_results", [])
            if not organicos:
                break

            coletados_antes = coletados
            for item in organicos:
                titulo = (item.get("title") or "").strip()
                resumo = (item.get("snippet") or "").strip()
                link = (item.get("link") or "").strip()
                fonte = (item.get("source") or "").strip()
                data = (item.get("date") or item.get("snippet_highlighted_words") or "")
                data = str(data).strip()
                posicao = int(item.get("position") or 0)

                chave_unica = (titulo.lower(), link.lower())
                if not titulo or not resumo or not link or chave_unica in vistos:
                    continue
                vistos.add(chave_unica)

                estado_heuristico = extrair_estado_heuristico(
                    f"{titulo} {resumo} {link} {fonte}"
                )
                mencoes.append(
                    Mencao(
                        consulta=consulta,
                        titulo=titulo,
                        resumo=resumo,
                        link=link,
                        fonte=fonte,
                        data=data,
                        posicao=posicao,
                        estado_heuristico=estado_heuristico,
                    )
                )
                coletados += 1
                if coletados >= max_resultados_por_consulta:
                    break

            if coletados == coletados_antes:
                paginas_sem_novos += 1
            else:
                paginas_sem_novos = 0

            if paginas_sem_novos >= 2:
                # Evita percorrer muitas paginas quando os resultados passam a repetir.
                break

            paginas_processadas += 1
            start += lote
            time.sleep(sleep_segundos)

        print(f"[coleta] mencoes validas: {coletados} | paginas: {paginas_processadas}")

    return mencoes


def salvar_csv(mencoes: List[Mencao], arquivo_saida: Path) -> None:
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
    campos = [
        "consulta",
        "titulo",
        "resumo",
        "link",
        "fonte",
        "data",
        "posicao",
        "estado_heuristico",
    ]
    with arquivo_saida.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for m in mencoes:
            writer.writerow(
                {
                    "consulta": m.consulta,
                    "titulo": m.titulo,
                    "resumo": m.resumo,
                    "link": m.link,
                    "fonte": m.fonte,
                    "data": m.data,
                    "posicao": m.posicao,
                    "estado_heuristico": m.estado_heuristico,
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Coleta mencoes do Melhor em Casa via SerpAPI para etapa de classificacao."
    )
    parser.add_argument(
        "--max-resultados-por-consulta",
        type=int,
        default=20,
        help="Quantidade maxima por consulta tematica.",
    )
    parser.add_argument(
        "--sleep-segundos",
        type=float,
        default=1.5,
        help="Pausa entre chamadas da API para evitar bloqueio.",
    )
    parser.add_argument(
        "--max-paginas-por-consulta",
        type=int,
        default=4,
        help="Limite de paginas por consulta para evitar coleta muito longa.",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("Outputs&Codigo/PARTE5/resultados/mencoes_serpapi_brutas.csv"),
        help="CSV de saida da coleta.",
    )
    return parser.parse_args()


def main() -> None:
    carregar_env_arquivo()
    args = parse_args()
    chave = obter_chave_serpapi()
    consultas = construir_consultas()

    mencoes = coletar_mencoes(
        chave=chave,
        consultas=consultas,
        max_resultados_por_consulta=args.max_resultados_por_consulta,
        sleep_segundos=args.sleep_segundos,
        max_paginas_por_consulta=args.max_paginas_por_consulta,
    )
    salvar_csv(mencoes, args.saida)

    print(f"Consultas executadas: {len(consultas)}")
    print(f"Mencoes salvas: {len(mencoes)}")
    print(f"Arquivo: {args.saida}")


if __name__ == "__main__":
    main()
