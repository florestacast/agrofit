# 🔗 Diagrama de Relacionamentos - AGROFIT PRÉ/PÓS-EMERGENTES

## Arquitetura Relacional para Busca de Combinações

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     🌱 SISTEMA AGROFIT - RELACIONAMENTOS                      │
└─────────────────────────────────────────────────────────────────────────────┘

                              ⭐ NÚCLEO CENTRAL ⭐
                           PRODUTO_FORMULADO
                    (18 colunas - MASTER/FATO)
                          │
                ┌─────────┼─────────┬──────────┬──────────────┐
                │         │         │          │              │
                ▼         ▼         ▼          ▼              ▼
        ┌──────────┐ ┌──────────┐ ┌────────┐ ┌────────────┐ ┌─────────┐
        │CLASSES   │ │INGREDI-  │ │TÉCNICA │ │MODO_AÇÃO   │ │INDICAÇÃO│
        │CATEGOR   │ │ENTE_ATIVO│ │APLICAÇÃO│ │           │ │PRODUTO  │
        │AGRONOMIC │ │          │ │        │ │ (filtrar  │ │(CULTURA │
        │  🎯      │ │🌿 ATIVO  │ │ 🎯PRÉ/ │ │ modo)     │ │+ PRAGA/ │
        │          │ │QUÍMICO   │ │ PÓS    │ │           │ │DANINHA) │
        └──────────┘ └──────────┘ └────────┘ └────────────┘ └─────────┘
            │              │           │           │              │
            │ (LOOKUP)      │ (LOOKUP)  │ (LOOKUP)  │ (LOOKUP)     │ (JSON)
            │              │           │           │              │
            ▼              ▼           ▼           ▼              ▼
        ┌──────────┐ ┌──────────┐ ┌────────┐ ┌────────────┐ ┌─────────┐
        │ CLASSE   │ │INGREDI-  │ │TÉCNICA │ │ MODO      │ │CULTURA  │
        │CATEGORIA │ │ENTE_ATIVO│ │APLICAÇÃO│ │ AÇÃO      │ │  (nome) │
        │ (nome)   │ │ DETALHADO│ │ (nome) │ │ (nome)    │ │         │
        └──────────┘ └──────────┘ └────────┘ └────────────┘ └─────────┘
                                                                    │
                                                                    │ (associada)
                                                                    │
                                                    ┌───────────────┼──────────┐
                                                    │               │          │
                                                    ▼               ▼          ▼
                                         ┌─────────────────┐ ┌──────────┐ ┌──────────┐
                                         │ PRAGA .csv      │ │PLANTA    │ │ CULTURA  │
                                         │ classificação   │ │DANINHA   │ │ (nome)   │
                                         │ nome_cientifico │ │          │ │          │
                                         │ nome_comum      │ │nome_cient│ │ (lookup) │
                                         │ cultura[]       │ │nome_comum│ │          │
                                         └─────────────────┘ └──────────┘ └──────────┘

                           📊 TABELAS DE SUPORTE

    ┌─────────────┐ ┌──────────────────┐ ┌─────────────────┐ ┌─────────────┐
    │MARCA_COMERC │ │TITULAR_REGISTRO  │ │CLASSIFICAÇÃO    │ │FORMULAÇÃO   │
    │ (nome)      │ │ (nome)           │ │TOXICOLÓGICA     │ │ (nome)      │
    │             │ │                  │ │ (nome)          │ │             │
    └─────────────┘ └──────────────────┘ └─────────────────┘ └─────────────┘

    ┌──────────────────────┐ ┌────────────────────┐ ┌──────────────┐
    │CLASSIFICAÇÃO         │ │PRODUTO_TÉCNICO     │ │VERSÃO        │
    │AMBIENTAL             │ │ (derivado)         │ │ (metadata)   │
    │ (nome)               │ │                    │ │              │
    └──────────────────────┘ └────────────────────┘ └──────────────┘
