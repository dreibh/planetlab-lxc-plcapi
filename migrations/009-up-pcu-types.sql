--
-- Tony Mack - PlanetLab
--
-- migration 009
--
-- purpose: provide a means for storing details about pcu models
--
--

CREATE TABLE pcu_types (
    pcu_type_id serial PRIMARY KEY, 	
    model text NOT NULL ,	    	-- PCU model name
    name text   	  		-- Full PCU model name
) WITH OIDS;
CREATE INDEX pcu_types_model_idx ON pcu_types (model);

CREATE TABLE pcu_type_port (
    pcu_type_id integer REFERENCES pcu_types NOT NULL, 	-- PCU type identifier
    port integer NOT NULL, 				-- PCU port
    protocol text NOT NULL, 				-- Protocol 		    
    supported boolean NOT NULL			  	-- Does PLC support
) WITH OIDS;
CREATE INDEX pcu_type_port_pcu_type_id ON pcu_type_port (pcu_type_id);
  

CREATE OR REPLACE VIEW pcu_type_ports AS
SELECT pcu_type_id,
array_accum(port) as ports,
array_accum(protocol) as protocols,
array_accum(supported) as supported
FROM pcu_type_port
GROUP BY pcu_type_id;
    
CREATE OR REPLACE VIEW view_pcu_types AS
SELECT
pcu_types.pcu_type_id,
pcu_types.model,
pcu_types.name,
COALESCE((SELECT ports FROM pcu_type_ports WHERE pcu_type_ports.pcu_type_id = pcu_types.pcu_type_id), '{}') AS ports,
COALESCE((SELECT protocols FROM pcu_type_ports WHERE pcu_type_ports.pcu_type_id = pcu_types.pcu_type_id), '{}') AS protocols,
COALESCE((SELECT supported FROM pcu_type_ports WHERE pcu_type_ports.pcu_type_id = pcu_types.pcu_type_id), '{}') AS supported
FROM pcu_types; 

UPDATE plc_db_version SET subversion = 9;
