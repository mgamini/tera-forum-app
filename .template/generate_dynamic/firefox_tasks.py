import codecs
import os
from os import path
import shutil
import logging
import sys

from lib import task
from utils import run_shell


LOG = logging.getLogger(__name__)

def clean_firefox(build_type_dir):
	original_harness_options = os.path.join(build_type_dir, 'firefox', 'harness-options.json')
	backup_harness_options = os.path.join(build_type_dir, 'firefox', 'harness-options-bak.json')
	LOG.debug('Cleaning up after firefox run')
	if os.path.isfile(backup_harness_options):
		shutil.move(backup_harness_options, original_harness_options)

@task
def run_firefox(build, build_type_dir):
	python = sys.executable
	generate_dynamic_root = path.abspath(
		path.join(__file__, path.pardir)
	)
	try:
		run_shell(python, path.join(generate_dynamic_root, 'run-firefox.zip'), command_log_level=logging.INFO)
	finally:
		clean_firefox(build_type_dir)
