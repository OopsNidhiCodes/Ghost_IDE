-- Initialize the database with required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create initial tables will be handled by SQLAlchemy migrations
-- This file is for any initial database setup that needs to happen before the application starts