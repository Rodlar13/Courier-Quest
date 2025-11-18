import pygame
from base import calcular_velocidad, mover_con_colision
from configurar import OBSTACULOS, ANCHO, ALTO, FPS
from grafo import greedy_best_first

class IAMedio:
    def __init__(self, nombre, mapa, sistema_clima, pantalla):
        self.nombre = nombre
        self.mapa = mapa
        self.sistema_clima = sistema_clima
        self.pantalla = pantalla
        
        # Estado de la IA
        self.energia = 100
        self.dinero_ganado = 0
        self.reputacion = 70
        self.entregas = 0
        
        # Posición y tamaño en el mapa
        self.rect = pygame.Rect(200, 200, 48, 48)
        
        # Pedidos y pathfinding
        self.ofertas_disponibles = []
        self.pedidos_activos = []
        self.llevando_id = None
        self.camino_actual = []
        self.bloqueos_consecutivos = 0  # contador de pasos bloqueados
        self.indice_camino = 0
        self.objetivo_actual = None
        self.pedido_actual = None
        
        # Control de tiempo para actualizaciones periódicas
        self.ultimo_tick_energia = pygame.time.get_ticks()
        self.ultima_actualizacion = pygame.time.get_ticks()
        
        # Debug
        self.estado_actual = "Buscando pedido"
        self.ultimo_error = ""
        
    def actualizar(self, ofertas_globales):
        """Actualiza el estado de la IA: energía, movimiento y lógica de pedidos"""
        ahora = pygame.time.get_ticks()
        
        # Actualizar la lista de ofertas no aceptadas por otras IA
        self.ofertas_disponibles = [p for p in ofertas_globales if not p.get("aceptado_ia", False)]
        
        # Recargar energía cada 2 segundos
        if ahora - self.ultimo_tick_energia >= 2000:
            self.energia = min(100, self.energia + 2)
            self.ultimo_tick_energia = ahora
        
        # Mover la IA si ya tiene un camino calculado
        if self.camino_actual:
            self.mover_por_camino()
        
        # Ejecutar lógica principal solo cada 2 segundos
        if ahora - self.ultima_actualizacion < 2000:
            return
            
        self.ultima_actualizacion = ahora
        self.estado_actual = "Buscando pedido"
        
        try:
            # Elegir y aceptar un pedido si no hay activos
            if not self.pedidos_activos and self.ofertas_disponibles:
                self.elegir_y_aceptar_pedido()
            
            # Manejar el pedido actual si hay alguno
            if self.pedidos_activos:
                self.manejar_pedido_actual()
                
            # Calcular ruta si hay un objetivo pero no camino
            if not self.camino_actual and self.objetivo_actual:
                self.calcular_ruta_objetivo()
                
        except Exception as e:
            self.ultimo_error = f"Error en IA: {str(e)}"
            print(self.ultimo_error)
    
    def elegir_y_aceptar_pedido(self):
        """Elige el pedido más rentable usando Greedy Best-First y lo acepta"""
        if not self.ofertas_disponibles:
            return
            
        mejor_pedido = None
        mejor_puntaje = -1000
        mejor_camino = None
        
        for pedido in self.ofertas_disponibles:
            try:
                inicio = (self.rect.centerx, self.rect.centery)
                pickup = pedido["pickup"].center
                
                # Calcular ruta hacia el punto de pickup
                camino_recogida, costo_recogida = greedy_best_first(
                    self.mapa.grafo, inicio, pickup, self.sistema_clima
                )
                
                if not camino_recogida:
                    continue
                    
                # Calcular puntaje considerando payout y costo
                puntaje = pedido["payout"] - costo_recogida
                
                # Penalizar pedidos con deadline corto
                tiempo_restante = pedido["deadline"] - pygame.time.get_ticks()
                if tiempo_restante < 30000:
                    puntaje -= 20
                
                # Ajustar puntaje según peso del pedido
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
        
        # Aceptar el pedido seleccionado
        if mejor_pedido and mejor_camino:
            try:
                mejor_pedido["aceptado_ia"] = True
                self.pedidos_activos.append(mejor_pedido)
                self.pedido_actual = mejor_pedido
                self.camino_actual = mejor_camino
                self.indice_camino = 0
                self.objetivo_actual = mejor_pedido["pickup"].center
                self.estado_actual = f"Yendo a pickup #{mejor_pedido['id']}"
            except Exception as e:
                print(f"Error aceptando pedido: {e}")
    
    def manejar_pedido_actual(self):
        """Gestiona la recolección y entrega del pedido actual"""
        if not self.pedido_actual and self.pedidos_activos:
            self.pedido_actual = self.pedidos_activos[0]
            return
        
        if not self.pedido_actual:
            return
        
        # Recoger pedido si estamos en la posición de pickup
        if not self.llevando_id and self.rect.colliderect(self.pedido_actual["pickup"]):
            self.llevando_id = self.pedido_actual["id"]
            self.objetivo_actual = self.pedido_actual["dropoff"].center
            self.camino_actual = []  # Forzar recálculo de ruta
            self.estado_actual = f"Recogido #{self.pedido_actual['id']}, yendo a entrega"
            self.calcular_ruta_objetivo()
        
        # Entregar pedido si estamos en la posición de dropoff
        elif self.llevando_id and self.rect.colliderect(self.pedido_actual["dropoff"]):
            self.entregar_pedido()
    
    def entregar_pedido(self):
        """Entrega el pedido y actualiza dinero, entregas y reputación"""
        if not self.pedido_actual:
            return
            
        try:
            recompensa_base = self.pedido_actual["payout"]
            if self.reputacion >= 90:
                recompensa_base = int(recompensa_base * 1.05)
            
            self.dinero_ganado += recompensa_base
            self.entregas += 1
            self.reputacion = min(100, self.reputacion + 2)
            
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
        """Calcula ruta hacia el objetivo actual usando Greedy Best-First"""
        if not self.objetivo_actual:
            return
            
        try:
            inicio = (self.rect.centerx, self.rect.centery)
            nuevo_camino, _ = greedy_best_first(self.mapa.grafo, inicio, self.objetivo_actual, self.sistema_clima)
            if nuevo_camino:
                self.camino_actual = nuevo_camino
                self.indice_camino = 0
        except Exception as e:
            print(f"Error calculando ruta: {e}")
    
    def mover_por_camino(self):
        """Mueve la IA a lo largo del camino calculado, ajustando velocidad y colisiones"""
        if self.indice_camino >= len(self.camino_actual):
            self.camino_actual = []
            return
        
        try:
            objetivo = self.camino_actual[self.indice_camino]
            dx = objetivo[0] - self.rect.centerx
            dy = objetivo[1] - self.rect.centery
            
            # Ajustar velocidad según peso del pedido, reputación, energía y clima
            peso_total = self.pedido_actual["peso"] if self.llevando_id else 0
            VEL = calcular_velocidad(peso_total, self.reputacion, self.energia, self.sistema_clima.get_weather_multiplier())
            
            distancia = max(1, (dx**2 + dy**2)**0.5)
            dx_normalizado = dx / distancia
            dy_normalizado = dy / distancia
            
            pos_anterior = self.rect.copy()
            mover_con_colision(self.rect, dx_normalizado * VEL * 0.033, dy_normalizado * VEL * 0.033, OBSTACULOS, self.pantalla)
            
            if self.energia > 0:
                self.energia = max(0, self.energia - 0.05)
            
            # Verificar si se movió realmente, si no, avanzar al siguiente nodo
            se_movio = (abs(self.rect.x - pos_anterior.x) > 1 or abs(self.rect.y - pos_anterior.y) > 1)
            if not se_movio and (abs(dx) > 10 or abs(dy) > 10):
                self.indice_camino += 1
                return
            
            # Avanzar al siguiente nodo si estamos cerca del objetivo
            if abs(dx) < 20 and abs(dy) < 20:
                self.indice_camino += 1
                    
        except Exception as e:
            print(f"Error moviendo IA: {e}")
    

    def desatascar(self):
        """Intenta sacar a la IA de zonas donde está completamente atascada.

        Busca posiciones cercanas alrededor de la posición actual que:
        - Estén dentro de la pantalla
        - No colisionen con OBSTACULOS
        """
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
                        # Reubicar IA y limpiar camino para forzar recálculo
                        self.rect.center = candidato.center
                        self.camino_actual = []
                        self.indice_camino = 0
                        self.bloqueos_consecutivos = 0
                        print(f"IA media desatascada a {self.rect.center}")
                        return
            # Si no se encontró nada mejor, mantener posición original
            self.rect = original
        except Exception as e:
            print(f"Error desatascando IA media: {e}")

    def dibujar(self, pantalla, img_ia):
        """Dibuja la IA y los iconos de pickup/dropoff de sus pedidos"""
        try:
            pantalla.blit(img_ia, self.rect.topleft)
            color_ia = (100, 255, 100)  # verde para IA media
            
            for pedido in self.pedidos_activos:
                pygame.draw.rect(pantalla, color_ia, pedido["pickup"], 3)
                pygame.draw.rect(pantalla, color_ia, pedido["dropoff"], 3)
                
                # Mostrar icono según estado del pedido
                if self.llevando_id == pedido["id"]:
                    self.dibujar_icono_dropoff(pantalla, pedido["dropoff"], color_ia)
                else:
                    self.dibujar_icono_pickup(pantalla, pedido["pickup"], color_ia)
                    
        except Exception as e:
            print(f"Error dibujando IA: {e}")
    
    def dibujar_icono_pickup(self, pantalla, rect, color):
        """Dibuja un triángulo sobre la ubicación de pickup"""
        cx, cy = rect.center
        pts = [(cx, cy-8), (cx-8, cy+8), (cx+8, cy+8)]
        pygame.draw.polygon(pantalla, color, pts)
        pygame.draw.polygon(pantalla, (50, 50, 50), pts, 2)
    
    def dibujar_icono_dropoff(self, pantalla, rect, color):
        """Dibuja un círculo sobre la ubicación de dropoff"""
        cx, cy = rect.center
        pygame.draw.circle(pantalla, color, (cx, cy), 10)
        pygame.draw.circle(pantalla, (50, 50, 50), (cx, cy), 10, 2)
