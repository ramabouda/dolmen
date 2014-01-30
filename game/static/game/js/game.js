define([
    'jquery',
    "dajaxice",
    "angular",
    "./app",
    "./routes",
    "angular-route"
],        
function($, Dajaxice, angular){
      


    $(document).ready(function()
    {
    //    $('#current-resources .resource img').each(function()
    //        {
    //            $(this).listenTooltip({delay: 150})
    //        });

        angular.element().ready(function() {
            angular.bootstrap(document, ['gameApp']);
            console.log('Angular Bootstrapped');
        });

        $('.delete-report').click(function()
            {
                id = $(this).data('report-id');
                Dajaxice.game.delete_report(
                        function(arg){
                            if (arg.success)
                                $('#report-' + id).remove();
                            else
                                alert(arg.message);
                        },
                        {'report_id': id}
                    );
            }   
        );
        $('.mark-read-report').click(function()
            {
                id = $(this).data('report-id');
                Dajaxice.game.mark_read_report(
                        function(arg){
                            if (arg.success)
                                alert('marqué lu');
                            else
                                alert(arg.message);
                        },
                        {'report_id': id}
                    );
            }   
        );
        $('.mark-unread-report').click(function()
            {
                id = $(this).data('report-id');
                Dajaxice.game.mark_unread_report(
                        function(arg){
                            if (arg.success)
                                alert('marqué non lu');
                            else
                                alert(arg.message);
                        },
                        {'report_id': id}
                    );
            }   
        );
    
        $('#tribe-name').focusout(function(){
            Dajaxice.game.change_tribe_name(
                function(){},
                {'new_name': $(this).text()}
            )
        });
        $('#tribe-name').keypress(function(event){
            if (event.which == 13)
                $(this).blur();
        });
    
        $('#village-name').focusout(function()
                {
                Dajaxice.game.change_village_name(
                    function(){},
                    {'new_name': $(this).text()})
                });
        $('#village-name').keypress(function(event){
            if (event.which == 13)
                $(this).blur();
        });
        $('#select-session-village-btn').click(function()
                {
                    $.ajax({
                        url: "/game/choose_village/" + $('#select-session-village-select').val()
                    }).done(function(data)
                        {location.reload();}
                    ).fail(function(data){console.log("cheating you are, hum?")});
                });
    });
});

