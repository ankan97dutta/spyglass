# Prometheus exporter

Metrics:
- `spyglass_http_requests_total`
- `spyglass_http_request_duration_seconds` (histogram)
- `spyglass_db_queries_total`
- `spyglass_db_query_duration_seconds` (histogram)
- `spyglass_function_calls_total`
- `spyglass_function_duration_seconds`

Label plan: service, instance, worker, route/status, function, db_vendor.
