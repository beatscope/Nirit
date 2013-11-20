# nirit/uploads.py
"""
Django views to handle Uploads via AJAX.

"""
import os
import re
import time
import logging
from io import FileIO, BufferedWriter
from django.utils import simplejson as json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseBadRequest, Http404, HttpResponseNotAllowed
from django.conf import settings
from PIL import Image
from nirit import models

logger = logging.getLogger('nirit.uploads')


class UploadStorage(object):
    BUFFER_SIZE = 10485760  # 10MB

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.size = None

    def set_size(self, width, height):
        self.size = int(width), int(height)
        #logger.debug(self.size)

    def setup(self, filename, upload_to):
        """ Creates the filename on the system, along with the required folder structure. """
        self.filename = filename
        self.upload_to = upload_to
        #logger.debug('File: '+self.filename)
        self._path = self.update_filename()
        #logger.debug('Dir: '+self._dir)
        #logger.debug('Path: '+self._path)
        #logger.debug(os.path.realpath(os.path.dirname(self._path)))
        try:
            os.makedirs(os.path.realpath(os.path.dirname(self._path)))
        except:
            pass
        self._dest = BufferedWriter(FileIO(self._path, "w"))

    def upload_chunk(self, chunk, *args, **kwargs):
        self._dest.write(chunk)

    def upload_complete(self):
        path = settings.MEDIA_URL + "/" + self.upload_to + "/" + self.filename
        self._dest.close()
        return {"path": path}

    def update_filename(self):
        """
        Returns a new name for the file being uploaded.
        Ensure file with name doesn't exist, and if it does,
        create a unique filename to avoid overwriting

        """
        unique_filename = False
        filename_suffix = 0

        # remove trailing current folder if given
        if self.upload_to[:2] == './':
            self.upload_to = self.upload_to[2:]
        # format upload path with date formats
        self.upload_to = time.strftime(self.upload_to)
        self._dir = os.path.join(settings.MEDIA_ROOT, self.upload_to)
        #logger.debug('Upload to: '+self._dir)

        # Check if file at filename exists)
        if os.path.isfile(os.path.join(self._dir, self.filename)):
            #logger.debug('this file already exists')
            while not unique_filename:
                try:
                    if filename_suffix == 0:
                        open(os.path.join(self._dir, self.filename))
                    else:
                        filename_no_extension, extension = os.path.splitext(self.filename)
                        open(os.path.join(self._dir, "{}_{}{}".format(filename_no_extension, str(filename_suffix), extension)))
                    filename_suffix += 1
                except IOError:
                    unique_filename = True

        if filename_suffix > 0:
            self.filename = "{}_{}{}".format(filename_no_extension, str(filename_suffix), extension)
        return os.path.join(self._dir, self.filename)

    def upload(self, uploaded, raw_data):
        try:
            if raw_data:
                # File was uploaded via ajax, and is streaming in.
                chunk = uploaded.read(self.BUFFER_SIZE)
                while len(chunk) > 0:
                    self.upload_chunk(chunk)
                    chunk = uploaded.read(self.BUFFER_SIZE)
            else:
                # File was uploaded via a POST, and is here.
                for chunk in uploaded.chunks():
                    self.upload_chunk(chunk)
            # make sure the file is closed
            self._dest.close()
            # file has been uploaded
            self.filename = os.path.join(settings.MEDIA_URL, self.upload_to, self.filename)
            image = Image.open(self._path)
            #logger.debug("{} {} {}".format(image.format, image.size, image.mode))
            # resize image
            if self.size:
                #logger.debug(self.size)
                image = image.convert('RGBA')
                # the image is resized using the minimum dimension
                width, height = self.size
                if image.size[0] < image.size[1]:
                    # the height is bigger than the width
                    # we set the maximum height to the original height,
                    # so that the image fits the width
                    height = image.size[1]
                elif image.size[0] > image.size[1]:
                    # the width is bigger than the height
                    # we set the maximum width to the original width,
                    # so that the image fits the height
                    width = image.size[0]
                else:
                    # we have a square
                    pass
                image.thumbnail((width, height), Image.ANTIALIAS)
                # if the image is not a square, we crop the exceeding width/length as required,
                # to fit the square
                if image.size[0] != image.size[1]:
                    # we crop in the middle of the image
                    if self.size[0] == image.size[0]:
                        # the width fits the container, center the height
                        x0 = 0
                        y0 = (image.size[1] / 2) - (self.size[1] / 2)
                        x1 = self.size[0]
                        y1 = y0 + self.size[1]
                    else:
                        # center the width
                        x0 = (image.size[0] / 2) - (self.size[0] / 2)
                        y0 = 0
                        x1 = x0 + self.size[0]
                        y1 = self.size[1] 
                    box = (x0, y0, x1, y1)
                    region = image.crop(box)
                    background = Image.new('RGBA', size = self.size, color = (255, 255, 255, 0))
                    background.paste(region, (0, 0))
                    #logger.debug("{} {} {}".format(background.format, background.size, background.mode))
                    background.save(self._path)
                else:
                    image.save(self._path)
            return True
        except Exception as e:
            logger.error(e)
            return False


class FileUploader(object):
    def __init__(self):
        self.storage = UploadStorage()

    def __call__(self, request):
        return self._ajax_upload(request)

    def _ajax_upload(self, request):
        if request.method == "POST":
            # determine which model and field this upload relates to
            try:
                model = request.POST['model']
                field = request.POST['field']
            except KeyError:
                return HttpResponseBadRequest("AJAX request not valid")
            else:
                # is the field one of the fields allowed?
                if field not in ('logo','square_logo','thumbnail'):
                    return HttpResponseBadRequest("AJAX request not valid")

            if request.is_ajax():
                # /!\ try this with Chrome / this is HTML5
                # the file is stored raw in the request
                is_raw = True
                upload = request
                try:
                    filename = request.POST['file']
                except KeyError:
                    return HttpResponseBadRequest("AJAX request not valid")
            # not an ajax upload, so it was the "basic" iframe version with
            # submission via form
            else:
                is_raw = False
                if len(request.FILES) == 1:
                    # FILES is a dictionary in Django but Ajax Upload gives
                    # the uploaded file an ID based on a random number, so it
                    # cannot be guessed here in the code. Rather than editing
                    # Ajax Upload to pass the ID in the querystring, observe
                    # that each upload is a separate request, so FILES should
                    # only have one entry. Thus, we can just grab the first
                    # (and only) value in the dict.
                    upload = request.FILES.values()[0]
                    filename = upload.name
                else:
                    raise Http404("Bad Upload")

            # we have a filename, now determine where to put it
            # first, we need to figure out what model this refers to
            #logger.debug(model + '/' + field)
            try:
                _model = getattr(models, model)
                upload_to = _model._meta.get_field(field).upload_to
            except Exception as e:
                logger.error(e)
                return HttpResponseBadRequest("Bad Request")

            # do we need to resize the image?
            width = request.POST['width'] if request.POST.has_key('width') else None
            height = request.POST['height'] if request.POST.has_key('height') else None
            if width and height:
                self.storage.set_size(width, height)

            # save the file
            self.storage.setup(filename, upload_to)
            success = self.storage.upload(upload, is_raw)
            ret_json = {'success': success, 'filename': self.storage.filename}
            return HttpResponse(json.dumps(ret_json, cls=DjangoJSONEncoder), content_type='application/json; charset=utf-8')
        else:
            response = HttpResponseNotAllowed(['POST'])
            response.write("Only POST allowed")
            return response
