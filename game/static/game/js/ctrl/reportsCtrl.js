define([
	"./module",
    'jquery',
    "dajaxice",
    "angular",
    "angular-route"
],        
function(controllers, $, Dajaxice, angular){

	//var reportsCtrl = angular.module('reportsCtrl', []);
	 
	controllers.controller('ReportsListCtrl', ['$scope', '$http',
	  function ($scope, $http) {
	    $http.get('api/reports').success(function(data) {
	      $scope.reports = data;
	    });
	 

        console.log('DO STUFF');
	  }]);
	 
/*	reportsCtrl.controller('PhoneDetailCtrl', ['$scope', '$routeParams',
	  function($scope, $routeParams) {
	    $scope.phoneId = $routeParams.phoneId;
	  }]);*/
	
	//return reportsCtrl;
});