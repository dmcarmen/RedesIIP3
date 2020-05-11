import socket
import users
import video


class Control:
    # Info general
    video_client = None
    gui = None
    users_descubrimiento = None
    ip = None
    socketListen = None
    tcp_port = None
    udp_port = None
    v = None

    # TODO check if needed. tambien si necesitamos dst_ip aqui
    dst_udp_port = None
    dst_tcp_port = None

    # Constantes
    max_conexiones = 10

    # TODO errores al conectar/enviar
    # TODO what we are doing with protocols_dst
    # TODO servidor de descubrimiento
    def __init__(self, video_client, users_descubrimiento, ip, tcp_port, udp_port):
        self.video_client = video_client
        self.gui = video_client.app
        self.users_descubrimiento = users_descubrimiento
        self.ip = ip
        self.tcp_port = tcp_port
        self.udp_port = udp_port

        # Creamos el socket para recibir mensajes del resto de usuarios
        self.socketListen = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketListen.bind(("", tcp_port))
        self.socketListen.listen(self.max_conexiones)

    # TODO lo de estatico
    def send_msg(self, msg, dst_ip, dst_port):
        socket_send = socket.socket()
        socket_send.connect((dst_ip, dst_port))
        socket_send.send(bytes(msg,'utf-8'))
        socket_send.close()

    # Funciones que envian mensajes de control
    def calling(self, nick, dst_ip, dst_port):
        self.gui.setStatusbar("Llamando a {}...".format(nick), 0)
        msg = "CALLING {} {}".format(nick, self.udp_port)
        self.send_msg(msg, dst_ip, dst_port)

    def call_hold(self, nick, dst_ip, dst_port):
        msg = "CALL_HOLD {}".format(nick)
        self.send_msg(msg, dst_ip, dst_port)
        self.gui.setStatusbar("Llamada pausada.", 0)
        self.video_client.pause_event = True

    def call_resume(self, nick, dst_ip, dst_port):
        msg = "CALL_RESUME {}".format(nick)
        self.send_msg(msg, dst_ip, dst_port)
        self.gui.setStatusbar("En llamada.", 0)
        self.video_client.pause_event = False

    def call_end(self, nick, dst_ip, dst_port):
        msg = "CALL_END {}".format(nick)
        self.send_msg(msg, dst_ip, dst_port)
        self.gui.setStatusbar("Llamada finalizada.", 0)
        self.video_client.flag_en_llamada = False
        self.video_client.end_event = True
        self.v = None

    # Funciones para enviar mensajes de respuesta a CALLING
    def call_accepted(self, nick, dst_ip, dst_port):
        msg = "CALL_ACCEPTED {} {}".format(nick, self.udp_port)
        self.send_msg(msg, dst_ip, dst_port)

    def call_denied(self, nick, dst_ip, dst_port):
        msg = "CALL_DENIED {}".format(nick)
        self.send_msg(msg, dst_ip, dst_port)

    def call_busy(self, dst_ip, dst_port):
        msg = "CALL_BUSY"
        self.send_msg(msg, dst_ip, dst_port)

    # Funciones para realizar las acciones necesarias tras procesar mensaje
    def calling_handler(self, nick, dst_udp_port):

        user_info = self.users_descubrimiento.query(nick)
        dst_ip = user_info[1]
        dst_port = user_info[2]
        protocolos = user_info[3]  # TODO que hacer con protocolos

        if not self.video_client.flag_en_llamada:

            res = self.gui.yesNoBox("Llamada entrante", nick)
            if res:
                self.video_client.flag_en_llamada = True
                self.video_client.end_event = False

                self.call_accepted(self.video_client.nick, dst_ip, dst_port)
                self.dst_udp_port = dst_udp_port
                self.dst_tcp_port = dst_port
                self.gui.setStatusbar("En llamada.", 0)

                self.video_client.dst_ip = dst_ip
                self.video_client.dst_port = dst_port

                self.v = video.Video(self.video_client, dst_ip, int(self.udp_port), int(self.dst_udp_port))
                self.v.tomadaca()

                # TODO threads, video etc

            else:
                self.call_denied(nick, dst_ip, dst_port)

        else:
            self.call_busy(dst_ip, dst_port)

    def call_hold_handler(self, nick):
        if self.video_client.flag_en_llamada:
            self.gui.setStatusbar("Llamada pausada.", 0)
            self.video_client.pause_event = True

    def call_resume_handler(self, nick):
        if self.video_client.flag_en_llamada:
            self.gui.setStatusbar("En llamada.", 0)
            self.video_client.pause_event = False

    def call_end_handler(self, nick):
        if self.video_client.flag_en_llamada:
            self.dst_tcp_port = None
            self.dst_udp_port = None

            self.gui.setStatusbar("Llamada finalizada.", 0)
            self.video_client.flag_en_llamada = False
            self.video_client.end_event = True
            self.v = None

    def call_accepted_handler(self, nick, dst_udp_port):
        if not self.video_client.flag_en_llamada:
            user_info = self.users_descubrimiento.query(nick)
            dst_ip = user_info[1]
            self.dst_tcp_port = user_info[2]
            self.dst_udp_port = dst_udp_port
            self.video_client.flag_en_llamada = True
            self.video_client.end_event = False

            self.gui.infoBox("Informacinó de llamada", "{} ha aceptado tu llamada.".format(nick))
            self.gui.setStatusbar("En llamada.", 0)

            self.video_client.dst_ip = dst_ip
            self.video_client.dst_port = self.dst_tcp_port

            self.v = video.Video(self.video_client, dst_ip, int(self.udp_port), int(self.dst_udp_port))
            self.v.tomadaca()

            # TODO threads, video etc

    def call_denied_handler(self, nick):
        self.gui.infoBox("Información de llamada", "{} no ha aceptado tu llamada.".format(nick))
        self.gui.setStatusbar("", 0)

    def call_busy_handler(self):
        self.gui.infoBox("Información de llamada", "El usuario se encuentra en una llamada.")
        self.gui.setStatusbar("", 0)

    # Funciones para recibir y procesar peticiones
    def listening(self):
        while 1:  # TODO flag o similar para parar
            host, port = self.socketListen.accept()
            msg = host.recv(1024)

            if msg:
                msg = msg.decode('utf-8')
                print("Mensaje recibido:" + msg)
                self.procesar_peticion(msg)

    def procesar_peticion(self, msg):
        campos = msg.split(" ")
        comando = campos[0]

        # TODO maybe check resto de parametros?
        if comando == "CALLING":
            self.calling_handler(campos[1], campos[2])

        elif comando == "CALL_HOLD":
            self.call_hold_handler(campos[1])

        elif comando == "CALL_RESUME":
            self.call_resume_handler(campos[1])

        elif comando == "CALL_END":
            self.call_end_handler(campos[1])

        elif comando == "CALL_ACCEPTED":
            self.call_accepted_handler(campos[1], campos[2])

        elif comando == "CALL_DENIED":
            self.call_denied_handler(campos[1])

        elif comando == "CALL_BUSY":
            self.call_busy_handler()
        else:
            print("Mensaje incorrecto")  # TODO que hacer cuando mensaje distino
