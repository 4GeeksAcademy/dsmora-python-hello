import unittest

from fastapi.testclient import TestClient

from app.api import create_app
from app.models.repository import PostgreSQLDummyRepository


class ShoppingListAPITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(PostgreSQLDummyRepository()))

    def test_get_shopping_list(self):
        response = self.client.get("/shopping-list")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertGreaterEqual(len(response.json()), 1)

    def test_create_item(self):
        response = self.client.post(
            "/shopping-list",
            json={"name": "Huevos", "quantity": 6, "completed": False},
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["name"], "Huevos")
        self.assertEqual(payload["quantity"], 6)
        self.assertFalse(payload["completed"])

    def test_update_and_delete_item(self):
        created = self.client.post(
            "/shopping-list",
            json={"name": "Leche", "quantity": 2, "completed": False},
        ).json()

        updated = self.client.put(
            f"/shopping-list/{created['id']}",
            json={"name": "Leche", "quantity": 3, "completed": True},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["quantity"], 3)
        self.assertTrue(updated.json()["completed"])

        deleted = self.client.delete(f"/shopping-list/{created['id']}")
        self.assertEqual(deleted.status_code, 204)


if __name__ == "__main__":
    unittest.main()
