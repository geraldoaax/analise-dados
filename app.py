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
    
    # Filtrar arquivos temporários do Excel (que começam com ~$)
    all_files = [f for f in all_files if not os.path.basename(f).startswith('~$')]
    
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
    all_files_raw = glob.glob(path + "/*.xlsx")
    
    # Filtrar arquivos temporários do Excel (que começam com ~$)
    temp_files = [f for f in all_files_raw if os.path.basename(f).startswith('~$')]
    all_files = [f for f in all_files_raw if not os.path.basename(f).startswith('~$')]
    
    if temp_files:
        logger.info(f"🗑️  Ignorando {len(temp_files)} arquivo(s) temporário(s) do Excel: {[os.path.basename(f) for f in temp_files]}")
    
    logger.info(f"📁 Encontrados {len(all_files)} arquivos Excel válidos")
    
    # Verificar se há arquivos válidos para processar
    if not all_files:
        logger.error("❌ Nenhum arquivo Excel válido encontrado para processar")
        raise ValueError("Nenhum arquivo Excel válido encontrado na pasta CicloDetalhado")
    
    df_list = []
    total_rows = 0
    
    for i, filename in enumerate(all_files, 1):
        logger.info(f"📊 Carregando arquivo {i}/{len(all_files)}: {filename}")
        file_start = time.time()
        
        try:
            # Carregar as colunas necessárias (incluindo Tag carga para produtividade por equipamento e Frota transporte para filtros)
            df = pd.read_excel(filename, usecols=['DataHoraInicio', 'Tipo Input', 'Massa', 'Tipo de atividade', 'Especificacao de material', 'Material', 'Tag carga', 'Frota transporte'])
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

def get_processed_cycles_by_tipo_input(data_inicio=None, data_fim=None, tipos_input=None, frota_transporte=None):
    """Obtém dados processados por Tipo Input com filtros de data, tipos de input e frota de transporte"""
    logger.info("🔄 Processando dados por Tipo Input com filtros avançados...")
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
    
    # Aplicar filtro por tipos de input se fornecido
    if tipos_input and len(tipos_input) > 0:
        df = df[df['Tipo Input'].isin(tipos_input)]
        logger.info(f"🔍 Aplicado filtro de Tipo Input: {tipos_input}")
        logger.info(f"📊 Registros após filtro de Tipo Input: {len(df):,}")
    
    # Aplicar filtro por frota de transporte se fornecido
    if frota_transporte and len(frota_transporte) > 0:
        # Verificar se a coluna Frota transporte existe
        if 'Frota transporte' in df.columns:
            df = df[df['Frota transporte'].isin(frota_transporte)]
            logger.info(f"🔍 Aplicado filtro de Frota de Transporte: {frota_transporte}")
            logger.info(f"📊 Registros após filtro de Frota de Transporte: {len(df):,}")
    
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

