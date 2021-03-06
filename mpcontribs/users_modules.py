from mpcontribs import users as mpcontribs_users
import os, pkgutil

def get_users_modules():
    mod_iter = pkgutil.iter_modules(mpcontribs_users.__path__)
    return [
        os.path.join(mpcontribs_users.__path__[0], mod)
        for imp, mod, ispkg in mod_iter if ispkg
    ]

def get_user_urlpatterns():
    urlpatterns = []
    for mod_path in get_users_modules():
        if os.path.exists(os.path.join(mod_path, 'explorer', 'apps.py')):
            url = '^{}'.format(os.path.join(os.path.basename(mod_path), ''))
            mod_path_split = os.path.normpath(mod_path).split(os.sep)[-3:]
            include_urls = '.'.join(mod_path_split + ['explorer', 'urls'])
            urlpatterns.append((url, include_urls))
    return urlpatterns

def get_user_static_dirs():
    static_dirs = []
    for mod_path in get_users_modules():
        static_dir = os.path.join(mod_path, 'explorer', 'static')
        if os.path.exists(static_dir):
            rel_static_dir = os.sep.join(
                os.path.normpath(static_dir).split(os.sep)[-5:]
            )
            static_dirs.append(rel_static_dir)
    return static_dirs

def get_user_explorer_name(path, view='index'):
    return '_'.join(
        os.path.dirname(os.path.normpath(path)).split(os.sep)[-4:] + [view]
    )

def get_user_classname(mod):
    return ''.join(mod.replace('_', ' ').title().split())

def get_user_explorer_config(mod):
    return get_user_classname(mod) + 'ExplorerConfig'

def get_user_installed_apps():
    installed_apps = []
    for mod_path in get_users_modules():
        mod = os.path.basename(mod_path)
        explorer = os.path.join(mod_path, 'explorer', 'apps.py')
        if os.path.exists(explorer):
            #config = get_user_explorer_config(mod)
            #installed_apps.append('.'.join(['test_site', 'apps', config]))
            mod_path_split = os.path.normpath(mod_path).split(os.sep)[-3:]
            name = '.'.join(mod_path_split + ['explorer'])
            installed_apps.append(name)
    return installed_apps

def get_user_rester(mod):
    return get_user_classname(mod) + 'Rester'
