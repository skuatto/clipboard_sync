import socket
import threading
import pyperclip
import time
import tkinter as tk
from tkinter import messagebox

# ⚠️ CAMBIA ESTA IP por la del otro PC
REMOTE_PC_IP = "192.168.1.20"
PORT = 65432

last_clipboard = ""
running = True

def send_clipboard_to_remote(text):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((REMOTE_PC_IP, PORT))
            s.sendall(text.encode("utf-8"))
    except Exception as e:
        print("❌ Error enviando al otro PC:", e)

def clipboard_monitor():
    global last_clipboard, running
    while running:
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

def start_gui():
    def on_close():
        global running
        running = False
        root.destroy()

    root = tk.Tk()
    root.title("Clipboard Sync")
    root.geometry("220x90")
    root.resizable(False, False)
    tk.Label(root, text="Sync activado 🟢", font=("Arial", 12)).pack(pady=10)
    tk.Button(root, text="Cerrar", command=on_close).pack()
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

# Inicia los hilos
threading.Thread(target=clipboard_monitor, daemon=True).start()
threading.Thread(target=start_server, daemon=True).start()
start_gui()
