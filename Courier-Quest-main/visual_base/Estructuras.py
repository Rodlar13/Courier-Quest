import requests
import random
import math
import json
import os
from datetime import datetime
import pygame

# -------------------- Configuración API --------------------
BASE_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"

def obtener_datos_API(endpoint, archivo):
    try:
        r = requests.get(BASE_URL + endpoint, timeout=5)
        datos = r.json()
        with open(archivo, "w") as f:
            json.dump(datos, f, indent=2)
        print(f"Archivo {archivo} actualizado desde el API.")
        return datos
    except:
        print(f"No se pudo conectar. Revisando archivo {archivo}...")
        if os.path.exists(archivo):
            with open(archivo, "r") as f:
                return json.load(f)
        else:
            print("No hay datos disponibles.")
            return None

def cargarDatosAPI():
    mapa = obtener_datos_API("/city/map", "ciudad.json")
    jobs = obtener_datos_API("/city/jobs", "pedidos.json")
    clima = obtener_datos_API("/city/weather", "weather.json")
    return mapa, jobs, clima

cargarDatosAPI()

# -------------------- Configuración general --------------------
ANCHO, ALTO = 1500, 900
FPS = 60
VEL = 300.0  # píxeles/seg
SAVE_FILE = "partida.json"
RECORDS_FILE = "records.json"

pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Courier Quest")

# -------------------- Imágenes --------------------
TAM_JUGADOR = (48, 48)
TAM_CLIENTE = (42, 42)
TAM_ICONO = (32, 32)

icono = pygame.image.load("mensajero.png")
icono = pygame.transform.smoothscale(icono, TAM_ICONO)
pygame.display.set_icon(icono)

img_jugador = pygame.image.load("mensajero.png").convert_alpha()
img_jugador = pygame.transform.smoothscale(img_jugador, TAM_JUGADOR)

img_cliente = pygame.image.load("audiencia.png").convert_alpha()
img_cliente = pygame.transform.smoothscale(img_cliente, TAM_CLIENTE)

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

# Clima
climas = ["soleado", "lluvia", "tormenta"]
clima_actual = random.choice(climas)
ultimo_cambio_clima = pygame.time.get_ticks()
TIEMPO_CLIMA = 45000  # 45 seg

ultimo_tick_energia = pygame.time.get_ticks()

# -------------------- Funciones auxiliares --------------------

def dentro_pantalla(rect):
    return pantalla.get_rect().contains(rect)

def punto_valido(x, y):
    p = pygame.Rect(0, 0, 32, 32)
    p.center = (x, y)
    if not dentro_pantalla(p): return False
    for w in OBSTACULOS:
        if p.colliderect(w): return False
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
            if dx > 0: rect.right = w.left
            elif dx < 0: rect.left = w.right
    # Y
    rect.y += int(round(dy))
    for w in paredes:
        if rect.colliderect(w):
            if dy > 0: rect.bottom = w.top
            elif dy < 0: rect.top = w.bottom
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
        "clima_actual": clima_actual,
    }

def aplicar_partida(data):
    global jugador_rect, pedido_actual, tiene_paquete, entregas, energia, dinero_ganado, reputacion, msg, clima_actual
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

    # Validar pickup/dropoff no esté en obstáculo o fuera pantalla
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
    clima_actual = data.get("clima_actual", random.choice(climas))

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
    pantalla.fill((51, 124, 196))
    for r in OBSTACULOS:
        pygame.draw.rect(pantalla, (170, 120, 80), r, border_radius=6)
        pygame.draw.rect(pantalla, (140, 90, 60), r, 3, border_radius=6)

def dibujar_hud():
    y = 8
    lineas = (
        f"Entregas: {entregas}",
        "WASD/Flechas: mover | Q: aceptar | R: rechazar | E: entregar | G: guardar | ESC: menú",
        f"Energia: {energia_barras} -> {energia} %",
        f"Reputación: {reputacion}",
        f"Dinero ganado: {dinero_ganado} $",
        f"Clima: {clima_actual}",
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

    # Pantalla de inicio eliminada: el juego inicia directamente en el menú principal

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

    # Juego: cambiar clima cada 45 seg
    if ahora - ultimo_cambio_clima > TIEMPO_CLIMA:
        clima_actual = random.choice(climas)
        ultimo_cambio_clima = ahora

    # Disminuir energía cada segundo si se mueve
    if ahora - ultimo_tick_energia >= 1000:
        if jugador_x_cambio_positivo or jugador_x_cambio_negativo or jugador_y_cambio_positivo or jugador_y_cambio_negativo:
            costo = {"soleado": 1, "lluvia": 2, "tormenta": 3}[clima_actual]
            if tiene_paquete:
                costo += pedido_actual["peso"] // 5
            energia = max(0, energia - costo)
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

    # Dibujar
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
