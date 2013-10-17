/**
 * Nirit - Edit Company Scripts
 * (c) 2013 Beatscope Limited | http://www.beatscope.co.uk/
 */

if (typeof(NIRIT) === 'undefined') {
    console.log('NIRIT Core is required.');
}

NIRIT.Company = function (csrf_token, token) {
    this.csrf_token = csrf_token;
    this.token = token;
    this.init();
};

NIRIT.Company.prototype.init = function () {
    var self = this;

    // Image upload
    new NIRIT.Upload({
        'field': 'image',
        'model': 'Organization',
        'token': this.csrf_token,
        'width': 626,
        'height': 192
    });

    // Logo upload
    new NIRIT.Upload({
        'field': 'logo',
        'model': 'Organization',
        'token': this.csrf_token,
        'width': 180,
        'height': 90
    });

    // Square logo upload
    new NIRIT.Upload({
        'field': 'square_logo',
        'model': 'Organization',
        'token': this.csrf_token,
        'width': 60,
        'height': 60
    });

    // Expandable textareas
    $('#id_description').elastic();

    /**
     * Expertise Autocomplete
     */
    var AE = new NIRIT.Company.Expertise();

    // Hide & Remove un-selected items from the select
    $('#id_expertise').hide().find('option').each(function (i) {
        if (typeof($(this).attr('selected')) === 'undefined') {
            $(this).remove();
        } else {
            AE.addExpertiseToList({
                'label': $(this).text(),
                'value': $(this).val()
            });
        }
    });

    // Add autocomplete widget
    $("#expertise").keypress(NIRIT.utils.preventEnterSubmit); // make sure the input field never submits the form
    $("#expertise").autocomplete({
        minLength: 0,
        source: function (request, callback) {
            $.ajax({
                url: '/api/expertise',
                data: { search: request.term },
                dataType: "json",
                success: function (response) {
                    var _response = [];
                    if (response.length <= 0) {
                        _response.push({
                            'label': $("#expertise").val(),
                            'value': 'add'
                        });
                    } else {
                        var new_input = true;
                        for (var r in response) {
                            _response.push({
                                'label': response[r]['title'],
                                'value': response[r]['id']
                            });
                            if (response[r]['title'].toLowerCase() == $("#expertise").val().toLowerCase()) {
                                new_input = false;
                            }
                        }
                        // always add the raw text as an option
                        // if it is different to any other matches of course
                        if (new_input) {
                            _response.push({
                                'label': $("#expertise").val(),
                                'value': 'add'
                            });
                        }
                    }
                    callback(_response);
                }
            });
        },
        focus: function (event, ui) {
            $("#expertise").val(ui.item.label);
            return false;
        },
        select: function(event, ui) {
            $("#expertise").val(null);
            // when the value of the selected item is 'add',
            // we first need to create the new Expertise
            if (ui.item.value == 'add') {
                // capitalise the value before submitting it
                var phrase = ui.item.label.split(/ +/);
                var words = [];
                for (var word in phrase) {
                    words.push(phrase[word].charAt(0).toUpperCase() + phrase[word].slice(1));
                }
                value = words.join(' ');
                $.ajax({
                    url: '/api/expertise/add',
                    data: { 'title': value },
                    type: 'POST',
                    dataType: "json",
                    success: function (response) {
                        AE.addExpertise({
                            'label': response.title,
                            'value': response.id
                        });
                    },
                    error: function (e) {
                        console.log('FAILED -- ' + e);
                    },
                    headers: {
                        "Authorization": "Token " + self.token
                    }
                });
            } else {
                AE.addExpertise({
                    'label': ui.item.label,
                    'value': ui.item.value
                });
            }
            return false;
        }
    });

};


/**
 * Expertise Autocomplete
 */
NIRIT.Company.Expertise = function () {};

NIRIT.Company.Expertise.prototype.addExpertise = function (expertise) {
    this.addExpertiseToList(expertise);
    this.addExpertiseToSelect(expertise);
};

NIRIT.Company.Expertise.prototype.removeExpertise = function (expertise) {
    // find the item already listed
    $('#expertise_list').find('li').each(function (i) {
        if (expertise.value == $(this).data('value')) {
            // remove from select
            $('#id_expertise').find('option').each(function (i) {
                if (expertise.value == $(this).val()) {
                    $(this).remove();
                }
            });
            // then remove from list
            $(this).remove();
        }
    });
};

NIRIT.Company.Expertise.prototype.addExpertiseToList = function (expertise) {
    var self = this;

    // is the item already listed
    var list = [];
    $('#expertise_list').find('li').each(function (i) {
        list.push($(this));
    });
    for (var exp in list) {
        if (expertise.value == list[exp].data('value')) {
            return false;
        }
    };
    // if not, add it to the list
    var item = $('<li class="expertise-item">');
    item.data('value', expertise.value);
    item.text(expertise.label);
    var remove = $('<span class="remove">');
    remove.click(function (e) {
        self.removeExpertise(expertise);
    });
    item.append(remove);
    $('#expertise_list').append(item);
};

NIRIT.Company.Expertise.prototype.addExpertiseToSelect = function (expertise) {
    // is the item already listed
    var list = [];
    $('#id_expertise').find('option').each(function (i) {
        list.push($(this));
    });
    for (var exp in list) {
        if (expertise.value == list[exp].val()) {
            return false;
        }
    };
    // if not, add it to the select
    var item = $('<option>');
    item.attr('selected', 'selected');
    item.val(expertise.value);
    item.text(expertise.label);
    $('#id_expertise').append(item);
}

