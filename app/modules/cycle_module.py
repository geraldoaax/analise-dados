from typing import Optional

from fastapi import APIRouter

from app.controllers.cycle_controller import router as cycle_router
from app.repositories.cycle_repository import CycleRepository
from app.services.cycle_service import CycleService

# Instâncias singleton
_cycle_repository: Optional[CycleRepository] = None
_cycle_service: Optional[CycleService] = None


def get_cycle_repository() -> CycleRepository:
    """Retorna instância singleton do CycleRepository"""
    global _cycle_repository
    if _cycle_repository is None:
        _cycle_repository = CycleRepository()
    return _cycle_repository


def get_cycle_service() -> CycleService:
    """Retorna instância singleton do CycleService"""
    global _cycle_service
    if _cycle_service is None:
        repository = get_cycle_repository()
        _cycle_service = CycleService(repository)
    return _cycle_service


def get_cycle_router() -> APIRouter:
    """Retorna o router do módulo de ciclo"""
    return cycle_router


# Configuração do módulo
def configure_cycle_module():
    """Configura o módulo de ciclo"""
    # Inicializar dependências
    get_cycle_repository()
    get_cycle_service()
