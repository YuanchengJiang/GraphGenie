To produce bugs found by GraphGenie in neo4j-5.1.0

```
sudo docker build -t graphgenie/neo4j:5.1.0 .
sudo docker run -dit graphgenie/neo4j:5.1.0 bash
```

Go into the docker (you need your own docker id)
```
sudo docker exec -it 9cbf5bc6d11fc1ce07c6e05c661ed5f7661bb1208ec08680d9c398c12af61c1e bash
```

Start the neo4j server
```
root@9cbf5bc6d11f:/# ./neo4j-community-5.1.0/bin/neo4j start
Directories in use:
home:         /neo4j-community-5.1.0
config:       /neo4j-community-5.1.0/conf
logs:         /neo4j-community-5.1.0/logs
plugins:      /neo4j-community-5.1.0/plugins
import:       /neo4j-community-5.1.0/import
data:         /neo4j-community-5.1.0/data
certificates: /neo4j-community-5.1.0/certificates
licenses:     /neo4j-community-5.1.0/licenses
run:          /neo4j-community-5.1.0/run
Starting Neo4j.
Started neo4j (pid:56). It is available at http://localhost:7474
There may be a short delay until the server is ready.
```

Run the reproducing script
```
root@9cbf5bc6d11f:/# python3 reproduce.py
##### neo4j 12988 #####
unexpected exception: {code: Neo.DatabaseError.Statement.ExecutionFailed} {message: Expected:
RegularSinglePlannerQuery(QueryGraph {Optional Matches: : ['QueryGraph {Shortest paths: ['ShortestPathPattern(Some(p),(a)-[  UNNAMED0:IN_GENRE*]-(c),true)']}']},InterestingOrder(RequiredOrderCandidate(List()),List(InterestingOrderCandidate(List(Asc(Variable(p),Map()))), InterestingOrderCandidate(List(Desc(Variable(p),Map()))))),DistinctQueryProjection(Map(p -> Variable(p)),QueryPagination(None,None),Selections(Set())),None,None)

Actual:
RegularSinglePlannerQuery(QueryGraph {Optional Matches: : ['QueryGraph {}']},InterestingOrder(RequiredOrderCandidate(List()),List()),DistinctQueryProjection(Map(p -> Variable(p)),QueryPagination(None,None),Selections(Set())),None,None)

Plan:
.produceResults("p")
.distinct("p AS p")
.apply(fromSubquery = false)
.|.optional()
.|.argument()
.argument()
.build()

Verbose plan:
ProduceResult(List(p))
Distinct(Map(p -> Variable(p)))
Apply(false)
| Optional(Set())
| Argument(Set())
Argument(Set())

Differences:
 - QueryGraph
    Expected: QueryGraph {Optional Matches: : ['QueryGraph {Shortest paths: ['ShortestPathPattern(Some(p),(a)-[  UNNAMED0:IN_GENRE*]-(c),true)']}']}
    Actual:   QueryGraph {Optional Matches: : ['QueryGraph {}']}
}
##### neo4j 12991 #####
==base query `OPTIONAL MATCH (s1)-[s0:DIRECTED]-()<-[s2:ACTED_IN]-(s1) RETURN count(s1);` result: 43==
==mutated query `OPTIONAL MATCH (s1)-[s0]-()<-[s2:ACTED_IN]-(s1) WHERE s0:DIRECTED RETURN count(s1);` result: 491==
##### neo4j 12996 #####
==base query `MATCH (a)-[b:RATED]->(c) RETURN count(a) SKIP 1;` result: None==
==mutated query `MATCH (a)-[b:RATED]->(c) RETURN count(b) SKIP 1;` result: 100004==
```

