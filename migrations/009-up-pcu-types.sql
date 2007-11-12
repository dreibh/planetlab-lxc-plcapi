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
    model text NOT NULL,	    	-- PCU model name
    name text   	  		-- Full PCU model name
) WITH OIDS;
CREATE INDEX pcu_types_model_idx ON pcu_types (model);

CREATE TABLE pcu_protocol_type (
    pcu_protocol_type_id serial PRIMARY KEY,	
    pcu_type_id integer REFERENCES pcu_types NOT NULL, 	-- PCU type identifier
    port integer NOT NULL, 				-- PCU port
    protocol text NOT NULL, 				-- Protocol 		    
    supported boolean NOT NULL DEFAULT True	  	-- Does PLC support
) WITH OIDS;
CREATE INDEX pcu_protocol_type_pcu_type_id ON pcu_protocol_type (pcu_type_id);
  

CREATE OR REPLACE VIEW pcu_protocol_types AS
SELECT pcu_type_id,
array_accum(pcu_protocol_type_id) as pcu_protocol_type_ids
FROM pcu_protocol_type
GROUP BY pcu_type_id;
    
CREATE OR REPLACE VIEW view_pcu_types AS
SELECT
pcu_types.pcu_type_id,
pcu_types.model,
pcu_types.name,
COALESCE((SELECT pcu_protocol_type_ids FROM pcu_protocol_types WHERE pcu_protocol_types.pcu_type_id = pcu_types.pcu_type_id), '{}') AS pcu_protocol_type_ids 
FROM pcu_types; 

UPDATE plc_db_version SET subversion = 9;