def get_processed_production_by_activity_type(data_inicio=None, data_fim=None, tipos_input=None, frota_transporte=None):
    """Obtém dados de produção (soma de massa) por tipo de atividade com filtros avançados"""
    logger.info("🔄 Processando dados de produção por tipo de atividade com filtros avançados...")
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
    if 'Tipo Input' not in df.columns:
        raise ValueError('Coluna Tipo Input não encontrada nos dados')
    
    # Processar dados de forma otimizada
    logger.info("🔄 Convertendo datas...")
    df['DataHoraInicio'] = pd.to_datetime(df['DataHoraInicio'], errors='coerce')
    
    # Remover datas inválidas e valores nulos
    df = df.dropna(subset=['DataHoraInicio', 'Tipo de atividade', 'Massa', 'Tipo Input'])
    
    # Aplicar filtros de data se fornecidos
    if data_inicio:
        data_inicio_dt = pd.to_datetime(data_inicio)
        df = df[df['DataHoraInicio'] >= data_inicio_dt]
        logger.info(f"📅 Aplicado filtro de data início: {data_inicio}")
    
    if data_fim:
        data_fim_dt = pd.to_datetime(data_fim)
        df = df[df['DataHoraInicio'] <= data_fim_dt]
        logger.info(f"📅 Aplicado filtro de data fim: {data_fim}")
    
    # Aplicar filtro por tipos de input se fornecido
    if tipos_input and len(tipos_input) > 0:
        df = df[df['Tipo Input'].isin(tipos_input)]
        logger.info(f"🔍 Aplicado filtro de Tipo Input: {tipos_input}")
        logger.info(f"📊 Registros após filtro de Tipo Input: {len(df):,}")
    
    # Aplicar filtro por frota de transporte se fornecido
    if frota_transporte and len(frota_transporte) > 0:
        # Verificar se a coluna Frota transporte existe
        if 'Frota transporte' in df.columns:
            df = df[df['Frota transporte'].isin(frota_transporte)]
            logger.info(f"🔍 Aplicado filtro de Frota de Transporte: {frota_transporte}")
            logger.info(f"📊 Registros após filtro de Frota de Transporte: {len(df):,}")
    
    logger.info(f"📊 Registros após filtros: {len(df):,}")
    
    # Verificar se restaram dados após filtros
    if len(df) == 0:
        logger.warning("⚠️ Nenhum registro encontrado após aplicar filtros")
        return []
    
    logger.info("📅 Criando períodos...")
    df['AnoMes'] = df['DataHoraInicio'].dt.to_period('M')
    
    logger.info("📊 Agrupando dados por tipo de atividade e somando massa...")
    # Primeiro, calcular totais por tipo de atividade para identificar os maiores
    totals_by_activity = df.groupby('Tipo de atividade')['Massa'].sum().sort_values(ascending=False)
    logger.info(f"📋 Tipos de atividade encontrados: {len(totals_by_activity)}")
    
    # Definir quantos tipos de atividade mostrar individualmente (top 2)
    top_n = 2
    top_activities = totals_by_activity.head(top_n).index.tolist()
    logger.info(f"🔝 Top {top_n} tipos de atividade: {top_activities}")
    
    # Log detalhado dos tipos de atividade e suas massas
    for i, (activity, massa) in enumerate(totals_by_activity.head(10).items(), 1):
        status = "🏆 TOP" if activity in top_activities else "📦 OUTROS"
        logger.info(f"   {i:2d}. {activity}: {massa:,.0f} kg - {status}")
    
    # Criar nova coluna agrupando tipos de atividade menores em "Outros"
    df['Activity_Agrupada'] = df['Tipo de atividade'].apply(
        lambda x: x if x in top_activities else 'Outros'
    )
    
    # Agrupar por período e tipo de atividade agrupada
    production_data = df.groupby(['AnoMes', 'Activity_Agrupada'])['Massa'].sum().reset_index(name='massa_total')
    
    # Renomear coluna para manter compatibilidade com frontend
    production_data = production_data.rename(columns={'Activity_Agrupada': 'Tipo de atividade'})
    
    # Converter período para string e ordenar
    production_data['AnoMes'] = production_data['AnoMes'].astype(str)
    production_data = production_data.sort_values(['AnoMes', 'Tipo de atividade'])
    
    # Log do agrupamento realizado
    activities_finais = production_data['Tipo de atividade'].unique()
    tem_outros = 'Outros' in activities_finais
    logger.info(f"📋 Tipos de atividade no resultado final: {list(activities_finais)}")
    if tem_outros:
        outros_total = production_data[production_data['Tipo de atividade'] == 'Outros']['massa_total'].sum()
        logger.info(f"📦 Total agrupado em 'Outros': {outros_total:,.2f} kg")
    
    # Converter para dict para JSON
    result = production_data.to_dict(orient='records')
    
    process_time = time.time() - process_start
    logger.info(f"✅ Processamento de produção por tipo de atividade concluído em {process_time:.2f}s")
    logger.info(f"📊 {len(result)} registros encontrados")
    
    return result

def get_processed_production_by_material_spec(data_inicio=None, data_fim=None, tipos_input=None, frota_transporte=None):
    """Obtém dados de produção (soma de massa) por especificação de material com filtros avançados"""
    logger.info("🔄 Processando dados de produção por especificação de material com filtros avançados...")
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
    if 'Tipo Input' not in df.columns:
        raise ValueError('Coluna Tipo Input não encontrada nos dados')
    
    # Processar dados de forma otimizada
    logger.info("🔄 Convertendo datas...")
    df['DataHoraInicio'] = pd.to_datetime(df['DataHoraInicio'], errors='coerce')
    
    # Remover datas inválidas e valores nulos
    df = df.dropna(subset=['DataHoraInicio', 'Especificacao de material', 'Massa', 'Tipo Input'])
    
    # Aplicar filtros de data se fornecidos
    if data_inicio:
        data_inicio_dt = pd.to_datetime(data_inicio)
        df = df[df['DataHoraInicio'] >= data_inicio_dt]
        logger.info(f"📅 Aplicado filtro de data início: {data_inicio}")
    
    if data_fim:
        data_fim_dt = pd.to_datetime(data_fim)
        df = df[df['DataHoraInicio'] <= data_fim_dt]
        logger.info(f"📅 Aplicado filtro de data fim: {data_fim}")
    
    # Aplicar filtro por tipos de input se fornecido
    if tipos_input and len(tipos_input) > 0:
        df = df[df['Tipo Input'].isin(tipos_input)]
        logger.info(f"🔍 Aplicado filtro de Tipo Input: {tipos_input}")
        logger.info(f"📊 Registros após filtro de Tipo Input: {len(df):,}")
    
    # Aplicar filtro por frota de transporte se fornecido
    if frota_transporte and len(frota_transporte) > 0:
        # Verificar se a coluna Frota transporte existe
        if 'Frota transporte' in df.columns:
            df = df[df['Frota transporte'].isin(frota_transporte)]
            logger.info(f"🔍 Aplicado filtro de Frota de Transporte: {frota_transporte}")
            logger.info(f"📊 Registros após filtro de Frota de Transporte: {len(df):,}")
    
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

