-- ==============================================================================
-- PROJECT ATLAS - DATABASE USER PROVISIONING & LEAST PRIVILEGE (03-users.sql)
-- Configures the operational app user and the restricted read-only SQL tool user.
-- ==============================================================================

USE `project_atlas`;

-- 1. Create Application Operational User
CREATE USER IF NOT EXISTS 'atlas_app'@'%' IDENTIFIED BY 'atlas_app_secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON `project_atlas`.* TO 'atlas_app'@'%';

-- 2. Create Read-Only Analytical User (Restricted Least-Privilege Account)
-- This user is strictly limited to SELECT on public and market metric catalog tables.
-- Cannot read client keys, emails, user chats, feedbacks, or escalations.
-- Cannot execute INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE.
CREATE USER IF NOT EXISTS 'atlas_readonly'@'%' IDENTIFIED BY 'atlas_readonly_secure_password';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'atlas_readonly'@'%';

-- Grant SELECT only on safe catalog tables
GRANT SELECT ON `project_atlas`.`reports` TO 'atlas_readonly'@'%';
GRANT SELECT ON `project_atlas`.`market_metrics` TO 'atlas_readonly'@'%';

FLUSH PRIVILEGES;
