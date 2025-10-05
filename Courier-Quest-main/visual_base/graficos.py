import pygame
import random
import os
import sys
from configurar import ANCHO, ALTO, TAM_JUGADOR, TAM_CLIENTE, TAM_ICONO, OBSTACULOS, CLIMAS_ES

def cargar_imagen_robusta(nombre, size=None, exit_on_fail=False):
    """
    Intenta cargar una imagen desde el directorio del script. 
    Si falla, retorna una superficie simple.
    """
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

def dibujar_fondo_y_obs(pantalla, clima_actual):
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
                msg, energia):
    y = 8
    linea_clima = f"Clima: {CLIMAS_ES.get(clima_actual, clima_actual)} ({intensidad_actual:.2f})"
    lineas = (
        "Mover: WASD | TAB panel | ←/→ pestaña | ↑/↓ selección | ENTER aceptar/cancelar | R rechazar",
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

    pantalla.blit(font.render("Energía:", True, (255, 255, 255)), (10, y))
    dibujar_barra(pantalla, 100, y, energia, 100, 200, 18)

    if reputacion >= 90:
        pantalla.blit(font.render("Pago: +5% (Excelencia)", True, (255, 220, 120)), (320, 8))

# colores por pedido
_def_color_cache = {}

def color_for_order(oid):
    c = _def_color_cache.get(oid)
    if c:
        return c
    rnd = random.Random(oid * 9973)
    r = rnd.randint(70, 235)
    g = rnd.randint(70, 235)
    b = rnd.randint(70, 235)
    _def_color_cache[oid] = (r, g, b)
    return _def_color_cache[oid]

# iconos pickup/dropoff
def draw_pickup_icon(pantalla, rect, color):
    cx, cy = rect.center
    pts = [(cx, cy-10), (cx-10, cy+10), (cx+10, cy+10)]
    pygame.draw.polygon(pantalla, color, pts)
    pygame.draw.polygon(pantalla, (10,10,10), pts, 2)

def draw_dropoff_icon(pantalla, rect, color):
    cx, cy = rect.center
    pygame.draw.circle(pantalla, color, (cx, cy), 12)
    pygame.draw.circle(pantalla, (10,10,10), (cx, cy), 12, 2)

# Panel de pedidos
def dibujar_panel(pantalla, font, font_big, panel_tab, panel_idx, ofertas, activos):
    ancho = 520
    rect = pygame.Rect(ANCHO - ancho, 0, ancho, ALTO)
    pygame.draw.rect(pantalla, (20, 24, 28), rect)
    pygame.draw.rect(pantalla, (80, 90, 100), rect, 2)
    t = font_big.render("Pedidos", True, (255, 255, 255))
    pantalla.blit(t, (rect.x + 20, 20))
    tabs = ["Ofertas", "Activos"]
    x0 = rect.x + 20
    for i, name in enumerate(tabs):
        c = (255, 255, 0) if i == panel_tab else (200, 200, 200)
        s = font.render(name, True, c)
        pantalla.blit(s, (x0 + i * 120, 70))
    lista = ofertas if panel_tab == 0 else activos
    y = 110
    if not lista:
        pantalla.blit(font.render("(vacío)", True, (180, 180, 180)), (rect.x + 20, y))
        return
    for i, p in enumerate(lista):
        sel = (i == panel_idx)
        bg = pygame.Rect(rect.x + 12, y - 4, rect.w - 24, 54)
        pygame.draw.rect(pantalla, (35, 40, 46) if not sel else (55, 65, 76), bg, border_radius=6)
        swatch = pygame.Rect(rect.x + 20, y + 6, 16, 16)
        pygame.draw.rect(pantalla, color_for_order(p['id']), swatch, border_radius=3)
        info = f"#{p['id']} • {p['peso']}kg • paga {p['payout']}$"
        dur = p.get("duration", 90000)
        now = pygame.time.get_ticks()
        restante = max(0, int((p['deadline'] - now) / 1000))
        tiempo = f"t:{restante}s"
        pantalla.blit(font.render(info, True, (240, 240, 240)), (rect.x + 44, y))
        pantalla.blit(font.render(tiempo, True, (220, 220, 220)), (rect.x + 44, y + 22))
        y += 64

# graficos.py - Función dibujar_records corregida
def dibujar_records(pantalla, font, font_big, RECORDS_FILE):
    """Dibuja la pantalla de records con score y reputación"""
    from datos import cargar_records
    
    pantalla.fill((20, 24, 28))
    
    # Título
    t = font_big.render("Records - Top 10", True, (255, 255, 255))
    pantalla.blit(t, (ANCHO // 2 - t.get_width() // 2, 80))
    
    # Subtítulo explicando el score
    subtitle = font.render("Score = Dinero × Reputación", True, (200, 200, 200))
    pantalla.blit(subtitle, (ANCHO // 2 - subtitle.get_width() // 2, 130))
    
    recs = cargar_records(RECORDS_FILE)
    
    if not recs:
        # No hay records
        no_records = font.render("No hay records aún. ¡Juega para establecer nuevos records!", True, (180, 180, 180))
        pantalla.blit(no_records, (ANCHO // 2 - no_records.get_width() // 2, 200))
    else:
        # Encabezado de la tabla
        y = 180
        header_bg = pygame.Rect(ANCHO // 2 - 400, y - 10, 800, 30)
        pygame.draw.rect(pantalla, (50, 60, 70), header_bg, border_radius=5)
        
        headers = ["Pos", "Entregas", "Dinero", "Reputación", "Score", "Fecha"]
        header_x_positions = [50, 150, 250, 350, 450, 600]
        
        for i, header in enumerate(headers):
            header_text = font.render(header, True, (255, 255, 0))
            pantalla.blit(header_text, (ANCHO // 2 - 400 + header_x_positions[i], y))
        
        y += 40
        
        # Lista de records
        for idx, r in enumerate(recs, 1):
            # Fondo alternado para mejor legibilidad
            bg_color = (35, 40, 46) if idx % 2 == 0 else (45, 50, 56)
            row_bg = pygame.Rect(ANCHO // 2 - 400, y - 5, 800, 30)
            pygame.draw.rect(pantalla, bg_color, row_bg, border_radius=4)
            
            # Datos del record
            entregas = r.get('entregas', 0)
            dinero = r.get('dinero', 0)
            reputacion_val = r.get('reputacion', 0)
            score = r.get('score', dinero * reputacion_val)  # Usar score guardado o calcular
            fecha = r.get('fecha', '')
            
            # Formatear números con separadores de miles
            dinero_str = f"{dinero:,}"
            score_str = f"{score:,}"
            
            # Textos de cada columna
            textos = [
                f"{idx}.",
                f"{entregas}",
                f"${dinero_str}",
                f"{reputacion_val}%",
                f"{score_str}",
                fecha
            ]
            
            # Dibujar cada columna
            for i, texto in enumerate(textos):
                color = (255, 255, 255)
                # Destacar el score
                if i == 4:  # Columna de score
                    color = (120, 255, 120) if score >= 100000 else (255, 255, 255)
                
                text_surf = font.render(texto, True, color)
                pantalla.blit(text_surf, (ANCHO // 2 - 400 + header_x_positions[i], y))
            
            y += 35
            
            # Limitar a 10 records visibles
            if idx >= 10:
                break
    
    # Instrucciones para volver
    volver_text = font.render("Presiona ESC para volver al menú", True, (200, 200, 200))
    pantalla.blit(volver_text, (ANCHO // 2 - volver_text.get_width() // 2, ALTO - 60))
    
    # Leyenda de colores
    leyenda = font.render("Score: Verde = ≥100,000 | Blanco = <100,000", True, (150, 150, 150))
    pantalla.blit(leyenda, (ANCHO // 2 - leyenda.get_width() // 2, ALTO - 30))