# Prometheus exporter

Metrics:
- `profilis_http_requests_total`
- `profilis_http_request_duration_seconds` (histogram)
- `profilis_db_queries_total`
- `profilis_db_query_duration_seconds` (histogram)
- `profilis_function_calls_total`
- `profilis_function_duration_seconds`

Label plan: service, instance, worker, route/status, function, db_vendor.
