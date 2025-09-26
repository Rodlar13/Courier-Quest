# Estructuras.py
# Archivo completo con lógica de juego y reputación según las reglas especificadas.

import os
import sys
import json
import random
import math
from datetime import datetime, date

# -------------------- imports externos --------------------
try:
    import pygame
except Exception:
    print("ERROR: pygame no está instalado. Ejecuta 'pip install pygame' y vuelve a intentar.")
    sys.exit(1)

# -------------------- Configuración API (opcional) --------------------
BASE_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"


def obtener_datos_API(endpoint, archivo):
    try:
        import requests
        r = requests.get(BASE_URL + endpoint, timeout=5)
        datos = r.json()
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print(f"Archivo {archivo} actualizado desde el API.")
        return datos
    except Exception as e:
        # No fatal: si no hay internet, usar archivo local si existe
        print(f"No se pudo conectar ({e}). Revisando archivo {archivo}...")
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None


def cargarDatosAPI():
    # llamadas opcionales, no necesarias para que el juego funcione
    try:
        mapa = obtener_datos_API("/city/map", "ciudad.json")
        jobs = obtener_datos_API("/city/jobs", "pedidos.json")
        clima = obtener_datos_API("/city/weather", "weather.json")
        return mapa, jobs, clima
    except Exception:
        return None, None, None

# Intentar cargar datos (no obligatorio)
cargarDatosAPI()

# -------------------- Configuración general --------------------
ANCHO, ALTO = 1500, 900
FPS = 60
CELDA = 48
v0 = 3 * CELDA  # velocidad base (px/seg)
SAVE_FILE = "partida.json"
RECORDS_FILE = "records.json"

pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Courier Quest")

# Fuentes
font = pygame.font.SysFont(None, 22)
font_big = pygame.font.SysFont(None, 44)

# -------------------- Imágenes --------------------
TAM_JUGADOR = (48, 48)
TAM_CLIENTE = (42, 42)
TAM_ICONO = (32, 32)


def cargar_imagen_robusta(nombre, size=None, exit_on_fail=False):
    """Intenta cargar una imagen desde el directorio del script. Si falla, retorna una superficie simple.
    Si exit_on_fail es True terminará el programa."""
    ruta = os.path.join(os.path.dirname(__file__), nombre)
    try:
        img = pygame.image.load(ruta)
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img.convert_alpha()
    except Exception as e:
        print(f"Aviso: no se pudo cargar {nombre}: {e}")
        if exit_on_fail:
            pygame.quit()
            sys.exit(f"Coloca {nombre} en la carpeta y vuelve a intentar.")
        # fallback: generar superficie identificable
        surf = pygame.Surface(size if size else (48, 48), pygame.SRCALPHA)
        surf.fill((200, 80, 80, 255))
        return surf

icono = cargar_imagen_robusta("mensajero.png", TAM_ICONO, exit_on_fail=False)
pygame.display.set_icon(icono)
img_jugador = cargar_imagen_robusta("mensajero.png", TAM_JUGADOR)
img_cliente = cargar_imagen_robusta("audiencia.png", TAM_CLIENTE)

# -------------------- Obstáculos --------------------
OBSTACULOS = [
    pygame.Rect(120, 120, 225, 140),  pygame.Rect(465, 120, 225, 140),
    pygame.Rect(810, 120, 225, 140),  pygame.Rect(1155, 120, 225, 140),
    pygame.Rect(120, 380, 225, 140),  pygame.Rect(465, 380, 225, 140),
    pygame.Rect(810, 380, 225, 140),  pygame.Rect(1155, 380, 225, 140),
    pygame.Rect(120, 640, 225, 140),  pygame.Rect(465, 640, 225, 140),
    pygame.Rect(810, 640, 225, 140),  pygame.Rect(1155, 640, 225, 140),
]

