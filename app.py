import glob
import logging
import os
import time
from datetime import datetime

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_from_directory

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Cache global para os dados processados
_cache = {
    'raw_data': None,
    'processed_data': None,
    'last_check': None,
    'files_hash': None
}

def get_files_hash():
    """Calcula hash dos arquivos para detectar mudanças"""
    path = 'CicloDetalhado'
    all_files = glob.glob(path + "/*.xlsx")
    
    files_info = []
    for filename in all_files:
        stat = os.stat(filename)
        files_info.append(f"{filename}:{stat.st_size}:{stat.st_mtime}")
    
    return hash(tuple(sorted(files_info)))

def load_data_with_cache():
    """Carrega dados com cache inteligente"""
    global _cache
    
    # Verificar se precisa recarregar
    current_hash = get_files_hash()
    current_time = datetime.now()
    
    # Se tem cache válido, usar
    if (_cache['raw_data'] is not None and 
        _cache['files_hash'] == current_hash):
        logger.info("✅ Usando dados do cache (arquivos não modificados)")
        return _cache['raw_data']
    
    logger.info("🔄 Cache inválido ou inexistente, carregando dados...")
    start_time = time.time()
    
    path = 'CicloDetalhado'
    all_files = glob.glob(path + "/*.xlsx")
    logger.info(f"📁 Encontrados {len(all_files)} arquivos Excel")
    
    df_list = []
    total_rows = 0
    
    for i, filename in enumerate(all_files, 1):
        logger.info(f"📊 Carregando arquivo {i}/{len(all_files)}: {filename}")
        file_start = time.time()
        
        try:
            # Carregar as colunas necessárias (incluindo Massa, Tipo de atividade, Especificacao de material e Material)
            df = pd.read_excel(filename, usecols=['DataHoraInicio', 'Tipo Input', 'Massa', 'Tipo de atividade', 'Especificacao de material', 'Material'])
            rows = len(df)
            total_rows += rows
            df_list.append(df)
            file_time = time.time() - file_start
            logger.info(f"   ✅ Carregado: {rows:,} linhas em {file_time:.2f}s")
        except Exception as e:
            logger.error(f"   ❌ Erro ao carregar {filename}: {e}")
            raise
    
    logger.info(f"🔀 Combinando {len(df_list)} DataFrames...")
    combine_start = time.time()
    combined_df = pd.concat(df_list, ignore_index=True)
    combine_time = time.time() - combine_start
    
    total_time = time.time() - start_time
    logger.info(f"✅ Dados carregados com sucesso!")
    logger.info(f"   📈 Total de registros: {len(combined_df):,}")
    logger.info(f"   ⏱️  Tempo de combinação: {combine_time:.2f}s")
    logger.info(f"   ⏱️  Tempo total: {total_time:.2f}s")
    
    # Atualizar cache
    _cache['raw_data'] = combined_df
    _cache['files_hash'] = current_hash
    _cache['last_check'] = current_time
    logger.info("💾 Cache atualizado")
    
    return combined_df

def get_processed_cycles_data(data_inicio=None, data_fim=None):
    """Obtém dados processados com filtro de data"""
    logger.info("🔄 Processando dados com filtro de data...")
    process_start = time.time()
    
    # Carregar dados brutos
    df = load_data_with_cache()
    
    # Verificar se a coluna existe
    if 'DataHoraInicio' not in df.columns:
        raise ValueError('Coluna DataHoraInicio não encontrada nos dados')
    
    # Processar dados de forma otimizada
    logger.info("🔄 Convertendo datas...")
    df['DataHoraInicio'] = pd.to_datetime(df['DataHoraInicio'], errors='coerce')
    
    # Remover datas inválidas
    df = df.dropna(subset=['DataHoraInicio'])
    
    # Aplicar filtros de data se fornecidos
    if data_inicio:
        data_inicio_dt = pd.to_datetime(data_inicio)
        df = df[df['DataHoraInicio'] >= data_inicio_dt]
        logger.info(f"📅 Aplicado filtro de data início: {data_inicio}")
    
    if data_fim:
        data_fim_dt = pd.to_datetime(data_fim)
        df = df[df['DataHoraInicio'] <= data_fim_dt]
        logger.info(f"📅 Aplicado filtro de data fim: {data_fim}")
    
    logger.info(f"📊 Registros após filtros: {len(df):,}")
    
    # Verificar se restaram dados após filtros
    if len(df) == 0:
        logger.warning("⚠️ Nenhum registro encontrado após aplicar filtros")
        return []
    
    logger.info("📅 Criando períodos...")
    df['AnoMes'] = df['DataHoraInicio'].dt.to_period('M')
    
    logger.info("📊 Agrupando dados...")
    cycle_counts = df.groupby('AnoMes').size().reset_index(name='count')
    
    # Converter e ordenar
    cycle_counts['AnoMes'] = cycle_counts['AnoMes'].astype(str)
    cycle_counts = cycle_counts.sort_values('AnoMes')
    
    # Converter para dict para JSON
    result = cycle_counts.to_dict(orient='records')
    
    process_time = time.time() - process_start
    logger.info(f"✅ Processamento concluído em {process_time:.2f}s")
    logger.info(f"📊 {len(result)} períodos encontrados")
    
    return result

