import pygame
import sys
import math
from configurar import *
import datos
from reputacion import *
from clima import *
from base import *
from grafo import *
from graficos import *
from IAdificil import *
from IAMedio import *

def seleccionar_dificultad_menu(pantalla, font, font_big):
    """Menú para seleccionar dificultad del juego"""
    opciones = ["Fácil", "Medio", "Difícil"]
    seleccionado = 0
    corriendo = True
    
    while corriendo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_UP, pygame.K_w):
                    seleccionado = (seleccionado - 1) % len(opciones)
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    seleccionado = (seleccionado + 1) % len(opciones)
                elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return opciones[seleccionado]
                elif evento.key == pygame.K_ESCAPE:
                    return None
        
        # Dibujar menú de dificultad
        pantalla.fill((20, 24, 28))
        
        # Título
        titulo = font_big.render("Seleccionar Dificultad", True, (255, 255, 255))
        pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 140))
        
        # Descripciones de dificultad
        descripciones = {
            "Fácil": "IA toma decisiones aleatorias",
            "Medio": "IA busca rutas óptima con Búsqueda Greedy", 
            "Difícil": "IA busca rutas óptimas con Dijkstra"
        }
        
        # Dibujar opciones
        y0 = 280
        for i, opcion in enumerate(opciones):
            color = (255, 255, 0) if i == seleccionado else (220, 220, 220)
            texto = font.render(opcion, True, color)
            pantalla.blit(texto, (ANCHO // 2 - texto.get_width() // 2, y0 + i * 60))
            
            # Dibujar descripción
            desc = font.render(descripciones[opcion], True, (180, 180, 180))
            pantalla.blit(desc, (ANCHO // 2 - desc.get_width() // 2, y0 + i * 60 + 30))
        
        # Instrucciones
        instrucciones = font.render("Usa ↑/↓ para navegar, ENTER para seleccionar, ESC para volver", 
                                  True, (150, 150, 150))
        pantalla.blit(instrucciones, (ANCHO // 2 - instrucciones.get_width() // 2, ALTO - 60))
        
        pygame.display.flip()
    
    return None

def dibujar_hud_completo(pantalla, font, entregas, dinero_ganado, reputacion, clima_actual, intensidad_actual, 
                        msg, energia, dificultad_actual=None,
                        cpu_entregas=0, cpu_dinero=0, cpu_reputacion=0, cpu_energia=0, cpu_ia=None):
    y = 8
    linea_clima = f"Clima: {CLIMAS_ES.get(clima_actual, clima_actual)} ({intensidad_actual:.2f})"
    
    # Información del jugador humano
    lineas = (
        "Mover: WASD | TAB panel | ← / → pestaña | ↑ / ↓ selección | ENTER aceptar/cancelar | R rechazar",
        "Q recoger (en pickup) | E entregar (en dropoff) | ESC menú",
        f"Entregas: {entregas}",
        f"Dinero ganado: {dinero_ganado} $",
        f"Reputación: {reputacion}",
        linea_clima,
        msg,
    )
    
    for linea in lineas:
        pantalla.blit(font.render(linea, True, (255, 255, 255)), (10, y))
        y += 26


    # Barra de energía jugador
    pantalla.blit(font.render("Energía:", True, (255, 255, 255)), (10, y))
    dibujar_barra(pantalla, 100, y, energia, 100, 200, 18)

    if reputacion >= 90:
        pantalla.blit(font.render("Pago: +5% (Excelencia)", True, (255, 220, 120)), (320, 8))
    

    # Mostrar solo la IA correspondiente a la dificultad seleccionada
    x_texto = ANCHO - 350  
    x_barra = ANCHO - 200
    y_ia = 8
    espacio = 20

    if dificultad_actual == 'Fácil' and (cpu_entregas > 0 or cpu_dinero > 0):
        pantalla.blit(font.render(f"Dinero: ${cpu_dinero}", True, (100, 255, 100)), (x_texto, y_ia))
        y_ia += espacio
        pantalla.blit(font.render(f"Entregas: {cpu_entregas}", True, (100, 255, 100)), (x_texto, y_ia))
        y_ia += espacio
        pantalla.blit(font.render("Energía IA Fácil:", True, (100, 255, 100)), (x_texto, y_ia))
        dibujar_barra(pantalla, x_barra, y_ia, cpu_energia, 100, 120, 10)

    elif dificultad_actual == 'Medio' and cpu_ia:
        pantalla.blit(font.render(f"Dinero: ${cpu_ia.dinero_ganado}", True, (255, 100, 100)), (x_texto, y_ia))
        y_ia += espacio
        pantalla.blit(font.render(f"Entregas: {cpu_ia.entregas}", True, (255, 100, 100)), (x_texto, y_ia))
        y_ia += espacio
        pantalla.blit(font.render("Energía IA Medio:", True, (255, 100, 100)), (x_texto, y_ia))
        dibujar_barra(pantalla, x_barra, y_ia, cpu_ia.energia, 100, 120, 10)

    elif dificultad_actual == 'Difícil' and cpu_ia:
        pantalla.blit(font.render(f"Dinero: ${cpu_ia.dinero_ganado}", True, (255, 100, 100)), (x_texto, y_ia))
        y_ia += espacio
        pantalla.blit(font.render(f"Entregas: {cpu_ia.entregas}", True, (255, 100, 100)), (x_texto, y_ia))
        y_ia += espacio
        pantalla.blit(font.render("Energía IA Difícil:", True, (255, 100, 100)), (x_texto, y_ia))
        dibujar_barra(pantalla, x_barra, y_ia, cpu_ia.energia, 100, 120, 10)

def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Courier Quest")
    
    # Variables para el sistema de dificultad
    dificultad_actual = None
    cpu_ia = None  # Para IA
    mapa_ciudad = MapaJuego() # Cargar mapa de la ciudad

    # fuentes
    font = pygame.font.SysFont(None, 22)
    font_big = pygame.font.SysFont(None, 44)

    # imágenes
    icono = cargar_imagen_robusta("mensajero.png", TAM_ICONO, exit_on_fail=False)
    pygame.display.set_icon(icono)
    img_jugador = cargar_imagen_robusta("mensajero.png", TAM_JUGADOR)

    # Sprite para la IA
    try:
        img_cpu = cargar_imagen_robusta("mensajero-IA.png", TAM_JUGADOR)
    except:
        #usar mensajero normal pero tintado de azul
        img_cpu = cargar_imagen_robusta("mensajero.png", TAM_JUGADOR)
        # Crear copia y tintar
        img_cpu_copy = img_cpu.copy()
        # Aplicar tintado azul
        color_filter = pygame.Surface(TAM_JUGADOR, pygame.SRCALPHA)
        color_filter.fill((100, 100, 255, 100))  # Azul semitransparente
        img_cpu_copy.blit(color_filter, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        img_cpu = img_cpu_copy

    img_cliente = cargar_imagen_robusta("audiencia.png", TAM_CLIENTE)


    # estado
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

    # --- Estado para jugador CPU (IA, dificultad fácil) ---
    cpu_rect = None  # se inicializa en reset_cpu_state
    cpu_entregas = 0
    cpu_dinero = 0
    cpu_reputacion = 70
    cpu_energia = 100
    cpu_llevando_id = None
    cpu_frames_sin_mover = 0  # contador de frames seguidos sin mover la CPU
    cpu_activos = []
    cpu_vx = 0.0
    cpu_vy = 0.0
    cpu_ultimo_cambio_dir = 0
    cpu_ultimo_tick_energia = pygame.time.get_ticks()
    cpu_ultimo_intento_pedido = 0

    # pedidos
    ofertas = []
    activos = []
    llevando_id = None
    ultimo_tick_energia = pygame.time.get_ticks()
    msg = "Bienvenido a Courier Quest - TAB para abrir panel de pedidos"

    # autosave
    ultimo_guardado_auto = pygame.time.get_ticks()
    intervalo_guardado_auto = 30000
    msg_temporal = None
    tiempo_msg_temporal = 0
    duracion_msg_temporal = 2000

    # panel
    panel_abierto = False
    panel_tab = 0  # 0=Ofertas, 1=Activos
    panel_idx = 0

    # spawn ofertas
    ultimo_spawn = pygame.time.get_ticks()

    # estados
    estado = MENU
    menu_idx = 0
    menu_msg = ""

    # clima
    weather_system = WeatherSystem()

    # api (opcional)
    datos.cargarDatosAPI()

    # --- Helpers para IA CPU (dificultad fácil) ---
    def reset_cpu_state():
        nonlocal cpu_rect, cpu_entregas, cpu_dinero, cpu_reputacion, cpu_energia
        nonlocal cpu_llevando_id, cpu_activos, cpu_vx, cpu_vy
        nonlocal cpu_ultimo_cambio_dir, cpu_ultimo_tick_energia
        nonlocal jugador_rect

        # Spawnear CPU en una calle válida cercana al jugador
        spawn = spawnear_cliente(jugador_rect.center, img_cliente, OBSTACULOS, pantalla)
        cpu_rect = img_cpu.get_rect(center=spawn.center)
        cpu_entregas = 0
        cpu_dinero = 0
        cpu_reputacion = 70
        cpu_energia = 100
        cpu_llevando_id = None
        cpu_activos = []
        cpu_vx = 0.0
        cpu_vy = 0.0
        now_cpu = pygame.time.get_ticks()
        cpu_ultimo_cambio_dir = now_cpu
        cpu_ultimo_tick_energia = now_cpu
        cpu_ultimo_intento_pedido = now_cpu

    # reset
    def reset_partida():
        nonlocal jugador_rect, energia, dinero_ganado, reputacion, msg
        nonlocal racha_sin_penalizacion, primera_tardanza_fecha, entregas
        nonlocal ofertas, activos, llevando_id, ultimo_spawn, ultimo_guardado_auto
        nonlocal msg_temporal, tiempo_msg_temporal, weather_system
        nonlocal cpu_rect, cpu_entregas, cpu_dinero, cpu_reputacion, cpu_energia
        nonlocal cpu_llevando_id, cpu_activos, cpu_vx, cpu_vy
        nonlocal cpu_ultimo_cambio_dir, cpu_ultimo_tick_energia, cpu_ultimo_intento_pedido
        nonlocal cpu_ia, dificultad_actual, mapa_ciudad

        jugador_rect = pygame.Rect(728, 836, 48, 48)
        energia = 100
        dinero_ganado = 0
        reputacion = 70
        msg = "TAB para abrir panel de pedidos"
        racha_sin_penalizacion = 0

        # Reiniciar también el estado de la IA CPU fácil
        reset_cpu_state()
        
        # Reiniciar IA difícil si estaba activa
        if cpu_ia:
            cpu_ia = None
        dificultad_actual = None
        mapa_ciudad = None
        
        primera_tardanza_fecha = None
        entregas = 0
        ofertas = [nuevo_pedido(jugador_rect, img_cliente, OBSTACULOS, pantalla) for _ in range(3)]
        activos = []
        llevando_id = None
        ultimo_spawn = pygame.time.get_ticks()
        ultimo_guardado_auto = pygame.time.get_ticks()
        msg_temporal = None

    # reiniciar clima
    weather_system = WeatherSystem()

    # derrota
    def fin_derrota():
        nonlocal estado, msg
        msg = "¡Has perdido! Tu reputación llegó a menos de 20."
        datos.registrar_record(entregas, dinero_ganado, reputacion, RECORDS_FILE)
        pygame.display.flip()
        pygame.time.wait(2000)
        estado = MENU

    # actualizar clima
    def actualizar_clima():
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


    def update_cpu_facil(dt):
        """IA de dificultad fácil para el jugador CPU.

        - Acepta pedidos automáticamente cuando hay ofertas disponibles.
        - Se mueve de forma dirigida hacia el pickup / dropoff de su pedido actual.
        - Usa la energía igual que el jugador: se gasta al moverse y se regenera al descansar.
        """
        nonlocal cpu_rect, cpu_vx, cpu_vy, cpu_llevando_id, cpu_activos
        nonlocal cpu_entregas, cpu_dinero, cpu_reputacion, cpu_energia
        nonlocal cpu_ultimo_cambio_dir, cpu_ultimo_tick_energia, cpu_ultimo_intento_pedido
        nonlocal ofertas, msg_temporal, weather_system

        if cpu_rect is None:
            return

        now = pygame.time.get_ticks()

        # --- Energía de la CPU (similar al jugador) ---
        if now - cpu_ultimo_tick_energia >= 1000:
            moving_cpu = (cpu_vx != 0.0 or cpu_vy != 0.0)
            if moving_cpu:
                # En dificultad fácil, la CPU se cansa un poco más rápido que el jugador
                cpu_cost = weather_system.get_energy_cost() * 1.3
                if cpu_llevando_id is not None:
                    p_llev_cpu = next((x for x in cpu_activos if x["id"] == cpu_llevando_id), None)
                    if p_llev_cpu:
                        cpu_cost += p_llev_cpu["peso"] // 5
                cpu_energia = max(0, cpu_energia - int(round(cpu_cost)))
            else:
                # Si la CPU está quieta, también regenera energía
                cpu_energia = min(100, cpu_energia + 3)
            cpu_ultimo_tick_energia = now

        # --- Lógica de aceptación y objetivo de pedido ---
        # Si no tiene pedido activo, toma uno de las ofertas, pero con retraso y probabilidad < 100%
        if cpu_llevando_id is None and not cpu_activos and ofertas:
            # La CPU en fácil no reacciona de inmediato y a veces ignora pedidos
            if now - cpu_ultimo_intento_pedido >= 4000:
                cpu_ultimo_intento_pedido = now
                if random.random() < 0.6:  # solo 60% de las veces acepta
                    idx = random.randrange(len(ofertas))
                    p = ofertas.pop(idx)
                    p["aceptado"] = True
                    p["owner"] = "cpu"
                    cpu_activos.append(p)
                    msg_temporal = f"CPU (fácil) aceptó pedido #{p['id']}"

        # Asegurar que tenga un id de pedido actual si hay pedidos activos
        if cpu_llevando_id is None and cpu_activos:
            cpu_llevando_id = cpu_activos[0]["id"]

        objetivo = None
        pedido_actual = None
        if cpu_llevando_id is not None:
            pedido_actual = next((x for x in cpu_activos if x["id"] == cpu_llevando_id), None)
            if pedido_actual is not None:
                # Si aún no ha recogido, ir al pickup; si ya lo lleva, ir al dropoff
                if not pedido_actual.get("llevando_cpu", False):
                    objetivo = pedido_actual["pickup"].center
                else:
                    objetivo = pedido_actual["dropoff"].center

        # --- Dirección de movimiento ---
        if cpu_energia <= 0:
            # Sin energía: se queda quieto hasta recargar
            cpu_vx = 0.0
            cpu_vy = 0.0
        else:
            if objetivo is not None:
                # IA fácil: movimientos poco optimizados con algo de ruido aleatorio.
                # Intenta moverse vagamente hacia el objetivo, pero sin pathfinding sofisticado.
                tx, ty = objetivo
                cx, cy = cpu_rect.center
                dx = tx - cx
                dy = ty - cy

                if dx == 0 and dy == 0:
                    # Ya está encima del objetivo; la lógica de colisión se encarga del pickup/dropoff
                    cpu_vx = 0.0
                    cpu_vy = 0.0
                else:
                    # Construimos una lista de direcciones candidatas:
                    #  - Una dirección "lógica" hacia el objetivo
                    #  - El resto de direcciones cardinales para meter ruido
                    dirs_candidatas = []

                    if abs(dx) >= abs(dy):
                        # preferencia por moverse en x
                        step_x = 1 if dx > 0 else -1
                        dirs_candidatas.append((step_x, 0))
                    else:
                        # preferencia por moverse en y
                        step_y = 1 if dy > 0 else -1
                        dirs_candidatas.append((0, step_y))

                    # Añadir todas las direcciones cardinales, permitiendo que muchas veces
                    # se elija una dirección que NO es la óptima.
                    for extra in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        if extra not in dirs_candidatas:
                            dirs_candidatas.append(extra)

                    # De vez en cuando mantenemos la dirección actual para que no sea tan errático
                    # y solo cambiamos dirección cada cierto tiempo.
                    if now - cpu_ultimo_cambio_dir >= 700:
                        random.shuffle(dirs_candidatas)
                        elegido = (cpu_vx, cpu_vy)
                        for ddx, ddy in dirs_candidatas:
                            paso = 48
                            test = cpu_rect.copy()
                            test.x += ddx * paso
                            test.y += ddy * paso
                            if not dentro_pantalla(test, pantalla):
                                continue
                            choca = False
                            for w in OBSTACULOS:
                                if test.colliderect(w):
                                    choca = True
                                    break
                            if not choca:
                                elegido = (float(ddx), float(ddy))
                                break

                        cpu_vx, cpu_vy = elegido
                        cpu_ultimo_cambio_dir = now
            else:
                # Sin pedido: movimiento aleatorio suave por la ciudad
                if now - cpu_ultimo_cambio_dir >= 800:
                    posibles = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                    random.shuffle(posibles)
                    elegido = (0.0, 0.0)
                    for dx, dy in posibles:
                        paso = 48
                        test = cpu_rect.copy()
                        test.x += dx * paso
                        test.y += dy * paso
                        if not dentro_pantalla(test, pantalla):
                            continue
                        choca = False
                        for w in OBSTACULOS:
                            if test.colliderect(w):
                                choca = True
                                break
                        if not choca:
                            elegido = (float(dx), float(dy))
                            break
                    cpu_vx, cpu_vy = elegido
                    cpu_ultimo_cambio_dir = now

        # --- Interacción con pickup/dropoff de la CPU ---
        if pedido_actual is not None:
            # Recoger
            if not pedido_actual.get("llevando_cpu", False) and cpu_rect.colliderect(pedido_actual["pickup"]):
                pedido_actual["llevando_cpu"] = True
            # Entregar
            elif pedido_actual.get("llevando_cpu", False) and cpu_rect.colliderect(pedido_actual["dropoff"]):
                now_ms = pygame.time.get_ticks()
                duration = pedido_actual.get("duration", max(60000, pedido_actual["deadline"] - pedido_actual.get("created_at", now_ms)))
                tiempo_restante = pedido_actual["deadline"] - now_ms
                if tiempo_restante >= 0:
                    if tiempo_restante >= 0.2 * duration:
                        evento_str = 'temprano'
                    else:
                        evento_str = 'a_tiempo'
                else:
                    evento_str = 'tarde'

                cpu_reputacion, _, _, _, _ = actualizar_reputacion(
                    evento_str, cpu_reputacion, 0, None
                )
                cpu_dinero += calcular_pago(pedido_actual.get("payout", 0), cpu_reputacion)
                cpu_entregas += 1
                cpu_activos = [x for x in cpu_activos if x["id"] != cpu_llevando_id]
                cpu_llevando_id = None
                msg_temporal = f"CPU (fácil) entregó pedido #{pedido_actual['id']}"

    clock = pygame.time.Clock()
    corriendo = True

    while corriendo:
        dt = clock.tick(FPS) / 1000.0
        ahora = pygame.time.get_ticks()

        # menú
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
                            
                            # Mostrar menú de dificultad
                            dificultad_seleccionada = seleccionar_dificultad_menu(pantalla, font, font_big)
                            
                            if dificultad_seleccionada:
                                dificultad_actual = dificultad_seleccionada
                                mapa_ciudad = MapaJuego()   # Inicializar mapa
                                
                                if dificultad_seleccionada == 'Fácil':
                                    # Usar la IA fácil existente
                                    reset_cpu_state()
                                    
                                    
                                elif dificultad_seleccionada == 'Medio':
                                    # Inicializar IA medio
                                    cpu_ia = IAMedio("CPU-Medio", mapa_ciudad, weather_system, pantalla)                                    
                                    
                                elif dificultad_seleccionada == 'Difícil':
                                    # Inicializar IA difícil
                                    cpu_ia = IADificil("CPU-Difícil", mapa_ciudad, weather_system, pantalla)
                                    
                                
                                estado = GAME
                            else:
                                # Si presionó ESC, volver al menú principal
                                menu_msg = "Selección cancelada"

                        elif seleccion == "Cargar partida":
                            loaded = datos.cargar_partida(SAVE_FILE)
                            if loaded:
                                jugador_rect = loaded['jugador_rect']
                                activos = loaded['activos']
                                ofertas = loaded['ofertas']
                                llevando_id = loaded['llevando_id']
                                entregas = loaded['entregas']
                                energia = loaded['energia']
                                dinero_ganado = loaded['dinero_ganado']
                                reputacion = loaded['reputacion']
                                msg = loaded['msg']
                                racha_sin_penalizacion = loaded['racha_sin_penalizacion']
                                primera_tardanza_fecha = loaded['primera_tardanza_fecha']
                                weather_system = WeatherSystem()
                                
                                # Cargar dificultad (si estaba guardada)
                                dificultad_cargada = loaded.get('dificultad', 'Fácil')
                                if dificultad_cargada == 'Difícil':
                                    mapa_ciudad = MapaJuego()
                                    cpu_ia = IADificil("CPU-Difícil", mapa_ciudad, weather_system, pantalla)
                                else:
                                    if dificultad_cargada == 'Medio':
                                        mapa_ciudad = MapaJuego()
                                        cpu_ia = IAMedio("CPU-Medio", mapa_ciudad, weather_system, pantalla)
                                    else:
                                        reset_cpu_state()
                                
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

        # records
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
        
        # Actualizar sistemas
        actualizar_clima()
        ultimo_spawn = intentar_spawn_oferta(ofertas, ultimo_spawn, OFERTAS_MAX, SPAWN_CADA_MS,
                                             jugador_rect, img_cliente, OBSTACULOS, pantalla)

        # Actualizar IA difícil si está activa
        if cpu_ia and estado == GAME:
            cpu_ia.actualizar(ofertas)

        # autosave
        if estado == GAME and ahora - ultimo_guardado_auto > intervalo_guardado_auto:
            snapshot = datos.snapshot_partida(
                jugador_rect, activos, ofertas, llevando_id, entregas, energia,
                dinero_ganado, reputacion, msg, racha_sin_penalizacion, primera_tardanza_fecha
            )
            # Agregar dificultad al snapshot
            snapshot["dificultad"] = dificultad_actual
            ok, m = datos.guardar_partida(snapshot, SAVE_FILE)
            if ok:
                msg_temporal = "Partida guardada automáticamente"
                tiempo_msg_temporal = ahora
                ultimo_guardado_auto = ahora
            else:
                msg_temporal = f"Error: {m}"
                tiempo_msg_temporal = ahora
                
        if msg_temporal and ahora - tiempo_msg_temporal > duracion_msg_temporal:
            msg_temporal = None

        # energía jugador humano
        if ahora - ultimo_tick_energia >= 1000:
            moving = (jugador_x_cambio_positivo or jugador_x_cambio_negativo or
                      jugador_y_cambio_positivo or jugador_y_cambio_negativo)
            if moving:
                costo = weather_system.get_energy_cost()
                if llevando_id is not None:
                    p_llev = next((x for x in activos if x["id"] == llevando_id), None)
                    if p_llev:
                        costo += p_llev["peso"] // 5
                energia = max(0, energia - int(round(costo)))
            else:
                # Si no se está moviendo, la energía se regenera poco a poco
                energia = min(100, energia + 3)
            ultimo_tick_energia = ahora

        # IA CPU fácil (si está activa)
        if estado == GAME and dificultad_actual in ['Fácil']:
            update_cpu_facil(dt)

        # input
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                datos.registrar_record(entregas, dinero_ganado, reputacion, RECORDS_FILE)
                corriendo = False

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    datos.registrar_record(entregas, dinero_ganado, reputacion, RECORDS_FILE)
                    estado = MENU

                # WASD mueve al jugador
                elif evento.key == pygame.K_s:
                    jugador_y_cambio_positivo = 0.1
                elif evento.key == pygame.K_w:
                    jugador_y_cambio_negativo = -0.1
                elif evento.key == pygame.K_a:
                    jugador_x_cambio_negativo = -0.1
                elif evento.key == pygame.K_d:
                    jugador_x_cambio_positivo = 0.1

                # panel
                elif evento.key == pygame.K_TAB:
                    panel_abierto = not panel_abierto
                    panel_idx = 0

                elif panel_abierto and evento.key == pygame.K_LEFT:
                    panel_tab = (panel_tab - 1) % 2
                    panel_idx = 0
                elif panel_abierto and evento.key == pygame.K_RIGHT:
                    panel_tab = (panel_tab + 1) % 2
                    panel_idx = 0
                elif panel_abierto and evento.key == pygame.K_UP:
                    lista = ofertas if panel_tab == 0 else activos
                    if lista:
                        panel_idx = (panel_idx - 1) % len(lista)
                elif panel_abierto and evento.key == pygame.K_DOWN:
                    lista = ofertas if panel_tab == 0 else activos
                    if lista:
                        panel_idx = (panel_idx + 1) % len(lista)
                elif panel_abierto and evento.key == pygame.K_RETURN:
                    if panel_tab == 0:
                        if ofertas:
                            p, new_msg = aceptar_oferta_seleccionada(panel_tab, panel_idx, ofertas, activos)
                            if p:
                                msg = new_msg
                                panel_idx = min(panel_idx, max(0, len(ofertas) - 1))
                        else:
                            msg = "No hay ofertas"
                    else:
                        if activos:
                            p, new_llevando_id, new_msg, new_reputacion, game_over, new_racha, new_fecha = cancelar_activo_seleccionado(
                                panel_tab, panel_idx, activos, llevando_id, reputacion, racha_sin_penalizacion,
                                primera_tardanza_fecha
                            )
                            if p:
                                llevando_id = new_llevando_id
                                msg = new_msg
                                reputacion = new_reputacion
                                racha_sin_penalizacion = new_racha
                                primera_tardanza_fecha = new_fecha
                                panel_idx = min(panel_idx, max(0, len(activos) - 1))
                                if game_over:
                                    fin_derrota()
                        else:
                            msg = "No hay pedidos activos"
                elif panel_abierto and evento.key == pygame.K_r:
                    if panel_tab == 0:
                        if ofertas:
                            p, new_msg = rechazar_oferta_seleccionada(panel_tab, panel_idx, ofertas)
                            if p:
                                msg = new_msg
                                panel_idx = min(panel_idx, max(0, len(ofertas) - 1))
                        else:
                            msg = "No hay ofertas"

                # recoger / entregar
                elif evento.key == pygame.K_q:
                    if llevando_id is None:
                        for p in activos:
                            if jugador_rect.colliderect(p["pickup"]):
                                llevando_id = p["id"]
                                msg = f"Recogido #{p['id']} ({p['peso']}kg)"
                                break
                elif evento.key == pygame.K_e:
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

                            reputacion, cambio, game_over, racha_sin_penalizacion, primera_tardanza_fecha = actualizar_reputacion(
                                evento_str, reputacion, racha_sin_penalizacion, primera_tardanza_fecha,
                                retraso_seg if evento_str == 'tarde' else 0
                            )

                            dinero_ganado += calcular_pago(p.get("payout", 0), reputacion)
                            activos = [x for x in activos if x["id"] != llevando_id]
                            entregas += 1
                            llevando_id = None

                            if game_over:
                                fin_derrota()

                # guardar
                elif evento.key == pygame.K_g:
                    snapshot = datos.snapshot_partida(
                        jugador_rect, activos, ofertas, llevando_id, entregas, energia,
                        dinero_ganado, reputacion, msg, racha_sin_penalizacion, primera_tardanza_fecha
                    )
                    snapshot["dificultad"] = dificultad_actual
                    ok, m = datos.guardar_partida(snapshot, SAVE_FILE)
                    if ok:
                        msg_temporal = "✓ Partida guardada manualmente"
                    else:
                        msg_temporal = f"✗ Error: {m}"
                    tiempo_msg_temporal = ahora
                    ultimo_guardado_auto = ahora

            elif evento.type == pygame.KEYUP:
                if evento.key == pygame.K_s:
                    jugador_y_cambio_positivo = 0.0
                elif evento.key == pygame.K_w:
                    jugador_y_cambio_negativo = 0.0
                elif evento.key == pygame.K_a:
                    jugador_x_cambio_negativo = 0.0
                elif evento.key == pygame.K_d:
                    jugador_x_cambio_positivo = 0.0

        # velocidad jugador humano
        peso_total = 0
        if llevando_id is not None:
            p_llev = next((x for x in activos if x["id"] == llevando_id), None)
            if p_llev:
                peso_total = p_llev["peso"]
        VEL = calcular_velocidad(peso_total, reputacion, energia, weather_system.get_weather_multiplier())

        # movimiento jugador humano
        vx_raw = jugador_x_cambio_positivo + jugador_x_cambio_negativo
        vy_raw = jugador_y_cambio_positivo + jugador_y_cambio_negativo
        dx = dy = 0.0
        if vx_raw != 0.0 or vy_raw != 0.0:
            l = math.hypot(vx_raw, vy_raw)
            if l != 0:
                ux, uy = vx_raw / l, vy_raw / l
                dx, dy = ux * VEL * dt, uy * VEL * dt
        mover_con_colision(jugador_rect, dx, dy, OBSTACULOS, pantalla)

        # movimiento CPU (dificultad fácil)
        if cpu_rect is not None and dificultad_actual in ['Fácil', 'Medio']:
            cpu_dx = cpu_dy = 0.0
            cpu_peso_total = 0
            if cpu_llevando_id is not None:
                p_llev_cpu = next((x for x in cpu_activos if x["id"] == cpu_llevando_id), None)
                if p_llev_cpu:
                    cpu_peso_total = p_llev_cpu["peso"]
            # La CPU usa la misma fórmula de velocidad que el jugador para que se muevan igual
            cpu_vel = calcular_velocidad(cpu_peso_total, cpu_reputacion, cpu_energia,
                                         weather_system.get_weather_multiplier())

            pos_cpu_antes = cpu_rect.copy()
            if cpu_vx != 0.0 or cpu_vy != 0.0:
                l_cpu = math.hypot(cpu_vx, cpu_vy)
                if l_cpu != 0:
                    ux_c, uy_c = cpu_vx / l_cpu, cpu_vy / l_cpu
                    cpu_dx, cpu_dy = ux_c * cpu_vel * dt, uy_c * cpu_vel * dt
            mover_con_colision(cpu_rect, cpu_dx, cpu_dy, OBSTACULOS, pantalla)

            # Detectar CPU atascada (tiene energía y/o objetivo pero no cambia de posición durante muchos frames)
            if cpu_energia > 5:
                if abs(cpu_rect.x - pos_cpu_antes.x) <= 1 and abs(cpu_rect.y - pos_cpu_antes.y) <= 1 and (cpu_vx != 0.0 or cpu_vy != 0.0):
                    cpu_frames_sin_mover += 1
                else:
                    cpu_frames_sin_mover = 0

                if cpu_frames_sin_mover >= 60:  # ~1 segundo sin moverse
                    # Reubicar suavemente a la CPU cerca de su posición actual
                    print("CPU fácil detectada como atascada, intentando desatascar...")
                    radios = [20, 40, 60, 80]
                    angulos = [0, 45, 90, 135, 180, 225, 270, 315]
                    nuevo_rect = cpu_rect.copy()
                    desatascada = False
                    for r in radios:
                        for ang in angulos:
                            rad = math.radians(ang)
                            nx = int(cpu_rect.centerx + r * math.cos(rad))
                            ny = int(cpu_rect.centery + r * math.sin(rad))
                            candidato = cpu_rect.copy()
                            candidato.center = (nx, ny)
                            if not pantalla.get_rect().contains(candidato):
                                continue
                            choca = False
                            for w in OBSTACULOS:
                                if candidato.colliderect(w):
                                    choca = True
                                    break
                            if not choca:
                                nuevo_rect = candidato
                                desatascada = True
                                break
                        if desatascada:
                            break
                    cpu_rect = nuevo_rect
                    cpu_frames_sin_mover = 0

        # expiraciones jugador humano
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

        # expiración de pedidos de la CPU fácil
        if dificultad_actual in ['Fácil', 'Medio']:
            expirados_cpu = [p for p in cpu_activos if ahora_ms > p["deadline"]]
            for p in expirados_cpu:
                cpu_reputacion, _, _, _, _ = actualizar_reputacion('perdido', cpu_reputacion, 0, None)
                if cpu_llevando_id == p["id"]:
                    cpu_llevando_id = None
                cpu_activos = [x for x in cpu_activos if x["id"] != p["id"]]

        # ===== DIBUJADO =====
        dibujar_fondo_y_obs(pantalla, weather_system.clima_actual)
        
        # Dibujar pedidos activos del jugador humano
        for p in activos:
            col = color_for_order(p['id'])
            pygame.draw.rect(pantalla, col, p["pickup"], 3)
            pygame.draw.rect(pantalla, col, p["dropoff"], 3)
            if llevando_id == p['id']:
                draw_dropoff_icon(pantalla, p["dropoff"], col)
            else:
                draw_pickup_icon(pantalla, p["pickup"], col)

        # Dibujar jugador humano
        pantalla.blit(img_jugador, jugador_rect.topleft)
        
        # Dibujar IA fácil 
        if cpu_rect is not None and dificultad_actual in ['Fácil']:
            pantalla.blit(img_cpu, cpu_rect.topleft)

        # Dibujar IA difícil
        if cpu_ia:
            cpu_ia.dibujar(pantalla, img_cpu)
            
        # Dibujar HUD completo
        dibujar_hud_completo(pantalla, font, entregas, dinero_ganado, reputacion,
                              weather_system.clima_actual, weather_system.intensidad_actual,
                              msg, energia, dificultad_actual, 
                              cpu_entregas, cpu_dinero, cpu_reputacion, cpu_energia, cpu_ia)

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