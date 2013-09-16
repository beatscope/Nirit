# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Expertise'
        db.create_table(u'nirit_expertise', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
        ))
        db.send_create_signal(u'nirit', ['Expertise'])

        # Adding model 'Notice'
        db.create_table(u'nirit_notice', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('body', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('type', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('is_official', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_reply', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('reply_to', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['nirit.Notice'], null=True)),
        ))
        db.send_create_signal(u'nirit', ['Notice'])

        # Adding model 'Organization'
        db.create_table(u'nirit_organization', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('codename', self.gf('django.db.models.fields.CharField')(max_length=64, unique=True, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('created', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('logo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('square_logo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('department', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('size', self.gf('django.db.models.fields.CharField')(max_length=1, null=True)),
            ('founded', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
        ))
        db.send_create_signal(u'nirit', ['Organization'])

        # Adding M2M table for field expertise on 'Organization'
        db.create_table(u'nirit_organization_expertise', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm[u'nirit.organization'], null=False)),
            ('expertise', models.ForeignKey(orm[u'nirit.expertise'], null=False))
        ))
        db.create_unique(u'nirit_organization_expertise', ['organization_id', 'expertise_id'])

        # Adding model 'Building'
        db.create_table(u'nirit_building', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('codename', self.gf('django.db.models.fields.CharField')(max_length=64, unique=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'nirit', ['Building'])

        # Adding M2M table for field notices on 'Building'
        db.create_table(u'nirit_building_notices', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('building', models.ForeignKey(orm[u'nirit.building'], null=False)),
            ('notice', models.ForeignKey(orm[u'nirit.notice'], null=False))
        ))
        db.create_unique(u'nirit_building_notices', ['building_id', 'notice_id'])

        # Adding model 'CompanyProfile'
        db.create_table(u'nirit_companyprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('organization', self.gf('django.db.models.fields.related.ForeignKey')(related_name='company_profile', to=orm['nirit.Organization'])),
            ('building', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='building_profile', null=True, to=orm['nirit.Building'])),
            ('floor', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'nirit', ['CompanyProfile'])

        # Adding model 'OToken'
        db.create_table(u'nirit_otoken', (
            ('key', self.gf('django.db.models.fields.CharField')(max_length=14, primary_key=True)),
            ('building', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['nirit.Building'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('redeemed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'nirit', ['OToken'])

        # Adding model 'UserProfile'
        db.create_table(u'nirit_userprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='profile', unique=True, to=orm['auth.User'])),
            ('codename', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('company', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='company', null=True, on_delete=models.SET_NULL, to=orm['nirit.Organization'])),
            ('building', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['nirit.Building'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('thumbnail', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('job_title', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('bio', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'nirit', ['UserProfile'])

        # Adding M2M table for field starred on 'UserProfile'
        db.create_table(u'nirit_userprofile_starred', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm[u'nirit.userprofile'], null=False)),
            ('notice', models.ForeignKey(orm[u'nirit.notice'], null=False))
        ))
        db.create_unique(u'nirit_userprofile_starred', ['userprofile_id', 'notice_id'])

        # Adding M2M table for field networked on 'UserProfile'
        db.create_table(u'nirit_userprofile_networked', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm[u'nirit.userprofile'], null=False)),
            ('organization', models.ForeignKey(orm[u'nirit.organization'], null=False))
        ))
        db.create_unique(u'nirit_userprofile_networked', ['userprofile_id', 'organization_id'])

        # Adding model 'Page'
        db.create_table(u'nirit_page', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('slug', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('body', self.gf('markitup.fields.MarkupField')(no_rendered_field=True)),
            ('status', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('_body_rendered', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'nirit', ['Page'])


    def backwards(self, orm):
        # Deleting model 'Expertise'
        db.delete_table(u'nirit_expertise')

        # Deleting model 'Notice'
        db.delete_table(u'nirit_notice')

        # Deleting model 'Organization'
        db.delete_table(u'nirit_organization')

        # Removing M2M table for field expertise on 'Organization'
        db.delete_table('nirit_organization_expertise')

        # Deleting model 'Building'
        db.delete_table(u'nirit_building')

        # Removing M2M table for field notices on 'Building'
        db.delete_table('nirit_building_notices')

        # Deleting model 'CompanyProfile'
        db.delete_table(u'nirit_companyprofile')

        # Deleting model 'OToken'
        db.delete_table(u'nirit_otoken')

        # Deleting model 'UserProfile'
        db.delete_table(u'nirit_userprofile')

        # Removing M2M table for field starred on 'UserProfile'
        db.delete_table('nirit_userprofile_starred')

        # Removing M2M table for field networked on 'UserProfile'
        db.delete_table('nirit_userprofile_networked')

        # Deleting model 'Page'
        db.delete_table(u'nirit_page')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'nirit.building': {
            'Meta': {'object_name': 'Building'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'notices': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['nirit.Notice']", 'null': 'True', 'blank': 'True'})
        },
        u'nirit.companyprofile': {
            'Meta': {'object_name': 'CompanyProfile'},
            'building': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'building_profile'", 'null': 'True', 'to': u"orm['nirit.Building']"}),
            'floor': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'company_profile'", 'to': u"orm['nirit.Organization']"}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'nirit.expertise': {
            'Meta': {'ordering': "['title']", 'object_name': 'Expertise'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        },
        u'nirit.notice': {
            'Meta': {'object_name': 'Notice'},
            'body': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_official': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_reply': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reply_to': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['nirit.Notice']", 'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'nirit.organization': {
            'Meta': {'object_name': 'Organization'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'department': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'expertise': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['nirit.Expertise']", 'null': 'True', 'blank': 'True'}),
            'founded': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'size': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True'}),
            'square_logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'nirit.otoken': {
            'Meta': {'object_name': 'OToken'},
            'building': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['nirit.Building']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '14', 'primary_key': 'True'}),
            'redeemed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        u'nirit.page': {
            'Meta': {'object_name': 'Page'},
            '_body_rendered': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'body': ('markitup.fields.MarkupField', [], {'no_rendered_field': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'status': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        u'nirit.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'bio': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'building': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['nirit.Building']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'codename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'company'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['nirit.Organization']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_title': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'networked': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'networked'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['nirit.Organization']"}),
            'starred': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['nirit.Notice']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['nirit']