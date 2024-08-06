#! /bin/bash

# Dew Point Fan Controller Cron Job Script to WLAN switch fan relay
# alternative to the inline relay module a cron job controls a WLAN
# switch with REST calls

# minimum dew point difference at which the fan switches
switch_min=4.0

# distance from switch-on and switch-off point
hysteresis=1.0

# minimum indoor temperature at which the ventilation is activated
temp_indoor_min=10.0

# minimum outdoor temperature at which the ventilation is activated
temp_outdoor_min=-10.0

PROMETHEUS_QUERY_URL="http://nisset:8080/api/v1/query?query="
SWITCH_URL="http://192.168.10.44/relay"

indoor_temp=$(curl -s "${PROMETHEUS_QUERY_URL}avg_over_time(indoor_temp\[15m\])" | jq --raw-output .data.result[0].value[1])
outdoor_temp=$(curl -s "${PROMETHEUS_QUERY_URL}avg_over_time(outdoor_temp\[15m\])" | jq --raw-output .data.result[0].value[1])
indoor_dew_point=$(curl -s "${PROMETHEUS_QUERY_URL}avg_over_time(indoor_dew_point\[15m\])" | jq --raw-output .data.result[0].value[1])
outdoor_dew_point=$(curl -s "${PROMETHEUS_QUERY_URL}avg_over_time(outdoor_dew_point\[15m\])" | jq --raw-output .data.result[0].value[1])

echo "indoor_temp=${indoor_temp} indoor_dew_point=${indoor_dew_point}"
echo "outdoor_temp=${outdoor_temp} outdoor_dew_point=${outdoor_dew_point}"

dew_point_delta=$(bc -l <<< "${indoor_dew_point}-${outdoor_dew_point}")
echo "dew_point_delta=${dew_point_delta}"

fan_control_state=$(curl -s ${SWITCH_URL} | jq --raw-output .on)
echo current fan state="${fan_control_state}"

fan_control="${fan_control_state}"

if (test $(bc -l <<< "${dew_point_delta} > (${switch_min} + ${hysteresis})") -eq 1); then
  echo "set fan_control=true (dew point threshold passed)"
  fan_control=true
fi

if (test $(bc -l <<< "${dew_point_delta} < ${switch_min}") -eq 1); then
  echo "set fan_control=false (dew point threshold undershoot)"
  fan_control=false
fi

if (test $(bc -l <<< "${indoor_temp} < ${temp_indoor_min}") -eq 1); then
  echo "set fan_control=false (indoor temp is too low for ventilation)"
  fan_control=false
fi

if (test $(bc -l <<< "${outdoor_temp} < ${temp_outdoor_min}") -eq 1); then
  echo "set fan_control=false (outdoor temp is too low for ventilation)"
  fan_control=false
fi

if [ "${fan_control_state}" == "${fan_control}" ]; then
  echo Fan state unchanged
else
  if (${fan_control} eq "true"); then
    echo "switching fan on"
    curl ${SWITCH_URL}?state=1
  else
    echo "switching fan off"
    curl ${SWITCH_URL}?state=0
  fi
fi
