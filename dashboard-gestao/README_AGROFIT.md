# Agrofit Dashboard

Dashboard interativo para consulta de dados da API Embrapa Agrofit, permitindo rastrear informações de pragas, produtos formulados e ingredientes ativos por cultura.

## Estrutura do Projeto

```
dashboard-gestao/
├── agrofit_streamlit.py       # Dashboard principal
├── requirements.txt            # Dependências
├── logomarca.jpg              # Logo
├── .streamlit/
│   └── config.toml            # Configurações do Streamlit
└── ../Dados/Embrapa/
    ├── Agrofit_csv/           # Dados estáticos
    └── Agrofit_snapshots/     # Snapshots versionados
```

## Instalação Local

```bash
cd "D:\Meu Drive\Trabalho\Floresta_cast\ADM\P&D&I\dashboard-gestao"
pip install -r requirements.txt
streamlit run agrofit_streamlit.py
```

## Deploy no Streamlit Cloud

### Pré-requisitos
1. Repositório GitHub: [github.com/florestacast/agrofit](https://github.com/florestacast/agrofit)
2. Upload dos arquivos:
   - `agrofit_streamlit.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `logomarca.jpg`
   - Pasta `Dados/Embrapa/Agrofit_csv/` com os CSVs

### Passos

1. Fazer upload para o repositório:
```bash
cd "D:\Meu Drive\Trabalho\Floresta_cast\ADM\P&D&I\dashboard-gestao"
git init
git add agrofit_streamlit.py requirements.txt logomarca.jpg .streamlit/ .gitignore
git add ../Dados/Embrapa/Agrofit_csv/*.csv
git commit -m "Agrofit dashboard - Floresta Cast"
git branch -M main
git remote add origin https://github.com/florestacast/agrofit.git
git push -u origin main
```

2. Deploy no Streamlit Cloud:
   - Acesse [share.streamlit.io](https://share.streamlit.io)
   - Conecte sua conta GitHub
   - Clique em "New app"
   - Selecione:
     - Repository: `florestacast/agrofit`
     - Branch: `main`
     - Main file path: `agrofit_streamlit.py`
   - Clique em "Deploy!"

URL do app: `https://florestacast-agrofit.streamlit.app`

## Atualização de Dados

Para atualizar os dados da API:

```bash
cd "D:\Meu Drive\Trabalho\Floresta_cast\ADM\P&D&I\API\Embrapa"
python update_agrofit_pipeline.py
```

Isso cria um novo snapshot em `Dados/Embrapa/Agrofit_snapshots/` que pode ser selecionado no dashboard.

## Funcionalidades

- **Filtro por cultura**: Selecione a cultura para visualizar informações específicas
- **Pragas associadas**: Lista de pragas (nome científico e comum) que afetam a cultura
- **Produtos formulados**: Produtos indicados com detalhes de ingredientes ativos, classificação e fabricantes
- **Resumo estatístico**: Contadores e listas de classes, modos de ação e ingredientes únicos
- **Seleção de snapshot**: Escolha entre versões históricas dos dados

## Tecnologias

- Python 3.10+
- Streamlit
- Pandas
