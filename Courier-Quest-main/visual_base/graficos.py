import pygame
import os, sys
from configurar import ANCHO, ALTO, pantalla,font, font_big
from datos import cargar_records, entregas, dinero_ganado, reputacion, msg, energia 
from obstaculos import OBSTACULOS
from clima import clima_actual, intensidad_actual, CLIMAS_ES


# -------------------- Imágenes --------------------
TAM_JUGADOR = (48, 48)
TAM_CLIENTE = (42, 42)
TAM_ICONO = (32, 32)


def cargar_imagen_robusta(nombre, size=None, exit_on_fail=False):
    """Intenta cargar una imagen desde el directorio del script. Si falla, retorna una superficie simple.
    Si exit_on_fail es True terminará el programa."""
    ruta = os.path.join(os.path.dirname(__file__), nombre)
    try:
        img = pygame.image.load(ruta)
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img.convert_alpha()
    except Exception as e:
        print(f"Aviso: no se pudo cargar {nombre}: {e}")
        if exit_on_fail:
            pygame.quit()
            sys.exit(f"Coloca {nombre} en la carpeta y vuelve a intentar.")
        # fallback: generar superficie identificable
        surf = pygame.Surface(size if size else (48, 48), pygame.SRCALPHA)
        surf.fill((200, 80, 80, 255))
        return surf

icono = cargar_imagen_robusta("mensajero.png", TAM_ICONO, exit_on_fail=False)
pygame.display.set_icon(icono)
img_jugador = cargar_imagen_robusta("mensajero.png", TAM_JUGADOR)
img_cliente = cargar_imagen_robusta("audiencia.png", TAM_CLIENTE)


# -------------------- Dibujo --------------------

def dibujar_fondo_y_obs():
    base_color = (51, 124, 196)
    if clima_actual in ("rain", "storm", "rain_light"):
        base_color = (40, 80, 120)
    elif clima_actual in ("clouds", "fog"):
        base_color = (80, 110, 140)
    elif clima_actual in ("heat",):
        base_color = (140, 120, 80)
    elif clima_actual in ("cold",):
        base_color = (90, 110, 140)
    pantalla.fill(base_color)

    for r in OBSTACULOS:
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
    recs = cargar_records()
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
    linea_clima = f"Clima: {CLIMAS_ES.get(clima_actual, clima_actual)} ({intensidad_actual:.2f})"
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

    # mostrar multiplicador si aplica
    if reputacion >= 90:
        pantalla.blit(font.render("Pago: +5% (Excelencia)", True, (255, 220, 120)), (320, 8))
