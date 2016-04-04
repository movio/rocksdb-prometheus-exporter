# rocksdb-prometheus-exporter
Feed RocksDB metrics into Prometheus.

## Example usage

```sh
docker run -d --name rocksdb-prometheus-exporter \
  -p 8080:8080 \
  -v <path(s) to stores on host>:/stores:ro \
  -e "PATHS=/stores/*/*/*" \
  <registry>/rocksdb-prometheus-exporter:<version>
```

As you can see, `$PATHS` can be a glob which gets expanded internally. This lets you specify multiple stores to monitor. The stores are mounted readonly (using `:ro`) to ensure we don't accidentally corrupt any stores.

See the [Dockerfile](Dockerfile) for more on how to configure the other settings.
