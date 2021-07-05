#!/usr/bin/python3
# --------------------------------
# OTHERS
import argparse
import logging
from time import sleep
from pycomfoconnect import *

# --------------------------------
# MQTT
import paho.mqtt.client as mqtt
from mqtt_strings import sensor_name


inputaction = []

parser = argparse.ArgumentParser()
parser.add_argument('--ip', help='ip address of the bridge')
args = parser.parse_args()

## Configuration #######################################################################################################

# --------------------------------
# MQTT
mqttBroker = "192.168.2.55"
mqttBrokerUser = "loxberry"
mqttBrokerPW = "ED358WN1ZrAOIYWK"
client = mqtt.Client("ComfoConnect", clean_session=True)

mqttTopic = "ComfoConnect/"
# --------------------------------
pin = 0
local_name = 'Computer'
local_uuid = bytes.fromhex('00000000000000000000000000000005')


def bridge_discovery():
    ## Bridge discovery ################################################################################################

    # Method 1: Use discovery to initialise Bridge
    bridges = Bridge.discover(timeout=8)
    if bridges:
        bridge = bridges[0]
        print("Bridge found with discover")
    else:
        bridge = None

    # Method 2: Use direct discovery to initialise Bridge
    bridges = Bridge.discover(args.ip)
    #bridges = Bridge.discover("192.168.2.194")
    if bridges:
        bridge = bridges[0]
        print("Bridge found with IP set")
    else:
        bridge = None

    # Method 3: Setup bridge manually
    # bridge = Bridge(args.ip, bytes.fromhex('0000000000251010800170b3d54264b4'))

    if bridge is None:
        print("No bridge found!")
        exit(1)

    print("Bridge found: %s (%s)" % (bridge.uuid.hex(), bridge.host))
    bridge.debug = True

    return bridge


def callback_sensor(var, value):
    ## Callback sensors ###############################################

    #print("%s = %s" % (var, value))
    #print("%s = %i\n" % (mqttTopic + sensor_name[var], int(value, base=16)) )
    #print(value)
    print("to MQTT %s = %s\n" % (mqttTopic + sensor_name[var], value))
    # local_name.client
    # print("---------")
    (rc, mid) = client.publish(mqttTopic + sensor_name[var], value)
    # print("rc: " + str(rc) + "   mid: " + str(mid))

def on_publish(client, userdata, mid):
    # print("mid: "+str(mid))
    pass

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))

#def on_message(client, userdata, msg):
    # comfoconnect.cmd_rmi_request(CMD_FAN_MODE_LOW)  # Set fan speed to 1
    #print("on_message: " , end='')
    #print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))

def on_connect(mqtt_client, obj, flags, rc):
    print("Now Connected rc: " + str(rc))
    client.subscribe(mqttTopic + "#", qos=2)
    #client.message_callback_add(mqttTopic +"FAN_MODE", on_message_FAN_MODE)
    client.message_callback_add(mqttTopic + "FAN_MODE_AWAY", on_message_CMD)
    client.message_callback_add(mqttTopic + "FAN_MODE_LOW", on_message_CMD)
    client.message_callback_add(mqttTopic + "FAN_MODE_MEDIUM", on_message_CMD)
    client.message_callback_add(mqttTopic + "FAN_MODE_HIGH", on_message_CMD)
    client.message_callback_add(mqttTopic + "MODE_AUTO", on_message_CMD)
    client.message_callback_add(mqttTopic + "MODE_MANUAL", on_message_CMD)
    client.message_callback_add(mqttTopic + "VENTMODE_SUPPLY", on_message_CMD)
    client.message_callback_add(mqttTopic + "VENTMODE_BALANCE", on_message_CMD)
    client.message_callback_add(mqttTopic + "TEMPPROF_NORMAL", on_message_CMD)
    client.message_callback_add(mqttTopic + "TEMPPROF_COOL", on_message_CMD)
    client.message_callback_add(mqttTopic + "TEMPPROF_WARM", on_message_CMD)
    client.message_callback_add(mqttTopic + "BYPASS_ON", on_message_CMD)
    client.message_callback_add(mqttTopic + "BYPASS_OFF", on_message_CMD)
    client.message_callback_add(mqttTopic + "BYPASS_AUTO", on_message_CMD)
    client.message_callback_add(mqttTopic + "SENSOR_TEMP_OFF", on_message_CMD)
    client.message_callback_add(mqttTopic + "SENSOR_TEMP_AUTO", on_message_CMD)
    client.message_callback_add(mqttTopic + "SENSOR_TEMP_ON", on_message_CMD)
    client.message_callback_add(mqttTopic + "SENSOR_HUMC_OFF", on_message_CMD)
    client.message_callback_add(mqttTopic + "SENSOR_HUMC_AUTO", on_message_CMD)
    client.message_callback_add(mqttTopic + "SENSOR_HUMC_ON", on_message_CMD)
    client.message_callback_add(mqttTopic + "SENSOR_HUMP_OFF", on_message_CMD)
    client.message_callback_add(mqttTopic + "SENSOR_HUMP_AUTO", on_message_CMD)
    client.message_callback_add(mqttTopic + "SENSOR_HUMP_ON", on_message_CMD)

