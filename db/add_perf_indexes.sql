-- Speed-up indexes for NGO search/filter (city, verified flag) and the
-- login lookup by email. Safe to run once against an existing DB.
-- Run with: mysql -u root -p impactconnect < db/add_perf_indexes.sql

ALTER TABLE ngos ADD INDEX idx_ngos_city (city);
ALTER TABLE ngos ADD INDEX idx_ngos_verified (verified);
-- users.email is already UNIQUE, which MySQL auto-indexes, so nothing needed there.
