# nirit/utils.py
"""
Common Utilities.

"""
import datetime
import json
import logging
import math
import re
import requests
import urllib2
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.conf import settings

logger = logging.getLogger('nirit.utils')


def validate_year(value):
    """
    Validator function:
    * Validates a valid four-digit year.
    * Must be a current or future year.
    """
    year_re = re.compile('^\d{4}$') # Matches any 4-digit number
    # If year does not match our regex
    if not year_re.match(str(value)):
        raise ValidationError(u'{} is not a valid year.'.format(value))
    # Check not after this year
    today = datetime.datetime.now()
    if int(value) > today.year:
        raise ValidationError(u'{} is in the future; please enter a current or past year.'.format(value))


def lookup_email(email):
    """
    Lookup through the Users list for emails with the same TLD.
    When one is found, its Company is returned,
    otherwise, return None.

    We assume the email is valid.

    """
    # Extract TLD
    # format: [nickname]@[tld]
    try:
        tld = email.split('@')[1]
    except IndexError:
        return None
    else:
        # Check whether the TLD belongs to a public domain
        domains = DomainParser().fetch()
        for domain in domains:
            pattern = r'{}'.format(re.escape(domain).replace('\*', '.*'))
            if re.match(pattern, tld) is not None:
                # This TLD belongs to the public domain
                return None
        # If this point is reached, the domain is private
        users = User.objects.filter(email__endswith=tld)\
                            .filter(groups__name__in=['Space Manager', 'Owner', 'Rep', 'Staff'])
        # Users with the same domain are supposed to belong to the same company
        if users:
            try:
                company = users[0].get_profile().company
                return company
            except:
                return None
    return None


BING_MAPS_KEY = settings.BING_MAPS_KEY
BING_MAPS_LOCATION_URL = 'http://dev.virtualearth.net/REST/v1/Locations'

def get_postcode_point(postcode):
    """
    Use the Bing Maps REST API to get the location point for a postcode.
    http(s)://msdn.microsoft.com/en-us/library/ff701714.aspx

    Return floating point minutes tuple: (latitude, longitude)

    """
    url = BING_MAPS_LOCATION_URL
    params = {
        'postalCode': postcode,
        'key': BING_MAPS_KEY
    }
    response = requests.get(url, params=params)
    if response.text:
        try:
            data = json.loads(response.text)
        except Exception:
            raise
        else:
            if data["statusCode"] != 200:
                raise Exception('API Error: {}'.format(data["statusDescription"]))
            try:
                coordinates = data["resourceSets"][0]["resources"][0]["point"]["coordinates"]
            except (IndexError, KeyError):
                raise Exception('API Error: {}'.format('Invalid postcode'))
            else:
                return (coordinates[0], coordinates[1])
    return (0, 0)


def get_postcodes_distance(postcode_from, postcode_to):
    """
    Calculates the distance between 2 postcodes,
    using the Haversine formula.

    Returns a tuple with kilometers and miles values.
    1Km is equivalent to 0.6214 miles.

    """
    point_from = get_postcode_point(postcode_from)
    point_to = get_postcode_point(postcode_to)
    return get_distance(point_from[0], point_from[1], point_to[0], point_to[1])


def get_distance(latitude_from, longitude_from, latitude_to, longitude_to):
    R = 6371;
    dLon = math.radians(longitude_to - longitude_from)
    dLat = math.radians(latitude_to - latitude_from)
    lat1 = math.radians(latitude_from);
    lat2 = math.radians(latitude_to);
    a = math.sin(dLat/2) * math.sin(dLat/2) \
      + math.sin(dLon/2) * math.sin(dLon/2) \
      * math.cos(lat1) * math.cos(lat2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c; # KM
    miles = distance * 0.6214
    return (distance, miles)


class Extractor(object):
    regex_tags = re.compile(r'(#[_\w-]+)')
    regex_flags = re.compile(r'(@[_\w-]+)')

    def __init__(self, string):
        self.string = string

    def extract_postcode(self):
        """
        Extract UK postcode.

        """
        outcode_pattern = '[A-PR-UWYZ]([0-9]{1,2}|([A-HIK-Y][0-9](|[0-9]|[ABEHMNPRVWXY]))|[0-9][A-HJKSTUW])'
        incode_pattern = '[0-9][ABD-HJLNP-UW-Z]{2}'
        postcode_re = re.compile(r'(GIR 0AA|%s %s)' % (outcode_pattern, incode_pattern))
        space_re = re.compile(r' *(%s)$' % incode_pattern)
        location = space_re.sub(r' \1', self.string.upper().strip())
        postcode = postcode_re.search(location)
        if postcode is not None:
            return postcode.group(1)
        return None


class DomainParser(object):
    """
    Uses public repo from SpamAssassin.
    @see: http://svn.apache.org/repos/asf/spamassassin/trunk/rules/20_freemail_domains.cf

    """
    
    def __init__(self):
        url = 'http://svn.apache.org/repos/asf/spamassassin/trunk/rules/20_freemail_domains.cf'
        request = urllib2.Request(url)
        opener = urllib2.build_opener()
        r = opener.open(request)
        self.domain = []
        for line in r.readlines():
            if line.startswith('freemail_domains'):
                domains = line.strip().split(' ')
                domains.pop(domains.index('freemail_domains')) # remove 'freemail_domains'
                self.domain.extend([d for d in domains if d]) # remove empty entries
        r.close()
    
    def fetch(self):
        return self.domain
