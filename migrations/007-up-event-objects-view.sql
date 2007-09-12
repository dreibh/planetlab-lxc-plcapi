--
-- migration 007
-- change the way event objects are fetched, use a view for that purpose
-- 


CREATE OR REPLACE VIEW view_event_objects AS 
SELECT
events.event_id,
events.person_id,
events.node_id,
events.fault_code,
events.call_name,
events.call,
events.message,
events.runtime,
CAST(date_part('epoch', events.time) AS bigint) AS time,
event_object.object_id,
event_object.object_type
FROM events LEFT JOIN event_object USING (event_id);


---------- bump subversion

UPDATE plc_db_version SET subversion = 7;
SELECT subversion from plc_db_version;
