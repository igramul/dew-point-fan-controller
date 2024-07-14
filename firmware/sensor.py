import ujson
import dht


class SensorDHT22(object):

    def __init__(self, machine_pin, name):
        self._offset_temp = 0.0
        self._offset_hum = 0.0
        with open('calibration.json') as fp:
            calibration_data = ujson.loads(fp.read())
            for data in calibration_data.get('CalibrationData').get('DHT22'):
                if data.get('name') == name:
                    self._offset_temp = data.get('offset-temp')
                    self._offset_hum = data.get('offset-hum')
        self._dht22 = dht.DHT22(machine_pin)

    def measure(self):
        self._dht22.measure()
        return self._dht22.temperature() + self._offset_temp, self._dht22.humidity() + self._offset_hum
