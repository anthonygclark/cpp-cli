import ConfigParser
import sys
import os

""" 
ConfigParser wrapper providing error messages, 
simpler nomenclature and overrides. While it 
can technically just be used as an argv parser
it is meant to be used with a config file.
"""

# Simple config file error handler. Sometimes, this just
# wraps ConfigParser exceptions
class ConfigException(Exception):
	def __init__(self, err_code=0, arg=''):
		self.err_code	= err_code
		self.arg		= arg
		self.err_str	= self.get_err()

	def get_err(self):
		return { 1: "Error 1: Config File Not Found:",
				 2: "Error 2: Config File Cannot Be Correctly Parsed:",
				 3: "Error 3: Section Not Found:",
				 4: "Error 4: Mismatched arguments.",
				 5: "Error 5: Option Not Found:",
				 6: "Error 6: Cannot parse using mode: ",
				 7: "Error 7: Unsupported type for overrides: ",
			   }.get(self.err_code, "")
   
	def __str__(self):
		return '%s %s' % (self.err_str, self.arg)


# Note: `switches` is for options without args. These must be parsed manually
class Config(object, ConfigParser.ConfigParser):

	CONFIG_REG	 = 0x01 # Regular: Single argument
	CONFIG_CSV	 = 0x02 # CSV	 : Comma seperated
	CONFIG_COSV  = 0x04 # COSV	 : Colon seperated
	CONFIG_SSV	 = 0x08 # SSV	 : Space Seperated

	def __init__(self, fname, section=None):
		# Super
		ConfigParser.RawConfigParser.__init__(self, allow_no_value=True)
		self._configfile 	= fname
		self._overrides		= []

		try:
			self.readfp(open(self._configfile))
		except IOError as e:
			raise ConfigException(arg=e)
		except ConfigParser.ParsingError as err:
			raise ConfigException(2, self._configfile)

		# open the first section unless a section is provided
		try:
			self._section = section or self.sections()[0] 
		except IndexError:
			self._section = None


	""" Properties """
	@property
	def section(self):
		return self._section

	@section.setter
	def section(self, val):
		if self.has_section(val):
			self._section = val
		else:
			raise ConfigException(3, self._configfile)

	@property
	def overrides(self):
		return self._overrides

	@overrides.setter
	def overrides(self, val):
		self._overrides = self._create_overrides_dict(val)


	""" Initializes a Config object against a new file 
		Warning, this is destructive
	"""
	@classmethod
	def newConfig(cls, fname, section):
		with open(fname, 'w') as config: 
			config.write('[%s]\n' % section)
		return cls(fname, section)


	""" Initializes a Config that handles overrides from sys.argv """
	@classmethod
	def applicationConfig(cls, fname, ignore=[]):
		# think of ignore as switches, like -h for help
		_inst = cls(fname)
		_inst.overrides = filter(lambda ov: ov not in ignore, sys.argv[1:])
		return _inst


	""" Converts provided overrides into dict """
	def _create_overrides_dict(self, overrides):
		_split = lambda x: x.split('=')
		result = {}
		values = ()

		# for lists, we want --opt=arg, to be able to know which option
		# belongs where.
		if type(overrides) is list:
			try:
				values = [(i,k) for i,k in map(_split, overrides)]
			except:
				raise ConfigException(4)

		# For dicts, we basically proceed to parsing
		elif type(overrides) is dict:
			values = overrides.items()
		else:
			raise ConfigException(7, type(overrides))
			return None

		# Parse / create override dict
		for key,val in values:
			if key.startswith('--'):
				result[key[2:]] = val
			else:
				result[key] = val
		
		return result


	""" Returns dict of all of the available options in the current section """
	# TODO doesnt parse overrides
	def get_all_options(self, sect=None):
		if not sect:
			return dict(self.items(self.section))
		if not self.has_section(sect):
			raise ConfigException(3, self._configfile)
		return dict(self.items(sect))

	
	""" Changes a config value """
	def set_option(self, opt, val, section=None):
		if not section:
			self.set(self.section, opt, str(val)) 
		else:
			self.set(section, opt, str(val))
	

	""" Writes the modified config object to a file """
	def save_config(self, output_file=None):
		if not output_file: 
			output_file = self._configfile
		
		with open(output_file, 'wb') as outf:
			self.write(outf)

	
	""" Changes the section """
	def change_section(self, section):
		if self.has_section(section):
			self.section = section
		else:
			raise ConfigException(3, self._configfile)


	""" Internal method for parsing a line based on mode """
	def _value_parse(self, mode, conf_value):
		if mode & self.CONFIG_REG:
			return conf_value
		elif mode & self.CONFIG_CSV:
			conf_value = conf_value.split(',')
		elif mode & self.CONFIG_COSV:
			conf_value = conf_value.split(':')
		elif mode & self.CONFIG_SSV:
			conf_value = conf_value.split(' ')
		else:
			raise ConfigException(6, mode)

		return conf_value


	""" Retrieves option from the config file. """
	def get_option(self, opt, mode=CONFIG_REG):
		# Attempt to get option from the config file using the
		# appropriate parser. 
		try:
			# Attempt to get the option from overrides first
			if self._overrides and opt in self._overrides: 
				conf_value = self._overrides[opt] 
			else:
				conf_value = self.get(self.section, opt)

			# Parse the value 
			return self._value_parse(mode, conf_value)
		
		except ConfigParser.NoOptionError as err:
			raise ConfigException(5, opt)


	""" Helper for printing overridable options"""
	def print_overrides_for_help(self):
		# Dont do anything for empty config or if the first
		# section is blank
		if not len(self.sections()) or not len(self.items(self.sections()[0])):
			return

		print 'config file overrides:'
		for sect in self.sections():
			# Dont print empty sections
			if len(self.items(sect)):
				for key,value in self.get_all_options(sect).items():
					print '  --%s = %s' % (key, value)
	

	""" String representation """
	def __repr__(self):
		return 'Config File: %s, Current Section: %s' % (self._configfile,self.section)
