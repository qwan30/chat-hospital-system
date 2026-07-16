from locust import HttpUser, between, task


class ChatbotUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # We assume static tokens are allowed in dev for load testing
        self.client.headers = {"Authorization": "Bearer dev-doctor"}

    @task(3)
    def ask_general_question(self):
        self.client.post("/api/v1/chat", json={"question": "What is the hospital policy on visitors?", "top_k": 3})

    @task(1)
    def get_dashboard(self):
        self.client.get("/api/v1/dashboard/patients")

    @task(2)
    def view_patient_record(self):
        # Using a dummy UUID for the patient
        self.client.get("/api/v1/patients/20000000-0000-0000-0000-000000000001")
