-- ==============================================================================
-- PROJECT ATLAS - MYSQL SEED DATA (02-seed.sql)
-- Seed data for clients, reports, entitlements, and market metrics.
-- ==============================================================================

USE `project_atlas`;

-- 1. Seed Reports Catalog
INSERT INTO `reports` (`id`, `title`, `publisher`, `published_date`, `sector`, `access_type`, `summary`, `total_pages`, `file_path`) VALUES
('R-101', 'Global Smart Water Meter Market 2025', 'CMR', '2025-03-10', 'Utilities', 'paid', 
 'Comprehensive global market analysis of advanced metering infrastructure (AMI) and automated meter reading (AMR) across hardware, software, and managed utility services.', 
 24, 'reports/R-101_Global_Smart_Water_Meter_Market_2025.txt'),

('R-102', 'Smart Water Metering: Industry Outlook 2024', 'Aquila Insights', '2024-06-18', 'Utilities', 'public_excerpt', 
 'Industry outlook examining utility adoption, regulatory pressures, and procurement of smart water meter hardware units and communications modules.', 
 18, 'reports/R-102_Smart_Water_Metering_Industry_Outlook_2024.txt'),

('R-103', 'Residential Water Purifier Market 2025', 'CMR', '2025-01-22', 'Consumer Durables', 'paid', 
 'Global overview of point-of-use and point-of-entry residential water purification systems including reverse osmosis, ultraviolet, and ultrafiltration technologies.', 
 20, 'reports/R-103_Residential_Water_Purifier_Market_2025.txt'),

('R-104', 'Industrial IoT Sensors Market 2025', 'Precision Sense', '2025-02-14', 'Manufacturing', 'paid', 
 'Analysis of edge sensing deployments, vibration monitoring, and predictive maintenance sensors in discrete and process manufacturing facilities.', 
 22, 'reports/R-104_Industrial_IoT_Sensors_Market_2025.txt'),

('R-105', 'Commercial Heat Pump Systems Outlook 2024', 'ThermalDynamics', '2024-11-05', 'Energy & HVAC', 'paid', 
 'Market evaluation of commercial and district heating heat pumps, industrial refrigeration heat recovery, and decarbonization incentives.', 
 26, 'reports/R-105_Commercial_Heat_Pump_Systems_Outlook_2024.txt'),

('R-106', 'Electric Vehicle Charging Infrastructure Market 2025', 'VoltMetrics', '2025-04-01', 'Automotive & Mobility', 'paid', 
 'Global study of public and private EV fast charging stations, ultra-fast DC dispensers, grid integration, and fleet depot electrification.', 
 30, 'reports/R-106_Electric_Vehicle_Charging_Infrastructure_Market_2025.txt'),

('R-107', 'Agricultural Drone & Precision Farming Report 2025', 'AgriTech Review', '2025-05-18', 'Agriculture', 'paid', 
 'Market trends in autonomous agricultural aerial vehicles, multispectral crop health mapping, and targeted precision pesticide and fertilizer dispersion.', 
 19, 'reports/R-107_Agricultural_Drone_Precision_Farming_Report_2025.txt')
ON DUPLICATE KEY UPDATE `title` = VALUES(`title`), `summary` = VALUES(`summary`);

-- 2. Seed Clients
-- Client C-01: Northwind Utilities
-- Client C-02: Blue Delta Infra
INSERT INTO `clients` (`id`, `company_name`, `contact_email`, `api_key`, `status`) VALUES
('C-01', 'Northwind Utilities', 'northwind.analyst@example-corp.internal', 'client_key_c01_northwind_utilities_secret_2026', 'active'),
('C-02', 'Blue Delta Infra', 'research.team@bluedelta-infra.internal', 'client_key_c02_blue_delta_infra_secret_2026', 'active')
ON DUPLICATE KEY UPDATE `company_name` = VALUES(`company_name`), `api_key` = VALUES(`api_key`);

-- 3. Seed Normalized Report Entitlements
-- Client C-01 purchased R-101 and R-103
-- Client C-02 purchased R-103
-- Note: R-102 is a public excerpt, managed through public excerpt permissions
INSERT INTO `report_entitlements` (`client_id`, `report_id`, `access_granted`, `scope`, `valid_from`, `valid_to`) VALUES
('C-01', 'R-101', TRUE, 'full', '2025-01-01', '2027-12-31'),
('C-01', 'R-103', TRUE, 'full', '2025-01-01', '2027-12-31'),
('C-02', 'R-103', TRUE, 'full', '2025-01-01', '2027-12-31')
ON DUPLICATE KEY UPDATE `access_granted` = VALUES(`access_granted`), `scope` = VALUES(`scope`);

