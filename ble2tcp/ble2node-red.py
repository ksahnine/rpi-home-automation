#! /usr/bin/python
# -*- coding: utf-8 -*-

__author__  = "Kadda SAHNINE"
__contact__ = "ksahnine@gmail.com"
__license__ = 'GPL v3'

import bluetooth
import getopt
import logging
import os
import socket
import sys
import time
import yaml
import json

def usage():
    """
    Display usage
    """
    sys.stderr.write( "Usage: ble2node-red.py [-c <config-file> | --config=<config-file>\n"+
          "                   [-H <tcp-host>   | --tcp-host=<tcp-host>\n"+
          "                   [-p <tcp-port>   | --tcp-port=<tcp-port>\n")

def notify(tcpHost, tcpPort, device, logger):
    """
    Notify TCP node (Node Red)
    """
    logger.log(logging.DEBUG, "Connecting to Node-Red TCP listener [%s:%d]" % (tcpHost, tcpPort))
    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    data = json.dumps(device)
    try:
        # Connect to TCP server and send data
        sock.connect((tcpHost, tcpPort))
        sock.send(data)
    except socket.error:
        logger.log(logging.ERROR, "Unable to connect to %s:%s. Please check your Node RED flow." % (tcpHost, tcpPort))
    finally:
       sock.close()
    logger.log(logging.DEBUG, "Sent data: [%s]" % (data))

def main(argv):
    """
    Main
    """
    configFile = "devices.yml"
    tcpHost = os.getenv('TCP_HOST', 'localhost')
    tcpPort = int(os.getenv('TCP_PORT', '8888'))
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)

    # Checks the optional parameters
    try:
        opts, args = getopt.getopt(argv, "hH:p:c:",
                     ["help","tcp-host=","tcp-port=","config"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-H", "--tcp-host" ):
            mqttHost = a
        if o in ("-p", "--tcp-port" ):
            mqttPort = int(a)
        if o in ("-c", "--config" ):
            configFile = a

    # Loads the configuration file
    if os.path.isfile(configFile):
        with open(configFile, 'r') as f:
            conf = yaml.load(f)
    else:
        print "ERROR. The config file [%s] does not exist !" % configFile
        usage()
        sys.exit(3)
    
    # Configure the logger
    handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    )
    logger.setLevel(conf['logging_level'])
    logger.addHandler(handler)

    delay = int(conf["delay"])
    timeout = int(conf["timeout"])
    
    print "*** BLE to Node-Red TCP gateway ***"
    print " - Devices config file : %s" % configFile
    print " - TCP host           : %s" % tcpHost
    print " - TCP port           : %d" % tcpPort
    
    while True:
        for device in conf["devices"]:
            result = bluetooth.lookup_name(device['addr'], timeout=timeout)
            isNear = (result != None)
            if ('isNear' not in device) or (device['isNear'] != isNear):
                device['isNear'] = isNear
       	        logger.log(logging.DEBUG, "%s: in" % device)
                notify(tcpHost, tcpPort, device, logger)
    
        time.sleep(delay)

if __name__ == "__main__":
    main(sys.argv[1:])
