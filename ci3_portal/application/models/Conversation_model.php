<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/**
 * Project Atlas - CodeIgniter 3 Conversation Model
 * Tracks active session conversation IDs and loads recent message histories.
 */
class Conversation_model extends CI_Model {

    public function __construct() {
        parent::__construct();
    }

    /**
     * Gets or creates the current conversation ID in the user session.
     */
    public function get_active_conversation_id() {
        $conv_id = $this->session->userdata('atlas_active_conv_id');
        if (!$conv_id) {
            $conv_id = 'conv-' . bin2hex(random_bytes(6));
            $this->session->set_userdata('atlas_active_conv_id', $conv_id);
        }
        return $conv_id;
    }

    /**
     * Resets active conversation session.
     */
    public function new_conversation() {
        $conv_id = 'conv-' . bin2hex(random_bytes(6));
        $this->session->set_userdata('atlas_active_conv_id', $conv_id);
        $this->session->set_userdata('atlas_messages', array());
        return $conv_id;
    }

    /**
     * Appends message to session cache for rendering.
     */
    public function add_message($role, $content, $metadata = array()) {
        $messages = $this->session->userdata('atlas_messages') ?: array();
        $msg_id = 'msg-' . bin2hex(random_bytes(6));
        $messages[] = array(
            'id' => $msg_id,
            'role' => $role,
            'content' => $content,
            'metadata' => $metadata,
            'timestamp' => date('Y-m-d H:i:s')
        );
        $this->session->set_userdata('atlas_messages', $messages);
        return $msg_id;
    }

    /**
     * Retrieves stored session messages.
     */
    public function get_messages() {
        return $this->session->userdata('atlas_messages') ?: array();
    }
}
