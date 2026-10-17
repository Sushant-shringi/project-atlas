<?php
defined('BASEPATH') OR exit('No direct script access allowed');

$route['default_controller'] = 'chat';
$route['404_override'] = '';
$route['translate_uri_dashes'] = FALSE;

// Application Routes
$route['chat'] = 'chat/index';
$route['chat/send'] = 'chat/send_message';
$route['chat/feedback'] = 'chat/feedback';
$route['chat/escalations'] = 'chat/escalations';
$route['chat/switch_client'] = 'chat/switch_client';
