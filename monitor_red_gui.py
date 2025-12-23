import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import threading
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pythonping import ping

# --- CONFIGURACIÓN ---
ROUTER_IP = "192.168.60.1"
INTERNET_IP = "8.8.8.8"
INTERVALO = 3

# Dispositivos a monitorear (nombre, IP)
DISPOSITIVOS = [
    ("Router", "192.168.60.1"),
    ("Internet", "8.8.8.8"),
    ("Tablet Android", "192.168.60.177"),
]


class MonitorRedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Red Avanzado")
        self.root.geometry("1000x700")
        self.root.configure(bg="#1e1e2e")

        self.running = False
        self.scanning = False
        self.logs = {"Router": [], "Internet": [], "Tablet Android": [], "Escaneo": []}
        self.estadisticas = {}

        for nombre, ip in DISPOSITIVOS:
            self.estadisticas[ip] = {
                "nombre": nombre,
                "ok": 0,
                "fail": 0,
                "ultima_caida": None,
                "estado_anterior": None
            }

        self.crear_interfaz()

    def crear_interfaz(self):
        # Título
        tk.Label(
            self.root,
            text="Monitor de Red Avanzado",
            font=("Arial", 18, "bold"),
            bg="#1e1e2e",
            fg="#89b4fa"
        ).pack(pady=8)

        # Frame superior con dispositivos y diagnóstico
        frame_superior = tk.Frame(self.root, bg="#1e1e2e")
        frame_superior.pack(fill="x", padx=20, pady=5)

        # Dispositivos en línea horizontal
        self.labels_dispositivos = {}
        for nombre, ip in DISPOSITIVOS:
            frame = tk.Frame(frame_superior, bg="#313244", padx=15, pady=8)
            frame.pack(side="left", padx=5, fill="x", expand=True)

            tk.Label(
                frame,
                text=f"{nombre}",
                font=("Arial", 10, "bold"),
                bg="#313244",
                fg="#cdd6f4"
            ).pack()

            tk.Label(
                frame,
                text=f"({ip})",
                font=("Arial", 8),
                bg="#313244",
                fg="#a6adc8"
            ).pack()

            label_estado = tk.Label(
                frame,
                text="-- ms",
                font=("Arial", 14, "bold"),
                bg="#313244",
                fg="#6c7086"
            )
            label_estado.pack(pady=2)

            label_uptime = tk.Label(
                frame,
                text="Uptime: --%",
                font=("Arial", 9),
                bg="#313244",
                fg="#a6adc8"
            )
            label_uptime.pack()

            self.labels_dispositivos[ip] = {
                "estado": label_estado,
                "uptime": label_uptime
            }

        # Diagnóstico general
        self.label_diagnostico = tk.Label(
            self.root,
            text="Presiona Iniciar para comenzar",
            font=("Arial", 11),
            bg="#1e1e2e",
            fg="#a6adc8"
        )
        self.label_diagnostico.pack(pady=5)

        # Botones
        frame_botones = tk.Frame(self.root, bg="#1e1e2e")
        frame_botones.pack(pady=5)

        self.btn_iniciar = tk.Button(
            frame_botones, text="Iniciar", font=("Arial", 10),
            bg="#a6e3a1", fg="#1e1e2e", width=10,
            command=self.iniciar_monitor
        )
        self.btn_iniciar.pack(side="left", padx=3)

        self.btn_detener = tk.Button(
            frame_botones, text="Detener", font=("Arial", 10),
            bg="#f38ba8", fg="#1e1e2e", width=10,
            command=self.detener_monitor, state="disabled"
        )
        self.btn_detener.pack(side="left", padx=3)

        self.btn_escanear = tk.Button(
            frame_botones, text="Escanear Red", font=("Arial", 10),
            bg="#cba6f7", fg="#1e1e2e", width=12,
            command=self.escanear_red
        )
        self.btn_escanear.pack(side="left", padx=3)

        self.btn_exportar = tk.Button(
            frame_botones, text="Exportar", font=("Arial", 10),
            bg="#89b4fa", fg="#1e1e2e", width=10,
            command=self.exportar_logs
        )
        self.btn_exportar.pack(side="left", padx=3)

        self.btn_limpiar = tk.Button(
            frame_botones, text="Limpiar", font=("Arial", 10),
            bg="#fab387", fg="#1e1e2e", width=10,
            command=self.limpiar_logs
        )
        self.btn_limpiar.pack(side="left", padx=3)

        # Frame contenedor de los 4 paneles (2x2)
        frame_paneles = tk.Frame(self.root, bg="#1e1e2e")
        frame_paneles.pack(fill="both", expand=True, padx=10, pady=5)

        # Configurar grid 2x2
        frame_paneles.grid_columnconfigure(0, weight=1)
        frame_paneles.grid_columnconfigure(1, weight=1)
        frame_paneles.grid_rowconfigure(0, weight=1)
        frame_paneles.grid_rowconfigure(1, weight=1)

        self.text_widgets = {}

        # Panel Router (arriba izquierda)
        self.text_widgets["Router"] = self._crear_panel(
            frame_paneles, "Router", "#a6e3a1", 0, 0
        )

        # Panel Internet (arriba derecha)
        self.text_widgets["Internet"] = self._crear_panel(
            frame_paneles, "Internet", "#89b4fa", 0, 1
        )

        # Panel Tablet (abajo izquierda)
        self.text_widgets["Tablet Android"] = self._crear_panel(
            frame_paneles, "Tablet Android", "#fab387", 1, 0
        )

        # Panel Escaneo (abajo derecha)
        self.text_widgets["Escaneo"] = self._crear_panel(
            frame_paneles, "Escaneo de Red", "#cba6f7", 1, 1
        )

    def _crear_panel(self, parent, titulo, color, row, col):
        frame = tk.Frame(parent, bg="#1e1e2e")
        frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)

        # Título del panel
        tk.Label(
            frame,
            text=titulo,
            font=("Arial", 11, "bold"),
            bg="#1e1e2e",
            fg=color
        ).pack(anchor="w")

        # Área de texto
        text = scrolledtext.ScrolledText(
            frame,
            font=("Courier", 9),
            bg="#11111b",
            fg="#cdd6f4",
            state="disabled",
            height=12
        )
        text.pack(fill="both", expand=True, pady=2)

        # Tags de colores
        text.tag_config("ok", foreground="#a6e3a1")
        text.tag_config("warning", foreground="#f9e2af")
        text.tag_config("error", foreground="#f38ba8")
        text.tag_config("info", foreground="#89b4fa")
        text.tag_config("header", foreground=color, font=("Courier", 9, "bold"))

        return text

    def realizar_ping(self, target):
        try:
            response = ping(target, count=2, timeout=1)
            if response.success():
                return round(response.rtt_avg_ms, 2)
            return None
        except Exception:
            return None

    def actualizar_dispositivo(self, ip, latencia):
        labels = self.labels_dispositivos[ip]
        stats = self.estadisticas[ip]
        nombre = stats["nombre"]

        timestamp = datetime.now().strftime("%H:%M:%S")

        if latencia is not None:
            stats["ok"] += 1
            color = "#a6e3a1" if latencia < 50 else "#f9e2af" if latencia < 100 else "#fab387"
            labels["estado"].config(text=f"{latencia} ms", fg=color)

            if latencia < 50:
                tag = "ok"
                status = "OK"
            elif latencia < 100:
                tag = "warning"
                status = "LENTO"
            else:
                tag = "error"
                status = "MUY LENTO"

            log_entry = f"[{timestamp}] {latencia:>6} ms - {status}\n"

            if stats["estado_anterior"] == False:
                log_entry = f"[{timestamp}] *** RECONECTADO *** {latencia} ms\n"
                tag = "ok"

            stats["estado_anterior"] = True
        else:
            stats["fail"] += 1
            labels["estado"].config(text="OFFLINE", fg="#f38ba8")
            log_entry = f"[{timestamp}]  FALLO - SIN RESPUESTA\n"
            tag = "error"

            if stats["estado_anterior"] == True or stats["estado_anterior"] is None:
                stats["ultima_caida"] = datetime.now()
                log_entry = f"[{timestamp}] *** DESCONEXION ***\n"

            stats["estado_anterior"] = False

        self.agregar_log(nombre, log_entry, tag)

        total = stats["ok"] + stats["fail"]
        if total > 0:
            uptime = (stats["ok"] / total) * 100
            color_uptime = "#a6e3a1" if uptime > 95 else "#f9e2af" if uptime > 80 else "#f38ba8"
            labels["uptime"].config(text=f"Uptime: {uptime:.1f}%", fg=color_uptime)

    def agregar_log(self, dispositivo, mensaje, tag="info"):
        self.logs[dispositivo].append((mensaje, tag))

        text_widget = self.text_widgets.get(dispositivo)
        if text_widget:
            text_widget.config(state="normal")
            text_widget.insert("end", mensaje, tag)
            text_widget.see("end")
            text_widget.config(state="disabled")

    def diagnosticar_red(self):
        estados = {}
        for nombre, ip in DISPOSITIVOS:
            estados[nombre] = self.estadisticas[ip]["estado_anterior"]

        router_ok = estados.get("Router", False)
        internet_ok = estados.get("Internet", False)
        tablet_ok = estados.get("Tablet Android", False)

        if not router_ok:
            return ("CRITICO: Sin conexión al router", "#f38ba8")
        elif not internet_ok and router_ok:
            return ("PROBLEMA ISP: Router OK pero sin internet", "#f9e2af")
        elif not tablet_ok and router_ok and internet_ok:
            return ("TABLET OFFLINE: No responde", "#fab387")
        elif all(estados.values()):
            return ("Todo funcionando correctamente", "#a6e3a1")
        else:
            offline = [n for n, ok in estados.items() if not ok]
            return (f"OFFLINE: {', '.join(offline)}", "#f38ba8")

    def escanear_red(self):
        if self.scanning:
            return

        self.scanning = True
        self.btn_escanear.config(state="disabled", text="Escaneando...")

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.agregar_log("Escaneo", f"[{timestamp}] === INICIANDO ESCANEO ===\n", "header")

        threading.Thread(target=self._escanear_red_thread, daemon=True).start()

    def _escanear_red_thread(self):
        base_ip = ".".join(ROUTER_IP.split(".")[:-1])
        dispositivos_encontrados = []

        self.root.after(0, lambda: self.agregar_log(
            "Escaneo", f"Escaneando {base_ip}.1-254...\n\n", "info"))

        def ping_ip(ip):
            try:
                response = ping(ip, count=1, timeout=0.5)
                if response.success():
                    return (ip, round(response.rtt_avg_ms, 2))
            except:
                pass
            return None

        ips_to_scan = [f"{base_ip}.{i}" for i in range(1, 255)]

        with ThreadPoolExecutor(max_workers=50) as executor:
            results = list(executor.map(ping_ip, ips_to_scan))

        for result in results:
            if result:
                dispositivos_encontrados.append(result)

        dispositivos_encontrados.sort(key=lambda x: [int(p) for p in x[0].split(".")])

        self.root.after(0, self._mostrar_resultado_escaneo, dispositivos_encontrados)

    def _mostrar_resultado_escaneo(self, dispositivos):
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.agregar_log("Escaneo", f"Encontrados {len(dispositivos)} dispositivos:\n", "ok")
        self.agregar_log("Escaneo", "-" * 35 + "\n", "info")

        for ip, lat in dispositivos:
            conocido = ""
            tag = "info"
            for nombre, ip_conocida in DISPOSITIVOS:
                if ip == ip_conocida:
                    conocido = f" <- {nombre}"
                    tag = "ok"
                    break

            self.agregar_log("Escaneo", f" {ip:15} {lat:>5} ms{conocido}\n", tag)

        self.agregar_log("Escaneo", "-" * 35 + "\n", "info")
        self.agregar_log("Escaneo", f"[{timestamp}] === COMPLETADO ===\n\n", "header")

        self.btn_escanear.config(state="normal", text="Escanear Red")
        self.scanning = False

    def limpiar_logs(self):
        for nombre in self.logs:
            self.logs[nombre] = []
            text_widget = self.text_widgets.get(nombre)
            if text_widget:
                text_widget.config(state="normal")
                text_widget.delete("1.0", "end")
                text_widget.config(state="disabled")

        for ip in self.estadisticas:
            self.estadisticas[ip]["ok"] = 0
            self.estadisticas[ip]["fail"] = 0
            self.estadisticas[ip]["ultima_caida"] = None
            self.estadisticas[ip]["estado_anterior"] = None

        for ip, labels in self.labels_dispositivos.items():
            labels["estado"].config(text="-- ms", fg="#6c7086")
            labels["uptime"].config(text="Uptime: --%", fg="#a6adc8")

        self.label_diagnostico.config(text="Logs limpiados", fg="#a6adc8")

    def exportar_logs(self):
        tiene_logs = any(len(logs) > 0 for logs in self.logs.values())
        if not tiene_logs:
            messagebox.showwarning("Aviso", "No hay logs para exportar")
            return

        archivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt")],
            initialfile=f"network_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if archivo:
            with open(archivo, "w") as f:
                f.write("=" * 50 + "\n")
                f.write("MONITOR DE RED - REPORTE\n")
                f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")

                f.write("ESTADISTICAS:\n")
                f.write("-" * 30 + "\n")
                for ip, stats in self.estadisticas.items():
                    total = stats["ok"] + stats["fail"]
                    uptime = (stats["ok"] / total * 100) if total > 0 else 0
                    f.write(f"{stats['nombre']}: Uptime {uptime:.1f}%\n")

                for nombre, logs in self.logs.items():
                    if logs:
                        f.write(f"\n{'=' * 50}\n")
                        f.write(f"HISTORIAL: {nombre}\n")
                        f.write("=" * 50 + "\n")
                        for log_entry, tag in logs:
                            f.write(log_entry)

            self.label_diagnostico.config(text=f"Exportado", fg="#a6e3a1")

    def loop_monitoreo(self):
        while self.running:
            for nombre, ip in DISPOSITIVOS:
                latencia = self.realizar_ping(ip)
                self.root.after(0, self.actualizar_dispositivo, ip, latencia)

            diag_texto, diag_color = self.diagnosticar_red()
            self.root.after(0, lambda t=diag_texto, c=diag_color:
                           self.label_diagnostico.config(text=t, fg=c))

            time.sleep(INTERVALO)

    def iniciar_monitor(self):
        self.running = True
        self.btn_iniciar.config(state="disabled")
        self.btn_detener.config(state="normal")

        timestamp = datetime.now().strftime("%H:%M:%S")
        for nombre, ip in DISPOSITIVOS:
            self.agregar_log(nombre, f"[{timestamp}] === INICIADO ===\n", "header")

        threading.Thread(target=self.loop_monitoreo, daemon=True).start()

    def detener_monitor(self):
        self.running = False
        self.btn_iniciar.config(state="normal")
        self.btn_detener.config(state="disabled")

        timestamp = datetime.now().strftime("%H:%M:%S")
        for nombre, ip in DISPOSITIVOS:
            self.agregar_log(nombre, f"[{timestamp}] === DETENIDO ===\n\n", "header")

        self.label_diagnostico.config(text="Monitor detenido", fg="#a6adc8")


def main():
    root = tk.Tk()
    app = MonitorRedApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
