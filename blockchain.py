import hashlib
import time


# --------------------------
# BLOCK CLASS
# --------------------------
class Block:
    def __init__(self, index, data, previous_hash, difficulty=2):
        self.index = index
        self.timestamp = time.time()
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.mine_block(difficulty)

    def compute_hash(self):
        block_string = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty):
        prefix = "0" * difficulty
        while True:
            new_hash = self.compute_hash()
            if new_hash.startswith(prefix):
                return new_hash
            self.nonce += 1


# --------------------------
# BLOCKCHAIN CLASS
# --------------------------
class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.mining_reward = 50
        self.pending_rewards = {}

    def create_genesis_block(self):
        return Block(0, "Genesis Block", "0")

    def add_block(self, data, difficulty=2):
        last_block = self.chain[-1]
        new_block = Block(len(self.chain), data, last_block.hash, difficulty)
        self.chain.append(new_block)
        return new_block

    # Mining a block + reward system
    def mine_block(self, miner_address, difficulty=2):
        reward_data = f"Reward to {miner_address}: {self.mining_reward} coins"
        new_block = Block(len(self.chain), reward_data, self.chain[-1].hash, difficulty)
        self.chain.append(new_block)

        self.pending_rewards[miner_address] = \
            self.pending_rewards.get(miner_address, 0) + self.mining_reward

        return new_block

    # Validation
    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            # Check stored hash vs recomputed hash
            if current.hash != current.compute_hash():
                print(f"❌ Invalid hash at block {i}")
                return False

            # Check chain linkage
            if current.previous_hash != previous.hash:
                print(f"❌ Chain broken between block {i} and block {i-1}")
                return False

        return True

    # Helper to print chain
    def print_chain(self):
        for block in self.chain:
            print("----------------------------")
            print(f"Index: {block.index}")
            print(f"Timestamp: {block.timestamp}")
            print(f"Data: {block.data}")
            print(f"Previous Hash: {block.previous_hash}")
            print(f"Hash: {block.hash}")
            print(f"Nonce: {block.nonce}")
            print("----------------------------")

    # Reward printer
    def print_rewards(self):
        print("\n=== Miner Balances ===")
        for miner, balance in self.pending_rewards.items():
            print(f"{miner}: {balance} coins")



# --------------------------
# NODE CLASS (P2P Sync)
# --------------------------
class Node:
    def __init__(self, name):
        self.name = name
        self.blockchain = Blockchain()

    def sync_with(self, other_node):
        if len(self.blockchain.chain) < len(other_node.blockchain.chain):
            self.blockchain.chain = other_node.blockchain.chain
            print(f"{self.name} synced with {other_node.name}")
        else:
            print(f"{self.name} already has the longest chain")
