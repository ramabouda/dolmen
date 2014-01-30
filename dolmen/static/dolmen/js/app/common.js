require([
    'jquery',
    "less",
    "bootstrap",
	"lib_overrides"
], function($) {
	'use strict';
    
    // Bind custom hide function when clicking outside the popover
    $('html').on('click.popover.data-api', hide_popover);
    $('html .popover ul.action-list a').on('click', hide_popover);
    //hide on escape key
    $(document).keyup(function(e){
        if (e.keyCode == 27){
            hide_popover(e);
        }
    })
    
    //hide all the popover having the css class .has_popover, except if the click is inside the popover
    function hide_popover(e) {
        if($(e.target).closest('.popover').length == 0){
            $('.has_popover').each(function () {
                //if has_popover or what is inside is not clicked
                //if is not the popup itself
                if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
                    var popover = $(this).data('popover');
                    var shown = popover && popover.tip().is(':visible');
                    if(shown) {
                        $(this).popover('hide');
                        enable_pathfinding();
                        set_path($(e.target))
                    }
                }
            });
            return true;
        }
        else {return false;}
    }
    
    
 
});
