import configparser
import os
import time
from pprint import pprint

from icinga2api.client import Client as IcingaClient
from icinga2api.exceptions import Icinga2ApiException
import paho.mqtt.client as mqtt_client


def get_unacknowledged_problems():
    try:
        return icinga.objects.list(
            'Service',
            filters='service.state != ServiceOK && service.downtime_depth == 0.0 '
                    '&& service.acknowledgement == 0.0 && service.state_type == 1 '
                    '&& service.last_reachable == true',
            attrs=['state', 'state_type', 'downtime_depth', 'acknowledgement', 'last_reachable'],
        )
    except Icinga2ApiException as e:
        if e.upstream_error is None or e.upstream_error.get('error', 1) != 404:
            raise
        return []


def on_mqtt_connect(client, userdata, flags, rc):
    print('connected to mqtt server')


config = configparser.ConfigParser()
config.read([os.environ.get('BEACONRELAY_CONFIG', 'beaconrelay.cfg')], encoding='utf-8')


icinga = IcingaClient(
    url=config['icinga']['address'], 
    username=config.get('icinga', 'user', fallback=None),
    password=config.get('icinga', 'password', fallback=None),
    certificate=config.get('icinga', 'certificate', fallback=None),
    key=config.get('icinga', 'key', fallback=None),
    ca_certificate=config.get('icinga', 'ca_certificate', fallback=None),

)
mqtt = mqtt_client.Client()
mqtt.enable_logger()
mqtt.on_connect = on_mqtt_connect
mqtt_tls = config.getboolean('mqtt', 'tls', fallback=False)
if mqtt_tls:
    mqtt.tls_set()
mqtt.username_pw_set(config['mqtt']['user'], config['mqtt']['password'])
print("connecting to mqtt server")
mqtt.connect(config['mqtt']['hostname'], config.getint('mqtt', 'port', fallback=(8883 if mqtt_tls else 1883)), 60)
mqtt.loop_start()
glowcat_mode_topic = 'glowcat/all/cmd/mode'
glowcat_modes = {
    'ok': '4',
    'warning': '1',
    'critical': '6',
}

notfiybeacon_mode_topic = 'notifybeacon/all/cmd/mode'
notfiybeacon_modes = {
    'ok': '4',
    'warning': '9',
    'critical': '9',
}
notfiybeacon_color_topic = 'notifybeacon/all/cmd/color'
notfiybeacon_colors = {
    'ok': '#FF0095',
    'warning': '#FF7300',
    'critical': '#FF0000',
}


last_state = ''
last_send = 0


def sendstate(state):
    global last_send
    global last_state
    if state == last_state and last_send + config.getint('relay', 'resendinterval', fallback=300) > time.time():
        return
    print('sending state %s' % state)
    last_state = state
    last_send = time.time()
    mqtt.publish(glowcat_mode_topic, glowcat_modes[state])
    mqtt.publish(notfiybeacon_color_topic, notfiybeacon_colors[state])
    mqtt.publish(notfiybeacon_mode_topic, notfiybeacon_modes[state])


try:
    while True:
        problems = get_unacknowledged_problems()
        if not problems or len(problems) == 0:
            sendstate('ok')
        else:
            states = {int(service['attrs']['state']) for service in problems}
            if 2 in states:
                sendstate('critical')
            elif 1 in states:
                sendstate('warning')
        time.sleep(config.getint('relay', 'pollinterval', fallback=5))
except KeyboardInterrupt:
    mqtt.disconnect()
    mqtt.loop_stop()
