from django.urls import path
from . import views

urlpatterns = [
   path('', views.signin_view, name='login'),
   path('transaction', views.transaction, name='transaction'),
   path('logout', views.logout_view, name='logout'),
   
   
   path('financial/add/', views.add_financial, name='add_financial'),
   path('financial/edit/<int:pk>/', views.edit_financial, name='edit_financial'),
   path('financial/delete/<int:pk>/', views.delete_financial, name='delete_financial'),
   path('transactions/export/', views.export_transactions_excel, name='export_transactions_excel'),
   # path('transaction/<int:transaction_id>/percentages/', views.view_transaction_percentages, name='transaction_percentages'),
   # path('transaction/percentages/', views.all_transactions_percentages, name='all_transactions_percentages'),
   path('transaction/percentages/', views.returns_summary, name='returns_summary'),
   path('transaction/percentages/export/', views.export_returns_summary, name='export_returns_summary'),
   
]
