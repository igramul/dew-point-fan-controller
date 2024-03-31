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

VERSION = '0.2.0'

SWITCHmin = 5.0 #  minimum dew point difference at which the fan switches
HYSTERESIS = 1.0 #  distance from switch-on and switch-off point
TEMP_indoor_min = 10.0 #  minimum indoor temperature at which the ventilation is activated
TEMP_outdoor_min = -10.0 #  minimum outdoor temperature at which the ventilation is activated

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

HTML = """<!DOCTYPE html>
<html>
    <head> <title>Dew Point Fan Controller</title> </head>
    <body> <h1>Dew Point Fan Controller</h1>
        <p>%s</p>
    </body>
</html>
"""

METRICS = """# HELP indoor_temp Indoor temperature in degree Celsius.
# TYPE indoor_temp gauge
indoor_temp %f
# HELP indoor_hum Indoor humidity in percent.
# TYPE indoor_hum gauge
indoor_hum %f
# HELP indoor_dew_point Indoor dew point in degree Celsius.
# TYPE indoor_dew_point gauge
indoor_dew_point %f
# HELP outdoor_temp Indoor temperature in degree Celsius.
# TYPE outdoor_temp gauge
outdoor_temp %f
# HELP outdoor_hum Indoor humidity in percent.
# TYPE outdoor_hum gauge
outdoor_hum %f
# HELP outdoor_dew_point Indoor dew point in degree Celsius.
# TYPE outdoor_dew_point gauge
outdoor_dew_point %f
# HELP measurement_counter Counter for the measurements taken since startup.
# TYPE measurement_counter counter
measurement_counter %i
# HELP fan_control Fan Control (1: on, 0: off)
# TYPE fan_contoll gauge
fan_control %i
# HELP fan_state Fan state (1: on, 0: off)
# TYPE fan_state gauge
fan_state %i"""

led_wlan = machine.Pin(0, machine.Pin.OUT)
led_fan_status = machine.Pin(18, machine.Pin.OUT, value=0)
led_onboard = machine.Pin("LED", machine.Pin.OUT, value=0)

sensor_indoor = dht.DHT22(machine.Pin(6))
sensor_outdoor = dht.DHT22(machine.Pin(7))

fan_relais = machine.Pin(15, machine.Pin.OUT)
fan_status = machine.Pin(13, machine.Pin.IN)

i2c = machine.I2C(1, sda=machine.Pin(2), scl=machine.Pin(3), freq=400000)
pcf8574 = PCF8574(i2c)
hd44780 = HD44780(pcf8574, num_lines=4, num_columns=20)
lcd = LCD(hd44780, pcf8574)

touch_lcd_on = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_DOWN)

timer_lcd_light = machine.Timer()
def iluminate_lcd_background():
    global lcd
    print('LCD backlight on for 60s.')
    lcd.backlight_on()
    timer_lcd_light.init(mode=machine.Timer.ONE_SHOT, period=60000, callback=lambda t: lcd.backlight_off())

touch_lcd_on.irq(lambda irq:iluminate_lcd_background(), machine.Pin.IRQ_RISING)

lcd.write_line('Dew Point Fan Contr.', 0)
lcd.write_line('--------------------', 1)
lcd.write_line(f'Version {VERSION}', 2)
lcd.write_line('lburger@igramul.ch', 3)
iluminate_lcd_background()

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


class MeasurementData(object):
    
    def __init__(self):
        self.indoor_temp = None
        self.indoor_hum = None
        self.indoor_dew_point = None
        self.outdoor_temp = None
        self.outdoor_hum = None
        self.outdoor_dew_point = None
        self.time_utc = ''
        self.fan = False
        self.counter = 0

    def set_indoor_measurement(self, temp, hum):
        self.indoor_temp = temp
        self.indoor_hum = hum
        self.indoor_dew_point = taupunkt(temp, hum)
    
    def set_outdoor_measurement(self, temp, hum):
        self.outdoor_temp = temp
        self.outdoor_hum = hum
        self.outdoor_dew_point = taupunkt(temp, hum)

    def set_time_utc(self, time_utc):
        self.time_utc = time_utc

    def get_data(self):
        return {
            "indoor_temp": self.indoor_temp,
            "indoor_hum": self.indoor_hum,
            "indoor_dew_point" : self.indoor_dew_point,
            "outdoor_temp" : self.outdoor_temp,
            "outdoor_hum" : self.outdoor_hum,
            "outdoor_dew_point" : self.outdoor_dew_point,
            "time_utc" : self.time_utc,
            "fan" : self.fan,
            "counter" : self.counter}

    def get_dew_point_delta(self):
        return self.indoor_dew_point - self.outdoor_dew_point

        
