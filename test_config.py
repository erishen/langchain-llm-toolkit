from config import settings

print("Testing configuration module...")
print(f"APP_NAME: {settings.APP_NAME}")
print(f"DEFAULT_MODEL: {settings.DEFAULT_MODEL}")
print(f"DEBUG: {settings.DEBUG}")
print(f"OPENAI_API_KEY: {'Set' if settings.OPENAI_API_KEY else 'Not set'}")
print(f"ANTHROPIC_API_KEY: {'Set' if settings.ANTHROPIC_API_KEY else 'Not set'}")
print(f"GOOGLE_API_KEY: {'Set' if settings.GOOGLE_API_KEY else 'Not set'}")
print(f"HUGGINGFACE_API_KEY: {'Set' if settings.HUGGINGFACE_API_KEY else 'Not set'}")
print(f"LANGSMITH_API_KEY: {'Set' if settings.LANGSMITH_API_KEY else 'Not set'}")
print("Configuration module test completed successfully!")
