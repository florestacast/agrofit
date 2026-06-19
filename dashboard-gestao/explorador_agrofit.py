"""
🌱 EXPLORADOR DE RELACIONAMENTOS AGROFIT
Script para entender estrutura de dados e relacionamentos pré/pós-emergentes
"""

import pandas as pd
import json
from pathlib import Path

# ============================================================================
# 1. CARREGAMENTO DE DADOS
# ============================================================================

DATA_PATH = Path("../Dados/Embrapa/Agrofit_csv")

def load_csv(filename):
    """Carrega um arquivo CSV com tratamento de erros."""
    try:
        return pd.read_csv(DATA_PATH / filename, engine='python', on_bad_lines='skip')
    except Exception as e:
        try:
            return pd.read_csv(DATA_PATH / filename)
        except Exception as e2:
            print(f"❌ Erro ao carregar {filename}: {e2}")
            return None

# Carregar tabelas principais
print("📥 Carregando arquivos CSV...")
df_produto_formulado = load_csv("produto_formulado.csv")
df_ingrediente_ativo = load_csv("ingrediente_ativo.csv")
df_cultura = load_csv("cultura.csv")
df_praga = load_csv("praga.csv")
df_tecnica_aplicacao = load_csv("tecnica_aplicacao.csv")
df_classe_categoria = load_csv("classes_categorias_agronomicas.csv")
df_modo_acao = load_csv("modo_acao.csv")

print("✅ Dados carregados!\n")

# ============================================================================
# 2. EXPLORAÇÃO DE ESTRUTURA
# ============================================================================

def show_table_structure(df, table_name):
    """Mostra estrutura de uma tabela."""
    print(f"\n{'='*70}")
    print(f"📋 TABELA: {table_name.upper()}")
    print(f"{'='*70}")
    print(f"Linhas: {len(df)} | Colunas: {len(df.columns)}")
    print(f"\n📊 Colunas ({len(df.columns)}):")
    for i, col in enumerate(df.columns, 1):
        dtype = df[col].dtype
        nulls = df[col].isna().sum()
        print(f"  {i:2d}. {col:35s} | Tipo: {str(dtype):15s} | Nulos: {nulls:5d}")
    
    print(f"\n📌 Primeiras 2 amostras:")
    print(df.head(2).to_string())

# ============================================================================
# 3. ANÁLISE DE PRÉ/PÓS-EMERGENTES
# ============================================================================

def analyze_categoria_agronomica():
    """Analisa categorias agrônomicas disponíveis."""
    print(f"\n{'='*70}")
    print("🎯 CATEGORIAS AGRÔNOMICAS (pré/pós-emergentes)")
    print(f"{'='*70}")
    
    if df_classe_categoria is not None:
        categorias = df_classe_categoria['nome'].unique()
        print(f"\nTotal de categorias: {len(categorias)}\n")
        for cat in sorted(categorias):
            print(f"  ✓ {cat}")
    
    # Contar por categoria na tabela de produtos
    if df_produto_formulado is not None:
        print(f"\n📊 Distribuição de produtos por categoria:")
        contagem = df_produto_formulado['classe_categoria_agronomica'].value_counts()
        for categoria, count in contagem.items():
            print(f"  {categoria:40s} : {count:5d} produtos")

# ============================================================================
# 4. BUSCA POR PRÉ-EMERGENTES
# ============================================================================

def buscar_pre_emergentes(cultura=None):
    """Busca pré-emergentes opcionalmente filtrando por cultura."""
    print(f"\n{'='*70}")
    print("🌿 PRÉ-EMERGENTES")
    print(f"{'='*70}")
    
    if df_produto_formulado is None:
        print("❌ Dados não carregados")
        return
    
    # Filtrar por pré-emergente
    pre_emergentes = df_produto_formulado[
        df_produto_formulado['classe_categoria_agronomica'].str.contains('pré-emergente', case=False, na=False)
    ]
    
    print(f"\nTotal encontrado: {len(pre_emergentes)} produtos")
    
    if cultura:
        print(f"Filtrando por cultura: {cultura}")
        # Nota: indicacao_uso pode ser JSON/lista, precisa parsing
    
    print(f"\n📋 Amostra de pré-emergentes:")
    cols = ['numero_registro', 'marca_comercial', 'ingrediente_ativo', 'indicacao_uso']
    print(pre_emergentes[cols].head(5).to_string())
    
    return pre_emergentes

