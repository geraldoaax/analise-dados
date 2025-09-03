import os

import pandas as pd


def verificar_colunas_excel():
    """Verifica as colunas disponíveis nos arquivos Excel"""
    
    # Caminho para os arquivos
    excel_dir = "CicloDetalhado"
    
    if not os.path.exists(excel_dir):
        print(f"❌ Diretório {excel_dir} não encontrado")
        return
    
    excel_files = [f for f in os.listdir(excel_dir) if f.endswith('.xlsx')]
    
    if not excel_files:
        print(f"❌ Nenhum arquivo Excel encontrado em {excel_dir}")
        return
    
    print(f"🔍 Verificando {len(excel_files)} arquivo(s) Excel...")
    
    for filename in excel_files:
        filepath = os.path.join(excel_dir, filename)
        print(f"\n📁 Arquivo: {filename}")
        
        try:
            # Ler apenas as primeiras linhas para verificar colunas
            df = pd.read_excel(filepath, nrows=5)
            
            print(f"   📊 Colunas disponíveis ({len(df.columns)}):")
            for i, col in enumerate(df.columns):
                print(f"      {i+1:2d}. {col}")
            
            # Verificar se existe coluna "Frota carga" real
            if 'Frota carga' in df.columns:
                print(f"   ✅ Coluna 'Frota carga' encontrada!")
                # Mostrar alguns valores únicos
                valores_unicos = df['Frota carga'].dropna().unique()[:10]
                print(f"   📋 Valores únicos (primeiros 10): {valores_unicos}")
            else:
                print(f"   ❌ Coluna 'Frota carga' NÃO encontrada")
            
            # Verificar se existe coluna "Tag carga"
            if 'Tag carga' in df.columns:
                print(f"   ✅ Coluna 'Tag carga' encontrada!")
                # Mostrar alguns valores únicos
                valores_unicos = df['Tag carga'].dropna().unique()[:10]
                print(f"   📋 Valores únicos (primeiros 10): {valores_unicos}")
            else:
                print(f"   ❌ Coluna 'Tag carga' NÃO encontrada")
                
        except Exception as e:
            print(f"   ❌ Erro ao ler arquivo: {e}")

if __name__ == "__main__":
    verificar_colunas_excel() 