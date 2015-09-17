#!/bin/bash

if [ "$#" != 0 ]; then
  localTag=$1
else
  dateVar=$(date +%Y-%m-%d-%H%M%S)
  localTag=DEPLOY_PIE_24_$dateVar
fi

# Create the tag and push
git tag $localTag
git push origin $localTag
