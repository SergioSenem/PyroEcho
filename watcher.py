import Pyro4


@Pyro4.expose
class Watcher:

    def __init__(self):
        self.nameserver = Pyro4.locateNS()
        self.servers = []

    def add_server_name(self, name):
        server = self.servers[-1]
        server['name'] = name
        self.list_servers()

    def server_connected(self, connection, data):
        try:
            connection_id = connection.__hash__()
            print(f"A server connected with id {connection_id}")
            self.add_server(connection_id)
        except Exception as e:
            print(e)
        return data

    def add_server(self, connection_id):
        is_master = len(self.servers) == 0
        server = {'id': connection_id, 'is_master': is_master}
        self.servers.append(server)

    def server_disconnected(self, connection):
        try:
            connection_id = connection.__hash__()
            print(f"Server with id {connection_id} disconnected.")
            self.remove_server(connection_id)
        except Exception as e:
            print(e)

    def remove_server(self, connection_id):
        server = next((server for server in self.servers if server.get('id') == connection_id), None)
        self.servers.remove(server)
        if server.get('is_master'):
            print("Master server is down! Promoting another server.")
            self.create_new_master()
        elif server.get('name'):
            self.nameserver.remove(server.get('name'))

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
daemon.validateHandshake = watcher.server_connected
daemon.clientDisconnect = watcher.server_disconnected
print("Watcher is starting.")
daemon.requestLoop()
