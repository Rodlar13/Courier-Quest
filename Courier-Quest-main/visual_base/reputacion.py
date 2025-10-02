
import math
from datetime import datetime, date

def calcular_pago(base_pago, reputacion):
    """Aplica bonus de reputación: +5% si reputación >= 90"""
    if reputacion >= 90:
        return int(round(base_pago * 1.05))
    return int(base_pago)

def actualizar_reputacion(evento, reputacion, racha_sin_penalizacion, primera_tardanza_fecha, tiempo_retraso_seg=0):
    """
    Aplica la regla de reputación. Devuelve (nueva_reputacion, cambio, game_over, nueva_racha, nueva_fecha_tardanza).
    """
    cambio = 0
    nueva_racha = racha_sin_penalizacion
    nueva_fecha = primera_tardanza_fecha

    if evento == "temprano":
        cambio = +5
        nueva_racha += 1
    elif evento == "a_tiempo":
        cambio = +3
        nueva_racha += 1
    elif evento == "tarde":
        # determinar penalización base
        if tiempo_retraso_seg <= 30:
            penal = -2
        elif tiempo_retraso_seg <= 120:
            penal = -5
        else:
            penal = -10

        # Primera tardanza del día: mitad de penalización si reputación >= 85
        today = datetime.now().date()
        if reputacion >= 85 and (primera_tardanza_fecha is None or primera_tardanza_fecha != today):
            # aplicar mitad (redondear hacia 0)
            penal = int(math.ceil(penal / 2.0)) if penal < 0 else penal
            nueva_fecha = today

        cambio = penal
        # cortar racha
        nueva_racha = 0
    elif evento == "cancelado":
        cambio = -4
        nueva_racha = 0
    elif evento == "perdido":
        cambio = -6
        nueva_racha = 0

    # Bono por racha de 3 entregas sin penalización: +2 (se aplica una vez y reinicia la racha)
    if nueva_racha >= 3:
        cambio += 2
        nueva_racha = 0

    nueva_reputacion = max(0, min(100, reputacion + cambio))
    game_over = nueva_reputacion < 20
    
    return nueva_reputacion, cambio, game_over, nueva_racha, nueva_fecha