```

---

## 📋 FLUXO DE DADOS PARA BUSCA PRÉ/PÓS-EMERGENTE

```
USUÁRIO QUER ENCONTRAR >> "Pré-emergentes para Soja"
                            │
                            ▼
                ┌─────────────────────────────┐
                │ FILTRO 1: Classe Agronomica │
                │ classe = "Pré-emergente"    │
                └─────────────────────────────┘
                            │
                            ▼
            ┌──────────────────────────────────────┐
            │ FILTRO 2: Indicação de Uso           │
            │ indicacao_uso CONTÉM "Soja"          │
            │ E ("praga" OU "daninha" filtrado)    │
            └──────────────────────────────────────┘
                            │
                            ▼
        ┌────────────────────────────────────────────┐
        │ ENRIQUECIMENTO 1: Ingredientes Ativos      │
        │ JOIN com INGREDIENTE_ATIVO.csv             │
        │ Para mostrar químico/biológico             │
        └────────────────────────────────────────────┘
                            │
                            ▼
        ┌────────────────────────────────────────────┐
        │ ENRIQUECIMENTO 2: Modo de Ação             │
        │ JOIN com MODO_ACAO.csv                     │
        │ Para explicar como funciona                │
        └────────────────────────────────────────────┘
                            │
                            ▼
        ┌────────────────────────────────────────────┐
        │ ENRIQUECIMENTO 3: Técnica de Aplicação     │
        │ JOIN com TECNICA_APLICACAO.csv             │
        │ Para indicar como aplicar                  │
        └────────────────────────────────────────────┘
                            │
                            ▼
        ┌────────────────────────────────────────────┐
        │ RESULTADO FINAL                            │
        │ ✓ Produto (marca, registro)                │
        │ ✓ Ativo (ingrediente + grupo químico)      │
        │ ✓ Modo (como funciona)                     │
        │ ✓ Aplicação (técnica)                      │
        │ ✓ Toxicidade (classificação)               │
        │ ✓ Ambiental (impacto)                      │
        └────────────────────────────────────────────┘
```

---

## 🎯 CASOS DE USO PRINCIPAIS

### Caso 1: Buscar Pré-Emergentes para Cultura X
```
ENTRADA: Cultura = "Milho"
         Tipo = "Pré-emergente"

SQL:
  SELECT pf.* 
  FROM produto_formulado pf
  WHERE pf.classe_categoria_agronomica LIKE '%pré-emergente%'
    AND pf.indicacao_uso LIKE '%Milho%'
  LIMIT 20;

SAÍDA:
  ✓ 15 produtos pré-emergentes para Milho
  ✓ Mostra marca, ingrediente ativo, modo de ação
```

### Caso 2: Buscar Pós-Emergentes para Praga Específica
```
ENTRADA: Praga = "Broca-do-milho"
         Tipo = "Pós-emergente"

SQL:
  SELECT pf.*
  FROM produto_formulado pf
  WHERE pf.classe_categoria_agronomica LIKE '%pós-emergente%'
    AND pf.indicacao_uso LIKE '%Broca-do-milho%'
  LIMIT 20;

SAÍDA:
  ✓ 8 produtos pós-emergentes para Broca-do-milho
  ✓ Combina com técnica de aplicação correta
```

### Caso 3: Buscar Combinações Seguras
```
ENTRADA: Cultura = "Soja"
         Praga = "Lagarta-falsa-medideira"

SQL:
  SELECT pf.*, ia.grupo_quimico, ta.nome as tecnica
  FROM produto_formulado pf
  LEFT JOIN ingrediente_ativo ia ON pf.ingrediente_ativo = ia.nome_comum
  LEFT JOIN tecnica_aplicacao ta ON pf.tecnica_aplicacao = ta.nome
  WHERE pf.indicacao_uso LIKE '%Soja%'
    AND pf.indicacao_uso LIKE '%Lagarta-falsa-medideira%'
    AND pf.classificacao_toxicologica NOT LIKE '%Extremamente%'
  ORDER BY pf.classificacao_toxicologica;

SAÍDA:
  ✓ Produtos ordenados por toxicidade
  ✓ Mostra compatibilidade com aplicação
  ✓ Permite filtrar por segurança
```

### Caso 4: Análise de Ingredientes Comuns
```
ENTRADA: Cultura = "Trigo"
         Tipo = "Herbicida"

SQL:
  SELECT pf.ingrediente_ativo, 
         COUNT(*) as frequencia,
         GROUP_CONCAT(DISTINCT pf.marca_comercial) as marcas
  FROM produto_formulado pf
  WHERE pf.indicacao_uso LIKE '%Trigo%'
    AND pf.classe_categoria_agronomica = 'Herbicida'
  GROUP BY pf.ingrediente_ativo
  ORDER BY frequencia DESC;

