
"""
Structures for the Bitcoin transactions network and Bitcoin users graph
"""

import sys

from .bitcoin import Transaction, TransactionInput, TransactionOutput
from .users import UserNetwork


class TransactionNetwork:
    """ List of transactions with an unique set of all encountered addresses
        (as inputs or outputs of all transactions)
    """
    def __init__(self):
        self.addresses = UserNetwork()

    def build(self, spark_df):
        """ From a Spark dataframe following the json format build the transaction network

        :param spark_df: PySpark Dataframe object of bitcoin transactions
        """

        print("\nGetting already known addresses from Graph Database...")
        self.addresses.populate_known_addresses()

        # Will iterate over each row of the pyspark dataframe
        transactions_total = spark_df.count()

        transactions_iterator = spark_df.toLocalIterator()

        transactions_total_count = 0
        # Transactions are committed every 10000
        transactions_batch_limit = 10000
        transactions_batch_count = 0

        print("Building graph from", transactions_total, "transactions...")
        print("Transactions :     Addresses :    Progression :")

        for t in transactions_iterator:

            # Each transaction is converted to a Transaction object and processed by the UserNetwork
            self.addresses.add_transaction(TransactionNetwork.json_to_transaction(t))

            # Display transactions count and heuristics usage
            transactions_total_count += 1
            sys.stdout.write(
                "\r{0: >12}    {1: >12}      ({2}%)".format(
                    transactions_total_count,
                    len(self.addresses.known_addresses),
                    round(transactions_total_count/transactions_total*100, 2)
                ))
            sys.stdout.flush()

            # Commit new transactions every transactions_batch_limit
            transactions_batch_count += 1
            if transactions_batch_count == transactions_batch_limit:
                self.addresses.commit_new_entries()
                transactions_batch_count = 0

        print("\nDone")

    def build_identity_hint_network(self, spark_df):

        print("Building Identity hint network...")
        self.addresses.populate_known_addresses_with_users()

        transactions_iterator = spark_df.toLocalIterator()
        transactions_total = spark_df.count()

        transactions_total_count = 0
        # Transactions are committed every 10000
        transactions_batch_limit = 10000
        transactions_batch_count = 0

        print("Adding edges between users for", transactions_total, "transactions...")
        print("Transactions :    Progression :")
        for t in transactions_iterator:
            transactions_total_count += 1
            self.addresses.h4_community_detection(TransactionNetwork.json_to_transaction(t))

            sys.stdout.write(
                "\r{0: >12}      ({1}%)".format(
                    transactions_total_count,
                    round(transactions_total_count / transactions_total * 100, 2)
                ))
            sys.stdout.flush()

            # Commit new transactions every transactions_batch_limit
            transactions_batch_count += 1
            if transactions_batch_count == transactions_batch_limit:
                self.addresses.commit_new_user_relations()
                transactions_batch_count = 0

    @staticmethod
    def json_to_transaction(transaction_json):
        """ Create Transaction object from json representation

        :param transaction_json: JSON Object of a transaction
        """
        transaction_inputs = []
        transaction_outputs = []

        for t_in in transaction_json.tx_ins:
            transaction_in = TransactionInput(t_in.address, t_in.value)
            transaction_inputs.append(transaction_in)

        for t_out in transaction_json.tx_outs:
            transaction_out = TransactionOutput(t_out.address, t_out.value)
            transaction_outputs.append(transaction_out)

        return Transaction(transaction_inputs, transaction_outputs, transaction_json.timestamp)
