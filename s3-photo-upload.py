#!/usr/bin/env python
'''
 Script to sync photos to an Amazon S3 bucket
 
 Requires:
  - python-boto
  - a settings.py file containing:
     - AWS_ACCESS_KEY
     - AWS_SECRET_KEY
     - BUCKET
     - LOCAL_DIR
'''

import os
import os.path
import re
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import sys

from settings import *

l = {}
conn = S3Connection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
bucket = conn.get_bucket(BUCKET)

# Retrieve the list of existing files
rs = bucket.list()
for key in rs:
  l[key.name] = '[s3]'

prefix_length = len(LOCAL_DIR)+1

# Walk the local directory, upload any files not in the list of existing files
for root, dirs, files in os.walk(LOCAL_DIR):
  d = root[prefix_length:]
  m = re.match(r"(\d\d\d\d)_(\d\d)_(\d\d)",d)
  if m:
    for f in files:
      k = "pictures/%s/%s/%s/%s"%(m.group(1),m.group(2),m.group(3),f)
      if k in l:
        l[k] = "[ok]"
      else:
        print k,
        key = Key(bucket)
        key.key = k
        k.set_contents_from_filename(os.path.join(root,f))
        print "done"
        l[k] = "[  ]"


