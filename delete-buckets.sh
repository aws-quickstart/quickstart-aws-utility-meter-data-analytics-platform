#!/usr/bin/env bash

aws s3 rm s3://$1 --recursive && aws s3 rb s3://$1 --force &>/dev/null