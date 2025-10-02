
import pygame
import os
import sys

def cargar_imagen_robusta(nombre, size=None, exit_on_fail=False):
    """
    Intenta cargar una imagen desde el directorio del script. 
    Si falla, retorna una superficie simple.
    """
    ruta = os.path.join(os.path.dirname(__file__), "..", nombre)
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

def dibujar_fondo_y_obs(pantalla, obstaculos, weather_system):
    base_color = weather_system.get_base_color()
    pantalla.fill(base_color)

    for r in obstaculos:
        pygame.draw.rect(pantalla, (170, 120, 80), r, border_radius=6)
        pygame.draw.rect(pantalla, (140, 90, 60), r, 3, border_radius=6)

def dibujar_barra(pantalla, x, y, valor, max_valor, ancho, alto):
    v = max(0, min(valor, max_valor))
    pygame.draw.rect(pantalla, (60, 60, 60), (x, y, ancho, alto))
    relleno = int((v / max_valor) * ancho) if max_valor > 0 else 0
    if relleno > 0:
        pygame.draw.rect(pantalla, (0, 200, 0), (x, y, relleno, alto))

def dibujar_menu(pantalla, opciones, seleccionado, font, font_big, titulo="Courier Quest", subtitulo="Usa ↑/↓ y ENTER"):
    pantalla.fill((20, 24, 28))
    t = font_big.render(titulo, True, (255, 255, 255))
    pantalla.blit(t, (pantalla.get_width() // 2 - t.get_width() // 2, 140))
    s = font.render(subtitulo, True, (200, 200, 200))
    pantalla.blit(s, (pantalla.get_width() // 2 - s.get_width() // 2, 200))
    y0 = 280
    for i, op in enumerate(opciones):
        color = (255, 255, 0) if i == seleccionado else (220, 220, 220)
        surf = font.render(op, True, color)
        pantalla.blit(surf, (pantalla.get_width() // 2 - surf.get_width() // 2, y0 + i * 44))

def dibujar_hud(pantalla, font, entregas, dinero_ganado, reputacion, clima_actual, intensidad_actual, 
                msg, energia, weather_system):
    y = 8
    linea_clima = f"Clima: {weather_system.CLIMAS_ES.get(clima_actual, clima_actual)} ({intensidad_actual:.2f})"
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
    dibujar_barra(pantalla, 100, y, energia, 100, 200, 18)

    # mostrar multiplicador si aplica
    if reputacion >= 90:
        pantalla.blit(font.render("Pago: +5% (Excelencia)", True, (255, 220, 120)), (320, 8))