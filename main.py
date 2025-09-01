import logging

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.modules.cycle_module import configure_cycle_module, get_cycle_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema de Análise de Ciclo",
    description="API para análise de dados de ciclo de produção com arquitetura em camadas",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar módulos
configure_cycle_module()

# Incluir routers
app.include_router(get_cycle_router())


@app.get("/")
async def root():
    """Endpoint raiz que serve a interface web"""
    try:
        return FileResponse("templates/index.html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Interface web não encontrada")


@app.get("/health")
async def health_check():
    """Endpoint de verificação de saúde da aplicação"""
    return {
        "status": "healthy",
        "message": "Sistema de Análise de Ciclo funcionando corretamente",
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções não tratadas"""
    logger.error(f"Erro não tratado: {exc}")
    
    # Capturar erros específicos do FastAPI
    if hasattr(exc, 'status_code'):
        status_code = exc.status_code
    else:
        status_code = 500
    
    # Capturar erros de validação do Pydantic
    if "validation error" in str(exc).lower() or "field required" in str(exc).lower():
        logger.error(f"Erro de validação Pydantic: {exc}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "Erro de validação dos dados",
                "detail": str(exc),
                "type": "validation_error"
            }
        )
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": "Erro interno do servidor",
            "detail": str(exc),
            "type": "internal_error"
        }
    )


if __name__ == "__main__":
    logger.info("🚀 Iniciando aplicação FastAPI...")
    logger.info("🌐 Servidor será executado em: http://127.0.0.1:8000")
    logger.info("📊 Documentação da API: http://127.0.0.1:8000/docs")
    logger.info("🏠 Interface web: http://127.0.0.1:8000")
    logger.info("🔧 Modo debug: Ativado")
    logger.info("⚡ Para parar o servidor: Ctrl+C")
    logger.info("=" * 60)
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("🛑 Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar servidor: {e}")
        logger.exception("Detalhes do erro:")
