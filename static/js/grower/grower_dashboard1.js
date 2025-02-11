
//   Multiple Select Dropdown
// Farm Filter
document.multiselect('#farmsFields')
	.setCheckBoxClick("checkboxAll", function(target, args) {
		console.log("Checkbox 'Select All' was clicked and got value ", args.checked);
	})
	.setCheckBoxClick("1", function(target, args) {
		console.log("Checkbox for item with value '1' was clicked and got value ", args.checked);
	});

// Variety Filter
	document.multiselect('#varietyFilter')
	.setCheckBoxClick("checkboxAll", function(target, args) {
		console.log("Checkbox 'Select All' was clicked and got value ", args.checked);
	})
	.setCheckBoxClick("1", function(target, args) {
		console.log("Checkbox for item with value '1' was clicked and got value ", args.checked);
	});

// Variety Filter
	document.multiselect('#yearFilter')
	.setCheckBoxClick("checkboxAll", function(target, args) {
		console.log("Checkbox 'Select All' was clicked and got value ", args.checked);
	})
	.setCheckBoxClick("1", function(target, args) {
		console.log("Checkbox for item with value '1' was clicked and got value ", args.checked);

	});

// Variety Filter
	document.multiselect('#fields_Fields')
	.setCheckBoxClick("checkboxAll", function(target, args) {
		console.log("Checkbox 'Select All' was clicked and got value ", args.checked);
	})
	.setCheckBoxClick("1", function(target, args) {
		console.log("Checkbox for item with value '1' was clicked and got value ", args.checked);

	});