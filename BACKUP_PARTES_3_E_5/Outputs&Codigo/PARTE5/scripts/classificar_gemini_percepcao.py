#!/usr/bin/env python3
"""
Etapa 2: analise lexical das mencoes da Parte 5, sem uso de LLM.

Fluxo inspirado no estilo do notebook de referencia:
1) limpeza textual;
2) TF-IDF;
3) termos relevantes por registro;
4) inferencia heuristica de sentimento/gargalo;
5) visualizacoes (top termos, nuvem de palavras e rede).
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import networkx as nx
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

STOPWORDS_RUIDO = {
    "atencao", "domiciliar", "programa", "melhor", "casa", "servico", "servicos", "saude", "sus",
    "prefeitura", "municipio", "governo", "federal", "estadual", "ministerio", "secretaria", "site",
    "oficial", "brasil", "br", "gov", "www", "http", "https", "instagram", "youtube", "pdf",
    "sistema", "unico", "atendimento", "paciente", "pacientes",
}

TERMOS_BANIDOS_GRAFO = {
    "atendimento", "servico", "servicos", "paciente", "pacientes", "programa", "saude", "casa",
    "melhor", "prefeitura", "governo", "ministerio", "secretaria", "unidade", "municipio", "estado",
    "federal", "usuarios", "home", "care", "reclame", "aqui", "lista", "empresa", "visualizacoes",
    "reclamar", "clique", "saiba", "contato", "link", "brasil", "sistema", "unico",
}

SINAIS_NEGATIVOS = {
    "reclamacao", "falha", "atraso", "demora", "abandono", "omissao", "interrupcao", "desassistencia",
    "suspensao", "nao", "falta", "urgencia", "demissoes", "atrasos", "ausencia",
}

SINAIS_POSITIVOS = {
    "acolhimento", "qualidade", "humanizado", "dignidade", "garante", "fortalecido", "ampliacao",
    "atende", "cuidado", "visitam", "tratamento", "especializado",
}

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


def resolver_caminho(caminho: Path) -> Path:
    if caminho.is_absolute():
        return caminho
    return (PROJETO_ROOT / caminho).resolve()


def normalizar_ascii(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")


def limpar_texto(texto: str) -> str:
    bruto = "" if pd.isna(texto) else str(texto)
    bruto = normalizar_ascii(bruto.lower())
    bruto = re.sub(r"https?://\S+|www\.\S+", " ", bruto)
    bruto = re.sub(r"[^a-z\s]", " ", bruto)
    tokens = [
        token
        for token in bruto.split()
        if len(token) > 2 and token not in STOPWORDS_BASE and token not in STOPWORDS_RUIDO
    ]
    return " ".join(tokens)


def pontuar_lexico(texto: str, lexico: set[str]) -> int:
    score = 0
    for termo in lexico:
        if termo in texto:
            score += 1
    return score


def inferir_sentimento(consulta: str, texto_limpo: str) -> str:
    universo = f"{consulta.lower()} {texto_limpo}"
    score_neg = pontuar_lexico(universo, SINAIS_NEGATIVOS)
    score_pos = pontuar_lexico(universo, SINAIS_POSITIVOS)

    if any(chave in consulta.lower() for chave in ["reclamacao", "falha", "atraso", "demora", "desassistencia"]):
        score_neg += 1
    if any(chave in consulta.lower() for chave in ["depoimento", "avaliacao"]):
        score_pos += 1

    if score_neg >= score_pos + 1:
        return "negativo"
    if score_pos >= score_neg + 1:
        return "positivo"
    if score_neg > 0 and score_pos > 0:
        return "misto"
    return "neutro"


def inferir_gargalo(consulta: str, texto_limpo: str) -> str:
    universo = f"{consulta.lower()} {texto_limpo}"
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
        if termo in TERMOS_BANIDOS_GRAFO:
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
    df["texto_limpo"] = df["texto_fonte"].map(limpar_texto)

    ranking_global: List[Tuple[str, float]] = []
    termos_relevantes = ["" for _ in range(len(df))]

    corpus = df["texto_limpo"].tolist()
    corpus_nao_vazio = [texto for texto in corpus if texto.strip()]

    if corpus_nao_vazio:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.90)
        matriz = vectorizer.fit_transform(corpus)
        features = vectorizer.get_feature_names_out().tolist()

        medias = matriz.mean(axis=0).A1
        idx_ordenados = medias.argsort()[::-1]
        ranking_global = [(features[i], float(medias[i])) for i in idx_ordenados if medias[i] > 0]

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
        sentimentos.append(inferir_sentimento(consulta, texto_limpo))
        gargalos.append(inferir_gargalo(consulta, texto_limpo))

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


def plotar_top_termos_tfidf(ranking_global: List[Tuple[str, float]], caminho_saida: Path, n: int = 20) -> None:
    if not ranking_global:
        return

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    top = ranking_global[:n]
    labels = [par[0] for par in top][::-1]
    valores = [par[1] for par in top][::-1]

    plt.figure(figsize=(10, 8))
    plt.barh(labels, valores, color="#2b8cbe")
    plt.xlabel("TF-IDF medio")
    plt.ylabel("Termos")
    plt.title("Top termos por TF-IDF (Parte 5)")
    plt.tight_layout()
    plt.savefig(caminho_saida, dpi=240)
    plt.close()


def plotar_nuvem_tfidf(ranking_global: List[Tuple[str, float]], caminho_saida: Path) -> None:
    if not ranking_global:
        return

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    limite = max(25, min(120, len(ranking_global)))
    freq = {termo: peso for termo, peso in ranking_global[:limite] if termo not in TERMOS_BANIDOS_GRAFO}
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


def plotar_rede_gargalos(df: pd.DataFrame, caminho_saida: Path) -> None:
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    G = nx.Graph()
    df_validos = df[df["gargalo"] != "nenhum"]
    if df_validos.empty:
        return

    for _, row in df_validos.iterrows():
        gargalo = str(row["gargalo"])
        G.add_node(gargalo, tipo="gargalo", color="#d7301f")

        termos = [t.strip() for t in str(row.get("termos_relevantes", "")).split(",") if t.strip()]
        for termo in termos:
            if termo in TERMOS_BANIDOS_GRAFO or len(termo) < 3:
                continue
            G.add_node(termo, tipo="termo", color="#31a354")
            if G.has_edge(gargalo, termo):
                G[gargalo][termo]["weight"] += 1
            else:
                G.add_edge(gargalo, termo, weight=1)

    remover = [n for n, grau in G.degree() if grau < 2]
    G.remove_nodes_from(remover)
    if G.number_of_nodes() == 0:
        return

    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=1.5, seed=42)
    cores = [dados["color"] for _, dados in G.nodes(data=True)]
    pesos = [G[u][v]["weight"] for u, v in G.edges()]

    nx.draw_networkx_nodes(G, pos, node_size=1200, node_color=cores, alpha=0.85)
    nx.draw_networkx_edges(G, pos, width=pesos, alpha=0.35)
    nx.draw_networkx_labels(G, pos, font_size=9)
    plt.title("Rede de coocorrencia de gargalos e termos (Parte 5)")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(caminho_saida, dpi=280)
    plt.close()


def gerar_resumo_analitico(df: pd.DataFrame, ranking_global: List[Tuple[str, float]], caminho_saida: Path) -> None:
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    total = len(df)
    sentimentos = df["sentimento"].value_counts(dropna=False)
    gargalos = df["gargalo"].value_counts(dropna=False)

    mask_queixa = df["consulta"].str.contains(
        r"reclamacao|atraso|falha|demora|nao atendido|desassistencia|ouvidoria|cancelamento",
        case=False,
        regex=True,
        na=False,
    )
    n_queixa = int(mask_queixa.sum())

    tokens_queixa = " ".join(df.loc[mask_queixa, "texto_limpo"].fillna("").tolist()).split()
    freq_queixa = Counter(token for token in tokens_queixa if token not in TERMOS_BANIDOS_GRAFO)

    linhas = []
    linhas.append("RESUMO - PARTE 5 (ANALISE LEXICAL SEM LLM)")
    linhas.append(f"Total de mencoes analisadas: {total}")
    linhas.append(f"Mencoes de consultas com foco em queixa: {n_queixa} ({(100.0 * n_queixa / total) if total else 0:.1f}%)")
    linhas.append("")
    linhas.append("Distribuicao de sentimento (heuristica):")
    for classe, qtd in sentimentos.items():
        linhas.append(f"- {classe}: {qtd} ({(100.0 * qtd / total) if total else 0:.1f}%)")
    linhas.append("")
    linhas.append("Distribuicao de gargalo inferido:")
    for classe, qtd in gargalos.items():
        linhas.append(f"- {classe}: {qtd} ({(100.0 * qtd / total) if total else 0:.1f}%)")
    linhas.append("")
    linhas.append("Top 12 termos por TF-IDF medio:")
    for termo, peso in ranking_global[:12]:
        linhas.append(f"- {termo}: {peso:.4f}")
    linhas.append("")
    linhas.append("Top 12 termos frequentes nas consultas de queixa:")
    for termo, freq in freq_queixa.most_common(12):
        linhas.append(f"- {termo}: {freq}")

    caminho_saida.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classificacao lexical da Parte 5 sem LLM externa (TF-IDF + heuristicas)."
    )
    parser.add_argument(
        "--entrada",
        type=Path,
        default=Path("Outputs&Codigo/PARTE5/resultados/mencoes_serpapi_brutas.csv"),
        help="CSV com as mencoes brutas coletadas pela etapa 1.",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("Outputs&Codigo/PARTE5/percepcao_operacional.csv"),
        help="CSV final com campos inferidos por heuristica.",
    )
    parser.add_argument(
        "--top-k-termos",
        type=int,
        default=4,
        help="Quantidade de termos relevantes por mencao.",
    )
    parser.add_argument(
        "--fig-top-termos",
        type=Path,
        default=Path("Outputs&Codigo/PARTE5/visualizacoes/top_termos_tfidf.png"),
        help="Grafico de barras dos termos TF-IDF.",
    )
    parser.add_argument(
        "--fig-nuvem",
        type=Path,
        default=Path("Outputs&Codigo/PARTE5/visualizacoes/nuvem_palavras_tfidf.png"),
        help="Nuvem de palavras com base no ranking TF-IDF.",
    )
    parser.add_argument(
        "--fig-rede",
        type=Path,
        default=Path("Outputs&Codigo/PARTE5/visualizacoes/rede_gargalos.png"),
        help="Rede de coocorrencia entre gargalos e termos.",
    )
    parser.add_argument(
        "--resumo",
        type=Path,
        default=Path("Outputs&Codigo/PARTE5/resultados/resumo_analise_tfidf.txt"),
        help="Resumo textual com indicadores da analise.",
    )
    args = parser.parse_args()

    entrada = resolver_caminho(args.entrada)
    saida = resolver_caminho(args.saida)
    fig_top = resolver_caminho(args.fig_top_termos)
    fig_nuvem = resolver_caminho(args.fig_nuvem)
    fig_rede = resolver_caminho(args.fig_rede)
    resumo = resolver_caminho(args.resumo)

    if not entrada.exists():
        raise FileNotFoundError(f"Arquivo de entrada nao encontrado: {entrada}")

    df_bruto = pd.read_csv(entrada)
    df_saida, ranking_global = processar_df(df_bruto, top_k=max(1, args.top_k_termos))

    saida.parent.mkdir(parents=True, exist_ok=True)
    df_saida.to_csv(saida, index=False, encoding="utf-8")

    plotar_top_termos_tfidf(ranking_global, fig_top)
    plotar_nuvem_tfidf(ranking_global, fig_nuvem)
    plotar_rede_gargalos(df_saida, fig_rede)
    gerar_resumo_analitico(df_saida, ranking_global, resumo)

    print(f"Mencoes processadas: {len(df_saida)}")
    print(f"Saida principal: {saida}")
    print(f"Resumo: {resumo}")
    print(f"Figuras: {fig_top}, {fig_nuvem}, {fig_rede}")


if __name__ == "__main__":
    main()