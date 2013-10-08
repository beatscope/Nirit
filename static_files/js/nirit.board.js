/**
 * Nirit - Notice Board Scripts
 * (c) 2013 Beatscope Limited | http://www.beatscope.co.uk/
 */

if (typeof(NIRIT) === 'undefined') {
    var NIRIT = {};
}

/**
 * The Board Class is in charge of maintaining an updatable list of notices.
 * It also provides helpers to fetch and display replies for these notices.
 *
 * @param object
 */
NIRIT.Board = function (settings) {
    this.data = settings['data'];
    this.buildings = settings['buildings'];
    this.token = settings['token'];
    this.filter = null;
    this.account = settings['account'];
    this.cards = [];
    this.more = null;

    this.loading = false;

    if (this.data.hasOwnProperty('results')) {
        this.cards = this.data.results;
        this.more = this.get_next_uri(this.data.next);
    }
    if (!this.data.hasOwnProperty('results') || this.data.results.length == 0) {
        this.cards.push({
            "subject": "There are currently no notices on this board."
        });
    }
    this.notices = settings['notices'];

    // Parse query string parameters
    if (document.location.search) {
        this.filter = document.location.search.split('=')[1];
    }

    // Counters (used by filters)
    // not enabled when query string parameters are given
    this.counters = {
        'latest': settings['count']
    };

    // We store the latest view into a cookie
    // this is the view we'll use to decide which notice/reply is new for a particular user
    this.view = $.cookie('notices');
    if (this.view) {
        this.view = JSON.parse(this.view);
    }
    $.cookie('notices', JSON.stringify(this.notices), {'expires': 30, 'path': '/'});

    // Add initial cards to the board
    this.add_notices();

    // Handle board-type specific features
    switch (settings['filter']['type']) {
        case 'building':
            this.building = settings['filter']['value'];
            // start listening for updates
            // only if we are looking at all notices
            if (document.location.search) {
                break;
            }
            this.listen();
            break;
    }

};

/**
 * Return formatted API URL, based on the pagination
 */
NIRIT.Board.prototype.get_next_uri = function (url) {
    if (!url) {
        return null;
    }
    var uri = '/api/notices?' + url.split('?')[1];
    return uri;
};

/**
 * Check for new notices.
 */
NIRIT.Board.prototype.listen = function () {
    var self = this;
    setInterval(function() {
        $.ajax({
            url: '/api/notices?building='+self.building,
            type: 'OPTIONS',
            contentType: "application/json; charset=UTF-8",
            dataType: "json",
            success: function (response) {
                var latest_diff = response['results']['all'] - self.counters['latest'];
                if (latest_diff > 0) {
                    $('#latest_count').find('span').css('visibility', 'visible');
                    $('#latest_count').find('span').html('('+latest_diff+')');
                    $('#latest_count').animate({
                        color: '#ced9e4',
                        backgroundColor: '#2e7ea0'
                    }, 250).animate({
                        color: '#1a5a74',
                        backgroundColor: '#e2e8ee'
                    }, 500, function () {
                        $(this).attr('style', '');
                    });
                }
            },
            error: function (e) {
                //console.log('FAILED -- ' + JSON.parse(e.responseText).detail);
            },
            headers: {
                "Authorization": "Token " + self.token
            }
        });
    }, 30000);
};

/**
 * Theme the card using the template,
 * then add it to the board.
 *
 * The update argument is set to true when called dynamically
 * i.e. when more cards are fetched.
 */
NIRIT.Board.prototype.add_notices = function (update) {

    // Append cards
    for (var card in this.cards) {
        var notice = this.apply_template(this.cards[card]);
        this.add_notice(notice);
        notice = null;

        if (typeof(update) !== 'undefined' && update) {
            // Flash all newly displayed cards
            this.flash_card(this.cards[card].id);
        }
    }

    // Bind listeners
    this.set_listeners();

    var plus = $('a#plus');
    plus.hide();

    // Check if additional notices are available
    if (this.more) {
        var self = this;
        plus.show().unbind('click').bind('click', function () {
            self.fetch(plus);
            return false;
        });
    }

};

