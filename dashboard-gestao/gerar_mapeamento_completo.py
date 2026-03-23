#!/usr/bin/env python3
"""
Script: Gerador de Mapeamento de Herbicidas Pré/Pós-Emergentes

Objetivo: Extrair dados completos dos herbicidas Agrofit e gerar
mapeamento inferido de tipo de emergência baseado em modo de ação
e características químicas.

Uso:
    python3 gerar_mapeamento_completo.py > herbicidas_mapeamento.json
    python3 gerar_mapeamento_completo.py --csv > herbicidas_mapeamento.csv
"""

import pandas as pd
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# ==================== CONFIGURAÇÃO ====================
DATA_PATH = Path("/media/florestacast/Dados/Meu Drive/Trabalho/Floresta_cast/00_ADM/P&D&I/Dados/Embrapa/Agrofit_csv")

# Mapeamento de ingredientes ativos para tipo de emergência
INGREDIENTES_MAPEAMENTO = {
    # PRÉ-EMERGENTES (residual no solo)
    'atrazina': 'pre-emergente',
    'ametrina': 'pre-emergente',
    'pendimetalina': 'pre-emergente',
    'trifluralina': 'pre-emergente',
    'butaclor': 'pre-emergente',
    'acetoclor': 'pre-emergente',
    'oxadiazona': 'pre-emergente',
    'sulfentrazona': 'pre-emergente',
    'prosulfuron': 'pre-emergente',
    'flumetsulam': 'pre-emergente',
    'imazapic': 'pre-emergente',
    'imazamox': 'pre-emergente',
    'imazapyr': 'pre-emergente',
    'nicosulfuron': 'pre-emergente',
    'mesotriona': 'pre-emergente',
    
    # PÓS-EMERGENTES (contato/sistêmico foliar)
    '2,4-d': 'pos-emergente',
    'glifosato': 'pos-emergente',
    'diquate': 'pos-emergente',
    'paraquat': 'pos-emergente',
    'haloxifope': 'pos-emergente',
    'sethoxydim': 'pos-emergente',
    'clethodim': 'pos-emergente',
    'fenoxaprop': 'pos-emergente',
    '2,4-db': 'pos-emergente',
    'dicamba': 'pos-emergente',
    'bentazona': 'pos-emergente',
    'glufosinate': 'pos-emergente',
    'glufosinato': 'pos-emergente',
    'picloram': 'pos-emergente',
    'clomafenozida': 'pos-emergente',
}

# ==================== FUNÇÕES ====================

def inferir_tipo_emergencia(ingrediente_ativo: str) -> tuple[str, float]:
    """
    Inferir tipo de emergência baseado no ingrediente ativo.
    
    Retorna: (tipo, confiança)
        tipo: 'pre-emergente', 'pos-emergente', ou 'desconhecido'
        confiança: 0.0 a 1.0
    """
    ing_lower = ingrediente_ativo.lower()
    
    # Buscar correspondências
    for ing_mapeado, tipo in INGREDIENTES_MAPEAMENTO.items():
        if ing_mapeado in ing_lower:
            # Maior confiança se for correspondência exata vs parcial
            confianca = 0.95 if ing_lower.strip() == ing_mapeado else 0.80
            return tipo, confianca
    
    # Fallback: tentar heurísticas
    if any(x in ing_lower for x in ['residual', 'solo', 'absorção radicular']):
        return 'pre-emergente', 0.60
    elif any(x in ing_lower for x in ['contato', 'foliar', 'sistêmico']):
        return 'pos-emergente', 0.60
    
    return 'desconhecido', 0.00

def processar_indicacoes_uso(indicacao_uso_str: str) -> Dict:
    """Parse JSON de indicacao_uso e retornar estrutura limpa."""
    try:
        if pd.isna(indicacao_uso_str):
            return {}
        
        # Limpar string JSON (aspas simples → duplas)
        uso = json.loads(str(indicacao_uso_str).replace("'", '"'))
        
        if isinstance(uso, list):
            return {
                'total_indicacoes': len(uso),
                'culturas': list(set([u.get('cultura', 'N/A') for u in uso if isinstance(u, dict)])),
                'pragas': list(set([u.get('praga_nome_comum', 'N/A') for u in uso if isinstance(u, dict)]))[:5]  # top 5
            }
        return {}
    except Exception as e:
        return {'erro': str(e)}

