#!/usr/bin/python
# ----------------------------------------------
# collectDf.py - Simple module to collect details of the output of df and send to collectd for processing
#
# ----------------------------------------------
# In collectd.conf:
#
#  Import "collectDF"
#  <Module collectDf>
#    Verbose false
#  </Module>

import collectd
import subprocess
import re
import os

Verbose = false

def read(data=None):
	# obtain the output of df
	output = subprocess.check_output("df")
	# split out the lines
	lines = output.splitlines()

	# collectd requires:
	# dispatch([type][, values][, plugin_instance][, type_instance][, plugin][, host][, time][, interval]) -> None.
	vl = collectd.Values(plugin='mountedDrives')
	vl.host=os.uname()[1]

	# ignoring the first (the header), parse
	for line in lines[1:]:
		filesystem, size, used, avail, usePcnt, mountPoint = line.split()
		# TODO: allow volumes from config
		if filesystem not in ["udev",  "none", "tmpfs"]:
			# strip out /dev/, replace / to _
			fs = re.sub("/dev/","", filesystem)
			mount = re.sub("/","_",mountPoint)

			vl.plugin_instance="{}{}".format(fs,mount)
			vl.type='bytes'
			vl.type_instance='total'
			vl.values = [ size ]
			if verbose:
				collectd.info("Dispatch %s, %s bytes-total: %s" % (fs, mount, total) )
			vl.dispatch()
			
			vl.type_instance='used'
			vl.values = [ used ]
			if verbose:
				collectd.info("Dispatch %s, %s bytes-used: %s" % (fs, mount, used) )
			vl.dispatch()

			usePcnt = re.sub("%","", usePcnt)
			vl.type='gauge'
			vl.type_instance='pcntUsed'
			vl.values = [ usePcnt ]
			if verbose:
				collectd.info("Dispatch %s, %s gauge-pcntUsed: %s" % (fs, mount, usePcnt) )
			vl.dispatch()

def configure_callback(conf):
	global verbose
	for node in conf.children:
		if node.key == 'Verbose':
			verbose = bool(node.values[0])

collectd.register_read(read)
if verbose:
	collectd.info('Init of collectDF: Verbose = true')
collectd.register_config(configure_callback)


