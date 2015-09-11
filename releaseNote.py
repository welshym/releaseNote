# Release note creation in python
import argparse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import pystache
import subprocess
import traceback
import sys, os

class ReleaseNoteError(Exception):
	def __init__(self, msg):
		self.msg = msg
		Exception.__init__(self, msg)

config = {}
execPath = ""

#<a href="mailto:webmaster@example.com">Jon Doe</a>

def loadConfiguration():
	with open(os.path.join(execPath, 'config.json')) as data_file:    
		global config
		config = json.load(data_file)

def releaseNoteArgs():
    parser = argparse.ArgumentParser(description='Python API release note script.')
    parser.add_argument('-v', '--verbose', action="store_true", default=False, dest="verbose")
    parser.add_argument('-b', '--build', action="store", dest="buildNumber")
    parser.add_argument('-s', '--start', action="store", dest="startTag")
    parser.add_argument('-e', '--end', action="store", dest="endTag")
    parser.add_argument('-p', '--password', action="store", dest="emailPassword")
    
    return parser

def releaseNoteArgsParse(parser):
    return parser.parse_args()


def releaseNoteEmail (emailPassword, fileAttachment=None, message=None):
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
		session.login(config['emailFrom'], emailPassword)
	except:
		raise ReleaseNoteError("Cannot login into the SMTP server.")

	session.sendmail(config['emailFrom'], config['emailTo'].split(','), msg.as_string())
	session.quit()
    
def executeExternalCommand(cmd, path, shell=True):
	try:
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, shell=shell, cwd=path)
		commandOutput = p.communicate()
	except:
		raise ReleaseNoteError("Failed git command: " + cmd)
	return commandOutput

def getCommitLog(startTag=None, endTag=None, path="."):

	if startTag == None:
		startTag = str(config["defaultStartTag"])

	if endTag == None:
		endTag = str(config["defaultEndTag"])

	tagOut, tagErr = executeExternalCommand('git describe --tags --match ' + startTag + ' --abbrev=0', path=path)
	if tagOut == "":
		raise ReleaseNoteError("No tags matching criteria found, exiting.")

	logCmd = ['git', 'log', tagOut.rstrip("\n") + '...' + endTag, '--pretty=format:{\"author\":\"%cn\",\"message\":\"%s\",\"timestamp\":\"%ci\",\"hash\":\"%H\"}']
	logOut, tagErr = executeExternalCommand(logCmd, path=path, shell=False)
	if logOut == "":
		raise ReleaseNoteError("No git log data available.")

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

def getGitPath(path):
	pathOut, pathErr = executeExternalCommand('git config --get remote.origin.url', path=path)
	return pathOut


def generateReleaseNoteHTML(commitLogApps, commitLogLibs, buildNo):
	renderer = pystache.Renderer()
	summary = 'This is the release note for build ' + str(buildNo) + '.'
	furtherInfo = 'For more information contact ' + config['contactPoint'] + '.'

	renderer.search_dirs.append(execPath)
	releaseNoteHTML = renderer.render_path(os.path.join(execPath, 'releaseNoteLayout.mustache'), {
						'summary': summary, 
						'commitsApps': commitLogApps, 
						'commitsLibs': commitLogLibs, 
						'repoPathApps': getGitPath(config['gitRepoPathApps']), 
						'repoPathLibs': getGitPath(config['gitRepoPathLibs']), 
						'furtherInfo': furtherInfo})

	releaseNoteFile = open("releaseNote.html", 'w')
	releaseNoteFile.write(releaseNoteHTML)
	releaseNoteFile.close()


def main(args):

	commitLogApps = getCommitLog(startTag=argsParsed.startTag, endTag=argsParsed.endTag, path=config['gitRepoPathApps'])
	commitLogLibs = getCommitLog(startTag=argsParsed.startTag, endTag=argsParsed.endTag, path=config['gitRepoPathLibs'])

	generateReleaseNoteHTML(commitLogApps, commitLogLibs, buildNo=argsParsed.buildNumber)
	if config['emailEnabled'] == True:
		releaseNoteEmail(emailPassword=argsParsed.emailPassword, fileAttachment="releaseNote.html")


if __name__ == '__main__':

	argsParsed = releaseNoteArgsParse(releaseNoteArgs())
	execPath = os.path.dirname(os.path.abspath(__file__))
	loadConfiguration()

	if (config['emailEnabled'] == True) & (argsParsed.emailPassword == None):
		print "Configuration requires email address."
		exit(-1)

	try:
		main(argsParsed)
	except KeyboardInterrupt:
		print "OK, OK, exiting"
	except ReleaseNoteError as problem:
		print "Release note problem: {0}".format(problem)
	except SystemExit:
		print "Finished slightly oddly."
	except:
		print "EXCEPTION: What the hell did you do?"
		if argsParsed.verbose == True:
			traceback.print_exc()




# Notes
#
# git log v0.2...HEAD --pretty=format:"{\"author\":\"%cn\",\"message\":\"%s\",\"timestamp\":\"%ci\",\"hash\":\"%H\"}" > gitlog.json
# git describe --tags --match "v[0-9]*" --abbrev=0
