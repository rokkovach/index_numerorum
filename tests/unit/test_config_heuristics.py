from index_numerorum.config import suggest_model_for_column


class TestSuggestModel:
    def test_address_keywords(self):
        assert suggest_model_for_column("Shipping Address") == "address"
        assert suggest_model_for_column("Billing Address") == "address"
        assert suggest_model_for_column("Address Line 1") == "address"
        assert suggest_model_for_column("City") == "address"
        assert suggest_model_for_column("Postal Code") == "address"
        assert suggest_model_for_column("State") == "address"
        assert suggest_model_for_column("Street") == "address"

    def test_entity_keywords(self):
        assert suggest_model_for_column("Company Name") == "entity"
        assert suggest_model_for_column("Vendor") == "entity"
        assert suggest_model_for_column("Supplier") == "entity"
        assert suggest_model_for_column("Customer") == "entity"
        assert suggest_model_for_column("Organization") == "entity"
        assert suggest_model_for_column("Counterparty") == "entity"

    def test_default_falls_to_mini(self):
        assert suggest_model_for_column("Product Name") == "mini"
        assert suggest_model_for_column("Description") == "mini"
        assert suggest_model_for_column("Title") == "mini"