class DewPointFanController(object):
    
    def __init__(self, sensor_indoor, sensor_outdoor):
        # create a semaphore (A.K.A lock)
        self._lock = _thread.allocate_lock()
        self._sensor_indoor = sensor_indoor
        self._sensor_outdoor = sensor_outdoor
        self._measurement = MeasurementData()

    def measure(self, time_utc):
        start = time.ticks_us()

        # acquire the semaphore lock
        self._lock.acquire()
        
        self._measurement.set_time_utc(time_utc)
        
        self._sensor_indoor.measure()
        self._measurement.set_indoor_measurement(self._sensor_indoor.temperature(), self._sensor_indoor.humidity())
        
        self._sensor_outdoor.measure()
        self._measurement.set_outdoor_measurement(self._sensor_outdoor.temperature(), self._sensor_outdoor.humidity())
        
        dew_point_delta = self._measurement.get_dew_point_delta()
        if dew_point_delta > (SWITCHmin + HYSTERESIS):
            self._measurement.fan = True
        if dew_point_delta < SWITCHmin:
            self._measurement.fan = False
        if self._measurement.indoor_temp < TEMP_indoor_min:
            self._measurement.fan = False
        if self._measurement.outdoor_temp < TEMP_outdoor_min:
            self._measurement.fan = False

        self._measurement.counter += 1

        # release the semaphore lock
        self._lock.release()
        print('Measure: {}, Duration: {} us'.format(time_utc, time.ticks_diff(time.ticks_us(), start)))

    @property
    def fan(self):
        return self._measurement.fan

    def get_metrics(self):
        # acquire the semaphore lock
        self._lock.acquire()
        data = self._measurement.get_data()
        ans = METRICS % (
            data['indoor_temp'],
            data['indoor_hum'],
            data['indoor_dew_point'],
            data['outdoor_temp'],
            data['outdoor_hum'],
            data['outdoor_dew_point'],
            data['counter'],
            data['fan'],
            fan_status.value())
        # release the semaphore lock
        self._lock.release()
        return ans

    def get_lcd_string(self):
        # acquire the semaphore lock
        self._lock.acquire()
        data = self._measurement.get_data()
        ans = 'in:  %.1f\337C, %0.1f%%\nout: %0.1f\337C, %0.1f%%\nTi: %.1f\337C To: %.1f\337C' % (
            data['indoor_temp'],
            data['indoor_hum'],
            data['outdoor_temp'],
            data['outdoor_hum'],
            data['indoor_dew_point'],
            data['outdoor_dew_point'])
        # release the semaphore lock
        self._lock.release()
        return ans

    def get_measure_html(self):
        # acquire the semaphore lock
        self._lock.acquire()
        data = self._measurement.get_data()
        ans = '%s\nin:  %.1f&#176;C, %.1f%%\nout: %.1f&#176;C, %.1f%%\nTi: %.1f&#176;C To: %.1f&#176;C\nFan Control: %s\nFan State: %s' % (
            data['time_utc'],
            data['indoor_temp'],
            data['indoor_hum'],
            data['outdoor_temp'],
            data['outdoor_hum'],
            data['indoor_dew_point'],
            data['outdoor_dew_point'],
            data['fan'],
            bool(fan_status.value()))
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
        raise RuntimeError('No WLAN connection')


def get_time_string(t):
    return '%02i.%02i.%02i %02i:%02i:%02i' % (t[2], t[1], t[0], t[3], t[4], t[5])


async def serve_client(reader, writer):
    # Client connected
    request_line = await reader.readline()
    print('Request:', request_line)
    # not interested in HTTP request headers, skip them
    while await reader.readline() != b'\r\n':
        pass

    request = str(request_line)
    metrics = request.find('/metrics')

    if metrics == 6:
        response = dew_point_fan_controller.get_metrics()
    else:
        response = HTML % f'<pre>{dew_point_fan_controller.get_measure_html()}</pre>'

    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()
    # Client disconnected


dew_point_fan_controller = DewPointFanController(sensor_indoor, sensor_outdoor)

timer_messung = machine.Timer()
 
def tick(timer):
    t = time.localtime()
    time_utc =  get_time_string(t)
    lcd.write_line(time_utc, 0)
    if t[5] % 5 == 0:
        messung(time_utc)


def messung(time_utc):
    global dew_point_fan_controller
    global lcd
    dew_point_fan_controller.measure(time_utc)
    fan_relais.value(dew_point_fan_controller.fan)
    led_fan_status.value(dew_point_fan_controller.fan)
    for idx, line in enumerate(dew_point_fan_controller.get_lcd_string().splitlines()):
        lcd.write_line(line, idx+1)


async def main():
    print('Initial dew point measurement...')
    messung(get_time_string(time.localtime()))

    print('Setting up Webserver...')
    asyncio.create_task(asyncio.start_server(serve_client, '0.0.0.0', 80))

    print('Running Dew Point Fan Controller.')
    timer_messung.init(period=1000, mode=machine.Timer.PERIODIC, callback=tick)

    wdt = machine.WDT(timeout=8388)  # enable watchdog with a timeout of 8.3s

    while True:
        wdt.feed()
        led_onboard.on()
        await asyncio.sleep(0.25)
        led_onboard.off()
        await asyncio.sleep(2)


print('Connecting to Network...')
rp2.country('CH')
wlan = network.WLAN(network.STA_IF)
try:
    connect_to_network(wlan)
except Exception as e:
    lcd.write_line('Network Error', 0)
    print('Exception: %s' % e)
    machine.reset()
asyncio.run(main())
