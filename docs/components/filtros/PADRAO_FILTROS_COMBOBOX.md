# 📋 Padrão de Implementação de Filtros Combobox

## 🎯 Objetivo

Este documento estabelece o padrão para implementação de novos filtros de combobox no sistema de análise de ciclo, permitindo que a LLM gere automaticamente novos filtros baseados em colunas existentes seguindo a arquitetura estabelecida.

## 🏗️ Arquitetura dos Filtros

### Estrutura Atual

O projeto possui filtros implementados para:

- **Tipos de Input** (`tipos_input`)
- **Frota de Transporte** (`frota_transporte`)
- **Frota de Carga** (`frota_carga`)
- **Tag de Carga** (`tag_carga`)

### Padrão de Implementação

Cada filtro segue a mesma estrutura em 4 camadas:

```
DTO → Repository → Service → Controller
```

## 📝 1. DTO (Data Transfer Object)

### Localização: `app/dto/cycle_dto.py`

#### Padrão para Filtros de Combobox:

```python
class DateRangeDTO(BaseModel):
    """DTO para filtros de data e combobox"""
    data_inicio: Optional[str] = Field(None, description="Data de início no formato YYYY-MM-DD")
    data_fim: Optional[str] = Field(None, description="Data de fim no formato YYYY-MM-DD")

    # Filtros existentes
    tipos_input: Optional[List[str]] = Field(None, description="Lista de tipos de input para filtrar")
    frota_transporte: Optional[List[str]] = Field(None, description="Lista de frotas de transporte para filtrar")
    frota_carga: Optional[List[str]] = Field(None, description="Lista de frotas de carga para filtrar")
    tag_carga: Optional[List[str]] = Field(None, description="Lista de tags de carga para filtrar")

    # NOVO FILTRO - Siga este padrão:
    nome_coluna: Optional[List[str]] = Field(None, description="Lista de valores da coluna 'Nome Coluna' para filtrar")
```

#### Regras para Nomenclatura:

- **Nome do campo**: Use `snake_case` baseado no nome da coluna
- **Descrição**: Sempre inclua "Lista de valores da coluna 'Nome Coluna' para filtrar"
- **Tipo**: Sempre `Optional[List[str]]`
- **Validação**: Não é necessário adicionar validadores específicos

## 🗄️ 2. Repository

### Localização: `app/repositories/cycle_repository.py`

#### Padrão para Métodos de Filtros:

```python
def get_available_nome_coluna(self) -> List[str]:
    """Obtém valores únicos da coluna 'Nome Coluna' para filtros"""
    try:
        df = self.get_raw_data()

        if 'Nome Coluna' not in df.columns:
            logger.warning("⚠️ Coluna 'Nome Coluna' não encontrada nos dados")
            return []

        # Obter valores únicos, ordenados e sem valores nulos
        valores_unicos = df['Nome Coluna'].dropna().unique().tolist()
        valores_unicos.sort()

        logger.info(f"✅ Valores únicos obtidos para 'Nome Coluna': {len(valores_unicos)} valores")
        return valores_unicos

    except Exception as e:
        logger.error(f"❌ Erro ao obter valores únicos de 'Nome Coluna': {str(e)}")
        return []
```

#### Regras para Implementação:

- **Nome do método**: `get_available_nome_coluna()` (baseado no nome da coluna)
- **Logging**: Sempre inclua logs de sucesso e erro
- **Tratamento de erros**: Retorne lista vazia em caso de erro
- **Ordenação**: Sempre ordene os valores alfabeticamente
- **Validação**: Verifique se a coluna existe antes de processar

## ⚙️ 3. Service

### Localização: `app/services/cycle_service.py`

#### Padrão para Aplicação de Filtros:

```python
def _apply_filters(self, df: pd.DataFrame, filters: DateRangeDTO) -> pd.DataFrame:
    """Aplica filtros aos dados"""
    logger.info("🔄 Aplicando filtros aos dados...")

    # ... filtros existentes ...

    # NOVO FILTRO - Siga este padrão:
    if filters.nome_coluna and len(filters.nome_coluna) > 0:
        if 'Nome Coluna' in df.columns:
            df = df[df['Nome Coluna'].isin(filters.nome_coluna)]
            logger.info(f"🔍 Aplicado filtro de Nome Coluna: {filters.nome_coluna}")
            logger.info(f"📊 Registros após filtro de Nome Coluna: {len(df):,}")
        else:
            logger.warning("⚠️ Coluna 'Nome Coluna' não encontrada para aplicar filtro")

    return df
```

