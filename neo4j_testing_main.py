#!/usr/bin/env python3
# this file enables 7x24 monitoring of neo4j new releases; auto setting up, testing, and reporting

import os
import time
import json
import threading
import configparser
import datetime
import requests
from schema_scanner import *
from query_generator import *
from query_mutator import *

class Neo4jMonitor:
    # seconds to check new release
    refreshing_frequency = 60

    versions = []

    current_version = "5.16.0"

    def __init__(self):
        pass

    def monitoring_new_release(self):
        possible_new_versions = []
        x = self.current_version.split('.')
        a,b,c=int(x[0]),int(x[1]),int(x[2])
        possible_new_versions.append("{}.{}.{}".format(a+1,b,c))
        possible_new_versions.append("{}.{}.{}".format(a,b+1,c))
        possible_new_versions.append("{}.{}.{}".format(a,b,c+1))
        while True:
            for each in possible_new_versions:
                url = "https://dist.neo4j.org/neo4j-community-{}-unix.tar.gz".format(each)
                test_req = requests.get(url)
                if test_req.status_code==200:
                    print("==!!new version found!!==")
                    self.current_version=each
                    return

    def get_current_version(self):
        fuzzy_url = "https://dist.neo4j.org/neo4j-community-{}.{}.{}-unix.tar.gz"
        for a in range(5,10):
            for b in range(10,30):
                for c in range(0,10):
                    test_url = fuzzy_url.format(a,b,c)
                    test_req = requests.get(test_url)
                    if test_req.status_code==200:
                        self.versions.append("{}.{}.{}".format(a,b,c))
                    else:
                        break
        self.current_version = self.versions[-1]
        print(self.current_version)

    def auto_setup(self):
        # try:
        #     os.system("kill -9 `pgrep -f neo4j`")
        # except:
        #     pass
        os.chdir(os.getcwd()+"/dbs")
        if not os.path.exists("./cybersecurity".format(self.current_version)):
            os.system("git clone https://github.com/neo4j-graph-examples/cybersecurity.git")
        if not os.path.exists("./neo4j-community-{}-unix.tar.gz".format(self.current_version)):
            os.system("wget https://dist.neo4j.org/neo4j-community-{}-unix.tar.gz".format(self.current_version))
        if not os.path.exists("./neo4j-community-{}".format(self.current_version)):
            os.system("tar -xvf neo4j-community-{}-unix.tar.gz".format(self.current_version))
        os.chdir(os.getcwd()+"/neo4j-community-{}".format(self.current_version))
        os.system("./bin/neo4j-admin dbms set-initial-password 12344321".format(self.current_version))
        os.system("./bin/neo4j-admin database load --from-stdin --overwrite-destination=true neo4j < ../cybersecurity/data/cyber-security-ad-50.dump".format(self.current_version))
        f = open("./conf/neo4j.conf","r")
        content = f.read()
        f.close()
        if "dbms.transaction.timeout=30s" not in content:
            os.system('echo "dbms.transaction.timeout=30s" >> ./conf/neo4j.conf')
        os.system("./bin/neo4j start")

neo4j_monitor = Neo4jMonitor()

# neo4j_monitor.get_current_version()

neo4j_monitor.auto_setup()