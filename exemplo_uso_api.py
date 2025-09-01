#!/usr/bin/env python3
"""
Exemplo de uso da API refatorada do Sistema de Análise de Ciclo

Este script demonstra como usar a nova API FastAPI com arquitetura em camadas.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

import requests


class CycleAnalysisClient:
    """Cliente para interagir com a API de Análise de Ciclo"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Faz uma requisição para a API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, params=params)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {e}")
            return {"error": str(e)}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Verifica o status de saúde da API"""
        return self._make_request("GET", "/health")
    
    def get_cycles_by_year_month(self, 
                                data_inicio: str = None, 
                                data_fim: str = None,
                                tipos_input: List[str] = None,
                                frota_transporte: List[str] = None) -> Dict[str, Any]:
        """Obtém ciclos por ano/mês"""
        params = {}
        
        if data_inicio:
            params['data_inicio'] = data_inicio
        if data_fim:
            params['data_fim'] = data_fim
        if tipos_input:
            params['tipos_input'] = ','.join(tipos_input)
        if frota_transporte:
            params['frota_transporte'] = ','.join(frota_transporte)
        
        return self._make_request("GET", "/api/cycles_by_year_month", params)
    
    def get_cycles_by_type_input(self,
                                data_inicio: str = None,
                                data_fim: str = None,
                                tipos_input: List[str] = None,
                                frota_transporte: List[str] = None) -> Dict[str, Any]:
        """Obtém ciclos por tipo de input"""
        params = {}
        
        if data_inicio:
            params['data_inicio'] = data_inicio
        if data_fim:
            params['data_fim'] = data_fim
        if tipos_input:
            params['tipos_input'] = ','.join(tipos_input)
        if frota_transporte:
            params['frota_transporte'] = ','.join(frota_transporte)
        
        return self._make_request("GET", "/api/cycles_by_type_input", params)
    
    def get_production_by_activity_type(self,
                                       data_inicio: str = None,
                                       data_fim: str = None,
                                       tipos_input: List[str] = None,
                                       frota_transporte: List[str] = None) -> Dict[str, Any]:
        """Obtém produção por tipo de atividade"""
        params = {}
        
        if data_inicio:
            params['data_inicio'] = data_inicio
        if data_fim:
            params['data_fim'] = data_fim
        if tipos_input:
            params['tipos_input'] = ','.join(tipos_input)
        if frota_transporte:
            params['frota_transporte'] = ','.join(frota_transporte)
        
        return self._make_request("GET", "/api/production_by_activity_type", params)
    
    def get_productivity_analysis(self,
                                 data_inicio: str = None,
                                 data_fim: str = None,
                                 tipos_input: List[str] = None,
                                 frota_transporte: List[str] = None) -> Dict[str, Any]:
        """Obtém análise de produtividade"""
        params = {}
        
        if data_inicio:
            params['data_inicio'] = data_inicio
        if data_fim:
            params['data_fim'] = data_fim
        if tipos_input:
            params['tipos_input'] = ','.join(tipos_input)
        if frota_transporte:
            params['frota_transporte'] = ','.join(frota_transporte)
        
        return self._make_request("GET", "/api/productivity_analysis", params)
    
    def get_productivity_by_equipment(self,
                                     data_inicio: str = None,
                                     data_fim: str = None,
                                     frota_transporte: List[str] = None) -> Dict[str, Any]:
        """Obtém produtividade por equipamento"""
        params = {}
        
        if data_inicio:
            params['data_inicio'] = data_inicio
        if data_fim:
            params['data_fim'] = data_fim
        if frota_transporte:
            params['frota_transporte'] = ','.join(frota_transporte)
        
        return self._make_request("GET", "/api/productivity_by_equipment", params)
    
    def clear_cache(self) -> Dict[str, Any]:
        """Limpa o cache"""
        return self._make_request("POST", "/api/clear_cache")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Obtém status do cache"""
        return self._make_request("GET", "/api/cache_status")


def print_section(title: str):
    """Imprime uma seção formatada"""
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")


def print_json(data: Dict[str, Any], title: str = "Resposta"):
    """Imprime dados JSON formatados"""
    print(f"\n🔍 {title}:")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    """Função principal que demonstra o uso da API"""
    print("🚀 Exemplo de Uso da API de Análise de Ciclo")
    print("📅 Data/Hora:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Criar cliente
    client = CycleAnalysisClient()
    
    # 1. Verificar status da API
    print_section("Verificação de Status")
    health = client.get_health_status()
    print_json(health, "Status da API")
    
    # 2. Verificar status do cache
    print_section("Status do Cache")
    cache_status = client.get_cache_status()
    print_json(cache_status, "Status do Cache")
    
    # 3. Exemplo: Ciclos por ano/mês
    print_section("Ciclos por Ano/Mês")
    cycles_data = client.get_cycles_by_year_month(
        data_inicio="2024-01-01",
        data_fim="2024-12-31"
    )
    print_json(cycles_data, "Ciclos por Ano/Mês")
    
    # 4. Exemplo: Ciclos por tipo de input
    print_section("Ciclos por Tipo de Input")
    cycles_by_type = client.get_cycles_by_type_input(
        data_inicio="2024-01-01",
        data_fim="2024-12-31",
        tipos_input=["Minério", "Estéril"]
    )
    print_json(cycles_by_type, "Ciclos por Tipo de Input")
    
    # 5. Exemplo: Produção por tipo de atividade
    print_section("Produção por Tipo de Atividade")
    production_data = client.get_production_by_activity_type(
        data_inicio="2024-01-01",
        data_fim="2024-12-31"
    )
    print_json(production_data, "Produção por Tipo de Atividade")
    
    # 6. Exemplo: Análise de produtividade
    print_section("Análise de Produtividade")
    productivity_data = client.get_productivity_analysis(
        data_inicio="2024-01-01",
        data_fim="2024-12-31"
    )
    print_json(productivity_data, "Análise de Produtividade")
    
    # 7. Exemplo: Produtividade por equipamento
    print_section("Produtividade por Equipamento")
    equipment_data = client.get_productivity_by_equipment(
        data_inicio="2024-01-01",
        data_fim="2024-01-31"
    )
    print_json(equipment_data, "Produtividade por Equipamento")
    
    # 8. Exemplo: Limpar cache
    print_section("Limpeza do Cache")
    cache_clear = client.clear_cache()
    print_json(cache_clear, "Resultado da Limpeza do Cache")
    
    print_section("Demonstração Concluída")
    print("✅ Todos os exemplos foram executados com sucesso!")
    print("🌐 Acesse http://127.0.0.1:8000/docs para ver a documentação interativa")


if __name__ == "__main__":
    main()
