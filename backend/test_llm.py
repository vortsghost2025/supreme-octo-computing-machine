import pytest
from unittest.mock import patch, MagicMock


def test_llm_models_endpoint_returns_200():
    from backend.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/llm/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)
        assert len(data["models"]) > 0


def test_llm_models_endpoint_returns_sorted_list():
    from backend.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/llm/models")
        data = response.json()
        models = data["models"]
        assert models == sorted(models), "Models should be sorted alphabetically"


@patch("backend.main._llm_generate", new_callable=MagicMock)
def test_llm_generate_with_valid_model(mock_generate):
    from backend.main import app
    from fastapi.testclient import TestClient

    mock_generate.return_value = "Mocked response"
    with TestClient(app) as client:
        response = client.post(
            "/llm",
            json={"prompt": "Hello", "model": "llama3:8b"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "model" in data


def test_llm_generate_rejects_invalid_model():
    from backend.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.post(
            "/llm",
            json={"prompt": "Hello", "model": "invalid-model-not-allowed"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data


def test_llm_generate_invalid_model_error_contains_message():
    from backend.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.post(
            "/llm",
            json={"prompt": "Hello", "model": "banned-model"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        detail = data["detail"]
        assert isinstance(detail, dict) and "error" in detail


def test_llm_generate_error_handling_returns_json():
    from backend.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.post(
            "/llm",
            json={"prompt": "Hello", "model": "invalid-model"}
        )
        assert response.status_code == 400
        data = response.json()
        assert response.headers.get("content-type", "").startswith("application/json")
        assert "detail" in data


@patch("backend.main._llm_generate", new_callable=MagicMock)
def test_llm_generate_without_model_uses_default(mock_generate):
    from backend.main import app
    from fastapi.testclient import TestClient

    mock_generate.return_value = "Mock response"
    with TestClient(app) as client:
        response = client.post(
            "/llm",
            json={"prompt": "Hello"}
        )
        assert response.status_code == 200


def test_llm_models_endpoint_content_type_json():
    from backend.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/llm/models")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert content_type.startswith("application/json")


def test_model_whitelist_includes_expected_models():
    from backend.llm_client import ALLOWED_MODELS

    assert "llama3:8b" in ALLOWED_MODELS
    assert "mistral" in ALLOWED_MODELS
    assert "codellama:7b" in ALLOWED_MODELS


def test_model_whitelist_rejects_invalid_model():
    from backend.llm_client import _validate_model, OllamaError

    with pytest.raises(OllamaError) as exc:
        _validate_model("definitely-not-allowed-model")
    assert "not allowed" in str(exc.value).lower()