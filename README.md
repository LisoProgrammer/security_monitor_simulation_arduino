# Monitor de seguridad + Arduino Uno

Monitor de escritorio en PyQt6 conectado por puerto serial con el prototipo de
seguridad en Arduino Uno. Cuando se presiona el botón físico de intento, la
aplicación muestra una alerta a pantalla completa con el número de intentos y el
nivel de riesgo. Al presionar el botón físico de RESET, la alerta se cierra y se
muestra la confirmación de acceso bloqueado.

## Requisitos

- Windows con Python 3.10 o superior.
- Placa Arduino Uno conectada por USB con el sketch ya cargado.
- Dependencias de Python:

```powershell
py -m pip install -r requirements.txt
```

## Ejecutar

Desde `C:\monitor`:

```powershell
py run.py
```

El monitor abre el puerto serial automáticamente (9600 baudios). El monitor debe
estar abierto antes de presionar el botón físico; a partir de ese momento la
alerta aparece sola en cada pulsación.

Si la detección automática no encuentra la placa:

1. En la fila **Arduino** de la barra de controles, pulsa **Refresh ports**.
2. Selecciona el puerto de la placa (por ejemplo `COM3`).
3. Espera el indicador verde **● ARDUINO: COM3** en la cabecera.

Los botones **Simular intento** y **Simular RESET** permiten probar la interfaz
sin hardware. En modo demostración la alerta incluye además un botón
**Simular RESET (demo)** para volver al panel.

Si el puerto no abre, cierra el Monitor Serie del IDE de Arduino: un puerto COM
solo puede usarse desde un programa a la vez.

## Comportamiento

| Intentos en Arduino | LED físico | Nivel en el monitor | Alerta |
| --- | --- | --- | --- |
| 1 a 3 | Verde | Baja | Alerta verde |
| 4 a 6 | Amarillo | Intermedia | Alerta ámbar |
| 7 o más | Rojo + buzzer | Alta | Alerta roja intermitente |

La alerta ocupa toda la ventana y muestra:

- **Alguien está intentando ingresar al sistema**
- **Intentos (N)**
- **Alerta: Baja / Intermedia / Alta**
- **Presiona el botón de RESET para bloquear el acceso**

Al recibir `SISTEMA REINICIADO` desde la placa se muestra durante unos segundos
**ACCESO BLOQUEADO / Sistema reiniciado** y luego vuelve el panel principal.

Cada intento y cada reinicio físico también se registran en la tabla de eventos
y en la tarjeta **Physical attempts**.

## Protocolo serial

El sketch envía texto a 9600 baudios, una instrucción por línea. El monitor
reconoce:

```text
INTENTO REGISTRADO: 3
NIVEL VERDE: ACTIVIDAD NORMAL
NIVEL AMARILLO: ADVERTENCIA
NIVEL ROJO: ALERTA DE SEGURIDAD
ALARMA SONORA ACTIVADA
!!! SISTEMA REINICIADO !!!
```

## Conexiones del prototipo

| Elemento | Pin Arduino Uno |
| --- | --- |
| LED verde | 4 |
| LED amarillo | 5 |
| LED rojo | 6 |
| Botón de intento | 10 (a GND, `INPUT_PULLUP`) |
| Botón de RESET | 11 (a GND, `INPUT_PULLUP`) |
| Buzzer | 12 |

El sketch de referencia está en `arduino/program.ino`.

## Estructura

- `arduino_link.py`: detección del puerto, lectura serial en segundo plano y
  análisis del protocolo.
- `widgets/intrusion_overlay.py`: alerta grande a pantalla completa.
- `dashboard.py`: integración del lector serial con el panel y el registro.
- `run.py`: lanzador para ejecutar desde `C:\monitor`.
