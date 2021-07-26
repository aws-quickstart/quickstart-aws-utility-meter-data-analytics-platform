#!/usr/bin/env bash
rm -fr templates/prediction/.aws-sam
aws s3 sync . s3://$1 --exclude "*" --include "assets/*" --include "templates/*" --include "submodules/*"