#!/bin/sh

exec python ./sender/sender.py &
exec python ./triger/triger.py