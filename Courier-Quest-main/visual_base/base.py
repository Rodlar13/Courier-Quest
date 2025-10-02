
import math
import pygame
import random

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

def spawnear_cliente(lejos_de, obstaculos, pantalla, min_dist=180):
    for _ in range(400):
        x = random.randint(40, pantalla.get_width() - 40)
        y = random.randint(40, pantalla.get_height() - 40)
        if punto_valido(x, y, obstaculos, pantalla) and math.hypot(x - lejos_de[0], y - lejos_de[1]) >= min_dist:
            return pygame.Rect(0, 0, 42, 42)  
    return pygame.Rect(0, 0, 42, 42)  

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