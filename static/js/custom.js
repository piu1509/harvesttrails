function customAccordion(elem) {
    var a = document.getElementsByTagName('a')
    for (i = 0; i < a.length; i++) {
        a[i].classList.remove('active')

        $(".set > a i").removeClass("fa-plus").addClass("fa-minus");

    }

    elem.classList.add('active')

}



$(document).ready(function () {
    $("#myInput").on("keyup", function () {
        var value = $(this).val().toLowerCase();
        $("#myTable tr").filter(function () {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });

    $('#id_text').attr("rows", "4");
});


$(document).ready(function () {
    $("#toggle").click(function () {
        $(".bs-example, #forhide").toggle();
    });
    $("#toggle").dblclick(function () {
        $("#dbclick").toggle();
    });

    $("#toggle").dblclick(function () {
        $("#forhide").hide();
    });

});

// jQuery(function($){
// $('.table').footable();
// });
$(".forn-none19").click(function () {
    $(".rotate19").toggleClass("down");
})

$(".forn-none1").click(function () {
    $(".rotate").toggleClass("down");
})


$(".forn-none2").click(function () {
    $(".rotate2").toggleClass("down");
})


$(".forn-none3").click(function () {
    $(".rotate3").toggleClass("down");
})

$(".forn-none4").click(function () {
    $(".rotate4").toggleClass("down");
})

$(".forn-none6").click(function () {
    $(".rotate6").toggleClass("down");
})

$(".forn-none7").click(function () {
    $(".rotate7").toggleClass("down");
    $(".pull_right_new3").toggleClass("down");
})
$(".forn-none8").click(function () {
    $(".rotate8").toggleClass("down");
})
$(".forn-none9").click(function () {
    $(".rotate9").toggleClass("down");
})
$(".forn-none18").click(function () {
    $(".rotate18").toggleClass("down");
})
$(".forn-none10").click(function () {
    $(".rotate10").toggleClass("down");
})


$(".forn-none18").click(function () {
    $(".dropdown-18").toggle();
});
$(".forn-none19").click(function () {
    $(".dropdown-19").toggle();
});
$(".forn-none1").click(function () {
    $(".dropdown-2").toggle();
    $(".pull_right_new").toggleClass("down");
});

$(".forn-none2").click(function () {
    $(".dropdown-22").toggle();
});

$(".forn-none3").click(function () {
    $(".dropdown-33").toggle();
});

$(".forn-none4").click(function () {
    $(".dropdown-44").toggle();
});

$(".forn-none5").click(function () {
    $(".dropdown-55").toggle();
});


// 01/03/2024
// $(".forn-none11").click(function() {
//     $(".dropdown-1011").toggle();
// });
// 


$(".forn-none6").click(function () {
    $(".dropdown-66").toggle();
});

$(".forn-none7").click(function () {
    $(".dropdown-77").toggle();
});
$(".forn-none8").click(function () {
    $(".dropdown-88").toggle();
});
$(".forn-none9").click(function () {
    $(".dropdown-99").toggle();
});
$(".forn-none10").click(function () {
    $(".dropdown-1010").toggle();
});
$(".forn-none11").click(function () {
    $(this).siblings(".dropdown-1011").toggle();
    $(".pull_right_new1").toggleClass("down");
});
$(".forn-none12").click(function () {
    $(this).siblings(".dropdown-1013").toggle();
    $(".pull_right_new2").toggleClass("down");
});
// $(".forn-none5").click(function() {
//     $(".dropdown-55").toggle();
// });

// function variety(){
// 	document.getElementById('year20').onclick = function(){
// 		$('.savingsbyvariety-2020').addClass('blockChart')
// 	}
// }
// Variety Filter
$(document).click(function () {


    $('#myvariety').change(function () {
        let value = this.value;
        if (value == 2019) {
            $('#variety2019').show();
            $('#variety2020').hide();
            $('#variety2021').hide();
        } else if (value == 2020) {
            $('#variety2020').show();
            $('#variety2019').hide();
            $('#variety2021').hide();
        } else if (value == 2021) {
            $('#variety2021').show();
            $('#variety2020').hide();
            $('#variety2019').hide();
        }


    });
})

// Highest Yield Variety
$(document).click(function () {


    $('#highyieldvariety').change(function () {
        let value = this.value;
        if (value == 2019) {
            $('#highyieldvar2021').hide();
            $('#highyieldvar2020').hide();
            $('#highyieldvar2019').show();
        } else if (value == 2020) {
            $('#highyieldvar2021').hide();
            $('#highyieldvar2020').show();
            $('#highyieldvar2019').hide();
        } else if (value == 2021) {
            $('#highyieldvar2021').show();
            $('#highyieldvar2020').hide();
            $('#highyieldvar2019').hide();
        }


    });
})
// Water Savings Filter

$(document).click(function () {


    $('#mywatersaving').change(function () {
        let value = this.value;
        if (value == 20202021) {
            $('#watersavings20202021').show();
            $('#watersavings20192020').hide();
            $('#watersavings20182019').hide();

        } else if (value == 20192020) {
            $('#watersavings20202021').hide();
            $('#watersavings20192020').show();
            $('#watersavings20182019').hide();
        } else if (value == 20182019) {
            $('#watersavings20202021').hide();
            $('#watersavings20192020').hide();
            $('#watersavings20182019').show();
        }

    });
})

// Most Savings Variety Chart

$(document).click(function () {

    $('#mostsavingsvariety').change(function () {
        let value = this.value;
        if (value == 2021) {
            $('#mostsavingsvar2021').show();
            $('#mostsavingsvar2020').hide();
            $('#mostsavingsvar2019').hide();
        } else if (value == 2020) {
            $('#mostsavingsvar2021').hide();
            $('#mostsavingsvar2020').show();
            $('#mostsavingsvar2019').hide();
        } else if (value == 2019) {
            $('#mostsavingsvar2021').hide();
            $('#mostsavingsvar2020').hide();
            $('#mostsavingsvar2019').show();
        }

    });
})

// Land Use Savings Chart

$(document).click(function () {

    $('#landsaving').change(function () {
        let value = this.value;
        if (value == 2021) {
            $('#landuse2021').show();
            $('#landuse2020').hide();
            $('#landuse2019').hide();
        } else if (value == 2020) {
            $('#landuse2021').hide();
            $('#landuse2020').show();
            $('#landuse2019').hide();
        } else if (value == 2019) {
            $('#landuse2021').hide();
            $('#landuse2020').hide();
            $('#landuse2019').show();
        }

    });
})

// Carbon Emission Effect Chart

$(document).click(function () {

    $('#emissioneffect').change(function () {
        let value = this.value;
        if (value == 2021) {
            $('#carbonemission2021').show();
            $('#carbonemission2020').hide();
            $('#carbonemission2019').hide();
        } else if (value == 2020) {
            $('#carbonemission2021').hide();
            $('#carbonemission2020').show();
            $('#carbonemission2019').hide();
        } else if (value == 2019) {
            $('#carbonemission2021').hide();
            $('#carbonemission2020').hide();
            $('#carbonemission2019').show();
        }

    });
})

// <<<<<<<<<<<<<<<<<<<<<<<< Begin Respective Chart Filter >>>>>>>>>>>>>>>>>>>>>>>>
$(document).click(function () {

    $('#yearFilter').change(function () {
        let value = this.value;
        if (value == 2021) {
            $('#mostsavingsvar2021').show();
            $('#mostsavingsvar2020').hide();
            $('#mostsavingsvar2019').hide();
        } else if (value == 2020) {
            $('#mostsavingsvar2021').hide();
            $('#mostsavingsvar2020').show();
            $('#mostsavingsvar2019').hide();
        } else if (value == 2019) {
            $('#mostsavingsvar2021').hide();
            $('#mostsavingsvar2020').hide();
            $('#mostsavingsvar2019').show();
        }

    });
})

// <<<<<<<<<<<<<<<<<<<<<<<< End Respective Chart Filter >>>>>>>>>>>>>>>>>>>>>>>>

// $("#navMenus").on('click', 'li a', function() {
//     $("#navMenus li a.onlink").removeClass("onlink");
//     // adding classname 'active' to current click li 
//     $(this).addClass("onlink");
// });
// All chef Customer
function switchtab(evt, chefcustomer) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontentcontainer");
    var filt = document.getElementById("varietyFilter");
    console.log("Chart is clicked ", filt);

    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablinkschartdata");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(chefcustomer).style.display = "block";
    evt.currentTarget.className += " active";
}


// Side Navigation Bar

$("ul#navMenus li a").each(function () {
    if (this.href == window.location.href) {
        $(this).addClass("activeLink");
    }
});
$("ul#navMenus li.for-drop ul li a").each(function () {
    if (this.href == window.location.href) {
        $(this).addClass("active-nav");
    }
});
$("ul.dropdown-18 li a").each(function () {
    if (this.href == window.location.href) {
        $("ul.dropdown-18").addClass("disblock");
        $('.parent-nav18').addClass("activeLink");
        $('span.rotate18').addClass("down");
    }
});
$("ul.dropdown-19 li a").each(function () {
    if (this.href == window.location.href) {
        $("ul.dropdown-19").addClass("disblock");
        $('.parent-nav19').addClass("activeLink");
        $('span.rotate').addClass("down");
    }
});
$("ul.dropdown-2 li a").each(function () {
    if (this.href == window.location.href) {
        $("ul.dropdown-2").addClass("disblock");
        $('.parent-nav2').addClass("activeLink");
        $('span.rotate').addClass("down");
    }
});
$("ul.dropdown-22 li a").each(function () {
    if (this.href == window.location.href) {
        $("ul.dropdown-22").addClass("disblock");
        $('.parent-nav22').addClass("activeLink");
        $('span.rotate2').addClass("down");
    }
});
$("ul.dropdown-33 li a").each(function () {
    if (this.href == window.location.href) {
        $("ul.dropdown-33").addClass("disblock");
        $('.parent-nav33').addClass("activeLink");
        $('span.rotate3').addClass("down");
    }
});
$("ul.dropdown-44 li a").each(function () {
    if (this.href == window.location.href) {
        $("ul.dropdown-44").addClass("disblock");
        $('.parent-nav44').addClass("activeLink");
        $('span.rotate4').addClass("down");
    }
});
$("ul.dropdown-55 li a").each(function () {
    if (this.href == window.location.href) {
        $("ul.dropdown-55").addClass("disblock");
        $('.parent-nav55').addClass("activeLink");
        $('span.rotate5').addClass("down");
    }
});

// 01/03/2024
// $("ul.dropdown-1011 li a").each(function() {
//     if (this.href == window.location.href) {
//         $("ul.dropdown-1011").addClass("disblock");
//         $('.parent-nav1011').addClass("activeLink");
//         $('span.rotate11').addClass("down");
//     }
// });
// 01/03/2024

$("ul.dropdown-66 li a").each(function () {
    if (this.href == window.location.href) {
        $("ul.dropdown-66").addClass("disblock");
        $('.parent-nav66').addClass("activeLink");
        $('span.rotate6').addClass("down");
    }
});

$("ul.dropdown-77 li a").each(function () {
    if (this.href == window.location.href) {
        $("ul.dropdown-77").addClass("disblock");
        $('.parent-nav77').addClass("activeLink");
        $('span.rotate7').addClass("down");
    }
});
$("ul.dropdown-88 li a").each(function () {
    if (this.href == window.location.href) {
        $("ul.dropdown-88").addClass("disblock");
        $('.parent-nav88').addClass("activeLink");
        $('span.rotate8').addClass("down");
    }
});
$("ul.dropdown-99 li a").each(function () {
    if (this.href == window.location.href) {
        $("ul.dropdown-99").addClass("disblock");
        $('.parent-nav99').addClass("activeLink");
        $('span.rotate9').addClass("down");
    }
});
$("ul.dropdown-1010 li a").each(function () {
    if (this.href == window.location.href) {
        $("ul.dropdown-1010").addClass("disblock");
        $('.parent-nav1010').addClass("activeLink");
        $('span.rotate10').addClass("down");
    }
});
$("form").on("change", ".file-upload-field", function () {
    $(this).parent(".file-upload-wrapper").attr("data-text", $(this).val().replace(/.*(\/|\\)/, '')).addClass('bold-txt');
});

//$(".alert").alert('close')


$(document).ready(function () {
    $('#farmcancelbtn').click(function () {
        window.location.href = '/farms/csv_farms_create/';
    })
    $('#fieldcancelbtn').click(function () {
        window.location.href = '/field/csv_field_create/';
    })

})

$('#id_notes').attr('rows', '6')

// Add Custom JS

$('#NM').click(function (e) {
    $('#gen_div').addClass('showDiv').fadeTo("slow", 0.9);
    $('#temp_div').removeClass('showDiv');
    $('#moist_div').removeClass('showDiv');

});

$('#WY').click(function (e) {
    $('#temp_div').addClass('showDiv').fadeTo("slow", 0.9);
    $('#gen_div').removeClass('showDiv');
    $('#moist_div').removeClass('showDiv');

});

$('#CA').click(function (e) {
    $('#moist_div').addClass('showDiv').fadeTo("slow", 0.9);
    $('#temp_div').removeClass('showDiv');
    $('#gen_div').removeClass('showDiv');
});


jQuery(function ($) {
    $('.user-details-table').footable();
});

jQuery(function ($) {
    $('.account-footable-table').footable();
});

jQuery(function ($) {
    $('.farm-footable-table').footable();
});

jQuery(function ($) {
    $('.field-footable-table').footable();
});

jQuery(function ($) {
    $('.grower-dashborad1-details-table').footable();
});

jQuery(function ($) {
    $('.grower-dashborad2-details-table').footable();
});
