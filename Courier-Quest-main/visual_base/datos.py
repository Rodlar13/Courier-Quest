# datos.py - Versión corregida
import json
import os
from datetime import datetime, date
import pygame
from configurar import BASE_URL, SAVE_FILE, RECORDS_FILE

def obtener_datos_API(endpoint, archivo):
    """
    Intenta obtener datos del API y guardarlos localmente.
    Si falla, usa el archivo local si existe.
    """
    try:
        import requests
        r = requests.get(BASE_URL + endpoint, timeout=5)
        datos = r.json()
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print(f"Archivo {archivo} actualizado desde el API.")
        return datos
    except Exception as e:
        print(f"No se pudo conectar ({e}). Revisando archivo {archivo}...")
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

def cargarDatosAPI():
    """
    Carga datos del API (opcional) para mapa, pedidos y clima.
    No es necesario para que el juego funcione.
    """
    try:
        mapa = obtener_datos_API("/city/map", "ciudad.json")
        jobs = obtener_datos_API("/city/jobs", "pedidos.json")
        clima = obtener_datos_API("/city/weather", "weather.json")
        return mapa, jobs, clima
    except Exception:
        return None, None, None

def snapshot_partida(jugador_rect, activos, ofertas, llevando_id, entregas, energia, 
                    dinero_ganado, reputacion, msg, racha_sin_penalizacion, primera_tardanza_fecha):
    """Crea un snapshot del estado actual del juego para guardar (multi-order version)"""
    snapshot = {
        "jugador": {"x": jugador_rect.x, "y": jugador_rect.y},
        "activos": [
            {
                "id": p["id"],
                "pickup": [p["pickup"].x, p["pickup"].y, p["pickup"].w, p["pickup"].h],
                "dropoff": [p["dropoff"].x, p["dropoff"].y, p["dropoff"].w, p["dropoff"].h],
                "payout": p["payout"],
                "peso": p["peso"],
                "deadline": p["deadline"],
                "created_at": p["created_at"],
                "duration": p["duration"],
                "aceptado": True,
                "llevando": (llevando_id == p["id"]),
            }
            for p in activos
        ],
        "ofertas": [
            {
                "id": p["id"],
                "pickup": [p["pickup"].x, p["pickup"].y, p["pickup"].w, p["pickup"].h],
                "dropoff": [p["dropoff"].x, p["dropoff"].y, p["dropoff"].w, p["dropoff"].h],
                "payout": p["payout"],
                "peso": p["peso"],
                "deadline": p["deadline"],
                "created_at": p["created_at"],
                "duration": p["duration"],
            }
            for p in ofertas
        ],
        "llevando_id": llevando_id,
        "entregas": entregas,
        "energia": energia,
        "dinero": dinero_ganado,
        "reputacion": reputacion,
        "msg": msg,
        "racha_sin_penalizacion": racha_sin_penalizacion,
        "primera_tardanza_fecha": primera_tardanza_fecha.isoformat() if primera_tardanza_fecha else None,
    }
    return snapshot

def aplicar_partida(data):
    """Procesa los datos cargados y aplica el estado del juego (multi-order version)"""
    if not data:
        return None
    
    try:
        # Crear nuevo rectángulo para el jugador
        jugador_data = data.get("jugador", {})
        jugador_rect = pygame.Rect(
            int(jugador_data.get("x", 728)), 
            int(jugador_data.get("y", 836)), 
            48, 48  # TAM_JUGADOR
        )
        
        # Procesar pedidos activos
        activos = []
        for p in data.get("activos", []):
            try:
                activos.append({
                    "id": int(p["id"]),
                    "pickup": pygame.Rect(*p["pickup"]),
                    "dropoff": pygame.Rect(*p["dropoff"]),
                    "payout": int(p["payout"]),
                    "peso": int(p["peso"]),
                    "deadline": int(p["deadline"]),
                    "created_at": int(p.get("created_at", pygame.time.get_ticks())),
                    "duration": int(p.get("duration", 90000)),
                    "aceptado": True,
                    "llevando": bool(p.get("llevando", False)),
                })
            except Exception as e:
                print(f"Error procesando pedido activo: {e}")
                continue
        
        # Procesar ofertas
        ofertas = []
        for p in data.get("ofertas", []):
            try:
                ofertas.append({
                    "id": int(p["id"]),
                    "pickup": pygame.Rect(*p["pickup"]),
                    "dropoff": pygame.Rect(*p["dropoff"]),
                    "payout": int(p["payout"]),
                    "peso": int(p["peso"]),
                    "deadline": int(p["deadline"]),
                    "created_at": int(p.get("created_at", pygame.time.get_ticks())),
                    "duration": int(p.get("duration", 90000)),
                    "aceptado": False,
                    "llevando": False,
                })
            except Exception as e:
                print(f"Error procesando oferta: {e}")
                continue
        
        # Extraer otros datos
        llevando_id = data.get("llevando_id")
        entregas = int(data.get("entregas", 0))
        energia = int(data.get("energia", 100))
        dinero_ganado = int(data.get("dinero", 0))
        reputacion = int(data.get("reputacion", 70))
        racha_sin_penalizacion = int(data.get("racha_sin_penalizacion", 0))
        msg = data.get("msg", "Partida cargada")
        
        # Procesar fecha de primera tardanza
        primera_tardanza_fecha = None
        ptf = data.get("primera_tardanza_fecha")
        if ptf:
            try:
                primera_tardanza_fecha = date.fromisoformat(ptf)
            except Exception:
                primera_tardanza_fecha = None
        
        return {
            'jugador_rect': jugador_rect,
            'activos': activos,
            'ofertas': ofertas,
            'llevando_id': llevando_id,
            'entregas': entregas,
            'energia': energia,
            'dinero_ganado': dinero_ganado,
            'reputacion': reputacion,
            'msg': msg,
            'racha_sin_penalizacion': racha_sin_penalizacion,
            'primera_tardanza_fecha': primera_tardanza_fecha
        }
    except Exception as e:
        print(f"Error aplicando partida: {e}")
        return None

def guardar_partida(snapshot, SAVE_FILE):
    """Guarda la partida en un archivo"""
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        return True, "Partida guardada"
    except Exception as e:
        return False, f"Error al guardar: {e}"

def cargar_partida(SAVE_FILE):
    """Carga una partida desde archivo"""
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return aplicar_partida(data)
    except FileNotFoundError:
        print("No se encontró archivo de partida guardada")
        return None
    except Exception as e:
        print(f"Error al cargar partida: {e}")
        return None

def cargar_records(RECORDS_FILE):
    """Carga los records desde archivo"""
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def guardar_records(lista, RECORDS_FILE):
    """Guarda los records en archivo"""
    try:
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando records: {e}")

def registrar_record(entregas, dinero_ganado, reputacion, RECORDS_FILE):
    """Registra un nuevo record con score calculado"""
    from datetime import datetime
    
    recs = cargar_records(RECORDS_FILE)
    
    # Calcular score (dinero * reputación)
    score = dinero_ganado * reputacion
    
    nuevo_record = {
        "entregas": int(entregas),
        "dinero": int(dinero_ganado),
        "reputacion": int(reputacion),
        "score": int(score),  # Agregar score calculado
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    recs.append(nuevo_record)
    
    # Ordenar por score (primero) y luego por entregas
    recs.sort(key=lambda r: (r.get("score", 0), r.get("entregas", 0)), reverse=True)
    recs = recs[:10]  # Mantener solo los top 10
    
    guardar_records(recs, RECORDS_FILE)