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
from ClinicalTrials.study import Study
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
	
	# if we got a condition, dump the trials to CSV
	cond = bottle.request.query.get('cond')
	csv_name = None
	if cond is not None:
		Study.setup_tables('storage.db')

		lilly = LillyCOI()
		found_studies = lilly.search_for_condition(cond, True, ['id', 'eligibility'])
		
		# CSV header
		csv_name = 'criteria-%s.csv' % datetime.now().isoformat()[:-7]
		with codecs.open(csv_name, 'w', 'utf-8') as handle:
			handle.write('"NCT","criteria","","","","",""\n')
			
			# CSV rows
			for study in found_studies:
				study.load()
				handle.write('"%s","%s","","","","",""\n' % (study.nct, study.criteria_text.replace('"', '""')))
	
	# render index
	template = _jinja_templates.get_template('index.html')
	return template.render(csv=csv_name)


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
