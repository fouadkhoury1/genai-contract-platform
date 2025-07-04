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
from apps.clients_contracts.views import (
    ContractListCreateView,
    ContractDetailView,
    ContractAnalysisView,
    ContractAnalysisDetailView,
    ContractEvaluationView,
    HealthzView,
    ReadyzView,
    MetricsView,
    LogsView,
    ClientListCreateView,
    ClientContractsView
)
from apps.authentication.views import RegisterView, LoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('healthz/', HealthzView.as_view(), name='healthz'),
    path('readyz/', ReadyzView.as_view(), name='readyz'),
    path('metrics/', MetricsView.as_view(), name='metrics'),
    path('logs/', LogsView.as_view(), name='logs'),
    path('api/contracts/', ContractListCreateView.as_view(), name='contract-list-create'),
    path('api/contracts/<str:contract_id>/analysis/', ContractAnalysisDetailView.as_view(), name='contract-analysis-detail'),
    path('api/contracts/<str:contract_id>/', ContractDetailView.as_view(), name='contract-detail'),
  
    path('genai/analyze-contract/', ContractAnalysisView.as_view(), name='genai-analyze-contract'),
    path('contracts/<str:contract_id>/init-genai/', ContractAnalysisView.as_view(), name='init-genai-analysis'),
    path('genai/evaluate-contract/', ContractEvaluationView.as_view(), name='genai-evaluate-contract'),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('clients/', ClientListCreateView.as_view(), name='client-list-create'),
    path('clients/<str:client_id>/contracts/', ClientContractsView.as_view(), name='client-contracts'),
]
