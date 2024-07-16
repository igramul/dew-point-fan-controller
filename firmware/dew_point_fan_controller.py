# Dew Point Fan Controller
# January 2024, by Lukas Burger
import machine
import time
import ujson
import uasyncio as asyncio

from measurementdata import MeasurementData
from dewpointfancontroller import DewPointFanController
from display import Display
from sensor import SensorDHT22
from webserver import WebServer
from wlan import MicroPythonWlan

from version import version

with open('config.json') as fp:
    config = ujson.loads(fp.read())

with open('secrets.json') as fp:
    secrets = ujson.loads(fp.read())

led_onboard = machine.Pin("LED", machine.Pin.OUT, value=0)
led_wlan = machine.Pin(0, machine.Pin.OUT)
led_fan_status = machine.Pin(18, machine.Pin.OUT, value=0)
fan_relay = machine.Pin(15, machine.Pin.OUT)
touch_button = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_DOWN)
fan_status = machine.Pin(13, machine.Pin.IN)

sensor_outdoor = SensorDHT22(machine_pin=machine.Pin(7), name='DHT22-0003')
sensor_indoor = SensorDHT22(machine_pin=machine.Pin(6), name='DHT22-0002')

display = Display(i2c=machine.I2C(1, sda=machine.Pin(2), scl=machine.Pin(3), freq=400000))

measurement_data = MeasurementData()
dew_point_fan_controller = DewPointFanController(
    sensor_outdoor=sensor_outdoor,
    sensor_indoor=sensor_indoor,
    version=version,
    measurement_data=measurement_data,
    config=config.get('DewPointFanController')
)
web_server = WebServer(dew_point_fan_controller=dew_point_fan_controller)
wlan = MicroPythonWlan(config=config, secrets=secrets, led=led_wlan, display=display)


def get_time_string(t):
    (year, month, mday, hour, minute, second, weekday, yearday) = t
    return '%02i.%02i.%02i %02i:%02i:%02i' % (mday, month, year, hour, minute, second)


def tick(timer):
    t = time.localtime()
    time_utc = get_time_string(t)
    if wlan.is_connected:
        display.lcd.write_line(time_utc, 0)
    else:
        display.lcd.write_line('Dew Point Fan Contr.', 0)
    if t[5] % 5 == 0:
        measurement(time_utc)


def measurement(time_utc):
    dew_point_fan_controller.measure(time_utc)
    fan_relay.value(dew_point_fan_controller.fan)
    led_fan_status.value(dew_point_fan_controller.fan)
    dew_point_fan_controller.set_fan_status(fan_status.value())
    for idx, line in enumerate(dew_point_fan_controller.get_lcd_string().splitlines()):
        display.lcd.write_line(line, idx+1)


async def main():
    print('Initial dew point measurement')
    measurement(get_time_string(time.localtime()))

    if wlan.is_connected:
        print('Setting up Webserver')
        asyncio.create_task(asyncio.start_server(web_server.serve_client, '0.0.0.0', 80))

    print('Running Dew Point Fan Controller')
    machine.Timer().init(period=1000, mode=machine.Timer.PERIODIC, callback=tick)

    wdt = machine.WDT(timeout=8388)  # enable watchdog with a timeout of 8.3s

    while True:
        wdt.feed()
        led_onboard.on()
        await asyncio.sleep(0.25)
        led_onboard.off()
        await asyncio.sleep(2)

display.lcd.write_line('Dew Point Fan Contr.', 0)
display.lcd.write_line('--------------------', 1)
display.lcd.write_line(f'Version {version}', 2)
display.lcd.write_line('lburger@igramul.ch', 3)
display.illuminate()

touch_button.irq(lambda irq: display.illuminate(), machine.Pin.IRQ_RISING)

wlan.start()

asyncio.run(main())
