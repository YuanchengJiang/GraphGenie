#!/usr/bin/env python3
import re
import string
import configparser
from random import choice, randint

class CypherQueryMutator:
    cypher_query_pattern = "{_match} {_path} {_predicate} {_return} {_other}"

    def __init__(self, node_labels, edge_labels, node_properties, connectivity_matrix):
        config = configparser.ConfigParser()
        config.read('graphgenie.ini')
        self.graphdb = config['default']['graphdb']
        self.language = config['default']['language']
        self.random_symbol_len = int(config['query_generation_args']['random_symbol_len'])
        self.graph_pattern_mutation = int(config['testing_strategy']['graph_pattern_mutation'])
        self.mutated_query_num = int(config['testing_configs']['mutated_query_num'])
        self.node_labels = node_labels
        self.edge_labels = edge_labels
        self.node_properties = node_properties
        self.connectivity_matrix = connectivity_matrix
        pass

    def cypher_query_parser(self, query):
        _match = "OPTIONAL MATCH" if "OPTIONAL" in query else "MATCH"
        _path = query.split("MATCH ")[1].split(' ')[0].strip(' ')
        if "WHERE " not in query:
            _predicate = ""
        else:
            _predicate = "WHERE " + query.split("WHERE")[1].split("RETURN")[0].strip(' ')
        return_symbol = "RETURN DISTINCT " if "RETURN DISTINCT" in query else "RETURN "
        _return = return_symbol + query.split(return_symbol)[1].split(')')[0]+')'
        _other = ')'.join(query.split(return_symbol)[1].split(')')[1:])
        return _match, _path, _predicate, _return, _other

    def path_parser(self, path):
        symbols = []
        node_symbols = []
        edge_symbols = []
        symbol_list = re.findall("[(,\[][a-z]{{{sym_len}}}".format(sym_len=self.random_symbol_len), path)
        for each_symbol in symbol_list:
            symbol_name = each_symbol[1:]
            symbols.append(symbol_name)
            if each_symbol[0]=="(":
                node_symbols.append(symbol_name)
            elif each_symbol[0]=="[":
                edge_symbols.append(symbol_name)
        return symbols, node_symbols, edge_symbols

    def init_for_each_base_query(self, base_query):
        # meta data for base query
        self.base_query = base_query
        self.base_match = ""
        self.base_path = ""
        self.base_predicate = ""
        self.base_return = ""
        self.base_other = ""
        self.base_symbols = []
        self.base_node_symbols = []
        self.base_edge_symbols = []

        self.mutated_match = ""
        self.mutated_path = ""
        self.mutated_predicate = ""
        self.mutated_return = ""
        self.mutated_other = ""
        self.mutated_symbols = []
        self.mutated_node_symbols = []
        self.mutated_edge_symbols = []

        # we split rules into three classes: Non-GQT, Property-GQT, and Structure-GQT
        self.Non_GQT = [1,0,0]
        self.Property_GQT = [0,1,0]
        self.Structure_GQT = [0,0,1]
        self.equivalent_queries = []
        self.restricted_queries = []

        # eval list (a list of triple) records the rule using the tuple: [x,y,z]
        # x=1 indicates it includes Non-GQT transformation
        # y=1 indicates it includes Property-GQT transformation
        # z=1 indicates it includes Structure-GQT transformation
        self.equivalent_queries_eval = []
        self.restricted_queries_eval = []

    def strip_spaces(self, query):
        return re.sub(" +", " ", query)

    # This is a random choice wrapper for a given rate
    # E.g., if given_rate = 0.3, then 30% returns True and 70% return False
    def random_choice(self, given_rate):
        if randint(1,100)<=given_rate*100:
            return True
        else:
            return False

    def random_symbol(self):
        # Symbol length for self.random_symbol()
        return ''.join(choice(string.ascii_lowercase) for _ in range(self.random_symbol_len))

    def query_parser(self, base_query):
        self.init_for_each_base_query(base_query)
        self.base_match, self.base_path, self.base_predicate, self.base_return, self.base_other = self.cypher_query_parser(base_query)
        self.base_symbols, self.base_node_symbols, self.base_edge_symbols = self.path_parser(self.base_path)
        self.mutated_match, self.mutated_path, self.mutated_predicate, self.mutated_return, self.mutated_other = self.cypher_query_parser(base_query)
        self.mutated_symbols, self.mutated_node_symbols, self.mutated_edge_symbols = self.path_parser(self.mutated_path)

    def generate_restricted_queries(self, base_query):
        self.query_parser(base_query)
        if "count(" in self.base_return:
            self.generate_restricted_add_edge_direction()
            self.generate_restricted_add_edge_label()
            self.generate_restricted_add_node_label()
            self.generate_restricted_add_node()
        return self.restricted_queries, self.restricted_queries_eval

    def generate_restricted_add_node_label(self, mode=0):
        if self.graph_pattern_mutation==0:
            return
        if mode==0:
            if "()" not in self.base_path:
                return
            new_path = self.base_path.replace("()", "({}:{})".format(self.random_symbol(), choice(self.node_labels)), 1)
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.base_match,
                _path = new_path,
                _predicate = self.base_predicate,
                _return = self.base_return,
                _other = self.base_other
            )
        mutated_query = self.strip_spaces(mutated_query)
        self.restricted_queries.append(mutated_query)
        self.restricted_queries_eval.append(self.Property_GQT)

    def generate_restricted_add_edge_label(self, mode=0):
        if self.graph_pattern_mutation==0:
            return
        if mode==0:
            if "-[]-" not in self.base_path:
                return
            new_path = self.base_path.replace("-[]-", "-[:{}]-".format(choice(self.edge_labels)), 1)
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.base_match,
                _path = new_path,
                _predicate = self.base_predicate,
                _return = self.base_return,
                _other = self.base_other
            )
        if self.language=="gremlin":
            mutated_query = self.strip_dots(mutated_query)
        mutated_query = self.strip_spaces(mutated_query)
        self.restricted_queries.append(mutated_query)
        self.restricted_queries_eval.append(self.Property_GQT)

    def generate_restricted_add_edge_direction(self, mode=0):
        if self.graph_pattern_mutation==0:
            return
        if mode==0:
            if ")-[]-(" not in self.base_path:
                return
            new_path = self.base_path.replace(")-[]-(", choice([")-[]->(", ")<-[]-("]), 1)
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.base_match,
                _path = new_path,
                _predicate = self.base_predicate,
                _return = self.base_return,
                _other = self.base_other
            )
        mutated_query = self.strip_spaces(mutated_query)
        self.restricted_queries.append(mutated_query)
        self.restricted_queries_eval.append(self.Non_GQT)

    def generate_restricted_add_node(self, mode=0):
        if self.graph_pattern_mutation==0:
            return
        if mode==0:
            if "count(1)" in self.base_return:
                return
            new_path_pattern = ["{new_node}-[]-{path}", "{new_node}-[]->{path}", "{new_node}<-[]-{path}"]
            new_node_label = choice(["", ":{}".format(choice(self.node_labels))])
            new_node = "({}{})".format(self.random_symbol(), new_node_label)
            new_path = choice(new_path_pattern).format(new_node=new_node, path=self.base_path)
            new_return = self.base_return.replace("(", "(DISTINCT ", 1)
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.base_match,
                _path = new_path,
                _predicate = self.base_predicate,
                _return = new_return,
                _other = self.base_other
            )
        mutated_query = self.strip_spaces(mutated_query)
        self.restricted_queries.append(mutated_query)
        self.restricted_queries_eval.append(self.Non_GQT)

    def generate_equivalent_queries(self, base_query):
        # for mutation rules, we have two modes
        # if you call the function without argument
        # then it is single mutatoin
        # if you call the function with argument 1
        # then it is iterative mutation based on previous mutated query
        self.query_parser(base_query)
        # the query number for iterative mutation times
        recursive_mutated_query_num = 5
        # TODO: still have many mutation rules that I do not have time to implement
        # TODO: SplitNodeLabels - node with multiple labels can be splitted in to predicate
        # TODO: SplitEdgeLabels - edge with multiple labels can be splitted in to predicate
        # TODO: SplitDirection - edge without directions can be splitted into
        #   left direction plus right direction
        # note: all rules should be also applicable the other way round.
        if self.language=="cypher":
            self.generate_equivalent_switch_match()
            self.generate_equivalent_splitting_path()
            self.generate_equivalent_symmetrical_queries()
            self.generate_equivalent_unfold_cyclic()
            self.generate_equivalent_count_id()
            self.generate_equivalent_count_other_symbol()
            self.generate_equivalent_move_label_predicate()
            self.generate_equivalent_predicate_intersect()
            self.generate_equivalent_queries_adding_redundant_predicate_a()
            self.generate_equivalent_queries_adding_redundant_predicate_b()
            self.generate_equivalent_queries_adding_redundant_predicate_c()
            self.generate_equivalent_rename_symbols_up()
            self.generate_equivalent_rename_symbols_down()
            if self.graphdb=="neo4j":
                self.generate_equivalent_adding_call_wrapper()
            else:
                self.generate_equivalent_count_star()
            if self.language=="cypher" and self.graphdb!="agensgraph":
                # for iterative mutations, not all rules are applicable
                recursive_mutation_rules = [
                    "generate_equivalent_switch_match",
                    "generate_equivalent_count_other_symbol",
                    "generate_equivalent_queries_adding_redundant_predicate_a",
                    "generate_equivalent_queries_adding_redundant_predicate_b",
                    "generate_equivalent_queries_adding_redundant_predicate_c",
                    "generate_equivalent_symmetrical_queries",
                    "generate_equivalent_move_label_predicate",
                    "generate_equivalent_predicate_intersect"
                ]
                while True:
                    getattr(self, choice(recursive_mutation_rules))(1)
                    if len(self.equivalent_queries)==self.mutated_query_num:
                        break

            """
            # for Evaluation #
            # Structure-GQT
            self.generate_equivalent_splitting_path()
            self.generate_equivalent_symmetrical_queries()
            self.generate_equivalent_unfold_cyclic()
            # Property-GQT
            self.generate_equivalent_count_id()
            self.generate_equivalent_count_other_symbol()
            self.generate_equivalent_move_label_predicate()
            # Non
            self.generate_equivalent_predicate_intersect()
            self.generate_equivalent_queries_adding_redundant_predicate_b()
            self.generate_equivalent_rename_symbols_up()
            """
        return self.equivalent_queries, self.equivalent_queries_eval

    def generate_equivalent_count_other_symbol(self, mode=0):
        if self.graph_pattern_mutation==0:
            return
        if mode==0:
            if len(self.base_node_symbols)<2:
                return
            if "min" in self.base_return or "max" in self.base_return:
                return
            return_sym = self.base_return.split('(')[1].split(' ')[-1].split(')')[0]
            new_return = self.base_return.replace(return_sym, "id({})".format(choice(self.base_node_symbols)), 1)
            # return_list = self.base_return.split(' ')
            # if "count(DISTINCT" in self.base_return:
            #     return_list[-1] = "count(DISTINCT {})".format(choice(self.base_node_symbols))
            # else:
            #     return_list[-1] = "count({})".format(choice(self.base_node_symbols))
            # new_return = ' '.join(return_list)
            mutated_query = self.cypher_query_pattern.format(
                _match = self.base_match,
                _path = self.base_path,
                _predicate = self.base_predicate,
                _return = new_return,
                _other = self.base_other
            )
            mutated_query = self.strip_spaces(mutated_query)
        else:
            if len(self.mutated_node_symbols)<2:
                return
            if "min" in self.mutated_return or "max" in self.mutated_return:
                return
            return_list = self.mutated_return.split(' ')
            if "count(DISTINCT" in self.mutated_return:
                return_list[-1] = "count(DISTINCT {})".format(choice(self.mutated_node_symbols))
            else:
                return_list[-1] = "count({})".format(choice(self.mutated_node_symbols))
            self.mutated_return = ' '.join(return_list)
            mutated_query = self.cypher_query_pattern.format(
                _match = self.mutated_match,
                _path = self.mutated_path,
                _predicate = self.mutated_predicate,
                _return = self.mutated_return,
                _other = self.mutated_other
            )
            mutated_query = self.strip_spaces(mutated_query)
        self.equivalent_queries.append(mutated_query)
        if mode==0:
            self.equivalent_queries_eval.append(self.Property_GQT)
        else:
            last_eval = self.equivalent_queries_eval[-1]
            self.equivalent_queries_eval.append([last_eval[0], 1, last_eval[-1]])

    # This mutation is not recursive
    def generate_equivalent_count_star(self, mode=0):
        if self.graph_pattern_mutation==0:
            return
        if mode==0:
            new_return = "RETURN count(*)"
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.base_match,
                _path = self.base_path,
                _predicate = self.base_predicate,
                _return = new_return,
                _other = self.base_other
            )
        mutated_query = self.strip_spaces(mutated_query)
        self.equivalent_queries.append(mutated_query)
        if mode==0:
            self.equivalent_queries_eval.append(self.Property_GQT)
        else:
            last_eval = self.equivalent_queries_eval[-1]
            self.equivalent_queries_eval.append([last_eval[0], 1, last_eval[-1]])

    # This mutation is not recursive
    def generate_equivalent_count_id(self, mode=0):
        if self.graph_pattern_mutation==0:
            return
        if "count(1)" in self.base_return or "max" in self.base_return or "min" in self.base_return:
            return
        return_sym = self.base_return.split('(')[1].split(' ')[-1].split(')')[0]
        new_return = self.base_return.replace(return_sym, "id({})".format(return_sym), 1)
        # return_list = self.base_return.split(' ')
        # return_list[-1] = return_list[-1].replace(")", "))").replace("(", "(id(")
        # new_return = ' '.join(return_list)
        pattern = self.cypher_query_pattern
        mutated_query = pattern.format(
            _match = self.base_match,
            _path = self.base_path,
            _predicate = self.base_predicate,
            _return = new_return,
            _other = self.base_other
        )
        mutated_query = self.strip_spaces(mutated_query)
        self.equivalent_queries.append(mutated_query)
        self.equivalent_queries_eval.append(self.Property_GQT)

    def generate_equivalent_switch_match(self, mode=0):
        if mode==0:
            mutated_query = self.cypher_query_pattern.format(
                _match = "OPTIONAL MATCH" if self.base_match=="MATCH" else "MATCH",
                _path = self.base_path,
                _predicate = self.base_predicate,
                _return = self.base_return,
                _other = self.base_other
            )
        else:
            self.mutated_match = "OPTIONAL MATCH" if self.mutated_match=="MATCH" else "MATCH"
            mutated_query = self.cypher_query_pattern.format(
                _match = self.mutated_match,
                _path = self.mutated_path,
                _predicate = self.mutated_predicate,
                _return = self.mutated_return,
                _other = self.mutated_other
            )
        mutated_query = self.strip_spaces(mutated_query)
        self.equivalent_queries.append(mutated_query)
        if mode==0:
            self.equivalent_queries_eval.append(self.Non_GQT)
        else:
            last_eval = self.equivalent_queries_eval[-1]
            self.equivalent_queries_eval.append([1, last_eval[1], last_eval[2]])

    def generate_equivalent_predicate_intersect(self, mode=0):
        if mode==0:
            mutated_query = self.base_query.replace('AND', 'WITH * WHERE')
        else:
            self.mutated_predicate = self.mutated_predicate.replace('AND', 'WITH * WHERE')
            mutated_query = self.cypher_query_pattern.format(
                _match = self.mutated_match,
                _path = self.mutated_path,
                _predicate = self.mutated_predicate,
                _return = self.mutated_return,
                _other = self.mutated_other
            )
        mutated_query = self.strip_spaces(mutated_query)
        self.equivalent_queries.append(mutated_query)
        if mode==0:
            self.equivalent_queries_eval.append(self.Non_GQT)
        else:
            last_eval = self.equivalent_queries_eval[-1]
            self.equivalent_queries_eval.append([1, last_eval[1], last_eval[2]])

    def generate_equivalent_queries_adding_redundant_predicate_a(self, mode=0):
        if mode==0:
            if "WHERE " in self.base_predicate:
                new_predicate = self.base_predicate + " AND True"
            else:
                new_predicate = "WHERE True"
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.base_match,
                _path = self.base_path,
                _predicate = new_predicate,
                _return = self.base_return,
                _other = self.base_other
            )
        else:
            if "WHERE " in self.mutated_predicate:
                self.mutated_predicate = self.mutated_predicate + " AND True"
            else:
                self.mutated_predicate = "WHERE True"
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.mutated_match,
                _path = self.mutated_path,
                _predicate = self.mutated_predicate,
                _return = self.mutated_return,
                _other = self.mutated_other
            )
        mutated_query = self.strip_spaces(mutated_query)
        self.equivalent_queries.append(mutated_query)
        if mode==0:
            self.equivalent_queries_eval.append(self.Non_GQT)
        else:
            last_eval = self.equivalent_queries_eval[-1]
            self.equivalent_queries_eval.append([1, last_eval[1], last_eval[2]])

    def generate_equivalent_unfold_cyclic(self, mode=0):
        if "cccccccc" in self.base_path:
            new_path = self.base_path.replace("cccccccc", "start", 1).replace("cccccccc", "end", 1)
            if "WHERE " in self.base_predicate:
                new_predicate = self.base_predicate + " AND start=end"
            else:
                new_predicate = "WHERE start=end"
            new_predicate = new_predicate.replace("cccccccc", "start")
            new_return = self.base_return.replace("cccccccc", "start")
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.base_match,
                _path = new_path,
                _predicate = new_predicate,
                _return = new_return,
                _other = self.base_other
            )
            self.equivalent_queries.append(mutated_query)
            self.equivalent_queries_eval.append(self.Structure_GQT)


    def generate_equivalent_queries_adding_redundant_predicate_b(self, mode=0):
        if self.graph_pattern_mutation==0:
            return
        if mode==0:
            if len(self.base_symbols)==0:
                return
            if "WHERE " in self.base_predicate:
                new_predicate = self.base_predicate + " AND id({})>=0.0".format(choice(self.base_symbols))
            else:
                new_predicate = "WHERE id({})>=0.0".format(choice(self.base_symbols))
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.base_match,
                _path = self.base_path,
                _predicate = new_predicate,
                _return = self.base_return,
                _other = self.base_other
            )
        else:
            if len(self.mutated_symbols)==0:
                return
            if "WHERE " in self.mutated_predicate:
                self.mutated_predicate = self.mutated_predicate + " AND id({})>=0.0".format(choice(self.mutated_symbols))
            else:
                self.mutated_predicate = "WHERE id({})>=0.0".format(choice(self.mutated_symbols))
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.mutated_match,
                _path = self.mutated_path,
                _predicate = self.mutated_predicate,
                _return = self.mutated_return,
                _other = self.mutated_other
            )
        mutated_query = self.strip_spaces(mutated_query)
        self.equivalent_queries.append(mutated_query)
        if mode==0:
            self.equivalent_queries_eval.append(self.Non_GQT)
        else:
            last_eval = self.equivalent_queries_eval[-1]
            self.equivalent_queries_eval.append([1, last_eval[1], last_eval[2]])

    def generate_equivalent_queries_adding_redundant_predicate_c(self, mode=0):
        if self.graph_pattern_mutation==0:
            return
        if mode==0:
            if len(self.base_symbols)==0:
                return
            if "WHERE " in self.base_predicate:
                new_predicate = self.base_predicate + " AND {sym}={sym}".format(sym=choice(self.base_symbols))
            else:
                new_predicate = "WHERE {sym}={sym}".format(sym=choice(self.base_symbols))
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.base_match,
                _path = self.base_path,
                _predicate = new_predicate,
                _return = self.base_return,
                _other = self.base_other
            )
        else:
            if len(self.mutated_symbols)==0:
                return
            if "WHERE " in self.mutated_predicate:
                self.mutated_predicate = self.mutated_predicate + " AND {sym}={sym}".format(sym=choice(self.mutated_symbols))
            else:
                self.mutated_predicate = "WHERE {sym}={sym}".format(sym=choice(self.mutated_symbols))
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.mutated_match,
                _path = self.mutated_path,
                _predicate = self.mutated_predicate,
                _return = self.mutated_return,
                _other = self.mutated_other
            )
        mutated_query = self.strip_spaces(mutated_query)
        self.equivalent_queries.append(mutated_query)
        if mode==0:
            self.equivalent_queries_eval.append(self.Non_GQT)
        else:
            last_eval = self.equivalent_queries_eval[-1]
            self.equivalent_queries_eval.append([1, last_eval[1], last_eval[2]])


    def generate_equivalent_symmetrical_queries(self, mode=0):
        if self.graph_pattern_mutation==0:
            return
        if mode==0:
            path = self.base_path.split('-')
            path.reverse()
            for i in range(len(path)):
                if path[i]!='':
                    if path[i][0]=='>' and path[i][-1]!='<':
                        path[i] = path[i][1:] + '<'
                    elif path[i][0]!='>' and path[i][-1]=='<':
                        path[i] = '>' + path[i][:-1]
            new_path = '-'.join(path)
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.base_match,
                _path = new_path,
                _predicate = self.base_predicate,
                _return = self.base_return,
                _other = self.base_other
            )
        else:
            path = self.mutated_path.split('-')
            path.reverse()
            for i in range(len(path)):
                if path[i]!='':
                    if path[i][0]=='>' and path[i][-1]!='<':
                        path[i] = path[i][1:] + '<'
                    elif path[i][0]!='>' and path[i][-1]=='<':
                        path[i] = '>' + path[i][:-1]
            self.mutated_path = '-'.join(path)
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.mutated_match,
                _path = self.mutated_path,
                _predicate = self.mutated_predicate,
                _return = self.mutated_return,
                _other = self.mutated_other
            )
        mutated_query = self.strip_spaces(mutated_query)
        self.equivalent_queries.append(mutated_query)
        if mode==0:
            self.equivalent_queries_eval.append(self.Structure_GQT)
        else:
            last_eval = self.equivalent_queries_eval[-1]
            self.equivalent_queries_eval.append([last_eval[0], last_eval[1], 1])

    # # Mutation Rules:
    # def generate_equivalent_redundant_match_with(self):
    def generate_equivalent_adding_call_wrapper(self):
        return_alias = "deadbeef"
        new_return = "{} AS {}".format(self.base_return, return_alias)
        mutated_query = self.cypher_query_pattern.format(
                _match = self.base_match,
                _path = self.base_path,
                _predicate = self.base_predicate,
                _return = new_return,
                _other = self.base_other
            )
        mutated_query = "CALL {{ {} }} RETURN {}".format(mutated_query, return_alias)
        mutated_query = self.strip_spaces(mutated_query)
        self.equivalent_queries.append(mutated_query)
        self.equivalent_queries_eval.append(self.Non_GQT)

    # # Mutation Rules:
    def generate_equivalent_splitting_path(self, mode=0):
        if self.graph_pattern_mutation==0:
            return
        if mode==0:
            path = self.base_path
            split_sym_test = self.base_return.split('(')[1]
            if ' ' in split_sym_test:
                split_sym = split_sym_test.split(' ')[1].split(')')[0]
            else:
                split_sym = split_sym_test.split(')')[0]
            if split_sym not in self.base_node_symbols or split_sym=="cccccccc":
                return
            split_pattern = "{sym}{node_label}),({sym}"
            after_split = path.split(split_sym)
            node_label = after_split[1].split(')')[0] if after_split[1][0]==":" else ""
            new_split = split_pattern.format(sym=split_sym, node_label=node_label)
            new_path = after_split[0] + new_split + after_split[1]
            mutated_query = self.cypher_query_pattern.format(
                _match = self.base_match,
                _path = new_path,
                _predicate = self.base_predicate,
                _return = self.base_return,
                _other = self.base_other
            )
        else:
            path = self.mutated_path
            split_sym = self.mutated_return.split('(')[1].split(')')[0]
            if split_sym not in self.mutated_node_symbols or split_sym=="cccccccc":
                return
            split_pattern = "{sym}{node_label}),({sym}"
            after_split = path.split(split_sym)
            node_label = after_split[1].split(')')[0] if after_split[1][0]==":" else ""
            new_split = split_pattern.format(sym=split_sym, node_label=node_label)
            self.mutated_path = after_split[0] + new_split + after_split[1]
            mutated_query = self.cypher_query_pattern.format(
                _match = self.mutated_match,
                _path = self.mutated_path,
                _predicate = self.mutated_predicate,
                _return = self.mutated_return,
                _other = self.mutated_other
            )
        mutated_query = self.strip_spaces(mutated_query)
        self.equivalent_queries.append(mutated_query)
        if mode==0:
            self.equivalent_queries_eval.append(self.Structure_GQT)
        else:
            last_eval = self.equivalent_queries_eval[-1]
            self.equivalent_queries_eval.append([last_eval[0], last_eval[1], 1])


    #Before: match (a:Movie)--(b) return a;
    #After: match (a)--(b) where a:Movie return a;
    def generate_equivalent_move_label_predicate(self, mode=0):
        if self.graph_pattern_mutation==0:
            return
        if mode==0:
            path = self.base_path
            node_label_list = re.findall("[(,\[][a-z]{{{}}}:[\w]*[),\]]".format(self.random_symbol_len), path)
            if len(node_label_list)==0:
                return
            target_label = choice(node_label_list)
            target = target_label.split(':')[0][1:]
            if "cccccccc" in target:
                return
            label = target_label.split(':')[1][:-1]
            new_path = path.split(target_label)[0] + target_label.split(':')[0] + (')' if target_label[0]=='(' else ']') + path.split(target_label)[1]

            predicate = self.base_predicate
            if "WHERE " not in predicate:
                new_predicate = "WHERE {}:{}".format(target, label)
            else:
                new_predicate = "{} AND {}:{}".format(predicate, target, label)
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.base_match,
                _path = new_path,
                _predicate = new_predicate,
                _return = self.base_return,
                _other = self.base_other
            )
        else:
            path = self.mutated_path
            node_label_list = re.findall("[(,\[][a-z]{{{}}}:[\w]*[),\]]".format(self.random_symbol_len), path)
            if len(node_label_list)==0:
                return
            target_label = choice(node_label_list)
            target = target_label.split(':')[0][1:]
            if "cccccccc" in target:
                return
            label = target_label.split(':')[1][:-1]
            self.mutated_path = path.split(target_label)[0] + target_label.split(':')[0] + (')' if target_label[0]=='(' else ']') + path.split(target_label)[1]
            predicate = self.mutated_predicate
            if "WHERE " not in predicate:
                self.mutated_predicate = "WHERE {}:{}".format(target, label)
            else:
                self.mutated_predicate = "{} AND {}:{}".format(predicate, target, label)
            pattern = self.cypher_query_pattern
            mutated_query = pattern.format(
                _match = self.mutated_match,
                _path = self.mutated_path,
                _predicate = self.mutated_predicate,
                _return = self.mutated_return,
                _other = self.mutated_other
            )
        mutated_query = self.strip_spaces(mutated_query)
        self.equivalent_queries.append(mutated_query)
        if mode==0:
            self.equivalent_queries_eval.append(self.Property_GQT)
        else:
            last_eval = self.equivalent_queries_eval[-1]
            self.equivalent_queries_eval.append([last_eval[0], 1, last_eval[2]])

    def random_symbol_up(self):
        # Symbol length for self.random_symbol()
        return ''.join(choice(string.ascii_lowercase) for _ in range(32))

    # not combinable
    def generate_equivalent_rename_symbols_down(self):
        base_query = self.base_query
        count = 0
        targets = set(re.findall("[(,\[][a-z]{"+str(self.random_symbol_len)+"}", base_query))
        for each_sym in targets:
            base_query = re.sub(each_sym[1:], "s{}".format(count), base_query)
            count = count+1
        equivalent_query = base_query
        self.equivalent_queries.append(equivalent_query)
        self.equivalent_queries_eval.append(self.Non_GQT)

    def generate_equivalent_rename_symbols_up(self):
        base_query = self.base_query
        targets = set(re.findall("[(,\[][a-z]{"+str(self.random_symbol_len)+"}", base_query))
        for each_sym in targets:
            base_query = re.sub(each_sym[1:], self.random_symbol_up(), base_query)
        equivalent_query = base_query
        self.equivalent_queries.append(equivalent_query)
        self.equivalent_queries_eval.append(self.Non_GQT)