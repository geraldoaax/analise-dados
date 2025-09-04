from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class DateRangeDTO(BaseModel):
    """DTO para filtros de data"""
    data_inicio: Optional[str] = Field(None, description="Data de início no formato YYYY-MM-DD")
    data_fim: Optional[str] = Field(None, description="Data de fim no formato YYYY-MM-DD")
    tipos_input: Optional[List[str]] = Field(None, description="Lista de tipos de input para filtrar")
    frota_transporte: Optional[List[str]] = Field(None, description="Lista de frotas de transporte para filtrar")
    frota_carga: Optional[List[str]] = Field(None, description="Lista de frotas de carga para filtrar")
    tag_carga: Optional[List[str]] = Field(None, description="Lista de valores da coluna 'Tag Carga' para filtrar")

    @validator('data_inicio', 'data_fim')
    def validate_date_format(cls, v):
        if v is not None:
            # Tentar diferentes formatos de data
            date_formats = [
                '%Y-%m-%d',           # YYYY-MM-DD
                '%Y-%m-%dT%H:%M',     # YYYY-MM-DDTHH:MM
                '%Y-%m-%dT%H:%M:%S',  # YYYY-MM-DDTHH:MM:SS
                '%Y-%m-%dT%H:%M:%S.%f'  # YYYY-MM-DDTHH:MM:SS.microseconds
            ]
            
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(v, date_format)
                    # Retornar apenas a parte da data (YYYY-MM-DD)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            raise ValueError('Data deve estar no formato YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS')
        return v


class CycleDataDTO(BaseModel):
    """DTO para dados de ciclo processados"""
    ano_mes: str = Field(..., description="Período no formato YYYY-MM")
    count: int = Field(..., description="Quantidade de ciclos no período")


class CycleByTypeDTO(BaseModel):
    """DTO para dados de ciclo por tipo de input"""
    ano_mes: str = Field(..., description="Período no formato YYYY-MM")
    tipo_input: str = Field(..., description="Tipo de input")
    count: int = Field(..., description="Quantidade de ciclos")


class ProductionDataDTO(BaseModel):
    """DTO para dados de produção por tipo de atividade"""
    ano_mes: str = Field(..., description="Período no formato YYYY-MM")
    tipo_atividade: str = Field(..., description="Tipo de atividade")
    massa_total: float = Field(..., description="Massa total em kg")
    count: int = Field(..., description="Quantidade de registros")


class ProductivityDataDTO(BaseModel):
    """DTO para dados de produtividade"""
    ano_mes: str = Field(..., description="Período no formato YYYY-MM")
    toneladas_total: float = Field(..., description="Toneladas totais")
    produtividade_media_ton_h: float = Field(..., description="Produtividade média em t/h")
    crescimento_toneladas_pct: float = Field(..., description="Crescimento percentual")
    horas_trabalhadas: float = Field(..., description="Horas trabalhadas")


class EquipmentProductivityDTO(BaseModel):
    """DTO para produtividade por equipamento"""
    data: str = Field(..., description="Data no formato YYYY-MM-DD")
    equipamento: str = Field(..., description="Identificação do equipamento")
    toneladas_por_hora: float = Field(..., description="Produtividade em t/h")
    total_toneladas: float = Field(..., description="Total de toneladas")
    horas_trabalhadas: float = Field(..., description="Horas trabalhadas")


class MaterialSpecProductionDTO(BaseModel):
    """DTO para produção por especificação de material"""
    ano_mes: str = Field(..., description="Período no formato YYYY-MM")
    especificacao_material: str = Field(..., description="Especificação do material")
    massa_total: float = Field(..., description="Massa total em kg")
    count: int = Field(..., description="Quantidade de registros")


class MaterialProductionDTO(BaseModel):
    """DTO para produção por material"""
    ano_mes: str = Field(..., description="Período no formato YYYY-MM")
    material: str = Field(..., description="Tipo de material")
    massa_total: float = Field(..., description="Massa total em kg")
    count: int = Field(..., description="Quantidade de registros")


class FrotaTransporteProductionDTO(BaseModel):
    """DTO para produção por frota de transporte"""
    ano_mes: str = Field(..., description="Período no formato YYYY-MM")
    frota_transporte: str = Field(..., description="Frota de transporte")
    massa_total: float = Field(..., description="Massa total em kg")
    count: int = Field(..., description="Quantidade de registros")


class FrotaCargaProductionDTO(BaseModel):
    """DTO para produção por frota de carga"""
    ano_mes: str = Field(..., description="Período no formato YYYY-MM")
    frota_carga: str = Field(..., description="Frota de carga")
    massa_total: float = Field(..., description="Massa total em kg")
    count: int = Field(..., description="Quantidade de registros")


class CacheStatusDTO(BaseModel):
    """DTO para status do cache"""
    message: str = Field(..., description="Mensagem de status")
    had_raw_data: bool = Field(..., description="Se tinha dados brutos no cache")
    had_processed_data: bool = Field(..., description="Se tinha dados processados no cache")
    timestamp: str = Field(..., description="Timestamp da operação")
    info: str = Field(..., description="Informações adicionais")


class ErrorResponseDTO(BaseModel):
    """DTO para respostas de erro"""
    error: str = Field(..., description="Mensagem de erro")
    detail: Optional[str] = Field(None, description="Detalhes do erro")
    timestamp: str = Field(..., description="Timestamp do erro")
