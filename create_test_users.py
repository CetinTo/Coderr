"""
Script to create test users from frontend configuration.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts_app.models import User, BusinessProfile, CustomerProfile


def create_customer_user():
    """Create customer test user."""
    customer_user, created = User.objects.get_or_create(
        username='andrey',
        defaults={
            'email': 'andrey@test.de',
            'user_type': 'customer',
            'first_name': 'Andrey',
            'last_name': 'Test'
        }
    )
    if created:
        customer_user.set_password('asdasd')
        customer_user.save()
        CustomerProfile.objects.get_or_create(user=customer_user)
    return created


def create_business_user():
    """Create business test user."""
    business_user, created = User.objects.get_or_create(
        username='kevin',
        defaults={
            'email': 'kevin@test.de',
            'user_type': 'business',
            'first_name': 'Kevin',
            'last_name': 'Test'
        }
    )
    if created:
        business_user.set_password('asdasd24')
        business_user.save()
        BusinessProfile.objects.get_or_create(
            user=business_user,
            defaults={
                'company_name': 'Kevins Business',
                'description': 'Test Business'
            }
        )
    return created


if __name__ == '__main__':
    create_customer_user()
    create_business_user()

