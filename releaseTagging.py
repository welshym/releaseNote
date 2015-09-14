# Release note creation in python
import json
import argparse
import subprocess
import traceback
import sys, os, re, time

class TaggingError(Exception):
	def __init__(self, msg):
		self.msg = msg
		Exception.__init__(self, msg)

config = {}
execPath = ""

def loadConfiguration(argsParsed):
	with open(os.path.join(execPath, 'config.json')) as data_file:    
		global config
		config = json.load(data_file)

	config['tag'] = argsParsed.tag
	config['delete'] = argsParsed.delete
	config['verbose'] = argsParsed.verbose
	if argsParsed.environment != None:
		config['deploymentEnv'] = argsParsed.environment

	if (argsParsed.delete == True) & (argsParsed.tag == None):
		print "Cannot delete tag without tag definition"
		raise TaggingError("Missing git tag to delete")


def taggingArgs():
    parser = argparse.ArgumentParser(description='Python API tagging script. Tags the current repo using an annotated string based on the config.json \"<releaseTag>_<environment>_<timestamp>. \
    												Command line parameter -e <environment> overrides the config environment definition. \
    												Can also delete a tag using the -d <tag> parameter.')
    parser.add_argument('-v', '--verbose', action="store_true", default=False, dest="verbose")
    parser.add_argument('-t', '--tag', action="store", dest="tag")
    parser.add_argument('-e', '--env', action="store", dest="environment")
    parser.add_argument('-d', '--delete', action="store_true", default=False, dest="delete")
    
    return parser

def taggingArgsParse(parser):
    return parser.parse_args()
    
def executeExternalCommand(cmd, path, shell=True):
	if config['verbose'] == True:
		print "Executing: ", cmd

	try:
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=shell, cwd=path)
		commandOutput = p.communicate()
	except:
		raise TaggingError("Failed git command: " + cmd)
	return commandOutput


def tagRelease(tag, path="."):

	createTagMessage = " -m 'Deployment Tag'"
	deleteTagStr = ""
	if config['delete'] == True:
		deleteTagStr = "-d "
		createTagMessage = ""

	tagOut, tagErr = executeExternalCommand('git tag -a ' + deleteTagStr + tag + createTagMessage, path=path)
	if tagErr != "":
		raise TaggingError("Could not tag release, exiting. " + tagErr)

	tagPushOut, tagPushErr = executeExternalCommand('git push origin ' + tag, path=path)
	if tagPushOut != "":
		raise TaggingError("Couldn't push tag, exiting.")


def createTag():
	tag = config['releaseTag'] + "_" + config['deploymentEnv'] + "_" + time.strftime("%d-%m-%Y-%H%M%S", time.gmtime())
	return tag

def main(args):

	if config['tag'] == None:
		tag = createTag()
	else:
		tag = config['tag']

	tagRelease(tag, path=config['gitRepoPathApps'])
	tagRelease(tag, path=config['gitRepoPathLibs'])

if __name__ == '__main__':

	execPath = os.path.dirname(os.path.abspath(__file__))
	argsParsed = taggingArgsParse(taggingArgs())
	loadConfiguration(argsParsed)

	try:
		main(argsParsed)
	except KeyboardInterrupt:
		print "OK, OK, exiting"
	except TaggingError as problem:
		print "Tagging problem: {0}".format(problem)
	except SystemExit:
		print "Finished slightly oddly."
	except:
		print "EXCEPTION: What the hell did you do?"
		if argsParsed.verbose == True:
			traceback.print_exc()
