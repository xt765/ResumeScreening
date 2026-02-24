import os
import time
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"
TEST_RESUME_DIR = r"d:\TraeProjects\ResumeScreening\.trae\test_resume"

def test_resume_screening():
    print(f"Starting E2E test for resume screening...")
    
    # 1. Login
    print("\n[1] Logging in...")
    client = httpx.Client(base_url=BASE_URL, timeout=60.0)
    files_to_upload = []

    try:
        # Login using JSON
        login_resp = client.post("/auth/login", json={"username": "xt765", "password": "123456"})
        
        if login_resp.status_code == 200:
            resp_json = login_resp.json()
            if resp_json["success"]:
                token = resp_json["data"]["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                print("Login successful.")
            else:
                print(f"Login failed logic: {resp_json}")
                return
        else:
            print(f"Login failed http: {login_resp.status_code} {login_resp.text}")
            return

        # 2. Prepare files
        files = []
        file_paths = []
        if not os.path.exists(TEST_RESUME_DIR):
             print(f"Test resume dir not found: {TEST_RESUME_DIR}")
             return

        for filename in os.listdir(TEST_RESUME_DIR):
            if filename.endswith(".pdf") or filename.endswith(".docx"):
                filepath = os.path.join(TEST_RESUME_DIR, filename)
                file_paths.append(filepath)
                # Limit to 2 files for testing
                if len(file_paths) >= 2:
                    break
        
        print(f"Selected files: {file_paths}")
        
        files_to_upload = []
        for fp in file_paths:
            # httpx files format: (field_name, (filename, file_content, content_type))
            files_to_upload.append(("files", (os.path.basename(fp), open(fp, "rb"), "application/octet-stream")))

        # 3. Upload
        print("\n[2] Uploading files...")
        # Need filter config as JSON string (optional, can be None for parsing only)
        # We'll omit it to test default behavior or pass empty structure
        # Note: The API expects 'filter_config' query param if provided
        
        # We send files as multipart/form-data
        # Note: headers should not include Content-Type as httpx sets it for multipart
        
        resp = client.post("/talents/batch-upload", files=files_to_upload, headers=headers)
        
        if resp.status_code != 200 and resp.status_code != 201:
            print(f"Upload failed: {resp.status_code} {resp.text}")
            return

        result = resp.json()
        if not result["success"]:
            print(f"Upload API returned error: {result}")
            return
            
        task_id = result["data"]["task_id"]
        print(f"Upload successful. Task ID: {task_id}")
        
        # 4. Poll Status
        print("\n[3] Polling task status...")
        while True:
            status_resp = client.get(f"/talents/tasks/{task_id}", headers=headers)
            if status_resp.status_code != 200:
                print(f"Status check failed: {status_resp.status_code}")
                break
                
            status_data = status_resp.json()["data"]
            status = status_data["status"]
            progress = status_data.get("progress", {})
            print(f"Status: {status}, Progress: {progress.get('percentage', 0)}% - {progress.get('message', '')}")
            
            if status in ["completed", "failed", "cancelled"]:
                print(f"\nTask finished with status: {status}")
                if status == "completed":
                    print("Results:", json.dumps(status_data.get("result", {}), ensure_ascii=False, indent=2))
                break
            
            time.sleep(2)

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close files
        for _, (name, f, _) in files_to_upload:
            f.close()

if __name__ == "__main__":
    test_resume_screening()