#### Padrão para Métodos de Filtros Disponíveis:

```python
def get_available_nome_coluna(self) -> List[str]:
    """Obtém valores únicos da coluna 'Nome Coluna' para filtros"""
    logger.info("🔄 Obtendo valores únicos da coluna 'Nome Coluna'...")

    try:
        result = self.cycle_repository.get_available_nome_coluna()

        logger.info(f"✅ Valores únicos obtidos: {len(result)} valores")
        return result

    except Exception as e:
        logger.error(f"❌ Erro ao obter valores únicos: {str(e)}")
        return []
```

#### Regras para Implementação:

- **Nome do método**: `get_available_nome_coluna()` (baseado no nome da coluna)
- **Logging**: Sempre inclua logs de início, sucesso e erro
- **Delegação**: Sempre delegue para o repository
- **Tratamento de erros**: Retorne lista vazia em caso de erro

## 🎮 4. Controller

### Localização: `app/controllers/cycle_controller.py`

#### Padrão para Endpoints de Filtros:

```python
@router.get("/nome_coluna", response_model=List[str])
async def get_nome_coluna(cycle_service: CycleService = Depends(get_cycle_service)):
    """Obtém lista de valores da coluna 'Nome Coluna' disponíveis para filtros"""
    logger.info("🚀 API nome_coluna chamada")
    api_start_time = time.time()

    try:
        result = cycle_service.get_available_nome_coluna()

        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API nome_coluna concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Valores retornados: {len(result)}")

        return result

    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API nome_coluna após {error_time:.2f}s: {str(e)}")
        logger.exception("Detalhes do erro:")
        raise HTTPException(status_code=500, detail=f"Erro ao obter valores: {str(e)}")
```

#### Regras para Implementação:

- **Nome do endpoint**: `/nome_coluna` (baseado no nome da coluna)
- **Método HTTP**: Sempre `GET`
- **Response model**: Sempre `List[str]`
- **Logging**: Sempre inclua logs de início, sucesso e erro
- **Medição de tempo**: Sempre meça o tempo de execução
- **Tratamento de erros**: Sempre use HTTPException com status 500

## 🔧 5. Interface HTML/JavaScript

### Localização: `templates/index.html`

#### Padrão para Combobox HTML:

```html
<!-- NOVO FILTRO - Siga este padrão -->
<div class="multiselect-container">
  <div
    class="multiselect-display"
    id="nomeColunaDisplay"
    onclick="toggleNomeColunaDropdown()"
  >
    <span id="nomeColunaText">Selecionar Nome Coluna</span>
    <span class="multiselect-arrow">▼</span>
  </div>

  <div class="multiselect-dropdown" id="nomeColunaDropdown">
    <div class="multiselect-option">
      <input
        type="checkbox"
        id="selectAllNomeColuna"
        onchange="toggleAllNomeColuna(this)"
      />
      <label for="selectAllNomeColuna">Selecionar Todos</label>
    </div>
    <!-- Opções serão preenchidas dinamicamente -->
  </div>
</div>
```

#### Padrão para JavaScript:

```javascript
// NOVO FILTRO - Siga este padrão

// Função para carregar opções
async function loadNomeColunaOptions() {
  try {
    const response = await fetch("/api/nome_coluna");
    const options = await response.json();

    const dropdown = document.getElementById("nomeColunaDropdown");

    // Adicionar opções (pular a primeira que é "Selecionar Todos")
    for (let i = 1; i < dropdown.children.length; i++) {
      dropdown.removeChild(dropdown.children[i]);
    }

    options.forEach((option) => {
      const optionDiv = document.createElement("div");
      optionDiv.className = "multiselect-option";

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.id = `nomeColuna_${option.replace(/\s+/g, "_")}`;
      checkbox.value = option;
      checkbox.onchange = () => updateNomeColunaSelection();

      const label = document.createElement("label");
      label.htmlFor = checkbox.id;
      label.textContent = option;

      optionDiv.appendChild(checkbox);
      optionDiv.appendChild(label);
      dropdown.appendChild(optionDiv);
    });

    // Selecionar todos por padrão
    document.getElementById("selectAllNomeColuna").checked = true;
    updateNomeColunaSelection();
  } catch (error) {
    console.error("Erro ao carregar opções:", error);
  }
}

// Função para alternar dropdown
function toggleNomeColunaDropdown() {
  const dropdown = document.getElementById("nomeColunaDropdown");
  const arrow = document.querySelector("#nomeColunaDisplay .multiselect-arrow");

  if (dropdown.classList.contains("show")) {
    dropdown.classList.remove("show");
    arrow.style.transform = "rotate(0deg)";
  } else {
    // Fechar outros dropdowns
    document
      .querySelectorAll(".multiselect-dropdown.show")
      .forEach((d) => d.classList.remove("show"));
    document
      .querySelectorAll(".multiselect-arrow")
      .forEach((a) => (a.style.transform = "rotate(0deg)"));

    dropdown.classList.add("show");
    arrow.style.transform = "rotate(180deg)";
  }
}

// Função para selecionar/desselecionar todos
function toggleAllNomeColuna(selectAll) {
  const checkboxes = document.querySelectorAll(
    '#nomeColunaDropdown input[type="checkbox"]:not(#selectAllNomeColuna)'
  );
  checkboxes.forEach((checkbox) => {
    checkbox.checked = selectAll.checked;
  });
  updateNomeColunaSelection();
}

// Função para atualizar seleção
function updateNomeColunaSelection() {
  const checkboxes = document.querySelectorAll(
    '#nomeColunaDropdown input[type="checkbox"]:not(#selectAllNomeColuna)'
  );
  const selectedOptions = Array.from(checkboxes)
    .filter((checkbox) => checkbox.checked)
    .map((checkbox) => checkbox.value);

  const displayText = document.getElementById("nomeColunaText");

  if (selectedOptions.length === 0) {
    displayText.textContent = "Selecionar Nome Coluna";
  } else if (selectedOptions.length === checkboxes.length) {
    displayText.textContent = "Todos selecionados";
  } else if (selectedOptions.length === 1) {
    displayText.textContent = selectedOptions[0];
  } else {
    displayText.textContent = `${selectedOptions.length} selecionados`;
  }

  // Atualizar estado do "Selecionar Todos"
  const selectAll = document.getElementById("selectAllNomeColuna");
  selectAll.checked = selectedOptions.length === checkboxes.length;

  // Atualizar filtros globais
  updateGlobalFilters();
}

// Função para obter valores selecionados
function getSelectedNomeColuna() {
  const checkboxes = document.querySelectorAll(
    '#nomeColunaDropdown input[type="checkbox"]:not(#selectAllNomeColuna)'
  );
  return Array.from(checkboxes)
    .filter((checkbox) => checkbox.checked)
    .map((checkbox) => checkbox.value);
}
```

## 📋 6. Checklist de Implementação

### Para implementar um novo filtro de combobox:

#### ✅ DTO

- [ ] Adicionar campo no `DateRangeDTO`
- [ ] Usar nomenclatura `snake_case`
- [ ] Incluir descrição clara
- [ ] Usar tipo `Optional[List[str]]`

#### ✅ Repository

- [ ] Criar método `get_available_nome_coluna()`
- [ ] Verificar existência da coluna
- [ ] Retornar valores únicos ordenados
- [ ] Incluir logs e tratamento de erros

#### ✅ Service

- [ ] Adicionar filtro no método `_apply_filters()`
- [ ] Criar método `get_available_nome_coluna()`
- [ ] Incluir logs e tratamento de erros
- [ ] Delegar para repository

#### ✅ Controller

- [ ] Criar endpoint `GET /api/nome_coluna`
- [ ] Usar response model `List[str]`
- [ ] Incluir logs e medição de tempo
- [ ] Tratar erros com HTTPException

#### ✅ Interface

- [ ] Adicionar HTML do combobox
- [ ] Implementar JavaScript para controle
- [ ] Integrar com sistema de filtros globais
- [ ] Testar funcionalidade

## 🚀 7. Exemplo de Implementação Completa

