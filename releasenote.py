# Release note creation in python
import argparse
import json
import pystache
import traceback
import sys, os, re
import globalconfig
import gitmodule

def loadLocalConfiguration(argsParsed):
	globalconfig.config['buildNumber'] = argsParsed.buildNumber

def getCommitLog(path="."):

	tagListOut, tagListErr = gitmodule.executeExternalCommand(cmd='git for-each-ref --sort=taggerdate --format "%(refname)"', path=path)
	if tagListOut == "":
		raise ExecutionError("No tags matching criteria found, exiting.")

	tagsMatch = gitmodule.findMatchedTags(tagList=tagListOut.splitlines(), tagRegEx=globalconfig.config['releaseTag'] + "_" + globalconfig.config['deploymentEnv'] + ".*")

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
	logOut, tagErr = gitmodule.executeExternalCommand(logCmd, path=path, shell=False)

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



def generateReleaseNoteHTML(repoData, buildNo):
	renderer = pystache.Renderer()
	summary = 'This is the release note for build ' + str(buildNo) + '.'
	furtherInfo = 'For more information contact ' + globalconfig.config['contactPoint'] + '.'

	renderer.search_dirs.append(globalconfig.execPath)
	releaseNoteHTML = renderer.render_path(os.path.join(globalconfig.execPath, 'releaseNoteLayout.mustache'), {
						'summary': summary, 
						'repos': repoData, 
						'furtherInfo': furtherInfo})

	releaseNoteFile = open("releaseNote.html", 'w')
	releaseNoteFile.write(releaseNoteHTML)
	releaseNoteFile.close()


def main(args):

	repoData = globalconfig.config['gitRepos']

	deploymentTag = gitmodule.createTag()

	for x in range(0, len(repoData)):
		repoData[x]['repoLatestStageTag'] = gitmodule.getLatestStageTag(path=repoData[x]['repoFileSystemPath'])
		gitmodule.checkoutStage(stageTag=repoData[x]['repoLatestStageTag'], path=repoData[x]['repoFileSystemPath'])
		gitmodule.tagRelease(deploymentTag, path=repoData[x]['repoFileSystemPath'])
		repoData[x]['repoChangeList'] = getCommitLog(path=repoData[x]['repoFileSystemPath'])
		repoData[x]['repoPath'] = gitmodule.getGitPath(repoData[x]['repoFileSystemPath']) 

	generateReleaseNoteHTML(repoData=repoData, buildNo=globalconfig.config['buildNumber'])
	if globalconfig.config['emailEnabled'] == True:
		releaseNoteEmail(globalconfig.config['emailPassword'], fileAttachment="releaseNote.html")


if __name__ == '__main__':

	globalconfig.init()

	parser = globalconfig.getArgParser()
	parser.add_argument('-b', '--build', action="store", dest="buildNumber")
	argsParsed = globalconfig.parseArgs(parser)

	globalconfig.loadGlobalConfiguration(argsParsed)
	loadLocalConfiguration(argsParsed)

	try:
		main(argsParsed)
	except KeyboardInterrupt:
		print ("OK, OK, exiting")
	except gitmodule.ExecutionError as problem:
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
