#!/usr/bin/python
# ----------------------------------------------
# collectDf.py - Simple module to collect details of the output of df via collectd process
#  collectd sends to carbon/graphite on different host
#
# ----------------------------------------------
# In collectd.conf:
#
#  Import "collectDf"
#  <Module collectDf>
#    Verbose False/True
#  </Module>

# types.db for df = total:GAUGE:0:U, used:GAUGE:0:U, pcntUsed:GAUGE:0:100
#  may need to replace df in original types.db with df_old if using a custom type.db file

import collectd
import subprocess
import re
import os

Verbose = False

def read(data=None):
	vl = collectd.Values(plugin='mountedDrives')
	vl.host=os.uname()[1]

	# obtain the output of df
	output = subprocess.check_output("df")
	# split out the lines
	lines = output.splitlines()

	#/dev/sda1      487727216  11126468 452186748   3% /
	#/dev/sde1      240362656 180626476  47526380  80% /mnt/hd
	#/dev/sda6      478169232 236302260 217931280  53% /home

	# need to send 3 values, total, size, pcntUsed for each line

	# ignoring the first (the header), parse
	for line in lines[1:]:
		filesystem, size, used, avail, usePcnt, mountPoint = line.split()
		# TODO: allow volumes from config
		if filesystem not in ["udev",  "none", "tmpfs"]:
			# strip out /dev/, replace / to _
			fs = re.sub("dev/","", filesystem[1:])
			if mountPoint == "/":
				mountPoint = "/ROOT"
			mount = re.sub("/","_",mountPoint)
			usePcnt = re.sub("%","", usePcnt)

			vl.type='df'
			vl.type_instance="{}{}".format(fs,mount)
			vl.values = [ size, used, usePcnt ]
			if Verbose:
				collectd.info("collectDf: Dispatch %s%s [ %s, %s, %s ]" % (fs, mount, size,used,usePcnt) )
			vl.dispatch()

def configure_callback(conf):
	global Verbose
	for node in conf.children:
		if node.key == 'Verbose':
			Verbose = bool(node.values[0])

collectd.register_read(read)
if Verbose:
	collectd.info('Init of collectDF: Verbose = true')
collectd.register_config(configure_callback)


