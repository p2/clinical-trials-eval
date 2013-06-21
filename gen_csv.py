#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# simple CSV generation


import sys
import logging
import datetime
from dateutil import parser
import codecs

from ClinicalTrials.lillycoi import LillyCOI


# main
if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG)
	
	# ask for a condition and recruitment status
	condition = raw_input("Search for condition: ")
	if condition is None or len(condition) < 1:
		print "Nothing to search for, good bye"
		sys.exit(0)
	
	# recruitment status
	recruiting = True
	recruiting_in = raw_input("Recruiting: [yes] ")
	if recruiting_in is not None and len(recruiting_in) > 0:
		recruiting = False if recruiting_in[:1] is 'n' or recruiting_in[:1] is 'N' else True
	
	# get trials
	lilly = LillyCOI()
	fields = [
		'id',
		'lastchanged_date',
		'firstreceived_date',
		'primary_completion_date',
		'verification_date'
	]
	found = lilly.search_for_condition(condition, recruiting, fields)
	if len(found) > 0:
		print "Found %d" % len(found)
		now = datetime.datetime.now()
		
		# list trials
		with codecs.open('years.csv', 'w') as csv:
			csv.write("nct,first,last,completion,veri\n")
			
			for trial in found:
				
				# date comparison
				first = trial.date('firstreceived_date')
				first_y = round((now - first[1]).days / 365.25 * 10) / 10 if first[1] else 99
				last = trial.date('lastchanged_date')
				last_y = round((now - last[1]).days / 365.25 * 10) / 10 if last[1] else 99
				comp = trial.date('primary_completion_date')
				comp_y = round((now - comp[1]).days / 365.25 * 10) / 10 if comp[1] else 99
				veri = trial.date('verification_date')
				veri_y = round((now - veri[1]).days / 365.25 * 10) / 10 if veri[1] else 99
				
				csv.write('"%s",%.1f,%.1f,%.1f,%.1f\n' % (trial.nct, first_y, last_y, comp_y, veri_y))
	else:
		print "None found"
