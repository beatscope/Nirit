# nirit/fixtures.py
from django.conf import settings

""" Full list of Departments / Main Industries. """
DEPARTMENTS = (
(0, 'Accounting'),
(1, 'Airlines/Aviation'),
(2, 'Alternative Dispute Resolution'),
(3, 'Alternative Medicine'),
(4, 'Animation'),
(5, 'Apparel & Fashion'),
(6, 'Architecture & Planning'),
(7, 'Arts & Crafts'),
(8, 'Automotive'),
(9, 'Aviation & Aerospace'),
(10, 'Banking'),
(11, 'Biotechnology'),
(12, 'Broadcast Media'),
(13, 'Building Materials'),
(14, 'Business Supplies & Equipment'),
(15, 'Capital Markets'),
(16, 'Chemicals'),
(17, 'Civic & Social Organization'),
(18, 'Civil Engineering'),
(19, 'Commercial Real Estate'),
(20, 'Computer & Network Security'),
(21, 'Computer Games'),
(22, 'Computer Hardware'),
(23, 'Computer Networking'),
(24, 'Computer Software'),
(25, 'Construction'),
(26, 'Consumer Electronics'),
(27, 'Consumer Goods'),
(28, 'Consumer Services'),
(29, 'Cosmetics'),
(30, 'Dairy'),
(31, 'Defence & Space'),
(32, 'Design'),
(33, 'Education Management'),
(34, 'E-learning'),
(35, 'Electrical & Electronic Manufacturing'),
(36, 'Entertainment'),
(37, 'Environmental Services'),
(38, 'Events Services'),
(39, 'Executive Office'),
(40, 'Facilities Services'),
(41, 'Farming'),
(42, 'Financial Services'),
(43, 'Fine Art'),
(44, 'Fishery'),
(45, 'Food & Beverages'),
(46, 'Food Production'),
(47, 'Fundraising'),
(48, 'Furniture'),
(49, 'Gambling & Casinos'),
(50, 'Glass, Ceramics & Concrete'),
(51, 'Government Administration'),
(52, 'Government Relations'),
(53, 'Graphic Design'),
(54, 'Health, Wellness & Fitness'),
(55, 'Higher Education'),
(56, 'Hospital & Health Care'),
(57, 'Hospitality'),
(58, 'Human Resources'),
(59, 'Import & Export'),
(60, 'Individual & Family Services'),
(61, 'Industrial Automation'),
(62, 'Information Services'),
(63, 'Information Technology & Services'),
(64, 'Insurance'),
(65, 'International Affairs'),
(66, 'International Trade & Development'),
(67, 'Internet'),
(68, 'Investment Banking/Venture'),
(69, 'Investment Management'),
(70, 'Judiciary'),
(71, 'Law Enforcement'),
(72, 'Law Practice'),
(73, 'Legal Services'),
(74, 'Legislative Office'),
(75, 'Leisure & Travel'),
(76, 'Libraries'),
(77, 'Logistics & Supply Chain'),
(78, 'Luxury Goods & Jewellery'),
(79, 'Machinery'),
(80, 'Management Consulting'),
(81, 'Maritime'),
(82, 'Marketing & Advertising'),
(83, 'Market Research'),
(84, 'Mechanical or Industrial Engineering'),
(85, 'Media Production'),
(86, 'Medical Device'),
(87, 'Medical Practice'),
(88, 'Mental Health Care'),
(89, 'Military'),
(90, 'Mining & Metals'),
(91, 'Motion Pictures & Film'),
(92, 'Museums & Institutions'),
(93, 'Music'),
(94, 'Nanotechnology'),
(95, 'Newspapers'),
(96, 'Non-profit Organization Management'),
(97, 'Oil & Energy'),
(98, 'Online Publishing'),
(99, 'Outsourcing/Offshoring'),
(100, 'Package/Freight Delivery'),
(101, 'Packaging & Containers'),
(102, 'Paper & Forest Products'),
(103, 'Performing Arts'),
(104, 'Pharmaceuticals'),
(105, 'Philanthropy'),
(106, 'Photography'),
(107, 'Plastics'),
(108, 'Political Organization'),
(109, 'Primary/Secondary'),
(110, 'Printing'),
(111, 'Professional Training'),
(112, 'Program Development'),
(113, 'Public Policy'),
(114, 'Public Relations'),
(115, 'Public Safety'),
(116, 'Publishing'),
(117, 'Railroad Manufacture'),
(118, 'Ranching'),
(119, 'Real Estate'),
(120, 'Recreational Facilities & Services'),
(121, 'Religious Institutions'),
(122, 'Renewables & Environment'),
(123, 'Research'),
(124, 'Restaurants'),
(125, 'Retail'),
(126, 'Security & Investigations'),
(127, 'Semiconductors'),
(128, 'Shipbuilding'),
(129, 'Sporting Goods'),
(130, 'Sports'),
(131, 'Staffing & Recruiting'),
(132, 'Supermarkets'),
(133, 'Telecommunications'),
(134, 'Textiles'),
(135, 'Think Tanks'),
(136, 'Tobacco'),
(137, 'Translation & Localization'),
(138, 'Transportation/Trucking/Railroad'),
(139, 'Utilities'),
(140, 'Venture Capital'),
(141, 'Veterinary'),
(142, 'Warehousing'),
(143, 'Wholesale'),
(144, 'Wine & Spirits'),
(145, 'Wireless'),
(146, 'Writing & Editing'),
)