# ============================================================================
# 5. BUSCA POR PÓS-EMERGENTES
# ============================================================================

def buscar_pos_emergentes():
    """Busca pós-emergentes."""
    print(f"\n{'='*70}")
    print("🌾 PÓS-EMERGENTES")
    print(f"{'='*70}")
    
    if df_produto_formulado is None:
        print("❌ Dados não carregados")
        return
    
    # Filtrar por pós-emergente
    pos_emergentes = df_produto_formulado[
        df_produto_formulado['classe_categoria_agronomica'].str.contains('pós-emergente', case=False, na=False)
    ]
    
    print(f"\nTotal encontrado: {len(pos_emergentes)} produtos")
    
    print(f"\n📋 Amostra de pós-emergentes:")
    cols = ['numero_registro', 'marca_comercial', 'ingrediente_ativo', 'indicacao_uso']
    print(pos_emergentes[cols].head(5).to_string())
    
    return pos_emergentes

# ============================================================================
# 6. ANÁLISE DE INGREDIENTES ATIVOS
# ============================================================================

def analisar_ingredientes_comuns():
    """Identifica ingredientes ativos mais comuns."""
    print(f"\n{'='*70}")
    print("⚗️  INGREDIENTES ATIVOS MAIS COMUNS")
    print(f"{'='*70}")
    
    if df_ingrediente_ativo is None:
        print("❌ Dados não carregados")
        return
    
    print(f"\nTotal de ingredientes: {len(df_ingrediente_ativo)}")
    print("\n📊 Top 15 ingredientes by frequência:")
    print(df_ingrediente_ativo['nome_comum'].value_counts().head(15).to_string())
    
    print("\n📊 Top 10 grupos químicos:")
    print(df_ingrediente_ativo['grupo_quimico'].value_counts().head(10).to_string())
    
    print("\n📊 Classes de ingredientes:")
    print(df_ingrediente_ativo['classe'].value_counts().to_string())

# ============================================================================
# 7. ANÁLISE DE CULTURAS
# ============================================================================

def analisar_culturas():
    """Analisa culturas disponíveis."""
    print(f"\n{'='*70}")
    print("🌾 CULTURAS DISPONÍVEIS")
    print(f"{'='*70}")
    
    if df_cultura is None:
        print("❌ Dados não carregados")
        return
    
    print(f"\nTotal de culturas: {len(df_cultura)}")
    print("\n🌱 Primeiras 20 culturas:")
    for i, cultura in enumerate(df_cultura['nome'].head(20), 1):
        print(f"  {i:2d}. {cultura}")

# ============================================================================
# 8. ANÁLISE DE TÉCNICAS DE APLICAÇÃO
# ============================================================================

def analisar_tecnicas_aplicacao():
    """Analisa técnicas de aplicação disponíveis."""
    print(f"\n{'='*70}")
    print("🎯 TÉCNICAS DE APLICAÇÃO")
    print(f"{'='*70}")
    
    if df_tecnica_aplicacao is None:
        print("❌ Dados não carregados")
        return
    
    print(f"\nTotal de técnicas: {len(df_tecnica_aplicacao)}")
    print("\n📋 Técnicas disponíveis:")
    for i, tecnica in enumerate(df_tecnica_aplicacao['nome'], 1):
        print(f"  {i:2d}. {tecnica}")

# ============================================================================
# MAIN - EXECUTAR EXPLORAÇÕES
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌱 EXPLORADOR DE DADOS AGROFIT - PRÉ/PÓS-EMERGENTES")
    print("="*70 + "\n")
    
    # Mostrar estruturas
    show_table_structure(df_produto_formulado, "PRODUTO_FORMULADO")
    show_table_structure(df_ingrediente_ativo, "INGREDIENTE_ATIVO")
    
    # Análises
    analyze_categoria_agronomica()
    buscar_pre_emergentes()
    buscar_pos_emergentes()
    analisar_ingredientes_comuns()
    analisar_culturas()
    analisar_tecnicas_aplicacao()
    
    print("\n" + "="*70)
    print("✅ Exploração concluída!")
    print("="*70)
