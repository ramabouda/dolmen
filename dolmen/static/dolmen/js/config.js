

var dolmen = "dolmen/js/"; //can be used to have several baseURL

require.config({
	paths: {
		"angular-mocks": dolmen+"lib/angular-mocks/angular-mocks",
		"angular-route": dolmen+"lib/angular-route/angular-route",
		"angular-sanitize": dolmen+"lib/angular-sanitize/angular-sanitize",
		"angular": dolmen+"lib/angular/angular",
		"angularAMD": dolmen+"lib/angularAMD/angularAMD",
		"angular-scenario": dolmen+"lib/angular-scenario/angular-scenario",
		"jquery": dolmen+"lib/jquery/jquery",
		"bootstrap": dolmen+"lib/bootstrap/docs/assets/js/bootstrap",
		"requirejs-text": dolmen+"lib/requirejs-text/text",
		"less" : dolmen+"lib/less/dist/less-1.4.2",
		"lib_overrides" : dolmen+"lib_standalone/lib_overrides",
		"dajaxice" : dolmen+"lib_standalone/dajaxice.core",
		
		"app.common" : dolmen+"app/common"
	},
	baseUrl: '/static/',
	shim: {
		'angular' : {'exports' : 'angular'},
		'angular-route': ['angular'],
		'angular-mocks': ['angular'],
		'angular-sanitize': ['angular'],
		'angularAMD': ['angular'],
		"bootstrap": ['jquery']
	},
	priority: [
		"angular"
	],
	urlArgs: 'v=0.1'
});

