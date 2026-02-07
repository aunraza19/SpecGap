#!/usr/bin/env python3
"""
SpecGap Backend Runner
Run with: python run_backend.py [--prod] [--port PORT]
"""

import os
import sys
import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run SpecGap Backend Server")
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Run in production mode (no reload, optimized)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run on (default: 8000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of workers for production (default: 1)"
    )

    args = parser.parse_args()

    # Configuration based on mode
    config = {
        "app": "app.main:app",
        "host": args.host,
        "port": args.port,
    }

    if args.prod:
        # Production settings
        config.update({
            "reload": False,
            "workers": args.workers,
            "log_level": "warning",
            "access_log": True,
        })
        os.environ.setdefault("ENV", "production")
        print(f"🚀 Starting SpecGap in PRODUCTION mode on {args.host}:{args.port}")
    else:
        # Development settings
        config.update({
            "reload": True,
            "log_level": "info",
        })
        os.environ.setdefault("ENV", "development")
        print(f"🔧 Starting SpecGap in DEVELOPMENT mode on {args.host}:{args.port}")
        print(f"📚 API Docs: http://localhost:{args.port}/docs")
        print(f"📖 ReDoc: http://localhost:{args.port}/redoc")

    uvicorn.run(**config)


if __name__ == "__main__":
    main()
