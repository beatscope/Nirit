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
    this.space = settings['space'];
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
    var counter = '<div class="counter"><span>' + this.data.count + '</span> ';
    counter += this.data.count > 1 ? 'companies' : 'company';
    counter += ' listed.</div>';
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
            html += '<div class="card">';
            html += '<h3>' + object['label'] + '</h3>';
            for (var c in object['cards']) {
                var card = this.apply_template(object['cards'][c], 'company');
                html += card;
                card = null;
            }
            html += '</div>';
            break;

        case 'department-group':
            html += '<div class="card">';
            html += '<h3>' + object['label'] + '</h3>';
            for (var c in object['cards']) {
                var card = this.apply_template(object['cards'][c], 'company');
                html += card;
                card = null;
            }
            html += '</div>';
            break;

        case 'name-group':
            html += '<div class="card">';
            html += '<h3>' + object['label'] + '</h3>';
            for (var c in object['cards']) {
                var card = this.apply_template(object['cards'][c], 'company');
                html += card;
                card = null;
            }
            html += '</div>';
            break;

        case 'company':
            var floor = ( object.hasOwnProperty('floor_tag') && typeof(object.floor_tag) !== 'undefined' ) ? object.floor_tag : null;
            var square_logo =  NIRIT.STATIC_URL  + 'images/nirit-icon-32x32-grey.png';
            if (object.square_logo) {
                square_logo = object.square_logo;
            }
            html += '<div class="company-item">';
            html += '<img src="' + square_logo + '" alt="" width="32" height="32" />';
            html += '<div class="company-info">';
            html += '<div class="company-name"><a href="/company/' + object.slug + '" title="' + object.name + '">' + object.name + '</a></div>';
            if (floor && this.group != 'floor') {
                html += '<div class="company-floor">' + floor + ' Floor</div>';
            }
            if (this.group != 'department') {
                html += '<div class="company-department">' + object.department + '</div>';
            }
            html += '<div class="company-expertise">' + object.expertise.join(', ') + '</div>';
            html += '</div>';
            html += '</div>';
            break;

    }
    return html;
};
