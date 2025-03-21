"""
Script para teste e homologação do sistema de relatórios de leilão.

Este script se conecta ao ambiente de teste da API de leilões para buscar informações
sobre lotes vendidos e não vendidos. Ele fornece um relatório detalhado incluindo:
- Status de cada lote
- Valores de avaliação, mínimo e arrematação
- Estatísticas do leilão (total arrematado, menor/maior valor)

Exemplo de uso:
    python last_teste.py 15324
"""

import httpx
import json
import logging
from typing import Dict, List, Optional
from config2 import API_CONFIG

logging.basicConfig(level=logging.INFO)

def fazer_requisicao(leilao_id: str) -> Optional[List[Dict]]:
    """
    Faz requisições para a API de leilões para buscar lotes vendidos e não vendidos.

    Args:
        leilao_id (str): ID do leilão a ser consultado

    Returns:
        Optional[List[Dict]]: Lista de lotes encontrados ou None em caso de erro.
        Cada lote contém as seguintes informações:
        - nu_lote: Número do lote
        - nm_status: Status (Vendido/Não Vendido)
        - nm_osa: Número do OSA
        - vl_avaliacao: Valor de avaliação
        - vl_minimo: Valor mínimo
        - arrematacao: Dicionário com valor arrematado (se vendido)

    Raises:
        Exception: Em caso de erro na requisição ou processamento dos dados
    """
    """
    Faz a requisição para a API de leilões com sistema de retry.
    """
    print("="*50)
    print(f"Iniciando requisição para o leilão {leilao_id}")
    print("="*50)
    
    # Primeiro busca os vendidos
    form_data_vendidos = {
        "url_leiloeiro": "teste.giordanoleiloes.com.br",
        "leilao_id": str(leilao_id),
        "nm_vendidos": "S"  # S para vendidos
    }
    
    # Depois busca os não vendidos
    form_data_nao_vendidos = {
        "url_leiloeiro": "teste.giordanoleiloes.com.br",
        "leilao_id": str(leilao_id),
        "nm_vendidos": "N"  # N para não vendidos
    }
    
    todos_lotes = []
    
    try:
        # Busca lotes vendidos
        print("\nBuscando lotes vendidos...")
        print(f"Form data: {json.dumps(form_data_vendidos, indent=2)}")
        
        response_vendidos = httpx.post(
            API_CONFIG["url_test"],
            data=form_data_vendidos,
            headers=API_CONFIG["headers"],
            verify=False,
            follow_redirects=True,
            timeout=30.0
        )
        
        if response_vendidos.status_code == 200:
            try:
                lotes_vendidos = response_vendidos.json()
                if isinstance(lotes_vendidos, list):
                    print(f"\nSucesso! Recebidos {len(lotes_vendidos)} lotes vendidos")
                    todos_lotes.extend(lotes_vendidos)
            except Exception as e:
                print(f"\nErro ao processar JSON dos lotes vendidos: {e}")
        else:
            print(f"\nErro na requisição de lotes vendidos: Status {response_vendidos.status_code}")
            print("Resposta do servidor:")
            print(response_vendidos.text[:200])
        
        # Busca lotes não vendidos
        print("\nBuscando lotes não vendidos...")
        print(f"Form data: {json.dumps(form_data_nao_vendidos, indent=2)}")
        
        response_nao_vendidos = httpx.post(
            API_CONFIG["url_test"],
            data=form_data_nao_vendidos,
            headers=API_CONFIG["headers"],
            verify=False,
            follow_redirects=True,
            timeout=30.0
        )
        
        if response_nao_vendidos.status_code == 200:
            try:
                lotes_nao_vendidos = response_nao_vendidos.json()
                if isinstance(lotes_nao_vendidos, list):
                    print(f"\nSucesso! Recebidos {len(lotes_nao_vendidos)} lotes não vendidos")
                    todos_lotes.extend(lotes_nao_vendidos)
            except Exception as e:
                print(f"\nErro ao processar JSON dos lotes não vendidos: {e}")
        else:
            print(f"\nErro na requisição de lotes não vendidos: Status {response_nao_vendidos.status_code}")
            print("Resposta do servidor:")
            print(response_nao_vendidos.text[:200])
        
        # Mostra detalhes de todos os lotes
        if todos_lotes:
            print(f"\nTotal de lotes encontrados: {len(todos_lotes)}")
            print("\nDetalhes dos lotes:")
            
            # Ordena os lotes por número
            todos_lotes.sort(key=lambda x: int(x.get('nu_lote', 0)))
            
            vendidos = []
            nao_vendidos = []
            
            for lote in todos_lotes:
                status = lote.get('nm_status', 'N/A')
                valor_arrematado = float(lote['arrematacao'].get('vl', 0)) if isinstance(lote.get('arrematacao'), dict) else 0
                
                info_lote = {
                    'numero': lote.get('nu_lote', 'N/A'),
                    'status': status,
                    'valor_avaliacao': float(lote.get('vl_avaliacao', 0)),
                    'valor_minimo': float(lote.get('vl_minimo', 0)),
                    'valor_arrematado': valor_arrematado
                }
                
                if status == 'Vendido':
                    vendidos.append(info_lote)
                else:
                    nao_vendidos.append(info_lote)
                
                print(f"\nLote {info_lote['numero']}:")
                print(f"- Status: {status}")
                print(f"- OSA: {lote.get('nm_osa', 'N/A')}")
                print(f"- Valor Avaliação: R$ {info_lote['valor_avaliacao']:,.2f}")
                print(f"- Valor Mínimo: R$ {info_lote['valor_minimo']:,.2f}")
                if valor_arrematado > 0:
                    print(f"- Valor Arrematado: R$ {valor_arrematado:,.2f}")
            
            # Resumo do leilão
            print("\n" + "="*50)
            print("RESUMO DO LEILÃO")
            print("="*50)
            print(f"Total de lotes: {len(todos_lotes)}")
            print(f"Lotes vendidos: {len(vendidos)}")
            print(f"Lotes não vendidos: {len(nao_vendidos)}")
            
            if vendidos:
                total_arrematado = sum(l['valor_arrematado'] for l in vendidos)
                print(f"\nValor total arrematado: R$ {total_arrematado:,.2f}")
                
                menor_valor = min(vendidos, key=lambda x: x['valor_arrematado'])
                maior_valor = max(vendidos, key=lambda x: x['valor_arrematado'])
                
                print(f"Menor valor arrematado: R$ {menor_valor['valor_arrematado']:,.2f} (Lote {menor_valor['numero']})")
                print(f"Maior valor arrematado: R$ {maior_valor['valor_arrematado']:,.2f} (Lote {maior_valor['numero']})")
            
            return todos_lotes
        else:
            print("\nNenhum lote encontrado!")
            
    except Exception as e:
        print("\nErro ao fazer requisição:")
        print(str(e))
    
    return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Uso: python last_teste.py <id_leilao>")
        print("\nExemplo:")
        print("  python last_teste.py 15324")
        sys.exit(1)
    
    leilao_id = sys.argv[1]
    fazer_requisicao(leilao_id)
