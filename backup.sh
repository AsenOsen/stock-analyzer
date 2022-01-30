#!/bin/bash
store_path="$1"
mongodump -h=localhost -d=webull --archive=${store_path} --gzip
