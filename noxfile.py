# SPDX-License-Identifier: BSD-3-Clause

import shutil
from pathlib        import Path
from setuptools_scm import (
	get_version, ScmVersion
)

import nox

ROOT_DIR  = Path(__file__).parent

BUILD_DIR = (ROOT_DIR  / 'build')
CNTRB_DIR = (ROOT_DIR  / 'contrib')
DOCS_DIR  = (ROOT_DIR  / 'docs')
DIST_DIR  = (BUILD_DIR / 'dist')


# Default sessions to run
nox.options.sessions = (
	'test',
	'lint',
	'typecheck'
)

def usb_construct_version() -> str:
	def scheme(version: ScmVersion) -> str:
		if version.tag and not version.distance:
			return version.format_with('')
		else:
			return version.format_choice('+{node}', '+{node}.dirty')

	return get_version(
		root           = str(ROOT_DIR),
		version_scheme = 'guess-next-dev',
		local_scheme   = scheme,
		relative_to    = __file__
	)

@nox.session(reuse_venv = True)
def test(session: nox.Session) -> None:
	out_dir = (BUILD_DIR / 'tests')
	out_dir.mkdir(parents = True, exist_ok = True)
	coverage = '--coverage' in session.posargs

	unitest_args = ('-m', 'unittest', 'discover', '-s', str(ROOT_DIR))

	session.install('.')
	if coverage:
		session.log('Coverage support enabled')
		session.install('coverage')
		coverage_args = (
			'-m', 'coverage', 'run',
			f'--rcfile={CNTRB_DIR / "coveragerc"}'
		)
	else:
		coverage_args = ()

	session.chdir(str(out_dir))
	session.run(
		'python', *coverage_args, *unitest_args
	)

	if coverage:
		session.run(
			'python', '-m', 'coverage', 'xml',
			f'--rcfile={CNTRB_DIR / "coveragerc"}'
		)

@nox.session
def docs(session: nox.Session) -> None:
	out_dir = (BUILD_DIR / 'docs')
	shutil.rmtree(out_dir, ignore_errors = True)
	session.install('-r', str(DOCS_DIR / 'requirements.txt'))
	session.install('.')
	session.run('sphinx-build', '-b', 'html', str(DOCS_DIR), str(out_dir))

@nox.session
def typecheck(session: nox.Session) -> None:
	out_dir = (BUILD_DIR / 'mypy')
	out_dir.mkdir(parents = True, exist_ok = True)

	session.install('mypy')
	session.install('lxml')
	session.install('construct-typing') # Stubs for Construct
	session.install('.')
	session.run(
		'mypy', '--non-interactive', '--install-types', '--pretty',
		'--cache-dir', str((out_dir / '.mypy-cache').resolve()),
		'--config-file', str((CNTRB_DIR / '.mypy.ini').resolve()),
		'-p', 'usb_construct', '--html-report', str(out_dir.resolve())
	)

@nox.session
def lint(session: nox.Session) -> None:
	session.install('flake8')
	session.run(
		'flake8', '--config', str((CNTRB_DIR / '.flake8').resolve()), './usb_construct'
	)
	session.run(
		'flake8', '--config', str((CNTRB_DIR / '.flake8').resolve()), './tests'
	)
	session.run(
		'flake8', '--config', str((CNTRB_DIR / '.flake8').resolve()), './examples'
	)

@nox.session
def dist(session: nox.Session) -> None:
	session.install('build')
	session.run(
		'python', '-m', 'build',
		'-o', str(DIST_DIR)
	)

@nox.session
def upload(session: nox.Session) -> None:
	session.install('twine')
	dist(session)
	session.log(f'Uploading usb-construct-{usb_construct_version()} to PyPi')
	session.run(
		'python', '-m', 'twine', 'upload',
		f'{DIST_DIR}/usb-construct-{usb_construct_version()}*',
		f'{DIST_DIR}/usb_construct-{usb_construct_version()}*'
	)
