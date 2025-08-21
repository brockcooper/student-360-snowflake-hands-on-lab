-- Student 360 – Reset script
-- This will remove all objects created by the lab by dropping the databases.
-- Note: This does NOT touch your warehouses or any external resources (e.g., S3).

USE ROLE SYSADMIN;

-- Drop analytics/reporting warehouse database and all contained objects
DROP DATABASE IF EXISTS STUDENT_DATA_WAREHOUSE;

-- Drop source/lake database and all contained objects (schemas, stages, file formats, tables)
DROP DATABASE IF EXISTS STUDENT_DATA_LAKE;


