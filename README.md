# Sistema de Análise de Ciclo - Refatoração para Arquitetura em Camadas

## 📋 Visão Geral

Este projeto foi refatorado de uma aplicação Flask monolítica para uma arquitetura em camadas usando **FastAPI**, seguindo os princípios do **NestJS** para melhor organização, manutenibilidade e escalabilidade.

## 🏗️ Arquitetura

### Estrutura de Camadas

```
app/
├── dto/                    # Objetos de Transferência de Dados
│   ├── __init__.py
│   └── cycle_dto.py       # DTOs para validação de entrada/saída
├── repositories/          # Acesso ao banco de dados
│   ├── __init__.py
│   └── cycle_repository.py # Repository com cache inteligente
├── services/             # Regras de negócio
│   ├── __init__.py
│   └── cycle_service.py  # Lógica de processamento
├── controllers/          # Endpoints HTTP
│   ├── __init__.py
│   └── cycle_controller.py # Controllers FastAPI
└── modules/              # Agrupamento organizacional
    ├── __init__.py
    └── cycle_module.py   # Módulo que agrupa componentes
```

### Responsabilidades por Camada

#### 1. **DTOs (Data Transfer Objects)**

- **Responsabilidade**: Validação de entrada e saída de dados
- **Tecnologia**: Pydantic
- **Benefícios**: Validação automática, documentação automática da API

#### 2. **Repositories**

- **Responsabilidade**: Acesso aos dados (Excel files)
- **Funcionalidades**: Cache inteligente, detecção de mudanças de arquivos
- **Benefícios**: Isolamento da lógica de acesso a dados

#### 3. **Services**

- **Responsabilidade**: Regras de negócio e processamento
- **Funcionalidades**: Filtros, agregações, cálculos de produtividade
- **Benefícios**: Lógica de negócio centralizada e reutilizável

#### 4. **Controllers**

- **Responsabilidade**: Definição dos endpoints HTTP
- **Tecnologia**: FastAPI
- **Benefícios**: Documentação automática, validação automática

#### 5. **Modules**

- **Responsabilidade**: Agrupamento e configuração de componentes
- **Funcionalidades**: Dependency injection, singleton pattern
- **Benefícios**: Organização modular, facilita testes

## 🚀 Como Executar

### 1. Configurar Ambiente Virtual

```bash
# Criar ambiente virtual (se não existir)
python -m venv venv

# Ativar ambiente virtual
# Windows (PowerShell/CMD):
venv\Scripts\activate

# Windows (WSL/Linux):
.\venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate
```

### 2. Instalar Dependências

```bash
# Com ambiente virtual ativado
pip install -r requirements.txt
```

### 3. Executar a Aplicação

```bash
# Com ambiente virtual ativado
python main.py
```

### 4. Desativar Ambiente Virtual (quando terminar)

```bash
deactivate
```

## 🔧 Gerenciamento do Ambiente Virtual

### Comandos Úteis

```bash
# Verificar se o ambiente virtual está ativo
# O prompt deve mostrar (venv) no início
(venv) C:\Users\usuario\projeto>

# Listar pacotes instalados
pip list

# Atualizar pip
python -m pip install --upgrade pip

# Gerar requirements.txt atualizado
pip freeze > requirements.txt

# Remover ambiente virtual (se necessário)
# Windows:
rmdir /s venv

# Linux/macOS:
rm -rf venv
```

### Estrutura do Ambiente Virtual

```
venv/
├── Scripts/              # Windows (activate, python, pip)
├── bin/                  # Linux/macOS (activate, python, pip)
├── include/              # Headers Python
├── lib/                  # Bibliotecas instaladas
└── pyvenv.cfg           # Configuração do ambiente
```

### 3. Acessar a Aplicação

- **Interface Web**: http://127.0.0.1:8000
- **Documentação da API**: http://127.0.0.1:8000/docs
- **Documentação ReDoc**: http://127.0.0.1:8000/redoc
- **Health Check**: http://127.0.0.1:8000/health

## 📊 Endpoints da API

### Análise de Ciclos

- `GET /api/cycles_by_year_month` - Ciclos por ano/mês
- `GET /api/cycles_by_type_input` - Ciclos por tipo de input

### Análise de Produção

- `GET /api/production_by_activity_type` - Produção por tipo de atividade

### Análise de Produtividade

- `GET /api/productivity_analysis` - Análise geral de produtividade
- `GET /api/productivity_by_equipment` - Produtividade por equipamento

### Gerenciamento de Cache

- `POST /api/clear_cache` - Limpar cache
- `GET /api/cache_status` - Status do cache

## 🔧 Parâmetros de Filtro

Todos os endpoints suportam os seguintes parâmetros de query:

- `data_inicio` (YYYY-MM-DD): Data de início do período
- `data_fim` (YYYY-MM-DD): Data de fim do período
- `tipos_input` (string): Tipos de input separados por vírgula
- `frota_transporte` (string): Frotas de transporte separadas por vírgula

### Exemplo de Uso

```
GET /api/cycles_by_year_month?data_inicio=2024-01-01&data_fim=2024-12-31&tipos_input=Minério,Estéril
```

## 🧪 Benefícios da Refatoração

### 1. **Separação de Responsabilidades**

- Cada camada tem uma responsabilidade bem definida
- Facilita manutenção e testes

### 2. **Validação Automática**

- Pydantic valida automaticamente entrada e saída
- Reduz erros de runtime

### 3. **Documentação Automática**

- FastAPI gera documentação interativa automaticamente
- Swagger UI e ReDoc incluídos

### 4. **Cache Inteligente**

- Repository detecta mudanças nos arquivos Excel
- Evita reprocessamento desnecessário

### 5. **Tratamento de Erros**

- Exceções centralizadas e padronizadas
- Logs detalhados para debugging

### 6. **Escalabilidade**

- Arquitetura modular facilita adição de novos recursos
- Dependency injection permite fácil substituição de componentes

### 7. **Testabilidade**

- Cada camada pode ser testada independentemente
- Mocks e stubs facilitam testes unitários

## 📈 Melhorias Implementadas

### Performance

- Cache inteligente com detecção de mudanças
- Processamento otimizado de dados
- Logs de performance detalhados

### Manutenibilidade

- Código organizado em camadas
- Nomes consistentes e descritivos
- Documentação inline

### Robustez

- Validação de entrada rigorosa
- Tratamento de exceções abrangente
- Logs estruturados

### Usabilidade

- Documentação automática da API
- Endpoints RESTful padronizados
- Respostas JSON consistentes

## 🔄 Migração do Flask para FastAPI

### Principais Mudanças

1. **Framework**: Flask → FastAPI
2. **Validação**: Manual → Pydantic automática
3. **Documentação**: Manual → Automática
4. **Performance**: Síncrono → Assíncrono (quando apropriado)
5. **Tipagem**: Dinâmica → Estática com type hints

### Compatibilidade

- Todos os endpoints mantêm a mesma funcionalidade
- Parâmetros de query preservados
- Respostas JSON mantêm o mesmo formato

## 🛠️ Próximos Passos

### Funcionalidades Sugeridas

1. **Testes Unitários**: Implementar testes para cada camada
2. **Banco de Dados**: Migrar de Excel para banco relacional
3. **Autenticação**: Adicionar sistema de autenticação
4. **Cache Redis**: Implementar cache distribuído
5. **Monitoramento**: Adicionar métricas e alertas

### Padrões de Desenvolvimento

- **`PADRAO_FILTROS_COMBOBOX.md`**: Documento completo para implementação de novos filtros de combobox seguindo a arquitetura estabelecida
- **`EXEMPLO_IMPLEMENTACAO_FILTRO.md`**: Exemplo prático de implementação de filtro para coluna "Local"
- **`RESUMO_LLM_FILTROS.md`**: Resumo rápido para implementação rápida de filtros pela LLM
- **`INSTRUCOES_USO_FILTROS.md`**: Instruções completas de uso do sistema de filtros
- **`INDICE_DOCUMENTACAO.md`**: Índice completo de toda a documentação criada

### Melhorias Técnicas

1. **Async/Await**: Implementar processamento assíncrono
2. **Background Tasks**: Processamento em background
3. **Rate Limiting**: Limitar requisições por usuário
4. **Compressão**: Comprimir respostas grandes
5. **Caching**: Cache de respostas HTTP

## 📝 Logs e Monitoramento

O sistema inclui logs detalhados para:

- Performance de cada operação
- Status do cache
- Erros e exceções
- Filtros aplicados
- Quantidade de dados processados

### Exemplo de Log

```
2024-01-15 10:30:45 - app.services.cycle_service - INFO - 🔄 Processando dados de ciclos por ano/mês...
2024-01-15 10:30:46 - app.repositories.cycle_repository - INFO - ✅ Usando dados do cache (arquivos não modificados)
2024-01-15 10:30:47 - app.services.cycle_service - INFO - ✅ Processamento concluído em 1.23s
2024-01-15 10:30:47 - app.controllers.cycle_controller - INFO - 📊 Dados retornados: 24 períodos
```

## 🤝 Contribuição

Para contribuir com o projeto:

1. Siga a arquitetura em camadas estabelecida
2. Mantenha a separação de responsabilidades
3. Adicione testes para novas funcionalidades
4. Documente mudanças na API
5. Mantenha logs detalhados

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.
