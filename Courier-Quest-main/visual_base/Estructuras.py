# main.py
# -------------------- Librerías -------------------
import requests
import random
import math
import json
import os
from datetime import datetime
import pygame
import time
import sys

# -------------------- Configuración API --------------------
BASE_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"

def obtener_datos_API(endpoint, archivo):
    try:
        r = requests.get(BASE_URL + endpoint, timeout=5)
        datos = r.json()
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print(f"Archivo {archivo} actualizado desde el API.")
        return datos
    except Exception as e:
        print(f"No se pudo conectar ({e}). Revisando archivo {archivo}...")
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        else:
            print("No hay datos disponibles.")
            return None

def cargarDatosAPI():
    mapa = obtener_datos_API("/city/map", "ciudad.json")
    jobs = obtener_datos_API("/city/jobs", "pedidos.json")
    clima = obtener_datos_API("/city/weather", "weather.json")
    return mapa, jobs, clima

# Intentamos cargar (no es crítico fallar)
cargarDatosAPI()

# -------------------- Configuración general --------------------
ANCHO, ALTO = 1500, 900
FPS = 60
VEL = 300.0  # píxeles/seg (se usa para movimiento)
SAVE_FILE = "partida.json"
RECORDS_FILE = "records.json"

pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Courier Quest")

# -------------------- Imágenes --------------------
TAM_JUGADOR = (48, 48)
TAM_CLIENTE = (42, 42)
TAM_ICONO = (32, 32)

# Cargar imágenes (termina si faltan)
try:
    icono = pygame.image.load("mensajero.png")
    icono = pygame.transform.smoothscale(icono, TAM_ICONO)
    pygame.display.set_icon(icono)

    img_jugador = pygame.image.load("mensajero.png").convert_alpha()
    img_jugador = pygame.transform.smoothscale(img_jugador, TAM_JUGADOR)

    img_cliente = pygame.image.load("audiencia.png").convert_alpha()
    img_cliente = pygame.transform.smoothscale(img_cliente, TAM_CLIENTE)
except Exception as e:
    print("No se pudieron cargar imágenes:", e)
    pygame.quit()
    sys.exit("Coloca mensajero.png y audiencia.png en la carpeta y vuelve a intentar.")

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
font = pygame.font.SysFont(None, 28)
font_big = pygame.font.SysFont(None, 56)
msg = "Acércate al cliente y acepta (Q) o rechaza (R) el pedido"
energia = 100
energia_barras = "[ | | | | | | | | | | ]"
dinero_ganado = 0
reputacion = 70
entregas = 0

jugador_rect = img_jugador.get_rect(topleft=(728, 836))
jugador_x_cambio_positivo = 0.0
jugador_x_cambio_negativo = 0.0
jugador_y_cambio_positivo = 0.0
jugador_y_cambio_negativo = 0.0

# Pedido actual y paquete
pedido_actual = None
tiene_paquete = False

ultimo_tick_energia = pygame.time.get_ticks()

# -------------------- Clima (integrado, robusto) --------------------

# Matriz de transición de Markov para todos los climas
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

# Mapeos español <-> inglés
CLIMAS_MAP = {
    "despejado": "clear",
    "soleado": "clear",
    "nublado": "clouds",
    "parcialmente nublado": "clouds",
    "lluvia ligera": "rain_light",
    "llovizna": "rain_light",
    "lluvia": "rain",
    "tormenta": "storm",
    "tormentoso": "storm",
    "niebla": "fog",
    "bruma": "fog",
    "viento": "wind",
    "calor": "heat",
    "frío": "cold",
    "frio": "cold",
}

# Inglés -> Español para HUD (capitalizado)
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

# Estado inicial del clima
clima_actual = "clear"
intensidad_actual = random.uniform(0.3, 0.7)
# Guardar intensidad de inicio para interpolar correctamente
intensidad_inicio = intensidad_actual
clima_objetivo = clima_actual
intensidad_objetivo = intensidad_actual
transicion = False
transicion_inicio = 0  # ms
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

