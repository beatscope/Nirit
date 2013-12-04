# nirit/fixtures.py
from django.template import loader
from django.conf import settings


class Message(object):

    MESSAGES = {

        ### Sign-up Messages ###
        'welcome': 'welcome.html',                                              # Welcome message on Sign-up page
        'welcome/join': 'welcome_join.html',                                    # Welcome message on Join Space page
        'email_failed': 'email_failed.html',                                    # Email domain match failed message on Sign-up page
        'invalid_token': 'invalid_token.html',                                  # Invalid Token message on Sign-up page

        ### Emails ###
        'email_register_interest_text': 'emails/register_interest.txt',         # Home page widget email (text)
        'email_activation_required_text': 'emails/activation_required.txt',     # Activation Required Email (text)
        'email_activation_required_html': 'emails/activation_required.html',    # Activation Required Email (html)
        'email_new_company_text': 'emails/new_company_joined.txt',              # New Company Joined (text)
        'email_new_company_html': 'emails/new_company_joined.html',             # New Company Joined (html)
        'email_sign_up_success_text': 'emails/sign_up_new.txt',                 # Sign up success (text)
        'email_sign_up_success_html': 'emails/sign_up_new.html',                # Sign up success (html)
        'email_sign_up_failed_text': 'emails/sign_up_failed.txt',               # Sign up failed (text)
        'email_sign_up_failed_html': 'emails/sign_up_failed.html',              # Sign up failed (html)
        'email_sign_up_activated_text': 'emails/sign_up_activated.txt',         # Sign up activated (text)
        'email_sign_up_activated_html': 'emails/sign_up_activated.html',        # Sign up activated (html)
        'email_company_contact_text': 'emails/company_contact.txt',             # Contact Company (text)
        'email_company_contact_html': 'emails/company_contact.html',            # Contact Company (html)
        'email_invite_members_text': 'emails/invite_members.txt',               # Invite Members (text)
        'email_invite_members_html': 'emails/invite_members.html',              # Invite Members (html)
        'email_invite_company_text': 'emails/invite_company.txt',               # Invite Company (text)
        'email_invite_company_html': 'emails/invite_company.html',              # Invite Company (html)
        'email_member_contact_text': 'emails/member_contact.txt',               # Contact Member (text)
        'email_member_contact_html': 'emails/member_contact.html',              # Contact Member (html)
        'email_supplier_details_text': 'emails/supplier_details.txt',           # Supplier Request - New/Edit (text)
        'email_supplier_details_html': 'emails/supplier_details.html',          # Supplier Request - New/Edit (html)

    }

    def get(self, key, data={}):
        if self.MESSAGES.has_key(key):
            filename = self.MESSAGES[key]
            content = loader.render_to_string('messages/{}'.format(filename), data)
            return content
        else:
            return ''


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

""" Full list of Supplier Types. """
SUPPLIER_TYPES = (
(0, 'Miscellaneous'),
(1, 'Bar'),
(2, 'Coffee Shop'),
(3, 'Restaurant'),
(4, 'Takeaway'),
(5, 'Post Office'),
(6, 'Club'),
(7, 'Pub'),
(8, 'Shopping'),
(9, 'Stationary'),
(10, 'Dry Cleaning'),
(11, 'Gym'),
(12, 'Street Food'),
)
