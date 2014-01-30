from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.base import TemplateView
from game.views import NewTribe

from django.contrib import admin
admin.autodiscover()

from dajaxice.core import dajaxice_autodiscover, dajaxice_config
dajaxice_autodiscover()

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='dolmen/landing.html')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
	url(r'^game/', include('game.urls', namespace='game')),
    #	url('^accounts/', include('registration.urls')),
    url(r'', include('social_auth.urls')),
	url(r'^creer_tribe/$', NewTribe.as_view()),
    url('^login/$', 'django.contrib.auth.views.login', name='login'),
    url('^logout/$', 'django.contrib.auth.views.logout', name='logout'),

    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),

    url(r'^api/', include('rest_framework.urls', namespace='rest_framework')),
)

#works only if settings.DEBUG is true
urlpatterns += staticfiles_urlpatterns()


#local media files
if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )
    
