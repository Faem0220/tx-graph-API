import time
import json
import requests
import pandas as pd


def graph_from_address(account, token):
    ''' Return array of nodes and edges of and account and adjacents '''
    nodes, edges, adjacents = generate_graph(account, token)
    for account in adjacents:
        time.sleep(5)
        print('Fetching account: ',account)
        node,edge,adj = generate_graph(account, token)
        nodes.extend(node)
        edges.extend(edge)
    # Remove duplicated nodes and edges
    nodes = list({ node["data"]['address'] : node for node in nodes }.values())
    edges = list({ edge["data"]['id'] : edge for edge in edges }.values())
    nodes.extend(edges)
    return nodes

def token_to_api_endpoint(account, token):
    tokens = dict(
        usdc = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        usdt = '0xdAC17F958D2ee523a2206206994597C13D831ec7',
        dai = '0x6B175474E89094C44Da98b954EedeAC495271d0F',
        busd = '0x4Fabb145d64652a948d72533023f6E7A623C7C53'
    )
    return f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={tokens[token]}&address={account}&page=1&offset=100&startblock=0&endblock=99999999&sort=asc&apikey=YourApiKeyToken"


def generate_graph(account,token='eth'):
    '''Generate lists of node and edge for a graph from account'''

    if token == 'eth':
        api_endpoint = f"https://api.etherscan.io/api?module=account&action=txlist&address={account}&startblock=0&endblock=99999999&page=1&offset=10&sort=desc&apikey=YourApiKeyToken"
    else:
        api_endpoint = token_to_api_endpoint(account, token)
    
    response = requests.get(api_endpoint)
    # List of transactions to dataframe
    txs = response.json()['result']
    txs = pd.DataFrame(txs)
    # Format wei to eth
    token_decimal = 18
    if token == 'usdc' or token == 'usdt':
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
    
    # Format to cytoscapejs
    nodes = [
        {
            'data': {'id': account[:7], 'address': account }
        }
    ]
    edges = []
    adjacents = []
    for index,children in total_children.iterrows():
        if children['value']!= 0 and children['to'] != "":
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
        if parent['value']!= 0 and parent['from'] != "":
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