import socket
import time
import queue

class Video:
    # Info general
    gui = None
    ext_ip = None
    socket_send = None
    socket_listen = None
    local_port = None
    ext_port = None
    n_orden = None
    buffer_circ = None

    # Constantes
    local_ip = "127.0.0.1"
    buffer_tam = 2048 #TODO no se que tam
    fps = 20
    resol = '640x480'

    def __init__(self, gui, ip, local_port, ext_port):
        self.gui = gui
        self.ext_ip = ip
        self.local_port = local_port
        self.ext_port = ext_port
        self.n_orden = 0
        self.buffer_circ = queue.PriorityQueue(self.fps*2) #fps*2secs

        self.socket_send = self.create_socket()
        self.socket_send.bind((ip, ext_port))

        self.socket_listen = self.create_socket()

    def create_socket(self):
        """
            Nombre: create_listen_socket
            Descripcion: Funcion
            Argumentos:
            Retorno:
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print("Socket UDP para enviar creado")
        except socket.error as err:
            print("La creación del socket UDP para enviar falló: error {}".format(err))
            return None

        #TODO ctrl errores de vuelta
        return s

    # Funciones para enviar mensajes
    def enviar_frame(self, frame):
		# Compresión JPG al 50% de resolución (se puede variar)
		encode_param = [cv2.IMWRITE_JPEG_QUALITY,50]
		result,encimg = cv2.imencode('.jpg', frame, encode_param)
		if result == False:
			print('Error al codificar imagen')
		#encimg = encimg.tobytes()

        msg = '{}#{}#{}#{}#'.format(self.n_orden, time.time(), self.resol, self.fps)
        self.socket_send.sendto(bytes(msg+encimg, 'utf-8'), (self.ext_ip, self.ext_port_udp)) #TODO maybe to_bytes el frame jaj
        self.n_orden += 1

    # Funciones para recibir mensajes
    def listening(self):
        while 1:  # TODO cuando acabar
            self.recibir_frame()

    def recibir_frame(self):
        msg = self.socket_listen.recvfrom(buffer_tam)
        msg = msg.split(b'#', 4)

        encimg = msg[4]

        # Descompresión de los datos, una vez recibidos
        decimg = cv2.imdecode(np.frombuffer(encimg,np.uint8), 1)

        # Conversión de formato para su uso en el GUI
        # TODO maybe frame = cv2.resize(decimg, (resW,resH)); cv2_im = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        cv2_im = cv2.cvtColor(decimg,cv2.COLOR_BGR2RGB)
        img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))

        d = {'ts':msg[1], 'resol':msg[2], 'fps':msg[3], 'img_tk':img_tk}
        self.buffer_circ.put(int(msg[0]), d)

    def reproducir(self):
        while not self.buffer_circ.full():
            continue
        while 1:
            if self.buffer_circ.empty():
                continue
            d = self.buffer_circ.get()
            img_tk = d['img_tk']
            # TODO gui
