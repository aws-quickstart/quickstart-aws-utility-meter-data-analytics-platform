#!/usr/bin/env bash

aws s3 sync . s3://$1 --exclude "*" --include "assets/*" --include "templates/*"