require([
	'../../../dolmen/js/config'
], function(config){
    path = "game/js/";
	require(['app.common', path+'game', path+'map']);
});