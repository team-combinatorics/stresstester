from msl.loadlib import Client64


class Client(Client64):

    def __init__(self):
        # pass the server file we just created in module32=, the host am using is localhost, leave port as none for self assigning
        super(Client, self).__init__(module32='server', host="127.0.0.1", port=None)

    # define a function that calls the an existing server function and passes the args
    def hwinfo(self) -> bytes:
        return self.request32('hwinfo')
