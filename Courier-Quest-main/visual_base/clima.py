import random
import pygame

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