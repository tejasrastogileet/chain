from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Optional
from pathlib import Path

# Import from the same directory
# from .blockchain_core import Blockchain, Node
from blockchain_core import Blockchain, Node


app = FastAPI(title="Mini Blockchain Demo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # allow ALL origins
    allow_credentials=True,
    allow_methods=["*"],        # allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],        # allow all headers
)

# Get the frontend directory path
# BASE_DIR = Path(__file__).resolve().parent.parent
# FRONTEND_DIR = BASE_DIR / "frontend"

# # Mount static files
# app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# Single main blockchain for simple demos
blockchain = Blockchain()

# Simple in-memory node registry
nodes: Dict[str, Node] = {}


# ---------- Pydantic models for request bodies ----------

class MineRequest(BaseModel):
    miner_address: str
    difficulty: int = 2


class AddDataBlockRequest(BaseModel):
    data: str
    difficulty: int = 2


class TamperRequest(BaseModel):
    index: int
    new_data: str


class AttackRequest(BaseModel):
    start_index: int = 1


class NodeCreateRequest(BaseModel):
    name: str


class NodeMineRequest(BaseModel):
    node_name: str
    miner_address: str
    difficulty: int = 2


class NodeSyncRequest(BaseModel):
    target_node: str
    from_node: str


# ---------- Basic blockchain endpoints ----------

@app.get("/chain")
def get_chain():
    is_valid, error = blockchain.validate_chain()
    return {
        "valid": is_valid,
        "error": error,
        "length": len(blockchain.chain),
        "chain": blockchain.to_list(),
    }


@app.post("/mine-reward")
def mine_reward(req: MineRequest):
    block = blockchain.mine_reward_block(req.miner_address, req.difficulty)
    is_valid, error = blockchain.validate_chain()
    return {
        "message": "Block mined with reward",
        "block": block.to_dict(),
        "valid": is_valid,
        "error": error,
        "rewards": blockchain.get_rewards(),
    }


@app.post("/add-block")
def add_data_block(req: AddDataBlockRequest):
    block = blockchain.add_data_block(req.data, req.difficulty)
    is_valid, error = blockchain.validate_chain()
    return {
        "message": "Data block added",
        "block": block.to_dict(),
        "valid": is_valid,
        "error": error,
    }


@app.get("/validate")
def validate():
    is_valid, error = blockchain.validate_chain()
    return {"valid": is_valid, "error": error}


@app.post("/tamper")
def tamper(req: TamperRequest):
    success = blockchain.tamper_block(req.index, req.new_data)
    is_valid, error = blockchain.validate_chain()
    return {
        "tampered": success,
        "valid_after_tamper": is_valid,
        "error": error,
        "chain": blockchain.to_list(),
    }


@app.post("/attack-51")
def attack_51(req: AttackRequest):
    blockchain.simulate_51_attack(req.start_index)
    is_valid, error = blockchain.validate_chain()
    return {
        "message": "51% attack simulated (hashes recomputed)",
        "valid_after_attack": is_valid,
        "error": error,
        "chain": blockchain.to_list(),
    }


@app.get("/rewards")
def get_rewards():
    return {"rewards": blockchain.get_rewards()}


@app.post("/reset")
def reset_chain():
    blockchain.reset()
    return {"message": "Blockchain reset to genesis block", "chain": blockchain.to_list()}


# ---------- Node / P2P endpoints ----------

@app.post("/nodes")
def create_node(req: NodeCreateRequest):
    if req.name in nodes:
        return {"message": "Node already exists", "node": nodes[req.name].to_dict()}

    node = Node(req.name)
    nodes[req.name] = node
    return {"message": "Node created", "node": node.to_dict()}


@app.get("/nodes")
def list_nodes():
    return {name: node.to_dict() for name, node in nodes.items()}


@app.post("/nodes/mine")
def node_mine(req: NodeMineRequest):
    node = nodes.get(req.node_name)
    if not node:
        return {"error": f"Node '{req.node_name}' not found"}

    block = node.blockchain.mine_reward_block(req.miner_address, req.difficulty)
    is_valid, error = node.blockchain.validate_chain()
    return {
        "message": f"Node {req.node_name} mined a reward block",
        "block": block.to_dict(),
        "node": node.to_dict(),
        "valid": is_valid,
        "error": error,
    }


@app.post("/nodes/sync")
def node_sync(req: NodeSyncRequest):
    target = nodes.get(req.target_node)
    from_node = nodes.get(req.from_node)

    if not target or not from_node:
        return {"error": "One or both nodes not found"}

    changed = target.sync_with(from_node)
    return {
        "synced": changed,
        "target_node": target.to_dict(),
        "from_node": from_node.to_dict(),
    }


# ---------- Frontend routes ----------

# @app.get("/")
# def read_root():
#     """Serve the homepage"""
#     return FileResponse(str(FRONTEND_DIR / "index.html"))


# @app.get("/about")
# def read_about():
#     """Serve the about page"""
#     return FileResponse(str(FRONTEND_DIR / "about.html"))


# @app.get("/visualizer")
# def read_visualizer():
#     """Serve the visualizer page"""
#     return FileResponse(str(FRONTEND_DIR / "visualizer.html"))
