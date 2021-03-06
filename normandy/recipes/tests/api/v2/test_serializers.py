import pytest
from rest_framework import serializers

from normandy.base.tests import Whatever
from normandy.recipes.tests import (
    ARGUMENTS_SCHEMA,
    ActionFactory,
    ApprovalRequestFactory,
    RecipeFactory,
)
from normandy.recipes.api.v2.serializers import (
    ActionSerializer,
    RecipeRevisionSerializer,
    RecipeSerializer,
)


@pytest.mark.django_db()
class TestRecipeSerializer:
    def test_it_works(self, rf):
        recipe = RecipeFactory(arguments={"foo": "bar"}, filter_object_json=None)
        approval = ApprovalRequestFactory(revision=recipe.latest_revision)
        action = recipe.action
        serializer = RecipeSerializer(recipe, context={"request": rf.get("/")})

        assert serializer.data == {
            "name": recipe.name,
            "id": recipe.id,
            "last_updated": Whatever(),
            "enabled": recipe.enabled,
            "extra_filter_expression": recipe.extra_filter_expression,
            "filter_expression": recipe.filter_expression,
            "filter_object": [],
            "action": {
                "arguments_schema": {},
                "id": action.id,
                "implementation_url": Whatever(),
                "name": action.name,
            },
            "arguments": {"foo": "bar"},
            "is_approved": False,
            "latest_revision": RecipeRevisionSerializer(recipe.latest_revision).data,
            "approved_revision": None,
            "approval_request": {
                "id": approval.id,
                "created": Whatever(),
                "creator": Whatever(),
                "approved": None,
                "approver": None,
                "comment": None,
            },
            "identicon_seed": Whatever.startswith("v1:"),
        }

    def test_validation_with_invalid_action(self):
        serializer = RecipeSerializer(
            data={"action_id": "action-that-doesnt-exist", "arguments": {}}
        )

        with pytest.raises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

        assert serializer.errors["action_id"] == [
            serializers.PrimaryKeyRelatedField.default_error_messages["incorrect_type"].format(
                data_type="str"
            )
        ]

    # If the action specified cannot be found, raise validation
    # error indicating the arguments schema could not be loaded
    def test_validation_with_wrong_action(self):
        serializer = RecipeSerializer(data={"action_id": "9999", "arguments": {}})

        with pytest.raises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

        assert serializer.errors["action_id"] == [
            serializers.PrimaryKeyRelatedField.default_error_messages["does_not_exist"].format(
                pk_value=9999
            )
        ]

    # If the action can be found, raise validation error
    # with the arguments error formatted appropriately
    def test_validation_with_wrong_arguments(self):
        action = ActionFactory(name="show-heartbeat", arguments_schema=ARGUMENTS_SCHEMA)

        serializer = RecipeSerializer(
            data={
                "action_id": action.id,
                "name": "Any name",
                "extra_filter_expression": "true",
                "arguments": {
                    "surveyId": "",
                    "surveys": [
                        {"title": "", "weight": 1},
                        {"title": "bar", "weight": 1},
                        {"title": "foo", "weight": 0},
                        {"title": "baz", "weight": "lorem ipsum"},
                    ],
                },
            }
        )

        with pytest.raises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

        assert serializer.errors["arguments"] == {
            "surveyId": "This field may not be blank.",
            "surveys": {
                0: {"title": "This field may not be blank."},
                2: {"weight": "0 is less than the minimum of 1"},
                3: {"weight": "'lorem ipsum' is not of type 'integer'"},
            },
        }

    def test_validation_with_invalid_filter_expression(self):
        ActionFactory(name="show-heartbeat", arguments_schema=ARGUMENTS_SCHEMA)

        serializer = RecipeSerializer(
            data={
                "name": "bar",
                "enabled": True,
                "extra_filter_expression": "inv(-alsid",
                "action": "show-heartbeat",
                "arguments": {
                    "surveyId": "lorem-ipsum-dolor",
                    "surveys": [
                        {"title": "adipscing", "weight": 1},
                        {"title": "consequetar", "weight": 1},
                    ],
                },
            }
        )

        assert not serializer.is_valid()
        assert serializer.errors["extra_filter_expression"] == [
            "Could not parse expression: inv(-alsid"
        ]

    def test_validation_with_jexl_exception(self):
        serializer = RecipeSerializer(
            data={
                "name": "bar",
                "enabled": True,
                "extra_filter_expression": '"\\',
                "action": "show-heartbeat",
                "arguments": {
                    "surveyId": "lorem-ipsum-dolor",
                    "surveys": [
                        {"title": "adipscing", "weight": 1},
                        {"title": "consequetar", "weight": 1},
                    ],
                },
            }
        )

        assert not serializer.is_valid()
        assert serializer.errors["extra_filter_expression"] == ['Could not parse expression: "\\']

    def test_validation_with_valid_data(self):
        mockAction = ActionFactory(name="show-heartbeat", arguments_schema=ARGUMENTS_SCHEMA)

        serializer = RecipeSerializer(
            data={
                "name": "bar",
                "enabled": True,
                "extra_filter_expression": "[]",
                "action_id": mockAction.id,
                "arguments": {
                    "surveyId": "lorem-ipsum-dolor",
                    "surveys": [
                        {"title": "adipscing", "weight": 1},
                        {"title": "consequetar", "weight": 1},
                    ],
                },
            }
        )

        assert serializer.is_valid()
        assert serializer.validated_data == {
            "name": "bar",
            "extra_filter_expression": "[]",
            "action": mockAction,
            "arguments": {
                "surveyId": "lorem-ipsum-dolor",
                "surveys": [
                    {"title": "adipscing", "weight": 1},
                    {"title": "consequetar", "weight": 1},
                ],
            },
        }
        assert serializer.errors == {}


@pytest.mark.django_db()
class TestActionSerializer:
    def test_it_uses_cdn_url(self, rf, settings):
        settings.CDN_URL = "https://example.com/cdn/"
        action = ActionFactory()
        serializer = ActionSerializer(action, context={"request": rf.get("/")})
        assert serializer.data["implementation_url"].startswith(settings.CDN_URL)