NIRIT.Board.prototype.fetch = function (element, callback) {
    var self = this;
    if (!self.more) {
        return false;
    }
    element.addClass('loading');
    element.find('span').text('Loading more notices...');
    $.get(self.more, function (data) {
        element.removeClass('loading');
        element.find('span').text('More');

        // Update internal variables
        self.cards = data.results;
        self.more = self.get_next_uri(data.next);

        // Add new notices to board
        self.add_notices(true);

        // Remove the 'plus' icon if no more cards left
        if (!self.more) {
            element.hide();
        }

        // Bind new elements
        self.set_listeners();

        // Callback
        if (typeof(callback) === 'function') {
            callback();
        }

    }, 'json');
};

/**
 * Adds Replies to the target card on the board.
 * Reply cards are simpler to add, as they do not need any event handlers.
 */
NIRIT.Board.prototype.add_replies = function (uri, target) {
    var self = this;
    target.data('uri', uri); // store URI in target object context

    // Fetch replies
    target.parent().find('.plus').addClass('loading');
    target.parent().find('.plus').find('span').text('Loading more notices...');
    $.get(uri, function (data) {
        target.parent().find('.plus').removeClass('loading');
        target.parent().find('.plus').find('span').text('More');
        var cards = data.results;

        // Append cards
        for (var card in cards) {
            var notice = self.apply_template(cards[card], 'reply');
            self.add_notice(notice, target);
            notice = null;
            // Flash all newly displayed cards
            self.flash_card(cards[card].id, 500);
        }

        // Add pagination data to target element
        if (data.next) {
            target.parent().find('.plus').show().unbind('click').bind('click', function () {
                // re-create the URI based on the API pagination
                var uri = [];
                uri.push(target.data('uri').split('?')[0]);
                uri.push(data.next.split('?')[1]);
                uri = uri.join('?');
                self.add_replies(uri, target);
                return false;
            });
        } else {
            target.parent().find('.plus').hide();
        }
    }, 'json');
};

/**
 * Add HTML code to the board element
 */
