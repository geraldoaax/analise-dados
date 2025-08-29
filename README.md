# Análise de Ciclos

Este projeto Python oferece uma ferramenta para ler e consolidar dados de ciclos a partir de arquivos Excel, apresentando análises interativas através de uma interface web.

## Funcionalidades

- Leitura e união automática de todos os arquivos `.xlsx` presentes na pasta `CicloDetalhado`.
- Interface web interativa construída com Flask.
- Visualização de dados através de múltiplos gráficos:
  - Contagem de ciclos por ano/mês
  - Ciclos por tipo input
  - Produção por tipo de atividade (soma de massa)
  - Produção por especificação de material (soma de massa)
  - Produção por material (soma de massa)
  - **🚛 Produtividade (Toneladas)** (total de toneladas por período e produtividade por ciclo)
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

Certifique-se de que seus arquivos Excel (`.xlsx`) estejam localizados na pasta `CicloDetalhado/` dentro do diretório raiz do projeto. O script espera que cada arquivo Excel contenha as seguintes colunas:

- `DataHoraInicio`: Data e hora de início do ciclo
- `Tipo Input`: Tipo do input do ciclo
- `Massa`: Massa transportada (para relatórios de produção)
- `Tipo de atividade`: Tipo da atividade realizada
- `Especificacao de material`: Especificação do material transportado
- `Material`: Material transportado

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

    - Crie uma nova rota `@app.route('/api/sua_nova_analise')`.
    - Dentro da função, carregue os dados (`df = load_data()`) e realize sua análise com `pandas`.
    - Retorne os resultados em formato JSON usando `jsonify(seus_dados.to_dict(orient='records'))`.

2.  **No `templates/index.html`:**
    - Adicione um novo item ao menu (`<li><a href="#" onclick="selecionarAnalise('sua_nova_analise')">Sua Nova Análise</a></li>`).
    - Na função `selecionarAnalise(tipo)`, adicione uma nova condição para atualizar o título.
    - Na função `showAnalysis(analysisType)`, adicione um novo `else if (analysisType === 'sua_nova_analise')`.
    - Dentro deste bloco, faça um `fetch` para sua nova rota de API (`/api/sua_nova_analise`) e use Plotly.js para criar o gráfico desejado com os dados retornados.

### Exemplos de Análises Disponíveis

- **Ciclos por Ano/Mês**: Contagem de ciclos agrupados por período
- **Ciclos por Tipo Input**: Contagem de ciclos segmentados por tipo de input
- **Produção por Tipo de Atividade**: Soma de massa por tipo de atividade
- **Produção por Esp. Material**: Soma de massa por especificação de material (top 3 especificações + "Outros")
- **Produção por Material**: Soma de massa por material (top 3 materiais + "Outros")
- **🚛 Produtividade (Toneladas)**:
  - Total de toneladas transportadas por período
  - Produtividade por ciclo (toneladas/ciclo)
  - Visualização simples e clara com dois eixos
  - Foco na métrica principal: toneladas