def get_processed_cycles_by_tipo_input(data_inicio=None, data_fim=None):
    """Obtém dados processados por Tipo Input com filtro de data"""
    logger.info("🔄 Processando dados por Tipo Input com filtro de data...")
    process_start = time.time()
    
    # Carregar dados brutos
    df = load_data_with_cache()
    
    # Verificar se as colunas existem
    if 'DataHoraInicio' not in df.columns:
        raise ValueError('Coluna DataHoraInicio não encontrada nos dados')
    if 'Tipo Input' not in df.columns:
        raise ValueError('Coluna Tipo Input não encontrada nos dados')
    
    # Processar dados de forma otimizada
    logger.info("🔄 Convertendo datas...")
    df['DataHoraInicio'] = pd.to_datetime(df['DataHoraInicio'], errors='coerce')
    
    # Remover datas inválidas e valores nulos em Tipo Input
    df = df.dropna(subset=['DataHoraInicio', 'Tipo Input'])
    
    # Aplicar filtros de data se fornecidos
    if data_inicio:
        data_inicio_dt = pd.to_datetime(data_inicio)
        df = df[df['DataHoraInicio'] >= data_inicio_dt]
        logger.info(f"📅 Aplicado filtro de data início: {data_inicio}")
    
    if data_fim:
        data_fim_dt = pd.to_datetime(data_fim)
        df = df[df['DataHoraInicio'] <= data_fim_dt]
        logger.info(f"📅 Aplicado filtro de data fim: {data_fim}")
    
    logger.info(f"📊 Registros após filtros: {len(df):,}")
    
    # Verificar se restaram dados após filtros
    if len(df) == 0:
        logger.warning("⚠️ Nenhum registro encontrado após aplicar filtros")
        return []
    
    logger.info("📅 Criando períodos...")
    df['AnoMes'] = df['DataHoraInicio'].dt.to_period('M')
    
    logger.info("📊 Agrupando dados por Tipo Input...")
    cycle_counts = df.groupby(['AnoMes', 'Tipo Input']).size().reset_index(name='count')
    
    # Converter período para string e ordenar
    cycle_counts['AnoMes'] = cycle_counts['AnoMes'].astype(str)
    cycle_counts = cycle_counts.sort_values(['AnoMes', 'Tipo Input'])
    
    # Converter para dict para JSON
    result = cycle_counts.to_dict(orient='records')
    
    process_time = time.time() - process_start
    logger.info(f"✅ Processamento por Tipo Input concluído em {process_time:.2f}s")
    logger.info(f"📊 {len(result)} registros encontrados")
    
    return result

