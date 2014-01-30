#!/usr/bin/python
#vim: set fileencoding=utf-8 :
from django import template


register = template.Library()


@register.filter
def object_id(o):
    """ the python unique object identifier, useful to get a unique ID"""
    return id(o)
