from setuptools import setup, find_packages

setup(
    name="kolibri-webview-demo",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'kolibri_webview_demo': ['data/**/*']
    },
    entry_points={
        'console_scripts': [
            'kolibri_webview_demo = kolibri_webview_demo.__main__:main'
        ]
    },
    python_requires='>=3.6',
    install_requires=[
        'PyGObject>=3.28.0',
        'SQLAlchemy>=1.3.11',
    ]
)
