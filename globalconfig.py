import json
import argparse
import os

config = {}
execPath = ""

def init():
	global execPath
	execPath = os.path.dirname(os.path.abspath(__file__))

def loadGlobalConfiguration(argsParsed):
	with open(os.path.join(execPath, 'config.json')) as data_file:    
		global config
		config = json.load(data_file)

	config['verbose'] = argsParsed.verbose
	if argsParsed.environment != None:
		config['deploymentEnv'] = argsParsed.environment

def getArgParser():
    parser = argparse.ArgumentParser(description='Python API release note script.')
    parser.add_argument('-v', '--verbose', action="store_true", default=False, dest="verbose")
    parser.add_argument('-e', '--env', action="store", dest="environment")
    
    return parser

def parseArgs(parser):
    return parser.parse_args()
