#!/usr/bin/env python
import argparse
import inspect
import os
import socket
import sys

SCRIPT_DIR = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.append(ROOT_DIR)


if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.settings-' + socket.gethostname()
    from nirit.manager import ModelManager

    parser = argparse.ArgumentParser(description="Nirit Command-Line Tool")
    parser.add_argument('command', type=str, help='command to execute', choices=['create', 'delete', 'add', 'remove', 'post', 'set', 'show'])
    parser.add_argument('object', type=str, help='object to apply command to', choices=['building', 'organization', 'user', 'group', 'notice', 'reply'])
    parser.add_argument('-b', '--buildings', type=str, help='Building Name, or ID(s) (use comma-separated list for multiple buildings)')
    parser.add_argument('-o', '--organization', type=str, help='Organization Name or ID')
    parser.add_argument('-u', '--user', type=str, help='User Email')
    parser.add_argument('-g', '--group', type=str, help='Group Name')
    parser.add_argument('-s', '--subject', type=str, help='Notice Subject')
    parser.add_argument('-n', '--notice', type=str, help='Notice ID')
    parser.add_argument('-t', '--notice_type', type=int, help='Notice type (NOTICE=1, INFO=0)')
    parser.add_argument('--official', action="store_true", help='Whether the notice should be official')
    parser.add_argument('--name', type=str, help='Object Name when looking up (show) objects')
    args = parser.parse_args()

    manager = ModelManager(verbose=True)

    if args.command == 'create':
        # Can create Buildings, Organizations, Users and Groups
        # Objects are created by name (names are unique)
        if args.object == 'building':
            if args.buildings is None:
                print '> [{}] {}'.format(400, "No object given.")
            else:
                res = manager.create('building', args.buildings)
                print '> [{}] {}'.format(res['status'], res['response'])
        elif args.object == 'organization':
            if args.organization is None:
                print '> [{}] {}'.format(400, "No object given.")
            else:
                res = manager.create('organization', args.organization)
                print '> [{}] {}'.format(res['status'], res['response'])
        elif args.object == 'user':
            if args.user is None:
                print '> [{}] {}'.format(400, "No object given.")
            else:
                res = manager.create('user', args.user)
                print '> [{}] {}'.format(res['status'], res['response'])
        elif args.object == 'group':
            if args.group is None:
                print '> [{}] {}'.format(400, "No object given.")
            else:
                res = manager.create('group', args.group)
                print '> [{}] {}'.format(res['status'], res['response'])
        else:
            parser.print_help()

    elif args.command == 'delete':
        # Can delete Buildings, Organizations, Users, Groups and Notices
        # Objects are deleted by ID
        if args.object == 'building':
            if args.buildings is None:
                print '> [{}] {}'.format(400, "No ID given.")
            else:
                res = manager.delete('building', args.buildings)
                print '> [{}] {}'.format(res['status'], res['response'])
        elif args.object == 'organization':
            if args.organization is None:
                print '> [{}] {}'.format(400, "No ID given.")
            else:
                res = manager.delete('organization', args.organization)
                print '> [{}] {}'.format(res['status'], res['response'])
        elif args.object == 'user':
            if args.user is None:
                print '> [{}] {}'.format(400, "No username given.")
            else:
                res = manager.delete('user', args.user)
                print '> [{}] {}'.format(res['status'], res['response'])
        elif args.object == 'group':
            if args.group is None:
                print '> [{}] {}'.format(400, "No ID given.")
            else:
                res = manager.delete('group', args.group)
                print '> [{}] {}'.format(res['status'], res['response'])
        elif args.object == 'notice':
            if args.notice is None:
                print '> [{}] {}'.format(400, "No ID given.")
            else:
                res = manager.delete('notice', args.notice)
                print '> [{}] {}'.format(res['status'], res['response'])
        else:
            parser.print_help()

    elif args.command == 'add':
        # Can add:
        #   - Organization to Building
        #   - User to Organization
        #   - User to Group
        if args.object == 'organization':
            if args.organization is None:
                print '> [{}] {}'.format(400, "Organization ID or Name required.")
            elif args.buildings is None:
                print '> [{}] {}'.format(400, "Building ID or Name required.")
            else:
                res = manager.add('organization', args.organization, args.buildings)
                print '> [{}] {}'.format(res['status'], res['response'])
        elif args.object == 'user':
            if args.organization is None and args.group is None:
                print '> [{}] {}'.format(400, "Organization or Group required.")
            elif args.group is None:
                res = manager.add('user_to_organization', args.user, args.organization)
                print '> [{}] {}'.format(res['status'], res['response'])
            else:
                res = manager.add('user_to_group', args.user, args.group)
                print '> [{}] {}'.format(res['status'], res['response'])
        else:
            parser.print_help()
    
    elif args.command == 'remove':
        # Can remove:
        #   - Organization from Building
        #   - User from Organization
        #   - User from Group
        if args.object == 'organization':
            if args.organization is None:
                print '> [{}] {}'.format(400, "Organization ID or Name required.")
            elif args.buildings is None:
                print '> [{}] {}'.format(400, "Building ID or Name required.")
            else:
                res = manager.remove('organization', args.organization, args.buildings)
                print '> [{}] {}'.format(res['status'], res['response'])
        elif args.object == 'user':
            if args.organization is None and args.group is None:
                print '> [{}] {}'.format(400, "Organization or Group required.")
            elif args.group is None:
                res = manager.remove('user_from_organization', args.user, args.organization)
                print '> [{}] {}'.format(res['status'], res['response'])
            else:
                res = manager.remove('user_from_group', args.user, args.group)
                print '> [{}] {}'.format(res['status'], res['response'])
        else:
            parser.print_help()

    elif args.command == 'post':
        if args.object == 'notice':
            # Post new Notice to 1 or more buildings
            if args.subject is None:
                print '> [{}] {}'.format(400, "No Subject given.")
            elif args.user is None:
                print '> [{}] {}'.format(400, "No Sender (User) given.")
            elif args.buildings is None:
                print '> [{}] {}'.format(400, "No Building ID(s) given.")
            else:
                res = manager.post('notice', subject=args.subject, sender=args.user, buildings=args.buildings, notice_type=args.notice_type, is_official=args.official)
                print '> [{}] {}'.format(res['status'], res['response'])
        elif args.object == 'reply':
            # Reply to existing Notice
            if args.subject is None:
                print '> [{}] {}'.format(400, "No Subject given.")
            elif args.user is None:
                print '> [{}] {}'.format(400, "No Sender (User) given.")
            elif args.notice is None:
                print '> [{}] {}'.format(400, "No Notice ID(s) given.")
            else:
                res = manager.post('reply', subject=args.subject, sender=args.user, nid=args.notice, is_official=args.official)
                print '> [{}] {}'.format(res['status'], res['response'])
        else:
            parser.print_help()

    elif args.command == 'set' and args.object == 'user':
        # Set User preferences
        if args.user is None:
            print '> [{}] {}'.format(400, "No User given.")
        else:
            if args.buildings is not None:
                res = manager.set_preference(user=args.user, preference='active-building', value=args.buildings)
                print '> [{}] {}'.format(res['status'], res['response'])
            elif args.organization is not None:
                res = manager.set_preference(user=args.user, preference='network', value=args.organization)
                print '> [{}] {}'.format(res['status'], res['response'])
            elif args.notice is not None:
                res = manager.set_preference(user=args.user, preference='starred', value=args.notice)
                print '> [{}] {}'.format(res['status'], res['response'])
            else:
                parser.print_help()
        
    elif args.command == 'show':
        # Show returns the loaded object given by name
        if args.name is None:
            print '> [{}] {}'.format(400, "No name given.")
        else:
            res = manager.show(args.object, args.name)
            print '> [{}] {}'.format(res['status'], res['response'])

    else:
        parser.print_help()
