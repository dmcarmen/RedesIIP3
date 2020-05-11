import socket
import time
import queue
from PIL import Image, ImageTk
import numpy as np
import cv2
import threading


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
    #flag_webcam = None
    #video = None
    flag = 1

    # Constantes
    local_ip = "127.0.0.1"
    buffer_tam = 65536  # TODO no se que tam
    fps = 20
    resol = '640x480'

    def __init__(self, gui, ip, local_port, ext_port):
        self.gui = gui
        self.ext_ip = ip
        self.local_port = local_port
        self.ext_port = ext_port
        self.n_orden = 0
        self.buffer_circ = queue.PriorityQueue(self.fps * 2)  # fps*2secs
        #self.flag_webcam = flag_webcam
        #self.video = video

        self.socket_send = self.create_socket()

        self.socket_listen = self.create_socket()
        self.socket_listen.bind(('', local_port))

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

        # TODO ctrl errores de vuelta
        return s

    # Funciones para enviar mensajes
    def enviar_frame(self, frame):
        # Compresión JPG al 50% de resolución (se puede variar)
        encode_param = [cv2.IMWRITE_JPEG_QUALITY, 50]
        result, encimg = cv2.imencode('.jpg', frame, encode_param)
        if result == False:
            print('Error al codificar imagen')
        # encimg = encimg.tobytes()

        msg = '{}#{}#{}#{}#'.format(self.n_orden, time.time(), self.resol, self.fps)
        msg = msg.encode() + encimg.tostring()
        self.socket_send.sendto(msg,
                                (self.ext_ip, self.ext_port))  # TODO maybe to_bytes el frame jaj
        self.n_orden += 1


    # Funciones para recibir mensajes
    def listening(self):
        while not self.gui.end_event:  # TODO cuando acabar
            if not self.gui.pause_event:
                self.recibir_frame()

        self.socket_listen.close()
        self.socket_send.close()

    def recibir_frame(self):
        msg, ip = self.socket_listen.recvfrom(self.buffer_tam)

        msg = msg.split(b'#', 4)

        encimg = msg[4]
        # Descompresión de los datos, una vez recibidos
        decimg = cv2.imdecode(np.frombuffer(encimg, np.uint8), 1)

        # Conversión de formato para su uso en el GUI
        # TODO maybe frame = cv2.resize(decimg, (resW,resH)); cv2_im = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        cv2_im = cv2.cvtColor(decimg, cv2.COLOR_BGR2RGB)
        img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))

        d = {'ts': msg[1], 'resol': msg[2], 'fps': msg[3], 'img_tk': img_tk}
        self.buffer_circ.put((int(msg[0]), d))

    def reproducir(self):
        self.gui.app.showSubWindow("2")
        while not self.buffer_circ.full():
            continue
        while not self.gui.end_event:
            if not self.gui.pause_event:
                if self.buffer_circ.empty():
                    continue
                d = self.buffer_circ.get()[1]
                img_tk = d.get('img_tk')


                # TODO no va la subwindow
                self.gui.app.showSubWindow("2")
                #self.gui.app.setImageSize("2", 640, 480)
                self.gui.app.setImageData("El otro", img_tk, fmt='PhotoImage')
                #self.gui.app.setImageData("2", img_tk, fmt = 'PhotoImage')

        photo = ImageTk.PhotoImage(Image.open("imgs/webcam.gif"))
        self.gui.app.setImageData("El otro", photo , fmt='PhotoImage')
        self.gui.app.hideSubWindow("2")


    def tomadaca(self):
        thread_listen = threading.Thread(target=self.listening)
        thread_listen.start()

        thread_play = threading.Thread(target=self.reproducir)
        thread_play.start()
