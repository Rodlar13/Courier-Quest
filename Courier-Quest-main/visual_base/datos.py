
import json
import os
from datetime import datetime, date
import pygame

def obtener_datos_API(endpoint, archivo, BASE_URL):
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
        # No fatal: si no hay internet, usar archivo local si existe
        print(f"No se pudo conectar ({e}). Revisando archivo {archivo}...")
        if os.path.exists(archivo):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

def cargarDatosAPI(BASE_URL):
    """
    Carga datos del API (opcional) para mapa, pedidos y clima.
    No es necesario para que el juego funcione.
    """
    try:
        mapa = obtener_datos_API("/city/map", "ciudad.json", BASE_URL)
        jobs = obtener_datos_API("/city/jobs", "pedidos.json", BASE_URL)
        clima = obtener_datos_API("/city/weather", "weather.json", BASE_URL)
        return mapa, jobs, clima
    except Exception:
        return None, None, None

def snapshot_partida(jugador_rect, pedido_actual, tiene_paquete, entregas, energia, 
                    dinero_ganado, reputacion, msg, racha_sin_penalizacion, primera_tardanza_fecha):
    """Crea un snapshot del estado actual del juego para guardar"""
    snapshot = {
        "jugador": {"x": jugador_rect.x, "y": jugador_rect.y},
        "tiene_paquete": tiene_paquete,
        "entregas": entregas,
        "energia": energia,
        "dinero": dinero_ganado,
        "reputacion": reputacion,
        "msg": msg,
        "racha_sin_penalizacion": racha_sin_penalizacion,
        "primera_tardanza_fecha": primera_tardanza_fecha.isoformat() if primera_tardanza_fecha else None
    }
    
    if pedido_actual:
        snapshot["pedido"] = {
            "pickup": [pedido_actual["pickup"].x, pedido_actual["pickup"].y,
                      pedido_actual["pickup"].width, pedido_actual["pickup"].height],
            "dropoff": [pedido_actual["dropoff"].x, pedido_actual["dropoff"].y,
                       pedido_actual["dropoff"].width, pedido_actual["dropoff"].height],
            "payout": pedido_actual["payout"],
            "peso": pedido_actual["peso"],
            "deadline": pedido_actual["deadline"],
            "created_at": pedido_actual.get("created_at"),
            "duration": pedido_actual.get("duration")
        }
    else:
        snapshot["pedido"] = None
        
    return snapshot

def aplicar_partida(data):
    """
    Procesa los datos cargados y devuelve un diccionario con todos los estados.
    El main será responsable de aplicar estos datos.
    """
    if not data:
        return None

    # Extraer datos del jugador
    jugador_data = data.get("jugador", {})
    
    # Procesar datos del pedido
    pedido_data = data.get("pedido")
    pedido_actual = None
    if pedido_data:
        try:
            pedido_actual = {
                "pickup": pygame.Rect(*pedido_data["pickup"]),
                "dropoff": pygame.Rect(*pedido_data["dropoff"]),
                "payout": pedido_data["payout"],
                "peso": pedido_data["peso"],
                "deadline": pedido_data["deadline"],
                "created_at": pedido_data.get("created_at", pygame.time.get_ticks()),
                "duration": pedido_data.get("duration", max(60000, pedido_data["deadline"] - pedido_data.get("created_at", pygame.time.get_ticks())))
            }
        except Exception:
            pedido_actual = None

    # Extraer otros datos del juego
    tiene_paquete = data.get("tiene_paquete", False)
    entregas = int(data.get("entregas", 0))
    energia = int(data.get("energia", 100))
    dinero_ganado = int(data.get("dinero", 0))
    reputacion = int(data.get("reputacion", 70))
    msg = data.get("msg", "")
    racha_sin_penalizacion = int(data.get("racha_sin_penalizacion", 0))

    # Procesar fecha de primera tardanza
    primera_tardanza_fecha = None
    ptf = data.get("primera_tardanza_fecha")
    if ptf:
        try:
            primera_tardanza_fecha = date.fromisoformat(ptf)
        except Exception:
            primera_tardanza_fecha = None
            
    return {
        'jugador_pos': (int(jugador_data.get("x", 728)), int(jugador_data.get("y", 836))),
        'pedido_actual': pedido_actual,
        'tiene_paquete': tiene_paquete,
        'entregas': entregas,
        'energia': energia,
        'dinero_ganado': dinero_ganado,
        'reputacion': reputacion,
        'msg': msg,
        'racha_sin_penalizacion': racha_sin_penalizacion,
        'primera_tardanza_fecha': primera_tardanza_fecha
    }

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
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error al cargar: {e}")
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
    except Exception:
        pass

def registrar_record(entregas, dinero_ganado, reputacion,RECORDS_FILE):
    """Registra un nuevo record"""
    from datetime import datetime  # Import local para evitar dependencias
    
    recs = cargar_records(RECORDS_FILE)
    recs.append({
        "entregas": int(entregas),
        "dinero": int(dinero_ganado),
        "reputacion": int(reputacion),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    })
    recs.sort(key=lambda r: (r.get("entregas", 0), r.get("dinero", 0)), reverse=True)
    recs = recs[:10]
    guardar_records(recs, RECORDS_FILE)