NIRIT.Board.prototype.add_notice = function (html, target, before) {
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
 * Theme a card object into an HTML string
 */
NIRIT.Board.prototype.apply_template = function (card, template) {
    try {
        // Sender's display name
        var sender = card.sender.full_name;
        if (card.sender.is_admin) {
            sender = 'System Administrator';
        }
        // Card avatar
        // use company logo when sent officially
        // or when the card is an INTRO
        var avatar = card.sender.avatar;
        if ((card.official || card.type == 'INTRO') && card.sender.company.square_logo)  {
            avatar = card.sender.company.square_logo;
        }
    } catch (e) {
        var sender = null;
        var avatar = NIRIT.STATIC_URL + 'images/useravatar_60x60.png';
    }

    var card_tag = '<div id="card_' + card.id + '" class="card ';
    // Check if this card is new
    if (this.view) {
        if (typeof(template) === 'undefined') {
            if (!(card.id in this.view)) {
                card_tag += ' is-new';
            }
        }
    }
    card_tag += '">';

    // Card category
    card_tag += '<div class="category';
    switch (card.type) {
        case 'ALERT':
            card_tag += ' alert';
            break;
        case 'INTRO':
            card_tag += ' official';
            break;
        case 'NOTICE':
        default:
            if (card.official) {
                card_tag += ' official';
            }
            break;
    }
    card_tag += '"></div>';

    card_tag += '<div class="avatar"><img src="' + avatar + '" alt="' + sender + '" width="60px" height="auto" /></div>';

    // Subject is not shown on replies
    if (typeof(template) === 'undefined') {
        card_tag += '<div class="subject">' + card.subject + '</div>';
    }

    // The body is initially truncated to 255 characters
    var body = card.hasOwnProperty('body') ? card.body : false;
    if (body) {
        // Only truncate body on cards, not on reply cards
        if (typeof(template) === 'undefined') {
            var truncated = (body.length > 255) ? true : false;
            if (truncated) {
                card_tag += '<div class="body truncated">';
                card_tag += '<div class="hidden full-body">' + body + '</div>';
                card_tag += '<div class="truncated-body">' + body.substr(0, 255) + '...</div>';
                card_tag += '</div>';
            } else {
                card_tag += '<div class="body">' + body + '</div>';
            }
        } else {
            card_tag += '<div class="body">' + body + '</div>';
        }
    }

    // Sender
    if (sender) {
        card_tag += '<div class="age">' + card.age + ' ago</div>';
        if (card.sender.is_admin) {
            card_tag += '<div class="sender">' + sender + '</a>'
        } else if (card.official) {
            card_tag += '<div class="sender"><span><a href="/company/' + card.sender.company.slug + '">' + card.sender.company.name + '</span></a>';
            card_tag += ' - <a href="/member/' + card.sender.codename + '">' + sender + '</a>';
        } else {
            card_tag += '<div class="sender"><a href="/member/' + card.sender.codename + '">' + sender + '</a>';
            card_tag += ', <span><a href="/company/' + card.sender.company.slug + '">' + card.sender.company.name + '</a></span>';
        }
    }

    card_tag += '</div>';

    // The Reply/View Replies feature is
    //  - for notice cards only (not replies)
    //  - for all cards but ALERTs
    //  - for non-admins
    if (sender && card.type != 'ALERT' && !card.sender.is_admin && typeof(template) === 'undefined') {

        // Star/Reply/View Replies line
        card_tag += '<ul>';
        // -> replies
        if (card.replies.length > 0) {
            // Check if this card has got any new replies for this user?
            // 1. is the card in the view?
            // new cards will be flagged as new, so no need to flag the replies as well
            if (this.view) {
                if (card.id in this.view) {
                    // 2. when the number of replies in the view and for the card do not match,
                    // there are new replies for this user
                    if (this.view[card.id].length != card.replies.length) {
                        card_tag += '<li class="has-new"><span>new</span></li>';
                    }
                }
            }
            card_tag += '<li class="replies"><a href="" class="open-replies';
            card_tag += '" rel="' + card.id + '">';
            card_tag += card.replies.length;
            card_tag += '</a></li>';
        }
        // -> reply
        card_tag += '<li class="reply"><a href="" class="open-reply" rel="' + card.id + '"></a></li>';
        // -> star
        card_tag += '<li class="star"><a href="" class="star';
        if ($.inArray(card.id, this.account.starred) > -1) {
            card_tag += ' active"';
            card_tag += '" title="Unflag notice"';
        } else {
            card_tag += '" title="Flag notice"';
        }
        card_tag += ' rel="' + card.id + '">';
        card_tag += '</a></li>';
        card_tag += '</ul>';

        // Replies container
        card_tag += '<div class="card-replies hidden" rel="' + card.id + '">';
        card_tag += '<p class="box-title">All Replies <span class="close"></span></p>';
        card_tag += '<div class="card-replies-holder"></div>';
        card_tag += '<a href="" class="plus"><span>More</span></a>';
        card_tag += '</div>';

        // Reply box
        card_tag += '<div class="card-reply hidden" rel="' + card.id + '">';
        card_tag += '<p class="box-title">Leave a reply <span class="close"></span></p>';
        card_tag += '<textarea class="reply elastic" rows="2" cols="70"></textarea>';
        if ($.inArray('Owner', this.account.roles) > -1 || $.inArray('Rep', this.account.roles) > -1) {
            card_tag += '<div class="reply-as-org">';
            card_tag += '<label>';
            card_tag += '<input type="checkbox" class="reply-is-official"'
                     + ' name="' + this.account.company.name +'"'
                     + ' value="' + this.account.company.codename + '">'
                     + 'on behalf of <strong>' + this.account.company.name + '</strong>'
            card_tag += '</label>';
            card_tag += '</div>';
        }
        card_tag += '<button class="reply">Reply</button>';
        card_tag += '</div>';

    }

    card_tag += '</div>';
    return card_tag;
};

/**
 * Temporaily highlight a card
 */
NIRIT.Board.prototype.flash_card = function (card_id, delay) {
    var duration = 1000; //default animation length
    if (typeof(delay) !== 'undefined') {
        duration = delay;
    }
    var card = $('#card_'+card_id);
    card.addClass('highlight');
    setTimeout(function () {
        card.animate({
            backgroundColor: '#fff'
        }, duration, function () {
            $(this).removeClass('highlight');
            $(this).attr('style', '');
        });
    }, duration);
};

/**
 * Set/reset all event listeners.
 * Needs to be called every time new cards are added to the board.
 */
NIRIT.Board.prototype.set_listeners = function () {
    var self = this;
    var max_characters = 2000;

    // Expandable textareas
    $('.elastic').elastic();
    $('.elastic').each(function () {
        if ($(this).hasClass('no-limit')) {
            return;
        }
        var char_counter = $('<div>');
        char_counter.addClass('char_count');
        char_counter.html(max_characters);
        $(this).before(char_counter);
        // Disable new characters once limit is reached
        $(this).bind('keydown', function(e) {
            // once the limit has been reached, the following keyCodes needs to be enabled
            // to allow user to edit the text:
            //  - backspace     8
            //  - left          37
            //  - up            38
            //  - right         39
            //  - down          40
            //  - home          36
            //  - end           35
            //  - page up       33
            //  - page down     34
            if (parseInt(max_characters - $(this).val().length) <= 0 
                && (e.keyCode !== 8 && e.keyCode !== 37 && e.keyCode !== 38 && e.keyCode !== 39 && e.keyCode !== 40)) {
                return false;
            }
        });
        $(this).keyup(function () {
            char_counter.html(Math.max(0, max_characters - $(this).val().length));
            // when pasting, extra characters can still be inserted,
            // so we need to strip the text to make sure
            if ($(this).val().length > max_characters) {
                $(this).val($(this).val().substring(0, max_characters));
            }
        });
    });

    // New Notice
    $('#new_card').unbind('click').bind('click', function () {
        // clear content
        $('#add_card_subject').val('');
        $('#add_card_body').val('');
        if ($('.card-add').is(':visible')) {
            $('.card-add').slideUp(250);
        } else {
            $('.card-add').slideDown(250, function () {
                $('#add_card_subject').focus();
            });
        }
        return false;
    });
    $('.card-add').find('span.close').unbind('click').bind('click', function () {
        $('.card-add').slideUp(250);
    });
    $('#add_card').unbind('click').bind('click', function () {
        var subject = $('#add_card_subject').val();
        var body = $('#add_card_body').val();
        // we assume a user is a member of only 1 org
        var is_official = $('#add_is_official').is(':checked') ? 'on' : '';
        var type = $('#add_is_type').find('option:selected');
        type = type.length > 0 ? type.val() : null;
        if (subject.length > 0) {
            $.ajax({
                url: '/api/notices/post',
                data: JSON.stringify({
                    'subject': trim(subject),
                    'body': trim(body),
                    'buildings': self.buildings,
                    'official': is_official,
                    'type': type
                }),
                type: 'POST',
                contentType: "application/json; charset=UTF-8",
                dataType: "json",
                success: function (response) {
                    location.reload(true);
                },
                error: function (e) {
                    //console.log('FAILED -- ' + JSON.parse(e.responseText).detail);
                },
                headers: {
                    "Authorization": "Token " + self.token
                }
            });
        }
    });

    // Reply to Notice
    $('.open-reply').unbind('click').bind('click', function () {
        var _self = $(this);
        $('.card-reply').each(function() {
            // Accordion: close all other boxes
            if ($(this).attr('rel') == _self.attr('rel')) {
                if ($(this).is(':visible')) {
                    $(this).slideUp();
                } else {
                    // clear content before opening
                    $(this).find('textarea').val('');
                    $(this).slideDown(250, function () {
                        $(this).find('textarea').focus();
                    });
                }
            } else {
                $(this).slideUp(250);
            }
        });
        return false;
    });
    $('.card-reply').find('span.close').unbind('click').bind('click', function () {
        $('.card-reply').slideUp(250);
    });
    $('.card-reply').each(function() {
        var _self = $(this);
        $(this).attr('card_id', $(this).attr('rel'));
        $(this).find('button').unbind('click').bind('click', function () {
            var subject = null;
            // Find the subject of the card being replied to
            for (var c in self.cards) {
                if (self.cards[c].id == _self.attr('card_id')) {
                    subject = self.cards[c].subject;
                    break;
                }
            }
            var body = _self.find('textarea').val();
            // we assume a user is a member of only 1 org
            var is_official = _self.find('.reply-is-official').is(':checked') ? 'on' : '';
            if (subject && body.length > 0) {
                $.ajax({
                    url: '/api/notices/post',
                    data: JSON.stringify({
                        'subject': subject,
                        'body': trim(body),
                        'buildings': self.buildings,
                        'official': is_official,
                        'nid': _self.attr('card_id')
                    }),
                    type: 'POST',
                    contentType: "application/json; charset=UTF-8",
                    dataType: "json",
                    success: function (response) {
                        // Reload page to get 1 ad impression
                        location.reload(true);
                    },
                    error: function (e) {
                        //console.log('FAILED -- ' + JSON.parse(e.responseText).detail);
                    },
                    headers: {
                        "Authorization": "Token " + self.token
                    }
                });
            }
        });
    });

    // View Notice Replies
    $('.open-replies').unbind('click').bind('click', function () {
        var _self = $(this);
        $('.card-replies').each(function() {
            var card = $(this);
            if (card.attr('rel') == _self.attr('rel')) {
                if (card.is(':visible')) {
                    card.slideUp();
                } else {
                    card.find('.card-replies-holder').empty(); // empty container
                    card.slideDown(250, function () {
                        card.find('.card-replies-holder').each(function () {
                            var holder = $(this);
                            var uri = '/api/notices/' + _self.attr('rel') + '/';
                            self.add_replies(uri, holder);
                        });
                    });
                }
            } else {
                $(this).slideUp(250);
            }
        });
        return false;
    });
    $('.card-replies').find('span.close').unbind('click').bind('click', function () {
        $('.card-replies').slideUp(250);
    });

    // Mark card as READ
    $('.card.is-new').unbind('click').bind('click', function () {
        var _self = $(this);
        _self.animate({ 
            backgroundColor:'#fff'
        }, 500, function () {
            _self.removeClass('is-new');
        });
    });

    // Expand/Collapse
    $('.body.truncated').each(function () {
        var _self = $(this);
        _self.find('.label').remove(); // remove existing labels first
        var button = $('<span class="label">expand</span>');
        // no need to unbind the event as this element is entirely re-created
        button.bind('click', function () {
            if (_self.hasClass('open')) {
                // close
                _self.find('.full-body').hide();
                _self.find('.truncated-body').show();
                _self.removeClass('open');
                button.text('expand');
            } else {
                // open
                _self.find('.truncated-body').hide();
                _self.find('.full-body').show();
                _self.addClass('open');
                button.text('collapse');
            }
        });

        button.appendTo(_self);
    });

    // Flag/Unflag Notices
    $('a.star').unbind('click').bind('click', function () {
        var _self = $(this);
        NIRIT.utils.set_member_preference('starred', _self.attr('rel'), function (data) {
            if (_self.hasClass('active')) { _self.removeClass('active'); }
            else { _self.addClass('active'); }
        });
        return false;
    });

    // Fetch more when end of page is reached
    $(window).scroll(function() {
        if (!self.loading) {
            var trigger = $("body").height() - 173;
            if ($(document).scrollTop() + $(window).height() >= trigger) {
                var plus = $('a#plus');
                self.loading = true;
                self.fetch(plus, function () {
                    console.log('Done');
                    self.loading = false;
                });
            }
        }
    });

};
