import socket


class Control:
    # Info general
    gui = None
    ip = None
    socketListen = None
    port_tcp = None
    port_udp = None

    # Constantes
    max_conexiones = 10

    # TODO portUDP al inicializar
    # TODO errores al conectar/enviar
    # TODO what we are doing with protocols_dest
    def __init__(self, gui, ip, port_tcp, port_udp):
        self.gui = gui
        self.ip = ip
        self.port_tcp = port_tcp
        self.port_udp = port_udp

        # Creamos el socket para recibir mensajes del resto de usuarios
        self.socketListen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketListen.bind(("", port_tcp))
        self.socketListen.listen(self.max_conexiones)

    # TODO lo de estatico
    def send_msg(self, msg, ip_dest, port_dst):
        socket_send = socket.socket()
        socket_send.connect((ip_dest, port_dst))
        socket_send.send(msg)
        socket_send.close()

    # Funciones que envian mensajes de control
    def calling(self, nick, ip_dest, port_dst):
        msg = "CALLING {} {}".format(nick, self.port_udp)
        self.send_msg(msg, ip_dest, port_dst)

    def call_hold(self, nick, ip_dest, port_dst):
        msg = "CALL_HOLD {}".format(nick)
        self.send_msg(msg, ip_dest, port_dst)

    def call_resume(self, nick, ip_dest, port_dst):
        msg = "CALL_RESUME {}".format(nick)
        self.send_msg(msg, ip_dest, port_dst)

    def call_end(self, nick, ip_dest, port_dst):
        msg = "CALL_END {}".format(nick)
        self.send_msg(msg, ip_dest, port_dst)

    # Funciones para recibir mensajes
    def listening(self):
        while 1:  # TODO cuando acabar
            host, port = self.socketListen.accept()
            msg = host.recv(1024)

            if msg:
                print("Mensaje recibido:" + msg.decode('utf-8'))  # TODO que hacer
