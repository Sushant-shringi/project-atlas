<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/**
 * Project Atlas - CodeIgniter 3 Chat Controller
 * Manages chat interface, tenant identity switching, AJAX query dispatch,
 * thumbs up/down feedback, and escalation viewing.
 */
class Chat extends CI_Controller {

    public function __construct() {
        parent::__construct();
        $this->load->library('session');
        $this->load->library('atlas_api');
        $this->load->model('conversation_model');
        $this->load->model('client_model');
        $this->load->helper('security');
        $this->load->helper('url');

        // Set default authenticated client to C-01 (Northwind Utilities) if not set
        if (!$this->session->userdata('atlas_client_id')) {
            $this->session->set_userdata('atlas_client_id', 'C-01');
        }
    }

    /**
     * Main Portal Chat View.
     */
    public function index() {
        $client_id = $this->session->userdata('atlas_client_id') ?: 'C-01';

        // 1. Fetch real client company name from MySQL
        $client_row = $this->client_model->get_client($client_id);
        $company_name = !empty($client_row['company_name']) ? $client_row['company_name'] : 'Unknown Enterprise';

        // 2. Fetch real entitlements and complete catalog access from MySQL
        $entitlements_summary = $this->client_model->get_client_entitlements_summary($client_id);
        $catalog_reports = $this->client_model->get_catalog_access($client_id);

        $client_info = array(
            'company_name' => $company_name,
            'purchased_reports' => $entitlements_summary['purchased_reports'],
            'accessible_excerpts' => $entitlements_summary['accessible_excerpts']
        );

        $data = array(
            'client_id' => $client_id,
            'client_info' => $client_info,
            'catalog_reports' => $catalog_reports,
            'conversation_id' => $this->conversation_model->get_active_conversation_id(),
            'messages' => $this->conversation_model->get_messages(),
            'csrf_name' => $this->security->get_csrf_token_name(),
            'csrf_hash' => $this->security->get_csrf_hash()
        );

        $this->load->view('chat_view', $data);
    }

    /**
     * AJAX endpoint to dispatch a query to the Python Copilot API.
     */
    public function send_message() {
        // Enforce JSON header
        $this->output->set_content_type('application/json');

        // Verify CSRF
        // CI3 automatically checks CSRF if enabled, but we also verify post input
        $question = trim($this->input->post('question', TRUE));
        if (empty($question)) {
            $this->output->set_status_header(400);
            echo json_encode(array('success' => FALSE, 'error' => 'Question cannot be empty.'));
            return;
        }

        // Use the authenticated server-side identity — do NOT trust client ID from untrusted browser!
        $client_id = $this->session->userdata('atlas_client_id');
        $conv_id = $this->conversation_model->get_active_conversation_id();

        // Record user message in session history
        $this->conversation_model->add_message('user', $question);

        // Call Python API via library wrapper
        $api_result = $this->atlas_api->query_copilot($client_id, $question, $conv_id);

        if ($api_result && isset($api_result['answer'])) {
            // Record assistant response
            $msg_id = $this->conversation_model->add_message('assistant', $api_result['answer'], $api_result);
            $api_result['message_id'] = $msg_id;
        }

        // Return new CSRF token hash for subsequent AJAX requests
        $api_result['csrf_name'] = $this->security->get_csrf_token_name();
        $api_result['csrf_hash'] = $this->security->get_csrf_hash();

        echo json_encode($api_result);
    }

    /**
     * AJAX endpoint to submit thumbs up / down feedback.
     */
    public function feedback() {
        $this->output->set_content_type('application/json');

        $message_id = $this->input->post('message_id', TRUE);
        $rating = $this->input->post('rating', TRUE);
        $comment = $this->input->post('comment', TRUE);

        if (!$message_id || !in_array($rating, array('thumbs_up', 'thumbs_down'))) {
            $this->output->set_status_header(400);
            echo json_encode(array('success' => FALSE, 'error' => 'Invalid feedback parameters.'));
            return;
        }

        $client_id = $this->session->userdata('atlas_client_id');
        $res = $this->atlas_api->submit_feedback($message_id, $client_id, $rating, $comment);

        $res['csrf_name'] = $this->security->get_csrf_token_name();
        $res['csrf_hash'] = $this->security->get_csrf_hash();
        echo json_encode($res);
    }

    /**
     * Switch client identity (used for demo between Client C-01 and Client C-02).
     */
    public function switch_client() {
        $new_client = $this->input->post('client_id', TRUE);
        if (empty($new_client)) {
            $new_client = $this->input->post('client_btn', TRUE);
        }
        if (in_array($new_client, array('C-01', 'C-02'))) {
            $this->session->set_userdata('atlas_client_id', $new_client);
            $this->conversation_model->get_active_conversation_id();
        }
        header('Location: /chat');
        exit;
    }


    /**
     * Returns JSON list of escalations for the current client.
     */
    public function escalations() {
        $this->output->set_content_type('application/json');
        $client_id = $this->session->userdata('atlas_client_id');
        $res = $this->atlas_api->get_escalations($client_id);
        echo json_encode($res);
    }
}
