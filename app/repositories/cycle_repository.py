import glob
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class CycleRepository:
    """Repository para acesso aos dados de ciclo com cache inteligente"""
    
    def __init__(self, data_path: str = 'CicloDetalhado'):
        self.data_path = data_path
        self._cache: Dict[str, Any] = {
            'raw_data': None,
            'processed_data': None,
            'last_check': None,
            'files_hash': None
        }
    
    def _get_files_hash(self) -> int:
        """Calcula hash dos arquivos para detectar mudanças"""
        all_files = glob.glob(f"{self.data_path}/*.xlsx")
        
        # Filtrar arquivos temporários do Excel (que começam com ~$)
        all_files = [f for f in all_files if not os.path.basename(f).startswith('~$')]
        
        files_info = []
        for filename in all_files:
            stat = os.stat(filename)
            files_info.append(f"{filename}:{stat.st_size}:{stat.st_mtime}")
        
        return hash(tuple(sorted(files_info)))
    
    def _load_excel_files(self) -> pd.DataFrame:
        """Carrega dados dos arquivos Excel"""
        logger.info("🔄 Carregando dados dos arquivos Excel...")
        start_time = time.time()
        
        all_files_raw = glob.glob(f"{self.data_path}/*.xlsx")
        
        # Filtrar arquivos temporários do Excel
        temp_files = [f for f in all_files_raw if os.path.basename(f).startswith('~$')]
        all_files = [f for f in all_files_raw if not os.path.basename(f).startswith('~$')]
        
        if temp_files:
            logger.info(f"🗑️  Ignorando {len(temp_files)} arquivo(s) temporário(s) do Excel")
        
        logger.info(f"📁 Encontrados {len(all_files)} arquivos Excel válidos")
        
        if not all_files:
            raise ValueError("Nenhum arquivo Excel válido encontrado na pasta CicloDetalhado")
        
        df_list = []
        total_rows = 0
        
        for i, filename in enumerate(all_files, 1):
            logger.info(f"📊 Carregando arquivo {i}/{len(all_files)}: {filename}")
            file_start = time.time()
            
            try:
                # Carregar as colunas necessárias
                df = pd.read_excel(
                    filename, 
                    usecols=[
                        'DataHoraInicio', 'Tipo Input', 'Massa', 
                        'Tipo de atividade', 'Especificacao de material', 
                        'Material', 'Tag carga', 'Frota carga', 'Frota transporte'
                    ]
                )
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
        
        return combined_df
    
    def get_raw_data(self) -> pd.DataFrame:
        """Obtém dados brutos com cache inteligente"""
        current_hash = self._get_files_hash()
        current_time = datetime.now()
        
        # Se tem cache válido, usar
        if (self._cache['raw_data'] is not None and 
            self._cache['files_hash'] == current_hash):
            logger.info("✅ Usando dados do cache (arquivos não modificados)")
            return self._cache['raw_data']
        
        logger.info("🔄 Cache inválido ou inexistente, carregando dados...")
        
        # Carregar dados
        raw_data = self._load_excel_files()
        
        # Atualizar cache
        self._cache['raw_data'] = raw_data
        self._cache['files_hash'] = current_hash
        self._cache['last_check'] = current_time
        logger.info("💾 Cache atualizado")
        
        return raw_data
    
    def clear_cache(self) -> Dict[str, Any]:
        """Limpa o cache e retorna informações sobre o estado anterior"""
        logger.info("🗑️  Limpando cache...")
        
        old_cache = self._cache.copy()
        self._cache['raw_data'] = None
        self._cache['processed_data'] = None
        self._cache['files_hash'] = None
        self._cache['last_check'] = None
        
        had_data = old_cache['raw_data'] is not None
        had_processed = old_cache['processed_data'] is not None
        
        logger.info("✅ Cache limpo com sucesso!")
        
        return {
            'had_raw_data': had_data,
            'had_processed_data': had_processed,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Retorna o status atual do cache"""
        return {
            'has_raw_data': self._cache['raw_data'] is not None,
            'has_processed_data': self._cache['processed_data'] is not None,
            'last_check': self._cache['last_check'].isoformat() if self._cache['last_check'] else None,
            'files_hash': self._cache['files_hash'],
            'current_files_hash': self._get_files_hash(),
            'cache_valid': (self._cache['raw_data'] is not None and 
                           self._cache['files_hash'] == self._get_files_hash())
        }
