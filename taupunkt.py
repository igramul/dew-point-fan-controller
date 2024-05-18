import math

def taupunkt(t, r):
    # Taupunkt Formel: https://www.wetterochs.de/wetter/feuchte.html
    if t >= 0:
        a = 7.5
        b = 237.3
    else: #  t < 0
        a = 7.6
        b = 240.7

    # Sättigungsdampfdruck in hPa
    sdd = 6.1078 * pow(10, (a*t)/(b+t))

    # Dampfdruck in hPa
    dd = sdd * (r/100)

    # v-Parameter
    v = math.log10(dd/6.1078)

    # Taupunkttemperatur (°C)
    tt = (b*v) / (a-v)
    return tt
