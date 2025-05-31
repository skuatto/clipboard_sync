
import socket
import threading
import pyperclip
import time
import tkinter as tk
from tkinter import simpledialog
import os
import json
import pystray
from pystray import MenuItem as item
from PIL import Image

CONFIG_FILE = "clipboard_sync_config.json"
DEFAULT_PORT = 65432
last_clipboard = ""
running = True
monitoring = True
REMOTE_PC_IP = "127.0.0.1"
PORT = DEFAULT_PORT
root = None

def load_config():
    global REMOTE_PC_IP, PORT
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            REMOTE_PC_IP = config.get("ip", REMOTE_PC_IP)
            PORT = config.get("port", PORT)

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump({"ip": REMOTE_PC_IP, "port": PORT}, f)

def send_clipboard_to_remote(text):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((REMOTE_PC_IP, PORT))
            s.sendall(text.encode("utf-8"))
    except Exception as e:
        print("❌ Error enviando al otro PC:", e)

def clipboard_monitor():
    global last_clipboard, running, monitoring
    while running:
        if monitoring:
            try:
                current = pyperclip.paste()
                if current != last_clipboard:
                    last_clipboard = current
                    send_clipboard_to_remote(current)
            except Exception as e:
                print("❌ Error monitorizando clipboard:", e)
        time.sleep(0.5)

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", PORT))
        s.listen()
        while running:
            try:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(8192)
                    if data:
                        text = data.decode("utf-8")
                        pyperclip.copy(text)
                        print(f"📥 Código recibido de {addr[0]}")
            except Exception as e:
                print("❌ Error en el servidor:", e)

def show_window():
    global root
    if root is not None:
        root.deiconify()

def hide_window():
    global root
    if root is not None:
        root.withdraw()

def on_quit(icon, item):
    global running
    running = False
    icon.stop()
    if root:
        root.quit()

def toggle_monitoring(icon, item):
    global monitoring
    monitoring = not monitoring

def change_ip(icon, item):
    global REMOTE_PC_IP
    ip = simpledialog.askstring("Configurar IP", "Introduce la IP del otro PC:", initialvalue=REMOTE_PC_IP)
    if ip:
        REMOTE_PC_IP = ip
        save_config()

def setup_systray():
    icon_image = Image.open("clipboard_sync_icon.ico")
    menu = (
        item("Mostrar ventana", lambda icon, item: show_window()),
        item("Activar/Desactivar", toggle_monitoring),
        item("Cambiar IP", change_ip),
        item("Salir", on_quit)
    )
    tray_icon = pystray.Icon("ClipboardSync", icon_image, "Clipboard Sync", menu)
    tray_icon.run()

def start_gui():
    global root
    root = tk.Tk()
    root.title("Clipboard Sync")
    root.geometry("250x100")
    root.resizable(False, False)
    root.withdraw()

load_config()
threading.Thread(target=clipboard_monitor, daemon=True).start()
threading.Thread(target=start_server, daemon=True).start()
threading.Thread(target=setup_systray, daemon=True).start()
start_gui()
