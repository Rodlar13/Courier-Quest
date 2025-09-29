import pygame
import sys
import api
import configurar
import datos
import reputacion
import graficos
import clima
import obstaculos



"""
import pygame
import sys
import math
from configurar import pantalla, FPS, font, ANCHO, ALTO, jugador_rect, jugador_x_cambio_positivo, jugador_x_cambio_negativo, jugador_y_cambio_positivo, jugador_y_cambio_negativo, energia, msg, reputacion, dinero_ganado, entregas, pedido_actual, tiene_paquete, ultimo_tick_energia
from api import cargarDatosAPI
from datos import cargar_partida, registrar_record
from graficos import dibujar_menu, dibujar_records, dibujar_fondo_y_obs, dibujar_hud, img_jugador, img_cliente
from base import reset_partida, mover_con_colision, nuevo_pedido
from obstaculos import OBSTACULOS
from reputacion import actualizar_reputacion, calcular_pago
from clima import actualizar_clima, clima_actual

# -------------------- Inicializar --------------------

pygame.init()
clock = pygame.time.Clock()

# Estados de la máquina

MENU, GAME, RECORDS = 1, 2, 3
estado = MENU
menu_idx = 0
menu_msg = ""

# -------------------- Cargar datos iniciales --------------------

print("Cargando datos del API (mapa, pedidos, clima)...")
mapa, jobs, clima = cargarDatosAPI()
print("Listo.")

# -------------------- Lazo principal --------------------

corriendo = True
while corriendo:
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
            pantalla.blit(info, (ANCHO // 2 - info.get_width() // 2, 400))
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
    

if estado == GAME:
    actualizar_clima()
    ahora = pygame.time.get_ticks()

    # Disminuir energía una vez por segundo si se mueve
    if ahora - ultimo_tick_energia >= 1000:
        moving = (jugador_x_cambio_positivo != 0.0 or jugador_x_cambio_negativo != 0.0 or
                  jugador_y_cambio_positivo != 0.0 or jugador_y_cambio_negativo != 0.0)
        if moving:
            energia = max(0, energia - 1)
        ultimo_tick_energia = ahora

    # Eventos
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            registrar_record()
            corriendo = False
        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                registrar_record()
                estado = MENU
                menu_msg = "Sesión guardada en records"
            elif ev.key in (pygame.K_DOWN, pygame.K_s):
                jugador_y_cambio_positivo = 0.1
            elif ev.key in (pygame.K_UP, pygame.K_w):
                jugador_y_cambio_negativo = -0.1
            elif ev.key in (pygame.K_LEFT, pygame.K_a):
                jugador_x_cambio_negativo = -0.1
            elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                jugador_x_cambio_positivo = 0.1
            elif ev.key == pygame.K_q:  # aceptar pedido
                if pedido_actual and jugador_rect.colliderect(pedido_actual["pickup"]) and not tiene_paquete:
                    tiene_paquete = True
                    msg = f"Pedido aceptado ({pedido_actual['peso']}kg)"
            elif ev.key == pygame.K_e:  # entregar pedido
                if tiene_paquete and pedido_actual and jugador_rect.colliderect(pedido_actual["dropoff"]):
                    cambio, game_over = actualizar_reputacion('a_tiempo')
                    dinero_ganado += calcular_pago(pedido_actual["payout"])
                    entregas += 1
                    tiene_paquete = False
                    pedido_actual = nuevo_pedido()
                    msg = f"Entrega completada. Reputación {reputacion} ({cambio})"
                    if game_over:
                        msg = "¡Has perdido! Tu reputación llegó a menos de 20."
                        registrar_record()
                        pygame.display.flip()
                        pygame.time.wait(2000)
                        estado = MENU
                        break
        elif ev.type == pygame.KEYUP:
            if ev.key in (pygame.K_DOWN, pygame.K_s):
                jugador_y_cambio_positivo = 0.0
            elif ev.key in (pygame.K_UP, pygame.K_w):
                jugador_y_cambio_negativo = 0.0
            elif ev.key in (pygame.K_LEFT, pygame.K_a):
                jugador_x_cambio_negativo = 0.0
            elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                jugador_x_cambio_positivo = 0.0

    # Movimiento
    vx_raw = jugador_x_cambio_positivo + jugador_x_cambio_negativo
    vy_raw = jugador_y_cambio_positivo + jugador_y_cambio_negativo
    dx = dy = 0.0
    if vx_raw != 0.0 or vy_raw != 0.0:
        l = math.hypot(vx_raw, vy_raw)
        if l != 0:
            ux, uy = vx_raw / l, vy_raw / l
            dx, dy = ux * 3 * 48 * (1/60), uy * 3 * 48 * (1/60)
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

clock.tick(FPS)

pygame.quit()
sys.exit()
"""