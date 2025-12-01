from app.modules.auth.models import User
from app.modules.profile.models import UserProfile
from core.seeders.BaseSeeder import BaseSeeder


class AuthSeeder(BaseSeeder):

    priority = 1  # Higher priority

    def run(self):

        # Check if users already exist
        existing_users = []
        users_to_create = []

        user_data = [
            ("user1@example.com", "1234"),
            ("user2@example.com", "1234"),
        ]

        for email, password in user_data:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                existing_users.append(existing_user)
            else:
                users_to_create.append(User(email=email, password=password))

        # Seed only new users
        seeded_users = []
        if users_to_create:
            seeded_users = self.seed(users_to_create)

        # Combine existing and newly seeded users
        all_users = existing_users + seeded_users

        # Create profiles for each user (skip if profile already exists)
        user_profiles = []
        names = [("John", "Doe"), ("Jane", "Doe")]

        for user, name in zip(all_users, names):
            # Check if profile already exists
            existing_profile = UserProfile.query.filter_by(user_id=user.id).first()
            if not existing_profile:
                profile_data = {
                    "user_id": user.id,
                    "orcid": "",
                    "affiliation": "Some University",
                    "name": name[0],
                    "surname": name[1],
                }
                user_profile = UserProfile(**profile_data)
                user_profiles.append(user_profile)

        # Seeding user profiles
        if user_profiles:
            self.seed(user_profiles)
