"""Configuration module for AdVisor backend"""
from .supabase_client import get_client, get_supabase_client

__all__ = ['get_client', 'get_supabase_client']
