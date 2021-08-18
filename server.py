import Pyro4
import uuid


@Pyro4.expose
class Server:
    def __init__(self, name, is_master=False):
        self.name = name
        self.messages = []
        self.is_master = is_master

    def get_messages(self):
        print("Listing messages: ", self.messages)
        return self.messages

    def add_message(self, message):
        self.messages.append(message)
        print(f"Including message '{message}' in list.")
        self.replicate_message(message)

    def promote(self):
        self.name = "server"
        self.is_master = True
        print("Promoted the master!")

    def replicate_message(self, message):
        if self.is_master:
            try:
                nameserver = Pyro4.locateNS()
                servers = get_servers(nameserver, self.name)
                for server in servers:
                    obj = Pyro4.Proxy(server.get('uri'))
                    print(f"Replicating message '{message}' to server {server}.")
                    obj.add_message(message)
            except Exception as e:
                print(e)


def start_server(daemon, nameserver):
    servers = get_servers(nameserver)
    index = len(servers)
    is_master = index == 0
    name = 'server_' + str(uuid.uuid1()) if not is_master else 'server'
    obj = Server(name, is_master)
    if not is_master:
        master = get_master_server(servers)
        master_obj = Pyro4.Proxy(master.get('uri'))
        obj.messages = master_obj.get_messages()
    uri = daemon.register(obj)
    nameserver.register(name, uri)
    if is_master:
        print(f"Starting Server as master.")
    else:
        print(f"Starting Server with name {name} as slave.")
    return obj


def get_servers(nameserver, ignore_name=None):
    names = nameserver.list()
    servers = []
    for key, value in names.items():
        if 'server' in key and (ignore_name is None or key != ignore_name):
            server = {'name': key, 'uri': value}
            servers.append(server)
    return servers


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


d = Pyro4.Daemon()
ns = Pyro4.locateNS()
s = start_server(d, ns)
watcher_uri = ns.lookup('watcher')
watcher = Pyro4.Proxy(watcher_uri)
watcher.add_server_name(s.name)
list_servers(ns)
d.requestLoop()
