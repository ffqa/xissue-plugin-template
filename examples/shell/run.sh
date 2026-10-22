#!/bin/sh
# The payload is on stdin. Keep it bounded: plugins have a 15s timeout.
payload=$(cat)
case "$payload" in
  *'"event":"run_finished"'*|*'"event": "run_finished"'*)
    printf '%s\n' '{"actions":[{"type":"notify","message":"run finished"}]}'
    ;;
esac
