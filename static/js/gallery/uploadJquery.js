$(".doc-field").hide()

   $(document).ready(function(){
     $(".img-r").click(function(){
       $(".doc-field").hide();
       $(".img-field").show();

     });
   });

   $(document).ready(function(){
     $(".doc-r").click(function(){
       $(".img-field").hide();
       $(".doc-field").show();
       
     });
   });
