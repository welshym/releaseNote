import argparse
import json
import traceback
import sys, os, re, time
import globalconfig
import gitmodule

reportStartDate = ""
reportEndDate = ""
additions = 0
deletions = 0


def loadLocalConfiguration(argsParsed):
	global reportEndDate
	global reportStartDate

	reportStartDate = argsParsed.reportStartDate

	reportEndDate = time.strftime("%Y-%m-%d", time.gmtime())

	repoData = globalconfig.config['gitRepos']


def processLinesOfChange(logResponseOut):
	global additions
	global deletions

	additionRE = re.compile(".*([\d]).*insertion")
	deletionRE = re.compile(".*([\d]).*deletion")
	for line in logResponseOut.splitlines():
		additionMatch = additionRE.match(line)
		deletionMatch = deletionRE.match(line)
		if additionMatch:
			additions += int(additionMatch.group(1))

		if deletionMatch:
			deletions += int(deletionMatch.group(1))


def main(args):

	for x in range(0, len(globalconfig.config['gitRepos'])):
		logResponseOut, logResponseErr = gitmodule.executeExternalCommand(cmd='git log --after="'+ reportStartDate + '" --before="' + reportEndDate + '" --pretty=tformat: --shortstat --oneline', path=globalconfig.config['gitRepos'][x]['repoFileSystemPath'])

		if logResponseOut != "":
			processLinesOfChange(logResponseOut)

	print "Additions: ", additions
	print "Deletions: ", deletions


if __name__ == '__main__':
	globalconfig.init()

	parser = globalconfig.getArgParser()
	parser.add_argument('-d', '--date', action="store", dest="reportStartDate", required=True)
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

