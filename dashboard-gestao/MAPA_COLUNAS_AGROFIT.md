# 📊 Mapa de Colunas e Relacionamentos - Agrofit Embrapa

## 🎯 Objetivo
Mapear todas as colunas disponíveis nos arquivos CSV para construir a mecânica de busca por pré-emergentes e pós-emergentes, com análise de combinações por cultura e momento adequado.

---

## 📋 TABELAS PRINCIPAIS (Core)

### 1. **PRODUTO_FORMULADO.csv** ⭐ (CENTRAL)
**Descrição:** Produtos formulados com informações completas de registro
**18 Colunas:**

| # | Coluna | Tipo | Descrição |
|---|--------|------|-----------|
| 1 | `numero_registro` | ID | Identificador único do produto |
| 2 | `marca_comercial` | TEXT | Nome da marca do produto |
| 3 | `titular_registro` | TEXT | Empresa titular do registro |
| 4 | `produto_biologico` | BOOL | Indica se é produto biológico |
| 5 | **`classe_categoria_agronomica`** | CATEGORICAL | ⚠️ Tipo de produto (ex: pré-emergente, pós-emergente) |
| 6 | `formulacao` | TEXT | Tipo de formulação |
| 7 | **`ingrediente_ativo`** | ARRAY | Princípio ativo do produto |
| 8 | `ingrediente_ativo_detalhado` | ARRAY | Detalhes dos ingredientes ativos |
| 9 | **`modo_acao`** | ARRAY | Como o produto funciona |
| 10 | **`tecnica_aplicacao`** | ARRAY | ⚠️ Método de aplicação (pré/pós) |
| 11 | **`indicacao_uso`** | ARRAY | ⚠️ Culturas + pragas/plantas daninhas |
| 12 | `classificacao_toxicologica` | CATEGORICAL | Nível de toxicidade |
| 13 | `classificacao_ambiental` | CATEGORICAL | Impacto ambiental |
| 14 | `inflamavel` | BOOL | Propriedade física |
| 15 | `corrosivo` | BOOL | Propriedade física |
| 16 | `documento_cadastrado` | BOOL | Status do registro |
| 17 | `produto_agricultura_organica` | BOOL | Certificado orgânico |
| 18 | `url_agrofit` | URL | Link para detalhes no Agrofit |

---

### 2. **PRODUTO_TECNICO.csv**
**Descrição:** Produtos técnicos (princípios ativos puros)
**12 Colunas:**

```
numero_registro
marca_comercial
titular_registro
classe_categoria_agronomica
ingrediente_ativo
classificacao_toxicologica
classificacao_ambiental
formulacao
ingrediente_ativo_detalhado
documento_cadastrado
produto_formulado_vinculado (FK para PRODUTO_FORMULADO)
url_agrofit
```

---

## 🌱 TABELAS DE DIMENSÃO (Lookup/Reference)

### 3. **CULTURA.csv**
**Descrição:** Culturas agrícolas disponíveis
```
nome
```
**Exemplos:** Abacate, Abacaxi, Arroz, Milho, Soja, Trigo...

---

### 4. **PRAGA.csv** ⚠️ IMPORTANTE PARA PRÉ/PÓS
**Descrição:** Pragas organizadas por classificação
**4 Colunas:**

```
classificacao          (ex: Insetos, Doença, Ácaros)
nome_cientifico        (ex: Acanthoscelides obtectus)
nome_comum             (ex: ['Caruncho-do-feijão', 'Gorgulho-do-feijão'])
cultura                (ARRAY de culturas afetadas)
```

---

### 5. **PLANTA_DANINHA.csv**
**Descrição:** Plantas daninhas
**3 Colunas:**

```
nome_cientifico
nome_comum
url_agrofit
```

---

### 6. **INGREDIENTE_ATIVO.csv**
**Descrição:** Ativos químicos/biológicos
**4 Colunas:**

```
nome_comum             (ex: Glifosato, Atrazina)
grupo_quimico          (ex: Fosfônico, Triazinas)
classe                 (ex: Herbicida, Inseticida)
url_agrofit
```

---

### 7. **MODO_ACAO.csv**
**Descrição:** Como o produto atua
```
nome (ex: Contato, Sistêmico, Fumigante)
```

---

### 8. **TECNICA_APLICACAO.csv** 🎯 CHAVE PARA PRÉ/PÓS
**Descrição:** Métodos de aplicação
```
nome (ex: Pulverização, Herbigação, Tratamento de sementes)
```

---

### 9. **FORMULACAO.csv**
**Descrição:** Tipos de formulação
```
nome (ex: Solução aquosa, Pó, Suspensão)
```

---

### 10. **CLASSES_CATEGORIAS_AGRONOMICAS.csv** ⭐ PRÉ/PÓS AQUI!
**Descrição:** Categorias agrônomicas que incluem pré/pós-emergentes
```
nome (ex: Pré-emergente, Pós-emergente, Herbicida Total, Dessecante)
```

---

### 11. **CLASSIFICACAO_TOXICOLOGICA.csv**
**Descrição:** Níveis de toxicidade
```
nome (ex: Classe toxicológica I - Extremamente tóxico)
```