def gerar_csv(herbicidas: List[Dict]) -> str:
    """Gerar saída em formato CSV."""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'numero_registro', 'marca_comercial', 'ingrediente_ativo', 
        'classe_categoria', 'tipo_emergencia', 'confianca',
        'total_culturas', 'total_pragas', 'tecnica_aplicacao'
    ])
    
    writer.writeheader()
    for h in herbicidas:
        writer.writerow({
            'numero_registro': h['numero_registro'],
            'marca_comercial': ', '.join(h['marca_comercial']) if isinstance(h['marca_comercial'], list) else h['marca_comercial'],
            'ingrediente_ativo': ', '.join(h['ingrediente_ativo']) if isinstance(h['ingrediente_ativo'], list) else h['ingrediente_ativo'],
            'classe_categoria': ', '.join(h['classe_categoria']) if isinstance(h['classe_categoria'], list) else h['classe_categoria'],
            'tipo_emergencia': h['tipo_emergencia'],
            'confianca': f"{h['confianca']:.2f}",
            'total_culturas': h['total_culturas'],
            'total_pragas': h['total_pragas'],
            'tecnica_aplicacao': h['tecnica_aplicacao'],
        })
    
    return output.getvalue()

def main():
    """Função principal."""
    print("🌾 GERADOR DE MAPEAMENTO HERBICIDAS AGROFIT", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    # Carregar dados
    print(f"📂 Carregando dados de: {DATA_PATH}", file=sys.stderr)
    df = pd.read_csv(DATA_PATH / "produto_formulado.csv", on_bad_lines='skip')
    
    # Filtrar herbicidas
    herbicidas_df = df[df['classe_categoria_agronomica'].astype(str).str.contains('Herbicida', case=False, na=False)]
    print(f"✅ Encontrados {len(herbicidas_df)} herbicidas", file=sys.stderr)
    
    # Processar cada herbicida
    herbicidas = []
    for idx, (i, row) in enumerate(herbicidas_df.iterrows(), 1):
        # Inferir tipo de emergência
        ing_str = str(row.get('ingrediente_ativo', ''))
        tipo, confianca = inferir_tipo_emergencia(ing_str)
        
        # Processar indicações de uso
        indicacoes = processar_indicacoes_uso(row.get('indicacao_uso'))
        
        herbicida = {
            'numero_registro': row['numero_registro'],
            'marca_comercial': row['marca_comercial'],
            'ingrediente_ativo': row['ingrediente_ativo'],
            'classe_categoria': row['classe_categoria_agronomica'],
            'tipo_emergencia': tipo,
            'confianca': confianca,
            'formulacao': row['formulacao'],
            'tecnica_aplicacao': row['tecnica_aplicacao'],
            'total_culturas': indicacoes.get('total_indicacoes', 0),
            'total_pragas': len(indicacoes.get('pragas', [])),
            'culturas_amostra': indicacoes.get('culturas', [])[:3],
            'pragas_amostra': indicacoes.get('pragas', [])[:3],
        }
        herbicidas.append(herbicida)
        
        print(f"  {idx:2d}. {herbicida['marca_comercial']} -> {tipo}", file=sys.stderr)
    
    print("", file=sys.stderr)
    
    # Output em JSON ou CSV
    if '--csv' in sys.argv:
        output = gerar_csv(herbicidas)
    else:
        # JSON format
        output_data = {
            'metadata': {
                'total_herbicidas': len(herbicidas),
                'data': pd.Timestamp.now().isoformat(),
                'fonte': 'Agrofit Embrapa',
            },
            'herbicidas': herbicidas
        }
        output = json.dumps(output_data, indent=2, ensure_ascii=False)
    
    print(output)
    
    # Estatísticas
    tipos_count = {}
    for h in herbicidas:
        tipo = h['tipo_emergencia']
        tipos_count[tipo] = tipos_count.get(tipo, 0) + 1
    
    print("\n📊 RESUMO", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    for tipo, count in sorted(tipos_count.items()):
        pct = (count / len(herbicidas)) * 100
        print(f"  {tipo:20s}: {count:3d} ({pct:5.1f}%)", file=sys.stderr)

if __name__ == '__main__':
    main()
