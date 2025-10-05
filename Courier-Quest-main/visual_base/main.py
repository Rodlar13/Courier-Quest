import pygame
import sys
import math
from configurar import *
import datos
from reputacion import *
from clima import *
from base import *
from graficos import *

def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Courier Quest")
    
    # Fuentes
    font = pygame.font.SysFont(None, 22)
    font_big = pygame.font.SysFont(None, 44)
    
    # Cargar imágenes
    icono = cargar_imagen_robusta("mensajero.png", TAM_ICONO, exit_on_fail=False)
    pygame.display.set_icon(icono)
    img_jugador = cargar_imagen_robusta("mensajero.png", TAM_JUGADOR)
    img_cliente = cargar_imagen_robusta("audiencia.png", TAM_CLIENTE)
    
    # Estado del juego (multi-order version)
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
    
    # Sistema de pedidos múltiples
    ofertas = []
    activos = []
    llevando_id = None
    ultimo_tick_energia = pygame.time.get_ticks()
    msg = "Bienvenido a Courier Quest - TAB para abrir panel de pedidos"
    
    # Guardado automático
    ultimo_guardado_auto = pygame.time.get_ticks()
    intervalo_guardado_auto = 30000  # 30 segundos
    
    # Mensaje temporal para guardado automático
    msg_temporal = None
    tiempo_msg_temporal = 0
    duracion_msg_temporal = 2000  # 2 segundos
    
    # Panel de pedidos
    panel_abierto = False
    panel_tab = 0  # 0=Ofertas, 1=Activos
    panel_idx = 0
    
    # Spawn de ofertas
    ultimo_spawn = pygame.time.get_ticks()
    
    # Estados
    estado = MENU
    menu_idx = 0
    menu_msg = ""
    
    # Sistema de clima
    weather_system = WeatherSystem()
    
    # Cargar datos desde API
    datos.cargarDatosAPI()

    def reset_partida():
        nonlocal jugador_rect, energia, dinero_ganado, reputacion, msg
        nonlocal racha_sin_penalizacion, primera_tardanza_fecha, entregas
        nonlocal ofertas, activos, llevando_id, ultimo_spawn, ultimo_guardado_auto
        nonlocal msg_temporal, tiempo_msg_temporal, weather_system
        
        jugador_rect = pygame.Rect(728, 836, 48, 48)  # Crear nuevo rect
        energia = 100
        dinero_ganado = 0
        reputacion = 70
        msg = "TAB para abrir panel de pedidos"
        racha_sin_penalizacion = 0
        primera_tardanza_fecha = None
        entregas = 0
        ofertas = [nuevo_pedido(jugador_rect, img_cliente, OBSTACULOS, pantalla) for _ in range(3)]
        activos = []
        llevando_id = None
        ultimo_spawn = pygame.time.get_ticks()
        ultimo_guardado_auto = pygame.time.get_ticks()
        msg_temporal = None
    
    # Reiniciar sistema de clima
    weather_system = WeatherSystem()

    def fin_derrota():
        nonlocal estado, msg
        msg = "¡Has perdido! Tu reputación llegó a menos de 20."
        datos.registrar_record(entregas, dinero_ganado, reputacion, RECORDS_FILE)
        pygame.display.flip()
        pygame.time.wait(2000)
        estado = MENU

    def actualizar_clima():
        """Actualiza el sistema de clima"""
        ahora = pygame.time.get_ticks()
        if weather_system.transicion:
            dur = weather_system.transicion_duracion if weather_system.transicion_duracion > 0 else 1
            t = (ahora - weather_system.transicion_inicio) / dur
            if t >= 1.0:
                weather_system.clima_actual = weather_system.clima_objetivo
                weather_system.intensidad_actual = weather_system.intensidad_objetivo
                weather_system.transicion = False
                weather_system.ultimo_cambio_clima = ahora
                weather_system.duracion_actual = random.uniform(45000, 60000)
            else:
                weather_system.intensidad_actual = (1 - t) * weather_system.intensidad_inicio + t * weather_system.intensidad_objetivo
            return
        
        if ahora - weather_system.ultimo_cambio_clima > weather_system.duracion_actual:
            siguiente = weather_system.elegir_siguiente_clima(weather_system.clima_actual)
            weather_system.iniciar_transicion(siguiente, ahora)

    clock = pygame.time.Clock()
    corriendo = True
    
    while corriendo:
        if energia == 0 and estado == GAME:
            msg = "Sin energía. Cargando..."
            dibujar_fondo_y_obs(pantalla, weather_system.clima_actual)
            
            # Dibujar pedidos activos
            for p in activos:
                col = color_for_order(p['id'])
                pygame.draw.rect(pantalla, col, p["pickup"], 2)
                pygame.draw.rect(pantalla, col, p["dropoff"], 2)
                if llevando_id == p['id']:
                    draw_dropoff_icon(pantalla, p["dropoff"], col)
                else:
                    draw_pickup_icon(pantalla, p["pickup"], col)
            
            pantalla.blit(img_jugador, jugador_rect.topleft)
            dibujar_hud(pantalla, font, entregas, dinero_ganado, reputacion, 
                       weather_system.clima_actual, weather_system.intensidad_actual, 
                       msg, energia)
            
            # Dibujar mensaje temporal si existe
            if msg_temporal:
                msg_surf = font.render(msg_temporal, True, (120, 255, 120))
                pantalla.blit(msg_surf, (ANCHO - msg_surf.get_width() - 20, ALTO - 40))
            
            if panel_abierto:
                dibujar_panel(pantalla, font, font_big, panel_tab, panel_idx, ofertas, activos)
            pygame.display.flip()
            pygame.time.wait(60000)
            energia = 70
            msg = "Energía recargada a 70. Continúa jugando."
            ultimo_tick_energia = pygame.time.get_ticks()
            continue

        dt = clock.tick(FPS) / 1000.0
        ahora = pygame.time.get_ticks()

        # Estado del juego
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
                            loaded_data = datos.cargar_partida(SAVE_FILE)
                            if loaded_data:
                                jugador_rect = loaded_data['jugador_rect']
                                activos = loaded_data['activos']
                                ofertas = loaded_data['ofertas']
                                llevando_id = loaded_data['llevando_id']
                                entregas = loaded_data['entregas']
                                energia = loaded_data['energia']
                                dinero_ganado = loaded_data['dinero_ganado']
                                reputacion = loaded_data['reputacion']
                                msg = loaded_data['msg']
                                racha_sin_penalizacion = loaded_data['racha_sin_penalizacion']
                                primera_tardanza_fecha = loaded_data['primera_tardanza_fecha']
                                weather_system = WeatherSystem()
                                menu_msg = "Partida cargada"
                                estado = GAME
                            else:
                                menu_msg = "No hay partida guardada o error al cargar"
                        elif seleccion == "Records":
                            estado = RECORDS
                        elif seleccion == "Salir":
                            corriendo = False
            
            dibujar_menu(pantalla, opciones, menu_idx, font, font_big)
            if menu_msg:
                info = font.render(menu_msg, True, (255, 220, 120))
                pantalla.blit(info, (ANCHO // 2 - info.get_width() // 2, 280 + len(opciones) * 44 + 20))
            pygame.display.flip()
            continue

        # Dibujar records
        if estado == RECORDS:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    corriendo = False
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    estado = MENU
            
            dibujar_records(pantalla, font, font_big, RECORDS_FILE)
            pygame.display.flip()
            continue

        # ===== GAME LOGIC =====
        
        # Guardado automático cada 30 segundos
        if estado == GAME and ahora - ultimo_guardado_auto > intervalo_guardado_auto:
            snapshot = datos.snapshot_partida(
                jugador_rect, activos, ofertas, llevando_id, entregas, energia,
                dinero_ganado, reputacion, msg, racha_sin_penalizacion, primera_tardanza_fecha
            )
            ok, m = datos.guardar_partida(snapshot, SAVE_FILE)
            if ok:
                msg_temporal = "✓ Partida guardada automáticamente"
                tiempo_msg_temporal = ahora
                ultimo_guardado_auto = ahora
            else:
                msg_temporal = f"✗ Error: {m}"
                tiempo_msg_temporal = ahora
        
        # Manejar mensaje temporal (guardado automático)
        if msg_temporal and ahora - tiempo_msg_temporal > duracion_msg_temporal:
            msg_temporal = None
        
        # Actualizar sistemas
        actualizar_clima()
        ultimo_spawn = intentar_spawn_oferta(ofertas, ultimo_spawn, OFERTAS_MAX, SPAWN_CADA_MS, 
                                           jugador_rect, img_cliente, OBSTACULOS, pantalla)

        # Energía
        if ahora - ultimo_tick_energia >= 1000:
            moving = (jugador_x_cambio_positivo or jugador_x_cambio_negativo or 
                     jugador_y_cambio_positivo or jugador_y_cambio_negativo)
            if moving:
                costo = weather_system.get_energy_cost()
                if llevando_id is not None:
                    p = next((x for x in activos if x["id"] == llevando_id), None)
                    if p:
                        costo += p["peso"] // 5
                energia = max(0, energia - int(round(costo)))
            ultimo_tick_energia = ahora

        # Manejo de eventos
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                datos.registrar_record(entregas, dinero_ganado, reputacion, RECORDS_FILE)
                corriendo = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    datos.registrar_record(entregas, dinero_ganado, reputacion, RECORDS_FILE)
                    estado = MENU
                elif evento.key == pygame.K_g:  # Guardar partida manual
                    snapshot = datos.snapshot_partida(
                        jugador_rect, activos, ofertas, llevando_id, entregas, energia,
                        dinero_ganado, reputacion, msg, racha_sin_penalizacion, primera_tardanza_fecha
                    )
                    ok, m = datos.guardar_partida(snapshot, SAVE_FILE)
                    if ok:
                        msg_temporal = "✓ Partida guardada manualmente"
                    else:
                        msg_temporal = f"✗ Error: {m}"
                    tiempo_msg_temporal = ahora
                    # Reiniciar contador de guardado automático
                    ultimo_guardado_auto = ahora
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    jugador_y_cambio_positivo = 0.1
                elif evento.key in (pygame.K_UP, pygame.K_w):
                    jugador_y_cambio_negativo = -0.1
                elif evento.key in (pygame.K_LEFT, pygame.K_a):
                    jugador_x_cambio_negativo = -0.1
                elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                    jugador_x_cambio_positivo = 0.1
                elif evento.key == pygame.K_TAB:
                    panel_abierto = not panel_abierto
                    panel_idx = 0
                elif panel_abierto and evento.key in (pygame.K_LEFT,):
                    panel_tab = (panel_tab - 1) % 2
                    panel_idx = 0
                elif panel_abierto and evento.key in (pygame.K_RIGHT,):
                    panel_tab = (panel_tab + 1) % 2
                    panel_idx = 0
                elif panel_abierto and evento.key in (pygame.K_UP,):
                    lista = ofertas if panel_tab == 0 else activos
                    if lista:
                        panel_idx = (panel_idx - 1) % len(lista)
                elif panel_abierto and evento.key in (pygame.K_DOWN,):
                    lista = ofertas if panel_tab == 0 else activos
                    if lista:
                        panel_idx = (panel_idx + 1) % len(lista)
                elif panel_abierto and evento.key == pygame.K_RETURN:
                    if panel_tab == 0:
                        p, new_msg = aceptar_oferta_seleccionada(panel_tab, panel_idx, ofertas, activos)
                        if p:
                            msg = new_msg
                    else:
                        p, new_llevando_id, new_msg, new_reputacion, game_over, new_racha, new_fecha = cancelar_activo_seleccionado(
                            panel_tab, panel_idx, activos, llevando_id, reputacion, racha_sin_penalizacion, primera_tardanza_fecha
                        )
                        if p:
                            llevando_id = new_llevando_id
                            msg = new_msg
                            reputacion = new_reputacion
                            racha_sin_penalizacion = new_racha
                            primera_tardanza_fecha = new_fecha
                            if game_over:
                                fin_derrota()
                elif panel_abierto and evento.key == pygame.K_r:
                    if panel_tab == 0:
                        p, new_msg = rechazar_oferta_seleccionada(panel_tab, panel_idx, ofertas)
                        if p:
                            msg = new_msg
                elif evento.key == pygame.K_q:  # Recoger paquete
                    if llevando_id is None:
                        for p in activos:
                            if jugador_rect.colliderect(p["pickup"]):
                                llevando_id = p["id"]
                                msg = f"Recogido #{p['id']} ({p['peso']}kg)"
                                break
                elif evento.key == pygame.K_e:  # Entregar paquete
                    if llevando_id is not None:
                        p = next((x for x in activos if x["id"] == llevando_id), None)
                        if p and jugador_rect.colliderect(p["dropoff"]):
                            now = pygame.time.get_ticks()
                            duration = p.get("duration", max(60000, p["deadline"] - p.get("created_at", now)))
                            tiempo_restante = p["deadline"] - now

                            if tiempo_restante >= 0:
                                if tiempo_restante >= 0.2 * duration:
                                    evento_str = 'temprano'
                                    msg = "Entrega temprana"
                                else:
                                    evento_str = 'a_tiempo'
                                    msg = "Entrega a tiempo"
                            else:
                                retraso_seg = (now - p["deadline"]) / 1000.0
                                evento_str = 'tarde'
                                msg = f"Entrega tardía ({int(retraso_seg)}s)"

                            # Actualizar reputación
                            reputacion, cambio, game_over, racha_sin_penalizacion, primera_tardanza_fecha = actualizar_reputacion(
                                evento_str, reputacion, racha_sin_penalizacion, primera_tardanza_fecha,
                                retraso_seg if evento_str == 'tarde' else 0
                            )

                            # Actualizar dinero y estado
                            dinero_ganado += calcular_pago(p.get("payout", 0), reputacion)
                            activos = [x for x in activos if x["id"] != llevando_id]
                            entregas += 1
                            llevando_id = None

                            if game_over:
                                fin_derrota()

            elif evento.type == pygame.KEYUP:
                if evento.key in (pygame.K_DOWN, pygame.K_s):
                    jugador_y_cambio_positivo = 0.0
                elif evento.key in (pygame.K_UP, pygame.K_w):
                    jugador_y_cambio_negativo = 0.0
                elif evento.key in (pygame.K_LEFT, pygame.K_a):
                    jugador_x_cambio_negativo = 0.0
                elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                    jugador_x_cambio_positivo = 0.0

        # Calcular velocidad
        peso_total = 0
        if llevando_id is not None:
            p = next((x for x in activos if x["id"] == llevando_id), None)
            if p:
                peso_total = p["peso"]
        
        VEL = calcular_velocidad(peso_total, reputacion, energia, weather_system.get_weather_multiplier())

        # Movimiento
        vx_raw = jugador_x_cambio_positivo + jugador_x_cambio_negativo
        vy_raw = jugador_y_cambio_positivo + jugador_y_cambio_negativo
        dx = dy = 0.0
        if vx_raw != 0.0 or vy_raw != 0.0:
            l = math.hypot(vx_raw, vy_raw)
            if l != 0:
                ux, uy = vx_raw / l, vy_raw / l
                dx, dy = ux * VEL * dt, uy * VEL * dt
        mover_con_colision(jugador_rect, dx, dy, OBSTACULOS, pantalla)

        # Verificar expiraciones
        ahora_ms = pygame.time.get_ticks()
        expirados = [p for p in activos if ahora_ms > p["deadline"]]
        for p in expirados:
            reputacion, cambio, game_over, racha_sin_penalizacion, primera_tardanza_fecha = actualizar_reputacion(
                'perdido', reputacion, racha_sin_penalizacion, primera_tardanza_fecha
            )
            if llevando_id == p["id"]:
                llevando_id = None
            activos = [x for x in activos if x["id"] != p["id"]]
            msg = f"Pedido #{p['id']} expiró ({cambio})"
            if game_over:
                fin_derrota()
                break

        # ===== DIBUJADO =====
        dibujar_fondo_y_obs(pantalla, weather_system.clima_actual)
        
        # Dibujar pedidos activos
        for p in activos:
            col = color_for_order(p['id'])
            pygame.draw.rect(pantalla, col, p["pickup"], 3)
            pygame.draw.rect(pantalla, col, p["dropoff"], 3)
            if llevando_id == p['id']:
                draw_dropoff_icon(pantalla, p["dropoff"], col)
            else:
                draw_pickup_icon(pantalla, p["pickup"], col)
        
        pantalla.blit(img_jugador, jugador_rect.topleft)
        dibujar_hud(pantalla, font, entregas, dinero_ganado, reputacion, 
                   weather_system.clima_actual, weather_system.intensidad_actual, 
                   msg, energia)
        
        # Dibujar mensaje temporal de guardado (si existe)
        if msg_temporal:
            msg_surf = font.render(msg_temporal, True, (120, 255, 120))
            pantalla.blit(msg_surf, (ANCHO - msg_surf.get_width() - 20, ALTO - 40))
        
        if panel_abierto:
            dibujar_panel(pantalla, font, font_big, panel_tab, panel_idx, ofertas, activos)
        
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()