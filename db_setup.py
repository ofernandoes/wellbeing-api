# db_setup.py

from app import app, db, User

# Import all models to ensure they are known to SQLAlchemy
from app import WellbeingData 

with app.app_context():
    # Attempt to create tables. If the database file is not present, 
    # SQLite will create it. If tables don't exist, they will be created.
    print("Attempting to create database and tables...")
    db.create_all()
    print("Database creation attempt finished.")

    # Ensure the dummy test user exists (as defined in get_current_user logic)
    if not db.session.execute(db.select(User).filter_by(username='test_user')).scalar_one_or_none():
        dummy_user = User(username='test_user', tier='free')
        db.session.add(dummy_user)
        db.session.commit()
        print("Test user created.")
    else:
        print("Test user already exists.")

print("Database setup script finished.")
