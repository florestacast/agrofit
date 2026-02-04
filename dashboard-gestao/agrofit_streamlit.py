from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, List

import pandas as pd
import streamlit as st


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
                    "classificacao_toxicologica": row.get("classificacao_toxicologica", ""),
                    "classificacao_ambiental": row.get("classificacao_ambiental", ""),
                    "url_agrofit": row.get("url_agrofit", ""),
                    "praga_nome_cientifico": item.get("praga_nome_cientifico", ""),
                    "praga_nome_comum": "; ".join(_parse_list(item.get("praga_nome_comum"))),
                }
            )
    return pd.DataFrame(registros)


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

    render_summary(produtos_df)

    st.subheader("Pragas associadas")
    st.dataframe(pragas_df, use_container_width=True, hide_index=True)

    st.subheader("Produtos formulados indicados")
    st.dataframe(produtos_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
