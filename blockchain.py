import hashlib
import json

from time import time
from uuid import uuid4
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request



class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        #create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        #creates a new block and adds it to the chain
        """
        Create a new block in the blockchain
        :param proof: <int>the proof given by the proof of work algorithm
        :param previous_hash: (Optional)<str> Hash of previous block
        :return: <dict> New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }
        #reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """"
        Creates a new transaction to go into the next mined Block
        :param sender: <str> Address of the sender
        :param recipient: <str>Address of the recipient
        :param amount:<int> Amount
        :return: <int>The index of the Block that will hold this transaction
        """

        self.current_transactions.append({"sender": sender, "recipient": recipient, "amount": amount})

        return self.last_block['index'] + 1


    @property
    def last_block(self):
        #returns the last block in the chain
        return self.chain[-1]

    @staticmethod
    def hash(block):
        #hashes a block
        """
        Creates a SHA-256 hash of a block
        :param block: <dict> Block
        :return: <str>
        """
        #we must make sure that the dictionary is ordered or we will hace inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof):
        """
        Simple proof of work algorithm:
        -find a number p' such that hash(pp') contains leading 4 zeroes, where p is previous p'
        -p is the previous proof, and p' is the new proof
        :param last_proof: <int>
        :return: <int>
        """
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the proof: does hash(last_proof, proof) contain 4 leading zeroes ?

        :param last_proof: <int> Previous proof
        :param proof: <int> current proof
        :return: <bool> True if correct
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def register_node(self, address):
        """
        add a new node to the list of nodes
        :param address: <str>Address of node Eg. 'http://192.168.0.5:5000'
        :return: NOne
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        determine if a gicen blockchain is valid
        "param chain: <list> a blockchain
        :return: <bool> True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f"{last_block}")
            print(f"{block}")
            print("\n----------------\n")
            #check that the hash of block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False
            #check that the proof of work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1
        return True
    def resolve_conflict(self):
        """this is our consensus algorithm
        it resolves conflicts by replacing our chain with the longest one in the network
        :return: <bool> true if our chain was replaced false if not
        """
        neighbours = self.nodes
        new_chain = None

        #we are only looking fot chains longer than ours
        max_length = len(self.chain)

        #grab and verify chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                #check if the lenght is longer than the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        #replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True
        return False

#instantiate our node
app = Flask(__name__)
#generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

#instantiate the blockchain
blockchain = Blockchain()

@app.route('/mine',methods=['GET'])
def mine():
    #we run the proof of work algorithm to get the next proof
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    #we must receive a reward for finding the proof
    #the sender is 0 to signify that this node has mined a new coin
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )
    #forge the new block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New block forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    #check that the required fields are in the POSTed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing Values', 400
    #create a new transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': "New nodes have been added",
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflict()

    if replaced:
        response = {
            'message': "Our chain was replaced",
            "new_chain": blockchain.chain
        }
    else:
        response = {
            'message': "Our chain was authorative",
            'chain': blockchain.chain
        }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)