import errno
import json
import logging
import os
from os import path
import re
import shutil
import sys
import subprocess
import threading
from urlparse import urljoin

import requests

import lib
from lib import cd, task
from utils import run_shell, ShellError

LOG = logging.getLogger(__name__)

class WebError(lib.BASE_EXCEPTION):
	pass

@task
def run_web(build, build_type_dir, **kw):
	# run Node locally
	def show_local_server():
		_open_url("http://localhost:3000/")

	with cd(path.join("development", "web")):
		try:
			run_shell("npm", "install")
			timer = threading.Timer(3, show_local_server).start()
			run_shell("npm", "start", command_log_level=logging.INFO)
		except Exception:
			LOG.error("failed to run npm: do you have Node.js installed and on your path?")
			timer.cancel()
			raise

def _git(cmd, *args, **kwargs):
	"""Runs a git command and scrapes the output for common problems, so that we can try
	to advise the user about them

	e.g. _git('push', '--all')
	"""
	try:
		output = run_shell('git', cmd, *args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs)
	except OSError as e:
		if e.errno == errno.ENOENT:
			# TODO: download portable copy of git/locate git?
			raise WebError("Can't run git commands - you need to install git and make sure it's in your PATH")
	except ShellError as e:
		LOG.info('Encountered problem with git {0} {1}:\n {2}'.format(cmd, args, e.output))

		def _key_problem(output):
			lines = output.split('\n')
			if len(lines) > 0:
				first = lines[0]
				return first.startswith('Permission denied (publickey)')

		if _key_problem(e.output):
			# TODO: prompt user with choice to use existing .pub in ~/.ssh
			# or create new keypair and submit to heroku
			raise WebError('Failed to access remote git repo, you need to set up key based access')

		raise WebError('Problem running git {cmd}:\n {output}'.format(cmd=cmd, output=e.output))

	return output

def _heroku_credentials():
	"""Fetches credentials for Heroku API calls stored for this app, raises if not there"""
	path = os.path.expanduser(os.path.join('~', '.heroku', 'credentials'))
	with open(path) as credentials_file:
		return credentials_file.readlines()

def _present_choice(message, choices, prompt):
	"""Presents the user with a numerical choice on the command line
	
	:param message: The question to ask the user
	:param choices: A list of possible choices
	:param prompt: The text shown to the user on the line they enter their choice
	:return n: An int, in range(len(choices))

	*NB* asks repeatedly until the user enters a valid choice
	"""
	lines = ["%d) %s" % (i,choices[i]) for i in xrange(len(choices))]
	
	LOG.info(
		message + "\n" + "\n".join(lines)
	)

	choice = None
	while choice is None:
		try:
			inp = raw_input(prompt)
			n = int(inp.strip())

			if not (0 <= n < len(choices)):
				raise ValueError

			choice = n
		except ValueError:
			LOG.info("Invalid choice")

	return choice

# TODO: error code checking on responses
def _heroku_get(api_key, api_url):
	# see https://api-docs.heroku.com/apps
	# heroku api requires a blank user and api_key as http auth details
	auth = ('', api_key)
	headers = {
		'Accept': 'application/json',
	}
	url = urljoin('https://api.heroku.com/', api_url)
	return requests.get(url, auth=auth, headers=headers)

# TODO: error code checking on responses
def _heroku_post(api_key, api_url, data):
	# heroku api requires a blank user and api_key as http auth details
	auth = ('', api_key)
	headers = {
		'Accept': 'application/json',
	}
	url = urljoin('https://api.heroku.com/', api_url)
	return requests.post(url, data=data, auth=auth, headers=headers)

def _open_url(url):
	'''Attempt to open the provided URL in the default browser'''
	if sys.platform.startswith('darwin'):
		run_shell('open', url, fail_silently=True)
	elif sys.platform.startswith('win'):
		# 'start' seems to need shell=True to be found (probably a builtin)
		cmd = subprocess.list2cmdline(['start', url])
		subprocess.call(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	elif sys.platform.startswith('linux'):
		run_shell('xdg-open', url, fail_silently=True)

@task
def package_web(build, interactive=True, **kw):
	development = path.abspath(path.join('development', 'web'))
	output = path.abspath(path.join('release', 'web', 'heroku'))

	# deploy to Heroku
	if sys.platform.startswith("win"):
		heroku = "heroku.bat"
	else:
		heroku = "heroku"
	with cd(development):
		username = None
		api_key = None

		while username is None:
			try:
				# TODO: may want to check the api key is actually valid by hitting the api?
				username, api_key = _heroku_credentials()
			except IOError:
				login_call = subprocess.call([heroku, 'login'])
				if login_call != 0:
					raise Exception("Failed to login with the heroku api")

		# do we already have a .git directory?
		if not path.isdir(path.join(output, '.git')):
			if not path.isdir(output):
				os.makedirs(output)

			with cd(output):

				# TODO: tools should be able to pass through with --app or force creation with --create
				if not interactive:
					raise Exception("Need to specify an heroku app")

				LOG.info('Querying heroku about registered apps...')
				apps = json.loads(_heroku_get(api_key, 'apps').content)
				app_names = [app['name'] for app in apps]

				create_new_heroku_app = True

				if app_names:
					message = (
						'Since this is your first time deploying this app to heroku, '
						'you can choose either to:'
					)

					chosen_n = _present_choice(message, ['Create a new heroku application', 'Push to a currently registered heroku application'], 'Choice: ')

					if chosen_n == 0:
						create_new_heroku_app = True
					else:
						create_new_heroku_app = False

				# either create a new heroku app, or choose an already existing app
				if create_new_heroku_app:
					# TODO: allow user to specify app name?
					# have to deal with name already taken
					LOG.info('Creating new heroku application')
					response = _heroku_post(api_key, 'apps', data='app[stack]=cedar')
					chosen_app = json.loads(response.content)['name']

				else:
					chosen_n = _present_choice('Choose an existing heroku app to deploy to:', 
							app_names, 'Deploy to: ')

					chosen_app = app_names[chosen_n]

				LOG.debug('Creating git repo now we have somewhere to fetch/push to')
				_git('init')

				LOG.debug('Create dummy first commit')
				with open('.forge.txt', 'w') as forge_file:
					forge_file.write('')
				_git('add', '.')
				_git('commit', '-am', '"first commit"')

				LOG.debug('Setting up git remote')
				_git('remote', 'add', 'heroku', 'git@heroku.com:%s.git' % chosen_app)

		# remove all previous files/folders except for .git!
		with cd(output):
			for f in os.listdir('.'):
				if not f == '.git':
					if path.isfile(f):
						os.remove(f)

					elif path.isdir(f):
						shutil.rmtree(f)

		# copy code from development to release!
		with cd(development):
			for f in os.listdir('.'):
				if path.isfile(f):
					shutil.copy2(f, output)
				elif path.isdir(f) and path.basename(f) != '.git':
					shutil.copytree(f, path.join(output, f))

		with cd(output):
			# commit
			_git('add', '.')
			diff = _git('diff', 'HEAD')
			if not diff.strip():
				raise WebError("no app changes found: did you forget to forge build?")
			_git('commit', '-am', 'forge package web')

			# push
			push_output = _git('push', 'heroku', '--all', '--force', command_log_level=logging.INFO)
			deploy_pattern = re.compile(r'(http://[^ ]+) deployed to Heroku')
			deploy_match = deploy_pattern.search(push_output)
			if deploy_match:
				_open_url(deploy_match.group(1))
			LOG.info('Pushed to heroku')
