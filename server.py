import Pyro4
import uuid


@Pyro4.expose
class Server:
    def __init__(self, name, is_master=False):
        self.name = name
        self.messages = []
        self.is_master = is_master

    # Exposed method used by the client and slave servers
    def get_messages(self):
        print("Listing messages: ", self.messages)
        return self.messages

    # Exposed method used by the client and the master server to add message
    def add_message(self, message):
        self.messages.append(message)
        print(f"Including message '{message}' in list.")
        self.replicate_message(message)

    # Exposed method used by the watcher to promote slave to master
    def promote(self):
        self.name = "server"
        self.is_master = True
        print("Promoted to master!")

    # Master unique method to replicate a client sent message to the slave servers
    def replicate_message(self, message):
        if self.is_master:
            try:
                nameserver = Pyro4.locateNS()
                # Get the list of servers, ignoring itself
                servers = get_servers(nameserver, self.name)
                for server in servers:
                    # Calls the server object and includes the message inside it's list
                    obj = Pyro4.Proxy(server.get('uri'))
                    print(f"Replicating message '{message}' to server {server}.")
                    obj.add_message(message)
            except Exception as e:
                print(e)


def get_servers(nameserver, ignore_name=None):
    names = nameserver.list()
    servers = []
    for key, value in names.items():
        if 'server' in key and (ignore_name is None or key != ignore_name):
            server = {'name': key, 'uri': value}
            servers.append(server)
    return servers


# Create and register server in name server, if there are no other servers connected, create it as master
def start_server(daemon, nameserver):
    servers = get_servers(nameserver)
    is_master = len(servers) == 0
    name = get_server_name(is_master)
    obj = Server(name, is_master)
    # If the server is not the master, import the messages list from the master
    if not is_master:
        import_master_server_messages(obj, servers)
    uri = daemon.register(obj)
    nameserver.register(name, uri)
    print_starting_server_message(is_master, name)
    return obj


def get_server_name(is_master):
    return 'server_' + str(uuid.uuid1()) if not is_master else 'server'


def import_master_server_messages(obj, servers):
    master = get_master_server(servers)
    master_obj = Pyro4.Proxy(master.get('uri'))
    obj.messages = master_obj.get_messages()


def print_starting_server_message(is_master, name):
    if is_master:
        print(f"Starting Server as master.")
    else:
        print(f"Starting Server with name {name} as slave.")


def get_master_server(servers):
    for server in servers:
        if server.get('name') == 'server':
            return server
    return None


def list_servers(nameserver):
    print("Server list:")
    servers = get_servers(nameserver)
    for server in servers:
        print(server)


# Start the server and create a connection with the watcher
# If this connection fails, the watcher will remove the server from the name server
d = Pyro4.Daemon()
ns = Pyro4.locateNS()
s = start_server(d, ns)
watcher_uri = ns.lookup('watcher')
watcher = Pyro4.Proxy(watcher_uri)
# For better management from the watcher, the server will send his name to the watcher
watcher.add_server_name(s.name)
list_servers(ns)
d.requestLoop()
