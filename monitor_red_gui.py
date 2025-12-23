import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import threading
import time
from datetime import datetime
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
        self.root.geometry("500x550")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        self.running = False
        self.thread = None
        self.logs = []

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
        titulo.pack(pady=10)

        # Frame para el router
        frame_router = tk.Frame(self.root, bg="#313244", padx=20, pady=10)
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
            font=("Arial", 20, "bold"),
            bg="#313244",
            fg="#6c7086"
        )
        self.label_router.pack(anchor="w")

        # Frame para internet
        frame_internet = tk.Frame(self.root, bg="#313244", padx=20, pady=10)
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
            font=("Arial", 20, "bold"),
            bg="#313244",
            fg="#6c7086"
        )
        self.label_internet.pack(anchor="w")

        # Frame diagnóstico
        frame_diag = tk.Frame(self.root, bg="#1e1e2e")
        frame_diag.pack(fill="x", padx=20, pady=5)

        self.label_diagnostico = tk.Label(
            frame_diag,
            text="Presiona Iniciar para comenzar",
            font=("Arial", 10),
            bg="#1e1e2e",
            fg="#a6adc8",
            wraplength=450
        )
        self.label_diagnostico.pack()

        # Botones principales
        frame_botones = tk.Frame(self.root, bg="#1e1e2e")
        frame_botones.pack(pady=10)

        self.btn_iniciar = tk.Button(
            frame_botones,
            text="▶ Iniciar",
            font=("Arial", 11),
            bg="#a6e3a1",
            fg="#1e1e2e",
            width=10,
            command=self.iniciar_monitor
        )
        self.btn_iniciar.pack(side="left", padx=5)

        self.btn_detener = tk.Button(
            frame_botones,
            text="⏹ Detener",
            font=("Arial", 11),
            bg="#f38ba8",
            fg="#1e1e2e",
            width=10,
            command=self.detener_monitor,
            state="disabled"
        )
        self.btn_detener.pack(side="left", padx=5)

        self.btn_exportar = tk.Button(
            frame_botones,
            text="💾 Exportar",
            font=("Arial", 11),
            bg="#89b4fa",
            fg="#1e1e2e",
            width=10,
            command=self.exportar_logs
        )
        self.btn_exportar.pack(side="left", padx=5)

        # Historial de logs
        frame_logs = tk.Frame(self.root, bg="#1e1e2e")
        frame_logs.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Label(
            frame_logs,
            text="📋 Historial de Logs",
            font=("Arial", 11, "bold"),
            bg="#1e1e2e",
            fg="#cdd6f4"
        ).pack(anchor="w")

        self.text_logs = scrolledtext.ScrolledText(
            frame_logs,
            height=10,
            font=("Courier", 9),
            bg="#11111b",
            fg="#cdd6f4",
            insertbackground="#cdd6f4",
            state="disabled"
        )
        self.text_logs.pack(fill="both", expand=True, pady=5)

        # Configurar tags de colores para el texto
        self.text_logs.tag_config("ok", foreground="#a6e3a1")
        self.text_logs.tag_config("warning", foreground="#f9e2af")
        self.text_logs.tag_config("error", foreground="#f38ba8")
        self.text_logs.tag_config("info", foreground="#89b4fa")

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
                color = "#a6e3a1"
            elif valor < UMBRAL_LATENCIA:
                color = "#f9e2af"
            else:
                color = "#fab387"
            label.config(text=f"{valor} ms", fg=color)
        else:
            label.config(text="SIN CONEXIÓN", fg="#f38ba8")

    def diagnosticar(self, local_ms, web_ms):
        if local_ms is None:
            return ("CRÍTICO: No hay conexión al router", "#f38ba8", "error")
        elif web_ms is None:
            return ("PROBLEMA ISP: Router OK pero sin internet", "#f9e2af", "warning")
        elif web_ms > UMBRAL_LATENCIA and local_ms < 10:
            return ("SATURACIÓN: Red local OK, internet lento", "#cba6f7", "warning")
        elif local_ms > 50:
            return ("INTERFERENCIA: Router lento", "#f9e2af", "warning")
        else:
            return ("Conexión estable", "#a6e3a1", "ok")

    def agregar_log(self, local_ms, web_ms, diagnostico, tag):
        timestamp = datetime.now().strftime("%H:%M:%S")
        local_str = f"{local_ms} ms" if local_ms else "FALLO"
        web_str = f"{web_ms} ms" if web_ms else "FALLO"

        log_entry = f"[{timestamp}] Router: {local_str} | Internet: {web_str} | {diagnostico}\n"

        # Guardar en lista para exportar
        self.logs.append(log_entry)

        # Mostrar en el widget de texto
        self.text_logs.config(state="normal")
        self.text_logs.insert("end", log_entry, tag)
        self.text_logs.see("end")
        self.text_logs.config(state="disabled")

    def exportar_logs(self):
        if not self.logs:
            self.label_diagnostico.config(text="No hay logs para exportar", fg="#f9e2af")
            return

        archivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt"), ("Todos los archivos", "*.*")],
            initialfile=f"network_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if archivo:
            with open(archivo, "w") as f:
                f.write("=" * 60 + "\n")
                f.write("MONITOR DE RED - HISTORIAL DE LOGS\n")
                f.write(f"Exportado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Router: {ROUTER_IP} | Internet: {INTERNET_IP}\n")
                f.write("=" * 60 + "\n\n")
                f.writelines(self.logs)
            self.label_diagnostico.config(text=f"Logs exportados: {archivo}", fg="#a6e3a1")

    def loop_monitoreo(self):
        while self.running:
            lat_local = self.realizar_ping(ROUTER_IP)
            lat_web = self.realizar_ping(INTERNET_IP)

            self.root.after(0, self.actualizar_label, self.label_router, lat_local, 20)
            self.root.after(0, self.actualizar_label, self.label_internet, lat_web, 50)

            diag_texto, diag_color, diag_tag = self.diagnosticar(lat_local, lat_web)
            self.root.after(0, lambda t=diag_texto, c=diag_color:
                           self.label_diagnostico.config(text=t, fg=c))

            # Agregar al historial
            self.root.after(0, self.agregar_log, lat_local, lat_web, diag_texto, diag_tag)

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
