#!/usr/bin/env python

# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Python sample for connecting to Google Cloud IoT Core via MQTT, using JWT.
This example connects to Google Cloud IoT Core via MQTT, using a JWT for device
authentication. After connecting, by default the device publishes 100 messages
to the device's MQTT topic at a rate of one per second, and then exits.
Before you run the sample, you must follow the instructions in the README
for this sample.
"""

import argparse
import datetime
import os
import time
import json

import jwt
import paho.mqtt.client as mqtt

import random

def create_jwt(project_id, key_file, algorithm):
    """Creates a JWT (https://jwt.io) to establish an MQTT connection.
        Args:
         project_id: The cloud project ID this device belongs to
         key_file: A path to a file containing either an RSA256 or
                 ES256 private key.
         algorithm: The encryption algorithm to use. Either 'RS256' or 'ES256'
        Returns:
            on MQTT generated from the given project_id and private key, which
            expires in 20 minutes. After 20 minutes, your client will be
            disconnected, and a new JWT will have to be generated.
        Raises:
            ValueError: If the key_file does not contain a known key.
        """

    token = {
            # The time that the token was issued at
            'iat': datetime.datetime.utcnow(),
            # The time the token expires.
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            # The audience field should always be set to the GCP project id.
            'aud': project_id
    }

    # Read the private key file.
    with open(key_file, 'r') as f:
        key = f.read()

    print('Creating JWT using {} from private key file {}'.format(
            algorithm, key_file))

    return jwt.encode(token, key, algorithm=algorithm)


def error_str(rc):
    """Convert a Paho error to a human readable string."""
    return '{}: {}'.format(rc, mqtt.error_string(rc))


def on_connect(unused_client, unused_userdata, unused_flags, rc):
    """Callback for when a device connects."""
    print('on_connect', error_str(rc))


def on_disconnect(unused_client, unused_userdata, rc):
    """Paho callback for when a device disconnects."""
    print('on_disconnect', error_str(rc))


def on_publish(unused_client, unused_userdata, unused_mid):
    """Paho callback when a message is sent to the broker."""
    print('on_publish')

# shingo
def on_subscribe(unused_client, unused_userdata, unused_mid,
                     granted_qos):
    """Callback when the device receives a SUBACK from the MQTT bridge."""
    print('Subscribed: ', granted_qos)
    if granted_qos[0] == 128:
        print('Subscription failed.')
# shingo
def on_message(unused_client, unused_userdata, message):
    """Callback when the device receives a message on a subscription."""
    payload = message.payload.decode('utf-8')
    print('Received message \'{}\' on topic \'{}\' with Qos {}'.format(
        payload, message.topic, str(message.qos)))

def get_state():
    power = True
    version = 20201019
    return {'power':power, 'version':version}

def parse_command_line_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=(
            'Example Google Cloud IoT Core MQTT device connection code.'))
    parser.add_argument(
            '--project_id',
            default=os.environ.get('GOOGLE_CLOUD_PROJECT'),
            help='GCP cloud project name')
    parser.add_argument(
            '--registry_id', required=True, help='Cloud IoT Core registry id')
    parser.add_argument(
            '--device_id', required=True, help='Cloud IoT Core device id')
    parser.add_argument(
            '--key_file',
            required=True, help='Path to private key file.')
    parser.add_argument(
            '--algorithm',
            choices=('RS256', 'ES256'),
            required=True,
            help='Which encryption algorithm to use to generate the JWT.')
    parser.add_argument(
            '--cloud_region', default='us-central1', help='GCP cloud region')
    parser.add_argument(
            '--ca_certs',
            default='roots.pem',
            help=('CA root from https://pki.google.com/roots.pem'))
    parser.add_argument(
            '--num_messages',
            type=int,
            default=100,
            help='Number of messages to publish.')
    parser.add_argument(
            '--message_type',
            choices=('event', 'state'),
            default='event',
            required=True,
            help=('Indicates whether the message to be published is a '
                  'telemetry event or a device state message.'))
    parser.add_argument(
            '--mqtt_bridge_hostname',
            default='mqtt.googleapis.com',
            help='MQTT bridge hostname.')
    parser.add_argument(
            '--mqtt_bridge_port',
            default=8883,
            type=int,
            help='MQTT bridge port.')

    return parser.parse_args()


def get_dht_sensor():
    import Adafruit_DHT
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, '4')
    print('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperature, humidity))
    try:
        temperature_f = '{0:0.1f}'.format(temperature)
        humidity_f = '{0:0.1f}'.format(humidity)
    except:
        pass

    return dict(humidity=humidity_f, temperature=temperature_f)

def main():
    args = parse_command_line_args()

    print("Connecting to {} as {}".format(args.registry_id, args.device_id))

    # Create our MQTT client. The client_id is a unique string that identifies
    # this device. For Google Cloud IoT Core, it must be in the format below.
    client = mqtt.Client(
            client_id=('projects/{}/locations/{}/registries/{}/devices/{}'
                       .format(
                               args.project_id,
                               args.cloud_region,
                               args.registry_id,
                               args.device_id)))



    # With Google Cloud IoT Core, the username field is ignored, and the
    # password field is used to transmit a JWT to authorize the device.
    client.username_pw_set(
            username='unused',
            password=create_jwt(
                    args.project_id, args.key_file, args.algorithm))

    # Enable SSL/TLS support.
    client.tls_set(ca_certs=args.ca_certs)

    # Register message callbacks. https://eclipse.org/paho/clients/python/docs/
    # describes additional callbacks that Paho supports. In this example, the
    # callbacks just print to standard out.
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe
    client.on_message = on_message

    # Connect to the Google MQTT bridge.
    client.connect(args.mqtt_bridge_hostname, args.mqtt_bridge_port)

    # Start the network loop.
    client.loop_start()

    # Publish to the events or state topic based on the flag.
    sub_topic = 'events' if args.message_type == 'event' else 'state'

    mqtt_topic = '/devices/{}/{}'.format(args.device_id, sub_topic)

    random.seed(args.device_id)  # A given device ID will always generate
                                 # the same random data

    simulated_temp = 10 + random.random() * 20

    if random.random() > 0.5:
        temperature_trend = +1     # temps will slowly rise
    else:
        temperature_trend = -1     # temps will slowly fall

    # shingo starting
    # ref: https://cloud.google.com/iot/docs/how-tos/config/configuring-devices#iot-core-mqtt-get-config-python
    # This is the topic that the device will receive configuration updates on.
    mqtt_config_topic = '/devices/{}/config'.format(args.device_id)
    # Subscribe to the config topic.
    client.subscribe(mqtt_config_topic, qos=1)
    # The topic that the device will receive commands on.
    mqtt_command_topic = '/devices/{}/commands/#'.format(args.device_id)
    # Subscribe to the commands topic, QoS 1 enables message acknowledgement.
    print('Subscribing to {}'.format(mqtt_command_topic))
    client.subscribe(mqtt_command_topic, qos=0)

    state_topic = '/devices/{}/state'.format(args.device_id)
    # shingo finished

    # Publish num_messages mesages to the MQTT bridge once per second.
    i = 0
    while True:
    # for i in range(1, args.num_messages + 1):

        simulated_temp = simulated_temp + temperature_trend * random.normalvariate(0.01,0.005)
        # simulated_temp = get_dht_sensor()['temperature']
        payload = {"timestamp": int(time.time()), "device": args.device_id, "temperature": simulated_temp}
        payload['geo1'] = '{ "type": "Point", "coordinates": [-111,20] }'
        payload = get_payload()
        print('Publishing message: \'{}\''.format(payload))
        jsonpayload =  json.dumps(payload,indent=4)
        # Publish "jsonpayload" to the MQTT topic. qos=1 means at least once
        # delivery. Cloud IoT Core also supports qos=0 for at most once
        # delivery.
        r = client.publish(mqtt_topic, jsonpayload, qos=1)
        if not r.is_published:
            print("Error while publishing")
        print(r.rc)

        # Send events every second. State should not be updated as often
        time.sleep(5 if args.message_type == 'event' else 10)

        # shingo
        i += 1
        if (i + 1) % 5 == 0:
            statepayload = json.dumps(get_state())
            client.publish(state_topic, statepayload, qos=1)

            client.username_pw_set(
                username='unused',
                password=create_jwt(
                    args.project_id, args.key_file, args.algorithm))

        # shingo

    # End the network loop and finish.
    client.loop_stop()
    print('Finished.')


def get_payload():
    d = {}
    import datetime
    import random as rd
    d['datetime'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    d["module"] = os.environ.get("HOST", __name__)
    d["channel0"] = round(rd.uniform(0.1,0.2), 2) 
    d["channel1"] = round(rd.uniform(0.1,0.9), 2)
    d["channel2"] = round(rd.uniform(1.1,2.9), 6)
    d["channel3"] = round(rd.uniform(0.2,2.9), 1)
    d["channel4"] = round(rd.uniform(0.2,2.9), 2)
    d["channel5"] = round(rd.uniform(0.2,5.9), 3)
    d["channel6"] = round(rd.uniform(0.2,3.9), 1)
    d["channel7"] = round(rd.uniform(0.2,2.9), 6)
    d["channel8"] = round(rd.uniform(0.2,3.9), 1)
    d["channel9"] = rd.randint(0,9)
    return d

def get_schema():
    data  = "datetime:STRING,"
    data += "module:STRING,"
    data += "channel0:FLOAT,"
    data += "channel1:FLOAT,"
    data += "channel2:FLOAT,"
    data += "channel3:FLOAT,"
    data += "channel4:FLOAT,"
    data += "channel5:FLOAT,"
    data += "channel6:FLOAT,"
    data += "channel7:FLOAT,"
    data += "channel8:FLOAT,"
    data += "channel9:INTEGER"
    return data

if __name__ == '__main__':
    main()

