    $("#growerSelection").change(function () {
      var url = $("#farmSelection").attr("load-url");
      var grower_id = $(this).val();

      $.ajax({
        url: url,
        data: {
          'grower_id': grower_id,
        },
        success: function (data) {

          $("#farmSelection").html(data);
        }
      });
    });

	$("#farmSelection").change(function () {
    var url = $("#fieldSelection").attr("load-url");
    var farm_id = $(this).val();
	  var grower_id = $("#growerSelection").val();

      $.ajax({
        url: url,
        data: {
          'farm_id': farm_id,
		  'grower_id' : grower_id,
        },
        success: function (data) {
          $("#fieldSelection").html(data);
        }
      });

    });


	$("#fieldSelection").change(function () {
      var url = $("#yearSelection").attr("load-url");
      var field_id = $("#fieldSelection").val();
	  var grower_id = $("#growerSelection").val();
	  var farm_id = $("#farmSelection").val();


      $.ajax({
        url: url,
        data: {
			'field_id' : field_id,
      'farm_id': farm_id,
		  'grower_id' : grower_id,
        },
        success: function (data) {
          $("#yearSelection").html(data);
        }
      });

    });


  $(document).ready(function(){
		   //Disable send button by default in Survey Rejact popup
		   $("#emailsend").prop('disabled', true);

		   //Reloading page on close button in survey accept popup
		   $('#closeBtn').click(function() {
			location.reload();
			});


      //for not Consultant user / if Non-Consultant user is logged in
      //Loading farms single select drop down button
      if ($("#nonConsGrower").val() != 'undefined'){
        var url = $("#farmSelection").attr("load-url");
        var grower_id = $("#nonConsGrower").val();

        $.ajax({
          url: url,
          data: {
            'grower_id': grower_id,
          },
          success: function (data) {

            $("#farmSelection").html(data);
          }
        });
      }


			$( "#remarkText" ).keyup(function() {
				  var rt = $("#remarkText").val()
				if ( rt.length > 0 ) {
					$("#emailsend").prop('disabled', false);
					$("#emailsend").removeClass('custom-mute');

				}
				else{
					$("#emailsend").prop('disabled', true);
					$("#emailsend").addClass('custom-mute');
				}
			  });

		   //Function updateing survey status True/ False for provisional score and final score
		   $("#acceptBtn").click(function(){
			 console.log("Running acceptbtn function");
			 var url = "/survey/statusupdate/";
          $.get(url,
          {
            grower_id : $("#growerSelection").val(),
            farm_id : $("#farmSelection").val(),
            field_id : $("#fieldSelection").val(),
            year : $("#yearSelection").val(),
          },
          function(data, status){

            if(data==1){
				console.log("score status updated")
            }
            else{
				console.log("score status is not updated")
            }
            }).fail(function(response) {
              console.log('Error: ' + response.responseText);
            });
          });

		  //Sending email notification to grower's email id on survey rejection
          $("#emailsend").click(function(){
              $("#remarkText").show();

          $.get("/survey/surveyreject/",
          {

            id : $("#growerSelection").val(),
            remark: $("#remarkText").val(),

          },
          function(data, status){
            if(data==1){
			  $("#message").text("Email notification has been sent to the grower.");
			  $("#emailsend").prop('disabled', false);

            }
            else{
              $("#message").text("Email notification sending unsuccessful.");
			  $("#emailsend").prop('disabled', false);
             }
            }).fail(function(response) {
              console.log('Error: ' + response.responseText);
            });
          });

});

/*For passing file_path,img_path,farm_name,field_name,survey_name,year
in popup (for displaying document detail) on sustamiability view*/
function loadPopup(file_path,img_path,farm_name,field_name,survey_name,year,pk,url)
{
  //var url = url
  $.ajax({
    url: url,
    data: {
      'pk': pk,
    },
    success: function (data) {

      $("#imageboxpopup").html(data);
    }
  });

  let file_name = file_path.split('/').slice(-1);
  $("#popFileName").text(file_name);
  $("#popImg").attr('src',img_path);
  $("#popDownloadLink").attr('href',file_path);
  $("#popDownloadLink").attr('download',file_path);
  $("#popFarmName").text(farm_name);
  $("#popFieldName").text(field_name);
  $("#popSurveyType").text(survey_name);
  $("#popYear").text(year);
  
}