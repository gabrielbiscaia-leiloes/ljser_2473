import logging
import time
import json
from typing import Dict, List, Optional
import httpx
from config import API_CONFIG, REQUEST_CONFIG, FILE_CONFIG
import pandas as pd
import re
import argparse
import sys
import io

# Configurar a codificação da saída
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('leiloes.log', encoding='utf-8', mode='w'),  # Modo 'w' para limpar o arquivo a cada execução
        logging.StreamHandler()
    ]
)

def validar_resposta(data: List[Dict]) -> bool:
    """
    Valida se a resposta da API está no formato esperado.
    """
    campos_obrigatorios = [
        "url_leiloeiro", "leilao_id", "nm_leilao", "dt_leilao", "tipo_leilao",
        "nm_leiloeiro", "lote_id", "nu_lote", "nm_lote", "descricao",
        "nm_descricao_vistoria", "nm_status", "vl_avaliacao", "vl_minimo",
        "nu_parcelas", "vl_comissao", "nu_comissao", "dt_lance",
        "nu_total_lance", "arrematacao", "tipo_arrematacao", "processo", "nm_osa"
    ]

    if not isinstance(data, list):
        logging.error("Resposta não é uma lista")
        return False

    for item in data:
        if not isinstance(item, dict):
            logging.error(f"Item não é um dicionário: {type(item)}")
            return False
            
        # Verifica se todos os campos obrigatórios estão presentes
        campos_faltando = [campo for campo in campos_obrigatorios if campo not in item]
        if campos_faltando:
            logging.error(f"Campos obrigatórios faltando: {campos_faltando}")
            return False

    return True

