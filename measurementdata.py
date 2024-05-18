from taupunkt import taupunkt


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
