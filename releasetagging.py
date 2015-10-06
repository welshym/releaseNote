# Script to tag git repos
import sys, os, re, time
import argparse
import subprocess
import traceback
import gitmodule
import globalconfig

def loadLocalConfiguration(argsParsed):
    globalconfig.config['tag'] = argsParsed.tag
    globalconfig.config['delete'] = argsParsed.delete
    globalconfig.config['staging'] = argsParsed.staging

    if (argsParsed.delete == True) & (argsParsed.tag == None):
        print ("Cannot delete tag without tag definition")
        raise gitmodule.ExecutionError("Missing git tag to delete")

def main(args):

    if globalconfig.config['tag'] == None:
        tag = gitmodule.createTag()
    else:
        tag = globalconfig.config['tag']

    for x in range(0, len(globalconfig.config['gitRepos'])):
        if os.path.exists(globalconfig.config['gitRepos'][x]['repoFileSystemPath']) == False:
            continue
        gitmodule.tagRelease(tag, path=globalconfig.config['gitRepos'][x]['repoFileSystemPath'])


if __name__ == '__main__':
    globalconfig.init()

    parser = globalconfig.getArgParser()
    parser.add_argument('-t', '--tag', action="store", dest="tag")
    parser.add_argument('-d', '--delete', action="store_true", default=False, dest="delete")
    parser.add_argument('-s', '--staging', action="store_true", default=False, dest="staging")
    argsParsed = globalconfig.parseArgs(parser)

    globalconfig.loadGlobalConfiguration(argsParsed)
    loadLocalConfiguration(argsParsed)

    try:
        main(argsParsed)
    except KeyboardInterrupt:
        print ("OK, OK, exiting")
    except gitmodule.ExecutionError as problem:
        print ("Tagging problem: {0}".format(problem))
    except SystemExit:
        print ("Finished slightly oddly.")
    except:
        print ("EXCEPTION: What the hell did you do?")
        if argsParsed.verbose == True:
            traceback.print_exc()
