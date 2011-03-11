//var $q=jQuery.noConflict();
	$(document).ready(function(){	
		$("#commentform").validate({		
			//set the rules for the field names
			rules: {
				name: {
					required: true,
					minlength: 2
				},
				email: {
					required: true,
					email: true
				},				
				url: {
					url:true
				},				
				comment: {
					required: true,
					minlength: 5
				}
			},	
			//set messages to appear inline
			messages: {
				name: {
					required:"Enter your Name",
					minlength:"Enter atleast 2 characters"
				},
				email: {
					required:"An email is required",
					email:"Enter a valid e-mail"
				},
				comment: {
					required:"A comment is required",
					minlength:"Enter atleast 5 characters"
				}
			},
			
			//hide errors forever. We just need element highlighting
			errorPlacement: function(error, element) {
				error.hide();
			},

			//Submit the Form  
			submitHandler: function() {			
			//Post the form values via ajax post 
				$.post($("#commentform").attr('action'), $("#commentform").serialize()+'&ajax=1', function(result){				
						$('#commentform').remove();		//hide comment form
						$('#mail_success').fadeIn(500);	//Show mail success div			
				});			
			}		
		});
	});
