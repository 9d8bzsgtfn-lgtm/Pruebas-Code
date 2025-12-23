import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import threading
import time
import subprocess
import platform
from datetime import datetime
from pythonping import ping

# --- CONFIGURACIÓN ---
ROUTER_IP = "192.168.60.1"  # Cambia si tu router es diferente
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
        self.root.geometry("650x700")
        self.root.configure(bg="#1e1e2e")

        self.running = False
        self.scanning = False
        self.logs = []
        self.estadisticas = {}  # {ip: {"ok": 0, "fail": 0, "ultima_caida": None}}

        for nombre, ip in DISPOSITIVOS:
            self.estadisticas[ip] = {"nombre": nombre, "ok": 0, "fail": 0, "ultima_caida": None, "estado_anterior": None}

        self.crear_interfaz()

    def crear_interfaz(self):
        # Título
        tk.Label(
            self.root,
            text="Monitor de Red Avanzado",
            font=("Arial", 18, "bold"),
            bg="#1e1e2e",
            fg="#89b4fa"
        ).pack(pady=10)

        # Frame para dispositivos monitoreados
        frame_dispositivos = tk.Frame(self.root, bg="#1e1e2e")
        frame_dispositivos.pack(fill="x", padx=20, pady=5)

        tk.Label(
            frame_dispositivos,
            text="Dispositivos Monitoreados",
            font=("Arial", 12, "bold"),
            bg="#1e1e2e",
            fg="#cdd6f4"
        ).pack(anchor="w")

        self.labels_dispositivos = {}
        for nombre, ip in DISPOSITIVOS:
            frame = tk.Frame(frame_dispositivos, bg="#313244", padx=15, pady=8)
            frame.pack(fill="x", pady=2)

            tk.Label(
                frame,
                text=f"{nombre} ({ip})",
                font=("Arial", 10),
                bg="#313244",
                fg="#cdd6f4",
                width=30,
                anchor="w"
            ).pack(side="left")

            label_estado = tk.Label(
                frame,
                text="-- ms",
                font=("Arial", 12, "bold"),
                bg="#313244",
                fg="#6c7086",
                width=15
            )
            label_estado.pack(side="left", padx=10)

            label_uptime = tk.Label(
                frame,
                text="Uptime: --%",
                font=("Arial", 9),
                bg="#313244",
                fg="#a6adc8",
                width=15
            )
            label_uptime.pack(side="right")

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
            fg="#a6adc8",
            wraplength=600
        )
        self.label_diagnostico.pack(pady=10)

        # Botones principales
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

        # Historial de logs
        frame_logs = tk.Frame(self.root, bg="#1e1e2e")
        frame_logs.pack(fill="both", expand=True, padx=20, pady=5)

        tk.Label(
            frame_logs,
            text="Historial de Eventos",
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
            state="disabled"
        )
        self.text_logs.pack(fill="both", expand=True, pady=3)

        self.text_logs.tag_config("ok", foreground="#a6e3a1")
        self.text_logs.tag_config("warning", foreground="#f9e2af")
        self.text_logs.tag_config("error", foreground="#f38ba8")
        self.text_logs.tag_config("info", foreground="#89b4fa")
        self.text_logs.tag_config("scan", foreground="#cba6f7")

        # Panel de dispositivos en red
        frame_red = tk.Frame(self.root, bg="#1e1e2e")
        frame_red.pack(fill="both", expand=True, padx=20, pady=5)

        tk.Label(
            frame_red,
            text="Dispositivos Detectados en Red",
            font=("Arial", 11, "bold"),
            bg="#1e1e2e",
            fg="#cdd6f4"
        ).pack(anchor="w")

        self.text_red = scrolledtext.ScrolledText(
            frame_red,
            height=8,
            font=("Courier", 9),
            bg="#11111b",
            fg="#cba6f7",
            state="disabled"
        )
        self.text_red.pack(fill="both", expand=True, pady=3)

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

        if latencia is not None:
            stats["ok"] += 1
            color = "#a6e3a1" if latencia < 50 else "#f9e2af" if latencia < 100 else "#fab387"
            labels["estado"].config(text=f"{latencia} ms", fg=color)

            # Detectar reconexión
            if stats["estado_anterior"] == False:
                self.agregar_log(f"RECONECTADO: {stats['nombre']} ({ip}) vuelve a responder", "ok")
            stats["estado_anterior"] = True
        else:
            stats["fail"] += 1
            labels["estado"].config(text="OFFLINE", fg="#f38ba8")

            # Detectar nueva desconexión
            if stats["estado_anterior"] == True or stats["estado_anterior"] is None:
                stats["ultima_caida"] = datetime.now()
                self.agregar_log(f"DESCONEXION: {stats['nombre']} ({ip}) no responde!", "error")
            stats["estado_anterior"] = False

        # Calcular uptime
        total = stats["ok"] + stats["fail"]
        if total > 0:
            uptime = (stats["ok"] / total) * 100
            color_uptime = "#a6e3a1" if uptime > 95 else "#f9e2af" if uptime > 80 else "#f38ba8"
            labels["uptime"].config(text=f"Uptime: {uptime:.1f}%", fg=color_uptime)

    def diagnosticar_red(self):
        estados = {}
        for nombre, ip in DISPOSITIVOS:
            estados[nombre] = self.estadisticas[ip]["estado_anterior"]

        router_ok = estados.get("Router", False)
        internet_ok = estados.get("Internet", False)
        tablet_ok = estados.get("Tablet Android", False)

        if not router_ok:
            return ("CRITICO: Sin conexión al router. Verifica WiFi o cable.", "#f38ba8")
        elif not internet_ok and router_ok:
            return ("PROBLEMA ISP: Router OK pero sin internet. Llama a tu proveedor.", "#f9e2af")
        elif not tablet_ok and router_ok and internet_ok:
            return ("TABLET OFFLINE: La tablet no responde. Puede estar apagada o fuera de alcance WiFi.", "#fab387")
        elif all(estados.values()):
            return ("Todo funcionando correctamente", "#a6e3a1")
        else:
            offline = [n for n, ok in estados.items() if not ok]
            return (f"OFFLINE: {', '.join(offline)}", "#f38ba8")

    def agregar_log(self, mensaje, tag="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {mensaje}\n"
        self.logs.append(entry)

        self.text_logs.config(state="normal")
        self.text_logs.insert("end", entry, tag)
        self.text_logs.see("end")
        self.text_logs.config(state="disabled")

    def escanear_red(self):
        if self.scanning:
            return

        self.scanning = True
        self.btn_escanear.config(state="disabled", text="Escaneando...")
        self.agregar_log("Iniciando escaneo de red...", "scan")

        threading.Thread(target=self._escanear_red_thread, daemon=True).start()

    def _escanear_red_thread(self):
        # Detectar el rango de red basado en el router
        base_ip = ".".join(ROUTER_IP.split(".")[:-1])
        dispositivos_encontrados = []

        self.root.after(0, lambda: self.text_red.config(state="normal"))
        self.root.after(0, lambda: self.text_red.delete("1.0", "end"))
        self.root.after(0, lambda: self.text_red.insert("end", f"Escaneando {base_ip}.1-254...\n\n"))

        def ping_ip(ip):
            try:
                response = ping(ip, count=1, timeout=0.5)
                if response.success():
                    return (ip, round(response.rtt_avg_ms, 2))
            except:
                pass
            return None

        # Escanear en paralelo usando threads
        from concurrent.futures import ThreadPoolExecutor
        ips_to_scan = [f"{base_ip}.{i}" for i in range(1, 255)]

        with ThreadPoolExecutor(max_workers=50) as executor:
            results = executor.map(ping_ip, ips_to_scan)

        for result in results:
            if result:
                ip, latencia = result
                dispositivos_encontrados.append((ip, latencia))

        # Mostrar resultados
        self.root.after(0, lambda: self.text_red.delete("1.0", "end"))

        if dispositivos_encontrados:
            dispositivos_encontrados.sort(key=lambda x: [int(p) for p in x[0].split(".")])
            resultado = f"Encontrados {len(dispositivos_encontrados)} dispositivos:\n\n"
            for ip, lat in dispositivos_encontrados:
                # Marcar dispositivos conocidos
                conocido = ""
                for nombre, ip_conocida in DISPOSITIVOS:
                    if ip == ip_conocida:
                        conocido = f" <- {nombre}"
                        break
                resultado += f"  {ip:15} ({lat} ms){conocido}\n"
        else:
            resultado = "No se encontraron dispositivos"

        self.root.after(0, lambda r=resultado: self._mostrar_resultado_escaneo(r))

    def _mostrar_resultado_escaneo(self, resultado):
        self.text_red.config(state="normal")
        self.text_red.delete("1.0", "end")
        self.text_red.insert("end", resultado)
        self.text_red.config(state="disabled")
        self.btn_escanear.config(state="normal", text="Escanear Red")
        self.scanning = False
        self.agregar_log("Escaneo de red completado", "scan")

    def exportar_logs(self):
        if not self.logs:
            messagebox.showwarning("Aviso", "No hay logs para exportar")
            return

        archivo = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt")],
            initialfile=f"network_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if archivo:
            with open(archivo, "w") as f:
                f.write("=" * 60 + "\n")
                f.write("MONITOR DE RED - REPORTE\n")
                f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")

                f.write("ESTADISTICAS POR DISPOSITIVO:\n")
                f.write("-" * 40 + "\n")
                for ip, stats in self.estadisticas.items():
                    total = stats["ok"] + stats["fail"]
                    uptime = (stats["ok"] / total * 100) if total > 0 else 0
                    f.write(f"{stats['nombre']} ({ip})\n")
                    f.write(f"  - Uptime: {uptime:.1f}%\n")
                    f.write(f"  - Checks OK: {stats['ok']}, Fallos: {stats['fail']}\n")
                    if stats["ultima_caida"]:
                        f.write(f"  - Ultima caida: {stats['ultima_caida'].strftime('%H:%M:%S')}\n")
                    f.write("\n")

                f.write("\nHISTORIAL DE EVENTOS:\n")
                f.write("-" * 40 + "\n")
                f.writelines(self.logs)

            self.agregar_log(f"Logs exportados: {archivo}", "info")

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
        self.agregar_log("Monitor iniciado", "info")
        threading.Thread(target=self.loop_monitoreo, daemon=True).start()

    def detener_monitor(self):
        self.running = False
        self.btn_iniciar.config(state="normal")
        self.btn_detener.config(state="disabled")
        self.agregar_log("Monitor detenido", "info")


def main():
    root = tk.Tk()
    app = MonitorRedApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
