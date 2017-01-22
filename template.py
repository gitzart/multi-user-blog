"""template.py: Jinja2 template system settings and function definitions."""


__author__ = 'Alan'
__copyright__ = 'Copyright 2017, Multi User Project'


import os
import time

import jinja2

from webapp2 import uri_for
from markdown import markdown


DIR_NAME = 'templates'
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), DIR_NAME)

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATE_DIR), autoescape=True,
)
env.lstrip_blocks = True,
env.trim_blocks = True


# Datetime formatting
def datetime_format(dt, format='%d %b, %y'):
    return dt.strftime(format)


# REVIEW: Could be created as a function rather than a filter.
def get_url(target, *args, **kwargs):
    """Build the URL for the target endpoint."""
    return uri_for(str(target), *args, **kwargs)


# TODO: Extend the Markdown features.
def convert_md(md):
    """Convert the Markdown to normal HTML text."""
    return jinja2.Markup(markdown(md))


env.filters['dtf'] = datetime_format
env.filters['url'] = get_url
env.filters['mdf'] = convert_md
