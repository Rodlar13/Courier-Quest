
import os
import pygame


ANCHO, ALTO = 1500, 900
FPS = 60
CELDA = 48
v0 = 3 * CELDA  


SAVE_FILE = "partida.json"
RECORDS_FILE = "records.json"


BASE_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"


TAM_JUGADOR = (48, 48)
TAM_CLIENTE = (42, 42)
TAM_ICONO = (32, 32)


INICIO, MENU, GAME, RECORDS = 0, 1, 2, 3


OBSTACULOS = [
    pygame.Rect(120, 120, 225, 140), pygame.Rect(465, 120, 225, 140),
    pygame.Rect(810, 120, 225, 140), pygame.Rect(1155, 120, 225, 140),
    pygame.Rect(120, 380, 225, 140), pygame.Rect(465, 380, 225, 140),
    pygame.Rect(810, 380, 225, 140), pygame.Rect(1155, 380, 225, 140),
    pygame.Rect(120, 640, 225, 140), pygame.Rect(465, 640, 225, 140),
    pygame.Rect(810, 640, 225, 140), pygame.Rect(1155, 640, 225, 140),
]