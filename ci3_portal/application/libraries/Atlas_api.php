<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/**
 * Project Atlas - CodeIgniter 3 API Service Client
 * Handles communication with the Python FastAPI backend with timeouts,
 * secure server-side client authentication, and error containment.
 */
class Atlas_api {

    protected $CI;
    protected $base_url;
    protected $timeout;
    protected $client_keys;

    public function __construct() {
        $this->CI =& get_instance();
        $this->CI->load->config('atlas_api', TRUE);
        $raw_url = $this->CI->config->item('atlas_api_base_url', 'atlas_api') ?: 'http://api:8000';
        $this->base_url = rtrim((string)$raw_url, '/');
        $this->timeout = $this->CI->config->item('atlas_api_timeout', 'atlas_api') ?: 25;
        $this->client_keys = $this->CI->config->item('atlas_client_keys', 'atlas_api') ?: array();
    }

    /**
     * Resolves the server-side API key for a client from MySQL database or config.
     */
    public function get_client_key($client_id) {
        // 1. Lookup from MySQL clients table directly
        if (isset($this->CI->db)) {
            $row = $this->CI->db->get_where('clients', array('id' => $client_id))->row_array();
            if (!empty($row['api_key'])) {
                return $row['api_key'];
            }
        }

        // 2. Fallback to loaded config mapping
        if (isset($this->client_keys[$client_id]['api_key'])) {
            return $this->client_keys[$client_id]['api_key'];
        }

        return NULL;
    }

    /**
     * Executes POST /chat with authenticated client credentials.
     */
    public function query_copilot($client_id, $question, $conversation_id = NULL) {
        $api_key = $this->get_client_key($client_id);
        if (!$api_key) {
            return array(
                'success' => FALSE,
                'error' => 'Client identity not configured on server.',
                'answer' => 'Authentication Error: Unrecognized client credentials.'
            );
        }

        $payload = array(
            'client_id' => $client_id,
            'question' => $question,
            'conversation_id' => $conversation_id
        );

        $headers = array(
            'Content-Type: application/json',
            'X-Client-Key: ' . $api_key
        );

        $url = $this->base_url . '/chat';
        $result = $this->_execute_request('POST', $url, $payload, $headers);
        return $result;
    }

    /**
     * Executes POST /feedback to record thumbs-up or down feedback.
     */
    public function submit_feedback($message_id, $client_id, $rating, $comment = '') {
        $api_key = $this->get_client_key($client_id);
        $payload = array(
            'message_id' => $message_id,
            'client_id' => $client_id,
            'rating' => $rating,
            'comment' => $comment
        );
        $headers = array(
            'Content-Type: application/json',
            'X-Client-Key: ' . $api_key
        );
        $url = $this->base_url . '/feedback';
        return $this->_execute_request('POST', $url, $payload, $headers);
    }

    /**
     * Executes GET /escalations.
     */
    public function get_escalations($client_id) {
        $api_key = $this->get_client_key($client_id);
        $headers = array(
            'X-Client-Key: ' . $api_key
        );
        $url = $this->base_url . '/escalations?client_id=' . urlencode($client_id);
        return $this->_execute_request('GET', $url, NULL, $headers);
    }

    /**
     * Executes GET /health.
     */
    public function get_health() {
        $url = $this->base_url . '/health';
        return $this->_execute_request('GET', $url);
    }

    /**
     * Private cURL executor with error and timeout handling.
     */
    protected function _execute_request($method, $url, $payload = NULL, $headers = array()) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, TRUE);
        curl_setopt($ch, CURLOPT_TIMEOUT, $this->timeout);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 5);

        if (!empty($headers)) {
            curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        }

        if ($method === 'POST') {
            curl_setopt($ch, CURLOPT_POST, TRUE);
            if ($payload !== NULL) {
                curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
            }
        }

        $raw_response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curl_error = curl_error($ch);
        curl_close($ch);

        if ($curl_error) {
            log_message('error', 'Atlas_api cURL error: ' . $curl_error);
            return array(
                'success' => FALSE,
                'error' => 'Backend service is currently unavailable or timed out.',
                'answer' => 'Connection Notice: The Report Copilot service did not respond within the allocated timeout. Please retry in a few moments.'
            );
        }

        $decoded = json_decode($raw_response, TRUE);
        if ($http_code >= 400 || !is_array($decoded)) {
            $msg = isset($decoded['detail']) ? $decoded['detail'] : 'Backend service returned an error status (' . $http_code . ').';
            return array(
                'success' => FALSE,
                'http_code' => $http_code,
                'error' => $msg,
                'answer' => 'Notice: ' . $msg
            );
        }

        $decoded['success'] = TRUE;
        return $decoded;
    }
}
