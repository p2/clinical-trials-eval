#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Takes a CSV and updates some columns


import sys
import logging
import datetime
from dateutil import parser
import codecs
import csv
import os.path

from ClinicalTrials.lillycoi import LillyCOI


# main
if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG)
	csv_path = None
	
	# get the CSV to be updated
	if '-f' in sys.argv:
		csv_path = sys.argv[sys.argv.index('-f') + 1]
	else:
		print "Provide the path to the CSV to be updated after the -f flag"
		sys.exit(1)
	
	if csv_path is None or not os.path.exists(csv_path):
		raise Exception("There is no such file (%s)" % csv_path)
	
	# read CSV
	with codecs.open(csv_path, 'r') as handle:
		reader = csv.reader(handle)
		header = reader.next()
		
		idx_nct = header.index('NCT')
		idx_drop = header.index('criteria')
		idx_first = header.index('first received yrs ago')
		idx_last = header.index('last update yrs ago')
		
		# open output file
		csv_new = "%s-auto-updated.csv" % os.path.splitext(csv_path)[0].replace('-manual', '')
		with codecs.open(csv_new, 'w') as w_handle:
			lilly = LillyCOI()
			# ref_date = datetime.datetime(2013, 7, 30)		# this can NOT be used against date last updated, of course
			ref_date = datetime.datetime.now()
			
			writer = csv.writer(w_handle)
			header.pop(idx_drop)
			writer.writerow(header)
			
			# loop trials
			for row in reader:
				trial = lilly.get_trial(row[idx_nct])
				
				# date calculations
				first = trial.date('firstreceived_date')
				first_y = round((ref_date - first[1]).days / 365.25 * 10) / 10 if first[1] else 99
				last = trial.date('lastchanged_date')
				last_y = round((ref_date - last[1]).days / 365.25 * 10) / 10 if last[1] else 99
				comp = trial.date('primary_completion_date')
				comp_y = round((ref_date - comp[1]).days / 365.25 * 10) / 10 if comp[1] else 99
				veri = trial.date('verification_date')
				veri_y = round((ref_date - veri[1]).days / 365.25 * 10) / 10 if veri[1] else 99
				
				# write updated row
				row[idx_first] = first_y
				row[idx_last] = last_y
				row.pop(idx_drop)
				writer.writerow(row)
		
		print 'Written to "%s"' % csv_new