def get_processed_production_by_activity_type(data_inicio=None, data_fim=None):
    """Obtém dados de produção (soma de massa) por tipo de atividade com filtro de data"""
    logger.info("🔄 Processando dados de produção por tipo de atividade com filtro de data...")
    process_start = time.time()
    
    # Carregar dados brutos
    df = load_data_with_cache()
    
    # Verificar se as colunas existem
    if 'DataHoraInicio' not in df.columns:
        raise ValueError('Coluna DataHoraInicio não encontrada nos dados')
    if 'Tipo de atividade' not in df.columns:
        raise ValueError('Coluna Tipo de atividade não encontrada nos dados')
    if 'Massa' not in df.columns:
        raise ValueError('Coluna Massa não encontrada nos dados')
    
    # Processar dados de forma otimizada
    logger.info("🔄 Convertendo datas...")
    df['DataHoraInicio'] = pd.to_datetime(df['DataHoraInicio'], errors='coerce')
    
    # Remover datas inválidas e valores nulos
    df = df.dropna(subset=['DataHoraInicio', 'Tipo de atividade', 'Massa'])
    
    # Aplicar filtros de data se fornecidos
    if data_inicio:
        data_inicio_dt = pd.to_datetime(data_inicio)
        df = df[df['DataHoraInicio'] >= data_inicio_dt]
        logger.info(f"📅 Aplicado filtro de data início: {data_inicio}")
    
    if data_fim:
        data_fim_dt = pd.to_datetime(data_fim)
        df = df[df['DataHoraInicio'] <= data_fim_dt]
        logger.info(f"📅 Aplicado filtro de data fim: {data_fim}")
    
    logger.info(f"📊 Registros após filtros: {len(df):,}")
    
    # Verificar se restaram dados após filtros
    if len(df) == 0:
        logger.warning("⚠️ Nenhum registro encontrado após aplicar filtros")
        return []
    
    logger.info("📅 Criando períodos...")
    df['AnoMes'] = df['DataHoraInicio'].dt.to_period('M')
    
    logger.info("📊 Agrupando dados por tipo de atividade e somando massa...")
    production_data = df.groupby(['AnoMes', 'Tipo de atividade'])['Massa'].sum().reset_index(name='massa_total')
    
    # Converter período para string e ordenar
    production_data['AnoMes'] = production_data['AnoMes'].astype(str)
    production_data = production_data.sort_values(['AnoMes', 'Tipo de atividade'])
    
    # Converter para dict para JSON
    result = production_data.to_dict(orient='records')
    
    process_time = time.time() - process_start
    logger.info(f"✅ Processamento de produção concluído em {process_time:.2f}s")
    logger.info(f"📊 {len(result)} registros encontrados")
    
    return result

def get_processed_production_by_material_spec(data_inicio=None, data_fim=None):
    """Obtém dados de produção (soma de massa) por especificação de material com filtro de data"""
    logger.info("🔄 Processando dados de produção por especificação de material com filtro de data...")
    process_start = time.time()
    
    # Carregar dados brutos
    df = load_data_with_cache()
    
    # Verificar se as colunas existem
    if 'DataHoraInicio' not in df.columns:
        raise ValueError('Coluna DataHoraInicio não encontrada nos dados')
    if 'Especificacao de material' not in df.columns:
        raise ValueError('Coluna Especificacao de material não encontrada nos dados')
    if 'Massa' not in df.columns:
        raise ValueError('Coluna Massa não encontrada nos dados')
    
    # Processar dados de forma otimizada
    logger.info("🔄 Convertendo datas...")
    df['DataHoraInicio'] = pd.to_datetime(df['DataHoraInicio'], errors='coerce')
    
    # Remover datas inválidas e valores nulos
    df = df.dropna(subset=['DataHoraInicio', 'Especificacao de material', 'Massa'])
    
    # Aplicar filtros de data se fornecidos
    if data_inicio:
        data_inicio_dt = pd.to_datetime(data_inicio)
        df = df[df['DataHoraInicio'] >= data_inicio_dt]
        logger.info(f"📅 Aplicado filtro de data início: {data_inicio}")
    
    if data_fim:
        data_fim_dt = pd.to_datetime(data_fim)
        df = df[df['DataHoraInicio'] <= data_fim_dt]
        logger.info(f"📅 Aplicado filtro de data fim: {data_fim}")
    
    logger.info(f"📊 Registros após filtros: {len(df):,}")
    
    # Verificar se restaram dados após filtros
    if len(df) == 0:
        logger.warning("⚠️ Nenhum registro encontrado após aplicar filtros")
        return []
    
    logger.info("📅 Criando períodos...")
    df['AnoMes'] = df['DataHoraInicio'].dt.to_period('M')
    
    logger.info("📊 Agrupando dados por especificação de material e somando massa...")
    # Primeiro, calcular totais por especificação para identificar os maiores
    totals_by_spec = df.groupby('Especificacao de material')['Massa'].sum().sort_values(ascending=False)
    logger.info(f"📋 Especificações encontradas: {len(totals_by_spec)}")
    
    # Definir quantos especificações mostrar individualmente (top 3)
    top_n = 3
    top_specs = totals_by_spec.head(top_n).index.tolist()
    logger.info(f"🔝 Top {top_n} especificações: {top_specs}")
    
    # Log detalhado das especificações e suas massas
    for i, (spec, massa) in enumerate(totals_by_spec.head(10).items(), 1):
        status = "🏆 TOP" if spec in top_specs else "📦 OUTROS"
        logger.info(f"   {i:2d}. {spec}: {massa:,.0f} kg - {status}")
    
    # Criar nova coluna agrupando especificações menores em "Outros"
    df['Spec_Agrupada'] = df['Especificacao de material'].apply(
        lambda x: x if x in top_specs else 'Outros'
    )
    
    # Agrupar por período e especificação agrupada
    production_data = df.groupby(['AnoMes', 'Spec_Agrupada'])['Massa'].sum().reset_index(name='massa_total')
    
    # Renomear coluna para manter compatibilidade com frontend
    production_data = production_data.rename(columns={'Spec_Agrupada': 'Especificacao de material'})
    
    # Converter período para string e ordenar
    production_data['AnoMes'] = production_data['AnoMes'].astype(str)
    production_data = production_data.sort_values(['AnoMes', 'Especificacao de material'])
    
    # Log do agrupamento realizado
    specs_finais = production_data['Especificacao de material'].unique()
    tem_outros = 'Outros' in specs_finais
    logger.info(f"📋 Especificações no resultado final: {list(specs_finais)}")
    if tem_outros:
        outros_total = production_data[production_data['Especificacao de material'] == 'Outros']['massa_total'].sum()
        logger.info(f"📦 Total agrupado em 'Outros': {outros_total:,.2f} kg")
    
    # Converter para dict para JSON
    result = production_data.to_dict(orient='records')
    
    process_time = time.time() - process_start
    logger.info(f"✅ Processamento de produção por especificação de material concluído em {process_time:.2f}s")
    logger.info(f"📊 {len(result)} registros encontrados")
    
    return result

