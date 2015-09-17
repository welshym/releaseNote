# Git library functionality to support release notes
import globalconfig
import time
import subprocess
import re
import json


class ExecutionError(Exception):
	def __init__(self, msg):
		self.msg = msg
		Exception.__init__(self, msg)


def createTag():
	if globalconfig.config.has_key('staging') and globalconfig.config['staging']:
		tag = globalconfig.config['stageTag'] + "_" + time.strftime("%d-%m-%Y-%H%M%S", time.gmtime())
	else:
		tag = globalconfig.config['releaseTag'] + "_" + globalconfig.config['deploymentEnv'] + "_" + time.strftime("%d-%m-%Y-%H%M%S", time.gmtime())

	return tag

def tagRelease(tag, path="."):

	createTagMessage = " -m 'Deployment Tag'"

	if ((globalconfig.config.has_key('delete') == True) and (globalconfig.config['delete'] == True)):
		tagOut, tagErr = executeExternalCommand('git tag -d ' + tag, path=path)
		deleteRefs = ":refs/tags/"
	else:
		tagOut, tagErr = executeExternalCommand('git tag -a ' + tag + ' -m "Deployment Tag"', path=path)
		deleteRefs = ""

	if tagErr != "":
		raise ExecutionError("Could not tag release, exiting. " + tagErr)

	tagPushOut, tagPushErr = executeExternalCommand('git push origin ' + deleteRefs + tag, path=path)
	if tagPushOut != "":
		raise ExecutionError("Couldn't push tag, exiting.")


def executeExternalCommand(cmd, path=".", shell=True):
	if globalconfig.config['verbose'] == True:
		print "Executing: ", cmd

	try:
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=shell, cwd=path)
		commandOutput = p.communicate()
	except:
		raise ExecutionError("Failed git command: " + cmd)
	return commandOutput


def checkoutStage(stageTag, path="."):
	tagOut, tagErr = executeExternalCommand('git checkout ' + stageTag , path=path)
	if tagErr.startswith("error:") == True:
		raise ExecutionError("Couldn't checkout tag release, exiting. " + tagErr)

def getLatestStageTag(path="."):
	tagListOut, tagListErr = executeExternalCommand(cmd='git for-each-ref --sort=taggerdate --format "%(refname)"', path=path)
	if tagListOut == "":
		raise ExecutionError("No tags matching criteria found, exiting.")

	tagsMatch = findMatchedTags(tagList=tagListOut.splitlines(), tagRegEx=globalconfig.config['stageTag'] + ".*")

	print tagsMatch

	if len(tagsMatch) == 0:
		return ""
	else:
		return tagsMatch.pop()


def findMatchedTags(tagList, tagRegEx):
	matchedTags = []

	p = re.compile("refs/tags/(" + tagRegEx + ")")
	for tag in tagList:
		match = p.match(tag)
		if match:
			matchedTags.append(match.group(1))

	return matchedTags


def getGitPath(path='.'):
	pathOut, pathErr = executeExternalCommand('git config --get remote.origin.url', path=path)
	return pathOut.rstrip("\n")


def getCommitLog(tagRegEx, path="."):

	tagListOut, tagListErr = executeExternalCommand(cmd='git for-each-ref --sort=taggerdate --format "%(refname)"', path=path)
	if tagListOut == "":
		raise ExecutionError("No tags matching criteria found, exiting.")

	tagsMatch = findMatchedTags(tagList=tagListOut.splitlines(), tagRegEx=tagRegEx)

	if len(tagsMatch) == 0:
		return ""

	later = tagsMatch.pop()
	try:
		earlier = tagsMatch.pop() + "..."
	except:
		earlier = ""

	if globalconfig.config['verbose'] == True:
		print ("Earlier Tag: ", earlier)
		print ("Later Tag: ", later)

	logCmd = ['git', 'log', earlier + later, '--pretty=format:{\"author\":\"%cn\",\"message\":\"%s\",\"timestamp\":\"%ci\",\"hash\":\"%H\"}']
	logOut, tagErr = executeExternalCommand(logCmd, path=path, shell=False)

	if (logOut == "") & (globalconfig.config['verbose'] == True):
		print ("No changes in this deployment.")

	commitJsonString = "["
	firstElement = True
	for line in logOut.splitlines():
		if firstElement == True:
			firstElement = False
		else:
			commitJsonString += ","
		commitJsonString = commitJsonString + line
	commitJsonString += "]"

	commitLog = json.loads(commitJsonString)

	return commitLog