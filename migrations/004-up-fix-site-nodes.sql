-- 
-- bugfix
-- the site_nodes should restrict to nodes where deleted is false
--

CREATE OR REPLACE VIEW site_nodes AS
SELECT site_id,
array_accum(node_id) AS node_ids
FROM nodes
WHERE deleted is false
GROUP BY site_id;

-- Bump subversion
UPDATE plc_db_version SET subversion = 4;
SELECT subversion from plc_db_version;

