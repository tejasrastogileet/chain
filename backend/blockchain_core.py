import hashlib
import time
from typing import List, Dict, Tuple, Optional, Any


class Block:
    """
    Represents a single block in the blockchain.
    """

    def __init__(
        self,
        index: int,
        data: str,
        previous_hash: str,
        difficulty: int = 2,
        timestamp: Optional[float] = None,
        mine_immediately: bool = True,
    ):
        self.index = index
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        # This will be filled in either by mine() or by a direct compute (for tampering)
        self.hash = ""

        if mine_immediately:
            self.mine(difficulty)

    def compute_hash(self) -> str:
        """
        Compute SHA-256 hash of the block's contents.
        """
        block_string = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine(self, difficulty: int) -> str:
        """
        Proof-of-Work: find a hash that starts with 'difficulty' leading zeroes.
        """
        prefix = "0" * difficulty
        while True:
            candidate = self.compute_hash()
            if candidate.startswith(prefix):
                self.hash = candidate
                return self.hash
            self.nonce += 1

    def to_dict(self) -> Dict[str, Any]:
        """
        Represent block as a JSON-serializable dict (for UI / APIs).
        """
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
            "nonce": self.nonce,
        }


class Blockchain:
    """
    Represents the blockchain (a list of linked blocks).
    Includes PoW, validation, rewards, and helper methods for demos.
    """

    def __init__(self):
        self.chain: List[Block] = [self._create_genesis_block()]
        self.mining_reward: int = 50
        self.pending_rewards: Dict[str, int] = {}

    # ---------- BASIC STRUCTURE ----------

    def _create_genesis_block(self) -> Block:
        """
        Creates the genesis (first) block.
        """
        return Block(
            index=0,
            data="Genesis Block",
            previous_hash="0",
            difficulty=2,
        )

    def get_last_block(self) -> Block:
        return self.chain[-1]

    # ---------- NORMAL BLOCK / REWARD BLOCK ----------

    def add_data_block(self, data: str, difficulty: int = 2) -> Block:
        """
        Add a normal block with arbitrary data (no reward).
        """
        last_block = self.get_last_block()
        new_block = Block(
            index=len(self.chain),
            data=data,
            previous_hash=last_block.hash,
            difficulty=difficulty,
        )
        self.chain.append(new_block)
        return new_block

    def mine_reward_block(self, miner_address: str, difficulty: int = 2) -> Block:
        """
        Mine a block that includes a mining reward for the given miner.
        """
        reward_data = f"Reward to {miner_address}: {self.mining_reward} coins"
        last_block = self.get_last_block()
        new_block = Block(
            index=len(self.chain),
            data=reward_data,
            previous_hash=last_block.hash,
            difficulty=difficulty,
        )
        self.chain.append(new_block)

        # Track miner rewards
        self.pending_rewards[miner_address] = (
            self.pending_rewards.get(miner_address, 0) + self.mining_reward
        )
        return new_block

    # ---------- VALIDATION & INTEGRITY ----------

    def validate_chain(self) -> Tuple[bool, Optional[str]]:
        """
        Validate the entire chain.
        Returns (is_valid, error_message_if_any)
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Check hash integrity
            if current.hash != current.compute_hash():
                return False, f"Invalid hash at block index {i}"

            # Check previous hash linkage
            if current.previous_hash != previous.hash:
                return False, f"Broken chain between block {i - 1} and {i}"

        return True, None

    # ---------- TAMPERING & 51% ATTACK DEMOS ----------

    def tamper_block(self, index: int, new_data: str) -> bool:
        """
        Directly modify data of a given block and recompute its hash WITHOUT PoW.
        (Just for demo/testing.)
        Returns True if tampering was applied, False if index is invalid or genesis.
        """
        if index <= 0 or index >= len(self.chain):
            # Do not tamper with genesis or out of range
            return False

        block = self.chain[index]
        block.data = new_data
        # Recompute hash without PoW difficulty constraint (attacker cheating).
        block.hash = block.compute_hash()
        return True

    def simulate_51_attack(self, start_index: int = 1) -> None:
        """
        Simulate a 51% attack:
        - After tampering one block, recompute hashes of all subsequent blocks
          to "cover up" the attack and make the chain look consistent again.
        """
        if start_index <= 0:
            start_index = 1  # never re-generate genesis from here

        for i in range(start_index, len(self.chain)):
            previous_block = self.chain[i - 1]
            current_block = self.chain[i]
            current_block.previous_hash = previous_block.hash
            # Attacker just recomputes hash (could run their own PoW off-chain)
            current_block.hash = current_block.compute_hash()

    # ---------- VIEWS / HELPERS FOR UI ----------

    def to_list(self) -> List[Dict[str, Any]]:
        """
        Return entire chain as list of dicts.
        """
        return [block.to_dict() for block in self.chain]

    def get_rewards(self) -> Dict[str, int]:
        return dict(self.pending_rewards)

    def reset(self) -> None:
        """
        Reset blockchain to just the genesis block and clear rewards.
        """
        self.chain = [self._create_genesis_block()]
        self.pending_rewards.clear()


class Node:
    """
    Represents a node in a simple P2P network.
    Each node has its own Blockchain instance.
    """

    def __init__(self, name: str):
        self.name = name
        self.blockchain = Blockchain()

    def sync_with(self, other_node: "Node") -> bool:
        """
        Sync this node's blockchain with another node
        by adopting the longer valid chain.
        Returns True if sync happened, False otherwise.
        """
        my_chain_len = len(self.blockchain.chain)
        other_chain_len = len(other_node.blockchain.chain)

        # Only sync if the other chain is strictly longer and valid.
        is_valid, _ = other_node.blockchain.validate_chain()
        if other_chain_len > my_chain_len and is_valid:
            self.blockchain.chain = [
                Block(
                    index=b.index,
                    data=b.data,
                    previous_hash=b.previous_hash,
                    difficulty=2,
                    timestamp=b.timestamp,
                    mine_immediately=False,
                )
                for b in other_node.blockchain.chain
            ]
            # Copy hashes & nonces over
            for i, b in enumerate(other_node.blockchain.chain):
                self.blockchain.chain[i].nonce = b.nonce
                self.blockchain.chain[i].hash = b.hash
            return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "chain_length": len(self.blockchain.chain),
            "chain": self.blockchain.to_list(),
            "rewards": self.blockchain.get_rewards(),
        }
