try:
    import flask
    print("✅ Flask is installed!")
    print(f"Flask version: {flask.__version__}")
    print(f"Flask location: {flask.__file__}")
except ImportError:
    print("❌ Flask is NOT installed!")