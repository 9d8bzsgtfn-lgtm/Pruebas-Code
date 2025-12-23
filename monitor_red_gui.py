import tkinter as tk
from tkinter import ttk
import threading
import time
from pythonping import ping

# --- CONFIGURACIÓN ---
ROUTER_IP = "192.168.1.1"
INTERNET_IP = "8.8.8.8"
INTERVALO = 2
UMBRAL_LATENCIA = 100


class MonitorRedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Red")
        self.root.geometry("450x350")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        self.running = False
        self.thread = None

        self.crear_interfaz()

    def crear_interfaz(self):
        # Título
        titulo = tk.Label(
            self.root,
            text="🌐 Monitor de Red en Tiempo Real",
            font=("Arial", 16, "bold"),
            bg="#1e1e2e",
            fg="#89b4fa"
        )
        titulo.pack(pady=15)

        # Frame para el router
        frame_router = tk.Frame(self.root, bg="#313244", padx=20, pady=15)
        frame_router.pack(fill="x", padx=20, pady=5)

        tk.Label(
            frame_router,
            text=f"Router Local ({ROUTER_IP})",
            font=("Arial", 11),
            bg="#313244",
            fg="#cdd6f4"
        ).pack(anchor="w")

        self.label_router = tk.Label(
            frame_router,
            text="-- ms",
            font=("Arial", 24, "bold"),
            bg="#313244",
            fg="#6c7086"
        )
        self.label_router.pack(anchor="w")

        # Frame para internet
        frame_internet = tk.Frame(self.root, bg="#313244", padx=20, pady=15)
        frame_internet.pack(fill="x", padx=20, pady=5)

        tk.Label(
            frame_internet,
            text=f"Internet ({INTERNET_IP})",
            font=("Arial", 11),
            bg="#313244",
            fg="#cdd6f4"
        ).pack(anchor="w")

        self.label_internet = tk.Label(
            frame_internet,
            text="-- ms",
            font=("Arial", 24, "bold"),
            bg="#313244",
            fg="#6c7086"
        )
        self.label_internet.pack(anchor="w")

        # Frame diagnóstico
        frame_diag = tk.Frame(self.root, bg="#1e1e2e")
        frame_diag.pack(fill="x", padx=20, pady=10)

        self.label_diagnostico = tk.Label(
            frame_diag,
            text="Presiona Iniciar para comenzar",
            font=("Arial", 10),
            bg="#1e1e2e",
            fg="#a6adc8",
            wraplength=400
        )
        self.label_diagnostico.pack()

        # Botones
        frame_botones = tk.Frame(self.root, bg="#1e1e2e")
        frame_botones.pack(pady=15)

        self.btn_iniciar = tk.Button(
            frame_botones,
            text="▶ Iniciar",
            font=("Arial", 11),
            bg="#a6e3a1",
            fg="#1e1e2e",
            width=12,
            command=self.iniciar_monitor
        )
        self.btn_iniciar.pack(side="left", padx=5)

        self.btn_detener = tk.Button(
            frame_botones,
            text="⏹ Detener",
            font=("Arial", 11),
            bg="#f38ba8",
            fg="#1e1e2e",
            width=12,
            command=self.detener_monitor,
            state="disabled"
        )
        self.btn_detener.pack(side="left", padx=5)

    def realizar_ping(self, target):
        try:
            response = ping(target, count=2, timeout=1)
            if response.success():
                return round(response.rtt_avg_ms, 2)
            return None
        except Exception:
            return None

    def actualizar_label(self, label, valor, umbral_bueno=20):
        if valor is not None:
            if valor < umbral_bueno:
                color = "#a6e3a1"  # Verde
            elif valor < UMBRAL_LATENCIA:
                color = "#f9e2af"  # Amarillo
            else:
                color = "#fab387"  # Naranja
            label.config(text=f"{valor} ms", fg=color)
        else:
            label.config(text="SIN CONEXIÓN", fg="#f38ba8")

    def diagnosticar(self, local_ms, web_ms):
        if local_ms is None:
            return ("⚠️ CRÍTICO: No hay conexión al router. "
                    "Revisa el cable Ethernet o la señal WiFi.", "#f38ba8")
        elif web_ms is None:
            return ("⚠️ PROBLEMA ISP: El router responde pero no hay internet. "
                    "Contacta a tu proveedor.", "#f9e2af")
        elif web_ms > UMBRAL_LATENCIA and local_ms < 10:
            return ("⚡ SATURACIÓN: Tu red local está bien, "
                    "pero la conexión externa va lenta.", "#cba6f7")
        elif local_ms > 50:
            return ("📶 INTERFERENCIA: El router tarda en responder. "
                    "Posible congestión WiFi.", "#f9e2af")
        else:
            return ("✅ Conexión estable", "#a6e3a1")

    def loop_monitoreo(self):
        while self.running:
            lat_local = self.realizar_ping(ROUTER_IP)
            lat_web = self.realizar_ping(INTERNET_IP)

            # Actualizar UI desde el hilo principal
            self.root.after(0, self.actualizar_label, self.label_router, lat_local, 20)
            self.root.after(0, self.actualizar_label, self.label_internet, lat_web, 50)

            diag_texto, diag_color = self.diagnosticar(lat_local, lat_web)
            self.root.after(0, lambda t=diag_texto, c=diag_color:
                           self.label_diagnostico.config(text=t, fg=c))

            time.sleep(INTERVALO)

    def iniciar_monitor(self):
        self.running = True
        self.btn_iniciar.config(state="disabled")
        self.btn_detener.config(state="normal")
        self.thread = threading.Thread(target=self.loop_monitoreo, daemon=True)
        self.thread.start()

    def detener_monitor(self):
        self.running = False
        self.btn_iniciar.config(state="normal")
        self.btn_detener.config(state="disabled")
        self.label_diagnostico.config(text="Monitor detenido", fg="#a6adc8")


def main():
    root = tk.Tk()
    app = MonitorRedApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
