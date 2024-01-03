To produce bugs found by GraphGenie in neo4j-5.4.0

```
sudo docker build -t graphgenie/neo4j:5.4.0 .
sudo docker run -dit graphgenie/neo4j:5.4.0 bash
```

Go into the docker (you need your own docker id)
```
sudo docker exec -it cd7922d9561445fa17dd1d3cfbe1b5b8c7f9c89f4e832b692f8587ce8a9aeec6 bash
```

Start the neo4j server
```
root@cd7922d95614:/# ./neo4j-community-5.4.0/bin/neo4j start
Directories in use:
home:         /neo4j-community-5.4.0
config:       /neo4j-community-5.4.0/conf
logs:         /neo4j-community-5.4.0/logs
plugins:      /neo4j-community-5.4.0/plugins
import:       /neo4j-community-5.4.0/import
data:         /neo4j-community-5.4.0/data
certificates: /neo4j-community-5.4.0/certificates
licenses:     /neo4j-community-5.4.0/licenses
run:          /neo4j-community-5.4.0/run
Starting Neo4j.
Started neo4j (pid:54). It is available at http://localhost:7474
There may be a short delay until the server is ready.
```

Run the reproducing script
```
root@cd7922d95614:/# python3 reproduce.py
##### neo4j 12991 #####
unexpected exception: {code: Neo.DatabaseError.Statement.ExecutionFailed} {message: arraycopy: last destination index 2 out of bounds for object array[1]}
```