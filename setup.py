from setuptools import setup


setup(
    name='flight-sim',
    options={
        'build_apps': {
            'gui_apps': {
                'flight-sim': 'main.py',
            },

            # Set up output logging, important for GUI apps!
            'log_filename': '$USER_APPDATA/flight-sim/output.log',
            'log_append': False,

            # Specify which files are included with the distribution
            'include_patterns': [
                'models/**',
                'terrain/**',
                'ui/**',
                'fonts/*.ttf',
                'sounds/*.ogg'
            ],

            # Platforms that we're building for.
            'platforms': [
                "manylinux1_x86_64",
                "macosx_10_6_x86_64",
                "win_amd64"
            ],

            # Include the OpenGL renderer and OpenAL audio plug-in
            'plugins': [
                'pandagl',
                'p3openal_audio',
                'p3assimp'
            ],

            'include_modules': {'*': ['scipy._lib.messagestream', 'scipy.spatial.transform._rotation_groups']}
        }
    }
)