def get_processed_production_by_material(data_inicio=None, data_fim=None, tipos_input=None, frota_transporte=None):
    """Obtém dados de produção (soma de massa) por material com filtros avançados"""
    logger.info("🔄 Processando dados de produção por material com filtros avançados...")
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
    if 'Tipo Input' not in df.columns:
        raise ValueError('Coluna Tipo Input não encontrada nos dados')
    
    # Processar dados de forma otimizada
    logger.info("🔄 Convertendo datas...")
    df['DataHoraInicio'] = pd.to_datetime(df['DataHoraInicio'], errors='coerce')
    
    # Remover datas inválidas e valores nulos
    df = df.dropna(subset=['DataHoraInicio', 'Material', 'Massa', 'Tipo Input'])
    
    # Aplicar filtros de data se fornecidos
    if data_inicio:
        data_inicio_dt = pd.to_datetime(data_inicio)
        df = df[df['DataHoraInicio'] >= data_inicio_dt]
        logger.info(f"📅 Aplicado filtro de data início: {data_inicio}")
    
    if data_fim:
        data_fim_dt = pd.to_datetime(data_fim)
        df = df[df['DataHoraInicio'] <= data_fim_dt]
        logger.info(f"📅 Aplicado filtro de data fim: {data_fim}")
    
    # Aplicar filtro por tipos de input se fornecido
    if tipos_input and len(tipos_input) > 0:
        df = df[df['Tipo Input'].isin(tipos_input)]
        logger.info(f"🔍 Aplicado filtro de Tipo Input: {tipos_input}")
        logger.info(f"📊 Registros após filtro de Tipo Input: {len(df):,}")
    
    # Aplicar filtro por frota de transporte se fornecido
    if frota_transporte and len(frota_transporte) > 0:
        # Verificar se a coluna Frota transporte existe
        if 'Frota transporte' in df.columns:
            df = df[df['Frota transporte'].isin(frota_transporte)]
            logger.info(f"🔍 Aplicado filtro de Frota de Transporte: {frota_transporte}")
            logger.info(f"📊 Registros após filtro de Frota de Transporte: {len(df):,}")
    
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

def get_processed_production_by_frota_transporte(data_inicio=None, data_fim=None, tipos_input=None, frota_transporte=None):
    """Obtém dados de produção (soma de massa) por frota de transporte com filtros avançados"""
    logger.info("🔄 Processando dados de produção por frota de transporte com filtros avançados...")
    process_start = time.time()
    
    # Carregar dados brutos
    df = load_data_with_cache()
    
    # Verificar se as colunas existem
    if 'DataHoraInicio' not in df.columns:
        raise ValueError('Coluna DataHoraInicio não encontrada nos dados')
    if 'Frota transporte' not in df.columns:
        raise ValueError('Coluna Frota transporte não encontrada nos dados')
    if 'Massa' not in df.columns:
        raise ValueError('Coluna Massa não encontrada nos dados')
    if 'Tipo Input' not in df.columns:
        raise ValueError('Coluna Tipo Input não encontrada nos dados')
    
    # Processar dados de forma otimizada
    logger.info("🔄 Convertendo datas...")
    df['DataHoraInicio'] = pd.to_datetime(df['DataHoraInicio'], errors='coerce')
    
    # Remover datas inválidas e valores nulos, incluindo frotas vazias ou "-"
    df = df.dropna(subset=['DataHoraInicio', 'Frota transporte', 'Massa', 'Tipo Input'])
    # Filtrar frotas válidas (não vazias e diferentes de "-")
    df = df[df['Frota transporte'] != '-']
    df = df[df['Frota transporte'].str.strip() != '']
    
    # Aplicar filtros de data se fornecidos
    if data_inicio:
        data_inicio_dt = pd.to_datetime(data_inicio)
        df = df[df['DataHoraInicio'] >= data_inicio_dt]
        logger.info(f"📅 Aplicado filtro de data início: {data_inicio}")
    
    if data_fim:
        data_fim_dt = pd.to_datetime(data_fim)
        df = df[df['DataHoraInicio'] <= data_fim_dt]
        logger.info(f"📅 Aplicado filtro de data fim: {data_fim}")
    
    # Aplicar filtro por tipos de input se fornecido
    if tipos_input and len(tipos_input) > 0:
        df = df[df['Tipo Input'].isin(tipos_input)]
        logger.info(f"🔍 Aplicado filtro de Tipo Input: {tipos_input}")
        logger.info(f"📊 Registros após filtro de Tipo Input: {len(df):,}")
    
    # Aplicar filtro por frota de transporte se fornecido
    if frota_transporte and len(frota_transporte) > 0:
        df = df[df['Frota transporte'].isin(frota_transporte)]
        logger.info(f"🔍 Aplicado filtro de Frota de Transporte: {frota_transporte}")
        logger.info(f"📊 Registros após filtro de Frota de Transporte: {len(df):,}")
    
    logger.info(f"📊 Registros após filtros: {len(df):,}")
    
    # Verificar se restaram dados após filtros
    if len(df) == 0:
        logger.warning("⚠️ Nenhum registro encontrado após aplicar filtros")
        return []
    
    logger.info("📅 Criando períodos...")
    df['AnoMes'] = df['DataHoraInicio'].dt.to_period('M')
    
    logger.info("📊 Agrupando dados por frota de transporte e somando massa...")
    # Primeiro, calcular totais por frota para identificar os maiores
    totals_by_frota = df.groupby('Frota transporte')['Massa'].sum().sort_values(ascending=False)
    logger.info(f"📋 Frotas de transporte encontradas: {len(totals_by_frota)}")
    
    # Definir quantas frotas mostrar individualmente (top 3)
    top_n = 3
    top_frotas = totals_by_frota.head(top_n).index.tolist()
    logger.info(f"🔝 Top {top_n} frotas de transporte: {top_frotas}")
    
    # Log detalhado das frotas e suas massas
    for i, (frota, massa) in enumerate(totals_by_frota.head(10).items(), 1):
        status = "🏆 TOP" if frota in top_frotas else "📦 OUTROS"
        logger.info(f"   {i:2d}. {frota}: {massa:,.0f} kg - {status}")
    
    # Criar nova coluna agrupando frotas menores em "Outros"
    df['Frota_Agrupada'] = df['Frota transporte'].apply(
        lambda x: x if x in top_frotas else 'Outros'
    )
    
    # Agrupar por período e frota agrupada
    production_data = df.groupby(['AnoMes', 'Frota_Agrupada'])['Massa'].sum().reset_index(name='massa_total')
    
    # Renomear coluna para manter compatibilidade com frontend
    production_data = production_data.rename(columns={'Frota_Agrupada': 'Frota transporte'})
    
    # Converter período para string e ordenar
    production_data['AnoMes'] = production_data['AnoMes'].astype(str)
    production_data = production_data.sort_values(['AnoMes', 'Frota transporte'])
    
    # Log do agrupamento realizado
    frotas_finais = production_data['Frota transporte'].unique()
    tem_outros = 'Outros' in frotas_finais
    logger.info(f"📋 Frotas de transporte no resultado final: {list(frotas_finais)}")
    if tem_outros:
        outros_total = production_data[production_data['Frota transporte'] == 'Outros']['massa_total'].sum()
        logger.info(f"📦 Total agrupado em 'Outros': {outros_total:,.2f} kg")
    
    # Converter para dict para JSON
    result = production_data.to_dict(orient='records')
    
    process_time = time.time() - process_start
    logger.info(f"✅ Processamento de produção por frota de transporte concluído em {process_time:.2f}s")
    logger.info(f"📊 {len(result)} registros encontrados")
    
    return result

