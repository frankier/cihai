# -*- coding: utf8 - *-
"""Cihai client object."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals, with_statement)

import argparse
import logging
import os

import kaptan
from sqlalchemy import create_engine

from cihai import db, exc
from cihai.util import merge_dict
from cihai.conf import default_config, expand_config

log = logging.getLogger(__name__)


class Cihai(object):

    """Cihai query client. May use :meth:`~.get()` to grab 中文.

    Cihai object is inspired by `pypa/warehouse`_ Warehouse applicaton object.

    .. _pypa/warehouse: https://github.com/pypa/warehouse

    """

    def __init__(self, config, engine=None):

        #: configuration dictionary. Available as attributes. ``.config.debug``
        self.config = merge_dict(default_config(), config)

        #: Expand template variables
        expand_config(self.config)

        #: absolute path to cihai data files.
        if 'data_path' not in self.config:
            self.config['data_path'] = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 'data/'
            ))

        if engine is None and self.config['database']['url']:
            engine = create_engine(self.config['database']['url'])
        #: :class:`sqlalchemy.engine.Engine` instance.
        self.engine = engine

        #: :class:`sqlalchemy.schema.MetaData` instance.
        self.metadata = db.metadata
        self.metadata.bind = self.engine

    @classmethod
    def from_file(cls, config_path=None, *args, **kwargs):
        """Create a Cihai instance from a JSON or YAML config.

        :param config_path: path to custom config file
        :type confiig_path: str
        :rtype: :class:`Cihai`

        """

        config_reader = kaptan.Kaptan()

        config = {}

        if config_path:
            if not os.path.exists(config_path):
                raise exc.CihaiException(
                    '{0} does not exist.'.format(os.path.abspath(config_path)))
            if not any(
                config_path.endswith(ext) for ext in
                ('json', 'yml', 'yaml', 'ini')
            ):
                raise exc.CihaiException(
                    '{0} does not have a yaml,yml,json,ini extension.'
                    .format(os.path.abspath(config_path))
                )
            else:
                custom_config = config_reader.import_config(config_path).get()
                config = merge_dict(config, custom_config)

        return cls(config)

    @classmethod
    def from_cli(cls, argv):
        """Cihai from :py:class:`argparse` / CLI args.

        :param argv: list of arguments, i.e. ``['-c', 'dev/config.yml']``.
        :type argv: list
        :rtype: :class:`Cihai`

        """
        parser = argparse.ArgumentParser(prog="cihai")
        parser.add_argument("-c", "--config", dest="_config")

        args = parser.parse_args(argv)
        if not args._config:
            parser.print_help()
        else:
            config = args._config if args._config is not None else {}
            return cls.from_file(config)
