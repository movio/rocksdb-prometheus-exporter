from setuptools import setup, find_packages

setup(
    name='rocksdb-prometheus-exporter',
    version='0.4.0',
    description='RocksDB Prometheus exporter',
    url='https://github.com/movio/rocksdb-prometheus-exporter',
    author='Nicolas Maquet',
    author_email='nicolas@movio.co',
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Monitoring',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='monitoring prometheus exporter rocksdb',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'prometheus-client>=0.0.13'
    ],
    entry_points={
        'console_scripts': [
            'rocksdb-prometheus-exporter=rocksdb_prometheus_exporter:main',
        ],
    },
)
