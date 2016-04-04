# -*- coding: utf-8 -*-

import os
import glob
import argparse
import time
import itertools
from prometheus_client import start_http_server, Gauge, REGISTRY
from threading import Lock, Thread

GAUGES = {}
GAUGES_LAST_UPDATE = {}
GAUGES_LABELS_LAST_UPDATE = {}
GAUGES_LOCK = Lock()
GAUGES_TTL = 60

SST_ABSPATH_TO_SIZE_IN_BYTES = {}

def metric_name_escape(name):
    return name.replace(".", "_").replace("-", "_").replace(" ", "_")

def incrementAbsPathGaugeValue(name, abs_path, amount, description = ""):
    labels = [ "dir_abs_path" ]
    label_values = [ abs_path ]
    i = 0
    while abs_path != os.sep:
        abs_path, basename = os.path.split(abs_path)
        labels += [ 'dir_%d' % i ]
        label_values += [ basename ]
        i += 1
    incrementGaugeValue(name, labels, label_values, amount, description)

def incrementGaugeValue(name, labels, label_values, amount, description = ""):
    with GAUGES_LOCK:
        name = metric_name_escape(name)
        if name not in GAUGES:
            GAUGES[name] = Gauge(name, description, labels)
        if labels:
            GAUGES[name].labels(*label_values).inc(amount)
            GAUGES_LABELS_LAST_UPDATE[(name, tuple(label_values))] = time.time()
        else:
            GAUGES[name].inc(amount)
        GAUGES_LAST_UPDATE[name] = time.time()

def set_gauges_ttl(ttl):
    global GAUGES_TTL
    if ttl is not None: GAUGES_TTL = ttl

def start_ttl_watchdog_thread():
    t = Thread(target=ttl_watchdog)
    t.daemon = True
    t.start()

def ttl_watchdog_unregister_old_metrics(now):
    for (name, last_update) in list(GAUGES_LAST_UPDATE.items()):
        if now - last_update > GAUGES_TTL:
            REGISTRY.unregister(GAUGES[name])
            del GAUGES[name]
            del GAUGES_LAST_UPDATE[name]
            for (other_name, label_values) in list(GAUGES_LABELS_LAST_UPDATE.keys()):
                if name == other_name:
                    del GAUGES_LABELS_LAST_UPDATE[(name, label_values)]

def ttl_watchdog_remove_old_label_values(now):
    for ((name, label_values), last_update) in list(GAUGES_LABELS_LAST_UPDATE.items()):
        if now - last_update > GAUGES_TTL:
            GAUGES[name].remove(*label_values)
            del GAUGES_LABELS_LAST_UPDATE[(name, label_values)]

def ttl_watchdog():
    while True:
        time.sleep(GAUGES_TTL / 10.0)
        now = time.time()
        with GAUGES_LOCK:
            ttl_watchdog_unregister_old_metrics(now)
            ttl_watchdog_remove_old_label_values(now)

def file_extension(path):
    return os.path.splitext(path)[1]

def update_bytes_written_metric(dir_abs_path, sst_abspath):
    try:
        sst_file_size = os.stat(sst_abspath).st_size
    except OSError:
        return
    if sst_abspath not in SST_ABSPATH_TO_SIZE_IN_BYTES:
        incrementAbsPathGaugeValue("rocksdb:sst_file_bytes_written", dir_abs_path, sst_file_size)
    else:
        previous_sst_file_size = SST_ABSPATH_TO_SIZE_IN_BYTES[sst_abspath]
        incrementAbsPathGaugeValue("rocksdb:sst_file_bytes_written", dir_abs_path, sst_file_size - previous_sst_file_size)
    SST_ABSPATH_TO_SIZE_IN_BYTES[sst_abspath] = sst_file_size

def update_bytes_compacted_metric(dir_abs_path, sst_abspath):
    if not os.path.exists(sst_abspath):
        incrementAbsPathGaugeValue("rocksdb:sst_file_bytes_compacted", dir_abs_path, SST_ABSPATH_TO_SIZE_IN_BYTES[sst_abspath])
        del SST_ABSPATH_TO_SIZE_IN_BYTES[sst_abspath]

def update_rocksdb_metrics(dir_paths):
    for dir_path in dir_paths:
        dir_abs_path = os.path.abspath(dir_path)
        current_sst_abspaths = set([
            os.path.abspath(os.path.join(dir_path, sst_basename))
            for sst_basename in os.listdir(dir_path)
            if file_extension(sst_basename) == '.sst'
        ])
        for sst_abspath in current_sst_abspaths:
            update_bytes_written_metric(dir_abs_path, sst_abspath)
        for sst_abspath in [ path for path in SST_ABSPATH_TO_SIZE_IN_BYTES.keys() if path.startswith(dir_abs_path) ]:
            update_bytes_compacted_metric(dir_abs_path, sst_abspath)

def main():
    parser = argparse.ArgumentParser(description='Feed Rocksdb metrics into Prometheus.')
    parser.add_argument('-n', '--interval', metavar='SECONDS', type=int, nargs='?', default=15,
                        help="update interval (default: 15)"),
    parser.add_argument('-p', '--port', metavar='PORT', type=int, nargs='?', default=8080,
                        help='port to serve metrics to Prometheus (default: 8080)')
    parser.add_argument('-t', '--ttl', metavar='SECONDS', type=int, nargs='?',
                        help='interval after which a metric is no longer reported when not updated (default: 60)')
    parser.add_argument('paths', metavar='PATH', type=str, nargs='+',
                        help='path to a RocksDB directory')

    args = parser.parse_args()

    set_gauges_ttl(args.ttl)
    start_http_server(args.port)
    start_ttl_watchdog_thread()

    paths = list(itertools.chain(*[ glob.glob(path_pattern) for path_pattern in args.paths ]))

    while True:
        update_rocksdb_metrics(args.paths)
        time.sleep(args.interval)
