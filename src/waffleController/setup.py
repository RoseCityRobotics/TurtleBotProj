from setuptools import find_packages, setup

package_name = 'waffleController'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=[
        'setuptools',
        'evdev',
    ],
    zip_safe=True,
    maintainer='kenny',
    maintainer_email='kenny@todo.todo',
    description='TurtleBot3 Waffle Pi Bluetooth Controller',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'waffle_controller = waffleController.waffleControls:main',
        ],
    },
)
