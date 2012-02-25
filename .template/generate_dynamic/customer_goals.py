'''Goals are a collection of phases which are automatically added to a build, then executed.

The idea here is for the calling code to not need to know about the right phases to include
when getting a higher-level "goal" done; e.g. running or generating an app.
'''
import platform
import sys

# TODO: could maybe replace this with a schema file - might want to do more
# validation than just filtering for these
RUN_CONFIG = (
	'build_type_dir',
	'device',
	'sdk',

	'interactive',
)

PACKAGE_CONFIG = (
	# ios packaging options
	'provisioning_profile', 
	'certificate_to_sign_with',

	# android packaging options
	'sdk', 
	'keystore',
	'storepass',
	'keyalias',
	'keypass',

	# web packaging options
	'heroku_key',
)

def _filter_kw(kw, allowed):
	"""Takes a dict and returns only the parts of it that we want to pass
	through to the customer phases and tasks
	"""
	return dict((k,v) for k,v in kw.items() if k in allowed)

def log_build(build, action):
	'''
	Bundle together some stats and send it to the server for tracking
	This is called by every other function in this module, just before running
	the build.
	'''
	from forge import build_config
	import forge
	from forge.remote import Remote

	log = {}
	log['action']   = action
	log['platform'] = platform.platform()
	log['version']  = sys.version
	log['uuid']     = build.config['uuid']
	log['tools_version'] = forge.VERSION
	config = build_config.load(expect_app_config=False)
	remote = Remote(config)
	remote._authenticate()
	remote._api_post('track/', data=log)


def generate_app_from_template(generate_module, build_to_run, server=False, **kw):
	'''Inject code into a previously built template.
	
	:param generate_module: the :mod:`generate.generate` module
	:param build_to_run: a :class:`build.Build` instance
	:param server: are we running on the server context or on a customer's machine
	'''
	build_to_run.add_steps(generate_module.customer_phases.resolve_urls())
	build_to_run.add_steps(generate_module.customer_phases.copy_user_source_to_template(server=server, ignore_patterns=build_to_run.ignore_patterns))
	build_to_run.add_steps(generate_module.customer_phases.include_platform_in_html(server=server))
	build_to_run.add_steps(generate_module.customer_phases.include_icons())
	build_to_run.add_steps(generate_module.customer_phases.make_installers(build_to_run.output_dir))

	log_build(build_to_run, "generate")
	build_to_run.run()

def run_app(generate_module, build_to_run, target, server=False, **kw):
	'''Run a generated app on a device or emulator.
	
	:param generate_module: the :mod:`generate.generate` module
	:param build_to_run: a :class:`build.Build` instance
	:param target: the target to run on, e.g. "android" or "firefox"
	:param server: are we running on the server context or on a customer's machine
	:param kw: extra configuration that will be passed through into each phase
	'''
	kw = _filter_kw(kw, RUN_CONFIG)

	if target == 'android':
		build_to_run.add_steps(
			generate_module.customer_phases.run_android_phase(build_to_run.output_dir, **kw)
		)
	elif target == 'ios':
		build_to_run.add_steps(
			generate_module.customer_phases.run_ios_phase(build_to_run.output_dir, **kw)
		)
	elif target == 'firefox':
		build_to_run.add_steps(
			generate_module.customer_phases.run_firefox_phase(build_to_run.output_dir, **kw)
		)
	elif target == 'web':
		build_to_run.add_steps(
			generate_module.customer_phases.run_web_phase(build_to_run.output_dir, **kw)
		)
	
	log_build(build_to_run, "run")
	build_to_run.run()

def package_app(generate_module, build_to_run, target, server=False, **kw):
	kw = _filter_kw(kw, PACKAGE_CONFIG)

	build_to_run.add_steps(
		generate_module.customer_phases.package(build_to_run.output_dir, **kw)
	)
	log_build(build_to_run, "package")
	build_to_run.run()
