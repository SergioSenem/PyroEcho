PyroEcho
=======================

Final project of UDESC School Subject: Distributed systems.

# Dependency #

Python version 3 or above
Pyro4

## Running the project

* First you need the execute the command `pyro4-ns` in a terminal
* Once you have a name server running, execute the watcher script with the command `python watcher.py`
* Now that the watcher is managing the connections to the name server, you can run one or many servers with the command `python server.py`
* To open a client interface, run the last script `python client.py`

# Why a Watcher?

* The watcher script controls the servers connections with the name server. 
* Once a server disconnects for any reason, this will close the socket connection between the watcher and the server, triggering the watcher method to remove the server from the name server.
* If the disconnected server was the master, the watcher is the responsible to promote a slave server to a new master.
