import _thread
import time
import ujson

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
# HELP measurement_count Counter for the measurements taken since startup.
# TYPE measurement_count counter
measurement_count{version="%s"} %i
# HELP fan_control Fan Control (1: on, 0: off)
# TYPE fan_contoll gauge
fan_control %i
# HELP fan_state Fan state (1: on, 0: off)
# TYPE fan_state gauge
fan_state %i"""


class DewPointFanController(object):

    def __init__(self, sensor_indoor, sensor_outdoor, version, measurementdata):
        # create a semaphore (A.K.A lock)
        self._lock = _thread.allocate_lock()
        self._sensor_indoor = sensor_indoor
        self._sensor_outdoor = sensor_outdoor
        self._measurement = measurementdata
        self._fan_status = None
        self._version = version

    def measure(self, time_utc):
        start = time.ticks_us()

        # acquire the semaphore lock
        self._lock.acquire()

        with open('config.json') as fp:
            config = ujson.loads(fp.read()).get('DewPointFanController')

        SWITCHmin = config.get('switch-min').get('value', 5.0)  # minimum dew point difference at which the fan switches
        HYSTERESIS = config.get('hysteresis').get('value', 1.0)  # distance from switch-on and switch-off point
        TEMP_indoor_min = config.get('temp-indoor-min').get('value', 10.0)  # minimum indoor temperature at which the ventilation is activated
        TEMP_outdoor_min = config.get('temp-outdoor-min').get('value', -10.0)  # minimum outdoor temperature at which the ventilation is activated

        self._measurement.set_time_utc(time_utc)

        temp_indoor, hum_indoor = self._sensor_indoor.measure()
        self._measurement.set_indoor_measurement(temp_indoor, hum_indoor)

        temp_outdoor, hum_outdoor = self._sensor_outdoor.measure()
        self._measurement.set_outdoor_measurement(temp_outdoor, hum_outdoor)

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

    def set_fan_status(self, fan_status):
        self._fan_status = fan_status

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
            self._version,
            data['counter'],
            data['fan'],
            self._fan_status)
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
            bool(self._fan_status))
        # release the semaphore lock
        self._lock.release()
        return ans