def get_processed_productivity_analysis(data_inicio=None, data_fim=None, tipos_input=None, frota_transporte=None):
    """Obtém análise de produtividade: toneladas por período e toneladas por hora (média diária e mensal)"""
    logger.info("🔄 Processando análise de produtividade com base em ton/h (média diária e mensal)...")
    process_start = time.time()
    
    # Carregar dados brutos
    df = load_data_with_cache()
    
    # Verificar se as colunas existem
    if 'DataHoraInicio' not in df.columns:
        raise ValueError('Coluna DataHoraInicio não encontrada nos dados')
    if 'Massa' not in df.columns:
        raise ValueError('Coluna Massa não encontrada nos dados')
    if 'Tipo Input' not in df.columns:
        raise ValueError('Coluna Tipo Input não encontrada nos dados')
    
    # Processar dados de forma otimizada
    logger.info("🔄 Convertendo datas...")
    df['DataHoraInicio'] = pd.to_datetime(df['DataHoraInicio'], errors='coerce')
    
    # Remover datas inválidas e valores nulos em Massa e Tipo Input
    df = df.dropna(subset=['DataHoraInicio', 'Massa', 'Tipo Input'])
    
    # Aplicar filtros de data se fornecidos
    if data_inicio:
        data_inicio_dt = pd.to_datetime(data_inicio)
        df = df[df['DataHoraInicio'] >= data_inicio_dt]
        logger.info(f"📅 Aplicado filtro de data início: {data_inicio}")
    
    if data_fim:
        data_fim_dt = pd.to_datetime(data_fim)
        df = df[df['DataHoraInicio'] <= data_fim_dt]
        logger.info(f"📅 Aplicado filtro de data fim: {data_fim}")
    
    # Aplicar filtro por tipos de input se fornecido
    if tipos_input and len(tipos_input) > 0:
        df = df[df['Tipo Input'].isin(tipos_input)]
        logger.info(f"🔍 Aplicado filtro de Tipo Input: {tipos_input}")
        logger.info(f"📊 Registros após filtro de Tipo Input: {len(df):,}")
    
    # Aplicar filtro por frota de transporte se fornecido
    if frota_transporte and len(frota_transporte) > 0:
        # Verificar se a coluna Frota transporte existe
        if 'Frota transporte' in df.columns:
            df = df[df['Frota transporte'].isin(frota_transporte)]
            logger.info(f"🔍 Aplicado filtro de Frota de Transporte: {frota_transporte}")
            logger.info(f"📊 Registros após filtro de Frota de Transporte: {len(df):,}")
    
    logger.info(f"📊 Registros após filtros: {len(df):,}")
    
    # Verificar se restaram dados após filtros
    if len(df) == 0:
        logger.warning("⚠️ Nenhum registro encontrado após aplicar filtros")
        return []
    
    logger.info("📅 Criando estrutura de dados para cálculo de produtividade por hora...")
    
    # Adicionar colunas auxiliares para cálculos
    df['Data'] = df['DataHoraInicio'].dt.date
    df['DataHora'] = df['DataHoraInicio'].dt.floor('h')  # Agrupar por hora
    df['AnoMes'] = df['DataHoraInicio'].dt.to_period('M')
    
    logger.info("📊 Calculando produtividade diária (ton/h)...")
    
    # Primeiro, calcular produtividade diária (ton/h)
    daily_productivity = []
    
    # Agrupar por data para calcular produtividade diária
    grouped_daily = df.groupby('Data')
    
    for data, day_data in grouped_daily:
        # Calcular massa total do dia em toneladas
        total_massa_kg = day_data['Massa'].sum()
        total_toneladas = total_massa_kg / 1000
        
        # Calcular horas operacionais únicas no dia
        horas_operacionais = len(day_data['DataHora'].unique())
        
        # Calcular produtividade diária (ton/h)
        if horas_operacionais > 0:
            produtividade_ton_h = total_toneladas / horas_operacionais
        else:
            produtividade_ton_h = 0
        
        daily_productivity.append({
            'Data': data,
            'AnoMes': day_data['AnoMes'].iloc[0],
            'total_toneladas': round(total_toneladas, 2),
            'horas_operacionais': horas_operacionais,
            'produtividade_ton_h': round(produtividade_ton_h, 2),
            'total_ciclos': len(day_data)
        })
    
    # Converter para DataFrame
    daily_df = pd.DataFrame(daily_productivity)
    
    logger.info("📊 Calculando métricas mensais (média das produtividades diárias)...")
    
    # Agrupar por período mensal e calcular médias
    productivity_metrics = daily_df.groupby('AnoMes').agg({
        'total_toneladas': 'sum',  # Soma total de toneladas no mês
        'produtividade_ton_h': 'mean',  # Média das produtividades diárias (ton/h)
        'horas_operacionais': 'sum',  # Total de horas operacionais no mês
        'total_ciclos': 'sum'  # Total de ciclos no mês
    }).round(2)
    
    # Renomear colunas para clareza
    productivity_metrics.columns = ['toneladas_total', 'produtividade_media_ton_h', 'horas_operacionais_total', 'total_ciclos']
    
    # Calcular crescimento em toneladas e produtividade
    productivity_metrics['crescimento_toneladas_pct'] = productivity_metrics['toneladas_total'].pct_change() * 100
    productivity_metrics['crescimento_prod_pct'] = productivity_metrics['produtividade_media_ton_h'].pct_change() * 100
    
    # Resetar index e converter período para string
    productivity_metrics = productivity_metrics.reset_index()
    productivity_metrics['AnoMes'] = productivity_metrics['AnoMes'].astype(str)
    
    # Preencher NaN com 0 para o primeiro período (sem período anterior para comparar)
    productivity_metrics = productivity_metrics.fillna(0)
    
    # Ordenar por período
    productivity_metrics = productivity_metrics.sort_values('AnoMes')
    
    # Log das métricas calculadas
    logger.info("📊 Métricas de produtividade (ton/h - média mensal das médias diárias):")
    for _, row in productivity_metrics.iterrows():
        logger.info(f"   📅 {row['AnoMes']}: {row['toneladas_total']:.1f} t total, "
                   f"{row['produtividade_media_ton_h']:.2f} t/h (média), "
                   f"{row['horas_operacionais_total']:,.0f} h operacionais, "
                   f"{row['total_ciclos']:,.0f} ciclos")
    
    # Converter para dict para JSON
    result = productivity_metrics.to_dict(orient='records')
    
    process_time = time.time() - process_start
    logger.info(f"✅ Análise de produtividade (ton/h) concluída em {process_time:.2f}s")
    logger.info(f"📊 {len(result)} períodos analisados")
    
    return result

