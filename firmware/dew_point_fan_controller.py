# Dew Point Fan Controller
# January 2024, by Lukas Burger

import machine
import rp2
import dht
import time
import ubinascii
import network
import ntptime
import ujson
import uasyncio as asyncio
import sys


sys.path.append('micropython_i2c_lcd')

from pcf8574 import PCF8574
from hd44780 import HD44780
from lcd import LCD

from networkstat import NetworkStat, STAT_NO_IP
import measurementdata
import dewpointfancontroller
import webserver

from version import version

ntptime.host = '1.europe.pool.ntp.org'  # default time server

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
    print('LCD backlight on for 60s.')
    lcd.backlight_on()
    timer_lcd_light.init(mode=machine.Timer.ONE_SHOT, period=60000, callback=lambda t: lcd.backlight_off())


touch_lcd_on.irq(lambda irq:iluminate_lcd_background(), machine.Pin.IRQ_RISING)

lcd.write_line('Dew Point Fan Contr.', 0)
lcd.write_line('--------------------', 1)
lcd.write_line(f'Version {version}', 2)
lcd.write_line('lburger@igramul.ch', 3)
iluminate_lcd_background()

with open('secrets.json') as fp:
    secrets = ujson.loads(fp.read())


def wlan_connect():
    global secrets
    if not wlan.isconnected():
        led_wlan.off()
        wlan.active(False)
        print('WLAN connecting')
        wlan.active(True)
        mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
        print(f'--> MAC address: {mac}')
        if mac == '00:00:00:00:00:00':
            raise RuntimeError('Invalid Mac Address')
        wlan.config(pm = 0xa11140) # disable WiFi power-save mode for a web server

        wlans = wlan.scan()
        search_wlan = True
        for (ssid, bssid, channel, RSSI, security, hidden) in wlans:
            print(f'Found WLAN with ssid: {ssid}')
            for (my_ssid, my_passwd) in [(_.get('ssid'), _.get('password')) for _ in secrets.get('wlans')]:
                if ssid.decode('utf8') == my_ssid:
                    search_wlan = False
                    print(f'  Match! WLAN credentials found.')
                    lcd.write_line(f'WiFi {my_ssid}', 1)
                    wlan.connect(my_ssid, my_passwd)
                    break
            if not search_wlan:
                break

        for i in range(10):
            wlan_status = wlan.status()
            if wlan_status not in [network.STAT_CONNECTING, STAT_NO_IP]:
                break
            print('--> WLAN status:', NetworkStat[wlan_status])
            led_wlan.toggle()
            time.sleep(0.25)
            led_wlan.toggle()
            time.sleep(0.25)

    if wlan.isconnected():
        print('WLAN connection ok')
        led_wlan.on()
        print('WLAN status:', NetworkStat[wlan.status()])
        netConfig = wlan.ifconfig()
        print('  - IPv4 addresse', netConfig[0], '/', netConfig[1])
        print('  - standard gateway:', netConfig[2])
        print('  - DNS server:', netConfig[3])
        ntptime.settime()
    else:
        print('WLAN connection failed')
        print('WLAN status:', NetworkStat[wlan_status])
        raise RuntimeError('No WLAN connection')


def get_time_string(t):
    return '%02i.%02i.%02i %02i:%02i:%02i' % (t[2], t[1], t[0], t[3], t[4], t[5])


def tick(timer):
    t = time.localtime()
    time_utc = get_time_string(t)
    if wlan.isconnected():
        lcd.write_line(time_utc, 0)
    else:
        lcd.write_line('Dew Point Fan Contr.', 0)
    if t[5] % 5 == 0:
        messung(time_utc)


def messung(time_utc):
    dew_point_fan_controller.measure(time_utc)
    fan_relais.value(dew_point_fan_controller.fan)
    led_fan_status.value(dew_point_fan_controller.fan)
    dew_point_fan_controller.set_fan_status(fan_status.value())
    for idx, line in enumerate(dew_point_fan_controller.get_lcd_string().splitlines()):
        lcd.write_line(line, idx+1)


measurement_data = measurementdata.MeasurementData()

dew_point_fan_controller = dewpointfancontroller.DewPointFanController(sensor_indoor, sensor_outdoor, version, measurement_data)

web_server = webserver.WebServer(dew_point_fan_controller=dew_point_fan_controller)


async def main():
    print('Initial dew point measurement')
    messung(get_time_string(time.localtime()))

    if wlan.isconnected():
        print('Setting up Webserver')
        asyncio.create_task(asyncio.start_server(web_server.serve_client, '0.0.0.0', 80))

    print('Running Dew Point Fan Controller')
    timer_messung.init(period=1000, mode=machine.Timer.PERIODIC, callback=tick)

    wdt = machine.WDT(timeout=8388)  # enable watchdog with a timeout of 8.3s

    while True:
        wdt.feed()
        led_onboard.on()
        await asyncio.sleep(0.25)
        led_onboard.off()
        await asyncio.sleep(2)

timer_messung = machine.Timer()

# set Wi-Fi Country
rp2.country('CH')
network.country('CH')

# set hostname
network.hostname("dwpt")

wlan = network.WLAN(network.STA_IF)
for i in range(4):
    try:
        wlan_connect()
    except RuntimeError as e:
        lcd.write_line('Network Error %i' % i, 0)
        lcd.write_line('%s' % e, 1)
        print('WLAN status:', NetworkStat[wlan.status()])
        print('Exception: %s' % e)
    if wlan.isconnected():
        break

asyncio.run(main())
