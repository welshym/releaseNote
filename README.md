# releaseNote

This repo contains two key scripts:

    1. releasetagging.py
    2. releasenote.py

#Releasetagging

This script tags the repos defined by the config.json "gitRepos" element. It creates a tag based on whether the environment is staging defined by "-s" argument or a release tag. Both tags use the tag definitions within config.json and append a timestamp.

To delete a specific tag execute with -d -t <tag definition>

Typical use would be wen deploying to the Nexus staging area. An example tag would be: NEXUS_DEPLOY_17-09-2015-130503

#Releasenote

This script creates an html release note based on the changes between two tags. The first tag used is either the begining of time (initial commit) or the tag used the last time this script was run. The second tag is placed on the codeline at the point the code was deployed to the staging area (relies on the deployment to the staging area having run the releasetagging.py to tag the deployment) effectively retagging the original deployment tag with a new tag.

Typical use would be when deploying code to a test environment. An example tag would be: ENV_DEPLOY_PIE1234_17-09-2015-132154

