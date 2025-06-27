"""
Custom migration to create sample fitness classes for testing.
"""
import logging
from django.db import migrations
from django.utils import timezone
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


def create_sample_classes(apps, schema_editor):
    """
    Create sample fitness classes with categories, instructors, and schedules.
    """
    # Get models
    User = apps.get_model('users', 'User')
    ClassCategory = apps.get_model('classes', 'ClassCategory')
    FitnessClass = apps.get_model('classes', 'FitnessClass')
    ClassSchedule = apps.get_model('classes', 'ClassSchedule')
    
    # Create admin user if not exists
    admin_user, created = User.objects.get_or_create(
        email='admin@getfit.com',
        defaults={
            'first_name': 'Admin',
            'last_name': 'User',
            'user_type': 'admin',
            'is_verified': True,
            'company_name': 'Get Fit Platform',
            'bio': 'Platform Administrator'
        }
    )
    if created:
        admin_user.set_password('adminpass123')
        admin_user.save()
        logger.info(f'Created admin user: {admin_user.email}')
    
    # Create instructor users
    instructors_data = [
        {
            'email': 'sarah.yoga@getfit.com',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'bio': 'Certified yoga instructor with 8 years of experience. Specializes in Vinyasa and Hatha yoga.',
            'company_name': 'Yoga Studio Plus'
        },
        {
            'email': 'mike.pilates@getfit.com',
            'first_name': 'Mike',
            'last_name': 'Chen',
            'bio': 'Pilates instructor with 5 years of experience. Focuses on core strength and flexibility.',
            'company_name': 'Core Fitness Studio'
        },
        {
            'email': 'jessica.cardio@getfit.com',
            'first_name': 'Jessica',
            'last_name': 'Williams',
            'bio': 'High-energy cardio instructor specializing in HIIT and dance fitness.',
            'company_name': 'Energy Fitness'
        },
        {
            'email': 'david.strength@getfit.com',
            'first_name': 'David',
            'last_name': 'Brown',
            'bio': 'Strength training specialist with 10 years of experience in functional fitness.',
            'company_name': 'Power Gym'
        },
        {
            'email': 'emma.spinning@getfit.com',
            'first_name': 'Emma',
            'last_name': 'Davis',
            'bio': 'Spinning instructor passionate about indoor cycling and endurance training.',
            'company_name': 'Cycle Studio'
        }
    ]
    
    instructors = []
    for instructor_data in instructors_data:
        instructor, created = User.objects.get_or_create(
            email=instructor_data['email'],
            defaults={
                'first_name': instructor_data['first_name'],
                'last_name': instructor_data['last_name'],
                'user_type': 'instructor',
                'is_verified': True,
                'bio': instructor_data['bio'],
                'company_name': instructor_data['company_name']
            }
        )
        if created:
            instructor.set_password('instructor123')
            instructor.save()
            logger.info(f'Created instructor: {instructor.email}')
        instructors.append(instructor)
    
    # Create class categories
    categories_data = [
        {'name': 'Yoga', 'description': 'Mind-body practices for flexibility, strength, and relaxation'},
        {'name': 'Pilates', 'description': 'Core strengthening and flexibility training'},
        {'name': 'Cardio', 'description': 'High-intensity cardiovascular workouts'},
        {'name': 'Strength Training', 'description': 'Muscle building and strength development'},
        {'name': 'Spinning', 'description': 'Indoor cycling workouts'},
        {'name': 'Dance Fitness', 'description': 'Fun dance-based cardio workouts'},
        {'name': 'HIIT', 'description': 'High-Intensity Interval Training'},
        {'name': 'Stretching', 'description': 'Flexibility and mobility training'}
    ]
    
    categories = []
    for category_data in categories_data:
        category, created = ClassCategory.objects.get_or_create(
            name=category_data['name'],
            defaults={'description': category_data['description']}
        )
        if created:
            logger.info(f'Created category: {category.name}')
        categories.append(category)
    
    # Sample classes data
    classes_data = [
        # Yoga Classes
        {
            'name': 'Morning Vinyasa Flow',
            'description': 'Start your day with a dynamic vinyasa flow that energizes your body and mind.',
            'category': categories[0],  # Yoga
            'instructor': instructors[0],  # Sarah
            'duration': 60,
            'max_capacity': 20,
            'price': 15.00,
            'difficulty_level': 'intermediate',
            'is_featured': True
        },
        {
            'name': 'Gentle Hatha Yoga',
            'description': 'Perfect for beginners. Focus on basic poses and breathing techniques.',
            'category': categories[0],  # Yoga
            'instructor': instructors[0],  # Sarah
            'duration': 75,
            'max_capacity': 25,
            'price': 12.00,
            'difficulty_level': 'beginner',
            'is_featured': False
        },
        {
            'name': 'Power Yoga',
            'description': 'Intensive yoga session combining strength, flexibility, and cardio.',
            'category': categories[0],  # Yoga
            'instructor': instructors[0],  # Sarah
            'duration': 90,
            'max_capacity': 18,
            'price': 18.00,
            'difficulty_level': 'advanced',
            'is_featured': True
        },
        
        # Pilates Classes
        {
            'name': 'Mat Pilates Basics',
            'description': 'Learn the fundamentals of Pilates on the mat. Great for core strength.',
            'category': categories[1],  # Pilates
            'instructor': instructors[1],  # Mike
            'duration': 45,
            'max_capacity': 15,
            'price': 14.00,
            'difficulty_level': 'beginner',
            'is_featured': False
        },
        {
            'name': 'Advanced Pilates',
            'description': 'Challenging Pilates session for experienced practitioners.',
            'category': categories[1],  # Pilates
            'instructor': instructors[1],  # Mike
            'duration': 60,
            'max_capacity': 12,
            'price': 16.00,
            'difficulty_level': 'advanced',
            'is_featured': True
        },
        
        # Cardio Classes
        {
            'name': 'Cardio Blast',
            'description': 'High-energy cardio workout combining various exercises for maximum calorie burn.',
            'category': categories[2],  # Cardio
            'instructor': instructors[2],  # Jessica
            'duration': 45,
            'max_capacity': 30,
            'price': 13.00,
            'difficulty_level': 'intermediate',
            'is_featured': False
        },
        {
            'name': 'Dance Cardio',
            'description': 'Fun dance-based cardio class. No dance experience required!',
            'category': categories[5],  # Dance Fitness
            'instructor': instructors[2],  # Jessica
            'duration': 60,
            'max_capacity': 35,
            'price': 12.00,
            'difficulty_level': 'beginner',
            'is_featured': True
        },
        
        # Strength Training
        {
            'name': 'Total Body Strength',
            'description': 'Comprehensive strength training targeting all major muscle groups.',
            'category': categories[3],  # Strength Training
            'instructor': instructors[3],  # David
            'duration': 60,
            'max_capacity': 20,
            'price': 15.00,
            'difficulty_level': 'intermediate',
            'is_featured': False
        },
        {
            'name': 'Power Lifting',
            'description': 'Advanced strength training focusing on compound movements.',
            'category': categories[3],  # Strength Training
            'instructor': instructors[3],  # David
            'duration': 75,
            'max_capacity': 15,
            'price': 18.00,
            'difficulty_level': 'advanced',
            'is_featured': True
        },
        
        # Spinning
        {
            'name': 'Morning Spin',
            'description': 'Energizing morning cycling session to start your day right.',
            'category': categories[4],  # Spinning
            'instructor': instructors[4],  # Emma
            'duration': 45,
            'max_capacity': 25,
            'price': 14.00,
            'difficulty_level': 'intermediate',
            'is_featured': False
        },
        {
            'name': 'Endurance Spin',
            'description': 'Long-distance cycling simulation for endurance training.',
            'category': categories[4],  # Spinning
            'instructor': instructors[4],  # Emma
            'duration': 90,
            'max_capacity': 20,
            'price': 16.00,
            'difficulty_level': 'advanced',
            'is_featured': True
        },
        
        # HIIT Classes
        {
            'name': 'HIIT Circuit',
            'description': 'High-intensity interval training with circuit-style exercises.',
            'category': categories[6],  # HIIT
            'instructor': instructors[2],  # Jessica
            'duration': 30,
            'max_capacity': 25,
            'price': 13.00,
            'difficulty_level': 'intermediate',
            'is_featured': False
        },
        {
            'name': 'Tabata Training',
            'description': 'Intense Tabata-style HIIT workout for maximum fat burn.',
            'category': categories[6],  # HIIT
            'instructor': instructors[3],  # David
            'duration': 45,
            'max_capacity': 20,
            'price': 15.00,
            'difficulty_level': 'advanced',
            'is_featured': True
        },
        
        # Stretching
        {
            'name': 'Flexibility Flow',
            'description': 'Gentle stretching session to improve flexibility and mobility.',
            'category': categories[7],  # Stretching
            'instructor': instructors[0],  # Sarah
            'duration': 45,
            'max_capacity': 30,
            'price': 10.00,
            'difficulty_level': 'beginner',
            'is_featured': False
        },
        
        # Additional Classes
        {
            'name': 'Yin Yoga',
            'description': 'Slow-paced yoga with long-held poses for deep stretching.',
            'category': categories[0],  # Yoga
            'instructor': instructors[0],  # Sarah
            'duration': 75,
            'max_capacity': 20,
            'price': 14.00,
            'difficulty_level': 'beginner',
            'is_featured': False
        },
        {
            'name': 'Reformer Pilates',
            'description': 'Pilates on the reformer machine for enhanced resistance training.',
            'category': categories[1],  # Pilates
            'instructor': instructors[1],  # Mike
            'duration': 60,
            'max_capacity': 8,
            'price': 25.00,
            'difficulty_level': 'intermediate',
            'is_featured': True
        },
        {
            'name': 'Zumba Fitness',
            'description': 'Latin-inspired dance fitness class that\'s fun and effective.',
            'category': categories[5],  # Dance Fitness
            'instructor': instructors[2],  # Jessica
            'duration': 60,
            'max_capacity': 40,
            'price': 12.00,
            'difficulty_level': 'beginner',
            'is_featured': True
        },
        {
            'name': 'Functional Training',
            'description': 'Movement-based strength training for everyday activities.',
            'category': categories[3],  # Strength Training
            'instructor': instructors[3],  # David
            'duration': 60,
            'max_capacity': 18,
            'price': 16.00,
            'difficulty_level': 'intermediate',
            'is_featured': False
        },
        {
            'name': 'Recovery Spin',
            'description': 'Low-intensity cycling session perfect for active recovery.',
            'category': categories[4],  # Spinning
            'instructor': instructors[4],  # Emma
            'duration': 45,
            'max_capacity': 25,
            'price': 12.00,
            'difficulty_level': 'beginner',
            'is_featured': False
        },
        {
            'name': 'Core Focus',
            'description': 'Intensive core strengthening and stability training.',
            'category': categories[1],  # Pilates
            'instructor': instructors[1],  # Mike
            'duration': 45,
            'max_capacity': 20,
            'price': 13.00,
            'difficulty_level': 'intermediate',
            'is_featured': False
        }
    ]
    
    # Create classes
    created_classes = []
    for class_data in classes_data:
        fitness_class, created = FitnessClass.objects.get_or_create(
            name=class_data['name'],
            defaults=class_data
        )
        if created:
            logger.info(f'Created class: {fitness_class.name}')
        created_classes.append(fitness_class)
    
    # Create class schedules for the next 30 days
    schedule_times = [
        ('06:00', 'morning'),
        ('07:00', 'morning'),
        ('08:00', 'morning'),
        ('09:00', 'morning'),
        ('10:00', 'morning'),
        ('12:00', 'afternoon'),
        ('13:00', 'afternoon'),
        ('14:00', 'afternoon'),
        ('15:00', 'afternoon'),
        ('16:00', 'afternoon'),
        ('17:00', 'evening'),
        ('18:00', 'evening'),
        ('19:00', 'evening'),
        ('20:00', 'evening'),
    ]
    
    # Days of the week (0=Monday, 6=Sunday)
    days_of_week = [0, 1, 2, 3, 4, 5, 6]  # All days
    
    # Create schedules for the next 30 days
    start_date = timezone.now().date()
    for day_offset in range(30):
        current_date = start_date + timedelta(days=day_offset)
        day_of_week = current_date.weekday()
        
        # Create 2-4 schedules per day
        num_schedules = random.randint(2, 4)
        selected_times = random.sample(schedule_times, num_schedules)
        
        for time_str, time_of_day in selected_times:
            # Randomly select a class
            fitness_class = random.choice(created_classes)
            
            # Create schedule
            schedule_time = datetime.strptime(time_str, '%H:%M').time()
            schedule_datetime = datetime.combine(current_date, schedule_time)
            
            # Add some randomness to capacity
            current_capacity = random.randint(0, fitness_class.max_capacity)
            
            schedule, created = ClassSchedule.objects.get_or_create(
                fitness_class=fitness_class,
                start_time=schedule_datetime,
                defaults={
                    'end_time': schedule_datetime + timedelta(minutes=fitness_class.duration),
                    'current_capacity': current_capacity,
                    'is_active': True
                }
            )
            if created:
                logger.info(f'Created schedule: {fitness_class.name} on {current_date} at {time_str}')
    
    logger.info(f'Successfully created {len(created_classes)} classes with schedules')


def remove_sample_classes(apps, schema_editor):
    """
    Remove sample classes created by this migration.
    """
    User = apps.get_model('users', 'User')
    ClassCategory = apps.get_model('classes', 'ClassCategory')
    FitnessClass = apps.get_model('classes', 'FitnessClass')
    ClassSchedule = apps.get_model('classes', 'ClassSchedule')
    
    # Remove schedules first
    ClassSchedule.objects.all().delete()
    
    # Remove classes
    FitnessClass.objects.all().delete()
    
    # Remove categories
    ClassCategory.objects.all().delete()
    
    # Remove instructor users (but keep admin)
    User.objects.filter(user_type='instructor').delete()
    
    logger.info('Removed all sample classes and related data')


class Migration(migrations.Migration):
    """
    Migration to create sample fitness classes.
    """
    
    dependencies = [
        ('classes', '0001_initial'),
        ('users', '0003_remove_user_license_number_remove_user_website_and_more'),
    ]
    
    operations = [
        migrations.RunPython(create_sample_classes, remove_sample_classes),
    ] 