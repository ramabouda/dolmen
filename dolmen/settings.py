 #!/usr/bin/python
#vim: set fileencoding=utf-8 :
import os.path
import djcelery
djcelery.setup_loader()

DEBUG = True
TEMPLATE_DEBUG = DEBUG
FAST_FORWARD = False
FAST_MOVES = False
FAST_BUILDING = False
FAST_RESEARCH = False

PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

ADMINS = (
	('Vincent', 'vincent.desprez@gmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'vincentdesprez_dolmen',                      # Or path to database file if using sqlite3.
        'USER': '29987_dolmen',                      # Not used with sqlite3.
        'PASSWORD': 'BlAd0lmen',                  # Not used with sqlite3.
        'HOST': 'mysql.alwaysdata.com',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}



# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Paris'
USE_TZ = True

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'fr-FR'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'public/site_media/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/site_media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_PATH, 'public/static/')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.	
    os.path.join(PROJECT_PATH, 'static/'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'dajaxice.finders.DajaxiceFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '@v^-++t@&r&@p#ehj9bo@o^!d25arbr9(d@2@%wso2ad#!52ys'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

INTERNAL_IPS = (
        '127.0.0.1',
		)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'dolmen.middleware.LoginRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    'game.middleware.PopulateSessionMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
		"django.core.context_processors.request",
		'django.contrib.auth.context_processors.auth',
		'django.core.context_processors.debug',
		'django.core.context_processors.static',
        #		'social_auth.context_processors.social_auth_by_name_backends',
        #'social_auth.context_processors.social_auth_backends',
        #'social_auth.context_processors.social_auth_by_type_backends',
		'game.context_processors.add_common_template_data',
		'django.contrib.messages.context_processors.messages'
	)

AUTHENTICATION_BACKENDS = (
        #		'social_auth.backends.twitter.TwitterBackend',
        #'social_auth.backends.facebook.FacebookBackend',
        'social_auth.backends.google.GoogleOAuthBackend',
        'social_auth.backends.google.GoogleOAuth2Backend',
        'social_auth.backends.google.GoogleBackend',
        #'social_auth.backends.yahoo.YahooBackend',
        #'social_auth.backends.contrib.orkut.OrkutBackend',
        #'social_auth.backends.OpenIDBackend',
		'django.contrib.auth.backends.ModelBackend',
		)

#AUTH_USER_MODEL = 'custom_user.EmailUser'

#Django social-auth 
TWITTER_CONSUMER_KEY         = ''
TWITTER_CONSUMER_SECRET      = ''
FACEBOOK_APP_ID              = ''
FACEBOOK_API_SECRET          = ''
ORKUT_CONSUMER_KEY           = ''
ORKUT_CONSUMER_SECRET        = ''
GOOGLE_CONSUMER_KEY          = ''
GOOGLE_CONSUMER_SECRET       = ''
GOOGLE_OAUTH2_CLIENT_ID      = ''
GOOGLE_OAUTH2_CLIENT_SECRET  = ''
INSTAGRAM_CLIENT_ID          = ''
INSTAGRAM_CLIENT_SECRET      = ''

OPENID_CREATE_USERS = True
OPENID_UPDATE_DETAILS_FROM_SREG = True

SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/game/view_map'
LOGIN_URL = '/login'
LOGIN_REDIRECT_URL = '/game/view_map'
LOGIN_ERROR_URL = '/'
LOGIN_EXEMPT_URLS = (r'^(?!game).*',)



#django-celery config
BROKER_URL = "amqp://"
CELERY_RESULT_BACKEND = "amqp"
CELERY_TASK_RESULT_EXPIRES = 300




DEBUG_TOOLBAR_CONFIG = {
		'INTERCEPT_REDIRECTS': False,
		}

#DEBUG_TOOLBAR_PANELS = (
        #'debug_toolbar.panels.version.VersionDebugPanel',
        #'debug_toolbar.panels.timer.TimerDebugPanel',
        #'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
        #'debug_toolbar.panels.headers.HeaderDebugPanel',
        #'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
        #'debug_toolbar.panels.template.TemplateDebugPanel',
        #'debug_toolbar.panels.sql.SQLDebugPanel',
        #'debug_toolbar.panels.signals.SignalDebugPanel',
        #'debug_toolbar.panels.logger.LoggingPanel',
        #'debug_toolbar.panels.profiling.ProfilingDebugPanel',
##        'template_timings_panel.panels.TemplateTimings.TemplateTimings',
        #)

ROOT_URLCONF = 'dolmen.urls'

TEMPLATE_DIRS = (
	os.path.join(PROJECT_PATH, 'templates/'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.webdesign',
    'django.contrib.humanize',
	'django_extensions',
	#'debug_toolbar',
#    'template_timings_panel',
    #'south',
    #'custom_user',

    'dajaxice',
    'rest_framework',

    'extra_views',
	'djcelery',

	'social_auth',
#	'registration',

    'game',
)


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse'
            }
        },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}


try:
	from local_settings import *
except:
	pass
