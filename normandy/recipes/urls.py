from django.conf.urls import url, include

from normandy.base.api.routers import MixedViewRouter
from normandy.recipes.api.v1 import views as api_v1_views
from normandy.recipes.api.v2 import views as api_v2_views
from normandy.recipes.api.v3 import views as api_v3_views


# API Router
v1_router = MixedViewRouter()
v1_router.register("action", api_v1_views.ActionViewSet)
v1_router.register("recipe", api_v1_views.RecipeViewSet)
v1_router.register("recipe_revision", api_v1_views.RecipeRevisionViewSet)
v1_router.register(r"approval_request", api_v1_views.ApprovalRequestViewSet)

v1_router.register_view(
    "classify_client", api_v1_views.ClassifyClient, name="classify-client", allow_cdn=False
)

v2_router = MixedViewRouter()
v2_router.register("action", api_v2_views.ActionViewSet)
v2_router.register("recipe", api_v2_views.RecipeViewSet)
v2_router.register("recipe_revision", api_v2_views.RecipeRevisionViewSet)
v2_router.register(r"approval_request", api_v2_views.ApprovalRequestViewSet)

v3_router = MixedViewRouter()
v3_router.register("action", api_v3_views.ActionViewSet)
v3_router.register("recipe", api_v3_views.RecipeViewSet)
v3_router.register("recipe_revision", api_v3_views.RecipeRevisionViewSet)
v3_router.register(r"approval_request", api_v3_views.ApprovalRequestViewSet)
v3_router.register_view("filters", api_v3_views.Filters, name="filters")

app_name = "recipes"

urlpatterns = [
    url(r"^api/v1/", include((v1_router.urls, "recipes"), namespace="v1")),
    url(
        r"^api/v1/action/(?P<name>[_\-\w]+)/implementation/(?P<impl_hash>[a-zA-Z0-9_-]*)/$",
        api_v1_views.ActionImplementationView.as_view(),
        name="action-implementation",
    ),
    url(r"^api/v2/", include((v2_router.urls, "recipes"), namespace="v2")),
    url(
        r"^api/v2/identicon/(?P<generation>v[0-9]):(?P<seed>.{1,64})\.svg",
        api_v2_views.IdenticonView.as_view(),
        name="identicon-v2",
    ),
    url(
        r"^api/v3/identicon/(?P<generation>v[0-9]):(?P<seed>.{1,64})\.svg",
        api_v2_views.IdenticonView.as_view(),
        name="identicon",
    ),
    url(r"^api/v3/", include((v3_router.urls, "recipes"), namespace="v3")),
]
