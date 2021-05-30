#!/bin/bash
store_path=/media/sf_SHARED_DRIVE/webull.db.gz
mongodump -h=localhost -d=webull --archive=${store_path} --gzip