class Message(object):

    MESSAGES = {

        # Welcome
        'welcome': (
            '<h3>Why sign up to Nirit?</h3>'\
            + '<p><strong>Nirit</strong> is a <strong>Business-to-Business Network</strong>. '\
            + 'It aims to connect local businesses to each other, primarily based on location. '\
            + 'It allows businesses to find and communicate with suppliers and customers, '\
            + 'who might be very close, potentially in the same building, but otherwise might never find each other.</p>'\
            + '<h3>How does it work?</h3>'\
            + '<p><strong>Staff Members</strong> are authenticated by their work email addresses, '\
            + 'and anytime a coworker (someone from the same email domain, like @beatscope.co.uk) joins Nirit, '\
            + 'they automatically become a member of their associated Company, '\
            + 'and can instantly browse the <strong>Building Directory</strong>, and use the <strong>Notice Board</strong>.</p>'\
            + '<p><strong>Business Owners</strong> with a valid <strong>Authorization Code</strong> can create a Business Profile for their Company '\
            + 'by registering it with Nirit.</p>',
            'text'
        ),

        # Email domain match failed
        'email_failed': (
            '<h3>Email Domain Not Found</h3>'\
            + '<p>We did not find any company matching your email address.</p>'\
            + '<p>You might be using a private domain (such as google.com or outlook.com), or your company hasn\'t joined Nirit yet.</p>'\
            + '<p>Regardless, <a href="/contact">get in touch</a> so that we can help you get set up.</p>',
            'text'
        ),

        # Invalid Token
        'invalid_token': (
            '<h3>Invalid Authorization Code</h3>'\
            + '<p>The code you have entered is invalid. Please make sure you have typed it correctly.</p>'\
            + '<p>Contact us via <a href="/contact">this form</a> if you have any problems.</p>',
            'text'
        ),

        ### EMAILS ###

        # Activation Required Email (text)
        'email_activation_required_text': (
            'Hi {first_name}\n\n'\
            + 'An account has been created on Nirit using this email address.\n\n'\
            + 'Please click the following link to confirm your email address and activate your account and create a Business Profile.\n\n'\
            + '{link}\n\n'\
            + 'If you did not create this account please contact the Nirit team via support@nirit.co.uk.\n\n'\
            + 'The team @ Nirit',
            'text'
        ),

        # Activation Required Email (html)
        'email_activation_required_html': (
            'sign_up_activation_required.html',
            'file'
        ),

        # New Company Joined (text)
        'email_new_company_text': (
            '{name} has just joined Nirit.\n\n'\
            + 'Visit your account to activate this company: {link}\n\n'\
            + 'The team @ Nirit',
            'text'
        ),

        # New Company Joined (html)
        'email_new_company_html': (
            'new_company_joined.html',
            'file'
        ),

        # Sign up success (text)
        'email_sign_up_success_text': (
            '{name} has just joined {company}.\n\n'\
            + 'This user needs to be approved in order to access Nirit\'s features.\n\n'\
            + 'Visit {company}\'s Staff page to activate this account.\n'\
            + '{link}\n\n'\
            + 'The team @ Nirit',
            'text'
        ),

        # Sign up success (html)
        'email_sign_up_success_html': (
            'sign_up_new.html',
            'file'
        ),

        # Sign up failed (text)
        'email_sign_up_failed_text': (
            'A user has attempted to create an account.\n\n'\
            + 'The user might have an email address in a public domain (i.e. google.com). '\
            + 'In which case the Company would need to be created manually.\n\n'\
            + 'Please contact: {contact}\n\n'\
            + 'The team @ Nirit',
            'text'
        ),

        # Sign up failed (html)
        'email_sign_up_failed_html': (
            'sign_up_failed.html',
            'file'
        ),

        # Sign up activated (text)
        'email_sign_up_activated_text': (
            'Hi {first_name}\n\n'\
            + 'Your account on Nirit has been approved.\n\n'\
            + 'Please click the following link to access you profile:\n\n'\
            + '{link}\n\n'\
            + 'The team @ Nirit',
            'text'
        ),

        # Sign up activated (html)
        'email_sign_up_activated_html': (
            'sign_up_activated.html',
            'file'
        ),

        # contact Company (text)
        'email_company_contact_text': (
            '{name} has sent a message to {company} via Nirit.\n\n'\
            + '{subject}\n\n'\
            + 'Visit {name}\'s Profile: {link}\n\n'\
            + 'The team @ Nirit',
            'text'
        ),

        # Contact Company (html)
        'email_company_contact_html': (
            'company_contact.html',
            'file'
        ),

        # Contact Member(text)
        'email_member_contact_text': (
            '{name} from {company} has sent you a message via Nirit.\n\n'\
            + '{subject}\n\n'\
            + 'Visit {name}\'s Profile: {link}\n\n'\
            + 'The team @ Nirit',
            'text'
        ),

        # Contact Member (html)
        'email_member_contact_html': (
            'member_contact.html',
            'file'
        ),

    }

    def get(self, key, data={}):
        if self.MESSAGES.has_key(key):
            msg = self.MESSAGES[key]
            if msg[1] == 'file':
                html_file = open('{}/emails/{}'.format(settings.TEMPLATE_DIRS[0], msg[0]))
                html = html_file.read()
                html_file.close()
                if data:
                    html = html.format(**data)
                return html
            else:
                text = msg[0]
                if data:
                    text = text.format(**data)
                return text
        else:
            return ''
