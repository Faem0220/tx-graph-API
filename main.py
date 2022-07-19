from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import txs_graph

app = FastAPI()
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/{account}/{token}")
async def root(account: str, token: str):
    try:
        graph_json = txs_graph.graph_from_address(account,token)
    except:
        graph_json = [] 
    return graph_json