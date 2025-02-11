//For updating chat in sustaniability view
var chartsurvey1
 $(document).ready(function(){
  $('#jsBtn').on('click', function() {
      var grower_id = $('#growerSelection').val();
      var farm_id = $('#farmSelection').val();
      var field_id = $('#fieldSelection').val();
      var year = $('#yearSelection').val();

      $.get('/survey/surveychartdata/',{
        grower_id : grower_id,
        farm_id : farm_id,
        field_id : field_id,
        year : year,
      },function(jsondata, status){

    //get the line chart canvas
    var ctx = $("#srpscorechart");

    //line chart data
    var data = {
     labels: jsondata.label,
     datasets: [
       {
         label: "SRP SCORING",
         data: jsondata.data,
         backgroundColor: ['#FFB300','#FF370D', '#55CF61'],
         // borderRadius: 10,
         barThickness: 80,
         // borderColor: "#FF6D4D",
         fill: false,
         lineTension: 0,
         radius: 50
       },
     ]
    };

    //options
    var options = {
     responsive: true,
     title: {
       display: true,
       position: "left",
       // text: "Side",
       fontSize: 16,
       fontColor: "#111"
     },
     legend: {
       display: true,
       position: "bottom",
       labels: {
         fontColor: "#333",
         fontSize: 16
       }
     }
    };

    if (chartsurvey1) {
     chartsurvey1.destroy();
    }
    //create Chart class object
    chartsurvey1 = new Chart(ctx, {
     type: "bar",
     data: data,
     options: options
    });
    });
  });
 });