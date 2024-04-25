#!/usr/bin/env python3
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import argparse
import subprocess
import sys
from pathlib import Path


def get_debian_control_dependencies():
    with (Path(__file__).parent.parent / 'debian' / 'control').open() as f:
        debian_control = f.read()
        dependencies = debian_control.split('\nDepends:')[1].split('\nPre-Depends:')[0]

        # remove comments, remove spaces, recombine lines, split on comma
        dependencies_list = ''.join(line.replace(' ', '')
            for line in dependencies.split('\n')
            if not line.startswith('#')
        ).split(',')
        return [dep for dep in dependencies_list if dep and not dep.startswith('$')]


def show(cmd):
    show_cmd = ' '.join(cmd)
    print('>', show_cmd)
    return show_cmd


def run(cmd):
    show_cmd = show(cmd)
    returncode = subprocess.run(cmd, check=False).returncode
    if returncode:
        print(f'Error {returncode} while executing {show_cmd}')
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Install or list all dependencies, create users, ... to make a full setup, use -eacd")
    parser.add_argument("-e", "--execute",
                        action=argparse.BooleanOptionalAction,
                        help="Execute the commands, will only list them if not set.",
                        )
    parser.add_argument("-c", "--create-user",
                        action=argparse.BooleanOptionalAction,
                        help="Create postgresql user",
                        )

    parser.add_argument("-p", "--postgress",
                        action=argparse.BooleanOptionalAction,
                        help="Install postgress",
                        )
    parser.add_argument("-r", "--rtl",
                        action=argparse.BooleanOptionalAction,
                        help="Add rtl",
                        )

    parser.add_argument("-d", "--dev",
                        action=argparse.BooleanOptionalAction,
                        help="Add optionnal packages mainly for devlopment",
                        )
    parser.add_argument("-a", "--all",
                        action=argparse.BooleanOptionalAction,
                        help="Install all package needed, postgress, ... If not set, will only install odoo dependencies",
                        )

    args = parser.parse_args()
    if not args.execute:
        run = show

    packages = []

    if args.all or args.postgress:
        print('-- Installing postgresql packages')
        run(['sudo apt-get install postgresql postgresql-client'.split(' ')])

    if args.all or args.create_user:
        print('-- Creating postgresql user')
        run('sudo -u postgres createuser -d -R -S $USER'.split(' '))
        run('createdb $USER'.split(' '))

    print('-- Adding debian-package dependencies')
    packages += get_debian_control_dependencies()
    run(['sudo', 'apt-get', 'install', '-y'] + packages)

    if args.all or args.rtl:
        print('-- Installing rtlcss')
        run(['sudo apt-get install npm'])
        run(['sudo', 'npm', 'install', '-g', 'rtlcss'])
        # pt-transport-https build-essential ca-certificates curl file fonts-freefont-ttf fonts-noto-cjk gawk gnupg gsfonts libldap2-dev libjpeg9-dev libsasl2-dev libxslt1-dev lsb-release npm ocrmypdf sed sudo unzip xfonts-75dpi zip zlib1g-dev

    if args.all:
        print('-- Note: This tool does not support wkhtmltopdf install')
