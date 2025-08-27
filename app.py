import glob
import logging
import os
import time
from datetime import datetime

import pandas as pd
from flask import Flask, jsonify, render_template

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
            # Carregar apenas as colunas necessárias para economizar memória
            df = pd.read_excel(filename, usecols=['DataHoraInicio'])  # Apenas a coluna necessária
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

def get_processed_cycles_data():
    """Obtém dados processados com cache"""
    global _cache
    
    # Verificar se tem dados processados em cache
    if _cache['processed_data'] is not None:
        logger.info("⚡ Usando dados processados do cache")
        return _cache['processed_data']
    
    logger.info("🔄 Processando dados pela primeira vez...")
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
    
    # Cachear resultado processado
    _cache['processed_data'] = result
    logger.info("💾 Dados processados salvos no cache")
    
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cycles_by_year_month')
def cycles_by_year_month():
    logger.info("🚀 API cycles_by_year_month chamada")
    api_start_time = time.time()
    
    try:
        # Usar função otimizada com cache
        result = get_processed_cycles_data()
        
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

@app.route('/api/clear_cache')
def clear_cache():
    """Endpoint para limpar o cache manualmente"""
    global _cache
    logger.info("🗑️  Limpando cache...")
    
    old_cache = _cache.copy()
    _cache['raw_data'] = None
    _cache['processed_data'] = None
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
