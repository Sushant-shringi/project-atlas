-- ==============================================================================
-- PROJECT ATLAS - MYSQL DATABASE SCHEMA (01-schema.sql)
-- Multi-tenant schema enforcing entitlements, conversations, escalations,
-- audit events, and analytical metrics tracking.
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS `project_atlas` 
  DEFAULT CHARACTER SET utf8mb4 
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `project_atlas`;

-- 1. Reports Catalog
CREATE TABLE IF NOT EXISTS `reports` (
    `id` VARCHAR(32) NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `publisher` VARCHAR(100) NOT NULL,
    `published_date` DATE NOT NULL,
    `sector` VARCHAR(100) NOT NULL,
    `access_type` ENUM('paid', 'public_excerpt', 'free') NOT NULL DEFAULT 'paid',
    `summary` TEXT NULL,
    `total_pages` INT NOT NULL DEFAULT 1,
    `file_path` VARCHAR(255) NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_reports_sector` (`sector`),
    INDEX `idx_reports_access` (`access_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Client Tenants
CREATE TABLE IF NOT EXISTS `clients` (
    `id` VARCHAR(32) NOT NULL,
    `company_name` VARCHAR(255) NOT NULL,
    `contact_email` VARCHAR(255) NOT NULL,
    `api_key` VARCHAR(128) NOT NULL,
    `status` ENUM('active', 'suspended') NOT NULL DEFAULT 'active',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_clients_api_key` (`api_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Normalized Report Entitlements
CREATE TABLE IF NOT EXISTS `report_entitlements` (
    `id` INT AUTO_INCREMENT NOT NULL,
    `client_id` VARCHAR(32) NOT NULL,
    `report_id` VARCHAR(32) NOT NULL,
    `access_granted` BOOLEAN NOT NULL DEFAULT TRUE,
    `scope` ENUM('full', 'public_excerpt') NOT NULL DEFAULT 'full',
    `valid_from` DATE NOT NULL,
    `valid_to` DATE NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_client_report_entitlement` (`client_id`, `report_id`),
    INDEX `idx_entitlement_client` (`client_id`),
    INDEX `idx_entitlement_report` (`report_id`),
    CONSTRAINT `fk_entitlement_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_entitlement_report` FOREIGN KEY (`report_id`) REFERENCES `reports` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Structured Market Research Metrics
CREATE TABLE IF NOT EXISTS `market_metrics` (
    `id` INT AUTO_INCREMENT NOT NULL,
    `report_id` VARCHAR(32) NOT NULL,
    `metric_name` VARCHAR(150) NOT NULL,
    `metric_value` DECIMAL(14,4) NOT NULL,
    `unit` VARCHAR(50) NOT NULL,
    `year` INT NOT NULL,
    `cagr` DECIMAL(6,2) NULL,
    `cagr_period` VARCHAR(50) NULL,
    `region` VARCHAR(100) NOT NULL DEFAULT 'Global',
    `scope` VARCHAR(255) NOT NULL,
    `page_number` INT NOT NULL,
    `source_quote` TEXT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_metrics_report` (`report_id`),
    INDEX `idx_metrics_name_year` (`metric_name`, `year`),
    CONSTRAINT `fk_metrics_report` FOREIGN KEY (`report_id`) REFERENCES `reports` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Conversations
CREATE TABLE IF NOT EXISTS `conversations` (
    `id` VARCHAR(64) NOT NULL,
    `client_id` VARCHAR(32) NOT NULL,
    `title` VARCHAR(255) NOT NULL DEFAULT 'Market Research Chat',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_conversations_client` (`client_id`),
    CONSTRAINT `fk_conversations_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Conversation Messages
CREATE TABLE IF NOT EXISTS `conversation_messages` (
    `id` VARCHAR(64) NOT NULL,
    `conversation_id` VARCHAR(64) NOT NULL,
    `role` ENUM('user', 'assistant', 'system') NOT NULL,
    `content` MEDIUMTEXT NOT NULL,
    `citations_json` JSON NULL,
    `confidence` DECIMAL(4,3) NULL,
    `conflicts_json` JSON NULL,
    `derived_values_json` JSON NULL,
    `escalated` BOOLEAN NOT NULL DEFAULT FALSE,
    `latency_ms` INT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_messages_conversation` (`conversation_id`),
    CONSTRAINT `fk_messages_conversation` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. User Feedback (Thumbs-Up / Thumbs-Down)
CREATE TABLE IF NOT EXISTS `user_feedback` (
    `id` INT AUTO_INCREMENT NOT NULL,
    `message_id` VARCHAR(64) NOT NULL,
    `client_id` VARCHAR(32) NOT NULL,
    `rating` ENUM('thumbs_up', 'thumbs_down') NOT NULL,
    `comment` TEXT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_feedback_message` (`message_id`),
    INDEX `idx_feedback_client` (`client_id`),
    CONSTRAINT `fk_feedback_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Escalation Tickets
CREATE TABLE IF NOT EXISTS `escalation_tickets` (
    `id` VARCHAR(64) NOT NULL,
    `client_id` VARCHAR(32) NOT NULL,
    `conversation_id` VARCHAR(64) NULL,
    `question` TEXT NOT NULL,
    `reason` TEXT NOT NULL,
    `confidence_score` DECIMAL(4,3) NULL,
    `status` ENUM('pending', 'in_review', 'resolved') NOT NULL DEFAULT 'pending',
    `resolution_notes` TEXT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_escalations_client` (`client_id`),
    INDEX `idx_escalations_status` (`status`),
    CONSTRAINT `fk_escalations_client` FOREIGN KEY (`client_id`) REFERENCES `clients` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Security Audit Events
CREATE TABLE IF NOT EXISTS `audit_events` (
    `id` INT AUTO_INCREMENT NOT NULL,
    `client_id` VARCHAR(32) NULL,
    `event_type` VARCHAR(64) NOT NULL,
    `details` JSON NULL,
    `ip_address` VARCHAR(45) NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_audit_event_type` (`event_type`),
    INDEX `idx_audit_client` (`client_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. LLM Usage & Cost Tracking Records
CREATE TABLE IF NOT EXISTS `llm_usage_records` (
    `id` INT AUTO_INCREMENT NOT NULL,
    `request_id` VARCHAR(64) NOT NULL,
    `client_id` VARCHAR(32) NOT NULL,
    `model` VARCHAR(64) NOT NULL,
    `prompt_tokens` INT NOT NULL DEFAULT 0,
    `completion_tokens` INT NOT NULL DEFAULT 0,
    `total_tokens` INT NOT NULL DEFAULT 0,
    `estimated_cost_usd` DECIMAL(10,6) NOT NULL DEFAULT 0.000000,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_usage_request` (`request_id`),
    INDEX `idx_usage_client` (`client_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
