function delGrower(url){
    //alert(url);
    //$('#message').html("Are you sure you want to delete?");
    $('#growerDelete').show();
    $('#growerDelete').attr('url',url);
}

function delUser(url){
  //alert(url);
  //$('#message').html("Are you sure you want to delete?");
  $('#userDelete').show();
  $('#userDelete').attr('url',url);
}

function delRole(url){
  //alert(url);
  //$('#message').html("Are you sure you want to delete?");
  $('#roleDelete').show();
  $('#roleDelete').attr('url',url);
}


function growerdeleteNow(){
    url = $('#growerDelete').attr('url');
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


function userdeleteNow(){
  url = $('#userDelete').attr('url');
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


function roledeleteNow(){
  url = $('#roleDelete').attr('url');
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

