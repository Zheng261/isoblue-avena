#!/usr/bin/env python3

import requests   # Used to get docker-compose from server
import os         # Used to check for existence of docker-compose files, move, and delete them
import sys        # Used to exit the program
import subprocess # Used to interact with docker-compose
import socket     # Used to get hostname

# Get current docker-compose from the server
hostname = socket.gethostname()
url = 'http://172.16.0.1:8006/' + 'avena-apalis-dev06' + '/docker-compose.yml'
print('Querying server for docker-compose file')
response = requests.get(url)

# Ensure we got a valid response
print('Ensuring we got a valid response')
if response.status_code != 200:
    print('Got a HTTP response code ', response, '. Is there a docker-compose.yml file in the right location?')
    sys.exit()

# Extract the docker-compose
serverdc = response.content.decode('ascii')

# Validate docker-compose
open('./docker-compose.yml.new', 'w').write(serverdc)
print('Validating new docker-compose')
valid = subprocess.run(['docker-compose', '-f', './docker-compose.yml.new', 'config'])
if valid.returncode != 0:
    print('Return code is not valid! Not using new docker-compose')
    os.remove('./docker-compose.yml.new')
    sys.exit()

if not os.path.isfile('./docker-compose.yml'):
    # If no current docker-compose, write it
    print('Writing initial docker-compose from server')
    os.rename('./docker-compose.yml.new', './docker-compose.yml')
else:
    print('docker-compose file found, comparing to server version')

    # Get docker-compose config
    localdc = ''
    with open ("./docker-compose.yml", "r") as openfile:
        localdc = openfile.read()

    # If they are the same, exit
    if localdc == serverdc:
        print('Server and local docker-compose files are the same. Exiting')
        sys.exit()

    # Write the new docker-compose
    print('Server and local docker-compose files are not the same. Replacing docker-compose and restarting all docker containers')
    os.rename('./docker-compose.yml.new', './docker-compose.yml')
    print('New docker-compose written. Stopping and removing all docker containers')

# Get a list of the currently running docker containers
print('Getting current containers')
dockerps = subprocess.run(['docker', 'ps', '-a', '-q'], capture_output=True)

containers = dockerps.stdout.decode('ascii').split('\n')
if containers[-1] == '':
    del containers[-1]
print(containers)

if containers != []:
    # Stop all containers
    print('Stopping and removing current containers')
    subprocess.run(['docker', 'stop'] + containers ) 
    
    # Remove all containers
    print('Removing current containers')
    subprocess.run(['docker', 'rm'] + containers)

# Use docker-compose to bring containers back up with new config
print('Starting containers with docker-compose')
subprocess.run(['docker-compose', '-f', 'docker-compose.yml', 'up', '-d'])