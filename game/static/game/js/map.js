require([
    'jquery', 
    'dajaxice', 
    './game/js/pathfinding',
    'bootstrap'
], function(
    $, 
    Dajaxice, 
    PathFinding
){

    ///////// POPUP MENU ACTIONS
    
    /*
    This object represents a tile zoomed in.
    */
    var TileDetails = (function () {
        var constructor = function(tile_id){
            that = this;             //context accessible everywhere
            this.tile_id = tile_id;
            
            //Ajax request to get the tile and display it
            this.get_tile = function(tile_id){
                if (this.tile_id == undefined) {
                    this.tile_id = tile_id;
                }
                $('#tile-details').show();
                Dajaxice.game.tile_details_request(
                    (function(ctx){         //closure to transmit the object context
                        return function(arg){
                            ctx.show_details(arg.html);
                            ctx.watch_details_events();
                        }
                    })(that),
                    {'tile_id': tile_id}
                );
            }
            
            this.show_details = function(html) {
                $('#tile-details').html(html);
                $('#map').hide();
            }
            
            this.watch_details_events = function() {
                //close button
                $('#tile-details .close-button').click(function(){
                    $('#tile-details').html('');
                    $('#map').show();
                });
                //set popovers
                $('.default_popover').popover({html: true});
            }
        }    
        return constructor;
    })();



    //highlight the selected group
    function highlight_selected()
    {
        try {
            $('.tile .detail.group').attr('src', $('.tile .detail.group').attr('src').replace('_selected', ''));
        } catch (error) {}
        coord_group = [$('#selected_group').data('x'), $('#selected_group').data('y')]
        tile = $(".tile[data-x=" + coord_group[0] + "][data-y=" + coord_group[1] + "]");
        tile.children('img').attr('src', tile.children('img').attr('src').replace('group_small', 'group_small_selected'));
    }

    //start mission
    function start_mission(tile_id, type) {
        group_id = $('#selected_group').data('id');
        args = {
            'group_id': group_id,
            'path': JSON.stringify(path),
            'mission_type':type
        };
        split_form = $('#split-group-form');
        if (split_form.length != 0) {
            var split_array = {};
            inputs = split_form.find('input[type=range]');
            inputs.each(function(){
                $this = $(this)
                split_array[$this.data('unit-id')] = $this.val()
            })
            args['split_group'] = JSON.stringify(split_array);
        }
        switch (type)   
        {
            case 'move':
                break;

            case 'gather':
                break;

            case 'annex':
                //todo
                args['target_id'] = $(this).data('village-id');
                break;

            case 'carry':
                //TODO
                break;

            case 'loot':
                //TODO
                break;

            case 'attack':
                //todo
                args['target_id'] = $(this).data('group-id');
                break;

        }
        Dajaxice.game.mission_request(
            function(arg){console.log(arg); alert(arg.message)},
            args
        );
    }



    ////////// EVENT HANDLERS ///////////

    $(document).ready(function()
    {
        //pathfinding setup
        var tile_menu_open = false;
        var action_name;
        function enable_pathfinding(){ tile_menu_open = false }
        function lock_pathfinding(){ tile_menu_open = true }
        mapArray = PathFinding.constructArray();
        
        //set popovers
        $('.default_popover').popover({html: true});
                
        //groups
        $($('#groups-overview .group-list li')[0]).attr('id', 'selected_group');
        highlight_selected();
        $('#groups-overview .group-list li').click(function()
            {
                $('.in_path').removeClass('in_path');
                $('#selected_group').attr('id', '');
                $(this).attr('id', 'selected_group');
                highlight_selected();
            });
        
        //tiles hover effect
        $('.tile').hover(function(){
            set_path($(this));
        });
        
        //hightlight on the map the path to the tile
        function set_path(img) {
            if (!tile_menu_open){
                coord_group = [$('#selected_group').data('x'), $('#selected_group').data('y')]
                coord_to = [img.data('x'), img.data('y')];
                $('.in_path').removeClass('in_path');
                PathFinding.show_path(mapArray, coord_group, coord_to[0], coord_to[1]);
            }
        }
       
        
        //set popover and build popups for the map
        $('.tile.has_popover').each(
            function(){
                var tile_id = $(this).data('id');
                var popup_content = $('<div>', { 'class': "tile-menu"});
                var ul = $('<ul>', {'class':'action-list'});
                $('menu ul li', $(this)).each(
                    function() {
                        var mission_name = $(this).text();
                        ul.append(
                            $('<li>', {
                                'data-mission-type': mission_name,                            
                            })
                            .append($('<a>', {'href' : '#'})
                                .append(mission_name)
                            )
                        );
                    }
                );
                popup_content.append(ul);
                
                btn = $('<button class="split_group_btn">Choisir les unités</button>');
                popup_content.append(btn);
                
                $(this).popover({
                    content: popup_content.prop('outerHTML'),
                    html: true,
                    onShow : function(){
                        setTimeout(lock_pathfinding, 50);
                    },
                    onHide : enable_pathfinding
                });
                
            }
        );
        $('body').on('click', '.popover .split_group_btn', create_group_split);
        
        
        
        //handles popup content events
        popup_actions_functions = {
            'inspect': (new TileDetails()).get_tile,
            'move' : start_mission,
            'gather' : start_mission
        }
        for (action_name in popup_actions_functions) {
            var local_callback = function(action_name){
                return function() {
                    $(this).parents(".popover").prev().popover('hide');
                    popup_actions_functions[action_name]($(this).parents(".popover").prev().data('id'), action_name);
                }
            }
            $('body').delegate('li[data-mission-type='+ action_name +']', 'click', local_callback(action_name));
        }
        
        
        
    });


    //create the form to split a group from the current group and add it to the popup
    function create_group_split() {
        var $this = $(this)
        if($this.next('.split_group').length > 0){
            $this.next('.split_group').remove()
        }
        else{
            var popover = $this.parents('.popover');
            var height = parseInt($this.parents('.popover').css('height'));
            var units = $('#selected_group .unitstack').clone()
            //add range input
            units.each(function(){
                var $this = $(this)
                var number = $this.find('.number').text()
                var unit_type_id = $this.data('unit_type_id')
                var input = $('<input type="range" name="split-'+unit_type_id+'" min="0" step="1" max="'+number+'" value="'+number+'" data-unit-id="'+unit_type_id+'" />')
                //watch range input changes
                input.on('change', function(){
                    var unit = $(this).parent('.unitstack')
                    var number = unit.find('.number')
                    number.html(unit.find('input[type=range]').val() +'/'+ number.text().split('/')[1])
                })
                $this.append(input)
            })
            //complete unit number indicatorre
            units.find('.number').each(function(){
                var $this = $(this)
                $this.html($this.text() +'/'+ $this.text())
            })
            //gather content
            var html = $('<form id="split-group-form"></form>').append(units)
            var div = $('<div class="split_group"></div>').append(html);
            $this.after(div);
            $this.parents('.popover').find('.arrow').css('top', height/2 + "px");
        }
        
    }

});