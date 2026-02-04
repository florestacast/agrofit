"""
Script para localizar arquivos CC*.xlsx
"""
from pathlib import Path

print("🔍 DIAGNÓSTICO - Localizando arquivos CC*.xlsx")
print("=" * 60)

# Caminhos a verificar
caminhos = [
    Path(r"D:\Meu Drive\Trabalho\Bracell\Relatorios\Boletins\CC"),
    Path(r"D:\Meu Drive\Trabalho\Bracell\Relatorios\Boletins\CC\Atual\OS_aberta"),
    Path(r"D:\Meu Drive\Trabalho\Bracell\Relatorios\Boletins\CC\Atual\OS_fechada"),
]

for caminho in caminhos:
    print(f"\n📁 Verificando: {caminho}")
    print(f"   Existe? {caminho.exists()}")
    
    if caminho.exists():
        # Buscar arquivos CC*.xlsx
        arquivos_cc = list(caminho.glob("CC*.xlsx"))
        print(f"   Arquivos CC*.xlsx encontrados: {len(arquivos_cc)}")
        
        for arq in arquivos_cc:
            print(f"      ✓ {arq.name}")
        
        # Buscar qualquer .xlsx
        if len(arquivos_cc) == 0:
            todos_xlsx = list(caminho.glob("*.xlsx"))
            print(f"   Outros arquivos .xlsx: {len(todos_xlsx)}")
            for arq in todos_xlsx[:5]:  # Mostrar apenas 5
                print(f"      - {arq.name}")

print("\n" + "=" * 60)