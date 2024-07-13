import dht


class Sensor(object):

    def __init__(self, machine_pin, offset_temp, offset_hum):
        self._offset_temp = offset_temp
        self._offset_hum = offset_hum
        self._dht22 = dht.DHT22(machine_pin)

    def measure(self):
        self._dht22.measure()
        return self._dht22.temperature(), self._dht22.humidity()
