import dht


class Sensor(object):

    def __init__(self, machine_pin, config):
        self._offset_temp = config.get('offset-temp')
        self._offset_hum = config.get('offset-hum')
        self._dht22 = dht.DHT22(machine_pin)

    def measure(self):
        self._dht22.measure()
        return self._dht22.temperature() + self._offset_temp, self._dht22.humidity() + self._offset_hum
