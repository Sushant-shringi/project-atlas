<?php
defined('BASEPATH') OR exit('No direct script access allowed');

// Backend Python FastAPI Base URL
$config['atlas_api_base_url'] = getenv('API_BASE_URL') ?: 'http://api:8000';
$config['atlas_api_timeout'] = 30; // Seconds

// Server-Side Client API Key Mapping (Strictly kept server-side; NEVER leaked to browser!)
$config['atlas_client_keys'] = array(
    'C-01' => array(
        'company_name' => 'Northwind Utilities',
        'api_key' => 'client_key_c01_northwind_utilities_secret_2026',
        'purchased_reports' => array('R-101', 'R-103'),
        'accessible_excerpts' => array('R-102')
    ),
    'C-02' => array(
        'company_name' => 'Blue Delta Infra',
        'api_key' => 'client_key_c02_blue_delta_infra_secret_2026',
        'purchased_reports' => array('R-103'),
        'accessible_excerpts' => array('R-102')
    )
);
