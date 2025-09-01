import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from app.dto.cycle_dto import DateRangeDTO
from app.repositories.cycle_repository import CycleRepository

logger = logging.getLogger(__name__)


class CycleService:
    """Service para processamento de dados de ciclo com lógica de negócio"""
    
    def __init__(self, cycle_repository: CycleRepository):
        self.cycle_repository = cycle_repository
    
    def _apply_filters(self, df: pd.DataFrame, filters: DateRangeDTO) -> pd.DataFrame:
        """Aplica filtros aos dados"""
        logger.info("🔄 Aplicando filtros aos dados...")
        
        # Verificar se a coluna DataHoraInicio existe
        if 'DataHoraInicio' not in df.columns:
            raise ValueError('Coluna DataHoraInicio não encontrada nos dados')
        
        # Converter datas
        df['DataHoraInicio'] = pd.to_datetime(df['DataHoraInicio'], errors='coerce')
        df = df.dropna(subset=['DataHoraInicio'])
        
        # Aplicar filtros de data
        if filters.data_inicio:
            data_inicio_dt = pd.to_datetime(filters.data_inicio)
            df = df[df['DataHoraInicio'] >= data_inicio_dt]
            logger.info(f"📅 Aplicado filtro de data início: {filters.data_inicio}")
        
        if filters.data_fim:
            data_fim_dt = pd.to_datetime(filters.data_fim)
            df = df[df['DataHoraInicio'] <= data_fim_dt]
            logger.info(f"📅 Aplicado filtro de data fim: {filters.data_fim}")
        
        # Aplicar filtro por tipos de input
        if filters.tipos_input and len(filters.tipos_input) > 0:
            if 'Tipo Input' in df.columns:
                df = df[df['Tipo Input'].isin(filters.tipos_input)]
                logger.info(f"🔍 Aplicado filtro de Tipo Input: {filters.tipos_input}")
                logger.info(f"📊 Registros após filtro de Tipo Input: {len(df):,}")
        
        # Aplicar filtro por frota de transporte
        if filters.frota_transporte and len(filters.frota_transporte) > 0:
            if 'Frota transporte' in df.columns:
                df = df[df['Frota transporte'].isin(filters.frota_transporte)]
                logger.info(f"🔍 Aplicado filtro de Frota de Transporte: {filters.frota_transporte}")
                logger.info(f"📊 Registros após filtro de Frota de Transporte: {len(df):,}")
        
        logger.info(f"📊 Registros após filtros: {len(df):,}")
        
        if len(df) == 0:
            logger.warning("⚠️ Nenhum registro encontrado após aplicar filtros")
        
        return df
    
    def get_cycles_by_year_month(self, filters: DateRangeDTO) -> List[Dict[str, Any]]:
        """Obtém dados de ciclos por ano/mês"""
        logger.info("🔄 Processando dados de ciclos por ano/mês...")
        process_start = time.time()
        
        # Obter dados brutos
        df = self.cycle_repository.get_raw_data()
        
        # Aplicar filtros
        df = self._apply_filters(df, filters)
        
        if len(df) == 0:
            return []
        
        # Processar dados
        logger.info("📅 Criando períodos...")
        df['AnoMes'] = df['DataHoraInicio'].dt.to_period('M')
        
        logger.info("📊 Agrupando dados...")
        cycle_counts = df.groupby('AnoMes').size().reset_index(name='count')
        
        # Converter e ordenar
        cycle_counts['AnoMes'] = cycle_counts['AnoMes'].astype(str)
        cycle_counts = cycle_counts.sort_values('AnoMes')
        
        # Mapear campos para o formato esperado pelo DTO
        result = []
        for _, row in cycle_counts.iterrows():
            result.append({
                'ano_mes': row['AnoMes'],
                'count': row['count']
            })
        
        process_time = time.time() - process_start
        logger.info(f"✅ Processamento concluído em {process_time:.2f}s")
        logger.info(f"📊 {len(result)} períodos encontrados")
        
        return result
    
    def get_cycles_by_type_input(self, filters: DateRangeDTO) -> List[Dict[str, Any]]:
        """Obtém dados de ciclos por tipo de input"""
        logger.info("🔄 Processando dados de ciclos por tipo de input...")
        process_start = time.time()
        
        # Obter dados brutos
        df = self.cycle_repository.get_raw_data()
        
        # Verificar se a coluna Tipo Input existe
        if 'Tipo Input' not in df.columns:
            raise ValueError('Coluna Tipo Input não encontrada nos dados')
        
        # Aplicar filtros
        df = self._apply_filters(df, filters)
        
        if len(df) == 0:
            return []
        
        # Remover valores nulos em Tipo Input
        df = df.dropna(subset=['Tipo Input'])
        
        # Processar dados
        logger.info("📅 Criando períodos...")
        df['AnoMes'] = df['DataHoraInicio'].dt.to_period('M')
        
        logger.info("📊 Agrupando dados por Tipo Input...")
        cycle_counts = df.groupby(['AnoMes', 'Tipo Input']).size().reset_index(name='count')
        
        # Converter período para string e ordenar
        cycle_counts['AnoMes'] = cycle_counts['AnoMes'].astype(str)
        cycle_counts = cycle_counts.sort_values(['AnoMes', 'Tipo Input'])
        
        # Mapear campos para o formato esperado pelo DTO
        result = []
        for _, row in cycle_counts.iterrows():
            result.append({
                'ano_mes': row['AnoMes'],
                'tipo_input': row['Tipo Input'],
                'count': row['count']
            })
        
        process_time = time.time() - process_start
        logger.info(f"✅ Processamento por Tipo Input concluído em {process_time:.2f}s")
        logger.info(f"📊 {len(result)} registros encontrados")
        
        return result
    
    def get_production_by_activity_type(self, filters: DateRangeDTO) -> List[Dict[str, Any]]:
        """Obtém dados de produção por tipo de atividade"""
        logger.info("🔄 Processando dados de produção por tipo de atividade...")
        process_start = time.time()
        
        # Obter dados brutos
        df = self.cycle_repository.get_raw_data()
        
        # Verificar se as colunas necessárias existem
        required_columns = ['DataHoraInicio', 'Tipo de atividade', 'Massa', 'Tipo Input']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f'Coluna {col} não encontrada nos dados')
        
        # Aplicar filtros
        df = self._apply_filters(df, filters)
        
        if len(df) == 0:
            return []
        
        # Remover valores nulos
        df = df.dropna(subset=['DataHoraInicio', 'Tipo de atividade', 'Massa', 'Tipo Input'])
        
        # Processar dados
        logger.info("📅 Criando períodos...")
        df['AnoMes'] = df['DataHoraInicio'].dt.to_period('M')
        
        logger.info("📊 Agrupando dados por tipo de atividade...")
        production_data = df.groupby(['AnoMes', 'Tipo de atividade']).agg({
            'Massa': 'sum',
            'DataHoraInicio': 'count'
        }).reset_index()
        
        production_data.columns = ['AnoMes', 'Tipo de atividade', 'massa_total', 'count']
        
        # Converter período para string e ordenar
        production_data['AnoMes'] = production_data['AnoMes'].astype(str)
        production_data = production_data.sort_values(['AnoMes', 'Tipo de atividade'])
        
        # Mapear campos para o formato esperado pelo DTO
        result = []
        for _, row in production_data.iterrows():
            result.append({
                'ano_mes': row['AnoMes'],
                'tipo_atividade': row['Tipo de atividade'],
                'massa_total': row['massa_total'],
                'count': row['count']
            })
        
        process_time = time.time() - process_start
        logger.info(f"✅ Processamento de produção concluído em {process_time:.2f}s")
        logger.info(f"📊 {len(result)} registros encontrados")
        
        return result
    
    def get_productivity_analysis(self, filters: DateRangeDTO) -> List[Dict[str, Any]]:
        """Obtém análise de produtividade"""
        logger.info("🔄 Processando análise de produtividade...")
        process_start = time.time()
        
        # Obter dados brutos
        df = self.cycle_repository.get_raw_data()
        
        # Verificar se as colunas necessárias existem
        required_columns = ['DataHoraInicio', 'Massa', 'Tipo Input']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f'Coluna {col} não encontrada nos dados')
        
        # Aplicar filtros
        df = self._apply_filters(df, filters)
        
        if len(df) == 0:
            return []
        
        # Remover valores nulos
        df = df.dropna(subset=['DataHoraInicio', 'Massa', 'Tipo Input'])
        
        # Processar dados
        logger.info("📅 Criando períodos...")
        df['AnoMes'] = df['DataHoraInicio'].dt.to_period('M')
        
        logger.info("📊 Calculando produtividade...")
        productivity_data = df.groupby('AnoMes').agg({
            'Massa': 'sum',
            'DataHoraInicio': 'count'
        }).reset_index()
        
        productivity_data.columns = ['AnoMes', 'massa_total', 'count']
        
        # Calcular horas trabalhadas (assumindo 24h por dia, 30 dias por mês)
        productivity_data['horas_trabalhadas'] = 24 * 30
        
        # Calcular produtividade em t/h
        productivity_data['produtividade_media_ton_h'] = (
            productivity_data['massa_total'] / 1000 / productivity_data['horas_trabalhadas']
        )
        
        # Calcular crescimento percentual
        productivity_data['crescimento_toneladas_pct'] = productivity_data['massa_total'].pct_change() * 100
        # Preencher NaN com 0 para o primeiro período
        productivity_data['crescimento_toneladas_pct'] = productivity_data['crescimento_toneladas_pct'].fillna(0)
        
        # Converter período para string e ordenar
        productivity_data['AnoMes'] = productivity_data['AnoMes'].astype(str)
        productivity_data = productivity_data.sort_values('AnoMes')
        
        # Mapear campos para o formato esperado pelo DTO
        result = []
        for _, row in productivity_data.iterrows():
            result.append({
                'ano_mes': row['AnoMes'],
                'toneladas_total': row['massa_total'] / 1000,  # Converter kg para toneladas
                'produtividade_media_ton_h': row['produtividade_media_ton_h'],
                'crescimento_toneladas_pct': row['crescimento_toneladas_pct'],
                'horas_trabalhadas': row['horas_trabalhadas']
            })
        
        process_time = time.time() - process_start
        logger.info(f"✅ Análise de produtividade concluída em {process_time:.2f}s")
        logger.info(f"📊 {len(result)} períodos encontrados")
        
        return result
    
    def get_productivity_by_equipment(self, filters: DateRangeDTO) -> List[Dict[str, Any]]:
        """Obtém produtividade por equipamento"""
        logger.info("🔄 Processando produtividade por equipamento...")
        process_start = time.time()
        
        # Obter dados brutos
        df = self.cycle_repository.get_raw_data()
        
        # Verificar se as colunas necessárias existem
        required_columns = ['DataHoraInicio', 'Massa', 'Tag carga']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f'Coluna {col} não encontrada nos dados')
        
        # Aplicar filtros
        df = self._apply_filters(df, filters)
        
        if len(df) == 0:
            return []
        
        # Remover valores nulos
        df = df.dropna(subset=['DataHoraInicio', 'Massa', 'Tag carga'])
        
        # Processar dados
        logger.info("📅 Criando datas...")
        df['Data'] = df['DataHoraInicio'].dt.date.astype(str)
        
        logger.info("📊 Calculando produtividade por equipamento/dia...")
        equipment_data = df.groupby(['Data', 'Tag carga']).agg({
            'Massa': 'sum',
            'DataHoraInicio': 'count'
        }).reset_index()
        
        equipment_data.columns = ['Data', 'Equipamento', 'massa_total', 'count']
        
        # Calcular horas trabalhadas (assumindo 24h por dia)
        equipment_data['horas_trabalhadas'] = 24
        
        # Calcular produtividade em t/h
        equipment_data['toneladas_por_hora'] = (
            equipment_data['massa_total'] / 1000 / equipment_data['horas_trabalhadas']
        )
        
        # Converter massa para toneladas
        equipment_data['total_toneladas'] = equipment_data['massa_total'] / 1000
        
        # Ordenar
        equipment_data = equipment_data.sort_values(['Data', 'Equipamento'])
        
        # Mapear campos para o formato esperado pelo DTO
        result = []
        for _, row in equipment_data.iterrows():
            result.append({
                'data': row['Data'],
                'equipamento': row['Equipamento'],
                'toneladas_por_hora': row['toneladas_por_hora'],
                'total_toneladas': row['total_toneladas'],
                'horas_trabalhadas': row['horas_trabalhadas']
            })
        
        process_time = time.time() - process_start
        logger.info(f"✅ Produtividade por equipamento concluída em {process_time:.2f}s")
        logger.info(f"📊 {len(result)} registros encontrados")
        
        return result
    
    def clear_cache(self) -> Dict[str, Any]:
        """Limpa o cache"""
        return self.cycle_repository.clear_cache()
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Obtém status do cache"""
        return self.cycle_repository.get_cache_status()
