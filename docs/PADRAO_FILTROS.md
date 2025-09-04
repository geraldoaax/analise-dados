# 🎯 Padrão de Filtros Combobox - Guia Completo

## 📋 Visão Geral

Este documento estabelece o padrão para implementação de filtros de combobox no sistema de análise de ciclo. Permite que a LLM gere automaticamente novos filtros baseados em colunas existentes seguindo uma arquitetura consistente.

## 🏗️ Arquitetura

### Estrutura em 4 Camadas
```
DTO → Repository → Service → Controller
```

### Filtros Implementados
- **Tipos de Input** (`tipos_input`)
- **Frota de Transporte** (`frota_transporte`) 
- **Frota de Carga** (`frota_carga`)
- **Tag de Carga** (`tag_carga`)

## 🚀 Comando para Implementar

```
Implemente um filtro de combobox para a coluna "[NOME_DA_COLUNA]" seguindo o padrão estabelecido no PADRAO_FILTROS.md
```

## 📝 Implementação por Camada

### 1. DTO - `app/dto/cycle_dto.py`

```python
class DateRangeDTO(BaseModel):
    # Campos existentes...
    
    # NOVO FILTRO - Siga este padrão:
    nome_coluna: Optional[List[str]] = Field(None, description="Lista de valores da coluna 'Nome Coluna' para filtrar")
```

**Regras:**
- Nome do campo: `snake_case` baseado no nome da coluna
- Tipo: `Optional[List[str]]`
- Descrição: "Lista de valores da coluna 'Nome Coluna' para filtrar"

### 2. Repository - `app/repositories/cycle_repository.py`

```python
def get_available_nome_coluna(self) -> List[str]:
    """Obtém valores únicos da coluna 'Nome Coluna' para filtros"""
    try:
        df = self.get_raw_data()
        if 'Nome Coluna' not in df.columns:
            logger.warning("⚠️ Coluna 'Nome Coluna' não encontrada nos dados")
            return []
        
        valores_unicos = df['Nome Coluna'].dropna().unique().tolist()
        valores_unicos.sort()
        
        logger.info(f"✅ Valores únicos obtidos para 'Nome Coluna': {len(valores_unicos)} valores")
        return valores_unicos
    except Exception as e:
        logger.error(f"❌ Erro ao obter valores únicos de 'Nome Coluna': {str(e)}")
        return []
```

**Regras:**
- Nome do método: `get_available_nome_coluna()`
- Verificar existência da coluna
- Retornar valores únicos ordenados
- Incluir logs e tratamento de erros

### 3. Service - `app/services/cycle_service.py`

#### Aplicar Filtro em `_apply_filters()`:
```python
# NOVO FILTRO - Siga este padrão:
if filters.nome_coluna and len(filters.nome_coluna) > 0:
    if 'Nome Coluna' in df.columns:
        df = df[df['Nome Coluna'].isin(filters.nome_coluna)]
        logger.info(f"🔍 Aplicado filtro de Nome Coluna: {filters.nome_coluna}")
        logger.info(f"📊 Registros após filtro de Nome Coluna: {len(df):,}")
    else:
        logger.warning("⚠️ Coluna 'Nome Coluna' não encontrada para aplicar filtro")
```

#### Método para Obter Valores:
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

### 4. Controller - `app/controllers/cycle_controller.py`

#### Endpoint da API:
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

#### Adicionar Parâmetro nos Endpoints Existentes:
```python
@router.get("/cycles_by_year_month", response_model=List[CycleDataDTO])
async def get_cycles_by_year_month(
    # ... outros parâmetros ...
    nome_coluna: Optional[str] = Query(None, description="Valores da coluna separados por vírgula"),
    cycle_service: CycleService = Depends(get_cycle_service)
):
    # Processar parâmetro
    nome_coluna_list = None
    if nome_coluna:
        nome_coluna_list = [item.strip() for item in nome_coluna.split(',') if item.strip()]
    
    # Criar DTO de filtros
    filters = DateRangeDTO(
        # ... outros filtros ...
        nome_coluna=nome_coluna_list
    )
```

### 5. Interface - `templates/index.html`