# -------------------- Funciones auxiliares del juego --------------------

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
    return {
        "pickup": pickup,
        "dropoff": dropoff,
        "payout": random.randint(10, 50),
        "peso": random.randint(1, 10),
        "deadline": pygame.time.get_ticks() + random.randint(60000, 120000)
    }

def mover_con_colision(rect: pygame.Rect, dx: float, dy: float, paredes):
    # X
    rect.x += int(round(dx))
    for w in paredes:
        if rect.colliderect(w):
            if dx > 0:
                rect.right = w.left
            elif dx < 0:
                rect.left = w.right
    # Y
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
            "deadline": pedido_actual["deadline"]
        } if pedido_actual else None,
        "tiene_paquete": tiene_paquete,
        "entregas": entregas,
        "energia": energia,
        "dinero": dinero_ganado,
        "reputacion": reputacion,
        "msg": msg,
        "clima_actual": clima_actual,               # estado interno (inglés)
        "clima_display": CLIMAS_ES.get(clima_actual, clima_actual),  # opcional, para lectura
        "intensidad_actual": float(intensidad_actual)
    }

def aplicar_partida(data):
    global jugador_rect, pedido_actual, tiene_paquete, entregas, energia, dinero_ganado, reputacion, msg, clima_actual, intensidad_actual, ultimo_cambio_clima, duracion_actual, transicion
    jx, jy = data["jugador"]["x"], data["jugador"]["y"]
    jugador_rect.topleft = (int(jx), int(jy))

    p = data.get("pedido")
    if p:
        pedido_actual = {
            "pickup": pygame.Rect(*p["pickup"]),
            "dropoff": pygame.Rect(*p["dropoff"]),
            "payout": p["payout"],
            "peso": p["peso"],
            "deadline": p["deadline"]
        }
    else:
        pedido_actual = nuevo_pedido()

    # Validar pickup/dropoff
    if pedido_actual and (any(pedido_actual["pickup"].colliderect(w) for w in OBSTACULOS) or not dentro_pantalla(pedido_actual["pickup"])):
        pedido_actual["pickup"] = spawnear_cliente(jugador_rect.center)
    if pedido_actual and (any(pedido_actual["dropoff"].colliderect(w) for w in OBSTACULOS) or not dentro_pantalla(pedido_actual["dropoff"])):
        pedido_actual["dropoff"] = spawnear_cliente(pedido_actual["pickup"].center)

    tiene_paquete = data.get("tiene_paquete", False)
    entregas = int(data.get("entregas", 0))
    energia = int(data.get("energia", 100))
    dinero_ganado = int(data.get("dinero", 0))
    reputacion = int(data.get("reputacion", 70))
    msg = data.get("msg", "Partida cargada")

    # Cargar clima: aceptar tanto inglés como español en archivo de guardado
    saved_clima = data.get("clima_actual") or data.get("clima_display")
    if saved_clima:
        sc = str(saved_clima).strip().lower()
        # si está en inglés y es conocido:
        if sc in TRANSICIONES:
            clima_actual = sc
        else:
            # intentar mapear de español a inglés
            if sc in CLIMAS_MAP:
                clima_actual = CLIMAS_MAP[sc]
            else:
                # intentar buscar palabra dentro del string
                encontrado = None
                for esp, ing in CLIMAS_MAP.items():
                    if esp in sc:
                        encontrado = ing
                        break
                clima_actual = encontrado if encontrado else "clear"
    else:
        clima_actual = random.choice(list(TRANSICIONES.keys()))

    intensidad_actual = float(data.get("intensidad_actual", random.uniform(0.3, 0.7)))
    # Reiniciar temporizadores para evitar un cambio inmediato
    ultimo_cambio_clima = pygame.time.get_ticks()
    duracion_actual = random.uniform(45000, 60000)
    transicion = False

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
    except:
        return []

