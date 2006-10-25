<?php
//
// PlanetLab Central Slice API (PLCAPI) PHP interface
//
// DO NOT EDIT. This file was automatically generated at
// @DATE@.
//
// Mark Huang <mlhuang@cs.princeton.edu>
// Copyright (C) 2005-2006 The Trustees of Princeton University
//
// $Id: gen_php_api.py,v 1.13 2006/03/23 04:29:08 mlhuang Exp $
//
//

require_once 'plc_config.php';

class PLCAPI
{
  var $auth;
  var $server;
  var $port;
  var $path;
  var $errors;
  var $trace;
  var $calls;
  var $multicall;

  function PLCAPI ($auth,
		   $server = PLC_API_HOST,
		   $port = 8000, # PLC_API_PORT,
		   $path = PLC_API_PATH,
		   $cainfo = NULL)
  {
    $this->auth = $auth;
    $this->server = $server;
    $this->port = $port;
    $this->path = $path;
    $this->cainfo = $cainfo;
    $this->errors = array();
    $this->trace = array();
    $this->calls = array ();
    $this->multicall = false;
  }

  function error_log($error_msg, $backtrace_level = 1)
  {
    $backtrace = debug_backtrace();
    $file = $backtrace[$backtrace_level]['file'];
    $line = $backtrace[$backtrace_level]['line'];

    $this->errors[] = 'PLCAPI error:  ' . $error_msg . ' in ' . $file . ' on line ' . $line;
    error_log(end($this->errors));
  }

  function error ()
  {
    if (empty($this->trace)) {
      return NULL;
    } else {
      $last_trace = end($this->trace);
      return implode("\\n", $last_trace['errors']);
    }
  }

  function trace ()
  {
    return $this->trace;
  }

  function microtime_float()
  {
    list($usec, $sec) = explode(" ", microtime());
    return ((float) $usec + (float) $sec);
  }

  function call($method, $args = NULL)
  {
    if ($this->multicall) {
	$this->calls[] = array ('methodName' => $method,
				'params' => $args);
	return NULL;
    } else {
	return $this->internal_call ($method, $args, 3);
    }
  }

  function internal_call ($method, $args = NULL, $backtrace_level = 2)
  {
    $curl = curl_init();

    // Verify peer certificate if talking over SSL
    if ($this->port == 443) {
      curl_setopt($curl, CURLOPT_SSL_VERIFYPEER, 2);
      if (!empty($this->cainfo)) {
	curl_setopt($curl, CURLOPT_CAINFO, $this->cainfo);
      } elseif (defined('PLC_API_SSL_CRT')) {
        curl_setopt($curl, CURLOPT_CAINFO, PLC_API_SSL_CRT);
      }
      $url = 'https://';
    } else {
      $url = 'http://';
    }

    // Set the URL for the request
    $url .= $this->server . ':' . $this->port . '/' . $this->path;
    curl_setopt($curl, CURLOPT_URL, $url);

    // Marshal the XML-RPC request as a POST variable
    $request = xmlrpc_encode_request($method, $args);
    curl_setopt($curl, CURLOPT_POSTFIELDS, $request);

    // Construct the HTTP header
    $header[] = 'Content-type: text/xml';
    $header[] = 'Content-length: ' . strlen($request);
    curl_setopt($curl, CURLOPT_HTTPHEADER, $header);

    // Set some miscellaneous options
    curl_setopt($curl, CURLOPT_TIMEOUT, 30);

    // Get the output of the request
    curl_setopt($curl, CURLOPT_RETURNTRANSFER, 1);
    $t0 = $this->microtime_float();
    $output = curl_exec($curl);
    $t1 = $this->microtime_float();

    if (curl_errno($curl)) {
      $this->error_log('curl: ' . curl_error($curl), true);
      $ret = NULL;
    } else {
      $ret = xmlrpc_decode($output);
      if (is_array($ret) && xmlrpc_is_fault($ret)) {
        $this->error_log('Fault Code ' . $ret['faultCode'] . ': ' .
                         $ret['faultString'], $backtrace_level, true);
	$ret = NULL;
      }
    }

    curl_close($curl);

    $this->trace[] = array('method' => $method,
                           'args' => $args,
                           'runtime' => $t1 - $t0,
                           'return' => $ret,
                           'errors' => $this->errors);
    $this->errors = array();

    return $ret;
  }

  function begin()
  {
    if (!empty($this->calls)) {
      $this->error_log ('Warning: multicall already in progress');
    }

    $this->multicall = true;
  }

  function commit ()
  {
    if (!empty ($this->calls)) {
      $ret = array();
      $results = $this->internal_call ('system.multicall', array ($this->calls));
      foreach ($results as $result) {
        if (is_array($result)) {
          if (xmlrpc_is_fault($result)) {
            $this->error_log('Fault Code ' . $result['faultCode'] . ': ' .
                             $result['faultString'], 1, true);
            $ret[] = NULL;
          } else {
            $ret[] = $result[0];
          }
        } else {
          $ret[] = $result;
        }
      }
    } else {
      $ret = NULL;
    }

    $this->calls = array ();
    $this->multicall = false;

    return $ret;
  }

  //
  // PLCAPI Methods
  //

