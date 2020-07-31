#! /bin/sh
wget \
 --header="Authorization: Bearer $TOKEN" \
 --post-data="{}" \
 $WEBHOOK
