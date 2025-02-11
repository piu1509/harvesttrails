$(document).ready(function(){
  $("#uploadbtn").click(function(){

    var flag = 0
    if ($("#growerSelect").val() == null){
        $("#msg").text("Select Grower name");

        $("#growerSelect").css('color', '#dc3545');
        flag +=1
    }
    else{
        $("#growerSelect").css('color', 'black');
        };

        $( ".map" ).each(function( index ) {

            if ($(this).val() == null){
                $(this).css('color','#dc3545');
                flag +=1
            }
            else{
                $(this).css('color','black');
            }

        });

    if (flag==0){
        return true
    };
    $("#msg").text("Please select red highlighted dropdowns.").css('color','#dc3545');
    return false

  });
  $("#Name_id option[value='Blank']").remove();

  $('#mandetory').change(function() {
    if(this.checked) {
        $( ".map" ).each(function( index ) {
            if ($(this).attr('id') != 'Name_id'){
                $(this).val('Blank').css({'color':'blue'});
            }
        });
    }
    else{
              $( ".map" ).each(function( index ) {
              if ($(this).attr('id') != 'Name_id'){
                 $(this).val('Select').css({'color':'black'});

            }

        });
    }
});
});
