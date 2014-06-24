#!/usr/bin/env python2
# Anthony Clark
#	Simple C/GCC evaluation loop
#
import os
import sys
import readline
import subprocess
import random
import io
from config import Config
from config import ConfigException

VER = 0.01
WPATH = os.path.realpath(sys.argv[0])
ANSI_BASE = '\001\033[%sm\002'

_F="""Simple C interpreter V{} - Anthony Clark""".format(VER)

ABOUT="""\
Simple C interpreter V{} - Anthony Clark
Options:
	-h  This message
	-p  To compile and run previous file
""".format(VER)

HEADER="""\
{includes}

{prototypes}

{_globals}

{functions}

"""

MAIN_HEADER="""\
int main(int argc, char **argv)
{
"""

MAIN_FOOTER="""\

	return errno;
}
"""

def colorize(color, str):
	s = '' + (ANSI_BASE % color) + str + (ANSI_BASE % 0)
	return s


class Compiler(object):
	_section = 'compiler'
	
	def __init__(self, conf):
		self.config = conf
		self.config.section = self._section

		self.std = self.config.get_option('std')
		self.warnings = self.config.get_option('warnings')
		self.command = self.config.get_option('command')
		self.includes = self.config.get_option('includes', Config.CONFIG_CSV)
		self.includes = ["#include <%s>" % i.strip() for i in self.includes]
		self.output_name = self.config.get_option('output')
		self.output_bin = self.config.get_option('binary')

	def assemble_command(self):
		return self.command

	def write_contents(self, stream, _g, _f, _l):
			_gl = []
			_fl = []

			for g in _g:
				for l in g.lines:
					_gl.append(l)

			for f in _f:
				for l in f.lines:
					_fl.append(l)

			stream.write(HEADER.format(
				includes='\n'.join(self.includes),
				prototypes='\n'.join([fn.create_prototype() for fn in _f]),
				_globals='\n'.join(_gl),
				functions='\n'.join(_fl)))

			stream.write(MAIN_HEADER)
			stream.write('\n'.join(_l))
			stream.write(MAIN_FOOTER)

	def write_file(self, _g, _f, _l):
		with open(self.output_name, 'w+') as out:
			self.write_contents(out, _g, _f, _l)

	def compile(self):
		_r = subprocess.call([str(tok) for tok in self.assemble_command().split(' ')])
		if not _r: # 0 is good
			_r = subprocess.call([self.output_bin])
		return _r


class Function(object):
	token = 'f'
	color = 0

	def __init__(self, ps2):
		self.lines = []
		self.ps2 = ps2

	def create_prototype(self):
		return self.lines[0] + ';'

	def loop(self):
		read = 1
		while read:
			read = raw_input(colorize(self.color, ('%-5s' % self.ps2)))
			self.lines.append(read);


class Global(object):
	token = 'g'
	color = 0
	
	def __init__(self, ps2):
		self.lines = []
		self.ps2 = ps2

	def loop(self):
		read = 1
		while read:
			read = raw_input(colorize(self.color, ('%-5s' % self.ps2)))
			self.lines.append(read);


class Features(object):
	_section = 'features'
	def __init__(self, conf):
		self.config = conf


class Editor(object):
	_section = 'editor'
	ps1color = 0
	ps2color = 0

	color_map = {
			'black'			:'0;30',
			'red'			:'0;31',
			'green'			:'0;32',
			'brown'			:'0;33',
			'blue'			:'0;34',
			'purple'		:'0;35',
			'cyan'			:'0;36',
			'lightgray'		:'0;37',
			'darkgray'		:'1;30',
			'lightred'		:'1;31',
			'lightgreen'	:'1;32',
			'yellow'		:'1;33',
			'lightblue'		:'1;34',
			'lightpurple'	:'1;35',
			'lightcyan'		:'1;36',
			'white'			:'1;37',
	}
	
	def __init__(self, conf, comp, feat):
		self.lines = []
		self.funcs = []
		self.globs = []

		self.config = conf
		self.config.section = self._section
		self.ps1 = self.config.get_option('PS1')
		self.ps2 = self.config.get_option('PS2')
		self.regcol  = self.color_map.get(str(self.config.get_option('reg_color')))
		self.contcol = self.color_map.get(str(self.config.get_option('cont_color')))
		self.fncol  = self.color_map.get(str(self.config.get_option('fn_color')))
		self.glcol  = self.color_map.get(str(self.config.get_option('gl_color')))

		self.ext = self.config.get_option('external_editor')
		if self.ext[0] == '$':
			self.ext = os.environ.get(self.ext[1:], 'nano')

		Editor.ps1color = self.regcol
		Editor.ps2color = self.contcol
		Function.color = self.fncol
		Global.color = self.glcol

		self.compiler = comp
		self.features = feat

	def loop(self):
		read = 1
		ps1 = colorize(Editor.ps1color, ('%-5s' % self.ps1))
		ps2 = colorize(Editor.ps2color, ('%-5s' % self.ps2))

		# colored header
		_f = _F.split(' ')
		_r  = random.sample(self.color_map.keys(), len(_f))
		for i,r in enumerate(_r):
			_f[i] = colorize(self.color_map[r], _f[i])
		print ' '.join(_f)

		# repl
		while read:
			read = raw_input(ps1)
			
			if not read:
				break
			
			if read == Function.token:
				function_ctx = Function(self.ps2)
				function_ctx.loop()
				self.funcs.append(function_ctx)
				continue;
			
			if read == Global.token:
				global_ctx = Global(self.ps2)
				global_ctx.loop()
				self.globs.append(global_ctx)
				continue;
			
			if read == 'r': # review
				highlight = subprocess.Popen(['highlight', '-S','c','-O','xterm256'], stdin=subprocess.PIPE,
									stdout=subprocess.PIPE, bufsize=-1)
				
				buff = io.BytesIO()
				self.compiler.write_contents(buff, self.globs, self.funcs, self.lines)
				out, err = highlight.communicate(buff.getvalue())
				print out

				continue
			
			self.lines.append('\t' + read)
			
			if read[len(read)-1] not in [';', '}']:
				r = 1
				while r:
					r = raw_input(ps2)
					if r: self.lines.append('\t\t'+r)
				continue;

			
	def compile(self, opt=0):
		if not opt:
			self.compiler.write_file(self.globs, self.funcs, self.lines)
		self.compiler.compile()


class RuntimeEnvironment(object):
	# Runtime Env init
	def __init__(self, conf):
		self.config = conf
		self.compiler = Compiler(self.config)
		self.features = Features(self.config)
		self.editor = Editor(self.config, self.compiler, self.features)

def main(argc, argv):
	if any(arg in ['-h', '--help'] for arg in sys.argv[1:]):
		print ABOUT
		return

	tok = 0 or any(map(lambda x: x in sys.argv, ['-r', '-p']))

	config = Config('config.cfg')
	runtime = RuntimeEnvironment(config)

	if not tok:
		runtime.editor.loop()
	
	sys.exit(runtime.editor.compile(tok))
	

if __name__ == "__main__":
	os.chdir(os.path.dirname(WPATH))
	try:
		main(len(sys.argv), sys.argv)
	except KeyboardInterrupt as k:
		pass
	except ConfigException as c:
		print 'Error:{}'.format(c)
		sys.exit(1)
