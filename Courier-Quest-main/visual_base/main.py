
import pygame
import sys
import random
import math
from configurar import *
import datos
from reputacion import *
from clima import *
from base import *
from graficos import *
from datos import *

def main():
    
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Courier Quest")
    
    
    font = pygame.font.SysFont(None, 22)
    font_big = pygame.font.SysFont(None, 44)
    
    
    icono = cargar_imagen_robusta("mensajero.png", TAM_ICONO, exit_on_fail=False)
    pygame.display.set_icon(icono)
    img_jugador = cargar_imagen_robusta("mensajero.png", TAM_JUGADOR)
    img_cliente = cargar_imagen_robusta("audiencia.png", TAM_CLIENTE)
    
    
    obstaculos = [pygame.Rect(*obs) for obs in OBSTACULOS]
    
    
    energia = 100
    dinero_ganado = 0
    reputacion = 70
    entregas = 0
    racha_sin_penalizacion = 0
    primera_tardanza_fecha = None
    
    jugador_rect = img_jugador.get_rect(topleft=(728, 836))
    jugador_x_cambio_positivo = 0.0
    jugador_x_cambio_negativo = 0.0
    jugador_y_cambio_positivo = 0.0
    jugador_y_cambio_negativo = 0.0
    
    pedido_actual = None
    tiene_paquete = False
    ultimo_tick_energia = pygame.time.get_ticks()
    msg = "Bienvenido a Courier Quest"
    
    estado = MENU
    menu_idx = 0
    menu_msg = ""
    
    
    weather_system = WeatherSystem()
    
    
    datos.cargarDatosAPI(BASE_URL)
    
    def spawnear_cliente(lejos_de, img_cliente, min_dist=180):
        """Generate a valid position for a client"""
        for _ in range(400):
            x = random.randint(40, ANCHO - 40)
            y = random.randint(40, ALTO - 40)
            p = pygame.Rect(0, 0, 32, 32)
            p.center = (x, y)
            
            
            if not pantalla.get_rect().contains(p):
                continue
                
            valid = True
            for w in obstaculos:
                if p.colliderect(w):
                    valid = False
                    break
                    
            if valid and math.hypot(x - lejos_de[0], y - lejos_de[1]) >= min_dist:
                return img_cliente.get_rect(center=(x, y))
        return img_cliente.get_rect(center=(80, 80))
    
    def reset_partida():
        nonlocal jugador_rect, pedido_actual, tiene_paquete, entregas, energia, dinero_ganado, reputacion, msg
        nonlocal racha_sin_penalizacion, primera_tardanza_fecha
        
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
    
    def nuevo_pedido():
        pickup = spawnear_cliente(jugador_rect.center, img_cliente)
        dropoff = spawnear_cliente(pickup.center, img_cliente)
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
    
    def calcular_velocidad(peso_total, reputacion, energia, weather_multiplier):
        """Calculate player velocity based on various factors"""
        Mpeso = max(0.8, 1 - 0.03 * peso_total)
        Mrep = 1.03 if reputacion >= 90 else 1.0
        
        if energia > 30:
            Mresistencia = 1.0
        elif energia > 10:
            Mresistencia = 0.8
        else:
            Mresistencia = 0.0
            
        surf_weight = 1.0
        return v0 * Mpeso * Mrep * Mresistencia * weather_multiplier * surf_weight
    
    def calcular_movimiento(vx_raw, vy_raw, VEL, dt):
        """Calculate movement vector"""
        dx = dy = 0.0
        if vx_raw != 0.0 or vy_raw != 0.0:
            l = math.hypot(vx_raw, vy_raw)
            if l != 0:
                ux, uy = vx_raw / l, vy_raw / l
                dx, dy = ux * VEL * dt, uy * VEL * dt
        return dx, dy
    
    def mover_con_colision(rect, dx, dy, paredes):
        """Move rectangle with collision detection"""
        rect.x += int(round(dx))
        for w in paredes:
            if rect.colliderect(w):
                if dx > 0:
                    rect.right = w.left
                elif dx < 0:
                    rect.left = w.right
        rect.y += int(round(dy))
        for w in paredes:
            if rect.colliderect(w):
                if dy > 0:
                    rect.bottom = w.top
                elif dy < 0:
                    rect.top = w.bottom
        rect.clamp_ip(pantalla.get_rect())

    def dibujar_fondo_y_obs():
        base_color = weather_system.get_base_color()
        pantalla.fill(base_color)

        for r in obstaculos:
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
        recs = datos.cargar_records(RECORDS_FILE)
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
        linea_clima = f"Clima: {CLIMAS_ES.get(weather_system.clima_actual, weather_system.clima_actual)} ({weather_system.intensidad_actual:.2f})"
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

        if reputacion >= 90:
            pantalla.blit(font.render("Pago: +5% (Excelencia)", True, (255, 220, 120)), (320, 8))
    
    
    pedido_actual = nuevo_pedido()
    
    
    clock = pygame.time.Clock()
    corriendo = True
    
    while corriendo:
        
        if energia == 0 and estado == GAME:
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

        #Actualizar clima
        weather_system.actualizar(ahora)

        #Estado del juego
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
                            data = datos.cargar_partida(SAVE_FILE)
                            if data:
                                
                                j = data.get("jugador")
                                if j:
                                    jugador_rect.topleft = (int(j.get("x", 728)), int(j.get("y", 836)))
                                
                                p = data.get("pedido")
                                if p:
                                    try:
                                        pedido_actual = {
                                            "pickup": pygame.Rect(*p["pickup"]),
                                            "dropoff": pygame.Rect(*p["dropoff"]),
                                            "payout": p["payout"],
                                            "peso": p["peso"],
                                            "deadline": p["deadline"],
                                            "created_at": p.get("created_at", ahora),
                                            "duration": p.get("duration", 60000)
                                        }
                                    except:
                                        pedido_actual = nuevo_pedido()
                                
                                tiene_paquete = data.get("tiene_paquete", False)
                                entregas = int(data.get("entregas", 0))
                                energia = int(data.get("energia", 100))
                                dinero_ganado = int(data.get("dinero", 0))
                                reputacion = int(data.get("reputacion", 70))
                                msg = data.get("msg", msg)
                                racha_sin_penalizacion = int(data.get("racha_sin_penalizacion", 0))
                                
                                menu_msg = "Partida cargada"
                                estado = GAME
                            else:
                                menu_msg = "No hay partida guardada"
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

        #Dibujar records
        if estado == RECORDS:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    corriendo = False
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    estado = MENU
            
            dibujar_records()
            pygame.display.flip()
            continue

        # Calcular velocidad
        peso_total = pedido_actual["peso"] if (pedido_actual and tiene_paquete) else 0
        VEL = calcular_velocidad(peso_total, reputacion, energia, weather_system.get_weather_multiplier())

        # Energia
        moving = (jugador_x_cambio_positivo != 0.0 or jugador_x_cambio_negativo != 0.0 or
                  jugador_y_cambio_positivo != 0.0 or jugador_y_cambio_negativo != 0.0)
        
        if ahora - ultimo_tick_energia >= 1000:
            if moving:
                costo = weather_system.get_energy_cost()
                if tiene_paquete and pedido_actual:
                    costo += pedido_actual["peso"] // 5
                energia = max(0, energia - int(round(costo)))
            ultimo_tick_energia = ahora

        # Manejo de eventos
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                datos.registrar_record(entregas, dinero_ganado, RECORDS_FILE)
                corriendo = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    datos.registrar_record(entregas, dinero_ganado, RECORDS_FILE)
                    estado = MENU
                    menu_msg = "Sesión guardada en records"
                elif evento.key == pygame.K_g:  #Guardar partida 
                    snapshot = {
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
                        },
                        "tiene_paquete": tiene_paquete,
                        "entregas": entregas,
                        "energia": energia,
                        "dinero": dinero_ganado,
                        "reputacion": reputacion,
                        "msg": msg,
                        "racha_sin_penalizacion": racha_sin_penalizacion,
                        "primera_tardanza_fecha": primera_tardanza_fecha.isoformat() if primera_tardanza_fecha else None
                    }
                    ok, m = datos.guardar_partida(snapshot, SAVE_FILE)
                    msg = m
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    jugador_y_cambio_positivo = 0.1
                elif evento.key in (pygame.K_UP, pygame.K_w):
                    jugador_y_cambio_negativo = -0.1
                elif evento.key in (pygame.K_LEFT, pygame.K_a):
                    jugador_x_cambio_negativo = -0.1
                elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                    jugador_x_cambio_positivo = 0.1
                elif evento.key == pygame.K_q:  #Aceptar pedido
                    if pedido_actual and jugador_rect.colliderect(pedido_actual["pickup"]) and not tiene_paquete:
                        tiene_paquete = True
                        msg = f"Pedido aceptado ({pedido_actual['peso']}kg)"
                elif evento.key == pygame.K_r:  #Rechazar pedido 
                    if pedido_actual and jugador_rect.colliderect(pedido_actual["pickup"]) and not tiene_paquete:
                        pedido_actual = nuevo_pedido()
                        msg = "Pedido rechazado"
                    elif tiene_paquete and pedido_actual:
                        # Cancelar pedido en curso
                        (reputacion, cambio, game_over, 
                         racha_sin_penalizacion, 
                         primera_tardanza_fecha) = actualizar_reputacion(
                            'cancelado', reputacion, racha_sin_penalizacion, primera_tardanza_fecha
                        )
                        tiene_paquete = False
                        pedido_actual = nuevo_pedido()
                        msg = f"Pedido cancelado. Reputación {reputacion} ({cambio})"
                        if game_over:
                            msg = "¡Has perdido! Tu reputación llegó a menos de 20."
                            datos.registrar_record(entregas, dinero_ganado, RECORDS_FILE)
                            pygame.display.flip()
                            pygame.time.wait(2000)
                            estado = MENU
                elif evento.key == pygame.K_e:  #Entregar pedido
                    if tiene_paquete and pedido_actual and jugador_rect.colliderect(pedido_actual["dropoff"]):
                        
                        now = pygame.time.get_ticks()
                        duration = pedido_actual.get("duration", 
                            max(60000, pedido_actual["deadline"] - pedido_actual.get("created_at", now)))
                        tiempo_restante = pedido_actual["deadline"] - now

                        if tiempo_restante >= 0:
                            if tiempo_restante >= 0.2 * duration:
                                evento_str = 'temprano'
                                msg = "Entrega temprana"
                            else:
                                evento_str = 'a_tiempo'
                                msg = "Entrega a tiempo"
                        else:
                            retraso_seg = (now - pedido_actual["deadline"]) / 1000.0
                            evento_str = 'tarde'
                            msg = f"Entrega tardía ({int(retraso_seg)}s)"

                        # Actualizar reputación
                        (reputacion, cambio, game_over, 
                         racha_sin_penalizacion, 
                         primera_tardanza_fecha) = actualizar_reputacion(
                            evento_str, reputacion, racha_sin_penalizacion, primera_tardanza_fecha,
                            retraso_seg if evento_str == 'tarde' else 0
                        )

                        # Actualizar dinero y estado
                        dinero_ganado += calcular_pago(pedido_actual.get("payout", 0), reputacion)
                        entregas += 1
                        tiene_paquete = False
                        pedido_actual = nuevo_pedido()

                        if game_over:
                            msg = "¡Has perdido! Tu reputación llegó a menos de 20."
                            datos.registrar_record(entregas, dinero_ganado, RECORDS_FILE)
                            pygame.display.flip()
                            pygame.time.wait(2000)
                            estado = MENU

            elif evento.type == pygame.KEYUP:
                if evento.key in (pygame.K_DOWN, pygame.K_s):
                    jugador_y_cambio_positivo = 0.0
                elif evento.key in (pygame.K_UP, pygame.K_w):
                    jugador_y_cambio_negativo = 0.0
                elif evento.key in (pygame.K_LEFT, pygame.K_a):
                    jugador_x_cambio_negativo = 0.0
                elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                    jugador_x_cambio_positivo = 0.0

        # Calcular movimiento
        vx_raw = jugador_x_cambio_positivo + jugador_x_cambio_negativo
        vy_raw = jugador_y_cambio_positivo + jugador_y_cambio_negativo
        dx, dy = calcular_movimiento(vx_raw, vy_raw, VEL, dt)
        mover_con_colision(jugador_rect, dx, dy, obstaculos)

        # Verificar expiración del pedido
        if pedido_actual and tiene_paquete and ahora > pedido_actual["deadline"]:
            
            (reputacion, cambio, game_over, 
             racha_sin_penalizacion, 
             primera_tardanza_fecha) = actualizar_reputacion(
                'perdido', reputacion, racha_sin_penalizacion, primera_tardanza_fecha
            )
            
            if game_over:
                msg = "¡Has perdido! Tu reputación llegó a menos de 20."
                datos.registrar_record(entregas, dinero_ganado, RECORDS_FILE)
                pygame.display.flip()
                pygame.time.wait(2000)
                estado = MENU
            else:
                msg = "El paquete expiró"
            
            tiene_paquete = False
            pedido_actual = nuevo_pedido()

        # Dibujar todo
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
    sys.exit()

if __name__ == "__main__":
    main()