
"""
Driver handling connections with the Neo4j Graph Database,
transactions are handled though clauses and executed by the GraphDatabaseDriver
"""

from neo4j.v1 import GraphDatabase

from .databaseconfig import neo4j as cfg


class GraphDatabaseDriver:
    """ Neo4j Database driver

    """
    def __init__(self):
        self._driver = GraphDatabase.driver(cfg['uri'], auth=(cfg['user'], cfg['password']))

        # Create an Index on Address:hash, fasten MERGE operations by a lot
        with self._driver.session() as session:
            with session.begin_transaction() as tx:
                tx.run("CREATE INDEX ON :Address(hash)")

        # New addresses and transactions stored in memory before batch adding
        self.batch_new_addresses = []
        self.batch_new_relations = []

    def close(self):
        self._driver.close()

    def address_exists(self, address_hash):
        """ Check if a Bitcoin address is present in Graph database

        :param address_hash: address public key
        """
        with self._driver.session() as session:
            return session.write_transaction(self._address_exists, address_hash)

    @staticmethod
    def _address_exists(tx, address_hash):
        result = tx.run("MATCH (address:Address) "
                        "WHERE address.hash = $hash "
                        "RETURN address ", hash=address_hash)

        result = result.single()
        return result is not None and result[0] is not None

    def commit_additions(self):
        """ Add new addresses and new relations then clear current batch

        """
        self._add_addresses()
        self.batch_new_addresses.clear()

        self._add_relations()
        self.batch_new_relations.clear()

    def add_address(self, address):
        """ Add a new address for next commit

        :param address: String new address key
        """
        self.batch_new_addresses.append(address)

    def add_relation(self, relation):
        """ Add a new USER relation between two addresses for next commit

        :param relation: List of two address key
        """
        self.batch_new_relations.append(relation)

    def _add_addresses(self):
        """ Create nodes for all addresses in batch_new_addresses

        """
        query = "UNWIND $addresses AS h MERGE (a:Address{ hash: h })"
        with self._driver.session() as session:
            with session.begin_transaction() as tx:
                tx.run(query, addresses=self.batch_new_addresses)

    def _add_relations(self):
        """ Create edges for all addresses relations in batch_new_relations
        """
        query = "UNWIND $relations AS a " \
                "MATCH (a1:Address { hash: a[0] }) " \
                "MATCH (a2:Address { hash: a[1] }) " \
                "MERGE (a1)-[:USER]->(a2)"
        with self._driver.session() as session:
            with session.begin_transaction() as tx:
                tx.run(query, relations=self.batch_new_relations)
