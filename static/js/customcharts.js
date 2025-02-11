//  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Most savings across by region 2021 <<<<<<<<<<<<<<<<<<<<<<<<


//  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Land Saving Chart 2021 <<<<<<<<<<<<<<<<<<<<<<<<

$(function(){

  //get the line chart canvas
  var ctx = $("#landuse2021");

  //line chart data
  var data = {
    labels: ["Var 1", "Var 2", "Var 3", "Var 4", "Var 5"],
    datasets: [
      // {
      //   label: "2020",
      //   data: [220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320, 330],
      //   backgroundColor: "#414042",
      //   // borderColor: "#FF6D4D",
      //   fill: false,
      //   lineTension: 0,
      //   radius: 5
      // },
      {
        label: "Variety (2021)",
        data: [354, 364, 374, 384, 394, 404],
        backgroundColor: "#019846",
        borderColor: "#00b2588f",
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
      text: "Land Use",
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

  //create Chart class object
  var chart = new Chart(ctx, {
    type: "line",
    data: data,
    options: options
  });
});

//  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Land Saving Chart 2020 <<<<<<<<<<<<<<<<<<<<<<<<

$(function(){

  //get the line chart canvas
  var ctx = $("#landuse2020");

  //line chart data
  var data = {
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    datasets: [
      {
        label: "Year 2020",
        data: [254, 344, 471, 454, 556, 590, 466, 788, 620, 978, 887, 746],
        backgroundColor: "#00b258",
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
      text: "Land Use 2020",
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

  //create Chart class object
  var chart = new Chart(ctx, {
    type: "bar",
    data: data,
    options: options
  });
});

 //  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Land Saving Chart 2020 <<<<<<<<<<<<<<<<<<<<<<<<

 $(function(){

  //get the line chart canvas
  var ctx = $("#landuse2019");

  //line chart data
  var data = {
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    datasets: [
      {
        label: "Year 2019",
        data: [746, 887, 978, 820, 787, 990, 866, 688, 720, 978, 887, 946],
        backgroundColor: "#00b258",
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
      text: "Land Use 2019",
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

  //create Chart class object
  var chart = new Chart(ctx, {
    type: "bar",
    data: data,
    options: options
  });
});



//  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Line Chart 2021 <<<<<<<<<<<<<<<<<<<<<<<<

$(function(){

//get the line chart canvas
var ctx = $("#carbonemission2021");

//line chart data
var data = {
  labels: ["Variety 1", "Variety 2", "Variety 3", "Variety 4", "Variety 5", "Variety 6", "Variety 7", "Variety 8", "Variety 9", "Variety 10"],
  datasets: [
    {
      label: "Variety (2021)",
      data: [425, 445, 465, 485, 505, 525, 485, 505, 585, 605],
      backgroundColor: '#019846',
      borderColor: "#00b2588f",
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
    text: "Carbon Emission Offsets",
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

//create Chart class object
var chart = new Chart(ctx, {
  type: "line",
  data: data,
  options: options
});
});

//  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> carbon emission chart line Chart 2020 <<<<<<<<<<<<<<<<<<<<<<<<

$(function(){

//get the line chart canvas
var ctx = $("#carbonemission2020");

//line chart data
var data = {
  labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  datasets: [
    {
      label: "Year 2020",
      data: [354, 454, 571, 854, 1556, 1590, 1466, 1788, 1620, 1978, 1887, 1746],
      backgroundColor: '#019846',
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
    text: "Carbon Emission 2020",
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


//create Chart class object
var chart = new Chart(ctx, {
  type: "line",
  data: data,
  options: options
});
});

//  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Line Chart 2019 <<<<<<<<<<<<<<<<<<<<<<<<

$(function(){

//get the line chart canvas
var ctx = $("#carbonemission2019");

//line chart data
var data = {
  labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  datasets: [
    {
      label: "Year 2019",
      data: [1354, 2454, 1571, 1854, 2556, 2590, 2466, 2788, 2620, 2978, 2887, 2746],
      backgroundColor: '#019846',
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
    text: "Carbon Emission 2019",
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


//create Chart class object
var chart = new Chart(ctx, {
  type: "doughnut",
  data: data,
  options: options
});
});

//  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Most Savings Variety Chart 2019 <<<<<<<<<<<<<<<<<<<<<<<<

$(function(){

//get the line chart canvas
var ctx = $("#mostsavingsvar2019");

//line chart data
var data = {
  labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  datasets: [
    {
      label: "Variety 2019",
      data: [1354, 2454, 1571, 1854, 2556, 2590, 2466, 2788, 2620, 2978, 2887, 2746],
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
    text: "Acres",
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


//create Chart class object
var chart = new Chart(ctx, {
  type: "bar",
  data: data,
  options: options
});
});

//  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Most Savings Variety Chart 2020 <<<<<<<<<<<<<<<<<<<<<<<<

$(function(){

//get the line chart canvas
var ctx = $("#mostsavingsvar2020");

//line chart data
var data = {
  labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  datasets: [
    {
      label: "Variety 2020",
      data: [1254, 2754, 2571, 2854, 2956, 1590, 2966, 1788, 3620, 2278, 2087, 2146],
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
    text: "Acres",
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


//create Chart class object
var chart = new Chart(ctx, {
  type: "bar",
  data: data,
  options: options
});
});

//  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Most Savings Variety Chart 2021 <<<<<<<<<<<<<<<<<<<<<<<<

var chartobj1
var chart1 = function () {

  var growername = $('#grower-selection').val()
  var savings = $("#savings-selection1").val()

  $.get('/grower/chart1/?growername='+ growername + '&savings=' + savings,function(jsondata, status){
  

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
      radius: 5,
      barThickness: 50
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

if (chartobj1) {
  chartobj1.destroy();
}

//create Chart class object
chartobj1 = new Chart(ctx, {
  type: "bar",
  data: data,
  options: options
});
});

}

$(chart1);



//  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Most Savings Variety Chart 2019 <<<<<<<<<<<<<<<<<<<<<<<<

$(function(){

//get the line chart canvas
var ctx = $("#highyieldvar2019");

//line chart data
var data = {
  labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  datasets: [
    {
      label: "Acres 2019",
      data: [2354, 3454, 2571, 2854, 3556, 2590, 1466, 3788, 2620, 2078, 2587, 2796],
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
    text: "Growers",
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


//create Chart class object
var chart = new Chart(ctx, {
  type: "bar",
  data: data,
  options: options
});
});

//  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Most Savings Variety Chart 2020 <<<<<<<<<<<<<<<<<<<<<<<<

$(function(){

//get the line chart canvas
var ctx = $("#highyieldvar2020");

//line chart data
var data = {
  labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  datasets: [
    {
      label: "Acres 2020",
      data: [3354, 3554, 2571, 3854, 4556, 3590, 1466, 2788, 3620, 4078, 3587, 1796],
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
    text: "Growers",
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


//create Chart class object
var chart = new Chart(ctx, {
  type: "bar",
  data: data,
  options: options
});
});

//  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Most Savings Variety Chart 2021 <<<<<<<<<<<<<<<<<<<<<<<<
// Highest Yield Variety - Chart2
var chartobj2
var chart2 = function(){

  var growername = $('#grower-selection').val()

  $.get('/grower/chart2/?growername='+ growername,function(data, status){



//get the line chart canvas
var ctx = $("#highyieldvar2021");

//line chart data
var data = {
  labels: data.label,
  datasets: [
    {
      label: "Variety (2021)",
      data: data.data,
      backgroundColor: '#00b258',
      // borderColor: "#FF6D4D",
      fill: false,
      lineTension: 0,
      radius: 5,
      barThickness: 50
    },
  ]
};

//options
var options = {
  responsive: true,
  title: {
    display: true,
    position: "left",
    text: "Yield / Acres",
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
if (chartobj2){
  chartobj2.destroy();
}

//create Chart class object
chartobj2 = new Chart(ctx, {
  type: "bar",
  data: data,
  options: options
});
});

};

$(chart2);


//  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Most Savings across by region Chart 2021 <<<<<<<<<<<<<<<<<<<<<<<<

var chart3 = function(){

  var growername = $('#grower-selection').val()
  var savings = $("#savings-selection2").val()

  $.get('/grower/chart3/?growername='+ growername + '&savings=' + savings,function(jsondata, status){




//get the line chart canvas
var ctx = $("#mostsavingsacross2021");

//line chart data
var data = {
  labels: jsondata.label,
  datasets: [
    {
      label: "State (2021)",
      data: jsondata.data,
      backgroundColor: '#00b258',
      // borderColor: "#FF6D4D",
      fill: false,
      lineTension: 0,
      radius: 5,
      barThickness: 50
    },
  ]
};

//options
var options = {
  responsive: true,
  scales: {
    yAxes: [{
      ticks: {
        stepSize: 1,
        scaleStartValue : 1
      }


    }]
  },
  title: {
    display: true,
    position: "left",
    text: jsondata.savings,
    fontSize: 16,
    fontColor: "#414042"
  },
  legend: {
    display: true,
    position: "bottom",
    labels: {
      fontColor: "#414042",
      fontSize: 16
    }
  }
  




};


//create Chart class object
var chart = new Chart(ctx, {
  scaleOverride: true,
  scaleSteps: 1,
  scaleStepWidth: 1,
  scaleStartValue: 0,



  type: "bar",
  data: data,
  options: options
});
});
};

$(chart3);
// <<<<<<<<<<<<<<<<<<<<<<<<<< Water Use Savings >>>>>>>>>>>>>>>>>>>>>>>>>>>

$(function(){

//get the line chart canvas
var ctx = $("#waterusesavings2021");

//line chart data
var data = {
  labels: ["Var 1", "Var 2", "Var 3", "Var 4", "Var 5", "Var 6"],
  datasets: [
    {
      label: "Variety (2021)",
      data: [265, 275, 272, 285, 305, 315],
      backgroundColor: '#019846',
      borderColor: "#00b2588f",
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
    text: "Water use Savings",
    fontSize: 16,
    fontColor: "#414042"
  },
  legend: {
    display: true,
    position: "bottom",
    labels: {
      fontColor: "#414042",
      fontSize: 16
    }
  }
};

//create Chart class object
var chart = new Chart(ctx, {
  type: "line",
  data: data,
  options: options
});
});


// <<<<<<<<<<<<<<<<<<<<<<<<<< End Water Use Savings >>>>>>>>>>>>>>>>>>>>>>>