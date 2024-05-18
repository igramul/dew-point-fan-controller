import network

STAT_NO_IP = 2

NetworkStat = {
    network.STAT_IDLE: 'no connection and no activity',                 #   0
    network.STAT_CONNECTING: 'connecting in progress',                  #   1
    STAT_NO_IP: 'connected to wifi, but no IP address',                 #   2 (WTF! not defined in network)
    network.STAT_GOT_IP: 'connection successful',                       #   3
    network.STAT_CONNECT_FAIL: 'failed due to other problems',          #  -1
    network.STAT_NO_AP_FOUND: 'failed because no access point replied', #  -2
    network.STAT_WRONG_PASSWORD: 'failed due to incorrect password',    #  -3
}
