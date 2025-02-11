//For getting multiselect filter button data
var chartfilt
 $(document).ready(function(){
	$('#chartbtn').on('click', function() {
  	var year = [];
    $('.year[name="year"]:checked').each(function() {
    year.push($(this).val());
    });

	var state_name = [];
    $('.state_nm:checked').each(function() {
    state_name.push($(this).val());
    });

	var farm_name = [];
    $('.farm_nm:checked').each(function() {
    farm_name.push($(this).val());
    });

	var field_name = [];
    $('.field_nm:checked').each(function() {
    field_name.push($(this).val());
    });

	var growername = $("#grower-selection").val();
	var savings = $("#savings").val();
	var url = '/grower/chart1/?year='+ year.join(",") + "&farmname=" + farm_name.join(",") + "&fieldname="+ field_name.join(",")+ "&statename=" + state_name.join(",")  + "&growername="+ growername + "&savings=" + savings;


$(function(){

  $.get(url,function(jsondata, status){

//get the line chart canvas
var ctx = $("#mostsavingsvar2021");

//line chart data
var data = {
  labels: jsondata.label,
  datasets: [
    {
      label: "Variety (2021)",
      data: jsondata.data,
      backgroundColor: '#00b258',
      // borderColor: "#FF6D4D",
      fill: false,
      lineTension: 0,
      radius: 5
    },
  ]
};

//options
var options = {
  responsive: true,
  title: {
    display: true,
    position: "left",
    text: jsondata.savings,
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
if (chartfilt) {

  chartfilt.destroy();
}

//create Chart class object
chartfilt = new Chart(ctx, {
  type: "bar",
  data: data,
  options: options
});
});

});

});
});

//Function for updating grower detail on grower change event
var update_grower_detail = function() {

    growername  = document.getElementById('grower-selection').value

	console.log("Grower Name ",growername)
    url = '/grower/dashboard1/?growername='+ growername;
	window.open(url,"_self")
};

    $(document).ready(function(){
	$("#grower-selection").val($('#default_grower').val())
	$("#grower-selection").on('change',update_grower_detail)
	$('#chartbtn').click();
    });