# -------------------- Estados globales --------------------
energia = 100
dinero_ganado = 0
reputacion = 70 # INICIAL SEGUN REGLA
entregas = 0
racha_sin_penalizacion = 0
primera_tardanza_fecha = None  # date() cuando se aplicó la reducción de penalización

jugador_rect = img_jugador.get_rect(topleft=(728, 836))
jugador_x_cambio_positivo = 0.0
jugador_x_cambio_negativo = 0.0
jugador_y_cambio_positivo = 0.0
jugador_y_cambio_negativo = 0.0

pedido_actual = None
tiene_paquete = False
ultimo_tick_energia = pygame.time.get_ticks()
msg = "Bienvenido a Courier Quest"

# -------------------- Reputación: reglas e implementación --------------------

def calcular_pago(base_pago):
    """Aplica bonus de reputación: +5% si reputación >= 90"""
    global reputacion
    if reputacion >= 90:
        return int(round(base_pago * 1.05))
    return int(base_pago)


def actualizar_reputacion(evento, tiempo_retraso_seg=0):
    """Aplica la regla de reputación. Devuelve (cambio, game_over_bool).

    evento: 'temprano', 'a_tiempo', 'tarde', 'cancelado', 'perdido'
    tiempo_retraso_seg: segundos de retraso (solo para 'tarde')
    """
    global reputacion, racha_sin_penalizacion, primera_tardanza_fecha

    cambio = 0

    if evento == "temprano":
        cambio = +5
        racha_sin_penalizacion += 1
    elif evento == "a_tiempo":
        cambio = +3
        racha_sin_penalizacion += 1
    elif evento == "tarde":
        # determinar penalización base
        if tiempo_retraso_seg <= 30:
            penal = -2
        elif tiempo_retraso_seg <= 120:
            penal = -5
        else:
            penal = -10

        # Primera tardanza del día: mitad de penalización si reputación >= 85
        today = datetime.now().date()
        if reputacion >= 85 and (primera_tardanza_fecha is None or primera_tardanza_fecha != today):
            # aplicar mitad (redondear hacia 0)
            penal = int(math.ceil(penal / 2.0)) if penal < 0 else penal
            primera_tardanza_fecha = today

        cambio = penal
        # cortar racha
        racha_sin_penalizacion = 0
    elif evento == "cancelado":
        cambio = -4
        racha_sin_penalizacion = 0
    elif evento == "perdido":
        cambio = -6
        racha_sin_penalizacion = 0

    # Bono por racha de 3 entregas sin penalización: +2 (se aplica una vez y reinicia la racha)
    if racha_sin_penalizacion >= 3:
        cambio += 2
        racha_sin_penalizacion = 0

    reputacion = max(0, min(100, reputacion + cambio))

    game_over = reputacion < 20
    return cambio, game_over

# -------------------- Funciones auxiliares --------------------

def dentro_pantalla(rect):
    return pantalla.get_rect().contains(rect)


def punto_valido(x, y):
    p = pygame.Rect(0, 0, 32, 32)
    p.center = (x, y)
    if not dentro_pantalla(p):
        return False
    for w in OBSTACULOS:
        if p.colliderect(w):
            return False
    return True


def spawnear_cliente(lejos_de, min_dist=180):
    for _ in range(400):
        x = random.randint(40, ANCHO - 40)
        y = random.randint(40, ALTO - 40)
        if punto_valido(x, y) and math.hypot(x - lejos_de[0], y - lejos_de[1]) >= min_dist:
            return img_cliente.get_rect(center=(x, y))
    return img_cliente.get_rect(center=(80, 80))


def nuevo_pedido():
    pickup = spawnear_cliente(jugador_rect.center)
    dropoff = spawnear_cliente(pickup.center)
    now = pygame.time.get_ticks()
    duration = random.randint(60000, 120000)
    return {
        "pickup": pickup,
        "dropoff": dropoff,
        "payout": random.randint(10, 50),
        "peso": random.randint(1, 10),
        "deadline": now + duration,
        "created_at": now,
        "duration": duration
    }


