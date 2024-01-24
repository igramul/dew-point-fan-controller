# Dew Point Fan Controller
# January 2024, by Lukas Burger

import machine
import rp2
import dht
import time
import math
import ubinascii
import network
import ntptime
import ujson
import uasyncio as asyncio
import _thread


from pcf8574 import PCF8574
from hd44780 import HD44780
from lcd import LCD

VERSION = '0.1.1'

SCHALTmin = 5.0 #  minimum dew point difference at which the fan switches
HYSTERESE = 1.0 #  distance from switch-on and switch-off point
TEMP_indoor_min = 10.0 #  minimum indoor temperature at which the ventilation is activated
TEMP_oudside_min = -10.0 #  minimum outside temperature at which the ventilation is activated

ntptime.host = '1.europe.pool.ntp.org' # default time server


STAT_NO_IP = 2

NetworkStat = {
    network.STAT_IDLE: 'no connection and no activity',                 #   0
    network.STAT_CONNECTING: 'connecting in progress',                  #   1
    STAT_NO_IP: 'connected to wifi, but no IP address',                 #   2 (WTF! not defined in network)
    network.STAT_GOT_IP: 'connection successful',                       #   3
    network.STAT_CONNECT_FAIL: 'failed due to other problems',          #  -1 
    network.STAT_NO_AP_FOUND: 'failed because no access point replied', #  -2
    network.STAT_WRONG_PASSWORD: 'failed due to incorrect password',    #  -3
}

html = """<!DOCTYPE html>
<html>
    <head> <title>Dew Point Fan Controller</title> </head>
    <body> <h1>Dew Point Fan Controller</h1>
        <p>%s</p>
    </body>
</html>
"""

led_wlan = machine.Pin(17, machine.Pin.OUT)
led_status = machine.Pin(18, machine.Pin.OUT)
led_onboard = machine.Pin("LED", machine.Pin.OUT, value=0)

sensor_indoor = dht.DHT22(machine.Pin(14))
sensor_outside = dht.DHT22(machine.Pin(16))

fan_relais = machine.Pin(15, machine.Pin.OUT)

i2c = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)
pcf8574 = PCF8574(i2c)
hd44780 = HD44780(pcf8574, num_lines=4, num_columns=20)
lcd = LCD(hd44780, pcf8574)
lcd.backlight_on()
lcd.write_line('Dew Point Fan Contr.', 0)
lcd.write_line('--------------------', 1)
lcd.write_line(f'   Version {VERSION}', 2)
lcd.write_line('lburger@igramul.ch', 3)


with open('secrets.json') as fp:
    secrets = ujson.loads(fp.read())


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


class Measurement(object):
    
    def __init__(self):
        self.indoor = None
        self.outside = None
        
        
class DewPointController(object):
    
    def __init__(self, sensor_indoor, sensor_outside):
        # create a semaphore (A.K.A lock)
        self._lock = _thread.allocate_lock()
        self._time_utc = ''
        self._sensor_indoor = sensor_indoor
        self._sensor_outside = sensor_outside
        self._temp = Measurement()
        self._hum = Measurement()
        self._dew_point = Measurement()
        self._fan = False

    def measure(self, time_utc):
        # acquire the semaphore lock
        self._lock.acquire()
        
        self._time_utc = time_utc
        self._sensor_indoor.measure()
        self._temp.indoor = self._sensor_indoor.temperature()
        self._hum.indoor = self._sensor_indoor.humidity()
        self._dew_point.indoor = taupunkt(self._temp.indoor, self._hum.indoor)
        
        self._sensor_outside.measure()
        self._temp.outside = self._sensor_outside.temperature()
        self._hum.outside = self._sensor_outside.humidity()
        self._dew_point.outside = taupunkt(self._temp.outside, self._hum.outside)
        
        DeltaTP = self._dew_point.indoor - self._dew_point.outside
        if DeltaTP > (SCHALTmin + HYSTERESE):
            self._fan = True
        if DeltaTP < SCHALTmin:
            self._fan = False
        if self._dew_point.indoor < TEMP_indoor_min:
            self._fan = False
        if self._dew_point.outside < TEMP_oudside_min:
            self._fan = False

        # release the semaphore lock
        self._lock.release()

    @property
    def fan(self):
        return self._fan

    @property
    def fan_symbol(self):
        if self._fan:
            return '!'
        else:
            return ' '

    def __str__(self):
        # acquire the semaphore lock
        self._lock.acquire()
        ans = f'{self._time_utc}\nin:  {self._temp.indoor}\337C, {self._hum.indoor}% {self.fan_symbol}\nout: {self._temp.outside}\337C, {self._hum.outside}%\nTi: {self._dew_point.indoor:.01f}\337C To: {self._dew_point.outside:.01f}\337C'
        # release the semaphore lock
        self._lock.release()
        return ans

