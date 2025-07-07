"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from apps.authentication.views import LoginView, RegisterView
from apps.clients_contracts.views import (
    ContractListCreateView,
    ContractDetailView,
    ContractAnalysisView,
    ContractAnalysisDetailView,
    ContractEvaluationView,
    ContractClauseExtractionView,
    ContractReanalyzeView,
    HealthzView,
    ReadyzView,
    MetricsView,
    LogsView,
    ClientListCreateView,
    ClientDetailView,
    ClientContractsView
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path('healthz/', HealthzView.as_view(), name='health'),
    path('readyz/', ReadyzView.as_view(), name='ready'),
    path('metrics/', MetricsView.as_view(), name='metrics'),
    path('logs/', LogsView.as_view(), name='logs'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/contracts/', ContractListCreateView.as_view(), name='contracts'),
    path('api/contracts/<str:contract_id>/', ContractDetailView.as_view(), name='contract-detail'),
    path('api/contracts/<str:contract_id>/analysis/', ContractAnalysisDetailView.as_view(), name='contract-analysis-detail'),
    path('api/contracts/<str:contract_id>/reanalyze/', ContractReanalyzeView.as_view(), name='contract-reanalyze'),
    path('api/contracts/<str:contract_id>/clauses/', ContractClauseExtractionView.as_view(), name='contract-clauses'),
    path('api/contracts/analyze/', ContractAnalysisView.as_view(), name='contract-analysis'),
    path('api/contracts/evaluate/', ContractEvaluationView.as_view(), name='contract-evaluation'),
    path('api/clients/', ClientListCreateView.as_view(), name='clients'),
    path('api/clients/<str:client_id>/', ClientDetailView.as_view(), name='client-detail'),
    path('api/clients/<str:client_id>/contracts/', ClientContractsView.as_view(), name='client-contracts'),
]
