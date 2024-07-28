import _thread
import time
import ujson

METRICS = """# HELP outdoor_temp Indoor temperature in degree Celsius.
# TYPE outdoor_temp gauge
outdoor_temp %f
# HELP outdoor_hum Indoor humidity in percent.
# TYPE outdoor_hum gauge
outdoor_hum %f
# HELP outdoor_dew_point Indoor dew point in degree Celsius.
# TYPE outdoor_dew_point gauge
outdoor_dew_point %f
# HELP indoor_temp Indoor temperature in degree Celsius.
# TYPE indoor_temp gauge
indoor_temp %f
# HELP indoor_hum Indoor humidity in percent.
# TYPE indoor_hum gauge
indoor_hum %f
# HELP indoor_dew_point Indoor dew point in degree Celsius.
# TYPE indoor_dew_point gauge
indoor_dew_point %f
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

    def __init__(self,
                 led_fan_control,
                 pin_fan_control,
                 pin_fan_status,
                 sensor_outdoor,
                 sensor_indoor,
                 display,
                 version,
                 measurement_data,
                 config):
        # create a semaphore (A.K.A lock)
        self._lock = _thread.allocate_lock()
        self._led_fan_control = led_fan_control
        self._pin_fan_control = pin_fan_control
        self._pin_fan_status = pin_fan_status
        self._sensor_outdoor = sensor_outdoor
        self._sensor_indoor = sensor_indoor
        self._display = display
        self._measurement = measurement_data
        self._version = version
        self._config = config

        # this value stores the fan state (default off)
        self._fan_control_status = False

    def measure_control(self, time_utc):
        start = time.ticks_us()

        # acquire the semaphore lock
        self._lock.acquire()

        self._measurement.set_time_utc(time_utc)

        temp_outdoor, hum_outdoor = self._sensor_outdoor.measure()
        self._measurement.set_outdoor_measurement(temp_outdoor, hum_outdoor)

        temp_indoor, hum_indoor = self._sensor_indoor.measure()
        self._measurement.set_indoor_measurement(temp_indoor, hum_indoor)

        dew_point_delta = self._measurement.get_dew_point_delta()

        # minimum dew point difference at which the fan switches
        switch_min = self._config.get('switch-min').get('value')

        # distance from switch-on and switch-off point
        hysteresis = self._config.get('hysteresis').get('value')

        # minimum indoor temperature at which the ventilation is activated
        temp_indoor_min = self._config.get('temp-indoor-min').get('value')

        # minimum outdoor temperature at which the ventilation is activated
        temp_outdoor_min = self._config.get('temp-outdoor-min').get('value')

        if dew_point_delta > (switch_min + hysteresis):
            self._fan_control_status = True
        if dew_point_delta < switch_min:
            self._fan_control_status = False
        if self._measurement.indoor_temp < temp_indoor_min:
            self._fan_control_status = False
        if self._measurement.outdoor_temp < temp_outdoor_min:
            self._fan_control_status = False

        # apply fan_control to the output pins for LED and relay control
        self._led_fan_control = self._pin_fan_control = self._fan_control_status

        self._measurement.counter += 1

        # update display
        self._display.lcd.write_line('out: %.1f\337C, %0.1f%%' % (
            self._measurement.outdoor_temp,
            self._measurement.outdoor_hum), 1)

        self._display.lcd.write_line('in:  %0.1f\337C, %0.1f%%' % (
            self._measurement.indoor_temp,
            self._measurement.indoor_hum), 2)

        self._display.lcd.write_line('Ti: %.1f\337C To: %.1f\337C' % (
            self._measurement.indoor_dew_point,
            self._measurement.outdoor_dew_point), 3)

        # release the semaphore lock
        self._lock.release()
        print('Measure: {}, Duration: {} us'.format(time_utc, time.ticks_diff(time.ticks_us(), start)))

    def get_metrics(self):
        # acquire the semaphore lock
        self._lock.acquire()
        data = self._measurement.get_data()
        ans = METRICS % (
            data['outdoor_temp'],
            data['outdoor_hum'],
            data['outdoor_dew_point'],
            data['indoor_temp'],
            data['indoor_hum'],
            data['indoor_dew_point'],
            self._version,
            data['counter'],
            self._fan_control_status,
            self._pin_fan_status.value())
        # release the semaphore lock
        self._lock.release()
        return ans

    def get_measure_html(self):
        # acquire the semaphore lock
        self._lock.acquire()
        data = self._measurement.get_data()
        ans = '%s\nout: %.1f&#176;C, %.1f%%\nin:  %.1f&#176;C, %.1f%%\nTi: %.1f&#176;C To: %.1f&#176;C\nFan Control: %s\nFan State: %s' % (
            data['time_utc'],
            data['outdoor_temp'],
            data['outdoor_hum'],
            data['indoor_temp'],
            data['indoor_hum'],
            data['indoor_dew_point'],
            data['outdoor_dew_point'],
            bool(self._fan_control_status),
            bool(self._pin_fan_status.value()))
        # release the semaphore lock
        self._lock.release()
        return ans
