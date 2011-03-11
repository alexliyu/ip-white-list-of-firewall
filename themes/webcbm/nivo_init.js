(function($) {

  $.fn.example = function(text, args) {

    /* Only calculate once whether a callback has been used. */
    var isCallback = $.isFunction(text);

    /* Merge the arguments and given example text into one options object. */
    var options = $.extend({}, args, {example: text});

    return this.each(function() {

      /* Reduce method calls by saving the current jQuery object. */
      var $this = $(this);

      /* Merge the plugin defaults with the given options and, if present,
       * any metadata.
       */
      if ($.metadata) {
        var o = $.extend({}, $.fn.example.defaults, $this.metadata(), options);
      } else {
        var o = $.extend({}, $.fn.example.defaults, options);
      }

      /* The following event handlers only need to be bound once
       * per class name. In order to do this, an array of used
       * class names is stored and checked on each use of the plugin.
       * If the class name is in the array then this whole section
       * is skipped. If not, the events are bound and the class name
       * added to the array.
       *
       * As of 1.3.2, the class names are stored as keys in the
       * array, rather than as elements. This removes the need for
       * $.inArray().
       */
      if (!$.fn.example.boundClassNames[o.className]) {

        /* Because Gecko-based browsers cache form values
         * but ignore all other attributes such as class, all example
         * values must be cleared on page unload to prevent them from
         * being saved.
         */
        $(window).unload(function() {
          $('.' + o.className).val('');
        });

        /* Clear fields that are still examples before any form is submitted
         * otherwise those examples will be sent along as well.
         *
         * Prior to 1.3, this would only be bound to forms that were
         * parents of example fields but this meant that a page with
         * multiple forms would not work correctly.
         */
        $('form').submit(function() {

          /* Clear only the fields inside this particular form. */
          $(this).find('.' + o.className).val('');
        });

        /* Add the class name to the array. */
        $.fn.example.boundClassNames[o.className] = true;
      }

      /* Internet Explorer will cache form values even if they are cleared
       * on unload, so this will clear any value that matches the example
       * text and hasn't been specified in the value attribute.
       *
       * If a callback is used, it is not possible or safe to predict
       * what the example text is going to be so all non-default values
       * are cleared. This means that caching is effectively disabled for
       * that field.
       *
       * Many thanks to Klaus Hartl for helping resolve this issue.
       */
      if ($.browser.msie && !$this.attr('defaultValue') && (isCallback || $this.val() == o.example))
        $this.val('');

      /* Initially place the example text in the field if it is empty
       * and doesn't have focus yet.
       */
      if ($this.val() == '' && this != document.activeElement) {
        $this.addClass(o.className);

        /* The text argument can now be a function; if this is the case,
         * call it, passing the current element as `this`.
         */
        $this.val(isCallback ? o.example.call(this) : o.example);
      }

      /* Make the example text disappear when someone focuses.
       *
       * To determine whether the value of the field is an example or not,
       * check for the example class name only; comparing the actual value
       * seems wasteful and can stop people from using example values as real
       * input.
       */
      $this.focus(function() {

        /* jQuery 1.1 has no hasClass(), so is() must be used instead. */
        if ($(this).is('.' + o.className)) {
          $(this).val('');
          $(this).removeClass(o.className);
        }
      });

      /* Detect a change event to the field and remove the example class. */
      $this.change(function() {
        if ($(this).is('.' + o.className)) {
          $(this).removeClass(o.className);
        }
      });

      /* Make the example text reappear if the input is blank on blurring. */
      $this.blur(function() {
        if ($(this).val() == '') {
          $(this).addClass(o.className);

          /* Re-evaluate the callback function every time the user
           * blurs the field without entering anything. While this
           * is not as efficient as caching the value, it allows for
           * more dynamic applications of the plugin.
           */
          $(this).val(isCallback ? o.example.call(this) : o.example);
        }
      });
    });
  };

  /* Users can override the defaults for the plugin like so:
   *
   *   $.fn.example.defaults.className = 'not_example';
   */
  $.fn.example.defaults = {
    className: 'example'
  };

  /* All the class names used are stored as keys in the following array. */
  $.fn.example.boundClassNames = [];

})(jQuery);


$(document).ready(function(){

	// Featured projects carousel
	$(".feat_projects").jCarouselLite({
        visible: 5,
        auto:4000,
        speed:1000,
		scroll:1,
		easing:'swing',
       	btnNext: ".next",
       	btnPrev: ".prev"
    });

	// Testimonials carousel
	$(".testimonials").jCarouselLite({
		vertical:true,
        visible: 1,
        auto:4000,
        speed:1000,
		scroll:1,
		easing:'swing',
       	btnNext: ".next2",
       	btnPrev: ".prev2"
    });


	//Subscribe Field Text disappearance
	//-------------------------------
	$('#subscribe_field').example(function() {
		return $(this).attr('title');
	});


	$('ul#port_filter a').click(function() {
		$(this).css('outline','none');
		$('ul#port_filter .active').removeClass('active');
		$(this).parent().addClass('active');

		var cats = $(this).text().toLowerCase().replace(' ','-');
		var count1 = 1;
		var count2 = 1;
		if(cats == 'all') {
			$('ul.portfolio_holder li.hidden').fadeIn('fast').removeClass('hidden');
			$('ul.portfolio_holder li').each(function() {
							if(count1 % 4 == 0)
							{
								if(!$(this).hasClass('last'))
									{
										$(this).addClass('last');
									}
							}
							else
							{
								if($(this).hasClass('last'))
								{
									$(this).removeClass('last');
								}
							}
							count1++;

					});
		}
		else {
					$('ul.portfolio_holder li').each(function() {
							if(!$(this).hasClass(cats)) {
								$(this).fadeOut('fast').addClass('hidden');
							}
							else {
								$(this).fadeIn('fast').removeClass('hidden');


							if(count2 % 4 == 0)
							{
								if(!$(this).hasClass('last'))
									{
										$(this).addClass('last');
									}
							}
							else
							{
								if($(this).hasClass('last'))
								{
									$(this).removeClass('last');
								}
							}
							count2++;
					}
					});
			}

		return false;
	});

}) // end document.ready call
