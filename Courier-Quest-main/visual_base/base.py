import pygame
import math
import random
from configurar import ultimo_tick_energia, FPS, v0, ANCHO, ALTO, pantalla, font, jugador_rect, jugador_x_cambio_negativo, jugador_x_cambio_positivo, jugador_y_cambio_negativo, jugador_y_cambio_positivo   
from datos import registrar_record, cargar_partida, entregas, dinero_ganado, reputacion, msg, energia, pedido_actual, tiene_paquete
from obstaculos import OBSTACULOS
from reputacion import actualizar_reputacion, calcular_pago
from base import calcular_pago, actualizar_reputacion
from clima import actualizar_clima, clima_actual    
from graficos import img_jugador, img_cliente, dibujar_fondo_y_obs, dibujar_hud, dibujar_menu, dibujar_records



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


   