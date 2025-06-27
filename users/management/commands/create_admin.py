"""
Django management command to create admin users for the Get Fit platform.
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from users.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to create admin users.
    
    Usage:
        python manage.py create_admin --email admin@example.com --password mypassword --first-name Admin --last-name User
    """
    
    help = 'Create an admin user for the Get Fit platform'

    def add_arguments(self, parser):
        """
        Add command line arguments.
        """
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email address for the admin user'
        )
        parser.add_argument(
            '--password',
            type=str,
            required=True,
            help='Password for the admin user'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='',
            help='First name of the admin user'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='',
            help='Last name of the admin user'
        )
        parser.add_argument(
            '--phone-number',
            type=str,
            default='',
            help='Phone number of the admin user'
        )
        parser.add_argument(
            '--company-name',
            type=str,
            default='',
            help='Company name for the admin user'
        )
        parser.add_argument(
            '--bio',
            type=str,
            default='',
            help='Bio for the admin user'
        )
        parser.add_argument(
            '--verified',
            action='store_true',
            help='Mark the admin user as verified'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if user already exists'
        )

    def handle(self, *args, **options):
        """
        Handle the command execution.
        """
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        phone_number = options['phone_number']
        company_name = options['company_name']
        bio = options['bio']
        is_verified = options['verified']
        force = options['force']

        try:
            # Validate email format
            validate_email(email)
            
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                if force:
                    self.stdout.write(
                        self.style.WARNING(f'User with email {email} already exists. Updating...')
                    )
                    user = User.objects.get(email=email)
                    user.user_type = User.UserType.ADMIN
                    user.is_verified = is_verified
                    if first_name:
                        user.first_name = first_name
                    if last_name:
                        user.last_name = last_name
                    if phone_number:
                        user.phone_number = phone_number
                    if company_name:
                        user.company_name = company_name
                    if bio:
                        user.bio = bio
                    user.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Admin user {email} updated successfully!')
                    )
                    return
                else:
                    raise CommandError(f'User with email {email} already exists. Use --force to update.')

            # Create admin user
            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone_number,
                    user_type=User.UserType.ADMIN,
                    company_name=company_name,
                    bio=bio,
                    is_verified=is_verified
                )
                
                logger.info(f'Admin user created: {email}')
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Admin user {email} created successfully!\n'
                        f'User ID: {user.id}\n'
                        f'Full Name: {user.full_name}\n'
                        f'User Type: {user.user_type}\n'
                        f'Verified: {user.is_verified}'
                    )
                )

        except ValidationError as e:
            raise CommandError(f'Invalid email format: {e}')
        except Exception as e:
            logger.error(f'Error creating admin user: {str(e)}')
            raise CommandError(f'Failed to create admin user: {str(e)}') 