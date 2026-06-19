"""
Agrofit Dashboard - Consulta por Cultura
========================================
Dashboard interativo para consulta de dados da API Embrapa Agrofit.
Permite rastrear informacoes de pragas, produtos formulados e
ingredientes ativos por cultura, com ranking inteligente.
"""

from __future__ import annotations

import ast
import io
from pathlib import Path
from typing import Iterable, List

import pandas as pd
import streamlit as st


# =============================================================================
# CONSTANTES
# =============================================================================

PRE_EMERGENTE_KEYS = [
    "atrazina", "ametrina", "pendimetalina", "trifluralina",
    "acetoclor", "sulfentrazona", "imazapic", "imazamox", "imazapyr",
]

POS_EMERGENTE_KEYS = [
    "2,4-d", "glifosato", "diquate", "paraquat",
    "haloxifope", "sethoxydim", "clethodim", "fenoxaprop",
    "dicamba", "bentazona", "picloram",
]


# =============================================================================
# FUNCOES AUXILIARES
# =============================================================================

def _safe_str(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


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
        return parsed if isinstance(parsed, list) else [parsed]
    except Exception:
        return [text]


def _contains_culture(cultures: Iterable[dict], target: str) -> bool:
    for item in cultures:
        if isinstance(item, dict) and _safe_str(item.get("nome")) == target:
            return True
    return False


def _extract_unique_from_col(df: pd.DataFrame, col: str) -> List[str]:
    values: set[str] = set()
    if col not in df.columns:
        return []
    for raw in df[col].dropna():
        for item in str(raw).split(", "):
            item = item.strip()
            if item:
                values.add(item)
    return sorted(values)


def _inferir_tipo_emergencia(classe: str, ingrediente_ativo: str) -> str:
    classe_low = _safe_str(classe).lower()
    if "herbicida" not in classe_low:
        return "Nao se aplica"

    ing_low = _safe_str(ingrediente_ativo).lower()
    has_pre = any(k in ing_low for k in PRE_EMERGENTE_KEYS)
    has_pos = any(k in ing_low for k in POS_EMERGENTE_KEYS)

    if has_pre and has_pos:
        return "Ambos"
    if has_pre:
        return "Pre-emergente"
    if has_pos:
        return "Pos-emergente"
    return "Nao classificado"


def _toxicologia_penalty(value: str) -> int:
    text = _safe_str(value).lower()
    if not text:
        return 0
    if "extremamente toxico" in text or "classe i" in text:
        return 2
    if "altamente toxico" in text or "classe ii" in text:
        return 1
    return 0


def _ambiental_bonus(value: str) -> int:
    text = _safe_str(value).lower()
    if not text:
        return 0
    if "improvável" in text or "pouco" in text or "classe iii" in text or "classe iv" in text:
        return 1
    return 0


# =============================================================================
# CARREGAMENTO DE DADOS
# =============================================================================

@st.cache_data(show_spinner=False)
def load_data(base_dir: Path) -> dict[str, pd.DataFrame]:
    arquivos = {
        "culturas": "cultura.csv",
        "pragas": "praga.csv",
        "produto_formulado": "produto_formulado.csv",
    }
    data = {}
    for key, filename in arquivos.items():
        path = base_dir / filename
        try:
            data[key] = pd.read_csv(path)
        except Exception as e:
            st.error(f"Erro ao carregar {filename}: {e}")
            data[key] = pd.DataFrame()
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

    options = [snap.name for snap in snapshots]
    selected = st.sidebar.selectbox(
        "Fonte de dados", options, index=0,
        help="Selecione a versao dos dados",
    )
    selected_dir = snapshots_root / selected / "raw"
    return selected_dir if selected_dir.exists() else fallback


# =============================================================================
# CONSTRUCAO DE DATA FRAMES
# =============================================================================

def build_pragas_for_culture(pragas: pd.DataFrame, cultura: str, incluir_todas: bool) -> pd.DataFrame:
    rows = []
    for _, row in pragas.iterrows():
        culturas = _parse_list(row.get("cultura"))
        if _contains_culture(culturas, cultura) or (
            incluir_todas and _contains_culture(culturas, "Todas as culturas")
        ):
            rows.append({
                "classificacao": row.get("classificacao", ""),
                "nome_cientifico": row.get("nome_cientifico", ""),
                "nome_comum": "; ".join(_parse_list(row.get("nome_comum"))),
            })
    return pd.DataFrame(rows)


def build_produtos_for_culture(produtos: pd.DataFrame, cultura: str, incluir_todas: bool) -> pd.DataFrame:
    registros = []
    for _, row in produtos.iterrows():
        indicacoes = _parse_list(row.get("indicacao_uso"))
        for item in indicacoes:
            if not isinstance(item, dict):
                continue
            cultura_item = _safe_str(item.get("cultura"))
            if cultura_item != cultura and not (
                incluir_todas and cultura_item == "Todas as culturas"
            ):
                continue

            classe_agro = ", ".join(_parse_list(row.get("classe_categoria_agronomica")))
            ing_ativo = ", ".join(_parse_list(row.get("ingrediente_ativo")))

            registros.append({
                "numero_registro": row.get("numero_registro", ""),
                "marca_comercial": ", ".join(_parse_list(row.get("marca_comercial"))),
                "titular_registro": row.get("titular_registro", ""),
                "classe_categoria_agronomica": classe_agro,
                "formulacao": row.get("formulacao", ""),
                "ingrediente_ativo": ing_ativo,
                "modo_acao": ", ".join(_parse_list(row.get("modo_acao"))),
                "tecnica_aplicacao": ", ".join(_parse_list(row.get("tecnica_aplicacao"))),
                "classificacao_toxicologica": row.get("classificacao_toxicologica", ""),
                "classificacao_ambiental": row.get("classificacao_ambiental", ""),
                "url_agrofit": row.get("url_agrofit", ""),
                "praga_nome_cientifico": item.get("praga_nome_cientifico", ""),
                "praga_nome_comum": "; ".join(_parse_list(item.get("praga_nome_comum"))),
                "tipo_emergencia": _inferir_tipo_emergencia(classe_agro, ing_ativo),
            })
    return pd.DataFrame(registros)


# =============================================================================
# FILTROS
# =============================================================================

def apply_advanced_filters(produtos: pd.DataFrame, classes: List[str], tipo_emergencia: str, tecnicas: List[str], termo_busca: str) -> pd.DataFrame:
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
        cols_busca = ["marca_comercial", "ingrediente_ativo", "praga_nome_comum", "praga_nome_cientifico"]
        mask = pd.Series(False, index=df.index)
        for col in cols_busca:
            mask = mask | df[col].fillna("").str.contains(termo, case=False, regex=False)
        df = df[mask]

    return df


# =============================================================================
# COMPONENTES DE RENDERIZACAO
# =============================================================================

def render_sidebar(culturas: List[str]) -> tuple:
    with st.sidebar:
        logo_path = Path(__file__).resolve().parent / "logomarca.jpg"
        if logo_path.exists():
            st.image(str(logo_path), width=180)

        st.markdown("## Agrofit")
        st.caption("Consulta de defensivos agricolas por cultura")
        st.divider()

        st.markdown("### Cultura")
        cultura = st.selectbox("Selecione a cultura", culturas, index=0, label_visibility="collapsed")
        incluir_todas = st.checkbox(
            'Incluir "Todas as culturas"', value=True,
            help="Inclui registros genericos aplicaveis a todas as culturas",
        )
        st.divider()
        st.markdown("### Filtros")
        return cultura, incluir_todas


def render_filtros_avancados(produtos_df: pd.DataFrame) -> dict:
    classes = _extract_unique_from_col(produtos_df, "classe_categoria_agronomica")
    tecnicas = _extract_unique_from_col(produtos_df, "tecnica_aplicacao")

    col1, col2, col3, col4 = st.columns([1.5, 1.5, 2, 2])
    filtros = {
        "classes": col1.multiselect("Classe agronomica", classes, placeholder="Todas as classes"),
        "tipo_emergencia": col2.selectbox(
            "Emergencia",
            ["Todos", "Pre-emergente", "Pos-emergente", "Ambos", "Nao classificado", "Nao se aplica"],
            index=0,
        ),
        "tecnicas": col3.multiselect("Tecnica de aplicacao", tecnicas, placeholder="Todas as tecnicas"),
        "termo_busca": col4.text_input("Buscar", placeholder="Produto, ingrediente ou alvo...", label_visibility="collapsed"),
    }
    return filtros


def render_pesos_ranking() -> dict:
    st.markdown("#### Ajuste do ranking")
    cols = st.columns(5)
    pesos = {
        "peso_alvos": cols[0].slider("Alvos", 1, 5, 2, help="Peso para quantidade de alvos cobertos"),
        "peso_ocorrencias": cols[1].slider("Ocorrencias", 1, 5, 1, help="Peso para frequencia de mencoes"),
        "peso_tecnicas": cols[2].slider("Tecnicas", 0, 5, 1, help="Peso para variedade de tecnicas"),
        "penalidade_tox": cols[3].slider("Pen. toxicologica", 0, 5, 1, help="Penalidade por toxicidade alta"),
        "bonus_amb": cols[4].slider("Bonus ambiental", 0, 5, 1, help="Bonus por baixo impacto ambiental"),
    }
    return pesos


def render_kpis(produtos: pd.DataFrame, pragas: pd.DataFrame):
    if produtos.empty:
        st.info("Nenhum produto encontrado para esta cultura com os filtros atuais.")
        return

    cols = st.columns(5)
    cols[0].metric("Produtos", produtos["numero_registro"].nunique())
    cols[1].metric("Titulares", produtos["titular_registro"].nunique())
    cols[2].metric("Classes", produtos["classe_categoria_agronomica"].nunique())
    cols[3].metric("Pragas", pragas.shape[0])
    cols[4].metric("Ingredientes ativos", produtos["ingrediente_ativo"].nunique())


def render_detalhes_expander(produtos: pd.DataFrame):
    with st.expander("Ver classes, modos de acao e ingredientes em detalhe"):
        classes = sorted({c for row in produtos["classe_categoria_agronomica"].dropna() for c in str(row).split(", ") if c})
        modos = sorted({c for row in produtos["modo_acao"].dropna() for c in str(row).split(", ") if c})
        ingredientes = sorted({c for row in produtos["ingrediente_ativo"].dropna() for c in str(row).split(", ") if c})

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Classes ({len(classes)})**")
            st.caption(", ".join(classes))
        with col2:
            st.markdown(f"**Modos de acao ({len(modos)})**")
            st.caption(", ".join(modos))
        with col3:
            st.markdown(f"**Ingredientes ({len(ingredientes)})**")
            st.caption(", ".join(ingredientes))


def render_graficos(produtos: pd.DataFrame):
    if produtos.empty:
        return

    col1, col2 = st.columns(2)
    with col1:
        classes_counts = (
            produtos["classe_categoria_agronomica"].fillna("").replace("", pd.NA).dropna().value_counts().head(10)
        )
        if not classes_counts.empty:
            st.markdown("**Top 10 classes agronomicas**")
            st.bar_chart(classes_counts)

    with col2:
        emerg_counts = produtos["tipo_emergencia"].fillna("Nao classificado").value_counts()
        if not emerg_counts.empty:
            st.markdown("**Distribuicao por tipo de emergencia**")
            st.bar_chart(emerg_counts)


def render_visao_rapida(produtos: pd.DataFrame):
    col1, col2 = st.columns(2)
    with col1:
        top_pragas = produtos["praga_nome_comum"].fillna("").replace("", pd.NA).dropna().value_counts().head(5)
        st.markdown("**Top 5 alvos (pragas)**")
        if not top_pragas.empty:
            st.dataframe(top_pragas.rename_axis("alvo").reset_index(name="ocorrencias"), hide_index=True, use_container_width=True)
        else:
            st.caption("Nenhum alvo identificado.")
    with col2:
        top_classes = produtos["classe_categoria_agronomica"].fillna("").replace("", pd.NA).dropna().value_counts().head(5)
        st.markdown("**Top 5 classes**")
        if not top_classes.empty:
            st.dataframe(top_classes.rename_axis("classe").reset_index(name="ocorrencias"), hide_index=True, use_container_width=True)
        else:
            st.caption("Nenhuma classe identificada.")


def render_visao_operacional(produtos: pd.DataFrame):
    cols = ["numero_registro", "marca_comercial", "tipo_emergencia", "tecnica_aplicacao", "ingrediente_ativo", "praga_nome_comum"]
    st.dataframe(produtos[cols].drop_duplicates(), hide_index=True, use_container_width=True)


def render_visao_tecnica(produtos: pd.DataFrame):
    st.dataframe(produtos.drop_duplicates(), hide_index=True, use_container_width=True)


def render_ranking(produtos: pd.DataFrame, cultura: str, filtros_texto: str, pesos: dict):
    if produtos.empty:
        return

    base_cols = [
        "numero_registro", "marca_comercial", "ingrediente_ativo",
        "tipo_emergencia", "tecnica_aplicacao", "classe_categoria_agronomica",
        "classificacao_toxicologica", "classificacao_ambiental",
    ]

    ranking = produtos[base_cols + ["praga_nome_comum", "praga_nome_cientifico"]].copy()
    ranking = ranking.fillna("")

    grouped = (
        ranking.groupby(base_cols, dropna=False)
        .agg(
            ocorrencias=("numero_registro", "size"),
            alvos_comuns=("praga_nome_comum", lambda s: len({x for x in s if x})),
            alvos_cientificos=("praga_nome_cientifico", lambda s: len({x for x in s if x})),
            tecnicas_distintas=("tecnica_aplicacao", lambda s: len({x for x in s if x})),
            penalty_tox=(
                "classificacao_toxicologica",
                lambda s: max(_toxicologia_penalty(x) for x in s if _safe_str(x)) if any(_safe_str(x) for x in s) else 0,
            ),
            bonus_ambiental=(
                "classificacao_ambiental",
                lambda s: max(_ambiental_bonus(x) for x in s if _safe_str(x)) if any(_safe_str(x) for x in s) else 0,
            ),
        )
        .reset_index()
    )

    grouped["score"] = (
        (grouped["alvos_comuns"] + grouped["alvos_cientificos"]) * pesos["peso_alvos"]
        + grouped["ocorrencias"] * pesos["peso_ocorrencias"]
        + grouped["tecnicas_distintas"] * pesos["peso_tecnicas"]
        + grouped["bonus_ambiental"] * pesos["bonus_amb"]
        - grouped["penalty_tox"] * pesos["penalidade_tox"]
    )
    grouped = grouped.sort_values(["score", "ocorrencias", "alvos_comuns"], ascending=False)

    st.markdown("---")
    st.subheader("Ranking inteligente de produtos")
    st.caption("Pontuacao ajustada por cobertura de alvos, ocorrencias, tecnicas, com bonus ambiental e penalidade toxicologica.")

    cols_exibir = [
        "score", "numero_registro", "marca_comercial", "tipo_emergencia",
        "classe_categoria_agronomica", "ocorrencias", "alvos_comuns",
        "tecnicas_distintas", "penalty_tox", "bonus_ambiental",
    ]
    st.dataframe(
        grouped[cols_exibir],
        hide_index=True,
        use_container_width=True,
        column_config={
            "score": st.column_config.NumberColumn("Score", format="%d"),
            "ocorrencias": st.column_config.NumberColumn("Ocorr.", format="%d"),
            "alvos_comuns": st.column_config.NumberColumn("Alvos", format="%d"),
        },
    )

    export_df = grouped.copy()
    export_df.insert(0, "cultura", cultura)
    export_df.insert(1, "filtros_aplicados", filtros_texto)

    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)
    st.download_button(
        "Baixar ranking (CSV)",
        data=csv_buffer.getvalue(),
        file_name=f"ranking_agrofit_{cultura.replace(' ', '_').lower()}.csv",
        mime="text/csv",
        use_container_width=True,
    )


