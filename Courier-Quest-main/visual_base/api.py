import os, json, requests
from configurar import BASE_URL

def obtener_datos_API(endpoint, archivo):
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


def cargarDatosAPI():
    # llamadas opcionales, no necesarias para que el juego funcione
    try:
        mapa = obtener_datos_API("/city/map", "ciudad.json")
        jobs = obtener_datos_API("/city/jobs", "pedidos.json")
        clima = obtener_datos_API("/city/weather", "weather.json")
        return mapa, jobs, clima
    except Exception:
        return None, None, None