SAÍDA:
  ✓ Ingredientes mais usados
  ✓ Quantas marcas disponíveis por ingrediente
  ✓ Facilita comparações
```

---

## 🔑 CHAVES PRIMÁRIAS E ESTRANGEIRAS

| Tabela Principal | PK | FK Referências |
|---|---|---|
| `PRODUTO_FORMULADO` | numero_registro | CLASSE_CATEGORIA (classe_categoria_agronomica) |
| | | INGREDIENTE_ATIVO (ingrediente_ativo) |
| | | MODO_ACAO (modo_acao) |
| | | TECNICA_APLICACAO (tecnica_aplicacao) |
| | | CULTURA (via indicacao_uso - JSON) |
| | | PRAGA (via indicacao_uso - JSON) |
| | | MARCA_COMERCIAL (marca_comercial) |
| | | TITULAR_REGISTRO (titular_registro) |
| | | CLASSIFICACAO_TOXICOLOGICA (classificacao_toxicologica) |
| | | CLASSIFICACAO_AMBIENTAL (classificacao_ambiental) |

---

## 🎓 EXEMPLO DE ESTRUTURA NORMALIZADA PARA BD

### Se criar um banco relacional (PostgreSQL/MySQL):

```sql
-- Tabelas de Dimensão (Lookup)
CREATE TABLE cultura (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE classe_categoria_agronomica (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE ingrediente_ativo (
    id SERIAL PRIMARY KEY,
    nome_comum VARCHAR(100) NOT NULL,
    grupo_quimico VARCHAR(100),
    classe VARCHAR(100)
);

CREATE TABLE modo_acao (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE tecnica_aplicacao (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) UNIQUE NOT NULL
);

-- Tabela de Fatos (Central)
CREATE TABLE produto_formulado (
    numero_registro VARCHAR(50) PRIMARY KEY,
    marca_comercial VARCHAR(200),
    titular_registro VARCHAR(200),
    id_classe_categoria INT REFERENCES classe_categoria_agronomica(id),
    id_ingrediente_ativo INT REFERENCES ingrediente_ativo(id),
    id_modo_acao INT REFERENCES modo_acao(id),
    id_tecnica_aplicacao INT REFERENCES tecnica_aplicacao(id),
    indicacao_uso JSONB,  -- Armazena cultura + praga/daninha
    -- ... outros campos
);

-- Tabela de Junção para Múltiplos Ingredientes
CREATE TABLE produto_ingredientes (
    id SERIAL PRIMARY KEY,
    numero_registro VARCHAR(50) REFERENCES produto_formulado(numero_registro),
    id_ingrediente_ativo INT REFERENCES ingrediente_ativo(id),
    UNIQUE(numero_registro, id_ingrediente_ativo)
);

-- Tabela de Junção para Múltiplas Aplicações
CREATE TABLE produto_tecnicas (
    id SERIAL PRIMARY KEY,
    numero_registro VARCHAR(50) REFERENCES produto_formulado(numero_registro),
    id_tecnica_aplicacao INT REFERENCES tecnica_aplicacao(id),
    UNIQUE(numero_registro, id_tecnica_aplicacao)
);
```

---

## 📊 ESTATÍSTICAS ESPERADAS

Baseado na exploração dos CSVs:

| Métrica | Esperado |
|---------|----------|
| Total de produtos formulados | ~15,000 |
| Pré-emergentes | ~2,000-3,000 |
| Pós-emergentes | ~1,500-2,500 |
| Culturas diferentes | ~80-120 |
| Pragas cadastradas | ~500-800 |
| Ingredientes ativos | ~300-500 |
| Marcas comerciais | ~700-1,000 |
| Técnicas de aplicação | ~10-20 |
| Modo de ação distintos | ~15-30 |

---

## 🚀 Próximas Ações

- [ ] Executar `explorador_agrofit.py` para validação de dados
- [ ] Criar estrutura normalizada em banco de dados relacional
- [ ] Implementar parser de `indicacao_uso` (JSON estruturado)
- [ ] Construir interface de busca interativa
- [ ] Validar combinações permitidas (pré vs pós por cultura)
- [ ] Implementar recomendações inteligentes

---

**Documentação gerada:** 23/03/2026  
**Status:** ✅ Mapeamento relacional completo
