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

  function PLCAPI($auth = NULL,
		  $server = PLC_API_HOST,
		  $port = PLC_API_PORT,
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
    $this->calls = array();
    $this->multicall = false;
  }

  function rec_join ($arg) {
    if ( is_array($arg) ) {
        $ret = "";
        foreach ( $arg as $i ) {
            $l = $this->rec_join($i);
            # ignore html code.
            if ( $l[0] != "<" ) { $ret .= $l . ", "; }
        }
        return $ret;
    } else {
        settype($arg, "string");
        return $arg;
    }
  }

  function backtrace_php () {
    $backtrace = debug_backtrace();
    $msg = "";
    $len = count($backtrace);
    $cnt = 1;
    foreach( array_reverse($backtrace) as $line ) {
        $msg .= "File '". $line['file'] . "' line " . $line['line'] . "\n";
        $msg .= "    " . $line['function'] . "( "  . $this->rec_join($line['args']) . ")\n";
        $cnt += 1;
        if ( $cnt == $len ) { break; }
    }
    return $msg;
  }

  function error_log($error_msg, $backtrace_level = 1)
  {
    $backtrace = debug_backtrace();
    $file = $backtrace[$backtrace_level]['file'];
    $line = $backtrace[$backtrace_level]['line'];

    $error_line='PLCAPI error:  ' . $error_msg ;
    if ($file) $error_line .= ' in file ' . $file;
    if ($line) $error_line .= ' on line ' . $line;
    $this->errors[] = $error_line;
    # TODO: setup a config variable for more detailed stack traces, for API errors.
    if ( TRUE ){
      error_log($error_line);
    } else {
       error_log($this->backtrace_php());
    }
  }

  function error()
  {
    if (empty($this->trace)) {
      return NULL;
    } else {
      $last_trace = end($this->trace);
      return implode("\\n", $last_trace['errors']);
    }
  }

  function trace()
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

  function internal_call($method, $args = NULL, $backtrace_level = 2)
  {
    $curl = curl_init();

    // Verify peer certificate if talking over SSL
    if ($this->port == 443) {
      curl_setopt($curl, CURLOPT_SSL_VERIFYPEER, 2);
      if (!empty($this->cainfo)) {
	curl_setopt($curl, CURLOPT_CAINFO, $this->cainfo);
      } elseif (defined('PLC_API_CA_SSL_CRT')) {
        curl_setopt($curl, CURLOPT_CAINFO, PLC_API_CA_SSL_CRT);
      }
      $url = 'https://';
    } else {
      $url = 'http://';
    }

    // Set the URL for the request
    $url .= $this->server . ':' . $this->port . '/' . $this->path;
    curl_setopt($curl, CURLOPT_URL, $url);

    // Marshal the XML-RPC request as a POST variable. <nil/> is an
    // extension to the XML-RPC spec that is supported in our custom
    // version of xmlrpc.so via the 'allow_null' output_encoding key.
    $request = xmlrpc_encode_request($method, $args, array('allow_null' => TRUE));
    curl_setopt($curl, CURLOPT_POSTFIELDS, $request);

    // Construct the HTTP header
    $header[] = 'Content-type: text/xml';
    $header[] = 'Content-length: ' . strlen($request);
    curl_setopt($curl, CURLOPT_HTTPHEADER, $header);

    // Set some miscellaneous options
    curl_setopt($curl, CURLOPT_TIMEOUT, 180);

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

  function commit()
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
	    // Thierry - march 30 2007 
	    // using $adm->error() is broken with begin/commit style 
	    // this is because error() uses last item in trace and checks for ['errors']
	    // when using begin/commit we do run internal_call BUT internal_call checks for 
	    // multicall's result globally, not individual results, so ['errors'] comes empty
	    // I considered hacking internal_call 
	    // to *NOT* maintain this->trace at all when invoked with multicall
	    // but it is too complex to get all values right
	    // so let's go for the hacky way, and just record individual errors at the right place
            $this->trace[count($this->trace)-1]['errors'][] = end($this->errors);
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

    $this->calls = array();
    $this->multicall = false;

    return $ret;
  }

  //
  // PLCAPI Methods
  //

  function __call($name, $args)
  {
     array_unshift($args, $this->auth);
     return $this->call($name, $args);
  }
}

global $adm;

$adm = new PLCAPI(array('AuthMethod' => "capability",
			'Username' => PLC_API_MAINTENANCE_USER,
			'AuthString' => PLC_API_MAINTENANCE_PASSWORD));

?>
