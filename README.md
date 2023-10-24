<img src=fig/new_logo.png width=100% />

## Introduction

GraphGenie is an bug-finding tool to detect logic bugs and performance issues (we also find internal errors) in graph database management systems. Specifically, unlike most existing testing works mutating query predicates, GraphGenie leverages Graph Query Transformations (GQT) to construct semantically equivalent or variant graph query patterns, which enables comparative analysis on their results to reveal bugs. GraphGenie has been tested and found previous unknown bugs on popular graph database engines like Neo4j.

If you use, extend or build upon GraphGenie we kindly ask you to cite the our ICSE'24 paper:
```
@inproceedings{jiang2024detecting,
  title={Detecting Logic Bugs in Graph Database Management Systems via Injective and Surjective Graph Query Transformation},
  author={Jiang, Yuancheng and Liu, Jiahao and Ba, Jinsheng and Yap, Roland H.C. and Liang, Zhenkai and Rigger, Manuel},
  booktitle={Proceedings of the 46th International Conference on Software Engineering},
  publisher = {{ACM}},
  year={2024},
  doi = {10.1145/3597503.3623307}
}
```

## Environment Requirement
The code has been tested running under Python 3.8.10. The OS is 20.04.2 LTS Ubuntu Linux 64-bit distribution.

**Dependencies**
```
apt install python3
apt install python3-pip
pip3 install configparser
pip3 install neo4j
pip3 install redisgraph
pip3 install psycopg2
```

## Graph Database Engine Setup

We do not initialize graph data. We use existing graph dataset like [recommendations](https://github.com/neo4j-graph-examples/recommendations.git). We give concrete steps for setting up the [Neo4j](https://github.com/neo4j/neo4j) below. For other graph database engines, please refer to official documentations for installation and dataset initialization. We include the python drivers for [RedisGraph](https://github.com/RedisGraph/RedisGraph/) and [AgensGraph](https://github.com/bitnine-oss/agensgraph/) in our code.

**Neo4j**

```
apt install openjdk-17-jdk;
cd dbs;
wget https://dist.neo4j.org/neo4j-community-5.11.0-unix.tar.gz;
tar -xvf neo4j-community-5.11.0-unix.tar.gz;
git clone https://github.com/neo4j-graph-examples/recommendations.git;
cd neo4j-community-5.11.0;
./bin/neo4j-admin database load --from-stdin --overwrite-destination=true neo4j < ../recommendations/data/recommendations-50.dump;
echo "dbms.transaction.timeout=30s" >> ./conf/neo4j.conf
./bin/neo4j start
```
Then please connect to the server to config your password
(the default username:neo4j password:neo4j)
(password is 12344321 in our default setting)
```
./bin/cypher-shell
```

## Usage

Config graphgenie.ini first and then start the testing:

If you test Neo4j, simply run the main.py
```
./main.py
```
For other databases, you need to first initialize the dataset and specify
```
node_labels, edge_labels, node_properties, connectivity_matrix
```
in main.py line 332, or implement your own schema scanner (should be similar to Neo4j one).

Detected bugs can be found in `./bug.log` (logic bugs or performance issues) or `./exception.log` (internal errors). The `./testing.log` records all executed queries.

## Todos

We only implement the prototype code. There are still many todos:

* to support GDBMS: Memgraph/Kuzu/FalkorDB/..
* to have an option for automatically initializing the graph data so we do not need existing dataset
* to support testing update/insert clauses
* to have more mutation rules
* to limit the max threads

## About Gremlin

We focus on testing Cypher query language. Currently we do not release the code for testing Gremlin database engines because we are using the [cypher-for-gremlin](https://github.com/opencypher/cypher-for-gremlin) translator, which sometimes leads to inaccurate translation and false bug alarm.

## Bugs we found:

[Neo4j](https://github.com/neo4j/neo4j/issues/created_by/YuanchengJiang), [RedisGraph](https://github.com/RedisGraph/RedisGraph/issues/created_by/YuanchengJiang), [AgensGraph](https://github.com/bitnine-oss/agensgraph/issues/created_by/YuanchengJiang)
