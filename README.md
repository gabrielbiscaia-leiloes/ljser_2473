# Sistema de Relatório de Leilões

Este sistema foi desenvolvido para gerar relatórios detalhados de leilões, obtendo dados através da API da Giordano Leilões.

## Funcionalidades

- Busca de lotes vendidos e não vendidos
- Geração de relatório em Excel e Word
- Cálculo de estatísticas (total arrematado, menor/maior valor)
- Suporte a ambientes de produção e teste

## Estrutura do Projeto

```
ljser_2473/
├── main.py           # Script principal (produção)
├── main_word.py      # Gerador de relatório Word (produção)
├── last_teste.py     # Script de teste (homologação)
├── last_teste_word.py # Gerador de relatório Word (homologação)
├── config.py         # Configurações de produção
└── config2.py        # Configurações de teste
```

## Requisitos

- Python 3.6+
- Bibliotecas: httpx, pandas, openpyxl, python-docx

## Como Usar

### Ambiente de Produção

```bash
python main.py <id_leilao>      # Relatório Excel
python main_word.py <id_leilao> # Relatório Word
```

### Ambiente de Teste

```bash
python last_teste.py <id_leilao>      # Relatório Excel
python last_teste_word.py <id_leilao> # Relatório Word
```

Exemplo:
```bash
python last_teste_word.py 15324
```

## Formato da Saída

O script gera:

1. Log detalhado dos lotes:
   - Número do lote
   - Status (Vendido/Não Vendido)
   - OSA
   - Valor de avaliação
   - Valor mínimo
   - Valor arrematado (se vendido)

2. Resumo do leilão:
   - Total de lotes
   - Quantidade de lotes vendidos/não vendidos
   - Valor total arrematado
   - Menor e maior valor arrematado

3. Arquivo Excel com todos os dados

## Formato dos Relatórios

### Relatório Word

O relatório em Word inclui:

1. Cabeçalho com nome do leilão
2. Título formatado: "[Nome do Leilão] - RELATÓRIO DE VENDAS DE LEILÃO"
3. Tabela detalhada com as colunas:
   - OSA
   - Nº Lote
   - Tipo de Alienação
   - Descrição
   - Descrição da Vistoria
   - Status
   - Usuário
   - Estado
   - CPF/CNPJ
   - Valor avaliado
   - Lance inicial
   - Valor arrematado
   - Percentual de evolução (%)

## APIs

### Produção
- URL: https://www.giordanoleiloes.com.br/leilao/buscar-lotes

### Teste
- URL: https://teste.giordanoleiloes.com.br/leilao/buscar-lotes

### Parâmetros da API

- `url_leiloeiro`: Domínio do leiloeiro
- `leilao_id`: ID do leilão
- `nm_vendidos`: Status dos lotes a buscar
  - "S": Vendidos
  - "N": Não vendidos

## Exemplos de Resposta

### Lote Vendido
```json
{
    "nu_lote": "2",
    "nm_status": "Vendido",
    "nm_osa": "0001/2025",
    "vl_avaliacao": "200000.00",
    "vl_minimo": "175000.00",
    "arrematacao": {
        "vl": "179000.00"
    }
}
```

### Lote Não Vendido
```json
{
    "nu_lote": "1",
    "nm_status": "Não Vendido",
    "nm_osa": "2005/2025",
    "vl_avaliacao": "100000.00",
    "vl_minimo": "75000.00"
}
```

## Tratamento de Erros

O sistema inclui tratamento para:
- Timeout na conexão
- Erros de resposta da API
- Dados inválidos ou ausentes
- Problemas de parsing JSON
