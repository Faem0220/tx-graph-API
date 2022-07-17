import requests
import pandas as pd

def generate_graph(account,token='eth'):
    '''Generate lists of node and edge for a graph from account'''
    api_endpoint = f""" https://api.etherscan.io/api?module=account&action=txlist&address={account}&startblock=0&endblock=99999999&page=1&offset=10&sort=desc&apikey=YourApiKeyToken"""
    if token == 'usdc':
        api_endpoint = f'https://api.etherscan.io/api?module=account&action=tokentx&contractaddress=0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48&address={account}&page=1&offset=100&startblock=0&endblock=99999999&sort=asc&apikey=YourApiKeyToken'
    response = requests.get(api_endpoint)
    # List of transactions to dataframe
    txs = response.json()['result']
    txs = pd.DataFrame(txs)
    # Format wei to eth
    token_decimal = 18
    if token == 'usdc':
        token_decimal = 6 
    txs['value'] = round(txs['value'].astype(float)* 10**-token_decimal,4) 

    # Children node of account 
    children = txs[txs['to'] != account.lower()]
    children = children[['to','value']]
    # Sum of eth value for each children account
    total_children = children.groupby(['to']).sum().reset_index()
    # Parent node of account
    parents = txs[txs['from'] != account.lower()]
    parents = parents[['from','value']]
    # Sum of eth value for each parent account
    total_parents = parents.groupby(['from']).sum().reset_index()
    
    # Format to cytoscape graph
    nodes = [
        {
            'data': {'id': account[:7], 'address': account }
        }
    ]
    edges = []
    adjacents = []
    for index,children in total_children.iterrows():
        if(children['value']!= 0) and children['to'] != "":
            node = {
                'data': {
                    'id': children['to'][:7],
                    'address': children['to']
                }
            }
            adjacents.append(children['to'])
            nodes.insert(0,node)
            edge ={
                'data': {
                    'id': f"{account[:7]}-{children['to'][:7]}",
                    'source': account[:7],
                    'target': children['to'][:7],
                    'weight': children['value']
                }
            }
            edges.append(edge)
    for index,parent in total_parents.iterrows():
        if(parent['value']!= 0 and parent['from'] != ""):
            node = {
                'data': {
                    'id': parent['from'][:7],
                    'address': parent['from']
                }
            }
            nodes.insert(0,node)
            adjacents.append(parent['from'])
            edge ={
                'data': {
                    'id': f"{parent['from'][:7]}-{account[:7]}",
                    'source': parent['from'][:7],
                    'target': account[:7],
                    'weight': parent['value']
                }
            }
            
            edges.append(edge)

    return nodes,edges,adjacents