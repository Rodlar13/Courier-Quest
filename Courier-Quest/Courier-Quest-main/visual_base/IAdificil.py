# IAdificil.py
import pygame
import random
from base import calcular_velocidad, mover_con_colision
from configurar import OBSTACULOS, ANCHO, ALTO, FPS
from grafo import *


class IADificil:
    def __init__(self, nombre, mapa, sistema_clima, pantalla):
        self.nombre = nombre
        self.mapa = mapa
        self.sistema_clima = sistema_clima
        self.pantalla = pantalla
        self.energia = 100
        self.ultimo_consumo = pygame.time.get_ticks()
        
        # Estado del jugador IA
        self.energia = 100
        self.dinero_ganado = 0
        self.reputacion = 70
        self.entregas = 0
        # Posición inicial diferente del jugador humano
        self.rect = pygame.Rect(200, 200, 48, 48)
        
        # Sistema de pedidos
        self.ofertas_disponibles = []
        self.pedidos_activos = []
        self.llevando_id = None
        
        # Pathfinding
        self.bloqueos_consecutivos = 0  # contador de pasos bloqueados
        self.camino_actual = []
        self.indice_camino = 0
        self.objetivo_actual = None
        self.pedido_actual = None
        
        # Tiempo
        self.ultimo_tick_energia = pygame.time.get_ticks()
        self.ultima_actualizacion = pygame.time.get_ticks()
        
        # Debug
        self.estado_actual = "Buscando pedido"
        self.ultimo_error = ""
        
    def actualizar(self, ofertas_globales):
        """Actualiza el estado de la IA cada frame"""
        ahora = pygame.time.get_ticks()
        
        # Filtrar ofertas disponibles (no aceptadas por IA)
        self.ofertas_disponibles = [p for p in ofertas_globales if not p.get("aceptado_ia", False)]
        
        # Recargar energía lentamente
        
        if ahora - self.ultimo_tick_energia >= 2000:
            self.energia = min(100, self.energia + 2)
            self.ultimo_tick_energia = ahora
           
       # if not self.camino_actual:
        #    self.energia = min(100, self.energia + 0.5)
        
          # CONSUMO SIMPLE DE ENERGÍA
        if self.camino_actual and ahora - self.ultimo_consumo > 1000:  # Cada segundo
            self.energia = max(0, self.energia - 3)
            self.ultimo_consumo = ahora
        
        # Mover si hay camino (esto se hace cada frame para movimiento suave)
        if self.camino_actual:
            self.mover_por_camino()
        
        # Lógica principal cada 2 segundos para mejor performance
        if ahora - self.ultima_actualizacion < 2000:
            return
            
        self.ultima_actualizacion = ahora
        self.estado_actual = "Buscando pedido"
        
        try:
            # Si no tiene pedidos activos, elegir uno
            if not self.pedidos_activos and self.ofertas_disponibles:
                self.elegir_y_aceptar_pedido()
            
            # Si tiene pedidos activos, manejar el actual
            if self.pedidos_activos:
                self.manejar_pedido_actual()
                
            # Si no hay camino y hay objetivo, calcular ruta
            if not self.camino_actual and self.objetivo_actual:
                self.calcular_ruta_objetivo()
                
        except Exception as e:
            self.ultimo_error = f"Error en IA: {str(e)}"
            print(self.ultimo_error)
    
    def elegir_y_aceptar_pedido(self):
        """Elige el pedido más óptimo usando Dijkstra"""
        if not self.ofertas_disponibles:
            return
            
        mejor_pedido = None
        mejor_puntaje = -1000
        mejor_camino = None
        
        for pedido in self.ofertas_disponibles:
            try:
                # Calcular ruta desde posición actual al pickup
                inicio = (self.rect.centerx, self.rect.centery)
                pickup = pedido["pickup"].center
                
                print(f"IA calculando ruta desde {inicio} a {pickup}")
                camino_recogida, costo_recogida = dijkstra(
                    self.mapa.grafo, inicio, pickup, self.sistema_clima
                )
                
                if not camino_recogida:
                    print(f"No se encontró camino para pedido #{pedido['id']}")
                    continue
                
                print(f"Camino encontrado: {len(camino_recogida)} pasos, costo: {costo_recogida}")
                    
                # Calcular puntaje simple
                puntaje = pedido["payout"] - costo_recogida
                
                # Bonus/penalizaciones
                tiempo_restante = pedido["deadline"] - pygame.time.get_ticks()
                if tiempo_restante < 30000:
                    puntaje -= 20
                
                if pedido["peso"] <= 3:
                    puntaje += 5
                elif pedido["peso"] >= 8:
                    puntaje -= 5
                
                if puntaje > mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor_pedido = pedido
                    mejor_camino = camino_recogida
                    
            except Exception as e:
                print(f"Error evaluando pedido {pedido.get('id', '?')}: {e}")
                continue
        
        if mejor_pedido and mejor_camino:
            try:
                # Marcar pedido como aceptado por la IA
                mejor_pedido["aceptado_ia"] = True
                
                # Agregar a lista de pedidos activos de la IA
                self.pedidos_activos.append(mejor_pedido)
                self.pedido_actual = mejor_pedido
                
                # Configurar camino hacia pickup
                self.camino_actual = mejor_camino
                self.indice_camino = 0
                self.objetivo_actual = mejor_pedido["pickup"].center
                self.estado_actual = f"Yendo a pickup #{mejor_pedido['id']}"
                
                print(f"IA aceptó pedido #{mejor_pedido.get('id', '?')} con puntaje {mejor_puntaje:.1f}")
                print(f"Camino: {len(self.camino_actual)} pasos")
                
            except Exception as e:
                print(f"Error aceptando pedido: {e}")
    
    def manejar_pedido_actual(self):
        """Maneja el pedido actual de la IA"""
        if not self.pedido_actual and self.pedidos_activos:
            self.pedido_actual = self.pedidos_activos[0]
            return
        
        if not self.pedido_actual:
            return
        
        # Si no está llevando el paquete y llegó al pickup
        if not self.llevando_id and self.rect.colliderect(self.pedido_actual["pickup"]):
            self.llevando_id = self.pedido_actual["id"]
            self.objetivo_actual = self.pedido_actual["dropoff"].center
            self.camino_actual = []  # Forzar recálculo de ruta
            self.estado_actual = f"Recogido #{self.pedido_actual['id']}, yendo a entrega"
            print(f"IA recogió pedido #{self.pedido_actual.get('id', '?')}")
        
        # Si está llevando el paquete y llegó al dropoff
        elif self.llevando_id and self.rect.colliderect(self.pedido_actual["dropoff"]):
            self.entregar_pedido()
    
    def entregar_pedido(self):
        """Entrega el pedido actual"""
        if not self.pedido_actual:
            return
            
        try:
            # Calcular recompensa
            recompensa_base = self.pedido_actual["payout"]
            if self.reputacion >= 90:
                recompensa_base = int(recompensa_base * 1.05)
            
            self.dinero_ganado += recompensa_base
            self.entregas += 1
            self.reputacion = min(100, self.reputacion + 2)
            
            print(f"IA entregó pedido #{self.pedido_actual.get('id', '?')} por ${recompensa_base}")
            
            # Limpiar estado
            pedido_entregado = self.pedido_actual
            self.pedidos_activos.remove(pedido_entregado)
            self.llevando_id = None
            self.pedido_actual = None
            self.objetivo_actual = None
            self.camino_actual = []
            self.estado_actual = "Buscando nuevo pedido"
            
        except Exception as e:
            print(f"Error entregando pedido: {e}")
    
    def calcular_ruta_objetivo(self):
        """Calcula ruta hacia el objetivo actual"""
        if not self.objetivo_actual:
            return
            
        try:
            inicio = (self.rect.centerx, self.rect.centery)
            print(f"Recalculando ruta desde {inicio} a {self.objetivo_actual}")
            nuevo_camino, _ = dijkstra(self.mapa.grafo, inicio, self.objetivo_actual, self.sistema_clima)
            if nuevo_camino:
                self.camino_actual = nuevo_camino
                self.indice_camino = 0
                print(f"Nueva ruta calculada: {len(nuevo_camino)} pasos")
            else:
                print("No se pudo calcular nueva ruta")
        except Exception as e:
            print(f"Error calculando ruta: {e}")
    
    def mover_por_camino(self):
        """Mueve la IA hacia el siguiente punto del camino - CON RECUPERACIÓN DE BLOQUEOS"""
        if self.indice_camino >= len(self.camino_actual):
            print("Fin del camino alcanzado")
            self.camino_actual = []
            return
        
        try:
            objetivo = self.camino_actual[self.indice_camino]
            dx = objetivo[0] - self.rect.centerx
            dy = objetivo[1] - self.rect.centery
            
            # Calcular velocidad
            peso_total = 0
            if self.llevando_id and self.pedido_actual:
                peso_total = self.pedido_actual["peso"]
            
            VEL = calcular_velocidad(peso_total, self.reputacion, self.energia, 
                                self.sistema_clima.get_weather_multiplier())
            
            # Normalizar dirección
            distancia = max(1, (dx**2 + dy**2)**0.5)
            dx_normalizado = dx / distancia
            dy_normalizado = dy / distancia
            
            # Intentar mover
            movimiento_x = dx_normalizado * VEL * 0.033
            movimiento_y = dy_normalizado * VEL * 0.033
            
            # Guardar posición anterior para recuperación
            pos_anterior = self.rect.copy()
            
            # Intentar mover con colisiones
            mover_con_colision(self.rect, movimiento_x, movimiento_y, OBSTACULOS, self.pantalla)
            
            # DETECTAR SI SE QUEDÓ PEGADO
            se_movio = (abs(self.rect.x - pos_anterior.x) > 1 or 
                    abs(self.rect.y - pos_anterior.y) > 1)
            
            if not se_movio and (abs(dx) > 10 or abs(dy) > 10):
                print(f"IA bloqueada en paso {self.indice_camino}, saltando al siguiente...")
                self.indice_camino += 1
                return
            
            # Verificar si llegó al punto del camino
            if abs(dx) < 20 and abs(dy) < 20:
                self.indice_camino += 1
                print(f"IA avanzó al paso {self.indice_camino}/{len(self.camino_actual)}")
                    
        except Exception as e:
            print(f"Error moviendo IA: {e}")
    

    def desatascar(self):
        """Intenta sacar a la IA difícil de zonas donde está completamente atascada."""
        try:
            radios = [20, 40, 60, 80, 100]
            angulos = [0, 45, 90, 135, 180, 225, 270, 315]
            original = self.rect.copy()
            for r in radios:
                for ang in angulos:
                    rad = math.radians(ang)
                    nx = int(self.rect.centerx + r * math.cos(rad))
                    ny = int(self.rect.centery + r * math.sin(rad))
                    candidato = self.rect.copy()
                    candidato.center = (nx, ny)
                    if not self.pantalla.get_rect().contains(candidato):
                        continue
                    choca = False
                    for w in OBSTACULOS:
                        if candidato.colliderect(w):
                            choca = True
                            break
                    if not choca:
                        self.rect.center = candidato.center
                        self.camino_actual = []
                        self.indice_camino = 0
                        self.bloqueos_consecutivos = 0
                        print(f"IA difícil desatascada a {self.rect.center}")
                        return
            self.rect = original
        except Exception as e:
            print(f"Error desatascando IA difícil: {e}")

    def dibujar(self, pantalla, img_ia):
        """Dibuja la IA y sus pedidos en pantalla"""
        try:
            # Dibujar sprite de la IA
            pantalla.blit(img_ia, self.rect.topleft)
            
            # Dibujar pedidos activos de la IA
            for pedido in self.pedidos_activos:
                # Dibujar pickup y dropoff con color distintivo de la IA
                color_ia = (255, 100, 100)  # Rojo para IA difícil
                pygame.draw.rect(pantalla, color_ia, pedido["pickup"], 3)
                pygame.draw.rect(pantalla, color_ia, pedido["dropoff"], 3)
                
                # Dibujar iconos según estado
                if self.llevando_id == pedido["id"]:
                    self.dibujar_icono_dropoff(pantalla, pedido["dropoff"], color_ia)
                else:
                    self.dibujar_icono_pickup(pantalla, pedido["pickup"], color_ia)
            
            
        except Exception as e:
            print(f"Error dibujando IA: {e}")
    
    def dibujar_icono_pickup(self, pantalla, rect, color):
        """Dibuja icono de pickup para pedidos de la IA"""
        cx, cy = rect.center
        # Triángulo para pickup
        pts = [(cx, cy-8), (cx-8, cy+8), (cx+8, cy+8)]
        pygame.draw.polygon(pantalla, color, pts)
        pygame.draw.polygon(pantalla, (50, 50, 50), pts, 2)
    
    def dibujar_icono_dropoff(self, pantalla, rect, color):
        """Dibuja icono de dropoff para pedidos de la IA"""
        cx, cy = rect.center
        # Círculo para dropoff
        pygame.draw.circle(pantalla, color, (cx, cy), 10)
        pygame.draw.circle(pantalla, (50, 50, 50), (cx, cy), 10, 2)
    
    
   