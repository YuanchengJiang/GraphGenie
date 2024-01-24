#!/usr/bin/env python3
import string
import re
import configparser
from random import randint, choice

# this is a lightweight cypher query generator

class RandomCypherGenerator():
    # in GraphGenie, the high-level idea is to mutated the graph query pattern
    # that is, the _path, rather than _predicate mutated by many existing works
    cypher_query_pattern = "{_match} {_path} {_predicate} {_return} {_other}"

    # Note: we generate cypher queries in an incremental way
    # we start from a specific number (node_number) which limits the count of nodes
    # self._node_num = int(config['testing_configs']['_node_num'])
    # You can start from two nodes so it only generates (x)-[y]-(z)
    # path vectors store the previously tested graph query patterns
    # if we test duplicated patterns for many times (recorded in `stuck`)
    # we would increase the node number, now the condition is
    # ! threshold
    # self.stuck==2*self._node_num*self._node_num

    _path_vectors = []
    _last_vector_length = 0
    stuck = 0

    # cypher query elements
    _match = ""
    _path = ""
    _predicate = ""
    _return = ""
    _other = ""

    def __init__(self, node_labels, edge_labels, node_properties, connectivity_matrix):
        config = configparser.ConfigParser()
        config.read('graphgenie.ini')
        self.graphdb = config['default']['graphdb']
        self.language = config['default']['language']
        self._node_num = int(config['testing_configs']['_node_num'])
        self.min_node_num = int(config['query_generation_args']['min_node_num'])
        self.max_node_num = int(config['query_generation_args']['max_node_num'])
        self.variable_pathlen_rate = float(config['query_generation_args']['variable_pathlen_rate'])
        self.node_symbol_rate = float(config['query_generation_args']['node_symbol_rate'])
        self.edge_symbol_rate = float(config['query_generation_args']['edge_symbol_rate'])
        self.node_label_rate = float(config['query_generation_args']['node_label_rate'])
        self.edge_label_rate = float(config['query_generation_args']['edge_label_rate'])
        self.multi_node_label_rate = float(config['query_generation_args']['multi_node_label_rate'])
        self.multi_edge_label_rate = float(config['query_generation_args']['multi_edge_label_rate'])
        self.cyclic_rate = float(config['query_generation_args']['cyclic_rate'])
        self.random_symbol_len = int(config['query_generation_args']['random_symbol_len'])
        self.cyclic_symbol = config['query_generation_args']['cyclic_symbol']
        self.multi_node_labels = int(config['query_generation_args']['multi_node_labels'])
        self.multi_edge_labels = int(config['query_generation_args']['multi_edge_labels'])
        self.node_labels = node_labels
        self.edge_labels = edge_labels
        self.node_properties = node_properties
        # connectivity matrix compresses info to decide whether two nodes are connectable
        # it would be useful to create non-empty result graph query pattern
        self.connectivity_matrix = connectivity_matrix

    # call before each run of test
    def init(self):
        config = configparser.ConfigParser()
        config.read('graphgenie.ini')
        # this is the starting node number
        # we usually suggest start from 2 to fuzz simpler bugs.
        self._node_num = int(config['testing_configs']['_node_num'])
        self._path_vectors = []
        self._last_vector_length = 0
        self.stuck = 0
        self.init_query()

    # note: call before each generation
    def init_query(self):
        self._match = ""
        self._path = ""
        self._predicate = ""
        self._return = ""
        self._condition = ""
        self.symbols = []
        self.node_symbols = []
        self.edge_symbols = []
        self.name_label_dict = {}
        self.nodes_num = 0

    # this is a random choice api for a given rate
    # e.g., if given_rate = 0.3, then 30% returns true and 70% return false
    def random_choice(self, given_rate):
        if randint(1,100)<=given_rate*100:
            return True
        else:
            return False

    # this is a random symbol generator
    # note: we only consider lowercase letters in ascii
    def random_symbol(self):
        return ''.join(choice(string.ascii_lowercase) for _ in range(self.random_symbol_len))

    # this part is simple; TODO: any other magic MATCHes?
    # _match indicates the query is a graph-matching query rather than add/update/delete queries
    # cypher: `match` or `optional match` clause
    def match_generator(self):
        match_candidates = ["MATCH", "OPTIONAL MATCH"]
        self._match = choice(match_candidates)

    def random_node_multi_labels(self, connectable_node_labels):
        random_num = randint(2, len(connectable_node_labels))
        node_label = choice(connectable_node_labels)
        for i in range(random_num-1):
            node_label += "|{}".format(choice(self.node_labels))
        return node_label

    def random_edge_multi_types(self):
        type_num = len(self.edge_labels)
        random_num = randint(2, type_num)
        edge_type = choice(self.edge_labels)
        for i in range(random_num-1):
            edge_type += "|{}".format(choice(self.edge_labels))
        return edge_type

    # given the previous node, use connectivity matrix to find connectable node labels
    def connectable_node_labels(self, prev_node_label, prev_node_direction):
        # currently we do not support graph databases except neo4j
        if self.graphdb!="neo4j":
            return self.node_labels
        # if this is the first node or previous node has no specific label
        if prev_node_label==None or prev_node_label=="" or "%" in self.node_labels:
            return self.node_labels
        possible_node_labels = []
        # if there are multiple node labels, we need to consider all of them
        for each_prev_node_label in prev_node_label.split('|'):
            prev_node_index = self.node_labels.index(each_prev_node_label)
            for each_label in self.node_labels:
                each_label_index = self.node_labels.index(each_label)
                # for forward or backward direction, we refer to different indices
                # matrix[src][dst]=1 means connectable
                # otherwise not connectable; do not attach this node
                # TODO: edge types are not considered!!
                if prev_node_direction==">":
                    if self.connectivity_matrix[prev_node_index][each_label_index]!=0:
                        possible_node_labels.append(each_label)
                elif prev_node_direction=="<":
                    if self.connectivity_matrix[each_label_index][prev_node_index]!=0:
                        possible_node_labels.append(each_label)
                else:
                    # if no direction, need to consider both
                    if self.connectivity_matrix[prev_node_index][each_label_index]!=0 or self.connectivity_matrix[each_label_index][prev_node_index]!=0:
                        possible_node_labels.append(each_label)
        return possible_node_labels

    # to generate random path unit
    def random_path_unit(self, prev_node_label=None, prev_node_direction=None):
        connectable_node_labels = self.connectable_node_labels(prev_node_label, prev_node_direction)
        path_unit_candidates = [
            "({node_sym})-[{edge_sym}]-",
            "({node_sym})<-[{edge_sym}]-",
            "({node_sym})-[{edge_sym}]->"
            ]
        random_unit = choice(path_unit_candidates)
        # node can have no symbols => anonymous nodes
        # nodes without symbol cannot be used in predicates unless referring to the path() list?
        random_node_sym = self.random_symbol() if self.random_choice(self.node_symbol_rate) else ""
        random_edge_sym = self.random_symbol() if self.random_choice(self.edge_symbol_rate) else ""
        # determine whether we need node label
        if self.random_choice(self.node_label_rate) and random_node_sym!="" and len(connectable_node_labels)!=0:
            node_labels = ""
            # now we only support multi node labels in neo4j
            # only when connectable node number >= 2
            if self.graphdb=="neo4j" and self.multi_node_labels and len(connectable_node_labels)>=2:
                # TODO: multiple labels need also to ask connectivity matrix
                node_labels = self.random_node_multi_labels(connectable_node_labels) if self.random_choice(self.multi_node_label_rate) else choice(connectable_node_labels)
            else:
                node_labels = choice(connectable_node_labels)
            random_node_sym = "{}:{}".format(random_node_sym, node_labels)
        # determine whether we need edge label
        if self.random_choice(self.edge_label_rate) and random_edge_sym!="":
            # do not support multiple edge labels
            random_edge_sym = "{}:{}".format(random_edge_sym, choice(self.edge_labels))
        return random_unit.format(node_sym=random_node_sym, edge_sym=random_edge_sym)

    def cypher_get_unit_direction(self, path_unit):
        if "<" in path_unit:
            return "<"
        elif ">" in path_unit:
            return ">"
        else:
            return "-"

    def parse_path_unit_node_label(self, path_unit):
        the_node = path_unit.split('-')[0]
        if ':' not in the_node:
            return ""
        else:
            # extract Person from (a:Person)
            return the_node.split(':')[1].split(')')[0]

    # it is important to generate diverse graph query patterns
    def path_generator(self):
        nodes_num = self._node_num
        path = ""
        prev_node_label = ""
        prev_node_direction = "-"
        # given the number of nodes, we generate each node unit
        # it takes previous node label and edge information and checks the connectivity
        # connectivity: before testing, we have parsed the target dataset to pre-analyze
        # the connectivity among different types of nodes
        # note: if supporting update/insert clauses later, we need incremental updates to
        # the connectivity matrix
        for i in range(nodes_num):
            new_path_unit = self.random_path_unit(prev_node_label, prev_node_direction)
            # update the previous node label and edge direction after generation
            prev_node_label = self.parse_path_unit_node_label(new_path_unit)
            prev_node_direction = self.cypher_get_unit_direction(new_path_unit)
            if self.random_choice(self.variable_pathlen_rate):
                variable_length_expressions = ["*..1]", "*0..1]", "*0..0]", "*1..1]"]
                new_path_unit = new_path_unit.replace(']', choice(variable_length_expressions))
            path += new_path_unit
        # to strip the tail edge
        path = ")".join(path.split(")")[:-1])+")"
        # to generate cyclic path
        if self.random_choice(self.cyclic_rate):
            cyclic_str = "{cyc_sym}{node_label}".format(
                cyc_sym = self.cyclic_symbol,
                node_label= ":"+choice(self.node_labels) if self.random_choice(self.node_label_rate) else ""
            )
            path = ("({cyc})-{path}-({cyc})".format(cyc=cyclic_str, path="-".join(path.split("-")[1:-1])))
        self._path = path
        # parse the path to collect available nodes/edges for later creating predicates
        # TODO: finish it on the fly
        self.path_parser()

    def path_parser(self):
        self.nodes_num = self._path.count('-')/2 + 1
        symbol_list = re.findall("[(,\[][a-z]{{{sym_len}}}".format(sym_len=self.random_symbol_len), self._path)
        symbol_list_with_labels = re.findall("[(,\[][a-z]{{{sym_len}}}[:]?[\w]+".format(sym_len=self.random_symbol_len), self._path)
        for each_symbol in symbol_list:
            symbol_name = each_symbol[1:]
            self.symbols.append(symbol_name)
            if each_symbol[0]=="(":
                self.node_symbols.append(symbol_name)
            elif each_symbol[0]=="[":
                self.edge_symbols.append(symbol_name)
        for each_symbol in symbol_list_with_labels:
            symbol_name = each_symbol[1:].split(':')[0]
            symbol_label = each_symbol[1:].split(':')[1]
            self.symbols.append(symbol_name)
            if each_symbol[0]=="(":
                self.node_symbols.append(symbol_name)
            elif each_symbol[0]=="[":
                self.edge_symbols.append(symbol_name)
            self.name_label_dict.update({symbol_name: symbol_label})
        # to record the path, for incrementally generation
        # record node labels only, save as vector.
        all_nodes = re.findall("\([A-Za-z0-9:]*\)", self._path)
        path_vector = []
        for each_node in all_nodes:
            if ':' not in each_node:
                path_vector.append(0)
            else:
                node_label = each_node.split(':')[1].split(')')[0]
                path_vector.append(self.node_labels.index(node_label)+1)

        # the code below is for incremental base query generation
        # we encode the graph pattern into vectors
        # too many deduplicated queries would increase the node number of graph pattern
        if path_vector not in self._path_vectors:
            print("node num: {} tested vectors:{}".format(self._node_num, self._last_vector_length+1))
            self._path_vectors.append(path_vector)
        if self._last_vector_length == len(self._path_vectors):
            self.stuck += 1
        else:
            self.stuck = 0
        self._last_vector_length = len(self._path_vectors)
        if self.stuck==2*self._node_num*self._node_num:
            self.stuck = 0
            self._node_num += 1
            self._last_vector_length = 0
            self._path_vectors.clear()

    # as we do not partition the predicate, I do not plan to create complex predicate
    # TODO: but it is better to have more complex predicate
    def predicate_generator(self):
        pattern = "WHERE {}"
        predicate = "{} IS NOT NULL AND True".format(choice(self.node_symbols)) if len(self.node_symbols)>0 else "True"
        self._predicate = pattern.format(predicate)

    # note: we focus on testing `count`
    def return_generator(self):
        _return = "{return_keyword} {return_staff}"
        return_keywords = ["RETURN", "RETURN DISTINCT"]
        # TODO: to support count(DISTINCT ), max(), min()
        test_returns = ["count({})"]
        return_staff = choice(test_returns).format(choice(self.symbols)) if len(self.symbols)>0 else "count(1)"
        self._return = _return.format(
            return_keyword = choice(return_keywords),
            return_staff = return_staff
        )

    # for count() testing, we do not really need other clauses
    # following clauses are just random selections. they can be improved
    def other_generator(self):
        _other = "{order_by} {skip} {limit}"
        order_by_keywords = ["", "ORDER BY 1", "ORDER BY NULL"]
        if len(self.node_symbols)>0:
            order_by_keywords.append("ORDER BY {}".format(choice(self.node_symbols)))
        # SKIP 0 is redundant
        skip_keywords = ["", "SKIP 1", "SKIP 0", "SKIP 0", "SKIP 0", "SKIP 0", "SKIP 0", "SKIP 0"]
        # LIMIT >=1 is redundant to return count
        limit_keywords = ["", "LIMIT 0", "LIMIT 1", "LIMIT 1", "LIMIT 2", "LIMIT 3", "LIMIT 5", "LIMIT 1"]
        self._other = _other.format(
            order_by = choice(order_by_keywords),
            skip = choice(skip_keywords),
            limit = choice(limit_keywords)
        )

    def random_query_generator(self):
        self.init_query()
        self.match_generator()
        self.path_generator()
        self.predicate_generator()
        self.return_generator()
        self.other_generator()
        query = self.cypher_query_pattern.format(
            _match = self._match,
            _path = self._path,
            _predicate = self._predicate,
            _return = self._return,
            _other = self._other
        )
        query = re.sub(' +', ' ', query).strip(' ')
        query = re.sub('[*]+', '*', query).strip(' ')
        return query
