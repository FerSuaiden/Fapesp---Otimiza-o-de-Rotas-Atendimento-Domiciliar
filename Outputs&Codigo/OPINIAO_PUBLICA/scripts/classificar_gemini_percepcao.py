#!/usr/bin/env python3
"""
Etapa 2: analise lexical das mencoes de opiniao publica, sem uso de LLM.

Fluxo inspirado no estilo do notebook de referencia:
1) limpeza textual;
2) TF-IDF;
3) termos relevantes por registro;
4) inferencia heuristica de sentimento/gargalo;
5) visualizacao de nuvem de palavras.
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud

PROJETO_ROOT = Path(__file__).resolve().parents[3]

UF_LISTA = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}

STOPWORDS_BASE = {
    "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos", "e", "em", "entre",
    "esse", "essa", "isso", "foi", "ja", "mais", "mas", "mesmo", "na", "nas", "no", "nos", "o",
    "os", "ou", "para", "pela", "pelas", "pelo", "pelos", "por", "que", "se", "sem", "sua", "suas",
    "seu", "seus", "tem", "um", "uma", "umas", "uns",
}

STOPWORDS_MANUAIS = {
    "ele", "ela", "eles", "elas", "isso", "isto", "aquele", "aquela", "aqueles", "aquelas",
    "agora", "apenas", "ainda", "alem", "tambem", "junto", "geral", "neste", "nesta", "nessa",
    "nossa", "nosso", "nossos", "nossas", "voces", "ate", "sobre", "segundo", "forma", "ser",
    "estar", "esta", "tinha", "teve", "pode", "faz", "fazer", "feito", "sendo", "diz", "disse",
    "nao", "leva", "oferece", "conheca", "quem", "porque", "foram", "nada", "cada", "vez",
    "minha", "nos", "podem", "sendo", "sao", "anos", "objetivo", "objetivos",
    "qual", "possui", "definida", "avaliadas", "calcularmos", "vazio", "finalizado", "todas",
}

STOPWORDS_RUIDO = {
    "atencao", "domiciliar", "programa", "melhor", "casa", "servico", "servicos", "saude", "sus",
    "prefeitura", "municipio", "governo", "federal", "estadual", "ministerio", "secretaria", "site",
    "oficial", "brasil", "br", "gov", "www", "http", "https", "instagram", "youtube", "pdf",
    "sistema", "unico", "atendimento", "paciente", "pacientes", "sad", "saes", "ouvidoria",
    "imprimir", "fechar", "portal", "geral", "integrado", "especializada", "especializado",
    "mpgo", "wilker", "barreto", "beatriz", "orlando", "goiania", "cuiaba", "jundiai", "sjm",
}

TERMOS_BANIDOS_GRAFO = {
    "atendimento", "servico", "servicos", "paciente", "pacientes", "programa", "saude", "casa",
    "melhor", "prefeitura", "governo", "ministerio", "secretaria", "unidade", "municipio", "estado",
    "federal", "usuarios", "home", "care", "reclame", "aqui", "lista", "empresa", "visualizacoes",
    "reclamar", "clique", "saiba", "contato", "link", "brasil", "sistema", "unico",
}

SINAIS_NEGATIVOS = {
    "reclamacao", "falha", "atraso", "demora", "abandono", "omissao", "interrupcao", "desassistencia",
    "suspensao", "falta", "urgencia", "demissoes", "atrasos", "ausencia",
}

SINAIS_POSITIVOS = {
    "acolhimento", "qualidade", "humanizado", "dignidade", "garante", "fortalecido", "ampliacao",
    "atende", "cuidado", "visitam", "tratamento", "especializado",
}

SINAIS_NEGATIVOS_FRASES = {
    "nao atendido", "nao recomendada", "nao disponibiliza", "nao possui", "nao formalizou",
    "sem atendimento", "falta atendimento", "atraso alta", "esperando visita", "cada vez debilitada",
    "suspensao repasses", "ausencia atendimento", "demora atendimento",
}

SINAIS_POSITIVOS_FRASES = {
    "qualidade vida", "atendimento humanizado", "acolhimento dignidade", "atendimento especializado",
    "mais pacientes", "oferece atendimento", "garante atendimento",
}

STOPWORDS_TFIDF = STOPWORDS_BASE | STOPWORDS_MANUAIS | STOPWORDS_RUIDO

GARGALOS_LEXICO = {
    "pessoal": {
        "equipe", "equipes", "profissionais", "medico", "medicos", "enfermagem", "fisioterapia",
        "demissoes", "salarial", "salariais", "terceirizados", "cuidadores",
    },
    "frota": {
        "ambulancia", "veiculo", "veiculos", "frota", "transporte", "deslocamento", "oxigenio",
        "sonda", "medicamento", "medicamentos", "insumo", "insumos",
    },
    "escala": {
        "atraso", "demora", "espera", "interrupcao", "desassistencia", "suspensao", "nao atendido",
        "regularidade", "continuidade", "visita", "visitas", "cobertura",
    },
    "tempo de deslocamento": {
        "deslocamento", "transito", "distancia", "longa", "viagem", "rota", "rotas",
    },
}

# Correcao leve de ruido lexical comum em snippets do buscador.
TOKEN_CORRECOES = {
    "quipe": "equipe",
    "quipes": "equipe",
    "equipes": "equipe",
}


def resolver_caminho(caminho: Path) -> Path:
    if caminho.is_absolute():
        return caminho
    return (PROJETO_ROOT / caminho).resolve()


def normalizar_ascii(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")


def corrigir_token(token: str) -> str:
    return TOKEN_CORRECOES.get(token, token)


def token_relevante(token: str) -> bool:
    if not token or len(token) < 3:
        return False
    if token in STOPWORDS_TFIDF:
        return False
    if token in TERMOS_BANIDOS_GRAFO:
        return False
    if any(char.isdigit() for char in token):
        return False
    if len(set(token)) == 1:
        return False
    return True


def termo_relevante(termo: str) -> bool:
    partes = [p.strip() for p in termo.split() if p.strip()]
    if not partes:
        return False
    return all(token_relevante(p) for p in partes)


def limpar_texto(texto: str) -> str:
    bruto = "" if pd.isna(texto) else str(texto)
    bruto = normalizar_ascii(bruto.lower())
    bruto = re.sub(r"https?://\S+|www\.\S+", " ", bruto)
    bruto = re.sub(r"[^a-z\s]", " ", bruto)
    tokens = []
    for token in bruto.split():
        token_corrigido = corrigir_token(token)
        if token_relevante(token_corrigido):
            tokens.append(token_corrigido)
    return " ".join(tokens)


def normalizar_texto_base(texto: str) -> str:
    bruto = "" if pd.isna(texto) else str(texto)
    bruto = normalizar_ascii(bruto.lower())
    bruto = re.sub(r"https?://\S+|www\.\S+", " ", bruto)
    bruto = re.sub(r"[^a-z\s]", " ", bruto)
    tokens = [corrigir_token(token) for token in bruto.split()]
    return " ".join(tokens)


def pontuar_lexico(texto: str, lexico: set[str]) -> float:
    score = 0.0
    texto_pad = f" {texto} "
    for termo in lexico:
        if " " in termo:
            if termo in texto:
                score += 1.0
        elif f" {termo} " in texto_pad:
            score += 1.0
    return score


def inferir_sentimento(consulta: str, texto_limpo: str, texto_base_norm: str) -> str:
    universo = f"{consulta.lower()} {texto_base_norm}"
    score_neg = pontuar_lexico(universo, SINAIS_NEGATIVOS)
    score_pos = pontuar_lexico(universo, SINAIS_POSITIVOS)
    score_neg += 1.5 * pontuar_lexico(universo, SINAIS_NEGATIVOS_FRASES)
    score_pos += 1.2 * pontuar_lexico(universo, SINAIS_POSITIVOS_FRASES)

    if any(chave in consulta.lower() for chave in ["reclamacao", "falha", "atraso", "demora", "desassistencia"]):
        score_neg += 0.35
    if any(chave in consulta.lower() for chave in ["depoimento", "avaliacao"]):
        score_pos += 0.35

    if score_neg >= score_pos + 0.8:
        return "negativo"
    if score_pos >= score_neg + 0.8:
        return "positivo"
    if score_neg > 0 and score_pos > 0:
        return "misto"
    return "neutro"


def inferir_gargalo(consulta: str, texto_limpo: str, texto_base_norm: str) -> str:
    _ = consulta
    _ = texto_limpo
    universo = texto_base_norm
    scores = {gargalo: pontuar_lexico(universo, termos) for gargalo, termos in GARGALOS_LEXICO.items()}
    melhor, score = max(scores.items(), key=lambda item: item[1])
    if score == 0:
        return "nenhum"
    return melhor


def top_termos_linha(matriz_tfidf, features: List[str], idx_linha: int, top_k: int) -> List[str]:
    linha = matriz_tfidf.getrow(idx_linha)
    if linha.nnz == 0:
        return []

    pares = sorted(zip(linha.indices, linha.data), key=lambda item: item[1], reverse=True)
    termos = []
    for indice, _ in pares:
        termo = features[indice]
        if not termo_relevante(termo):
            continue
        termos.append(termo)
        if len(termos) >= top_k:
            break
    return termos


def processar_df(df_bruto: pd.DataFrame, top_k: int) -> Tuple[pd.DataFrame, List[Tuple[str, float]]]:
    df = df_bruto.copy()

    for coluna in ["consulta", "titulo", "resumo", "estado_heuristico"]:
        if coluna not in df.columns:
            df[coluna] = ""

    df["texto_fonte"] = df["titulo"].fillna("") + " " + df["resumo"].fillna("")
    df["texto_base_norm"] = df["texto_fonte"].map(normalizar_texto_base)
    df["texto_limpo"] = df["texto_fonte"].map(limpar_texto)

    ranking_global: List[Tuple[str, float]] = []
    termos_relevantes = ["" for _ in range(len(df))]

    corpus = df["texto_limpo"].tolist()
    corpus_nao_vazio = [texto for texto in corpus if texto.strip()]

    if corpus_nao_vazio:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.75,
            stop_words=sorted(STOPWORDS_TFIDF),
        )
        matriz = vectorizer.fit_transform(corpus)
        features = vectorizer.get_feature_names_out().tolist()

        medias = matriz.mean(axis=0).A1
        idx_ordenados = medias.argsort()[::-1]
        ranking_global = [
            (features[i], float(medias[i]))
            for i in idx_ordenados
            if medias[i] > 0 and termo_relevante(features[i])
        ]

        for i in range(len(df)):
            termos = top_termos_linha(matriz, features, i, top_k=top_k)
            termos_relevantes[i] = ", ".join(termos)

    estados = []
    sentimentos = []
    gargalos = []

    for row in df.itertuples(index=False):
        estado = str(getattr(row, "estado_heuristico", "NA")).upper().strip()
        if estado not in UF_LISTA:
            estado = "NA"
        estados.append(estado)

        consulta = str(getattr(row, "consulta", ""))
        texto_limpo = str(getattr(row, "texto_limpo", ""))
        texto_base_norm = str(getattr(row, "texto_base_norm", ""))
        sentimentos.append(inferir_sentimento(consulta, texto_limpo, texto_base_norm))
        gargalos.append(inferir_gargalo(consulta, texto_limpo, texto_base_norm))

    df["estado"] = estados
    df["sentimento"] = sentimentos
    df["gargalo"] = gargalos
    df["termos_relevantes"] = termos_relevantes
    df["erro_classificacao"] = ""

    colunas_saida = list(df_bruto.columns)
    for extra in ["sentimento", "estado", "gargalo", "texto_limpo", "termos_relevantes", "erro_classificacao"]:
        if extra not in colunas_saida:
            colunas_saida.append(extra)

    return df[colunas_saida], ranking_global


def plotar_nuvem_tfidf(ranking_global: List[Tuple[str, float]], caminho_saida: Path) -> None:
    if not ranking_global:
        return

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    limite = max(25, min(120, len(ranking_global)))
    freq = {termo: peso for termo, peso in ranking_global[:limite] if termo_relevante(termo)}
    if not freq:
        return

    nuvem = WordCloud(
        width=1200,
        height=600,
        background_color="white",
        collocations=False,
    ).generate_from_frequencies(freq)

    plt.figure(figsize=(12, 6))
    plt.imshow(nuvem, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(caminho_saida, dpi=240)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classificacao lexical de opiniao publica sem LLM externa (TF-IDF + heuristicas)."
    )
    parser.add_argument(
        "--perfil",
        type=str,
        default="problem-oriented",
        choices=["problem-oriented", "balanced"],
        help="Perfil de pastas para leitura/escrita dos arquivos da analise.",
    )
    parser.add_argument(
        "--entrada",
        type=Path,
        default=None,
        help=(
            "CSV com as mencoes brutas coletadas pela etapa 1. Se omitido, usa "
            "Outputs&Codigo/OPINIAO_PUBLICA/<perfil>/mencoes_serpapi_brutas.csv"
        ),
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=None,
        help=(
            "CSV final com campos inferidos por heuristica. Se omitido, usa "
            "Outputs&Codigo/OPINIAO_PUBLICA/<perfil>/percepcao_operacional.csv"
        ),
    )
    parser.add_argument(
        "--top-k-termos",
        type=int,
        default=4,
        help="Quantidade de termos relevantes por mencao.",
    )
    parser.add_argument(
        "--fig-nuvem",
        type=Path,
        default=None,
        help="Nuvem de palavras com base no ranking TF-IDF.",
    )
    args = parser.parse_args()

    base_perfil = Path(f"Outputs&Codigo/OPINIAO_PUBLICA/{args.perfil}")

    entrada_rel = args.entrada or (base_perfil / "mencoes_serpapi_brutas.csv")
    saida_rel = args.saida or (base_perfil / "percepcao_operacional.csv")
    fig_nuvem_rel = args.fig_nuvem or (base_perfil / "nuvem_palavras_tfidf.png")

    entrada = resolver_caminho(entrada_rel)
    saida = resolver_caminho(saida_rel)
    fig_nuvem = resolver_caminho(fig_nuvem_rel)

    if not entrada.exists():
        raise FileNotFoundError(f"Arquivo de entrada nao encontrado: {entrada}")

    df_bruto = pd.read_csv(entrada)
    df_saida, ranking_global = processar_df(df_bruto, top_k=max(1, args.top_k_termos))

    saida.parent.mkdir(parents=True, exist_ok=True)
    df_saida.to_csv(saida, index=False, encoding="utf-8")

    plotar_nuvem_tfidf(ranking_global, fig_nuvem)

    print(f"Mencoes processadas: {len(df_saida)}")
    print(f"Saida principal: {saida}")
    print(f"Figura: {fig_nuvem}")


if __name__ == "__main__":
    main()