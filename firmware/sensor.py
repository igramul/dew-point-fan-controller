import ujson
import dht


class SensorDHT22(object):

    def __init__(self, machine_pin, location):
        self._name = None
        self._offset_temp = 0.0
        self._offset_hum = 0.0
        with open('calibration.json') as fp:
            calibration_data = ujson.loads(fp.read())
            name = calibration_data.get('SensorConfiguration').get(location).get('SensorName')
            for data in calibration_data.get('CalibrationData').get('SensorsDHT22'):
                if data.get('SensorName') == name:
                    self._name = name
                    self._offset_temp = data.get('offset-temp')
                    self._offset_hum = data.get('offset-hum')
        self._dht22 = dht.DHT22(machine_pin)

    def measure(self):
        self._dht22.measure()
        return self._dht22.temperature() + self._offset_temp, self._dht22.humidity() + self._offset_hum

    @property
    def name(self):
        return self._name

    @property
    def offset_temp(self):
        return self._offset_temp

    @property
    def offset_hum(self):
        return self._offset_hum
