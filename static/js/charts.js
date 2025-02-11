var dataPrev = {
  2016: [
    ['Lorem Lispum', 24],
    ['Lorem Lispum', 24],
    ['Lorem Lispum', 24],
    ['Lorem Lispum', 24],
    ['Lorem Lispum', 24],
    ['Lorem Lispum', 38],
    ['Lispum Lorem', 29],
    ['Lispum Lispum', 46]
  ],
  2012: [
  
  ],
  2008: [
    
  ],
  2004: [
    
  ],
  2000: [
  
  ]
};

var data = {
  2016: [
    ['South Korea', 0],
    ['Japan', 0],
    ['Australia', 0],
    ['Lorem Lispum', 1],
    ['Lorem Lispum', 20],
    ['Lorem Lispum', 26],
    ['Lispum Lorem', 27],
    ['Lispum Lispum', 46]
  ],
  2012: [
    
  ],
  2008: [
    
  ],
  2004: [
   
  ],
  
};

var countries = [{  
}, {
  
}, {
  name: 'Lorem Lispum',
  flag: 197507,
  color: '#ababab'
}, {
  name: 'Lorem Lispum',
  flag: 197571,
  color: '#ababab'
}, {
  name: 'Lorem Lispum',
  flag: 197408,
  color: '#42008D'
}, {
  name: 'Lorem Lispum',
  flag: 197375,
  color: '#FFB300'
}, {
  name: 'Lispum Lorem',
  flag: 197374,
  color: '#414042'
}, {


  name: 'Lispum Lorem',
  flag: 197374,
  color: '#00b258'
}, {


}];


function getData(data) {
  return data.map(function (country, i) {
    return {
      name: country[0],
      y: country[1],
      color: countries[i].color
    };
  });
}

var chart = Highcharts.chart('container', {
  chart: {
    type: 'column',

  },

  plotOptions: {
    series: {
      grouping: false,
      borderTopRadius: 28,
    }
  },
  legend: {
    enabled: false
  },
    xAxis: {
    type: 'category',
    max: 3,
    labels: {
      useHTML: true,
      animate: true,
      formatter: function () {
        var value = this.value,
          output;

        countries.forEach(function (country) {
          if (country.name === value) {
            output = country.flag;
          }
        });

        return '';
      }
    }
  },
  yAxis: [{
    title: {
      text: 'Gold medals'
    },
    showFirstLabel: false
  }],
  series: [{
    color: '#cecece',
    pointPlacement: -0.2,
    linkedTo: 'main',
    data: dataPrev[2016].slice(),
    name: '2012'
  }, {
    name: '2016',
    id: 'main',
    dataSorting: {
      enabled: true,
      matchByName: true
    },
    dataLabels: [{
      enabled: true,
      inside: true,
      style: {
        fontSize: '16px'
      }
    }],
    data: getData(data[2016]).slice()
  }],
  exporting: {
    allowHTML: true
  }
});

var years = [2016, 2012, 2008, 2004, 2000];

years.forEach(function (year) {
  var btn = document.getElementById(year);

  btn.addEventListener('click', function () {

    document.querySelectorAll('.buttons button.active').forEach(function (active) {
      active.className = '';
    });
    btn.className = 'active';

    chart.update({
      title: {
        text: 'Summer Olympics ' + year + ' - Top 5 countries by Gold medals'
      },
      subtitle: {
        text: 'Comparing to results from Summer Olympics ' + (year - 4) + ' - Source: <a href="https://en.wikipedia.org/wiki/' + (year) + '_Summer_Olympics_medal_table">Wikipedia</a>'
      },
      series: [{
        name: year - 4,
        data: dataPrev[year].slice()
      }, {
        name: year,
        data: getData(data[year]).slice()
      }]
    }, true, false, {
      duration: 800
    });
  });
});



 Highcharts.chart('container', {

xAxis: {
  accessibility: {
    rangeDescription: 'Range: 2010 to 2017'
  }
},

legend: {
  layout: 'vertical',
  align: 'right',
  verticalAlign: 'middle'
},

plotOptions: {
  series: {
    label: {
      connectorAllowed: false
    },
    pointStart: 2010
  }
},

series: [ {
  name: 'Rice Long Grain',
  data: [null, null, 29742, 29851, 32490, 30282, 38121, 40434],
  color: '#ababab'
}, {
  name: 'Rice Med Grain',
  data: [null, null, 16005, 19771, 20185, 24377, 32147, 39387],
  color: '#414042'
}, {
  name: 'Michigan Beans',
  data: [null, null, 7988, 12169, 15112, 22452, 34400, 34227],
  color: '#00b258'
  
}, ],

responsive: {
  rules: [{
    condition: {
      maxWidth: 500
    },
    chartOptions: {
      legend: {
        layout: 'horizontal',
        align: 'center',
        verticalAlign: 'bottom'
      }
    }
  }]
}

});




 Highcharts.chart('container', {

xAxis: {
  accessibility: {
    rangeDescription: 'Range: 2010 to 2017'
  }
},

legend: {
  layout: 'vertical',
  align: 'right',
  verticalAlign: 'middle'
},

plotOptions: {
  series: {
    label: {
      connectorAllowed: false
    },
    pointStart: 2010
  }
},

series: [ {
  name: 'Rice Long Grain',
  data: [null, null, 29742, 29851, 32490, 30282, 38121, 40434],
  color: '#ababab'
}, {
  name: 'Rice Med Grain',
  data: [null, null, 16005, 19771, 20185, 24377, 32147, 39387],
  color: '#414042'
}, {
  name: 'Michigan Beans',
  data: [null, null, 7988, 12169, 15112, 22452, 34400, 34227],
  color: '#00b258'
  
}, ],

responsive: {
  rules: [{
    condition: {
      maxWidth: 500
    },
    chartOptions: {
      legend: {
        layout: 'horizontal',
        align: 'center',
        verticalAlign: 'bottom'
      }
    }
  }]
}

});

