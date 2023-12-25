import datetime
import hashlib
from multiprocessing import Process
import requests
import json

from uuid import uuid4
from urllib.parse import urlparse
from flask import Flask, request

from moeda.criptomoeda import Transaction


class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.create_block(proof=1, prev_hash="0", data="Genesis Block")
        self.nodes = set()

    def add_transaction_to_pool(self, sender, receiver, amount):
        self.current_transactions.append(Transaction(sender, receiver, amount))

    def create_block(self, proof, prev_hash, data):
        block = Block(
            index=len(self.chain) + 1,
            proof=proof,
            prev_hash=prev_hash,
            timestamp=datetime.datetime.now(),
            data=data,
            transactions=self.current_transactions,
        )
        self.current_transactions = []
        self.chain.append(block)

        return block

    def get_prev_block(self):
        return self.chain[-1]

    def proof_of_work(self, prev_proof):
        new_proof = 1
        while not self.valid_proof(prev_proof, new_proof):
            new_proof += 1
        return new_proof

    @staticmethod
    def valid_proof(prev_proof, new_proof):
        guess = f"{new_proof**2 - prev_proof**2}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def is_chain_valid(self, chain):
        prev_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            # verificando se o prev_hash do bloco atual
            # é igual ao hash do bloco anterior
            if block.prev_hash != prev_block.hash:
                return False
            # verificando se o proof do bloco anterior
            # é igual ao proof do bloco atual
            prev_proof = prev_block.proof
            proof = block.proof
            hash_operation = hashlib.sha256(
                f"{proof**2 - prev_proof**2}".encode()
            ).hexdigest()
            if hash_operation[:4] != "0000":
                return False
            prev_block = block
            block_index += 1

        return True

    def add_node(self, address):
        self.nodes.add(urlparse(address).netloc)

    def get_longest_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)

        for node in network:
            request = requests.get(f"http://{node}/get_chain")
            if request.status_code == 200:
                length = request.json()["length"]
                chain = request.json()["chain"]
                if length > max_length:
                    max_length = length
                    longest_chain = chain

        return longest_chain

    def replace_chain(self):
        longest_chain = self.get_longest_chain()

        if longest_chain:
            updated_chain = [Block.from_json(b) for b in longest_chain]

            self.chain = updated_chain

            return True
        return False

    def to_json(self):
        blockchain_data = {
            "chain": [block.to_json() for block in self.chain],
            "length": len(self.chain),
            "nodes": list(self.nodes),
        }
        return blockchain_data


class Block:
    def __init__(self, index, proof, prev_hash, timestamp, data, transactions):
        self.index = index
        self.transactions = transactions
        self.proof = proof
        self.hash = self.calc_hash(prev_hash, data)
        self.prev_hash = prev_hash
        self.timestamp = timestamp
        self.data = data

    def calc_hash(self, prev_hash, data):
        return hashlib.sha256(
            f"{self.index}{self.proof}{prev_hash}{data}".encode()
        ).hexdigest()

    def to_json(self):
        return {
            "index": self.index,
            "proof": self.proof,
            "hash": self.hash,
            "prev_hash": self.prev_hash,
            "timestamp": str(self.timestamp),
            "data": self.data,
            "transactions": [t.to_json() for t in self.transactions],
        }

    @classmethod
    def from_json(cls, js):
        transactions = [Transaction.from_json(t) for t in js.get("transactions", [])]

        return cls(
            index=js["index"],
            proof=js["proof"],
            prev_hash=js["prev_hash"],
            timestamp=datetime.datetime.strptime(
                js["timestamp"], "%Y-%m-%d %H:%M:%S.%f"
            ),
            data=js["data"],
            transactions=transactions,
        )


def create_app(config_filename=None):
    node_address = str(uuid4()).replace("-", "")

    app = Flask(__name__)

    if config_filename:
        app.config.from_pyfile(config_filename)

    bc = Blockchain()

    @app.route("/mine_block", methods=["GET"])
    def mine_block():
        prev_block = bc.get_prev_block()
        proof = bc.proof_of_work(prev_block.proof)
        prev_hash = prev_block.hash
        data = request.args.get("data")

        new_block = bc.create_block(
            proof=proof,
            prev_hash=prev_hash,
            data=data,
        )

        return new_block.to_json(), 200

    @app.route("/get_chain", methods=["GET"])
    def get_chain():
        return bc.to_json(), 200

    @app.route("/is_valid", methods=["GET"])
    def is_valid():
        return (
            json.dumps(
                {
                    "is_valid": bc.is_chain_valid(bc.chain),
                }
            ),
            200,
        )

    @app.route("/add_transaction", methods=["POST"])
    def add_transaction():
        json_file = request.get_json()
        transaction_keys = ["sender", "receiver", "amount"]
        if not any(key in json_file for key in transaction_keys):
            return json.dumps({"message": "Missing transaction keys"}), 400

        json_file["sender"] = node_address

        bc.add_transaction_to_pool(
            json_file["sender"],
            json_file["receiver"],
            json_file["amount"],
        )

        return (
            json.dumps(
                {"Message": "Transaction added to block"},
            ),
            201,
        )

    @app.route("/connect_node", methods=["POST"])
    def connect_node():
        json_file = request.get_json()
        nodes = json_file.get("nodes")

        if nodes is None:
            return "No node", 400

        for node in nodes:
            bc.add_node(node)

        return (
            json.dumps(
                {
                    "message": "All nodes connected",
                    "total_nodes": len(bc.nodes),
                }
            ),
            201,
        )

    @app.route("/replace_chain", methods=["GET"])
    def replace_chain():
        if bc.replace_chain():
            return (
                json.dumps(
                    {
                        "message": "Chain replaced",
                    }
                ),
                200,
            )
        return (
            json.dumps({"message": "Chain not replaced"}),
            200,
        )

    return app


def run_app(port):
    app = create_app()
    # app.config["PORT"] = port
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True,
        use_reloader=False,
    )


if __name__ == "__main__":
    ports = [5010, 5011, 5012]
    processes = []

    for port in ports:
        p = Process(target=run_app, args=(port,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
