<?php
defined('BASEPATH') OR exit('No direct script access allowed');

/**
 * Project Atlas - Client Model
 * Fetches tenant identities and report entitlement access status directly from MySQL.
 */
class Client_model extends CI_Model {

    public function __construct() {
        parent::__construct();
        $this->load->database();
    }

    /**
     * Retrieves client record by ID (e.g. C-01, C-02).
     */
    public function get_client($client_id) {
        $query = $this->db->get_where('clients', array('id' => $client_id));
        return $query->row_array();
    }

    /**
     * Returns a summary of full purchases and excerpt permissions for a client.
     */
    public function get_client_entitlements_summary($client_id) {
        $sql = "SELECT report_id, scope 
                FROM report_entitlements 
                WHERE client_id = ? AND access_granted = 1";
        $query = $this->db->query($sql, array($client_id));
        $rows = $query->result_array();

        $purchased = array();
        foreach ($rows as $r) {
            if ($r['scope'] === 'full') {
                $purchased[] = $r['report_id'];
            }
        }

        // R-102 is the designated public excerpt report in the system
        $excerpts = array('R-102');

        return array(
            'purchased_reports' => $purchased,
            'accessible_excerpts' => $excerpts
        );
    }

    /**
     * Retrieves complete report catalog joined with client's active entitlements.
     * Determines whether each report is Authorized (Full), Public Excerpt, or Restricted.
     */
    public function get_catalog_access($client_id) {
        $sql = "SELECT r.id, r.title, r.sector, r.access_type, r.total_pages,
                       re.scope, re.access_granted
                FROM reports r
                LEFT JOIN report_entitlements re 
                  ON r.id = re.report_id AND re.client_id = ? AND re.access_granted = 1
                ORDER BY r.id ASC";
        $query = $this->db->query($sql, array($client_id));
        $rows = $query->result_array();

        $catalog = array();
        foreach ($rows as $r) {
            if (!empty($r['access_granted']) && $r['scope'] === 'full') {
                $status = 'authorized';
                $label = 'Authorized (Full)';
            } elseif ($r['access_type'] === 'public_excerpt') {
                $status = 'public_excerpt';
                $label = 'Public Excerpt (pp. 1-14)';
            } else {
                $status = 'restricted';
                $label = 'Restricted';
            }

            $catalog[] = array(
                'id' => $r['id'],
                'title' => $r['title'],
                'sector' => $r['sector'],
                'access_type' => $r['access_type'],
                'status' => $status,
                'label' => $label
            );
        }

        return $catalog;
    }
}
