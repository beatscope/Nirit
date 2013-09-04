/**
 * Nirit - Directory Scripts
 * (c) 2013 Beatscope Limited | http://www.beatscope.co.uk/
 */

if (typeof(NIRIT) === 'undefined') {
    var NIRIT = {};
}

/**
 * The Directory Class is in charge of displaying the directory results,
 * filtering/selection, and pagination.
 *
 * @param object
 */
NIRIT.Directory = function (settings) {
    this.data = settings['data'];
    this.group = settings['group'];
    this.groups = this.data.results;
    // Add company cards
    this.add_cards();
};

/**
 * Theme the card using the template,
 * then add it to the directory.
 *
 * The update argument is set to true when called dynamically
 * i.e. when more cards are fetched.
 */
NIRIT.Directory.prototype.add_cards = function (update) {

    // Add results count
    var counter = '<div class="counter box"><span>' + this.data.count + '</span> results</div>';
    this.insert(counter);

    // Create group of cards
    for (var g in this.groups) {
        var group = this.apply_template({
            'label': this.groups[g]['label'],
            'cards': this.groups[g]['results']
        }, this.group + '-group');
        this.insert(group);
        group = null;
    }

    // Check if additional notices are available
    if (this.data.next) {
        var self = this;
        var plus = $('#plus');
        plus.show().unbind('click').bind('click', function () {
            $.get(self.data.next, function (data) {

                // Update internal variables
                self.data = data;
                self.groups = data.results;

                // Add new notices to board
                self.add_cards(true);

                // Remove the 'plus' icon if no more cards left
                if (!self.data.next) {
                    plus.hide();
                }

                // Bind new elements
                //self.set_listeners();

            }, 'json');
            return false;
        });
    }

};

/**
 * Insert HTML code.
 */
NIRIT.Directory.prototype.insert = function (html, target, before) {
    if (typeof(target) === 'undefined' || target === null) {
        target = $('#stream');
    }
    if (typeof(before) !== 'undefined' && before == true) {
        target.prepend(html);
    } else {
        target.append(html);
    }
};


/**
 * Theme an object into an HTML string
 */
NIRIT.Directory.prototype.apply_template = function (object, template) {
    var html = '';
    switch (template) {

        case 'floor-group':
            html += '<div class="box padded">';
            html += '<h3>' + object['label'] + '</h3>';
            for (var c in object['cards']) {
                var card = this.apply_template(object['cards'][c], 'company');
                html += card;
                card = null;
            }
            html += '</div>';
            break;

        case 'department-group':
            html += '<div class="box padded">';
            html += '<h3>' + object['label'] + '</h3>';
            for (var c in object['cards']) {
                var card = this.apply_template(object['cards'][c], 'company');
                html += card;
                card = null;
            }
            html += '</div>';
            break;

        case 'name-group':
            html += '<div class="box padded">';
            html += '<h3>' + object['label'] + '</h3>';
            for (var c in object['cards']) {
                var card = this.apply_template(object['cards'][c], 'company');
                html += card;
                card = null;
            }
            html += '</div>';
            break;

        case 'company':
            html += '<div>';
            html += '<a href="/company/' + object.slug + '" title="' + object.name + '">' + object.name + '</a>';
            html += '</div>';
            break;

    }
    return html;
};
