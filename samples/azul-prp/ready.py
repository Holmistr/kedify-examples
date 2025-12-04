#!/usr/bin/env python3
import sys
import os
from jmxquery import JMXConnection, JMXQuery

host = os.environ.get("JMX_HOST", "127.0.0.1")
port = int(os.environ.get("JMX_PORT", "9010"))
threshold = int(os.environ.get("OUTSTANDING_COMPILES_THRESHOLD", "500"))
print(f"JMX_HOST={host}")
print(f"JMX_PORT={port}")
print(f"OUTSTANDING_COMPILES_THRESHOLD={threshold}")

service_url = f"service:jmx:rmi:///jndi/rmi://{host}:{port}/jmxrmi"
bean = "com.azul.zing:type=Compilation"
attribute = "TotalOutstandingCompiles"

try:
    conn = JMXConnection(service_url)
    queries = [JMXQuery(f"{bean}", attribute=attribute)]

    metrics = conn.query(queries)
    # Expect exactly one result
    if not metrics:
        print("No value returned", file=sys.stderr)
        sys.exit(4)

    value = metrics[0].value
    print(value)

    if value < threshold:
        # Call finishWarmup() operation
        print(f"Compiler queue depth is below threshold ({value} < {threshold}), ending warmup", file=sys.stderr)
        try:
            result = conn.invoke_operation(bean, "finishWarmup", [])

            if result is True:
                print("Warmup complete", file=sys.stderr)
                sys.exit(0)
            else:
                print("finishWarmup() didn't succeed.", file=sys.stderr)
                sys.exit(5)
        except Exception as op_err:
            print(f"Error invoking finishWarmup(): {op_err}", file=sys.stderr)
            sys.exit(6)
    else:
        print(
            f"TotalOutstandingCompiles still above threshold: {value} >= {threshold}",
            file=sys.stderr
        )
        sys.exit(2)

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(3)
