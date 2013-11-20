/**
 * Nirit - Common Scripts
 * (c) 2013 Beatscope Limited | http://www.beatscope.co.uk/
 */

/**
 * jQuery Cookie plugin
 *
 * Copyright (c) 2010 Klaus Hartl (stilbuero.de)
 * Dual licensed under the MIT and GPL licenses:
 * http://www.opensource.org/licenses/mit-license.php
 * http://www.gnu.org/licenses/gpl.html
 *
 * Source: https://github.com/carhartl/jquery-cookie
 */
jQuery.cookie = function (key, value, options) {
    // key and at least value given, set cookie...
    if (arguments.length > 1 && String(value) !== "[object Object]") {
        options = jQuery.extend({}, options);
        if (value === null || value === undefined) {
            options.expires = -1;
        }
        if (typeof options.expires === 'number') {
            var days = options.expires, t = options.expires = new Date();
            t.setDate(t.getDate() + days);
        }
        value = String(value);
        return (document.cookie = [
            encodeURIComponent(key), '=',
            options.raw ? value : encodeURIComponent(value),
            options.expires ? '; expires=' + options.expires.toUTCString() : '', // use expires attribute, max-age is not supported by IE
            options.path ? '; path=' + options.path : '',
            options.domain ? '; domain=' + options.domain : '',
            options.secure ? '; secure' : ''
        ].join(''));
    }
    // key and possibly options given, get cookie...
    options = value || {};
    var result, decode = options.raw ? function (s) { return s; } : decodeURIComponent;
    return (result = new RegExp('(?:^|; )' + encodeURIComponent(key) + '=([^;]*)').exec(document.cookie)) ? decode(result[1]) : null;
};

/**
*   @name                           Elastic
*   @descripton                     Elastic is jQuery plugin that grow and shrink your textareas automatically
*   @version                        1.6.11
*   @requires                       jQuery 1.2.6+
*
*   @author                         Jan Jarfalk
*   @author-email                   jan.jarfalk@unwrongest.com
*   @author-website                 http://www.unwrongest.com
*
*   @licence                        MIT License - http://www.opensource.org/licenses/mit-license.php
*/
(function($){ 
    jQuery.fn.extend({  
        elastic: function() {
            //  We will create a div clone of the textarea
            //  by copying these attributes from the textarea to the div.
            var mimics = [
                'paddingTop',
                'paddingRight',
                'paddingBottom',
                'paddingLeft',
                'fontSize',
                'lineHeight',
                'fontFamily',
                'width',
                'fontWeight',
                'border-top-width',
                'border-right-width',
                'border-bottom-width',
                'border-left-width',
                'borderTopStyle',
                'borderTopColor',
                'borderRightStyle',
                'borderRightColor',
                'borderBottomStyle',
                'borderBottomColor',
                'borderLeftStyle',
                'borderLeftColor'
            ];
            
            return this.each( function() {

            // Elastic only works on textareas
            if ( this.type !== 'textarea' ) {
                return false;
            }
                    
            var $textarea   = jQuery(this),
                $twin       = jQuery('<div />').css({
                    'position'      : 'absolute',
                    'display'       : 'none',
                    'word-wrap'     : 'break-word',
                    'white-space'   :'pre-wrap'
                }),
                lineHeight  = parseInt($textarea.css('line-height'),10) || parseInt($textarea.css('font-size'),'10'),
                minheight   = parseInt($textarea.css('height'),10) || lineHeight*3,
                maxheight   = parseInt($textarea.css('max-height'),10) || Number.MAX_VALUE,
                goalheight  = 0;
                
                // Opera returns max-height of -1 if not set
                if (maxheight < 0) { maxheight = Number.MAX_VALUE; }
                    
                // Append the twin to the DOM
                // We are going to meassure the height of this, not the textarea.
                $twin.appendTo($textarea.parent());
                
                // Copy the essential styles (mimics) from the textarea to the twin
                var i = mimics.length;
                while(i--){
                    $twin.css(mimics[i].toString(),$textarea.css(mimics[i].toString()));
                }
                
                // Updates the width of the twin. (solution for textareas with widths in percent)
                function setTwinWidth(){
                    var curatedWidth = Math.floor(parseInt($textarea.width(),10));
                    if($twin.width() !== curatedWidth){
                        $twin.css({'width': curatedWidth + 'px'});
                        
                        // Update height of textarea
                        update(true);
                    }
                }
                
                // Sets a given height and overflow state on the textarea
                function setHeightAndOverflow(height, overflow){
                    var curratedHeight = Math.floor(parseInt(height,10));
                    if($textarea.height() !== curratedHeight){
                        $textarea.css({'height': curratedHeight + 'px','overflow':overflow});
                    }
                }
                
                // This function will update the height of the textarea if necessary 
                function update(forced) {
                    // Get curated content from the textarea.
                    var textareaContent = $textarea.val().replace(/&/g,'&amp;').replace(/ {2}/g, '&nbsp;').replace(/<|>/g, '&gt;').replace(/\n/g, '<br />');
                    
                    // Compare curated content with curated twin.
                    var twinContent = $twin.html().replace(/<br>/ig,'<br />');
                    
                    if(forced || textareaContent+'&nbsp;' !== twinContent){
                    
                        // Add an extra white space so new rows are added when you are at the end of a row.
                        $twin.html(textareaContent+'&nbsp;');
                        
                        // Change textarea height if twin plus the height of one line differs more than 3 pixel from textarea height
                        if(Math.abs($twin.height() + lineHeight - $textarea.height()) > 3){
                            
                            var goalheight = $twin.height()+lineHeight;
                            if(goalheight >= maxheight) {
                                setHeightAndOverflow(maxheight,'auto');
                            } else if(goalheight <= minheight) {
                                setHeightAndOverflow(minheight,'hidden');
                            } else {
                                setHeightAndOverflow(goalheight,'hidden');
                            }
                            
                        }
                        
                    }
                }
                
                // Hide scrollbars
                $textarea.css({'overflow':'hidden'});
                
                // Update textarea size on keyup, change, cut and paste
                $textarea.bind('keyup change cut paste', function(e) {
                    update(); 
                });
                
                // Update width of twin if browser or textarea is resized (solution for textareas with widths in percent)
                $(window).bind('resize', setTwinWidth);
                $textarea.bind('resize', setTwinWidth);
                $textarea.bind('update', update);
                
                // Compact textarea on blur
                // this feature breaks when the textarea is given padding
                /*$textarea.bind('blur',function(){
                    if($twin.height() < maxheight){
                        if($twin.height() > minheight) {
                            $textarea.height($twin.height());
                        } else {
                            $textarea.height(minheight);
                        }
                    }
                });*/
                
                // And this line is to catch the browser paste event
                $textarea.bind('input paste',function(e){ setTimeout( update, 250); });             
                
                // Run update once when elastic is initialized
                update();
                
            });
            
        } 
    }); 
})(jQuery);


