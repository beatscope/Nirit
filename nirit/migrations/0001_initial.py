# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Expertise'
        db.create_table('nirit_expertise', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
        ))
        db.send_create_signal('nirit', ['Expertise'])

        # Adding model 'Notice'
        db.create_table('nirit_notice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('type', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('is_official', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_reply', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('reply_to', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['nirit.Notice'], null=True)),
        ))
        db.send_create_signal('nirit', ['Notice'])

        # Adding model 'Organization'
        db.create_table('nirit_organization', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('codename', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('department', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('size', self.gf('django.db.models.fields.CharField')(max_length=1, null=True)),
            ('founded', self.gf('django.db.models.fields.DateField')(null=True)),
            ('floor', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('nirit', ['Organization'])

        # Adding M2M table for field members on 'Organization'
        db.create_table('nirit_organization_members', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['nirit.organization'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('nirit_organization_members', ['organization_id', 'user_id'])

        # Adding M2M table for field expertise on 'Organization'
        db.create_table('nirit_organization_expertise', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('organization', models.ForeignKey(orm['nirit.organization'], null=False)),
            ('expertise', models.ForeignKey(orm['nirit.expertise'], null=False))
        ))
        db.create_unique('nirit_organization_expertise', ['organization_id', 'expertise_id'])

        # Adding model 'Building'
        db.create_table('nirit_building', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('codename', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
        ))
        db.send_create_signal('nirit', ['Building'])

        # Adding M2M table for field organizations on 'Building'
        db.create_table('nirit_building_organizations', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('building', models.ForeignKey(orm['nirit.building'], null=False)),
            ('organization', models.ForeignKey(orm['nirit.organization'], null=False))
        ))
        db.create_unique('nirit_building_organizations', ['building_id', 'organization_id'])

        # Adding M2M table for field notices on 'Building'
        db.create_table('nirit_building_notices', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('building', models.ForeignKey(orm['nirit.building'], null=False)),
            ('notice', models.ForeignKey(orm['nirit.notice'], null=False))
        ))
        db.create_unique('nirit_building_notices', ['building_id', 'notice_id'])

        # Adding model 'UserProfile'
        db.create_table('nirit_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('building', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['nirit.Building'], null=True)),
        ))
        db.send_create_signal('nirit', ['UserProfile'])

        # Adding M2M table for field starred on 'UserProfile'
        db.create_table('nirit_userprofile_starred', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm['nirit.userprofile'], null=False)),
            ('notice', models.ForeignKey(orm['nirit.notice'], null=False))
        ))
        db.create_unique('nirit_userprofile_starred', ['userprofile_id', 'notice_id'])

        # Adding M2M table for field networked on 'UserProfile'
        db.create_table('nirit_userprofile_networked', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm['nirit.userprofile'], null=False)),
            ('organization', models.ForeignKey(orm['nirit.organization'], null=False))
        ))
        db.create_unique('nirit_userprofile_networked', ['userprofile_id', 'organization_id'])


    def backwards(self, orm):
        # Deleting model 'Expertise'
        db.delete_table('nirit_expertise')

        # Deleting model 'Notice'
        db.delete_table('nirit_notice')

        # Deleting model 'Organization'
        db.delete_table('nirit_organization')

        # Removing M2M table for field members on 'Organization'
        db.delete_table('nirit_organization_members')

        # Removing M2M table for field expertise on 'Organization'
        db.delete_table('nirit_organization_expertise')

        # Deleting model 'Building'
        db.delete_table('nirit_building')

        # Removing M2M table for field organizations on 'Building'
        db.delete_table('nirit_building_organizations')

        # Removing M2M table for field notices on 'Building'
        db.delete_table('nirit_building_notices')

        # Deleting model 'UserProfile'
        db.delete_table('nirit_userprofile')

        # Removing M2M table for field starred on 'UserProfile'
        db.delete_table('nirit_userprofile_starred')

        # Removing M2M table for field networked on 'UserProfile'
        db.delete_table('nirit_userprofile_networked')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'nirit.building': {
            'Meta': {'object_name': 'Building'},
            'codename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'notices': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['nirit.Notice']", 'symmetrical': 'False'}),
            'organizations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['nirit.Organization']", 'symmetrical': 'False'})
        },
        'nirit.expertise': {
            'Meta': {'object_name': 'Expertise'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        },
        'nirit.notice': {
            'Meta': {'object_name': 'Notice'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_official': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_reply': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reply_to': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['nirit.Notice']", 'null': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'nirit.organization': {
            'Meta': {'object_name': 'Organization'},
            'codename': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'department': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'expertise': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['nirit.Expertise']", 'symmetrical': 'False'}),
            'floor': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'founded': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'size': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'nirit.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'building': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['nirit.Building']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'networked': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['nirit.Organization']", 'symmetrical': 'False'}),
            'starred': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['nirit.Notice']", 'symmetrical': 'False'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['nirit']