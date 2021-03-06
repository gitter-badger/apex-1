"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mapex` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``apex.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``apex.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

# These imports are for python3 compatability inside python2
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import signal
import sys
import threading
import time
import traceback
import cachetools
import click

import apex.aprs
from apex.kiss import constants as kissConstants
from apex.pluginloader import getPlugins
from apex.pluginloader import loadPlugin

if sys.version_info < (3, 0):
    import ConfigParser  # noqa: F401
elif sys.version_info >= (3, 0):
    import configparser

__author__ = 'Jeffrey Phillips Freeman (WI2ARD)'
__maintainer__ = "Jeffrey Phillips Freeman (WI2ARD)"
__email__ = "jeffrey.freeman@syncleus.com"
__license__ = 'Apache License, Version 2.0'
__copyright__ = 'Copyright 2016, Syncleus, Inc. and contributors'
__credits__ = []


def find_config(config_paths, verbose):
    config_file = 'apex.conf'
    rc_file = '.apexrc'
    cur_path = os.path.join(os.curdir, config_file)
    home_path = os.path.join(os.path.expanduser("~"), rc_file)
    etc_path = os.path.join('etc', config_file)
    if config_paths is None:
        config_paths = [cur_path, home_path, etc_path]
    elif isinstance(config_paths, str):
        config_paths = [config_paths]
    elif not isinstance(config_paths, list):
        raise TypeError('config_paths argument was neither a string nor a list')

    if verbose:
        click.echo('Searching for configuration file in the following locations: %s' % repr(config_paths))

    config = configparser.ConfigParser()
    for config_path in config_paths:
        try:
            if len(config.read(config_path)) > 0:
                return config
        except IOError:
            pass

    return None


@click.command(context_settings=dict(auto_envvar_prefix='APEX'))
@click.option('-c',
              '--configfile',
              type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True, resolve_path=True),
              help='Configuration file for APEX.')
@click.option('-v', '--verbose', is_flag=True, help='Enables verbose mode.')
def main(verbose, configfile):

    port_map = {}
    config = find_config(configfile, verbose)
    if config is None:
        click.echo(click.style('Error: ', fg='red', bold=True, blink=True) +
                   click.style('No apex configuration found, can not continue.', bold=True))
        return
    for section in config.sections():
        if section.startswith("TNC "):
            tnc_name = section.split(" ")[1]
            if config.has_option(section, 'com_port') and config.has_option(section, 'baud'):
                com_port = config.get(section, 'com_port')
                baud = config.get(section, 'baud')
                kiss_tnc = apex.aprs.AprsKiss(com_port=com_port, baud=baud)
            elif config.has_option(section, 'tcp_host') and config.has_option(section, 'tcp_port'):
                tcp_host = config.get(section, 'tcp_host')
                tcp_port = config.get(section, 'tcp_port')
                kiss_tnc = apex.aprs.AprsKiss(host=tcp_host, tcp_port=tcp_port)
            else:
                click.echo(click.style('Error: ', fg='red', bold=True, blink=True) +
                           click.style("""Invalid configuration, must have both com_port and baud set or tcp_host and
                           tcp_port set in TNC sections of configuration file""", bold=True))
                return

            if not config.has_option(section, 'kiss_init'):
                click.echo(click.style('Error: ', fg='red', bold=True, blink=True) +
                           click.style("""Invalid configuration, must have kiss_init set in TNC sections of
                           configuration file""", bold=True))
                return
            kiss_init_string = config.get(section, 'kiss_init')
            if kiss_init_string == 'MODE_INIT_W8DED':
                kiss_tnc.start(kissConstants.MODE_INIT_W8DED)
            elif kiss_init_string == 'MODE_INIT_KENWOOD_D710':
                kiss_tnc.start(kissConstants.MODE_INIT_KENWOOD_D710)
            elif kiss_init_string == 'NONE':
                kiss_tnc.start()
            else:
                click.echo(click.style('Error: ', fg='red', bold=True, blink=True) +
                           click.style('Invalid configuration, value assigned to kiss_init was not recognized: %s'
                                       % kiss_init_string, bold=True))
                return
            for port in range(1, 1 + int(config.get(section, 'port_count'))):
                port_name = tnc_name + '-' + str(port)
                port_section = 'PORT ' + port_name
                port_identifier = config.get(port_section, 'identifier')
                port_net = config.get(port_section, 'net')
                tnc_port = int(config.get(port_section, 'tnc_port'))
                port_map[port_name] = {'identifier': port_identifier, 'net': port_net, 'tnc': kiss_tnc,
                                       'tnc_port': tnc_port}
    if config.has_section('APRS-IS'):
        aprsis_callsign = config.get('APRS-IS', 'callsign')
        if config.has_option('APRS-IS', 'password'):
            aprsis_password = config.get('APRS-IS', 'password')
        else:
            aprsis_password = -1
        aprsis_server = config.get('APRS-IS', 'server')
        aprsis_server_port = config.get('APRS-IS', 'server_port')
        aprsis = apex.aprs.AprsInternetService(aprsis_callsign, aprsis_password)
        aprsis.connect(aprsis_server, int(aprsis_server_port))

    def sigint_handler(signal, frame):
        for port in port_map.values():
            port['tnc'].close()
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)

    click.echo("Press ctrl + c at any time to exit")

    packet_cache = cachetools.TTLCache(10000, 5)
    # start the plugins
    plugins = []
    try:
        plugin_loaders = getPlugins()
        for plugin_loader in plugin_loaders:
            loaded_plugin = loadPlugin(plugin_loader)
            plugins.append(loaded_plugin)
            threading.Thread(target=loaded_plugin.start, args=(config, port_map, packet_cache, aprsis)).start()
    except IOError:
        click.echo(click.style('Error: ', fg='red', bold=True, blink=True) +
                   click.style('plugin directory not found, this program has nothing to do.', bold=True))
        return

    while 1:
        something_read = False
        try:
            for port_name in port_map.keys():
                port = port_map[port_name]
                frame = port['tnc'].read()
                if frame:
                    formatted_aprs = apex.aprs.util.format_aprs_frame(frame)
                    print(port_name + " << " + formatted_aprs)
                    for plugin in plugins:
                        something_read = True
                        plugin.handle_packet(frame, port, port_name)
        except Exception as ex:
            # We want to keep this thread alive so long as the application runs.
            traceback.print_exc(file=sys.stdout)
            click.echo("caught exception while reading packet: " + str(ex))

        if something_read is False:
            time.sleep(1)
