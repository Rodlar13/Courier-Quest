import json
from datetime import datetime
from configurar import SAVE_FILE, RECORDS_FILE


def guardar_partida():
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot_partida(), f, ensure_ascii=False, indent=2)
        return True, "Partida guardada"
    except Exception as e:
        return False, f"Error al guardar: {e}"
    
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