To produce bugs found by GraphGenie in neo4j-4.4.12

```
sudo docker build -t graphgenie/neo4j:4.4.12 .
sudo docker run -dit graphgenie/neo4j:4.4.12 bash
```

Go into the docker (you need your own docker id)
```
sudo docker exec -it 135569faee56cf780a5e2c5cff77aa63307439cc8f30679f0074cc829a48736d bash
```

Start the neo4j server
```
root@135569faee56:/# ./neo4j-community-4.4.12/bin/neo4j start
Directories in use:
home:         /neo4j-community-4.4.12
config:       /neo4j-community-4.4.12/conf
logs:         /neo4j-community-4.4.12/logs
plugins:      /neo4j-community-4.4.12/plugins
import:       /neo4j-community-4.4.12/import
data:         /neo4j-community-4.4.12/data
certificates: /neo4j-community-4.4.12/certificates
licenses:     /neo4j-community-4.4.12/licenses
run:          /neo4j-community-4.4.12/run
Starting Neo4j.
Started neo4j (pid:77). It is available at http://localhost:7474
There may be a short delay until the server is ready.
```

Run the reproducing script
```
root@135569faee56:/# python3 reproduce.py
##### neo4j 12968 #####
unexpected exception: {code: Neo.DatabaseError.Statement.ExecutionFailed} {message: Exception closing multiple resources.}
```