def get_processed_productivity_by_equipment(data_inicio=None, data_fim=None, frota_transporte=None):
    """Obtém análise de produtividade por equipamento de carga: toneladas/hora por Tag carga"""
    logger.info("🔄 Processando análise de produtividade por equipamento de carga com filtro de data...")
    process_start = time.time()
    
    # Carregar dados brutos
    df = load_data_with_cache()
    
    # Verificar se as colunas existem
    if 'DataHoraInicio' not in df.columns:
        raise ValueError('Coluna DataHoraInicio não encontrada nos dados')
    if 'Massa' not in df.columns:
        raise ValueError('Coluna Massa não encontrada nos dados')
    if 'Tag carga' not in df.columns:
        raise ValueError('Coluna Tag carga não encontrada nos dados')
    
    # Processar dados de forma otimizada
    logger.info("🔄 Convertendo datas...")
    df['DataHoraInicio'] = pd.to_datetime(df['DataHoraInicio'], errors='coerce')
    
    # Remover datas inválidas e valores nulos
    df = df.dropna(subset=['DataHoraInicio', 'Massa', 'Tag carga'])
    
    # Filtrar apenas registros com Tag carga válida (não '-' ou vazio)
    df = df[df['Tag carga'] != '-']
    df = df[df['Tag carga'].str.strip() != '']
    
    # Aplicar filtro por frota de transporte se fornecido
    if frota_transporte and len(frota_transporte) > 0:
        # Verificar se a coluna Frota transporte existe
        if 'Frota transporte' in df.columns:
            df = df[df['Frota transporte'].isin(frota_transporte)]
            logger.info(f"🔍 Aplicado filtro de Frota de Transporte: {frota_transporte}")
            logger.info(f"📊 Registros após filtro de Frota de Transporte: {len(df):,}")
    
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
    
    logger.info("📅 Criando períodos DIÁRIOS...")
    df['Data'] = df['DataHoraInicio'].dt.date
    
    logger.info("🚛 Calculando produtividade DIÁRIA por equipamento de carga...")
    
    # Calcular horas operacionais por equipamento (Tag carga) por DIA
    # Agrupamos por Data, Tag carga, e hora para contar horas únicas de operação
    df['DataHora'] = df['DataHoraInicio'].dt.floor('h')  # Agrupar por hora
    
    # Para cada equipamento e DIA, calcular:
    # 1. Total de massa transportada no dia
    # 2. Horas operacionais únicas no dia
    # 3. Toneladas por hora
    
    equipment_productivity = []
    
    # Agrupar por Data e Tag carga
    grouped = df.groupby(['Data', 'Tag carga'])
    
    for (data, equipamento), eq_data in grouped:
        # Calcular métricas do dia
        total_massa_kg = eq_data['Massa'].sum()
        total_toneladas = total_massa_kg / 1000
        total_ciclos = len(eq_data)
        
        # Calcular horas operacionais únicas no dia
        horas_operacionais = len(eq_data['DataHora'].unique())
        
        # Calcular toneladas por hora (se houve operação)
        if horas_operacionais > 0:
            toneladas_por_hora = total_toneladas / horas_operacionais
        else:
            toneladas_por_hora = 0
        
        equipment_productivity.append({
            'Data': str(data),
            'Equipamento': equipamento,
            'total_toneladas': round(total_toneladas, 2),
            'horas_operacionais': horas_operacionais,
            'toneladas_por_hora': round(toneladas_por_hora, 2),
            'total_ciclos': total_ciclos,
            'ciclos_por_hora': round(total_ciclos / horas_operacionais if horas_operacionais > 0 else 0, 1)
        })
    
    # Converter para DataFrame para facilitar ordenação
    result_df = pd.DataFrame(equipment_productivity)
    result_df = result_df.sort_values(['Data', 'Equipamento'])
    
    # Log das métricas calculadas
    logger.info("🚛 Métricas de produtividade DIÁRIA por equipamento de carga:")
    for _, row in result_df.head(10).iterrows():
        logger.info(f"   📅 {row['Data']} - {row['Equipamento']}: "
                   f"{row['toneladas_por_hora']:.2f} t/h, "
                   f"{row['total_toneladas']:.1f} t total, "
                   f"{row['horas_operacionais']} horas op.")
    
    # Converter para dict para JSON
    result = result_df.to_dict(orient='records')
    
    process_time = time.time() - process_start
    logger.info(f"✅ Análise de produtividade DIÁRIA por equipamento de carga concluída em {process_time:.2f}s")
    logger.info(f"📊 {len(result)} registros de equipamento/dia analisados")
    
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

