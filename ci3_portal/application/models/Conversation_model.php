<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/**
 * Project Atlas - CodeIgniter 3 Conversation Model
 * Tracks active session conversation IDs and loads recent message histories.
 */
class Conversation_model extends CI_Model {

    public function __construct() {
        parent::__construct();
        $this->load->library('session');
    }

    /**
     * Gets current client ID from session.
     */
    private function _get_client_id() {
        return $this->session->userdata('atlas_client_id') ?: 'C-01';
    }

    /**
     * Gets or creates the current conversation ID in the user session scoped to the client.
     */
    public function get_active_conversation_id() {
        $client_id = $this->_get_client_id();
        $key = 'atlas_conv_id_' . $client_id;
        $conv_id = $this->session->userdata($key);
        if (!$conv_id) {
            $conv_id = 'conv-' . strtolower(str_replace('-', '', $client_id)) . '-' . bin2hex(random_bytes(4));
            $this->session->set_userdata($key, $conv_id);
        }
        return $conv_id;
    }

    /**
     * Resets active conversation session for the current client.
     */
    public function new_conversation() {
        $client_id = $this->_get_client_id();
        $key = 'atlas_conv_id_' . $client_id;
        $msg_key = 'atlas_messages_' . $client_id;
        $conv_id = 'conv-' . strtolower(str_replace('-', '', $client_id)) . '-' . bin2hex(random_bytes(4));
        $this->session->set_userdata($key, $conv_id);
        $this->session->set_userdata($msg_key, array());
        return $conv_id;
    }

    /**
     * Appends message to session cache for rendering scoped to the client.
     */
    public function add_message($role, $content, $metadata = array()) {
        $client_id = $this->_get_client_id();
        $msg_key = 'atlas_messages_' . $client_id;
        $messages = $this->session->userdata($msg_key) ?: array();
        $msg_id = 'msg-' . bin2hex(random_bytes(6));
        $messages[] = array(
            'id' => $msg_id,
            'role' => $role,
            'content' => $content,
            'metadata' => $metadata,
            'timestamp' => date('Y-m-d H:i:s')
        );
        $this->session->set_userdata($msg_key, $messages);
        return $msg_id;
    }

    /**
     * Retrieves stored session messages for the current client.
     */
    public function get_messages() {
        $client_id = $this->_get_client_id();
        $msg_key = 'atlas_messages_' . $client_id;
        return $this->session->userdata($msg_key) ?: array();
    }
}

