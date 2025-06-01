
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
tray_icon = None
status_label = None

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
        root.after(0, root.deiconify)

def hide_window():
    global root
    if root is not None:
        root.after(0, root.withdraw)

def update_status_label():
    global status_label
    if status_label:
        status_label.config(text="Estado: 🟢 Activo" if monitoring else "Estado: 🔴 Inactivo")

def on_quit(icon, item):
    global running
    running = False
    if root:
        root.quit()
    icon.stop()

def toggle_monitoring_action():
    global monitoring
    monitoring = not monitoring
    update_status_label()

def toggle_monitoring(icon, item):
    toggle_monitoring_action()

def change_ip(icon, item):
    if root:
        def prompt():
            global REMOTE_PC_IP
            ip = simpledialog.askstring("Configurar IP", "Introduce la IP del otro PC:", initialvalue=REMOTE_PC_IP)
            if ip:
                REMOTE_PC_IP = ip
                save_config()
        root.after(0, prompt)

def setup_systray():
    global tray_icon
    try:
        icon_path = os.path.join(os.path.abspath("."), "clipboard_sync_icon.ico")
        image = Image.open(icon_path)
    except:
        image = Image.new("RGB", (64, 64), "gray")

    menu = (
        item("Mostrar ventana", lambda icon, item: show_window()),
        item("Activar/Desactivar", toggle_monitoring),
        item("Cambiar IP", change_ip),
        item("Salir", on_quit)
    )
    tray_icon = pystray.Icon("ClipboardSync", image, "Clipboard Sync", menu)
    tray_icon.run()

def start_gui():
    global root, status_label
    root = tk.Tk()
    root.title("Clipboard Sync")
    root.geometry("280x140")
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", lambda: root.withdraw())

    status_label = tk.Label(root, text="", font=("Arial", 11))
    status_label.pack(pady=10)

    toggle_btn = tk.Button(root, text="Activar/Desactivar", command=toggle_monitoring_action)
    toggle_btn.pack(pady=5)

    ip_btn = tk.Button(root, text="Cambiar IP", command=lambda: change_ip(None, None))
    ip_btn.pack(pady=5)

    update_status_label()
    root.withdraw()
    root.mainloop()

load_config()
threading.Thread(target=clipboard_monitor, daemon=True).start()
threading.Thread(target=start_server, daemon=True).start()
threading.Thread(target=setup_systray, daemon=True).start()
start_gui()
