import os

os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET"] = (
    "test-only-jwt-secret-for-aurora-tests-123456"
)
