# init_db.py

from app import app, db, User, WellbeingData # Import components from your app.py

# This block runs the code within the Flask application context,
# which is required for SQLAlchemy to interact with the database.
with app.app_context():
    # 1. Create all defined tables (User and WellbeingData)
    db.create_all()
    print("Database tables created successfully.")
    
    # 2. Add a test user if one doesn't exist (to ensure user ID 1 is available)
    if not db.session.execute(db.select(User).filter_by(username='test_user')).scalar_one_or_none():
        dummy_user = User(username='test_user', tier='premium') # Set to premium for full analysis check
        db.session.add(dummy_user)
        db.session.commit()
        print("Default 'test_user' (premium tier) created.")
    else:
        # If the user exists, ensure they are set to premium for this final test
        existing_user = db.session.execute(db.select(User).filter_by(username='test_user')).scalar_one()
        existing_user.tier = 'premium'
        db.session.commit()
        print("Existing 'test_user' updated to premium tier.")
