import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.dto.cycle_dto import (CacheStatusDTO, CycleByTypeDTO, CycleDataDTO,
                               DateRangeDTO, EquipmentProductivityDTO,
                               ErrorResponseDTO, ProductionDataDTO,
                               ProductivityDataDTO)
from app.services.cycle_service import CycleService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["cycle"])


def get_cycle_service() -> CycleService:
    """Dependency injection para CycleService"""
    from app.modules.cycle_module import get_cycle_service
    return get_cycle_service()


@router.get("/cycles_by_year_month", response_model=List[CycleDataDTO])
async def get_cycles_by_year_month(
    data_inicio: Optional[str] = Query(None, description="Data de início (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data de fim (YYYY-MM-DD)"),
    tipos_input: Optional[str] = Query(None, description="Tipos de input separados por vírgula"),
    frota_transporte: Optional[str] = Query(None, description="Frotas de transporte separadas por vírgula"),
    cycle_service: CycleService = Depends(get_cycle_service)
):
    """Obtém dados de ciclos por ano/mês"""
    logger.info("🚀 API cycles_by_year_month chamada")
    api_start_time = time.time()
    
    try:
        # Processar parâmetros
        tipos_input_list = None
        if tipos_input:
            tipos_input_list = [tipo.strip() for tipo in tipos_input.split(',') if tipo.strip()]
        
        frota_transporte_list = None
        if frota_transporte:
            frota_transporte_list = [frota.strip() for frota in frota_transporte.split(',') if frota.strip()]
        
        # Criar DTO de filtros
        filters = DateRangeDTO(
            data_inicio=data_inicio,
            data_fim=data_fim,
            tipos_input=tipos_input_list,
            frota_transporte=frota_transporte_list
        )
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        logger.info(f"🔍 Filtro Tipos Input: {tipos_input_list}")
        logger.info(f"🔍 Filtro Frota Transporte: {frota_transporte_list}")
        
        # Processar dados
        result = cycle_service.get_cycles_by_year_month(filters)
        
        # Validar estrutura dos dados antes de retornar
        if result:
            logger.info("🔍 Validando estrutura dos dados retornados...")
            for i, item in enumerate(result):
                if not isinstance(item, dict):
                    logger.error(f"❌ Item {i} não é um dicionário: {type(item)}")
                    raise HTTPException(status_code=500, detail=f"Estrutura de dados inválida: item {i}")
                
                required_fields = ['ano_mes', 'count']
                for field in required_fields:
                    if field not in item:
                        logger.error(f"❌ Campo obrigatório '{field}' não encontrado no item {i}")
                        raise HTTPException(status_code=500, detail=f"Campo obrigatório '{field}' não encontrado")
                
                logger.info(f"✅ Item {i} validado: {item}")
        
        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API cycles_by_year_month concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Dados retornados: {len(result)} períodos")
        
        return result
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API cycles_by_year_month após {error_time:.2f}s: {str(e)}")
        logger.exception("Detalhes do erro:")
        raise HTTPException(status_code=500, detail=f"Erro ao processar dados: {str(e)}")


