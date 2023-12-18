# blockchain geral

import datetime
import hashlib
import json

from flask import Flask


class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_block(proof=1, prev_hash='0')

    def create_block(self, proof, prev_hash):
        block = Block(proof, prev_hash,
                      datetime.datetime.now(), 'dados')
        self.chain.append(block)

        return block

    def get_prev_block(self):
        return self.chain[-1]

    def proof_of_work(self, prev_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(
                f'{new_proof**2 - prev_proof**2}'.encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1

        return new_proof

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
                f'{proof**2 - prev_proof**2}'.encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            prev_block = block
            block_index += 1

        return True

    def to_json(self):
        return json.dumps([block.to_json() for block in self.chain], indent=4)


class Block:
    index = -1

    def __init__(self,  proof,  prev_hash, timestamp, data):
        Block.index += 1
        self.index = Block.index
        self.proof = proof
        self.hash = hashlib.sha256(
            f'{self.index}{self.proof}{prev_hash}{data}'.encode()).hexdigest()
        self.prev_hash = prev_hash
        self.timestamp = timestamp
        self.data = data

    def to_json(self):
        return {
            'index': self.index,
            'proof': self.proof,
            'hash': self.hash,
            'prev_hash': self.prev_hash,
            'timestamp': str(self.timestamp),
            'data': self.data
        }


if __name__ == '__main__':
    app = Flask(__name__)

    bc = Blockchain()

    @app.route('/mine_block', methods=['GET'])
    def mine_block():
        prev_block = bc.get_prev_block()
        proof = bc.proof_of_work(prev_block.proof)
        prev_hash = prev_block.hash

        new_block = bc.create_block(
            proof=proof, prev_hash=prev_hash)

        return new_block.to_json(), 200

    @app.route('/get_chain', methods=['GET'])
    def get_chain():
        return bc.to_json(), 200

    @app.route('/is_valid', methods=['GET'])
    def is_valid():
        return json.dumps({
            "is_valid": bc.is_chain_valid(bc.chain)
        }), 200

    app.run(port=5001)