-- 4. Seed Material Market Research Metrics
INSERT INTO `market_metrics` 
(`report_id`, `metric_name`, `metric_value`, `unit`, `year`, `cagr`, `cagr_period`, `region`, `scope`, `page_number`, `source_quote`) 
VALUES
-- R-101 Smart Water Meter Market (CMR)
('R-101', 'Global Smart Water Meter Market Size', 4.21, 'USD Billion', 2024, 11.20, '2025-2030', 'Global', 'Hardware, software, and services', 8,
 'The global smart water meter market was valued at USD 4.21 billion in 2024 and is expected to grow at a CAGR of 11.2% from 2025 to 2030. Asia-Pacific accounted for 38% of 2024 revenue.'),

('R-101', 'Asia-Pacific Regional Market Share', 38.00, 'Percent', 2024, NULL, NULL, 'Asia-Pacific', 'Hardware, software, and services', 8,
 'Asia-Pacific accounted for 38% of 2024 revenue, driven by aggressive municipal utility modernization programs across China, India, and Japan.'),

-- R-102 Smart Water Metering Industry Outlook (Aquila Insights)
('R-102', 'Global Smart Water Metering Hardware Market Size', 3.87, 'USD Billion', 2024, 9.80, '2024-2029', 'Global', 'AMR/AMI hardware only', 14,
 'Global smart water meter hardware revenue reached USD 3.87 billion in 2024, expanding at a compound annual growth rate of 9.8% through 2029.'),

('R-102', 'Asia-Pacific Hardware Market Share', 41.00, 'Percent', 2024, NULL, NULL, 'Asia-Pacific', 'AMR/AMI hardware only', 14,
 'Asia-Pacific represented 41% of global physical unit shipments and module revenue in 2024.'),

-- R-103 Residential Water Purifier Market (CMR)
('R-103', 'Global Residential Water Purifier Market Size', 9.45, 'USD Billion', 2024, 7.40, '2025-2030', 'Global', 'RO, UV, and ultrafiltration point-of-use systems', 11,
 'The residential water purifier market reached USD 9.45 billion in 2024, propelled by growing consumer health awareness and municipal water quality challenges.'),

('R-103', 'North America Purifier Market Share', 34.00, 'Percent', 2024, NULL, NULL, 'North America', 'Point-of-use systems', 12,
 'North America accounted for 34% of global purification revenue in 2024.'),

-- R-104 Industrial IoT Sensors Market (Precision Sense)
('R-104', 'Global Industrial IoT Sensors Market Size', 12.80, 'USD Billion', 2024, 14.50, '2025-2030', 'Global', 'Vibration, acoustic, and thermal sensors', 6,
 'The global industrial IoT sensor sector reached USD 12.80 billion in 2024, with predictive maintenance adoption driving a 14.5% projected CAGR through 2030.'),

-- R-105 Commercial Heat Pump Systems Outlook (ThermalDynamics)
('R-105', 'Global Commercial Heat Pump Market Size', 7.15, 'USD Billion', 2023, 8.60, '2024-2029', 'Global', 'Air-source and ground-source commercial hydronic units', 9,
 'Commercial heat pump market valuation totaled USD 7.15 billion in 2023, supported by building decarbonization standards across the European Union and North America.'),

-- R-106 Electric Vehicle Charging Infrastructure Market (VoltMetrics)
('R-106', 'Global EV Charging Infrastructure Market Size', 26.50, 'USD Billion', 2024, 24.10, '2025-2030', 'Global', 'Level 2 AC and Level 3 DC fast charging hardware and networking', 15,
 'The worldwide EV charging infrastructure market stood at USD 26.50 billion in 2024, projected to expand at an exceptional CAGR of 24.1% through 2030.'),

-- R-107 Agricultural Drone Precision Farming (AgriTech Review)
('R-107', 'Global Agricultural Drone Market Size', 3.60, 'USD Billion', 2024, 18.20, '2025-2030', 'Global', 'Multispectral remote sensing and automated spray drones', 12,
 'Agricultural drone hardware and analytics platforms generated USD 3.60 billion in 2024, forecast to grow at an 18.2% CAGR from 2025 to 2030.');
