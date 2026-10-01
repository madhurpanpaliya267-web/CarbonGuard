import pytest
from app.engines.security.security_controls import (
    ControlCategory,
    SecurityControl,
    SecurityControlError,
    SECURITY_CONTROLS,
    get_supported_control_ids,
    validate_control_id,
    get_control,
    list_controls,
    list_controls_by_category,
    get_controls_for_attack,
    get_attack_types_for_control,
)


class TestControlCategory:
    def test_has_six_categories(self):
        assert len(ControlCategory) == 6


class TestSupportedControls:
    def test_all_ten_exist(self):
        ids = get_supported_control_ids()
        assert len(ids) == 10
        expected = {
            "firewall", "ids", "ips", "waf", "endpoint_security",
            "authentication", "encryption", "siem", "runtime_monitoring", "logging",
        }
        assert set(ids) == expected

    def test_security_controls_has_all(self):
        assert len(SECURITY_CONTROLS) == 10


class TestValidateControlId:
    def test_valid(self):
        validate_control_id("firewall")

    def test_invalid(self):
        with pytest.raises(SecurityControlError, match="Unknown security control"):
            validate_control_id("nonexistent")


class TestGetControl:
    def test_returns_security_control(self):
        ctrl = get_control("firewall")
        assert isinstance(ctrl, SecurityControl)
        assert ctrl.control_id == "firewall"
        assert ctrl.display_name == "Firewall"

    def test_invalid_raises(self):
        with pytest.raises(SecurityControlError):
            get_control("nonexistent")


class TestSecurityControlMetadata:
    def test_firewall(self):
        ctrl = get_control("firewall")
        assert ctrl.category == ControlCategory.NETWORK
        assert len(ctrl.description) > 0
        assert len(ctrl.supported_attack_types) > 0
        assert ctrl.enabled_by_default is True

    def test_ids(self):
        ctrl = get_control("ids")
        assert ctrl.category == ControlCategory.NETWORK

    def test_waf(self):
        ctrl = get_control("waf")
        assert ctrl.category == ControlCategory.APPLICATION
        assert "sql_injection" in ctrl.supported_attack_types

    def test_endpoint_security(self):
        ctrl = get_control("endpoint_security")
        assert ctrl.category == ControlCategory.ENDPOINT
        assert "malware" in ctrl.supported_attack_types

    def test_authentication(self):
        ctrl = get_control("authentication")
        assert ctrl.category == ControlCategory.IDENTITY

    def test_encryption(self):
        ctrl = get_control("encryption")
        assert ctrl.category == ControlCategory.DATA

    def test_siem(self):
        ctrl = get_control("siem")
        assert ctrl.category == ControlCategory.MONITORING

    def test_runtime_monitoring(self):
        ctrl = get_control("runtime_monitoring")
        assert ctrl.category == ControlCategory.MONITORING

    def test_logging(self):
        ctrl = get_control("logging")
        assert ctrl.category == ControlCategory.MONITORING

    def test_ips(self):
        ctrl = get_control("ips")
        assert ctrl.category == ControlCategory.NETWORK


class TestSecurityControlToDict:
    def test_to_dict(self):
        ctrl = get_control("firewall")
        d = ctrl.to_dict()
        assert d["control_id"] == "firewall"
        assert d["category"] == "network"
        assert isinstance(d["supported_attack_types"], list)
        assert isinstance(d["config_parameters"], dict)


class TestConfigParameters:
    def test_firewall_has_params(self):
        ctrl = get_control("firewall")
        assert "rules_count" in ctrl.config_parameters
        assert ctrl.config_parameters["rules_count"]["type"] == "int"

    def test_authentication_has_mfa(self):
        ctrl = get_control("authentication")
        assert "mfa_enabled" in ctrl.config_parameters
        assert ctrl.config_parameters["mfa_enabled"]["type"] == "bool"


class TestListControls:
    def test_returns_all_ten(self):
        controls = list_controls()
        assert len(controls) == 10

    def test_has_required_fields(self):
        controls = list_controls()
        for c in controls:
            assert "control_id" in c
            assert "display_name" in c
            assert "category" in c
            assert "description" in c
            assert "supported_attack_types" in c


class TestListControlsByCategory:
    def test_network_has_three(self):
        controls = list_controls_by_category(ControlCategory.NETWORK)
        assert len(controls) == 3
        ids = {c.control_id for c in controls}
        assert ids == {"firewall", "ids", "ips"}

    def test_monitoring_has_three(self):
        controls = list_controls_by_category(ControlCategory.MONITORING)
        assert len(controls) == 3
        ids = {c.control_id for c in controls}
        assert ids == {"siem", "runtime_monitoring", "logging"}


class TestGetControlsForAttack:
    def test_ddos_controls(self):
        controls = get_controls_for_attack("ddos")
        ids = {c.control_id for c in controls}
        assert "firewall" in ids
        assert "ids" in ids

    def test_brute_force_controls(self):
        controls = get_controls_for_attack("brute_force")
        ids = {c.control_id for c in controls}
        assert "authentication" in ids

    def test_sql_injection_controls(self):
        controls = get_controls_for_attack("sql_injection")
        ids = {c.control_id for c in controls}
        assert "waf" in ids

    def test_malware_controls(self):
        controls = get_controls_for_attack("malware")
        ids = {c.control_id for c in controls}
        assert "endpoint_security" in ids


class TestGetAttackTypesForControl:
    def test_firewall_attack_types(self):
        types = get_attack_types_for_control("firewall")
        assert "ddos" in types
        assert "brute_force" in types

    def test_invalid_control(self):
        with pytest.raises(SecurityControlError):
            get_attack_types_for_control("nonexistent")
