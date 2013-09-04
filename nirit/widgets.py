# nirit/widgets.py
"""
HTML Widget classes

"""
import logging
from django.conf import settings
from django.utils.html import escape, conditional_escape
from django.utils.translation import ugettext, ugettext_lazy
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.forms.widgets import FileInput, CheckboxInput

logger = logging.getLogger('nirit.widgets')

FILE_INPUT_CONTRADICTION = object()

class ImageWidget(FileInput):
    template_with_initial = u'<div>%(clear_template)s</div><div>%(initial)s</div><div id="%(change_id)s">Change: %(input)s</div>'
    template_with_clear = u'%(clear)s <label for="%(clear_checkbox_id)s">Remove</label>'

    def clear_checkbox_name(self, name):
        """
        Given the name of the file input, return the name of the clear checkbox
        input.
        """
        return name + '-clear'

    def clear_checkbox_id(self, name):
        """
        Given the name of the clear checkbox input, return the HTML id for it.
        """
        return name + '_id'

    def render(self, name, value, attrs=None):
        substitutions = {
            'clear_template': '',
        }
        template = u'%(input)s'
        substitutions['input'] = super(ImageWidget, self).render(name, value, attrs)

        if value and hasattr(value, "url"):
            template = self.template_with_initial
            substitutions['initial'] = '<img src="{}" class="{}-edit" />'.format(escape(value.url), name)
            substitutions['change_id'] = "{}_change".format(name)
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                substitutions['clear'] = CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
                substitutions['clear_template'] = self.template_with_clear % substitutions

        return mark_safe(template % substitutions)

    def value_from_datadict(self, data, files, name):
        upload = super(ImageWidget, self).value_from_datadict(data, files, name)
        if not self.is_required and CheckboxInput().value_from_datadict(
            data, files, self.clear_checkbox_name(name)):
            if upload:
                # If the user contradicts themselves (uploads a new file AND
                # checks the "clear" checkbox), we return a unique marker
                # object that FileField will turn into a ValidationError.
                return FILE_INPUT_CONTRADICTION
            # False signals to clear any existing value, as opposed to just None
            return False
        return upload
