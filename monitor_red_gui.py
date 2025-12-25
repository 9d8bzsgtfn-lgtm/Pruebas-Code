import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import threading
import subprocess
import platform
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pythonping import ping

# --- CONFIGURACIÓN ---
ROUTER_IP = "192.168.60.1"
INTERNET_IP = "8.8.8.8"
INTERVALO = 3

# Dispositivos base (el gateway ISP se detectará automáticamente)
DISPOSITIVOS_BASE = [
    ("Router", "192.168.60.1"),
    ("Internet", "8.8.8.8"),
    ("Tablet Android", "192.168.60.177"),
]


class MonitorRedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Monitor de Red Avanzado")
        self.root.geometry("1100x750")
        self.root.configure(bg="#1e1e2e")

        self.running = False
        self.scanning = False
        self.gateway_isp = None
        self.dispositivos = list(DISPOSITIVOS_BASE)
        self.logs = {"Router": [], "Internet": [], "Tablet Android": [], "Gateway ISP": [], "Escaneo": []}
        self.estadisticas = {}

        for nombre, ip in self.dispositivos:
            self.estadisticas[ip] = {
                "nombre": nombre,
                "ok": 0,
                "fail": 0,
                "ultima_caida": None,
                "estado_anterior": None
            }

        self.crear_interfaz()

        # Detectar gateway ISP al iniciar
        self.detectar_gateway_isp()

    def detectar_gateway_isp(self):
        """Detecta el gateway del ISP usando traceroute"""
        self.label_diagnostico.config(text="Detectando gateway del ISP...", fg="#89b4fa")
        threading.Thread(target=self._detectar_gateway_thread, daemon=True).start()

    def _detectar_gateway_thread(self):
        gateway_ip = None

        try:
            # Determinar comando según sistema operativo
            sistema = platform.system().lower()

            if sistema == "windows":
                cmd = ["tracert", "-h", "3", "-w", "1000", "8.8.8.8"]
            else:  # macOS / Linux
                cmd = ["traceroute", "-m", "3", "-w", "1", "8.8.8.8"]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            output = result.stdout

            # Parsear la salida para encontrar el segundo salto (gateway ISP)
            lines = output.strip().split('\n')

            for line in lines:
                # Buscar IPs en la línea
                ip_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                ips = re.findall(ip_pattern, line)

                for ip in ips:
                    # Ignorar el router local y localhost
                    if ip != ROUTER_IP and not ip.startswith("192.168.") and not ip.startswith("127."):
                        # Verificar que no sea una IP privada de nuestra red
                        if not ip.startswith("10.0.0.") or ip != "10.0.0.1":
                            gateway_ip = ip
                            break

                if gateway_ip:
                    break

            # Si no encontramos uno diferente, buscar cualquier IP que no sea el router
            if not gateway_ip:
                for line in lines:
                    ips = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                    for ip in ips:
                        if ip != ROUTER_IP and ip != "8.8.8.8":
                            gateway_ip = ip
                            break
                    if gateway_ip:
                        break

        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            pass

        self.root.after(0, self._configurar_gateway, gateway_ip)

    def _configurar_gateway(self, gateway_ip):
        if gateway_ip:
            self.gateway_isp = gateway_ip
            # Añadir a la lista de dispositivos
            self.dispositivos.insert(2, ("Gateway ISP", gateway_ip))
            self.estadisticas[gateway_ip] = {
                "nombre": "Gateway ISP",
                "ok": 0,
                "fail": 0,
                "ultima_caida": None,
                "estado_anterior": None
            }

            # Actualizar UI para mostrar el gateway
            self._añadir_panel_gateway(gateway_ip)
            self.label_diagnostico.config(
                text=f"Gateway ISP detectado: {gateway_ip}",
                fg="#a6e3a1"
            )
            self.agregar_log("Gateway ISP", f"Gateway detectado: {gateway_ip}\n", "header")
        else:
            self.label_diagnostico.config(
                text="No se pudo detectar gateway ISP. Usando monitoreo básico.",
                fg="#f9e2af"
            )

    def _añadir_panel_gateway(self, ip):
        # Añadir indicador en la barra superior
        frame = tk.Frame(self.frame_dispositivos_superior, bg="#313244", padx=15, pady=8)
        frame.pack(side="left", padx=5, fill="x", expand=True)

        tk.Label(
            frame,
            text="Gateway ISP",
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

    def crear_interfaz(self):
        # Título
        tk.Label(
            self.root,
            text="Monitor de Red Avanzado",
            font=("Arial", 18, "bold"),
            bg="#1e1e2e",
            fg="#89b4fa"
        ).pack(pady=8)

        # Frame superior con dispositivos
        self.frame_dispositivos_superior = tk.Frame(self.root, bg="#1e1e2e")
        self.frame_dispositivos_superior.pack(fill="x", padx=20, pady=5)

        # Dispositivos en línea horizontal
        self.labels_dispositivos = {}
        for nombre, ip in DISPOSITIVOS_BASE:
            frame = tk.Frame(self.frame_dispositivos_superior, bg="#313244", padx=15, pady=8)
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
            text="Detectando gateway del ISP...",
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

        self.btn_redetectar = tk.Button(
            frame_botones, text="Redetectar GW", font=("Arial", 10),
            bg="#94e2d5", fg="#1e1e2e", width=12,
            command=self.detectar_gateway_isp
        )
        self.btn_redetectar.pack(side="left", padx=3)

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

        # Frame contenedor de los 5 paneles (2 arriba, 3 abajo)
        frame_paneles = tk.Frame(self.root, bg="#1e1e2e")
        frame_paneles.pack(fill="both", expand=True, padx=10, pady=5)

        # Configurar grid
        frame_paneles.grid_columnconfigure(0, weight=1)
        frame_paneles.grid_columnconfigure(1, weight=1)
        frame_paneles.grid_columnconfigure(2, weight=1)
        frame_paneles.grid_rowconfigure(0, weight=1)
        frame_paneles.grid_rowconfigure(1, weight=1)

        self.text_widgets = {}

        # Fila superior: Router, Gateway ISP, Internet
        self.text_widgets["Router"] = self._crear_panel(
            frame_paneles, "Router", "#a6e3a1", 0, 0
        )

        self.text_widgets["Gateway ISP"] = self._crear_panel(
            frame_paneles, "Gateway ISP", "#94e2d5", 0, 1
        )

        self.text_widgets["Internet"] = self._crear_panel(
            frame_paneles, "Internet", "#89b4fa", 0, 2
        )

        # Fila inferior: Tablet, Escaneo (más ancho)
        self.text_widgets["Tablet Android"] = self._crear_panel(
            frame_paneles, "Tablet Android", "#fab387", 1, 0
        )

        # Panel de escaneo ocupa 2 columnas
        frame_escaneo = tk.Frame(frame_paneles, bg="#1e1e2e")
        frame_escaneo.grid(row=1, column=1, columnspan=2, sticky="nsew", padx=5, pady=5)

        tk.Label(
            frame_escaneo,
            text="Escaneo de Red",
            font=("Arial", 11, "bold"),
            bg="#1e1e2e",
            fg="#cba6f7"
        ).pack(anchor="w")

        text_escaneo = scrolledtext.ScrolledText(
            frame_escaneo,
            font=("Courier", 9),
            bg="#11111b",
            fg="#cdd6f4",
            state="disabled",
            height=12
        )
        text_escaneo.pack(fill="both", expand=True, pady=2)

        for tag, color in [("ok", "#a6e3a1"), ("warning", "#f9e2af"), ("error", "#f38ba8"),
                          ("info", "#89b4fa"), ("header", "#cba6f7")]:
            text_escaneo.tag_config(tag, foreground=color)

        self.text_widgets["Escaneo"] = text_escaneo

    def _crear_panel(self, parent, titulo, color, row, col):
        frame = tk.Frame(parent, bg="#1e1e2e")
        frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)

        tk.Label(
            frame,
            text=titulo,
            font=("Arial", 11, "bold"),
            bg="#1e1e2e",
            fg=color
        ).pack(anchor="w")

        text = scrolledtext.ScrolledText(
            frame,
            font=("Courier", 9),
            bg="#11111b",
            fg="#cdd6f4",
            state="disabled",
            height=10
        )
        text.pack(fill="both", expand=True, pady=2)

        for tag, c in [("ok", "#a6e3a1"), ("warning", "#f9e2af"), ("error", "#f38ba8"),
                       ("info", "#89b4fa"), ("header", color)]:
            text.tag_config(tag, foreground=c)

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
        if ip not in self.labels_dispositivos:
            return

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
        if dispositivo not in self.logs:
            self.logs[dispositivo] = []
        self.logs[dispositivo].append((mensaje, tag))

        text_widget = self.text_widgets.get(dispositivo)
        if text_widget:
            text_widget.config(state="normal")
            text_widget.insert("end", mensaje, tag)
            text_widget.see("end")
            text_widget.config(state="disabled")

    def diagnosticar_red(self):
        estados = {}
        for nombre, ip in self.dispositivos:
            if ip in self.estadisticas:
                estados[nombre] = self.estadisticas[ip]["estado_anterior"]

        router_ok = estados.get("Router", False)
        gateway_ok = estados.get("Gateway ISP", True)  # True por defecto si no existe
        internet_ok = estados.get("Internet", False)
        tablet_ok = estados.get("Tablet Android", False)

        # Diagnóstico mejorado con gateway ISP
        if not router_ok:
            return ("CRITICO: Sin conexión al router. Revisa WiFi/cable.", "#f38ba8")
        elif self.gateway_isp and not gateway_ok and router_ok:
            return ("PROBLEMA CONEXIÓN ISP: Router OK pero no llega al gateway. Posible corte de fibra/cable.", "#fab387")
        elif not internet_ok and gateway_ok and router_ok:
            return ("PROBLEMA ISP: Gateway OK pero sin internet. Fallo en servidores del ISP.", "#f9e2af")
        elif not internet_ok and router_ok:
            return ("SIN INTERNET: Router OK pero sin salida a internet.", "#f9e2af")
        elif not tablet_ok and router_ok and internet_ok:
            return ("TABLET OFFLINE: Red OK, tablet no responde.", "#fab387")
        elif all(v for v in estados.values() if v is not None):
            return ("Todo funcionando correctamente", "#a6e3a1")
        else:
            offline = [n for n, ok in estados.items() if ok == False]
            if offline:
                return (f"OFFLINE: {', '.join(offline)}", "#f38ba8")
            return ("Esperando datos...", "#a6adc8")

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
        self.agregar_log("Escaneo", "-" * 40 + "\n", "info")

        for ip, lat in dispositivos:
            conocido = ""
            tag = "info"
            for nombre, ip_conocida in self.dispositivos:
                if ip == ip_conocida:
                    conocido = f" <- {nombre}"
                    tag = "ok"
                    break

            self.agregar_log("Escaneo", f" {ip:15} {lat:>5} ms{conocido}\n", tag)

        self.agregar_log("Escaneo", "-" * 40 + "\n", "info")
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
                if self.gateway_isp:
                    f.write(f"Gateway ISP detectado: {self.gateway_isp}\n")
                f.write("=" * 50 + "\n\n")

                f.write("ESTADISTICAS:\n")
                f.write("-" * 30 + "\n")
                for ip, stats in self.estadisticas.items():
                    total = stats["ok"] + stats["fail"]
                    uptime = (stats["ok"] / total * 100) if total > 0 else 0
                    f.write(f"{stats['nombre']} ({ip}): Uptime {uptime:.1f}%\n")

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
            for nombre, ip in self.dispositivos:
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
        for nombre, ip in self.dispositivos:
            self.agregar_log(nombre, f"[{timestamp}] === INICIADO ===\n", "header")

        threading.Thread(target=self.loop_monitoreo, daemon=True).start()

    def detener_monitor(self):
        self.running = False
        self.btn_iniciar.config(state="normal")
        self.btn_detener.config(state="disabled")

        timestamp = datetime.now().strftime("%H:%M:%S")
        for nombre, ip in self.dispositivos:
            self.agregar_log(nombre, f"[{timestamp}] === DETENIDO ===\n\n", "header")

        self.label_diagnostico.config(text="Monitor detenido", fg="#a6adc8")


def main():
    root = tk.Tk()
    app = MonitorRedApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
