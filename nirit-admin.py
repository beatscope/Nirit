#!/usr/bin/env python
import argparse
import inspect
import os
import sys

SCRIPT_DIR = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.append(ROOT_DIR)


if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.nirit_settings'
    from nirit.manager import ModelManager

    choices = [
        'create-user',  # Create user, generating random password
        'create-token', # Create Authorization Tokens to create companies (can create more than 1 in bulk)
        'list-tokens',  # Lists all Tokens for a Space
        'set',          # Set user preference
        'lookup-email', # Lookup email TLD against Users Table
    ]
    parser = argparse.ArgumentParser(description="Nirit Command-Line Tool")
    parser.add_argument('command', type=str, help='command to execute', choices=choices)
    parser.add_argument('-b', '--space', type=str, help='Space Name ID')
    parser.add_argument('-o', '--organization', type=str, help='Organization Name or ID')
    parser.add_argument('-u', '--user', type=str, help='User Email')
    parser.add_argument('-n', '--notice', type=str, help='Notice ID')
    parser.add_argument('-c', '--count', type=int, default=1, help='Number')
    args = parser.parse_args()

    manager = ModelManager(verbose=True)

    if args.command == 'create-user':
        # Create User & associated Profile
        if args.user is None:
            print '> [{}] {}'.format(400, "Username/email required.")
            parser.print_help()
        else:
            res = manager.create_user(args.user)
            print '> [{}] {}'.format(res['status'], res['response'])

    elif args.command == 'create-token':
        # Create Authorization Token
        if args.space is None:
            # A token is associated with a space
            print '> [{}] {}'.format(400, "Space required.")
            parser.print_help()
        else:
            res = manager.create_token(args.space, args.count)
            print '> [{}]'.format(res['status'])
            print '\n'.join([str(r) for r in res['response']])

    elif args.command == 'list-tokens':
        if args.space is None:
            # A token is associated with a space
            print '> [{}] {}'.format(400, "Space required.")
            parser.print_help()
        else:
            res = manager.list_tokens(args.space)
            print '> [{}]'.format(res['status'])
            print '\n'.join([str(r) for r in res['response']])

    elif args.command == 'set':
        # Set User preferences
        if args.user is None:
            print '> [{}] {}'.format(400, "Username/email required.")
        else:
            if args.space is not None:
                res = manager.set_preference(user=args.user, preference='active-space', value=args.space)
                print '> [{}] {}'.format(res['status'], res['response'])
            elif args.organization is not None:
                res = manager.set_preference(user=args.user, preference='network', value=args.organization)
                print '> [{}] {}'.format(res['status'], res['response'])
            elif args.notice is not None:
                res = manager.set_preference(user=args.user, preference='starred', value=args.notice)
                print '> [{}] {}'.format(res['status'], res['response'])
            else:
                parser.print_help()

    elif args.command == 'lookup-email':
        if args.user is None:
            print '> [{}] {}'.format(400, "Username/email required.")
            parser.print_help()
        else:
            res = manager.lookup_email(args.user)
            print '> [{}] {}'.format(res['status'], res['response'])
        
    else:
        parser.print_help()