def get_processed_production_by_material(data_inicio=None, data_fim=None):
    """Obtém dados de produção (soma de massa) por material com filtro de data"""
    logger.info("🔄 Processando dados de produção por material com filtro de data...")
    process_start = time.time()
    
    # Carregar dados brutos
    df = load_data_with_cache()
    
    # Verificar se as colunas existem
    if 'DataHoraInicio' not in df.columns:
        raise ValueError('Coluna DataHoraInicio não encontrada nos dados')
    if 'Material' not in df.columns:
        raise ValueError('Coluna Material não encontrada nos dados')
    if 'Massa' not in df.columns:
        raise ValueError('Coluna Massa não encontrada nos dados')
    
    # Processar dados de forma otimizada
    logger.info("🔄 Convertendo datas...")
    df['DataHoraInicio'] = pd.to_datetime(df['DataHoraInicio'], errors='coerce')
    
    # Remover datas inválidas e valores nulos
    df = df.dropna(subset=['DataHoraInicio', 'Material', 'Massa'])
    
    # Aplicar filtros de data se fornecidos
    if data_inicio:
        data_inicio_dt = pd.to_datetime(data_inicio)
        df = df[df['DataHoraInicio'] >= data_inicio_dt]
        logger.info(f"📅 Aplicado filtro de data início: {data_inicio}")
    
    if data_fim:
        data_fim_dt = pd.to_datetime(data_fim)
        df = df[df['DataHoraInicio'] <= data_fim_dt]
        logger.info(f"📅 Aplicado filtro de data fim: {data_fim}")
    
    logger.info(f"📊 Registros após filtros: {len(df):,}")
    
    # Verificar se restaram dados após filtros
    if len(df) == 0:
        logger.warning("⚠️ Nenhum registro encontrado após aplicar filtros")
        return []
    
    logger.info("📅 Criando períodos...")
    df['AnoMes'] = df['DataHoraInicio'].dt.to_period('M')
    
    logger.info("📊 Agrupando dados por material e somando massa...")
    # Primeiro, calcular totais por material para identificar os maiores
    totals_by_material = df.groupby('Material')['Massa'].sum().sort_values(ascending=False)
    logger.info(f"📋 Materiais encontrados: {len(totals_by_material)}")
    
    # Definir quantos materiais mostrar individualmente (top 3)
    top_n = 3
    top_materials = totals_by_material.head(top_n).index.tolist()
    logger.info(f"🔝 Top {top_n} materiais: {top_materials}")
    
    # Log detalhado dos materiais e suas massas
    for i, (material, massa) in enumerate(totals_by_material.head(10).items(), 1):
        status = "🏆 TOP" if material in top_materials else "📦 OUTROS"
        logger.info(f"   {i:2d}. {material}: {massa:,.0f} kg - {status}")
    
    # Criar nova coluna agrupando materiais menores em "Outros"
    df['Material_Agrupado'] = df['Material'].apply(
        lambda x: x if x in top_materials else 'Outros'
    )
    
    # Agrupar por período e material agrupado
    production_data = df.groupby(['AnoMes', 'Material_Agrupado'])['Massa'].sum().reset_index(name='massa_total')
    
    # Renomear coluna para manter compatibilidade com frontend
    production_data = production_data.rename(columns={'Material_Agrupado': 'Material'})
    
    # Converter período para string e ordenar
    production_data['AnoMes'] = production_data['AnoMes'].astype(str)
    production_data = production_data.sort_values(['AnoMes', 'Material'])
    
    # Log do agrupamento realizado
    materiais_finais = production_data['Material'].unique()
    tem_outros = 'Outros' in materiais_finais
    logger.info(f"📋 Materiais no resultado final: {list(materiais_finais)}")
    if tem_outros:
        outros_total = production_data[production_data['Material'] == 'Outros']['massa_total'].sum()
        logger.info(f"📦 Total agrupado em 'Outros': {outros_total:,.2f} kg")
    
    # Converter para dict para JSON
    result = production_data.to_dict(orient='records')
    
    process_time = time.time() - process_start
    logger.info(f"✅ Processamento de produção por material concluído em {process_time:.2f}s")
    logger.info(f"📊 {len(result)} registros encontrados")
    
    return result