@router.get("/cycles_by_type_input", response_model=List[CycleByTypeDTO])
async def get_cycles_by_type_input(
    data_inicio: Optional[str] = Query(None, description="Data de início (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data de fim (YYYY-MM-DD)"),
    tipos_input: Optional[str] = Query(None, description="Tipos de input separados por vírgula"),
    frota_transporte: Optional[str] = Query(None, description="Frotas de transporte separadas por vírgula"),
    cycle_service: CycleService = Depends(get_cycle_service)
):
    """Obtém dados de ciclos por tipo de input"""
    logger.info("🚀 API cycles_by_type_input chamada")
    api_start_time = time.time()
    
    try:
        # Processar parâmetros
        tipos_input_list = None
        if tipos_input:
            tipos_input_list = [tipo.strip() for tipo in tipos_input.split(',') if tipo.strip()]
        
        frota_transporte_list = None
        if frota_transporte:
            frota_transporte_list = [frota.strip() for frota in frota_transporte.split(',') if frota.strip()]
        
        # Criar DTO de filtros
        filters = DateRangeDTO(
            data_inicio=data_inicio,
            data_fim=data_fim,
            tipos_input=tipos_input_list,
            frota_transporte=frota_transporte_list
        )
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        logger.info(f"🔍 Filtro Tipos Input: {tipos_input_list}")
        logger.info(f"🔍 Filtro Frota Transporte: {frota_transporte_list}")
        
        # Processar dados
        result = cycle_service.get_cycles_by_type_input(filters)
        
        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API cycles_by_type_input concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Dados retornados: {len(result)} registros")
        
        return result
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API cycles_by_type_input após {error_time:.2f}s: {str(e)}")
        logger.exception("Detalhes do erro:")
        raise HTTPException(status_code=500, detail=f"Erro ao processar dados: {str(e)}")


@router.get("/production_by_activity_type", response_model=List[ProductionDataDTO])
async def get_production_by_activity_type(
    data_inicio: Optional[str] = Query(None, description="Data de início (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data de fim (YYYY-MM-DD)"),
    tipos_input: Optional[str] = Query(None, description="Tipos de input separados por vírgula"),
    frota_transporte: Optional[str] = Query(None, description="Frotas de transporte separadas por vírgula"),
    cycle_service: CycleService = Depends(get_cycle_service)
):
    """Obtém dados de produção por tipo de atividade"""
    logger.info("🚀 API production_by_activity_type chamada")
    api_start_time = time.time()
    
    try:
        # Processar parâmetros
        tipos_input_list = None
        if tipos_input:
            tipos_input_list = [tipo.strip() for tipo in tipos_input.split(',') if tipo.strip()]
        
        frota_transporte_list = None
        if frota_transporte:
            frota_transporte_list = [frota.strip() for frota in frota_transporte.split(',') if frota.strip()]
        
        # Criar DTO de filtros
        filters = DateRangeDTO(
            data_inicio=data_inicio,
            data_fim=data_fim,
            tipos_input=tipos_input_list,
            frota_transporte=frota_transporte_list
        )
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        logger.info(f"🔍 Filtro Tipos Input: {tipos_input_list}")
        logger.info(f"🔍 Filtro Frota Transporte: {frota_transporte_list}")
        
        # Processar dados
        result = cycle_service.get_production_by_activity_type(filters)
        
        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API production_by_activity_type concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Dados retornados: {len(result)} registros")
        
        return result
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API production_by_activity_type após {error_time:.2f}s: {str(e)}")
        logger.exception("Detalhes do erro:")
        raise HTTPException(status_code=500, detail=f"Erro ao processar dados: {str(e)}")


@router.get("/productivity_analysis", response_model=List[ProductivityDataDTO])
async def get_productivity_analysis(
    data_inicio: Optional[str] = Query(None, description="Data de início (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data de fim (YYYY-MM-DD)"),
    tipos_input: Optional[str] = Query(None, description="Tipos de input separados por vírgula"),
    frota_transporte: Optional[str] = Query(None, description="Frotas de transporte separadas por vírgula"),
    cycle_service: CycleService = Depends(get_cycle_service)
):
    """Obtém análise de produtividade"""
    logger.info("🚀 API productivity_analysis chamada")
    api_start_time = time.time()
    
    try:
        # Processar parâmetros
        tipos_input_list = None
        if tipos_input:
            tipos_input_list = [tipo.strip() for tipo in tipos_input.split(',') if tipo.strip()]
        
        frota_transporte_list = None
        if frota_transporte:
            frota_transporte_list = [frota.strip() for frota in frota_transporte.split(',') if frota.strip()]
        
        # Criar DTO de filtros
        filters = DateRangeDTO(
            data_inicio=data_inicio,
            data_fim=data_fim,
            tipos_input=tipos_input_list,
            frota_transporte=frota_transporte_list
        )
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        logger.info(f"🔍 Filtro Tipos Input: {tipos_input_list}")
        logger.info(f"🔍 Filtro Frota Transporte: {frota_transporte_list}")
        
        # Processar dados
        result = cycle_service.get_productivity_analysis(filters)
        
        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API productivity_analysis concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Dados retornados: {len(result)} períodos")
        
        return result
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API productivity_analysis após {error_time:.2f}s: {str(e)}")
        logger.exception("Detalhes do erro:")
        raise HTTPException(status_code=500, detail=f"Erro ao processar dados: {str(e)}")


