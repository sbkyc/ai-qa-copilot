from __future__ import annotations

from app.db import connect, initialize_database, seed_database
from app.services import create_order, list_products


def test_seed_database_restores_demo_catalog_for_existing_database():
    connection = connect(":memory:")
    try:
        initialize_database(connection)
        seed_database(connection)
        create_order(connection, username="alice", product_id=1, quantity=10)

        seed_database(connection)

        products = list_products(connection)
        assert products[0]["name"] == "无线鼠标"
        assert products[0]["stock"] == 10
    finally:
        connection.close()
