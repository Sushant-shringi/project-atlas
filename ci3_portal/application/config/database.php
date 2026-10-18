<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/**
 * Project Atlas - CodeIgniter 3 Database Configuration
 * Connects to the project MySQL container via mysqli driver.
 */

$active_group = 'default';
$query_builder = TRUE;

$mysql_host = getenv('MYSQL_HOST') ?: ($_SERVER['MYSQL_HOST'] ?? 'mysql');
$mysql_port = (int)(getenv('MYSQL_PORT') ?: ($_SERVER['MYSQL_PORT'] ?? 3306));
$mysql_user = getenv('MYSQL_USER') ?: ($_SERVER['MYSQL_USER'] ?? 'atlas_app');
$mysql_password = getenv('MYSQL_PASSWORD') ?: ($_SERVER['MYSQL_PASSWORD'] ?? 'atlas_app_secure_password');
$mysql_database = getenv('MYSQL_DATABASE') ?: ($_SERVER['MYSQL_DATABASE'] ?? 'project_atlas');

$db['default'] = array(
	'dsn'	=> '',
	'hostname' => $mysql_host,
	'username' => $mysql_user,
	'password' => $mysql_password,
	'database' => $mysql_database,
	'port'     => $mysql_port,
	'dbdriver' => 'mysqli',
	'dbprefix' => '',
	'pconnect' => FALSE,
	'db_debug' => FALSE, // Suppress raw DB error exposure to browser
	'cache_on' => FALSE,
	'cachedir' => '',
	'char_set' => 'utf8mb4',
	'dbcollat' => 'utf8mb4_unicode_ci',
	'swap_pre' => '',
	'encrypt' => FALSE,
	'compress' => FALSE,
	'stricton' => FALSE,
	'failover' => array(),
	'save_queries' => TRUE
);
