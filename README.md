# Análise de Ciclos

Este projeto Python oferece uma ferramenta para ler e consolidar dados de ciclos a partir de arquivos Excel, apresentando análises interativas através de uma interface web.

## Funcionalidades

- Leitura e união automática de todos os arquivos `.xlsx` presentes na pasta `CicloDetalhado`.
- Interface web interativa construída com Flask.
- Visualização de dados através de gráficos (atualmente, contagem de ciclos por ano/mês).
- Estrutura modular para fácil adição de novas análises e tipos de gráficos.

## Pré-requisitos

- Python 3.x

## Configuração e Execução

Siga os passos abaixo para configurar e executar o projeto em seu ambiente local:

### 1. Clonar o Repositório (se aplicável)

```bash
git clone <URL_DO_SEU_REPOSITORIO>
cd analise_ciclo
```

### 2. Criar e Ativar o Ambiente Virtual

É altamente recomendável usar um ambiente virtual para gerenciar as dependências do projeto. Isso evita conflitos com outras instalações Python.

**No Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

**No macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as Dependências

Com o ambiente virtual ativado, instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

### 4. Preparar os Dados

Certifique-se de que seus arquivos Excel (`.xlsx`) estejam localizados na pasta `CicloDetalhado/` dentro do diretório raiz do projeto. O script espera que cada arquivo Excel contenha uma coluna de data, que será usada para as análises. Por padrão, o código espera uma coluna chamada `Data`.

### 5. Executar a Aplicação

Após instalar as dependências e preparar os dados, você pode iniciar a aplicação Flask:

```bash
python app.py
```

### 6. Acessar a Interface Web

Abra seu navegador e acesse:

[http://127.0.0.1:5000](http://127.0.0.1:5000)

## Estrutura do Projeto

```
analise_ciclo/
├── CicloDetalhado/             # Contém os arquivos Excel com os dados de ciclo
│   ├── CicloDetalhadoSLDM_01012024_31122024.xlsx
│   └── CicloDetalhadoSLDM_01012025_25082025.xlsx
├── templates/                  # Contém os templates HTML da interface web
│   └── index.html
├── static/                     # Contém arquivos estáticos (CSS, JS personalizados, etc.)
├── app.py                      # Lógica principal da aplicação Flask e rotas da API
├── requirements.txt            # Lista de dependências do Python
└── README.md                   # Este arquivo
```

## Como Adicionar Novas Análises

Para adicionar novas análises, siga os passos:

1.  **No `app.py`:**
    *   Crie uma nova rota `@app.route('/api/sua_nova_analise')`.
    *   Dentro da função, carregue os dados (`df = load_data()`) e realize sua análise com `pandas`.
    *   Retorne os resultados em formato JSON usando `jsonify(seus_dados.to_dict(orient='records'))`.

2.  **No `templates/index.html`:**
    *   Adicione um novo item ao menu (`<li><a href="#" onclick="showAnalysis('sua_nova_analise')">Sua Nova Análise</a></li>`).
    *   Na função `showAnalysis(analysisType)`, adicione um novo `else if (analysisType === 'sua_nova_analise')`.
    *   Dentro deste bloco, faça um `fetch` para sua nova rota de API (`/api/sua_nova_analise`) e use Plotly.js para criar o gráfico desejado com os dados retornados.

