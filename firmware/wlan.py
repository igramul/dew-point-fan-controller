import time
import rp2
import network
import ntptime
import ubinascii

from networkstat import NetworkStat, STAT_NO_IP


class MicroPythonWlan(object):

    def __init__(self, config, secrets, led, display):
        self._config = config
        self._secrets = secrets
        self._led = led
        self._display = display

        # set Wi-Fi Country
        rp2.country(self._config.get('Wi-Fi Country'))
        network.country(self._config.get('Wi-Fi Country'))

        # set hostname
        network.hostname(self._config.get('Hostname'))

        # default time server
        ntptime.host = '1.europe.pool.ntp.org'

        self._wlan = network.WLAN(network.STA_IF)

    def start(self):
        for i in range(4):
            try:
                self._wlan_connect()
            except RuntimeError as e:
                self._display.lcd.write_line('Network Error %i' % i, 0)
                self._display.lcd.write_line('%s' % e, 1)
                print('WLAN status:', NetworkStat[self._wlan.status()])
                print('Exception: %s' % e)
            if self._wlan.isconnected():
                self._display.lcd.write_line(f'Hostname: {self._config.get("Hostname")}', 2)
                break

    @property
    def is_connected(self):
        return self._wlan.isconnected()

    def _wlan_connect(self):
        if not self._wlan.isconnected():
            self._led.off()
            self._wlan.active(False)
            print('WLAN connecting')
            self._wlan.active(True)
            mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
            print(f'--> MAC address: {mac}')
            if mac == '00:00:00:00:00:00':
                raise RuntimeError('Invalid Mac Address')
            self._wlan.config(pm=0xa11140)  # disable WiFi power-save mode for a web server

            wlans = self._wlan.scan()
            search_wlan = True
            for (ssid, bssid, channel, RSSI, security, hidden) in wlans:
                print(f'Found WLAN with ssid: {ssid}')
                for (my_ssid, my_passwd) in [(_.get('ssid'), _.get('password')) for _ in self._secrets.get('wlans')]:
                    if ssid.decode('utf8') == my_ssid:
                        search_wlan = False
                        print(f'  Match! WLAN credentials found.')
                        self._display.lcd.write_line(f'WLAN: {my_ssid}', 1)
                        self._wlan.connect(my_ssid, my_passwd)
                        break
                if not search_wlan:
                    break

            for _ in range(10):
                wlan_status = self._wlan.status()
                if wlan_status not in [network.STAT_CONNECTING, STAT_NO_IP]:
                    break
                print('--> WLAN status:', NetworkStat[wlan_status])
                self._led.toggle()
                time.sleep(0.25)
                self._led.toggle()
                time.sleep(0.25)

        if self._wlan.isconnected():
            print('WLAN connection ok')
            self._led.on()
            print('WLAN status:', NetworkStat[self._wlan.status()])
            net_config = self._wlan.ifconfig()
            print('  - IPv4 addresse', net_config[0], '/', net_config[1])
            print('  - standard gateway:', net_config[2])
            print('  - DNS server:', net_config[3])
            ntptime.settime()
        else:
            print('WLAN connection failed')
            print('WLAN status:', NetworkStat[self._wlan.status()])
            raise RuntimeError('No WLAN connection')
