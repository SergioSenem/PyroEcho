import Pyro4


class Client:

    def __init__(self):
        self.nameserver = Pyro4.locateNS()

    def get_messages(self):
        server = self.get_server()
        return server.get_messages()

    def echo(self, message):
        server = self.get_server()
        server.add_message(message)

    def get_server(self):
        uri = self.nameserver.lookup('server')
        return Pyro4.Proxy(uri)


def menu(client):
    print("Welcome to Pyro Echo!")
    print("1 - Send a message")
    print("2 - Get messages")
    print("3 - Exit")

    mode = input("Mode: ")
    while mode != '3':
        if mode == '1':
            send_message_mode(client)
            mode = input("Mode: ")
        elif mode == '2':
            get_messages(client)
            mode = input("Mode: ")
        else:
            mode = input("Ops! That's not an option, try again: ")


def send_message_mode(client):
    message = input("Type a message: ")
    while message != "exit":
        client.echo(message)
        message = input("Type another message or type 'exit' to exit: ")


def get_messages(client):
    print("Messages sent:")
    messages = client.get_messages()
    for message in messages:
        print(message)


cli = Client()
menu(cli)