@router.get("/productivity_by_equipment", response_model=List[EquipmentProductivityDTO])
async def get_productivity_by_equipment(
    data_inicio: Optional[str] = Query(None, description="Data de início (YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data de fim (YYYY-MM-DD)"),
    frota_transporte: Optional[str] = Query(None, description="Frotas de transporte separadas por vírgula"),
    cycle_service: CycleService = Depends(get_cycle_service)
):
    """Obtém produtividade por equipamento"""
    logger.info("🚀 API productivity_by_equipment chamada")
    api_start_time = time.time()
    
    try:
        # Processar parâmetros
        frota_transporte_list = None
        if frota_transporte:
            frota_transporte_list = [frota.strip() for frota in frota_transporte.split(',') if frota.strip()]
        
        # Criar DTO de filtros
        filters = DateRangeDTO(
            data_inicio=data_inicio,
            data_fim=data_fim,
            tipos_input=None,
            frota_transporte=frota_transporte_list
        )
        
        logger.info(f"📅 Filtros recebidos - Início: {data_inicio}, Fim: {data_fim}")
        logger.info(f"🔍 Filtro Frota Transporte: {frota_transporte_list}")
        
        # Processar dados
        result = cycle_service.get_productivity_by_equipment(filters)
        
        total_api_time = time.time() - api_start_time
        logger.info(f"✅ API productivity_by_equipment concluída com sucesso!")
        logger.info(f"⏱️  Tempo total da API: {total_api_time:.2f}s")
        logger.info(f"📊 Dados retornados: {len(result)} registros")
        
        return result
    
    except Exception as e:
        error_time = time.time() - api_start_time
        logger.error(f"❌ Erro na API productivity_by_equipment após {error_time:.2f}s: {str(e)}")
        logger.exception("Detalhes do erro:")
        raise HTTPException(status_code=500, detail=f"Erro ao processar dados: {str(e)}")


@router.post("/clear_cache", response_model=CacheStatusDTO)
async def clear_cache(cycle_service: CycleService = Depends(get_cycle_service)):
    """Limpa o cache manualmente"""
    logger.info("🗑️  Limpando cache...")
    
    try:
        cache_info = cycle_service.clear_cache()
        
        return CacheStatusDTO(
            message="Cache limpo com sucesso",
            had_raw_data=cache_info['had_raw_data'],
            had_processed_data=cache_info['had_processed_data'],
            timestamp=cache_info['timestamp'],
            info="Cache limpo - próxima requisição irá recarregar todos os dados"
        )
    
    except Exception as e:
        logger.error(f"❌ Erro ao limpar cache: {str(e)}")
        logger.exception("Detalhes do erro:")
        raise HTTPException(status_code=500, detail=f"Erro ao limpar cache: {str(e)}")


@router.get("/cache_status", response_model=Dict[str, Any])
async def get_cache_status(cycle_service: CycleService = Depends(get_cycle_service)):
    """Obtém status do cache"""
    try:
        return cycle_service.get_cache_status()
    except Exception as e:
        logger.error(f"❌ Erro ao obter status do cache: {str(e)}")
        logger.exception("Detalhes do erro:")
        raise HTTPException(status_code=500, detail=f"Erro ao obter status do cache: {str(e)}")
