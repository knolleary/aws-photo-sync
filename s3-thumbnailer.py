#!/usr/bin/env python
'''
 Script to generate resized images (.jpg only) hosted on S3

 Intended to be run on an EC2 instance. 
 
 - searches all keys starting with 'pictures/2', eg:
    pictures/2010/10/01/IMG_0013.JPG
 - generates three resized versions in 'pictures/w/...' 
    pictures/w/2010/10/01/IMG_0013_m.JPG - 500x500 bounding box
    pictures/w/2010/10/01/IMG_0013_t.JPG - 100x100 bounding box
    pictures/w/2010/10/01/IMG_0013_s.JPG - 75x75 square
     
 Requires (on Ubuntu):
  - python-imaging
  - python-boto
  - a settings.py file containing:
     - AWS_ACCESS_KEY
     - AWS_SECRET_KEY
     - BUCKET
'''

import os
import re
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from PIL import Image

from settings import *

def get_new_filename(f,a):
  return "%s_%s%s"%(f[0:-4],a,f[-4:])

def get_scaled_size(img,target):
  if img.size[0] < img.size[1]:
    'portrait'
    targetHeight = target
    ratio = target/float(img.size[1])
    targetWidth = int(float(img.size[0])*float(ratio))
  else:
    'landscape'
    targetWidth = target
    ratio = target/float(img.size[0])
    targetHeight = int(float(img.size[1])*float(ratio))
  return (targetWidth,targetHeight)


def process_image(f):
  files = []
  img = Image.open(f)
  ''' m: 500 '''
  fn = get_new_filename(f,"m")
  img.copy().resize(get_scaled_size(img,500),Image.ANTIALIAS).save(fn)
  files.append(fn)
  ''' t: 100 '''
  fn = get_new_filename(f,"t")
  img_t = img.copy().resize(get_scaled_size(img,100),Image.ANTIALIAS).save(fn)
  files.append(fn)
  ''' s: 75x75 '''
  fn = get_new_filename(f,"s")
  halfsize = float(min(img.size))/2.
  crop = ( int((float(img.size[0])/2.)-halfsize),
           int((float(img.size[1])/2.)-halfsize),
           int((float(img.size[0])/2.)+halfsize),
           int((float(img.size[1])/2.)+halfsize)
          )
  img.crop(crop).resize((75,75),Image.ANTIALIAS).save(fn)
  files.append(fn)
  return files

conn = S3Connection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
bucket = conn.get_bucket(BUCKET)
rs = bucket.list(prefix='pictures/2')
for key in rs:
  if re.match(r".*\.jpg$",key.name,re.I):
    print key.name
    keyparts = key.name.split('/')
    filename = keyparts[-1]
    keyparts.insert(1,"w")
    keyparts = keyparts[:len(keyparts)-1]
    tkeyname = "%s/%s"%('/'.join(keyparts),get_new_filename(filename,"m"))
    if bucket.get_key(tkeyname) == None:
      print " getting %s"%(filename,)
      fp = open(filename, "w")
      key.get_file(fp)
      fp.flush()
      fp.close()
      print " processing images"
      files = process_image(filename)
      os.remove(filename)
      for f in files:
        print " uploading %s/%s"%('/'.join(keyparts),f)
        k = Key(bucket)
        k.key = "%s/%s"%('/'.join(keyparts),f)
        k.set_contents_from_filename(f)
        os.remove(f)
    else:
      print " skipping"
