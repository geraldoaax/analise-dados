# 📁 Guia do .gitignore - Projeto Análise de Ciclos

## 🎯 Visão Geral

Este arquivo `.gitignore` foi criado especificamente para o projeto de **Análise de Ciclos** que utiliza:

- **Python** (Flask + Pandas)
- **Dados Excel** para análise
- **Ambiente virtual** (venv)
- **Templates HTML** com Plotly

## 📋 O que está sendo ignorado

### 🐍 Python & Ambiente Virtual

- ✅ `__pycache__/` - Cache do Python
- ✅ `*.pyc` - Arquivos compilados
- ✅ `venv/` - Ambiente virtual completo
- ✅ `.env` - Variáveis de ambiente sensíveis

### 🌐 Web & Flask

- ✅ `instance/` - Configurações de instância Flask
- ✅ `.webassets-cache` - Cache de assets web
- ✅ `flask_session/` - Sessões do Flask

### 💻 IDEs & Editores

- ✅ `.vscode/` - Configurações do VS Code
- ✅ `.idea/` - Configurações do PyCharm
- ✅ `*.swp`, `*.swo` - Arquivos temporários

### 🖥️ Sistema Operacional

- ✅ `.DS_Store` (macOS)
- ✅ `Thumbs.db` (Windows)
- ✅ `*~` (Linux)

### 📊 Dados & Cache

- ✅ `*.log` - Arquivos de log
- ✅ `cache/` - Diretórios de cache
- ✅ `*.tmp` - Arquivos temporários

## ⚠️ IMPORTANTE: Arquivos Excel

### 📁 CicloDetalhado/\*.xlsx

**ATUALMENTE**: Os arquivos Excel **NÃO** estão sendo ignorados.

**Recomendações**:

#### ✅ **Para incluir no Git** (atual):

- **Vantagens**:

  - Dados disponíveis para todos os desenvolvedores
  - Facilita teste e desenvolvimento
  - Histórico de mudanças nos dados

- **Desvantagens**:
  - Aumenta o tamanho do repositório
  - Arquivos binários não mostram diff útil
  - Pode conter dados sensíveis

#### ❌ **Para excluir do Git**:

Se quiser ignorar os arquivos Excel, descomente as linhas no `.gitignore`:

```gitignore
# Arquivos grandes de dados (descomente se necessário)
*.xlsx
*.xls
*.csv
CicloDetalhado/*.xlsx
```

**Como proceder se excluir**:

1. Crie uma pasta `sample_data/` com dados de exemplo menores
2. Documente como obter os dados reais
3. Use variáveis de ambiente para caminhos de dados

## 🚀 Comandos Git Úteis

### Primeiro commit:

```bash
git add .
git commit -m "🎉 Projeto inicial de análise de ciclos"
```

### Verificar o que está sendo ignorado:

```bash
git status --ignored
```

### Verificar se um arquivo específico está sendo ignorado:

```bash
git check-ignore -v nome_do_arquivo
```

### Forçar adicionar um arquivo ignorado (se necessário):

```bash
git add -f arquivo_ignorado.txt
```

## 🔧 Personalizações

### Para este projeto específico:

1. **Logs de desenvolvimento**: Se quiser manter alguns logs no Git, crie uma exceção:

   ```gitignore
   *.log
   !important.log
   ```

2. **Configurações locais**: Para configurações específicas de desenvolvimento:

   ```gitignore
   config.py
   !config.example.py
   ```

3. **Outputs de análise**: Se gerar relatórios/gráficos:
   ```gitignore
   outputs/
   reports/
   exports/
   ```

## 📝 Manutenção

### Quando adicionar novas regras:

1. **Identifique o padrão** do que deve ser ignorado
2. **Adicione na seção apropriada** do `.gitignore`
3. **Comente** o que a regra faz
4. **Teste** com `git status`

### Exemplo de adição:

```gitignore
# ============================================================================
# ESPECÍFICO DESTE PROJETO - ANÁLISE DE CICLOS
# ============================================================================

# Novos outputs de relatórios
relatorios_*.pdf
dashboard_exports/
```

## 🎯 Boas Práticas

1. **✅ Sempre ignore**:

   - Arquivos de senha/API keys
   - Ambiente virtual (`venv/`)
   - Cache e arquivos temporários
   - Configurações específicas do IDE

2. **⚠️ Considere ignorar**:

   - Arquivos grandes de dados
   - Logs detalhados
   - Outputs temporários

3. **❌ Nunca ignore**:
   - Código fonte principal
   - Arquivos de configuração (templates)
   - Documentação
   - Testes

## 🆘 Problemas Comuns

### "Arquivo ainda aparece no Git após adicionar ao .gitignore"

**Solução**: O arquivo já estava sendo rastreado. Remova do índice:

```bash
git rm --cached nome_do_arquivo
git commit -m "Remove arquivo do tracking"
```

### "Quero ignorar uma pasta inteira exceto um arquivo"

**Solução**:

```gitignore
pasta/
!pasta/arquivo_importante.txt
```

### "Arquivo .env aparece no status"

**Verificação**: Confirme que está escrito corretamente no `.gitignore` e que não há espaços extras.

---

## 📞 Suporte

Se tiver dúvidas sobre o `.gitignore`, consulte:

- [Documentação oficial do Git](https://git-scm.com/docs/gitignore)
- [gitignore.io](https://gitignore.io) - Gerador online
- Este arquivo para referência específica do projeto

---

**Última atualização**: Criado junto com o projeto de análise de ciclos
**Mantido por**: Equipe de desenvolvimento
