import os
import pygame

# Screen settings
ANCHO, ALTO = 1500, 900
FPS = 60
CELDA = 48
v0 = 3 * CELDA

# Files
SAVE_FILE = "partida.json"
RECORDS_FILE = "records.json"
BASE_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"

# Sizes
TAM_JUGADOR = (48, 48)
TAM_CLIENTE = (42, 42)
TAM_ICONO = (32, 32)

# Game states
INICIO, MENU, GAME, RECORDS = 0, 1, 2, 3

# Obstacles
OBSTACULOS = [
    pygame.Rect(120, 120, 225, 140), pygame.Rect(465, 120, 225, 140),
    pygame.Rect(810, 120, 225, 140), pygame.Rect(1155, 120, 225, 140),
    pygame.Rect(120, 380, 225, 140), pygame.Rect(465, 380, 225, 140),
    pygame.Rect(810, 380, 225, 140), pygame.Rect(1155, 380, 225, 140),
    pygame.Rect(120, 640, 225, 140), pygame.Rect(465, 640, 225, 140),
    pygame.Rect(810, 640, 225, 140), pygame.Rect(1155, 640, 225, 140),
]

# Weather names
CLIMAS_ES = {
    "clear": "Despejado", "clouds": "Nublado", "rain_light": "Lluvia ligera",
    "rain": "Lluvia", "storm": "Tormenta", "fog": "Niebla",
    "wind": "Viento", "heat": "Calor", "cold": "Frío"
}

# Order settings
OFERTAS_MAX = 6
SPAWN_CADA_MS = 6000