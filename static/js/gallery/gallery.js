document.multiselect('#myselection_farm')
		.setCheckBoxClick("checkboxAll", function(target, args) {
			console.log("Checkbox 'Select All' was clicked and got value ", args.checked);
		})
		.setCheckBoxClick("1", function(target, args) {
			console.log("Checkbox for item with value '1' was clicked and got value ", args.checked);
		});

document.multiselect('#myselection_field')
		.setCheckBoxClick("checkboxAll", function(target, args) {
			console.log("Checkbox 'Select All' was clicked and got value ", args.checked);
		})
		.setCheckBoxClick("1", function(target, args) {
			console.log("Checkbox for item with value '1' was clicked and got value ", args.checked);
		});

document.multiselect('#myselection_survey_type')
		.setCheckBoxClick("checkboxAll", function(target, args) {
			console.log("Checkbox 'Select All' was clicked and got value ", args.checked);
		})
		.setCheckBoxClick("1", function(target, args) {
			console.log("Checkbox for item with value '1' was clicked and got value ", args.checked);
		});

        document.multiselect('#myselection_year_type')
		.setCheckBoxClick("checkboxAll", function(target, args) {
			console.log("Checkbox 'Select All' was clicked and got value ", args.checked);
		})
		.setCheckBoxClick("1", function(target, args) {
			console.log("Checkbox for item with value '1' was clicked and got value ", args.checked);
		});


function updateGrowerData(){
    document.getElementById("imgbutton").click();
}

window.onload = function() {
     if (document.getElementById("all-images") != null){
    document.getElementById("imgbutton").style.background = '#00b258';
    }
    else if (document.getElementById("all-files") != null){
        document.getElementById("docbutton").style.background = '#00b258';
    }

    };
    function photoshare(pname){
        document.getElementById("recordid").value = pname
        document.getElementById("emailsend").style.display = "block";
        document.getElementById("inputemail").style.display = "block";
        document.getElementById("EmailPopCloseBtn").style.display = "block";
        document.getElementById("EmailPopTitle").innerHTML = "Please provide one or more Email ID separated by comma";
        document.getElementById("EmailPopTitle").style.color = 'black'
        document.getElementById("remarkTextSingleShare").style.display = "block";
        document.getElementById("remarkLabelSingleShare").style.display = "block";
    }

    function ValidateEmail(){
    var mailformat = /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/;
    inputText = document.getElementById("inputemail")
    console.log("Email ID ",inputText);
    if (inputText.value.match(mailformat)){
    document.document.popup-email-input();
    return true;
    }
    else{
    alert("You have entered an invalid email address!");
    console.log("invalid")
    return false;
    }
    }

    var expanded = false;
    function showCheckboxes() {

    var checkboxes = document.getElementById("checkboxes");
    if (!expanded) {
        checkboxes.style.display = "block";
        expanded = true;
    } else {
        checkboxes.style.display = "none";
        expanded = false;
    }
    }

    var expanded2 = false;
    function showCheckboxesField() {

    var checkboxes2 = document.getElementById("checkboxes2");
    if (!expanded2) {
        checkboxes2.style.display = "block";
        expanded2 = true;
    } else {
        checkboxes2.style.display = "none";
        expanded2 = false;
    }
    }

    var expanded3 = false;
    function showCheckboxesSurveyType() {

    var checkboxes3 = document.getElementById("checkboxes3");
    if (!expanded2) {
        checkboxes3.style.display = "block";
        expanded2 = true;
    } else {
        checkboxes3.style.display = "none";
        expanded2 = false;
    }
    }
