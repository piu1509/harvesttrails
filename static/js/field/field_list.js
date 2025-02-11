$(document).ready(function() {
    $('#farmListtbl').DataTable();
});

function delField(url){
    //alert(url);
    //$('#message').html("Are you sure you want to delete?");
    $('#fieldDelete').show();
    $('#fieldDelete').attr('url',url);
  }
  

function fielddeleteNow(){
    url = $('#fieldDelete').attr('url');
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
  
  