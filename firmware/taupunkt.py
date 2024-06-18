import math


def taupunkt(T, r):
    # Taupunkt Formel: https://www.wetterochs.de/wetter/feuchte.html
    if T >= 0:
        a = 7.5
        b = 237.3
    else:  # t < 0
        a = 7.6
        b = 240.7

    # Sättigungsdampfdruck in hPa
    SDD = 6.1078 * pow(10, (a * T) / (b + T))

    # Dampfdruck in hPa
    DD = (r/100) * SDD

    # v-Parameter
    v = math.log10(DD/6.1078)

    # Taupunkttemperatur (°C)
    TD = b * v / (a-v)
    return TD
