import asyncio
import httpx
import subprocess
import sys
import time
import os

# Construct absolute path to the test application directory
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_APP_DIR = os.path.join(TESTS_DIR, "test")

# Ensure the test application is in the python path
sys.path.insert(0, TEST_APP_DIR)

BASE_URL = "http://127.0.0.1:8000"

async def run_csrf_test():
    """
    Tests that CSRF protection works correctly for various request types.
    """
    print("--- Starting CSRF Logic Test ---")
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        try:
            # 1. Make a GET request to a page to get a CSRF token from the cookie
            print("Step 1: Getting CSRF token from homepage...")
            get_response = await client.get("/")
            get_response.raise_for_status()
            assert "csrf_token" in client.cookies, "CSRF token not found in cookie"
            csrf_token = client.cookies["csrf_token"]
            print(f"   [PASS] CSRF token received: {csrf_token[:10]}...")

            # 2. Test POST without any CSRF token (should fail)
            print("\nStep 2: Testing POST to /api/test without CSRF token (expecting 403)...")
            fail_response = await client.post("/api/test", json={"message": "hello"})
            assert fail_response.status_code == 403, f"Expected status 403, but got {fail_response.status_code}"
            assert "CSRF token missing or invalid" in fail_response.text
            print("   [PASS] Request was correctly forbidden.")

            # 3. Test POST with CSRF token in JSON body (should pass)
            print("\nStep 3: Testing POST to /api/test with CSRF token in JSON body (expecting 200)...")
            payload_with_token = {"message": "hello", "csrf_token": csrf_token}
            success_response_body = await client.post("/api/test", json=payload_with_token)
            assert success_response_body.status_code == 200, f"Expected status 200, but got {success_response_body.status_code}"
            assert success_response_body.json()["message"] == "hello"
            print("   [PASS] Request with token in body was successful.")

            # 4. Test POST with CSRF token in header (should pass)
            print("\nStep 4: Testing POST to /api/test with CSRF token in header (expecting 200)...")
            headers = {"X-CSRF-Token": csrf_token}
            success_response_header = await client.post("/api/test", json={"message": "world"}, headers=headers)
            assert success_response_header.status_code == 200, f"Expected status 200, but got {success_response_header.status_code}"
            assert success_response_header.json()["message"] == "world"
            print("   [PASS] Request with token in header was successful.")

            # 5. Test empty-body POST with CSRF token in header (should pass validation, then redirect)
            print("\nStep 5: Testing empty-body POST to /logout with CSRF token in header (expecting 302)...")
            # Note: The /logout endpoint redirects after success, so we expect a 302
            # We disable auto-redirects to verify the 302 status directly
            empty_body_response = await client.post("/logout", headers=headers, follow_redirects=False)
            
            # If we got a 403, the CSRF check failed. If we got a 302, it passed!
            assert empty_body_response.status_code == 302, f"Expected status 302 (Redirect), but got {empty_body_response.status_code}. (403 means CSRF failed)"
            print("   [PASS] Empty-body request passed CSRF check and redirected.")

        except Exception as e:
            print(f"\n--- TEST FAILED ---")
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()
            return False

    print("\n--- ALL CSRF TESTS PASSED ---")
    return True


def main():
    print("Starting test server...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app"],
        cwd=TEST_APP_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,  # Decode stdout/stderr as text
    )
    
    # Give the server more time to start up
    print("Waiting 5 seconds for server to start...")
    time.sleep(5)

    # Check if the server process has terminated unexpectedly
    if server_process.poll() is not None:
        print("\n--- SERVER FAILED TO START ---")
        stdout, stderr = server_process.communicate()
        print("STDOUT:")
        print(stdout)
        print("\nSTDERR:")
        print(stderr)
        sys.exit(1)

    print("Server seems to be running. Starting tests.")
    test_passed = False
    try:
        test_passed = asyncio.run(run_csrf_test())
    finally:
        print("\nStopping test server...")
        server_process.terminate()
        # Get remaining output
        try:
            stdout, stderr = server_process.communicate(timeout=5)
            print("\n--- Server Output ---")
            print("STDOUT:")
            print(stdout)
            print("\nSTDERR:")
            print(stderr)
        except subprocess.TimeoutExpired:
            print("Server did not terminate gracefully.")
        
        if not test_passed:
            print("\nExiting with status 1 due to test failure.")
            sys.exit(1)


if __name__ == "__main__":
    main()
