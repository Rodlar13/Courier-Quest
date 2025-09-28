import math
from datetime import datetime

def calcular_pago(base_pago):
    """Aplica bonus de reputación: +5% si reputación >= 90"""
    global reputacion
    if reputacion >= 90:
        return int(round(base_pago * 1.05))
    return int(base_pago)


def actualizar_reputacion(evento, tiempo_retraso_seg=0):
    """Aplica la regla de reputación. Devuelve (cambio, game_over_bool).

    evento: 'temprano', 'a_tiempo', 'tarde', 'cancelado', 'perdido'
    tiempo_retraso_seg: segundos de retraso (solo para 'tarde')
    """
    global reputacion, racha_sin_penalizacion, primera_tardanza_fecha

    cambio = 0

    if evento == "temprano":
        cambio = +5
        racha_sin_penalizacion += 1
    elif evento == "a_tiempo":
        cambio = +3
        racha_sin_penalizacion += 1
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
            primera_tardanza_fecha = today

        cambio = penal
        # cortar racha
        racha_sin_penalizacion = 0
    elif evento == "cancelado":
        cambio = -4
        racha_sin_penalizacion = 0
    elif evento == "perdido":
        cambio = -6
        racha_sin_penalizacion = 0

    # Bono por racha de 3 entregas sin penalización: +2 (se aplica una vez y reinicia la racha)
    if racha_sin_penalizacion >= 3:
        cambio += 2
        racha_sin_penalizacion = 0

    reputacion = max(0, min(100, reputacion + cambio))

    game_over = reputacion < 20
    return cambio, game_over