def on_disconnect(client, userdata, rc):
    print("Now Disconnected rc: " + str(rc))

def on_message_CMD(client, userdata, msg):
    global inputaction  # make action list accessible here
    # print(msg.topic+" "+str(msg.qos)+" "+ msg.payload)
    print("from MQTT %s = %s\n" % (msg.topic , msg.payload))
    inputaction.append([msg.topic, msg.qos, msg.payload])  # add command to action list
    # print(list(inputaction))

#def on_message_FAN_MODE(client, userdata, msg):
    # print(msg.topic+" "+str(msg.qos)+" "+ msg.payload)

def on_log(client, userdata, level, buf):
    print (buf)
# --------------------------------------------------------------
# --------------------------------------------------------------
def main():

    connected_flag = 0
    connected_flag_old = 0

    # --------------------------------
    # MQTT
    # --------------------------------
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    client.enable_logger(logger)

    # client.on_publish = on_publish
    client.on_subscribe = on_subscribe
    #client.on_message = on_message
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.username_pw_set( mqttBrokerUser, mqttBrokerPW)
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    # Discover the bridge
    bridge = bridge_discovery()

    ## Setup a Comfoconnect session  ###################################################################################

    comfoconnect = ComfoConnect(bridge, local_uuid, local_name, pin)
    comfoconnect.callback_sensor = callback_sensor

    try:
        # Connect to the bridge
        # comfoconnect.connect(False)  # Don't disconnect existing clients.
        comfoconnect.connect(True)  # Disconnect existing clients.

    except Exception as e:
        print('ERROR: %s' % e)
        exit(1)


    ## Register sensors ################################################################################################

    comfoconnect.register_sensor(SENSOR_FAN_NEXT_CHANGE)  # General: Countdown until next fan speed change
    comfoconnect.register_sensor(SENSOR_FAN_SPEED_MODE)  # Fans: Fan speed setting
    #no
    comfoconnect.register_sensor(SENSOR_FAN_SUPPLY_DUTY)  # Fans: Supply fan duty
    comfoconnect.register_sensor(SENSOR_FAN_EXHAUST_DUTY)  # Fans: Exhaust fan duty
    comfoconnect.register_sensor(SENSOR_FAN_SUPPLY_FLOW)  # Fans: Supply fan flow
    comfoconnect.register_sensor(SENSOR_FAN_EXHAUST_FLOW)  # Fans: Exhaust fan flow
    comfoconnect.register_sensor(SENSOR_FAN_SUPPLY_SPEED)  # Fans: Supply fan speed
    comfoconnect.register_sensor(SENSOR_FAN_EXHAUST_SPEED)  # Fans: Exhaust fan speed
    comfoconnect.register_sensor(SENSOR_POWER_CURRENT)  # Power Consumption: Current Ventilation
    comfoconnect.register_sensor(SENSOR_POWER_TOTAL_YEAR)  # Power Consumption: Total year-to-date
    comfoconnect.register_sensor(SENSOR_POWER_TOTAL)  # Power Consumption: Total from start

    comfoconnect.register_sensor(SENSOR_DAYS_TO_REPLACE_FILTER)  # Days left before filters must be replaced
    #no
    comfoconnect.register_sensor(SENSOR_AVOIDED_HEATING_CURRENT)  # Avoided Heating: Avoided actual
    comfoconnect.register_sensor(SENSOR_AVOIDED_HEATING_TOTAL_YEAR)  # Avoided Heating: Avoided year-to-date
    comfoconnect.register_sensor(SENSOR_AVOIDED_HEATING_TOTAL)  # Avoided Heating: Avoided total

    comfoconnect.register_sensor(SENSOR_TEMPERATURE_SUPPLY)  # Temperature & Humidity: Supply Air (temperature)
    comfoconnect.register_sensor(SENSOR_TEMPERATURE_EXTRACT)  # Temperature & Humidity: Extract Air (temperature)
    comfoconnect.register_sensor(SENSOR_TEMPERATURE_EXHAUST)  # Temperature & Humidity: Exhaust Air (temperature)
    comfoconnect.register_sensor(SENSOR_TEMPERATURE_OUTDOOR)  # Temperature & Humidity: Outdoor Air (temperature)
    comfoconnect.register_sensor(SENSOR_HUMIDITY_SUPPLY)  # Temperature & Humidity: Supply Air (temperature)
    comfoconnect.register_sensor(SENSOR_HUMIDITY_EXTRACT)  # Temperature & Humidity: Extract Air (temperature)
    comfoconnect.register_sensor(SENSOR_HUMIDITY_EXHAUST)  # Temperature & Humidity: Exhaust Air (temperature)
    comfoconnect.register_sensor(SENSOR_HUMIDITY_OUTDOOR)  # Temperature & Humidity: Outdoor Air (temperature)
    comfoconnect.register_sensor(SENSOR_BYPASS_STATE)  # Bypass state
    comfoconnect.register_sensor(SENSOR_OPERATING_MODE)  # Operating mode
    comfoconnect.register_sensor(SENSOR_OPERATING_MODE_BIS)  # Operating mode (bis)

    # comfoconnect.register_sensor(16) # 1
    # comfoconnect.register_sensor(33) # 1
    # comfoconnect.register_sensor(37) # 0
    # comfoconnect.register_sensor(53) # -1
    # comfoconnect.register_sensor(66) # 0
    # comfoconnect.register_sensor(67) # 0
    # comfoconnect.register_sensor(70) # 0
    # comfoconnect.register_sensor(71) # 0
    # comfoconnect.register_sensor(82) # ffffffff
    # comfoconnect.register_sensor(85) # ffffffff
    # comfoconnect.register_sensor(86) # ffffffff
    # comfoconnect.register_sensor(87) # ffffffff
    # comfoconnect.register_sensor(144) # 0
    # comfoconnect.register_sensor(145) # 0
    # comfoconnect.register_sensor(146) # 0
    # comfoconnect.register_sensor(176) # 0
    # comfoconnect.register_sensor(208) # 0
    # comfoconnect.register_sensor(210) # 0
    # comfoconnect.register_sensor(211) # 0
    # comfoconnect.register_sensor(212) # 228
    # comfoconnect.register_sensor(216) # 0
    # comfoconnect.register_sensor(217) # 28
    # comfoconnect.register_sensor(218) # 28
    # comfoconnect.register_sensor(219) # 0
    # comfoconnect.register_sensor(224) # 3
    # comfoconnect.register_sensor(225) # 1
    # comfoconnect.register_sensor(226) # 100
    # comfoconnect.register_sensor(228) # 0
    # comfoconnect.register_sensor(321) # 15
    # comfoconnect.register_sensor(325) # 1
    # comfoconnect.register_sensor(337) #
    # comfoconnect.register_sensor(338) # 00000000
    # comfoconnect.register_sensor(341) # 00000000
    # comfoconnect.register_sensor(369) # 0
    # comfoconnect.register_sensor(370) # 0
    # comfoconnect.register_sensor(371) # 0
    # comfoconnect.register_sensor(372) # 0
    # comfoconnect.register_sensor(384) # 0
    # comfoconnect.register_sensor(386) # 0
    # comfoconnect.register_sensor(400) # 0
    # comfoconnect.register_sensor(401) # 0
    # comfoconnect.register_sensor(402) # 0
    # comfoconnect.register_sensor(416) # -400
    # comfoconnect.register_sensor(417) # 100
    # comfoconnect.register_sensor(418) # 0
    # comfoconnect.register_sensor(419) # 0

    ## Execute functions ###############################################################################################

    # ListRegisteredApps
    #for app in comfoconnect.cmd_list_registered_apps():
    #    print('%s: %s' % (app['uuid'].hex(), app['devicename']))

    # DeregisterApp
    # comfoconnect.cmd_deregister_app(bytes.fromhex('00000000000000000000000000000001'))

    # VersionRequest
    version = comfoconnect.cmd_version_request()
    print("Version: " + str(version))

    # TimeRequest
    timeinfo = comfoconnect.cmd_time_request()
    print("Timeinfo: " + str(timeinfo))

    ## Example for Executing functions #################################################################################

    # comfoconnect.cmd_rmi_request(CMD_FAN_MODE_AWAY)  # Go to away mode
    # comfoconnect.cmd_rmi_request(CMD_FAN_MODE_LOW)  # Set fan speed to 1
    # comfoconnect.cmd_rmi_request(CMD_FAN_MODE_MEDIUM)  # Set fan speed to 2
    # comfoconnect.cmd_rmi_request(CMD_FAN_MODE_HIGH)  # Set fan speed to 3

    ## Example interaction #############################################################################################

    try:
        print('Running... Stop with CTRL+C')
        while True:
            connected_flag_old = connected_flag             # update old flag state
            connected_flag = comfoconnect.is_connected()    # update flag status
            if connected_flag != connected_flag_old:        # check if flag has changed
                if connected_flag:                          # yes, it has
                    print('Connected to ComfoConnect ...')
                    # Connect to the broker
                    try:
                        client.connect(mqttBroker, 1883)
                    except Exception as e:
                        # print('ERROR: %s' % e)
                        pass
                    client.loop_start()

                else:
                    print('Not connected to ComfoConnect ...')
                    client.loop_stop()
                    client.disconnect()

            if connected_flag:
                # ---------------------------------------------------------------------------------------
                # Process action list, do one command each itteration until list is empty
                if inputaction:                 # anything to do ?
                    topic = inputaction[0][0]   # yes, extract topic from oldest list item
                    qos = inputaction[0][1]     # extract qos value from oldest list item
                    value = inputaction[0][2]   # extract payload value oldest from list item
                    inputaction.pop(0)          # remove oldest list item from list
                    # now execute matching command
                    if topic == mqttTopic + "FAN_MODE_AWAY":
                        comfoconnect.cmd_rmi_request(CMD_FAN_MODE_AWAY)  # Go to away mode
                    elif topic == mqttTopic + "FAN_MODE_LOW":
                        comfoconnect.cmd_rmi_request(CMD_FAN_MODE_LOW)  #
                    elif topic == mqttTopic + "FAN_MODE_MEDIUM":
                        comfoconnect.cmd_rmi_request(CMD_FAN_MODE_MEDIUM)  #
                    elif topic == mqttTopic + "FAN_MODE_HIGH":
                        comfoconnect.cmd_rmi_request(CMD_FAN_MODE_HIGH)  #
                    elif topic == mqttTopic + "MODE_AUTO":
                        comfoconnect.cmd_rmi_request(CMD_MODE_AUTO)  #
                    elif topic == mqttTopic + "MODE_MANUAL":
                        comfoconnect.cmd_rmi_request(CMD_MODE_MANUAL)  #
                    elif topic == mqttTopic + "VENTMODE_SUPPLY":
                        comfoconnect.cmd_rmi_request(CMD_VENTMODE_SUPPLY)  #
                    elif topic == mqttTopic + "VENTMODE_BALANCE":
                        comfoconnect.cmd_rmi_request(CMD_VENTMODE_BALANCE)  #
                    elif topic == mqttTopic + "TEMPPROF_NORMAL":
                        comfoconnect.cmd_rmi_request(CMD_TEMPPROF_NORMAL)  #
                    elif topic == mqttTopic + "TEMPPROF_COOL":
                        comfoconnect.cmd_rmi_request(CMD_TEMPPROF_COOL)  #
                    elif topic == mqttTopic + "TEMPPROF_WARM":
                        comfoconnect.cmd_rmi_request(CMD_TEMPPROF_WARM)  #
                    elif topic == mqttTopic + "BYPASS_ON":
                        comfoconnect.cmd_rmi_request(CMD_BYPASS_ON)  #
                    elif topic == mqttTopic + "BYPASS_OFF":
                        comfoconnect.cmd_rmi_request(CMD_BYPASS_OFF)  #
                    elif topic == mqttTopic + "BYPASS_AUTO":
                        comfoconnect.cmd_rmi_request(CMD_BYPASS_AUTO)  #
                    elif topic == mqttTopic + "SENSOR_TEMP_OFF":
                        comfoconnect.cmd_rmi_request(CMD_SENSOR_TEMP_OFF)  #
                    elif topic == mqttTopic + "SENSOR_TEMP_AUTO":
                        comfoconnect.cmd_rmi_request(CMD_SENSOR_TEMP_AUTO)  #
                    elif topic == mqttTopic + "SENSOR_TEMP_ON":
                        comfoconnect.cmd_rmi_request(CMD_SENSOR_TEMP_ON)  #
                    elif topic == mqttTopic + "SENSOR_HUMC_OFF":
                        comfoconnect.cmd_rmi_request(CMD_SENSOR_HUMC_OFF)  #
                    elif topic == mqttTopic + "SENSOR_HUMC_AUTO":
                        comfoconnect.cmd_rmi_request(CMD_SENSOR_HUMC_AUTO)  #
                    elif topic == mqttTopic + "SENSOR_HUMC_ON":
                        comfoconnect.cmd_rmi_request(CMD_SENSOR_HUMC_ON)  #
                    elif topic == mqttTopic + "SENSOR_HUMP_OFF":
                        comfoconnect.cmd_rmi_request(CMD_SENSOR_HUMP_OFF)  #
                    elif topic == mqttTopic + "SENSOR_HUMP_AUTO":
                        comfoconnect.cmd_rmi_request(CMD_SENSOR_HUMP_AUTO)  #
                    elif topic == mqttTopic + "SENSOR_HUMP_ON":
                        comfoconnect.cmd_rmi_request(CMD_SENSOR_HUMP_ON)  #

            sleep(1)


# ---------------------------------------------------------------------------------------
    except KeyboardInterrupt:
        pass

    ## Closing the session #############################################################################################
    print('Disconnecting...')
    comfoconnect.disconnect()


if __name__ == "__main__":
    main()
