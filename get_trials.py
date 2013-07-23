#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Takes a list of NCT, loads these studies from our database (or via Lilly if we
# don't yet have it) and returns a CSV with the given header data.


_list_path = 'nct-input.txt'
_headers = ['nct', 'entered', 'last_updated', 'title', 'overall_contact', 'locations']
_n_sample = 40
_force_update = False
_reference_lat_lng = [42.358, -71.06]			# Boston, MA


import sys
import logging
import codecs
import os.path
import csv
import math
import random

from ClinicalTrials.study import Study, trial_contact_parts
from ClinicalTrials.lillycoi import LillyCOI


# main
if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG)
	
	# parse arguments
	if '-f' in sys.argv:
		_force_update = True
	if '-l' in sys.argv:
		_list_path = sys.argv[sys.argv.index('-l') + 1]
	
	# ask for NCT list
	if _list_path is None:
		_list_path = raw_input('Path to the NCT list: ')
	
	# look for the list
	if not os.path.exists(_list_path):
		print 'x>  The list file at %s does not exist' % _list_path
		sys.exit(1)
	
	# read list
	with codecs.open(_list_path, 'r') as handle:
		ncts = [nct.strip() if len(nct.strip()) > 0 else None for nct in handle.readlines()]
		assert len(ncts) > 0
		trials = {}
		rows_and_years = []
		lilly = LillyCOI()
		
		# retrieve from our database
		if not _force_update:
			existing = Study.retrieve(ncts)
			for ex in existing:
				trials[ex.nct] = ex
		
		# loop trials
		for nct in ncts:
			if not nct:
				continue
			
			# get the trial fresh via web
			if nct in trials:
				trial = trials[nct]
			else:
				trial = lilly.get_trial(nct)
				if trial is None:
					raise Exception("No trial for %s" % nct)
				trial.store()
			
			# skip if not in the US
			countries = getattr(trial, 'location_countries')
			if countries is None or 0 == len(countries) or u'United States' not in countries.get('country', []):
				# print '-->  Skipping %s (%s)' % (nct, countries)
				continue
			# print '==>  Using %s' % nct
			
			first_y = trial.entered
			last_y = trial.last_updated
			
			# collect trial attributes
			row = []
			for key in _headers:
				if 'entered' == key:
					row.append(u'%.1f y' % first_y)
					continue
				if 'last_updated' == key:
					row.append(u'%.1f y' % last_y)
					continue
				
				# add locations
				if 'locations' == key:
					closest = trial.locations_closest_to(_reference_lat_lng[0], _reference_lat_lng[1], 3)
					for i in xrange(0,3):
						if len(closest) > i:
							row.append(u'[%s] %s: %s' % (closest[i].status, closest[i].city, '; '.join(closest[i].address_parts)))
						else:
							row.append(u'')
					continue
				
				# generic columns
				val = getattr(trial, key)
				
				# format overall contact
				if 'overall_contact' == key:
					val = u'; '.join(trial_contact_parts(val))
				
				row.append(val if val else '')
			
			rows_and_years.append((row, last_y, first_y))
		
		# sort by last_y and then first_y (second and third item per tuple)
		rows_and_years.sort(key=lambda tup: (tup[1], tup[2]))
		n_rows = len(rows_and_years)
		
		# random sampling -> _n_sample max, split list by 4 and select 5 random
		if n_rows > _n_sample:
			num_chunks = 4
			per_chunk = int(math.ceil(float(_n_sample) / num_chunks))
			chunk_size = int(math.ceil(float(n_rows) / num_chunks))
			if chunk_size < per_chunk:
				raise Exception("There would be less than %d elements per chunk, adjust the number of chunks for %d list elements" % (per_chunk, n_rows))
			
			new_rows = []
			for i in xrange(0, n_rows, chunk_size):
				rands = random.sample(rows_and_years[i:i+chunk_size], per_chunk)
				new_rows.extend(rands)
			
			# sort again
			rows_and_years = sorted(new_rows, key=lambda tup: (tup[1], tup[2]))
		
		rows = [r[0] for r in rows_and_years]
		
		# write to csv
		csv_new = "nct-output.csv"
		with open(csv_new, 'wb') as w_handle:
			writer = csv.writer(w_handle)
			writer.writerow(_headers)
			
			for row_raw in rows:
				row = [unicode(r).encode('utf-8') for r in row_raw]
				writer.writerow(row)
		
		print 'Written to "%s"' % csv_new

