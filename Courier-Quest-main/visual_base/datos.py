import json
from datetime import datetime, date
from configurar import SAVE_FILE, RECORDS_FILE, msg, jugador_rect
from base import nuevo_pedido
from graficos import img_jugador
import pygame

# -------------------- Guardar/Cargar partida --------------------

def snapshot_partida():
    return {
        "jugador": {"x": jugador_rect.x, "y": jugador_rect.y},
        "pedido": {
            "pickup": [pedido_actual["pickup"].x, pedido_actual["pickup"].y,
                       pedido_actual["pickup"].width, pedido_actual["pickup"].height],
            "dropoff": [pedido_actual["dropoff"].x, pedido_actual["dropoff"].y,
                        pedido_actual["dropoff"].width, pedido_actual["dropoff"].height],
            "payout": pedido_actual["payout"],
            "peso": pedido_actual["peso"],
            "deadline": pedido_actual["deadline"],
            "created_at": pedido_actual.get("created_at"),
            "duration": pedido_actual.get("duration")
        } if pedido_actual else None,
        "tiene_paquete": tiene_paquete,
        "entregas": entregas,
        "energia": energia,
        "dinero": dinero_ganado,
        "reputacion": reputacion,
        "msg": msg,
        "racha_sin_penalizacion": racha_sin_penalizacion,
        "primera_tardanza_fecha": primera_tardanza_fecha.isoformat() if primera_tardanza_fecha else None
    }


def aplicar_partida(data):
    global jugador_rect, pedido_actual, tiene_paquete, entregas, energia, dinero_ganado, reputacion, msg
    global racha_sin_penalizacion, primera_tardanza_fecha

    if not data:
        return

    j = data.get("jugador")
    if j:
        jugador_rect.topleft = (int(j.get("x", jugador_rect.x)), int(j.get("y", jugador_rect.y)))

    p = data.get("pedido")
    if p:
        try:
            pedido_actual = {
                "pickup": pygame.Rect(*p["pickup"]),
                "dropoff": pygame.Rect(*p["dropoff"]),
                "payout": p["payout"],
                "peso": p["peso"],
                "deadline": p["deadline"],
                "created_at": p.get("created_at", pygame.time.get_ticks()),
                "duration": p.get("duration", max(60000, p.get("deadline", pygame.time.get_ticks()) - p.get("created_at", pygame.time.get_ticks())))
            }
        except Exception:
            pedido_actual = nuevo_pedido()
    else:
        pedido_actual = nuevo_pedido()

    tiene_paquete = data.get("tiene_paquete", False)
    entregas = int(data.get("entregas", 0))
    energia = int(data.get("energia", 100))
    dinero_ganado = int(data.get("dinero", 0))
    reputacion = int(data.get("reputacion", 70))
    msg = data.get("msg", msg)
    racha_sin_penalizacion = int(data.get("racha_sin_penalizacion", 0))

    ptf = data.get("primera_tardanza_fecha")
    if ptf:
        try:
            primera_tardanza_fecha = date.fromisoformat(ptf)
        except Exception:
            primera_tardanza_fecha = None
    else:
        primera_tardanza_fecha = None


def guardar_partida():
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot_partida(), f, ensure_ascii=False, indent=2)
        return True, "Partida guardada"
    except Exception as e:
        return False, f"Error al guardar: {e}"


def cargar_partida():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        aplicar_partida(data)
        return True, "Partida cargada"
    except FileNotFoundError:
        return False, "No hay partida guardada"
    except Exception as e:
        return False, f"Error al cargar: {e}"


# -------------------- Records --------------------

def cargar_records():
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def guardar_records(lista):
    try:
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def registrar_record():
    recs = cargar_records()
    recs.append({
        "entregas": int(entregas),
        "dinero": int(dinero_ganado),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    recs.sort(key=lambda r: (r.get("entregas", 0), r.get("dinero", 0)), reverse=True)
    recs = recs[:10]
    guardar_records(recs)