from __future__ import annotations

import ast
import io
from pathlib import Path
from typing import Iterable, List

import pandas as pd
import streamlit as st


PRE_EMERGENTE_KEYS = [
    "atrazina",
    "ametrina",
    "pendimetalina",
    "trifluralina",
    "acetoclor",
    "sulfentrazona",
    "imazapic",
    "imazamox",
    "imazapyr",
]

POS_EMERGENTE_KEYS = [
    "2,4-d",
    "glifosato",
    "diquate",
    "paraquat",
    "haloxifope",
    "sethoxydim",
    "clethodim",
    "fenoxaprop",
    "dicamba",
    "bentazona",
    "picloram",
]


def _parse_list(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        return value
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    except Exception:
        return [text]


def _safe_str(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _contains_culture(cultures: Iterable[dict], target: str) -> bool:
    for item in cultures:
        if isinstance(item, dict) and _safe_str(item.get("nome")) == target:
            return True
    return False


def _inferir_tipo_emergencia(classe: str, ingrediente_ativo: str) -> str:
    classe_low = _safe_str(classe).lower()
    if "herbicida" not in classe_low:
        return "Não se aplica"

    ing_low = _safe_str(ingrediente_ativo).lower()
    has_pre = any(k in ing_low for k in PRE_EMERGENTE_KEYS)
    has_pos = any(k in ing_low for k in POS_EMERGENTE_KEYS)

    if has_pre and has_pos:
        return "Ambos"
    if has_pre:
        return "Pré-emergente"
    if has_pos:
        return "Pós-emergente"
    return "Não classificado"


def _extract_unique_from_col(df: pd.DataFrame, col: str) -> List[str]:
    values = set()
    if col not in df.columns:
        return []
    for raw in df[col].dropna():
        for item in str(raw).split(", "):
            item = item.strip()
            if item:
                values.add(item)
    return sorted(values)


def _to_low_text(value) -> str:
    return _safe_str(value).lower()


def _toxicologia_penalty(value: str) -> int:
    text = _to_low_text(value)
    if not text:
        return 0
    if "extremamente tóxico" in text or "classe i" in text:
        return 2
    if "altamente tóxico" in text or "classe ii" in text:
        return 1
    return 0


def _ambiental_bonus(value: str) -> int:
    text = _to_low_text(value)
    if not text:
        return 0
    if "improvável" in text or "classe iv" in text:
        return 1
    if "pouco" in text or "classe iii" in text:
        return 1
    return 0


def _build_export_dataframe(ranking: pd.DataFrame, cultura: str, filtros_texto: str) -> pd.DataFrame:
    export_df = ranking.copy()
    export_df.insert(0, "cultura", cultura)
    export_df.insert(1, "filtros_aplicados", filtros_texto)
    return export_df


def _render_export_produtos_filtrados(produtos: pd.DataFrame, cultura: str, filtros_texto: str):
    if produtos.empty:
        return
    export_df = produtos.copy()
    export_df.insert(0, "cultura", cultura)
    export_df.insert(1, "filtros_aplicados", filtros_texto)
    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)
    st.download_button(
        "Baixar produtos filtrados (CSV)",
        data=csv_buffer.getvalue(),
        file_name=f"produtos_filtrados_agrofit_{cultura.replace(' ', '_').lower()}.csv",
        mime="text/csv",
    )


@st.cache_data(show_spinner=False)
def load_data(base_dir: Path) -> dict[str, pd.DataFrame]:
    data = {
        "culturas": pd.read_csv(base_dir / "cultura.csv"),
        "pragas": pd.read_csv(base_dir / "praga.csv"),
        "produto_formulado": pd.read_csv(base_dir / "produto_formulado.csv"),
    }
    return data


def _get_snapshot_dirs(root: Path) -> List[Path]:
    if not root.exists():
        return []
    dirs = [d for d in root.iterdir() if d.is_dir()]
    return sorted(dirs, reverse=True)


def _get_data_dir() -> Path:
    base_root = Path(__file__).resolve().parents[1] / "Dados" / "Embrapa"
    snapshots_root = base_root / "Agrofit_snapshots"
    fallback = base_root / "Agrofit_csv"

    snapshots = _get_snapshot_dirs(snapshots_root)
    if not snapshots:
        return fallback

    st.sidebar.subheader("Fonte de dados")
    options = [snap.name for snap in snapshots]
    selected = st.sidebar.selectbox("Snapshot", options, index=0)
    selected_dir = snapshots_root / selected / "raw"
    if not selected_dir.exists():
        return fallback
    return selected_dir


def build_pragas_for_culture(pragas: pd.DataFrame, cultura: str, incluir_todas: bool) -> pd.DataFrame:
    rows = []
    for _, row in pragas.iterrows():
        culturas = _parse_list(row.get("cultura"))
        if _contains_culture(culturas, cultura) or (incluir_todas and _contains_culture(culturas, "Todas as culturas")):
            rows.append(
                {
                    "classificacao": row.get("classificacao", ""),
                    "nome_cientifico": row.get("nome_cientifico", ""),
                    "nome_comum": "; ".join(_parse_list(row.get("nome_comum"))),
                }
            )
    return pd.DataFrame(rows)


def build_produtos_for_culture(produtos: pd.DataFrame, cultura: str, incluir_todas: bool) -> pd.DataFrame:
    registros = []
    for _, row in produtos.iterrows():
        indicacoes = _parse_list(row.get("indicacao_uso"))
        for item in indicacoes:
            if not isinstance(item, dict):
                continue
            cultura_item = _safe_str(item.get("cultura"))
            if cultura_item != cultura and not (incluir_todas and cultura_item == "Todas as culturas"):
                continue
            registros.append(
                {
                    "numero_registro": row.get("numero_registro", ""),
                    "marca_comercial": ", ".join(_parse_list(row.get("marca_comercial"))),
                    "titular_registro": row.get("titular_registro", ""),
                    "classe_categoria_agronomica": ", ".join(_parse_list(row.get("classe_categoria_agronomica"))),
                    "formulacao": row.get("formulacao", ""),
                    "ingrediente_ativo": ", ".join(_parse_list(row.get("ingrediente_ativo"))),
                    "modo_acao": ", ".join(_parse_list(row.get("modo_acao"))),
                    "tecnica_aplicacao": ", ".join(_parse_list(row.get("tecnica_aplicacao"))),
                    "classificacao_toxicologica": row.get("classificacao_toxicologica", ""),
                    "classificacao_ambiental": row.get("classificacao_ambiental", ""),
                    "url_agrofit": row.get("url_agrofit", ""),
                    "praga_nome_cientifico": item.get("praga_nome_cientifico", ""),
                    "praga_nome_comum": "; ".join(_parse_list(item.get("praga_nome_comum"))),
                    "tipo_emergencia": _inferir_tipo_emergencia(
                        ", ".join(_parse_list(row.get("classe_categoria_agronomica"))),
                        ", ".join(_parse_list(row.get("ingrediente_ativo"))),
                    ),
                }
            )
    return pd.DataFrame(registros)


def apply_advanced_filters(
    produtos: pd.DataFrame,
    classes: List[str],
    tipo_emergencia: str,
    tecnicas: List[str],
    termo_busca: str,
) -> pd.DataFrame:
    df = produtos.copy()
    if df.empty:
        return df

    if classes:
        mask = pd.Series(False, index=df.index)
        for classe in classes:
            mask = mask | df["classe_categoria_agronomica"].fillna("").str.contains(classe, case=False, regex=False)
        df = df[mask]

    if tipo_emergencia != "Todos":
        df = df[df["tipo_emergencia"] == tipo_emergencia]

    if tecnicas:
        mask = pd.Series(False, index=df.index)
        for tecnica in tecnicas:
            mask = mask | df["tecnica_aplicacao"].fillna("").str.contains(tecnica, case=False, regex=False)
        df = df[mask]

    termo = _safe_str(termo_busca)
    if termo:
        mask = (
            df["marca_comercial"].fillna("").str.contains(termo, case=False, regex=False)
            | df["ingrediente_ativo"].fillna("").str.contains(termo, case=False, regex=False)
            | df["praga_nome_comum"].fillna("").str.contains(termo, case=False, regex=False)
            | df["praga_nome_cientifico"].fillna("").str.contains(termo, case=False, regex=False)
        )
        df = df[mask]

    return df


def render_summary(produtos: pd.DataFrame):
    if produtos.empty:
        st.info("Sem produtos encontrados para a cultura selecionada.")
        return

    st.subheader("Resumo")
    col1, col2, col3 = st.columns(3)
    col1.metric("Produtos", produtos["numero_registro"].nunique())
    col2.metric("Titulares", produtos["titular_registro"].nunique())
    col3.metric("Classes", produtos["classe_categoria_agronomica"].nunique())

    with st.expander("Ver detalhes de classes, modos de ação e ingredientes"):
        classes = sorted({c for row in produtos["classe_categoria_agronomica"].dropna() for c in str(row).split(", ") if c})
        modos = sorted({c for row in produtos["modo_acao"].dropna() for c in str(row).split(", ") if c})
        ingredientes = sorted({c for row in produtos["ingrediente_ativo"].dropna() for c in str(row).split(", ") if c})
        
        st.write(f"**Classes agronômicas ({len(classes)}):** {', '.join(classes)}")
        st.write(f"**Modos de ação ({len(modos)}):** {', '.join(modos)}")
        st.write(f"**Ingredientes ativos ({len(ingredientes)}):** {', '.join(ingredientes)}")


def render_response_levels(produtos: pd.DataFrame):
    if produtos.empty:
        return

    tab1, tab2, tab3 = st.tabs(["Nível 1 · Visão rápida", "Nível 2 · Operacional", "Nível 3 · Técnico"])

    with tab1:
        top_pragas = produtos["praga_nome_comum"].fillna("").replace("", pd.NA).dropna().value_counts().head(5)
        top_classes = produtos["classe_categoria_agronomica"].fillna("").replace("", pd.NA).dropna().value_counts().head(5)
        st.write("**Principais alvos (top 5):**")
        if not top_pragas.empty:
            st.dataframe(top_pragas.rename_axis("alvo").reset_index(name="ocorrências"), hide_index=True, use_container_width=True)
        else:
            st.caption("Sem alvos suficientes para ranking.")
        st.write("**Classes agronômicas mais frequentes:**")
        st.dataframe(top_classes.rename_axis("classe").reset_index(name="ocorrências"), hide_index=True, use_container_width=True)

    with tab2:
        cols = [
            "numero_registro",
            "marca_comercial",
            "tipo_emergencia",
            "tecnica_aplicacao",
            "ingrediente_ativo",
            "praga_nome_comum",
        ]
        st.dataframe(produtos[cols].drop_duplicates(), hide_index=True, use_container_width=True)

    with tab3:
        st.dataframe(produtos.drop_duplicates(), hide_index=True, use_container_width=True)


def render_product_ranking(
    produtos: pd.DataFrame,
    cultura: str,
    filtros_texto: str,
    peso_alvos: int,
    peso_ocorrencias: int,
    peso_tecnicas: int,
    penalidade_tox: int,
    bonus_amb: int,
):
    if produtos.empty:
        return

    base_cols = [
        "numero_registro",
        "marca_comercial",
        "ingrediente_ativo",
        "tipo_emergencia",
        "tecnica_aplicacao",
        "classe_categoria_agronomica",
        "classificacao_toxicologica",
        "classificacao_ambiental",
    ]
    ranking = produtos[base_cols + ["praga_nome_comum", "praga_nome_cientifico"]].copy()
    ranking = ranking.fillna("")

    # Score simples para priorizar produtos com maior cobertura de alvo no contexto atual.
    grouped = (
        ranking.groupby(base_cols, dropna=False)
        .agg(
            ocorrencias=("numero_registro", "size"),
            alvos_comuns=("praga_nome_comum", lambda s: len({x for x in s if x})),
            alvos_cientificos=("praga_nome_cientifico", lambda s: len({x for x in s if x})),
            tecnicas_distintas=("tecnica_aplicacao", lambda s: len({x for x in s if x})),
            penalty_tox=("classificacao_toxicologica", lambda s: max(_toxicologia_penalty(x) for x in s if _safe_str(x)) if any(_safe_str(x) for x in s) else 0),
            bonus_ambiental=("classificacao_ambiental", lambda s: max(_ambiental_bonus(x) for x in s if _safe_str(x)) if any(_safe_str(x) for x in s) else 0),
        )
        .reset_index()
    )

    grouped["score"] = (
        (grouped["alvos_comuns"] + grouped["alvos_cientificos"]) * peso_alvos
        + grouped["ocorrencias"] * peso_ocorrencias
        + grouped["tecnicas_distintas"] * peso_tecnicas
        + grouped["bonus_ambiental"] * bonus_amb
        - grouped["penalty_tox"] * penalidade_tox
    )
    grouped = grouped.sort_values(["score", "ocorrencias", "alvos_comuns"], ascending=False)

    st.subheader("Ranking de produtos (contexto atual)")
    st.caption("Pontuação ajustada pelos pesos selecionados, com bônus ambiental e penalidade toxicológica.")
    st.dataframe(
        grouped[
            [
                "score",
                "numero_registro",
                "marca_comercial",
                "tipo_emergencia",
                "classe_categoria_agronomica",
                "ocorrencias",
                "alvos_comuns",
                "tecnicas_distintas",
                "penalty_tox",
                "bonus_ambiental",
                "tecnica_aplicacao",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )

    export_df = _build_export_dataframe(grouped, cultura=cultura, filtros_texto=filtros_texto)
    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)
    st.download_button(
        "Baixar ranking filtrado (CSV)",
        data=csv_buffer.getvalue(),
        file_name=f"ranking_agrofit_{cultura.replace(' ', '_').lower()}.csv",
        mime="text/csv",
    )


def main():
    st.set_page_config(page_title="Agrofit | Cultura", layout="wide")
    
    # Logo
    logo_path = Path(__file__).resolve().parent / "logomarca.jpg"
    if logo_path.exists():
        st.image(str(logo_path), width=200)
    
    st.title("Agrofit | Consulta por cultura")

    data_dir = _get_data_dir()
    data = load_data(data_dir)

    st.write("### Qual cultura você quer conhecer melhor?")
    culturas = sorted(data["culturas"]["nome"].dropna().unique())
    cultura = st.selectbox("Cultura", culturas, index=0)
    incluir_todas = st.checkbox("Incluir registros de 'Todas as culturas'", value=True)

    pragas_df = build_pragas_for_culture(data["pragas"], cultura, incluir_todas)
    produtos_df = build_produtos_for_culture(data["produto_formulado"], cultura, incluir_todas)

    st.subheader("Filtros avançados")
    col_f1, col_f2, col_f3, col_f4 = st.columns([1, 2, 2, 2])
    classes_disponiveis = _extract_unique_from_col(produtos_df, "classe_categoria_agronomica")
    classes = col_f1.multiselect("Classe agronômica", classes_disponiveis)
    tipo_emergencia = col_f2.selectbox(
        "Tipo de emergência",
        ["Todos", "Pré-emergente", "Pós-emergente", "Ambos", "Não classificado", "Não se aplica"],
        index=0,
    )
    tecnicas_disponiveis = _extract_unique_from_col(produtos_df, "tecnica_aplicacao")
    tecnicas = col_f3.multiselect("Técnica de aplicação", tecnicas_disponiveis)
    termo_busca = col_f4.text_input("Buscar por produto, ingrediente ou alvo")

    with st.expander("Ajuste de pesos do ranking"):
        p1, p2, p3, p4, p5 = st.columns(5)
        peso_alvos = p1.slider("Peso alvos", 1, 5, 2)
        peso_ocorrencias = p2.slider("Peso ocorrências", 1, 5, 1)
        peso_tecnicas = p3.slider("Peso técnicas", 0, 5, 1)
        penalidade_tox = p4.slider("Penalidade tox", 0, 5, 1)
        bonus_amb = p5.slider("Bônus ambiental", 0, 5, 1)

    produtos_filtrados = apply_advanced_filters(produtos_df, classes, tipo_emergencia, tecnicas, termo_busca)

    filtros_texto = (
        f"classe={classes if classes else 'todas'} | "
        f"tipo_emergencia={tipo_emergencia} | "
        f"tecnicas={tecnicas if tecnicas else 'todas'} | "
        f"busca={termo_busca if termo_busca else 'vazio'}"
    )

    render_summary(produtos_filtrados)
    render_response_levels(produtos_filtrados)
    render_product_ranking(
        produtos_filtrados,
        cultura=cultura,
        filtros_texto=filtros_texto,
        peso_alvos=peso_alvos,
        peso_ocorrencias=peso_ocorrencias,
        peso_tecnicas=peso_tecnicas,
        penalidade_tox=penalidade_tox,
        bonus_amb=bonus_amb,
    )

    st.subheader("Pragas associadas")
    st.dataframe(pragas_df, use_container_width=True, hide_index=True)

    st.subheader("Produtos formulados indicados")
    st.dataframe(produtos_filtrados, use_container_width=True, hide_index=True)
    _render_export_produtos_filtrados(produtos_filtrados, cultura=cultura, filtros_texto=filtros_texto)


if __name__ == "__main__":
    main()
