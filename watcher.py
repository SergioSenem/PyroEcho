import Pyro4


@Pyro4.expose
class Watcher:

    def __init__(self):
        self.nameserver = Pyro4.locateNS()
        self.servers = []

    # Exposed method to the server name itself in the watcher server list
    # This way the watcher can remove the correct server from the name server once it disconnects
    def add_server_name(self, name):
        server = self.servers[-1]
        server['name'] = name
        self.list_servers()

    # Method called when a new server connects with the watcher
    def server_connected(self, connection, data):
        try:
            connection_id = connection.__hash__()
            print(f"A server connected with id {connection_id}")
            self.add_server(connection_id)
        except Exception as e:
            print(e)
        return data

    # Adds the server the the server list, if the list is empty, this is the master server
    def add_server(self, connection_id):
        is_master = len(self.servers) == 0
        server = {'id': connection_id, 'is_master': is_master}
        self.servers.append(server)

    # Method called when a server disconnects
    def server_disconnected(self, connection):
        try:
            connection_id = connection.__hash__()
            print(f"Server with id {connection_id} disconnected.")
            self.remove_server(connection_id)
        except Exception as e:
            print(e)

    # If the server is a slave, simply remove it from the list
    # If the server is a master, promote a slave to master
    def remove_server(self, connection_id):
        server = next((server for server in self.servers if server.get('id') == connection_id), None)
        self.servers.remove(server)
        if server.get('is_master'):
            print("Master server is down! Promoting another server.")
            self.create_new_master()
        elif server.get('name'):
            self.nameserver.remove(server.get('name'))

    # To promote a slave, first the watcher removes the master from the list
    # Then updates the first slave server is_master value in the watcher list
    # Then, the watcher consults the name server to get the servers URIs
    # Then, the watcher calls the first slave server promote method, this updates the inner values of the object
    # At last, the watcher removes slave from the name server and re-register it in the name server as the master
    def create_new_master(self):
        self.nameserver.remove('server')
        server = next(iter(self.servers), None)
        if server:
            server['is_master'] = True
        servers = self.nameserver.list()
        for name, server_uri in servers.items():
            if 'server' in name:
                obj = Pyro4.Proxy(server_uri)
                obj.promote()
                self.nameserver.remove(name)
                self.nameserver.register('server', server_uri)
                print(f"Server {name} promoted to master.")
                return
        print('There are no other servers connected.')

    def list_servers(self):
        print("Server list: ")
        for server in self.servers:
            print(server)


daemon = Pyro4.Daemon()
watcher = Watcher()
uri = daemon.register(watcher)
watcher.nameserver.register('watcher', uri)
# This is where the watcher connection and disconnection methods are configured
daemon.validateHandshake = watcher.server_connected
daemon.clientDisconnect = watcher.server_disconnected
print("Watcher is starting.")
daemon.requestLoop()
