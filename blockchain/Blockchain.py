import datetime
import hashlib
import json
import copy


# Define the Blockchain class
class Blockchain:
    def __init__(self):
        # Initialize the blockchain with an empty chain, difficulty, transactions, balances, and a copy of the chain
        # for peer comparison

        # stores the chain of blocks
        self.chain = []

        # the condition specifies that the block's hash must start with '00000'
        self.difficulty = '00000'

        # will contain the pending transactions awaiting mining confirmation
        self.transactions = []

        # dictionary(Map) that tracks users balances within the blockchain
        # Each key-value pair represents a user’s public key and their corresponding balance
        self.balances = dict()

        # the very first block and it's hardcoded because there are no previous blocks
        self.genesis_block()

        # This is an order to make a copy of a chain
        # ************A deep copy means that all elements of self.chain are duplicated,
        # including nested objects.
        # This ensures that the copied object (self.peer_b) is completely independent of the original (self.chain),
        # so changes to self.chain won’t affect self.peer_b and vice versa.
        # *************A shallow copy, on the other hand, would only copy the references to objects,
        # meaning changes in nested objects could still affect the copy.
        self.peer_b = copy.deepcopy(self.chain)

    # ---------------------------------------------------------------------------------------------------------------

    # CREATE THE FIRST BLOCK
    def genesis_block(self):
        block = self.create_block(balances=dict(), previous_hash='0' * 64)
        self.chain.append(block)

    # CREATE BLOCK METHOD
    def create_block(self, balances, previous_hash):
        # increment the block index and add the creation date
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
        }

        # nonce is the number of miners compute to meet the difficulty condition
        nonce, hash = self.hash(block)
        block['nonce'] = nonce

        # Copying the balances and pending transactions
        block['balances'] = copy.deepcopy(balances)
        block['transactions'] = self.transactions

        # Setting the previous hash and the generated hash
        block['previous_hash'] = previous_hash
        block['hash'] = hash

        # Clearing the lists for transactions and balances
        self.transactions = []
        self.balances = dict()
        return block

    # hashing method
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        nonce = 0

        while True:
            hash_operation = hashlib.sha256(encoded_block + str(nonce).encode()).hexdigest()

            if hash_operation[:5] == self.difficulty:
                break
            else:
                nonce += 1

        return nonce, hash_operation

    # THIS METHOD RETURNS THE PREVIOUS BLOCK
    def get_previous_block(self):
        return self.chain[-1]

    # THIS METHOD ADDS TRANSACTION TO THE BLOCKCHAIN (append a new transaction to the list of pending transactions)
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    # ADD BALANCE METHOD
    def add_balance(self, receiver, amount):
        previous_block = self.get_previous_block()
        self.balances[receiver] = amount
        return previous_block['index'] + 1

    # VALIDATE THE BLOCKCHAIN INTEGRITY
    def is_chain_valid(self):
        previous_block = self.chain[0]
        block_index = 1

        while block_index < len(self.chain):
            block = self.chain[block_index]

            if block['previous_hash'] != previous_block['hash']:
                return False

            if block['hash'] != self.peer_b[block_index]['hash']:
                return False

            if block['hash'][:5] != self.difficulty:
                return False

            previous_block = block
            block_index += 1

        return True
