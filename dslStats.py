#!/usr/bin/env python
# dslStats.py - Simple module to collect details of the adsl output from a verizon router via collectd process
#  collectd sends to carbon/graphite on different host
#
# ----------------------------------------------
# In collectd.conf:
#
#  Import "dslStats"
#  <Module dslStats>
#    Verbose True
#    Username "username"
#    Password "password"
#    Address "192.168.x.x"
#    Hostname "dslRouter"
#  </Module>

# types.db needs:
#  dslStats	down:GAUGE:0:U, up:GAUGE:0:U

import collectd
import re
import telnetlib
import sys

Verbose = False
Username = ""
Password = ""
Hostname = ""
Address = ""

def read(data=None):

	tn = telnetlib.Telnet(Address)
	tn.read_until("Login: ")
	tn.write(Username + "\n")
	tn.read_until("Password: ")
	tn.write(Password + "\n")

	tn.write("adsl info --show\n")
	tn.write("exit\n")
	dslData = {}

	for line in tn.read_all().splitlines():
		#print ">>>%s" % (line)
		# looking for:
		#Channel:        INTR, Upstream rate = 864 Kbps, Downstream rate = 7616 Kbps

		match = re.search(r"Channel.*\s(\d+) Kbps.*\s(\d+) Kbps", line)
		if match:
			#print "match %s,%s" % (match.group(1), match.group(2))
			dslData['speed'] = {}
			dslData['speed']['up'] = match.group(1)
			dslData['speed']['down'] = match.group(2)

		# looking for: SNR (dB):        19.8            10.0

		match = re.search(r"^(.*):\s+(\d\S*)\s+(\d\S*)", line)
		if match:
			#print "match %s,%s,%s" % (match.group(1), match.group(2), match.group(3))
			key = match.group(1)
			key = re.sub("\s*\(.*\)","",key)
			down = match.group(2)
			up = match.group(3)
			dslData[key] ={}
			dslData[key]['down'] = down
			dslData[key]['up'] = up

	# end for each line
	#pprint(dslData)

	# collectd requires:
	# dispatch([type][, values][, plugin_instance][, type_instance][, plugin][, host][, time][, interval]) -> None
	# collectd.dslRouter.dslStats.
	
	# set up common items
	vl = collectd.Values(plugin='dsl')	# prevents the terrible: dslStats.dslStats. ... in the graphite system
	vl.host=Hostname
	wantedList = [ 'SNR', 'speed', 'Attn', 'delay' ]
	for item in wantedList:
		if Verbose:
			collectd.info('dslStats: Dispatching %s-down/up : %s,%s' % (item, dslData[item]['down'], dslData[item]['up']))
		vl.type='dslStats'
		vl.type_instance=item.lower()
		vl.values = [ dslData[item]['down'], dslData[item]['up'] ]
		vl.dispatch()

def configure_callback(conf):
	global Verbose, Username, Password, Hostname, Address
	for node in conf.children:
		if node.key == 'Verbose':
			Verbose = bool(node.values[0])
		if node.key == 'Username':
			Username = node.values[0]
		if node.key == 'Password':
			Password = node.values[0]
		if node.key == 'Hostname':
			Hostname = node.values[0]
		if node.key == 'Address':
			Address = node.values[0]


collectd.register_config(configure_callback)
if Verbose:
	collectd.info('Initialising dslStats for dslRouter: Verbose = True')
collectd.register_read(read)

