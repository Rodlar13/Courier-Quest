import requests
import json
import os

BASE_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"

def obtener_datos_API(endpoint, archivo):
    try:
        r = requests.get(BASE_URL + endpoint, timeout=5)
        datos = r.json()
        with open(archivo, "w") as f:
            json.dump(datos, f, indent=2)
        print(f"Archivo {archivo} actualizado desde el API.")
        return datos
    except:
        print(f"No se pudo conectar. Revisando archivo {archivo}...")
        if os.path.exists(archivo):
            with open(archivo, "r") as f:
                return json.load(f)
        else:
            print("No hay datos disponibles.")
            return None

def guardar_partida(partida, archivo="partida.json"):
    with open(archivo, "w") as f:
        json.dump(partida, f, indent=2)
    print("Partida guardada.")

def cargar_partida(archivo="partida.json"):
    if os.path.exists(archivo):
        with open(archivo, "r") as f:
            return json.load(f)
    print("No hay partida guardada.")
    return None

def guardar_puntaje(nombre, puntos, archivo="puntajes.json"):
    puntajes = []
    if os.path.exists(archivo):
        with open(archivo, "r") as f:
            puntajes = json.load(f)
    puntajes.append({"jugador": nombre, "puntos": puntos})
    with open(archivo, "w") as f:
        json.dump(puntajes, f, indent=2)
    print("Puntaje guardado.")

def mostrar_puntajes(archivo="puntajes.json"):
    if os.path.exists(archivo):
        with open(archivo, "r") as f:
            puntajes = json.load(f)
            for p in puntajes:
                print(f"{p['jugador']}: {p['puntos']} puntos")
    else:
        print("No hay puntajes registrados.")