---

### 12. **CLASSIFICACAO_AMBIENTAL.csv**
**Descrição:** Impacto ambiental
```
nome
```

---

### 13. **MARCA_COMERCIAL.csv**
**Descrição:** Fabricantes/distribuidores
```
nome
```

---

### 14. **TITULAR_REGISTRO.csv**
**Descrição:** Empresas titulares de registro
```
nome
```

---

## 🔗 RELACIONAMENTOS PRINCIPAIS

### Fluxo para Busca PRÉ-EMERGENTE/PÓS-EMERGENTE:

```
PRODUTO_FORMULADO
    ├─ classe_categoria_agronomica → CLASSES_CATEGORIAS_AGRONOMICAS
    │  └─ ✅ Filtrar por "Pré-emergente" ou "Pós-emergente"
    │
    ├─ indicacao_uso → CULTURA + PRAGA/PLANTA_DANINHA
    │  └─ Buscar combinações por cultura desejada
    │
    ├─ ingrediente_ativo → INGREDIENTE_ATIVO
    │  └─ Entender o químico/biológico ativo
    │
    ├─ tecnica_aplicacao → TECNICA_APLICACAO
    │  └─ Saber como aplicar
    │
    ├─ modo_acao → MODO_ACAO
    │  └─ Como o produto funciona
    │
    ├─ marca_comercial → MARCA_COMERCIAL
    │  └─ Nome do produto
    │
    └─ titular_registro → TITULAR_REGISTRO
       └─ Fabricante/distribuidor
```

---

## 📊 CAMPOS CRÍTICOS PARA MECÂNICA PRÉ/PÓS

| Campo | Tabela | Uso |
|-------|--------|-----|
| `classe_categoria_agronomica` | PRODUTO_FORMULADO | **Filtro principal** (pré vs pós) |
| `indicacao_uso` | PRODUTO_FORMULADO | Cultura + alvo (praga/daninha) |
| `tecnica_aplicacao` | PRODUTO_FORMULADO | Momento correto (antes/depois) |
| `ingrediente_ativo` | PRODUTO_FORMULADO + INGREDIENTE_ATIVO | Combinações químicas |
| `modo_acao` | PRODUTO_FORMULADO + MODO_ACAO | Efeito esperado |
| `categoria` | PRAGA.csv | Tipo de alvo (inseto, doença, daninha) |
| `cultura` | CULTURA.csv + PRAGA.csv | Contexto agrícola |

---

## 🔍 QUERIES INICIAIS RECOMENDADAS

### Query 1: Buscar todos os pré-emergentes para uma cultura
```sql
SELECT DISTINCT 
    pf.numero_registro,
    pf.marca_comercial,
    pf.classe_categoria_agronomica,
    pf.ingrediente_ativo,
    pf.indicacao_uso
FROM produto_formulado pf
WHERE pf.classe_categoria_agronomica = 'Pré-emergente'
  AND pf.indicacao_uso LIKE '%CulturaDdesejada%'
```

### Query 2: Buscar pós-emergentes para uma praga específica
```sql
SELECT DISTINCT pf.*
FROM produto_formulado pf
WHERE pf.classe_categoria_agronomica = 'Pós-emergente'
  AND pf.indicacao_uso LIKE '%NomeDapraga%'
```

### Query 3: Combinações de ativos para uma cultura
```sql
SELECT DISTINCT 
    pf.ingrediente_ativo,
    COUNT(*) as quantidade_produtos,
    GROUP_CONCAT(DISTINCT pf.marca_comercial) as marcas
FROM produto_formulado pf
WHERE pf.indicacao_uso LIKE '%Cultura%'
GROUP BY pf.ingrediente_ativo
ORDER BY quantidade_produtos DESC
```

---

## 📝 PRÓXIMOS PASSOS

1. ✅ Entender estrutura (FEITO)
2. ⏳ Criar tabelas normalizadas no banco de dados
3. ⏳ Implementar parser de `indicacao_uso` (JSON estruturado)
4. ⏳ Criar interface de busca para pré/pós-emergentes
5. ⏳ Implementar lógica de combinações seguras
6. ⏳ Adicionar validação de momento adequado por cultura

---

## 🗂️ ESTRUTURA DE ARQUIVOS

```
Agrofit_csv/
├── produto_formulado.csv ⭐ (CENTRAL)
├── produto_tecnico.csv
├── ingrediente_ativo.csv
├── cultura.csv
├── praga.csv
├── planta_daninha.csv
├── modo_acao.csv
├── tecnica_aplicacao.csv 🎯
├── classes_categorias_agronomicas.csv 🎯
├── formulacao.csv
├── classificacao_toxicologica.csv
├── classificacao_ambiental.csv
├── marca_comercial.csv
├── titular_registro.csv
├── planta_daninha_nome_comum.csv
├── praga_nome_cientifico.csv
├── praga_nome_comum.csv
└── versao.csv
```

---

**Criado em:** 23/03/2026  
**Status:** Mapa estruturado completo ✅
