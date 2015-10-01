# Script to create release notes
import sys, os, re

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

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
		repoData[x]['repoChangeList'] = gitmodule.getCommitLog(tagRegEx=globalconfig.config['releaseTag'] + "_" + globalconfig.config['deploymentEnv'] + ".*", path=repoData[x]['repoFileSystemPath'])
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
