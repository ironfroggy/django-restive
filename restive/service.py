
from django.utils import simplejson as json
from django.core import serializers
from django.http import HttpResponse

from django.conf.urls.defaults import patterns
from django.conf import settings

import traceback

class NeverRaised(Exception): pass

class Service:
    def __init__(self, prefix = ''):
        self.url_list = []
        self.prefix = prefix

    def add(self, function=None, prefix='', name=None, urlparams=()):
        def actual_dec(function):
            def meta(request, **kwargs):
                try:
                    data = json.loads(getattr(request, request.method).get('data', '{}'))
                except KeyError:
                    res = {'error': 'invalid arguments [no "data" key]'}
                except:
                    res = {'error': 'invalid arguments [not JSON]'}
                else:
                    try:
                        data.update(kwargs)
                        res = function(request, **data)
                    except NeverRaised if settings.DEBUG else TypeError:
                        res = {'error':'invalid arguments '+str(data), 'tb':traceback.format_exc()}
                    except NeverRaised if settings.DEBUG else Exception,e:
                        res = {'error':str(e), 'tb':traceback.format_exc()}
                    else:
                        if not res.has_key('error'):
                            res['error'] = None
                if res.has_key('_models'):
                    res['_models'] = serializers.serialize('json', res['_models'], use_natural_keys=True)
                return HttpResponse(json.dumps(res))
            fname = name
            if fname is None:
                fname = function.__name__

            def append_url(optional_params):
                self.url_list.append(['^' + self.prefix + prefix + fname + optional_params + '/$', meta])
            append_url('')
            if urlparams:
                params = list(urlparams)
                for (i, (param_name, param_pattern)) in enumerate(params):
                    params[i] = param_pattern % (param_name,)
                for i in xrange(len(params)):
                    append_url('/'+'/'.join(params[:i+1]))

            return function
        if function is not None:
            return actual_dec(function)
        return actual_dec

    def urls(self):
        return patterns('', *self.url_list)

# vim: et sw=4 sts=4
