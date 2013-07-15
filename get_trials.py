#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Takes a list of NCT, loads these studies from our database or via Lilly if we
# don't yet know about it, and returns a CSV with the given header data.


_list_path = 'nct-input.txt'
_headers = ['nct', 'title', 'overall_contact', 'locations']
_force_update = False
_reference_lat_lng = [42.358, -71.06]			# Boston, MA


import sys
import logging
import codecs
import os.path
import csv

from ClinicalTrials.study import Study, trial_contact_parts
from ClinicalTrials.lillycoi import LillyCOI


# main
if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG)
	
	# look for the list
	if not os.path.exists(_list_path):
		print 'x>  The list is missing, it should reside at %s and contain one NCT per line' % _list_path
		sys.exit(1)
	
	# read list
	with codecs.open(_list_path, 'r') as handle:
		ncts = [nct.strip() if len(nct.strip()) > 0 else None for nct in handle.readlines()]
		assert len(ncts) > 0
		trials = {}
		lilly = LillyCOI()
		
		# retrieve from our database
		if not _force_update:
			existing = Study.retrieve(ncts)
			for ex in existing:
				trials[ex.nct] = ex
		
		# open output file and write header
		csv_new = "nct-output.csv"
		with open(csv_new, 'wb') as w_handle:
			writer = csv.writer(w_handle)
			writer.writerow(_headers)
			
			# loop trials
			for nct in ncts:
				if not nct:
					continue
				
				# get the trial
				if nct in trials:
					trial = trials[nct]
				else:
					trial = lilly.get_trial(nct)
					if trial is None:
						raise Exception("No trial for %s" % nct)
					trial.store()
				
				# collect trial attributes
				row = []
				for key in _headers:
					
					# add locations
					if 'locations' == key:
						closest = trial.locations_closest_to(_reference_lat_lng[0], _reference_lat_lng[1], 3)
						for i in xrange(0,3):
							if len(closest) > i:
								row.append('[%s] %s: %s' % (closest[i].status, closest[i].city, '; '.join(closest[i].address_parts)))
							else:
								row.append('')
						continue
					
					# generic columns
					val = getattr(trial, key)
					
					# format overall contact
					if 'overall_contact' == key:
						val = '; '.join(trial_contact_parts(val))
					
					if type(val) != unicode:
						val = unicode(val)
					row.append(val.encode('utf-8') if val else '')
				
				# write row
				writer.writerow(row)
		
		print 'Written to "%s"' % csv_new