function csrfSafeMethod (method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    crossDomain: true,
    beforeSend: function (xhr, settings) {
        var csrftoken = $.cookie('csrftoken');
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
            xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
        }
    }
});

function trim (str) {
    // trim beginning and end
    str = str.replace(/^\s+/, '');
    for (var i = str.length - 1; i >= 0; i--) {
        if (/\S/.test(str.charAt(i))) {
            str = str.substring(0, i + 1);
            break;
        }
    }
    // trim whitespaces
    //str = str.replace(/\s\s*/g, ' ');
    return str;
}

if (typeof(NIRIT) === 'undefined') {
    var NIRIT = {};
}
if (!window.NIRIT) { window.NIRIT=NIRIT; }


/**
 * Utility Functions
 */
NIRIT.Utils = function () {};

// Change the visibility of an Image field
NIRIT.Utils.prototype.set_image_visibility = function (field, visibility) {
    if (visibility) {
        $('img.'+field+'-edit').slideDown(250).show();
        $('#'+field+'_change').show();
    } else {
        $('img.'+field+'-edit').slideUp(250).hide();
        $('#'+field+'_change').hide();
    }
};

// Prevents enter key press from submitting the form
NIRIT.Utils.prototype.preventEnterSubmit = function (e) {
    if (e.which == 13) {
        var $targ = $(e.target);
        if (!$targ.is("textarea") && !$targ.is(":button,:submit")) {
        var focusNext = false;
            $(this).find(":input:visible:not([disabled],[readonly]), a").each(function () {
                if (this === e.target) {
                    focusNext = true;
                } else if (focusNext){
                    $(this).focus();
                    return false;
                }
            });
            return false;
        }
    }
};

// Add/remove company from member network
NIRIT.Utils.prototype.set_member_preference = function (setting, preference, callback) {
    var url = '/member/set-preference/' + setting + '/' + preference;
    $.get(url, function (data) {
        if (typeof(callback) === 'function') {
            callback(data);
        }
    });
}

// Add the Utils instance to the NIRIT object
NIRIT.utils = new NIRIT.Utils();


/**
 * Utility Objects
 */

// Image Upload Handler
NIRIT.Upload = function (settings) {
    this.field = settings['field'];
    this.model = settings['model'];
    this.token = settings['token'];
    if (settings.hasOwnProperty('width')) {
        this.width = settings['width'];
    } else {
        this.width = 'auto';
    }
    if (settings.hasOwnProperty('height')) {
        this.height = settings['height'];
    } else {
        this.height = 'auto';
    }

    var self = this;

    $('input#'+this.field+'-clear_id').change(function () {
        NIRIT.utils.set_image_visibility(self.field, !$(this).is(':checked'));
    });

    var post_params =  {
        'csrfmiddlewaretoken': this.token,
        'model': this.model,
        'field': this.field
    }
    if (this.width !== 'auto') { post_params['width'] = this.width; }
    if (this.height !== 'auto') { post_params['height'] = this.height; }

    $('input#id_'+this.field).ajaxfileupload({
        'action': '/upload',
        'params': post_params,
        'onComplete': function(response) {
            if ($('img.'+self.field+'-edit').length > 0) {
                $('img.'+self.field+'-edit').attr('src', response['filename']);
            } else {
                var img = $('<img>');
                img.addClass(self.field+'-edit');
                img.attr('width', self.width);
                img.attr('height', self.height);
                img.attr('src', response['filename']);
                $('input#id_'+self.field).before(img);
            }
            // Add hidden field with uploaded file value
            $('input#id_'+self.field+'_filepath').remove(); // remove field if already on the page
            var input = $('<input>');
            input.attr('type', "hidden");
            input.val(response['filename']);
            input.attr('name', self.field);
            input.attr('id', "id_"+self.field+"_filepath");
            $('input#id_'+self.field).after(input);

            NIRIT.utils.set_image_visibility(self.field, true);
        },
        'onStart': function() {
            if ($('img.'+self.field+'-edit').length > 0) {
                NIRIT.utils.set_image_visibility(self.field, false);
            }
        }
    });

};

$(document).ready(function () {

    // Cookie Control
    (function () {
        if (!$.cookie('ck_allowed')) {
            setTimeout(function () {
                $('#niritcookies').slideDown();
            }, 500);
            $('#cookies-continue-button').click(function () {
                $.cookie('ck_allowed', 1, {'expires': 365, 'path': '/'});
                $('#niritcookies').slideUp();
            });
        }
    })();

});