def guardar_records(lista):
    try:
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False, indent=2)
    except:
        pass

def registrar_record():
    recs = cargar_records()
    recs.append({
        "entregas": int(entregas),
        "dinero": int(dinero_ganado),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    # Top 10 por entregas desc, dinero desc
    recs.sort(key=lambda r: (r.get("entregas", 0), r.get("dinero", 0)), reverse=True)
    recs = recs[:10]
    guardar_records(recs)

# -------------------- Dibujo --------------------

def dibujar_fondo_y_obs():
    # Ajustar color base según clima
    base_color = (51, 124, 196)
    if clima_actual in ("rain", "storm", "rain_light"):
        base_color = (40, 80, 120)
    elif clima_actual in ("clouds", "fog"):
        base_color = (80, 110, 140)
    elif clima_actual in ("heat"):
        base_color = (140, 120, 80)
    elif clima_actual in ("cold"):
        base_color = (90, 110, 140)
    pantalla.fill(base_color)

    for r in OBSTACULOS:
        pygame.draw.rect(pantalla, (170, 120, 80), r, border_radius=6)
        pygame.draw.rect(pantalla, (140, 90, 60), r, 3, border_radius=6)

def dibujar_hud():
    y = 8
    linea_clima = f"Clima: {CLIMAS_ES.get(clima_actual, clima_actual)} ({intensidad_actual:.2f})"
    lineas = (
        f"Entregas: {entregas}",
        "WASD/Flechas: mover | Q: aceptar | R: rechazar | E: entregar | G: guardar | ESC: menú",
        f"Energia: {energia_barras} -> {energia} %",
        f"Reputación: {reputacion}",
        f"Dinero ganado: {dinero_ganado} $",
        linea_clima,
        msg,
    )
    for linea in lineas:
        pantalla.blit(font.render(linea, True, (255, 255, 255)), (10, y))
        y += 26

def dibujar_menu(opciones, seleccionado, titulo="Courier Quest", subtitulo="Usa ↑/↓ y ENTER"):
    pantalla.fill((20, 24, 28))
    t = font_big.render(titulo, True, (255, 255, 255))
    pantalla.blit(t, (ANCHO//2 - t.get_width()//2, 140))
    s = font.render(subtitulo, True, (200, 200, 200))
    pantalla.blit(s, (ANCHO//2 - s.get_width()//2, 200))
    y0 = 280
    for i, op in enumerate(opciones):
        color = (255, 255, 0) if i == seleccionado else (220, 220, 220)
        surf = font.render(op, True, color)
        pantalla.blit(surf, (ANCHO//2 - surf.get_width()//2, y0 + i*44))

def dibujar_records():
    pantalla.fill((20, 24, 28))
    t = font_big.render("Records", True, (255, 255, 255))
    pantalla.blit(t, (ANCHO//2 - t.get_width()//2, 120))
    recs = cargar_records()
    if not recs:
        pantalla.blit(font.render("No hay records aún.", True, (220, 220, 220)),
                      (ANCHO//2 - 120, 220))
    else:
        y = 220
        for idx, r in enumerate(recs, 1):
            linea = f"{idx:>2}. Entregas: {r.get('entregas',0):>3}  |  Dinero: {r.get('dinero',0):>4}  |  {r.get('fecha','')}"
            pantalla.blit(font.render(linea, True, (230, 230, 230)), (ANCHO//2 - 280, y))
            y += 34
    pantalla.blit(font.render("ESC: volver", True, (200, 200, 200)), (20, ALTO - 40))

# -------------------- Máquina de estados --------------------
INICIO, MENU, GAME, RECORDS = 0, 1, 2, 3
estado = MENU
menu_idx = 0
menu_msg = ""

def reset_partida():
    global jugador_rect, pedido_actual, tiene_paquete, entregas, energia, dinero_ganado, reputacion, msg
    jugador_rect.topleft = (728, 836)
    pedido_actual = nuevo_pedido()
    tiene_paquete = False
    entregas = 0
    energia = 100
    dinero_ganado = 0
    reputacion = 70
    msg = "Acércate al cliente y acepta (Q) o rechaza (R) el pedido"

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
            pantalla.blit(info, (ANCHO//2 - info.get_width()//2, 280 + len(opciones)*44 + 20))
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
    # Actualizar clima (usa Markov + transiciones suaves)
    actualizar_clima()

    # Disminuir energía una vez por segundo si se está moviendo
    if ahora - ultimo_tick_energia >= 1000:
        if jugador_x_cambio_positivo or jugador_x_cambio_negativo or jugador_y_cambio_positivo or jugador_y_cambio_negativo:
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

    # Manejo eventos
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            registrar_record()
            corriendo = False
        elif evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                registrar_record()
                estado = MENU
                menu_msg = "Sesión guardada en records"
            elif evento.key == pygame.K_DOWN or evento.key == pygame.K_s:
                jugador_y_cambio_positivo = 0.1
            elif evento.key == pygame.K_UP or evento.key == pygame.K_w:
                jugador_y_cambio_negativo = -0.1
            elif evento.key == pygame.K_LEFT or evento.key == pygame.K_a:
                jugador_x_cambio_negativo = -0.1
            elif evento.key == pygame.K_RIGHT or evento.key == pygame.K_d:
                jugador_x_cambio_positivo = 0.1
            elif evento.key == pygame.K_q:  # aceptar pedido
                if pedido_actual and jugador_rect.colliderect(pedido_actual["pickup"]) and not tiene_paquete:
                    tiene_paquete = True
                    msg = f"Pedido aceptado ({pedido_actual['peso']}kg)"
            elif evento.key == pygame.K_r:  # rechazar pedido
                if pedido_actual and jugador_rect.colliderect(pedido_actual["pickup"]) and not tiene_paquete:
                    pedido_actual = nuevo_pedido()
                    reputacion = max(0, reputacion - 5)
                    if reputacion <= 30:
                        msg = "¡Has perdido! Tu reputación llegó a 30."
                        registrar_record()
                        pygame.display.flip()
                        pygame.time.wait(2000)
                        corriendo = False
                        break
                    else:
                        msg = "Pedido rechazado"
            elif evento.key == pygame.K_e:  # entregar pedido
                if tiene_paquete and pedido_actual and jugador_rect.colliderect(pedido_actual["dropoff"]):
                    entregas += 1
                    dinero_ganado += pedido_actual["payout"]
                    reputacion = min(100, reputacion + 5)
                    msg = "Entrega realizada"
                    tiene_paquete = False
                    pedido_actual = nuevo_pedido()
                else:
                    msg = "No tienes pedido o no estás en destino"
            elif evento.key == pygame.K_g:  # guardar partida
                ok, m = guardar_partida()
                msg = m
        elif evento.type == pygame.KEYUP:
            if evento.key == pygame.K_LEFT or evento.key == pygame.K_a:
                jugador_x_cambio_negativo = 0.0
            elif evento.key == pygame.K_RIGHT or evento.key == pygame.K_d:
                jugador_x_cambio_positivo = 0.0
            elif evento.key == pygame.K_UP or evento.key == pygame.K_w:
                jugador_y_cambio_negativo = 0.0
            elif evento.key == pygame.K_DOWN or evento.key == pygame.K_s:
                jugador_y_cambio_positivo = 0.0

    # Movimiento fluido
    vx_raw = jugador_x_cambio_positivo + jugador_x_cambio_negativo
    vy_raw = jugador_y_cambio_positivo + jugador_y_cambio_negativo
    dx = dy = 0.0
    if vx_raw != 0.0 or vy_raw != 0.0:
        l = math.hypot(vx_raw, vy_raw)
        ux, uy = vx_raw / l, vy_raw / l
        dx, dy = ux * VEL * dt, uy * VEL * dt
    mover_con_colision(jugador_rect, dx, dy, OBSTACULOS)

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
