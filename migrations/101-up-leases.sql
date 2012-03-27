-- we're using the 'lease' nodetype to model reservable nodes
INSERT INTO node_types VALUES ('reservable');
-- also the dummynet node_type is obsolete
DELETE FROM node_types WHERE node_type='dummynet';

SET TIMEZONE TO 'UTC';

CREATE TABLE leases (
    lease_id serial PRIMARY KEY,			-- id
    t_from timestamp with time zone NOT NULL,	-- from
    t_until timestamp with time zone NOT NULL,	-- until
    node_id integer REFERENCES nodes NOT NULL,		-- subject node
    slice_id integer REFERENCES slices,			-- slice owning the node
-- xxx for testing
--    CONSTRAINT future CHECK (t_from > CURRENT_TIMESTAMP),
    CONSTRAINT start_before_end CHECK (t_until > t_from)
) WITH OIDS;

--
-- hook to check for overlapping time slots on a given node_id
-- xxx might use the builtin OVERLAPS feature
-- http://www.postgresql.org/docs/8.3/interactive/functions-datetime.html
-- 
CREATE language plpgsql;
CREATE FUNCTION overlapping_trigger() RETURNS trigger AS $overlapping_trigger$
BEGIN
  PERFORM lease_id FROM leases WHERE 
    -- consider only leases on the same node
        NEW.node_id = node_id
    -- consider only non expired leases    
    AND t_until > CURRENT_TIMESTAMP
    -- useful for updates
    AND NEW.lease_id <> lease_id
    -- new start date is in range
    AND (   (NEW.t_from >= t_from AND NEW.t_from < t_until)
    -- new end date is in range
          OR (NEW.t_until > t_from AND NEW.t_until <= t_until)
    -- complete overlap: new from before from, new until after until
          OR (NEW.t_from <= t_from AND NEW.t_until >= t_until));
  IF FOUND THEN
    RAISE EXCEPTION 'overlapping  error: node % - slice %, % -> %', NEW.node_id, NEW.slice_id, NEW.t_from, NEW.t_until;
  END IF;
  RETURN NEW;
END;
$overlapping_trigger$ LANGUAGE plpgsql;

CREATE 
  TRIGGER overlapping_trigger BEFORE INSERT OR UPDATE 
  ON leases FOR EACH ROW EXECUTE PROCEDURE overlapping_trigger();

       
-- this is to let the API a chance to check for leases attached 
-- to a node that is not 'reservable'
CREATE OR REPLACE VIEW view_all_leases AS
SELECT 
leases.lease_id,
CAST(date_part('epoch', leases.t_from) AS bigint) AS t_from,
CAST(date_part('epoch', leases.t_until) AS bigint) AS t_until,
-- dbg
leases.t_from as s_from,
leases.t_until as s_until,
leases.node_id,
leases.slice_id,
nodes.hostname,
nodes.node_type,
slices.name,
slices.site_id,
CAST( date_part ('epoch',leases.t_until-leases.t_from) AS bigint) AS duration,
leases.t_until < CURRENT_TIMESTAMP as expired
FROM slices INNER JOIN leases USING (slice_id)
JOIN nodes USING (node_id);

-- only the relevant leases
CREATE OR REPLACE VIEW view_leases AS
SELECT * FROM view_all_leases
WHERE node_type = 'reservable';


--------------------------------------------------
UPDATE plc_db_version SET subversion = 101;