#### HTML do Combobox:
```html
<!-- NOVO FILTRO - Siga este padrão -->
<div class="filter-group-secondary" id="filtroNomeColuna">
  <label>Filtrar por Nome Coluna:</label>
  <div class="multiselect-container">
    <div class="multiselect-display" id="nomeColunaDisplay" onclick="toggleNomeColunaDropdown()">
      <span id="nomeColunaText">Todas as opções</span>
      <span class="multiselect-arrow">▼</span>
    </div>
    <div class="multiselect-dropdown" id="nomeColunaDropdown">
      <div class="multiselect-option">
        <input type="checkbox" id="selectAllNomeColuna" onchange="toggleAllNomeColuna(this)" />
        <label for="selectAllNomeColuna">Selecionar Todos</label>
      </div>
    </div>
  </div>
</div>
```

#### JavaScript:
```javascript
// Variáveis globais
let nomeColunaDisponiveis = [];
let nomeColunaSelecionadas = [];

// Carregar opções
async function loadNomeColuna() {
  try {
    const response = await fetch("/api/nome_coluna");
    const data = await response.json();
    
    nomeColunaDisponiveis = data;
    nomeColunaSelecionadas = [...data];
    
    populateNomeColunaOptions();
    updateNomeColunaDisplay();
  } catch (error) {
    console.error("Erro ao carregar opções:", error);
  }
}

// Popular opções no dropdown
function populateNomeColunaOptions() {
  const dropdown = document.getElementById("nomeColunaDropdown");
  
  // Limpar opções existentes (exceto "Selecionar Todos")
  while (dropdown.children.length > 1) {
    dropdown.removeChild(dropdown.lastChild);
  }
  
  // Adicionar opções
  nomeColunaDisponiveis.forEach(option => {
    const optionDiv = document.createElement("div");
    optionDiv.className = "multiselect-option";
    
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.id = `nomeColuna_${option.replace(/\s+/g, "_")}`;
    checkbox.value = option;
    checkbox.checked = nomeColunaSelecionadas.includes(option);
    checkbox.onchange = () => toggleNomeColuna(option);
    
    const label = document.createElement("label");
    label.htmlFor = checkbox.id;
    label.textContent = option;
    
    optionDiv.appendChild(checkbox);
    optionDiv.appendChild(label);
    dropdown.appendChild(optionDiv);
  });
  
  updateSelectAllNomeColunaState();
}

// Toggle dropdown
function toggleNomeColunaDropdown() {
  const dropdown = document.getElementById("nomeColunaDropdown");
  const arrow = document.querySelector("#nomeColunaDisplay .multiselect-arrow");
  
  if (dropdown.classList.contains("show")) {
    dropdown.classList.remove("show");
    arrow.style.transform = "rotate(0deg)";
  } else {
    // Fechar outros dropdowns
    document.querySelectorAll(".multiselect-dropdown.show").forEach(d => d.classList.remove("show"));
    document.querySelectorAll(".multiselect-arrow").forEach(a => a.style.transform = "rotate(0deg)");
    
    dropdown.classList.add("show");
    arrow.style.transform = "rotate(180deg)";
  }
}

// Toggle seleção individual
function toggleNomeColuna(option) {
  if (nomeColunaSelecionadas.includes(option)) {
    nomeColunaSelecionadas = nomeColunaSelecionadas.filter(item => item !== option);
  } else {
    nomeColunaSelecionadas.push(option);
  }
  
  updateNomeColunaDisplay();
  updateSelectAllNomeColunaState();
  
  // Atualizar gráfico se já tiver dados
  if (graficoComDados) {
    atualizarGraficoComFiltro();
  }
}

// Toggle selecionar todos
function toggleAllNomeColuna(selectAll) {
  const checkboxes = document.querySelectorAll('#nomeColunaDropdown input[type="checkbox"]:not(#selectAllNomeColuna)');
  
  checkboxes.forEach(checkbox => {
    checkbox.checked = selectAll.checked;
  });
  
  nomeColunaSelecionadas = selectAll.checked ? [...nomeColunaDisponiveis] : [];
  updateNomeColunaDisplay();
}

// Atualizar estado do "Selecionar Todos"
function updateSelectAllNomeColunaState() {
  const selectAll = document.getElementById("selectAllNomeColuna");
  const totalOptions = nomeColunaDisponiveis.length;
  const selectedOptions = nomeColunaSelecionadas.length;
  
  selectAll.checked = selectedOptions === totalOptions;
  selectAll.indeterminate = selectedOptions > 0 && selectedOptions < totalOptions;
}

// Atualizar display
function updateNomeColunaDisplay() {
  const displayText = document.getElementById("nomeColunaText");
  
  if (nomeColunaSelecionadas.length === 0) {
    displayText.textContent = "Selecionar opções";
  } else if (nomeColunaSelecionadas.length === nomeColunaDisponiveis.length) {
    displayText.textContent = "Todas as opções";
  } else if (nomeColunaSelecionadas.length === 1) {
    displayText.textContent = nomeColunaSelecionadas[0];
  } else {
    displayText.textContent = `${nomeColunaSelecionadas.length} selecionadas`;
  }
}

// Reset filtro
function resetNomeColuna() {
  nomeColunaSelecionadas = [...nomeColunaDisponiveis];
  populateNomeColunaOptions();
  updateNomeColunaDisplay();
}
```

