from __future__ import print_function
import sys
import os
import argparse


def navi_create_command():
    parser = argparse.ArgumentParser(
        description="Create bots with navi's magic")
    parser.add_argument('bot_name')
    args = parser.parse_args()
    bot_name = parser.bot_name

    navi_path = os.path.dirname(os.path.realpath(__file__))
    cwd = os.getcwd()
    bot_dir = os.path.join(cwd, bot_name)

    if not os.path.exists(bot_dir):
        try:
            os.makedirs(bot_dir)
        except:
            print("Couldn't create {} directory".format(bot_name),
                  file=sys.stderr)
            sys.exit()
    else:
        print("Directory {} already exists".format(bot_name), file=sys.stderr)
        sys.exit()

    bot_module_dir = os.path.join(bot_dir, bot_name)
    secret_dir = os.path.join(bot_dir, 'secret')

    try:
        os.makedirs(bot_module_dir)
        os.makedirs(secret_dir)
    except:
        print("Couldn't create files inside {} directory".format(bot_name),
              file=sys.stderr)
        sys.exit()

    substitution = {'bot_name': bot_name}


def _render_template(file, subs, dest_dir):

    with open("") as template_file:

        template = Template(template_file.read())
        result = template.substitute(substitution)