def get_processed_productivity_analysis(data_inicio=None, data_fim=None):
    """Obtém análise de produtividade: toneladas por período e toneladas por ciclo"""
    logger.info("🔄 Processando análise de produtividade simplificada com filtro de data...")
    process_start = time.time()
    
    # Carregar dados brutos
    df = load_data_with_cache()
    
    # Verificar se as colunas existem
    if 'DataHoraInicio' not in df.columns:
        raise ValueError('Coluna DataHoraInicio não encontrada nos dados')
    if 'Massa' not in df.columns:
        raise ValueError('Coluna Massa não encontrada nos dados')
    
    # Processar dados de forma otimizada
    logger.info("🔄 Convertendo datas...")
    df['DataHoraInicio'] = pd.to_datetime(df['DataHoraInicio'], errors='coerce')
    
    # Remover datas inválidas e valores nulos em Massa
    df = df.dropna(subset=['DataHoraInicio', 'Massa'])
    
    # Aplicar filtros de data se fornecidos
    if data_inicio:
        data_inicio_dt = pd.to_datetime(data_inicio)
        df = df[df['DataHoraInicio'] >= data_inicio_dt]
        logger.info(f"📅 Aplicado filtro de data início: {data_inicio}")
    
    if data_fim:
        data_fim_dt = pd.to_datetime(data_fim)
        df = df[df['DataHoraInicio'] <= data_fim_dt]
        logger.info(f"📅 Aplicado filtro de data fim: {data_fim}")
    
    logger.info(f"📊 Registros após filtros: {len(df):,}")
    
    # Verificar se restaram dados após filtros
    if len(df) == 0:
        logger.warning("⚠️ Nenhum registro encontrado após aplicar filtros")
        return []
    
    logger.info("📅 Criando períodos...")
    df['AnoMes'] = df['DataHoraInicio'].dt.to_period('M')
    
    logger.info("📊 Calculando métricas de produtividade simplificadas...")
    
    # Agrupar por período e calcular métricas simples
    productivity_metrics = df.groupby('AnoMes').agg({
        'Massa': ['count', 'sum', 'mean']
    }).round(2)
    
    # Simplificar nomes das colunas
    productivity_metrics.columns = ['total_ciclos', 'massa_total_kg', 'massa_media_kg_ciclo']
    
    # Converter para toneladas e calcular métricas principais
    productivity_metrics['toneladas_total'] = (productivity_metrics['massa_total_kg'] / 1000).round(2)
    productivity_metrics['toneladas_por_ciclo'] = (productivity_metrics['massa_media_kg_ciclo'] / 1000).round(3)
    
    # Calcular crescimento em toneladas
    productivity_metrics['crescimento_toneladas_pct'] = productivity_metrics['toneladas_total'].pct_change() * 100
    productivity_metrics['crescimento_prod_pct'] = productivity_metrics['toneladas_por_ciclo'].pct_change() * 100
    
    # Resetar index e converter período para string
    productivity_metrics = productivity_metrics.reset_index()
    productivity_metrics['AnoMes'] = productivity_metrics['AnoMes'].astype(str)
    
    # Preencher NaN com 0 para o primeiro período (sem período anterior para comparar)
    productivity_metrics = productivity_metrics.fillna(0)
    
    # Ordenar por período
    productivity_metrics = productivity_metrics.sort_values('AnoMes')
    
    # Log das métricas calculadas
    logger.info("📊 Métricas de produtividade simplificadas:")
    for _, row in productivity_metrics.iterrows():
        logger.info(f"   📅 {row['AnoMes']}: {row['toneladas_total']:.1f} t total, "
                   f"{row['toneladas_por_ciclo']:.3f} t/ciclo, "
                   f"{row['total_ciclos']:,.0f} ciclos")
    
    # Converter para dict para JSON
    result = productivity_metrics.to_dict(orient='records')
    
    process_time = time.time() - process_start
    logger.info(f"✅ Análise de produtividade simplificada concluída em {process_time:.2f}s")
    logger.info(f"📊 {len(result)} períodos analisados")
    
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/images/<filename>')
def serve_image(filename):
    """Servir imagens da pasta images"""
    return send_from_directory('images', filename)

