#!/usr/bin/python
#
#

import os
import sys
import logging
import codecs
from datetime import datetime

# bottle
import bottle
from beaker.middleware import SessionMiddleware
from jinja2 import Template, Environment, PackageLoader

# SMART
# from smart_client_python.smart import SmartClient
from rdflib.graph import Graph

# App
from ClinicalTrials.lillycoi import LillyCOI


# bottle, beaker and Jinja setup
session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 300,
    'session.data_dir': './session_data',
    'session.auto': True
}
app = application = SessionMiddleware(bottle.app(), session_opts)		# "application" is needed for some services like AppFog
_jinja_templates = Environment(loader=PackageLoader('wsgi', 'templates'), trim_blocks=True)

DEBUG = True


# ------------------------------------------------------------------------------ Utilities
def _get_session():
	return bottle.request.environ.get('beaker.session')


# ------------------------------------------------------------------------------ Index
@bottle.get('/')
@bottle.get('/index.html')
def index():
	""" The index page """
	
	# get parameters
	cond = bottle.request.query.get('cond')
	if cond is not None and len(cond) < 1:
		cond = None
	criteria = None
	csv_name = None
	trials = []
	num_trials = 0
	
	# if we got a condition
	if cond is not None:
		dump = True if bottle.request.query.get('criteria') is not None else False
		csv = True if bottle.request.query.get('csv') is not None else False
		
		lilly = LillyCOI()
		args = None if not dump and not csv else ['id', 'eligibility']
		found_trials = lilly.search_for_condition(cond, True, args)
		num_trials = len(found_trials)
		
		# list criteria
		if dump:
			trials = found_trials
		
		# return CSV
		elif csv:
			csv_name = 'criteria-%s.csv' % datetime.now().isoformat()[:-7]
			with codecs.open(csv_name, 'w', 'utf-8') as handle:
				heads = ["format","num in","num ex","w age","w gender","w pregnancy","incomplete","overly complex","sub-populations","negated inclusions","labs","scores","acronyms","temporal components","patient behavior/abilities","investigator-subjective components","sum"]
				headers = ','.join('""' for h in heads)
				
				# CSV header
				handle.write('"NCT","first received yrs ago","last update yrs ago","has completion","completion and status compatible","criteria",%s\n' % ','.join(['"%s"' % h for h in heads]))
				
				# CSV rows
				i = 0;
				every = 1;
				for study in found_trials:
					if 0 == i % every:
						study.load()
						handle.write('"%s","","","","","%s",%s\n' % (study.nct, study.criteria_text.replace('"', '""'), headers))
					i += 1;
	
	# render index
	template = _jinja_templates.get_template('index.html')
	return template.render(cond=cond, trials=trials, csv=csv_name, num=num_trials)


# ------------------------------------------------------------------------------ RESTful paths
@bottle.put('/session')
def session():
	""" To change the current session parameters.
	PUT form-encoded requests here to update the client's session params.
	"""
	
	put_data = bottle.request.forms
	keys = put_data.keys()
	if keys is not None and len(keys) > 0:
		sess = _get_session()
		for key in keys:
			sess[key] = put_data[key]
		
		sess.save()
	
	return 'ok'


# ------------------------------------------------------------------------------ Static Files
def _serve_static(file, root='.', **kwargs):
	""" Serves a static file or a 404 """
	try:
		return bottle.static_file(file, root=root, **kwargs)
	except Exception, e:
		bottle.abort(404)

@bottle.get('/static/<filename>')
def static(filename):
	return _serve_static(filename, 'static')

@bottle.get('/templates/<ejs_name>.ejs')
def ejs(ejs_name):
	return _serve_static('%s.ejs' % ejs_name, 'templates')

@bottle.get('/criteria-<timestamp>.csv')
def criteria(timestamp):
	return _serve_static('criteria-%s.csv' % timestamp, download=True)


# setup logging and run as server
if __name__ == '__main__':
	if DEBUG:
		logging.basicConfig(level=logging.DEBUG)
		bottle.run(app=app, host='0.0.0.0', port=8008, reloader=True)
	else:
		logging.basicConfig(level=logging.WARNING)
		bottle.run(app=app, host='0.0.0.0', port=8008, reloader=False)