def render_exportar(produtos: pd.DataFrame, cultura: str, filtros_texto: str):
    if produtos.empty:
        return

    col1, col2 = st.columns(2)
    export_df = produtos.copy()
    export_df.insert(0, "cultura", cultura)
    export_df.insert(1, "filtros_aplicados", filtros_texto)

    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)

    with col1:
        st.download_button(
            "Baixar produtos filtrados (CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"produtos_agrofit_{cultura.replace(' ', '_').lower()}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col2:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            export_df.to_excel(writer, sheet_name="Produtos", index=False)
        st.download_button(
            "Baixar como Excel (XLSX)",
            data=excel_buffer.getvalue(),
            file_name=f"produtos_agrofit_{cultura.replace(' ', '_').lower()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# =============================================================================
# PAGINA PRINCIPAL
# =============================================================================

def main():
    st.set_page_config(
        page_title="Agrofit - Consulta por Cultura",
        page_icon=":herb:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    data_dir = _get_data_dir()
    with st.spinner("Carregando dados..."):
        data = load_data(data_dir)

    if data["culturas"].empty:
        st.error("Dados nao encontrados. Verifique o diretorio de dados.")
        st.stop()

    culturas = sorted(data["culturas"]["nome"].dropna().unique())
    cultura, incluir_todas = render_sidebar(culturas)

    with st.spinner("Processando dados..."):
        pragas_df = build_pragas_for_culture(data["pragas"], cultura, incluir_todas)
        produtos_df = build_produtos_for_culture(data["produto_formulado"], cultura, incluir_todas)

    with st.container():
        st.markdown(f"## Analise: **{cultura}**")
        filtros = render_filtros_avancados(produtos_df)

    with st.expander("Configuracoes do ranking inteligente", expanded=False):
        pesos = render_pesos_ranking()

    produtos_filtrados = apply_advanced_filters(
        produtos_df,
        filtros["classes"],
        filtros["tipo_emergencia"],
        filtros["tecnicas"],
        filtros["termo_busca"],
    )

    filtros_texto = (
        f"classe={filtros['classes'] if filtros['classes'] else 'todas'} | "
        f"emergencia={filtros['tipo_emergencia']} | "
        f"tecnicas={filtros['tecnicas'] if filtros['tecnicas'] else 'todas'} | "
        f"busca={filtros['termo_busca'] if filtros['termo_busca'] else 'vazio'}"
    )

    render_kpis(produtos_filtrados, pragas_df)

    if not produtos_filtrados.empty:
        render_detalhes_expander(produtos_filtrados)

    render_graficos(produtos_filtrados)

    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["Visao rapida", "Operacional", "Tecnico", "Ranking"])

    with tab1:
        render_visao_rapida(produtos_filtrados)
    with tab2:
        render_visao_operacional(produtos_filtrados)
    with tab3:
        render_visao_tecnica(produtos_filtrados)
    with tab4:
        render_ranking(produtos_filtrados, cultura=cultura, filtros_texto=filtros_texto, pesos=pesos)

    st.markdown("---")
    st.subheader("Pragas associadas a cultura")
    if not pragas_df.empty:
        st.dataframe(pragas_df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma praga cadastrada para esta cultura.")

    st.subheader("Produtos formulados indicados")
    if not produtos_filtrados.empty:
        st.dataframe(produtos_filtrados, use_container_width=True, hide_index=True)
        render_exportar(produtos_filtrados, cultura=cultura, filtros_texto=filtros_texto)
    else:
        st.info("Nenhum produto encontrado. Tente ajustar os filtros.")


if __name__ == "__main__":
    main()
