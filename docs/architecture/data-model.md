# Data model

**Request**
- ts_ms, trace_id, span_id, method, route, status, latency_ms, bytes_in/out, exception, exception_type

**Function**
- trace_id, span_id, parent_span_id, name, latency_ms, success, exception_type

**DB**
- trace_id, span_id, parent_span_id, db_vendor, statement (redacted), duration_ms, rowcount, extra
