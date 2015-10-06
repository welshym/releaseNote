# Global configuration file
import json
import argparse
import os
import time


config = {}
execPath = ""
executionTime = time.strftime("%d%m%Y-%H%M%S", time.gmtime())

def init():
	global execPath
	execPath = os.path.dirname(os.path.abspath(__file__))

def loadGlobalConfiguration(argsParsed):

	if argsParsed.configFile != None:
		configFile = argsParsed.configFile
	else:
		configFile = os.path.join(execPath, 'config.json')

	with open(configFile) as data_file:    
		global config
		config = json.load(data_file)

	config['verbose'] = argsParsed.verbose
	if argsParsed.environment != None:
		config['deploymentEnv'] = argsParsed.environment
	else:
		config['deploymentEnv'] = "NOENV"

def getArgParser():
    parser = argparse.ArgumentParser(description='Python API release note script.')
    parser.add_argument('-v', '--verbose', action="store_true", default=False, dest="verbose")
    parser.add_argument('-e', '--env', action="store", dest="environment")
    parser.add_argument('-c', '--config', action="store", dest="configFile")
    
    return parser

def parseArgs(parser):
    return parser.parse_args()
