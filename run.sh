#!/bin/bash
if test -z $PROJECT_ID || test -z $MY_REGION;
then
  echo "PROJECT_ID or MY_REGION were empty"
  exit 255
fi

if test -z $HOST;
then
  HOST=`hostname -s`
fi

if test -z $KEY_FILE;
then
  KEY_FILE=/var/key/rsa_private.pem
fi

# default registry name is 'iotlab-registry'
REGISTRY=${1:-iotlab-registry}

python3 my-sample.py \
   --project_id=$PROJECT_ID \
   --cloud_region=$MY_REGION \
   --registry_id=$REGISTRY \
   --device_id=$HOST \
   --key_file=$KEY_FILE \
   --message_type=event \
   --algorithm=RS256
