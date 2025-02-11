var update_grower_detail = function() {
    growerid  = document.getElementById('id_grower').value

     $.get('/gallery/growerdetails/?growerid='+ growerid,function(data, status){

    var s1 = document.getElementById('id_farm');
    var s2 = document.getElementById('id_field');
    document.getElementById('id_farm').options.length = 0;
    document.getElementById('id_field').options.length = 0;

    var farms = data.farm
    var fields = data.field

    for(let i = 0; i < farms.length; i++){
        var newoption = document.createElement("option");
        newoption.value = data.farm_id[i];
        newoption.innerHTML = farms[i];
        s1.options.add(newoption);
    }


    for(let i = 0; i < fields.length; i++){
        var newoption = document.createElement("option");
        newoption.value = data.field_id[i];
        newoption.innerHTML = fields[i];
        s2.options.add(newoption);
    }
    });
};

    $(document).ready(function(){
        $("#id_grower").on('change',update_grower_detail)

    });


//for updating grower detail for non superuser
var update_grower_detail_nsu = function() {
    growerid  = document.getElementById("defGrower").innerHTML

     $.get('/gallery/growerdetails/?growerid='+ growerid,function(data, status){

    var s1 = document.getElementById('id_farm');
    var s2 = document.getElementById('id_field');
    document.getElementById('id_farm').options.length = 0;
    document.getElementById('id_field').options.length = 0;
    var farms = data.farm
    var fields = data.field

    for(let i = 0; i < farms.length; i++){
        var newoption = document.createElement("option");
        newoption.value = data.farm_id[i];
        newoption.innerHTML = farms[i];
        s1.options.add(newoption);
    }

    for(let i = 0; i < fields.length; i++){
        var newoption = document.createElement("option");
        newoption.value = data.field_id[i];
        newoption.innerHTML = fields[i];
        s2.options.add(newoption);
    }
    });
};

    $(document).ready(function(){
        var growerid = document.getElementById("defGrower");
        if (growerid != null) {
            document.getElementById('id_grower').value = growerid.innerHTML;
            $(update_grower_detail_nsu);

        }

    });