### Cenário: Adicionar filtro para coluna "Local"

#### 1. DTO (`app/dto/cycle_dto.py`):

```python
class DateRangeDTO(BaseModel):
    # ... campos existentes ...
    local: Optional[List[str]] = Field(None, description="Lista de valores da coluna 'Local' para filtrar")
```

#### 2. Repository (`app/repositories/cycle_repository.py`):

```python
def get_available_local(self) -> List[str]:
    """Obtém valores únicos da coluna 'Local' para filtros"""
    try:
        df = self.get_raw_data()

        if 'Local' not in df.columns:
            logger.warning("⚠️ Coluna 'Local' não encontrada nos dados")
            return []

        valores_unicos = df['Local'].dropna().unique().tolist()
        valores_unicos.sort()

        logger.info(f"✅ Valores únicos obtidos para 'Local': {len(valores_unicos)} valores")
        return valores_unicos

    except Exception as e:
        logger.error(f"❌ Erro ao obter valores únicos de 'Local': {str(e)}")
        return []
```

#### 3. Service (`app/services/cycle_service.py`):

```python
def _apply_filters(self, df: pd.DataFrame, filters: DateRangeDTO) -> pd.DataFrame:
    # ... filtros existentes ...

    if filters.local and len(filters.local) > 0:
        if 'Local' in df.columns:
            df = df[df['Local'].isin(filters.local)]
            logger.info(f"🔍 Aplicado filtro de Local: {filters.local}")
            logger.info(f"📊 Registros após filtro de Local: {len(df):,}")
        else:
            logger.warning("⚠️ Coluna 'Local' não encontrada para aplicar filtro")

    return df

def get_available_local(self) -> List[str]:
    """Obtém valores únicos da coluna 'Local' para filtros"""
    logger.info("🔄 Obtendo valores únicos da coluna 'Local'...")

    try:
        result = self.cycle_repository.get_available_local()

        logger.info(f"✅ Valores únicos obtidos: {len(result)} valores")
        return result

    except Exception as e:
        logger.error(f"❌ Erro ao obter valores únicos: {str(e)}")
        return []
```

#### 4. Controller (`app/controllers/cycle_controller.py`):

```python
@router.get("/local", response_model=List[str])
async def get_local(cycle_service: CycleService = Depends(get_cycle_service)):
    """Obtém lista de valores da coluna 'Local' disponíveis para filtros"""
    logger.info("🚀 API local chamada")
    api_start_time = time.time()

    try:
        result = cycle_service.get_available_local()

        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API local concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Valores retornados: {len(result)}")

        return result

    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API local após {error_time:.2f}s: {str(e)}")
        logger.exception("Detalhes do erro:")
        raise HTTPException(status_code=500, detail=f"Erro ao obter valores: {str(e)}")
```

## 🎯 8. Comandos para a LLM

### Para implementar um novo filtro, use:

```
Implemente um filtro de combobox para a coluna "[NOME_DA_COLUNA]" seguindo o padrão estabelecido no PADRAO_FILTROS_COMBOBOX.md
```

### A LLM deve:

1. **Identificar a coluna** no dataset
2. **Seguir o padrão arquitetural** em 4 camadas
3. **Implementar todas as funcionalidades** (DTO, Repository, Service, Controller, Interface)
4. **Manter consistência** com filtros existentes
5. **Incluir logs e tratamento de erros** adequados
6. **Testar a funcionalidade** completa

## 📚 9. Recursos Adicionais

### Logs Padrão:

- 🚀 API chamada
- 🔄 Processando dados
- ✅ Operação concluída
- ❌ Erro ocorreu
- ⚠️ Aviso/atenção
- 📊 Dados/estatísticas
- ⏱️ Tempo de execução

### Tratamento de Erros:

- Sempre use try/catch
- Log detalhado de erros
- Retorne valores padrão seguros
- Use HTTPException para APIs

### Performance:

- Sempre meça tempo de execução
- Use cache quando apropriado
- Log de quantidade de dados processados
- Otimize consultas de dados

---

**📝 Nota**: Este padrão garante consistência, manutenibilidade e escalabilidade do sistema de filtros. Siga rigorosamente todas as etapas para manter a qualidade do código.
