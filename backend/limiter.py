"""Shared SlowAPI rate limiter instance.

Import this module in main.py (to attach to the app) and in any route
module that needs per-endpoint limits.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
