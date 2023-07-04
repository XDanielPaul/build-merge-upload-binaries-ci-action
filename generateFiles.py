import re
import sys
import subprocess
import os
import rtoml

# Environment variables
github_repository = os.environ.get('GITHUB_REPOSITORY').split('/')
tag_name = os.environ.get('TAG_NAME')
idf_version = os.environ.get('IDF_VERSION')

github_owner = github_repository[0]
github_repo = github_repository[1]

# Root toml object
toml_obj = {'esp_toml_version': 1.0, 'firmware_images_url': f'https://{github_owner}.github.io/{github_repository}', 'supported_apps': []}

class App:
    
    def __init__(self, app):
        # App directory
        self.app_dir = app
        # Name of the app
        if app:
            self.name = app.split('/')[-1]
        # List of targets (esp32, esp32s2, etc)
        self.targets = []
        # List of tuples (kit, target)
        self.boards = []

current_app = App(None)

def get_app_dir(line):
    return re.search(r'"app_dir":\s*"([^"]*)",', line).group(1) if re.search(r'"app_dir":\s*"([^"]*)",', line) else None

def get_target(line):
    return re.search(r'"target":\s*"([^"]*)",', line).group(1) if re.search(r'"target":\s*"([^"]*)",', line) else None

def get_kit(line):
    return re.search(r'"config":\s*"([^"]*)",', line).group(1) if re.search(r'"config":\s*"([^"]*)",', line) else None

def squash_json(input_str):
    global current_app
    # Split the input into lines
    lines = input_str.splitlines()
    output_list = []
    for line in lines:
        # Get the app_dir
        app = get_app_dir(line)
        # If its a not a None and not the same as the current app
        if current_app.app_dir != app:
            # Save the previous app
            if current_app.app_dir:
                output_list.append(current_app.__dict__)
            current_app = App(app)

        # If we are building for a kit        
        if (get_kit(line) != ''):
            current_app.boards.append((get_kit(line), get_target(line)))
        # If we are building for targets
        else:
            current_app.targets.append(get_target(line))

    # Append last app
    output_list.append(current_app.__dict__)
    
    return output_list

def merge_binaries(apps):
    subprocess.run(['mkdir', 'binaries'])
    for app in apps:
        # If we are merging binaries for kits
        if app.get('boards'):
            for board in app['boards']:
                kit = board[0]
                target = board[1]
                cmd = ['esptool.py', '--chip', target, 'merge_bin', '-o', app['name'] + '-' + kit + '-' + target + '-' + idf_version + '.bin', '@flash_args']
                cwd = app.get('app_dir') + '/build_' + kit
                subprocess.run(cmd, cwd=cwd)
                print('Merged binaries for ' + app['name'] + '-' + kit + '-' + target + '-' + idf_version + '.bin')
                subprocess.run(['mv', cwd + '/' + app['name'] + '-' + kit + '-' + target + '-' + idf_version + '.bin', 'binaries'])
        # If we are merging binaries for targets
        else:
            for target in app['targets']:            
                cmd = ['esptool.py', '--chip', target, 'merge_bin', '-o', app['name'] + '-' + target + '-' + idf_version + '.bin', '@flash_args']
                cwd = app.get('app_dir') + '/build'
                subprocess.run(cmd, cwd=cwd)
                print('Merged binaries for ' + app['name'] + '-' + target + '-' + idf_version + '.bin')
                subprocess.run(['mv', cwd + '/' + app['name'] + '-' + target + '-' + idf_version + '.bin', 'binaries'])

def write_app(app):
    if app.get('boards'):
        for board in app['boards']:
            kit = board[0]
            target = board[1]
            toml_obj[f'{app["name"]}-{kit}-{idf_version}'] = {}
            toml_obj[f'{app["name"]}-{kit}-{idf_version}']['chipsets'] = [target]
            toml_obj[f'{app["name"]}-{kit}-{idf_version}'][f'image.{target}'] = f'{app["name"]}-{kit}-{target}-{idf_version}.bin'
            toml_obj[f'{app["name"]}-{kit}-{idf_version}']['android_app_url'] = ''
            toml_obj[f'{app["name"]}-{kit}-{idf_version}']['ios_app_url'] = ''
    else:
        toml_obj[f'{app["name"]}-{idf_version}'] = {}
        toml_obj[f'{app["name"]}-{idf_version}']['chipsets'] = app['targets']
        for target in app['targets']:
            toml_obj[f'{app["name"]}-{idf_version}'][f'image.{target}'] = f'{app["name"]}-{target}-{idf_version}.bin'
        toml_obj[f'{app["name"]}-{idf_version}']['android_app_url'] = ''
        toml_obj[f'{app["name"]}-{idf_version}']['ios_app_url'] = ''

def create_config_toml(apps):
    for app in apps:
            if app.get('boards'):
                toml_obj['supported_apps'].extend([f'{app["name"]}-{board[0]}-{idf_version}' for board in app['boards']])
            else:
                toml_obj['supported_apps'].extend([f'{app["name"]}-{idf_version}'])
            for app in apps:
                write_app(app)

            with open('binaries/config.toml', 'w') as toml_file:
                rtoml.dump(toml_obj, toml_file)

with open(sys.argv[1], 'r') as file:
    apps = squash_json(file.read())
    merge_binaries(apps)
    create_config_toml(apps)