# CLAUDE.md - Monitor de Red Avanzado

Este archivo proporciona contexto a Claude Code para trabajar efectivamente en este proyecto.

## Descripción del Proyecto

Aplicación de escritorio para monitoreo de red en tiempo real. Permite supervisar la conectividad de múltiples dispositivos en una red local, detectar automáticamente el gateway del ISP, escanear la red y mantener logs detallados.

## Stack Tecnológico

- **Lenguaje:** Python 3
- **GUI:** tkinter (biblioteca estándar)
- **Networking:** pythonping
- **Concurrencia:** threading, concurrent.futures

## Estructura del Proyecto

```
/
├── monitor_red_gui.py    # Aplicación principal (archivo único)
└── CLAUDE.md             # Este archivo
```

## Comandos Útiles

```bash
# Ejecutar la aplicación
python monitor_red_gui.py

# Instalar dependencias
pip install pythonping
```

## Configuración por Defecto

Los valores de configuración están en las líneas 13-22 de `monitor_red_gui.py`:
- `ROUTER_IP`: IP del router local (192.168.60.1)
- `INTERNET_IP`: IP para verificar conectividad a internet (8.8.8.8)
- `INTERVALO`: Intervalo de monitoreo en segundos (3)
- `DISPOSITIVOS_BASE`: Lista de dispositivos a monitorear

## Arquitectura

### Clase Principal: `MonitorRedApp`

| Método | Propósito |
|--------|-----------|
| `crear_interfaz()` | Construye la GUI con layout de paneles |
| `realizar_ping()` | Ejecuta ping a un dispositivo |
| `loop_monitoreo()` | Bucle principal de monitoreo |
| `detectar_gateway_isp()` | Detecta gateway ISP via traceroute |
| `escanear_red()` | Escanea la red local en paralelo |
| `diagnosticar_red()` | Analiza estado general de la red |
| `exportar_logs()` | Guarda logs a archivo de texto |

### Modelo de Threading

- **Hilo principal:** Loop de eventos de tkinter (GUI)
- **Hilos daemon:** Monitoreo continuo, detección de gateway, escaneo de red

## Convenciones de Código

- **Idioma:** Código y comentarios en español
- **Estilo:** PEP 8 con nombres descriptivos en español
- **Colores:** Tema oscuro estilo Catppuccin
  - Verde (#a6e3a1): Latencia < 50ms
  - Amarillo (#f9e2af): Latencia 50-100ms
  - Naranja (#fab387): Latencia > 100ms
  - Rojo (#f38ba8): Dispositivo offline

## Funcionalidades Clave

1. **Monitoreo en tiempo real** de múltiples dispositivos
2. **Detección automática** del gateway del ISP via traceroute
3. **Escaneo de red** con 50 hilos concurrentes
4. **Logs por dispositivo** con códigos de color
5. **Exportación** de logs y estadísticas
6. **Soporte multiplataforma** (Windows, macOS, Linux)

## Consideraciones para Desarrollo

- La aplicación es un archivo único monolítico
- No hay tests automatizados actualmente
- Los timeouts de red están configurados para balance entre rapidez y confiabilidad
- El escaneo de red asume una subred /24

## Dependencias

```
pythonping>=1.1.4
```

## Notas

- Requiere permisos de administrador/root en algunos sistemas para ejecutar pings ICMP
- En Windows usa `tracert`, en Unix usa `traceroute`