@app.route('/api/cycles_by_year_month')
def cycles_by_year_month():
    logger.info("🚀 API cycles_by_year_month chamada")
    api_start_time = time.time()
    
    try:
        # Obter parâmetros de data da URL
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        
        # Usar função com filtros de data
        result = get_processed_cycles_data(data_inicio, data_fim)
        
        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Dados retornados: {len(result)} períodos")
        
        # Log dos primeiros registros para debug
        if result:
            logger.info("📋 Primeiros registros:")
            for i, record in enumerate(result[:3]):
                logger.info(f"   {i+1}. {record['AnoMes']}: {record['count']:,} ciclos")
            if len(result) > 3:
                logger.info(f"   ... e mais {len(result) - 3} períodos")
        
        return jsonify(result)
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API após {error_time:.2f}s: {str(e)}")
        logger.exception("Detalhes do erro:")
        return jsonify({'error': f'Erro ao processar dados: {str(e)}'})

@app.route('/api/cycles_by_tipo_input')
def cycles_by_tipo_input():
    logger.info("🚀 API cycles_by_tipo_input chamada")
    api_start_time = time.time()
    
    try:
        # Obter parâmetros de data da URL
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        
        # Usar função com filtros de data
        result = get_processed_cycles_by_tipo_input(data_inicio, data_fim)
        
        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API cycles_by_tipo_input concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Dados retornados: {len(result)} registros")
        
        # Log dos primeiros registros para debug
        if result:
            logger.info("📋 Primeiros registros:")
            for i, record in enumerate(result[:5]):
                logger.info(f"   {i+1}. {record['AnoMes']} - {record['Tipo Input']}: {record['count']:,} ciclos")
            if len(result) > 5:
                logger.info(f"   ... e mais {len(result) - 5} registros")
        
        return jsonify(result)
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API cycles_by_tipo_input após {error_time:.2f}s: {str(e)}")
        logger.exception("Detalhes do erro:")
        return jsonify({'error': f'Erro ao processar dados: {str(e)}'})

@app.route('/api/production_by_activity_type')
def production_by_activity_type():
    logger.info("🚀 API production_by_activity_type chamada")
    api_start_time = time.time()
    
    try:
        # Obter parâmetros de data da URL
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        
        # Usar função com filtros de data
        result = get_processed_production_by_activity_type(data_inicio, data_fim)
        
        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API production_by_activity_type concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Dados retornados: {len(result)} registros")
        
        # Log dos primeiros registros para debug
        if result:
            logger.info("📋 Primeiros registros:")
            for i, record in enumerate(result[:5]):
                logger.info(f"   {i+1}. {record['AnoMes']} - {record['Tipo de atividade']}: {record['massa_total']:,.2f} kg")
            if len(result) > 5:
                logger.info(f"   ... e mais {len(result) - 5} registros")
        
        return jsonify(result)
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API production_by_activity_type após {error_time:.2f}s: {str(e)}")
        logger.exception("Detalhes do erro:")
        return jsonify({'error': f'Erro ao processar dados: {str(e)}'})

