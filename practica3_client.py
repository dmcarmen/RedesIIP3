# import the library
from appJar import gui
from PIL import Image, ImageTk
import numpy as np
import cv2
import users
import control
import video
import threading


class VideoClient(object):
	##############################################
	descubrimiento = None
	control = None

	nick = "usuario1" # "usuario2"
	ip_address = "127.0.0.1"
	tcp_port = 49152 # 49154
	udp_port = 49153 # 49155
	password = "kk"
	protocols = "V0"

	dst_ip = None
	dst_port = None

	flag_en_llamada = False
	end_event = False
	pause_event = False

	resol = None

	##############################################
	def __init__(self, window_size):

		# Creamos una variable que contenga el GUI principal
		self.app = gui("Redes2 - P2P", window_size)
		self.app.setGuiPadding(10)

		# Preparación del interfaz
		self.app.addLabel("title", "Cliente Multimedia P2P - Redes2 ")
		self.app.addImage("video", "imgs/webcam.gif")

		# Registramos la función de captura de video
		# Esta misma función también sirve para enviar un vídeo
		self.cap = cv2.VideoCapture(0)
		self.app.setPollTime(20)
		self.app.registerEvent(self.capturaVideo)


		# La ventana del otro video
		self.app.startSubWindow("2")
		self.app.addImage("El otro", "imgs/webcam.gif")
		self.app.stopSubWindow()
		self.app.hideSubWindow("2")

		# Añadir los botones
		self.app.addButtons(["Conectar", "Pausar/Reanudar", "Colgar", "Salir"], self.buttonsCallback)

		# Barra de estado
		# Debe actualizarse con información útil sobre la llamada (duración, FPS, etc...)
		self.app.addStatusbar(fields=2)

		self.resol = '640x480' #empezamos con la máxima por defecto

		############################################
		self.descubrimiento = users.Users_descubrimiento()
		self.descubrimiento.register(self.nick, self.ip_address, self.tcp_port, self.password, self.protocols)
		self.control = control.Control(self, self.descubrimiento, self.ip_address, self.tcp_port, self.udp_port)
		thread = threading.Thread(target=self.control.listening)
		thread.start()

	#############################################

	def start(self):
		self.app.go()

	# Función que captura el frame a mostrar en cada momento
	def capturaVideo(self):

		# Capturamos un frame de la cámara o del vídeo
		ret, frame = self.cap.read()
		if ret is True:
			try:
				frame_ver = cv2.resize(frame, (640, 480))
				cv2_im = cv2.cvtColor(frame_ver, cv2.COLOR_BGR2RGB)
				img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))
				# Lo mostramos en el GUI
				self.app.setImageData("video", img_tk, fmt='PhotoImage')
			except Exception:
				pass
			if self.control.v is not None:
				self.control.v.enviar_frame(frame)
		else:
			frame = cv2.imread("imgs/webcam.jpeg")
			photo = ImageTk.PhotoImage(Image.open("imgs/webcam.jpeg"))
			self.app.setImageData("video", photo, fmt='PhotoImage')

			if self.control.v is not None:
				self.control.v.enviar_frame(frame)
		# Los datos "encimg" ya están listos para su envío por la red
		# enviar(encimg)

	# Establece la resolución de la imagen capturada
	def setImageResolution(self, resolution):
		# Se establece la resolución de captura de la webcam
		# Puede añadirse algún valor superior si la cámara lo permite
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

	# Función que gestiona los callbacks de los botones
	def buttonsCallback(self, button):

		if button == "Salir":
			# Salimos de la aplicación
			self.app.stop()
		elif button == "Conectar":
			# Entrada del nick del usuario a conectar
			nick = self.app.textBox("Conexión",
									"Introduce el nick del usuario a buscar")
			info = self.descubrimiento.query(nick)
			self.dst_ip = info[1]
			self.dst_port = info[2]
			self.control.calling(self.nick, info[1], info[2])

		elif button == "Colgar":
			if self.flag_en_llamada:
				self.control.call_end(self.nick,self.dst_ip, self.dst_port)
				self.dst_ip = None
				self.dst_port = None
		elif button == "Pausar/Reanudar":
			if self.flag_en_llamada:
				if self.pause_event:
					self.control.call_resume(self.nick,self.dst_ip, self.dst_port)
				else:
					self.control.call_hold(self.nick, self.dst_ip, self.dst_port)


if __name__ == '__main__':
	vc = VideoClient("640x520")

	# Crear aquí los threads de lectura, de recepción y,
	# en general, todo el código de inicialización que sea necesario
	# ...

	# Lanza el bucle principal del GUI
	# El control ya NO vuelve de esta función, por lo que todas las
	# acciones deberán ser gestionadas desde callbacks y threads
	vc.start()