def mover_con_colision(rect: pygame.Rect, dx: float, dy: float, paredes):
    # mover en X
    rect.x += int(round(dx))
    for w in paredes:
        if rect.colliderect(w):
            if dx > 0:
                rect.right = w.left
            elif dx < 0:
                rect.left = w.right
    # mover en Y
    rect.y += int(round(dy))
    for w in paredes:
        if rect.colliderect(w):
            if dy > 0:
                rect.bottom = w.top
            elif dy < 0:
                rect.top = w.bottom
    rect.clamp_ip(pantalla.get_rect())

# -------------------- Guardar/Cargar partida --------------------

def snapshot_partida():
    return {
        "jugador": {"x": jugador_rect.x, "y": jugador_rect.y},
        "pedido": {
            "pickup": [pedido_actual["pickup"].x, pedido_actual["pickup"].y,
                       pedido_actual["pickup"].width, pedido_actual["pickup"].height],
            "dropoff": [pedido_actual["dropoff"].x, pedido_actual["dropoff"].y,
                        pedido_actual["dropoff"].width, pedido_actual["dropoff"].height],
            "payout": pedido_actual["payout"],
            "peso": pedido_actual["peso"],
            "deadline": pedido_actual["deadline"],
            "created_at": pedido_actual.get("created_at"),
            "duration": pedido_actual.get("duration")
        } if pedido_actual else None,
        "tiene_paquete": tiene_paquete,
        "entregas": entregas,
        "energia": energia,
        "dinero": dinero_ganado,
        "reputacion": reputacion,
        "msg": msg,
        "racha_sin_penalizacion": racha_sin_penalizacion,
        "primera_tardanza_fecha": primera_tardanza_fecha.isoformat() if primera_tardanza_fecha else None
    }


def aplicar_partida(data):
    global jugador_rect, pedido_actual, tiene_paquete, entregas, energia, dinero_ganado, reputacion, msg
    global racha_sin_penalizacion, primera_tardanza_fecha

    if not data:
        return

    j = data.get("jugador")
    if j:
        jugador_rect.topleft = (int(j.get("x", jugador_rect.x)), int(j.get("y", jugador_rect.y)))

    p = data.get("pedido")
    if p:
        try:
            pedido_actual = {
                "pickup": pygame.Rect(*p["pickup"]),
                "dropoff": pygame.Rect(*p["dropoff"]),
                "payout": p["payout"],
                "peso": p["peso"],
                "deadline": p["deadline"],
                "created_at": p.get("created_at", pygame.time.get_ticks()),
                "duration": p.get("duration", max(60000, p.get("deadline", pygame.time.get_ticks()) - p.get("created_at", pygame.time.get_ticks())))
            }
        except Exception:
            pedido_actual = nuevo_pedido()
    else:
        pedido_actual = nuevo_pedido()

    tiene_paquete = data.get("tiene_paquete", False)
    entregas = int(data.get("entregas", 0))
    energia = int(data.get("energia", 100))
    dinero_ganado = int(data.get("dinero", 0))
    reputacion = int(data.get("reputacion", 70))
    msg = data.get("msg", msg)
    racha_sin_penalizacion = int(data.get("racha_sin_penalizacion", 0))

    ptf = data.get("primera_tardanza_fecha")
    if ptf:
        try:
            primera_tardanza_fecha = date.fromisoformat(ptf)
        except Exception:
            primera_tardanza_fecha = None
    else:
        primera_tardanza_fecha = None


def guardar_partida():
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot_partida(), f, ensure_ascii=False, indent=2)
        return True, "Partida guardada"
    except Exception as e:
        return False, f"Error al guardar: {e}"


def cargar_partida():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        aplicar_partida(data)
        return True, "Partida cargada"
    except FileNotFoundError:
        return False, "No hay partida guardada"
    except Exception as e:
        return False, f"Error al cargar: {e}"

