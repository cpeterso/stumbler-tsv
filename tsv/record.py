from __future__ import absolute_import, division

# literal: http://stackoverflow.com/questions/3335268/are-object-literals-pythonic
# Record: https://github.com/pthatcher/pyrec/blob/master/Record.py
class Record(object):
    def __init__(self, **kwargs):
        object.__setattr__(self, '__dict__', kwargs)
    def __repr__(self):
        return 'record(%s)' % ', '.join('%s=%r' % i for i in sorted(self.__dict__.iteritems()))
    def __str__(self):
        return repr(self)
    def __setattr__(self, name, value):
        raise AttributeError('%s.__setattr__(%s)' % (self, name))
    def __delattr__(self, name):
        raise AttributeError('%s.__delattr__(%s)' % (self, name))
