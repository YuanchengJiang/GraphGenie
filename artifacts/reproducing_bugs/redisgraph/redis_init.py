#!/usr/bin/env python3
import redis
from redisgraph import Edge, Graph, Path

f = open("./dataset.txt", "r")

query = f.read()
#query = "match ()-[n]-() return count(n)"

host = "127.0.0.1"
port = 6379
graph = "test"
r = redis.Redis(host=host, port=port)
driver = Graph(graph, r)
result = driver.query(query)
print(result.result_set)
