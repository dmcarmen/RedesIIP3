from appJar import gui
from PIL import Image, ImageTk
import cv2
import users
import control
import threading
import os.path


class VideoClient(object):
    # Onjetos de cada clase
    descubrimiento = None
    control = None
    video = None

    # Informacion del usuario
    nick = None  # "usuario2" #"usuario1"
    ip_address = None # "127.0.0.1"
    tcp_port = None  # 49154 #49152
    udp_port = None #49153  # 49155
    password = None
    protocols = None # 'V0'

    # Informacion del destino
    dst_ip = None
    dst_port = None

    # Lista de usuarios del DS
    d_users = None

    # Flags para saber si en llamada o en pausa
    flag_en_llamada = False
    flag_pause = False

    # Resolucion
    resol = None

    def __init__(self, window_size):
        """
            Nombre: __init__
            Descripcion: Constructor de la clase.
            Argumentos:
                -window_size: tamaño de la ventana
            Retorno: objecto VideoClient
        """

        # Creamos una variable que contenga el GUI principal
        self.app = gui("Redes2 - P2P", window_size)
        self.app.setGuiPadding(10)

        # Preparacion del interfaz
        self.app.addLabel("title", "Cliente Multimedia P2P - Redes2 ")
        self.app.addImage("video", "imgs/webcam.gif")

        # La ventana del video de la llamada
        self.app.startSubWindow("Llamada")
        self.app.addImage("Llamada", "imgs/webcam.gif")
        self.app.stopSubWindow()
        self.app.hideSubWindow("Llamada")

        # Añadir los botones y escondemos los botones que todavía no se pueden utilizar
        self.app.addButtons(["Elegir fuente","Iniciar sesión", "Mostrar usuarios", "Conectar", "Pausar/Reanudar", "Colgar", "Salir"], self.buttonsCallback)
        self.app.hideButton("Iniciar sesión")
        self.app.hideButton("Mostrar usuarios")
        self.app.hideButton("Conectar")
        self.app.hideButton("Pausar/Reanudar")
        self.app.hideButton("Colgar")

        # Barra de estado
        # Debe actualizarse con informacion util sobre la llamada (duracion, FPS, etc...)
        self.app.addStatusbar(fields=2)

        self.resol = '640x480'  # empezamos con la máxima resolución por defecto

        # Creamos la clase de conexión con el servidor de descubrimiento
        self.descubrimiento = users.UsersDescubrimiento()

    def start(self):
        """
            Nombre: start
            Descripcion: Funcion que inicializa la app.
            Argumentos: Ninguno
            Retorno: Ninguno
        """
        self.app.go()

    def capturaVideo(self):
        """
            Nombre: capturaVideo
            Descripcion: Funcion que captura el frame a mostrar en cada momento.
            Argumentos: Ninguno
            Retorno: Ninguno
        """
        # Capturamos un frame de la camara o del video
        ret, frame = self.cap.read()
        if ret is True:
            try:
                frame_ver = cv2.resize(frame, (640, 480))
                cv2_im = cv2.cvtColor(frame_ver, cv2.COLOR_BGR2RGB)
                img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))
                # Lo mostramos en el GUI
                self.app.setImageData("video", img_tk, fmt='PhotoImage')
            except:
                pass
            # Si estamos enviando video, enviamos el frame
            if self.video is not None and not self.flag_pause:
                self.video.enviar_frame(frame)
        # Si estamos reproduciendo un video y ya ha acabado, mostramos
        # y enviamos la foto inicial
        else:
            frame = cv2.imread("imgs/webcam.jpeg")
            photo = ImageTk.PhotoImage(Image.open("imgs/webcam.jpeg"))
            self.app.setImageData("video", photo, fmt='PhotoImage')

            if self.video is not None and not self.flag_pause:
                self.video.enviar_frame(frame)

    def setImageResolution(self, resolution):
        """
            Nombre: setImageResolution
            Descripcion: Funcion que establece la resolucion de la imagen capturada.
            Argumentos:
                -resolution: resolucion de la imagen
            Retorno: Ninguno
        """
        # Se establece la resolucion de captura de la webcam
        # Puede añadirse algun valor superior si la camara lo permite
        # pero no modificar estos
        if resolution == "LOW" and self.resol != "160x120":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
            self.resol = "160x120"
        elif resolution == "MEDIUM" and self.resol != "320x240":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            self.resol = "320x240"
        elif resolution == "HIGH" and self.resol != "640x480":
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.resol = "640x480"

    def buttonsCallback(self, button):
        """
            Nombre: buttonsCallback
            Descripcion: Funcion que gestiona los callbacks de los botones.
            Argumentos:
                -button: boton pulsado
            Retorno: Ninguno
        """

        if button == "Salir":
            # Salimos de la aplicacion
            self.descubrimiento.quit()
            self.app.stop()
        elif button == "Conectar":
            # Llamamos al usuario si no estamos en llamada
            if not self.flag_en_llamada:
                # Entrada del nick del usuario a conectar
                nick = self.app.textBox("Conexión",
                                        "Introduce el nick del usuario a buscar")
                # Evitamos llamarnos a nosotros mismos
                if nick != self.nick:
                    info = self.descubrimiento.query(nick)
                    self.dst_ip = info[1]
                    self.dst_port = info[2]
                    self.control.calling(nick, info[1], info[2])
            else:
                self.app.warningBox("En llamada", "Ya estás en llamada.")

        elif button == "Colgar":
            # Si nos encontramos en llamada, se finaliza
            if self.flag_en_llamada:
                self.control.call_end(self.nick, self.dst_ip, self.dst_port)
                self.dst_ip = None
                self.dst_port = None

        elif button == "Pausar/Reanudar":
            # Se comprueba que nos encontramos en llamada
            if self.flag_en_llamada:
                # Si esta en pausa, se reanuda la llamada
                if self.flag_pause:
                    self.control.call_resume(self.nick, self.dst_ip, self.dst_port)
                # Si no, se pausa la llamada
                else:
                    self.control.call_hold(self.nick, self.dst_ip, self.dst_port)

        elif button == "Iniciar sesión":
            # Creamos una nueva ventana para introducir los datos
            self.app.startSubWindow("Inicio de sesión")

            # Campos a rellenar para iniciar sesión
            self.app.addLabelEntry("Nick:")
            self.app.addLabelSecretEntry("Contraseña:")
            self.app.addLabelEntry("Dirección IP:")
            self.app.addLabelEntry("Puerto TCP:")
            self.app.addLabelEntry("Puerto UDP:")

            # Añadimos el botón para enviar los datos
            self.app.addButtons(["Iniciar"], self.buttonsCallback)
            self.app.showSubWindow("Inicio de sesión")
            self.app.stopSubWindow()

        elif button == "Iniciar":
            # Cogemos los datos introducidos
            nick = self.app.getEntry("Nick:")
            password = self.app.getEntry("Contraseña:")
            ip_address = self.app.getEntry("Dirección IP:")
            tcp_port = self.app.getEntry("Puerto TCP:")
            udp_port = self.app.getEntry("Puerto UDP:")
            protocols = "V0"

            # Si falta alguno pedimos que los rellene
            if not nick or not password or not ip_address or not tcp_port or not udp_port:
                self.app.warningBox("Error en parámetros", "Rellena todos los campos.")

            else:
                # Registramos al usuario en el DS
                msg = self.descubrimiento.register(nick, ip_address, tcp_port, password, protocols)
                if msg == 'NOK WRONG_PASS':
                    self.app.warningBox("Contraseña incorrecta", "Intenta iniciar sesión de nuevo.")
                # Si es correcto guardamos los datos y enseñamos los botones siguientes
                elif msg.split(' ')[0] == 'OK':
                    self.nick = nick
                    self.password = password
                    self.ip_address = ip_address
                    self.tcp_port = int(tcp_port)
                    self.protocols = protocols
                    self.udp_port = udp_port

                    self.app.hideSubWindow("Inicio de sesión")
                    self.app.hideButton("Iniciar sesión")

                    self.app.showButton("Colgar")
                    self.app.showButton("Mostrar usuarios")
                    self.app.showButton("Conectar")
                    self.app.showButton("Pausar/Reanudar")

                    # Creamos el objeto de control
                    self.control = control.Control(self, self.descubrimiento, self.tcp_port, self.udp_port)
                    # Creamos el hilo para escuchar los comandos de control
                    thread = threading.Thread(target=self.control.listening)
                    thread.daemon = True
                    thread.start()

        elif button == "Mostrar usuarios":
            # Obtenemos la lista de usuarios y la mostramos en una nueva ventana
            self.d_users = self.descubrimiento.list_users()

            self.app.startSubWindow("Usuarios")
            self.app.addListBox('lista', self.d_users.keys())

            self.app.addButton("Llamar", self.buttonsCallback)

            self.app.showSubWindow("Usuarios")
            self.app.stopSubWindow()

        elif button == "Llamar":
            # Si no estamos en llamada, llamamos al user marcado
            if not self.flag_en_llamada:
                nick = self.app.getListBox('lista')[0]
                d = self.d_users[nick]
                self.control.calling(nick, d['ip'], int(d['puerto']))
            else:
                self.app.warningBox("En llamada", "Ya estás en llamada.")

        elif button == "Elegir fuente":
            # Abrimos una nueva ventana para elegir si cogemos un vídeo o nuestra cámara
            self.app.startSubWindow("Fuente video")
            self.app.addLabelEntry("Path:")
            self.app.addButtons(["Cámara", "Archivo"], self.buttonsCallback)
            self.app.showSubWindow("Fuente video")
            self.app.stopSubWindow()

        elif button == "Cámara":
            # Registramos la funcion de captura de video a la cámara
            self.cap = cv2.VideoCapture(0)
            self.app.setPollTime(20)
            self.app.registerEvent(self.capturaVideo)
            self.app.hideSubWindow("Fuente video")
            self.app.hideButton("Elegir fuente")
            self.app.showButton("Iniciar sesión")

        elif button == "Archivo":
            # Registramos la funcion de captura de video al video
            path = self.app.getEntry("Path:")
            # Comprobamos que exista
            if os.path.isfile(path):
                self.cap = cv2.VideoCapture(path)
                self.app.setPollTime(20)
                self.app.registerEvent(self.capturaVideo)
                self.app.hideSubWindow("Fuente video")
                self.app.hideButton("Elegir fuente")
                self.app.showButton("Iniciar sesión")
            else:
                self.app.warningBox("Path incorrecto", "El archivo no existe.")

if __name__ == '__main__':
    vc = VideoClient("640x520")

    # Lanza el bucle principal del GUI
    vc.start()