def fazer_requisicao(leilao_id: str) -> Optional[List[Dict]]:
    """
    Faz a requisição para a API de leilões com sistema de retry.
    """
    print("="*50)
    print(f"Iniciando requisição para o leilão {leilao_id}")
    print("="*50)
    
    # Primeiro busca os vendidos
    form_data_vendidos = {
        "url_leiloeiro": "www.giordanoleiloes.com.br",
        "leilao_id": str(leilao_id),
        "nm_vendidos": "S"  # S para vendidos
    }
    
    # Depois busca os não vendidos
    form_data_nao_vendidos = {
        "url_leiloeiro": "www.giordanoleiloes.com.br",
        "leilao_id": str(leilao_id),
        "nm_vendidos": "N"  # N para não vendidos
    }
    
    todos_lotes = []
    
    try:
        # Busca lotes vendidos
        print("\nBuscando lotes vendidos...")
        print(f"Form data: {json.dumps(form_data_vendidos, indent=2)}")
        
        response_vendidos = httpx.post(
            API_CONFIG["url"],
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
        
        # Busca lotes não vendidos
        print("\nBuscando lotes não vendidos...")
        print(f"Form data: {json.dumps(form_data_nao_vendidos, indent=2)}")
        
        response_nao_vendidos = httpx.post(
            API_CONFIG["url"],
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
        
        # Mostra detalhes de todos os lotes
        if todos_lotes:
            print(f"\nTotal de lotes encontrados: {len(todos_lotes)}")
            print("\nDetalhes dos lotes:")
            for lote in todos_lotes:
                print(f"\nLote {lote.get('nu_lote', 'N/A')}:")
                print(f"- Status: {lote.get('nm_status', 'N/A')}")
                print(f"- OSA: {lote.get('nm_osa', 'N/A')}")
                print(f"- Valor Avaliação: R$ {float(lote.get('vl_avaliacao', 0)):,.2f}")
                print(f"- Valor Mínimo: R$ {float(lote.get('vl_minimo', 0)):,.2f}")
                if isinstance(lote.get('arrematacao'), dict):
                    print(f"- Valor Arrematado: R$ {float(lote['arrematacao'].get('vl', 0)):,.2f}")
            return todos_lotes
        else:
            print("\nNenhum lote encontrado!")
            
    except Exception as e:
        print("\nErro ao fazer requisição:")
        print(str(e))
    
    return None

def processar_lote(item: Dict) -> Dict:
    """
    Processa um lote individual e retorna um dicionário com os dados formatados.
    """
    def format_money(value: float) -> str:
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    valor_avaliado = float(item.get("vl_avaliacao", 0))
    lance_inicial = float(item.get("vl_minimo", 0))
    valor_arrematado = float(item.get("arrematacao", {}).get("vl", 0))

    # Calcular Percentual de Evolução (%)
    percentual_evolucao = 0
    if lance_inicial > 0 and valor_arrematado > 0:
        percentual_evolucao = ((valor_arrematado - lance_inicial) / lance_inicial) * 100

    # Determinar o status do lote
    status = item.get("nm_status", "").strip().upper()
    is_vendido = status == "VENDIDO"

    # Log dos dados do lote sendo processado
    logging.info(f"Processando lote {item.get('nu_lote')}:")
    logging.info(f"  - OSA: {item.get('nm_osa')}")
    logging.info(f"  - Status original: {item.get('nm_status')}")
    logging.info(f"  - Status normalizado: {status}")
    logging.info(f"  - Valor arrematado: {valor_arrematado}")
    logging.info(f"  - É vendido? {is_vendido}")

    return {
        "N° Lote": item.get("nu_lote"),
        "OSA": item.get("nm_osa"),  
        "Status": status,
        "Descrição do bem": re.sub(r"<.*?>", "", item.get("nm_descricao_vistoria", "")),
        "Valor avaliado": format_money(valor_avaliado),
        "Lance inicial": format_money(lance_inicial),
        "Valor arrematado": format_money(valor_arrematado),
        "Percentual de evolução (%)": f"{round(percentual_evolucao, 2)}%",
        "is_vendido": is_vendido  
    }

def gerar_relatorio(data: List[Dict]) -> bool:
    """
    Gera o relatório Excel com os dados dos lotes.
    Retorna True se o relatório foi gerado com sucesso.
    """
    try:
        logging.info("Iniciando processamento dos lotes...")
        lotes = []
        total_arrematados = 0
        total_nao_arrematados = 0

        # Processamento dos lotes
        for item in data:
            lote_processado = processar_lote(item)
            lotes.append(lote_processado)
            
            # Contagem baseada no campo is_vendido
            is_vendido = lote_processado["is_vendido"]
            logging.info(f"Analisando status do lote {item.get('nu_lote')}:")
            logging.info(f"  - Status: {lote_processado['Status']}")
            logging.info(f"  - É vendido? {is_vendido}")
            
            if is_vendido:
                total_arrematados += 1
                logging.info("  → Contabilizado como arrematado")
            else:
                total_nao_arrematados += 1
                logging.info("  → Contabilizado como não arrematado")

        logging.info("=== RESUMO DA CONTAGEM ===")
        logging.info(f"Total de lotes processados: {len(lotes)}")
        logging.info(f"Lotes arrematados: {total_arrematados}")
        logging.info(f"Lotes não arrematados: {total_nao_arrematados}")

        # Remover campo auxiliar antes de salvar
        for lote in lotes:
            del lote["is_vendido"]

        # Criar DataFrames
        df_lotes = pd.DataFrame(lotes)

        # Calcular valores para o quadro resumo
        total_lotes = len(lotes)
        perc_arrematados = (total_arrematados / total_lotes * 100) if total_lotes > 0 else 0
        perc_nao_arrematados = (total_nao_arrematados / total_lotes * 100) if total_lotes > 0 else 0
        
        # Calcular valor total arrematado
        valor_total_arrematado = sum(
            float(re.sub(r'[^\d,]', '', lote['Valor arrematado']).replace(',', '.'))
            for lote in lotes
            if lote['Status'] == 'VENDIDO'
        )

        df_resumo = pd.DataFrame({
            "QUADRO RESUMO": [
                "TOTAL DE LOTES",
                "TOTAL DE LOTES ARREMATADOS",
                "PERCENTUAL DE LOTES ARREMATADOS",
                "TOTAL DE LOTES NÃO ARREMATADOS",
                "PERCENTUAL DE LOTES NÃO ARREMATADOS",
                "VALOR TOTAL ARREMATADO"
            ],
            "Quantidade": [
                total_lotes,
                total_arrematados,
                f"{perc_arrematados:.2f}%",
                total_nao_arrematados,
                f"{perc_nao_arrematados:.2f}%",
                f"R$ {valor_total_arrematado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            ]
        })

        # Tentar salvar no Excel
        try:
            logging.info(f"Salvando relatório em {FILE_CONFIG['output_file']}...")
            with pd.ExcelWriter(FILE_CONFIG["output_file"], engine="openpyxl") as writer:
                df_lotes.to_excel(writer, sheet_name=FILE_CONFIG["sheets"]["lotes"], index=False)
                df_resumo.to_excel(writer, sheet_name=FILE_CONFIG["sheets"]["resumo"], index=False)
            logging.info("Arquivo Excel salvo com sucesso")
        except PermissionError:
            logging.error(f"Erro: O arquivo {FILE_CONFIG['output_file']} está aberto. Feche-o e tente novamente.")
            return False
        except Exception as e:
            logging.error(f"Erro ao salvar arquivo: {e}")
            return False

        logging.info(f"Relatório gerado com sucesso: {FILE_CONFIG['output_file']}")
        return True

    except Exception as e:
        logging.error(f"Erro ao gerar relatório: {e}")
        return False

def main(leilao_id: str):
    """
    Função principal que coordena o processo de coleta e geração do relatório.
    """
    logging.info(f"Iniciando busca de dados para o leilão {leilao_id}")
    
    # Busca os dados
    data = fazer_requisicao(leilao_id)
    if not data:
        logging.error("Não foi possível obter os dados do leilão")
        return

    # Valida o formato da resposta
    if not isinstance(data, list):
        logging.error("Erro: Resposta inesperada da API. Estrutura incorreta.")
        return

    # Gera o relatório
    if not gerar_relatorio(data):
        logging.error("Falha ao gerar relatório.")
        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerador de relatório de leilões")
    parser.add_argument("leilao_id", help="ID do leilão para buscar os lotes")
    args = parser.parse_args()
    
    main(args.leilao_id)
