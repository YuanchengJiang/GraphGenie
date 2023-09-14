#!/usr/bin/env python3

import os
import time

from neo4j import GraphDatabase

# currently we only support neo4j

class SchemaScanner:
    node_count = 0
    edge_count = 0
    node_labels = []
    edge_labels = []
    node_properties = {}
    connectivity_matrix = []

    def __init__(self, ip, port, username, password):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        pass

    def scan(self):
        pass

    def print_schema_info(self):
        print("Node count: {}".format(self.node_count))
        print("Edge count: {}".format(self.edge_count))
        print("Node labels: {}".format(str(self.node_labels)))
        print("Edge labels: {}".format(str(self.edge_labels)))

    def print_connectivity(self):
        for i in self.node_labels:
            print(i[0], end=" ")
        print()
        for x in self.connectivity_matrix:
            for y in x:
                print(y, end=" ")
            print()

class Neo4jSchemaScanner(SchemaScanner):
    def neo4j_init(self):
        url = "bolt://{}:{}".format(self.ip, self.port)
        username = self.username
        password = self.password
        self.driver = GraphDatabase.driver(url, auth=(username, password))
        
    def scan(self):
        self.neo4j_init()
        get_node_count_query = "MATCH (n) RETURN count(n)"
        self.node_count = (list(self.execute_query(get_node_count_query)[0].values())[0])
        get_edge_count_query = "MATCH ()-[n]-() RETURN count(n)"
        self.edge_count = (list(self.execute_query(get_edge_count_query)[0].values())[0])
        get_node_labels_query = """
            MATCH (n)
            WITH DISTINCT labels(n) AS labels
            UNWIND labels AS label
            RETURN DISTINCT label
            ORDER BY label;
        """
        query_result = self.execute_query(get_node_labels_query)
        for i in query_result:
            self.node_labels.append(i['label'])
        get_edge_labels_query = """
            MATCH ()-[n]-()
            WITH DISTINCT type(n) AS labels
            UNWIND labels AS label
            RETURN DISTINCT label
            ORDER BY label;
        """
        query_result = self.execute_query(get_edge_labels_query)
        for i in query_result:
            self.edge_labels.append(i['label'])
        self.print_schema_info()
        self.scan_properties()
        self.scan_connectivity()
        return self.node_labels, self.edge_labels, self.node_properties, self.connectivity_matrix

    def scan_properties(self):
        get_properties_query = """
            MATCH (n:{})
            WITH DISTINCT(keys(n)) as key_sets
            UNWIND(key_sets) as keys
            RETURN DISTINCT(keys) as key;
        """
        for each_node_label in self.node_labels:
            properties = []
            query_result = self.execute_query(get_properties_query.format(each_node_label))
            for i in query_result:
                properties.append(i['key'])
            self.node_properties[each_node_label] = properties

    def scan_connectivity(self):
        for each_node_label in self.node_labels:
            matrix_row = []
            for each_test_node_label in self.node_labels:
                if each_node_label==each_test_node_label:
                    matrix_row.append(0)
                else:
                    test_query = "MATCH (a:{})-->(b:{}) RETURN count(a)".format(
                        each_node_label,
                        each_test_node_label
                    )
                    query_result = (list(self.execute_query(test_query)[0].values())[0])
                    matrix_row.append(0 if query_result==0 else 1)
            self.connectivity_matrix.append(matrix_row)
        self.print_connectivity()

    def execute_query(self, query):
        with self.driver.session() as session:
            query_result = session.execute_write(self._new_execute, query)
            return query_result

    @staticmethod
    def _new_execute(tx, query):
        query_result = -1
        query_execute = tx.run(query)
        query_data = query_execute.data()
        return query_data
