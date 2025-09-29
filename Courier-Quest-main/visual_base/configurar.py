import pygame
import sys
from graficos import img_jugador

# -------------------- imports externos --------------------
try:
    import pygame
except Exception:
    print("ERROR: pygame no está instalado. Ejecuta 'pip install pygame' y vuelve a intentar.")
    sys.exit(1)
    
# -------------------- Configuración general --------------------

ANCHO, ALTO = 1500, 900
FPS = 60
CELDA = 48
v0 = 3 * CELDA  # velocidad base (px/seg)
SAVE_FILE = "partida.json"
RECORDS_FILE = "records.json"
BASE_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"

pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Courier Quest")

# Fuentes
font = pygame.font.SysFont(None, 22)
font_big = pygame.font.SysFont(None, 44)

# -------------------- Estados globales --------------------
energia = 100
dinero_ganado = 0
reputacion = 70 # INICIAL SEGUN REGLA
entregas = 0
racha_sin_penalizacion = 0
primera_tardanza_fecha = None  # date() cuando se aplicó la reducción de penalización

jugador_rect = img_jugador.get_rect(topleft=(728, 836))
jugador_x_cambio_positivo = 0.0
jugador_x_cambio_negativo = 0.0
jugador_y_cambio_positivo = 0.0
jugador_y_cambio_negativo = 0.0

pedido_actual = None
tiene_paquete = False
ultimo_tick_energia = pygame.time.get_ticks()
msg = "Bienvenido a Courier Quest"

