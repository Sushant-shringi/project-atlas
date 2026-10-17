<?php
defined('BASEPATH') OR exit('No direct script access allowed');

$autoload['packages'] = array();
$autoload['libraries'] = array('session', 'atlas_api');
$autoload['drivers'] = array();
$autoload['helper'] = array('url', 'security', 'html');
$autoload['config'] = array('atlas_api');
$autoload['language'] = array();
$autoload['model'] = array('conversation_model');