# -------------------- Records --------------------

def cargar_records():
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def guardar_records(lista):
    try:
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def registrar_record():
    recs = cargar_records()
    recs.append({
        "entregas": int(entregas),
        "dinero": int(dinero_ganado),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    recs.sort(key=lambda r: (r.get("entregas", 0), r.get("dinero", 0)), reverse=True)
    recs = recs[:10]
    guardar_records(recs)

# -------------------- Sistema de Clima --------------------
# Mapeo reducido: display en español
CLIMAS_ES = {
    "clear": "Despejado",
    "clouds": "Nublado",
    "rain_light": "Lluvia ligera",
    "rain": "Lluvia",
    "storm": "Tormenta",
    "fog": "Niebla",
    "wind": "Viento",
    "heat": "Calor",
    "cold": "Frío"
}

# Matriz de transición Markov (completa)
TRANSICIONES = {
    "clear": [
        ("clear", 0.40), ("clouds", 0.25), ("rain_light", 0.10),
        ("fog", 0.05), ("wind", 0.05), ("heat", 0.10), ("cold", 0.05)
    ],
    "clouds": [
        ("clear", 0.20), ("clouds", 0.40), ("rain_light", 0.15),
        ("rain", 0.10), ("fog", 0.05), ("wind", 0.05), ("cold", 0.05)
    ],
    "rain_light": [
        ("clouds", 0.20), ("rain_light", 0.30), ("rain", 0.25),
        ("storm", 0.10), ("fog", 0.05), ("clear", 0.10)
    ],
    "rain": [
        ("rain", 0.30), ("rain_light", 0.20), ("storm", 0.20),
        ("clouds", 0.20), ("clear", 0.10)
    ],
    "storm": [
        ("storm", 0.30), ("rain", 0.30), ("rain_light", 0.15),
        ("clouds", 0.15), ("clear", 0.10)
    ],
    "fog": [
        ("fog", 0.30), ("clouds", 0.25), ("clear", 0.20),
        ("rain_light", 0.10), ("rain", 0.10), ("cold", 0.05)
    ],
    "wind": [
        ("wind", 0.30), ("clear", 0.25), ("clouds", 0.20),
        ("rain_light", 0.10), ("rain", 0.10), ("storm", 0.05)
    ],
    "heat": [
        ("heat", 0.40), ("clear", 0.30), ("clouds", 0.15),
        ("wind", 0.10), ("storm", 0.05)
    ],
    "cold": [
        ("cold", 0.40), ("clouds", 0.25), ("clear", 0.20),
        ("fog", 0.10), ("snow", 0.05)
    ]
}

# Estado inicial del clima: siempre start en clear
clima_actual = "clear"
intensidad_actual = random.uniform(0.3, 0.7)
intensidad_inicio = intensidad_actual
clima_objetivo = clima_actual
intensidad_objetivo = intensidad_actual
transicion = False
transicion_inicio = 0  # ms (usamos time en segundos en varias partes, aquí usaremos time.get_ticks ms)
transicion_duracion = 0  # ms
ultimo_cambio_clima = pygame.time.get_ticks()  # ms
duracion_actual = random.uniform(45000, 60000)  # ms

def elegir_siguiente_clima(actual):
    trans = TRANSICIONES.get(actual, TRANSICIONES["clear"])
    r = random.random()
    acumulado = 0.0
    for estado, prob in trans:
        acumulado += prob
        if r <= acumulado:
            return estado
    return actual

def iniciar_transicion(nuevo_clima, ahora_ms):
    """Prepara variables para una transición suave"""
    global clima_objetivo, intensidad_objetivo, transicion, transicion_inicio, transicion_duracion, intensidad_inicio
    clima_objetivo = nuevo_clima
    intensidad_objetivo = random.uniform(0.3, 1.0)
    intensidad_inicio = intensidad_actual
    transicion = True
    transicion_inicio = ahora_ms
    transicion_duracion = random.uniform(3000, 5000)  # ms

def actualizar_clima():
    """Se llama cada frame. Controla ráfagas y transiciones (usa ms de pygame)."""
    global clima_actual, intensidad_actual, clima_objetivo, intensidad_objetivo
    global transicion, transicion_inicio, transicion_duracion, intensidad_inicio
    global ultimo_cambio_clima, duracion_actual

    ahora = pygame.time.get_ticks()  # ms

    if transicion:
        # proteger división por cero
        dur = transicion_duracion if transicion_duracion > 0 else 1
        t = (ahora - transicion_inicio) / dur
        if t >= 1.0:
            # fin transición
            clima_actual = clima_objetivo
            intensidad_actual = intensidad_objetivo
            transicion = False
            ultimo_cambio_clima = ahora
            duracion_actual = random.uniform(45000, 60000)
        else:
            # interpolación lineal entre intensidad_inicio y intensidad_objetivo
            intensidad_actual = (1 - t) * intensidad_inicio + t * intensidad_objetivo
        return

    # si terminó la ráfaga -> iniciar transición
    if ahora - ultimo_cambio_clima > duracion_actual:
        siguiente = elegir_siguiente_clima(clima_actual)
        iniciar_transicion(siguiente, ahora)

# -------------------- Dibujo --------------------

def dibujar_fondo_y_obs():
    base_color = (51, 124, 196)
    if clima_actual in ("rain", "storm", "rain_light"):
        base_color = (40, 80, 120)
    elif clima_actual in ("clouds", "fog"):
        base_color = (80, 110, 140)
    elif clima_actual in ("heat",):
        base_color = (140, 120, 80)
    elif clima_actual in ("cold",):
        base_color = (90, 110, 140)
    pantalla.fill(base_color)

    for r in OBSTACULOS:
        pygame.draw.rect(pantalla, (170, 120, 80), r, border_radius=6)
        pygame.draw.rect(pantalla, (140, 90, 60), r, 3, border_radius=6)


def dibujar_barra(x, y, valor, max_valor, ancho, alto):
    v = max(0, min(valor, max_valor))
    pygame.draw.rect(pantalla, (60, 60, 60), (x, y, ancho, alto))
    relleno = int((v / max_valor) * ancho) if max_valor > 0 else 0
    if relleno > 0:
        pygame.draw.rect(pantalla, (0, 200, 0), (x, y, relleno, alto))


def dibujar_menu(opciones, seleccionado, titulo="Courier Quest", subtitulo="Usa ↑/↓ y ENTER"):
    pantalla.fill((20, 24, 28))
    t = font_big.render(titulo, True, (255, 255, 255))
    pantalla.blit(t, (ANCHO // 2 - t.get_width() // 2, 140))
    s = font.render(subtitulo, True, (200, 200, 200))
    pantalla.blit(s, (ANCHO // 2 - s.get_width() // 2, 200))
    y0 = 280
    for i, op in enumerate(opciones):
        color = (255, 255, 0) if i == seleccionado else (220, 220, 220)
        surf = font.render(op, True, color)
        pantalla.blit(surf, (ANCHO // 2 - surf.get_width() // 2, y0 + i * 44))


def dibujar_records():
    pantalla.fill((20, 24, 28))
    t = font_big.render("Records", True, (255, 255, 255))
    pantalla.blit(t, (ANCHO // 2 - t.get_width() // 2, 120))
    recs = cargar_records()
    if not recs:
        pantalla.blit(font.render("No hay records aún.", True, (220, 220, 220)), (ANCHO // 2 - 120, 220))
    else:
        y = 220
        for idx, r in enumerate(recs, 1):
            linea = f"{idx:>2}. Entregas: {r.get('entregas',0):>3}  |  Dinero: {r.get('dinero',0):>4}  |  {r.get('fecha','')}"
            pantalla.blit(font.render(linea, True, (230, 230, 230)), (ANCHO // 2 - 280, y))
            y += 34
    pantalla.blit(font.render("ESC: volver", True, (200, 200, 200)), (20, ALTO - 40))


def dibujar_hud():
    y = 8
    linea_clima = f"Clima: {CLIMAS_ES.get(clima_actual, clima_actual)} ({intensidad_actual:.2f})"
    lineas = (
        "Q: aceptar | R: rechazar | E: entregar | G: guardar | ESC: menú",
        f"Entregas: {entregas}",
        f"Dinero ganado: {dinero_ganado} $",
        f"Reputación: {reputacion}",
        linea_clima,
        msg,
    )
    for linea in lineas:
        pantalla.blit(font.render(linea, True, (255, 255, 255)), (10, y))
        y += 26

    pantalla.blit(font.render("Energía:", True, (255, 255, 255)), (10, y))
    dibujar_barra(100, y, energia, 100, 200, 18)

    # mostrar multiplicador si aplica
    if reputacion >= 90:
        pantalla.blit(font.render("Pago: +5% (Excelencia)", True, (255, 220, 120)), (320, 8))

# -------------------- Máquina de estados --------------------
INICIO, MENU, GAME, RECORDS = 0, 1, 2, 3
estado = MENU
menu_idx = 0
menu_msg = ""


def reset_partida():
    global jugador_rect, pedido_actual, tiene_paquete, entregas, energia, dinero_ganado, reputacion, msg
    global racha_sin_penalizacion, primera_tardanza_fecha
    jugador_rect.topleft = (728, 836)
    pedido_actual = nuevo_pedido()
    tiene_paquete = False
    entregas = 0
    energia = 100
    dinero_ganado = 0
    reputacion = 70
    msg = "Acércate al cliente y acepta (Q) o rechaza (R) el pedido"
    racha_sin_penalizacion = 0
    primera_tardanza_fecha = None

clock = pygame.time.Clock()
corriendo = True

# -------------------- Lazo principal --------------------
while corriendo:
    # Si la energía es 0, pausar el juego 60 segundos y recargar a 70
    if energia == 0:
        msg = "Sin energía. Cargando..."
        dibujar_fondo_y_obs()
        if pedido_actual:
            if not tiene_paquete:
                pygame.draw.rect(pantalla, (0, 255, 0), pedido_actual["pickup"], 3)
                pantalla.blit(img_cliente, pedido_actual["pickup"].topleft)
            else:
                pygame.draw.rect(pantalla, (255, 0, 0), pedido_actual["dropoff"], 3)
                pantalla.blit(img_cliente, pedido_actual["dropoff"].topleft)
        pantalla.blit(img_jugador, jugador_rect.topleft)
        dibujar_hud()
        pygame.display.flip()
        pygame.time.wait(60000)
        energia = 70
        msg = "Energía recargada a 70. Continúa jugando."
        ultimo_tick_energia = pygame.time.get_ticks()
        continue

    dt = clock.tick(FPS) / 1000.0
    ahora = pygame.time.get_ticks()

    # -------- Velocidad dinámica --------
    peso_total = pedido_actual["peso"] if (pedido_actual and tiene_paquete) else 0
    Mpeso = max(0.8, 1 - 0.03 * peso_total)
    Mrep = 1.03 if reputacion >= 90 else 1.0
    if energia > 30:
        Mresistencia = 1.0
    elif energia > 10:
        Mresistencia = 0.8
    else:
        Mresistencia = 0.0
    Mclima = {
        "clear": 1.0,
        "clouds": 0.97,
        "rain_light": 0.95,
        "rain": 0.9,
        "storm": 0.85,
        "fog": 0.95,
        "wind": 0.9,
        "heat": 0.92,
        "cold": 0.95
    }.get(clima_actual, 1.0)
    surf_weight = 1.0
    VEL = v0 * Mpeso * Mrep * Mresistencia * Mclima * surf_weight

    # Estados de menú
    if estado == MENU:
        opciones = ["Nuevo juego", "Cargar partida", "Records", "Salir"]
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                corriendo = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    menu_idx = (menu_idx - 1) % len(opciones)
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    menu_idx = (menu_idx + 1) % len(opciones)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    seleccion = opciones[menu_idx]
                    if seleccion == "Nuevo juego":
                        reset_partida()
                        menu_msg = ""
                        estado = GAME
                    elif seleccion == "Cargar partida":
                        ok, m = cargar_partida()
                        menu_msg = m
                        if ok:
                            estado = GAME
                    elif seleccion == "Records":
                        estado = RECORDS
                    elif seleccion == "Salir":
                        corriendo = False
        dibujar_menu(opciones, menu_idx)
        if menu_msg:
            info = font.render(menu_msg, True, (255, 220, 120))
            pantalla.blit(info, (ANCHO // 2 - info.get_width() // 2, 280 + len(opciones) * 44 + 20))
        pygame.display.flip()
        continue

    if estado == RECORDS:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                corriendo = False
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                estado = MENU
        dibujar_records()
        pygame.display.flip()
        continue

    # -------------------- Actualizaciones por frame --------------------
    actualizar_clima()

    # Disminuir energía una vez por segundo si se está moviendo
    if ahora - ultimo_tick_energia >= 1000:
        moving = (jugador_x_cambio_positivo != 0.0 or jugador_x_cambio_negativo != 0.0 or
                  jugador_y_cambio_positivo != 0.0 or jugador_y_cambio_negativo != 0.0)
        if moving:
            costo_por_clima = {
                "clear": 1,
                "clouds": 1,
                "rain_light": 2,
                "rain": 3,
                "storm": 4,
                "fog": 1.5,
                "wind": 2,
                "heat": 1.2,
                "cold": 1.2
            }
            costo = costo_por_clima.get(clima_actual, 1)
            if tiene_paquete and pedido_actual:
                costo += pedido_actual["peso"] // 5
            energia = max(0, energia - int(round(costo)))
        ultimo_tick_energia = ahora

    # -------------------- Manejo eventos --------------------
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            registrar_record()
            corriendo = False
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                registrar_record()
                estado = MENU
                menu_msg = "Sesión guardada en records"
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                jugador_y_cambio_positivo = 0.1
            elif evento.key in (pygame.K_UP, pygame.K_w):
                jugador_y_cambio_negativo = -0.1
            elif evento.key in (pygame.K_LEFT, pygame.K_a):
                jugador_x_cambio_negativo = -0.1
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                jugador_x_cambio_positivo = 0.1
            elif evento.key == pygame.K_q:  # aceptar pedido
                if pedido_actual and jugador_rect.colliderect(pedido_actual["pickup"]) and not tiene_paquete:
                    tiene_paquete = True
                    msg = f"Pedido aceptado ({pedido_actual['peso']}kg)"
            elif evento.key == pygame.K_r:  # rechazar o cancelar pedido
                # Rechazar sin paquete (descartar oferta): no penaliza según reglas nuevas
                if pedido_actual and jugador_rect.colliderect(pedido_actual["pickup"]) and not tiene_paquete:
                    pedido_actual = nuevo_pedido()
                    msg = "Pedido rechazado"
                # Si ya tiene paquete, cancelar pedido aceptado -> penalización -4
                elif tiene_paquete and pedido_actual:
                    cambio, game_over = actualizar_reputacion('cancelado')
                    tiene_paquete = False
                    pedido_actual = nuevo_pedido()
                    msg = f"Pedido cancelado. Reputación {reputacion} ({cambio})"
                    if game_over:
                        msg = "¡Has perdido! Tu reputación llegó a menos de 20."
                        registrar_record()
                        pygame.display.flip()
                        pygame.time.wait(2000)
                        estado_juego = "menu"
                        break
            elif evento.key == pygame.K_e:  # entregar pedido
                if tiene_paquete and pedido_actual and jugador_rect.colliderect(pedido_actual["dropoff"]):
                    now = pygame.time.get_ticks()
                    duration = pedido_actual.get("duration", max(60000, pedido_actual["deadline"] - pedido_actual.get("created_at", now)))
                    tiempo_restante = pedido_actual["deadline"] - now

                    if tiempo_restante >= 0:
                        # entrega temprana o a tiempo
                        if tiempo_restante >= 0.2 * duration:
                            cambio, game_over = actualizar_reputacion('temprano')
                            msg = "Entrega temprana"
                        else:
                            cambio, game_over = actualizar_reputacion('a_tiempo')
                            msg = "Entrega a tiempo"
                    else:
                        retraso_seg = (now - pedido_actual["deadline"]) / 1000.0
                        cambio, game_over = actualizar_reputacion('tarde', retraso_seg)
                        msg = f"Entrega tardía ({int(retraso_seg)}s)"

                    # Aplicar pago y contadores
                    dinero_ganado += calcular_pago(pedido_actual.get("payout", 0))
                    entregas += 1
                    tiene_paquete = False
                    pedido_actual = nuevo_pedido()

                    if game_over:
                        msg = "¡Has perdido! Tu reputación llegó a menos de 20."
                        registrar_record()
                        pygame.display.flip()
                        pygame.time.wait(2000)
                        estado_juego = "menu"
                        break

        elif evento.type == pygame.KEYUP:
            # detener movimiento al soltar tecla correspondiente
            if evento.key in (pygame.K_DOWN, pygame.K_s):
                jugador_y_cambio_positivo = 0.0
            elif evento.key in (pygame.K_UP, pygame.K_w):
                jugador_y_cambio_negativo = 0.0
            elif evento.key in (pygame.K_LEFT, pygame.K_a):
                jugador_x_cambio_negativo = 0.0
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                jugador_x_cambio_positivo = 0.0

    # -------------------- Movimiento --------------------
    vx_raw = jugador_x_cambio_positivo + jugador_x_cambio_negativo
    vy_raw = jugador_y_cambio_positivo + jugador_y_cambio_negativo
    dx = dy = 0.0
    if vx_raw != 0.0 or vy_raw != 0.0:
        l = math.hypot(vx_raw, vy_raw)
        if l != 0:
            ux, uy = vx_raw / l, vy_raw / l
            dx, dy = ux * VEL * dt, uy * VEL * dt
    mover_con_colision(jugador_rect, dx, dy, OBSTACULOS)

    # Comprobar expiración del paquete aceptado
    if pedido_actual and tiene_paquete and ahora > pedido_actual["deadline"]:
        cambio, game_over = actualizar_reputacion('perdido')
        racha_sin_penalizacion = 0
        if game_over:
            msg = "¡Has perdido! Tu reputación llegó a menos de 20."
            registrar_record()
            pygame.display.flip()
            pygame.time.wait(2000)
            estado_juego = "menu"
            break
        else:
            msg = "El paquete expiró"
        tiene_paquete = False
        pedido_actual = nuevo_pedido()

    # Dibujar escena
    dibujar_fondo_y_obs()
    if pedido_actual:
        if not tiene_paquete:
            pygame.draw.rect(pantalla, (0, 255, 0), pedido_actual["pickup"], 3)
            pantalla.blit(img_cliente, pedido_actual["pickup"].topleft)
        else:
            pygame.draw.rect(pantalla, (255, 0, 0), pedido_actual["dropoff"], 3)
            pantalla.blit(img_cliente, pedido_actual["dropoff"].topleft)
    pantalla.blit(img_jugador, jugador_rect.topleft)
    dibujar_hud()
    pygame.display.flip()

pygame.quit()
