# game_map.py
import heapq
import math
import pygame
from configurar import ANCHO, ALTO, OBSTACULOS


def greedy_best_first(grafo, inicio, fin, sistema_clima=None):
    """
    Greedy Best-First Search.
    Retorna (camino, costo_estimado)
    """
    try:
        if not grafo.nodos:
            return [], 1000
        
        inicio = encontrar_nodo_cercano(grafo, inicio)
        fin = encontrar_nodo_cercano(grafo, fin)
        if inicio is None or fin is None:
            return [], 1000
        
        # Estructuras
        frontera = []
        heapq.heappush(frontera, (0, inicio))
        came_from = {}
        visitados = set()
        visitados.add(inicio)
        
        while frontera:
            _, actual = heapq.heappop(frontera)
            
            if actual == fin:
                # Reconstruir camino
                camino = []
                nodo = fin
                while nodo in came_from:
                    camino.append(nodo)
                    nodo = came_from[nodo]
                camino.append(inicio)
                camino.reverse()
                # Costo aproximado (heurística)
                return camino, math.hypot(fin[0]-inicio[0], fin[1]-inicio[1])
            
            # Explorar vecinos
            for vecino in grafo.aristas.get(actual, {}):
                if vecino not in visitados:
                    visitados.add(vecino)
                    prioridad = math.hypot(vecino[0]-fin[0], vecino[1]-fin[1])
                    heapq.heappush(frontera, (prioridad, vecino))
                    came_from[vecino] = actual
        
        return [], 1000
    
    except Exception as e:
        print(f"Error en Greedy Best-First: {e}")
        return [], 1000 

class Grafo:
    def __init__(self):
        self.nodos = {}
        self.aristas = {}
    
    def agregar_nodo(self, id_nodo, datos_nodo):
        self.nodos[id_nodo] = datos_nodo
    
    def agregar_arista(self, desde_nodo, hasta_nodo, peso):
        if desde_nodo not in self.aristas:
            self.aristas[desde_nodo] = {}
        self.aristas[desde_nodo][hasta_nodo] = peso
        # Calles bidireccionales
        if hasta_nodo not in self.aristas:
            self.aristas[hasta_nodo] = {}
        self.aristas[hasta_nodo][desde_nodo] = peso

class MapaJuego:
    def __init__(self):
        self.grafo = Grafo()
        self.inicializar_grafo()
        print(f"Grafo inicializado con {len(self.grafo.nodos)} nodos")
    
    def es_posicion_valida(self, x, y):
        """Verifica si una posición es transitable (sin obstáculos)"""
        rect = pygame.Rect(0, 0, 32, 32)
        rect.center = (x, y)
        
        # Verificar dentro de pantalla
        pantalla_rect = pygame.Rect(0, 0, ANCHO, ALTO)
        if not pantalla_rect.contains(rect):
            return False
            
        # Verificar colisión con obstáculos
        for obstaculo in OBSTACULOS:
            if rect.colliderect(obstaculo):
                return False
        return True
    
    def inicializar_grafo(self):
        """Convierte el mapa en un grafo para pathfinding"""
        tamano_celda = 32
        nodos_creados = 0
        
        for y in range(tamano_celda//2, ALTO, tamano_celda):
            for x in range(tamano_celda//2, ANCHO, tamano_celda):
                nodo_id = (x, y)
                
                # Solo agregar nodos transitables
                if self.es_posicion_valida(x, y):
                    self.grafo.agregar_nodo(nodo_id, {'tipo': 'calle'})
                    nodos_creados += 1
                    
                    # Conectar con vecinos transitables
                    for dx, dy in [(tamano_celda, 0), (-tamano_celda, 0), 
                                 (0, tamano_celda), (0, -tamano_celda)]:
                        nx, ny = x + dx, y + dy
                        vecino_id = (nx, ny)
                        if self.es_posicion_valida(nx, ny):
                            peso = 1.0  # Peso base
                            self.grafo.agregar_arista(nodo_id, vecino_id, peso)

def dijkstra(grafo, inicio, fin, sistema_clima):
    """Algoritmo de Dijkstra para encontrar el camino más corto entre dos nodos en el grafo"""
    try:
        # Si no hay grafo, retornar error
        if not grafo.nodos:
            return [], 1000
        
        # Buscar nodos más cercanos si los puntos exactos no están en el grafo
        inicio = encontrar_nodo_cercano(grafo, inicio)
        fin = encontrar_nodo_cercano(grafo, fin)
        
        if inicio is None or fin is None:
            return [], 1000
        
        # Multiplicador por clima
        multiplicador_clima = sistema_clima.get_weather_multiplier()
        
        # Inicializar estructuras
        distancias = {inicio: 0}
        anteriores = {}
        cola = [(0, inicio)]
        
        while cola:
            distancia_actual, nodo_actual = heapq.heappop(cola)
            
            # Si llegamos al destino
            if nodo_actual == fin:
                break
            
            # Si este nodo ya tiene una distancia menor, ignorar
            if distancia_actual > distancias.get(nodo_actual, float('inf')):
                continue
            
            # Explorar vecinos
            if nodo_actual in grafo.aristas:
                for vecino, peso_base in grafo.aristas[nodo_actual].items():
                    peso_ajustado = peso_base / multiplicador_clima
                    nueva_distancia = distancia_actual + peso_ajustado
                    
                    # Si encontramos un camino más corto
                    if nueva_distancia < distancias.get(vecino, float('inf')):
                        distancias[vecino] = nueva_distancia
                        anteriores[vecino] = nodo_actual
                        heapq.heappush(cola, (nueva_distancia, vecino))
        
        # Reconstruir camino si llegamos al destino
        if fin in anteriores or fin == inicio:
            camino = []
            actual = fin
            
            while actual in anteriores:
                camino.append(actual)
                actual = anteriores[actual]
            
            camino.append(inicio)
            camino.reverse()
            
            # Calcular costo total
            costo = distancias.get(fin, 1000)
            
            return camino, costo
        else:
            return [], 1000
            
    except Exception as e:
        print(f"Error en Dijkstra: {e}")
        return [], 1000

def encontrar_nodo_cercano(grafo, punto):
    """Encuentra el nodo más cercano a un punto dado"""
    if not grafo.nodos:
        return None
    
    mejor_nodo = None
    mejor_distancia = float('inf')
    punto_x, punto_y = punto
    
    for nodo in grafo.nodos:
        nodo_x, nodo_y = nodo
        distancia = ((nodo_x - punto_x) ** 2 + (nodo_y - punto_y) ** 2) ** 0.5
        
        if distancia < mejor_distancia:
            mejor_distancia = distancia
            mejor_nodo = nodo
    
    return mejor_nodo
