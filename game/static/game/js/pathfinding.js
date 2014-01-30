define(['jquery'], function($){

    var myPathFinding = {};

    // function found on developerfusion.com
    myPathFinding.MultiDimensionalArray = function(iRows,iCols) {
        var i;
        var j;
        var a = new Array(iRows);
        for (i=0; i < iRows; i++) {
            a[i] = new Array(iCols);
            for (j=0; j < iCols; j++) {
                a[i][j] = {'ground':-1, 'id':undefined};
            }
        }
        return(a);
    } 

    myPathFinding.constructArray = function(){
        temp = this.MultiDimensionalArray(11,11);
        tiles = document.getElementsByClassName('tile');
        for(i=0; i<tiles.length; i++)
        {
            tile = tiles[i];
            coord = [tile.dataset.x, tile.dataset.y];
            classes = tile.classList;
            temp[coord[0]][coord[1]] = {'ground':tile.dataset.ground, 'id': tile.dataset.id};    // should match for ground_x and therefore match[1] is the ground of the tile
        }
        return temp;
    }

    myPathFinding.hex_accessible = function(mapArray, x,y) {
        if(mapArray[x] == undefined) return false;
        if(mapArray[x][y] == undefined) return false;
        
        if(mapArray[x][y].ground == -1) return false;
        if(mapArray[x][y].ground == 3) return false;
        return true;
    }

    myPathFinding.hex_distance = function(x1,y1,x2,y2) {
        dx = Math.abs(x1-x2);
        dy = Math.abs(y2-y1);
        return Math.sqrt((dx*dx) + (dy*dy));
        //dx = Math.abs(x1-x2);
        //dy = Math.abs(y1-y2);
        //return dx + dy;
    }

    // A* Pathfinding with Manhatan Heuristics for Hexagons.
    myPathFinding.compute_path = function(mapArray, start_x, start_y, end_x, end_y) {
        // Check cases path is impossible from the start.
        var error=0;
        if(start_x == end_x && start_y == end_y) error=1;
        if(!this.hex_accessible(mapArray, start_x,start_y)) error=1;
        if(!this.hex_accessible(mapArray, end_x,end_y)) error=1;
        if(error==1) {
            //alert('Path is impossible to create.');
            return false;
        }
        
        mapsize_x = mapArray.length;
        mapsize_y = mapArray[0].length;
        // Init
        var openlist = new Array(mapsize_x*mapsize_y+2);
        var openlist_x = new Array(mapsize_x);
        var openlist_y = new Array(mapsize_y);
        var statelist = this.MultiDimensionalArray(mapsize_x+1,mapsize_y+1); // current open or closed state
        var openlist_g = this.MultiDimensionalArray(mapsize_x+1,mapsize_y+1);
        var openlist_f = this.MultiDimensionalArray(mapsize_x+1,mapsize_y+1);
        var openlist_h = this.MultiDimensionalArray(mapsize_x+1,mapsize_y+1);
        var parent_x = this.MultiDimensionalArray(mapsize_x+1,mapsize_y+1);
        var parent_y = this.MultiDimensionalArray(mapsize_x+1,mapsize_y+1);
        var path = Array();

        var select_x = 0;
        var select_y = 0;
        var node_x = 0;
        var node_y = 0;
        var counter = 1; // Openlist_ID counter
        var selected_id = 0; // Actual Openlist ID
        
        // Add start coordinates to openlist.
        openlist[1] = true;
        openlist_x[1] = start_x;
        openlist_y[1] = start_y;
        openlist_f[start_x][start_y] = 0;
        openlist_h[start_x][start_y] = 0;
        openlist_g[start_x][start_y] = 0;
        statelist[start_x][start_y] = true; 
        
        // Try to find the path until the target coordinate is found
        while (statelist[end_x][end_y] != true) {
            set_first = true;
            // Find lowest F in openlist
            for (var i in openlist) {
                if(openlist[i] == true){
                    select_x = openlist_x[i]; 
                    select_y = openlist_y[i]; 
                    if(set_first == true) {
                        lowest_found = openlist_f[select_x][select_y];
                        set_first = false;
                    }
                    if (openlist_f[select_x][select_y] <= lowest_found) {
                        lowest_found = openlist_f[select_x][select_y];
                        lowest_x = openlist_x[i];
                        lowest_y = openlist_y[i];
                        selected_id = i;
                    }
                }
            }
            if(set_first==true) {
                // open_list is empty
                alert('No possible route can be found.');
                return false;
            }
        // add it lowest F as closed to the statelist and remove from openlist
            statelist[lowest_x][lowest_y] = 2;
            openlist[selected_id]= false;
            // Add connected nodes to the openlist
            for(i=1;i<7;i++) {
                // Run node update for 6 neighbouring tiles.
                switch(i){
                    case 1:
                        node_x = lowest_x-1;
                        node_y = lowest_y;                      
                    break;
                    case 2:
                        node_x = lowest_x;
                        node_y = lowest_y-1;                        
                    break;
                  case 3:
                        node_x = lowest_x+1;
                        node_y = lowest_y-1;                        
                    break;
                    case 4:
                        node_x = lowest_x+1;
                        node_y = lowest_y;                      
                    break;
                    case 5:
                        node_x = lowest_x;
                        node_y = lowest_y+1;
                    break;
                    case 6:
                        node_x = lowest_x-1;
                        node_y = lowest_y+1;
                    break;
                }
              if (this.hex_accessible(mapArray, [node_x],[node_y])) {
                  if(statelist[node_x][node_y] == true) {
                    if(openlist_g[node_x][node_y] < openlist_g[lowest_x][lowest_y]) {
                        parent_x[lowest_x][lowest_y] = node_x;
                          parent_y[lowest_x][lowest_y] = node_y;
                          openlist_g[lowest_x][lowest_y] = openlist_g[node_x][node_y] + 10;
                          openlist_f[lowest_x][lowest_y] = openlist_g[lowest_x][lowest_y] + openlist_h[lowest_x][lowest_y];
                      }
                  } else if (statelist[node_x][node_y] == 2) {
                      // its on closed list do nothing.
                  } else {
                      counter++;
                      // add to open list
                      openlist[counter] = true;
                      openlist_x[counter] = node_x;
                      openlist_y[counter] = node_y;
                      statelist[node_x][node_y] = true;
                      // Set parent
                      parent_x[node_x][node_y] = lowest_x;
                      parent_y[node_x][node_y] = lowest_y;
                      // update H , G and F
                      var ydist = end_y - node_y;
                      if ( ydist < 0 ) ydist = ydist*-1;
                      var xdist = end_x - node_x;
                      if ( xdist < 0 ) xdist = xdist*-1;        
                      openlist_h[node_x][node_y] = this.hex_distance(node_x,node_y,end_x,end_y) * 10;
                      openlist_g[node_x][node_y] = openlist_g[lowest_x][lowest_y] + 10;
                      openlist_f[node_x][node_y] = openlist_g[node_x][node_y] + openlist_h[node_x][node_y];
                    }
              }
            }
        }
        
        // Get Path
        temp_x=end_x;
        temp_y=end_y;
        while(temp_x != start_x || temp_y != start_y) {
            path.push(parseInt(mapArray[temp_x][temp_y].id));
            temp = temp_x;
            temp_x = parent_x[temp_x][temp_y];
            temp_y = parent_y[temp][temp_y];
        }
        path.push(parseInt(mapArray[temp_x][temp_y].id));
        
        // Draw path.
        return path.reverse();
    }   

    myPathFinding.draw_path = function(path)
    {
        for(i=0; i<path.length; i++){
            if(path[i].ground != -1 ){
               $('#tile_' + path[i]).addClass('in_path');
            }
        }
    }

    var coord_group;

    myPathFinding.show_path = function(mapArray, coord_group, to_x, to_y)
    {
        path = this.compute_path(
                mapArray,
                parseInt(coord_group[0]),
                parseInt(coord_group[1]),
                parseInt(to_x), 
                parseInt(to_y)
                );
        this.draw_path(path);
    }

    return myPathFinding;
});


