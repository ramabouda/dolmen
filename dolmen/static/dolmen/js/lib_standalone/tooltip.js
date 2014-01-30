/**
Function to call to have a tip on a jQuery object
options{delay (in ms), content, className)
You can use the attribute data-tip to define a default content
//TODO dontMove option
 */
function listenTooltip(jQueryObject, options){
	if(typeof(options)==='undefined') options = {};
	if(options.content == undefined)
		options.content = jQueryObject.data().tip;
    jQueryObject.hover(
		function(){tip(options);},
        tipHide
    );
}

$.fn.listenTooltip = function(options) { listenTooltip(this, options)};


//----------------------------------------------------------

temps = null;

//Handle the tip options, see listenTooltip()
function tip(o){
    if(o.delay != 'undefined' && o.delay != 0){
        temps = setTimeout(
            function(){
				optionsInstant = new cloneObject(o);
				optionsInstant.delay = 0;
				tip(optionsInstant);
			}
            , o.delay
        );
    }
    else{
		className = 'classic';
		if(o.hasOwnProperty(className))
			className = o.className;
		content = '<div class="'+ className +'">'+ o.content +'</div>'
        enableTip(content);
	}
}


function tipHide(){
	clearTimeout(temps);
	disableTip();
}

function cloneObject(source) {
    for (i in source) {
        if (typeof source[i] == 'source') {
            this[i] = new cloneObject(source[i]);
        }
        else{
            this[i] = source[i];
	}
    }
}


var offsetxpoint=15 //Customize x offset of tooltip
var offsetypoint=10 //Customize y offset of tooltip
var enabletip=false
$(document).ready(function(){
    if($('#tip').length==0)
        $('body').append('<div id="tip"></div>');
    tipobj = $('#tip');
    $(document).mousemove(function(e){positiontip(e)});
})

//Function to call to display the tooltip
function enableTip(thetext){  
    tipobj.html(thetext);
    enabletip=true;
	
}

function positiontip(e){
    if (enabletip){
        var curX=e.pageX;
        var curY=e.pageY;
        //Find out how close the mouse is to the corner of the window
        var rightedge= $(window).width() - curX - offsetxpoint;
        var bottomedge= $(window).height() - curY - offsetypoint;
        
        var leftedge=(offsetxpoint<0)? offsetxpoint*(-1) : -1000
        
        //if the horizontal distance isn't enough to accomodate the width of the context menu
        if (rightedge<tipobj.offsetWidth)
        //move the horizontal position of the menu to the left by it's width
            tipobj.css('left', window.pageXOffset +  curX - tipobj.offsetWidth+"px");
        else if (curX<leftedge)
            tipobj.css('left', "5px");
        else
        //position the horizontal position of the menu where the mouse is positioned
            tipobj.css('left', curX+offsetxpoint+"px");
        
        //same concept with the vertical position
        if (bottomedge < tipobj.offsetHeight)
            tipobj.css('top', window.pageYOffset + curY - tipobj.offsetHeight - offsetypoint+"px");
        else
            tipobj.css('top', curY+offsetypoint+"px");
            tipobj.css('visibility', "visible");
    }
}

function disableTip(){
    enabletip=false
    tipobj.css('visibility', "hidden");
    tipobj.css('left', "-1000px");
}



