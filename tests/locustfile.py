from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def predict(self):
        payload = {
            "text": "I am unable to login to my account, it keeps saying incorrect password but I am sure it is correct."
        }
        self.client.post("/predict", json=payload)

    @task(1)
    def health_check(self):
        self.client.get("/health")
