$(document).ready(function() {  

    $('#growerSelction').change( function () {
    //var id = $('#growerSelction').val();
    //document.location.href = '/farms/farms_list/?grower_id=' + id;
    $('#submitBtn').click();
});

});


function delFarm(url){
    //alert(url);
    $('#farmDelete').show();
    $('#farmDelete').attr('url',url);
}


function farmdeleteNow(){
  url = $('#farmDelete').attr('url');
  $.ajax({
  url: url,
  data: { },
  success: function (data) {
    if (data==1){
      location.reload();
    }
  }
});
}


function delFarmgrouping(url){
  //alert(url);
  //$('#message').html("Are you sure you want to delete?");
  $('#farmgroupingDelete').show();
  $('#farmgroupingDelete').attr('url',url);
}



function farmgroupingdeleteNow(){
  url = $('#farmgroupingDelete').attr('url');
  $.ajax({
  url: url,
  data: { },
  success: function (data) {
    if (data==1){
      location.reload();
    }
  }
});
}