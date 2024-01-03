#!/usr/bin/env python3

import os
import time
import datetime

class Testing:
    threshold = 5
    def time_checking(self, base_time, testing_time):
        diff = max(base_time, testing_time)/min(base_time, testing_time)
        if diff>self.threshold and testing_time>50.0 and testing_time<base_time:
            self.log("[***** Potential Performance Bug: DIFF={:.2f}times *****]\n".format(diff))
            self.bug_rules_eval[0] += self.current_rules_eval[0]
            self.bug_rules_eval[1] += self.current_rules_eval[1]
            self.bug_rules_eval[2] += self.current_rules_eval[2]
            return 1
        return 0

    def result_checking(self, base_result, test_result, base_query, test_query):
        buggy = type(base_result)!=type(test_result) or base_result!=test_result
        if buggy and "count" in test_query:
            if base_result==None or test_result==None:
                self.log("[***** None Check *****]\n")
            else:
                # remove reduplicate bugs in one testing case
                if test_result in self.prev_results:
                    return
                self.detected_bug_num += 1
                self.bug_rules_eval[0] += self.current_rules_eval[0]
                self.bug_rules_eval[1] += self.current_rules_eval[1]
                self.bug_rules_eval[2] += self.current_rules_eval[2]
                self.log("[***** No.{} Potential Logic Bug: {} {} *****]\n".format(self.detected_bug_num, base_result, test_result))
                self.bug_log("{}\n[***** No.{} Potential Logic Bug:\n\tbase_query={}\n\ttest_query={}\n\tbase_result={}\ttest_result={}\n*****]\n".format(datetime.datetime.now(), self.detected_bug_num, base_query, test_query, base_result, test_result))
                self.prev_results.append(test_result)

    def testing(self, base_query, mutated_query):
        base_query_result, base_query_time = self.execute_ret_result_time(query=base_query, log_str="[BASE QUERY]")
        if mutated_query=="": # if it is an unexpected exception
            return
        mutated_query_result, mutated_query_time = self.execute_ret_result_time(query=mutated_query, log_str="[Mutated]")
        print("==base query `{}` result: \033[91m{}\033[0m==".format(base_query, base_query_result))
        print("==mutated query `{}` result: \033[91m{}\033[0m==".format(mutated_query, mutated_query_result))

class Neo4jTesting(Testing):
    # Neo4j Config
    def __init__(self):
        self.start_time = time.time()
        self.bolt_uri = "bolt://127.0.0.1:7687"
        self.driver = GraphDatabase.driver(self.bolt_uri, auth=("neo4j", "12344321"))

    # log/return result+time
    def execute_ret_result_time(self, query, log_str):
        driver = self.driver
        query_result = None
        query_time = -1
        with driver.session() as session:
            try:
                query_result, query_time = session.execute_write(self._new_execute, query)
            except Exception as e:
                print("unexpected exception: {}".format(str(e)))
                return None, -1
        return query_result, query_time

    @staticmethod
    def _new_execute(tx, query):
        ## clear cache first
        clear_query = "CALL db.clearQueryCaches();"
        tx.run(clear_query)
        query_result = -1
        query_time = -1
        query_execute = tx.run(query)
        query_data = query_execute.data()
        if len(query_data)==0:
            query_result = None
        else:
            query_result = (list(query_data[0].values())[0])
        query_time = query_execute.consume().result_available_after + query_execute.consume().result_consumed_after
        return query_result, query_time

class RedisGraphTesting(Testing):
    # Redis Config
    graph = "test"
    def __init__(self):
        r = redis.Redis(host="127.0.0.1", port="6379")
        self.driver = Graph(self.graph, r)

    def execute_ret_result_time(self, query, log_str):
        driver = self.driver
        query_result = None
        query_time = -1
        try:
            result = self.driver.query(query)
            first_result = result.result_set
            if len(first_result)==0:
                query_result = None
            else:
                query_result = first_result[0][0]
            query_time = result.run_time_ms
        except Exception as e:
            print("unexpected exception: {}".format(str(e)))
            return None, -1
        return query_result, query_time

class AgensGraphTesting(Testing):
    def __init__(self):
        self.init_testing_configs()
        self.start_time = time.time()
        if os.path.exists(self.logpath):
            self.init_log()
        self.log("***** Testing AgensGraph *****")
        self.connstr = "host={} port={} user={} password={}".format(
            self.ip,
            self.port,
            self.username,
            self.password
        )
        self.init_testing_configs()
        self.conn = psycopg2.connect(self.connstr)
        self.cur = self.conn.cursor()
        self.cur.execute("SET graph_path = t")

    def execute_ret_result_time(self, query, log_str):
        query_result = None
        query_time = -1
        query = query.replace('--', '-[]-')
        try:
            start_time = time.time()
            self.cur.execute(query)
            query_result = self.cur.fetchone()
            if query_result and len(query_result)>0:
                query_result = query_result[0]
            query_time = (time.time()-start_time)*1000
            self.cur.fetchall()
        except Exception as e:
            self.conn = psycopg2.connect(self.connstr)
            self.cur = self.conn.cursor()
            self.cur.execute("SET graph_path = t")
            self.except_log('\nQuery:{}\nInfo:{}\n'.format(query, str(e)))
            return None, -1
        self.executed_query_num += 1
        self.log("{} Query=\"{}\"\n\tQuery Result={}\n\tQuery Time={}\n".format(log_str, query, query_result, query_time))
        return query_result, query_time

if __name__ == "__main__":
    ##### reproduce neo4j bug #####
    import redis
    from redisgraph import Node, Edge, Graph, Path
    test = RedisGraphTesting()
    print("\033[91m##### redisgraph 2744 #####\033[0m")
    base_query = "MATCH ()-[a]-() RETURN count((a))"
    mutated_query = "MATCH ()-[a]-() RETURN count(id(a))"
    test.testing(base_query, mutated_query)
    print("\033[91m##### redisgraph 2858 #####\033[0m")
    base_query = "MATCH (c)--()--(c) return count(c)"
    mutated_query = "MATCH p=(c)--()--(c) return count(c)"
    test.testing(base_query, mutated_query)
    print("\033[91m##### redisgraph 2859 #####\033[0m")
    base_query = "MATCH (s1:A)--(s0:B)--(s2:A)<--()<--(s3:A)<--(s4:A)--(s5:A) WHERE s2=s5 RETURN count(s1)"
    mutated_query = "MATCH (s1:A)--(s0:B)--(s2:A)<--()<--(s3:A)<--(s4:A)--(s5:A) WHERE s2=s5 AND id(s0)>=0 RETURN count(s1)"
    test.testing(base_query, mutated_query)
    print("\033[91m##### redisgraph 2865 #####\033[0m")
    base_query = "MATCH (s1:B)-[*1..2]-(s3:A) RETURN count(s1)"
    mutated_query = "MATCH (s3:A)-[*1..2]-(s1:B) RETURN count(s1)"
    test.testing(base_query, mutated_query)
    print("\033[91m##### redisgraph 3071 #####\033[0m")
    base_query = "MATCH (n) RETURN count(elementId(n))"
    mutated_query = ""
    test.testing(base_query, mutated_query)
    print("redisgraph server crashed here.")

    # elif graphdb=="redisgraph":
    #     import redis
    #     from redisgraph import Node, Edge, Graph, Path
    #     test = RedisGraphTesting()
    # elif graphdb=="agensgraph":
    #     import psycopg2
    #     test = AgensGraphTesting()
    # else:
    #     pass

    # test.testing()