@app.route('/api/production_by_material_spec')
def production_by_material_spec():
    logger.info("🚀 API production_by_material_spec chamada")
    api_start_time = time.time()
    
    try:
        # Obter parâmetros de data da URL
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        
        # Usar função com filtros de data
        result = get_processed_production_by_material_spec(data_inicio, data_fim)
        
        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API production_by_material_spec concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Dados retornados: {len(result)} registros")
        
        # Log dos primeiros registros para debug
        if result:
            logger.info("📋 Primeiros registros:")
            for i, record in enumerate(result[:5]):
                logger.info(f"   {i+1}. {record['AnoMes']} - {record['Especificacao de material']}: {record['massa_total']:,.2f} kg")
            if len(result) > 5:
                logger.info(f"   ... e mais {len(result) - 5} registros")
        
        return jsonify(result)
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API production_by_material_spec após {error_time:.2f}s: {str(e)}")
        logger.exception("Detalhes do erro:")
        return jsonify({'error': f'Erro ao processar dados: {str(e)}'})

@app.route('/api/production_by_material')
def production_by_material():
    logger.info("🚀 API production_by_material chamada")
    api_start_time = time.time()
    
    try:
        # Obter parâmetros de data da URL
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        
        # Usar função com filtros de data
        result = get_processed_production_by_material(data_inicio, data_fim)
        
        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API production_by_material concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Dados retornados: {len(result)} registros")
        
        # Log dos primeiros registros para debug
        if result:
            logger.info("📋 Primeiros registros:")
            for i, record in enumerate(result[:5]):
                logger.info(f"   {i+1}. {record['AnoMes']} - {record['Material']}: {record['massa_total']:,.2f} kg")
            if len(result) > 5:
                logger.info(f"   ... e mais {len(result) - 5} registros")
        
        return jsonify(result)
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API production_by_material após {error_time:.2f}s: {str(e)}")
        logger.exception("Detalhes do erro:")
        return jsonify({'error': f'Erro ao processar dados: {str(e)}'})

@app.route('/api/productivity_analysis')
def productivity_analysis():
    logger.info("🚀 API productivity_analysis chamada")
    api_start_time = time.time()
    
    try:
        # Obter parâmetros de data da URL
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        
        # Usar função com filtros de data
        result = get_processed_productivity_analysis(data_inicio, data_fim)
        
        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API productivity_analysis concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Dados retornados: {len(result)} períodos")
        
        # Log dos primeiros registros para debug
        if result:
            logger.info("📋 Primeiros registros de produtividade:")
            for i, record in enumerate(result[:3]):
                logger.info(f"   {i+1}. {record['AnoMes']}: {record['toneladas_total']:.1f} t total, "
                           f"{record['toneladas_por_ciclo']:.3f} t/ciclo, "
                           f"crescimento: {record['crescimento_toneladas_pct']:.1f}%")
            if len(result) > 3:
                logger.info(f"   ... e mais {len(result) - 3} períodos")
        
        return jsonify(result)
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API productivity_analysis após {error_time:.2f}s: {str(e)}")
        logger.exception("Detalhes do erro:")
        return jsonify({'error': f'Erro ao processar dados: {str(e)}'})

@app.route('/api/clear_cache')
def clear_cache():
    """Endpoint para limpar o cache manualmente"""
    global _cache
    logger.info("🗑️  Limpando cache...")
    
    old_cache = _cache.copy()
    _cache['raw_data'] = None
    _cache['processed_data'] = None
    _cache['processed_data_tipo_input'] = None
    _cache['files_hash'] = None
    _cache['last_check'] = None
    
    had_data = old_cache['raw_data'] is not None
    had_processed = old_cache['processed_data'] is not None
    
    logger.info("✅ Cache limpo com sucesso!")
    
    return jsonify({
        'message': 'Cache limpo com sucesso',
        'had_raw_data': had_data,
        'had_processed_data': had_processed,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    logger.info("🚀 Iniciando aplicação Flask...")
    logger.info("🌐 Servidor será executado em: http://127.0.0.1:5000")
    logger.info("📊 Endpoint da API: http://127.0.0.1:5000/api/cycles_by_year_month")
    logger.info("🏠 Interface web: http://127.0.0.1:5000")
    logger.info("🔧 Modo debug: Ativado")
    logger.info("⚡ Para parar o servidor: Ctrl+C")
    logger.info("=" * 60)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        logger.info("🛑 Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar servidor: {e}")
        logger.exception("Detalhes do erro:")