@app.route('/api/tipos_input')
def get_tipos_input():
    """Retorna lista única de tipos de input disponíveis nos dados"""
    logger.info("🚀 API tipos_input chamada")
    api_start_time = time.time()
    
    try:
        # Carregar dados brutos
        df = load_data_with_cache()
        
        # Verificar se a coluna existe
        if 'Tipo Input' not in df.columns:
            raise ValueError('Coluna Tipo Input não encontrada nos dados')
        
        # Obter tipos únicos, excluindo valores nulos
        tipos_input = df['Tipo Input'].dropna().unique().tolist()
        tipos_input.sort()  # Ordenar alfabeticamente
        
        logger.info(f"✅ API tipos_input concluída com sucesso!")
        logger.info(f"📊 {len(tipos_input)} tipos de input encontrados: {tipos_input}")
        logger.info(f"⏱️ Tempo total da API: {time.time() - api_start_time:.2f}s")
        
        return jsonify(tipos_input)
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API tipos_input após {error_time:.2f}s: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/frota_transporte')
def get_frota_transporte():
    """Retorna lista única de frotas de transporte (Tag carga) disponíveis nos dados"""
    logger.info("🚀 API frota_transporte chamada")
    api_start_time = time.time()
    
    try:
        # Carregar dados brutos
        df = load_data_with_cache()
        
        # Verificar se a coluna existe
        if 'Frota transporte' not in df.columns:
            raise ValueError('Coluna Frota transporte não encontrada nos dados')
        
        # Obter frotas únicas, excluindo valores nulos, vazios e "-"
        frota_transporte = df['Frota transporte'].dropna()
        frota_transporte = frota_transporte[frota_transporte != '-']
        frota_transporte = frota_transporte[frota_transporte.str.strip() != '']
        frota_transporte = frota_transporte.unique().tolist()
        frota_transporte.sort()  # Ordenar alfabeticamente
        
        logger.info(f"✅ API frota_transporte concluída com sucesso!")
        logger.info(f"📊 {len(frota_transporte)} frotas de transporte encontradas: {frota_transporte}")
        logger.info(f"⏱️ Tempo total da API: {time.time() - api_start_time:.2f}s")
        
        return jsonify(frota_transporte)
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API frota_transporte após {error_time:.2f}s: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cycles_by_tipo_input')
def cycles_by_tipo_input():
    logger.info("🚀 API cycles_by_tipo_input chamada")
    api_start_time = time.time()
    
    try:
        # Obter parâmetros de data da URL
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Obter parâmetros de tipos de input (pode ser uma lista separada por vírgula)
        tipos_input_param = request.args.get('tipos_input')
        tipos_input = None
        if tipos_input_param:
            tipos_input = [tipo.strip() for tipo in tipos_input_param.split(',') if tipo.strip()]
        
        # Obter parâmetros de frota de transporte (pode ser uma lista separada por vírgula)
        frota_transporte_param = request.args.get('frota_transporte')
        frota_transporte = None
        if frota_transporte_param:
            frota_transporte = [frota.strip() for frota in frota_transporte_param.split(',') if frota.strip()]
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        logger.info(f"🔍 Filtro Tipos Input: {tipos_input}")
        logger.info(f"🔍 Filtro Frota Transporte: {frota_transporte}")
        
        # Usar função com filtros de data, tipos de input e frota de transporte
        result = get_processed_cycles_by_tipo_input(data_inicio, data_fim, tipos_input, frota_transporte)
        
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
        
        # Obter parâmetros de tipos de input (pode ser uma lista separada por vírgula)
        tipos_input_param = request.args.get('tipos_input')
        tipos_input = None
        if tipos_input_param:
            tipos_input = [tipo.strip() for tipo in tipos_input_param.split(',') if tipo.strip()]
        
        # Obter parâmetros de frota de transporte (pode ser uma lista separada por vírgula)
        frota_transporte_param = request.args.get('frota_transporte')
        frota_transporte = None
        if frota_transporte_param:
            frota_transporte = [frota.strip() for frota in frota_transporte_param.split(',') if frota.strip()]
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        logger.info(f"🔍 Filtro Tipos Input: {tipos_input}")
        logger.info(f"🔍 Filtro Frota Transporte: {frota_transporte}")
        
        # Usar função com filtros de data, tipos de input e frota de transporte
        result = get_processed_production_by_activity_type(data_inicio, data_fim, tipos_input, frota_transporte)
        
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
        
        # Obter parâmetros de tipos de input (pode ser uma lista separada por vírgula)
        tipos_input_param = request.args.get('tipos_input')
        tipos_input = None
        if tipos_input_param:
            tipos_input = [tipo.strip() for tipo in tipos_input_param.split(',') if tipo.strip()]
        
        # Obter parâmetros de frota de transporte (pode ser uma lista separada por vírgula)
        frota_transporte_param = request.args.get('frota_transporte')
        frota_transporte = None
        if frota_transporte_param:
            frota_transporte = [frota.strip() for frota in frota_transporte_param.split(',') if frota.strip()]
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        logger.info(f"🔍 Filtro Tipos Input: {tipos_input}")
        logger.info(f"🔍 Filtro Frota Transporte: {frota_transporte}")
        
        # Usar função com filtros de data, tipos de input e frota de transporte
        result = get_processed_production_by_material_spec(data_inicio, data_fim, tipos_input, frota_transporte)
        
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
        
        # Obter parâmetros de tipos de input (pode ser uma lista separada por vírgula)
        tipos_input_param = request.args.get('tipos_input')
        tipos_input = None
        if tipos_input_param:
            tipos_input = [tipo.strip() for tipo in tipos_input_param.split(',') if tipo.strip()]
        
        # Obter parâmetros de frota de transporte (pode ser uma lista separada por vírgula)
        frota_transporte_param = request.args.get('frota_transporte')
        frota_transporte = None
        if frota_transporte_param:
            frota_transporte = [frota.strip() for frota in frota_transporte_param.split(',') if frota.strip()]
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        logger.info(f"🔍 Filtro Tipos Input: {tipos_input}")
        logger.info(f"🔍 Filtro Frota Transporte: {frota_transporte}")
        
        # Usar função com filtros de data, tipos de input e frota de transporte
        result = get_processed_production_by_material(data_inicio, data_fim, tipos_input, frota_transporte)
        
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

