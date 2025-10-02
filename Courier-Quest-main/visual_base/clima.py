
import random


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

# Markov 
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

class WeatherSystem:
    def __init__(self):
        self.clima_actual = "clear"
        self.intensidad_actual = random.uniform(0.3, 0.7)
        self.intensidad_inicio = self.intensidad_actual
        self.clima_objetivo = self.clima_actual
        self.intensidad_objetivo = self.intensidad_actual
        self.transicion = False
        self.transicion_inicio = 0
        self.transicion_duracion = 0
        self.ultimo_cambio_clima = 0
        self.duracion_actual = random.uniform(45000, 60000)

    def elegir_siguiente_clima(self, actual):
        trans = TRANSICIONES.get(actual, TRANSICIONES["clear"])
        r = random.random()
        acumulado = 0.0
        for estado, prob in trans:
            acumulado += prob
            if r <= acumulado:
                return estado
        return actual

    def iniciar_transicion(self, nuevo_clima, ahora_ms):
        """Prepara variables para una transición suave"""
        self.clima_objetivo = nuevo_clima
        self.intensidad_objetivo = random.uniform(0.3, 1.0)
        self.intensidad_inicio = self.intensidad_actual
        self.transicion = True
        self.transicion_inicio = ahora_ms
        self.transicion_duracion = random.uniform(3000, 5000)

    def actualizar(self, ahora):
        """Se llama cada frame. Controla ráfagas y transiciones."""
        if self.transicion:
            dur = self.transicion_duracion if self.transicion_duracion > 0 else 1
            t = (ahora - self.transicion_inicio) / dur
            if t >= 1.0:
                # fin transición
                self.clima_actual = self.clima_objetivo
                self.intensidad_actual = self.intensidad_objetivo
                self.transicion = False
                self.ultimo_cambio_clima = ahora
                self.duracion_actual = random.uniform(45000, 60000)
            else:
                # interpolación lineal
                self.intensidad_actual = (1 - t) * self.intensidad_inicio + t * self.intensidad_objetivo
            return

        # si terminó la ráfaga -> iniciar transición
        if ahora - self.ultimo_cambio_clima > self.duracion_actual:
            siguiente = self.elegir_siguiente_clima(self.clima_actual)
            self.iniciar_transicion(siguiente, ahora)

    def get_weather_multiplier(self):
        """Returns speed multiplier based on current weather"""
        multipliers = {
            "clear": 1.0,
            "clouds": 0.97,
            "rain_light": 0.95,
            "rain": 0.9,
            "storm": 0.85,
            "fog": 0.95,
            "wind": 0.9,
            "heat": 0.92,
            "cold": 0.95
        }
        return multipliers.get(self.clima_actual, 1.0)

    def get_energy_cost(self):
        """Returns energy cost based on current weather"""
        costs = {
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
        return costs.get(self.clima_actual, 1)

    def get_base_color(self):
        """Returns background color based on weather"""
        colors = {
            "clear": (51, 124, 196),
            "rain": (40, 80, 120),
            "rain_light": (40, 80, 120),
            "storm": (40, 80, 120),
            "clouds": (80, 110, 140),
            "fog": (80, 110, 140),
            "heat": (140, 120, 80),
            "cold": (90, 110, 140)
        }
        return colors.get(self.clima_actual, (51, 124, 196))