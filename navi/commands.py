from __future__ import print_function
import sys
import os
import argparse
from string import Template

navi_path = os.path.dirname(os.path.realpath(__file__))
navi_templates_path = os.path.join(navi_path, 'templates')


def navi_create_command():
    parser = argparse.ArgumentParser(
        description="Create bots with navi's magic")
    parser.add_argument('bot_name')
    args = parser.parse_args()
    bot_name = args.bot_name

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
        open(os.path.join(bot_module_dir, '__init__.py'), 'a').close()
        os.makedirs(secret_dir)
        open(os.path.join(secret_dir, '__init__.py'), 'a').close()
    except:
        print("Couldn't create files inside {} directory".format(bot_name),
              file=sys.stderr)
        sys.exit()

    substitution = {'bot_name': bot_name}

    # create bot core
    for filename in ['intents.py', 'handlers.py', 'interfaces.py']:
        _render_template(filename, substitution, bot_module_dir)

    # and helpers
    _render_template('run.py', substitution, bot_dir)
    _render_template('config.py', substitution, bot_dir)
    _render_template('secret_config.py', substitution, secret_dir,
                     final_file_name="config.py")

    print("Done! Have fun :)")

def _render_template(file, subs, dest_dir, final_file_name=None):

    if final_file_name is None:
        final_file_name = file
    template_file_path = os.path.join(navi_templates_path,
                                      "{}.tpl".format(file))
    file_final_path = os.path.join(dest_dir, final_file_name)
    with open(template_file_path) as template_file:

        template = Template(template_file.read())
        result = template.substitute(subs)

        with open(file_final_path, "w") as f:
            print("Creating {}...".format(final_file_name))
            f.write(result)
