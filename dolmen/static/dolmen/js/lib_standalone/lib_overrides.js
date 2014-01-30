/******************************************************
 *
 * Add properties to some libs
 *
 ********************************************************/

require([
    'jquery',
    'bootstrap'
],        
function($){
        
    //Add the callback option to popover
    var tmp = $.fn.popover.Constructor.prototype.show;
    $.fn.popover.Constructor.prototype.show = function () {
        if (this.options.onShow) { this.options.onShow(); }
        tmp.call(this);
    };
    
    var tmp2 = $.fn.popover.Constructor.prototype.hide;
    $.fn.popover.Constructor.prototype.hide = function () {
        tmp2.call(this);
        if (this.options.onHide) { this.options.onHide(); }
    };
    
    //popover content in the next html element
    var parentGetContent = $.fn.popover.Constructor.prototype.getContent;
    $.fn.popover.Constructor.prototype.getContent = function () {
        var next = this.$element.next();
        if (next.hasClass('popover-content')) {
            return next.html();
        }
        return parentGetContent.call(this);
    };
});