@app.route('/api/production_by_frota_transporte')
def production_by_frota_transporte():
    logger.info("🚀 API production_by_frota_transporte chamada")
    api_start_time = time.time()
    
    try:
        # Obter parâmetros de data da URL
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Obter parâmetros de tipos de input (pode ser uma lista separada por vírgula)
        tipos_input_param = request.args.get('tipos_input')
        tipos_input = None
        if tipos_input_param:
            tipos_input = [tipo.strip() for tipo in tipos_input_param.split(',') if tipo.strip()]
        
        # Obter parâmetros de frota de transporte (pode ser uma lista separada por vírgula)
        frota_transporte_param = request.args.get('frota_transporte')
        frota_transporte = None
        if frota_transporte_param:
            frota_transporte = [frota.strip() for frota in frota_transporte_param.split(',') if frota.strip()]
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        logger.info(f"🔍 Filtro Tipos Input: {tipos_input}")
        logger.info(f"🔍 Filtro Frota Transporte: {frota_transporte}")
        
        # Usar função com filtros de data, tipos de input e frota de transporte
        result = get_processed_production_by_frota_transporte(data_inicio, data_fim, tipos_input, frota_transporte)
        
        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API production_by_frota_transporte concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Dados retornados: {len(result)} registros")
        
        # Log dos primeiros registros para debug
        if result:
            logger.info("📋 Primeiros registros:")
            for i, record in enumerate(result[:5]):
                logger.info(f"   {i+1}. {record['AnoMes']} - {record['Frota transporte']}: {record['massa_total']:,.2f} kg")
            if len(result) > 5:
                logger.info(f"   ... e mais {len(result) - 5} registros")
        
        return jsonify(result)
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API production_by_frota_transporte após {error_time:.2f}s: {str(e)}")
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
        
        # Obter parâmetros de tipos de input (pode ser uma lista separada por vírgula)
        tipos_input_param = request.args.get('tipos_input')
        tipos_input = None
        if tipos_input_param:
            tipos_input = [tipo.strip() for tipo in tipos_input_param.split(',') if tipo.strip()]
        
        # Obter parâmetros de frota de transporte (pode ser uma lista separada por vírgula)
        frota_transporte_param = request.args.get('frota_transporte')
        frota_transporte = None
        if frota_transporte_param:
            frota_transporte = [frota.strip() for frota in frota_transporte_param.split(',') if frota.strip()]
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        logger.info(f"🔍 Filtro Tipos Input: {tipos_input}")
        logger.info(f"🔍 Filtro Frota Transporte: {frota_transporte}")
        
        # Usar função com filtros de data, tipos de input e frota de transporte
        result = get_processed_productivity_analysis(data_inicio, data_fim, tipos_input, frota_transporte)
        
        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API productivity_analysis concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Dados retornados: {len(result)} períodos")
        
        # Log dos primeiros registros para debug
        if result:
            logger.info("📋 Primeiros registros de produtividade:")
            for i, record in enumerate(result[:3]):
                logger.info(f"   {i+1}. {record['AnoMes']}: {record['toneladas_total']:.1f} t total, "
                           f"{record['produtividade_media_ton_h']:.2f} t/h média, "
                           f"crescimento: {record['crescimento_toneladas_pct']:.1f}%")
            if len(result) > 3:
                logger.info(f"   ... e mais {len(result) - 3} períodos")
        
        return jsonify(result)
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API productivity_analysis após {error_time:.2f}s: {str(e)}")
        logger.exception("Detalhes do erro:")
        return jsonify({'error': f'Erro ao processar dados: {str(e)}'})

