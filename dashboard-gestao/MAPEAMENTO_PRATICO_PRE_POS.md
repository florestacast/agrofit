# Mapeamento Prático: Sistema Pré/Pós-Emergentes Agrofit

## 📊 Situação Atual dos Dados

### Dados Descobertos
- **Total de Herbicidas**: 28 produtos
- **Plantas Daninhas**: 100 tipos mapeadas
- **Estrutura de Indicações**: JSON em `indicacao_uso` com schema:
  ```json
  [
    {
      "cultura": "Cana-de-açúcar",
      "praga_nome_cientifico": "Acanthospermum hispidum",
      "praga_nome_comum": "Carrapicho-de-carneiro"
    }
  ]
  ```

### Observação Crítica ⚠️
A base Agrofit **NÃO POSSUI um campo específico** que classifique herbicidas como "pré-emergente" ou "pós-emergente". 

## 🔍 Por Que Pré/Pós-Emergente Não Está Explícito?

### Conceito Agronômico
- **Pré-emergente**: Herbicida aplicado **antes da germinação** da planta daninha
- **Pós-emergente**: Herbicida aplicado **após a planta daninha emergir**

Esta é uma **propriedade da aplicação**, não do produto em si. Alguns herbicidas podem ser usados de ambas as formas dependendo da situação.

### Opções de Implementação

#### **Opção 1: Usar Modo de Ação (Recomendado)**
Mapear ingredientes ativos por características de modo de ação: | Modo de Ação | Tipo |
|---|---|
| Absorção via folha + contato rápido | Pós-emergente |
| Absorção via solo + residual | Pré-emergente |
| Sistêmico de movimento rápido | Pós-emergente |
| Residual no solo | Pré-emergente |

**Exemplos:**
- **Atrazina** → Pré-emergente (residual no solo)
- **2,4-D** → Pós-emergente (contato/sistêmico foliar)
- **Glifosato** → Pós-emergente (sistêmico ágil)

#### **Opção 2: Criar Campo Inferido**
Analisar indicações de uso e técnicas de aplicação para **inferir probabilidade**: 
- Se técnica = "Trat. Sementes" → Pré-emergente
- Se indicação = produto com rápido efeito em plantas desenvolvidas → Pós-emergente

#### **Opção 3: Adicionar Tabela de Lookup**
Criar arquivo `herbicida_tipo_emergencia.csv` com mapeamento manual:
```
numero_registro,tipo,confianca
9520,pre-emergente,0.95
12620,pre-emergente,0.90
```

#### **Opção 4: Dados Externos**
Integrar com API Agrofit oficial ou IBAMA que pode ter esta classificação.

## 📋 Mapeamento de Ingredientes Ativos (Base para Classificação)

### Herbicidas Encontrados (28 total)

| # | Marca | Ingrediente Ativo | Classe | Modo de Ação Inferido |
|---|---|---|---|---|
| 1 | DK MAX | Atrazina | Triazina | Pré-emergente (residual) |
| 2 | DK Plus | Ametrina | Triazina | Pré-emergente (residual) |
| 3 | DMA 806 BR | 2,4-D-dimetilamina | Ácido ariloxialcanóico | Pós-emergente |
| 4 | DORAI | Dibrometo de diquate | Bipiridílio | Pós-emergente (contato rápido) |
| 5 | Daga | Haloxifope-P-metílico | Ariloxifenoxipropiônico | Pós-emergente |
| 6 | Danado | Picloram | Piridinocarboxílico | Pós-emergente |

*(Ver script `gerar_mapeamento_completo.py` para lista com todos 28)*

## 🏗️ Solução Recomendada para Dashboard

### Fase 1: MVP (Quick Win)
Implementar **Opção 1** (Modo de Ação) com tabela de lookup manual:

```python
HERBICIDA_TIPO = {
    'Atrazina': 'pre-emergente',
    'Ametrina': 'pre-emergente',
    '2,4-D': 'pos-emergente',
    'Glifosato': 'pos-emergente',
    'Diquate': 'pos-emergente',
    # ... completar com outros
}

def classificar_herbicida(ingrediente_ativo: str) -> str:
    for ing, tipo in HERBICIDA_TIPO.items():
        if ing.lower() in ingrediente_ativo.lower():
            return tipo
    return 'desconhecido'
```

### Fase 2: Integração com Banco
```sql
-- Tabela de referência
CREATE TABLE herbicida_tipo_emergencia (
    id INT PRIMARY KEY,
    numero_registro INT,
    tipo ENUM('pre-emergente', 'pos-emergente', 'ambos'),
    confianca DECIMAL(3,2),
    fonte VARCHAR(50),
    FOREIGN KEY (numero_registro) REFERENCES produto_formulado(numero_registro)
);
```

### Fase 3: Interface de Busca
```
Pesquisa de Herbicidas
├─ Cultura: [Dropdown culturas]
├─ Tipo de Emergência: [Pré] [Pós] [Ambos]
├─ Planta Alvo: [Texto/Dropdown plantas daninhas]
└─ Buscar

Resultados:
├─ DK MAX (Pré-emergente)
│  └─ Indicado para Cana-de-açúcar contra Carrapicho
├─ DMA 806 BR (Pós-emergente)
│  └─ Indicado para Soja contra Buva
```

## 📝 Estrutura de Dados Completada

### Arquivos Essenciais
- ✅ `produto_formulado.csv` (100 produtos)
- ✅ `ingrediente_ativo.csv` (lookup de ingredientes)
- ✅ `planta_daninha.csv` (100 pragas/plantas)
- ✅ `cultura.csv` (culturas)
- ✅ `tecnica_aplicacao.csv` (8 técnicas)

### Tabelas a Criar
- 🔄 `herbicida_tipo_emergencia.csv` (mapeamento pré/pós)
- 🔄 `modo_acao_emergencia.csv` (referência modo de ação)

## 🎯 Próximos Passos Recomendados

1. **Confirmar com usuário**: Qual opção de implementação preferida?
   - Modo de ação (Opção 1)
   - Tabela de lookup manual (Opção 3)
   - Dados externos (Opção 4)

2. **Criar script de classificação** baseado na escolha

3. **Popular banco de dados** com relações corretas

4. **Validar com agrônomo** se classificações fazem sentido

---

**Última atualização**: Análise de dados concluída  
**Status**: Aguardando decisão de arquitetura
