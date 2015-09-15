# Release note creation in python
import argparse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import pystache
import subprocess
import traceback
import sys, os, re

class ReleaseNoteError(Exception):
	def __init__(self, msg):
		self.msg = msg
		Exception.__init__(self, msg)

config = {}
execPath = ""

#<a href="mailto:webmaster@example.com">Jon Doe</a>

def loadConfiguration(argsParsed):
	with open(os.path.join(execPath, 'config.json')) as data_file:    
		global config
		config = json.load(data_file)

	if (config['emailEnabled'] == True) & (argsParsed.emailPassword == None):
		print ("Configuration requires email address.")
		exit(-1)

	config['emailPassword'] = argsParsed.emailPassword 
	config['verbose'] = argsParsed.verbose 
	if argsParsed.environment != None:
		config['deploymentEnv'] = argsParsed.environment 
	config['buildNumber'] = argsParsed.buildNumber


def releaseNoteArgs():
    parser = argparse.ArgumentParser(description='Python API release note script. Determines the change list for the repo the script is executed from between two tags (if no earlier tag its the start of time). \
    												Based on \"DEP_<environment>\" where the environment is defined in the config.json or passed on the command line. \
    												The build number can also be passed in for reference.')
    parser.add_argument('-v', '--verbose', action="store_true", default=False, dest="verbose")
    parser.add_argument('-b', '--build', action="store", dest="buildNumber")
    parser.add_argument('-e', '--env', action="store", dest="environment")
    parser.add_argument('-p', '--password', action="store", dest="emailPassword")
    
    return parser

def releaseNoteArgsParse(parser):
    return parser.parse_args()


def releaseNoteEmail (fileAttachment=None, message=None):
	msg = MIMEMultipart('alternative')
	msg['Subject'] = 'Release Note'
	msg['From'] = config['emailFrom']
	body = ""
	if message != None:
		body = message

	if fileAttachment != None:
		f = file(fileAttachment)
		body += f.read()

	content = MIMEText(body, 'html')
	msg.attach(content)

	session = smtplib.SMTP(config['SMTP_SERVER'], config['SMTP_PORT'])
	session.ehlo()
	session.starttls()
	session.ehlo

	try:
		session.login(config['emailFrom'], config['emailPassword'])
	except:
		raise ReleaseNoteError("Cannot login into the SMTP server.")

	session.sendmail(config['emailFrom'], config['emailTo'].split(','), msg.as_string())
	session.quit()
    
def executeExternalCommand(cmd, path, shell=True):
	if config['verbose'] == True:
		print ("Executing: ", cmd)

	try:
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=shell, cwd=path)
		stdOut, stdErr = p.communicate()
	except:
		raise TaggingError("Failed git command: " + cmd)
	return stdOut.decode('utf-8'), stdErr.decode('utf-8')


def findMatchedTags(tagList, tagRegEx):
	matchedTags = []

	p = re.compile("refs/tags/(" + tagRegEx + ")")
	for tag in tagList:
		match = p.match(tag)
		if match:
			matchedTags.append(match.group(1))

	return matchedTags


def getCommitLog(path="."):

	tagListOut, tagListErr = executeExternalCommand('git for-each-ref --sort=taggerdate --format "%(refname)"', path=path)
	if tagListOut == "":
		raise ReleaseNoteError("No tags matching criteria found, exiting.")

	tagsMatch = findMatchedTags(tagList=tagListOut.splitlines(), tagRegEx=config['releaseTag'] + "_" + config['deploymentEnv'] + ".*")

	if len(tagsMatch) == 0:
		return ""

	later = tagsMatch.pop()
	try:
		earlier = tagsMatch.pop() + "..."
	except:
		earlier = ""

	if config['verbose'] == True:
		print ("Earlier Tag: ", earlier)
		print ("Later Tag: ", later)

	logCmd = ['git', 'log', earlier + later, '--pretty=format:{\"author\":\"%cn\",\"message\":\"%s\",\"timestamp\":\"%ci\",\"hash\":\"%H\"}']
	logOut, tagErr = executeExternalCommand(logCmd, path=path, shell=False)

	if (logOut == "") & (config['verbose'] == True):
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

def getGitPath(path='.'):
	pathOut, pathErr = executeExternalCommand('git config --get remote.origin.url', path=path)
	return pathOut.rstrip("\n")


def generateReleaseNoteHTML(repoData, buildNo):
	renderer = pystache.Renderer()
	summary = 'This is the release note for build ' + str(buildNo) + '.'
	furtherInfo = 'For more information contact ' + config['contactPoint'] + '.'

	renderer.search_dirs.append(execPath)
	releaseNoteHTML = renderer.render_path(os.path.join(execPath, 'releaseNoteLayout.mustache'), {
						'summary': summary, 
						'repos': repoData, 
						'furtherInfo': furtherInfo})

	releaseNoteFile = open("releaseNote.html", 'w')
	releaseNoteFile.write(releaseNoteHTML)
	releaseNoteFile.close()


def main(args):

	repoData = config['gitRepos']

	for x in range(0, len(repoData)):
		repoData[x]['repoChangeList'] = getCommitLog(path=repoData[x]['repoFileSystemPath'])
		repoData[x]['repoPath'] = getGitPath(repoData[x]['repoFileSystemPath']) 

	generateReleaseNoteHTML(repoData=repoData, buildNo=config['buildNumber'])
	if config['emailEnabled'] == True:
		releaseNoteEmail(config['emailPassword'], fileAttachment="releaseNote.html")


if __name__ == '__main__':
	execPath = os.path.dirname(os.path.abspath(__file__))
	argsParsed = releaseNoteArgsParse(releaseNoteArgs())
	loadConfiguration(argsParsed)

	try:
		main(argsParsed)
	except KeyboardInterrupt:
		print ("OK, OK, exiting")
	except ReleaseNoteError as problem:
		print ("Release note problem: {0}".format(problem))
	except SystemExit:
		print ("Finished slightly oddly.")
	except:
		print ("EXCEPTION: What the hell did you do?")
		if argsParsed.verbose == True:
			traceback.print_exc()




# Notes
#
# git log v0.2...HEAD --pretty=format:"{\"author\":\"%cn\",\"message\":\"%s\",\"timestamp\":\"%ci\",\"hash\":\"%H\"}" > gitlog.json
# git describe --tags --match "v[0-9]*" --abbrev=0