@app.route('/api/productivity_by_equipment')
def productivity_by_equipment():
    logger.info("🚀 API productivity_by_equipment (Tag carga) chamada")
    api_start_time = time.time()
    
    try:
        # Obter parâmetros de data da URL
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Obter parâmetros de frota de transporte (pode ser uma lista separada por vírgula)
        frota_transporte_param = request.args.get('frota_transporte')
        frota_transporte = None
        if frota_transporte_param:
            frota_transporte = [frota.strip() for frota in frota_transporte_param.split(',') if frota.strip()]
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        logger.info(f"🔍 Filtro Frota Transporte: {frota_transporte}")
        
        # Usar função com filtros de data e frota de transporte
        result = get_processed_productivity_by_equipment(data_inicio, data_fim, frota_transporte)
        
        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API productivity_by_equipment (Tag carga DIÁRIA) concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Dados retornados: {len(result)} registros equipamento/dia")
        
        # Log dos primeiros registros para debug
        if result:
            logger.info("📋 Primeiros registros de produtividade DIÁRIA por equipamento de carga:")
            for i, record in enumerate(result[:5]):
                logger.info(f"   {i+1}. {record['Data']} - {record['Equipamento']}: "
                           f"{record['toneladas_por_hora']:.2f} t/h, "
                           f"{record['total_toneladas']:.1f} t total")
            if len(result) > 5:
                logger.info(f"   ... e mais {len(result) - 5} registros")
        
        return jsonify(result)
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API productivity_by_equipment após {error_time:.2f}s: {str(e)}")
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
        'timestamp': datetime.now().isoformat(),
        'info': 'Cache limpo - próxima requisição irá recarregar todos os dados'
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
