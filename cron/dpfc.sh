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

PROMETHEUS_QUERY_URL="http://nisset:32090/api/v1/query?query="
SWITCH_URL="http://192.168.10.44/relay"

# Function to Retrieve a Metric
get_metric() {
  query="$1"
  curl -s "${PROMETHEUS_QUERY_URL}${query}" | jq --raw-output .data.result[0].value[1]
}

# Retrieve Metrics
indoor_temp=$(get_metric "avg_over_time(indoor_temp\[5m\])")
if [ $? -ne 0 ] || [ -z "$indoor_temp" ]; then
  echo "Error retrieving indoor temperature. Script will be aborted."
  exit 1
fi
if [ "${indoor_temp}" == "null" ]; then
  echo "can not calculate new fan state because measurement value is null"
  exit
fi

outdoor_temp=$(get_metric "avg_over_time(outdoor_temp\[5m\])")
indoor_dew_point=$(get_metric "avg_over_time(indoor_dew_point\[5m\])")
outdoor_dew_point=$(get_metric "avg_over_time(outdoor_dew_point\[5m\])")

echo "indoor_temp=${indoor_temp} | indoor_dew_point=${indoor_dew_point}"
echo "outdoor_temp=${outdoor_temp} | outdoor_dew_point=${outdoor_dew_point}"

# Difference of Dew Points
dew_point_delta=$(bc -l <<< "${indoor_dew_point}-${outdoor_dew_point}")
echo "dew_point_delta=${dew_point_delta}"

# Retrieve Current Fan Status
fan_state=$(curl -s ${SWITCH_URL} | jq --raw-output .on)
if [ $? -ne 0 ] || [ -z "$fan_state" ]; then
  echo "Error retrieving fan status. Script will be aborted."
  exit 1
fi
echo fan_state="${fan_state}"

# Determine Desired State (true = Fan On, false = Fan Off)
desired="false"

if [ $(bc -l <<< "${dew_point_delta} > (${switch_min} + ${hysteresis})") -eq 1 ]; then
  echo "Dew point difference exceeds threshold: Fan On"
  desired="true"
fi

if [ $(bc -l <<< "${dew_point_delta} < ${switch_min}") -eq 1 ]; then
  echo "Dew point difference falls below threshold: Fan Off"
  desired="false"
fi

if [ $(bc -l <<< "${indoor_temp} < ${temp_indoor_min}") -eq 1 ]; then
  echo "Indoor temperature too low: Fan Off"
  desired="false"
fi

if [ $(bc -l <<< "${outdoor_temp} < ${temp_outdoor_min}") -eq 1 ]; then
  echo "Outdoor temperature too low: Fan Off"
  desired="false"
fi

# Make changes only if the state changes
if [ "${fan_state}" = "${desired}" ]; then
  echo "Fan status unchanged."
else
  if [ "${desired}" = "true" ]; then
    echo "switching fan on"
    curl "${SWITCH_URL}?state=1"
  else
    echo "switching fan off"
    curl "${SWITCH_URL}?state=0"
  fi
fi
