# 🚀 Exemplo Prático de Implementação de Filtro

## 📋 Cenário

Vamos implementar um filtro de combobox para a coluna **"Local"** seguindo o padrão estabelecido no `PADRAO_FILTROS_COMBOBOX.md`.

## 🔍 Passo a Passo

### 1. **DTO** - Adicionar campo no `DateRangeDTO`

**Arquivo**: `app/dto/cycle_dto.py`

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

    # NOVO FILTRO - Local
    local: Optional[List[str]] = Field(None, description="Lista de valores da coluna 'Local' para filtrar")
```

### 2. **Repository** - Criar método para obter valores únicos

**Arquivo**: `app/repositories/cycle_repository.py`

```python
def get_available_local(self) -> List[str]:
    """Obtém valores únicos da coluna 'Local' para filtros"""
    try:
        df = self.get_raw_data()

        if 'Local' not in df.columns:
            logger.warning("⚠️ Coluna 'Local' não encontrada nos dados")
            return []

        # Obter valores únicos, ordenados e sem valores nulos
        valores_unicos = df['Local'].dropna().unique().tolist()
        valores_unicos.sort()

        logger.info(f"✅ Valores únicos obtidos para 'Local': {len(valores_unicos)} valores")
        return valores_unicos

    except Exception as e:
        logger.error(f"❌ Erro ao obter valores únicos de 'Local': {str(e)}")
        return []
```

### 3. **Service** - Adicionar filtro e método de obtenção

**Arquivo**: `app/services/cycle_service.py`

#### 3.1 Adicionar filtro no método `_apply_filters`:

```python
def _apply_filters(self, df: pd.DataFrame, filters: DateRangeDTO) -> pd.DataFrame:
    """Aplica filtros aos dados"""
    logger.info("🔄 Aplicando filtros aos dados...")

    # ... filtros existentes ...

    # Aplicar filtro por tag de carga
    if filters.tag_carga and len(filters.tag_carga) > 0:
        if 'Tag carga' in df.columns:
            df = df[df['Tag carga'].isin(filters.tag_carga)]
            logger.info(f"🔍 Aplicado filtro de Tag de Carga: {filters.tag_carga}")
            logger.info(f"📊 Registros após filtro de Tag de Carga: {len(df):,}")

    # NOVO FILTRO - Local
    if filters.local and len(filters.local) > 0:
        if 'Local' in df.columns:
            df = df[df['Local'].isin(filters.local)]
            logger.info(f"🔍 Aplicado filtro de Local: {filters.local}")
            logger.info(f"📊 Registros após filtro de Local: {len(df):,}")
        else:
            logger.warning("⚠️ Coluna 'Local' não encontrada para aplicar filtro")

    logger.info(f"📊 Registros após filtros: {len(df):,}")

    if len(df) == 0:
        logger.warning("⚠️ Nenhum registro encontrado após aplicar filtros")

    return df
```

#### 3.2 Adicionar método para obter valores únicos:

```python
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

### 4. **Controller** - Criar endpoint para o filtro

**Arquivo**: `app/controllers/cycle_controller.py`

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

### 5. **Interface HTML** - Adicionar combobox

**Arquivo**: `templates/index.html`

#### 5.1 Adicionar HTML do combobox (após os filtros existentes):

```html
<!-- Filtro por Local -->
<div class="filter-group">
  <label>Local:</label>
  <div class="multiselect-container">
    <div
      class="multiselect-display"
      id="localDisplay"
      onclick="toggleLocalDropdown()"
    >
      <span id="localText">Selecionar Local</span>
      <span class="multiselect-arrow">▼</span>
    </div>

    <div class="multiselect-dropdown" id="localDropdown">
      <div class="multiselect-option">
        <input
          type="checkbox"
          id="selectAllLocal"
          onchange="toggleAllLocal(this)"
        />
        <label for="selectAllLocal">Selecionar Todos</label>
      </div>
      <!-- Opções serão preenchidas dinamicamente -->
    </div>
  </div>
</div>
```

#### 5.2 Adicionar JavaScript para controle do combobox:

```javascript
// Funções para controle do multiselect de Local

// Função para carregar opções
async function loadLocalOptions() {
  try {
    const response = await fetch("/api/local");
    const options = await response.json();

    const dropdown = document.getElementById("localDropdown");

    // Adicionar opções (pular a primeira que é "Selecionar Todos")
    for (let i = 1; i < dropdown.children.length; i++) {
      dropdown.removeChild(dropdown.children[i]);
    }

    options.forEach((option) => {
      const optionDiv = document.createElement("div");
      optionDiv.className = "multiselect-option";

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.id = `local_${option.replace(/\s+/g, "_")}`;
      checkbox.value = option;
      checkbox.onchange = () => updateLocalSelection();

      const label = document.createElement("label");
      label.htmlFor = checkbox.id;
      label.textContent = option;

      optionDiv.appendChild(checkbox);
      optionDiv.appendChild(label);
      dropdown.appendChild(optionDiv);
    });

    // Selecionar todos por padrão
    document.getElementById("selectAllLocal").checked = true;
    updateLocalSelection();
  } catch (error) {
    console.error("Erro ao carregar opções de Local:", error);
  }
}

// Função para alternar dropdown
function toggleLocalDropdown() {
  const dropdown = document.getElementById("localDropdown");
  const arrow = document.querySelector("#localDisplay .multiselect-arrow");

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
function toggleAllLocal(selectAll) {
  const checkboxes = document.querySelectorAll(
    '#localDropdown input[type="checkbox"]:not(#selectAllLocal)'
  );
  checkboxes.forEach((checkbox) => {
    checkbox.checked = selectAll.checked;
  });
  updateLocalSelection();
}

// Função para atualizar seleção
function updateLocalSelection() {
  const checkboxes = document.querySelectorAll(
    '#localDropdown input[type="checkbox"]:not(#selectAllLocal)'
  );
  const selectedOptions = Array.from(checkboxes)
    .filter((checkbox) => checkbox.checked)
    .map((checkbox) => checkbox.value);

  const displayText = document.getElementById("localText");

  if (selectedOptions.length === 0) {
    displayText.textContent = "Selecionar Local";
  } else if (selectedOptions.length === checkboxes.length) {
    displayText.textContent = "Todos selecionados";
  } else if (selectedOptions.length === 1) {
    displayText.textContent = selectedOptions[0];
  } else {
    displayText.textContent = `${selectedOptions.length} selecionados`;
  }

  // Atualizar estado do "Selecionar Todos"
  const selectAll = document.getElementById("selectAllLocal");
  selectAll.checked = selectedOptions.length === checkboxes.length;

  // Atualizar filtros globais
  updateGlobalFilters();
}

// Função para obter valores selecionados
function getSelectedLocal() {
  const checkboxes = document.querySelectorAll(
    '#localDropdown input[type="checkbox"]:not(#selectAllLocal)'
  );
  return Array.from(checkboxes)
    .filter((checkbox) => checkbox.checked)
    .map((checkbox) => checkbox.value);
}
```

#### 5.3 Atualizar função de filtros globais:

```javascript
function updateGlobalFilters() {
  // ... filtros existentes ...

  // Adicionar filtro de Local
  const localSelecionados = getSelectedLocal();
  if (localSelecionados.length > 0) {
    filters.local = localSelecionados.join(",");
  }

  // ... resto da função ...
}
```

#### 5.4 Atualizar função de carregamento inicial:

```javascript
async function loadAllFilterOptions() {
  // ... carregamento de filtros existentes ...

  // Carregar opções de Local
  await loadLocalOptions();

  // ... resto da função ...
}
```

## 🧪 Testando a Implementação

### 1. **Reiniciar a aplicação**:

```bash
python main.py
```

### 2. **Verificar endpoint da API**:

- Acesse: `http://127.0.0.1:8000/docs`
- Teste o endpoint: `GET /api/local`
- Deve retornar lista de valores únicos da coluna "Local"

### 3. **Verificar interface**:

- Acesse: `http://127.0.0.1:8000`
- O filtro "Local" deve aparecer na interface
- Deve carregar opções automaticamente
- Deve permitir seleção múltipla

### 4. **Verificar logs**:

- Verifique os logs da aplicação para confirmar funcionamento
- Deve mostrar logs de carregamento e aplicação de filtros

## 🔍 Verificações Finais

### ✅ Checklist de Implementação:

- [ ] **DTO**: Campo `local` adicionado no `DateRangeDTO`
- [ ] **Repository**: Método `get_available_local()` implementado
- [ ] **Service**: Filtro aplicado em `_apply_filters()` e método `get_available_local()` criado
- [ ] **Controller**: Endpoint `GET /api/local` implementado
- [ ] **Interface**: HTML e JavaScript do combobox implementados
- [ ] **Integração**: Filtro integrado ao sistema de filtros globais
- [ ] **Testes**: Funcionalidade testada e funcionando

## 🚀 Próximos Passos

Agora você pode implementar filtros para outras colunas seguindo exatamente o mesmo padrão:

1. **Substitua "Local"** pelo nome da nova coluna
2. **Siga a nomenclatura** estabelecida
3. **Mantenha a consistência** com filtros existentes
4. **Teste cada camada** antes de prosseguir

## 📚 Referências

- **PADRAO_FILTROS_COMBOBOX.md**: Documento completo de padrões
- **README.md**: Visão geral da arquitetura
- **Código existente**: Filtros já implementados como referência
