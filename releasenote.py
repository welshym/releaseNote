# Script to create release notes
import sys, os, re
import argparse
import pystache
import traceback
import globalconfig
import gitmodule


def loadLocalConfiguration(argsParsed):
	globalconfig.config['buildNumber'] = argsParsed.buildNumber


def generateReleaseNoteHTML(repoData, buildNo):
	renderer = pystache.Renderer()
	summary = 'This is the release note for build ' + str(buildNo) + '.'
	furtherInfo = 'For more information contact ' + globalconfig.config['contactPoint'] + '.'

	renderer.search_dirs.append(globalconfig.execPath)
	releaseNoteHTML = renderer.render_path(os.path.join(globalconfig.execPath, 'releaseNoteLayout.mustache'), {
						'summary': summary,
						'repos': repoData,
						'furtherInfo': furtherInfo})

	releaseNoteFile = open("releasenote-"+ globalconfig.config['deploymentEnv'] + "-" + globalconfig.executionTime + ".html", 'w')
	releaseNoteFile.write(releaseNoteHTML)
	releaseNoteFile.close()


def main(args):


	deploymentTag = gitmodule.createTag()

	repoData = []

	for x in range(0, len(globalconfig.config['gitRepos'])):
		if os.path.exists(globalconfig.config['gitRepos'][x]['repoFileSystemPath']) == False:
			continue
		
		globalconfig.config['gitRepos'][x]['repoLatestStageTag'] = gitmodule.getLatestStageTag(path=globalconfig.config['gitRepos'][x]['repoFileSystemPath'])
		gitmodule.checkoutStage(stageTag=globalconfig.config['gitRepos'][x]['repoLatestStageTag'], path=globalconfig.config['gitRepos'][x]['repoFileSystemPath'])
		gitmodule.tagRelease(deploymentTag, path=globalconfig.config['gitRepos'][x]['repoFileSystemPath'])
		globalconfig.config['gitRepos'][x]['repoChangeList'] = gitmodule.getCommitLog(tagRegEx=globalconfig.config['releaseTag'] + "_" + globalconfig.config['deploymentEnv'] + ".*", path=globalconfig.config['gitRepos'][x]['repoFileSystemPath'])
		globalconfig.config['gitRepos'][x]['repoPath'] = gitmodule.getGitPath(globalconfig.config['gitRepos'][x]['repoFileSystemPath'])
		repoData.append(globalconfig.config['gitRepos'][x])

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