#### Integração com Sistema de Filtros:
```javascript
// Adicionar ao DOMContentLoaded
document.addEventListener("DOMContentLoaded", function () {
  // ... outros carregamentos ...
  loadNomeColuna(); // OBRIGATÓRIO!
});

// Adicionar à função showAnalysis()
function showAnalysis(analysisType) {
  const params = new URLSearchParams();
  
  // ... outros parâmetros ...
  
  // Adicionar filtro de nome coluna
  if (nomeColunaSelecionadas.length > 0) {
    params.append("nome_coluna", nomeColunaSelecionadas.join(","));
    console.log("🔍 Filtro de Nome Coluna aplicado:", nomeColunaSelecionadas);
  }
  
  // ... resto da função ...
}
```

## ⚠️ Pontos Críticos

### 1. Carregamento Automático
**PROBLEMA**: Se `loadNomeColuna()` não for chamada na inicialização, o filtro ficará vazio.

**SOLUÇÃO**: Sempre incluir no `DOMContentLoaded`:
```javascript
document.addEventListener("DOMContentLoaded", function () {
  loadNomeColuna(); // NÃO ESQUECER!
});
```

### 2. Integração com API
**PROBLEMA**: Filtro pode não afetar os dados se não estiver integrado corretamente.

**SOLUÇÃO**: Verificar se o parâmetro está sendo enviado na função `showAnalysis()`:
```javascript
if (nomeColunaSelecionadas.length > 0) {
  params.append("nome_coluna", nomeColunaSelecionadas.join(","));
}
```

### 3. Visibilidade na Interface
**PROBLEMA**: Filtro pode não aparecer se não estiver configurado corretamente.

**SOLUÇÃO**: Verificar se o HTML foi adicionado e se está sendo mostrado/ocultado corretamente.

## 🧪 Checklist de Implementação

### ✅ Backend
- [ ] Campo adicionado no `DateRangeDTO`
- [ ] Método `get_available_nome_coluna()` no repository
- [ ] Filtro aplicado em `_apply_filters()` no service
- [ ] Método `get_available_nome_coluna()` no service
- [ ] Endpoint `GET /api/nome_coluna` no controller
- [ ] Parâmetro `nome_coluna` adicionado nos endpoints existentes

### ✅ Frontend
- [ ] HTML do combobox adicionado
- [ ] JavaScript para controle do filtro
- [ ] `loadNomeColuna()` chamada no `DOMContentLoaded`
- [ ] Filtro integrado na função `showAnalysis()`
- [ ] Teste de funcionalidade completa

## 🔍 Troubleshooting

### Filtro aparece vazio
- Verificar se `loadNomeColuna()` está sendo chamada
- Verificar se o endpoint `/api/nome_coluna` existe
- Verificar console do navegador para erros

### Filtro não afeta os dados
- Verificar se o parâmetro está sendo enviado na API
- Verificar se o filtro está sendo aplicado no service
- Verificar logs da aplicação

### Filtro não aparece na interface
- Verificar se o HTML foi adicionado
- Verificar se não está sendo ocultado por CSS
- Verificar se está sendo mostrado na função de seleção de análise

## 📚 Exemplo Prático

Para implementar um filtro para a coluna "Local":

1. **Substitua "Nome Coluna" por "Local"** em todo o código
2. **Use "local" como nome do campo** (snake_case)
3. **Siga exatamente o mesmo padrão** dos filtros existentes
4. **Teste cada camada** antes de prosseguir

## 🎯 Benefícios

- **Consistência**: Todos os filtros seguem o mesmo padrão
- **Manutenibilidade**: Código limpo e bem estruturado
- **Escalabilidade**: Fácil adição de novos filtros
- **Funcionalidade**: Filtros realmente afetam os dados
- **UX**: Interface intuitiva com múltipla seleção

---

**💡 Dica**: Use os filtros existentes como referência. O padrão é sempre o mesmo, apenas mude o nome da coluna!