def connect_to_network(wlan):
    global secrets
    if not wlan.isconnected():
        led_wlan.off()
        print('WLAN connecting...')
        wlan.active(True)
        mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
        print(f'Pico W MAC address: {mac}')        
        wlan.config(pm = 0xa11140) # disable power-save mode for a web server
        wlan.connect(secrets['wlan']['ssid'], secrets['wlan']['password'])
        for i in range(10):
            if wlan.status() not in [network.STAT_CONNECTING, STAT_NO_IP]:
                break
            led_wlan.toggle()
            time.sleep(0.25)
            led_wlan.toggle()
            time.sleep(0.25)
    print('WLAN status:', NetworkStat[wlan.status()])
    if wlan.isconnected():
        led_wlan.on()
        netConfig = wlan.ifconfig()
        print('  - IPv4 addresse', netConfig[0], '/', netConfig[1])
        print('  - standard gateway:', netConfig[2])
        print('  - DNS server:', netConfig[3])
        ntptime.settime()
    else:
        raise(RuntimeError('ERROR: no network connection.'))


def get_time_string(t):
    return '%02i.%02i.%02i %02i:%02i:%02i' % (t[2], t[1], t[0], t[3], t[4], t[5])


async def serve_client(reader, writer):
    
    print('Client connected')
    request_line = await reader.readline()
    print('Request:', request_line)
    # not interested in HTTP request headers, skip them
    while await reader.readline() != b'\r\n':
        pass

    request = str(request_line)
    led_on = request.find('/light/on')
    led_off = request.find('/light/off')
    measure = request.find('/measure')
    print( 'led on = ' + str(led_on))
    print( 'led off = ' + str(led_off))
    print( 'measure = ' + str(measure))

    stateis = ''
    if led_on == 6:
        print('led on')
        led_status.value(1)
        stateis = 'LED is ON'

    if led_off == 6:
        print('led off')
        led_status.value(0)
        stateis = 'LED is OFF'

    if measure == 6:
        print('measure')
        stateis = f'<pre>{str(dew_point_controller)}</pre>'

    response = html % stateis
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()
    print('Client disconnected')


dew_point_controller = DewPointController(sensor_indoor, sensor_outside)

timer_messung = machine.Timer()
 
def messung(timer):
    global dew_point_controller
    global lcd
    utc_time_str = get_time_string(time.localtime())
    print(f'measurement at {utc_time_str}')
    dew_point_controller.measure(utc_time_str)
    fan_relais.value(dew_point_controller.fan)
    for idx, line in enumerate(str(dew_point_controller).splitlines()):
        lcd.write_line(line, idx)

async def main():
    print('Connecting to Network...')
    rp2.country('CH')
    wlan = network.WLAN(network.STA_IF)
    connect_to_network(wlan)

    print('Setting up Webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, '0.0.0.0', 80))

    timer_messung.init(period=5000, mode=machine.Timer.PERIODIC, callback=messung)

    wdt = machine.WDT(timeout=8388)  # enable watchdog with a timeout of 8.3s

    while True:
        wdt.feed()
        led_onboard.on()
        await asyncio.sleep(0.25)
        led_onboard.off()
        await asyncio.sleep(2)


try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()


