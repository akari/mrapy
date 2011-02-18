#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2011 Evgeny Osatyuk
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from hashlib import md5
import urllib2
import httplib


try:
	import json
	_jloads = lambda s: json.loads(s)
except ImportError:
	try:
		import simplejson
		_jloads = lambda s: simplejson.loads(s)
	except ImportError:
		from django.utils import simplejson
		_jloads = lambda s: simplejson.loads(s)

def get_uid_by_email( email = None ):
	"""	
		Take email as required argument and don't handles any exceptions in case of wrong or missing email.\n
		Return u'<UID>'.
	"""
	email, domain = email.split('@')
	conn = httplib.HTTPConnection( 'www.appsmail.ru' )
	conn.request( 'GET', '/platform/%s/%s' % (domain.split('.')[0], email, ) )
	req = conn.getresponse()
	if req.status != 200:
		raise httplib.HTTPException
	return _jloads( req.read() )['uid']

class MrapyError( Exception ):
	def __init__( self, status, code, msg ):
		self.code = self.status, self.code, self.msg = ( status, code, msg )
		Exception.__init__( self )
	def __str__( self ):
		return "Error( status = '%s', code = '%s', message = '%s' )" % ( self.status, self.code, self.msg, )

class Mrapy():
	def __init__( self, app_id, session_key=None, uid=None, secret_key=None, setXML = False ):
		self._apihost = 'www.appsmail.ru'
		self._apiurl  = '/platform/api'
		self.app_id = app_id
		self.session_key = session_key
		self.uid = uid
		self.secret_key = secret_key
		self.isXML = setXML
		
	def sign( self, params ):
		return md5( "".join(k + "=" + str(params[k]) for k in sorted(params.keys())) + self.secret_key ).hexdigest()

	def tcall( self, method, hash = None ):
		return self.req_call( method, hash )
		
	def call( self, *args, **kwargs ):
		return self.req_call( args[0], kwargs )

	def req_call( self, method, m_params ):

		if m_params is None:
			m_params = {}
		
		params = {
			'method': method,
			'app_id': self.app_id,
			'secure': '1',
			'format': 'json'
		}

		force_uid = None
		if 'force_uid' in m_params:
			force_uid = m_params['force_uid']
			del m_params['force_uid']

		if self.isXML:
			params.update({ 'format': 'xml' })

		if force_uid or not self.session_key:
			params.update({ 'uid': force_uid or self.uid })
		else:
			params.update({ 'session_key': self.session_key })

		params.update( m_params )
		url = "&".join(k + "=" + str(params[k]) for k in params.keys()) + '&sig=' + self.sign( params )

		conn = httplib.HTTPConnection( self._apihost )
		conn.request( 'POST', self._apiurl, url )
		req = conn.getresponse()
		if req.status != 200:
			try:
				_error_data = _jloads( req.read() )
			except:
				raise MrapyError( req.status, '-1', 'No parsable json returned from api call (network problem or so).' )
			raise MrapyError( req.status, _error_data['error']['error_code'], _error_data['error']['error_msg'] )

		return _jloads( req.read() )

