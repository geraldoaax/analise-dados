import json
from datetime import datetime, timedelta

import requests


def testar_api_frota_carga():
    """Testa a API de produção por frota de carga"""
    
    # URL base da API
    base_url = "http://localhost:8000"
    
    # Calcular datas para o filtro (últimos 6 meses)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    # Parâmetros da requisição
    params = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }
    
    print(f"🧪 Testando API de produção por frota de carga...")
    print(f"📅 Período: {params['start_date']} até {params['end_date']}")
    print(f"🌐 URL: {base_url}/api/production_by_frota_carga")
    
    try:
        # Fazer requisição para a API
        response = requests.get(f"{base_url}/api/production_by_frota_carga", params=params)
        
        print(f"📡 Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dados recebidos com sucesso!")
            print(f"📊 Total de registros: {len(data)}")
            
            if len(data) > 0:
                print(f"\n🔍 Primeiros 3 registros:")
                for i, item in enumerate(data[:3]):
                    print(f"   Registro {i+1}:")
                    print(f"      ano_mes: {item.get('ano_mes')}")
                    print(f"      frota_carga: {item.get('frota_carga')}")
                    print(f"      massa_total: {item.get('massa_total')}")
                    print(f"      count: {item.get('count')}")
                
                # Verificar campos únicos
                frotas_carga = list(set(item.get('frota_carga') for item in data))
                periodos = list(set(item.get('ano_mes') for item in data))
                
                print(f"\n📋 Frotas de carga únicas ({len(frotas_carga)}):")
                for frota in sorted(frotas_carga):
                    print(f"   - {frota}")
                
                print(f"\n📅 Períodos únicos ({len(periodos)}):")
                for periodo in sorted(periodos):
                    print(f"   - {periodo}")
                
                # Verificar se há valores nulos ou vazios
                frotas_nulas = [item for item in data if not item.get('frota_carga')]
                if frotas_nulas:
                    print(f"\n⚠️  Registros com frota_carga nula/vazia: {len(frotas_nulas)}")
                
            else:
                print("⚠️  Nenhum dado retornado")
                
        else:
            print(f"❌ Erro na API: {response.status_code}")
            print(f"📝 Resposta: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro de conexão: API não está rodando")
        print("💡 Certifique-se de que o servidor está rodando em http://localhost:8000")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    testar_api_frota_carga() 