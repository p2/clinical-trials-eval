#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# simple CSV generation


import sys
import logging
import datetime
import codecs
import random

from ClinicalTrials.lillycoi import LillyCOI


# main
if __name__ == "__main__XX":
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
	get_trials(condition, recruiting)


def get_trials(condition, recruiting=True, filename='years.csv'):
	lilly = LillyCOI()
	fields = [
		'id',
		'lastchanged_date',
		'firstreceived_date',
		'primary_completion_date',
		'completion_date',
		'verification_date'
	]
	found = lilly.search_for_condition(condition, recruiting, fields)
	if len(found) > 0:
		print "Found %d" % len(found)
		now = datetime.datetime.now()
		
		# list trials
		with codecs.open(filename, 'w') as csv:
			csv.write('NCT,"first received yrs ago","last update yrs ago",primary,completion,veri,"has completion","completion and status compatible",criteria\n')
			
			if len(found) > 150:
				found = random.sample(found, len(found) / 4)
			
			for trial in found:
				
				# date comparison
				first = trial.date('firstreceived_date')
				first_y = round((now - first[1]).days / 365.25 * 10) / 10 if first[1] else 99
				last = trial.date('lastchanged_date')
				last_y = round((now - last[1]).days / 365.25 * 10) / 10 if last[1] else 99
				comp = trial.date('primary_completion_date')
				comp_y = round((now - comp[1]).days / 365.25 * 10) / 10 if comp[1] else 99
				done = trial.date('completion_date')
				done_y = round((now - done[1]).days / 365.25 * 10) / 10 if done[1] else 99
				veri = trial.date('verification_date')
				veri_y = round((now - veri[1]).days / 365.25 * 10) / 10 if veri[1] else 99
				
				csv.write('"%s",%.1f,%.1f,%.1f,%.1f,%.1f,%s,%s,""\n' % (trial.nct, first_y, last_y, comp_y, done_y, veri_y, 'TRUE' if done[1] else 'FALSE', 'TRUE' if done[1] and done[1] > now else 'FALSE'))
		print 'Written to "%s"' % filename
	else:
		print "None found"


if __name__ == "__main__":
	for cond in ['Gleevec', 'Cataract', 'Neuroblastoma', 'rheumatoid arthritis']:
		get_trials(cond, True, 'Set-%s.csv' % cond.replace('rheumatoid arthritis', 'RheumArth'))
