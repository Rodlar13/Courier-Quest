import math
import pygame
import random
from configurar import ANCHO, ALTO, OBSTACULOS

def dentro_pantalla(rect, pantalla):
    return pantalla.get_rect().contains(rect)

def punto_valido(x, y, obstaculos, pantalla):
    p = pygame.Rect(0, 0, 32, 32)
    p.center = (x, y)
    if not dentro_pantalla(p, pantalla):
        return False
    for w in obstaculos:
        if p.colliderect(w):
            return False
    return True

def spawnear_cliente(lejos_de, img_cliente, obstaculos, pantalla, min_dist=180):
    for _ in range(400):
        x = random.randint(40, pantalla.get_width() - 40)
        y = random.randint(40, pantalla.get_height() - 40)
        p = pygame.Rect(0, 0, 32, 32)
        p.center = (x, y)
        
        # verificar que esté dentro de la pantalla
        if not pantalla.get_rect().contains(p):
            continue
            
        valid = True
        for w in obstaculos:
            if p.colliderect(w):
                valid = False
                break
                
        if valid and math.hypot(x - lejos_de[0], y - lejos_de[1]) >= min_dist:
            return img_cliente.get_rect(center=(x, y))
    return img_cliente.get_rect(center=(80, 80))

def mover_con_colision(rect: pygame.Rect, dx: float, dy: float, paredes, pantalla):
    # mover en X
    rect.x += int(round(dx))
    for w in paredes:
        if rect.colliderect(w):
            if dx > 0:
                rect.right = w.left
            elif dx < 0:
                rect.left = w.right
    # mover en Y
    rect.y += int(round(dy))
    for w in paredes:
        if rect.colliderect(w):
            if dy > 0:
                rect.bottom = w.top
            elif dy < 0:
                rect.top = w.bottom
    rect.clamp_ip(pantalla.get_rect())

def calcular_velocidad(peso_total, reputacion, energia, weather_multiplier):
    """Calculate player velocity based on various factors"""
    Mpeso = max(0.8, 1 - 0.03 * peso_total)
    Mrep = 1.03 if reputacion >= 90 else 1.0
    
    if energia > 30:
        Mresistencia = 1.0
    elif energia > 10:
        Mresistencia = 0.8
    else:
        Mresistencia = 0.0
        
    surf_weight = 1.0
    return 3 * 48 * Mpeso * Mrep * Mresistencia * weather_multiplier * surf_weight  # v0 = 3 * CELDA

# Order ID generator
_next_order_id = 1

def gen_id():
    global _next_order_id
    i = _next_order_id
    _next_order_id += 1
    return i

def nuevo_pedido(jugador_rect, img_cliente, obstaculos, pantalla):
    """Create a new delivery order"""
    pickup = spawnear_cliente(jugador_rect.center, img_cliente, obstaculos, pantalla)
    dropoff = spawnear_cliente(pickup.center, img_cliente, obstaculos, pantalla)
    
    now = pygame.time.get_ticks()
    duration = random.randint(60000, 120000)
    
    return {
        "id": gen_id(),
        "pickup": pickup,
        "dropoff": dropoff,
        "payout": random.randint(10, 50),
        "peso": random.randint(1, 10),
        "deadline": now + duration,
        "created_at": now,
        "duration": duration,
        "aceptado": False,
        "llevando": False,
    }

def intentar_spawn_oferta(ofertas, ultimo_spawn, ofertas_max, spawn_cada_ms, jugador_rect, img_cliente, obstaculos, pantalla):
    """Try to spawn a new offer"""
    now = pygame.time.get_ticks()
    if now - ultimo_spawn >= spawn_cada_ms and len(ofertas) < ofertas_max:
        ofertas.append(nuevo_pedido(jugador_rect, img_cliente, obstaculos, pantalla))
        return now  # Return new spawn time
    return ultimo_spawn

# Panel helpers
def aceptar_oferta_seleccionada(panel_tab, panel_idx, ofertas, activos):
    """Accept selected offer"""
    if panel_tab != 0 or not ofertas:
        return None, "No hay ofertas seleccionadas"
    if not (0 <= panel_idx < len(ofertas)):
        return None, "Índice inválido"
    
    p = ofertas.pop(panel_idx)
    p["aceptado"] = True
    activos.append(p)
    return p, f"Pedido #{p['id']} aceptado"

def rechazar_oferta_seleccionada(panel_tab, panel_idx, ofertas):
    """Reject selected offer"""
    if panel_tab != 0 or not ofertas:
        return None, "No hay ofertas seleccionadas"
    if not (0 <= panel_idx < len(ofertas)):
        return None, "Índice inválido"
    
    p = ofertas.pop(panel_idx)
    return p, f"Oferta #{p['id']} rechazada"

def cancelar_activo_seleccionado(panel_tab, panel_idx, activos, llevando_id, reputacion, racha_sin_penalizacion, primera_tardanza_fecha):
    """Cancel selected active order"""
    if panel_tab != 1 or not activos:
        return None, None, "No hay pedidos activos seleccionados"
    if not (0 <= panel_idx < len(activos)):
        return None, None, "Índice inválido"
    
    p = activos.pop(panel_idx)
    new_llevando_id = llevando_id
    if llevando_id == p["id"]:
        new_llevando_id = None
    
    from reputacion import actualizar_reputacion
    nueva_reputacion, cambio, game_over, nueva_racha, nueva_fecha = actualizar_reputacion(
        'cancelado', reputacion, racha_sin_penalizacion, primera_tardanza_fecha
    )
    
    return p, new_llevando_id, f"Pedido #{p['id']} cancelado ({cambio})", nueva_reputacion, game_over, nueva_racha, nueva_fecha